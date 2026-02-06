from __future__ import annotations

from dataclasses import dataclass

from veem_invoice_mcp.config import CONFIG
from veem_invoice_mcp.adapters.veem_api import VeemApiClient
from veem_invoice_mcp.adapters.stores.mysql_history_store import (
    PaymentHistoryStore,
    MySqlPaymentHistoryStore,
    NullPaymentHistoryStore,
)
from veem_invoice_mcp.adapters.stores.sqlite_schedule_store import SqliteScheduleStore
from veem_invoice_mcp.domain.invoice.extractor import (
    InvoiceExtractor,
    OpenAIInvoiceExtractor,
    NullInvoiceExtractor,
)


@dataclass
class Dependencies:
    veem: VeemApiClient
    history_store: PaymentHistoryStore
    schedule_store: SqliteScheduleStore
    invoice_extractor: InvoiceExtractor


def build_dependencies() -> Dependencies:
    # Veem API client
    veem = VeemApiClient(CONFIG.veem)

    # Optional history store
    history_store: PaymentHistoryStore
    if all([CONFIG.mysql.host, CONFIG.mysql.user, CONFIG.mysql.password, CONFIG.mysql.database]):
        history_store = MySqlPaymentHistoryStore(CONFIG.mysql)
    else:
        history_store = NullPaymentHistoryStore()

    # Schedule store (SQLite POC)
    schedule_store = SqliteScheduleStore(CONFIG.schedule_store)

    # Invoice extractor (LLM)
    if CONFIG.openai.api_key:
        invoice_extractor = OpenAIInvoiceExtractor(CONFIG.openai)
    else:
        invoice_extractor = NullInvoiceExtractor()

    return Dependencies(
        veem=veem,
        history_store=history_store,
        schedule_store=schedule_store,
        invoice_extractor=invoice_extractor,
    )


DEPS = build_dependencies()
