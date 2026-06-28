"""Plugin SDK: the common interface every discovery source implements.

A source adapter is self-contained. It receives an :class:`AdapterContext` (shared fetcher,
its own config slice, a logger) and never imports the pipeline, storage or other adapters.
Adding a source means dropping one file in ``adapters/sources/`` — no core changes.
"""

from __future__ import annotations

import abc
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from ..core.config import SourceConfig
from ..core.fetcher import Fetcher
from ..core.logging import get_logger
from ..core.models import AdapterMetadata, FieldValue, Lead, RawHit


@dataclass
class AdapterContext:
    fetcher: Fetcher
    config: SourceConfig
    log: Any

    def setting(self, key: str, default: Any = None) -> Any:
        """Read an adapter-specific config value (extras are allowed on SourceConfig)."""
        if hasattr(self.config, key):
            return getattr(self.config, key)
        extra = getattr(self.config, "model_extra", None) or {}
        return extra.get(key, default)


class SourceAdapter(abc.ABC):
    """Base class for all discovery sources."""

    #: Unique adapter slug; must match the key used in ``config/config.yaml`` ``sources``.
    name: str = ""

    @abc.abstractmethod
    def metadata(self) -> AdapterMetadata:
        """Static descriptor (name, categories, rate limit) for listing and health."""

    @abc.abstractmethod
    async def discover(self, ctx: AdapterContext) -> AsyncIterator[RawHit]:
        """Yield raw discovery hits from public listings."""
        raise NotImplementedError
        yield  # pragma: no cover — marks this as an async generator

    async def enrich(self, ctx: AdapterContext, lead: Lead) -> list[FieldValue]:
        """Optional source-specific enrichment. Default: nothing extra."""
        return []

    async def health_check(self, ctx: AdapterContext) -> bool:
        """Lightweight liveness probe. Default: True (overridden by real sources)."""
        return True

    def make_logger(self):
        return get_logger(f"adapter.{self.name or self.__class__.__name__}")
