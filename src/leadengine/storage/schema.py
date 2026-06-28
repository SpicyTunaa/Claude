"""SQLAlchemy ORM schema (SQLite).

Deliberately small: leads + their contacts/technologies, an append-only ``field_evidence``
table for provenance, and a ``runs`` table for per-execution KPI counts.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from ..core.models import utcnow


class Base(DeclarativeBase):
    pass


class LeadRow(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    registrable_domain: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    website: Mapped[str] = mapped_column(String(1024))
    company_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    product_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    categories: Mapped[list] = mapped_column(JSON, default=list)
    country: Mapped[str | None] = mapped_column(String(8), nullable=True)
    language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    owner_org: Mapped[str | None] = mapped_column(String(512), nullable=True)
    tech_stack: Mapped[list] = mapped_column(JSON, default=list)
    hosting: Mapped[str | None] = mapped_column(String(128), nullable=True)
    cms: Mapped[str | None] = mapped_column(String(128), nullable=True)
    framework: Mapped[str | None] = mapped_column(String(128), nullable=True)
    discovery_source: Mapped[str] = mapped_column(String(128), default="")

    # Optional monetization tags (NULL until the optional layer runs).
    monetization_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ad_networks: Mapped[list] = mapped_column(JSON, default=list)
    revenue_intensity_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    friction_level: Mapped[str | None] = mapped_column(String(16), nullable=True)

    completeness_score: Mapped[int] = mapped_column(Integer, default=0)
    confidence_score: Mapped[int] = mapped_column(Integer, default=0)
    outreach_priority: Mapped[str] = mapped_column(String(16), default="low")

    stage: Mapped[str] = mapped_column(String(32), default="discovered", index=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_changed: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    contacts: Mapped[list[ContactRow]] = relationship(
        back_populates="lead", cascade="all, delete-orphan"
    )
    technologies: Mapped[list[TechRow]] = relationship(
        back_populates="lead", cascade="all, delete-orphan"
    )


class ContactRow(Base):
    __tablename__ = "contacts"
    __table_args__ = (UniqueConstraint("lead_id", "email", name="uq_contact_lead_email"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)
    email: Mapped[str] = mapped_column(String(320))
    type: Mapped[str] = mapped_column(String(32), default="generic")
    validation_status: Mapped[str] = mapped_column(String(32), default="unvalidated")
    source: Mapped[str] = mapped_column(String(128), default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)

    lead: Mapped[LeadRow] = relationship(back_populates="contacts")


class TechRow(Base):
    __tablename__ = "technologies"
    __table_args__ = (
        UniqueConstraint("lead_id", "technology", name="uq_tech_lead_tech"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)
    technology: Mapped[str] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(64), default="")
    source: Mapped[str] = mapped_column(String(64), default="fingerprint")
    confidence: Mapped[float] = mapped_column(Float, default=0.6)
    version: Mapped[str | None] = mapped_column(String(64), nullable=True)

    lead: Mapped[LeadRow] = relationship(back_populates="technologies")


class FieldEvidenceRow(Base):
    """Append-only provenance: never updated or deleted, only inserted."""

    __tablename__ = "field_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)
    field: Mapped[str] = mapped_column(String(64))
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(128), default="")
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    raw_value: Mapped[str | None] = mapped_column(Text, nullable=True)


class RunRow(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(128), default="")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    discovered: Mapped[int] = mapped_column(Integer, default=0)
    new_leads: Mapped[int] = mapped_column(Integer, default=0)
    duplicates: Mapped[int] = mapped_column(Integer, default=0)
    with_contact: Mapped[int] = mapped_column(Integer, default=0)
    exported: Mapped[int] = mapped_column(Integer, default=0)
