import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from domain_hunter import cache


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path / ".cache")


def test_cache_safe_key():
    key1 = cache._key("crtsh", "example.com")
    key2 = cache._key("crtsh", "evil../../../etc/passwd")
    key3 = cache._key("crtsh", "a" * 300)

    for key in (key1, key2, key3):
        assert len(key) == 16
        assert key.isalnum()
        assert "/" not in key
        assert "." not in key


def test_cache_save_and_load():
    cache.save("crtsh", "example.com", ["a.com", "b.com"])
    result = cache.load("crtsh", "example.com", use_cache=True)
    assert set(result) == {"a.com", "b.com"}


def test_cache_metadata_structure(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)
    cache.save("crtsh", "example.com", ["x.com"])
    path = tmp_path / f"{cache._key('crtsh', 'example.com')}.json"
    data = json.loads(path.read_text())
    assert "source" in data
    assert "seed" in data
    assert "created_at" in data
    assert "domains" in data
    assert data["source"] == "crtsh"
    assert data["seed"] == "example.com"


def test_cache_ttl_expired(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)
    cache.save("crtsh", "example.com", ["x.com"])
    path = tmp_path / f"{cache._key('crtsh', 'example.com')}.json"

    # Backdate created_at by 25 hours
    data = json.loads(path.read_text())
    data["created_at"] = (datetime.utcnow() - timedelta(hours=25)).isoformat()
    path.write_text(json.dumps(data))

    result = cache.load("crtsh", "example.com", use_cache=True)
    assert result is None


def test_cache_disabled_returns_none():
    cache.save("crtsh", "example.com", ["x.com"])
    result = cache.load("crtsh", "example.com", use_cache=False)
    assert result is None


def test_cache_miss_returns_none():
    result = cache.load("crtsh", "nonexistent.com", use_cache=True)
    assert result is None
