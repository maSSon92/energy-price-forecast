import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
import os


def evaluate_models(df: pd.DataFrame):
    """
    Trenuje kilka modeli ML i zwraca porównanie metryk (MAE, RMSE, R2).
    Dodatkowo zapisuje wykres MAE jako PNG.
    """
    results = []

    # Przygotuj dane wejściowe
    df = df.copy()
    df = df.dropna()
    if not all(col in df.columns for col in ["Godzina", "Dzien_tygodnia", "Miesiac", "Cena [PLN/MWh]"]):
        raise ValueError("Brak wymaganych kolumn w danych.")

    X = df[["Godzina", "Dzien_tygodnia", "Miesiac"]]
    y = df["Cena [PLN/MWh]"]

    models = {
        "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
        "XGBoost": XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42),
        "Linear Regression": LinearRegression()
    }

    maes = []
    labels = []

    for name, model in models.items():
        model.fit(X, y)
        preds = model.predict(X)
        mae = mean_absolute_error(y, preds)
        rmse = mean_squared_error(y, preds, squared=False)
        r2 = r2_score(y, preds)
        results.append({
            "Model": name,
            "MAE": round(mae, 2),
            "RMSE": round(rmse, 2),
            "R2": round(r2, 3)
        })
        maes.append(mae)
        labels.append(name)

    # Zapisz wykres MAE jako PNG
    os.makedirs("app/static/exports", exist_ok=True)
    plt.figure(figsize=(8, 5))
    bars = plt.bar(labels, maes, color=["#007bff", "#28a745", "#ffc107"])
    plt.title("Porównanie MAE modeli")
    plt.ylabel("MAE")
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + 0.5, f"{yval:.2f}", ha='center', va='bottom')
    plt.tight_layout()
    plot_path = "app/static/exports/porownanie_mae.png"
    plt.savefig(plot_path)
    plt.close()

    return pd.DataFrame(results)