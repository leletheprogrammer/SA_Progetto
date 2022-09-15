# Caso di studio per Sistemi ad Agenti - NLPWebPlatform
NLPWebPlatform è una piattaforma web che offre la possibilità di gestire Intents, Entities e Datasets (propri per ogni utente), l’addestramento, il download, la cancellazione di tre modelli di NLP (IR, EE e SA), la visualizzazione dei risultati degli addestramenti e il loro testing.<br />
Membri del gruppo:
- Di Gennaro Emmanuele, matricola: 723030, email: e.digennaro3@studenti.uniba.it
- Di Gennaro Massimo, matricola: 723029, email: m.digennaro25@studenti.uniba.it

## 1. Linguaggio di programmazione utilizzato
Python 3.9

## 2. Librerie principali utilizzate
- Flask
- Flask-PyMongo
- Flask-SocketIO
- PyTorch-Ignite
- scikit-learn
- spaCy==2.3.5
- transformers
- it-core-news-sm

## 3. Avvio
Per l'avvio da locale, aprire il Prompt dei comandi ed eseguire mongod.exe; successivamente aprire Anaconda Powershell Prompt come amministratore, settare la variabile d'ambiente FLASK_APP a `main.py` ed eseguire il comando run per flask. Sarà così avviato il server locale in ascolto sulla porta 5000:<br />*127.0.0.1:5000*

## 4. Chiusura
Per la chiusura da locale, recarsi su Anaconda Powershell Prompt e premere *CTRL* + *C*.
