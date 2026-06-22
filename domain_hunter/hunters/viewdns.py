import asyncio
import logging
import random

from bs4 import BeautifulSoup

from domain_hunter.hunters.base import BaseHunter
from domain_hunter.utils.http_client import build_headers

logger = logging.getLogger("domain_hunter.hunters.viewdns")

BASE_URL = "https://viewdns.info/reverseip/?host={domain}&t=1"


class ViewDnsHunter(BaseHunter):
    SOURCE_NAME = "viewdns"

    async def _do_hunt(self, seed_domain: str, vertical: str) -> list[str]:
        domains: set[str] = set()

        for page in range(1, self.config.MAX_VIEWDNS_PAGES + 1):
            url = BASE_URL.format(domain=seed_domain)
            if page > 1:
                url += f"&page={page}"

            new_domains, has_next = await self._scrape_page(url)
            domains.update(new_domains)

            if not has_next or not new_domains:
                break

            await asyncio.sleep(random.uniform(3, 6))

        self.logger.info("ViewDNS found %d domains for %s", len(domains), seed_domain)
        return list(domains)

    async def _scrape_page(self, url: str) -> tuple[list[str], bool]:
        headers = build_headers(include_referer=True)
        try:
            async with await self._get(url, headers=headers) as resp:
                if resp.status == 429:
                    self.logger.warning("ViewDNS rate limited (429)")
                    return [], False
                if resp.status != 200:
                    self.logger.warning("ViewDNS returned %d", resp.status)
                    return [], False
                html = await resp.text()
        except Exception as e:
            self.logger.error("ViewDNS error: %s", e)
            return [], False

        soup = BeautifulSoup(html, "lxml")
        table = soup.find("table", {"border": "1"})
        if not table:
            return [], False

        domains = []
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if cols:
                d = cols[0].get_text(strip=True).lower()
                if d and "." in d:
                    domains.append(d)

        has_next = bool(soup.find("a", string=lambda t: t and "next" in t.lower()))
        return domains, has_next
