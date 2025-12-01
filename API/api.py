from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
from gensim.models import Word2Vec
import numpy as np
import json
import random
from fastapi import FastAPI


def load_hero_names(json_file="heroes.json"):
    '''
    Charge les noms des héros à partir d'un fichier JSON.
    param json_file: chemin vers le fichier JSON contenant les noms des héros
    return: dictionnaire mappant les codes des héros à leurs noms
    '''
    with open(json_file, "r", encoding="utf-8") as f:
        hero_dict = json.load(f)
    return hero_dict

def get_hero_name(hero_code, hero_dict):
    '''
    récupère le nom du héros à partir de son code.
    param hero_code: code du héros
    param hero_dict: dictionnaire mappant les codes des héros à leurs noms
    return: nom du héros
    '''
    return hero_dict.get(hero_code, hero_code)

def transform_draft_to_vectors_padded(draft_sequence, word2vec_model, maxlen=10):
    '''
    Transforme une séquence de codes de héros en une séquence de vecteurs Word2Vec, puis la remplit pour atteindre une longueur fixe.
    param draft_sequence: liste des codes des héros dans le draft
    param word2vec_model: modèle Word2Vec pré-entraîné
    param maxlen: longueur maximale de la séquence après remplissage
    return: séquence de vecteurs remplie
    '''
    draft_vectors = [word2vec_model.wv[code] for code in draft_sequence]
    draft_padded = pad_sequences([draft_vectors], maxlen=maxlen, padding='pre', dtype='float32')
    return draft_padded

def choose_top_heroes(draaft_padded, model, word2vec_model, topn=5):
    '''
    Prédit le prochain héros à choisir en utilisant le modèle et retourne les héros les plus similaires.
    param draaft_padded: séquence de vecteurs remplie représentant le draft actuel
    param model: modèle Keras pré-entraîné pour la prédiction
    param word2vec_model: modèle Word2Vec pré-entraîné
    param topn: nombre de héros similaires à retourner
    return: liste des héros les plus similaires au vecteur prédit
    '''
    prediction = model.predict(draaft_padded)
    predicted_vector = prediction[0]
    closest_heroes = word2vec_model.wv.similar_by_vector(predicted_vector, topn=topn)
    return random.choices(closest_heroes, k=1)

app = FastAPI()

model = load_model("data/modele2.keras")
word2vec_model = Word2Vec.load("data/word2vec_16.model")
hero_dict = load_hero_names("data/heroes.json")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/next_pick/")
async def next_pick(draft: str):
    try:
        draft_sequence = draft.split(",")
    except Exception as e:
        return {"error": f"Invalid draft format: {str(e)}"}
    try:
        draft_padded = transform_draft_to_vectors_padded(draft_sequence, word2vec_model, maxlen=10)
    except KeyError as e:
        return {"error": f"Hero code not found in Word2Vec model: {str(e)}"}
    try:
        top_hero = choose_top_heroes(draft_padded, model, word2vec_model, topn=5)
    except Exception as e:
        return {"error": f"Error during prediction: {str(e)}"}
    try:
        hero_code, similarity = top_hero[0]
        hero_name = get_hero_name(hero_code, hero_dict)
    except Exception as e:
        return {"error": f"Error retrieving hero name: {str(e)}"}
    return {
        "predicted_hero_code": hero_code,
        "predicted_hero_name": hero_name,
        "similarity": float(similarity)
    }

@app.get("/get_name/")
async def get_name(hero_code: str):
    if(hero_code == ""):
        return {"error": "Hero code cannot be empty"}
    hero_name = get_hero_name(hero_code, hero_dict)
    return {"hero_code": hero_code, "hero_name": hero_name}

@app.get("/get_codes/")
async def get_codes(hero_name: str):
    codes = [code for code, name in hero_dict.items() if name.lower() == hero_name.lower()]
    if not codes:
        return {"error": f"No hero codes found for hero name: {hero_name}"}
    codes_str = ", ".join(codes)
    return {"hero_name": hero_name, "hero_codes": codes_str}