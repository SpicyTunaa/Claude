import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from domain_hunter.hunters.crtsh import CrtShHunter
from domain_hunter import cache


@pytest.fixture
def hunter(mock_session, rate_limiter, config):
    return CrtShHunter(mock_session, rate_limiter, config)


def make_response(data, status=200):
    resp = MagicMock()
    resp.status = status
    resp.json = AsyncMock(return_value=data)
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    return resp


@pytest.mark.asyncio
async def test_hunt_parses_domains(hunter, monkeypatch):
    monkeypatch.setattr(cache, "load", lambda *a, **kw: None)
    monkeypatch.setattr(cache, "save", lambda *a: None)

    crt_data = [
        {"name_value": "sub.example.com"},
        {"name_value": "*.example.com\nsub2.example.com"},
        {"name_value": "other.net"},
    ]
    resp = make_response(crt_data)
    hunter._get = AsyncMock(return_value=resp)

    with patch("asyncio.sleep", new_callable=AsyncMock):
        results = await hunter.hunt("example.com", "test")

    domains = {r.domain for r in results}
    assert "sub.example.com" in domains
    assert "sub2.example.com" in domains
    assert "other.net" in domains
    assert all(r.sources == {"crtsh"} for r in results)


@pytest.mark.asyncio
async def test_hunt_handles_http_error(hunter, monkeypatch):
    monkeypatch.setattr(cache, "load", lambda *a, **kw: None)
    monkeypatch.setattr(cache, "save", lambda *a: None)

    resp = make_response([], status=503)
    hunter._get = AsyncMock(return_value=resp)

    with patch("asyncio.sleep", new_callable=AsyncMock):
        results = await hunter.hunt("example.com", "test")

    assert results == []


@pytest.mark.asyncio
async def test_hunt_handles_exception(hunter, monkeypatch):
    monkeypatch.setattr(cache, "load", lambda *a, **kw: None)
    monkeypatch.setattr(cache, "save", lambda *a: None)

    hunter._get = AsyncMock(side_effect=Exception("network error"))
    results = await hunter.hunt("example.com", "test")
    assert results == []


@pytest.mark.asyncio
async def test_hunt_returns_cache_hit(hunter, monkeypatch):
    monkeypatch.setattr(cache, "load", lambda *a, **kw: ["cached.com", "cached2.com"])

    results = await hunter.hunt("example.com", "test")
    assert len(results) == 2
    assert any(r.domain == "cached.com" for r in results)
