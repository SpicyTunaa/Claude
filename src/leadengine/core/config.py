"""Configuration loading.

Config is YAML-first (``config/config.yaml``) with environment-variable overrides via
``pydantic-settings`` (prefix ``LEADENGINE_``, nested keys joined by ``__``). Keeping all
tunables here means sources can be enabled/disabled and rate-limited without touching code.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _project_root() -> Path:
    # src/leadengine/core/config.py -> project root is three parents up from this file's dir.
    return Path(__file__).resolve().parents[3]


def _config_dir() -> Path:
    override = os.environ.get("LEADENGINE_CONFIG_DIR")
    if override:
        return Path(override)
    return _project_root() / "config"


class DatabaseConfig(BaseModel):
    url: str = "sqlite+pysqlite:///data/leadengine.db"


class FetcherConfig(BaseModel):
    timeout: float = 15.0
    max_retries: int = 3
    default_rate_limit: float = 1.0
    respect_robots: bool = True
    user_agents: list[str] = Field(
        default_factory=lambda: ["Mozilla/5.0 (compatible; LeadEngineBot/0.1)"]
    )


class EnrichmentConfig(BaseModel):
    enabled: bool = True
    ttl_hours: int = 168


class MonetizationConfig(BaseModel):
    enabled: bool = True
    affect_score: bool = False
    score_adjustments: dict[str, int] = Field(default_factory=dict)


class ExportConfig(BaseModel):
    output_dir: str = "output"
    formats: list[str] = Field(default_factory=lambda: ["csv", "json"])


class SourceConfig(BaseModel):
    enabled: bool = True
    rate_limit: float | None = None
    # Adapter-specific extras are tolerated (e.g. max_items).
    model_config = SettingsConfigDict(extra="allow")


class Settings(BaseSettings):
    """Top-level settings, merged from YAML defaults then environment overrides."""

    model_config = SettingsConfigDict(
        env_prefix="LEADENGINE_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    fetcher: FetcherConfig = Field(default_factory=FetcherConfig)
    enrichment: EnrichmentConfig = Field(default_factory=EnrichmentConfig)
    monetization: MonetizationConfig = Field(default_factory=MonetizationConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)
    sources: dict[str, SourceConfig] = Field(default_factory=dict)

    # Loaded auxiliary config (not env-overridable; file-driven).
    categories: list[dict[str, Any]] = Field(default_factory=list)
    scoring: dict[str, Any] = Field(default_factory=dict)

    def source(self, name: str) -> SourceConfig:
        return self.sources.get(name, SourceConfig())

    def category_slugs(self) -> set[str]:
        return {c["slug"] for c in self.categories if "slug" in c}


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_settings(config_dir: Path | None = None) -> Settings:
    """Load YAML config, then let environment variables override scalar fields."""
    cfg_dir = config_dir or _config_dir()
    base = _read_yaml(cfg_dir / "config.yaml")
    base["categories"] = _read_yaml(cfg_dir / "categories.yaml").get("categories", [])
    base["scoring"] = _read_yaml(cfg_dir / "scoring.yaml")
    # Pydantic-settings applies env overrides on top of these initialization values.
    return Settings(**base)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings()


def reset_settings_cache() -> None:
    """Used by tests that load alternative config directories."""
    get_settings.cache_clear()
