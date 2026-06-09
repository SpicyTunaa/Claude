import asyncio
import logging

import aiohttp

from domain_hunter.config import Config
from domain_hunter.models import DomainRecord

logger = logging.getLogger("domain_hunter.validators.http_validator")

LIVE_STATUSES = {200, 201, 204, 301, 302, 303, 307, 308, 401, 403}


async def validate_all(
    records: list[DomainRecord],
    session: aiohttp.ClientSession,
    config: Config,
) -> list[DomainRecord]:
    sem = asyncio.Semaphore(config.HTTP_VALIDATOR_CONCURRENCY)
    tasks = [validate_one(r, session, sem, config) for r in records]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    validated = []
    for r in results:
        if isinstance(r, DomainRecord):
            validated.append(r)
        else:
            logger.debug("Validation exception: %s", r)
    return validated


async def validate_one(
    record: DomainRecord,
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    config: Config,
) -> DomainRecord:
    async with sem:
        timeout = aiohttp.ClientTimeout(total=config.HTTP_VALIDATOR_TIMEOUT)
        for scheme in ("https", "http"):
            try:
                async with session.get(
                    f"{scheme}://{record.domain}",
                    timeout=timeout,
                    allow_redirects=True,
                    max_redirects=5,
                    ssl=False,
                ) as resp:
                    record.status_code = resp.status
                    record.is_live = resp.status in LIVE_STATUSES
                    record.final_url = str(resp.url)
                    return record
            except Exception:
                continue
        record.is_live = False
        return record
