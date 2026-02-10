#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
scarica.py

Script utility per Instagram scraping e download massivo.
Converte ID→shortcode, pulisce Unicode, estrae metadata post, scansiona dataset
e scarica foto/video da profili usando ProfileLooter + login automatico.
'''

from instalooter.looters import PostLooter, ProfileLooter
import os
import json
import base64
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv()

DATASET_PATH = os.getenv('DATASET_PATH', './dataset/')
INSTAGRAM_USER = os.getenv('INSTAGRAM_USERNAME', '')
INSTAGRAM_PASS = os.getenv('INSTAGRAM_PASSWORD', '')


def id_to_shortcode(instagram_id):
    #Converte ID numerico Instagram in shortcode URL
    id_bytes = instagram_id.to_bytes(9, 'big')
    encoded = base64.b64encode(id_bytes, b'-_').decode()
    shortcode = encoded.replace('A', ' ').lstrip().replace(' ', 'A')
    return shortcode


def clean_unicode_string(text):
    #Pulisce stringhe con caratteri Unicode corrotti
    try:
        decoded_text = bytes(text, "unicode-escape").decode("unicode-escape")
    except:
        return text
    
    clean_text = ""
    for char in decoded_text:
        try:
            utf_char = char.encode("utf-8").decode("utf-8")
            clean_text += utf_char
        except:
            continue
    
    return clean_text


def extract_post_fields(post_data):
    #Estrae campi rilevanti dai dati JSON di un post
    chosen_keys = [
        "edge_media_to_tagged_user",
        "edge_media_to_caption",
        "location",
        "clips_music_attribution_info"
    ]
    
    extracted = {}
    for key in chosen_keys:
        if key in post_data:
            extracted[key] = post_data[key]
    
    return extracted


def scan_accounts_with_info():
    #Scansiona dataset e salva account con info.json in account.txt
    account_file = open(os.path.join(DATASET_PATH, "account.txt"), "a+")
    dirs = os.listdir(DATASET_PATH)
    os.chdir(DATASET_PATH)
    
    for item in dirs:
        if item == "log.txt":
            continue
        
        if os.path.isdir(item):
            if "info.json" in os.listdir(item):
                account_file.write(item + "\n")
    
    account_file.close()


def download_all_profiles():
    #Scarica foto e video da tutti i profili nel dataset
    dirs = os.listdir(DATASET_PATH)
    
    for accountname in dirs:
        # Salta file non-account
        if accountname in ["log.txt", "account.txt", "dataset_completo.json"]:
            continue
        
        if not os.path.isdir(os.path.join(DATASET_PATH, accountname)):
            continue
        
        print(f"Download di {accountname}")
        
        try:
            # Crea ProfileLooter
            looter = ProfileLooter(accountname)
            looter.login(INSTAGRAM_USER, INSTAGRAM_PASS)
            
            # Download foto e video
            download_path = os.path.join(DATASET_PATH, accountname)
            looter.download_pictures(download_path, media_count=10)
            looter.download_videos(download_path, media_count=5)
            
            print("Done..")
            
        except:
            continue


if __name__ == "__main__":
    # Scan account con info.json
    scan_accounts_with_info()
    
    # Download tutti i profili
    download_all_profiles()
