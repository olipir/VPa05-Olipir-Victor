import threading
import time
from notifier import notify


class NotificationScheduler:
    def __init__(self, db, refresh_callback=None):
        self.db = db
        self.refresh_callback = refresh_callback
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def _run(self):
        while not self._stop_event.is_set():
            try:
                self.db.mark_overdue()
                due = self.db.get_due_reminders()
                for r in due:
                    notify(r["title"], r["description"] or "(нет описания)")
                    self.db.update_status(r["id"], "Просрочено")
                if due and self.refresh_callback:
                    self.refresh_callback()
            except Exception:
                pass
            time.sleep(30)
