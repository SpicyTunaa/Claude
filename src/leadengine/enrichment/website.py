"""Website enrichment: fetch the homepage and extract public descriptive fields.

Produces a :class:`PageBundle` (HTML + response headers) that downstream stages
(contact extraction, fingerprinting, monetization) reuse, so the page is fetched once.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup

from ..core.fetcher import Fetcher
from ..core.models import FieldValue, Lead

_COPYRIGHT_RE = re.compile(
    r"(?:©|&copy;|\(c\)|copyright)\s*\d{0,4}\s*([A-Z][\w&.\- ]{2,60}?)(?:\.|,|<|$)",
    re.IGNORECASE,
)


@dataclass
class PageBundle:
    final_url: str
    html: str
    headers: dict[str, str] = field(default_factory=dict)


async def fetch_page(
    fetcher: Fetcher, url: str, *, rate_limit: float | None = None
) -> PageBundle | None:
    result = await fetcher.try_fetch(url, rate_limit=rate_limit)
    if result is None:
        return None
    return PageBundle(final_url=result.url, html=result.text, headers=result.headers)


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html or "", "lxml")


def parse_page(lead: Lead, bundle: PageBundle, *, source: str) -> list[FieldValue]:
    """Extract description, language, owner/org and socials. Mutates ``lead``."""
    evidence: list[FieldValue] = []
    soup = _soup(bundle.html)
    url = bundle.final_url

    def record(field_name: str, value: str | None, confidence: float, raw: str | None = None):
        if value:
            evidence.append(
                FieldValue(
                    field=field_name,
                    value=value,
                    source=source,
                    url=url,
                    confidence=confidence,
                    raw_value=raw,
                )
            )

    # Language from <html lang="...">.
    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        lang = str(html_tag.get("lang")).split("-")[0].lower()[:8]
        if not lead.language:
            lead.language = lang
        record("language", lang, 0.8)

    # Description from meta description, else the first paragraph.
    if not lead.description:
        meta = soup.find("meta", attrs={"name": "description"})
        desc = meta.get("content") if meta and meta.get("content") else None
        if not desc:
            p = soup.find("p")
            desc = p.get_text(strip=True) if p else None
        if desc:
            lead.description = desc.strip()[:500]
            record("description", lead.description, 0.7, raw=desc)

    # Company name from <title> / first <h1> when missing.
    if not lead.company_name:
        title = soup.find("title")
        h1 = soup.find("h1")
        name = (title.get_text(strip=True) if title else None) or (
            h1.get_text(strip=True) if h1 else None
        )
        if name:
            lead.company_name = name.strip()[:200]
            record("company_name", lead.company_name, 0.5, raw=name)

    # Owner/org from a copyright line in the footer/body text.
    if not lead.owner_org:
        text = soup.get_text(" ", strip=True)
        m = _COPYRIGHT_RE.search(text)
        if m:
            owner = m.group(1).strip()
            lead.owner_org = owner[:200]
            record("owner_org", lead.owner_org, 0.6, raw=m.group(0))

    # Social links (evidence only).
    for a in soup.find_all("a", href=True):
        href = a["href"]
        low = href.lower()
        if "github.com/" in low:
            record("github", href, 0.7)
        elif "twitter.com/" in low or "x.com/" in low:
            record("twitter", href, 0.7)
        elif "linkedin.com/" in low:
            record("linkedin", href, 0.7)

    return evidence
