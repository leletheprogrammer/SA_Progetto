import preparation as p

def train(mongo, path):
    p.creation_files(mongo.db.training_phrases.find({'entities': {'$exists': 1,'$ne': '[]'}},{'_id': 0,'intent': 0, 'sentiment': 0, 'emotion': 0}), path)