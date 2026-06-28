"""Deterministic lead scoring.

Weights come from ``config/scoring.yaml``. The score reflects DATA QUALITY + BUSINESS FIT
+ OUTREACH READINESS — never vulnerability or security-weakness severity. Same input
always yields the same output.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..core.models import Lead, MonetizationTags, utcnow


@dataclass
class ScoreResult:
    completeness_score: int
    confidence_score: int
    outreach_priority: str


def _present(lead: Lead, field: str) -> bool:
    if field == "category":
        return bool(lead.categories)
    if field == "tech_stack":
        return bool(lead.tech_stack)
    return bool(getattr(lead, field, None))


def _completeness(lead: Lead, cfg: dict) -> tuple[int, int]:
    fields: dict[str, int] = cfg.get("completeness_fields", {})
    total = sum(fields.values()) or 1
    got = sum(weight for field, weight in fields.items() if _present(lead, field))
    return got, total


def _contact_points(lead: Lead, cfg: dict) -> int:
    c = cfg.get("contact", {})
    if not lead.contacts:
        return 0
    points = c.get("any_contact", 20)
    points += c.get("per_extra_contact", 5) * (len(lead.contacts) - 1)
    return min(points, c.get("max_contact_points", 35))


def _tech_points(lead: Lead, cfg: dict) -> int:
    t = cfg.get("tech", {})
    if not lead.tech_stack:
        return 0
    points = t.get("any_tech", 8)
    points += t.get("per_extra_tech", 2) * (len(lead.tech_stack) - 1)
    return min(points, t.get("max_tech_points", 16))


def _recency_points(lead: Lead, cfg: dict, now: datetime) -> int:
    r = cfg.get("recency", {})
    full = r.get("days_full_points", 7)
    zero = r.get("days_zero_points", 90)
    max_points = r.get("max_points", 15)
    age_days = max(0, (now - lead.first_seen).days)
    if age_days <= full:
        return max_points
    if age_days >= zero:
        return 0
    span = max(1, zero - full)
    return round(max_points * (zero - age_days) / span)


def _monetization_adjustment(mon: MonetizationTags, mon_cfg) -> int:
    if not getattr(mon_cfg, "affect_score", False):
        return 0
    if not mon.monetization_type:
        return 0
    return int(getattr(mon_cfg, "score_adjustments", {}).get(mon.monetization_type, 0))


def score_lead(
    lead: Lead,
    scoring_cfg: dict,
    *,
    monetization_cfg=None,
    now: datetime | None = None,
) -> ScoreResult:
    now = now or utcnow()
    got, total = _completeness(lead, scoring_cfg)
    completeness_score = round(100 * got / total)

    points = (
        got
        + _contact_points(lead, scoring_cfg)
        + _tech_points(lead, scoring_cfg)
        + _recency_points(lead, scoring_cfg, now)
    )
    if monetization_cfg is not None:
        points += _monetization_adjustment(lead.monetization, monetization_cfg)

    confidence_score = max(0, min(100, points))

    buckets = scoring_cfg.get("priority_buckets", {})
    high = buckets.get("high", 70)
    medium = buckets.get("medium", 45)
    if confidence_score >= high:
        priority = "high"
    elif confidence_score >= medium:
        priority = "medium"
    else:
        priority = "low"

    return ScoreResult(
        completeness_score=completeness_score,
        confidence_score=confidence_score,
        outreach_priority=priority,
    )
