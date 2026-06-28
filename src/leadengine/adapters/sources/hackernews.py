"""Hacker News "Show HN" discovery source (real, public Firebase API, no key).

Pulls the public Show-HN story list and emits each story's external URL as a lead. Network
calls go through the shared fetcher; offline tests mock the endpoints with recorded JSON.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from ...core.logging import get_logger
from ...core.models import AdapterMetadata, RawHit
from .. import register
from ..base import AdapterContext, SourceAdapter

_API = "https://hacker-news.firebaseio.com/v0"
_SHOW_STORIES = f"{_API}/showstories.json"

log = get_logger("adapter.hackernews")


@register
class HackerNewsSource(SourceAdapter):
    name = "hackernews"

    def metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            name=self.name,
            categories=["website", "saas", "developer-tool"],
            rate_limit=1.0,
            description="Show HN stories with an external URL (public Firebase API).",
        )

    async def discover(self, ctx: AdapterContext) -> AsyncIterator[RawHit]:
        max_items = int(ctx.setting("max_items", 50))
        rate = ctx.config.rate_limit
        listing = await ctx.fetcher.fetch(_SHOW_STORIES, rate_limit=rate)
        try:
            ids = json.loads(listing.text)
        except json.JSONDecodeError:
            ctx.log.warning("hackernews_bad_listing")
            return
        for story_id in ids[:max_items]:
            item = await ctx.fetcher.try_fetch(f"{_API}/item/{story_id}.json", rate_limit=rate)
            if item is None:
                continue
            try:
                data = json.loads(item.text)
            except json.JSONDecodeError:
                continue
            if not data:
                continue
            url = data.get("url")
            if not url:  # "Ask HN" / text posts have no external URL — skip
                continue
            yield RawHit(
                source=self.name,
                url=url,
                title=data.get("title"),
                description=data.get("title"),
                categories=["website"],
                extra={"hn_id": str(story_id), "author": str(data.get("by", ""))},
            )

    async def health_check(self, ctx: AdapterContext) -> bool:
        result = await ctx.fetcher.try_fetch(_SHOW_STORIES, rate_limit=ctx.config.rate_limit)
        return bool(result and result.status_code == 200)
