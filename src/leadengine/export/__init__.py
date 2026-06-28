"""Export layer: turn persisted leads into deterministic CSV / JSON artifacts."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from ..storage import repository
from ..storage.schema import LeadRow
from . import csv as csv_export
from . import json as json_export

_WRITERS = {
    "csv": csv_export.write,
    "json": json_export.write,
}


def _iso(dt) -> str:
    return dt.isoformat() if dt is not None else ""


def lead_to_dict(row: LeadRow) -> dict:
    """Flat, ordered representation of a lead for export."""
    return {
        "registrable_domain": row.registrable_domain,
        "website": row.website,
        "company_name": row.company_name or "",
        "product_name": row.product_name or "",
        "description": row.description or "",
        "categories": ";".join(sorted(row.categories or [])),
        "country": row.country or "",
        "language": row.language or "",
        "owner_org": row.owner_org or "",
        "tech_stack": ";".join(sorted(row.tech_stack or [])),
        "hosting": row.hosting or "",
        "cms": row.cms or "",
        "framework": row.framework or "",
        "discovery_source": row.discovery_source,
        "monetization_type": row.monetization_type or "",
        "ad_networks": ";".join(sorted(row.ad_networks or [])),
        "revenue_intensity_score": row.revenue_intensity_score
        if row.revenue_intensity_score is not None
        else "",
        "friction_level": row.friction_level or "",
        "completeness_score": row.completeness_score,
        "confidence_score": row.confidence_score,
        "outreach_priority": row.outreach_priority,
        "contact_count": len(row.contacts),
        "primary_contact": row.contacts[0].email if row.contacts else "",
        "stage": row.stage,
        "first_seen": _iso(row.first_seen),
        "last_seen": _iso(row.last_seen),
        "last_changed": _iso(row.last_changed),
    }


def contact_rows(rows: list[LeadRow]) -> list[dict]:
    out: list[dict] = []
    for row in rows:
        for c in sorted(row.contacts, key=lambda x: x.email):
            out.append(
                {
                    "registrable_domain": row.registrable_domain,
                    "email": c.email,
                    "type": c.type,
                    "validation_status": c.validation_status,
                    "source": c.source,
                    "confidence": c.confidence,
                }
            )
    return out


def export_all(session: Session, output_dir: str | Path, formats: list[str]) -> list[Path]:
    """Write leads + contacts in each requested format. Returns written file paths."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = repository.all_leads(session)
    leads = [lead_to_dict(r) for r in rows]
    contacts = contact_rows(rows)

    written: list[Path] = []
    for fmt in formats:
        writer = _WRITERS.get(fmt)
        if writer is None:
            raise ValueError(f"Unsupported export format: {fmt!r}")
        written.extend(writer(out_dir, leads, contacts))
    return written
