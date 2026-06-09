import asyncio
import logging

from domain_hunter.hunters.base import BaseHunter

logger = logging.getLogger("domain_hunter.hunters.crtsh")

API_URL = "https://crt.sh/?q=%25.{domain}&output=json"


class CrtShHunter(BaseHunter):
    SOURCE_NAME = "crtsh"

    async def _do_hunt(self, seed_domain: str, vertical: str) -> list[str]:
        url = API_URL.format(domain=seed_domain)
        try:
            async with await self._get(url) as resp:
                if resp.status != 200:
                    self.logger.warning("crt.sh returned %d for %s", resp.status, seed_domain)
                    return []
                data = await resp.json(content_type=None)
        except Exception as e:
            self.logger.error("crt.sh error for %s: %s", seed_domain, e)
            return []

        await asyncio.sleep(1.5)

        domains: set[str] = set()
        for entry in data:
            name_value = entry.get("name_value", "")
            for name in name_value.split("\n"):
                name = name.strip().lstrip("*.")
                if name and "." in name:
                    domains.add(name.lower())

        self.logger.info("crt.sh found %d domains for %s", len(domains), seed_domain)
        return list(domains)
