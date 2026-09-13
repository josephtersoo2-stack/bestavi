from __future__ import annotations

import sqlite3
import threading
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class RoundRecord:
    stake: float
    result: str
    multiplier: float
    profit_loss: float
    balance: float
    time: str | None = None
    site: str = "ilotbet"


class SQLiteHistory:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # The controller records rounds from its worker thread while the UI may
        # read recent history from the main thread.
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._lock = threading.Lock()
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("""
            CREATE TABLE IF NOT EXISTS round_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TEXT NOT NULL,
                stake REAL NOT NULL,
                result TEXT NOT NULL,
                multiplier REAL NOT NULL,
                profit_loss REAL NOT NULL,
                balance REAL NOT NULL,
                site TEXT NOT NULL DEFAULT 'ilotbet'
            )
        """)
        self._connection.execute("""
            CREATE TABLE IF NOT EXISTS observed_rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TEXT NOT NULL,
                phase TEXT NOT NULL,
                multiplier REAL,
                balance REAL,
                site TEXT NOT NULL DEFAULT 'ilotbet'
            )
        """)
        # Migrate databases created before platform-aware history was added.
        self._ensure_column("round_history", "site", "TEXT NOT NULL DEFAULT 'ilotbet'")
        self._ensure_column("observed_rounds", "site", "TEXT NOT NULL DEFAULT 'ilotbet'")
        self._connection.commit()

    def record(self, record: RoundRecord) -> int:
        timestamp = record.time or datetime.now(timezone.utc).isoformat()
        with self._lock:
            cur = self._connection.execute(
                "INSERT INTO round_history(time, stake, result, multiplier, profit_loss, balance, site) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (timestamp, record.stake, record.result, record.multiplier, record.profit_loss, record.balance, record.site),
            )
            self._connection.commit()
        return int(cur.lastrowid)

    def recent(self, limit: int = 50, site: str | None = None) -> list[dict]:
        with self._lock:
            if site:
                rows = self._connection.execute("SELECT * FROM round_history WHERE site = ? ORDER BY id DESC LIMIT ?", (site, limit)).fetchall()
            else:
                rows = self._connection.execute("SELECT * FROM round_history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]

    def record_observation(self, phase: str, multiplier: float | None, balance: float | None,
                           time_value: str | None = None, site: str = "ilotbet") -> int:
        timestamp = time_value or datetime.now(timezone.utc).isoformat()
        with self._lock:
            cur = self._connection.execute(
                "INSERT INTO observed_rounds(time, phase, multiplier, balance, site) VALUES (?, ?, ?, ?, ?)",
                (timestamp, phase, multiplier, balance, site),
            )
            self._connection.commit()
        return int(cur.lastrowid)

    def recent_observations(self, limit: int = 50, site: str | None = None) -> list[dict]:
        with self._lock:
            if site:
                rows = self._connection.execute("SELECT * FROM observed_rounds WHERE site = ? ORDER BY id DESC LIMIT ?", (site, limit)).fetchall()
            else:
                rows = self._connection.execute("SELECT * FROM observed_rounds ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]

    def append_dataset_file(self, site: str, multiplier: float, timestamp: str | None = None) -> None:
        """Automatically append an extracted round to the continuous dataset file for LLM / data analysis."""
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        site_clean = site.lower().strip()
        data_dir = self.path.parent
        data_dir.mkdir(parents=True, exist_ok=True)
        txt_path = data_dir / f"{site_clean}_crash_history.txt"
        csv_path = data_dir / f"{site_clean}_crash_history.csv"

        # 1. Append to TXT
        if not txt_path.exists():
            txt_path.write_text(f"# Platform: {site_clean.upper()} Aviator Crash Dataset\n# Format: Timestamp | Multiplier\n", encoding="utf-8")
        with open(txt_path, "a", encoding="utf-8") as f:
            f.write(f"{ts} | {multiplier:.2f}x\n")

        # 2. Append to CSV
        if not csv_path.exists():
            csv_path.write_text(f"# Platform: {site_clean.upper()}\nTimestamp,Multiplier\n", encoding="utf-8")
        with open(csv_path, "a", encoding="utf-8") as f:
            f.write(f"{ts},{multiplier:.2f}x\n")

    def export_observations(self, fmt: str, site: str | None = None, limit: int = 500) -> str:
        """Return recent crash results as clean text, CSV, JSON, or Markdown without personal balance."""
        rows = list(reversed(self.recent_observations(limit, site)))
        valid_rows = [r for r in rows if r.get("multiplier") is not None]
        site_header = (site or "ilotbet").upper()
        normalized = fmt.lower().lstrip(".")

        if normalized == "csv":
            title = f"# Platform: {site_header}\nTimestamp,Platform,Result\n"
            body = "".join(f"{row['time']},{row.get('site', 'ilotbet')},{row['multiplier']:.2f}x\n" for row in valid_rows)
            return title + body

        if normalized == "json":
            data = {
                "platform": site_header,
                "site": (site or "ilotbet").lower(),
                "data": [{"time": row["time"], "site": row.get("site", "ilotbet"), "result": f"{row['multiplier']:.2f}x"} for row in valid_rows]
            }
            return json.dumps(data, indent=2, ensure_ascii=False) + "\n"

        if normalized in {"md", "markdown"}:
            title = f"# Platform: {site_header} Aviator Crash History\n\n"
            header = "| Time | Platform | Result |\n|---|---|---:|\n"
            body = "".join(f"| {row['time']} | {row.get('site', 'ilotbet')} | {row['multiplier']:.2f}x |\n" for row in valid_rows)
            return title + header + body

        if normalized not in {"txt", "text"}:
            raise ValueError("format must be txt, csv, json, or md")

        title = f"# Platform: {site_header} Aviator Crash History\n# Format: Timestamp | Platform | Result\n"
        body = "".join(f"{row['time']} | {row.get('site', 'ilotbet')} | {row['multiplier']:.2f}x\n" for row in valid_rows)
        return title + body

    def _ensure_column(self, table: str, column: str, definition: str) -> None:
        columns = {row[1] for row in self._connection.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in columns:
            self._connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "SQLiteHistory": return self
    def __exit__(self, *_: object) -> None: self.close()
