import asyncio
import logging
import socket

from domain_hunter.hunters.base import BaseHunter
from domain_hunter.rate_limiter import QuotaExhaustedError

logger = logging.getLogger("domain_hunter.hunters.hackertarget")

REVERSE_IP_URL = "https://api.hackertarget.com/reverseiplookup/?q={ip}"
SHARED_DNS_URL = "https://api.hackertarget.com/findshareddns/?q={host}"
MAX_RESULTS_PER_IP = 500


class HackerTargetHunter(BaseHunter):
    SOURCE_NAME = "hackertarget"

    async def _do_hunt(self, seed_domain: str, vertical: str) -> list[str]:
        ips = await self._resolve_ips(seed_domain)
        if not ips:
            self.logger.warning("Could not resolve IPs for %s", seed_domain)
            return []

        results: set[str] = set()
        for ip in ips[:3]:
            domains = await self._reverse_ip(ip)
            results.update(domains)

        self.logger.info("HackerTarget found %d domains for %s", len(results), seed_domain)
        return list(results)

    async def _resolve_ips(self, domain: str) -> list[str]:
        loop = asyncio.get_event_loop()
        try:
            infos = await loop.run_in_executor(None, socket.getaddrinfo, domain, None)
            return list({info[4][0] for info in infos})
        except socket.gaierror as e:
            self.logger.error("DNS resolution failed for %s: %s", domain, e)
            return []

    async def _reverse_ip(self, ip: str) -> list[str]:
        url = REVERSE_IP_URL.format(ip=ip)
        try:
            async with await self._get(url) as resp:
                if resp.status != 200:
                    self.logger.warning("HackerTarget reverse IP returned %d for %s", resp.status, ip)
                    return []
                text = await resp.text()
        except QuotaExhaustedError:
            return []
        except Exception as e:
            self.logger.error("HackerTarget error for IP %s: %s", ip, e)
            return []

        if "API count exceeded" in text or text.strip().startswith("error"):
            self.logger.warning("HackerTarget API limit or error: %s", text[:100])
            return []

        domains = [ln.strip() for ln in text.splitlines() if ln.strip() and "." in ln]
        return domains[:MAX_RESULTS_PER_IP]

    async def findshareddns(self, host: str) -> list[str]:
        url = SHARED_DNS_URL.format(host=host)
        try:
            async with await self._get(url) as resp:
                if resp.status != 200:
                    return []
                text = await resp.text()
        except (QuotaExhaustedError, Exception) as e:
            self.logger.error("HackerTarget findshareddns error for %s: %s", host, e)
            return []

        if "API count exceeded" in text:
            return []

        return [ln.strip() for ln in text.splitlines() if ln.strip() and "." in ln]
