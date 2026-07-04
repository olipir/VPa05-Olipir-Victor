import threading
import tkinter as tk
from tkinter import ttk


def notify(title, message):
    try:
        from win10toast import ToastNotifier

        toaster = ToastNotifier()
        toaster.show_toast(title, message, duration=8, threaded=True)
    except ImportError:
        _show_popup(title, message)


def _show_popup(title, message):
    root = tk.Tk()
    root.withdraw()

    popup = tk.Toplevel(root)
    popup.title(title)
    popup.attributes("-topmost", True)
    popup.resizable(False, False)

    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    w, h = 400, 160
    x = screen_w - w - 20
    y = screen_h - h - 60
    popup.geometry(f"{w}x{h}+{x}+{y}")
    popup.overrideredirect(True)

    frame = ttk.Frame(popup, padding=16)
    frame.pack(fill="both", expand=True)

    lbl_title = ttk.Label(frame, text=title, font=("Segoe UI", 11, "bold"))
    lbl_title.pack(anchor="w")

    separator = ttk.Separator(frame, orient="horizontal")
    separator.pack(fill="x", pady=6)

    msg = tk.Text(frame, wrap="word", height=3, borderwidth=0,
                  font=("Segoe UI", 10), relief="flat")
    msg.insert("1.0", message)
    msg.config(state="disabled")
    msg.pack(fill="both", expand=True)

    btn_frame = ttk.Frame(frame)
    btn_frame.pack(fill="x", pady=(8, 0))

    ok_btn = ttk.Button(btn_frame, text="OK", command=popup.destroy)
    ok_btn.pack(side="right")

    popup.after(8000, popup.destroy)
    popup.mainloop()
