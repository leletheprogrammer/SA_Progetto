'''import class Flask, methods render_template and request 
from module flask'''
from flask import Flask, render_template, request
#import module sqlite3
import sqlite3

'''app represents the web application and
__name__ represents the name of the current file'''
app = Flask(__name__)

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
            
            selection = cursor.execute('SELECT Category FROM NamedEntities WHERE Category = "' + value + '"').fetchall()
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
            '''the value accessible through the key 'newTrainingPhrase'
            is stored in the variable "value"'''
            new_value = form_data['newTrainingPhrase']
            if (new_value.isspace() == False) and (new_value != ''):
                #removes duplicated spaces
                new_value = ' '.join(new_value.split())
                
                selection = cursor.execute('SELECT Phrase FROM TrainingPhrases WHERE Phrase = "' + new_value + '"').fetchall()
                if (not len(selection)):
                    cursor.execute('UPDATE TrainingPhrases SET Phrase = "' + new_value + '" WHERE Phrase = "' + old_value + '"')
                    
                    #saves the changes made to the database
                    connection.commit()
        elif (form_data['submitButton'] == 'deleteButton'):
            '''the value accessible through the key 'deleteTrainingPhrase'
            is stored in the variable "value"'''
            value = form_data['deleteTrainingPhrase']
            
            cursor.execute('DELETE FROM TrainingPhrases WHERE Phrase = "' + value + '"')
            
            #saves the changes made to the database
            connection.commit()
        else:
            pass
        
        phrases = cursor.execute('SELECT Phrase FROM TrainingPhrases').fetchall()
        
        connection.close()
        
        return render_template('modify_training_phrase.html', phrases = phrases)
    elif request.method == 'GET':
        phrases = cursor.execute('SELECT Phrase FROM TrainingPhrases').fetchall()
        
        return render_template('modify_training_phrase.html', phrases = phrases)

'''decorator that defines the url path of the
page where to write down training phrases'''
@app.route('/write_down_training')
def write_down_training():
	return 'write_down_training'

'''decorator that defines the url path
of the page where to train the models'''
@app.route('/start_training_model')
def start_training_model():
	return 'start_training_model'

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