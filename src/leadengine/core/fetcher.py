"""Async HTTP fetcher: per-domain rate limiting, retries, User-Agent rotation, robots.txt.

This is the single shared network primitive. Adapters and enrichment never create their
own HTTP clients — they receive a :class:`Fetcher` via the run context so politeness and
compliance are enforced centrally.
"""

from __future__ import annotations

import asyncio
import urllib.robotparser
from dataclasses import dataclass

import httpx
from aiolimiter import AsyncLimiter
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import FetcherConfig
from .logging import get_logger
from .models import extract_host

log = get_logger("fetcher")

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class RobotsDisallowed(Exception):
    """Raised when robots.txt disallows fetching a URL and enforcement is on."""


@dataclass
class FetchResult:
    url: str
    status_code: int
    text: str
    headers: dict[str, str]


class Fetcher:
    def __init__(self, config: FetcherConfig, client: httpx.AsyncClient | None = None):
        self._config = config
        self._client = client
        self._owns_client = client is None
        self._limiters: dict[str, AsyncLimiter] = {}
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self._robots_locks: dict[str, asyncio.Lock] = {}
        self._ua_index = 0

    async def __aenter__(self) -> Fetcher:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self._config.timeout, follow_redirects=True
            )
            self._owns_client = True
        return self

    async def __aexit__(self, *exc) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()

    # -- helpers -----------------------------------------------------------------------

    def _next_user_agent(self) -> str:
        uas = self._config.user_agents or ["LeadEngineBot/0.1"]
        ua = uas[self._ua_index % len(uas)]
        self._ua_index += 1
        return ua

    def _limiter_for(self, host: str, rate_limit: float | None) -> AsyncLimiter:
        rate = rate_limit or self._config.default_rate_limit
        key = f"{host}:{rate}"
        if key not in self._limiters:
            # rate requests per 1 second window.
            self._limiters[key] = AsyncLimiter(max_rate=max(rate, 0.001), time_period=1.0)
        return self._limiters[key]

    async def _allowed_by_robots(self, url: str, user_agent: str) -> bool:
        if not self._config.respect_robots:
            return True
        host = extract_host(url)
        if host not in self._robots_locks:
            self._robots_locks[host] = asyncio.Lock()
        async with self._robots_locks[host]:
            if host not in self._robots:
                self._robots[host] = await self._load_robots(url)
        parser = self._robots[host]
        if parser is None:  # fail-open when robots.txt cannot be retrieved
            return True
        return parser.can_fetch(user_agent, url)

    async def _load_robots(self, url: str):
        scheme = url.split("://", 1)[0] if "://" in url else "https"
        host = extract_host(url)
        robots_url = f"{scheme}://{host}/robots.txt"
        parser = urllib.robotparser.RobotFileParser()
        try:
            assert self._client is not None
            resp = await self._client.get(robots_url)
            if resp.status_code >= 400:
                return None
            parser.parse(resp.text.splitlines())
            return parser
        except Exception:  # noqa: BLE001 — robots failures fail open
            return None

    # -- public API --------------------------------------------------------------------

    async def fetch(self, url: str, *, rate_limit: float | None = None) -> FetchResult:
        """GET a URL with rate limiting, robots check, UA rotation and retries.

        Raises :class:`RobotsDisallowed` if blocked, or the last httpx error on failure.
        """
        assert self._client is not None, "Fetcher must be used as an async context manager"
        host = extract_host(url)
        user_agent = self._next_user_agent()

        if not await self._allowed_by_robots(url, user_agent):
            log.info("robots_disallowed", url=url)
            raise RobotsDisallowed(url)

        limiter = self._limiter_for(host, rate_limit)

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self._config.max_retries),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
            retry=retry_if_exception_type((httpx.TransportError, _RetryableStatus)),
            reraise=True,
        ):
            with attempt:
                async with limiter:
                    resp = await self._client.get(url, headers={"User-Agent": user_agent})
                if resp.status_code in _RETRYABLE_STATUS:
                    raise _RetryableStatus(resp.status_code)
                return FetchResult(
                    url=str(resp.url),
                    status_code=resp.status_code,
                    text=resp.text,
                    headers={k.lower(): v for k, v in resp.headers.items()},
                )
        raise RuntimeError("unreachable")  # pragma: no cover

    async def try_fetch(self, url: str, *, rate_limit: float | None = None) -> FetchResult | None:
        """Like :meth:`fetch` but returns ``None`` instead of raising — handy for enrichment."""
        try:
            return await self.fetch(url, rate_limit=rate_limit)
        except (httpx.HTTPError, RobotsDisallowed, RuntimeError) as exc:
            log.info("fetch_failed", url=url, error=str(exc))
            return None


class _RetryableStatus(Exception):
    def __init__(self, status_code: int):
        super().__init__(f"retryable status {status_code}")
        self.status_code = status_code
