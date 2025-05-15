from fpdf import FPDF
import os
from datetime import datetime

def safe(text):
    return str(text).encode("latin-1", "replace").decode("latin-1")

def generate_pdf_report(df, image_path=None, forecast_date=None, folder="app/static/exports"):
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
    pdf.cell(200, 10, safe(f"Raport dzienny – {title_str}"), ln=True, align="C")

    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, safe("Model: XGBoost Fixing I & II, dane: pogoda + PSE"), ln=True)

    if image_path and os.path.exists(image_path):
        pdf.image(image_path, x=10, y=40, w=190)
        pdf.set_y(120)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, safe("Błędy względne:"), ln=True)

    try:
        mae_i = df["Fixing I % Difference"].abs().mean()
        mae_ii = df["Fixing II % Difference"].abs().mean()
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 8, safe(f"- Fixing I: {mae_i:.2f}%"), ln=True)
        pdf.cell(0, 8, safe(f"- Fixing II: {mae_ii:.2f}%"), ln=True)
    except:
        pdf.cell(0, 8, safe("Brak danych rzeczywistych do analizy."), ln=True)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, safe("Prognozy i błędy godzinowe:"), ln=True)

    pdf.set_font("Arial", size=9)
    for _, row in df.iterrows():
        hour = int(row.get("Hour", row.get("Hour", -1)))

        fix1 = row.get("Predicted Fixing I - Kurs", 0.0)
        act1 = row.get("Fixing I - Kurs", None)
        err1 = row.get("Fixing I % Difference", None)

        fix2 = row.get("Predicted Fixing II - Kurs", 0.0)
        act2 = row.get("Fixing II - Kurs", None)
        err2 = row.get("Fixing II % Difference", None)

        line = f"Hour {hour:02d}: "
        line += f"Fixing I = {fix1:.2f} zł"
        if act1 is not None:
            line += f", Rzecz = {act1:.2f} zł, Błąd = {err1:.2f}%"
        line += " | "
        line += f"Fixing II = {fix2:.2f} zł"
        if act2 is not None:
            line += f", Rzecz = {act2:.2f} zł, Błąd = {err2:.2f}%"

        pdf.cell(0, 6, safe(line), ln=True)

    pdf.output(pdf_path)
    print(f"📄 PDF zapisany: {pdf_path}")
    return pdf_path
