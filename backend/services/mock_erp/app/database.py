from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[3]

SEED_FILES = {
    "users": "users.json",
    "permissions": "permissions.json",
    "claims": "claims.json",
    "approval_flows": "approval_flows.json",
    "vouchers": "vouchers.json",
    "interface_logs": "interface_logs.json",
    "tickets": "tickets.json",
}
PRIMARY_KEYS = {
    "users": "user_id",
    "permissions": "user_id",
    "claims": "claim_id",
    "approval_flows": "claim_id",
    "vouchers": "claim_id",
    "interface_logs": "log_id",
    "tickets": "ticket_id",
}


def db_path() -> Path:
    return Path(os.getenv("ERP_DB_PATH", str(BACKEND_ROOT / "runtime/erp.db")))


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def seed_database(force: bool = False, data_dir: str | Path | None = None) -> Path:
    path = db_path()
    if force and path.exists():
        path.unlink()
    with connect() as connection:
        for table, filename in SEED_FILES.items():
            connection.execute(
                f"""CREATE TABLE IF NOT EXISTS {table} (
                    record_id TEXT PRIMARY KEY, payload TEXT NOT NULL
                )"""
            )
            if connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]:
                continue
            source_dir = Path(data_dir) if data_dir else BACKEND_ROOT / "data/synthetic"
            rows = json.loads((source_dir / filename).read_text(encoding="utf-8"))
            for index, row in enumerate(rows):
                record_id = str(row.get(PRIMARY_KEYS[table]) or index)
                connection.execute(
                    f"INSERT INTO {table}(record_id, payload) VALUES (?, ?)",
                    (record_id, json.dumps(row, ensure_ascii=False)),
                )
    return path


def get_one(table: str, record_id: str) -> dict[str, Any] | None:
    with connect() as connection:
        row = connection.execute(
            f"SELECT payload FROM {table} WHERE record_id = ?", (record_id,)
        ).fetchone()
    return json.loads(row["payload"]) if row else None


def find_many(table: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute(f"SELECT payload FROM {table}").fetchall()
    values = [json.loads(row["payload"]) for row in rows]
    return [
        item for item in values if all(item.get(key) == value for key, value in filters.items())
    ]


def insert(table: str, record_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    with connect() as connection:
        connection.execute(
            f"INSERT INTO {table}(record_id, payload) VALUES (?, ?)",
            (record_id, json.dumps(payload, ensure_ascii=False)),
        )
    return payload


def count(table: str) -> int:
    with connect() as connection:
        return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
