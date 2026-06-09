import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ALLOWED_CHAT_IDS: list[int] = [
        int(x) for x in os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "").split(",") if x.strip()
    ]
    TELEGRAM_CHAT_ID: str | None = os.getenv("TELEGRAM_CHAT_ID")

    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

    HACKERTARGET_DAILY_QUOTA: int = int(os.getenv("HACKERTARGET_DAILY_QUOTA", "100"))
    HTTP_VALIDATOR_CONCURRENCY: int = int(os.getenv("HTTP_VALIDATOR_CONCURRENCY", "50"))
    HTTP_VALIDATOR_TIMEOUT: int = int(os.getenv("HTTP_VALIDATOR_TIMEOUT_SECONDS", "5"))
    HUNTER_TIMEOUT_SECONDS: int = int(os.getenv("HUNTER_TIMEOUT_SECONDS", "90"))

    OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "./output"))

    DISABLED_HUNTERS: set[str] = {
        x.strip() for x in os.getenv("DISABLED_HUNTERS", "").split(",") if x.strip()
    }

    USE_CACHE: bool = os.getenv("USE_CACHE", "true").lower() not in ("false", "0", "no")

    DUCKDUCKGO_DELAY_MIN: float = float(os.getenv("DUCKDUCKGO_DELAY_MIN_SECONDS", "5"))
    DUCKDUCKGO_DELAY_MAX: float = float(os.getenv("DUCKDUCKGO_DELAY_MAX_SECONDS", "10"))
    YANDEX_DELAY_MIN: float = float(os.getenv("YANDEX_DELAY_MIN_SECONDS", "8"))
    YANDEX_DELAY_MAX: float = float(os.getenv("YANDEX_DELAY_MAX_SECONDS", "15"))
    MAX_VIEWDNS_PAGES: int = int(os.getenv("MAX_VIEWDNS_PAGES", "3"))

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str | None = os.getenv("LOG_FILE") or None

    HACKERTARGET_QUOTA_FILE: Path = Path.home() / ".dh_ht_quota.json"


def load_config() -> Config:
    return Config()
