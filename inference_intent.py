import torch
from torch import nn
from joblib import load
from transformers import BertForSequenceClassification, AutoTokenizer


class IntentRecognition:

    def __init__(self):
        path = 'models/intent'
        self.model = BertForSequenceClassification.from_pretrained(path)
        self.tokenizer = AutoTokenizer.from_pretrained(path)
        self.le = load('mapping_intent.joblib')
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        self.model.eval()

    def recognize(self, text, code=False):
        tensor = torch.tensor(self.tokenizer.encode(text, add_special_tokens=True)).unsqueeze(0).long().to(
            self.device)
        with torch.no_grad():
            output = self.model(input_ids=tensor)
            logits, = nn.functional.softmax(output[0], dim=1)
            max_prob = torch.max(logits).item()
            intent_code = torch.argmax(logits).item()
            if code:
                return intent_code
            else:
                intent = self.le.inverse_transform([intent_code])[0] \
                    if max_prob >= 0.60 else 'NotUnderstand'
                return intent