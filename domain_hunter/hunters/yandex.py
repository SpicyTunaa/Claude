import asyncio
import logging
import random
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from domain_hunter.hunters.base import BaseHunter
from domain_hunter.utils.http_client import build_headers

logger = logging.getLogger("domain_hunter.hunters.yandex")

YANDEX_URL = "https://yandex.com/search/?text={query}&lr=213"
DOMAIN_RE = re.compile(r"https?://([a-zA-Z0-9.-]+)")


class YandexBlockedError(Exception):
    pass


class YandexHunter(BaseHunter):
    SOURCE_NAME = "yandex"

    async def _do_hunt(self, seed_domain: str, vertical: str) -> list[str]:
        domains: set[str] = set()

        for query in [f"site:{seed_domain}"]:
            try:
                found = await self._search(query)
                domains.update(found)
            except YandexBlockedError:
                self.logger.warning("Yandex blocked request, backing off 60s")
                await asyncio.sleep(60)
                break

            await asyncio.sleep(random.uniform(self.config.YANDEX_DELAY_MIN, self.config.YANDEX_DELAY_MAX))

        self.logger.info("Yandex found %d domains for %s", len(domains), seed_domain)
        return list(domains)

    async def _search(self, query: str) -> list[str]:
        url = YANDEX_URL.format(query=query.replace(" ", "+"))
        headers = build_headers()
        headers["Accept-Language"] = "ru-RU,ru;q=0.9,en;q=0.8"
        headers["Referer"] = "https://yandex.com/"

        try:
            async with await self._get(url, headers=headers) as resp:
                if resp.status in (429, 403):
                    raise YandexBlockedError(f"HTTP {resp.status}")
                if resp.status != 200:
                    self.logger.warning("Yandex returned %d", resp.status)
                    return []
                html = await resp.text()
        except YandexBlockedError:
            raise
        except Exception as e:
            self.logger.error("Yandex error: %s", e)
            return []

        if "captcha" in html.lower()[:1000]:
            raise YandexBlockedError("CAPTCHA detected")

        soup = BeautifulSoup(html, "lxml")
        domains = []

        for item in soup.find_all(class_=lambda c: c and "serp-item" in c):
            for link in item.find_all("a", href=True):
                href = link["href"]
                if href.startswith("http"):
                    parsed = urlparse(href)
                    if parsed.netloc:
                        domains.append(parsed.netloc.lower().lstrip("www."))

        for match in DOMAIN_RE.findall(html):
            domains.append(match.lower().lstrip("www."))

        return list(set(d for d in domains if "." in d))
