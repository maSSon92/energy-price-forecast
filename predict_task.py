from app.models.compare_predictions import compare_predictions_to_actuals
from app.models.generate_chart import generate_error_chart
from app.models.database import update_actual_price
import app.models.xgb_model as xgb_model
from datetime import datetime, timedelta
import pandas as pd
import os

if __name__ == "__main__":
    print("🚀 Zadanie automatyczne wystartowało...")

    try:
        # Ustal datę do porównania
        now = datetime.now()
        if now.hour < 15:
            date_to_check = now.date() - timedelta(days=1)
        else:
            date_to_check = now.date()
        day = date_to_check.day
        month = date_to_check.month
        date_str = date_to_check.strftime("%Y-%m-%d")

        # Ścieżka do pliku prognozy
        pred_path = f"app/static/exports/prognoza_{day:02d}_{month:02d}.xlsx"
        if not os.path.exists(pred_path):
            print(f"❌ Brak pliku prognozy: {pred_path}")
            exit()

        pred_df = pd.read_excel(pred_path)

        # Określ kolumnę z godziną
        hour_col = "Hour"
        if "Hour" not in pred_df.columns:
            if "Godzina" in pred_df.columns:
                hour_col = "Godzina"
            else:
                raise KeyError("Brak kolumny Hour lub Godzina w pliku prognozy.")

        actual_prices = xgb_model.fetch_actual_prices(date_str)
        if not actual_prices:
            print("❌ Brak danych rzeczywistych z API PSE")
            exit()

        pred_df["Actual Fixing I - Kurs"] = pred_df[hour_col].apply(lambda h: actual_prices.get(h, {}).get("fix_i"))
        pred_df["Actual Fixing II - Kurs"] = pred_df[hour_col].apply(lambda h: actual_prices.get(h, {}).get("fix_ii"))

        pred_df["Fixing I % Difference"] = 100 * (pred_df["Predicted Fixing I - Kurs"] - pred_df["Actual Fixing I - Kurs"]) / pred_df["Actual Fixing I - Kurs"]
        pred_df["Fixing II % Difference"] = 100 * (pred_df["Predicted Fixing II - Kurs"] - pred_df["Actual Fixing II - Kurs"]) / pred_df["Actual Fixing II - Kurs"]

        # Zapisz zaktualizowany plik
        pred_df.to_excel(pred_path, index=False)
        print(f"✅ Zaktualizowano plik: {pred_path}")

        # Zapisz do bazy
        for _, row in pred_df.iterrows():
            update_actual_price(date_str, int(row[hour_col]), float(row["Actual Fixing I - Kurs"]))

        # Wygeneruj wykres
        generate_error_chart()

        print("✅ Zadanie zakończone pomyślnie!")

    except Exception as e:
        print(f"❌ Błąd podczas zadania automatycznego: {e}")
