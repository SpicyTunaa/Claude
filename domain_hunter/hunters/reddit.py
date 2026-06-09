import asyncio
import logging
import re

from domain_hunter.hunters.base import BaseHunter
from domain_hunter.utils.http_client import build_headers

logger = logging.getLogger("domain_hunter.hunters.reddit")

REDDIT_SEARCH_URL = (
    "https://old.reddit.com/search.json?q={query}&sort=relevance&t=year&limit=25"
)
PUSHSHIFT_URL = "https://api.pushshift.io/reddit/search/comment/?q={query}&size=50"
DOMAIN_RE = re.compile(r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b")


class RedditHunter(BaseHunter):
    SOURCE_NAME = "reddit"

    async def _do_hunt(self, seed_domain: str, vertical: str) -> list[str]:
        query = f"{vertical} {seed_domain}"
        domains: set[str] = set()

        domains.update(await self._search_reddit(query))

        # Pushshift is optional — any failure is silently ignored
        try:
            domains.update(await self._search_pushshift(seed_domain))
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
            self.logger.error("Reddit error: %s", e)
            return []

        domains = []
        for post in data.get("data", {}).get("children", []):
            post_data = post.get("data", {})
            text = f"{post_data.get('title', '')} {post_data.get('selftext', '')}"
            for match in DOMAIN_RE.findall(text):
                if len(match) > 4:
                    domains.append(match.lower())

        return list(set(domains))

    async def _search_pushshift(self, query: str) -> list[str]:
        url = PUSHSHIFT_URL.format(query=query.replace(" ", "+"))
        headers = build_headers()
        headers["Accept"] = "application/json"

        async with await self._get(url, headers=headers) as resp:
            if resp.status != 200:
                return []
            data = await resp.json(content_type=None)

        domains = []
        for item in data.get("data", []):
            text = item.get("body", "")
            for match in DOMAIN_RE.findall(text):
                if len(match) > 4:
                    domains.append(match.lower())
        return list(set(domains))
