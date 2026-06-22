import logging
from abc import ABC, abstractmethod

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from domain_hunter import cache
from domain_hunter.config import Config
from domain_hunter.models import DomainRecord
from domain_hunter.rate_limiter import RateLimiter, QuotaExhaustedError
from domain_hunter.utils.http_client import build_headers

logger = logging.getLogger("domain_hunter.hunters")


class BaseHunter(ABC):
    SOURCE_NAME: str = ""

    def __init__(self, session: aiohttp.ClientSession, rate_limiter: RateLimiter, config: Config):
        self.session = session
        self.rate_limiter = rate_limiter
        self.config = config
        self.logger = logging.getLogger(f"domain_hunter.hunters.{self.SOURCE_NAME}")

    @abstractmethod
    async def _do_hunt(self, seed_domain: str, vertical: str) -> list[str]:
        """Return raw domain strings."""
        ...

    async def hunt(self, seed_domain: str, vertical: str) -> list[DomainRecord]:
        cached = cache.load(self.SOURCE_NAME, seed_domain, self.config.USE_CACHE)
        if cached is not None:
            self.logger.info("%s: cache hit (%d domains)", self.SOURCE_NAME, len(cached))
            return [self._make_record(d) for d in cached]

        domains = await self._do_hunt(seed_domain, vertical)
        cache.save(self.SOURCE_NAME, seed_domain, domains)
        return [self._make_record(d) for d in domains]

    async def _get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        try:
            await self.rate_limiter.acquire(self.SOURCE_NAME)
        except QuotaExhaustedError as e:
            self.logger.warning("%s", e)
            raise

        headers = kwargs.pop("headers", build_headers())
        return await self._get_with_retry(url, headers=headers, **kwargs)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(aiohttp.ClientError),
        reraise=True,
    )
    async def _get_with_retry(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        return await self.session.get(url, **kwargs)

    def _make_record(self, domain: str) -> DomainRecord:
        return DomainRecord(domain=domain.lower().strip(), sources={self.SOURCE_NAME})
