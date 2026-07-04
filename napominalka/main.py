from database import Database
from gui import ReminderApp
from scheduler import NotificationScheduler


def main():
    db = Database()
    app = ReminderApp(db)

    scheduler = NotificationScheduler(db, refresh_callback=app.refresh_list)
    scheduler.start()

    try:
        app.mainloop()
    finally:
        scheduler.stop()
        db.close()


if __name__ == "__main__":
    main()
