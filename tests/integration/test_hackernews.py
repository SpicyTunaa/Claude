"""Integration test for the real Hacker News adapter with all HTTP mocked (offline)."""

from __future__ import annotations

import httpx
import respx

from leadengine.core.config import SourceConfig
from leadengine.core.pipeline import Pipeline
from leadengine.storage import repository
from leadengine.storage.db import make_engine, make_session_factory

_API = "https://hacker-news.firebaseio.com/v0"

_WP_HTML = """
<html><head><meta name="generator" content="WordPress 6.5"></head>
<body><a href="mailto:support@startup-one.example">support</a></body></html>
"""


@respx.mock
async def test_hackernews_discovers_and_enriches(settings):
    settings.sources = {
        "hackernews": SourceConfig(enabled=True, rate_limit=100.0, max_items=10),
        "example": SourceConfig(enabled=False),
    }

    respx.get(f"{_API}/showstories.json").mock(return_value=httpx.Response(200, json=[1, 2, 3]))
    respx.get(f"{_API}/item/1.json").mock(
        return_value=httpx.Response(200, json={"url": "https://startup-one.example", "title": "One", "by": "alice"})
    )
    # Item 2 is an "Ask HN" with no URL -> must be skipped.
    respx.get(f"{_API}/item/2.json").mock(
        return_value=httpx.Response(200, json={"title": "Ask HN: anything?", "by": "bob"})
    )
    respx.get(f"{_API}/item/3.json").mock(
        return_value=httpx.Response(200, json={"url": "https://startup-three.example", "title": "Three", "by": "carol"})
    )
    respx.get("https://startup-one.example").mock(return_value=httpx.Response(200, text=_WP_HTML))
    respx.get("https://startup-three.example").mock(
        return_value=httpx.Response(200, text="<html><body><p>plain</p></body></html>")
    )

    stats = await Pipeline(settings).run(sources=["hackernews"])
    assert stats.new_leads == 2  # items 1 and 3; item 2 skipped

    engine = make_engine(settings.database.url)
    with make_session_factory(engine)() as session:
        rows = {r.registrable_domain: r for r in repository.all_leads(session)}

    assert set(rows) == {"startup-one.example", "startup-three.example"}
    one = rows["startup-one.example"]
    assert "WordPress" in (one.tech_stack or [])
    assert any(c.email == "support@startup-one.example" for c in one.contacts)
    assert one.stage == "exported"
