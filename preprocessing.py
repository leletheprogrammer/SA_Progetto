import spacy
from transformers import AutoTokenizer

import dataset_intent as di
import dataset_sentiment as ds

def preprocess(df_train, df_val, col_name):
    transformer_model_name = 'dbmdz/bert-base-italian-xxl-cased'
    spacy_model_name = 'it_core_news_sm'
    tokenizer = AutoTokenizer.from_pretrained(transformer_model_name)
    nlp = spacy.load(spacy_model_name)
    for name, df in [('train', df_train), ('val', df_val)]:
        if col_name == 'intent':
            processor = di.DatasetProcessor(
                df=df, tokenizer=tokenizer, nlp=nlp, max_len=80, text_col='phrase', label_col=col_name)
            processor.run(f'{name}_{col_name}_preprocessed.json')
        elif col_name == 'sentiment':
            processor = ds.DatasetProcessor(
                df=df, tokenizer=tokenizer, nlp=nlp, max_len=80, text_col='phrase', label_col=col_name)
            processor.run(f'{name}_{col_name}_preprocessed.json')
