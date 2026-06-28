"""Adapter registry + auto-discovery.

Adapters self-register with ``@register``. Importing this package imports every module in
``sources/`` so dropping a new file there is enough for it to appear — zero core edits.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import TYPE_CHECKING

from .base import AdapterContext, SourceAdapter

if TYPE_CHECKING:
    from collections.abc import Iterable

_REGISTRY: dict[str, type[SourceAdapter]] = {}


def register(cls: type[SourceAdapter]) -> type[SourceAdapter]:
    """Class decorator that registers a source adapter by its ``name``."""
    if not getattr(cls, "name", ""):
        raise ValueError(f"{cls.__name__} must define a non-empty 'name'")
    if cls.name in _REGISTRY and _REGISTRY[cls.name] is not cls:
        raise ValueError(f"Duplicate adapter name: {cls.name!r}")
    _REGISTRY[cls.name] = cls
    return cls


def _load_sources() -> None:
    from . import sources

    for mod in pkgutil.iter_modules(sources.__path__):
        importlib.import_module(f"{sources.__name__}.{mod.name}")


def available_adapters() -> dict[str, type[SourceAdapter]]:
    """All registered adapter classes, keyed by name (sorted for determinism)."""
    _load_sources()
    return dict(sorted(_REGISTRY.items()))


def get_adapter(name: str) -> type[SourceAdapter]:
    _load_sources()
    return _REGISTRY[name]


def iter_enabled(enabled_names: Iterable[str]) -> list[SourceAdapter]:
    """Instantiate adapters whose names are in ``enabled_names`` (sorted)."""
    adapters = available_adapters()
    return [adapters[n]() for n in sorted(enabled_names) if n in adapters]


__all__ = [
    "AdapterContext",
    "SourceAdapter",
    "available_adapters",
    "get_adapter",
    "iter_enabled",
    "register",
]
