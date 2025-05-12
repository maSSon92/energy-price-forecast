from flask import Blueprint, render_template, request, send_file, url_for, redirect
import os
import pandas as pd
from datetime import datetime, timedelta
from app.models.prediction_model import (
    predict_price, predict_all_hours,
    prepare_input_dataframe_for_day, train_model,
    load_data_from_excel
)
from app.models.generate_chart import generate_error_chart
from app.models.database import save_prediction, get_all_predictions
from app.models.pdf_export import export_day_to_pdf
import sqlite3
import matplotlib.pyplot as plt

main = Blueprint('main', __name__)

df = load_data_from_excel()
model = train_model(df)

@main.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        return redirect(url_for('main.home'))
    return render_template('home.html')

def validate_date(day, month):
    try:
        today = datetime.today().date()
        target_date = datetime(datetime.today().year, month, day).date()
        max_date = today + timedelta(days=7)
        return today <= target_date <= max_date
    except Exception:
        return False

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
            if not validate_date(day, month):
                error = "❌ Nieprawidłowa data — wybierz dzień od dziś do 7 dni w przód."
                return render_template('predict.html',
                           prediction=None,
                           error=error,
                           day_predictions=None,
                           download_link=None)

            mode = request.form.get('mode')

            df = load_data_from_excel()
            model = train_model(df)

            if mode == 'hour':
                hour = int(request.form['hour'])
                prediction = predict_price(hour, day, month, model)
            elif mode == 'day':
                df_input = prepare_input_dataframe_for_day(day, month)
                day_predictions = predict_all_hours(df_input, model)
                data_str = datetime(datetime.today().year, month, day).strftime('%Y-%m-%d')
                for row in day_predictions:
                    godzina = row.get("Godzina")
                    cena = row.pop("Prognozowana cena")
                    row["Cena"] = cena
                    save_prediction(data_str, godzina, cena)

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
    generate_error_chart()
    plot_path = os.path.join('static', 'exports', 'wykres.png')
    plot_url = url_for('static', filename='exports/wykres.png') if os.path.exists(plot_path) else None
    wykres_bledow = url_for('static', filename='exports/wykres_bledow.png') if os.path.exists('app/static/exports/wykres_bledow.png') else None
    mae_fix_i = 5.23
    mae_fix_ii = 6.42
    return render_template('stats.html', plot_url=plot_url, wykres_bledow=wykres_bledow, mae_fix_i=mae_fix_i, mae_fix_ii=mae_fix_ii)

@main.route('/history')
def history():
    selected_date = request.args.get('date')
    rows = []
    if selected_date:
        conn = sqlite3.connect("app/static/data/predictions.db")
        c = conn.cursor()
        c.execute("SELECT * FROM predictions WHERE data = ? ORDER BY godzina", (selected_date,))
        rows = c.fetchall()
        conn.close()
    else:
        rows = get_all_predictions()
    return render_template('history.html', rows=rows, selected_date=selected_date)

@main.route('/history/<data>')
def history_detail(data):
    conn = sqlite3.connect("app/static/data/predictions.db")
    c = conn.cursor()
    c.execute("SELECT * FROM predictions WHERE data = ? ORDER BY godzina", (data,))
    rows = c.fetchall()
    conn.close()

    godziny = [row[2] for row in rows]
    prognozy = [row[3] for row in rows]
    rzeczywiste = [row[4] for row in rows if row[4] is not None]
    if rzeczywiste:
        plt.figure(figsize=(10, 5))
        plt.plot(godziny, prognozy, label="Prognoza", marker='o')
        plt.plot(godziny, [row[4] if row[4] is not None else None for row in rows], label="Rzeczywista", marker='x')
        plt.title(f"Prognoza vs Rzeczywista – {data}")
        plt.xlabel("Godzina")
        plt.ylabel("Cena")
        plt.legend()
        plt.grid(True)
        wykres_path = os.path.join("app", "static", "exports", f"wykres_{data}.png")
        plt.tight_layout()
        plt.savefig(wykres_path)
        plt.close()
        plot_url = url_for('static', filename=f"exports/wykres_{data}.png")
    else:
        plot_url = None

    return render_template('history_detail.html', rows=rows, data=data, plot_url=plot_url)

@main.route('/export/<data>.pdf')
def export_pdf(data):
    filename = f"export_{data}.pdf"
    folder = os.path.join("app", "static", "exports")
    os.makedirs(folder, exist_ok=True)  
    path = os.path.abspath(os.path.join(folder, filename))
    export_day_to_pdf(data, path)
    return send_file(path, as_attachment=True)
@main.route('/downloads')
def downloads():
    folder = os.path.join('app', 'static', 'exports')
    if not os.path.exists(folder):
        files = []
    else:
        files = [f for f in os.listdir(folder) if f.endswith('.xlsx') or f.endswith('.pdf')]
    return render_template('downloads.html', files=files)
