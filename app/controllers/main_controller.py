from flask import Blueprint, render_template, request, send_file, url_for, redirect
import os
import pandas as pd
from datetime import datetime, timedelta
from app.models.prediction_model import (
    predict_price, predict_all_hours,
    prepare_input_dataframe_for_day, train_model,
    load_data_from_excel
)

main = Blueprint('main', __name__)

df = load_data_from_excel()
model = train_model(df)

@main.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        return redirect(url_for('main.home'))
    return render_template('home.html')

@main.route('/predict', methods=['GET', 'POST'])
def predict():
    prediction = None
    error = None
    day_predictions = None
    download_link = None

    if request.method == 'POST':
        try:
            day = int(request.form['day'])
            month = int(request.form['month'])
            mode = request.form.get('mode')

            df = load_data_from_excel()
            model = train_model(df)

            if mode == 'hour':
                hour = int(request.form['hour'])
                prediction = predict_price(hour, day, month, model)
            elif mode == 'day':
                df_input = prepare_input_dataframe_for_day(day, month)
                day_predictions = predict_all_hours(df_input, model)
                for row in day_predictions:
                    row["Cena"] = row.pop("Prognozowana cena")

                filename = f"prognoza_{day:02d}_{month:02d}.xlsx"
                folder = os.path.join('static', 'exports')
                os.makedirs(folder, exist_ok=True)
                path = os.path.join(folder, filename)
                pd.DataFrame(day_predictions).to_excel(path, index=False)
                download_link = f"/static/exports/{filename}"
            else:
                error = "Nieprawidłowy tryb prognozy."

        except Exception as e:
            error = f"Błąd danych wejściowych: {e}"

    return render_template('predict.html',
                           prediction=prediction,
                           error=error,
                           day_predictions=day_predictions,
                           download_link=download_link)

@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/me')
def me():
    return render_template('me.html')

@main.route('/contact')
def contact():
    return render_template('contact.html')

@main.route('/stats')
def stats():
    # Tu możesz dodać odczyt wykresu i błędów z pliku
    plot_path = os.path.join('static', 'exports', 'wykres.png')
    plot_url = url_for('static', filename='exports/wykres.png') if os.path.exists(plot_path) else None
    mae_fix_i = 5.23
    mae_fix_ii = 6.42
    return render_template('stats.html', plot_url=plot_url, mae_fix_i=mae_fix_i, mae_fix_ii=mae_fix_ii)

@main.route('/downloads')
def downloads():
    folder = os.path.join('app', 'static', 'exports')
    if not os.path.exists(folder):
        files = []
    else:
        files = [f for f in os.listdir(folder) if f.endswith('.xlsx') or f.endswith('.pdf')]
    return render_template('downloads.html', files=files)