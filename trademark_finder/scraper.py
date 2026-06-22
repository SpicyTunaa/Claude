"""
Contact page scraper — fallback when WHOIS returns no usable email.
Crawls up to MAX_PAGES contact-relevant pages per domain.
Uses standard browser headers only (no proxy needed for ~20 domains).
"""

import asyncio
import logging
import random
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger("trademark_finder.scraper")

# Pages most likely to contain registrant/operator contact info
CONTACT_PATHS = [
    "/contact",
    "/contact-us",
    "/about",
    "/about-us",
    "/privacy",
    "/privacy-policy",
    "/terms",
    "/terms-of-service",
    "/advertise",
    "/advertise-with-us",
    "/dmca",
]

# Obfuscated email patterns: "name [at] domain.com", "admin(at)domain.org"
EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+\s*(?:\[at\]|\(at\)|@)\s*[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

# Cleanup: normalise [at] / (at) back to @
AT_RE = re.compile(r"\s*(?:\[at\]|\(at\))\s*", re.IGNORECASE)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

TIMEOUT = httpx.Timeout(10.0, connect=5.0)


def _normalise_email(raw: str) -> str:
    return AT_RE.sub("@", raw).replace(" ", "").lower()


def _extract_emails_from_html(html: str) -> set[str]:
    emails: set[str] = set()
    for match in EMAIL_RE.findall(html):
        emails.add(_normalise_email(match))
    # Also parse plain mailto: links
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all("a", href=re.compile(r"^mailto:", re.I)):
        addr = tag["href"].replace("mailto:", "").split("?")[0].strip().lower()
        if "@" in addr:
            emails.add(addr)
    return emails


async def scrape_domain(domain: str, max_pages: int = 5, delay: float = 2.0) -> list[str]:
    """
    Try the homepage then up to max_pages contact-relevant paths.
    Returns a deduplicated list of raw email strings found.
    """
    base = f"https://{domain}"
    found: set[str] = set()
    pages_tried = 0

    async with httpx.AsyncClient(
        headers=HEADERS,
        timeout=TIMEOUT,
        follow_redirects=True,
        verify=False,       # many infringing sites have expired/self-signed certs
    ) as client:
        # 1. Homepage — may already expose contact info
        emails = await _fetch_and_extract(client, base)
        found.update(emails)
        pages_tried += 1

        if found:
            logger.info("%s: found email(s) on homepage", domain)
            return list(found)

        # 2. Walk contact-relevant paths until we hit max_pages or find something
        for path in CONTACT_PATHS:
            if pages_tried >= max_pages:
                break
            await asyncio.sleep(delay + random.uniform(0, 1))  # polite jitter
            url = urljoin(base, path)
            emails = await _fetch_and_extract(client, url)
            pages_tried += 1
            if emails:
                found.update(emails)
                logger.info("%s: found email(s) at %s", domain, path)
                break  # first hit is enough for takedown purposes

    if not found:
        logger.info("%s: no email found after scraping %d page(s)", domain, pages_tried)

    return list(found)


async def _fetch_and_extract(client: httpx.AsyncClient, url: str) -> set[str]:
    try:
        resp = await client.get(url)
        if resp.status_code >= 400:
            return set()
        return _extract_emails_from_html(resp.text)
    except Exception as exc:
        logger.debug("Fetch failed for %s: %s", url, exc)
        return set()
