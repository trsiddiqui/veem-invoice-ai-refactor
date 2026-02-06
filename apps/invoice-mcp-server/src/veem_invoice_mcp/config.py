"""Configuration for the Invoice MCP server.

All configuration is via environment variables so the server can run in:
- local dev (dotenv)
- container deploy (Smithery / k8s)
- managed infra

The MCP server itself should be able to *list tools* without requiring secrets.
Tools that need Veem/OpenAI credentials fail with a clear error when invoked.
"""

from __future__ import annotations

from dataclasses import dataclass
import os


def _env(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name)
    return v if v not in (None, "") else default


@dataclass(frozen=True)
class VeemConfig:
    base_url: str = _env("VEEM_API_BASE_URL", "https://api.qa.veem.com/veem/v1.2")  # POC default
    account_id: str | None = _env("VEEM_ACCOUNT_ID")
    access_token: str | None = _env("VEEM_ACCESS_TOKEN")


@dataclass(frozen=True)
class OpenAIConfig:
    api_key: str | None = _env("OPENAI_API_KEY")
    model: str = _env("OPENAI_INVOICE_MODEL", "gpt-4.1-mini")  # pick your preferred default
    temperature: float = float(_env("OPENAI_TEMPERATURE", "0") or "0")


@dataclass(frozen=True)
class MySQLConfig:
    host: str | None = _env("VEEM_MYSQL_HOST")
    user: str | None = _env("VEEM_MYSQL_USER")
    password: str | None = _env("VEEM_MYSQL_PASSWORD")
    database: str | None = _env("VEEM_MYSQL_DATABASE")


@dataclass(frozen=True)
class ScheduleStoreConfig:
    sqlite_path: str = _env("VEEM_SCHEDULE_SQLITE_PATH", "./.data/schedules.sqlite") or "./.data/schedules.sqlite"


@dataclass(frozen=True)
class AppConfig:
    veem: VeemConfig = VeemConfig()
    openai: OpenAIConfig = OpenAIConfig()
    mysql: MySQLConfig = MySQLConfig()
    schedule_store: ScheduleStoreConfig = ScheduleStoreConfig()


CONFIG = AppConfig()
