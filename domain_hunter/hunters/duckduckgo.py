import asyncio
import logging
import random
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from domain_hunter.hunters.base import BaseHunter
from domain_hunter.utils.http_client import build_headers

logger = logging.getLogger("domain_hunter.hunters.duckduckgo")

DDG_URL = "https://html.duckduckgo.com/html/?q={query}"
DOMAIN_RE = re.compile(r"https?://([a-zA-Z0-9.-]+)")


class DuckDuckGoHunter(BaseHunter):
    SOURCE_NAME = "duckduckgo"

    async def _do_hunt(self, seed_domain: str, vertical: str) -> list[str]:
        queries = [
            f"site:*.{seed_domain}",
            f"{vertical} {seed_domain} domains",
        ]

        domains: set[str] = set()
        for query in queries:
            found = await self._search(query)
            domains.update(found)
            await asyncio.sleep(random.uniform(self.config.DUCKDUCKGO_DELAY_MIN, self.config.DUCKDUCKGO_DELAY_MAX))

        self.logger.info("DuckDuckGo found %d domains for %s", len(domains), seed_domain)
        return list(domains)

    async def _search(self, query: str) -> list[str]:
        url = DDG_URL.format(query=query.replace(" ", "+"))
        headers = build_headers(include_referer=True)

        try:
            async with await self._get(url, headers=headers) as resp:
                if resp.status != 200:
                    self.logger.warning("DuckDuckGo returned %d, trying fallback", resp.status)
                    return self._fallback_search(query)
                html = await resp.text()
        except Exception as e:
            self.logger.error("DuckDuckGo scrape error: %s", e)
            return self._fallback_search(query)

        soup = BeautifulSoup(html, "lxml")
        domains = []

        for link in soup.find_all("a", class_="result__url"):
            href = link.get("href", "")
            if href:
                if not href.startswith("http"):
                    href = f"https://{href}"
                parsed = urlparse(href)
                if parsed.netloc:
                    domains.append(parsed.netloc.lower().lstrip("www."))

        for match in DOMAIN_RE.findall(html):
            domains.append(match.lower().lstrip("www."))

        return list(set(d for d in domains if "." in d))

    def _fallback_search(self, query: str) -> list[str]:
        try:
            from duckduckgo_search import DDGS
            results = list(DDGS().text(query, max_results=30))
            domains = []
            for r in results:
                url = r.get("href", "")
                if url:
                    parsed = urlparse(url)
                    if parsed.netloc:
                        domains.append(parsed.netloc.lower().lstrip("www."))
            return domains
        except Exception as e:
            self.logger.error("DuckDuckGo fallback error: %s", e)
            return []
