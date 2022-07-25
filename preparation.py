import random
import json
import spacy
from spacy.training import offsets_to_biluo_tags
from sklearn.model_selection import train_test_split

def creation_files(query, path):
    nlp = spacy.load('it_core_news_sm')
    nlp_entities = []
    phrases_entities = []
    for phrase_entities in query:
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
        tags = offsets_to_biluo_tags(nlp(phrase_entities['phrase']), entities)
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
    training, test = train_test_split(phrases_entities, test_size=0.2)
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
    validation, test = train_test_split(test, test_size=0.5)
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
    ner = nlp.get_pipe('ner')
    for entity in nlp_entities:
        ner.add_label(entity)
    nlp.to_disk(path + '/models/entities')