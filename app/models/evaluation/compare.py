import os
import pandas as pd
from datetime import datetime
from app.models.helpers.api_helpers import fetch_actual_prices

def compare_predictions_to_actuals(folder="results"):
    today_str = datetime.now().strftime('%Y-%m-%d')
    path = os.path.join(folder, f"Prognoza_{today_str}.xlsx")
    if not os.path.exists(path):
        print(f"❌ Brak pliku {path}")
        return

    df = pd.read_excel(path)
    real = fetch_actual_prices(today_str)

    df["Actual Fixing I - Kurs"] = df["Hour"].apply(lambda h: real.get(h, {}).get("fix_i"))
    df["Actual Fixing II - Kurs"] = df["Hour"].apply(lambda h: real.get(h, {}).get("fix_ii"))
    df["Fixing I % Difference"] = 100 * (df["Predicted Fixing I - Kurs"] - df["Actual Fixing I - Kurs"]) / df["Actual Fixing I - Kurs"]
    df["Fixing II % Difference"] = 100 * (df["Predicted Fixing II - Kurs"] - df["Actual Fixing II - Kurs"]) / df["Actual Fixing II - Kurs"]

    mae_i = df["Fixing I % Difference"].abs().mean()
    mae_ii = df["Fixing II % Difference"].abs().mean()
    print(f"📈 Średni błąd Fixing I: {mae_i:.2f}% | Fixing II: {mae_ii:.2f}%")

    df.to_excel(path, index=False)
    return df
