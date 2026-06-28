"""OPTIONAL monetization detection layer (intelligence/tagging, not a core dependency).

Runs after fingerprinting over the already-fetched page. The pipeline wraps the call so any
failure is caught and skipped — it must NEVER affect core pipeline correctness. With the
layer disabled, leads carry NULL monetization tags and scores are unchanged.

Reads only public, already-loaded page content (same posture as tech fingerprinting).
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

from ..core.models import MonetizationTags
from ..enrichment.website import PageBundle

_SCRIPT_SRC_RE = re.compile(r"<script[^>]+src=[\"']([^\"']+)[\"']", re.IGNORECASE)


@lru_cache(maxsize=1)
def _load_networks() -> list[dict]:
    path = Path(__file__).with_name("monetization.yaml")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data.get("networks", [])


def _matches(rule: dict, html_lower: str, script_srcs: list[str]) -> bool:
    for needle in rule.get("script_src", []) or []:
        if any(needle.lower() in src.lower() for src in script_srcs):
            return True
    for needle in rule.get("html_contains", []) or []:
        if needle.lower() in html_lower:
            return True
    return False


def detect(bundle: PageBundle) -> MonetizationTags:
    html_lower = (bundle.html or "").lower()
    script_srcs = _SCRIPT_SRC_RE.findall(bundle.html or "")

    networks: list[str] = []
    kinds: set[str] = set()
    for rule in _load_networks():
        if _matches(rule, html_lower, script_srcs):
            networks.append(rule["name"])
            kinds.add(rule["kind"])

    networks = sorted(set(networks))
    has_ads = "ad-network" in kinds
    has_lock = "link-locker" in kinds
    has_payments = "payments" in kinds

    # Classify monetization model (deterministic precedence).
    if has_lock and (has_ads or has_payments):
        mon_type = "hybrid"
    elif has_lock:
        mon_type = "link-lock"
    elif has_ads and has_payments:
        mon_type = "hybrid"
    elif has_ads or "affiliate" in kinds:
        mon_type = "ads"
    elif has_payments:
        mon_type = "subscription-SaaS"
    else:
        mon_type = "unknown"

    # Revenue intensity: deterministic function of model + breadth of signals.
    base = {
        "link-lock": 70,
        "hybrid": 60,
        "ads": 45,
        "subscription-SaaS": 40,
        "unknown": 0,
    }[mon_type]
    intensity = min(100, base + 10 * max(0, len(networks) - 1)) if mon_type != "unknown" else 0

    # Friction level from the user's perspective.
    if has_lock:
        friction = "high"
    elif has_ads:
        friction = "medium"
    elif mon_type == "subscription-SaaS":
        friction = "low"
    else:
        friction = "low"

    return MonetizationTags(
        monetization_type=mon_type,
        ad_networks=networks,
        revenue_intensity_score=intensity,
        friction_level=friction,
    )
