"""Command-line interface (Typer).

Commands: list-sources, adapter-health, run [--once], resume, export, init-db, version.
"""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .adapters import AdapterContext, available_adapters
from .core.config import load_settings
from .core.fetcher import Fetcher
from .core.logging import configure_logging, get_logger
from .core.pipeline import Pipeline
from .storage import repository
from .storage.db import init_db, make_engine, make_session_factory

app = typer.Typer(add_completion=False, help="Lead Discovery & Enrichment Engine (MVP).")
console = Console()
log = get_logger("cli")


@app.callback()
def _main(verbose: bool = typer.Option(False, "--verbose", "-v", help="Debug logging.")):
    configure_logging(level="DEBUG" if verbose else "INFO")


def _settings():
    return load_settings()


@app.command("version")
def version() -> None:
    """Print the engine version."""
    console.print(f"leadengine {__version__}")


@app.command("list-sources")
def list_sources() -> None:
    """List all registered discovery adapters and whether they are enabled in config."""
    settings = _settings()
    table = Table(title="Discovery sources")
    table.add_column("name")
    table.add_column("enabled")
    table.add_column("rate_limit")
    table.add_column("categories")
    table.add_column("description")
    for name, cls in available_adapters().items():
        meta = cls().metadata()
        cfg = settings.source(name)
        rate = cfg.rate_limit if cfg.rate_limit is not None else meta.rate_limit
        table.add_row(
            name,
            "yes" if cfg.enabled else "no",
            str(rate),
            ",".join(meta.categories),
            meta.description,
        )
    console.print(table)


@app.command("adapter-health")
def adapter_health() -> None:
    """Run each enabled adapter's health_check()."""
    settings = _settings()

    async def _run() -> list[tuple[str, bool]]:
        results: list[tuple[str, bool]] = []
        async with Fetcher(settings.fetcher) as fetcher:
            for name, cls in available_adapters().items():
                cfg = settings.source(name)
                if not cfg.enabled:
                    continue
                ctx = AdapterContext(fetcher=fetcher, config=cfg, log=get_logger(f"adapter.{name}"))
                try:
                    ok = await cls().health_check(ctx)
                except Exception as exc:  # noqa: BLE001
                    log.warning("health_check_error", source=name, error=str(exc))
                    ok = False
                results.append((name, ok))
        return results

    results = asyncio.run(_run())
    table = Table(title="Adapter health")
    table.add_column("name")
    table.add_column("healthy")
    for name, ok in results:
        table.add_row(name, "[green]ok[/green]" if ok else "[red]down[/red]")
    console.print(table)


@app.command("run")
def run(
    once: bool = typer.Option(True, "--once/--loop", help="Run a single pass (default)."),
    source: list[str] = typer.Option(None, "--source", "-s", help="Limit to these sources."),
) -> None:
    """Discover -> enrich -> contact -> fingerprint -> score -> export."""
    settings = _settings()
    pipeline = Pipeline(settings)
    stats = asyncio.run(pipeline.run(sources=source or None))
    _print_stats(stats)


@app.command("resume")
def resume() -> None:
    """Finish processing any not-yet-exported leads, then export."""
    settings = _settings()
    pipeline = Pipeline(settings)
    stats = asyncio.run(pipeline.resume())
    _print_stats(stats)


@app.command("export")
def export() -> None:
    """Re-export the current database to CSV/JSON without re-processing."""
    settings = _settings()
    engine = make_engine(settings.database.url)
    init_db(engine)
    Session = make_session_factory(engine)
    from . import export as export_layer

    with Session() as session:
        files = export_layer.export_all(
            session, settings.export.output_dir, settings.export.formats
        )
    for f in files:
        console.print(f"wrote {f}")


@app.command("init-db")
def init_db_cmd() -> None:
    """Create database tables."""
    settings = _settings()
    engine = make_engine(settings.database.url)
    init_db(engine)
    console.print(f"initialized {settings.database.url}")


@app.command("stats")
def stats_cmd() -> None:
    """Show counts from the local database."""
    settings = _settings()
    engine = make_engine(settings.database.url)
    init_db(engine)
    Session = make_session_factory(engine)
    with Session() as session:
        leads = repository.all_leads(session)
    total = len(leads)
    with_contact = sum(1 for r in leads if r.contacts)
    console.print(f"leads={total} with_contact={with_contact}")


def _print_stats(stats) -> None:
    table = Table(title="Run summary")
    table.add_column("metric")
    table.add_column("value", justify="right")
    table.add_row("discovered", str(stats.discovered))
    table.add_row("new_leads", str(stats.new_leads))
    table.add_row("duplicates", str(stats.duplicates))
    table.add_row("processed", str(stats.processed))
    table.add_row("with_contact", str(stats.with_contact))
    table.add_row("exported", str(stats.exported))
    console.print(table)
    for f in stats.files:
        console.print(f"wrote {f}")


if __name__ == "__main__":
    app()
