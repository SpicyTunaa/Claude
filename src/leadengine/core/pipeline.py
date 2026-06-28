"""Pipeline orchestrator: a single linear pass with per-lead, DB-backed checkpoints.

Discovery upserts leads; processing runs enrich -> extract contact -> fingerprint
(+ optional monetization) -> score for each not-yet-exported lead, persisting after every
stage so an interrupted run can resume. Export writes the full current dataset.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .. import export as export_layer
from ..adapters import AdapterContext, available_adapters, get_adapter
from ..contact.extract import extract_contacts
from ..enrichment.website import PageBundle, fetch_page, parse_page
from ..scoring.engine import score_lead
from ..storage import repository
from ..storage.db import init_db, make_engine, make_session_factory
from ..storage.schema import LeadRow
from ..techdetect import detector
from ..techdetect import monetization as monetization_detect
from .config import Settings
from .fetcher import Fetcher
from .logging import get_logger
from .models import (
    STAGE_ORDER,
    FieldValue,
    Lead,
    RawHit,
    Stage,
    normalize_url,
    registrable_domain,
)

log = get_logger("pipeline")


@dataclass
class RunStats:
    discovered: int = 0
    new_leads: int = 0
    duplicates: int = 0
    processed: int = 0
    with_contact: int = 0
    exported: int = 0
    files: list = field(default_factory=list)


class Pipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.engine = make_engine(settings.database.url)
        init_db(self.engine)
        self.Session = make_session_factory(self.engine)
        # In-memory page cache for the current process (adapter-embedded HTML, e.g. mock).
        self._page_cache: dict[str, PageBundle] = {}

    # -- public entry points -----------------------------------------------------------

    async def run(self, *, sources: list[str] | None = None) -> RunStats:
        stats = RunStats()
        async with Fetcher(self.settings.fetcher) as fetcher:
            await self._discover(fetcher, stats, sources)
            await self._process(fetcher, stats)
            self._export(stats)
        return stats

    async def resume(self) -> RunStats:
        """Process any not-yet-exported leads without re-running discovery."""
        stats = RunStats()
        async with Fetcher(self.settings.fetcher) as fetcher:
            await self._process(fetcher, stats)
            self._export(stats)
        return stats

    # -- discovery ---------------------------------------------------------------------

    def _enabled_sources(self, sources: list[str] | None) -> list[str]:
        available = available_adapters()
        enabled = [
            name
            for name, cfg in self.settings.sources.items()
            if cfg.enabled and name in available
        ]
        if sources:
            enabled = [n for n in enabled if n in sources]
        return sorted(enabled)

    def _context(self, fetcher: Fetcher, name: str) -> AdapterContext:
        return AdapterContext(
            fetcher=fetcher,
            config=self.settings.source(name),
            log=get_logger(f"adapter.{name}"),
        )

    async def _discover(self, fetcher: Fetcher, stats: RunStats, sources: list[str] | None) -> None:
        allowed_categories = self.settings.category_slugs()
        for name in self._enabled_sources(sources):
            adapter = get_adapter(name)()
            ctx = self._context(fetcher, name)
            log.info("discovery_start", source=name)
            try:
                async for hit in adapter.discover(ctx):
                    self._ingest_hit(hit, name, allowed_categories, stats)
            except Exception as exc:  # noqa: BLE001 — one source must not abort the run
                log.warning("discovery_error", source=name, error=str(exc))
            log.info("discovery_done", source=name, discovered=stats.discovered)

    def _ingest_hit(
        self, hit: RawHit, source: str, allowed_categories: set[str], stats: RunStats
    ) -> None:
        domain = registrable_domain(hit.url)
        if not domain:
            return
        stats.discovered += 1
        categories = [
            c for c in hit.categories if not allowed_categories or c in allowed_categories
        ]
        lead = Lead(
            registrable_domain=domain,
            website=normalize_url(hit.url),
            company_name=hit.title,
            description=hit.description,
            categories=categories,
            discovery_source=source,
        )
        with self.Session() as session:
            row, is_new = repository.upsert_discovered(session, lead)
            repository.add_evidence(
                session,
                row.id,
                [
                    FieldValue(
                        field="discovery_url",
                        value=lead.website,
                        source=source,
                        url=lead.website,
                        confidence=1.0,
                        raw_value=hit.title,
                    )
                ],
            )
            session.commit()
        if is_new:
            stats.new_leads += 1
        else:
            stats.duplicates += 1
        # Cache adapter-embedded HTML so processing can run fully offline.
        if "html" in hit.extra:
            self._page_cache[domain] = PageBundle(
                final_url=lead.website, html=hit.extra["html"], headers={}
            )

    # -- processing --------------------------------------------------------------------

    async def _bundle_for(self, fetcher: Fetcher, lead: Lead) -> PageBundle | None:
        if lead.registrable_domain in self._page_cache:
            return self._page_cache[lead.registrable_domain]
        if not self.settings.enrichment.enabled:
            return None
        rate = self.settings.source(lead.discovery_source).rate_limit
        return await fetch_page(fetcher, lead.website, rate_limit=rate)

    async def _process(self, fetcher: Fetcher, stats: RunStats) -> None:
        with self.Session() as session:
            lead_ids = [r.id for r in repository.leads_to_process(session)]

        for lead_id in lead_ids:
            with self.Session() as session:
                row = session.get(LeadRow, lead_id)
                if row is None:
                    continue
                lead = repository.row_to_lead(row)
            bundle = await self._bundle_for(fetcher, lead)
            with self.Session() as session:
                self._process_one(session, lead, bundle, fetcher)
                session.commit()
            stats.processed += 1
            if lead.contacts:
                stats.with_contact += 1

    def _should_run(self, lead: Lead, stage: Stage) -> bool:
        return STAGE_ORDER.index(stage) > STAGE_ORDER.index(lead.stage)

    def _process_one(
        self, session, lead: Lead, bundle: PageBundle | None, fetcher: Fetcher
    ) -> None:
        row = repository.get_lead_row(session, lead.registrable_domain)
        assert row is not None
        lead_id = row.id

        # --- enrichment ---
        if self._should_run(lead, Stage.ENRICHED):
            if bundle is not None:
                evidence = parse_page(lead, bundle, source=lead.discovery_source)
                repository.add_evidence(session, lead_id, evidence)
            repository.save_lead_progress(session, lead, Stage.ENRICHED)

        # --- contact discovery ---
        if self._should_run(lead, Stage.CONTACTED):
            if bundle is not None:
                evidence = extract_contacts(lead, bundle, source=lead.discovery_source)
                repository.add_evidence(session, lead_id, evidence)
            repository.save_lead_progress(session, lead, Stage.CONTACTED)

        # --- technology fingerprinting (+ optional monetization) ---
        if self._should_run(lead, Stage.FINGERPRINTED):
            if bundle is not None:
                self._apply_fingerprint(lead, bundle)
                self._apply_monetization(lead, bundle)
            repository.save_lead_progress(session, lead, Stage.FINGERPRINTED)

        # --- scoring ---
        if self._should_run(lead, Stage.SCORED):
            result = score_lead(
                lead,
                self.settings.scoring,
                monetization_cfg=self.settings.monetization,
            )
            lead.completeness_score = result.completeness_score
            lead.confidence_score = result.confidence_score
            lead.outreach_priority = result.outreach_priority
            repository.save_lead_progress(session, lead, Stage.SCORED)

    def _apply_fingerprint(self, lead: Lead, bundle: PageBundle) -> None:
        signals = detector.detect(bundle)
        lead.technologies = signals
        lead.tech_stack = sorted({s.technology for s in signals})
        for s in signals:
            if s.category == "hosting" and not lead.hosting:
                lead.hosting = s.technology
            elif s.category == "cms" and not lead.cms:
                lead.cms = s.technology
            elif s.category == "framework" and not lead.framework:
                lead.framework = s.technology

    def _apply_monetization(self, lead: Lead, bundle: PageBundle) -> None:
        """Optional, non-blocking. Any failure is swallowed — never breaks the pipeline."""
        if not self.settings.monetization.enabled:
            return
        try:
            lead.monetization = monetization_detect.detect(bundle)
        except Exception as exc:  # noqa: BLE001 — intelligence layer must not affect core
            log.warning("monetization_failed", domain=lead.registrable_domain, error=str(exc))

    # -- export ------------------------------------------------------------------------

    def _export(self, stats: RunStats) -> None:
        with self.Session() as session:
            files = export_layer.export_all(
                session, self.settings.export.output_dir, self.settings.export.formats
            )
            # Mark every processed (SCORED) lead as exported.
            rows = repository.leads_to_process(session)
            exported = 0
            for row in rows:
                if row.stage == Stage.SCORED.value:
                    row.stage = Stage.EXPORTED.value
                    exported += 1
            session.commit()
            stats.exported = exported
            stats.files = [str(p) for p in files]
