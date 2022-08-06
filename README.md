# Caso di studio per Sistemi ad Agenti - NLPWebPlatform
Web Platform che offre diversi servizi, tra cui la gestione di Intents, Entities e Training Phrases, l’addestramento, il download,<br />
la cancellazione di tre modelli di NLP (IR, SA e EE), la visualizzazione dei risultati degli addestramenti e il loro testing.<br />
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
Per l'avvio, aprire il terminale ed eseguire mongod.exe; successivamente aprire Anaconda PowerShell Prompt come amministratore,<br />
settare la variabile d'ambiente FLASK_APP a `main.py` ed eseguire il comando run per flask. Sarà così avviato il server locale in<br />
ascolto sulla porta 5000: *127.0.0.1:5000*

## 4. Chiusura
Per la chiusura, recarsi sul terminale e premere *CTRL* + *C*.
