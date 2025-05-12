import sqlite3
from datetime import datetime
import os

DB_PATH = "app/static/data/predictions.db"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            godzina INTEGER,
            cena_prognoza REAL,
            cena_rzeczywista REAL,
            blad REAL
        )
    ''')
    conn.commit()
    conn.close()

def save_prediction(data, godzina, cena_prognoza):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO predictions (data, godzina, cena_prognoza)
        VALUES (?, ?, ?)
    """, (data, godzina, cena_prognoza))
    conn.commit()
    conn.close()

def update_actual_price(data, godzina, cena_rzeczywista):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # policz blad tylko jeśli prognoza istnieje
    c.execute("""
        SELECT cena_prognoza FROM predictions
        WHERE data = ? AND godzina = ?
    """, (data, godzina))
    row = c.fetchone()
    if row:
        cena_prognoza = row[0]
        blad = abs(cena_prognoza - cena_rzeczywista)
        c.execute("""
            UPDATE predictions
            SET cena_rzeczywista = ?, blad = ?
            WHERE data = ? AND godzina = ?
        """, (cena_rzeczywista, blad, data, godzina))
    conn.commit()
    conn.close()

def get_all_predictions():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM predictions ORDER BY data, godzina")
    rows = c.fetchall()
    conn.close()
    return rows

# Inicjalizacja przy imporcie
init_db()
