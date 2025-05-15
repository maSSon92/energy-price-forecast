import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime


def save_predictions(predictions_df, folder="app/static/exports", forecast_date=None):
    # Ustal datę prognozy
    if forecast_date is None:
        forecast_date = datetime.today().strftime("%Y-%m-%d")

    parsed_date = datetime.strptime(forecast_date, "%Y-%m-%d")
    day_str = f"{parsed_date.day:02d}_{parsed_date.month:02d}"

    # Nazwy plików
    filename = f"prognoza_{parsed_date.strftime('%d_%m')}.xlsx"
    chart_name = f"wykres_{parsed_date.strftime('%d_%m')}.png"


    # Ścieżki
    filepath = os.path.join(folder, filename)
    chart_path = os.path.join(folder, chart_name)
    os.makedirs(folder, exist_ok=True)

    # Dodaj dodatkowe kolumny
    if "Hour" not in predictions_df.columns:
        predictions_df["Hour"] = [row["Godzina"] for row in predictions_df.to_dict("records")]

    predictions_df["Predicted Fixing I - Kurs"] = [row.get("Fixing I", 0.0) for row in predictions_df.to_dict("records")]
    predictions_df["Predicted Fixing II - Kurs"] = [row.get("Fixing II", 0.0) for row in predictions_df.to_dict("records")]
    predictions_df["Date"] = forecast_date
    predictions_df["Actual Fixing I - Kurs"] = None
    predictions_df["Actual Fixing II - Kurs"] = None
    predictions_df["Fixing I % Difference"] = None
    predictions_df["Fixing II % Difference"] = None

    # Zapis do Excela
    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        predictions_df.to_excel(writer, index=False, sheet_name="Prognoza")

    # Wykres
    plt.figure(figsize=(12, 6))
    plt.plot(predictions_df["Hour"], predictions_df["Predicted Fixing I - Kurs"], label="Fixing I")
    plt.plot(predictions_df["Hour"], predictions_df["Predicted Fixing II - Kurs"], label="Fixing II")
    plt.title(f"Prognoza cen energii na {forecast_date}")
    plt.xlabel("Godzina")
    plt.ylabel("Cena [PLN/MWh]")
    plt.grid(True)
    plt.legend()
    plt.savefig(chart_path)
    plt.close()

    print(f"✅ Zapisano prognozę do {filepath}")
    return filepath, chart_path


