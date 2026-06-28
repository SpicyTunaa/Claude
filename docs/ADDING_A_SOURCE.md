# Adding a new discovery source (< 30 minutes)

Every source is a self-contained adapter. Adding one means creating **one file** in
`src/leadengine/adapters/sources/` and adding a config block — **no core code changes**.

## 1. Create the adapter file

`src/leadengine/adapters/sources/mysource.py`:

```python
from __future__ import annotations

from collections.abc import AsyncIterator

from ...core.models import AdapterMetadata, RawHit
from .. import register
from ..base import AdapterContext, SourceAdapter


@register
class MySource(SourceAdapter):
    name = "mysource"  # must match the key in config/config.yaml -> sources

    def metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            name=self.name,
            categories=["saas"],          # any slugs from config/categories.yaml
            rate_limit=1.0,               # requests/second hint
            description="What this source discovers.",
        )

    async def discover(self, ctx: AdapterContext) -> AsyncIterator[RawHit]:
        # Use the SHARED fetcher (rate-limited, robots-aware, UA-rotating).
        result = await ctx.fetcher.fetch("https://example.com/list", rate_limit=ctx.config.rate_limit)
        for item in parse(result.text):          # your parsing
            yield RawHit(
                source=self.name,
                url=item["url"],                 # external business URL
                title=item.get("name"),
                description=item.get("tagline"),
                categories=["saas"],
                # extra={"html": "<...>"}        # optional: embed HTML to skip a re-fetch
            )

    async def health_check(self, ctx: AdapterContext) -> bool:
        r = await ctx.fetcher.try_fetch("https://example.com/list")
        return bool(r and r.status_code == 200)
```

### Rules
- Touch the world **only** through `ctx.fetcher` — never create your own HTTP client and
  never import the pipeline, storage, or other adapters.
- `discover()` yields `RawHit`s. The core handles dedup (by registrable domain),
  enrichment, contact extraction, fingerprinting, scoring, and export.
- Read adapter-specific config via `ctx.setting("key", default)` or `ctx.config.<field>`.
- `normalize()`/`enrich()` are optional hooks with sensible defaults — override only if
  the source provides extra structured fields.

## 2. Enable it in config

`config/config.yaml`:

```yaml
sources:
  mysource:
    enabled: true
    rate_limit: 1.0
    # any extra keys (e.g. max_items: 100) are readable via ctx.setting(...)
```

## 3. Verify

```bash
.venv/bin/leadengine list-sources      # mysource should appear
.venv/bin/leadengine adapter-health    # mysource health_check runs
.venv/bin/leadengine run --source mysource
```

## 4. Add a fixture-backed test (recommended, offline)

Mock HTTP with `respx` and assert leads are produced — see
`tests/integration/test_hackernews.py` for a complete example.

That's it: the registry auto-imports every module in `sources/`, so the new file is picked
up automatically.
