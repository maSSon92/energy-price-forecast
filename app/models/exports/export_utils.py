import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def save_predictions(predictions_df, folder="app/static/exports"):
    today_str = datetime.now().strftime('%Y-%m-%d')
    filename = f"Prognoza_{today_str}.xlsx"
    filepath = os.path.join(folder, filename)
    os.makedirs(folder, exist_ok=True)

    predictions_df["Date"] = today_str
    predictions_df["Actual Fixing I - Kurs"] = None
    predictions_df["Actual Fixing II - Kurs"] = None
    predictions_df["Fixing I % Difference"] = None
    predictions_df["Fixing II % Difference"] = None

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        predictions_df.to_excel(writer, index=False, sheet_name="Prognoza")

    # wykres
    plt.figure(figsize=(12, 6))
    plt.plot(predictions_df["Hour"], predictions_df["Predicted Fixing I - Kurs"], label="Fixing I")
    plt.plot(predictions_df["Hour"], predictions_df["Predicted Fixing II - Kurs"], label="Fixing II")
    plt.title(f"Prognoza cen energii na {today_str}")
    plt.xlabel("Godzina")
    plt.ylabel("Cena [PLN/MWh]")
    plt.grid(True)
    plt.legend()
    chart_path = os.path.join(folder, f"Wykres_{today_str}.png")
    plt.savefig(chart_path)
    plt.close()

    print(f"✅ Zapisano prognozę do {filepath}")
    return filepath, chart_path
