import sqlite3
import hashlib
import os


DB_FILE = "passwords.db"


def _get_db_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_FILE)


def _connect():
    return sqlite3.connect(_get_db_path())


def init_db():
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS master (
            id INTEGER PRIMARY KEY,
            hash TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            login TEXT NOT NULL,
            password BLOB NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def master_password_exists():
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM master")
    count = cur.fetchone()[0]
    conn.close()
    return count > 0


def set_master_password(password: str):
    h = hashlib.sha256(password.encode()).hexdigest()
    conn = _connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM master")
    cur.execute("INSERT INTO master (id, hash) VALUES (1, ?)", (h,))
    conn.commit()
    conn.close()


def verify_master_password(password: str) -> bool:
    h = hashlib.sha256(password.encode()).hexdigest()
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT hash FROM master WHERE id = 1")
    row = cur.fetchone()
    conn.close()
    return row is not None and row[0] == h


def add_entry(name: str, login: str, encrypted_password: bytes):
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO entries (name, login, password) VALUES (?, ?, ?)",
        (name, login, encrypted_password),
    )
    conn.commit()
    conn.close()


def get_entry(name: str):
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT login, password FROM entries WHERE name = ?", (name,))
    row = cur.fetchone()
    conn.close()
    return row


def list_entries():
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT name, login FROM entries ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return rows


def delete_entry(name: str) -> bool:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM entries WHERE name = ?", (name,))
    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted
