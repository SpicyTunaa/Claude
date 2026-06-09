import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from contextlib import asynccontextmanager

import aiohttp

from domain_hunter.models import DomainRecord
from domain_hunter.validators.http_validator import validate_one, LIVE_STATUSES


@pytest.fixture
def config():
    from domain_hunter.config import Config
    cfg = Config()
    cfg.HTTP_VALIDATOR_CONCURRENCY = 5
    cfg.HTTP_VALIDATOR_TIMEOUT = 3
    return cfg


def make_resp(status, url="https://example.com"):
    resp = MagicMock()
    resp.status = status
    resp.url = url
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    return resp


@pytest.mark.asyncio
async def test_live_200(config):
    record = DomainRecord("example.com", {"crtsh"})
    session = MagicMock()
    session.get = MagicMock(return_value=make_resp(200))
    sem = asyncio.Semaphore(5)
    result = await validate_one(record, session, sem, config)
    assert result.is_live is True
    assert result.status_code == 200


@pytest.mark.asyncio
async def test_http_validator_403_live(config):
    record = DomainRecord("example.com", {"crtsh"})
    session = MagicMock()
    session.get = MagicMock(return_value=make_resp(403))
    sem = asyncio.Semaphore(5)
    result = await validate_one(record, session, sem, config)
    assert result.is_live is True
    assert result.status_code == 403


@pytest.mark.asyncio
async def test_http_validator_401_live(config):
    record = DomainRecord("example.com", {"crtsh"})
    session = MagicMock()
    session.get = MagicMock(return_value=make_resp(401))
    sem = asyncio.Semaphore(5)
    result = await validate_one(record, session, sem, config)
    assert result.is_live is True


@pytest.mark.asyncio
async def test_404_not_live(config):
    record = DomainRecord("example.com", {"crtsh"})
    session = MagicMock()
    session.get = MagicMock(return_value=make_resp(404))
    sem = asyncio.Semaphore(5)
    result = await validate_one(record, session, sem, config)
    assert result.is_live is False
    assert result.status_code == 404


@pytest.mark.asyncio
async def test_dead_domain_connection_error(config):
    record = DomainRecord("dead.example.com", {"crtsh"})
    session = MagicMock()
    session.get = MagicMock(side_effect=aiohttp.ClientError("connection refused"))
    sem = asyncio.Semaphore(5)
    result = await validate_one(record, session, sem, config)
    assert result.is_live is False


@pytest.mark.asyncio
async def test_final_url_captured(config):
    record = DomainRecord("example.com", {"crtsh"})
    final = "https://www.example.com/redirected"
    session = MagicMock()
    session.get = MagicMock(return_value=make_resp(200, url=final))
    sem = asyncio.Semaphore(5)
    result = await validate_one(record, session, sem, config)
    assert result.final_url == final


def test_live_statuses_set():
    assert 403 in LIVE_STATUSES
    assert 401 in LIVE_STATUSES
    assert 200 in LIVE_STATUSES
    assert 301 in LIVE_STATUSES
    assert 404 not in LIVE_STATUSES
    assert 500 not in LIVE_STATUSES
