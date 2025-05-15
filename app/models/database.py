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
            Hour INTEGER,
            cena_prognoza REAL,
            cena_rzeczywista REAL,
            blad REAL
        )
    ''')
    conn.commit()
    conn.close()

def save_prediction(data, Hour, cena_prognoza):
    conn = sqlite3.connect("app/static/data/predictions.db")
    c = conn.cursor()

    # Sprawdzenie czy istnieje już taki rekord
    c.execute("SELECT id FROM predictions WHERE data = ? AND Hour = ?", (data, Hour))
    exists = c.fetchone()

    if not exists:
        c.execute("INSERT INTO predictions (data, Hour, cena_prognoza) VALUES (?, ?, ?)",
                  (data, Hour, cena_prognoza))

    conn.commit()
    conn.close()

def update_actual_price(data, Hour, cena_rzeczywista):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # policz blad tylko jeśli prognoza istnieje
    c.execute("""
        SELECT cena_prognoza FROM predictions
        WHERE data = ? AND Hour = ?
    """, (data, Hour))
    row = c.fetchone()
    if row:
        cena_prognoza = row[0]
        blad = abs(cena_prognoza - cena_rzeczywista)
        c.execute("""
            UPDATE predictions
            SET cena_rzeczywista = ?, blad = ?
            WHERE data = ? AND Hour = ?
        """, (cena_rzeczywista, blad, data, Hour))
    conn.commit()
    conn.close()

def get_all_predictions():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM predictions ORDER BY data, Hour")
    rows = c.fetchall()
    conn.close()
    return rows

# Inicjalizacja przy imporcie
init_db()
