import os
import preparation as p
import training as t

ended = True

def train(mongo, path, dropout_from, dropout_to, batch_from, batch_to, max_iterations_entities):
    global ended
    ended = False
    p.creation_files(mongo.db.training_phrases.find({'entities': {'$exists': 1,'$ne': '[]'}},{'_id': 0,'intent': 0, 'sentiment': 0, 'emotion': 0}), path)
    t.create_results()
    t.train(lang='it', output_path=path + '/models/entities/trained-model', base_model=path + '/models/entities/base-model', pipeline='ner', n_early_stopping=1, train_path=path + '/train_entities.json', dev_path=path + '/validation_entities.json', dropout_from = dropout_from, dropout_to = dropout_to, batch_from = batch_from, batch_to = batch_to, n_iter = max_iterations_entities)
    if os.path.isfile(os.path.join(path, 'train_entities.json')):
        os.remove(os.path.join(path, 'train_entities.json'))
    if os.path.isfile(os.path.join(path, 'validation_entities.json')):
        os.remove(os.path.join(path, 'validation_entities.json'))
    ended = True

def get_num_iteration():
    return t.get_num_iteration()

def get_num_progress():
    return t.get_num_progress()

def get_ended():
    global ended
    return ended