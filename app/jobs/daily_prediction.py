import os
import pandas as pd
from datetime import datetime
from app.models.prediction_model import load_data_from_excel, prepare_input_dataframe_for_day, predict_all_hours
from app.models.database import save_prediction
from app.models.exports.export_utils import save_predictions
from app.models.evaluation.compare import compare_predictions_to_actuals
from app.models.exports.pdf_report import generate_pdf_report

def run_daily_prediction():
    print("📅 Uruchamiam codzienną prognozę...")

    try:
        df = load_data_from_excel()
        if df.empty:
            print("❌ Brak danych wejściowych")
            return

        day_predictions = predict_all_hours(df)
        today = datetime.now().date().strftime("%Y-%m-%d")

        for row in day_predictions:
            godzina = row.get("Godzina")
            cena = row.get("Prognozowana cena")
            save_prediction(today, godzina, cena)

        # przygotuj DataFrame do eksportu
        df_export = pd.DataFrame(day_predictions)
        df_export["Hour"] = df_export["Godzina"]
        df_export["Predicted Fixing I - Kurs"] = df_export["Prognozowana cena"]
        df_export["Predicted Fixing II - Kurs"] = df_export["Prognozowana cena"]

        excel_path, chart_path = save_predictions(df_export)
        compare_predictions_to_actuals()
        generate_pdf_report(df_export, chart_path)

        print("✅ Prognoza zakończona sukcesem!")

    except Exception as e:
        print(f"🚨 Błąd: {e}")

if __name__ == "__main__":
    run_daily_prediction()
