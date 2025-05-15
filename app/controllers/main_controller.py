from flask import Blueprint, render_template, request, send_file, url_for, redirect, session
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
from app.models.model_evaluator import evaluate_models
from app.models.exports.export_utils import save_predictions
from app.models.exports.pdf_report import generate_pdf_report
from app.models.evaluation.compare import compare_predictions_to_actuals
import sqlite3
import matplotlib.pyplot as plt
from app.models.feature_engineering import (
    get_load_forecast,
    prepare_prediction_features
)
from flask import jsonify

# Dane z API
#weather = get_weather_forecast()
#load = get_load_forecast()

# Cechy dla modelu
#features_df = prepare_features("2025-05-17", weather=weather, pse_load=load)
main = Blueprint('main', __name__)
SECRET_PASSWORD = "admin123"  # 🔒 Można potem ukryć w zmiennej środowiskowej

def validate_date(day, month):
    try:
        today = datetime.today().date()
        target_date = datetime(datetime.today().year, month, day).date()
        return today <= target_date <= today + timedelta(days=7)
    except Exception:
        return False

@main.route('/admin', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        password = request.form.get('password')
        if password == SECRET_PASSWORD:
            session['admin'] = True
            return redirect(url_for('main.admin_panel'))
        else:
            error = "❌ Niepoprawne hasło."
    return render_template('admin_login.html', error=error)

@main.route('/admin/panel')
def admin_panel():
    if not session.get('admin'):
        return redirect(url_for('main.admin_login'))

    conn = sqlite3.connect("app/static/data/predictions.db")
    c = conn.cursor()
    c.execute("SELECT * FROM predictions ORDER BY data, Hour")
    rows = c.fetchall()
    conn.close()
    return render_template("admin_panel.html", rows=rows)

@main.route('/admin/update', methods=['POST'])
def admin_update():
    if not session.get('admin'):
        return redirect(url_for('main.admin_login'))

    data = request.form.get('data')
    Hour = int(request.form.get('Hour'))
    new_value = float(request.form.get('cena_rzeczywista'))

    conn = sqlite3.connect("app/static/data/predictions.db")
    c = conn.cursor()
    c.execute("UPDATE predictions SET cena_rzeczywista = ?, blad = ABS(cena_prognoza - ?) WHERE data = ? AND Hour = ?",
              (new_value, new_value, data, Hour))
    conn.commit()
    conn.close()

    return redirect(url_for('main.admin_panel'))

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

            if not validate_date(day, month):
                error = "❌ Nieprawidłowa data – wybierz dzień od dziś do 7 dni w przód."
                return render_template('predict.html', prediction=None, error=error)

            if mode == 'day':
                # 🔄 Przygotowanie danych historycznych
                df = prepare_input_dataframe_for_day(day, month)
                if df.empty:
                    raise ValueError("Brak danych historycznych do predykcji.")

                # 🔮 Predykcja dla całego dnia
                day_predictions = predict_all_hours(df, day=day, month=month)

                # 🔐 Zapis do bazy
                data_str = datetime(datetime.today().year, month, day).strftime('%Y-%m-%d')
                for row in day_predictions:
                    if "Fixing I" in row:
                        row["Cena"] = row["Fixing I"]
                    else:
                        row["Cena"] = 0.0  # domyślnie, gdyby coś się wywaliło


                # 💾 Zapis do Excela + wykres
                df_export = pd.DataFrame(day_predictions)
                df_export["Godzina"] = df_export["Hour"]
                df_export["Predicted Fixing I - Kurs"] = df_export["Fixing I"]
                df_export["Predicted Fixing II - Kurs"] = df_export["Fixing II"]

                excel_path, chart_path = save_predictions(df_export, forecast_date=data_str)

                # ⚖️ Porównanie z danymi rzeczywistymi
                compare_predictions_to_actuals()

                # 📝 Wczytanie zaktualizowanego Excela i generowanie PDF
                updated_df = pd.read_excel(excel_path)
                generate_pdf_report(updated_df, image_path=chart_path, forecast_date=data_str)

                # 🔗 Link do pobrania
                download_link = "/static/exports/" + os.path.basename(excel_path)

            elif mode == 'hour':
                error = "🔒 Tryb godzinowy wyłączony – dostępna tylko prognoza całodniowa."

            else:
                error = "Nieprawidłowy tryb prognozy."

        except Exception as e:
            error = f"❌ Błąd danych wejściowych: {e}"

    return render_template('predict.html',
                           prediction=prediction,
                           error=error,
                           day_predictions=day_predictions,
                           download_link=download_link)


@main.route('/modelling')
def modelling():
    try:
        df = load_data_from_excel()
        comparison_df = evaluate_models(df)
        return render_template('modelling.html', table=comparison_df.to_dict(orient='records'))
    except Exception as e:
        return render_template('modelling.html', error=str(e), table=[])

@main.route('/stats')
def stats():
    generate_error_chart()
    plot_path = os.path.join('static', 'exports', 'wykres.png')
    wykres_bledow = url_for('static', filename='exports/wykres_bledow.png') if os.path.exists('app/static/exports/wykres_bledow.png') else None
    mae_fix_i = 5.23
    mae_fix_ii = 6.42
    return render_template('stats.html', plot_url=plot_path, wykres_bledow=wykres_bledow, mae_fix_i=mae_fix_i, mae_fix_ii=mae_fix_ii)

@main.route('/history')
def history():
    selected_date = request.args.get('date')
    rows = []
    if selected_date:
        conn = sqlite3.connect("app/static/data/predictions.db")
        c = conn.cursor()
        c.execute("SELECT * FROM predictions WHERE data = ? ORDER BY Hour", (selected_date,))
        rows = c.fetchall()
        conn.close()
    else:
        rows = get_all_predictions()
    return render_template('history.html', rows=rows, selected_date=selected_date)

@main.route('/history/<data>')
def history_detail(data):
    conn = sqlite3.connect("app/static/data/predictions.db")
    c = conn.cursor()
    c.execute("SELECT * FROM predictions WHERE data = ? ORDER BY Hour", (data,))
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
        plt.xlabel("Hour")
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

@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/me')
def me():
    return render_template('me.html')

@main.route('/contact')
def contact():
    return render_template('contact.html')

@main.route('/api/predict', methods=['GET'])
def api_predict():
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({"error": "Brak parametru date, np. ?date=2025-05-19"}), 400

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        day = date_obj.day
        month = date_obj.month

        df = prepare_input_dataframe_for_day(day, month)
        if df.empty:
            return jsonify({"error": "Brak danych historycznych do predykcji."}), 404

        prediction = predict_all_hours(df, day=day, month=month)
        fixing_i = [row["Fixing I"] for row in prediction]
        fixing_ii = [row["Fixing II"] for row in prediction]

        return jsonify({
            "date": date_str,
            "fixing_i": fixing_i,
            "fixing_ii": fixing_ii
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/')
def home():
    return render_template('home.html')
