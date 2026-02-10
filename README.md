# Social Mapper – Instagram Privacy & OSINT Project

Questo progetto è una tesina per il corso di **Fondamenti di Data Science e Machine Learning** e utilizza ed estende lo strumento open source **Social Mapper** per analizzare quanto gli utenti di Instagram condividano informazioni sensibili, fino a ricostruire (in modo dimostrativo) un **codice fiscale** a partire dai dati pubblici di un profilo.

L’obiettivo non è sviluppare Social Mapper, ma **sfruttarlo e ampliarlo** per mostrare in pratica i rischi di privacy, social engineering e profilazione mirata.

## Obiettivi

- Effettuare **crawling automatico** di profili Instagram partendo da una lista di nomi.
- Costruire un **dataset strutturato** di:
  - foto, video, didascalie, bio, hashtag, geolocalizzazioni, musica.
- Applicare tecniche di:
  - **NLP** (Named Entity Recognition),
  - **object detection** (YOLOv5),
  - analisi statistica
  per valutare quante informazioni sensibili vengono esposte.
- Dimostrare, su un caso concreto, come arrivare a stimare il **codice fiscale** di un utente (nome, cognome, luogo e data di nascita) a partire dai dati pubblici.

## Architettura generale

Il progetto si appoggia a:

- **Social Mapper** (Jacob Wilkin) per la ricerca di profili su vari social.
- Una serie di **script Python** aggiuntivi che estendono e automatizzano:
  - crawling Instagram,
  - download media,
  - estrazione di testo/metadati,
  - analisi NLP e computer vision,
  - aggregazione dei risultati in un dataset unico.

Pipeline ad alto livello:

1. **Input nomi** (CSV).
2. Social Mapper (esteso) + Instalooter → download di profili e media Instagram.
3. Script di supporto → estrazione di bio, didascalie, location, hashtag, musica.
4. YOLOv5 → riconoscimento oggetti nei media.
5. CoreNLP (via pycorenlp) → NER su bio e descrizioni.
6. Aggregazione in JSON (`general.json` per account, `dataset_completo.json` globale).
7. Analisi statistica + caso di studio per ricostruire un codice fiscale.

## Estensioni a Social Mapper

Rispetto al progetto originale, sono state introdotte/aggiornate le seguenti funzionalità:

- **Fix login Instagram**:
  - riscrittura parziale del metodo `doLogin` per adattarsi ai cambi di HTML e ai nuovi controlli cookie di Instagram (altrimenti la homepage non si caricava).

- **Opzione `csv-nophoto`**:
  - nuova modalità che permette di fare crawling partendo **solo da un CSV di nomi e cognomi**, senza foto di riferimento.
  - utile per costruire rapidamente un dataset di profili Instagram collegati a una lista di nomi.

- **Metodo `getInstaProfilePhotos`**:
  - automatizza il download di ~15 media (foto + video) per account, usando **Instalooter**.
  - genera, per ogni profilo, una cartella con i post da analizzare.

Oltre a queste modifiche integrate in Social Mapper, sono stati creati script esterni dedicati a funzioni specifiche di crawling/estrazione (non integrati nel core del tool).

## Script principali

### Crawling e metadati

- `bio.py`  
  Scarica la **bio** (descrizione del profilo) degli utenti, minimizzando il rischio di ban degli account di crawling.

- `didascalia.py`  
  Dato il media (via `mediaid`), ricostruisce il link al post e scarica:
  - luogo,
  - utenti taggati,
  - descrizione,
  - hashtag,
  - didascalia,
  producendo un file `info.json` per account.

- `music_recognizer.py`  
  - Estrae l’audio dai video (con **MoviePy**).
  - Invia l’audio alle REST API di **audd.io** per la **music recognition**.
  - Produce `music_info.json` con le tracce rilevate.

### Object detection e interessi

- `generayolo.py` + `leggiimmagini.py`  
  - Applicano **YOLOv5** a foto e video.
  - Producono `dentrofoto.json` con lista e conteggio degli oggetti riconosciuti per media, con soglie di confidenza:
    - ≥55% per i video,
    - ≥45% per le immagini.

- `interessi.py` + `normalizza.py`  
  - Aggregano gli oggetti più frequenti e li mappano su **categorie di interesse** (scala 1–5), ad esempio:
    - `sociale`, `kitchen`, `classy`, `sport`, `gamer`, `tvaddicted`,  
      `safefood`, `animali`, `junkfood`, `road`, `travel`.

### NLP e aggregazione dataset

- `bio_nlp.py`  
  - Applica NER (via **pycorenlp / Stanford CoreNLP**) alle **bio**.
  - Annotators usati:
    - `ssplit`, `ner`, `depparse`.
  - Estrae entità come: `person`, `location`, `organization`, `number`, `date`, `email`, `url`, `city`, `state or province`, `country`, `nationality`, `religion`, `title`, `ideology`.

- `descrizione_nlp.py`  
  - Stessa logica ma applicata alle **didascalie** (descrizioni dei post).
  - Produce file `nlp.json` e `didascalia_nlp.json`.

- `merge_json.py`  
  - Unisce tutti i JSON per singolo account in un file `general.json`.

- `generate_complete_dataset.py`  
  - Unisce tutti i `general.json` in un unico `dataset_completo.json`.

## Dataset

Caratteristiche principali:

- **108 account Instagram**, divisi equamente tra maschi e femmine.
- Per ogni nome:
  - fino a 5 profili associati,
  - fino a 10 post foto + 5 post video per profilo (ma i carousel possono aumentare il numero reale di media).
- Per ogni account, `general.json` raccoglie:
  - `username`
  - `info_name`
  - `info_locations`
  - `music` (da info.json + audd.io)
  - `didascalia_location`
  - `didascalia_hashtags`
  - tutte le entità NER:
    - `nlp_name`, `nlp_location`, `nlp_organization`, `nlp_number`, `nlp_date`, `nlp_email`, `nlp_url`, `nlp_city`, `nlp_state_or_province`, `nlp_country`, `nlp_nationality`, `nlp_religion`, `nlp_titles`, `nlp_ideology`
    - e le corrispondenti `didascalia_nlp_*`
  - gli **interessi** per categoria (da 1 a 5).

`dataset_completo.json` è l’aggregazione di tutti i `general.json` ed è la base per l’analisi statistica.

## Analisi e grafici (privacy & social engineering)

Dai dati raccolti sono stati generati diversi grafici (nel report PDF) che mostrano:

- **Bio e didascalie**:
  - frequenza di:
    - lavoro,
    - organizzazione (luogo di lavoro),
    - città / stato / paese,
    - email,
    - URL,
    - religione, nazionalità, ideologia.
  - Risultato: molti utenti pubblicano lavoro, organizzazione, luogo; quasi nessuno religione/ideologia.

- **Musica**:
  - 36 utenti con canzoni identificabili.
  - Canzoni più condivise (es. “Can’t Help Falling in Love”, “1999”, “Runaway”, ecc.).
  - Artisti più presenti, con mix tra classici e brani recenti.

- **Hashtag**:
  - hashtag più usati (es. `makeupartist`, `love`, `follow`, fitness, moda, ecc.).
  - indicano lavori, passioni, stile di vita.

- **Date**:
  - pochissimi utenti pubblicano date complete (giorno/mese/anno),
  - alcune date generiche (now, tomorrow, ecc.) potenzialmente precisabili con analisi contestuale.

- **Numeri in bio**:
  - rilevato almeno un numero telefonico,
  - età pubblicata in chiaro da alcuni utenti.

- **Nomi nella bio**:
  - confrontando testo bio con un file di nomi (`Nomi.csv`) tramite **fuzzywuzzy**:
    - molti utenti inseriscono nome e cognome completi,
    - pochi non inseriscono alcun nome.

- **Geolocalizzazione (geotag)**:
  - ~73 utenti su 108 usano il geotagging nei post,
  - alcuni indicano posizione in bio o didascalia,
  - in totale, 77 utenti su 108 danno qualche indicazione sul luogo.

Tutti questi elementi mostrano quanto sia facile ricostruire profili molto ricchi di informazioni, utili sia per marketing mirato sia per attacchi di social engineering.

## Caso di studio: ricostruzione del codice fiscale

Il progetto include un esempio concreto (utente italiano dal dataset):

1. **Nome e cognome**: estratti da `dataset_completo.json` (es. da campi `info_name` / entità NER).
2. **Genere**: dedotto dal nome (euristica).
3. **Luogo di nascita**:
   - analisi dei post geotaggati → molti post in un’area specifica (es. cittadina in Sardegna).
   - inferenza: probabile luogo di provenienza.
   - uso di Google per associare ospedale/capoluogo di provincia → città di nascita (es. Cagliari).
4. **Data di nascita**:
   - nessuna informazione negli ultimi 15 post → ipotesi di attaccante che scarica *tutto* il profilo.
   - NER trova un numero (es. 26) in una didascalia.
   - interpretato come età in quel momento, incrociata con la data del post → anno di nascita stimato.
5. **Calcolo del codice fiscale**:
   - con nome, cognome, sesso, luogo e data nascita → uso di un calcolatore di CF online.
   - ottenimento di un codice fiscale altamente probabile.

Questo esempio dimostra come combinando informazioni apparentemente innocue (bio, geotag, età, nome, luogo) si possa arrivare a un’identità quasi completa.

## Tecnologie principali

- **Python** (script di crawling, parsing, aggregazione, analisi).
- **Social Mapper** (ricerca profili cross‑social, esteso per CSV-only e Instagram).
- **Selenium / Instalooter** (supporto al crawling Instagram).
- **Stanford CoreNLP** + `pycorenlp` (NER e annotazioni NLP).
- **YOLOv5** (object detection nei media).
- **MoviePy** (estrazione audio dai video).
- **fuzzywuzzy** (similarità stringhe per confrontare nomi).
- **audd.io** (music recognition via REST API).

## Stato del progetto e licenza

Questo progetto nasce come **tesina universitaria** e ha finalità esclusivamente **didattiche** e di **sensibilizzazione sulla privacy**.

- Social Mapper è un progetto **open source di terzi** (Jacob Wilkin): questo repository non ne è autore ma lo **estende** e lo usa come base.
- Al momento **non è definita alcuna licenza esplicita** per il materiale di questa tesina: tutti i diritti sui testi, script e analisi sono riservati agli autori.
