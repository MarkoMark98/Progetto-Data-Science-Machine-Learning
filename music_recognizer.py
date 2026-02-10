#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
music_recognizer.py (Versione Originale Commentata)

Script per riconoscere la musica nei video Instagram usando AudD.io API.
Converte i file MP4 in MP3 e utilizza l'API di riconoscimento musicale.

ATTENZIONE: Richiede API token AudD.io valido
"""

import requests, os, base64, json
from moviepy.editor import *
from dotenv import load_dotenv

# Carica le variabili d'ambiente
load_dotenv()

# Apre il file di log per tracciare l'avanzamento e gli errori
log_file = open("log.txt","a+")

# Path del dataset contenente le cartelle degli account
dataset_path = os.getenv('DATASET_PATH', '')

# Ottiene la lista di tutti gli account nel dataset
accounts = os.listdir(dataset_path)

# Lista per tracciare i file MP3 generati (opzionale)
mp3_files = []

# Contatore per tenere traccia del progresso
i = 1

# Itera su tutti gli account
for account in accounts:
    # Salta il file di log
    if account == "log.txt":
        continue
    
    # Lista per raccogliere le informazioni musicali di questo account
    music_info = []
    
    # Path completo della cartella dell'account
    account_path = dataset_path + "/" + account
    
    # Ottiene la lista di tutti i file nella cartella dell'account
    files = os.listdir(account_path)
    
    # Se music_info.json esiste già, salta questo account
    if "music_info.json" in files:
        i+=1
        continue
    
    # Stampa e logga l'account in elaborazione
    print("#",i," Analizzo: "+account)
    log_file.write("\n#"+str(i)+" Analizzo: "+account)
    
    # Prepara il file JSON per salvare i risultati
    json_file = open(account_path+"/music_info.json", "w")
    
    # Itera su tutti i file nella cartella dell'account
    for f in files:
        # Separa il nome del file dall'estensione
        file_name, extension = f.split(".")
        
        # Processa solo i file video MP4
        if extension == "mp4":
            print("\tConverto l'mp4 in mp3 "+f)
            log_file.write("\n\tConverto l'mp4 in mp3 "+f)
           
            try:
                # Carica il video con MoviePy
                video = VideoFileClip(os.path.join(account_path, f))
                
                # Estrae l'audio e lo salva come MP3
                video.audio.write_audiofile(os.path.join(account_path, file_name+".mp3"))
                
            except AttributeError as e:
                # Il video non contiene una traccia audio
                print("\tQuesto video non contiene audio "+f)
                log_file.write("\n\tQuesto video non contiene audio "+f)
                continue
                
            except OSError as osErr:
                # Il file video è corrotto o non leggibile
                print("\tIl file è corrotto "+f)
                log_file.write("\n\tIl file è corrotto "+f)
                continue

            # Aggiunge il path del file MP3 alla lista (opzionale)
            mp3_files.append(account_path+"/"+file_name+".mp3")
            
            # Apre il file MP3 appena creato in modalità binaria
            video = open(account_path+"/"+file_name+".mp3", 'rb')

            # Prepara i parametri per la chiamata API AudD.io
            data = {
                'accurate_offsets': 'true',  # Usa offset accurati
                'skip': '3',                  # Salta i primi 3 secondi
                'every': '1',                 # Analizza ogni secondo
                'api_token': os.getenv('AUDD_API_TOKEN', '')  # Token API da .env
            }
            
            print("\tRiconosco la musica...")
            log_file.write("\n\tRiconosco la musica...")
            
            # Invia la richiesta POST all'API AudD.io con il file audio
            result = requests.post('https://enterprise.audd.io/', data=data, files={"file":video}).json()
            
            # Verifica se la richiesta è andata a buon fine
            if result["status"] == "success":
                # Se ci sono risultati (musica riconosciuta)
                if len(result["result"]) > 0:
                    print("\tCorrispondenze trovate!")
                    log_file.write("\n\tCorrispondenze trovate!")
                    # Aggiunge i risultati alla lista
                    music_info.append(result["result"])
                else:
                    # Nessuna corrispondenza trovata nel database musicale
                    print("\tNon sono riuscito a trovare nessuna corrispondenza per questo file")
                    log_file.write("\n\tNon sono riuscito a trovare nessuna corrispondenza per questo file")
    
    # Stampa e logga il numero di canzoni riconosciute per questo account
    print("\tCorrispondenze trovate per per "+account+": "+str(len(music_info)))
    log_file.write("\n\tCorrispondenze trovate per "+account+": "+str(len(music_info)))
    log_file.flush()  # Forza la scrittura su disco
    
    # Salva tutte le informazioni musicali nel file JSON
    json.dump(music_info, json_file)
    
    # Incrementa il contatore
    i+=1

# Messaggio finale
print("Tutti gli account sono stati analizzati!")
log_file.write("\nTutti gli account sono stati analizzati!")
log_file.flush()
log_file.close()
