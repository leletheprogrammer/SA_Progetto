import json
import random
import spacy
from spacy.gold import GoldParse
from spacy.scorer import Scorer


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