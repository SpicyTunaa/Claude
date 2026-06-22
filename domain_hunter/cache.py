import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger("domain_hunter.cache")

CACHE_TTL_HOURS = 24
CACHE_DIR = Path(".cache/domain_hunter")


def _key(source: str, seed: str) -> str:
    return hashlib.sha256(f"{source}:{seed}".encode()).hexdigest()[:16]


def _cache_path(source: str, seed: str) -> Path:
    return CACHE_DIR / f"{_key(source, seed)}.json"


def load(source: str, seed: str, use_cache: bool = True) -> Optional[list[str]]:
    if not use_cache:
        return None
    path = _cache_path(source, seed)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        created = datetime.fromisoformat(data["created_at"])
        if datetime.utcnow() - created > timedelta(hours=CACHE_TTL_HOURS):
            logger.debug("Cache expired for %s:%s", source, seed)
            return None
        logger.debug("Cache hit for %s:%s (%d domains)", source, seed, len(data["domains"]))
        return data["domains"]
    except (KeyError, ValueError, json.JSONDecodeError):
        return None


def save(source: str, seed: str, domains: list[str]) -> None:
    if not domains:
        return  # Never cache empty results — let the next run retry
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_path(source, seed)
    data = {
        "source": source,
        "seed": seed,
        "created_at": datetime.utcnow().isoformat(),
        "domains": domains,
    }
    path.write_text(json.dumps(data, indent=2))
    logger.debug("Cache saved for %s:%s (%d domains)", source, seed, len(domains))
