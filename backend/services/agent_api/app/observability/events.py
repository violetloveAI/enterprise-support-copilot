from __future__ import annotations

import json
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class RunRepository:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.setup()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def setup(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                  run_id TEXT PRIMARY KEY, thread_id TEXT NOT NULL, status TEXT NOT NULL,
                  query TEXT NOT NULL, result_json TEXT,
                  created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS run_events (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  run_id TEXT NOT NULL, sequence INTEGER NOT NULL,
                  timestamp TEXT NOT NULL, event_type TEXT NOT NULL, node_name TEXT NOT NULL,
                  status TEXT NOT NULL, duration_ms INTEGER, details_json TEXT NOT NULL
                );
                """
            )

    def start_run(self, run_id: str, thread_id: str, query: str) -> None:
        now = datetime.now(UTC).isoformat()
        with self._lock, self.connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO runs VALUES (?, ?, 'running', ?, NULL, ?, ?)",
                (run_id, thread_id, query, now, now),
            )

    def event(
        self,
        run_id: str,
        event_type: str,
        node_name: str,
        status: str = "completed",
        duration_ms: int | None = None,
        **details: Any,
    ) -> None:
        with self._lock, self.connect() as connection:
            sequence = connection.execute(
                "SELECT COALESCE(MAX(sequence), 0) + 1 FROM run_events WHERE run_id = ?", (run_id,)
            ).fetchone()[0]
            connection.execute(
                """INSERT INTO run_events(
                    run_id, sequence, timestamp, event_type, node_name,
                    status, duration_ms, details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id,
                    sequence,
                    datetime.now(UTC).isoformat(),
                    event_type,
                    node_name,
                    status,
                    duration_ms,
                    json.dumps(details, ensure_ascii=False, default=str),
                ),
            )

    def finish(self, run_id: str, status: str, result: dict[str, Any]) -> None:
        with self._lock, self.connect() as connection:
            connection.execute(
                "UPDATE runs SET status = ?, result_json = ?, updated_at = ? WHERE run_id = ?",
                (
                    status,
                    json.dumps(result, ensure_ascii=False, default=str),
                    datetime.now(UTC).isoformat(),
                    run_id,
                ),
            )

    def get(self, run_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            run = connection.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if not run:
            return None
        value = dict(run)
        value["result"] = json.loads(value.pop("result_json")) if value["result_json"] else None
        return value

    def events(self, run_id: str) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM run_events WHERE run_id = ? ORDER BY sequence", (run_id,)
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["details"] = json.loads(item.pop("details_json"))
            result.append(item)
        return result
