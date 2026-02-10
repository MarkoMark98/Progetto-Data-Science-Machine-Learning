#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StanfordCoreWithStanza.py

Script di test per verificare la connessione e il funzionamento di 
Stanford CoreNLP utilizzando la libreria Stanza come client.
"""

from stanza.server import CoreNLPClient
import time, json
import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente
load_dotenv()

# Costruisce un client CoreNLP con annotatori di base, 
# allocazione di memoria di 4GB e porta 9000
client = CoreNLPClient(
    annotators=['ner'],  # Annotatore per Named Entity Recognition
    memory='4G',         # Memoria allocata al server Java
    endpoint=os.getenv('CORENLP_URL', 'http://localhost:9000'),  # URL del server
    be_quiet=False       # Mostra output del server
)
print(client)

# Avvia il server in background e attende alcuni secondi
# Nota: in pratica questo è totalmente opzionale, poiché di default 
# il server verrà avviato automaticamente alla prima annotazione
client.start()
time.sleep(10)  # Aspetta che il server si avvii completamente

# Path del file bio.json da analizzare (configurabile tramite .env)
bio_file_path = os.getenv('TEST_BIO_FILE', './dataset/example_account/bio.json')

# Apre e carica il file bio.json contenente il testo da analizzare
js = open(bio_file_path)
sentence = json.load(js)
print(sentence)

# Invia il testo al server CoreNLP per l'annotazione NER
document = client.annotate(sentence)

# Stampa il tipo di oggetto restituito (dovrebbe essere un protobuf Document)
print(type(document))

# Esempio di come accedere alle entità estratte:
# for sentence in document.sentence:
#     for token in sentence.token:
#         if token.ner != 'O':  # 'O' significa nessuna entità
#             print(f"Token: {token.word}, NER: {token.ner}")
