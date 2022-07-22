import torch
from torch import nn
from joblib import load
from transformers import BertForSequenceClassification, AutoTokenizer


class SentimentRecognition:

    def __init__(self):
        path = 'models/sentiment'
        self.model = BertForSequenceClassification.from_pretrained(path)
        self.tokenizer = AutoTokenizer.from_pretrained(path)
        self.le = load('mapping_sentiment.joblib')
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        self.model.eval()

    def recognize(self, text, code=False):
        tensor = torch.tensor(self.tokenizer.encode(text, add_special_tokens=True)).unsqueeze(0).long().to(
            self.device)
        with torch.no_grad():
            output = self.model(input_ids=tensor)
            logits, = nn.functional.softmax(output[0], dim=1)
            sentiment_code = torch.argmax(logits).item()
            if code:
                return sentiment_code
            else:
                sentiment = self.le.inverse_transform([sentiment_code])[0]
                return sentiment
