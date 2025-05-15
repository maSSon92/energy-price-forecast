import os
from fpdf import FPDF
import matplotlib.pyplot as plt
from datetime import datetime

def safe(text):
    return str(text).encode("latin-1", "replace").decode("latin-1")

def generate_pdf_report(predictions_df, image_path=None, forecast_date=None, folder="app/static/exports"):
    # Ustal datę raportu
    if forecast_date is None:
        forecast_date = datetime.now().strftime('%Y-%m-%d')

    parsed_date = datetime.strptime(forecast_date, "%Y-%m-%d")
    date_str = parsed_date.strftime('%d_%m')
    title_str = parsed_date.strftime('%Y-%m-%d')

    os.makedirs(folder, exist_ok=True)
    pdf_path = os.path.join(folder, f"raport_{date_str}.pdf")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, safe(f"Raport dzienny - {title_str}"), ln=True, align="C")

    pdf.set_font("Arial", size=10)
    subtitle = "Model: XGBoost per hour, dane: API PSE + pogoda"
    pdf.cell(200, 10, safe(subtitle), ln=True)

    if image_path and os.path.exists(image_path):
        pdf.image(image_path, x=10, y=40, w=190)
        pdf.set_y(120)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, safe("Średnie błędy względne:"), ln=True)

    try:
        mae_i = predictions_df["Fixing I % Difference"].abs().mean()
        mae_ii = predictions_df["Fixing II % Difference"].abs().mean()
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 8, safe(f"- Fixing I: {mae_i:.2f}%"), ln=True)
        pdf.cell(0, 8, safe(f"- Fixing II: {mae_ii:.2f}%"), ln=True)
    except:
        pdf.cell(0, 8, safe("Brak danych rzeczywistych do analizy."), ln=True)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, safe("Szczegółowe prognozy:"), ln=True)

    pdf.set_font("Arial", size=9)
    for _, row in predictions_df.iterrows():
        hour = int(row.get("Hour", -1))
        fix_i = row.get("Predicted Fixing I - Kurs", row.get("Cena", 0.0))
        fix_ii = row.get("Predicted Fixing II - Kurs", row.get("Cena", 0.0))
        line = f"Godzina {hour:02d}: Fixing I = {fix_i:.2f} zł, Fixing II = {fix_ii:.2f} zł"
        pdf.cell(0, 6, safe(line), ln=True)

    pdf.output(pdf_path)
    print(f"📄 PDF zapisany: {pdf_path}")
    return pdf_path
