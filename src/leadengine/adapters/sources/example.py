"""Example (mock) discovery source — fully deterministic and offline.

Generates synthetic-but-realistic leads with self-contained HTML so the whole pipeline
(enrich -> contact -> fingerprint -> score -> export) can run and be tested without any
network. Demonstrates the plugin contract; copy this file to add a real source.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from ...core.models import AdapterMetadata, RawHit
from .. import register
from ..base import AdapterContext, SourceAdapter

# Rotating category + tech profiles keep the generated dataset varied yet deterministic.
_CATEGORIES = ["saas", "ai-tool", "web-app", "developer-tool", "website"]
_GENERATORS = ["WordPress 6.5", "", "Drupal 10", "", "Ghost 5.0"]
_HAS_REACT = [True, False, True, False, False]
_HAS_ADS = [False, True, False, True, False]  # embeds an ad-network script when True


def _html_for(idx: int, domain: str, name: str) -> str:
    generator = _GENERATORS[idx % len(_GENERATORS)]
    gen_meta = f'<meta name="generator" content="{generator}">' if generator else ""
    react = (
        '<script src="https://cdn.example.com/react.production.min.js"></script>'
        if _HAS_REACT[idx % len(_HAS_REACT)]
        else ""
    )
    ads = (
        '<script src="https://a.adsterra.com/tag.js" async></script>'
        if _HAS_ADS[idx % len(_HAS_ADS)]
        else ""
    )
    # Every second lead also exposes a security@ address.
    security = (
        f'<a href="mailto:security@{domain}">security</a>' if idx % 2 == 0 else ""
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <title>{name}</title>
  {gen_meta}
  <meta name="description" content="{name} is a public demo product for the LeadEngine MVP.">
  {react}
  {ads}
</head>
<body>
  <header><h1>{name}</h1></header>
  <p>{name} helps teams ship faster. Built by {name} Labs.</p>
  <footer>
    <a href="/about">About</a>
    <a href="/contact">Contact</a>
    <a href="mailto:support@{domain}">Email support</a>
    {security}
    <a href="https://github.com/{name.lower().replace(' ', '')}">GitHub</a>
    <a href="https://twitter.com/{name.lower().replace(' ', '')}">Twitter</a>
    <span>&copy; 2026 {name} Labs Ltd.</span>
  </footer>
</body>
</html>"""


@register
class ExampleSource(SourceAdapter):
    name = "example"

    def metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            name=self.name,
            categories=sorted(set(_CATEGORIES)),
            rate_limit=5.0,
            description="Deterministic offline mock source for demos and tests.",
        )

    async def discover(self, ctx: AdapterContext) -> AsyncIterator[RawHit]:
        count = int(ctx.setting("count", 60))
        for idx in range(count):
            name = f"Acme {idx:03d}"
            domain = f"acme-{idx:03d}.example"
            category = _CATEGORIES[idx % len(_CATEGORIES)]
            yield RawHit(
                source=self.name,
                url=f"https://{domain}",
                title=name,
                description=f"{name} — demo {category} product.",
                categories=[category],
                extra={"html": _html_for(idx, domain, name)},
            )

    async def health_check(self, ctx: AdapterContext) -> bool:
        return True
