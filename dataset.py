import pandas as pd
import numpy as np
from multiprocessing import Pool
import torch
from sklearn.preprocessing import LabelEncoder
from torch.utils.data import Dataset
import json
from joblib import dump


class DatasetProcessor:

    def __init__(self, df, tokenizer, nlp, text_col='phrase', label_col='intent', max_len=80):
        self.df = df.sample(frac=1, random_state=97)
        self.nlp = nlp
        self.label_col = label_col
        self.text_col = text_col
        self.max_len = max_len
        self.tokenizer = tokenizer
        self.mapping = self.get_mapping()

    def get_mapping(self):
        le = LabelEncoder()
        le.fit(self.df['intent'])
        le_name_mapping = dict(zip(le.classes_, le.transform(le.classes_)))
        dump(le, 'mapping.joblib')
        return le_name_mapping

    def process(self, df_row):
        doc = self.nlp(df_row[self.text_col])
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
