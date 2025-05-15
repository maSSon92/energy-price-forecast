import pandas as pd
import os
from datetime import datetime, timedelta
from app.models.database import update_actual_price

def compare_predictions_to_actuals():
    print("🔍 Porównuję Fixing I i II z rzeczywistymi danymi...")

    now = datetime.now()
    if now.hour < 15:
        date_to_check = now.date() - timedelta(days=1)
    else:
        date_to_check = now.date()

    day = date_to_check.day
    month = date_to_check.month

    pred_file = f"app/static/exports/prognoza_{day:02d}_{month:02d}.xlsx"
    actual_file = f"dane_rzeczywiste_{day:02d}_{month:02d}.xlsx"

    try:
        pred_df = pd.read_excel(pred_file)
        actual_df = pd.read_excel(actual_file)
    except Exception as e:
        print(f"❌ Błąd wczytywania plików: {e}")
        return

    # Sprawdzenie kolumn
    required_cols = ["Fixing I - Kurs", "Fixing II - Kurs", "Hour"]
    if not all(col in actual_df.columns for col in required_cols):
        print("❌ Brakuje wymaganych kolumn w pliku rzeczywistym.")
        return

    # Porównanie
    merged = pd.merge(pred_df, actual_df, on="Hour", suffixes=("_prognoza", "_rzeczywista"))

    merged["Fixing I % Difference"] = abs(
        merged["Predicted Fixing I - Kurs"] - merged["Fixing I - Kurs"]) / merged["Fixing I - Kurs"] * 100
    merged["Fixing II % Difference"] = abs(
        merged["Predicted Fixing II - Kurs"] - merged["Fixing II - Kurs"]) / merged["Fixing II - Kurs"] * 100

    merged["Data"] = date_to_check.strftime("%Y-%m-%d")

    for _, row in merged.iterrows():
        update_actual_price(
            data=row["Data"],
            Houra=int(row["Hour"]),
            cena_rzeczywista=row["Fixing I - Kurs"]
        )

    # Nadpisz prognozę
    merged.to_excel(pred_file, index=False)
    print(f"✅ Zaktualizowano plik prognozy: {pred_file}")
