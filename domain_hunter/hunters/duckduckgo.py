import asyncio
import logging
import random
import re
from urllib.parse import urlparse, unquote

from bs4 import BeautifulSoup

from domain_hunter.hunters.base import BaseHunter
from domain_hunter.utils.http_client import build_headers

logger = logging.getLogger("domain_hunter.hunters.duckduckgo")

DDG_URL = "https://html.duckduckgo.com/html/?q={query}"
DOMAIN_RE = re.compile(r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b")


class DuckDuckGoHunter(BaseHunter):
    SOURCE_NAME = "duckduckgo"

    async def _do_hunt(self, seed_domain: str, vertical: str) -> list[str]:
        # Focus on finding related/competitor sites rather than subdomains
        queries = [
            f'sites like {seed_domain}',
            f'best {vertical} websites',
            f'top {vertical} sites',
            f'{vertical} {seed_domain} alternatives',
        ]

        domains: set[str] = set()
        for query in queries:
            found = await self._search(query)
            domains.update(found)
            await asyncio.sleep(random.uniform(
                self.config.DUCKDUCKGO_DELAY_MIN,
                self.config.DUCKDUCKGO_DELAY_MAX,
            ))

        self.logger.info("DuckDuckGo found %d domains for %s", len(domains), seed_domain)
        return list(domains)

    async def _search(self, query: str) -> list[str]:
        url = DDG_URL.format(query=query.replace(" ", "+"))
        headers = build_headers(include_referer=True)
        headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        headers["Accept-Language"] = "en-US,en;q=0.9"

        try:
            async with await self._get(url, headers=headers) as resp:
                if resp.status != 200:
                    self.logger.warning("DuckDuckGo returned %d for query '%s', trying fallback", resp.status, query)
                    return self._fallback_search(query)
                html = await resp.text()
        except Exception as e:
            self.logger.warning("DuckDuckGo scrape error: %s — trying fallback", e)
            return self._fallback_search(query)

        soup = BeautifulSoup(html, "lxml")
        domains: set[str] = set()

        # Strategy 1: result__a links (the main clickable result titles)
        for link in soup.find_all("a", class_="result__a"):
            href = link.get("href", "")
            extracted = _extract_domain(href)
            if extracted:
                domains.add(extracted)

        # Strategy 2: result__url spans (the URL label displayed under each result)
        for tag in soup.find_all(["a", "span"], class_="result__url"):
            text = tag.get_text(strip=True) or tag.get("href", "")
            extracted = _extract_domain(text if text.startswith("http") else f"https://{text}")
            if extracted:
                domains.add(extracted)

        # Strategy 3: DDG redirect links (/l/?uddg=...)
        for link in soup.find_all("a", href=re.compile(r"/l/\?uddg=")):
            href = link.get("href", "")
            m = re.search(r"uddg=([^&]+)", href)
            if m:
                decoded = unquote(m.group(1))
                extracted = _extract_domain(decoded)
                if extracted:
                    domains.add(extracted)

        if not domains:
            # HTML parse yielded nothing — DDG may have blocked; try library fallback
            self.logger.debug("No domains from HTML parse for query '%s', trying DDGS fallback", query)
            return self._fallback_search(query)

        return list(domains)

    def _fallback_search(self, query: str) -> list[str]:
        try:
            from duckduckgo_search import DDGS
            results = list(DDGS().text(query, max_results=30))
            domains = []
            for r in results:
                url = r.get("href", "")
                if url:
                    extracted = _extract_domain(url)
                    if extracted:
                        domains.append(extracted)
            self.logger.info("DDGS fallback returned %d domains for '%s'", len(domains), query)
            return domains
        except Exception as e:
            self.logger.warning("DuckDuckGo fallback error: %s", e)
            return []


def _extract_domain(url: str) -> str | None:
    if not url:
        return None
    if not url.startswith("http"):
        url = f"https://{url}"
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc and "." in netloc:
            # Strip port, strip leading www.
            netloc = netloc.split(":")[0]
            if netloc.startswith("www."):
                netloc = netloc[4:]
            # Skip DDG's own infrastructure
            if any(netloc.endswith(skip) for skip in ("duckduckgo.com", "ddg.gg")):
                return None
            return netloc
    except Exception:
        pass
    return None
