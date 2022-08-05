from matplotlib.figure import Figure
import os
import pandas as pd

def graphic_loss_creation(form_data):
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    if(form_data['graphicLoss'] == 'graphicLossIntent'):
        df_intent = pd.read_csv('results_intent.csv')
        axis.plot(df_intent[['Loss Training', 'Loss Validation']])
        axis.legend(['Loss Training', 'Loss Validation'])
    elif(form_data['graphicLoss'] == 'graphicLossSentiment'):
        df_sentiment = pd.read_csv('results_sentiment.csv')
        axis.plot(df_sentiment[['Loss Training', 'Loss Validation']])
        axis.legend(['Loss Training', 'Loss Validation'])
    elif(form_data['graphicLoss'] == 'graphicLossEntities'):
        df_entities = pd.read_csv('results_entities.csv')
        axis.plot(df_entities[['loss']])
    axis.set_xlabel('epoch')
    axis.set_ylabel('loss')
    if not os.path.isdir('static'):
        os.mkdir('static')
    if not os.path.isdir(os.path.join('static', 'images')):
        os.mkdir(os.path.join('static', 'images'))
    if(form_data['graphicLoss'] == 'graphicLossIntent'):
        fig.savefig(os.path.join('static', 'images','loss_graphic_intent.png'))
    elif(form_data['graphicLoss'] == 'graphicLossSentiment'):
        fig.savefig(os.path.join('static', 'images','loss_graphic_sentiment.png'))
    elif(form_data['graphicLoss'] == 'graphicLossEntities'):
        fig.savefig(os.path.join('static', 'images','loss_graphic_entities.png'))

def graphic_score_creation(form_data):
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    if(form_data['graphicScore'] == 'graphicScoreIntent'):
        df_intent = pd.read_csv('results_intent.csv')
        axis.plot(df_intent[['F1-Score Training', 'F1-Score Validation']])
        axis.legend(['F1-Score Training', 'F1-Score Validation'])
    elif(form_data['graphicScore'] == 'graphicScoreSentiment'):
        df_sentiment = pd.read_csv('results_sentiment.csv')
        axis.plot(df_sentiment[['F1-Score Training', 'F1-Score Validation']])
        axis.legend(['F1-Score Training', 'F1-Score Validation'])
    elif(form_data['graphicScore'] == 'graphicScoreEntities'):
        df_entities = pd.read_csv('results_entities.csv')
        axis.plot(df_entities[['f1']])
    axis.set_xlabel('epoch')
    axis.set_ylabel('score')
    if not os.path.isdir('static'):
        os.mkdir('static')
    if not os.path.isdir(os.path.join('static', 'images')):
        os.mkdir(os.path.join('static', 'images'))
    if(form_data['graphicScore'] == 'graphicScoreIntent'):
        fig.savefig(os.path.join('static', 'images','score_graphic_intent.png'))
    elif(form_data['graphicScore'] == 'graphicScoreSentiment'):
        fig.savefig(os.path.join('static', 'images','score_graphic_sentiment.png'))
    elif(form_data['graphicScore'] == 'graphicScoreEntities'):
        fig.savefig(os.path.join('static', 'images','score_graphic_entities.png'))