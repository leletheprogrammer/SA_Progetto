import pandas as pd

from sklearn.metrics import f1_score

from inference import Recognition, SpacyTesting

def testing_intent(name, dataset):
    return testing_models('intent', 'test_intent_' + name + '_' + dataset + '.csv', name + '_' + dataset)

def testing_entities(name, dataset):
    st = SpacyTesting(name, dataset)
    f1 = st.run()
    return f1

def testing_sentiment(name, dataset):
    return testing_models('sentiment', 'test_sentiment_' + name + '_' + dataset + '.csv', name + '_' + dataset)

def testing_models(type, file, name):
    r = Recognition(type, name)
    
    test_df = pd.read_csv(file)
    test_df['y_true'] = test_df[type].map(lambda x: r.le.transform([x])[0])
    test_df['y_pred'] = test_df['phrase'].map(lambda x: r.recognize(type, x, code=True))
    y_true = test_df['y_true'].values
    y_pred = test_df['y_pred'].values
    
    return f1_score(y_true, y_pred, average="micro")