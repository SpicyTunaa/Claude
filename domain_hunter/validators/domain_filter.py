import re

from domain_hunter.models import DomainRecord

DOMAIN_RE = re.compile(r"^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$")
PRIVATE_PTR_RE = re.compile(r"\d+\.\d+\.\d+\.\d+\.in-addr\.arpa")

CDN_NOISE = {
    "cloudflare.com", "cloudfront.net", "fastly.net", "akamaiedge.net",
    "akamai.net", "amazonaws.com", "googleusercontent.com", "azureedge.net",
    "trafficmanager.net", "azurewebsites.net", "appspot.com", "herokussl.com",
}


def is_valid(domain: str) -> bool:
    if not domain or len(domain) > 253:
        return False
    if PRIVATE_PTR_RE.search(domain):
        return False
    if not DOMAIN_RE.match(domain):
        return False
    # check CDN noise by registered domain suffix
    parts = domain.split(".")
    if len(parts) >= 2:
        base = ".".join(parts[-2:])
        if base in CDN_NOISE:
            return False
    return True


def apply(records: list[DomainRecord]) -> list[DomainRecord]:
    return [r for r in records if isinstance(r, DomainRecord) and is_valid(r.domain)]
