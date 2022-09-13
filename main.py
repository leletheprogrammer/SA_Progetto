from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import pandas as pd
from random import randint
import smtplib
import ssl
from threading import Lock

from flask import Flask, render_template, request, redirect, url_for, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from flask_pymongo import PyMongo
from flask_socketio import SocketIO

import crud_tables_management as ct
import download_erasure as de
import plot_results as pr
import testing as te
import training as tr

'''app represents the web application and
__name__ represents the name of the current file'''
app = Flask(__name__)
sio = SocketIO(app)

mongo = PyMongo(app, 'mongodb://localhost:27017/NLPDatabase', connect = True)

login_user = None
needed = None

thread_training_intent = {}
thread_training_sentiment = {}
thread_training_entities = {}
thread_lock = Lock()
max_epoch_intent = {}
max_epoch_sentiment = {}
max_iterations_entities = {}

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
        email_valid = True
        name_valid = True
        found = False
        email = None
        if request.method == 'POST':
            form_data = request.form
            
            email = form_data['email']
            name = form_data['name']
            password = form_data['password']
            
            email_user = mongo.db.users.find_one({'email': email})
            if email_user != None:
                email_valid = not email_valid
            name_user = mongo.db.users.find_one({'name': name})
            if name_user != None:
                name_valid = not name_valid
            if (email_user != None) or (name_user != None):
                return render_template('sign_up.html', validation = validation, email_valid = email_valid, name_valid = name_valid, found = found, email = email)
            
            email_to_validate = mongo.db.users_to_validate.find_one({'email': email})
            name_to_validate = mongo.db.users_to_validate.find_one({'name': name})
            if (email_to_validate != None) or (name_to_validate != None):
                found = not found
                return render_template('sign_up.html', validation = validation, email_valid = email_valid, name_valid = name_valid, found = found, email = email)
            
            code = generate_password_hash(str(randint(0, 10000)), method = 'sha256')
            
            mongo.db.users_to_validate.insert_one({'email': email, 'name': name,
                                                   'password': generate_password_hash(password, method = 'sha256'), 'code': code})
            
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
            return render_template('sign_up.html', validation = validation, email_valid = email_valid, name_valid = name_valid, found = found, email = email)
        elif request.method == 'GET':
            return render_template('sign_up.html', validation = validation, email_valid = email_valid, name_valid = name_valid, found = found, email = email)

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
        ct.initialization_database(mongo)
        name = login_user['name']
        partial_name = name + 'dataset'
        global max_epoch_intent
        global max_epoch_sentiment
        global max_iterations_entities
        global thread_training_intent
        global thread_training_sentiment
        global thread_training_entities
        for element in mongo.db.list_collection_names():
            if partial_name in element:
                if element not in max_epoch_intent.keys():
                    max_epoch_intent[element] = 0
                if element not in max_epoch_sentiment.keys():
                    max_epoch_sentiment[element] = 0
                if element not in max_iterations_entities.keys():
                    max_iterations_entities[element] = 0
                if element not in thread_training_intent.keys():
                    thread_training_intent[element] = None
                if element not in thread_training_sentiment.keys():
                    thread_training_sentiment[element] = None
                if element not in thread_training_entities.keys():
                    thread_training_entities[element] = None
        return render_template('home.html', name = name)
    else:
        global needed
        needed = True
        return redirect(url_for('login'))

'''decorator that defines the url path
where will be the intents'''
@app.route('/home/intents', methods = ['POST', 'GET'])
#standard name for functions that works on the home page
def intents():
    global login_user
    if login_user:
        page = int(request.args.get('page'))
        numberIntents = mongo.db.intents.estimated_document_count()
        if (numberIntents > 0 and (page < 1 or (page > 1 and ((int(numberIntents / 20) + 1) < page) or
                                                (numberIntents % 20 == 0 and  numberIntents / 20 < page)))):
            return redirect(url_for('intents', page = 1))
        
        if request.method == 'POST':
            form_data = request.form
            ct.post_intents_table(mongo, form_data)

            #offers a html template on the page
            return redirect(url_for('intents', page = page))
        elif request.method == 'GET':
            typologies = ct.get_intents_table(mongo)
            
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
        if (numberEntities > 0 and (page < 1 or (page > 1 and ((int(numberEntities / 20) + 1) < page) or
                                                 (numberEntities % 20 == 0 and  numberEntities / 20 < page)))):
            return redirect(url_for('entities', page = 1))
        
        if request.method == 'POST':
            form_data = request.form
            ct.post_entities_table(mongo, form_data)
            
            #offers a html template on the page
            return redirect(url_for('entities', page = page))
        elif request.method == 'GET':
            namedEntities = ct.get_entities_table(mongo)
            
            #offers a html template on the page
            return render_template('entities.html', page = page, namedEntities = namedEntities)
    else:
        global needed
        needed = True
        return redirect(url_for('login'))

'''decorator that defines the url path
where will be the buttons of the dataset'''
@app.route('/home/datasets', methods = ['POST', 'GET'])
def datasets():
    global login_user
    if login_user:
        collection_list = mongo.db.list_collection_names()
        name = login_user['name']
        if request.method == 'POST':
            form_data = request.form
            if form_data['submitButton'] == 'createDataset':
                i = 1
                while True:
                    dataset_name = name + 'dataset' + str(i)
                    if dataset_name in collection_list:
                        i = i + 1
                    else:
                        break
            elif 'accessDataset' in form_data['submitButton']:
                i = int(form_data['submitButton'][13 : ])
            elif 'Cancella Dataset' in form_data['submitButton']:
                index = int(form_data['submitButton'][17 : ])
                mongo.db[name + 'dataset' + str(index)].drop()
                dataset_list = []
                partial_name = name + 'dataset'
                for element in mongo.db.list_collection_names():
                    if partial_name in element:
                        dataset_list.append(element)
                partial_len = len(partial_name)
                i = 0
                while i < len(dataset_list) - 1:
                    j = i + 1
                    while j < len(dataset_list):
                        if int(dataset_list[i][partial_len : ]) > int(dataset_list[j][partial_len : ]):
                            dataset_list[i], dataset_list[j] = dataset_list[j], dataset_list[i]
                        j = j + 1
                    i = i + 1
                i = 0
                while i < len(dataset_list):
                    if int(dataset_list[i][partial_len : ]) > index:
                        mongo.db[name + 'dataset' + dataset_list[i][partial_len : ]].rename(name + 'dataset' + str(int(dataset_list[i][partial_len : ]) - 1))
                    i = i + 1
                return render_template('datasets.html', dataset_list = dataset_list)
            return redirect(url_for('training_phrases', dataset = i, page = 1))
        elif request.method == 'GET':
            dataset_list = []
            partial_name = name + 'dataset'
            for element in collection_list:
                if partial_name in element:
                    dataset_list.append(element)
            partial_len = len(partial_name)
            i = 0
            while i < len(dataset_list) - 1:
                j = i + 1
                while j < len(dataset_list):
                    if int(dataset_list[i][partial_len : ]) > int(dataset_list[j][partial_len : ]):
                        dataset_list[i], dataset_list[j] = dataset_list[j], dataset_list[i]
                    j = j + 1
                i = i + 1
            return render_template('datasets.html', dataset_list = dataset_list)
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
        dataset = int(request.args.get('dataset'))
        name = login_user['name']
        partial_name = name + 'dataset'
        table = mongo.db[partial_name + str(dataset)]
        global max_epoch_intent
        global max_epoch_sentiment
        global max_iterations_entities
        global thread_training_intent
        global thread_training_sentiment
        global thread_training_entities
        for element in mongo.db.list_collection_names():
            if partial_name in element:
                if element not in max_epoch_intent.keys():
                    max_epoch_intent[element] = 0
                if element not in max_epoch_sentiment.keys():
                    max_epoch_sentiment[element] = 0
                if element not in max_iterations_entities.keys():
                    max_iterations_entities[element] = 0
                if element not in thread_training_intent.keys():
                    thread_training_intent[element] = None
                if element not in thread_training_sentiment.keys():
                    thread_training_sentiment[element] = None
                if element not in thread_training_entities.keys():
                    thread_training_entities[element] = None
        numberPhrases = table.estimated_document_count()
        if (numberPhrases > 0 and (page < 1 or (page > 1 and ((int(numberPhrases / 20) + 1) < page) or
                                                (numberPhrases % 20 == 0 and  numberPhrases / 20 < page)))):
            return redirect(url_for('training_phrases', dataset = dataset, page = 1))

        if request.method == 'POST':
            ct.post_training_phrases_table(mongo, table, request)
            
            #offers a html template on the page
            return redirect(url_for('training_phrases', dataset = dataset, page = page))
        elif request.method == 'GET':
            phrases, intents, namedEntities, sentiments, emotions = ct.get_training_phrases_table(mongo, table)
            
            #offers a html template on the page
            return render_template('training_phrases.html', dataset = dataset, page = page, phrases = phrases, intents = intents,
                                   namedEntities = namedEntities, sentiments = sentiments, emotions = emotions)
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
        num_datasets = 0
        name = login_user['name']
        collection_list = mongo.db.list_collection_names()
        partial_name = name + 'dataset'
        for element in collection_list:
            if partial_name in element:
                num_datasets = num_datasets + 1
        if request.method == 'POST':
            form_data = request.form
            if ('intentRecognition' in form_data['submitButton'] or 'sentimentAnalysis' in form_data['submitButton']):
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
                if ('intentRecognition' in form_data['submitButton']):
                    model_success = 'Intent Recognition del dataset ' + form_data['submitButton'][17 :]
                    data = login_user['name'] + 'dataset' + form_data['submitButton'][17 :]
                    tr.initialization(mongo, login_user['name'])
                    if tr.get_ended_intent(data):
                        global max_epoch_intent
                        max_epoch_intent[data] = 2
                        if 'insertMaxEpoch' in form_data:
                            try:
                                max_epoch_intent[data] = int(form_data['insertMaxEpoch'])
                            except ValueError:
                                max_epoch_intent[data] = 2
                        global thread_training_intent
                        with thread_lock:
                            thread_training_intent[data] = sio.start_background_task(tr.start_training_intent, mongo, data, login_user['name'], learning_rate, eps, batch_size,
                                                                               max_epoch_intent[data], patience, hidden_dropout_prob)
                    else:
                        return render_template('start_training_model.html', model_training = 'Intent Recognition del dataset ' + form_data['submitButton'][17 :], num_datasets = num_datasets)
                elif ('sentimentAnalysis' in form_data['submitButton']):
                    model_success = 'Sentiment Analysis del dataset ' + form_data['submitButton'][17 :]
                    data = login_user['name'] + 'dataset' + form_data['submitButton'][17 :]
                    tr.initialization(mongo, login_user['name'])
                    if tr.get_ended_sentiment(data):
                        global max_epoch_sentiment
                        max_epoch_sentiment[data] = 2
                        if 'insertMaxEpoch' in form_data:
                            try:
                                max_epoch_sentiment[data] = int(form_data['insertMaxEpoch'])
                            except ValueError:
                                max_epoch_sentiment[data] = 2
                        global thread_training_sentiment
                        with thread_lock:
                            thread_training_sentiment[data] = sio.start_background_task(tr.start_training_sentiment, mongo, data, login_user['name'], learning_rate, eps, batch_size,
                                                                                  max_epoch_sentiment[data], patience, hidden_dropout_prob)
                    else:
                        return render_template('start_training_model.html', model_training = 'Sentiment Analysis del dataset ' + form_data['submitButton'][17 :], num_datasets = num_datasets)
            elif ('entitiesExtraction' in form_data['submitButton']):
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
                model_success = 'Entities Extraction del dataset ' + form_data['submitButton'][18 :]
                data = login_user['name'] + 'dataset' + form_data['submitButton'][18 :]
                tr.initialization(mongo, login_user['name'])
                if tr.get_ended_entities(data):
                    global max_iterations_entities
                    max_iterations_entities[data] = 30
                    if 'insertNumIterations' in form_data:
                        try:
                            max_iterations_entities[data] = int(form_data['insertNumIterations'])
                        except ValueError:
                            max_iterations_entities[data] = 30
                    global thread_training_entities
                    with thread_lock:
                        thread_training_entities[data] = sio.start_background_task(tr.start_training_entities, mongo, data, login_user['name'], app.root_path, dropout_from, dropout_to,
                                                                             batch_from, batch_to, max_iterations_entities[data])
                else:
                    return render_template('start_training_model.html', model_training = 'Entities Extraction del dataset ' + form_data['submitButton'][18 :], num_datasets = num_datasets)
            return render_template('start_training_model.html', model_success = model_success, num_datasets = num_datasets)
        elif request.method == 'GET':
            return render_template('start_training_model.html', num_datasets = num_datasets)
    else:
        global needed
        needed = True
        return redirect(url_for('login'))

'''decorator that defines the url path
of the page where there is the page status'''
@app.route('/home/status', methods = ['POST', 'GET'])
def status():
    global login_user
    if login_user:
        collection_list = mongo.db.list_collection_names()
        name = login_user['name']
        if request.method == 'POST':
            form_data = request.form
            if 'statusIntent' in form_data['submitButton']:
                dataset = form_data['submitButton'][12 : ]
                return redirect(url_for('status_model_intent', dataset = dataset))
            elif 'statusEntities' in form_data['submitButton']:
                dataset = form_data['submitButton'][14 : ]
                return redirect(url_for('status_model_entities', dataset = dataset))
            elif 'statusSentiment' in form_data['submitButton']:
                dataset = form_data['submitButton'][15 : ]
                return redirect(url_for('status_model_sentiment', dataset = dataset))
        elif request.method == 'GET':
            dataset_list = []
            partial_name = name + 'dataset'
            for element in collection_list:
                if partial_name in element:
                    dataset_list.append(element)
            partial_len = len(partial_name)
            i = 0
            while i < len(dataset_list) - 1:
                j = i + 1
                while j < len(dataset_list):
                    if int(dataset_list[i][partial_len : ]) > int(dataset_list[j][partial_len : ]):
                        dataset_list[i], dataset_list[j] = dataset_list[j], dataset_list[i]
                    j = j + 1
                i = i + 1
            return render_template('status.html', dataset_list = dataset_list)
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
        data = login_user['name'] + 'dataset' + request.args['dataset']
        if thread_training_intent[data] is None:
            return render_template("status_model_intent.html", not_training = True)
        else:
            if(tr.get_num_epoch_intent(data) == -1):
                return render_template("status_model_intent.html", loading = True)
            else:
                global max_epoch_intent
                return render_template("status_model_intent.html", num_epoch = tr.get_num_epoch_intent(data), num_iteration = tr.get_num_iteration_intent(data),
                                       length_epoch = tr.get_epoch_length_intent(data), num_progress = tr.get_num_progress_intent(data),
                                       max_epoch = max_epoch_intent[data])
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
        data = login_user['name'] + 'dataset' + request.args['dataset']
        if thread_training_entities[data] is None:
            return render_template("status_model_entities.html", not_training = True)
        else:
            if(tr.get_num_iteration_entities(data) == -1):
                return render_template("status_model_entities.html", loading = True)
            else:
                global max_iterations_entities
                return render_template("status_model_entities.html", iteration = tr.get_num_iteration_entities(data), max_iteration = max_iterations_entities[data],
                                       num_progress = tr.get_num_progress_entities(data))
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
        data = login_user['name'] + 'dataset' + request.args['dataset']
        if thread_training_sentiment[data] is None:
            return render_template("status_model_sentiment.html", not_training = True)
        else:
            if(tr.get_num_epoch_sentiment(data) == -1):
                return render_template("status_model_sentiment.html", loading = True)
            else:
                global max_epoch_sentiment
                return render_template("status_model_sentiment.html", num_epoch = tr.get_num_epoch_sentiment(data),
                                       num_iteration = tr.get_num_iteration_sentiment(data), length_epoch = tr.get_epoch_length_sentiment(data),
                                       num_progress = tr.get_num_progress_sentiment(data), max_epoch = max_epoch_sentiment[data])
    else:
        global needed
        needed = True
        return redirect(url_for('login'))

'''decorator that defines the url path of the
page where to choose the dataset to test and
to show results of the models'''
@app.route('/home/dataset_results_testing', methods = ['POST', 'GET'])
def dataset_results_testing():
    global login_user
    if login_user:
        collection_list = mongo.db.list_collection_names()
        name = login_user['name']
        if request.method == 'POST':
            form_data = request.form
            if 'resultsDataset' in form_data['submitButton']:
                dataset = form_data['submitButton'][14 : ]
                return redirect(url_for('show_results_testing', dataset = dataset))
        elif request.method == 'GET':
            dataset_list = []
            partial_name = name + 'dataset'
            for element in collection_list:
                if partial_name in element:
                    dataset_list.append(element)
            partial_len = len(partial_name)
            i = 0
            while i < len(dataset_list) - 1:
                j = i + 1
                while j < len(dataset_list):
                    if int(dataset_list[i][partial_len : ]) > int(dataset_list[j][partial_len : ]):
                        dataset_list[i], dataset_list[j] = dataset_list[j], dataset_list[i]
                    j = j + 1
                i = i + 1
            return render_template('dataset_results_testing.html', dataset_list = dataset_list)
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
            name = login_user['name']
            dataset = request.args['dataset']
            if('submitButton' in form_data):
                if(form_data['submitButton'] == 'visualizeIntent'):
                    if(os.path.isfile('results_intent_' + name + '_' + dataset + '.csv')):
                        return render_template('show_results_testing.html', results_intent = pd.read_csv('results_intent_' + name + '_' + dataset + '.csv').values.tolist())
                    else:
                        return render_template('show_results_testing.html', not_present = 'Intent Recognition del dataset ' + dataset)
                elif(form_data['submitButton'] == 'visualizeEntities'):
                    if(os.path.isfile('results_entities_' + name + '_' + dataset + '.csv')):
                        return render_template('show_results_testing.html', results_entities = pd.read_csv('results_entities_' + name + '_' + dataset + '.csv').values.tolist())
                    else:
                        return render_template('show_results_testing.html', not_present = 'Entities Extraction del dataset ' + dataset)
                elif(form_data['submitButton'] == 'visualizeSentiment'):
                    if(os.path.isfile('results_sentiment_' + name + '_' + dataset + '.csv')):
                        return render_template('show_results_testing.html', results_sentiment = pd.read_csv('results_sentiment_' + name + '_' + dataset + '.csv').values.tolist())
                    else:
                        return render_template('show_results_testing.html', not_present = 'Sentiment Analysis del dataset ' + dataset)
                elif(form_data['submitButton'] == 'buttonTestingIntent'):
                    if(os.path.isfile('mapping_intent_' + name + '_' + dataset + '.joblib') and os.path.isfile('test_intent_' + name + '_' + dataset + '.csv')):
                        score = te.testing_intent(name, dataset)
                        return render_template('show_results_testing.html', testing_intent = str(score))
                    else:
                        return render_template('show_results_testing.html', not_present = 'Intent Recognition del dataset ' + dataset)
                elif(form_data['submitButton'] == 'buttonTestingEntities'):
                    if(os.path.isfile('test_entities_' + name + '_' + dataset + '.json')):
                        score = te.testing_entities(name, dataset)
                        return render_template('show_results_testing.html', testing_entities = str(score))
                    else:
                        return render_template('show_results_testing.html', not_present = 'Entities Extraction del dataset ' + dataset)
                elif(form_data['submitButton'] == 'buttonTestingSentiment'):
                    if(os.path.isfile('mapping_sentiment_' + name + '_' + dataset + '.joblib') and os.path.isfile('test_sentiment_' + name + '_' + dataset + '.csv')):
                        score = te.testing_sentiment(name, dataset)
                        return render_template('show_results_testing.html', testing_sentiment = str(score))
                    else:
                        return render_template('show_results_testing.html', not_present = 'Sentiment Analysis del dataset ' + dataset)
            if('graphicLoss' in form_data):
                pr.graphic_loss_creation(form_data, name, dataset)
                if(form_data['graphicLoss'] == 'graphicLossIntent'):
                    return render_template('show_results_testing.html', loss_intent = 'loss_intent_' + name + '_' + dataset + '.png')
                elif(form_data['graphicLoss'] == 'graphicLossSentiment'):
                    return render_template('show_results_testing.html', loss_sentiment = 'loss_sentiment_' + name + '_' + dataset + '.png')
                elif(form_data['graphicLoss'] == 'graphicLossEntities'):
                    return render_template('show_results_testing.html', loss_entities = 'loss_entities_' + name + '_' + dataset + '.png')
            if('graphicScore' in form_data):
                pr.graphic_score_creation(form_data, name, dataset)
                if(form_data['graphicScore'] == 'graphicScoreIntent'):
                    return render_template('show_results_testing.html', score_intent = 'score_intent_' + name + '_' + dataset + '.png')
                elif(form_data['graphicScore'] == 'graphicScoreSentiment'):
                    return render_template('show_results_testing.html', score_sentiment = 'score_sentiment_' + name + '_' + dataset + '.png')
                elif(form_data['graphicScore'] == 'graphicScoreEntities'):
                    return render_template('show_results_testing.html', score_entities = 'score_entities_' + name + '_' + dataset + '.png')
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
        num_datasets = 0
        name = login_user['name']
        collection_list = mongo.db.list_collection_names()
        partial_name = name + 'dataset'
        for element in collection_list:
            if partial_name in element:
                num_datasets = num_datasets + 1
        if request.method == 'POST':
            form_data = request.form
            if('downloadIntentRecognition' in form_data['submitButton']):
                if(not os.path.isdir(os.path.join('models', 'intent_' + name + '_' + form_data['submitButton'][25 : ]))):
                    return render_template('download_erasure_model.html', num_datasets = num_datasets, model_download = 'Intent Recognition del dataset ' + form_data['submitButton'][25 : ])
                else:
                    memory_file = de.download_intent(name, form_data['submitButton'][25 : ])
                    return send_file(memory_file, attachment_filename = 'intent_recognition_' + form_data['submitButton'][25 : ] + '.zip', as_attachment = True)
            elif('downloadEntitiesExtraction' in form_data['submitButton']):
                if(not os.path.isdir(os.path.join('models', 'entities_' + name + '_' + form_data['submitButton'][26 : ]))):
                    return render_template('download_erasure_model.html', num_datasets = num_datasets, model_download = 'Entities Extraction del dataset ' + form_data['submitButton'][26 : ])
                else:
                    memory_file = de.download_entities(name, form_data['submitButton'][26 : ])
                    return send_file(memory_file, attachment_filename = 'entities_extraction_' + form_data['submitButton'][26 : ] + '.zip', as_attachment = True)
            elif('downloadSentimentAnalysis' in form_data['submitButton']):
                if(not os.path.isdir(os.path.join('models', 'sentiment_' + name + '_' + form_data['submitButton'][25 : ]))):
                    return render_template('download_erasure_model.html', num_datasets = num_datasets, model_download = 'Sentiment Analysis del dataset ' + form_data['submitButton'][25: ])
                else:
                    memory_file = de.download_sentiment(name, form_data['submitButton'][25 : ])
                    return send_file(memory_file, attachment_filename = 'sentiment_analysis_' + form_data['submitButton'][25 : ] + '.zip', as_attachment = True)
            elif('deleteIntentRecognition' in form_data['submitButton']):
                if(not os.path.isdir(os.path.join('models', 'intent_' + name + '_' + form_data['submitButton'][23 : ]))):
                    return render_template('download_erasure_model.html', num_datasets = num_datasets, model_erasure = 'Intent Recognition del dataset ' + form_data['submitButton'][23 : ])
                else:
                    de.delete_intent(name, form_data['submitButton'][23 : ])
            elif('deleteEntitiesExtraction' in form_data['submitButton']):
                if(not os.path.isdir(os.path.join('models', 'entities_' + name + '_' + form_data['submitButton'][24 : ]))):
                    return render_template('download_erasure_model.html', num_datasets = num_datasets, model_erasure = 'Entities Extraction del dataset ' + form_data['submitButton'][24 : ])
                else:
                    de.delete_entities(name, form_data['submitButton'][24 : ])
            elif('deleteSentimentAnalysis' in form_data['submitButton']):
                if(not os.path.isdir(os.path.join('models', 'sentiment_' + name + '_' + form_data['submitButton'][23 : ]))):
                    return render_template('download_erasure_model.html', num_datasets = num_datasets, model_erasure = 'Sentiment Analysis del dataset ' + form_data['submitButton'][23 : ])
                else:
                    de.delete_sentiment(name, form_data['submitButton'][23 : ])
            return render_template('download_erasure_model.html', num_datasets = num_datasets)
        elif request.method == 'GET':
            return render_template('download_erasure_model.html', num_datasets = num_datasets)
    else:
        global needed
        needed = True
        return redirect(url_for('login'))

if __name__ == '__main__':
    sio.run(app)