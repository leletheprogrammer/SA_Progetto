import pandas as pd
import splitting as sp
import preprocessing as pc
import bert_training as bt

def start_training(mongo):
    phrasesIntents = []
    for phraseIntent in mongo.db.training_phrases.find({'intent': {'$exists': 1,'$ne': ''}},{'_id': 0,'entities': 0, 'sentiment': 0, 'emotion': 0}):
        phrasesIntents.append(phraseIntent)
    df = pd.DataFrame.from_records(phrasesIntents).drop_duplicates()
    df_train, df_val, df_test = sp.split_strat_train_val_test(df, stratify_colname='intent')
    df_train_grouped = df_train.groupby('intent').apply(lambda x: x.sample(n=300, replace=True))
    pc.preprocess(df_train_grouped, df_val)
    bt.train(df_train, learning_rate=5e-5, eps=1e-8, batch_size=16, hidden_dropout_prob=0.3, patience=2, max_epoch=2)