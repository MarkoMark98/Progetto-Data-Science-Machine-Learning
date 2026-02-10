#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
profilelooter.py

Script per estrarre i metadata dei post Instagram usando instalooter.
Converte gli ID dei media in shortcode e scarica informazioni come 
didascalie, tag, location, musica e owner per ogni post.
"""

import pandas as pd
from instalooter.looters import PostLooter
import base64
import json
import os 
import tqdm
from dotenv import load_dotenv

# Carica le variabili d'ambiente
load_dotenv()

# Cambia la directory di lavoro al path del dataset
dataset_path = os.getenv('DATASET_PATH', './dataset/')
os.chdir(dataset_path)

# Apre il file di log per tracciare gli errori
cavia = open("log.txt","a+")

# Itera su tutte le cartelle (account) nel dataset
for user in os.listdir(): 
    # Salta il file di log stesso
    if user == "log.txt":
        continue
    
    print(user)
    listone = []  # Lista per raccogliere tutti i metadata dei post
    
    # Se info.json esiste già, salta questo account
    if "info.json" in os.listdir(user):
        continue
    
    # Itera su tutti i file media nella cartella dell'account
    for media in os.listdir(user):
        # Salta alcuni media problematici specifici (se necessario)
        if media in ["2616109190035207246.jpg","2631999076914088920.mp4"]:
            continue
        
        print(media)
        
        # Estrae l'ID Instagram dal nome del file
        instagram_id = media.split(".")
        
        # Funzione per convertire l'ID numerico in shortcode Instagram
        id_to_shortcode = lambda instagram_id: base64.b64encode(
            instagram_id.to_bytes(9, 'big'), b'-_'
        ).decode().replace('A', ' ').lstrip().replace(' ', 'A')
        
        # Converte l'ID in shortcode
        codice = id_to_shortcode(int(instagram_id[0]))
        
        try:
            # Crea un PostLooter per questo shortcode
            x = PostLooter(codice)
            
            # Effettua il login se non già loggato (credenziali da .env)
            if not x.logged_in():
                instagram_user = os.getenv('INSTAGRAM_USERNAME', '')
                instagram_pass = os.getenv('INSTAGRAM_PASSWORD', '')
                x.login(instagram_user, instagram_pass)
            
            # Ottiene le informazioni del post
            post = x.get_post_info(codice)
            
        except:
            # Se fallisce, riprova una seconda volta
            try:
                x = PostLooter(codice)
                if not x.logged_in():
                    instagram_user = os.getenv('INSTAGRAM_USERNAME', '')
                    instagram_pass = os.getenv('INSTAGRAM_PASSWORD', '')
                    x.login(instagram_user, instagram_pass)
                post = x.get_post_info(codice)
            except Exception as e:
                # Se fallisce anche il secondo tentativo, logga l'errore
                print(e)
                cavia.write("{} + {} \n".format(user, media))
                cavia.flush()
                continue
        
        # Estrae le informazioni rilevanti dal post
        utente = post["owner"]
        testo = post["edge_media_to_caption"]["edges"]
        
        try:
            # Tenta di estrarre tutte le informazioni disponibili
            utile = {
                "descrizione": post["accessibility_caption"],
                "taggati": post["edge_media_to_tagged_user"]["edges"],
                "testo": testo,
                "location": post["location"],
                "musica": post["clips_music_attribution_info"],
                "nome": utente["full_name"]
            }
            listone.append(utile)
        except:
            # Se manca il campo musica, prova senza
            try:
                utile = {
                    "descrizione": post["accessibility_caption"],
                    "taggati": post["edge_media_to_tagged_user"]["edges"],
                    "testo": testo,
                    "location": post["location"],
                    "nome": utente["full_name"]
                }
                listone.append(utile)
            except:
                # Se manca anche la descrizione, salva solo i campi base
                utile = {
                    "taggati": post["edge_media_to_tagged_user"]["edges"],
                    "testo": testo,
                    "location": post["location"],
                    "nome": utente["full_name"]
                }
                listone.append(utile)
    
    # Salva tutti i metadata raccolti in info.json per questo account
    with open("{}/info.json".format(user),"w") as info:
        json.dump(listone, info)

# Chiude il file di log
cavia.close()
