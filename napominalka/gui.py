import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, time
from calendar import monthrange, month_name, day_name
from database import Database, STATUS_ACTIVE, STATUS_DONE, STATUS_OVERDUE, STATUS_CANCELLED
from notifier import notify


_FILTER_ALL = "Все"
_FILTERS = [_FILTER_ALL, STATUS_ACTIVE, STATUS_DONE, STATUS_OVERDUE, STATUS_CANCELLED]


class DatePicker(ttk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self._date = date.today()

        self._entry = ttk.Entry(self, width=14, state="readonly")
        self._entry.pack(side="left", padx=(0, 4))
        self._update_entry()

        btn = ttk.Button(self, text="...", width=3, command=self._open_calendar)
        btn.pack(side="left")

    def get_date(self):
        return self._date

    def set_date(self, d):
        self._date = d
        self._update_entry()

    def _update_entry(self):
        self._entry.configure(state="normal")
        self._entry.delete(0, "end")
        self._entry.insert(0, self._date.strftime("%Y-%m-%d"))
        self._entry.configure(state="readonly")

    def _open_calendar(self):
        CalendarPopup(self, self._date, self._on_selected)

    def _on_selected(self, d):
        self._date = d
        self._update_entry()


class CalendarPopup(tk.Toplevel):
    def __init__(self, parent, initial_date, callback):
        super().__init__(parent)
        self.callback = callback
        self._year = initial_date.year
        self._month = initial_date.day
        self._selected = None

        self.title("Выберите дату")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self._build()
        self._draw_days()

        x = parent.winfo_rootx()
        y = parent.winfo_rooty() + parent.winfo_height()
        self.geometry(f"+{x}+{y}")
        self.grab_set()
        self.focus_set()

    def _build(self):
        nav = ttk.Frame(self)
        nav.pack(fill="x", padx=6, pady=(6, 2))

        ttk.Button(nav, text="<", width=3,
                   command=self._prev_month).pack(side="left")
        self._month_label = ttk.Label(nav, font=("Segoe UI", 10, "bold"))
        self._month_label.pack(side="left", fill="x", expand=True)
        ttk.Button(nav, text=">", width=3,
                   command=self._next_month).pack(side="right")

        ttk.Button(nav, text="<<", width=3,
                   command=self._prev_year).pack(side="left", padx=(0, 2))
        ttk.Button(nav, text=">>", width=3,
                   command=self._next_year).pack(side="right", padx=(2, 0))

        days_frame = ttk.Frame(self)
        days_frame.pack(padx=6, pady=(0, 6))

        day_headers = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        for col, dh in enumerate(day_headers):
            lbl = ttk.Label(days_frame, text=dh, font=("Segoe UI", 9, "bold"),
                            anchor="center", width=4)
            lbl.grid(row=0, column=col, padx=1, pady=1)

        self._day_buttons = {}
        self._day_frame = days_frame

    def _draw_days(self):
        self._month_label.config(
            text=f"{month_name[self._month]} {self._year}"
        )

        for btn in self._day_buttons.values():
            btn.destroy()
        self._day_buttons.clear()

        first_day, days_in_month = monthrange(self._year, self._month)
        start_col = (first_day - 1) % 7 if first_day != 6 else 0

        row = 1
        for d in range(1, days_in_month + 1):
            col = (start_col + d - 1) % 7
            if d > 1 and col == 0:
                row += 1

            btn = ttk.Button(
                self._day_frame, text=str(d), width=4,
                command=lambda day=d: self._select_date(day)
            )
            btn.grid(row=row, column=col, padx=1, pady=1)
            self._day_buttons[d] = btn

    def _prev_month(self):
        self._month -= 1
        if self._month == 0:
            self._month = 12
            self._year -= 1
        self._draw_days()

    def _next_month(self):
        self._month += 1
        if self._month == 13:
            self._month = 1
            self._year += 1
        self._draw_days()

    def _prev_year(self):
        self._year -= 1
        self._draw_days()

    def _next_year(self):
        self._year += 1
        self._draw_days()

    def _select_date(self, day):
        self._selected = date(self._year, self._month, day)
        self.callback(self._selected)
        self.destroy()


class TimePicker(ttk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)

        self._hour_var = tk.StringVar(value="12")
        self._min_var = tk.StringVar(value="00")

        self._hour_combo = ttk.Combobox(
            self, textvariable=self._hour_var,
            values=[f"{h:02d}" for h in range(24)],
            width=4, state="readonly"
        )
        self._hour_combo.pack(side="left")

        ttk.Label(self, text=":").pack(side="left", padx=1)

        self._min_combo = ttk.Combobox(
            self, textvariable=self._min_var,
            values=[f"{m:02d}" for m in range(60)],
            width=4, state="readonly"
        )
        self._min_combo.pack(side="left")

    def get_time(self):
        return time(int(self._hour_var.get()), int(self._min_var.get()))


class ReminderApp(tk.Tk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.title("Напоминалка")
        self.geometry("780x520")
        self.minsize(600, 400)

        self._build_ui()
        self.refresh_list()
        self.after(30000, self._auto_refresh)

    def _build_ui(self):
        main = ttk.Frame(self, padding=12)
        main.pack(fill="both", expand=True)

        # --- Add form ---
        form = ttk.LabelFrame(main, text="Новое напоминание", padding=10)
        form.pack(fill="x", pady=(0, 10))

        ttk.Label(form, text="Заголовок *").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.entry_title = ttk.Entry(form, width=28)
        self.entry_title.grid(row=0, column=1, padx=(0, 12))

        ttk.Label(form, text="Описание").grid(row=0, column=2, sticky="w", padx=(0, 6))
        self.entry_desc = ttk.Entry(form, width=28)
        self.entry_desc.grid(row=0, column=3, padx=(0, 12))

        ttk.Label(form, text="Дата *").grid(row=0, column=4, sticky="w", padx=(0, 4))
        self.date_picker = DatePicker(form)
        self.date_picker.grid(row=0, column=5, padx=(0, 10))

        ttk.Label(form, text="Время *").grid(row=0, column=6, sticky="w", padx=(0, 4))
        self.time_picker = TimePicker(form)
        self.time_picker.grid(row=0, column=7, padx=(0, 10))

        btn_add = ttk.Button(form, text="Добавить", command=self._add_reminder)
        btn_add.grid(row=0, column=8)

        # --- Filter ---
        filter_frame = ttk.Frame(main)
        filter_frame.pack(fill="x", pady=(0, 6))

        ttk.Label(filter_frame, text="Фильтр:").pack(side="left", padx=(0, 6))
        self.filter_var = tk.StringVar(value=_FILTER_ALL)
        filter_combo = ttk.Combobox(
            filter_frame, textvariable=self.filter_var,
            values=_FILTERS, state="readonly", width=14
        )
        filter_combo.pack(side="left")
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_list())

        # --- Body: tree + scroll + action buttons ---
        body = ttk.Frame(main)
        body.pack(fill="both", expand=True)

        tree_frame = ttk.Frame(body)
        tree_frame.pack(side="left", fill="both", expand=True)

        columns = ("id", "title", "description", "due", "status")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Заголовок")
        self.tree.heading("description", text="Описание")
        self.tree.heading("due", text="Дата / Время")
        self.tree.heading("status", text="Статус")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("title", width=150)
        self.tree.column("description", width=200)
        self.tree.column("due", width=130, anchor="center")
        self.tree.column("status", width=100, anchor="center")

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # --- Action buttons (vertical, right side) ---
        actions = ttk.Frame(body, padding=(8, 0, 0, 0))
        actions.pack(side="left", fill="y")

        ttk.Button(actions, text="Удалить", command=self._delete_reminder).pack(fill="x", pady=(0, 6))
        ttk.Button(actions, text="Готово", command=lambda: self._set_status(STATUS_DONE)).pack(fill="x", pady=(0, 6))
        ttk.Button(actions, text="Отменено", command=lambda: self._set_status(STATUS_CANCELLED)).pack(fill="x", pady=(0, 6))
        ttk.Button(actions, text="Обновить", command=self.refresh_list).pack(fill="x", pady=(0, 18))
        ttk.Separator(actions, orient="horizontal").pack(fill="x", pady=(0, 6))
        ttk.Button(actions, text="Тест уведомления", command=self._test_notification).pack(fill="x")

    def refresh_list(self):
        self.db.mark_overdue()
        filter_val = self.filter_var.get()
        status_filter = None if filter_val == _FILTER_ALL else filter_val
        reminders = self.db.get_reminders(status_filter)

        for row in self.tree.get_children():
            self.tree.delete(row)

        for r in reminders:
            tag = ""
            if r["status"] == STATUS_OVERDUE:
                tag = "overdue"
            elif r["status"] == STATUS_DONE:
                tag = "done"
            elif r["status"] == STATUS_CANCELLED:
                tag = "cancelled"

            self.tree.insert(
                "", "end", values=(
                    r["id"], r["title"], r["description"],
                    r["due_datetime"], r["status"]
                ),
                tags=(tag,) if tag else ()
            )

        self.tree.tag_configure("overdue", foreground="red")
        self.tree.tag_configure("done", foreground="gray")
        self.tree.tag_configure("cancelled", foreground="gray")

    def _auto_refresh(self):
        self.refresh_list()
        self.after(30000, self._auto_refresh)

    def _add_reminder(self):
        title = self.entry_title.get().strip()
        desc = self.entry_desc.get().strip()

        if not title:
            messagebox.showwarning("Ошибка", "Заголовок обязателен!")
            return

        d = self.date_picker.get_date()
        t = self.time_picker.get_time()
        due = f"{d.strftime('%Y-%m-%d')} {t.strftime('%H:%M')}"

        self.db.add_reminder(title, desc, due)
        self.entry_title.delete(0, "end")
        self.entry_desc.delete(0, "end")
        self.refresh_list()

    def _delete_reminder(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Удаление", "Выберите напоминание из списка")
            return
        item = self.tree.item(selected[0])
        rid = item["values"][0]
        if messagebox.askyesno("Подтверждение", f"Удалить напоминание ID {rid}?"):
            self.db.delete_reminder(rid)
            self.refresh_list()

    def _set_status(self, new_status):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Статус", "Выберите напоминание из списка")
            return
        item = self.tree.item(selected[0])
        rid = item["values"][0]
        self.db.update_status(rid, new_status)
        self.refresh_list()

    def _test_notification(self):
        notify("Напоминалка — тест", "Если вы видите это сообщение, уведомления работают!")
