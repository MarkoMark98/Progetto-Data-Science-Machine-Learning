#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bio_nlp.py

Script per l'analisi NLP (Named Entity Recognition) delle biografie Instagram.
Utilizza Stanford CoreNLP per estrarre entità nominate come persone, luoghi, 
organizzazioni, date, email, URL, ecc. dalle biografie degli account.
"""

from pycorenlp import StanfordCoreNLP
import os, json, sys
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# (Opzionale) Avvio manuale del server Stanford CoreNLP se non è già in esecuzione
# os.chdir("C:/Program Files/stanford-corenlp-4.2.2")
# os.system("java -mx5g -cp \"*\" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -timeout 10000")

# Connessione al server Stanford CoreNLP (deve essere già avviato)
nlp = StanfordCoreNLP(os.getenv('CORENLP_URL', 'http://localhost:9000'))

# Annotatori da utilizzare: split delle frasi, NER, dependency parsing
annotators = "ssplit,ner,depparse"

# Chiavi delle entità nominate da estrarre
ner_keys = ["PERSON", "LOCATION", "ORGANIZATION", "NUMBER", "DATE", "EMAIL", 
            "URL", "CITY", "STATE_OR_PROVINCE", "COUNTRY", "NATIONALITY", 
            "RELIGION", "TITLE", "IDEOLOGY"]

# Chiavi per le dipendenze sintattiche (per analisi avanzata)
reference_keys = ["basicDependencies","enhancedDependencies","enhancedPlusPlusDependencies"]

# Path del dataset contenente le cartelle degli account
dataset_path = os.getenv('DATASET_PATH', '')

# Itera su tutte le cartelle degli account nel dataset
for account in os.listdir(dataset_path):
    # Salta il file di log
    if account == "log.txt":
        continue

    # (Opzionale) Salta gli account già processati
    # if "nlp.json" in os.listdir(dataset_path + account):
    #    continue

    print(account)
    
    # Apre il file bio.json contenente la biografia dell'account
    js = open(dataset_path + account+ "/bio.json")
    sentence = json.load(js)
    print(sentence)

    # Invia il testo al server CoreNLP per l'annotazione NLP
    res = nlp.annotate(sentence,
                    properties={
                        'annotators': annotators,
                        'outputFormat': 'json',
                        'timeout': 1000,
                    })
    
    # Se la risposta è una stringa (errore), salta questo account
    if isinstance(res,str):
        continue
    
    # Inizializza il dizionario per i risultati NLP
    nlp_res = dict()
    nlp_res["entities"] = []      # Lista di entità estratte
    nlp_res["references"] = []    # Lista di riferimenti sintattici

    # Processa ogni frase annotata
    for sent in res["sentences"]:
        check_references = []  # Lista temporanea per tracciare titoli e organizzazioni
        
        # Estrae ogni menzione di entità nella frase
        for m in sent["entitymentions"]:
            mention = m['text']  # Testo dell'entità
            ner = m["ner"]       # Tipo di entità (PERSON, LOCATION, ecc.)
            
            # Gestisce la confidenza della predizione NER
            if "nerConfidences" in m.keys():
                ner_confidence = m['nerConfidences']
                if isinstance(ner_confidence, dict):
                    if ner in ner_confidence.keys():
                        ner_confidence = ner_confidence[ner]
            else:
                ner_confidence = "None"

            # Processa solo le entità che ci interessano
            if ner in ner_keys:
                find = False
                
                # Cerca se l'entità esiste già nella lista
                for entity in nlp_res["entities"]:
                    if ner in entity.keys():
                        find = True
                        entity[ner].append(mention)
                        # Traccia titoli e organizzazioni per l'analisi delle dipendenze
                        if ner in ["TITLE", "ORGANIZATION"]:
                            check_references.append(mention)
                        break
                
                # Se non esiste, crea una nuova voce per questo tipo di entità
                if not find:
                    nlp_res["entities"].append({ner:[]})
                    find = False
                    for entity in nlp_res["entities"]:
                        if ner in entity.keys():
                            find = True
                            entity[ner].append(mention)
                            if ner in ["TITLE", "ORGANIZATION"]:
                                check_references.append(mention)
                            break
        
        # Analizza le dipendenze sintattiche per estrarre relazioni
        for k in reference_keys:
            for dependency in sent[k]:
                key = dependency["governorGloss"]  # Parola principale
                
                # Se la parola principale è un titolo o organizzazione che abbiamo tracciato
                if key in check_references:
                    find = False
                    
                    # Cerca se questa riferimento esiste già
                    for reference in nlp_res["references"]:
                        if key in reference.keys():
                            find = True
                            item = dependency["dependentGloss"]  # Parola dipendente
                            if not item in reference[key]:
                                reference[key].append(item)
                            break
                    
                    # Se non esiste, crea una nuova voce
                    if not find:
                        nlp_res["references"].append({key:[]})
                        find = False
                        for reference in nlp_res["references"]:
                            if key in reference.keys():
                                find = True
                                item = dependency["dependentGloss"]
                                if not item in reference[key]:
                                    reference[key].append(item)
                                break
    
    # Salva i risultati NLP in un file JSON
    with open(dataset_path+account+"/nlp.json", "w") as js:
        json.dump(nlp_res, js)
