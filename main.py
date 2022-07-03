'''import class Flask, methods render_template and request 
from module flask'''
from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo

import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from werkzeug.security import generate_password_hash, check_password_hash
#import spacy
#from spacy.util import minibatch, compounding
from random import randint

'''app represents the web application and
__name__ represents the name of the current file'''
app = Flask(__name__)

mongo = PyMongo(app, 'mongodb://localhost:27017/NLPDatabase', connect = True)

login_user = None
needed = None

#colors
color = {
        'blue': '002aff',
        'yellow': 'e1eb34',
        'green': '28fc03',
        'red': 'fc1703', 
        'purple': 'b503fc', 
        'orange': 'FF9733 ',
        'black' : 'FFFFFF',
        'light-blue': '0AE5E3', 
        'pink': 'FF95AE',
        'blue-green' : '95FFCA'
}

'''decorator that defines the url path
where will be the index page of the site'''
@app.route('/')
#standard name for functions that works on the index page
def index():
    #offers a html template on the page
    global login_user
    if login_user:
        return redirect(url_for('home'))
    else:
        return render_template('index.html')

@app.route('/services_area/')
def services_area():
    global login_user
    if login_user:
        return redirect(url_for('home'))
    else:
        return render_template('services_area.html')

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

@app.route('/services_area/sign_up/validation', methods = ['GET'])
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

@app.route('/home/')
def home():
    global login_user
    if login_user:
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
    page = int(request.args.get('page'))
    numberIntents = mongo.db.intents.estimated_document_count()
    if (page < 1 or (page > 1 and ((int(numberIntents / 20) + 1) < page) or (numberIntents % 20 == 0 and  numberIntents / 20 < page))):
        return redirect(url_for('intents', page = 1))
    if request.method == 'POST':
        form_data = request.form

        if form_data['submitButton'] == 'Elimina':
            oldIntent = form_data['oldIntent']
            mongo.db.intents.delete_one({'typology': oldIntent})
        elif form_data['submitButton'] == 'Modifica':
            oldIntent = form_data['oldIntent']
            newIntent = form_data['newIntent']
            
            found = False
            #iteration among the documents in the collection 'intents'
            for intent in mongo.db.intents.find():
                if intent['typology'] == newIntent:
                    found = not found
                    break
            
            if not found:
                mongo.db.intents.replace_one({'typology': oldIntent}, {'typology': newIntent})
        elif form_data['submitButton'] == 'Aggiungi':
            newIntent = form_data['newIntent']
            
            args = request.args
            updateIntent = args.get('updateIntent')
            deleteIntent = args.get('deleteIntent')
            
            if not found:
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

'''decorator that defines the url path
of the page where to create intent
@app.route('/create_intent', methods = ['POST', 'GET'])
def create_intent():
    if request.method == 'POST':
        connection = sqlite3.connect('NLPDatabase.db')
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        
        #form is a MultiDict with the parsed form data from 'PUT' or 'POST'
        form_data = request.form
        value = form_data['createIntent']
        if (value.isspace() == False) and (value != ''):
            #removes duplicated spaces
            value = ' '.join(value.split())
            
            selection = cursor.execute('SELECT Typology FROM Intents WHERE Typology = "' + value + '"').fetchall()
            if (not len(selection)):
                cursor.execute('INSERT INTO Intents VALUES("' + value + '")')
                
                #saves the changes made to the database
                connection.commit()
        connection.close()
        
        return render_template('create_intent.html', form_data = form_data)
    elif request.method == 'GET':
        return render_template('create_intent.html')'''

'''decorator that defines the url path
where will be the entities'''
@app.route('/home/entities', methods = ['POST', 'GET'])
#standard name for functions that works on the home page
def entities():
    page = int(request.args.get('page'))
    numberEntities = mongo.db.entities.estimated_document_count()
    if (page < 1 or (page > 1 and ((int(numberEntities / 20) + 1) < page) or (numberEntities % 20 == 0 and  numberEntities / 20 < page))):
        return redirect(url_for('entities', page = 1))
    if request.method == 'POST':
        form_data = request.form

        if form_data['submitButton'] == 'Elimina':
            oldEntity = form_data['oldEntity']
            mongo.db.entities.delete_one({'namedEntity': oldEntity})
        elif form_data['submitButton'] == 'Modifica':
            oldEntity = form_data['oldEntity']
            newEntity = form_data['newEntity']
            
            found = False
            #iteration among the documents in the collection 'intents'
            for entity in mongo.db.entities.find():
                if entity['namedEntity'] == newEntity:
                    found = not found
                    break
            
            if not found:
                mongo.db.entities.replace_one({'namedEntity': oldEntity}, {'namedEntity': newEntity})
        elif form_data['submitButton'] == 'Aggiungi':
            newEntity = form_data['newEntity']
            
            found = False
            #iteration among the documents in the collection 'intents'
            for entity in mongo.db.entities.find():
                if entity['namedEntity'] == newEntity:
                    found = not found
                    break
            
            if not found:
                mongo.db.entities.insert_one({'namedEntity': newEntity})

        #offers a html template on the page
        return redirect(url_for('entities', page = page))
    elif request.method == 'GET':
        namedEntities = []
        #iteration among the documents in the collection 'intents'
        for entity in mongo.db.entities.find():
            #intent is a dict, so typologies is a list of dict
            namedEntities.append(entity)

        #offers a html template on the page
        return render_template('entities.html', page = page, namedEntities = namedEntities)

'''decorator that defines the url path
of the page where to define new entities
@app.route('/define_entity', methods = ['POST', 'GET'])
def define_entity():
    if request.method == 'POST':
        connection = sqlite3.connect('NLPDatabase.db')
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        
        #form is a MultiDict with the parsed form data from 'PUT' or 'POST'
        form_data = request.form
        value = form_data['insertEntity']
        if (value.isspace() == False) and (value != ''):
            #removes duplicated spaces
            value = ' '.join(value.split())
            
            selection = cursor.execute('SELECT Entity FROM NamedEntities WHERE Entity = "' + value + '"').fetchall()
            if (not len(selection)):
                cursor.execute('INSERT INTO NamedEntities VALUES("' + value + '")')
                
                #saves the changes made to the database
                connection.commit()
        connection.close()
        
        return render_template('define_entity.html', form_data = form_data)
    elif request.method == 'GET':
        return render_template('define_entity.html')'''

'''decorator that defines the url path
where will be the intents'''
@app.route('/home/training_phrases')
#standard name for functions that works on the home page
def training_phrases():
    #offers a html template on the page
    return render_template('training_phrases.html')

'''decorator that defines the url path of the page
where to add,modify and delete training phrase
@app.route('/modify_training_phrase', methods = ['POST', 'GET'])
def modify_training_phrase():
    connection = sqlite3.connect('NLPDatabase.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    
    if request.method == 'POST':
        #form is a MultiDict with the parsed form data from 'PUT' or 'POST'
        form_data = request.form
        if (form_data['submitButton'] == 'addButton'):
            value = form_data['addTrainingPhrase']
            if (value.isspace() == False) and (value != ''):
                #removes duplicated spaces
                value = ' '.join(value.split())
                
                selection = cursor.execute('SELECT Phrase FROM TrainingPhrases WHERE Phrase = "' + value + '"').fetchall()
                if (not len(selection)):
                    cursor.execute('INSERT INTO TrainingPhrases VALUES("' + value + '")')
                    
                    #saves the changes made to the database
                    connection.commit()
        elif (form_data['submitButton'] == 'modifyButton'):
            old_value = form_data['selectTrainingPhrase']
            if old_value == '':
                phrases = cursor.execute('SELECT Phrase FROM TrainingPhrases').fetchall()
                
                connection.close()
                
                return render_template('modify_training_phrase.html', phrases = phrases, error1 = 'Errore: non è stata selezionata nessuna frase di training', color1 = 'red', color2 = 'black')
            
            new_value = form_data['newTrainingPhrase']
            if (new_value.isspace() == False) and (new_value != ''):
                #removes duplicated spaces
                new_value = ' '.join(new_value.split())
                if old_value == new_value:
                    phrases = cursor.execute('SELECT Phrase FROM TrainingPhrases').fetchall()
                    
                    connection.close()
                    
                    return render_template('modify_training_phrase.html', phrases = phrases, error1 = 'Errore: la frase da sostituire è uguale a quella inserita', color1 = 'red', color2 = 'black')
                
                selection = cursor.execute('SELECT Phrase FROM TrainingPhrases WHERE Phrase = "' + new_value + '"').fetchall()
                if (not len(selection)):
                    cursor.execute('UPDATE TrainingPhrases SET Phrase = "' + new_value + '" WHERE Phrase = "' + old_value + '"')
                    
                    #saves the changes made to the database
                    connection.commit()
            else:
                phrases = cursor.execute('SELECT Phrase FROM TrainingPhrases').fetchall()
                
                connection.close()
                
                return render_template('modify_training_phrase.html', phrases = phrases, error1 = 'Errore: sono stati inseriti valori inadatti per la nuova frase di training', color1 = 'red', color2 = 'black')
        elif (form_data['submitButton'] == 'deleteButton'):
            value = form_data['deleteTrainingPhrase']
            if value == '':
                phrases = cursor.execute('SELECT Phrase FROM TrainingPhrases').fetchall()
                
                connection.close()
                
                return render_template('modify_training_phrase.html', phrases = phrases, error2 = 'Errore: non è stata selezionata nessuna frase di training', color1 = 'black', color2 = 'red')
            
            cursor.execute('DELETE FROM TrainingPhrases WHERE Phrase = "' + value + '"')
            
            #saves the changes made to the database
            connection.commit()
        else:
            pass
        
        phrases = cursor.execute('SELECT Phrase FROM TrainingPhrases').fetchall()
        
        connection.close()
        
        return render_template('modify_training_phrase.html', phrases = phrases, color1 = 'black', color2 = 'black')
    elif request.method == 'GET':
        phrases = cursor.execute('SELECT Phrase FROM TrainingPhrases').fetchall()
        
        return render_template('modify_training_phrase.html', phrases = phrases, color1 = 'black', color2 = 'black')

decorator that defines the url path of the
page where to write down training phrases
@app.route('/write_down_training', methods = ['POST', 'GET'])
def write_down_training():
	connection = sqlite3.connect('NLPDatabase.db')
	connection.row_factory = sqlite3.Row
	cursor = connection.cursor()
	phrases = cursor.execute('SELECT Phrase FROM TrainingPhrases').fetchall()
	entities = cursor.execute('SELECT Entity FROM NamedEntities').fetchall()
	values = list()
	if request.method == 'POST':
		form_data = request.form
		if ('phraseSelected' in form_data):
				value = form_data['phraseSelected'].split()
				for string in value:
					if (not (string == ' ')):
						values.append(string)
		if ('submitButton' in form_data):
			if (form_data['submitButton'] == 'selectButton'):
				values.clear()
				
				value = form_data['selectTrainingPhrase'].split()
				for string in value:
					if (not (string == ' ')):
						values.append(string)
			elif (form_data['submitButton'] == 'entityButton'):
				value = form_data['phraseSelected'].split()
				for string in value:
					if (not (string == ' ')):
						values.append(string)
				

		connection.close()
		return render_template('write_down_training.html', phrases = phrases, values = values, entities = entities)
	elif request.method == 'GET':
		return render_template('write_down_training.html', phrases = phrases)'''

'''decorator that defines the url path
of the page where to train the models'''
@app.route('/home/start_training_model', methods = ['POST', 'GET'])
def start_training_model():
	if request.method == 'POST':
		form_data = request.form
		if (form_data['submitButton'] == 'intentRecognition'):
			pass
		elif (form_data['submitButton'] == 'entitiesExtraction'):
			trainingEntitiesExtraction()
		elif (form_data['submitButton'] == 'sentimentAnalysis'):
			pass
		return render_template('start_training_model.html')
	elif request.method == 'GET':
		return render_template('start_training_model.html')

def trainingEntitiesExtraction():
    '''
    tup = {}
    print(tup)

    connection = sqlite3.connect('NLPDatabase.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    model = None

    #create blank Language class
    nlp = spacy.blank('it')
    
    print("Created blank 'it' model")

    if 'ner' not in nlp.pipe_names:
        ner = nlp.create_pipe('ner')
        nlp.add_pipe('ner')
    else:
        ner = nlp.get_pipe('ner')
    
    entities = cursor.execute('SELECT Entity FROM NamedEntities').fetchall()

    # Add new entity labels to entity recognizer
    for i in entities:
        for j in i:
            ner.add_label(j)

    training_data = []
    training_phrases = cursor.execute('SELECT Phrase,Entities FROM TrainingPhrases').fetchall()

    for phrases in training_phrases:
        dict_entities = {}
        entities_phrase = []
        i = 0
        j = 0
        while phrases[1][i] != ']':
            if (phrases[1][i] == '('):
            	j = i
            elif (phrases[1][i] == ')'):
                entity_tuple = tupleEntity(phrases[1][j:i + 1])
                entities_phrase.append(entity_tuple)
            i += 1
        dict_entities.setDefault("entities", entities_phrase)
        phrase_tuple = (phrases[0], dict_entities)
        training_data.append(phrase_tuple)


    # Inititalizing optimizer
    if model is None:
        optimizer = nlp.begin_training()
    else:
        optimizer = nlp.entity.create_optimizer()

    # Get names of other pipes to disable them during training to train # only NER and update the weights
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != 'ner']
    with nlp.disable_pipes(*other_pipes):  # only train NER
        for itn in range(10): #numero di epoche(iperparametro)
            random.shuffle(training_data)
            losses = {}
            batches = minibatch(training_data, size=compounding(4., 32., 1.001))
            for batch in batches:
                texts, annotations = zip(*batch)
                #Updating the weights
                nlp.update(texts, annotations, sgd = optimizer, drop = 0.35, losses = losses)
                nlp.update(texts,annotations,sgd=optimizer,drop=0.35,losses=losses)
                print('Losses', losses)
                nlp.update(texts, annotations, sgd=optimizer, drop=0.35, losses=losses)
                print('Losses', losses)

    # Save model
    if output_dir is not None:
        output_dir = Path(#)
        nlp.to_disk(output_dir)
        print("Saved model to", output_dir)'''

def tupleEntity(entity):
    firstIndex = ''
    lastIndex = ''
    i = 1
    while(entity[i] != ','):
        firstIndex += entity[i]
        i += 1

    i += 2

    while(entity[i] != ','):
        lastIndex += entity[i]
        i += 1

    i += 2

    entityTuple = (int(firstIndex), int(lastIndex), entity[i:len(entity) - 1])
    return entityTuple

'''decorator that defines the url path of the
page where to test and show results of the models'''
@app.route('/home/show_results_testing')
def show_results_testing():
	return 'show_results_testing'

'''decorator that defines the url path of
the page where to download or erase the models'''
@app.route('/home/download_erasure_model')
def download_erasure_model():
	return 'download_erasure_model'

if __name__ == '__main__':
    app.run()
