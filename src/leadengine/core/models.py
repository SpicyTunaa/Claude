"""Domain models shared across the pipeline.

Plain dataclasses keep the data flow explicit and deterministic. Every collected field
is represented as a :class:`FieldValue` carrying provenance (value, source, url,
timestamp, confidence, raw value) so evidence can be retained append-only.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


def utcnow() -> datetime:
    """Current UTC time, or a frozen value when ``LEADENGINE_FROZEN_NOW`` is set.

    Freezing the clock (ISO-8601 string) makes runs fully reproducible — used by the
    determinism tests and for byte-stable demo output.
    """
    # Naive UTC throughout — SQLite stores datetimes without tzinfo, so keeping everything
    # naive avoids aware/naive subtraction errors and keeps exported timestamps stable.
    frozen = os.environ.get("LEADENGINE_FROZEN_NOW")
    if frozen:
        dt = datetime.fromisoformat(frozen)
        return dt.replace(tzinfo=None)
    return datetime.now(tz=UTC).replace(tzinfo=None)


class Stage(str, Enum):
    """Per-lead pipeline progress, used as the resumable checkpoint."""

    DISCOVERED = "discovered"
    ENRICHED = "enriched"
    CONTACTED = "contacted"  # contact-extraction done
    FINGERPRINTED = "fingerprinted"
    SCORED = "scored"
    EXPORTED = "exported"


# Order used to decide what "resume" still needs to process.
STAGE_ORDER: list[Stage] = [
    Stage.DISCOVERED,
    Stage.ENRICHED,
    Stage.CONTACTED,
    Stage.FINGERPRINTED,
    Stage.SCORED,
    Stage.EXPORTED,
]


@dataclass
class FieldValue:
    """A single observed field with full provenance (append-only evidence)."""

    field: str
    value: str | None
    source: str
    url: str | None = None
    confidence: float = 0.5
    raw_value: str | None = None
    observed_at: datetime = field(default_factory=utcnow)


@dataclass
class Contact:
    email: str
    type: str = "generic"  # security/support/sales/info/generic
    validation_status: str = "unvalidated"  # valid/invalid/unvalidated
    source: str = ""
    confidence: float = 0.5


@dataclass
class TechSignal:
    technology: str
    category: str  # cdn/hosting/cms/framework/analytics/...
    source: str = "fingerprint"
    confidence: float = 0.6
    version: str | None = None


@dataclass
class MonetizationTags:
    """Output of the optional, non-blocking monetization detection layer."""

    monetization_type: str | None = None  # ads/link-lock/subscription-SaaS/hybrid/unknown
    ad_networks: list[str] = field(default_factory=list)
    revenue_intensity_score: int | None = None  # 0-100
    friction_level: str | None = None  # low/medium/high


@dataclass
class RawHit:
    """A raw discovery result emitted by an adapter's ``discover()``."""

    source: str
    url: str
    title: str | None = None
    description: str | None = None
    categories: list[str] = field(default_factory=list)
    extra: dict[str, str] = field(default_factory=dict)


@dataclass
class Lead:
    """The canonical lead record assembled and persisted by the pipeline."""

    registrable_domain: str
    website: str
    company_name: str | None = None
    product_name: str | None = None
    description: str | None = None
    categories: list[str] = field(default_factory=list)
    country: str | None = None
    language: str | None = None
    owner_org: str | None = None
    tech_stack: list[str] = field(default_factory=list)
    hosting: str | None = None
    cms: str | None = None
    framework: str | None = None
    discovery_source: str = ""

    contacts: list[Contact] = field(default_factory=list)
    technologies: list[TechSignal] = field(default_factory=list)
    monetization: MonetizationTags = field(default_factory=MonetizationTags)

    completeness_score: int = 0
    confidence_score: int = 0
    outreach_priority: str = "low"

    stage: Stage = Stage.DISCOVERED
    first_seen: datetime = field(default_factory=utcnow)
    last_seen: datetime = field(default_factory=utcnow)
    last_changed: datetime = field(default_factory=utcnow)


@dataclass
class AdapterMetadata:
    name: str
    categories: list[str] = field(default_factory=list)
    rate_limit: float = 1.0
    requires_playwright: bool = False
    description: str = ""


# --- normalization helpers ------------------------------------------------------------

# A small set of multi-label public suffixes so "example.co.uk" -> "example.co.uk".
# Kept intentionally compact for the MVP (no external PSL dependency).
_MULTI_PART_SUFFIXES = {
    "co.uk", "org.uk", "gov.uk", "ac.uk", "co.jp", "or.jp", "ne.jp", "co.kr",
    "com.au", "net.au", "org.au", "com.br", "com.cn", "com.mx", "co.in", "co.za",
    "co.il", "org.il", "ac.il", "gov.il", "com.tr", "co.nz",
}

_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")


def normalize_url(url: str) -> str:
    """Lowercase scheme/host, ensure a scheme, strip fragments and trailing slashes."""
    url = (url or "").strip()
    if not url:
        return ""
    if not _SCHEME_RE.match(url):
        url = "https://" + url
    # Split off scheme.
    scheme, _, rest = url.partition("://")
    rest = rest.split("#", 1)[0]
    host, slash, path = rest.partition("/")
    host = host.lower()
    normalized = f"{scheme.lower()}://{host}{slash}{path}"
    return normalized.rstrip("/")


def extract_host(url: str) -> str:
    url = normalize_url(url)
    if not url:
        return ""
    rest = url.split("://", 1)[1]
    host = rest.split("/", 1)[0]
    # Drop credentials and port if present.
    host = host.split("@")[-1].split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    return host


def registrable_domain(url_or_host: str) -> str:
    """Best-effort registrable domain (eTLD+1) without an external PSL dependency."""
    host = url_or_host
    if "://" in host or "/" in host or host.startswith("www."):
        host = extract_host(host)
    host = host.lower().strip(".")
    if not host or "." not in host:
        return host
    parts = host.split(".")
    last_two = ".".join(parts[-2:])
    last_three = ".".join(parts[-3:]) if len(parts) >= 3 else last_two
    if last_two in _MULTI_PART_SUFFIXES and len(parts) >= 3:
        return last_three
    return last_two
