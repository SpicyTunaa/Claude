#!/usr/bin/env python3
"""Daily cron runner. Reads seeds from a file and runs domain_hunter for each."""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from domain_hunter.config import load_config
from domain_hunter.exporter import to_csv
from domain_hunter.orchestrator import run_hunt
from domain_hunter.utils.logger import setup_logger


def parse_seeds(seeds_file: Path) -> list[tuple[str, str]]:
    seeds = []
    for line in seeds_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(",", 1)
        if len(parts) == 2:
            seeds.append((parts[0].strip(), parts[1].strip()))
        else:
            logging.warning("Skipping invalid seeds line: %s", line)
    return seeds


def notify_telegram(csv_path: Path, seed_domain: str, record_count: int, config) -> None:
    if not (config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID):
        return
    try:
        import asyncio as _asyncio
        from telegram import Bot

        async def _send():
            bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
            await bot.send_message(
                chat_id=config.TELEGRAM_CHAT_ID,
                text=f"Daily hunt complete for *{seed_domain}*: {record_count} domains found.",
                parse_mode="Markdown",
            )
            with open(csv_path, "rb") as f:
                await bot.send_document(
                    chat_id=config.TELEGRAM_CHAT_ID,
                    document=f,
                    filename=csv_path.name,
                )

        _asyncio.run(_send())
    except Exception as e:
        logging.error("Telegram notification failed: %s", e)


def main() -> None:
    parser = argparse.ArgumentParser(description="Domain Hunter daily cron runner")
    parser.add_argument("--seeds-file", required=True, help="Path to seeds.txt (domain,vertical per line)")
    parser.add_argument("--output-dir", default="./output", help="Directory for CSV output")
    parser.add_argument("--no-validate", action="store_true", help="Skip HTTP validation")
    parser.add_argument("--notify-telegram", action="store_true", help="Send results via Telegram")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    config = load_config()
    if args.verbose:
        config.LOG_LEVEL = "DEBUG"
    setup_logger("domain_hunter", config.LOG_LEVEL, config.LOG_FILE)

    seeds = parse_seeds(Path(args.seeds_file))
    if not seeds:
        logging.error("No valid seeds found in %s", args.seeds_file)
        sys.exit(1)

    output_dir = Path(args.output_dir)
    logging.info("Starting daily hunt: %d seeds", len(seeds))

    for seed_domain, vertical in seeds:
        logging.info("Hunting: %s (%s)", seed_domain, vertical)
        try:
            result = asyncio.run(
                run_hunt(seed_domain, vertical, config, validate=not args.no_validate)
            )
            csv_path = to_csv(result, output_dir)
            logging.info("Saved: %s (%d domains)", csv_path, len(result.records))

            if args.notify_telegram:
                notify_telegram(csv_path, seed_domain, len(result.records), config)
        except Exception as e:
            logging.error("Hunt failed for %s: %s", seed_domain, e)

    logging.info("Daily hunt complete")


if __name__ == "__main__":
    main()
