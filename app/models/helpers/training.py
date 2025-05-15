import xgboost as xgb
from app.models.helpers.feature_engineering import prepare_prediction_features

def train_hourly_models(df, target_col):
    models = {}
    for hour in range(24):
        df_hour = df[df["Hour"] == hour]
        if df_hour.empty:
            continue
        X, y1, y2 = prepare_prediction_features(df_hour)
        y = y1 if target_col == "Fixing I - Kurs" else y2
        model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
        model.fit(X, y)
        models[hour] = model
    return models
