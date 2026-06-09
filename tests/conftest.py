import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest_asyncio

from domain_hunter.config import Config
from domain_hunter.rate_limiter import RateLimiter


@pytest.fixture
def config(tmp_path):
    cfg = Config()
    cfg.OUTPUT_DIR = tmp_path / "output"
    cfg.HACKERTARGET_QUOTA_FILE = tmp_path / ".dh_ht_quota.json"
    cfg.HTTP_VALIDATOR_CONCURRENCY = 5
    cfg.HTTP_VALIDATOR_TIMEOUT = 3
    cfg.DISABLED_HUNTERS = set()
    cfg.GITHUB_TOKEN = ""
    return cfg


@pytest.fixture
def rate_limiter(config):
    rl = RateLimiter(config.HACKERTARGET_QUOTA_FILE)
    # Override acquire to be a no-op in tests
    rl.acquire = AsyncMock(return_value=None)
    return rl


@pytest.fixture
def mock_session():
    session = MagicMock(spec=aiohttp.ClientSession)
    return session
