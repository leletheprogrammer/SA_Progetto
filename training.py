import os
import pandas as pd

import bert_training as bt
import preparation as p
import preprocessing as pc
import splitting as sp
import training_ee as t

ended_intent = {}
ended_entities = {}
ended_sentiment = {}

def initialization(mongo, name):
    global ended_intent
    global ended_entities
    global ended_sentiment
    partial_name = name + 'dataset'
    for element in mongo.db.list_collection_names():
        if partial_name in element:
            if element not in ended_intent.keys():
                ended_intent[element] = True
            if element not in ended_entities.keys():
                ended_entities[element] = True
            if element not in ended_sentiment.keys():
                ended_sentiment[element] = True

def start_training_intent(mongo, data, name, learning_rate, eps, batch_size, max_epoch, patience, hidden_dropout_prob):
    global ended_intent
    ended_intent[data] = False
    phrases = []
    for phrase in mongo.db[data].find({'intent': {'$exists': 1,'$ne': ''}},{'_id': 0,'entities': 0, 'sentiment': 0, 'emotion': 0}):
        phrases.append(phrase)
    bt.initialization(mongo, name)
    training_models(mongo, data, name + '_' + data[len(name) + 7 : ], 'intent', phrases, learning_rate, eps, batch_size, max_epoch, patience, hidden_dropout_prob)
    ended_intent[data] = True

def start_training_entities(mongo, path, dropout_from, dropout_to, batch_from, batch_to, max_iterations_entities):
    global ended_entities
    ended_entities = False
    p.delete_already_trained(path)
    p.creation_files(mongo, path)
    t.create_results()
    t.train(lang='it', output_path=path + '/models/base-train-entities/trained-models',
            base_model=path + '/models/base-train-entities/base-model',
            pipeline='ner', n_early_stopping=1, train_path=path + '/train_entities.json',
            dev_path=path + '/validation_entities.json', dropout_from = dropout_from, dropout_to = dropout_to,
            batch_from = batch_from, batch_to = batch_to, n_iter = max_iterations_entities)
    os.remove(os.path.join(path, 'train_entities.json'))
    os.remove(os.path.join(path, 'validation_entities.json'))
    p.delete_entities(path)
    p.copy_entities(path)
    ended_entities = True

def start_training_sentiment(mongo, data, name, learning_rate, eps, batch_size, max_epoch, patience, hidden_dropout_prob):
    global ended_sentiment
    ended_sentiment[data] = False
    phrases = []
    for phrase in mongo.db[data].find({'sentiment': {'$exists': 1,'$ne': ''}},{'_id': 0,'intent': 0,'entities': 0, 'emotion': 0}):
        phrases.append(phrase)
    bt.initialization(mongo, name)
    training_models(mongo, data, name + '_' + data[len(name) + 7 : ], 'sentiment', phrases, learning_rate, eps, batch_size, max_epoch, patience, hidden_dropout_prob)
    ended_sentiment[data] = True

def training_models(mongo, data, name, col_name, phrases, learning_rate, eps, batch_size, max_epoch, patience, hidden_dropout_prob):
    df = pd.DataFrame.from_records(phrases).drop_duplicates()
    df_train, df_val, df_test = sp.split_strat_train_val_test(df, stratify_colname=col_name)
    df_test.to_csv('test_' + col_name + '_' +  name + '_' +  '.csv', index=False)
    df_train_grouped = df_train.groupby(col_name).apply(lambda x: x.sample(n=300, replace=True))
    pc.preprocess(df_train_grouped, df_val, col_name=col_name, dataset_name=name)
    bt.train(df_train, data=data, name=name, col_name=col_name, learning_rate=learning_rate, eps=eps,
             batch_size=batch_size, hidden_dropout_prob=hidden_dropout_prob, patience=patience, max_epoch=max_epoch)
    os.remove('train_' + col_name + '_' + name + '_preprocessed.json')
    os.remove('val_' + col_name + '_' + name + '_preprocessed.json')
    for file_name in os.listdir('models'):
        if ('checkpoint_' + col_name + '_' + name) in file_name:
            file = os.path.join('models', file_name)
            if os.path.isfile(file):
                os.remove(file)

def get_num_epoch_intent(data):
    return bt.get_num_epoch_intent(data)

def get_num_iteration_intent(data):
    return bt.get_num_iteration_intent(data)

def get_epoch_length_intent(data):
    return bt.get_epoch_length_intent(data)

def get_num_progress_intent(data):
    return bt.get_num_progress_intent(data)

def get_num_epoch_sentiment(data):
    return bt.get_num_epoch_sentiment(data)

def get_num_iteration_sentiment(data):
    return bt.get_num_iteration_sentiment(data)

def get_epoch_length_sentiment(data):
    return bt.get_epoch_length_sentiment(data)

def get_num_progress_sentiment(data):
    return bt.get_num_progress_sentiment(data)

def get_num_iteration_entities():
    return t.get_num_iteration()

def get_num_progress_entities():
    return t.get_num_progress()

def get_ended_intent(data):
    global ended_intent
    return ended_intent[data]

def get_ended_sentiment(data):
    global ended_sentiment
    return ended_sentiment[data]

def get_ended_entities():
    global ended_entities
    return ended_entities