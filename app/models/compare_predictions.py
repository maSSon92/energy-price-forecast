import pandas as pd
import os
from datetime import datetime, timedelta
from app.models.database import update_actual_price

def compare_predictions_to_actuals():
    print("🔍 Rozpoczynam porównanie prognoz z rzeczywistością...")

    now = datetime.now()
    if now.hour < 15:
        date_to_check = now.date() - timedelta(days=1)
    else:
        date_to_check = now.date()

    day = date_to_check.day
    month = date_to_check.month

    prediction_file_path = f"app/static/exports/prognoza_{day:02d}_{month:02d}.xlsx"
    actual_file_path = f"dane_rzeczywiste_{day:02d}_{month:02d}.xlsx"
    output_csv = "app/static/exports/historyczne_bledy.csv"

    print(f"📂 Oczekiwane pliki:")
    print(f"- Prognoza: {prediction_file_path}")
    print(f"- Rzeczywiste: {actual_file_path}")

    try:
        pred_df = pd.read_excel(prediction_file_path)
        actual_df = pd.read_excel(actual_file_path)
    except Exception as e:
        print(f"❌ Błąd podczas wczytywania danych: {e}")
        return

    if 'Prognozowana cena' in pred_df.columns:
        pred_df.rename(columns={'Prognozowana cena': 'Cena'}, inplace=True)

    if 'Godzina' not in pred_df or 'Cena' not in pred_df:
        print("❌ Brakuje wymaganych kolumn w pliku prognozy")
        return

    if 'Godzina' not in actual_df or 'Cena' not in actual_df:
        print("❌ Brakuje wymaganych kolumn w pliku rzeczywistym")
        return

    merged = pd.merge(pred_df, actual_df, on='Godzina', suffixes=('_prognoza', '_rzeczywista'))
    merged['Blad [%]'] = abs(merged['Cena_prognoza'] - merged['Cena_rzeczywista']) / merged['Cena_rzeczywista'] * 100

    sredni_blad = merged['Blad [%]'].mean()
    print(f"✅ Średni błąd dla dnia {date_to_check}: {round(sredni_blad, 2)}%")

    merged['Data'] = date_to_check.strftime('%Y-%m-%d')
    merged['MAE'] = abs(merged['Cena_prognoza'] - merged['Cena_rzeczywista'])

    for _, row in merged.iterrows():
        update_actual_price(
            data=row['Data'],
            godzina=int(row['Godzina']),
            cena_rzeczywista=row['Cena_rzeczywista']
        )

    if os.path.exists(output_csv):
        history_df = pd.read_csv(output_csv)
        history_df = pd.concat([history_df, merged], ignore_index=True)
    else:
        history_df = merged

    history_df.to_csv(output_csv, index=False)
    print(f"📁 Zapisano wyniki do {output_csv}")


if __name__ == "__main__":
    compare_predictions_to_actuals()
