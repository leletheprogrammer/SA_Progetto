from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
from matplotlib.figure import Figure
import os
from os.path import basename
import pandas as pd
from random import randint
import smtplib
import ssl
from threading import Lock
import zipfile

from flask import Flask, render_template, request, redirect, url_for, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from flask_pymongo import PyMongo
from flask_socketio import SocketIO

import training_ir_sa as tis
import training_entities_extraction as tee
import testing_ir_sa as teis
import testing_entities as ten

'''app represents the web application and
__name__ represents the name of the current file'''
app = Flask(__name__)
sio = SocketIO(app)

mongo = PyMongo(app, 'mongodb://localhost:27017/NLPDatabase', connect = True)

login_user = None
needed = None

thread_training_intent = None
thread_training_sentiment = None
thread_training_entities = None
thread_lock = Lock()
max_epoch_intent = 0
max_epoch_sentiment = 0
max_iterations_entities = 0

'''decorator that defines the url path
where will be the index page of the site'''
@app.route('/')
#standard name for functions that works on the index page
def index():
    global login_user
    if login_user:
        return redirect(url_for('home'))
    else:
        return render_template('index.html')

'''decorator that defines the url path
where will be the services area of the site'''
@app.route('/services_area/')
def services_area():
    global login_user
    if login_user:
        return redirect(url_for('home'))
    else:
        return render_template('services_area.html')

'''decorator that defines the url path
where will be the login page of the site'''
@app.route('/services_area/login', methods = ['POST', 'GET'])
def login():
    global login_user
    if login_user:
        return redirect(url_for('home'))
    else:
        global needed
        valid = True
        if request.method == 'POST':
            needed = None
            form_data = request.form
            
            email = form_data['email']
            password = form_data['password']
            
            user = mongo.db.users.find_one({'email': email})
            if user == None:
                valid = not valid
            else:
                if check_password_hash(user['password'], password):
                    login_user = user
                    return redirect(url_for('home'))
                else:
                    valid = not valid
            
            return render_template('login.html', needed = needed, valid = valid)
        elif request.method == 'GET':
            return render_template('login.html', needed = needed, valid = valid)

'''decorator that defines the url path
where will be the sign up page of the site'''
@app.route('/services_area/sign_up/', methods = ['POST', 'GET'])
def sign_up():
    global login_user
    if login_user:
        return redirect(url_for('home'))
    else:
        validation = False
        valid = True
        found = False
        email = None
        if request.method == 'POST':
            form_data = request.form
            
            email = form_data['email']
            name = form_data['name']
            password = form_data['password']
            
            user = mongo.db.users.find_one({'email': email})
            if user != None:
                valid = not valid
                return render_template('sign_up.html', validation = validation, valid = valid, found = found, email = email)
            else:
                user_to_validate = mongo.db.users_to_validate.find_one({'email': email})
                if user_to_validate != None:
                    found = not found
                    return render_template('sign_up.html', validation = validation, valid = valid, found = found, email = email)
                else:
                    code = generate_password_hash(str(randint(0, 10000)), method = 'sha256')
                    
                    mongo.db.users_to_validate.insert_one({'email': email, 'name': name, 'password': generate_password_hash(password, method = 'sha256'), 'code': code})
                    
                    sender = 'nlpwebplatformserver@gmail.com'
                    receiver = email
                    
                    message = MIMEMultipart('alternative')
                    message['Subject'] = 'Email di conferma validazione registrazione'
                    message['From'] = sender
                    message['To'] = receiver
                    
                    #create the plain-text and HTML version of the message
                    text = '''Ciao, le è stata inviata questa email per confermare la registrazione al sito.\nClicchi su questo link:\nhttp://127.0.0.1:5000/services_area/sign_up/validation?email=''' + email + '''&code=''' + code
                    html = '''<html><body><p>Ciao, le è stata inviata questa email per confermare la registrazione al sito.<br>Clicchi su questo link:<br><a href="http://127.0.0.1:5000/services_area/sign_up/validation?email=''' + email + '''&code=''' + code + '''">http://127.0.0.1:5000/services_area/sign_up/validation?email=''' + email + '''&code=''' + code + '''</a></p></body></html>'''
                    
                    #turn these into plain/html MIMEText objects
                    part1 = MIMEText(text, 'plain')
                    part2 = MIMEText(html, 'html')
                    
                    #add HTML/plain-text parts to MIMEMultipart message
                    #the email client will try to render the last part first
                    message.attach(part1)
                    message.attach(part2)
                    
                    #create secure connection with server and send email
                    context = ssl.create_default_context()
                    with smtplib.SMTP_SSL('smtp.gmail.com', port = 465, context = context) as server:
                        server.login(sender, 'jcnkadjivnhhebnh')
                        server.sendmail(sender, receiver, message.as_string())
                    
                    validation = not validation
                    return render_template('sign_up.html', validation = validation, valid = valid, found = found, email = email)
        elif request.method == 'GET':
            return render_template('sign_up.html', validation = validation, valid = valid, found = found, email = email)

'''decorator that defines the url path
where will be the validation'''
@app.route('/services_area/sign_up/validation')
def validation():
    error = False
    
    args = request.args
    if args.__len__() == 2:
        email = args['email']
        code = args['code']
        
        user = mongo.db.users_to_validate.find_one({'email': email, 'code': code})
        if user == None:
            error = not error
            return render_template('validation.html', error = error)
        
        mongo.db.users.insert_one({'email': user['email'], 'name': user['name'], 'password': user['password']})
        mongo.db.users_to_validate.delete_one(user)
        
        return render_template('validation.html', error = error)
    else:
        error = not error
        return render_template('validation.html', error = error)

'''decorator that defines the url path
where will be the logout page of the site'''
@app.route('/logout')
def logout():
    global login_user
    if login_user:
        login_user = None
        global needed
        needed = None
        return render_template('logout.html')
    else:
        return redirect(url_for('index'))

'''decorator that defines the url path
where will be the home page of the site'''
@app.route('/home/')
def home():
    global login_user
    if login_user:
        initialization_database()
        name = login_user['name']
        return render_template('home.html', name = name)
    else:
        global needed
        needed = True
        return redirect(url_for('login'))

def initialization_database():
    numberSentiments = mongo.db.sentiments.estimated_document_count()
    if (numberSentiments == 0):
        mongo.db.sentiments.insert_one({'category': 'Positivo'})
        mongo.db.sentiments.insert_one({'category': 'Neutrale'})
        mongo.db.sentiments.insert_one({'category': 'Negativo'})
    numberEmotions = mongo.db.emotions.estimated_document_count()
    if (numberEmotions == 0):
        mongo.db.emotions.insert_one({'type': 'Felicità'})
        mongo.db.emotions.insert_one({'type': 'Tristezza'})
        mongo.db.emotions.insert_one({'type': 'Rabbia'})
        mongo.db.emotions.insert_one({'type': 'Disgusto'})
        mongo.db.emotions.insert_one({'type': 'Sorpresa'})
        mongo.db.emotions.insert_one({'type': 'Paura'})

'''decorator that defines the url path
where will be the intents'''
@app.route('/home/intents', methods = ['POST', 'GET'])
#standard name for functions that works on the home page
def intents():
    global login_user
    if login_user:
        page = int(request.args.get('page'))
        numberIntents = mongo.db.intents.estimated_document_count()
        if (numberIntents > 0 and (page < 1 or (page > 1 and ((int(numberIntents / 20) + 1) < page) or (numberIntents % 20 == 0 and  numberIntents / 20 < page)))):
            return redirect(url_for('intents', page = 1))
        
        if request.method == 'POST':
            form_data = request.form
            
            if form_data['submitButton'] == 'Elimina':
                oldIntent = form_data['oldIntent']
                mongo.db.intents.delete_one({'typology': oldIntent})
                
                for phrase in mongo.db.training_phrases.find({'intent': oldIntent}):
                    mongo.db.training_phrases.replace_one(phrase, {'phrase': phrase['phrase'], 'intent': '', 'entities': phrase['entities'], 'sentiment': phrase['sentiment'], 'emotion': phrase['emotion']})
            elif form_data['submitButton'] == 'Svuotamento':
                if len(list(mongo.db.intents.find())) != 0:
                    mongo.db.intents.delete_many({})
                    
                    for phrase in mongo.db.training_phrases.find():
                        mongo.db.training_phrases.replace_one(phrase, {'phrase': phrase['phrase'], 'intent': '', 'entities': phrase['entities'], 'sentiment': phrase['sentiment'], 'emotion': phrase['emotion']})
            elif form_data['submitButton'] == 'Modifica':
                oldIntent = form_data['oldIntent']
                newIntent = form_data['newIntent']
                if newIntent.isspace() == False:
                    newIntent = ' '.join(newIntent.split())
                    
                    intent = mongo.db.intents.find_one({'typology': newIntent})
                    if intent == None:
                        mongo.db.intents.replace_one({'typology': oldIntent}, {'typology': newIntent})
                        
                        for phrase in mongo.db.training_phrases.find({'intent': oldIntent}):
                            mongo.db.training_phrases.replace_one(phrase, {'phrase': phrase['phrase'], 'intent': '', 'entities': phrase['entities'], 'sentiment': phrase['sentiment'], 'emotion': phrase['emotion']})
            elif form_data['submitButton'] == 'Aggiungi':
                newIntent = form_data['newIntent']
                if newIntent.isspace() == False:
                    newIntent = ' '.join(newIntent.split())
                    
                    intent = mongo.db.intents.find_one({'typology': newIntent})
                    if intent == None:
                        mongo.db.intents.insert_one({'typology': newIntent})
            
            #offers a html template on the page
            return redirect(url_for('intents', page = page))
        elif request.method == 'GET':
            typologies = []
            #iteration among the documents in the collection 'intents'
            for intent in mongo.db.intents.find():
                #intent is a dict, so typologies is a list of dict
                typologies.append(intent)
            
            #offers a html template on the page
            return render_template('intents.html', page = page, typologies = typologies)
    else:
        global needed
        needed = True
        return redirect(url_for('login'))

'''decorator that defines the url path
where will be the entities'''
@app.route('/home/entities', methods = ['POST', 'GET'])
#standard name for functions that works on the home page
def entities():
    global login_user
    if login_user:
        page = int(request.args.get('page'))
        numberEntities = mongo.db.entities.estimated_document_count()
        if (numberEntities > 0 and (page < 1 or (page > 1 and ((int(numberEntities / 20) + 1) < page) or (numberEntities % 20 == 0 and  numberEntities / 20 < page)))):
            return redirect(url_for('entities', page = 1))
        
        if request.method == 'POST':
            form_data = request.form
            
            if form_data['submitButton'] == 'Elimina':
                oldEntity = form_data['oldEntity']
                mongo.db.entities.delete_one({'namedEntity': oldEntity})
                
                for phrase in mongo.db.training_phrases.find():
                    entities_list = phrase['entities'].replace('(', '').replace(')', '').replace('[', '').replace(']', '').split(',')
                    entities = '['
                    
                    if len(entities_list) != 1:
                        i = 0
                        while i < (len(entities_list) - 1):
                            if entities_list[i + 2] == oldEntity:
                                entities_list.pop(i)
                                entities_list.pop(i)
                                entities_list.pop(i)
                                i -= 3
                            else:
                                if i > 0:
                                    entities += ','
                                entities += '(' + entities_list[i] + ',' + entities_list[i + 1] + ',' + entities_list[i + 2] + ')'
                            i += 3
                    entities += ']'
                    
                    mongo.db.training_phrases.replace_one(phrase, {'phrase': phrase['phrase'], 'intent': phrase['intent'], 'entities': entities, 'sentiment': phrase['sentiment'], 'emotion': phrase['emotion']})
            elif form_data['submitButton'] == 'Svuotamento':
                if len(list(mongo.db.entities.find())) != 0:
                    mongo.db.entities.delete_many({})
                    
                    for phrase in mongo.db.training_phrases.find():
                        mongo.db.training_phrases.replace_one(phrase, {'phrase': phrase['phrase'], 'intent': phrase['intent'], 'entities': '[]', 'sentiment': phrase['sentiment'], 'emotion': phrase['emotion']})
            elif form_data['submitButton'] == 'Modifica':
                oldEntity = form_data['oldEntity']
                newEntity = form_data['newEntity']
                if newEntity.isspace() == False:
                    newEntity = ' '.join(newEntity.split())
                    
                    entity = mongo.db.entities.find_one({'namedEntity': newEntity})
                    if entity == None:
                        mongo.db.entities.replace_one({'namedEntity': oldEntity}, {'namedEntity': newEntity})
                        
                        for phrase in mongo.db.training_phrases.find():
                            entities_list = phrase['entities'].replace('(', '').replace(')', '').replace('[', '').replace(']', '').split(',')
                            entities = '['
                            
                            if len(entities_list) != 1:
                                i = 0
                                while i < (len(entities_list) - 1):
                                    if entities_list[i + 2] == oldEntity:
                                        entities_list.pop(i)
                                        entities_list.pop(i)
                                        entities_list.pop(i)
                                        i -= 3
                                    else:
                                        if i > 0:
                                            entities += ','
                                        entities += '(' + entities_list[i] + ',' + entities_list[i + 1] + ',' + entities_list[i + 2] + ')'
                                    i += 3
                            entities += ']'
                            
                            mongo.db.training_phrases.replace_one(phrase, {'phrase': phrase['phrase'], 'intent': phrase['intent'], 'entities': entities, 'sentiment': phrase['sentiment'], 'emotion': phrase['emotion']})
            elif form_data['submitButton'] == 'Aggiungi':
                newEntity = form_data['newEntity']
                
                if newEntity.isspace() == False:
                    newEntity = ' '.join(newEntity.split())
                    
                    entity = mongo.db.entities.find_one({'namedEntity': newEntity})
                    if entity == None:
                        mongo.db.entities.insert_one({'namedEntity': newEntity})
            
            #offers a html template on the page
            return redirect(url_for('entities', page = page))
        elif request.method == 'GET':
            namedEntities = []
            #iteration among the documents in the collection 'entities'
            for entity in mongo.db.entities.find():
                #entity is a dict, so typologies is a list of dict
                namedEntities.append(entity)
            
            #offers a html template on the page
            return render_template('entities.html', page = page, namedEntities = namedEntities)
    else:
        global needed
        needed = True
        return redirect(url_for('login'))

'''decorator that defines the url path
where will be the training phrases'''
@app.route('/home/training_phrases', methods = ['POST', 'GET'])
#standard name for functions that works on the home page
def training_phrases():
    global login_user
    if login_user:
        page = int(request.args.get('page'))
        numberPhrases = mongo.db.training_phrases.estimated_document_count()
        if (numberPhrases > 0 and (page < 1 or (page > 1 and ((int(numberPhrases / 20) + 1) < page) or (numberPhrases % 20 == 0 and  numberPhrases / 20 < page)))):
            return redirect(url_for('training_phrases', page = 1))
        if request.method == 'POST':
            form_data = request.form
            
            if form_data['submitButton'] == 'Elimina':
                oldPhrase = form_data['oldPhrase']
                mongo.db.training_phrases.delete_one({'phrase': oldPhrase})
            elif form_data['submitButton'] == 'Svuotamento':
                if len(list(mongo.db.training_phrases.find())) != 0:
                    mongo.db.training_phrases.delete_many({})
            elif form_data['submitButton'] == 'Modifica':
                oldPhrase = form_data['oldPhrase']
                newPhrase = form_data['newPhrase']
                if newPhrase.isspace() == False:
                    newPhrase = ' '.join(newPhrase.split())
                    
                    phrase = mongo.db.training_phrases.find_one({'phrase': newPhrase})
                    if phrase == None:
                        mongo.db.training_phrases.replace_one({'phrase': oldPhrase}, {'phrase': newPhrase})
            elif form_data['submitButton'] == 'Aggiungi':
                newPhrase = form_data['newPhrase']
                intentAssociated = form_data['selectIntent']
                entitiesAssociated = '['
                sentimentAssociated = form_data['selectSentiment']
                emotionAssociated = form_data['selectEmotion']
                if newPhrase.isspace() == False:
                    newPhrase = ' '.join(newPhrase.split())
                    
                    phrase = mongo.db.training_phrases.find_one({'phrase': newPhrase})
                    
                    i = 1
                    while True:
                        if 'entity' + str(i) in form_data.keys():
                            try:
                                first = newPhrase.index(form_data['entity' + str(i)])
                            except ValueError:
                                pass
                            entitiesAssociated += '(' + str(first) + ',' + str(first + len(form_data['entity' + str(i)]) - 1) + ',' + form_data['namedEntity' + str(i)] + '),'
                        else:
                            if (entitiesAssociated[len(entitiesAssociated) - 1] != '['):
                                entitiesAssociated = entitiesAssociated[:len(entitiesAssociated) - 1] + ']'
                            else:
                                entitiesAssociated += ']'
                            break
                        i = i + 1
            
                    if phrase == None:
                        mongo.db.training_phrases.insert_one({'phrase': newPhrase, 'intent': intentAssociated, 'entities': entitiesAssociated, 'sentiment': sentimentAssociated, 'emotion': emotionAssociated})
            elif form_data['submitButton'] == 'Annota':
                phraseSelected = form_data['notePhraseSelected']
                intentAssociated = form_data['selectNoteIntent']
                entitiesAssociated = '['
                sentimentAssociated = form_data['selectNoteSentiment']
                emotionAssociated = form_data['selectNoteEmotion']
                
                phrase = mongo.db.training_phrases.find_one({'phrase': phraseSelected})
                
                i = 1
                while True:
                    if 'entity' + str(i) in form_data.keys():
                        try:
                            first = phraseSelected.index(form_data['entity' + str(i)])
                        except ValueError:
                            pass
                        entitiesAssociated += '(' + str(first) + ',' + str(first + len(form_data['entity' + str(i)]) - 1) + ',' + form_data['namedEntity' + str(i)] + '),'
                    else:
                        if (entitiesAssociated[len(entitiesAssociated) - 1] != '['):
                            entitiesAssociated = entitiesAssociated[:len(entitiesAssociated) - 1] + ']'
                        else:
                            entitiesAssociated += ']'
                        break
                    i = i + 1
                
                mongo.db.training_phrases.replace_one(phrase, {'phrase': phraseSelected, 'intent': intentAssociated, 'entities': entitiesAssociated, 'sentiment': sentimentAssociated, 'emotion': emotionAssociated})
            elif form_data['submitButton'] == 'Invia':
                file = request.files['file']
                text = file.read().decode('utf-8').splitlines()
                
                phrases = ''.join(text).split('/:')
                
                i = 0
                while i < (len(phrases) - 1):
                    phrase = phrases[i]
                    intent = phrases[i + 1]
                    entities = phrases[i + 2]
                    sentiment = phrases[i + 3]
                    emotion = phrases[i + 4]
                    
                    if mongo.db.training_phrases.find_one({'phrase': phrase}) == None:
                        if intent != '':
                            temp_intent = mongo.db.intents.find_one({'typology': intent})
                            if temp_intent == None:
                                mongo.db.intents.insert_one({'typology': intent})
                        
                        if entities == '':
                            entities = '[]'
                        else:
                            entities_list = ':'.join(entities.split(',')).split(':')
                            entities = '['
                            j = 0
                            while j < (len(entities_list) - 1):
                                first_index = phrase.find(entities_list[j])
                                last_index = len(entities_list[j]) + first_index - 1
                                
                                if j != 0:
                                    entities += ','
                                entities += '(' + str(first_index) + ',' + str(last_index) + ',' + entities_list[j + 1] + ')'
                                
                                if mongo.db.entities.find_one({'namedEntity': entities_list[j + 1]}) == None:
                                    mongo.db.entities.insert_one({'namedEntity': entities_list[j + 1]})
                                
                                j += 2
                            
                            entities += ']'
                        
                        if sentiment != '':
                            temp_sentiment = mongo.db.sentiments.find_one({'category': sentiment})
                            if temp_sentiment == None:
                                mongo.db.sentiments.insert_one({'category': sentiment})
                        
                        if emotion != '':
                            temp_emotion = mongo.db.emotions.find_one({'type': emotion})
                            if temp_emotion == None:
                                mongo.db.emotions.insert_one({'type': emotion})
                        
                        mongo.db.training_phrases.insert_one({'phrase': phrase, 'intent': intent, 'entities': entities, 'sentiment': sentiment, 'emotion': emotion})
                    
                    i += 5
            
            #offers a html template on the page
            return redirect(url_for('training_phrases', page = page))
        elif request.method == 'GET':
            phrases = []
            #iteration among the documents in the collection 'training_phrases'
            for phrase in mongo.db.training_phrases.find():
                if phrase.get('entities') != None:
                    if phrase['entities'] == '[]':
                        phrase['entities'] = ''
                    else:
                        split_list = phrase['entities'].replace('[', '').replace(']', '').replace('(', '').replace(')', '').split(',')
                        
                        entities_list = []
                        i = 0
                        while i < len(split_list):
                            substring = phrase['phrase'][int(split_list[i]):int(split_list[i + 1]) + 1]
                            
                            if entities_list:
                                entities_list.append(', ')
                            
                            entities_list.append(substring)
                            entities_list.append(':')
                            entities_list.append(split_list[i + 2])
                            
                            i += 3
                        phrase['entities'] = ''.join(entities_list)
                #phrase is a dict, so typologies is a list of dict
                phrases.append(phrase)
            
            intents = []
            for intent in mongo.db.intents.find():
                intents.append(intent)
            
            namedEntities = []
            for entity in mongo.db.entities.find():
                namedEntities.append(entity)
            
            sentiments = []
            for sentiment in mongo.db.sentiments.find():
                sentiments.append(sentiment)
            
            emotions = []
            for emotion in mongo.db.emotions.find():
                emotions.append(emotion)
            
            #offers a html template on the page
            return render_template('training_phrases.html', page = page, phrases = phrases, intents = intents, namedEntities = namedEntities, sentiments = sentiments, emotions = emotions)
    else:
        global needed
        needed = True
        return redirect(url_for('login'))

'''decorator that defines the url path
of the page where to train the models'''
@app.route('/home/start_training_model', methods = ['POST', 'GET'])
def start_training_model():
    global login_user
    if login_user:
        if request.method == 'POST':
            form_data = request.form
            if (form_data['submitButton'] == 'intentRecognition' or form_data['submitButton'] == 'sentimentAnalysis'):
                learning_rate = 0.1
                eps = 0.5
                batch_size = 16
                patience = 2
                hidden_dropout_prob = 0.3
                if 'insertLearningRate' in form_data:
                    try:
                        learning_rate = float(form_data['insertLearningRate'])
                    except ValueError:
                        learning_rate = 0.1
                if 'insertEps' in form_data:
                    try:
                        eps = float(form_data['insertEps'])
                    except ValueError:
                        eps = 0.5
                if 'selectBatchSize' in form_data:
                    if form_data['selectBatchSize'] != '':
                        batch_size = int(form_data['selectBatchSize'])
                    else:
                        batch_size = 16
                if 'insertPatience' in form_data:
                    try:
                        patience = int(form_data['insertPatience'])
                    except ValueError:
                        patience = 2
                if 'insertHiddenDropout' in form_data:
                    try:
                        hidden_dropout_prob = float(form_data['insertHiddenDropout'])
                    except ValueError:
                        hidden_dropout_prob = 0.3
                if (form_data['submitButton'] == 'intentRecognition'):
                    if tis.get_ended_intent():
                        global max_epoch_intent
                        max_epoch_intent = 2
                        if 'insertMaxEpoch' in form_data:
                            try:
                                max_epoch_intent = int(form_data['insertMaxEpoch'])
                            except ValueError:
                                max_epoch_intent = 2
                        global thread_training_intent
                        with thread_lock:
                            thread_training_intent = sio.start_background_task(tis.start_training_intent, mongo, learning_rate, eps, batch_size, max_epoch_intent, patience, hidden_dropout_prob)
                    else:
                        return render_template('start_training_model.html', model_training = 'Intent Recognition')
                elif (form_data['submitButton'] == 'sentimentAnalysis'):
                    if tis.get_ended_sentiment():
                        global max_epoch_sentiment
                        max_epoch_intent = 2
                        if 'insertMaxEpoch' in form_data:
                            try:
                                max_epoch_sentiment = int(form_data['insertMaxEpoch'])
                            except ValueError:
                                max_epoch_sentiment = 2
                        global thread_training_sentiment
                        with thread_lock:
                            thread_training_sentiment = sio.start_background_task(tis.start_training_sentiment, mongo, learning_rate, eps, batch_size, max_epoch_sentiment, patience, hidden_dropout_prob)
                    else:
                        return render_template('start_training_model.html', model_training = 'Sentiment Analysis')
            elif (form_data['submitButton'] == 'entitiesExtraction'):
                dropout_from = 0.1
                dropout_to = 0.5
                batch_from = 100.0
                batch_to = 1000.0
                if 'insertDropoutFrom' in form_data:
                    try:
                        dropout_from = float(form_data['insertDropoutFrom'])
                    except ValueError:
                        dropout_from = 0.1
                if 'insertDropoutTo' in form_data:
                    try:
                        dropout_to = float(form_data['insertDropoutTo'])
                    except ValueError:
                        dropout_to = 0.5
                if 'insertBatchFrom' in form_data:
                    try:
                        batch_from = float(form_data['insertBatchFrom'])
                    except ValueError:
                        batch_from = 100.0
                if 'insertBatchTo' in form_data:
                    try:
                        batch_to = float(form_data['insertBatchTo'])
                    except ValueError:
                        batch_to = 1000.0
                if tee.get_ended():
                    global max_iterations_entities
                    max_iterations_entities = 30
                    if 'insertNumIterations' in form_data:
                        try:
                            max_iterations_entities = int(form_data['insertNumIterations'])
                        except ValueError:
                            max_iterations_entities = 30
                    global thread_training_entities
                    with thread_lock:
                        thread_training_entities = sio.start_background_task(tee.train, mongo, app.root_path, dropout_from, dropout_to, batch_from, batch_to, max_iterations_entities)
                else:
                    return render_template('start_training_model.html', model_training = 'Entities Extraction')
            return render_template('start_training_model.html', model_success = form_data['submitButton'])
        elif request.method == 'GET':
            return render_template('start_training_model.html')
    else:
        global needed
        needed = True
        return redirect(url_for('login'))

'''decorator that defines the url path
of the page where see the status of the
training of the intent recognition model'''
@app.route('/home/status_model_intent', methods = ['POST', 'GET'])
def status_model_intent():
    global login_user
    if login_user:
        if thread_training_intent is None:
            return render_template("status_model_intent.html", not_training = True)
        else:
            if(tis.get_num_epoch_intent() == -1):
                return render_template("status_model_intent.html", loading = True)
            else:
                global max_epoch_intent
                return render_template("status_model_intent.html", num_epoch = tis.get_num_epoch_intent(), num_iteration = tis.get_num_iteration_intent(), length_epoch = tis.get_epoch_length_intent(), num_progress = tis.get_num_progress_intent(), max_epoch = max_epoch_intent)
    else:
        global needed
        needed = True
        return redirect(url_for('login'))

'''decorator that defines the url path
of the page where see the status of the
training of the sentiment analysis model'''
@app.route('/home/status_model_entities', methods = ['POST', 'GET'])
def status_model_entities():
    global login_user
    if login_user:
        if thread_training_entities is None:
            return render_template("status_model_entities.html", not_training = True)
        else:
            if(tee.get_num_iteration() == -1):
                return render_template("status_model_entities.html", loading = True)
            else:
                global max_iterations_entities
                return render_template("status_model_entities.html", iteration = tee.get_num_iteration(), max_iteration = max_iterations_entities, num_progress = tee.get_num_progress())
    else:
        global needed
        needed = True
        return redirect(url_for('login'))

'''decorator that defines the url path
of the page where see the status of the
training of the sentiment analysis model'''
@app.route('/home/status_model_entities', methods = ['POST', 'GET'])
def status_model_entities():
    global login_user
    if login_user:
        if thread_training_entities is None:
            return render_template("status_model_entities.html", not_training = True)
        else:
            if(tee.get_num_iteration() == -1):
                return render_template("status_model_entities.html", loading = True)
            else:
                global max_iterations_entities
                return render_template("status_model_entities.html", iteration = tee.get_num_iteration(), max_iteration = max_iterations_entities, num_progress = tee.get_num_progress())
    else:
        global needed
        needed = True
        return redirect(url_for('login'))

'''decorator that defines the url path
of the page where see the status of the
training of the sentiment analysis model'''
@app.route('/home/status_model_sentiment', methods = ['POST', 'GET'])
def status_model_sentiment():
    global login_user
    if login_user:
        if thread_training_sentiment is None:
            return render_template("status_model_sentiment.html", not_training = True)
        else:
            if(tis.get_num_epoch_sentiment() == -1):
                return render_template("status_model_sentiment.html", loading = True)
            else:
                global max_epoch_sentiment
                return render_template("status_model_sentiment.html", num_epoch = tis.get_num_epoch_sentiment(), num_iteration = tis.get_num_iteration_sentiment(), length_epoch = tis.get_epoch_length_sentiment(), num_progress = tis.get_num_progress_sentiment(), max_epoch = max_epoch_sentiment)
    else:
        global needed
        needed = True
        return redirect(url_for('login'))

'''decorator that defines the url path of the
page where to test and show results of the models'''
@app.route('/home/show_results_testing', methods = ['POST', 'GET'])
def show_results_testing():
    global login_user
    if login_user:
        if request.method == 'POST':
            form_data = request.form
            if('submitButton' in form_data):
                if(form_data['submitButton'] == 'visualizeIntent'):
                    if(os.path.isfile('results_intent.csv')):
                        return render_template('show_results_testing.html', results_intent = pd.read_csv('results_intent.csv').values.tolist())
                    else:
                        return render_template('show_results_testing.html', not_present = 'Intent Recognition')
                elif(form_data['submitButton'] == 'visualizeEntities'):
                    if(os.path.isfile('results_entities.csv')):
                        return render_template('show_results_testing.html', results_entities = pd.read_csv('results_entities.csv').values.tolist())
                    else:
                        return render_template('show_results_testing.html', not_present = 'Entities Extraction')
                elif(form_data['submitButton'] == 'visualizeSentiment'):
                    if(os.path.isfile('results_sentiment.csv')):
                        return render_template('show_results_testing.html', results_sentiment = pd.read_csv('results_sentiment.csv').values.tolist())
                    else:
                        return render_template('show_results_testing.html', not_present = 'Sentiment Analysis')
                elif(form_data['submitButton'] == 'buttonTestingIntent'):
                    if(os.path.isfile('mapping_intent.joblib') and os.path.isfile('test_intent.csv')):
                        score = teis.testing_intent()
                        return render_template('show_results_testing.html', testing_intent = str(score))
                    else:
                        return render_template('show_results_testing.html', not_present = 'Intent Recognition')
                elif(form_data['submitButton'] == 'buttonTestingEntities'):
                    if(os.path.isfile('test_entities.json')):
                        score = ten.test()
                        return render_template('show_results_testing.html', testing_entities = str(score))
                    else:
                        return render_template('show_results_testing.html', not_present = 'Entities Extraction')
                elif(form_data['submitButton'] == 'buttonTestingSentiment'):
                    if(os.path.isfile('mapping_sentiment.joblib') and os.path.isfile('test_sentiment.csv')):
                        score = teis.testing_sentiment()
                        return render_template('show_results_testing.html', testing_sentiment = str(score))
                    else:
                        return render_template('show_results_testing.html', not_present = 'Sentiment Analysis')
            if('graphicLoss' in form_data):
                fig = Figure()
                axis = fig.add_subplot(1, 1, 1)
                if(form_data['graphicLoss'] == 'graphicLossIntent'):
                    df_intent = pd.read_csv('results_intent.csv')
                    axis.plot(df_intent[['Loss Training', 'Loss Validation']])
                    axis.legend(['Loss Training', 'Loss Validation'])
                elif(form_data['graphicLoss'] == 'graphicLossSentiment'):
                    df_sentiment = pd.read_csv('results_sentiment.csv')
                    axis.plot(df_sentiment[['Loss Training', 'Loss Validation']])
                    axis.legend(['Loss Training', 'Loss Validation'])
                elif(form_data['graphicLoss'] == 'graphicLossEntities'):
                    df_entities = pd.read_csv('results_entities.csv')
                    axis.plot(df_entities[['loss']])
                axis.set_xlabel('epoch')
                axis.set_ylabel('loss')
                if not os.path.isdir('static'):
                    os.mkdir('static')
                if not os.path.isdir(os.path.join('static', 'images')):
                    os.mkdir(os.path.join('static', 'images'))
                if(form_data['graphicLoss'] == 'graphicLossIntent'):
                    fig.savefig(os.path.join('static', 'images','loss_graphic_intent.png'))
                    return render_template('show_results_testing.html', loss_intent = 'loss_graphic_intent.png')
                elif(form_data['graphicLoss'] == 'graphicLossSentiment'):
                    fig.savefig(os.path.join('static', 'images','loss_graphic_sentiment.png'))
                    return render_template('show_results_testing.html', loss_sentiment = 'loss_graphic_sentiment.png')
                elif(form_data['graphicLoss'] == 'graphicLossEntities'):
                    fig.savefig(os.path.join('static', 'images','loss_graphic_entities.png'))
                    return render_template('show_results_testing.html', loss_entities = 'loss_graphic_entities.png')
            if('graphicScore' in form_data):
                fig = Figure()
                axis = fig.add_subplot(1, 1, 1)
                if(form_data['graphicScore'] == 'graphicScoreIntent'):
                    df_intent = pd.read_csv('results_intent.csv')
                    axis.plot(df_intent[['F1-Score Training', 'F1-Score Validation']])
                    axis.legend(['F1-Score Training', 'F1-Score Validation'])
                elif(form_data['graphicScore'] == 'graphicScoreSentiment'):
                    df_sentiment = pd.read_csv('results_sentiment.csv')
                    axis.plot(df_sentiment[['F1-Score Training', 'F1-Score Validation']])
                    axis.legend(['F1-Score Training', 'F1-Score Validation'])
                elif(form_data['graphicScore'] == 'graphicScoreEntities'):
                    df_entities = pd.read_csv('results_entities.csv')
                    axis.plot(df_entities[['f1']])
                axis.set_xlabel('epoch')
                axis.set_ylabel('score')
                if not os.path.isdir('static'):
                    os.mkdir('static')
                if not os.path.isdir(os.path.join('static', 'images')):
                    os.mkdir(os.path.join('static', 'images'))
                if(form_data['graphicScore'] == 'graphicScoreIntent'):
                    fig.savefig(os.path.join('static', 'images','score_graphic_intent.png'))
                    return render_template('show_results_testing.html', score_intent = 'score_graphic_intent.png')
                elif(form_data['graphicScore'] == 'graphicScoreSentiment'):
                    fig.savefig(os.path.join('static', 'images','score_graphic_sentiment.png'))
                    return render_template('show_results_testing.html', score_sentiment = 'score_graphic_sentiment.png')
                elif(form_data['graphicScore'] == 'graphicScoreEntities'):
                    fig.savefig(os.path.join('static', 'images','score_graphic_entities.png'))
                    return render_template('show_results_testing.html', score_entities = 'score_graphic_entities.png')
        elif request.method == 'GET':
            return render_template('show_results_testing.html')
    else:
        global needed
        needed = True
        return redirect(url_for('login'))

'''decorator that defines the url path of
the page where to download or erase the models'''
@app.route('/home/download_erasure_model', methods = ['POST', 'GET'])
def download_erasure_model():
    global login_user
    if login_user:
        if request.method == 'POST':
            form_data = request.form
            if(form_data['submitButton'] == 'downloadIntent'):
                if(not os.path.isdir(os.path.join('models', 'intent'))):
                    return render_template('download_erasure_model.html', model_download = 'Intent Recognition')
                else:
                    return render_template('download_erasure_model.html', model_download_present = 'downloadIntentRecognition')
            elif(form_data['submitButton'] == 'downloadEntities'):
                if(not os.path.isdir(os.path.join('models', 'entities'))):
                    return render_template('download_erasure_model.html', model_download = 'Entities Extraction')
                else:
                    return render_template('download_erasure_model.html', model_download_present = 'downloadEntitiesExtraction')
            elif(form_data['submitButton'] == 'downloadSentiment'):
                if(not os.path.isdir(os.path.join('models', 'sentiment'))):
                    return render_template('download_erasure_model.html', model_download = 'Sentiment Analysis')
                else:
                    return render_template('download_erasure_model.html', model_download_present = 'downloadSentimentAnalysis')
            elif(form_data['submitButton'] == 'deleteIntent'):
                if(not os.path.isdir(os.path.join('models', 'intent'))):
                    return render_template('download_erasure_model.html', model_erasure = 'Intent Recognition')
                else:
                    return render_template('download_erasure_model.html', model_erasure_present = 'deleteIntentRecognition')
            elif(form_data['submitButton'] == 'deleteEntities'):
                if(not os.path.isdir(os.path.join('models', 'entities'))):
                    return render_template('download_erasure_model.html', model_erasure = 'Entities Extraction')
                else:
                    return render_template('download_erasure_model.html', model_erasure_present = 'deleteEntitiesExtraction')
            elif(form_data['submitButton'] == 'deleteSentiment'):
                if(not os.path.isdir(os.path.join('models', 'sentiment'))):
                    return render_template('download_erasure_model.html', model_erasure = 'Sentiment Analysis')
                else:
                    return render_template('download_erasure_model.html', model_erasure_present = 'deleteSentimentAnalysis')
            elif(form_data['submitButton'] == 'downloadIntentRecognition'):
                memory_file = BytesIO()
                with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_name in os.listdir(os.path.join('models', 'intent')):
                        file = os.path.join('models', 'intent', file_name)
                        zipf.write(file, basename(file))
                memory_file.seek(0)
                return send_file(memory_file, attachment_filename = 'intent.zip', as_attachment = True)
            elif(form_data['submitButton'] == 'downloadEntitiesExtraction'):
                memory_file = BytesIO()
                with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for element_name in os.listdir(os.path.join('models', 'entities')):
                        element = os.path.join('models', 'entities', element_name)
                        if os.path.isfile(element):
                            zipf.write(element, basename(element))
                        else:
                            for sub_element_name in os.listdir(element):
                                sub_element = os.path.join(element, sub_element_name)
                                zipf.write(sub_element, os.path.join(element_name, sub_element_name))
                memory_file.seek(0)
                return send_file(memory_file, attachment_filename = 'entities.zip', as_attachment = True)
            elif(form_data['submitButton'] == 'downloadSentimentAnalysis'):
                memory_file = BytesIO()
                with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_name in os.listdir(os.path.join('models', 'sentiment')):
                        file = os.path.join('models', 'sentiment', file_name)
                        zipf.write(file, basename(file))
                memory_file.seek(0)
                return send_file(memory_file, attachment_filename = 'sentiment.zip', as_attachment = True)
            elif(form_data['submitButton'] == 'deleteIntentRecognition'):
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
            elif(form_data['submitButton'] == 'deleteEntitiesExtraction'):
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
            elif(form_data['submitButton'] == 'deleteSentimentAnalysis'):
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
            return render_template('download_erasure_model.html')
        elif request.method == 'GET':
            return render_template('download_erasure_model.html')
    else:
        global needed
        needed = True
        return redirect(url_for('login'))

if __name__ == '__main__':
    sio.run(app)