import fcntl
import json
import logging
from datetime import datetime
from pathlib import Path

from aiolimiter import AsyncLimiter

logger = logging.getLogger("domain_hunter.rate_limiter")

# (max_rate requests, per time_period seconds)
SOURCE_RATES: dict[str, tuple[float, float]] = {
    "crtsh":        (1,    1),    # 1 req/s
    "hackertarget": (1,    2),    # 1 req/2s
    "viewdns":      (1,    3),    # 1 req/3s
    "duckduckgo":   (1,    7),    # 1 req/7s
    "yandex":       (1,   10),    # 1 req/10s
    "reddit":       (1,    2),    # 1 req/2s
    "github":       (1,    6),    # 10 req/min
    "dns_expander": (2,    1),    # 2 req/s
}

DAILY_QUOTAS: dict[str, int] = {
    "hackertarget": 95,
}


class QuotaExhaustedError(Exception):
    pass


class RateLimiter:
    def __init__(self, quota_file: Path):
        self.quota_file = quota_file
        self._limiters: dict[str, AsyncLimiter] = {
            source: AsyncLimiter(max_rate=rate, time_period=period)
            for source, (rate, period) in SOURCE_RATES.items()
        }

    async def acquire(self, source_name: str) -> None:
        if source_name in DAILY_QUOTAS:
            self._check_daily_quota(source_name)
        if source_name in self._limiters:
            await self._limiters[source_name].acquire()

    def get_quota_status(self, source_name: str) -> dict:
        today = datetime.utcnow().date().isoformat()
        data = self._load_quota()
        entry = data.get(source_name, {"date": today, "count": 0})
        if entry["date"] != today:
            entry = {"date": today, "count": 0}
        return {
            "used": entry["count"],
            "limit": DAILY_QUOTAS.get(source_name),
            "date": entry["date"],
        }

    def _check_daily_quota(self, source_name: str) -> None:
        today = datetime.utcnow().date().isoformat()
        data = self._load_quota()
        entry = data.setdefault(source_name, {"date": today, "count": 0})

        if entry["date"] != today:
            entry.update({"date": today, "count": 0})

        if entry["count"] >= DAILY_QUOTAS[source_name]:
            raise QuotaExhaustedError(
                f"{source_name} daily quota of {DAILY_QUOTAS[source_name]} exhausted"
            )

        entry["count"] += 1
        self._save_quota(data)

    def _load_quota(self) -> dict:
        if not self.quota_file.exists():
            return {}
        try:
            with open(self.quota_file, "r") as f:
                fcntl.flock(f, fcntl.LOCK_SH)
                data = json.load(f)
                fcntl.flock(f, fcntl.LOCK_UN)
            return data
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_quota(self, data: dict) -> None:
        self.quota_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.quota_file, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            json.dump(data, f)
            fcntl.flock(f, fcntl.LOCK_UN)
