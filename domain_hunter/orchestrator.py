import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime

import aiohttp

from domain_hunter.config import Config
from domain_hunter.deduplicator import merge
from domain_hunter.hunters.crtsh import CrtShHunter
from domain_hunter.hunters.dns_expander import DnsExpanderHunter
from domain_hunter.hunters.duckduckgo import DuckDuckGoHunter
from domain_hunter.hunters.github import GitHubHunter
from domain_hunter.hunters.hackertarget import HackerTargetHunter
from domain_hunter.hunters.reddit import RedditHunter
from domain_hunter.hunters.viewdns import ViewDnsHunter
from domain_hunter.hunters.yandex import YandexHunter
from domain_hunter.models import DomainRecord, HuntResult, ProgressEvent
from domain_hunter.rate_limiter import RateLimiter
from domain_hunter.validators import domain_filter, http_validator

logger = logging.getLogger("domain_hunter.orchestrator")

HUNTER_CLASSES = [
    CrtShHunter,
    HackerTargetHunter,
    ViewDnsHunter,
    DuckDuckGoHunter,
    YandexHunter,
    RedditHunter,
    GitHubHunter,
    DnsExpanderHunter,
]


async def _run_hunter_with_timeout(
    hunter, seed_domain: str, vertical: str, timeout: int
) -> tuple[str, list[DomainRecord] | str]:
    try:
        result = await asyncio.wait_for(
            hunter.hunt(seed_domain, vertical),
            timeout=timeout,
        )
        return hunter.SOURCE_NAME, result
    except asyncio.TimeoutError:
        return hunter.SOURCE_NAME, "timeout"
    except Exception as e:
        return hunter.SOURCE_NAME, f"error: {e}"


def _print_summary(
    hunter_results: dict[str, list[DomainRecord] | str],
    total_unique: int,
    live_count: int,
    rate_limiter: RateLimiter,
) -> None:
    logger.info("─" * 50)
    logger.info("Hunt summary:")
    for source, result in hunter_results.items():
        if isinstance(result, list):
            logger.info("  %-16s %d domains", source + ":", len(result))
        else:
            logger.info("  %-16s %s", source + ":", result)
    ht_status = rate_limiter.get_quota_status("hackertarget")
    logger.info("  HackerTarget quota: %d/%d used", ht_status["used"], ht_status["limit"])
    logger.info("─" * 50)
    logger.info("  total unique: %d  |  live: %d", total_unique, live_count)
    logger.info("─" * 50)


async def run_hunt(
    seed_domain: str,
    vertical: str,
    config: Config,
    validate: bool = True,
    hunt_id: str | None = None,
    progress_callback: Callable[[ProgressEvent], Awaitable[None]] | None = None,
) -> HuntResult:
    started_at = datetime.utcnow()
    rate_limiter = RateLimiter(config.HACKERTARGET_QUOTA_FILE)

    async def _emit(event: str, **kwargs) -> None:
        if progress_callback and hunt_id:
            await progress_callback(ProgressEvent(hunt_id=hunt_id, event=event, **kwargs))

    connector = aiohttp.TCPConnector(limit=100, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        active = [
            H(session, rate_limiter, config)
            for H in HUNTER_CLASSES
            if H.SOURCE_NAME not in config.DISABLED_HUNTERS
        ]

        logger.info("Hunt started: seed=%s vertical=%s hunters=%d", seed_domain, vertical, len(active))

        tasks = [
            asyncio.create_task(
                _run_hunter_with_timeout(h, seed_domain, vertical, config.HUNTER_TIMEOUT_SECONDS)
            )
            for h in active
        ]

        raw: list[DomainRecord] = []
        hunter_results: dict[str, list[DomainRecord] | str] = {}

        for future in asyncio.as_completed(tasks):
            source, result = await future
            hunter_results[source] = result
            if isinstance(result, list):
                raw.extend(result)
            count = len(result) if isinstance(result, list) else 0
            await _emit(
                "hunter_done",
                hunter_name=source,
                domains_found=count,
                total_so_far=len(raw),
                message=result if isinstance(result, str) else None,
            )

        logger.info("Raw records collected: %d", len(raw))

        filtered = domain_filter.apply(raw)
        logger.info("After domain filter: %d", len(filtered))
        await _emit("filter_done", total_so_far=len(filtered))

        deduped = merge(filtered)
        logger.info("After dedup: %d unique domains", len(deduped))
        await _emit("dedup_done", total_so_far=len(deduped))

        if validate:
            logger.info("HTTP validation starting for %d domains...", len(deduped))
            await _emit("validation_start", total_so_far=len(deduped))
            deduped = await http_validator.validate_all(deduped, session, config)
            live = sum(1 for r in deduped if r.is_live)
            for r in deduped:
                if r.is_live:
                    r.confidence_score = round(min(1.0, r.confidence_score + 0.1), 3)
            await _emit("validation_done", total_so_far=len(deduped),
                        message=f"{live} live")
        else:
            live = 0

        _print_summary(hunter_results, len(deduped), live, rate_limiter)

        return HuntResult(
            seed_domain=seed_domain,
            vertical=vertical,
            records=deduped,
            started_at=started_at,
            finished_at=datetime.utcnow(),
        )
