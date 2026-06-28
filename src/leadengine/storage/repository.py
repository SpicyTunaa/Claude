"""Repository: all DB reads/writes for leads, contacts, technologies, evidence and runs.

Encapsulates dedup (by registrable domain), incremental update (first_seen / last_seen /
last_changed) and append-only evidence so the pipeline stays free of SQL.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..core.models import (
    Contact,
    FieldValue,
    Lead,
    MonetizationTags,
    Stage,
    TechSignal,
    utcnow,
)
from .schema import ContactRow, FieldEvidenceRow, LeadRow, RunRow, TechRow

# Fields whose change should bump ``last_changed``.
_TRACKED_FIELDS = (
    "website",
    "company_name",
    "product_name",
    "description",
    "categories",
    "country",
    "language",
    "owner_org",
    "tech_stack",
    "hosting",
    "cms",
    "framework",
)


def get_lead_row(session: Session, domain: str) -> LeadRow | None:
    return session.scalar(select(LeadRow).where(LeadRow.registrable_domain == domain))


def upsert_discovered(session: Session, lead: Lead) -> tuple[LeadRow, bool]:
    """Insert a freshly-discovered lead or refresh ``last_seen`` on an existing one.

    Returns ``(row, is_new)``. Discovery never regresses the processing stage of an
    existing lead.
    """
    row = get_lead_row(session, lead.registrable_domain)
    now = utcnow()
    if row is None:
        row = LeadRow(
            registrable_domain=lead.registrable_domain,
            website=lead.website,
            company_name=lead.company_name,
            product_name=lead.product_name,
            description=lead.description,
            categories=sorted(set(lead.categories)),
            discovery_source=lead.discovery_source,
            stage=Stage.DISCOVERED.value,
            first_seen=now,
            last_seen=now,
            last_changed=now,
        )
        session.add(row)
        session.flush()
        return row, True

    # Existing lead: refresh last_seen; merge any newly-provided descriptive fields.
    row.last_seen = now
    changed = False
    if lead.description and lead.description != row.description:
        row.description = lead.description
        changed = True
    if lead.company_name and lead.company_name != row.company_name:
        row.company_name = lead.company_name
        changed = True
    merged_categories = sorted(set(row.categories or []) | set(lead.categories))
    if merged_categories != (row.categories or []):
        row.categories = merged_categories
        changed = True
    if changed:
        row.last_changed = now
    session.flush()
    return row, False


def row_to_lead(row: LeadRow) -> Lead:
    lead = Lead(
        registrable_domain=row.registrable_domain,
        website=row.website,
        company_name=row.company_name,
        product_name=row.product_name,
        description=row.description,
        categories=list(row.categories or []),
        country=row.country,
        language=row.language,
        owner_org=row.owner_org,
        tech_stack=list(row.tech_stack or []),
        hosting=row.hosting,
        cms=row.cms,
        framework=row.framework,
        discovery_source=row.discovery_source,
        completeness_score=row.completeness_score,
        confidence_score=row.confidence_score,
        outreach_priority=row.outreach_priority,
        stage=Stage(row.stage),
        first_seen=row.first_seen,
        last_seen=row.last_seen,
        last_changed=row.last_changed,
    )
    lead.contacts = [
        Contact(
            email=c.email,
            type=c.type,
            validation_status=c.validation_status,
            source=c.source,
            confidence=c.confidence,
        )
        for c in row.contacts
    ]
    lead.technologies = [
        TechSignal(
            technology=t.technology,
            category=t.category,
            source=t.source,
            confidence=t.confidence,
            version=t.version,
        )
        for t in row.technologies
    ]
    lead.monetization = MonetizationTags(
        monetization_type=row.monetization_type,
        ad_networks=list(row.ad_networks or []),
        revenue_intensity_score=row.revenue_intensity_score,
        friction_level=row.friction_level,
    )
    return lead


def save_lead_progress(session: Session, lead: Lead, stage: Stage) -> LeadRow:
    """Persist the current state of a lead and advance its stage."""
    row = get_lead_row(session, lead.registrable_domain)
    if row is None:  # pragma: no cover — pipeline always discovers before processing
        row, _ = upsert_discovered(session, lead)

    changed = False
    for fname in _TRACKED_FIELDS:
        new_val = getattr(lead, fname)
        if isinstance(new_val, list):
            new_val = sorted(set(new_val))
        if getattr(row, fname) != new_val:
            setattr(row, fname, new_val)
            changed = True

    row.completeness_score = lead.completeness_score
    row.confidence_score = lead.confidence_score
    row.outreach_priority = lead.outreach_priority

    m = lead.monetization
    row.monetization_type = m.monetization_type
    row.ad_networks = list(m.ad_networks)
    row.revenue_intensity_score = m.revenue_intensity_score
    row.friction_level = m.friction_level

    row.stage = stage.value
    row.last_seen = utcnow()
    if changed:
        row.last_changed = utcnow()

    _sync_contacts(session, row, lead.contacts)
    _sync_technologies(session, row, lead.technologies)
    session.flush()
    return row


def _sync_contacts(session: Session, row: LeadRow, contacts: list[Contact]) -> None:
    existing = {c.email: c for c in row.contacts}
    for c in contacts:
        if c.email in existing:
            cur = existing[c.email]
            cur.type = c.type
            cur.validation_status = c.validation_status
            cur.confidence = c.confidence
            cur.source = c.source
        else:
            row.contacts.append(
                ContactRow(
                    email=c.email,
                    type=c.type,
                    validation_status=c.validation_status,
                    source=c.source,
                    confidence=c.confidence,
                )
            )


def _sync_technologies(session: Session, row: LeadRow, techs: list[TechSignal]) -> None:
    existing = {t.technology for t in row.technologies}
    for t in techs:
        if t.technology not in existing:
            row.technologies.append(
                TechRow(
                    technology=t.technology,
                    category=t.category,
                    source=t.source,
                    confidence=t.confidence,
                    version=t.version,
                )
            )


def add_evidence(session: Session, lead_id: int, values: list[FieldValue]) -> None:
    """Append provenance rows. Never updates or deletes existing evidence."""
    for v in values:
        if v.value is None:
            continue
        session.add(
            FieldEvidenceRow(
                lead_id=lead_id,
                field=v.field,
                value=v.value,
                source=v.source,
                source_url=v.url,
                observed_at=v.observed_at,
                confidence=v.confidence,
                raw_value=v.raw_value,
            )
        )


def leads_to_process(session: Session) -> list[LeadRow]:
    """Resume target: all leads not yet exported, ordered deterministically."""
    stmt = (
        select(LeadRow)
        .where(LeadRow.stage != Stage.EXPORTED.value)
        .order_by(LeadRow.registrable_domain)
    )
    return list(session.scalars(stmt))


def all_leads(session: Session) -> list[LeadRow]:
    stmt = (
        select(LeadRow)
        .options(selectinload(LeadRow.contacts), selectinload(LeadRow.technologies))
        .order_by(LeadRow.registrable_domain)
    )
    return list(session.scalars(stmt))


def start_run(session: Session, source: str) -> RunRow:
    run = RunRow(source=source)
    session.add(run)
    session.flush()
    return run


def finish_run(session: Session, run: RunRow, **counts: int) -> None:
    for key, value in counts.items():
        setattr(run, key, value)
    run.finished_at = utcnow()
    session.flush()
