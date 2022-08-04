import pandas as pd

from sklearn.metrics import f1_score

from inference_intent import IntentRecognition

def testing():
    ir = IntentRecognition()
    test_df = pd.read_csv('test_intent.csv')
    test_df['y_true'] = test_df['intent'].map(lambda x: ir.le.transform([x])[0])
    test_df['y_pred'] = test_df['phrase'].map(lambda x: ir.recognize(x, code=True))
    y_true = test_df['y_true'].values
    y_pred = test_df['y_pred'].values
    return f1_score(y_true, y_pred, average="micro")