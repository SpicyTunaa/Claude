import httpx
import pytest
import respx

from leadengine.core.config import FetcherConfig
from leadengine.core.fetcher import Fetcher, RobotsDisallowed


@respx.mock
async def test_fetch_returns_text():
    respx.get("https://api.example/data").mock(return_value=httpx.Response(200, text="hello"))
    async with Fetcher(FetcherConfig(respect_robots=False)) as f:
        result = await f.fetch("https://api.example/data")
    assert result.status_code == 200
    assert result.text == "hello"


@respx.mock
async def test_fetch_retries_on_503_then_succeeds():
    route = respx.get("https://api.example/flaky").mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(200, text="ok"),
        ]
    )
    async with Fetcher(FetcherConfig(respect_robots=False, max_retries=3)) as f:
        result = await f.fetch("https://api.example/flaky")
    assert result.text == "ok"
    assert route.call_count == 2


@respx.mock
async def test_robots_disallow_blocks_fetch():
    respx.get("https://blocked.example/robots.txt").mock(
        return_value=httpx.Response(200, text="User-agent: *\nDisallow: /")
    )
    respx.get("https://blocked.example/page").mock(return_value=httpx.Response(200, text="x"))
    async with Fetcher(FetcherConfig(respect_robots=True)) as f:
        with pytest.raises(RobotsDisallowed):
            await f.fetch("https://blocked.example/page")


@respx.mock
async def test_try_fetch_returns_none_on_error():
    respx.get("https://api.example/boom").mock(side_effect=httpx.ConnectError("down"))
    async with Fetcher(FetcherConfig(respect_robots=False, max_retries=2)) as f:
        assert await f.try_fetch("https://api.example/boom") is None
