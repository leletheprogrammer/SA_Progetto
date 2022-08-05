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
        ct.initialization_database(mongo)
        name = login_user['name']
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
where will be the training phrases'''
@app.route('/home/training_phrases', methods = ['POST', 'GET'])
#standard name for functions that works on the home page
def training_phrases():
    global login_user
    if login_user:
        page = int(request.args.get('page'))
        numberPhrases = mongo.db.training_phrases.estimated_document_count()
        if (numberPhrases > 0 and (page < 1 or (page > 1 and ((int(numberPhrases / 20) + 1) < page) or
                                                (numberPhrases % 20 == 0 and  numberPhrases / 20 < page)))):
            return redirect(url_for('training_phrases', page = 1))

        if request.method == 'POST':
            ct.post_training_phrases_table(mongo, request)
            
            #offers a html template on the page
            return redirect(url_for('training_phrases', page = page))
        elif request.method == 'GET':
            phrases, intents, namedEntities, sentiments, emotions = ct.get_training_phrases_table(mongo)
            
            #offers a html template on the page
            return render_template('training_phrases.html', page = page, phrases = phrases, intents = intents,
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
                    if tr.get_ended_intent():
                        global max_epoch_intent
                        max_epoch_intent = 2
                        if 'insertMaxEpoch' in form_data:
                            try:
                                max_epoch_intent = int(form_data['insertMaxEpoch'])
                            except ValueError:
                                max_epoch_intent = 2
                        global thread_training_intent
                        with thread_lock:
                            thread_training_intent = sio.start_background_task(tr.start_training_intent, mongo, learning_rate, eps, batch_size,
                                                                               max_epoch_intent, patience, hidden_dropout_prob)
                    else:
                        return render_template('start_training_model.html', model_training = 'Intent Recognition')
                elif (form_data['submitButton'] == 'sentimentAnalysis'):
                    if tr.get_ended_sentiment():
                        global max_epoch_sentiment
                        max_epoch_intent = 2
                        if 'insertMaxEpoch' in form_data:
                            try:
                                max_epoch_sentiment = int(form_data['insertMaxEpoch'])
                            except ValueError:
                                max_epoch_sentiment = 2
                        global thread_training_sentiment
                        with thread_lock:
                            thread_training_sentiment = sio.start_background_task(tr.start_training_sentiment, mongo, learning_rate, eps, batch_size,
                                                                                  max_epoch_sentiment, patience, hidden_dropout_prob)
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
                if tr.get_ended_entities():
                    global max_iterations_entities
                    max_iterations_entities = 30
                    if 'insertNumIterations' in form_data:
                        try:
                            max_iterations_entities = int(form_data['insertNumIterations'])
                        except ValueError:
                            max_iterations_entities = 30
                    global thread_training_entities
                    with thread_lock:
                        thread_training_entities = sio.start_background_task(tr.start_training_entities, mongo, app.root_path, dropout_from, dropout_to,
                                                                             batch_from, batch_to, max_iterations_entities)
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
            if(tr.get_num_epoch_intent() == -1):
                return render_template("status_model_intent.html", loading = True)
            else:
                global max_epoch_intent
                return render_template("status_model_intent.html", num_epoch = tr.get_num_epoch_intent(), num_iteration = tr.get_num_iteration_intent(),
                                       length_epoch = tr.get_epoch_length_intent(), num_progress = tr.get_num_progress_intent(),
                                       max_epoch = max_epoch_intent)
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
            if(tr.get_num_iteration_entities() == -1):
                return render_template("status_model_entities.html", loading = True)
            else:
                global max_iterations_entities
                return render_template("status_model_entities.html", iteration = tr.get_num_iteration_entities(), max_iteration = max_iterations_entities,
                                       num_progress = tr.get_num_progress_entities())
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
            if(tr.get_num_epoch_sentiment() == -1):
                return render_template("status_model_sentiment.html", loading = True)
            else:
                global max_epoch_sentiment
                return render_template("status_model_sentiment.html", num_epoch = tr.get_num_epoch_sentiment(),
                                       num_iteration = tr.get_num_iteration_sentiment(), length_epoch = tr.get_epoch_length_sentiment(),
                                       num_progress = tr.get_num_progress_sentiment(), max_epoch = max_epoch_sentiment)
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
                        score = te.testing_intent()
                        return render_template('show_results_testing.html', testing_intent = str(score))
                    else:
                        return render_template('show_results_testing.html', not_present = 'Intent Recognition')
                elif(form_data['submitButton'] == 'buttonTestingEntities'):
                    if(os.path.isfile('test_entities.json')):
                        score = te.testing_entities()
                        return render_template('show_results_testing.html', testing_entities = str(score))
                    else:
                        return render_template('show_results_testing.html', not_present = 'Entities Extraction')
                elif(form_data['submitButton'] == 'buttonTestingSentiment'):
                    if(os.path.isfile('mapping_sentiment.joblib') and os.path.isfile('test_sentiment.csv')):
                        score = te.testing_sentiment()
                        return render_template('show_results_testing.html', testing_sentiment = str(score))
                    else:
                        return render_template('show_results_testing.html', not_present = 'Sentiment Analysis')
            if('graphicLoss' in form_data):
                pr.graphic_loss_creation(form_data)
                if(form_data['graphicLoss'] == 'graphicLossIntent'):
                    return render_template('show_results_testing.html', loss_intent = 'loss_graphic_intent.png')
                elif(form_data['graphicLoss'] == 'graphicLossSentiment'):
                    return render_template('show_results_testing.html', loss_sentiment = 'loss_graphic_sentiment.png')
                elif(form_data['graphicLoss'] == 'graphicLossEntities'):
                    return render_template('show_results_testing.html', loss_entities = 'loss_graphic_entities.png')
            if('graphicScore' in form_data):
                pr.graphic_score_creation(form_data)
                if(form_data['graphicScore'] == 'graphicScoreIntent'):
                    return render_template('show_results_testing.html', score_intent = 'score_graphic_intent.png')
                elif(form_data['graphicScore'] == 'graphicScoreSentiment'):
                    return render_template('show_results_testing.html', score_sentiment = 'score_graphic_sentiment.png')
                elif(form_data['graphicScore'] == 'graphicScoreEntities'):
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
                memory_file = de.download_intent()
                return send_file(memory_file, attachment_filename = 'intent.zip', as_attachment = True)
            elif(form_data['submitButton'] == 'downloadEntitiesExtraction'):
                memory_file = de.download_entities()
                return send_file(memory_file, attachment_filename = 'entities.zip', as_attachment = True)
            elif(form_data['submitButton'] == 'downloadSentimentAnalysis'):
                memory_file = de.download_sentiment()
                return send_file(memory_file, attachment_filename = 'sentiment.zip', as_attachment = True)
            elif(form_data['submitButton'] == 'deleteIntentRecognition'):
                de.delete_intent()
            elif(form_data['submitButton'] == 'deleteEntitiesExtraction'):
                de.delete_entities()
            elif(form_data['submitButton'] == 'deleteSentimentAnalysis'):
                de.delete_sentiment()
            return render_template('download_erasure_model.html')
        elif request.method == 'GET':
            return render_template('download_erasure_model.html')
    else:
        global needed
        needed = True
        return redirect(url_for('login'))

if __name__ == '__main__':
    sio.run(app)