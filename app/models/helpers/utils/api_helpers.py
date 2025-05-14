import requests
import numpy as np

def fetch_pse_load_forecast(date_str):
    url = f"https://api.raporty.pse.pl/api/daily-load-forecast?$filter=business_date eq '{date_str}'"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json().get("value", [])
            return {
                int(item["udtczas"][-8:-6]): float(item["forecast_mw"])
                for item in data if item.get("forecast_mw") is not None
            }
    except Exception as e:
        print(f"[PSE LOAD] Błąd: {e}")
    return {}

def fetch_weather_forecast(date_str, lat=52.23, lon=21.01):
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&hourly=temperature_2m,windspeed_10m,cloudcover"
        f"&timezone=Europe%2FWarsaw&start_date={date_str}&end_date={date_str}"
    )
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json().get("hourly", {})
            return {
                h: {
                    "temp": data.get("temperature_2m", [])[h],
                    "wind": data.get("windspeed_10m", [])[h],
                    "cloud": data.get("cloudcover", [])[h]
                } for h in range(24)
            }
    except Exception as e:
        print(f"[WEATHER] Błąd: {e}")
    return {}
