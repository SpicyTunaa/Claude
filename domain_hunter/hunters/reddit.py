import logging
import re
from urllib.parse import urlparse

from domain_hunter.hunters.base import BaseHunter
from domain_hunter.utils.http_client import build_headers

logger = logging.getLogger("domain_hunter.hunters.reddit")

REDDIT_SEARCH_URL = (
    "https://old.reddit.com/search.json?q={query}&sort=relevance&t=all&limit=25&type=link,comment"
)
DOMAIN_RE = re.compile(r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b")
URL_RE = re.compile(r'https?://([a-zA-Z0-9.-]+)')


class RedditHunter(BaseHunter):
    SOURCE_NAME = "reddit"

    async def _do_hunt(self, seed_domain: str, vertical: str) -> list[str]:
        # Search for recommendations/alternatives in the vertical — finds competitor sites
        queries = [
            f'best {vertical} sites',
            f'{seed_domain} alternatives',
        ]

        domains: set[str] = set()
        for query in queries:
            found = await self._search_reddit(query)
            domains.update(found)

        # Pushshift is optional — any failure is silently ignored
        try:
            domains.update(await self._search_pushshift(f'{vertical} {seed_domain}'))
        except Exception:
            pass

        self.logger.info("Reddit found %d domains for %s", len(domains), seed_domain)
        return list(domains)

    async def _search_reddit(self, query: str) -> list[str]:
        url = REDDIT_SEARCH_URL.format(query=query.replace(" ", "+"))
        headers = build_headers()
        headers["Accept"] = "application/json"

        try:
            async with await self._get(url, headers=headers) as resp:
                if resp.status != 200:
                    self.logger.warning("Reddit returned %d", resp.status)
                    return []
                data = await resp.json(content_type=None)
        except Exception as e:
            self.logger.warning("Reddit error: %s", e)
            return []

        domains = []
        for post in data.get("data", {}).get("children", []):
            post_data = post.get("data", {})
            text = " ".join([
                post_data.get("title", ""),
                post_data.get("selftext", ""),
                post_data.get("url", ""),
            ])
            # Prefer extracting from URLs embedded in text (higher precision)
            for match in URL_RE.findall(text):
                d = match.lower().lstrip("www.")
                if "." in d and len(d) > 4:
                    domains.append(d)
            # Also extract bare domain mentions
            for match in DOMAIN_RE.findall(text):
                d = match.lower()
                if len(d) > 6 and "reddit" not in d:
                    domains.append(d)

        return list(set(domains))

    async def _search_pushshift(self, query: str) -> list[str]:
        url = f"https://api.pushshift.io/reddit/search/comment/?q={query.replace(' ', '+')}&size=50"
        headers = build_headers()
        headers["Accept"] = "application/json"

        async with await self._get(url, headers=headers) as resp:
            if resp.status != 200:
                return []
            data = await resp.json(content_type=None)

        domains = []
        for item in data.get("data", []):
            text = item.get("body", "")
            for match in URL_RE.findall(text):
                d = match.lower().lstrip("www.")
                if "." in d and len(d) > 4 and "reddit" not in d:
                    domains.append(d)
        return list(set(domains))
