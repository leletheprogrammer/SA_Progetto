import os
import torch
import random
import numpy as np
import pandas as pd
from ignite.contrib.handlers import ProgressBar
from ignite.engine import Engine, Events
from ignite.handlers import ModelCheckpoint, EarlyStopping
from ignite.metrics import RunningAverage, Precision, Loss, Recall
from torch.nn.functional import cross_entropy
from torch.utils.data import DataLoader
from transformers import BertForSequenceClassification, AutoTokenizer
from transformers.optimization import AdamW
from dataset import TextualDataset

def train(df_train, learning_rate, eps, batch_size, hidden_dropout_prob, patience, max_epoch):
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
    num_labels = len(df.intent.unique())
    print('num_labels:', num_labels)
    train_ds = TextualDataset('train_preprocessed.json', device)
    val_ds = TextualDataset('val_preprocessed.json', device)

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

    pbar = ProgressBar(persist=True, bar_format='')
    pbar.attach(trainer)

    def score_function(engine: Engine):
        return -engine.state.metrics['f1']

    early_stopping_handler = EarlyStopping(
        patience=patience,
        score_function=score_function,
        trainer=trainer,
    )

    validation_evaluator.add_event_handler(Events.COMPLETED, early_stopping_handler)

    @trainer.on(Events.EPOCH_COMPLETED)
    def log_training_results(engine):
        train_evaluator.run(train_dl)
        metrics = train_evaluator.state.metrics
        ce = metrics['ce']
        f1 = metrics['f1'] * 100
        train_logs[engine.state.epoch] = [f1, ce]
        pbar.log_message(
            f"Training Results - Epoch: {engine.state.epoch}  "
            f"Loss: {ce:.2f} "
            f"F1: {f1:.2f}%")

    @trainer.on(Events.EPOCH_COMPLETED)
    def log_validation_results(engine):
        validation_evaluator.run(val_dl)
        metrics = validation_evaluator.state.metrics
        ce = metrics['ce']
        f1 = metrics['f1'] * 100
        val_logs[engine.state.epoch] = [f1, ce]
        pbar.log_message(
            f"Validation Results - Epoch: {engine.state.epoch}  "
            f"Loss: {ce:.2f} "
            f"F1: {f1:.2f}%")

    checkpoint_handler = ModelCheckpoint(
        models_dir, 'checkpoint', n_saved=1, save_as_state_dict=True, require_empty=False)
    trainer.add_event_handler(Events.EPOCH_COMPLETED, checkpoint_handler, {'model': bert_model})

    @trainer.on(Events.COMPLETED)
    def intent_recognition_plot_handler():
        df_train_logs = pd.DataFrame.from_dict(train_logs, orient='index')
        df_train_logs.columns = ['F1-Score Training', 'Loss Training']
        df_val_logs = pd.DataFrame.from_dict(val_logs, orient='index')
        df_val_logs.columns = ['F1-Score Validation', 'Loss Validation']
        df_logs_merged = df_train_logs.merge(df_val_logs, left_index=True, right_index=True)
        df_logs_merged.to_csv('results.csv', index=False)

    @trainer.on(Events.COMPLETED)
    def intent_recognition_save_handler():
        os.mkdir(os.path.join(models_dir, 'intent_recognition'))
        bert_model.save_pretrained(save_directory=os.path.join(models_dir, 'intent_recognition'))
        AutoTokenizer.from_pretrained(model_name).save_pretrained(os.path.join(models_dir, 'intent_recognition'))

    trainer.run(train_dl, max_epochs=max_epoch)
    print('Run ended')
    validation_evaluator.run(val_dl)