import pandas as pd
import numpy as np
import requests
import os
import holidays
import json
from datetime import datetime, timedelta
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import mean_squared_error
import xgboost as xgb
from app.models.xgb_model import prepare_training_features


def fetch_pse_data(dates):
    data_frames = []
    for date in dates:
        url = f"https://api.raporty.pse.pl/api/rce-pln?$filter=business_date eq '{date}'"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json().get('value', [])
                seen_hours = set()
                data_list = []
                for item in data:
                    if 'udtczas' in item and 'rce_pln' in item:
                        hour = int(item['udtczas'][-8:-6])
                        if hour not in seen_hours:
                            seen_hours.add(hour)
                            fixing = float(item['rce_pln'])
                            data_list.append({
                                "Data": date,
                                "Hour": hour,
                                "Fixing I - Kurs": fixing,
                                "Fixing II - Kurs": fixing
                            })
                if data_list:
                    data_frames.append(pd.DataFrame(data_list))
        except Exception as e:
            print(f"Error fetching API data for {date}: {e}")
    if not data_frames:
        return pd.DataFrame(columns=["Data", "Hour", "Fixing I - Kurs", "Fixing II - Kurs"])

    return pd.concat(data_frames, ignore_index=True) if data_frames else pd.DataFrame(columns=[
        "Data", "Hour", "Fixing I - Kurs", "Fixing II - Kurs"
    ])



def fetch_weather_forecast(target_date, lat=52.23, lon=21.01):
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&hourly=temperature_2m,windspeed_10m,cloudcover"
        f"&timezone=Europe%2FWarsaw&start_date={target_date}&end_date={target_date}"
    )
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json().get("hourly", {})
            temps = data.get("temperature_2m", [])
            winds = data.get("windspeed_10m", [])
            clouds = data.get("cloudcover", [])
            return {
                h: {
                    "Temp": temps[h] if h < len(temps) else np.nan,
                    "wind": winds[h] if h < len(winds) else np.nan,
                    "cloud": clouds[h] if h < len(clouds) else np.nan,
                }
                for h in range(24)
            }
    except Exception as e:
        print(f"Weather API error: {e}")
    return {}

def fetch_actual_prices(date_str):
    url = f"https://api.raporty.pse.pl/api/rce-pln?$filter=business_date eq '{date_str}'"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json().get('value', [])
            result = {}
            for item in data:
                if 'udtczas' in item and 'rce_pln' in item:
                    hour = int(item['udtczas'][-8:-6])
                    kurs = float(item['rce_pln'])
                    result[hour] = {"fix_i": kurs, "fix_ii": kurs}
            return result
    except Exception as e:
        print(f"[fetch_actual_prices] Błąd pobierania: {e}")
    return {}


def fetch_pse_load_forecast(target_date):
    url = f"https://api.raporty.pse.pl/api/daily-load-forecast?$filter=business_date eq '{target_date}'"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json().get("value", [])
            forecast = {}
            for item in data:
                czas = item.get("udtczas", "")
                load = item.get("forecast_mw", None)
                if czas.endswith(":00:00") and load is not None:
                    hour = int(czas[-8:-6])
                    forecast[hour] = float(load)
            return forecast
    except Exception as e:
        print(f"Load forecast API error: {e}")
    return {}


def prepare_training_features(df):
    df = df.copy()
    df["Day of Week"] = df["Data"].dt.weekday
    df["Month"] = df["Data"].dt.month
    df["is_weekend"] = df["Day of Week"].isin([5, 6]).astype(int)
    df["is_holiday"] = df["Data"].isin(holidays.CountryHoliday("PL")).astype(int)
    df = df.sort_values(["Data", "Hour"])
    df["Cena_t-1"] = df["Fixing I - Kurs"].shift(1)
    df["Cena_t-24"] = df["Fixing I - Kurs"].shift(24)
    df = df.dropna()
    df["time_of_day"] = df["Hour"].apply(lambda h: 0 if h < 6 else 1 if h < 12 else 2 if h < 18 else 3)
    for col in ["Forecasted Load", "Temp", "wind", "cloud"]:
        if col not in df.columns:
            df[col] = 0.0

    feature_cols = [
        "Hour", "Day of Week", "Month", "is_weekend", "is_holiday",
        "time_of_day", "Cena_t-1", "Cena_t-24", "Forecasted Load",
        "Temp", "wind", "cloud"
    ]
    return df[feature_cols], df["Fixing I - Kurs"], df["Fixing II - Kurs"]


def train_hourly_models(df, target_col):
    models = {}
    for hour in range(24):
        df_hour = df[df["Hour"] == hour]
        X, y1, y2 = prepare_training_features(df_hour)
        y = y1 if target_col == "Fixing I - Kurs" else y2
        model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
        model.fit(X, y)
        models[hour] = model
    return models


def predict_day(date_str):
    date = datetime.strptime(date_str, "%Y-%m-%d").date()
    start_excel = date - timedelta(days=365+90)
    end_excel = date - timedelta(days=365+1)
    excel_dates = pd.date_range(start=start_excel, end=end_excel).date
    api_dates = pd.date_range(end=date - timedelta(days=1), periods=8).strftime('%Y-%m-%d').tolist()

    df_excel = pd.read_excel("Ceny_2024.xlsx")
    df_excel = df_excel[df_excel["Kod daty"].notna()]
    df_excel["Kod daty"] = pd.to_numeric(df_excel["Kod daty"], errors="coerce").astype(int)
    df_excel["Fixing I - Kurs"] = pd.to_numeric(df_excel["Fixing I - Kurs"], errors="coerce")
    df_excel["Fixing II - Kurs"] = pd.to_numeric(df_excel["Fixing II - Kurs"], errors="coerce")
    df_excel["Data"] = pd.to_datetime(df_excel["Kod daty"].astype(str).str[:8], format="%Y%m%d")
    df_excel["Hour"] = df_excel["Kod daty"].astype(str).str[8:].astype(int)
    df_excel = df_excel[df_excel["Data"].dt.date.isin(excel_dates)]

    df_api = fetch_pse_data(api_dates)
    combined = pd.concat([df_excel, df_api], ignore_index=True)
    required = ["Fixing I - Kurs", "Fixing II - Kurs"]
    for col in required:
        if col not in combined.columns:
            combined[col] = np.nan

    combined["Data"] = pd.to_datetime(combined["Data"], errors="coerce")  # 👈 TO DODAJ


    forecast_load = fetch_pse_load_forecast(date_str)
    forecast_weather = fetch_weather_forecast(date_str)

    combined["Forecasted Load"] = combined["Hour"].apply(lambda h: forecast_load.get(h, 18000.0))
    combined["Temp"] = combined["Hour"].apply(lambda h: forecast_weather.get(h, {}).get("Temp", 15.0))
    combined["wind"] = combined["Hour"].apply(lambda h: forecast_weather.get(h, {}).get("wind", 5.0))
    combined["cloud"] = combined["Hour"].apply(lambda h: forecast_weather.get(h, {}).get("cloud", 50.0))

    models_i = train_hourly_models(combined, "Fixing I - Kurs")
    models_ii = train_hourly_models(combined, "Fixing II - Kurs")

    tomorrow_data = pd.DataFrame({
        "Hour": list(range(24)),
        "Data": pd.date_range(start=date_str, periods=24, freq='H')
    })
    tomorrow_data["Day of Week"] = tomorrow_data["Data"].dt.weekday
    tomorrow_data["Month"] = tomorrow_data["Data"].dt.month
    tomorrow_data["is_weekend"] = tomorrow_data["Day of Week"].isin([5, 6]).astype(int)
    tomorrow_data["is_holiday"] = tomorrow_data["Data"].dt.date.isin(holidays.CountryHoliday("PL")).astype(int)
    tomorrow_data["time_of_day"] = tomorrow_data["Hour"].apply(lambda h: 0 if h < 6 else 1 if h < 12 else 2 if h < 18 else 3)
    if "Fixing I - Kurs" in combined.columns and combined["Fixing I - Kurs"].notna().any():
        avg_price = combined["Fixing I - Kurs"].mean()
    else:
        avg_price = 350.0  # domyślna cena, fallback
    tomorrow_data["Cena_t-1"] = avg_price
    tomorrow_data["Cena_t-24"] = avg_price
    tomorrow_data["Forecasted Load"] = tomorrow_data["Hour"].apply(lambda h: forecast_load.get(h, 18000.0))
    tomorrow_data["Temp"] = tomorrow_data["Hour"].apply(lambda h: forecast_weather.get(h, {}).get("Temp", 15.0))
    tomorrow_data["wind"] = tomorrow_data["Hour"].apply(lambda h: forecast_weather.get(h, {}).get("wind", 5.0))
    tomorrow_data["cloud"] = tomorrow_data["Hour"].apply(lambda h: forecast_weather.get(h, {}).get("cloud", 50.0))

    features, _, _ =prepare_training_features(tomorrow_data)

    preds_i = [models_i[h].predict([features.iloc[h]])[0] if h in models_i else np.nan for h in range(24)]
    preds_ii = [models_ii[h].predict([features.iloc[h]])[0] if h in models_ii else np.nan for h in range(24)]

    return pd.DataFrame({
        "Hour": list(range(24)),
        "Fixing I": np.round(preds_i, 2),
        "Fixing II": np.round(preds_ii, 2)
    })