import os
import pandas as pd

import bert_training as bt
import preprocessing as pc
import splitting as sp

ended_intent = True
ended_sentiment = True

def start_training_intent(mongo, learning_rate, eps, batch_size, max_epoch, patience, hidden_dropout_prob):
    global ended_intent
    ended_intent = False
    phrases = []
    for phrase in mongo.db.training_phrases.find({'intent': {'$exists': 1,'$ne': ''}},{'_id': 0,'entities': 0, 'sentiment': 0, 'emotion': 0}):
        phrases.append(phrase)
    training(mongo, 'intent', phrases, learning_rate, eps, batch_size, max_epoch, patience, hidden_dropout_prob)
    ended_intent = True

def start_training_sentiment(mongo, learning_rate, eps, batch_size, max_epoch, patience, hidden_dropout_prob):
    global ended_sentiment
    ended_sentiment = False
    phrases = []
    for phrase in mongo.db.training_phrases.find({'sentiment': {'$exists': 1,'$ne': ''}},{'_id': 0,'intent': 0,'entities': 0, 'emotion': 0}):
        phrases.append(phrase)
    training(mongo, 'sentiment', phrases, learning_rate, eps, batch_size, max_epoch, patience, hidden_dropout_prob)
    ended_sentiment = True

def training(mongo, col_name, phrases, learning_rate, eps, batch_size, max_epoch, patience, hidden_dropout_prob):
    df = pd.DataFrame.from_records(phrases).drop_duplicates()
    df_train, df_val, df_test = sp.split_strat_train_val_test(df, stratify_colname=col_name)
    df_test.to_csv('test_' + col_name + '.csv', index=False)
    df_train_grouped = df_train.groupby(col_name).apply(lambda x: x.sample(n=300, replace=True))
    pc.preprocess(df_train_grouped, df_val, col_name=col_name)
    bt.train(df_train, col_name=col_name, learning_rate=learning_rate, eps=eps,
             batch_size=batch_size, hidden_dropout_prob=hidden_dropout_prob, patience=patience, max_epoch=max_epoch)
    os.remove('train_' + col_name + '_preprocessed.json')
    os.remove('val_' + col_name + '_preprocessed.json')
    for file_name in os.listdir('models'):
        if ('checkpoint_' + col_name) in file_name:
            file = os.path.join('models', file_name)
            if os.path.isfile(file):
                os.remove(file)

def get_num_epoch_intent():
    return bt.get_num_epoch_intent()

def get_num_iteration_intent():
    return bt.get_num_iteration_intent()

def get_epoch_length_intent():
    return bt.get_epoch_length_intent()

def get_num_progress_intent():
    return bt.get_num_progress_intent()

def get_num_epoch_sentiment():
    return bt.get_num_epoch_sentiment()

def get_num_iteration_sentiment():
    return bt.get_num_iteration_sentiment()

def get_epoch_length_sentiment():
    return bt.get_epoch_length_sentiment()

def get_num_progress_sentiment():
    return bt.get_num_progress_sentiment()

def get_ended_intent():
    global ended_intent
    return ended_intent

def get_ended_sentiment():
    global ended_sentiment
    return ended_sentiment