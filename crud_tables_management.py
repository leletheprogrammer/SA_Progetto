def initialization_database(mongo):
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

def post_intents_table(mongo, form_data):
    if form_data['submitButton'] == 'Elimina':
        oldIntent = form_data['oldIntent']
        mongo.db.intents.delete_one({'typology': oldIntent})
        
        collection_list = mongo.db.list_collection_names()
        for element in collection_list:
            if (element != 'users' and element != 'users_to_validate' and element != 'intents' and element != 'entities' and
                element != 'sentiments' and element != 'emotions'):
                for phrase in mongo.db[element].find({'intent': oldIntent}):
                    mongo.db[element].replace_one(phrase, {'phrase': phrase['phrase'], 'intent': '', 'entities': phrase['entities'],
                                                           'sentiment': phrase['sentiment'], 'emotion': phrase['emotion']})
    elif form_data['submitButton'] == 'Svuotamento':
        if len(list(mongo.db.intents.find())) != 0:
            mongo.db.intents.delete_many({})
            
            collection_list = mongo.db.list_collection_names()
            for element in collection_list:
                if (element != 'users' and element != 'users_to_validate' and element != 'intents' and element != 'entities' and
                    element != 'sentiments' and element != 'emotions'):
                    for phrase in mongo.db[element].find():
                        mongo.db[element].replace_one(phrase, {'phrase': phrase['phrase'], 'intent': '', 'entities': phrase['entities'],
                                                               'sentiment': phrase['sentiment'], 'emotion': phrase['emotion']})
    elif form_data['submitButton'] == 'Modifica':
        oldIntent = form_data['oldIntent']
        newIntent = form_data['newIntent']
        if newIntent.isspace() == False:
            newIntent = ' '.join(newIntent.split())
            
            intent = mongo.db.intents.find_one({'typology': newIntent})
            if intent == None:
                mongo.db.intents.replace_one({'typology': oldIntent}, {'typology': newIntent})
                
                collection_list = mongo.db.list_collection_names()
                for element in collection_list:
                    if (element != 'users' and element != 'users_to_validate' and element != 'intents' and element != 'entities' and
                        element != 'sentiments' and element != 'emotions'):
                        for phrase in mongo.db[element].find({'intent': oldIntent}):
                            mongo.db[element].replace_one(phrase, {'phrase': phrase['phrase'], 'intent': '', 'entities': phrase['entities'],
                                                                   'sentiment': phrase['sentiment'], 'emotion': phrase['emotion']})
    elif form_data['submitButton'] == 'Aggiungi':
        newIntent = form_data['newIntent']
        if newIntent.isspace() == False:
            newIntent = ' '.join(newIntent.split())
            
            intent = mongo.db.intents.find_one({'typology': newIntent})
            if intent == None:
                mongo.db.intents.insert_one({'typology': newIntent})

def get_intents_table(mongo):
    typologies = []
    #iteration among the documents in the collection 'intents'
    for intent in mongo.db.intents.find():
        #intent is a dict, so typologies is a list of dict
        typologies.append(intent)
    return typologies

def post_entities_table(mongo, form_data):
    if form_data['submitButton'] == 'Elimina':
        oldEntity = form_data['oldEntity']
        mongo.db.entities.delete_one({'namedEntity': oldEntity})
        
        collection_list = mongo.db.list_collection_names()
        for element in collection_list:
            if (element != 'users' and element != 'users_to_validate' and element != 'intents' and element != 'entities' and
                element != 'sentiments' and element != 'emotions'):
                for phrase in mongo.db[element].find():
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
                    
                    mongo.db[element].replace_one(phrase, {'phrase': phrase['phrase'], 'intent': phrase['intent'], 'entities': entities,
                                                           'sentiment': phrase['sentiment'], 'emotion': phrase['emotion']})
    elif form_data['submitButton'] == 'Svuotamento':
        if len(list(mongo.db.entities.find())) != 0:
            mongo.db.entities.delete_many({})
            
            collection_list = mongo.db.list_collection_names()
            for element in collection_list:
                if (element != 'users' and element != 'users_to_validate' and element != 'intents' and element != 'entities' and
                    element != 'sentiments' and element != 'emotions'):
                    for phrase in mongo.db[element].find():
                        mongo.db[element].replace_one(phrase, {'phrase': phrase['phrase'], 'intent': phrase['intent'], 'entities': '[]',
                                                               'sentiment': phrase['sentiment'], 'emotion': phrase['emotion']})
    elif form_data['submitButton'] == 'Modifica':
        oldEntity = form_data['oldEntity']
        newEntity = form_data['newEntity']
        if newEntity.isspace() == False:
            newEntity = ' '.join(newEntity.split())
                    
            entity = mongo.db.entities.find_one({'namedEntity': newEntity})
            if entity == None:
                mongo.db.entities.replace_one({'namedEntity': oldEntity}, {'namedEntity': newEntity})
                
                collection_list = mongo.db.list_collection_names()
                for element in collection_list:
                    if (element != 'users' and element != 'users_to_validate' and element != 'intents' and element != 'entities' and
                        element != 'sentiments' and element != 'emotions'):
                        for phrase in mongo.db[element].find():
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
                            
                            mongo.db[element].replace_one(phrase, {'phrase': phrase['phrase'], 'intent': phrase['intent'], 'entities': entities,
                                                                   'sentiment': phrase['sentiment'], 'emotion': phrase['emotion']})
    elif form_data['submitButton'] == 'Aggiungi':
        newEntity = form_data['newEntity']
        
        if newEntity.isspace() == False:
            newEntity = ' '.join(newEntity.split())
            
            entity = mongo.db.entities.find_one({'namedEntity': newEntity})
            if entity == None:
                mongo.db.entities.insert_one({'namedEntity': newEntity})

def get_entities_table(mongo):
    namedEntities = []
    #iteration among the documents in the collection 'entities'
    for entity in mongo.db.entities.find():
        #entity is a dict, so typologies is a list of dict
        namedEntities.append(entity)
    return namedEntities

def post_training_phrases_table(mongo, table, request):
    form_data = request.form
    if form_data['submitButton'] == 'Elimina':
        oldPhrase = form_data['oldPhrase']
        table.delete_one({'phrase': oldPhrase})
    elif form_data['submitButton'] == 'Svuotamento':
        if len(list(table.find())) != 0:
            table.delete_many({})
    elif form_data['submitButton'] == 'Modifica':
        oldPhrase = form_data['oldPhrase']
        newPhrase = form_data['newPhrase']
        if newPhrase.isspace() == False:
            newPhrase = ' '.join(newPhrase.split())
                    
            phrase = table.find_one({'phrase': newPhrase})
            if phrase == None:
                table.replace_one({'phrase': oldPhrase}, {'phrase': newPhrase})
    elif form_data['submitButton'] == 'Aggiungi':
        newPhrase = form_data['newPhrase']
        intentAssociated = form_data['selectIntent']
        entitiesAssociated = '['
        sentimentAssociated = form_data['selectSentiment']
        emotionAssociated = form_data['selectEmotion']
        if newPhrase.isspace() == False:
            newPhrase = ' '.join(newPhrase.split())
                    
            phrase = table.find_one({'phrase': newPhrase})
                    
            i = 1
            while True:
                if 'entity' + str(i) in form_data.keys():
                    try:
                        first = newPhrase.index(form_data['entity' + str(i)])
                    except ValueError:
                        pass
                    entitiesAssociated += ('(' + str(first) + ',' + str(first + len(form_data['entity' + str(i)]) - 1) +
                                           ',' + form_data['namedEntity' + str(i)] + '),')
                else:
                    if (entitiesAssociated[len(entitiesAssociated) - 1] != '['):
                        entitiesAssociated = entitiesAssociated[:len(entitiesAssociated) - 1] + ']'
                    else:
                        entitiesAssociated += ']'
                    break
                i = i + 1
            
            if phrase == None:
                table.insert_one({'phrase': newPhrase, 'intent': intentAssociated, 'entities': entitiesAssociated,
                                                      'sentiment': sentimentAssociated, 'emotion': emotionAssociated})
    elif form_data['submitButton'] == 'Annota':
        phraseSelected = form_data['notePhraseSelected']
        intentAssociated = form_data['selectNoteIntent']
        entitiesAssociated = '['
        sentimentAssociated = form_data['selectNoteSentiment']
        emotionAssociated = form_data['selectNoteEmotion']
                
        phrase = table.find_one({'phrase': phraseSelected})
                
        i = 1
        while True:
            if 'entity' + str(i) in form_data.keys():
                try:
                    first = phraseSelected.index(form_data['entity' + str(i)])
                except ValueError:
                    pass
                entitiesAssociated += ('(' + str(first) + ',' + str(first + len(form_data['entity' + str(i)]) - 1) + ',' +
                                       form_data['namedEntity' + str(i)] + '),')
            else:
                if (entitiesAssociated[len(entitiesAssociated) - 1] != '['):
                    entitiesAssociated = entitiesAssociated[:len(entitiesAssociated) - 1] + ']'
                else:
                    entitiesAssociated += ']'
                break
            i = i + 1
        
        table.replace_one(phrase, {'phrase': phraseSelected, 'intent': intentAssociated, 'entities': entitiesAssociated,
                                                       'sentiment': sentimentAssociated, 'emotion': emotionAssociated})
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
                    
            if table.find_one({'phrase': phrase}) == None:
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
                        
                table.insert_one({'phrase': phrase, 'intent': intent, 'entities': entities, 'sentiment': sentiment, 'emotion': emotion})
                    
            i += 5

def get_training_phrases_table(mongo, table):
    phrases = []
    #iteration among the documents in the collection
    for phrase in table.find():
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
            
    sentiments = []
    for sentiment in mongo.db.sentiments.find():
        sentiments.append(sentiment)
            
    emotions = []
    for emotion in mongo.db.emotions.find():
        emotions.append(emotion)
    return phrases, get_intents_table(mongo), get_entities_table(mongo), sentiments, emotions