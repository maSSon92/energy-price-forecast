import pandas as pd
import numpy as np
import xgboost as xgb
import holidays
from datetime import datetime, timedelta
from app.models.helpers.api_helpers import fetch_pse_load_forecast, fetch_weather_forecast
from app.models.helpers.training import train_hourly_models
from app.models.helpers.feature_engineering import prepare_features


def predict_all_hours(df, day=None, month=None):
    if df.empty or "Data" not in df.columns:
        print("⚠️ Brak danych w df – używam daty dzisiejszej.")
        target_date = datetime.now().strftime("%Y-%m-%d")
    else:
        target_date = datetime(datetime.today().year, month, day).strftime("%Y-%m-%d") if day and month else df["Data"].iloc[0].date().strftime("%Y-%m-%d")

    avg_price = df["Fixing I - Kurs"].mean() if "Fixing I - Kurs" in df.columns else 350.0
    hour_list = list(range(24))
    load_forecast = fetch_pse_load_forecast(target_date)
    weather_forecast = fetch_weather_forecast(target_date)

    future_df = pd.DataFrame({
        "Hour": hour_list,
        "Data": pd.date_range(start=target_date, periods=24, freq='H')
    })
    future_df["Day of Week"] = future_df["Data"].dt.weekday
    future_df["Month"] = future_df["Data"].dt.month
    future_df["is_weekend"] = future_df["Day of Week"].isin([5, 6]).astype(int)
    future_df["is_holiday"] = future_df["Data"].dt.date.isin(holidays.CountryHoliday("PL")).astype(int)
    future_df["time_of_day"] = future_df["Hour"].apply(lambda h: 0 if h < 6 else 1 if h < 12 else 2 if h < 18 else 3)
    future_df["Cena_t-1"] = avg_price
    future_df["Cena_t-24"] = avg_price
    future_df["Forecasted Load"] = future_df["Hour"].apply(lambda h: load_forecast.get(h, 18000.0))
    future_df["temp"] = future_df["Hour"].apply(lambda h: weather_forecast.get(h, {}).get("temp", 15.0))
    future_df["wind"] = future_df["Hour"].apply(lambda h: weather_forecast.get(h, {}).get("wind", 5.0))
    future_df["cloud"] = future_df["Hour"].apply(lambda h: weather_forecast.get(h, {}).get("cloud", 50.0))

    features, y1_dummy, y2_dummy = prepare_features(future_df)

    print(f"🎯 Data do prognozy: {target_date}")
    print(f"📉 Średnia cena Fixing I (avg_price): {avg_price}")
    print(f"🧠 Rozpoczynam trening modeli...")

    models_i = train_hourly_models(df, "Fixing I - Kurs")
    models_ii = train_hourly_models(df, "Fixing II - Kurs")

    print(f"✅ Modele Fixing I: {len(models_i)} / Fixing II: {len(models_ii)}")

    if not models_i or not models_ii:
        print("❌ Modele nie zostały utworzone – brak danych historycznych.")
        return []

    if len(features) < 24:
        print(f"⚠️ Za mało wierszy w features: {len(features)} – przerywam predykcję.")
        return []

    preds_i = [float(models_i[h].predict([features.iloc[h]])[0]) if h in models_i else 0.0 for h in hour_list]
    preds_ii = [float(models_ii[h].predict([features.iloc[h]])[0]) if h in models_ii else 0.0 for h in hour_list]
    return [
        {"Godzina": h, "Prognozowana cena": round((preds_i[h] + preds_ii[h]) / 2, 2)}
        for h in hour_list
    ]


def load_data_from_excel():
    try:
        df = pd.read_excel("Ceny_2024.xlsx", sheet_name="Arkusz1")

        # Usuń pierwszy wiersz, jeśli cały pusty
        df = df.dropna(how='all')

        # Upewnij się, że kolumny istnieją
        if "Kod daty" not in df.columns or "Fixing I - Kurs" not in df.columns:
            print("❌ Plik Excel nie zawiera wymaganych kolumn.")
            return pd.DataFrame()

        # Konwersje
        df["Kod daty"] = pd.to_numeric(df["Kod daty"], errors="coerce")
        df["Fixing I - Kurs"] = pd.to_numeric(df["Fixing I - Kurs"], errors="coerce")
        df["Fixing II - Kurs"] = pd.to_numeric(df["Fixing II - Kurs"], errors="coerce")

        # Usuń niepełne wiersze
        df = df.dropna(subset=["Kod daty", "Fixing I - Kurs", "Fixing II - Kurs"])

        df["Kod daty"] = df["Kod daty"].astype(int)
        df["Data"] = pd.to_datetime(df["Kod daty"].astype(str).str[:8], format="%Y%m%d")
        df["Hour"] = df["Kod daty"].astype(str).str[8:].astype(int)

        print("✅ Wczytano dane z Excela:", df.shape)
        print(df.head())

        return df

    except Exception as e:
        print(f"❌ Błąd przy wczytywaniu danych z Excela: {e}")
        return pd.DataFrame()


def train_model(df):
    return None

def prepare_input_dataframe_for_day(day, month):
    df = load_data_from_excel()
    target_date = datetime(datetime.today().year, month, day)
    target_2024 = target_date.replace(year=2024)
    start = target_2024 - timedelta(days=7)
    end = target_2024

    df_filtered = df[(df["Data"] >= start) & (df["Data"] <= end)].copy()

    if df_filtered.empty:
        print(f"❌ Brak danych historycznych dla zakresu {start.date()} – {end.date()}")
    else:
        print(f"✅ Zakres danych historycznych: {start.date()} – {end.date()} ({len(df_filtered)} wierszy)")

    return df_filtered


def predict_price(hour, day, month, model=None):
    return 0.0
