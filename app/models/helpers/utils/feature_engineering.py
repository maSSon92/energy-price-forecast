import holidays

def prepare_features(df):
    df = df.copy()
    df["Day of Week"] = df["Data"].dt.weekday
    df["Month"] = df["Data"].dt.month
    df["is_weekend"] = df["Day of Week"].isin([5, 6]).astype(int)
    df["is_holiday"] = df["Data"].isin(holidays.CountryHoliday("PL")).astype(int)
    df = df.sort_values(["Data", "Hour"])
    df["Cena_t-1"] = df["Fixing I - Kurs"].shift(1)
    df["Cena_t-24"] = df["Fixing I - Kurs"].shift(24)
    df["time_of_day"] = df["Hour"].apply(lambda h: 0 if h < 6 else 1 if h < 12 else 2 if h < 18 else 3)
    for col in ["Forecasted Load", "temp", "wind", "cloud"]:
        if col not in df.columns:
            df[col] = 0.0
    df = df.dropna()
    X = df[[
        "Hour", "Day of Week", "Month", "is_weekend", "is_holiday",
        "time_of_day", "Cena_t-1", "Cena_t-24",
        "Forecasted Load", "temp", "wind", "cloud"
    ]]
    return X, df["Fixing I - Kurs"], df["Fixing II - Kurs"]
