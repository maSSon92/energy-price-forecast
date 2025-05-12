from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
import os
import sqlite3


def export_day_to_pdf(date_str, output_path):
    conn = sqlite3.connect("app/static/data/predictions.db")
    c = conn.cursor()
    c.execute("SELECT godzina, cena_prognoza, cena_rzeczywista, blad FROM predictions WHERE data = ? ORDER BY godzina", (date_str,))
    rows = c.fetchall()
    conn.close()

    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, f"Raport prognoz – {date_str}")

    # Wykres
    img_path = f"app/static/exports/wykres_{date_str}.png"
    if os.path.exists(img_path):
        c.drawImage(img_path, 50, height - 320, width=500, preserveAspectRatio=True)

    # Tabela
    data = [["Godzina", "Prognoza", "Rzeczywista", "Błąd"]]
    for row in rows:
        data.append([
            row[0],
            f"{row[1]:.2f}",
            f"{row[2]:.2f}" if row[2] is not None else "-",
            f"{row[3]:.2f}" if row[3] is not None else "-"
        ])

    table = Table(data, colWidths=[60, 100, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))

    table.wrapOn(c, width, height)
    table.drawOn(c, 50, 100)

    c.save()
    print(f"✅ PDF zapisany do {output_path}")
