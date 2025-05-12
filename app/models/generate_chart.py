import pandas as pd
import matplotlib.pyplot as plt
import os

def generate_error_chart(csv_path='app/static/exports/historyczne_bledy.csv', output_path='app/static/exports/wykres_bledow.png'):
    if not os.path.exists(csv_path):
        print("❌ Brak pliku historyczne_bledy.csv")
        return

    df = pd.read_csv(csv_path)
    if 'Data' not in df or 'Blad [%]' not in df:
        print("❌ Plik nie zawiera wymaganych kolumn: 'Data' i 'Blad [%]'")
        return

    df_grouped = df.groupby("Data").agg({"Blad [%]": "mean"}).reset_index()

    plt.figure(figsize=(10, 6))
    plt.plot(df_grouped["Data"], df_grouped["Blad [%]"], marker='o', linestyle='-', linewidth=2, color='steelblue')
    plt.title("Średni błąd prognozy – dzień po dniu", fontsize=14)
    plt.xlabel("Data")
    plt.ylabel("Średni błąd [%]")
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(output_path)
    plt.close()
    print(f"✅ Zapisano wykres do: {output_path}")

if __name__ == "__main__":
    generate_error_chart()
