from datetime import datetime

from leadengine.core.config import load_settings
from leadengine.core.models import Contact, Lead, TechSignal


def _lead() -> Lead:
    lead = Lead(
        registrable_domain="acme.example",
        website="https://acme.example",
        company_name="Acme",
        description="A demo product",
        categories=["saas"],
        owner_org="Acme Labs",
        first_seen=datetime(2026, 6, 28, 12, 0, 0),
    )
    lead.contacts = [Contact(email="support@acme.example", type="support")]
    lead.technologies = [TechSignal(technology="React", category="framework")]
    lead.tech_stack = ["React"]
    return lead


def test_scoring_is_deterministic_and_bucketed():
    from leadengine.scoring.engine import score_lead

    cfg = load_settings().scoring
    now = datetime(2026, 6, 28, 12, 0, 0)
    r1 = score_lead(_lead(), cfg, now=now)
    r2 = score_lead(_lead(), cfg, now=now)
    assert r1 == r2
    assert 0 <= r1.confidence_score <= 100
    assert 0 <= r1.completeness_score <= 100
    assert r1.outreach_priority in {"low", "medium", "high"}


def test_empty_lead_scores_low():
    from leadengine.scoring.engine import score_lead

    cfg = load_settings().scoring
    now = datetime(2026, 9, 1, 12, 0, 0)  # old + empty
    lead = Lead(registrable_domain="x.example", website="https://x.example",
                first_seen=datetime(2026, 1, 1))
    res = score_lead(lead, cfg, now=now)
    assert res.outreach_priority == "low"
    assert res.completeness_score < 50
