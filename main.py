'''import class Flask, methods render_template and request 
from module flask'''
from flask import Flask, render_template, request
#import module sqlite3
import sqlite3
import spacy
from spacy.util import minibatch, compounding
import random

'''app represents the web application and
__name__ represents the name of the current file'''
app = Flask(__name__)

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
where will be the home page of the site'''
@app.route('/')
#standard name for functions that works on the home page
def index():
    #offers a html template on the page
    return render_template('index.html')

'''decorator that defines the url path
of the page where to create intent'''
@app.route('/create_intent', methods = ['POST', 'GET'])
def create_intent():
    if request.method == 'POST':
        connection = sqlite3.connect('NLPDatabase.db')
        '''creation of a 'dictionary cursor': after a fetchall or a fetchone
        it starts returning dictionary rows'''
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        
        #form is a MultiDict with the parsed form data from 'PUT' or 'POST'
        form_data = request.form
        '''the value accessible through the key 'createIntent'
        is stored in the variable "value"'''
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
        return render_template('create_intent.html')

'''decorator that defines the url path
of the page where to define new entities'''
@app.route('/define_entity', methods = ['POST', 'GET'])
def define_entity():
    if request.method == 'POST':
        connection = sqlite3.connect('NLPDatabase.db')
        '''creation of a 'dictionary cursor': after a fetchall or a fetchone
        it starts returning dictionary rows'''
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        
        #form is a MultiDict with the parsed form data from 'PUT' or 'POST'
        form_data = request.form
        '''the value accessible through the key 'insertEntity'
        is stored in the variable "value"'''
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
        return render_template('define_entity.html')

'''decorator that defines the url path of the page
where to add,modify and delete training phrase'''
@app.route('/modify_training_phrase', methods = ['POST', 'GET'])
def modify_training_phrase():
    connection = sqlite3.connect('NLPDatabase.db')
    '''creation of a 'dictionary cursor': after a fetchall or a fetchone
    it starts returning dictionary rows'''
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    
    if request.method == 'POST':
        #form is a MultiDict with the parsed form data from 'PUT' or 'POST'
        form_data = request.form
        if (form_data['submitButton'] == 'addButton'):
            '''the value accessible through the key 'addTrainingPhrase'
            is stored in the variable "value"'''
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
            '''the value accessible through the key 'selectTrainingPhrase'
            is stored in the variable "value"'''
            old_value = form_data['selectTrainingPhrase']
            if old_value == '':
                phrases = cursor.execute('SELECT Phrase FROM TrainingPhrases').fetchall()
                
                connection.close()
                
                return render_template('modify_training_phrase.html', phrases = phrases, error1 = 'Errore: non è stata selezionata nessuna frase di training', color1 = 'red', color2 = 'black')
            
            '''the value accessible through the key 'newTrainingPhrase'
            is stored in the variable "value"'''
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
            '''the value accessible through the key 'deleteTrainingPhrase'
            is stored in the variable "value"'''
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

'''decorator that defines the url path of the
page where to write down training phrases'''
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
		return render_template('write_down_training.html', phrases = phrases)

'''decorator that defines the url path
of the page where to train the models'''
@app.route('/start_training_model', methods = ['POST', 'GET'])
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

    '''
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
        print("Saved model to", output_dir)

    '''

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
@app.route('/show_results_testing')
def show_results_testing():
	return 'show_results_testing'

'''decorator that defines the url path of
the page where to download or erase the models'''
@app.route('/download_erasure_model')
def download_erasure_model():
	return 'download_erasure_model'

if __name__ == '__main__':
    app.run()
