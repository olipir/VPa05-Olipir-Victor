import sqlite3
import threading
from datetime import datetime

DB_PATH = "reminders.db"

STATUS_ACTIVE = "Ожидает"
STATUS_DONE = "Готово"
STATUS_OVERDUE = "Просрочено"
STATUS_CANCELLED = "Отменено"

_ALL_STATUSES = [STATUS_ACTIVE, STATUS_DONE, STATUS_OVERDUE, STATUS_CANCELLED]


class Database:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path=DB_PATH):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, db_path=DB_PATH):
        if self._initialized:
            return
        self._initialized = True
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                description TEXT    DEFAULT '',
                due_datetime TEXT   NOT NULL,
                status      TEXT    NOT NULL DEFAULT 'Ожидает',
                created_at  TEXT    NOT NULL
            )
        """)
        self.conn.commit()

    def add_reminder(self, title, description, due_datetime):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor = self.conn.execute(
            "INSERT INTO reminders (title, description, due_datetime, status, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (title, description, due_datetime, STATUS_ACTIVE, now),
        )
        self.conn.commit()
        return cursor.lastrowid

    def delete_reminder(self, rid):
        cursor = self.conn.execute("DELETE FROM reminders WHERE id = ?", (rid,))
        self.conn.commit()
        return cursor.rowcount > 0

    def update_status(self, rid, new_status):
        if new_status not in _ALL_STATUSES:
            return False
        cursor = self.conn.execute(
            "UPDATE reminders SET status = ? WHERE id = ?", (new_status, rid)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def get_reminders(self, status_filter=None):
        if status_filter and status_filter in _ALL_STATUSES:
            rows = self.conn.execute(
                "SELECT * FROM reminders WHERE status = ? ORDER BY due_datetime ASC",
                (status_filter,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM reminders ORDER BY due_datetime ASC"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_due_reminders(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        rows = self.conn.execute(
            "SELECT * FROM reminders WHERE status = ? AND due_datetime <= ?",
            (STATUS_ACTIVE, now),
        ).fetchall()
        return [dict(r) for r in rows]

    def mark_overdue(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.conn.execute(
            "UPDATE reminders SET status = ? WHERE status = ? AND due_datetime < ?",
            (STATUS_OVERDUE, STATUS_ACTIVE, now),
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
