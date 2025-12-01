import json
import pandas as pd
import numpy as np
from gensim.models import Word2Vec
from pathlib import Path


def load_and_prepare_data(json_path: str):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    df = pd.DataFrame(columns=["pick_1", "pick_2", "pick_3", "pick_4", "pick_5", "pick_6", "pick_7", "pick_8", "pick_9", "pick_10", "result"])
    for match in data:
        if match["first_pick"] == "my_team":
            newListe = []
            # picks alternés selon l'ordre de draft
            order = [
                ("my_team", 0), ("enemy_team", 0),
                ("enemy_team", 1), ("my_team", 1),
                ("my_team", 2), ("enemy_team", 2),
                ("enemy_team", 3), ("my_team", 3),
                ("my_team", 4), ("enemy_team", 4)
            ]
            for team, idx in order:
                newListe.append(match[team][idx]["hero_code"])
            
            newListe.append(1 if match["winner"] == match["first_pick"] else 0)
            df.loc[len(df)] = newListe
        else:
            newListe = []
            order = [
                ("enemy_team", 0), ("my_team", 0),
                ("my_team", 1), ("enemy_team", 1),
                ("enemy_team", 2), ("my_team", 2),
                ("my_team", 3), ("enemy_team", 3),
                ("enemy_team", 4), ("my_team", 4)
            ]
            for team, idx in order:
                newListe.append(match[team][idx]["hero_code"])
            
            newListe.append(1 if match["winner"] == match["first_pick"] else 0)
            df.loc[len(df)] = newListe
    print(f"Data loaded with {len(df)} matches.")
    print(df.head())
    return df


def encode(df, vector_size=50):
    # 1. Garder uniquement les colonnes pick_*
    picks = df.drop(columns=["result"])

    # 2. Transformer chaque ligne en liste de picks
    sentences = picks.values.tolist()

    # 3. Entraîner le modèle Word2Vec sur l'ensemble des picks
    model = Word2Vec(
        sentences,
        vector_size=vector_size,
        window=5,
        min_count=1,
        sg=1,
        epochs=20
    )

    # 4. Transformer chaque pick en vecteur
    def get_pick_vectors(row):
        vectors = []
        for p in row:
            if p in model.wv:
                vectors.append(model.wv[p])
            else:
                vectors.append(np.zeros(vector_size))
        return np.array(vectors)  # shape (10, vector_size)

    # 5. Appliquer à tout le DataFrame
    X = np.stack(picks.apply(get_pick_vectors, axis=1).values)
    y = df["result"].values  # ou autre cible selon ton objectif

    return X, y, model

if __name__ == "__main__":
    print('-'*10)
    print(Path(__file__))
    print('-'*10)
    df = load_and_prepare_data("data/battle_data.json")

    X, y, model = encode(df, vector_size=16)

    print(X.shape)  # (9490, 10, 64)
    print(X[0])    # Premier match encodé
    print(y)       # Labels

    # Sauvegarde X et y
    np.save("data/X.npy", X)
    np.save("data/y.npy", y)

    # Sauvegarde le modèle Word2Vec
    model.save("data/word2vec_16.model")