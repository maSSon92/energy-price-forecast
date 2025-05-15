import holidays
import pandas as pd

def prepare_features(df):
    df = df.copy()
    df["Day of Week"] = df["Data"].dt.weekday
    df["Month"] = df["Data"].dt.month
    df["is_weekend"] = df["Day of Week"].isin([5, 6]).astype(int)
    df["is_holiday"] = df["Data"].isin(holidays.CountryHoliday("PL")).astype(int)
    df = df.sort_values(["Data", "Hour"])
    if "Fixing I - Kurs" in df.columns:
        df["Cena_t-1"] = df["Fixing I - Kurs"].shift(1)
        df["Cena_t-24"] = df["Fixing I - Kurs"].shift(24)
    else:
        df["Cena_t-1"] = 0.0
        df["Cena_t-24"] = 0.0

    df["time_of_day"] = df["Hour"].apply(lambda h: 0 if h < 6 else 1 if h < 12 else 2 if h < 18 else 3)
    for col in ["Forecasted Load", "temp", "wind", "cloud"]:
        if col not in df.columns:
            df[col] = 0.0
    df = df.fillna(0.0)
    X = df[[
        "Hour", "Day of Week", "Month", "is_weekend", "is_holiday",
        "time_of_day", "Cena_t-1", "Cena_t-24",
        "Forecasted Load", "temp", "wind", "cloud"
    ]]
    y1 = df["Fixing I - Kurs"] if "Fixing I - Kurs" in df.columns else pd.Series([0.0]*len(df))
    y2 = df["Fixing II - Kurs"] if "Fixing II - Kurs" in df.columns else pd.Series([0.0]*len(df))
    return X, y1, y2

