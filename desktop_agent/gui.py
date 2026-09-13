from __future__ import annotations

import json
import os
import sys
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

from .runner import DesktopRunnerClient

CONFIG_FILE = Path(__file__).parent / "config.json"


def load_local_config() -> dict[str, str]:
    defaults = {
        "server_url": os.getenv("CLOUD_SERVER_URL", "http://localhost:8000"),
        "api_key": os.getenv("BOT_API_KEY", "dee2cbd5d1693aa6d5b113a31649a0501d7da3b3661348dcd8481b84584e0e66"),
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                defaults.update(saved)
        except Exception:
            pass
    return defaults


def save_local_config(data: dict[str, str]) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


class DesktopAgentGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title("Best Aviator • Local Residential Desktop Agent")
        self.geometry("780x560")
        self.minsize(680, 480)
        self.configure(bg="#0a0e17")

        self.config_data = load_local_config()
        self.runner: DesktopRunnerClient | None = None
        self.key_visible = False

        self._build_ui()
        self._apply_theme()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _apply_theme(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")

        # Custom widget styling
        style.configure(".", background="#0a0e17", foreground="#f9fafb")
        style.configure("TLabel", background="#0a0e17", foreground="#9ca3af", font=("Segoe UI", 9))
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), foreground="#ffffff")
        style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"), foreground="#ffffff")
        style.configure("Sub.TLabel", font=("Segoe UI", 8), foreground="#6b7280")

        style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=6)
        style.map("TButton", background=[("active", "#1e293b")])

    def _build_ui(self) -> None:
        main_frame = tk.Frame(self, bg="#0a0e17", padx=20, pady=16)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Header with Brand and Live Status
        header_frame = tk.Frame(main_frame, bg="#111827", relief=tk.FLAT, bd=1, padx=16, pady=12)
        header_frame.pack(fill=tk.X, pady=(0, 14))

        title_box = tk.Frame(header_frame, bg="#111827")
        title_box.pack(side=tk.LEFT)

        brand_lbl = tk.Label(title_box, text="⚡ BEST AVIATOR", font=("Segoe UI", 13, "bold"), fg="#ef4444", bg="#111827")
        brand_lbl.pack(anchor=tk.W)

        desc_lbl = tk.Label(title_box, text="Residential Desktop Runner • Local Chrome Controller", font=("Segoe UI", 9), fg="#9ca3af", bg="#111827")
        desc_lbl.pack(anchor=tk.W)

        status_box = tk.Frame(header_frame, bg="#111827")
        status_box.pack(side=tk.RIGHT)

        self.status_badge = tk.Label(
            status_box,
            text="● OFFLINE",
            font=("Segoe UI", 9, "bold"),
            fg="#fb7185",
            bg="#27141a",
            padx=12,
            pady=4,
            relief=tk.FLAT
        )
        self.status_badge.pack(side=tk.RIGHT)

        # 2. Connection Settings Card
        settings_frame = tk.LabelFrame(main_frame, text=" Cloud Connection Parameters ", font=("Segoe UI", 9, "bold"), fg="#9ca3af", bg="#111827", padx=14, pady=10)
        settings_frame.pack(fill=tk.X, pady=(0, 14))

        # Server URL row
        url_row = tk.Frame(settings_frame, bg="#111827")
        url_row.pack(fill=tk.X, pady=4)

        tk.Label(url_row, text="Cloud Web URL:", width=15, anchor=tk.W, bg="#111827", fg="#d1d5db", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.url_entry = tk.Entry(url_row, font=("Segoe UI", 9), bg="#0a0e17", fg="#ffffff", insertbackground="#ffffff", relief=tk.SOLID, bd=1)
        self.url_entry.insert(0, self.config_data.get("server_url", "http://localhost:8000"))
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        # API Key row
        key_row = tk.Frame(settings_frame, bg="#111827")
        key_row.pack(fill=tk.X, pady=4)

        tk.Label(key_row, text="BOT_API_KEY:", width=15, anchor=tk.W, bg="#111827", fg="#d1d5db", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.key_entry = tk.Entry(key_row, font=("Segoe UI", 9), show="•", bg="#0a0e17", fg="#ffffff", insertbackground="#ffffff", relief=tk.SOLID, bd=1)
        self.key_entry.insert(0, self.config_data.get("api_key", ""))
        self.key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        self.eye_btn = tk.Button(key_row, text="👁", font=("Segoe UI", 8), bg="#1f2937", fg="#9ca3af", activebackground="#374151", relief=tk.FLAT, command=self._toggle_key_visibility, width=3)
        self.eye_btn.pack(side=tk.LEFT)

        # 3. Action Buttons Row
        action_row = tk.Frame(main_frame, bg="#0a0e17")
        action_row.pack(fill=tk.X, pady=(0, 12))

        self.connect_btn = tk.Button(
            action_row,
            text="Connect to Cloud",
            font=("Segoe UI", 9, "bold"),
            bg="#059669",
            fg="#ffffff",
            activebackground="#10b981",
            relief=tk.FLAT,
            padx=16,
            pady=6,
            command=self._toggle_connection
        )
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.test_browser_btn = tk.Button(
            action_row,
            text="Launch Browser (Local Test)",
            font=("Segoe UI", 9),
            bg="#1f2937",
            fg="#f3f4f6",
            activebackground="#374151",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            command=self._launch_browser_test
        )
        self.test_browser_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.stop_browser_btn = tk.Button(
            action_row,
            text="Stop Browser",
            font=("Segoe UI", 9),
            bg="#7f1d1d",
            fg="#fecaca",
            activebackground="#991b1b",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            command=self._stop_browser
        )
        self.stop_browser_btn.pack(side=tk.LEFT, padx=(0, 8))

        clear_btn = tk.Button(
            action_row,
            text="Clear Console",
            font=("Segoe UI", 9),
            bg="#1f2937",
            fg="#9ca3af",
            relief=tk.FLAT,
            padx=10,
            pady=6,
            command=self._clear_logs
        )
        clear_btn.pack(side=tk.RIGHT)

        # 4. Live Event Console
        console_frame = tk.LabelFrame(main_frame, text=" Real-Time Runner Telemetry & Logs ", font=("Segoe UI", 9, "bold"), fg="#9ca3af", bg="#111827", padx=10, pady=8)
        console_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            console_frame,
            font=("Consolas", 9),
            bg="#05070d",
            fg="#38bdf8",
            insertbackground="#ffffff",
            relief=tk.FLAT,
            wrap=tk.WORD,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self._append_log("[System] Desktop Agent Ready. Click 'Connect to Cloud' to link with your Web Dashboard.")

    def _toggle_key_visibility(self) -> None:
        self.key_visible = not self.key_visible
        self.key_entry.configure(show="" if self.key_visible else "•")

    def _append_log(self, message: str) -> None:
        def _insert():
            timestamp = time.strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
        self.after(0, _insert)

    def _clear_logs(self) -> None:
        self.log_text.delete("1.0", tk.END)

    def _update_status_ui(self, status: str, connected: bool) -> None:
        def _update():
            if connected:
                self.status_badge.configure(text="● ONLINE (RELAY ACTIVE)", fg="#34d399", bg="#064e3b")
                self.connect_btn.configure(text="Disconnect from Cloud", bg="#b91c1c", activebackground="#dc2626")
            elif status == "CONNECTING":
                self.status_badge.configure(text="● CONNECTING...", fg="#fbbf24", bg="#451a03")
                self.connect_btn.configure(text="Cancel Connecting", bg="#b91c1c", activebackground="#dc2626")
            else:
                self.status_badge.configure(text="● OFFLINE", fg="#fb7185", bg="#27141a")
                self.connect_btn.configure(text="Connect to Cloud", bg="#059669", activebackground="#10b981")
        self.after(0, _update)

    def _toggle_connection(self) -> None:
        if self.runner and self.runner.is_connected:
            self.runner.stop()
            self.runner = None
            self._update_status_ui("OFFLINE", False)
            self._append_log("[Agent] Disconnected from Cloud Web Platform.")
            return

        server_url = self.url_entry.get().strip()
        api_key = self.key_entry.get().strip()

        if not server_url:
            messagebox.showerror("Error", "Please enter a valid Cloud Web URL.")
            return
        if not api_key:
            messagebox.showerror("Error", "Please enter your BOT_API_KEY.")
            return

        save_local_config({"server_url": server_url, "api_key": api_key})

        self.runner = DesktopRunnerClient(
            server_url=server_url,
            api_key=api_key,
            on_log=self._append_log,
            on_status_change=self._update_status_ui,
        )
        self.runner.start()

    def _launch_browser_test(self) -> None:
        self._append_log("[Test] Testing browser launch locally...")
        threading.Thread(target=self._run_browser_test_worker, daemon=True).start()

    def _run_browser_test_worker(self) -> None:
        if not self.runner:
            self.runner = DesktopRunnerClient(
                server_url=self.url_entry.get().strip(),
                api_key=self.key_entry.get().strip(),
                on_log=self._append_log,
                on_status_change=self._update_status_ui,
            )
        self.runner._execute_prepare({"game_url": "https://www.ilotbet.com", "dry_run": False})

    def _stop_browser(self) -> None:
        if self.runner:
            self.runner._execute_stop()
        self._append_log("[Browser] Browser stopped.")

    def _on_close(self) -> None:
        if self.runner:
            self.runner.stop()
        self.destroy()


def main() -> None:
    app = DesktopAgentGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
