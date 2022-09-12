from joblib import dump
import json
from multiprocessing import Pool
import numpy as np
import pandas as pd
import re
import string

from sklearn.preprocessing import LabelEncoder
import torch
from torch.utils.data import Dataset

EMOJI_PATTERN = re.compile(
    "["
    u"\U0001F600-\U0001F64F"
    u"\U0001F300-\U0001F5FF"
    u"\U0001F680-\U0001F6FF"
    u"\U0001F1E0-\U0001F1FF"
    "]+", flags=re.UNICODE)
_RE_COMBINE_WHITESPACE = re.compile(r"\s+")

class DatasetProcessor:
    def __init__(self, df, tokenizer, nlp, label_col, dataset_name,text_col='phrase', max_len=80):
        self.df = df.sample(frac=1, random_state=123)
        self.nlp = nlp
        self.label_col = label_col
        self.text_col = text_col
        self.max_len = max_len
        self.tokenizer = tokenizer
        self.dataset_name = dataset_name
        self.mapping = self.get_mapping()

    def get_mapping(self):
        le = LabelEncoder()
        le.fit(self.df[self.label_col])
        le_name_mapping = dict(zip(le.classes_, le.transform(le.classes_)))
        dump(le, 'mapping_' + self.label_col + '_' + self.dataset_name + '.joblib')
        return le_name_mapping

    def clean(self, doc):
        out = ''
        for t in doc:
            bad = t.like_url
            bad |= t.text.startswith('@')
            bad |= t.text.startswith('#')
            bad |= t.like_email
            bad |= t.like_num
            if not bad:
                out += t.text_with_ws
        out = re.sub(r"""([?.!,;"'])""", r" ", out)
        out = out.translate(str.maketrans('', '', string.punctuation))
        out = EMOJI_PATTERN.sub(r'', out)
        out = _RE_COMBINE_WHITESPACE.sub(" ", out).strip()
        return self.nlp(out)

    def process(self, df_row):
        doc = self.nlp(df_row[self.text_col])
        if self.label_col == 'sentiment':
            doc = self.clean(doc)
        doc = doc[:self.max_len]
        input_ids = self.tokenizer.encode(doc.text, add_special_tokens=True)
        size = len(input_ids)
        if size > self.max_len:
            input_ids = input_ids[:self.max_len]
            size = len(input_ids)
        if size < self.max_len:
            input_ids += [self.tokenizer.pad_token_id] * (self.max_len - size)
        assert len(input_ids) == self.max_len
        token_type_ids = [0] * size + [1] * (self.max_len - size) if size < self.max_len else [0] * size
        attention_mask = [1] * size + [0] * (self.max_len - size) if size < self.max_len else [1] * size
        label = self.mapping[df_row[self.label_col]]
        return input_ids, attention_mask, token_type_ids, label

    def transform(self, df):
        processed = []
        for _, row in df.iterrows():
            processed.append(self.process(row))
        return pd.DataFrame(
            data=processed, columns=['input_ids', 'attention_mask', 'token_type_ids', 'labels'])

    def run(self, save_path):
        n_worker = 5
        df_split = np.array_split(self.df, n_worker)
        pool = Pool(n_worker)
        df = pd.concat(pool.map(self.transform, df_split))
        pool.close()
        pool.join()
        df.to_json(save_path, orient='values')


class TextualDataset(Dataset):
    def __init__(self, path, device):
        self.device = device
        with open(path, 'r') as fp:
            self.data = json.load(fp)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, item):
        ids, att, tokens, labels = list(map(lambda o: torch.tensor(o).to(self.device), self.data[item]))
        return ids.long(), att.float(), tokens.long(), labels.long()
