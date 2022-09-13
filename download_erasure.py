from io import BytesIO
import os
from os.path import basename
import zipfile

def download_intent(name, dataset):
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_name in os.listdir(os.path.join('models', 'intent_' + name + '_' + dataset)):
            file = os.path.join('models', 'intent_' + name + '_' + dataset, file_name)
            zipf.write(file, basename(file))
    memory_file.seek(0)
    return memory_file

def download_entities(name, dataset):
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for element_name in os.listdir(os.path.join('models', 'entities_' + name + '_' + dataset)):
            element = os.path.join('models', 'entities_' + name + '_' + dataset, element_name)
            if os.path.isfile(element):
                zipf.write(element, basename(element))
            else:
                for sub_element_name in os.listdir(element):
                    sub_element = os.path.join(element, sub_element_name)
                    zipf.write(sub_element, os.path.join(element_name, sub_element_name))
    memory_file.seek(0)
    return memory_file

def download_sentiment(name, dataset):
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_name in os.listdir(os.path.join('models', 'sentiment_' + name + '_' + dataset)):
            file = os.path.join('models', 'sentiment_' + name + '_' + dataset, file_name)
            zipf.write(file, basename(file))
    memory_file.seek(0)
    return memory_file

def delete_intent():
    if os.path.isfile('mapping_intent.joblib'):
        os.remove('mapping_intent.joblib')
    if os.path.isfile('test_intent.csv'):
        os.remove('test_intent.csv')
    if os.path.isfile('results_intent.csv'):
        os.remove('results_intent.csv')
    if os.path.isdir('static'):
        if os.path.isdir(os.path.join('static', 'images')):
            if os.path.isfile(os.path.join('static', 'images', 'loss_graphic_intent.png')):
                os.remove(os.path.join('static', 'images', 'loss_graphic_intent.png'))
            if os.path.isfile(os.path.join('static', 'images', 'score_graphic_intent.png')):
                os.remove(os.path.join('static', 'images', 'score_graphic_intent.png'))
    for file_name in os.listdir(os.path.join('models', 'intent')):
        file = os.path.join('models', 'intent', file_name)
        if os.path.isfile(file):
            os.remove(file)
    os.rmdir(os.path.join('models', 'intent'))

def delete_entities():
    if os.path.isfile('test_entities.json'):
        os.remove('test_entities.json')
    if os.path.isfile('results_entities.csv'):
        os.remove('results_entities.csv')
    if os.path.isdir('static'):
        if os.path.isdir(os.path.join('static', 'images')):
            if os.path.isfile(os.path.join('static', 'images', 'loss_graphic_entities.png')):
                os.remove(os.path.join('static', 'images', 'loss_graphic_entities.png'))
            if os.path.isfile(os.path.join('static', 'images', 'score_graphic_entities.png')):
                os.remove(os.path.join('static', 'images', 'score_graphic_entities.png'))
    for element_name in os.listdir(os.path.join('models', 'entities')):
        element = os.path.join('models', 'entities', element_name)
        if os.path.isfile(element):
            os.remove(element)
        else:
            for sub_element_name in os.listdir(element):
                sub_element = os.path.join(element, sub_element_name)
                if os.path.isfile(sub_element):
                    os.remove(sub_element)
            os.rmdir(element)
    os.rmdir(os.path.join('models', 'entities'))

def delete_sentiment():
    if os.path.isfile('mapping_sentiment.joblib'):
        os.remove('mapping_sentiment.joblib')
    if os.path.isfile('test_sentiment.csv'):
        os.remove('test_sentiment.csv')
    if os.path.isfile('results_sentiment.csv'):
        os.remove('results_sentiment.csv')
    if os.path.isdir('static'):
        if os.path.isdir(os.path.join('static', 'images')):
            if os.path.isfile(os.path.join('static', 'images', 'loss_graphic_sentiment.png')):
                os.remove(os.path.join('static', 'images', 'loss_graphic_sentiment.png'))
            if os.path.isfile(os.path.join('static', 'images', 'score_graphic_sentiment.png')):
                os.remove(os.path.join('static', 'images', 'score_graphic_sentiment.png'))
    for file_name in os.listdir(os.path.join('models', 'sentiment')):
        file = os.path.join('models', 'sentiment', file_name)
        if os.path.isfile(file):
            os.remove(file)
    os.rmdir(os.path.join('models', 'sentiment'))