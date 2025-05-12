import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime

# Ładuje dane z Excela i przygotowuje je
def load_data_from_excel():
    df = pd.read_excel("Ceny_2024.xlsx", sheet_name="Arkusz1")
    df = df.rename(columns={
        "Unnamed: 0": "Data",
        "Unnamed: 3": "Godzina",
        "Fixing I - Kurs": "Cena [PLN/MWh]"
    })
    df = df[["Data", "Godzina", "Cena [PLN/MWh]"]]
    df.dropna(inplace=True)
    df["Data"] = pd.to_datetime(df["Data"])
    df["Godzina"] = df["Godzina"].astype(int)
    df["Cena [PLN/MWh]"] = df["Cena [PLN/MWh]"].astype(float)
    df["Dzien_tygodnia"] = df["Data"].dt.dayofweek
    df["Miesiac"] = df["Data"].dt.month
    return df

def prepare_input_dataframe_for_day(day, month):
    date = pd.Timestamp(datetime(datetime.today().year, month, day))
    df = pd.DataFrame({
        "Data": [date] * 24,
        "Godzina": list(range(24)),
        "Dzien_tygodnia": [date.dayofweek] * 24,
        "Miesiac": [month] * 24
    })
    return df

def train_model(df_full):
    df = pd.read_excel("Ceny_2024.xlsx", sheet_name="Arkusz1", usecols=["Data", "Godzina", "Cena [PLN/MWh]"])
    df["Data"] = pd.to_datetime(df["Data"])
    df["Godzina"] = pd.to_numeric(df["Godzina"], errors="coerce")
    df["Cena [PLN/MWh]"] = pd.to_numeric(df["Cena [PLN/MWh]"], errors="coerce")
    df.dropna(inplace=True)
    df["Dzien_tygodnia"] = df["Data"].dt.dayofweek
    df["Miesiac"] = df["Data"].dt.month

    X = df[["Godzina", "Dzien_tygodnia", "Miesiac"]]
    y = df["Cena [PLN/MWh]"]
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model


# Trenuje model na podstawie całych danych
def train_model(df):
    X = df[["Godzina", "Dzien_tygodnia", "Miesiac"]]
    y = df["Cena [PLN/MWh]"]
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

# Prognoza pojedynczej godziny
def predict_price(hour, day, month, model):
    day_of_week = pd.Timestamp(year=2025, month=month, day=day).dayofweek
    prediction = model.predict([[hour, day_of_week, month]])
    return round(prediction[0], 2)

# Prognoza dla całej doby
def predict_all_hours(df, model):
    results = []
    for hour in range(24):
        prediction = model.predict([[hour, df["Dzien_tygodnia"].iloc[-1], df["Miesiac"].iloc[-1]]])
        results.append({
            "Godzina": hour,
            "Prognozowana cena": round(prediction[0], 2)
        })
    return results



def prepare_input_dataframe_for_day(day, month):
    try:
        date = datetime(datetime.today().year, month, day)
        df = pd.DataFrame({
            "Data": [date for _ in range(24)],
            "Godzina": list(range(24)),
            "Dzien_tygodnia": [date.weekday()] * 24,
            "Miesiac": [month] * 24
        })
        return df
    except Exception as e:
        raise ValueError(f"Nieprawidłowa data: {e}")
