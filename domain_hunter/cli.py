import asyncio
import csv as csv_module
from datetime import datetime
from pathlib import Path

import click

from domain_hunter.config import load_config
from domain_hunter.exporter import to_csv
from domain_hunter.models import DomainRecord, HuntResult
from domain_hunter.orchestrator import run_hunt
from domain_hunter.utils.logger import setup_logger


@click.group()
def cli():
    """Domain Hunter v2 — automated domain discovery using free sources."""


@cli.command()
@click.argument("domain")
@click.argument("vertical")
@click.option("--output", "-o", default="./output", show_default=True)
@click.option("--no-validate", is_flag=True, help="Skip HTTP validation")
@click.option("--no-cache", is_flag=True, help="Ignore cached results")
@click.option("--verbose", "-v", is_flag=True)
def hunt(domain: str, vertical: str, output: str, no_validate: bool, no_cache: bool, verbose: bool):
    """Discover domains related to DOMAIN in VERTICAL."""
    config = load_config()
    if verbose:
        config.LOG_LEVEL = "DEBUG"
    if no_cache:
        config.USE_CACHE = False
    setup_logger("domain_hunter", config.LOG_LEVEL, config.LOG_FILE)

    result = asyncio.run(run_hunt(domain, vertical, config, validate=not no_validate))
    csv_path = to_csv(result, Path(output))
    elapsed = (result.finished_at - result.started_at).total_seconds()
    live = sum(1 for r in result.records if r.is_live)

    click.echo(f"\nHunt complete for {domain} ({vertical})")
    click.echo(f"  Domains found : {len(result.records)}")
    if not no_validate:
        click.echo(f"  Live domains  : {live}")
    click.echo(f"  Elapsed       : {elapsed:.1f}s")
    click.echo(f"  Output        : {csv_path}")


@cli.command("hunt-many")
@click.argument("seeds_file", type=click.Path(exists=True))
@click.option("--output", "-o", default="./output", show_default=True)
@click.option("--no-validate", is_flag=True)
@click.option("--no-cache", is_flag=True)
@click.option("--verbose", "-v", is_flag=True)
def hunt_many(seeds_file: str, output: str, no_validate: bool, no_cache: bool, verbose: bool):
    """Run hunts for all seeds in SEEDS_FILE (domain,vertical per line).

    Runs sequentially to share HackerTarget daily quota across seeds.
    """
    config = load_config()
    if verbose:
        config.LOG_LEVEL = "DEBUG"
    if no_cache:
        config.USE_CACHE = False
    setup_logger("domain_hunter", config.LOG_LEVEL, config.LOG_FILE)

    seeds = _parse_seeds(Path(seeds_file))
    if not seeds:
        click.echo("No valid seeds found.", err=True)
        raise SystemExit(1)

    out_dir = Path(output)
    total = len(seeds)
    click.echo(f"Running {total} hunts sequentially...")

    for i, (domain, vertical) in enumerate(seeds, 1):
        click.echo(f"\n[{i}/{total}] {domain} ({vertical})")
        try:
            result = asyncio.run(run_hunt(domain, vertical, config, validate=not no_validate))
            csv_path = to_csv(result, out_dir)
            live = sum(1 for r in result.records if r.is_live)
            click.echo(f"  → {len(result.records)} domains ({live} live) → {csv_path.name}")
        except Exception as e:
            click.echo(f"  ✗ Failed: {e}", err=True)

    click.echo(f"\nAll {total} hunts complete. Output: {out_dir}")


@cli.command()
@click.argument("csv_file", type=click.Path(exists=True))
@click.option("--output", "-o", default=None)
def validate(csv_file: str, output: str | None):
    """Re-validate an existing CSV and write updated results."""
    import aiohttp
    from domain_hunter.validators import http_validator

    config = load_config()
    setup_logger("domain_hunter", config.LOG_LEVEL, config.LOG_FILE)

    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv_module.DictReader(f)
        records = [
            DomainRecord(
                domain=row["domain"],
                sources=set(row.get("sources", "").split("|")) if row.get("sources") else set(),
            )
            for row in reader
        ]

    async def _run():
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            return await http_validator.validate_all(records, session, config)

    validated = asyncio.run(_run())
    live = sum(1 for r in validated if r.is_live)

    out_dir = Path(output) if output else Path(csv_file).parent
    result = HuntResult("revalidated", "revalidated", validated, datetime.utcnow(), datetime.utcnow())
    out_path = to_csv(result, out_dir)

    click.echo(f"Validated {len(validated)} domains — {live} live")
    click.echo(f"Saved: {out_path}")


def _parse_seeds(path: Path) -> list[tuple[str, str]]:
    seeds = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(",", 1)
        if len(parts) == 2:
            seeds.append((parts[0].strip(), parts[1].strip()))
    return seeds


if __name__ == "__main__":
    cli()
