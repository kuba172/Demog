from sklearn.experimental import enable_iterative_imputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import IterativeImputer
from Models.data_storage_model import DataStorageModel
import pandas as pd
import os


# Funkcja do wczytywania danych z pliku .csv z imputacją brakujących wartości
def load_data(file_path):
    df = pd.read_csv(file_path, header=None, usecols=range(10))
    df.replace('-', 0, inplace=True)  # Zamiana '-' na 0
    df.columns = ['wiek', 'ludzie', 'mezczyzni', 'kobiety', 'miasto_ludzie', 'miasto_mezczyzni', 'miasto_kobiety',
                  'wies_ludzie', 'wies_mezczyzni', 'wies_kobiety']

    # Uzupełnienie brakujących wartości za pomocą IterativeImputer
    imputer = IterativeImputer(max_iter=10, random_state=42)
    df.iloc[:, 1:] = imputer.fit_transform(df.iloc[:, 1:])

    return df.astype(int)


# Funkcja do budowania modelu
def build_model(data):
    X = data[['wiek']]
    y = data.drop(['wiek'], axis=1)
    model = RandomForestRegressor(n_estimators=100, random_state=42, warm_start=True)
    model.fit(X, y)
    return model


# Funkcja do generowania predykcji dla zadanego roku
def generate_predictions(model, years, data_frames):
    all_predictions = []

    for i, year in enumerate(years):
        current_data = pd.concat(data_frames[:i + 1])  # Dane treningowe do bieżącego roku

        X_train = current_data[['wiek']]
        y_train = current_data.drop(['wiek'], axis=1)

        # Aktualizacja modelu
        model.n_estimators += 10  # Zwiększ liczbę drzew (dowolna wartość, można dostosować)
        model.fit(X_train, y_train)

        # Generowanie predykcji
        predictions = pd.DataFrame({'wiek': range(0, 71)})
        predicted_values = model.predict(predictions[['wiek']]).astype(int)

        # Dodanie predykcji do listy
        all_predictions.append(pd.DataFrame(data=predicted_values, columns=y_train.columns))

    return all_predictions


def model(district_name, user_year):
    # Ścieżka do folderu zawierającego pliki .csv
    folder_path = f"Data/train_data/{district_name}/"  # Ścieżke zmienić w zależności od tego gdzie są dane

    # Wczytanie danych z wszystkich plików
    years = range(2002, 2020)
    data_frames = []

    for year in years:
        file_path = folder_path + f'{year}.csv'
        data_frames.append(load_data(file_path))

    # Połączenie danych z różnych lat w jedną ramkę danych
    all_data = pd.concat(data_frames)

    # Budowa modelu na podstawie zebranych danych
    model = build_model(all_data)

    # Generowanie predykcji dla lat 2021-2060
    prediction_years = range(2021, 2061)
    all_predictions = generate_predictions(model, prediction_years, data_frames)

    # Pobranie wcześniej przygotowanej predykcji dla użytkownika
    user_data = all_predictions[prediction_years.index(user_year)]

    # Dodanie kolumny z wiekiem
    user_data.insert(0, 'wiek', range(0, 71))

    # Zapisanie wyników do Data Storage
    key = f'{district_name}_{user_year}'
    DataStorageModel.add(key, user_data)

    return key


def start(district_name, year_from, year_to):
    """
    Run a model to predict data for a selected district
    """
    for year in range(year_from, year_to + 1):
        model(district_name, year)
