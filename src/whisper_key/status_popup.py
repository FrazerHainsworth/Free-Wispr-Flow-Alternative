# status_popup.py
# Small always-on-top card that shows a spinner while a slow job runs
# (rewrite, prompt, speaker transcription) and a clear result when it finishes.
# Tray balloons are often swallowed by Windows, so this is the signal the user
# can actually see.

import logging
import threading

logger = logging.getLogger(__name__)


class StatusPopup:
    def __init__(self):
        self.root = None
        self._canvas = None
        self._text = None
        self._thread = None
        self._ready = threading.Event()
        self._spin_id = None
        self._hide_id = None
        self._angle = 0
        self._mode = "hidden"
        self._available = True

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True, name="status-popup")
        self._thread.start()
        self._ready.wait(timeout=2.0)

    def show(self, message: str):
        self._call(lambda: self._show_busy(message))

    def succeed(self, message: str, hold_ms: int = 4500):
        self._call(lambda: self._show_done(message, "#3fb950", hold_ms))

    def fail(self, message: str):
        self._call(lambda: self._show_done(message, "#f85149", 2800))

    def hide(self):
        self._call(self._hide)

    def shutdown(self):
        if not self.root:
            return
        try:
            self.root.after(0, self.root.destroy)
        except Exception:
            pass

    def _call(self, fn):
        if not self._available or not self.root:
            return
        try:
            self.root.after(0, fn)
        except Exception as e:
            logger.debug(f"Status popup call failed: {e}")

    def _run(self):
        try:
            import tkinter as tk
            self.root = tk.Tk()
            self.root.withdraw()
            self.root.overrideredirect(True)
            self.root.attributes("-topmost", True)
            try:
                self.root.attributes("-alpha", 0.96)
            except Exception:
                pass

            card = tk.Frame(self.root, bg="#161b22", highlightthickness=1, highlightbackground="#30363d")
            card.pack(fill="both", expand=True)
            self._canvas = tk.Canvas(card, width=28, height=28, bg="#161b22", highlightthickness=0)
            self._canvas.pack(side="left", padx=(12, 4), pady=12)
            self._text = tk.StringVar(value="")
            tk.Label(
                card, textvariable=self._text, bg="#161b22", fg="#c9d1d9",
                font=("Segoe UI", 10), anchor="w", justify="left", wraplength=300,
            ).pack(side="left", fill="x", expand=True, padx=(0, 14), pady=10)

            self._place()
            self._ready.set()
            self.root.mainloop()
        except Exception as e:
            logger.warning(f"Status popup disabled: {e}")
            self._available = False
            self._ready.set()

    def _place(self):
        # Grow with the message. A learned correction can be a short phrase,
        # and a fixed 56px card clips the second line.
        self.root.update_idletasks()
        width = 380
        height = min(160, max(56, self.root.winfo_reqheight()))
        screen_w = self.root.winfo_screenwidth()
        x = max(12, screen_w - width - 24)
        y = 48
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _show_busy(self, message: str):
        self._cancel_hide()
        self._mode = "busy"
        self._text.set(message)
        self._place()
        self.root.deiconify()
        self.root.lift()
        self._spin()

    def _show_done(self, message: str, color: str, hold_ms: int):
        self._stop_spin()
        self._cancel_hide()
        self._mode = "done"
        self._text.set(message)
        self._draw_mark(color)
        self._place()
        self.root.deiconify()
        self.root.lift()
        self._hide_id = self.root.after(hold_ms, self._hide)

    def _hide(self):
        self._stop_spin()
        self._mode = "hidden"
        try:
            self.root.withdraw()
        except Exception:
            pass

    def _spin(self):
        if self._mode != "busy" or not self._canvas:
            return
        self._angle = (self._angle + 28) % 360
        canvas = self._canvas
        canvas.delete("all")
        canvas.create_oval(4, 4, 24, 24, outline="#30363d", width=3)
        canvas.create_arc(4, 4, 24, 24, start=self._angle, extent=100, outline="#58a6ff", width=3, style="arc")
        self._spin_id = self.root.after(40, self._spin)

    def _draw_mark(self, color: str):
        if not self._canvas:
            return
        canvas = self._canvas
        canvas.delete("all")
        canvas.create_oval(4, 4, 24, 24, outline=color, width=2)
        if color == "#3fb950":
            canvas.create_line(8, 14, 12, 19, 20, 9, fill=color, width=2, capstyle="round")
        else:
            canvas.create_line(9, 9, 19, 19, fill=color, width=2)
            canvas.create_line(19, 9, 9, 19, fill=color, width=2)

    def _stop_spin(self):
        if self._spin_id is not None and self.root:
            try:
                self.root.after_cancel(self._spin_id)
            except Exception:
                pass
        self._spin_id = None

    def _cancel_hide(self):
        if self._hide_id is not None and self.root:
            try:
                self.root.after_cancel(self._hide_id)
            except Exception:
                pass
        self._hide_id = None
