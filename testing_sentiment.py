import pandas as pd
from sklearn.metrics import f1_score
from inference_sentiment import SentimentRecognition

def testing(file):
    sa = SentimentRecognition()
    test_df = pd.read_csv(file)
    test_df['y_true'] = test_df['sentiment'].map(lambda x: sa.le.transform([x])[0])
    test_df['y_pred'] = test_df['phrase'].map(lambda x: sa.recognize(x, code=True))
    y_true = test_df['y_true'].values
    y_pred = test_df['y_pred'].values
    return f1_score(y_true, y_pred, average="micro")