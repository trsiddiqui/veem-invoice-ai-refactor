from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Optional
import logging

from veem_invoice_mcp.config import MySQLConfig

logger = logging.getLogger(__name__)


class PaymentHistoryStore(Protocol):
    async def last_funding_method_id_for_payee(self, payee_email: str) -> Optional[str]:
        ...


@dataclass
class NullPaymentHistoryStore:
    async def last_funding_method_id_for_payee(self, payee_email: str) -> Optional[str]:
        return None


class MySqlPaymentHistoryStore:
    """Optional adapter that mirrors the old POC logic (query last payment funding method).

    This is intentionally isolated behind an interface so unit tests do not need MySQL.
    """

    def __init__(self, cfg: MySQLConfig):
        self._cfg = cfg

    def _enabled(self) -> bool:
        return all([self._cfg.host, self._cfg.user, self._cfg.password, self._cfg.database])

    async def last_funding_method_id_for_payee(self, payee_email: str) -> Optional[str]:
        if not self._enabled():
            return None

        # Import only when needed (keeps tool listing usable without MySQL deps).
        import mysql.connector  # type: ignore

        # NOTE: Query shape here is a placeholder; swap to your real schema.
        query = """
        SELECT payer_funding_method_id
        FROM payments
        WHERE payee_email = %s
        ORDER BY created_at DESC
        LIMIT 1
        """
        try:
            conn = mysql.connector.connect(
                host=self._cfg.host,
                user=self._cfg.user,
                password=self._cfg.password,
                database=self._cfg.database,
            )
            cur = conn.cursor()
            cur.execute(query, (payee_email,))
            row = cur.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.warning("MySQL history lookup failed: %s", e)
            return None
        finally:
            try:
                cur.close()
                conn.close()
            except Exception:
                pass
