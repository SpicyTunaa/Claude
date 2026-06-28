"""Rule-based technology fingerprinting over a fetched page (headers + HTML).

Signatures live in ``signatures.yaml`` (data, not code). Output is deterministic: signals
are sorted by category then technology name.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

from ..core.models import TechSignal
from ..enrichment.website import PageBundle

_SCRIPT_SRC_RE = re.compile(r"<script[^>]+src=[\"']([^\"']+)[\"']", re.IGNORECASE)


@lru_cache(maxsize=1)
def _load_signatures() -> list[dict]:
    path = Path(__file__).with_name("signatures.yaml")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data.get("technologies", [])


def _rule_matches(
    rule: dict, html_lower: str, script_srcs: list[str], headers: dict[str, str]
) -> bool:
    for name in rule.get("header_present", []) or []:
        if name.lower() in headers:
            return True
    for name, substr in (rule.get("header_equals", {}) or {}).items():
        val = headers.get(name.lower(), "")
        if substr.lower() in val.lower():
            return True
    for needle in rule.get("html_contains", []) or []:
        if needle.lower() in html_lower:
            return True
    for needle in rule.get("script_src", []) or []:
        if any(needle.lower() in src.lower() for src in script_srcs):
            return True
    return False


def detect(bundle: PageBundle) -> list[TechSignal]:
    html_lower = (bundle.html or "").lower()
    script_srcs = _SCRIPT_SRC_RE.findall(bundle.html or "")
    headers = {k.lower(): v for k, v in (bundle.headers or {}).items()}

    signals: list[TechSignal] = []
    for rule in _load_signatures():
        if _rule_matches(rule, html_lower, script_srcs, headers):
            signals.append(
                TechSignal(
                    technology=rule["name"],
                    category=rule.get("category", ""),
                    source="fingerprint",
                    confidence=0.7,
                )
            )
    signals.sort(key=lambda s: (s.category, s.technology))
    return signals
