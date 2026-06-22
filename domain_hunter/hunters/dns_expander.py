import asyncio
import logging
import socket

from domain_hunter.hunters.base import BaseHunter
from domain_hunter.models import DomainRecord

logger = logging.getLogger("domain_hunter.hunters.dns_expander")


class DnsExpanderHunter(BaseHunter):
    SOURCE_NAME = "dns_expander"

    async def _do_hunt(self, seed_domain: str, vertical: str) -> list[str]:
        from domain_hunter.hunters.hackertarget import HackerTargetHunter

        domains: set[str] = set()
        ht = HackerTargetHunter(self.session, self.rate_limiter, self.config)

        ns_records = await self._get_ns_records(seed_domain)
        mx_records = await self._get_mx_records(seed_domain)

        for ns_host in ns_records[:3]:
            try:
                ns_domains = await ht.findshareddns(ns_host)
                domains.update(ns_domains)
                await asyncio.sleep(2)
            except Exception as e:
                self.logger.error("findshareddns error for %s: %s", ns_host, e)

        for mx_host in mx_records[:2]:
            mx_ips = await self._resolve_ips(mx_host)
            for ip in mx_ips[:1]:
                try:
                    ip_domains = await ht._reverse_ip(ip)
                    domains.update(ip_domains)
                    await asyncio.sleep(2)
                except Exception as e:
                    self.logger.error("reverse IP error for %s: %s", ip, e)

        self.logger.info("DNS expander found %d domains for %s", len(domains), seed_domain)
        return [d.lower() for d in domains]

    async def _get_ns_records(self, domain: str) -> list[str]:
        loop = asyncio.get_event_loop()
        try:
            import dns.resolver
            answers = await loop.run_in_executor(None, dns.resolver.resolve, domain, "NS")
            return [str(r.target).rstrip(".").lower() for r in answers]
        except Exception as e:
            self.logger.warning("NS lookup failed for %s: %s", domain, e)
            return []

    async def _get_mx_records(self, domain: str) -> list[str]:
        loop = asyncio.get_event_loop()
        try:
            import dns.resolver
            answers = await loop.run_in_executor(None, dns.resolver.resolve, domain, "MX")
            return [str(r.exchange).rstrip(".").lower() for r in answers]
        except Exception as e:
            self.logger.warning("MX lookup failed for %s: %s", domain, e)
            return []

    async def _resolve_ips(self, host: str) -> list[str]:
        loop = asyncio.get_event_loop()
        try:
            infos = await loop.run_in_executor(None, socket.getaddrinfo, host, None)
            return list({info[4][0] for info in infos})
        except Exception:
            return []
