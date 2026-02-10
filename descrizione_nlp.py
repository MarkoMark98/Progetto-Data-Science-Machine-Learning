#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
descrizione_nlp.py

Script per l'analisi NLP delle didascalie (descrizioni) dei post Instagram.
Estrae entità nominate, location, utenti taggati e altre informazioni dalle 
descrizioni dei post usando Stanford CoreNLP.
"""

from pycorenlp import StanfordCoreNLP
import os, json, sys
from dotenv import load_dotenv

# Carica le variabili d'ambiente
load_dotenv()

# (Opzionale) Avvio manuale del server Stanford CoreNLP
# os.chdir("C:/Program Files/stanford-corenlp-4.2.2")
# os.system("java -mx5g -cp \"*\" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -timeout 10000")

# Connessione al server Stanford CoreNLP
nlp = StanfordCoreNLP(os.getenv('CORENLP_URL', 'http://localhost:9000'))

# Annotatori NLP da utilizzare
annotators = "ssplit,ner,depparse"

# Tipi di entità nominate da estrarre
ner_keys = ["PERSON", "LOCATION", "ORGANIZATION", "NUMBER", "DATE", "EMAIL", 
            "URL", "CITY", "STATE_OR_PROVINCE", "COUNTRY", "NATIONALITY", 
            "RELIGION", "TITLE", "IDEOLOGY"]

# Chiavi delle informazioni da estrarre dai post
info_keys = ["taggati", "testo", "location", "descrizione"]

# Chiavi per le dipendenze sintattiche
reference_keys = ["basicDependencies","enhancedDependencies","enhancedPlusPlusDependencies"]

# Path del dataset
dataset_path = os.getenv('DATASET_PATH', '')

# Itera su tutte le cartelle degli account
for account in os.listdir(dataset_path):
    # Salta il dataset completo
    if account == "dataset_completo.json":
        continue

    # (Opzionale) Salta account già processati
    # if "didascalia_nlp.json" in os.listdir(dataset_path + account):
    #    continue

    print(account)
    
    # Apre il file info.json contenente i dati dei post
    js = open(dataset_path + account+ "/info.json")
    try:
        info_arr = json.load(js)
    except:
        # Se il file è corrotto o non esiste, salta questo account
        continue

    # Inizializza il dizionario per le informazioni estratte
    info_js = dict()
    
    # Processa ogni post dell'account
    for info_pic in info_arr:
        info_js["pictures"] = []
        pic_metdata = dict()
        
        # Estrae diverse informazioni dal post
        for info_k in info_keys:
            if info_k in info_pic.keys():
                
                # Processa il testo della didascalia
                if info_k == "testo" and info_pic["testo"] != None:
                    testo = ""
                    
                    # Estrae il testo dal formato nested di Instagram
                    if len(info_pic["testo"]) > 0:
                        testo = info_pic["testo"][0]["node"]["text"]
                        
                        # Esegue l'annotazione NLP sul testo
                        res = nlp.annotate(testo,
                            properties={
                                'annotators': annotators,
                                'outputFormat': 'json',
                                'timeout': 1000,
                            })
            
                        # Se l'annotazione fallisce, salta questo testo
                        if isinstance(res,str):
                            continue
                        
                        # Inizializza struttura per risultati NLP
                        nlp_res = dict()
                        nlp_res["entities"] = []
                        nlp_res["references"] = []

                        # Processa ogni frase annotata
                        for sent in res["sentences"]:
                            check_references = []
                            
                            # Estrae ogni entità menzionata
                            for m in sent["entitymentions"]:
                                mention = m['text']
                                ner = m["ner"]
                                
                                # Gestisce la confidenza della predizione
                                if "nerConfidences" in m.keys():
                                    ner_confidence = m['nerConfidences']
                                    if isinstance(ner_confidence, dict):
                                        if ner in ner_confidence.keys():
                                            ner_confidence = ner_confidence[ner]
                                else:
                                    ner_confidence = "None"

                                # Processa solo entità di interesse
                                if ner in ner_keys:
                                    find = False
                                    
                                    # Cerca se l'entità esiste già
                                    for entity in nlp_res["entities"]:
                                        if ner in entity.keys():
                                            find = True
                                            entity[ner].append(mention)
                                            if ner in ["TITLE", "ORGANIZATION"]:
                                                check_references.append(mention)
                                            break
                                    
                                    # Se non esiste, crea nuova voce
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
                            
                            # Analizza le dipendenze sintattiche
                            for k in reference_keys:
                                for dependency in sent[k]:
                                    key = dependency["governorGloss"]
                                    
                                    if key in check_references:
                                        find = False
                                        
                                        for reference in nlp_res["references"]:
                                            if key in reference.keys():
                                                find = True
                                                item = dependency["dependentGloss"]
                                                if not item in reference[key]:
                                                    reference[key].append(item)
                                                break
                                        
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
                    
                    # Salva il testo e i risultati NLP se il testo non è vuoto
                    if testo != "":
                        pic_metdata.update({"didascalia":{"testo":testo, "nlp":nlp_res}})
                
                # Estrae la location del post
                elif info_k == "location" and info_pic["location"] != None:
                    pic_metdata.update({info_k:info_pic["location"]["name"]})

                # Estrae gli utenti taggati nel post
                elif info_k == "taggati" and info_pic["taggati"] != None:
                    taggati = []
                    for tag in info_pic["taggati"]:
                        if len(tag) > 0:
                            taggati.append({
                                "full_name": tag["node"]["user"]["full_name"], 
                                "username": tag["node"]["user"]["username"]
                            })
                    if len(taggati) > 0:
                        pic_metdata.update({info_k:taggati})
                
                # Estrae la descrizione accessibilità (alt text) dell'immagine
                elif info_k == "descrizione" and info_pic["descrizione"] != None:
                    pic_metdata.update({info_k:info_pic["descrizione"]})

        # Aggiunge i metadata del post alla lista
        info_js["pictures"].append({"metadata":pic_metdata})
    
    # Salva tutti i risultati in un file JSON
    with open(dataset_path+account+"/didascalia_nlp.json", "w") as js:
        json.dump(info_js, js)
