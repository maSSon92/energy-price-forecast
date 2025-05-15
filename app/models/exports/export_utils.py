import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime

def save_predictions(df, forecast_date):
    os.makedirs("app/static/exports", exist_ok=True)

    # Zapis Excela
    excel_path = f"app/static/exports/prognoza_{forecast_date[8:10]}_{forecast_date[5:7]}.xlsx"
    df.to_excel(excel_path, index=False)

    # Wykres
    plt.figure(figsize=(10, 5))
    plt.plot(df["Hour"], df["Fixing I"], label="Fixing I", marker="o")
    plt.plot(df["Hour"], df["Fixing II"], label="Fixing II", marker="x")
    plt.title(f"Prognoza cen – {forecast_date}")
    plt.xlabel("Hour")
    plt.ylabel("Cena [PLN/MWh]")
    plt.legend()
    plt.grid(True)

    chart_path = f"app/static/exports/wykres_{forecast_date[8:10]}_{forecast_date[5:7]}.png"
    plt.savefig(chart_path)
    plt.close()

    return excel_path, chart_path

