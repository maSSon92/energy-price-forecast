import pandas as pd
import requests
from datetime import datetime
import holidays

# 📌 Zwraca True jeśli dzień jest świętem w Polsce
def is_holiday(date_obj):
    pl_holidays = holidays.Poland()
    return date_obj in pl_holidays

# 📌 Pobiera dane pogodowe z IMGW dla stacji "Warszawa"
def get_weather_forecast():
    url = "https://danepubliczne.imgw.pl/api/data/synop"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Szukamy danych dla Warszawy
        for stacja in data:
            if stacja["stacja"].lower() == "warszawa":
                print("✅ Dane z IMGW (Warszawa):", stacja)
                return {
                    "Temp": float(stacja["temperatura"].replace(",", ".")),
                    "Wind": float(stacja["predkosc_wiatru"].replace(",", ".")),
                   # "Pressure": float(stacja["cisnienie"].replace(",", ".")),
                   # "Humidity": float(stacja.get("wilgotnosc_wzgledna", "0").replace(",", ".")) if stacja.get("wilgotnosc_wzgledna") else 0
                }

        print("⚠️ IMGW: Brak danych dla Warszawy.")
        return None

    except Exception as e:
        print(f"❌ Błąd pobierania danych IMGW: {e}")
        return None


# 📌 Pobiera zapotrzebowanie z API PSE (dane przykładowe - bez tokenu)
def get_load_forecast():
    try:
        url = "https://api.gios.gov.pl/pjp-api/rest/station/findAll"  # PRZYKŁADOWY – nie ma publicznego load forecast
        response = requests.get(url)
        response.raise_for_status()
        print("✅ Dane PSE zostały pobrane (tu: przykładowy endpoint GIOS)")
        return {hour: 18000 + hour * 10 for hour in range(24)}  # ZASYMULOWANE dane
    except Exception as e:
        print(f"❌ Błąd pobierania danych z PSE: {e}")
        return {hour: 0 for hour in range(24)}



# 📌 Przygotowuje cechy z danych wejściowych do predykcji/treningu

def prepare_prediction_features(date_str, godziny=range(24), weather=None, pse_load=None, avg_price=None):
    print("DEBUG: date_str =", date_str, type(date_str))
    features = []
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    is_hol = is_holiday(date_obj)
    is_weekend = date_obj.weekday() >= 5
    weekday = date_obj.weekday()
    month = date_obj.month

    for hour in godziny:
        row = {
            "Hour": hour,
            "Day of Week": weekday,
            "Month": month,
            "is_weekend": int(is_weekend),
            "is_holiday": int(is_hol),
            "time_of_day": 0 if hour < 6 else 1 if hour < 12 else 2 if hour < 18 else 3,
            "Cena_t-1": avg_price if avg_price is not None else 350.0,
            "Cena_t-24": avg_price if avg_price is not None else 350.0,
            "Forecasted Load": pse_load.get(hour, 18000.0) if pse_load else 18000.0,
            "temp": weather.get(hour, {}).get("Temp", 15.0) if weather else 15.0,
            "wind": weather.get(hour, {}).get("Wind", 5.0) if weather else 5.0,
            "cloud": weather.get(hour, {}).get("Cloud", 50.0) if weather else 50.0
        }
        features.append(row)

    return pd.DataFrame(features)



