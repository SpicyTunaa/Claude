"""End-to-end pipeline tests using the deterministic offline example source."""

from __future__ import annotations

import json
from pathlib import Path

from leadengine.core.pipeline import Pipeline
from leadengine.storage import repository
from leadengine.storage.db import make_engine, make_session_factory


def _leads(settings):
    engine = make_engine(settings.database.url)
    with make_session_factory(engine)() as session:
        return repository.all_leads(session)


async def test_full_pipeline_produces_actionable_leads(settings):
    stats = await Pipeline(settings).run(sources=["example"])
    assert stats.new_leads == 6
    assert stats.with_contact == 6
    assert stats.exported == 6

    rows = _leads(settings)
    assert len(rows) == 6
    assert all(r.stage == "exported" for r in rows)
    assert all(r.contacts for r in rows)               # every lead has a public contact
    assert all(r.confidence_score > 0 for r in rows)
    assert any(r.tech_stack for r in rows)             # some have a tech fingerprint
    assert all(r.monetization_type for r in rows)      # monetization layer tagged everything

    out = Path(settings.export.output_dir)
    for name in ("leads.csv", "contacts.csv", "leads.json", "contacts.json"):
        assert (out / name).exists()
    data = json.loads((out / "leads.json").read_text())
    assert len(data) == 6


async def test_rerun_is_incremental(settings):
    await Pipeline(settings).run(sources=["example"])
    stats2 = await Pipeline(settings).run(sources=["example"])
    assert stats2.new_leads == 0
    assert stats2.duplicates == 6


async def test_resume_completes_unfinished_leads(settings):
    await Pipeline(settings).run(sources=["example"])

    # Simulate an interrupted run: regress two leads to an earlier stage.
    engine = make_engine(settings.database.url)
    Session = make_session_factory(engine)
    with Session() as session:
        for row in repository.all_leads(session)[:2]:
            row.stage = "discovered"
        session.commit()

    stats = await Pipeline(settings).resume()
    assert stats.processed >= 2

    with Session() as session:
        assert all(r.stage == "exported" for r in repository.all_leads(session))


async def test_output_is_deterministic_across_fresh_runs(tmp_path, settings):
    from leadengine.core.config import load_settings

    await Pipeline(settings).run(sources=["example"])
    first = (Path(settings.export.output_dir) / "leads.json").read_text()

    s2 = load_settings()
    s2.database.url = f"sqlite+pysqlite:///{tmp_path / 'second.db'}"
    s2.export.output_dir = str(tmp_path / "out2")
    s2.fetcher.respect_robots = False
    s2.sources = settings.sources
    await Pipeline(s2).run(sources=["example"])
    second = (Path(s2.export.output_dir) / "leads.json").read_text()

    assert first == second
