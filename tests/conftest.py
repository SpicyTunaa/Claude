"""Shared pytest fixtures. All tests run fully offline and with a frozen clock."""

from __future__ import annotations

import pytest

from leadengine.core.config import SourceConfig, load_settings


@pytest.fixture(autouse=True)
def _frozen_clock(monkeypatch):
    # Deterministic timestamps across the whole suite.
    monkeypatch.setenv("LEADENGINE_FROZEN_NOW", "2026-06-28T12:00:00")


@pytest.fixture
def settings(tmp_path):
    """Settings pointed at a temp SQLite DB + output dir, robots disabled for mocks."""
    s = load_settings()
    s.database.url = f"sqlite+pysqlite:///{tmp_path / 'test.db'}"
    s.export.output_dir = str(tmp_path / "out")
    s.fetcher.respect_robots = False
    # Small, fast example dataset; only the example source enabled by default in tests.
    s.sources = {
        "example": SourceConfig(enabled=True, rate_limit=100.0, count=6),
        "hackernews": SourceConfig(enabled=False, rate_limit=100.0),
    }
    return s
