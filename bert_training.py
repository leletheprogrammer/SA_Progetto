import numpy as np
import os
import pandas as pd
import random

from ignite.engine import Engine, Events
from ignite.handlers import ModelCheckpoint, EarlyStopping
from ignite.metrics import RunningAverage, Precision, Loss, Recall
import torch
from torch.nn.functional import cross_entropy
from torch.utils.data import DataLoader
from transformers import BertForSequenceClassification, AutoTokenizer
from transformers.optimization import AdamW

import dataset_intent as di
import dataset_sentiment as ds

num_epoch_intent = -1
num_iteration_intent = -1
length_epoch_intent = -1
num_epoch_sentiment = -1
num_iteration_sentiment = -1
length_epoch_sentiment = -1

def train(df_train, col_name, learning_rate, eps, batch_size, hidden_dropout_prob, patience, max_epoch):

    global num_epoch_intent
    global num_iteration_intent
    global length_epoch_intent
    global num_epoch_sentiment
    global num_iteration_sentiment
    global length_epoch_sentiment
    if(col_name == 'intent'):
        num_epoch_intent = 0
        num_iteration_intent = 1
    elif(col_name == 'sentiment'):
        num_epoch_sentiment = 0
        num_iteration_sentiment = 1

    # Set Seed
    SEED = 123
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    np.random.seed(SEED)
    random.seed(SEED)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    df = df_train.drop_duplicates()
    model_name = 'dbmdz/bert-base-italian-xxl-cased'
    models_dir = 'models'
    if(col_name == 'intent'):
        num_labels = len(df.intent.unique())
    elif(col_name == 'sentiment'):
        num_labels = len(df.sentiment.unique())
    if(col_name == 'intent'):
        train_ds = di.TextualDataset('train_' + col_name + '_preprocessed.json', device)
        val_ds = di.TextualDataset('val_' + col_name + '_preprocessed.json', device)
    elif(col_name == 'sentiment'):
        train_ds = ds.TextualDataset('train_' + col_name + '_preprocessed.json', device)
        val_ds = ds.TextualDataset('val_' + col_name + '_preprocessed.json', device)

    bert_model = BertForSequenceClassification.from_pretrained(
        pretrained_model_name_or_path=model_name,
        num_labels=num_labels,
        output_attentions=False,
        output_hidden_states=False,
        hidden_dropout_prob=hidden_dropout_prob
    ).to(device)

    train_dl = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_dl = DataLoader(val_ds, batch_size=batch_size, shuffle=True, num_workers=0)

    optimizer = AdamW(bert_model.parameters(), lr=learning_rate, eps=eps)

    train_logs = {}
    val_logs = {}

    def process_function(engine, batch):
        bert_model.train()
        optimizer.zero_grad()
        input_ids, attention_mask, token_type_ids, labels = batch
        output = bert_model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            labels=labels
        )
        loss = output[0]
        loss.backward()
        optimizer.step()
        return loss.item()

    def eval_function(engine, batch):
        bert_model.eval()
        with torch.no_grad():
            input_ids, attention_mask, token_type_ids, labels = batch
            output = bert_model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                token_type_ids=token_type_ids,
                labels=labels
            )
        return output[1], labels

    trainer = Engine(process_function)
    train_evaluator = Engine(eval_function)
    validation_evaluator = Engine(eval_function)

    RunningAverage(output_transform=lambda x: x).attach(trainer, 'loss')

    ce_loss = Loss(cross_entropy)
    precision = Precision(average=True)
    recall = Recall(average=True)
    f1 = precision * recall * 2 / (precision + recall)

    ce_loss.attach(train_evaluator, 'ce')
    f1.attach(train_evaluator, 'f1')

    ce_loss.attach(validation_evaluator, 'ce')
    f1.attach(validation_evaluator, 'f1')

    def score_function(engine: Engine):
        return -engine.state.metrics['f1']

    early_stopping_handler = EarlyStopping(
        patience=patience,
        score_function=score_function,
        trainer=trainer,
    )

    validation_evaluator.add_event_handler(Events.COMPLETED, early_stopping_handler)

    @trainer.on(Events.STARTED)
    def assign_epoch_length(engine):
        global length_epoch_sentiment
        global length_epoch_intent
        if(col_name == 'intent'):
            length_epoch_intent = engine.state.epoch_length
        elif(col_name == 'sentiment'):
            length_epoch_sentiment = engine.state.epoch_length

    @trainer.on(Events.ITERATION_COMPLETED(every = 1))
    def increase_num_iteration(engine):
        global num_iteration_intent
        global num_iteration_sentiment
        if(col_name == 'intent'):
            num_iteration_intent = engine.state.iteration
        elif(col_name == 'sentiment'):
            num_iteration_sentiment = engine.state.iteration

    @trainer.on(Events.EPOCH_COMPLETED)
    def increase_num_epoch(engine):
        global num_iteration_intent
        global num_epoch_intent
        global num_iteration_sentiment
        global num_epoch_sentiment
        if(col_name == 'intent'):
            num_iteration_intent = 0
            num_epoch_intent = engine.state.epoch
        elif(col_name == 'sentiment'):
            num_iteration_sentiment = 0
            num_epoch_sentiment = engine.state.epoch

    @trainer.on(Events.EPOCH_COMPLETED)
    def log_training_results(engine):
        train_evaluator.run(train_dl)
        metrics = train_evaluator.state.metrics
        ce = metrics['ce']
        f1 = metrics['f1'] * 100
        train_logs[engine.state.epoch] = [f1, ce]

    @trainer.on(Events.EPOCH_COMPLETED)
    def log_validation_results(engine):
        validation_evaluator.run(val_dl)
        metrics = validation_evaluator.state.metrics
        ce = metrics['ce']
        f1 = metrics['f1'] * 100
        val_logs[engine.state.epoch] = [f1, ce]

    checkpoint_handler = ModelCheckpoint(
        models_dir, 'checkpoint_' + col_name, n_saved=1, save_as_state_dict=True, require_empty=False)
    trainer.add_event_handler(Events.EPOCH_COMPLETED, checkpoint_handler, {'model': bert_model})

    @trainer.on(Events.COMPLETED)
    def model_plot_handler():
        df_train_logs = pd.DataFrame.from_dict(train_logs, orient='index')
        df_train_logs.columns = ['F1-Score Training', 'Loss Training']
        df_val_logs = pd.DataFrame.from_dict(val_logs, orient='index')
        df_val_logs.columns = ['F1-Score Validation', 'Loss Validation']
        df_logs_merged = df_train_logs.merge(df_val_logs, left_index=True, right_index=True)
        df_logs_merged.to_csv('results_' + col_name + '.csv', index=False)

    @trainer.on(Events.COMPLETED)
    def model_save_handler():
        if os.path.isdir(os.path.join(models_dir, col_name)):
            for file_name in os.listdir(os.path.join(models_dir, col_name)):
                file = os.path.join(models_dir, col_name, file_name)
                if os.path.isfile(file):
                    os.remove(file)
            os.rmdir(os.path.join(models_dir, col_name))
        os.mkdir(os.path.join(models_dir, col_name))
        bert_model.save_pretrained(save_directory=os.path.join(models_dir, col_name))
        AutoTokenizer.from_pretrained(model_name).save_pretrained(os.path.join(models_dir, col_name))

    trainer.run(train_dl, max_epochs=max_epoch)
    validation_evaluator.run(val_dl)

def get_num_epoch_intent():
    global num_epoch_intent
    return num_epoch_intent

def get_num_epoch_sentiment():
    global num_epoch_sentiment
    return num_epoch_sentiment

def get_num_iteration_intent():
    global num_iteration_intent
    global length_epoch_intent
    while (num_iteration_intent > length_epoch_intent):
        num_iteration_intent -= length_epoch_intent
    return num_iteration_intent

def get_num_iteration_sentiment():
    global num_iteration_sentiment
    global length_epoch_sentiment
    while (num_iteration_sentiment > length_epoch_sentiment):
        num_iteration_sentiment -= length_epoch_sentiment
    return num_iteration_sentiment

def get_epoch_length_intent():
    global length_epoch_intent
    return length_epoch_intent

def get_epoch_length_sentiment():
    global length_epoch_sentiment
    return length_epoch_sentiment

def get_num_progress_intent():
    global num_iteration_intent
    global length_epoch_intent
    fraction_progress = (num_iteration_intent / length_epoch_intent) * 100
    num_progress = 0
    if ((fraction_progress - int(fraction_progress)) > 0.5):
        num_progress = int(fraction_progress) + 1
    else:
        num_progress = int(fraction_progress)
    return num_progress

def get_num_progress_sentiment():
    global num_iteration_sentiment
    global length_epoch_sentiment
    fraction_progress = (num_iteration_sentiment / length_epoch_sentiment) * 100
    num_progress = 0
    if ((fraction_progress - int(fraction_progress)) > 0.5):
        num_progress = int(fraction_progress) + 1
    else:
        num_progress = int(fraction_progress)
    return num_progress