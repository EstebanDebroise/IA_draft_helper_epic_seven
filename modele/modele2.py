import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten, Dropout
from sklearn.model_selection import train_test_split
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.preprocessing.sequence import pad_sequences



def build_model(input_shape=(10, 64)):
    model = Sequential([
        Flatten(input_shape=input_shape),
        Dense(16, activation='relu'),
        Dropout(0.3),
        Dense(16, activation='relu'),
        Dropout(0.2),
        Dense(16, activation='linear')  
    ])
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    return model



if __name__ == "__main__":
    # Charger les données préparées
    X = np.load("data/X.npy")

    X_inputs = []
    y_outputs = []

    for draft in X:
        for i in range(1, len(draft)):
            X_inputs.append(draft[:i])   # séquence de 1 à i éléments
            y_outputs.append(draft[i])   # prochain pick

    X_inputs = pad_sequences(X_inputs, maxlen=10, padding='pre', dtype='float32')  

    accuracies = []
    losses = []
    print(X_inputs.shape)
    print(len(y_outputs))


    # Split data
    y_outputs = np.array(y_outputs, dtype=np.float32)
    X_inputs = np.array(X_inputs, dtype=np.float32)

    X_train, X_val, y_train, y_val = train_test_split(X_inputs, y_outputs, test_size=0.2, random_state=i)
    print("X_train:", X_train.shape)
    print("y_train:", np.array(y_train).shape)
    print("type(y_train):", type(y_train))
    print("type(y_train[0]):", type(y_train[0]))


    model = build_model(input_shape=(X_inputs.shape[1], X_inputs.shape[2]))
    history = model.fit(X_train, y_train, epochs=30, batch_size=64, validation_data=(X_val, y_val), verbose=1)

    # Sauvegarde le modèle
    model.save("data/modele2.keras")




