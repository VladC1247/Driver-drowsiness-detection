import sqlite3
from datetime import datetime
import json

DB_PATH = "database.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            name TEXT PRIMARY KEY,
            embedding TEXT,
            role TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver TEXT,
            event TEXT,
            date TEXT,
            time TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_event(driver, event):
    now = datetime.now()
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO events (driver, event, date, time) VALUES (?, ?, ?, ?)",
              (driver, event, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")))
    conn.commit()
    conn.close()

def add_user(name, embedding, role="user"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (name, embedding, role) VALUES (?, ?, ?)",
              (name, json.dumps(embedding), role))
    conn.commit()
    conn.close()

def get_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT name, embedding, role FROM users")
    rows = c.fetchall()
    conn.close()
    return {name: {"embedding": json.loads(embedding), "role": role} for name, embedding, role in rows}

def get_user(name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT embedding, role FROM users WHERE name=?", (name,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"embedding": json.loads(row[0]), "role": row[1]}
    return None

def get_events():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, driver, date, time, event FROM events")
    rows = c.fetchall()
    conn.close()
    return rows

def update_event(event_id, driver, date, time, event):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE events SET driver=?, date=?, time=?, event=? WHERE id=?",
              (driver, date, time, event, event_id))
    conn.commit()
    conn.close()

def delete_event(event_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM events WHERE id=?", (event_id,))
    conn.commit()
    conn.close()

def add_event(driver, date, time, event):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO events (driver, date, time, event) VALUES (?, ?, ?, ?)",
              (driver, date, time, event))
    conn.commit()
    conn.close()

def update_user_role(name, new_role):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET role=? WHERE name=?", (new_role, name))
    conn.commit()
    conn.close()
