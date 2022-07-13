import pandas as pd
import splitting as sp
import preprocessing as pc
import bert_training as bt
import os

ended = True

def start_training(mongo, learning_rate, eps, batch_size, max_epoch, patience, hidden_dropout_prob):
    global ended
    ended = False
    phrasesSentiments = []
    for phraseSentiment in mongo.db.training_phrases.find({'sentiment': {'$exists': 1,'$ne': ''}},{'_id': 0,'intent': 0,'entities': 0, 'emotion': 0}):
        phrasesSentiments.append(phraseSentiment)
    df = pd.DataFrame.from_records(phrasesSentiments).drop_duplicates()
    df_train, df_val, df_test = sp.split_strat_train_val_test(df, stratify_colname='sentiment')
    df_train_grouped = df_train.groupby('sentiment').apply(lambda x: x.sample(n=300, replace=True))
    pc.preprocess(df_train_grouped, df_val, col_name='sentiment')
    bt.train(df_train, col_name='sentiment', learning_rate=learning_rate, eps=eps, batch_size=batch_size, hidden_dropout_prob=hidden_dropout_prob, patience=patience, max_epoch=max_epoch)
    os.remove('train_sentiment_preprocessed.json')
    os.remove('val_sentiment_preprocessed.json')
    for file_name in os.listdir('models'):
        if 'checkpoint_sentiment' in file_name:
            file = os.path.join('models', file_name)
            if os.path.isfile(file):
                os.remove(file)
    ended = True

def get_num_epoch():
    return bt.get_num_epoch_sentiment()

def get_num_iteration():
    return bt.get_num_iteration_sentiment()

def get_epoch_length():
    return bt.get_epoch_length_sentiment()

def get_num_progress():
    return bt.get_num_progress_sentiment()

def get_ended():
    global ended
    return ended