import pandas as pd
import numpy as np
import xgboost as xgb
import holidays
from datetime import datetime, timedelta
from app.models.helpers.api_helpers import fetch_pse_load_forecast, fetch_weather_forecast
from app.models.helpers.training import train_hourly_models
from app.models.helpers.feature_engineering import prepare_features



def prepare_features(df):
    df = df.copy()
    df["Day of Week"] = df["Data"].dt.weekday
    df["Month"] = df["Data"].dt.month
    df["is_weekend"] = df["Day of Week"].isin([5, 6]).astype(int)
    df["is_holiday"] = df["Data"].isin(holidays.CountryHoliday("PL")).astype(int)
    df = df.sort_values(["Data", "Hour"])
    df["Cena_t-1"] = df["Fixing I - Kurs"].shift(1)
    df["Cena_t-24"] = df["Fixing I - Kurs"].shift(24)
    df["time_of_day"] = df["Hour"].apply(lambda h: 0 if h < 6 else 1 if h < 12 else 2 if h < 18 else 3)
    for col in ["Forecasted Load", "temp", "wind", "cloud"]:
        if col not in df.columns:
            df[col] = 0.0
    df = df.dropna()
    feature_cols = [
        "Hour", "Day of Week", "Month", "is_weekend", "is_holiday",
        "time_of_day", "Cena_t-1", "Cena_t-24", "Forecasted Load",
        "temp", "wind", "cloud"
    ]
    return df[feature_cols], df["Fixing I - Kurs"], df["Fixing II - Kurs"]


def train_hourly_models(df, target_col):
    models = {}
    for hour in range(24):
        df_hour = df[df["Hour"] == hour]
        if df_hour.empty:
            continue
        X, y1, y2 = prepare_features(df_hour)
        y = y1 if target_col == "Fixing I - Kurs" else y2
        model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
        model.fit(X, y)
        models[hour] = model
    return models


def predict_all_hours(df):
    target_date = df["Data"].iloc[0].date().strftime("%Y-%m-%d")
    avg_price = df["Fixing I - Kurs"].mean()
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

    features, _, _ = prepare_features(future_df)
    models_i = train_hourly_models(df, "Fixing I - Kurs")
    models_ii = train_hourly_models(df, "Fixing II - Kurs")

    preds_i = [models_i[h].predict([features.iloc[h]])[0] if h in models_i else np.nan for h in hour_list]
    preds_ii = [models_ii[h].predict([features.iloc[h]])[0] if h in models_ii else np.nan for h in hour_list]

    return [
        {"Godzina": h, "Prognozowana cena": round((preds_i[h] + preds_ii[h]) / 2, 2)}
        for h in hour_list
    ]


def load_data_from_excel():
    df = pd.read_excel("Ceny_2024.xlsx")
    df = df[df["Kod daty"].notna()]
    df["Kod daty"] = pd.to_numeric(df["Kod daty"], errors="coerce").astype(int)
    df["Fixing I - Kurs"] = pd.to_numeric(df["Fixing I - Kurs"], errors="coerce")
    df["Fixing II - Kurs"] = pd.to_numeric(df["Fixing II - Kurs"], errors="coerce")
    df["Data"] = pd.to_datetime(df["Kod daty"].astype(str).str[:8], format="%Y%m%d")
    df["Hour"] = df["Kod daty"].astype(str).str[8:].astype(int)
    return df


def train_model(df):
    return None


def prepare_input_dataframe_for_day(day, month):
    date = datetime(datetime.today().year, month, day)
    df = pd.DataFrame({
        "Data": [date] * 24,
        "Hour": list(range(24))
    })
    return df


def predict_price(hour, day, month, model=None):
    return 0.0
