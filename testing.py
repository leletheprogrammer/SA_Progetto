import pandas as pd

from sklearn.metrics import f1_score

from inference import Recognition, SpacyTesting

def testing_intent():
    return testing_models('intent', 'test_intent.csv')

def testing_entities():
    st = SpacyTesting()
    f1 = st.run()
    return f1

def testing_sentiment():
    return testing_models('sentiment', 'test_sentiment.csv')

def testing_models(name, file):
    r = Recognition(name)
    
    test_df = pd.read_csv(file)
    test_df['y_true'] = test_df[name].map(lambda x: r.le.transform([x])[0])
    test_df['y_pred'] = test_df['phrase'].map(lambda x: r.recognize(name, x, code=True))
    y_true = test_df['y_true'].values
    y_pred = test_df['y_pred'].values
    
    return f1_score(y_true, y_pred, average="micro")