import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from domain_hunter.orchestrator import _run_hunter_with_timeout
from domain_hunter.models import DomainRecord


class SlowHunter:
    SOURCE_NAME = "slow"

    async def hunt(self, seed_domain, vertical):
        await asyncio.sleep(999)
        return []


class FastHunter:
    SOURCE_NAME = "fast"

    async def hunt(self, seed_domain, vertical):
        return [DomainRecord("fast.com", {"fast"})]


@pytest.mark.asyncio
async def test_hunter_timeout_returns_empty():
    hunter = SlowHunter()
    source, result = await _run_hunter_with_timeout(hunter, "example.com", "test", timeout=1)
    assert source == "slow"
    assert result == "timeout"


@pytest.mark.asyncio
async def test_hunter_success_returns_records():
    hunter = FastHunter()
    source, result = await _run_hunter_with_timeout(hunter, "example.com", "test", timeout=10)
    assert source == "fast"
    assert len(result) == 1
    assert result[0].domain == "fast.com"


@pytest.mark.asyncio
async def test_hunter_exception_returns_error_string():
    class BrokenHunter:
        SOURCE_NAME = "broken"
        async def hunt(self, seed, vertical):
            raise ValueError("something went wrong")

    source, result = await _run_hunter_with_timeout(BrokenHunter(), "example.com", "test", timeout=10)
    assert source == "broken"
    assert "error:" in result
