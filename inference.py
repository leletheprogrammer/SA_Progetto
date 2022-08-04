from joblib import load
import json
import random

import spacy
from spacy.gold import GoldParse
from spacy.scorer import Scorer
import torch
from torch import nn
from transformers import BertForSequenceClassification, AutoTokenizer

class Recognition:
    def __init__(self, name):
        path = 'models/' + name
        self.model = BertForSequenceClassification.from_pretrained(path)
        self.tokenizer = AutoTokenizer.from_pretrained(path)
        self.le = load('mapping_' + name + '.joblib')
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        self.model.eval()

    def recognize(self, name, text, code=False):
        tensor = torch.tensor(self.tokenizer.encode(text, add_special_tokens=True)).unsqueeze(0).long().to(self.device)
        with torch.no_grad():
            output = self.model(input_ids=tensor)
            logits, = nn.functional.softmax(output[0], dim=1)
            if(name == 'intent'):
                max_prob = torch.max(logits).item()
                intent_code = torch.argmax(logits).item()
                if code:
                    return intent_code
                else:
                    intent = self.le.inverse_transform([intent_code])[0] \
                        if max_prob >= 0.60 else 'NotUnderstand'
                    return intent
            elif(name == 'sentiment'):
                sentiment_code = torch.argmax(logits).item()
                if code:
                    return sentiment_code
                else:
                    sentiment = self.le.inverse_transform([sentiment_code])[0]
                    return sentiment

class SpacyTesting:
    def __init__(self):
        self.test = self.convert_json_to_spacy()

    @staticmethod
    def convert_json_to_spacy():
        dataset = []
        with open('test_entities.json', 'r') as test:
            lines = test.readlines()
            for line in lines:
                data = json.loads(line)
                text = data['phrase']
                entities = []
                try:
                    for annotation in data['entities']:
                        entities.append((annotation[0], annotation[1], annotation[2]))
                    dataset.append((text, {'entities': entities}))
                except TypeError:
                    pass
        random.shuffle(dataset)
        return dataset

    @staticmethod
    def evaluate(ner_model, examples):
        scorer = Scorer()
        examples = map(lambda example: (example[0], example[1]['entities']), examples)
        for input_, annot in examples:
            doc_gold_text = ner_model.make_doc(input_)
            gold = GoldParse(doc_gold_text, entities=annot)
            pred_value = ner_model(input_)
            scorer.score(pred_value, gold)
        return scorer.scores['ents_f']

    def run(self):
        nlp = spacy.load('models/entities')
        f1_score = self.evaluate(nlp, self.test)
        return f1_score