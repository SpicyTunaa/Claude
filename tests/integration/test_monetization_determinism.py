"""The optional monetization layer must never change core scores when affect_score=False."""

from __future__ import annotations

from pathlib import Path

from leadengine.core.config import load_settings
from leadengine.core.pipeline import Pipeline
from leadengine.storage import repository
from leadengine.storage.db import make_engine, make_session_factory


def _scores(settings) -> dict[str, int]:
    engine = make_engine(settings.database.url)
    with make_session_factory(engine)() as session:
        return {r.registrable_domain: r.confidence_score for r in repository.all_leads(session)}


def _fresh_settings(tmp_path: Path, name: str, *, monetization_enabled: bool):
    s = load_settings()
    s.database.url = f"sqlite+pysqlite:///{tmp_path / f'{name}.db'}"
    s.export.output_dir = str(tmp_path / f"out_{name}")
    s.fetcher.respect_robots = False
    s.monetization.enabled = monetization_enabled
    s.monetization.affect_score = False
    from leadengine.core.config import SourceConfig

    s.sources = {"example": SourceConfig(enabled=True, rate_limit=100.0, count=6)}
    return s


async def test_monetization_layer_is_non_blocking_and_score_neutral(tmp_path):
    on = _fresh_settings(tmp_path, "on", monetization_enabled=True)
    off = _fresh_settings(tmp_path, "off", monetization_enabled=False)

    await Pipeline(on).run(sources=["example"])
    await Pipeline(off).run(sources=["example"])

    # With affect_score=False, enabling the layer must not change confidence scores.
    assert _scores(on) == _scores(off)

    # ...but the layer DID populate tags when enabled, and left them empty when disabled.
    engine_on = make_engine(on.database.url)
    with make_session_factory(engine_on)() as session:
        rows = repository.all_leads(session)
    assert all(r.monetization_type for r in rows)

    engine_off = make_engine(off.database.url)
    with make_session_factory(engine_off)() as session:
        rows_off = repository.all_leads(session)
    assert all(r.monetization_type is None for r in rows_off)
