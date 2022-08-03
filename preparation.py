import random
import os
import shutil
import json
import spacy
from spacy.gold import biluo_tags_from_offsets
from sklearn.model_selection import train_test_split

def creation_files(mongo, path):
    nlp = spacy.load('it_core_news_sm')
    nlp_entities = []
    phrases_entities = []
    for phrase_entities in mongo.db.training_phrases.find({'entities': {'$exists': 1,'$ne': '[]'}},{'_id': 0,'intent': 0, 'sentiment': 0, 'emotion': 0}):
        ext_dict = {'id': 0}
        ext_list = []
        mid_dict = {'raw': phrase_entities['phrase']}
        mid_list = []
        in_dict = {}
        in_list = []
        entities = []
        i = 1
        while i < len(phrase_entities['entities']):
            if(phrase_entities['entities'][i] == '('):
                i += 1
                first_index = ''
                last_index = ''
                label = ''
                while(phrase_entities['entities'][i] != ','):
                    first_index += phrase_entities['entities'][i]
                    i += 1
                i += 1
                while(phrase_entities['entities'][i] != ','):
                    last_index += phrase_entities['entities'][i]
                    i += 1
                i += 1
                while(phrase_entities['entities'][i] != ')'):
                    label += phrase_entities['entities'][i]
                    i += 1
                i += 2
                entities.append((int(first_index), int(last_index) + 1, label))
                if label not in nlp_entities:
                    nlp_entities.append(label)
        tags = biluo_tags_from_offsets(nlp(phrase_entities['phrase']), entities)
        in_id = 0
        for word in phrase_entities['phrase'].split():
            in_list.append({'id': in_id, 'orth': word, 'ner': tags[in_id]})
            in_id += 1
        in_dict['tokens'] = in_list
        in_dict['brackets'] = []
        mid_list.append(in_dict)
        mid_dict['sentences'] = mid_list
        mid_dict['cats'] = []
        ext_list.append(mid_dict)
        ext_dict['paragraphs'] = ext_list
        phrases_entities.append(ext_dict)
    random.shuffle(phrases_entities)
    training, remaining = train_test_split(phrases_entities, train_size = 0.8)
    id = 0
    while id < len(training):
        training[id]['id'] = id
        id += 1
    blank_spaces = '  '
    with open('train_entities.json', 'w', encoding='utf8') as train:
        train.write('[\n')
        j = 1
        for line in training:
            train.write(blank_spaces + '{\n' + (blank_spaces * 2) + '"id":' + str(line['id']))
            train.write(',\n' + (blank_spaces * 2) + '"paragraphs":[\n' + (blank_spaces * 3) + '{\n')
            paragraphs = line['paragraphs'][0]
            train.write((blank_spaces * 4) + '"raw":"' + paragraphs['raw'] + '",\n' + (blank_spaces * 4))
            train.write('"sentences":[\n' + (blank_spaces * 5) + '{\n' + (blank_spaces * 6) + '"tokens":[\n')
            tokens = paragraphs['sentences'][0]['tokens']
            i = 1
            for token in tokens:
                train.write((blank_spaces * 7) + '{\n' + (blank_spaces * 8) + '"id":' + str(token['id']) + ',\n')
                train.write((blank_spaces * 8) + '"orth":"' + token['orth'] + '",\n')
                train.write((blank_spaces * 8) + '"ner":"' + token['ner'] + '"\n' + (blank_spaces * 7) + '}')
                if i < len(tokens):
                    train.write(',\n')
                else:
                    train.write('\n' + (blank_spaces * 6) + '],\n' + (blank_spaces * 6) + '"brackets":[\n\n' + (blank_spaces * 6) + ']')
                i += 1
            train.write('\n' + (blank_spaces * 5) + '}\n' + (blank_spaces * 4) + '],\n' + (blank_spaces * 4) + '"cats":[\n\n' + (blank_spaces * 4) + ']\n')
            train.write((blank_spaces * 3) + '}\n' + (blank_spaces * 2) + ']\n' + blank_spaces + '}')
            if j < len(training):
                train.write(',\n')
            else:
                train.write('\n]')
            j += 1
    validation, remaining = train_test_split(phrases_entities, test_size = 0.8)
    id = 0
    while id < len(validation):
        validation[id]['id'] = id
        id += 1
    with open('validation_entities.json', 'w', encoding='utf8') as val:
        val.write('[\n')
        j = 1
        for line in validation:
            val.write(blank_spaces + '{\n' + (blank_spaces * 2) + '"id":' + str(line['id']))
            val.write(',\n' + (blank_spaces * 2) + '"paragraphs":[\n' + (blank_spaces * 3) + '{\n')
            paragraphs = line['paragraphs'][0]
            val.write((blank_spaces * 4) + '"raw":"' + paragraphs['raw'] + '",\n' + (blank_spaces * 4))
            val.write('"sentences":[\n' + (blank_spaces * 5) + '{\n' + (blank_spaces * 6) + '"tokens":[\n')
            tokens = paragraphs['sentences'][0]['tokens']
            i = 1
            for token in tokens:
                val.write((blank_spaces * 7) + '{\n' + (blank_spaces * 8) + '"id":' + str(token['id']) + ',\n')
                val.write((blank_spaces * 8) + '"orth":"' + token['orth'] + '",\n')
                val.write((blank_spaces * 8) + '"ner":"' + token['ner'] + '"\n' + (blank_spaces * 7) + '}')
                if i < len(tokens):
                    val.write(',\n')
                else:
                    val.write('\n' + (blank_spaces * 6) + '],\n' + (blank_spaces * 6) + '"brackets":[\n\n' + (blank_spaces * 6) + ']')
                i += 1
            val.write('\n' + (blank_spaces * 5) + '}\n' + (blank_spaces * 4) + '],\n' + (blank_spaces * 4) + '"cats":[\n\n' + (blank_spaces * 4) + ']\n')
            val.write((blank_spaces * 3) + '}\n' + (blank_spaces * 2) + ']\n' + blank_spaces + '}')
            if j < len(validation):
                val.write(',\n')
            else:
                val.write('\n]')
            j += 1
    test, remaining = train_test_split(phrases_entities, test_size = 0.9)
    test_json = []
    for phrase_dict in test:
        text = phrase_dict['paragraphs'][0]['raw']
        for phrase_entities in mongo.db.training_phrases.find({'entities': {'$exists': 1,'$ne': '[]'}},{'_id': 0,'intent': 0, 'sentiment': 0, 'emotion': 0}):
            if text == phrase_entities['phrase']:
                entities = []
                i = 1
                while i < len(phrase_entities['entities']):
                    if(phrase_entities['entities'][i] == '('):
                        i += 1
                        first_index = ''
                        last_index = ''
                        label = ''
                        while(phrase_entities['entities'][i] != ','):
                            first_index += phrase_entities['entities'][i]
                            i += 1
                        i += 1
                        while(phrase_entities['entities'][i] != ','):
                            last_index += phrase_entities['entities'][i]
                            i += 1
                        i += 1
                        while(phrase_entities['entities'][i] != ')'):
                            label += phrase_entities['entities'][i]
                            i += 1
                        i += 2
                        entities.append((int(first_index), int(last_index) + 1, label))
                test_json.append({'phrase': text, 'entities': entities})
    with open('test_entities.json', 'w', encoding='utf8') as testing:
        for line in test_json:
            testing.write(json.dumps(line) + '\n')
    ner = nlp.get_pipe('ner')
    for entity in nlp_entities:
        ner.add_label(entity)
    if not os.path.isdir(path + '/models/base-train-entities'):
        os.mkdir(os.path.join(path, 'models', 'base-train-entities'))  
    nlp.to_disk(os.path.join(path, 'models', 'base-train-entities', 'base-model'))

def delete_entities(path):
    if os.path.isdir(os.path.join(path, 'models', 'base-train-entities', 'base-model')):
        for element_name in os.listdir(os.path.join(path, 'models', 'base-train-entities', 'base-model')):
            element = os.path.join(path, 'models', 'base-train-entities', 'base-model', element_name)
            if os.path.isfile(element):
                os.remove(element)
            else:
                for sub_element_name in os.listdir(element):
                    sub_element = os.path.join(element, sub_element_name)
                    if os.path.isfile(sub_element):
                        os.remove(sub_element)
                os.rmdir(element)
        os.rmdir(os.path.join(path, 'models', 'base-train-entities', 'base-model'))
    if os.path.isdir(os.path.join(path, 'models', 'base-train-entities', 'trained-models')):
        for model in os.listdir(os.path.join(path, 'models', 'base-train-entities', 'trained-models')):
            if model == 'entities':
                continue
            for element_name in os.listdir(os.path.join(path, 'models', 'base-train-entities', 'trained-models', model)):
                element = os.path.join(path, 'models', 'base-train-entities', 'trained-models', model, element_name)
                if os.path.isfile(element):
                    os.remove(element)
                else:
                    for sub_element_name in os.listdir(element):
                        sub_element = os.path.join(element, sub_element_name)
                        if os.path.isfile(sub_element):
                            os.remove(sub_element)
                    os.rmdir(element)
            os.rmdir(os.path.join(path, 'models', 'base-train-entities', 'trained-models', model))

def copy_entities(path):
    if os.path.isdir(os.path.join(path, 'models', 'base-train-entities', 'trained-models', 'entities')):
        os.mkdir(os.path.join(path, 'models', 'entities'))
        source_folder = os.path.join(path, 'models', 'base-train-entities', 'trained-models', 'entities')
        destination_folder = os.path.join(path, 'models', 'entities')
        for file_name in os.listdir(source_folder):
            source = os.path.join(source_folder, file_name)
            destination = os.path.join(destination_folder, file_name)
            if os.path.isfile(source):
                shutil.copy(source, destination)
                os.remove(source)
            else:
                os.mkdir(destination)
                for sub_element_name in os.listdir(source):
                    sub_element = os.path.join(source, sub_element_name)
                    sub_element_destination = os.path.join(destination, sub_element_name)
                    if os.path.isfile(sub_element):
                        shutil.copy(sub_element, sub_element_destination)
                        os.remove(sub_element)
                os.rmdir(source)
        os.rmdir(source_folder)
        os.rmdir(os.path.join(path, 'models', 'base-train-entities', 'trained-models'))
        os.rmdir(os.path.join(path, 'models', 'base-train-entities'))

def delete_already_trained(path):
    if os.path.isdir(os.path.join(path, 'models', 'entities')):
        for element_name in os.listdir(os.path.join(path, 'models', 'entities')):
            element = os.path.join(path, 'models', 'entities', element_name)
            if os.path.isfile(element):
                os.remove(element)
            else:
                for sub_element_name in os.listdir(element):
                    sub_element = os.path.join(element, sub_element_name)
                    if os.path.isfile(sub_element):
                        os.remove(sub_element)
                os.rmdir(element)
        os.rmdir(os.path.join(path, 'models', 'entities'))