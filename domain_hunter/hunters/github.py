import asyncio
import logging
import re

from domain_hunter.hunters.base import BaseHunter
from domain_hunter.utils.http_client import build_headers

logger = logging.getLogger("domain_hunter.hunters.github")

GITHUB_SEARCH_URL = "https://api.github.com/search/code?q={query}&per_page=30"
DOMAIN_RE = re.compile(r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b")


class GitHubHunter(BaseHunter):
    SOURCE_NAME = "github"

    async def _do_hunt(self, seed_domain: str, vertical: str) -> list[str]:
        if not self.config.GITHUB_TOKEN:
            self.logger.info("GitHub hunter skipped — set GITHUB_TOKEN for best results")
            return []

        domains: set[str] = set()

        for query in [seed_domain]:
            found = await self._search_code(query)
            domains.update(found)
            await asyncio.sleep(6)

        self.logger.info("GitHub found %d domains for %s", len(domains), seed_domain)
        return list(domains)

    async def _search_code(self, query: str) -> list[str]:
        url = GITHUB_SEARCH_URL.format(query=query.replace(" ", "+"))
        headers = build_headers()
        headers["Accept"] = "application/vnd.github+json"
        headers["Authorization"] = f"Bearer {self.config.GITHUB_TOKEN}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"

        try:
            async with await self._get(url, headers=headers) as resp:
                if resp.status == 403:
                    self.logger.warning("GitHub rate limited (403)")
                    return []
                if resp.status != 200:
                    self.logger.warning("GitHub returned %d", resp.status)
                    return []
                data = await resp.json(content_type=None)
        except Exception as e:
            self.logger.error("GitHub error: %s", e)
            return []

        domains = []
        for item in data.get("items", []):
            text = f"{item.get('path', '')} {item.get('name', '')}"
            for match in DOMAIN_RE.findall(text):
                if len(match) > 4:
                    domains.append(match.lower())

        return list(set(domains))
