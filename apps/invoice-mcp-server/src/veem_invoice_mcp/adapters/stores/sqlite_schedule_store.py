from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import json
import os
from veem_invoice_mcp.config import ScheduleStoreConfig


@dataclass
class SqliteScheduleStore:
    """POC schedule store.

    In production, replace this with a PaymentDomain scheduling API adapter.
    """

    cfg: ScheduleStoreConfig

    def _connect(self) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(self.cfg.sqlite_path), exist_ok=True)
        conn = sqlite3.connect(self.cfg.sqlite_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scheduled_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at_utc TEXT NOT NULL,
                run_at_utc TEXT NOT NULL,
                draft_json TEXT NOT NULL,
                status TEXT NOT NULL
            )
            """
        )
        return conn

    async def create(self, *, draft: dict[str, Any], run_at_utc: str) -> dict[str, Any]:
        # Validate datetime
        datetime.fromisoformat(run_at_utc.replace("Z", "+00:00"))
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO scheduled_payments (created_at_utc, run_at_utc, draft_json, status) VALUES (?, ?, ?, ?)",
                (datetime.now(timezone.utc).isoformat(), run_at_utc, json.dumps(draft), "scheduled"),
            )
            conn.commit()
            schedule_id = cur.lastrowid
            return {"schedule_id": str(schedule_id), "status": "scheduled", "run_at_utc": run_at_utc}
        finally:
            conn.close()
