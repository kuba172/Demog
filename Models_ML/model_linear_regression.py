from sklearn.experimental import enable_iterative_imputer
from sklearn.linear_model import LinearRegression
from sklearn.impute import IterativeImputer
from Models.data_storage_model import DataStorageModel
import pandas as pd
import os


def load_data(file_path):
    df = pd.read_csv(file_path, header=None, usecols=range(10))
    df.replace('-', 0, inplace=True)
    df.columns = ['wiek', 'ludzie', 'mezczyzni', 'kobiety', 'miasto_ludzie', 'miasto_mezczyzni', 'miasto_kobiety',
                  'wies_ludzie', 'wies_mezczyzni', 'wies_kobiety']

    imputer = IterativeImputer(max_iter=10, random_state=42)
    df.iloc[:, 1:] = imputer.fit_transform(df.iloc[:, 1:])

    return df.astype(int)


def build_model(data):
    X = data[['wiek']]
    y = data.drop(['wiek'], axis=1)
    model = LinearRegression()
    model.fit(X, y)
    return model


def generate_predictions(model, years, data_frames):
    all_predictions = []

    for i, year in enumerate(years):
        current_data = pd.concat(data_frames[:i + 1])

        X_train = current_data[['wiek']]
        y_train = current_data.drop(['wiek'], axis=1)

        model.fit(X_train, y_train)

        predictions = pd.DataFrame({'wiek': range(0, 71)})
        predicted_values = model.predict(predictions[['wiek']]).astype(int)

        all_predictions.append(pd.DataFrame(data=predicted_values, columns=y_train.columns))

    return all_predictions


def model(district_name, user_year):
    districtAndVoivodeship = str(district_name).split(", Woj. ")

    district = districtAndVoivodeship[0]
    voivodeship = districtAndVoivodeship[1]

    folder_path = f"Data/train_data/{voivodeship}/{district}/"

    years = range(2002, 2020)
    data_frames = []

    for year in years:
        file_path = folder_path + f'{year}.csv'
        data_frames.append(load_data(file_path))

    all_data = pd.concat(data_frames)

    model = build_model(all_data)

    prediction_years = range(2021, 2061)
    all_predictions = generate_predictions(model, prediction_years, data_frames)

    user_data = all_predictions[prediction_years.index(user_year)]
    user_data.insert(0, 'wiek', range(0, 71))

    key = f'{district_name}, rok {user_year}'
    DataStorageModel.add(key, user_data)

    return key


def start(district_name, year_from, year_to):
    for year in range(year_from, year_to + 1):
        model(district_name, year)