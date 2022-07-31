import pandas as pd

from sklearn.metrics import f1_score

from inference_ir_sa import Recognition

def testing_intent(file):
    return testing('intent', file)

def testing_sentiment(file):
    return testing('sentiment', file)

def testing(name, file):
    r = Recognition(name)
    
    test_df = pd.read_csv(file)
    test_df['y_true'] = test_df[name].map(lambda x: r.le.transform([x])[0])
    test_df['y_pred'] = test_df['phrase'].map(lambda x: r.recognize(name, x, code=True))
    y_true = test_df['y_true'].values
    y_pred = test_df['y_pred'].values
    
    return f1_score(y_true, y_pred, average="micro")