import logging

from telegram import Update
from telegram.ext import ContextTypes

from domain_hunter.config import load_config
from domain_hunter.exporter import to_csv
from domain_hunter.orchestrator import run_hunt
from domain_hunter.rate_limiter import RateLimiter

logger = logging.getLogger("domain_hunter.bot")
config = load_config()


def _authorized(update: Update) -> bool:
    if not config.TELEGRAM_ALLOWED_CHAT_IDS:
        return True
    return update.effective_chat.id in config.TELEGRAM_ALLOWED_CHAT_IDS


async def handle_hunt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        await update.message.reply_text("Unauthorized.")
        return

    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("Usage: /hunt <domain> <vertical>\nExample: /hunt example.com adtech")
        return

    seed_domain, vertical = args[0], args[1]
    progress = await update.message.reply_text(
        f"Starting hunt for *{seed_domain}* ({vertical})...\nThis may take 2–5 minutes.",
        parse_mode="Markdown",
    )

    try:
        result = await run_hunt(seed_domain, vertical, config, validate=True)
        csv_path = to_csv(result, config.OUTPUT_DIR)

        live = sum(1 for r in result.records if r.is_live)
        elapsed = (result.finished_at - result.started_at).total_seconds()
        sources = sorted({s for r in result.records for s in r.sources})

        summary = (
            f"Hunt complete for *{seed_domain}*\n"
            f"Domains found: {len(result.records)}\n"
            f"Live: {live}\n"
            f"Sources: {', '.join(sources)}\n"
            f"Elapsed: {elapsed:.0f}s"
        )

        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=progress.message_id,
            text=summary,
            parse_mode="Markdown",
        )

        with open(csv_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=csv_path.name,
                caption=f"Results for {seed_domain}",
            )

    except Exception as e:
        logger.error("Hunt failed for %s: %s", seed_domain, e)
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=progress.message_id,
            text=f"Hunt failed: {e}",
        )


async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        await update.message.reply_text("Unauthorized.")
        return

    rl = RateLimiter(config.HACKERTARGET_QUOTA_FILE)
    ht = rl.get_quota_status("hackertarget")
    remaining = (ht["limit"] or 0) - ht["used"]
    await update.message.reply_text(
        f"HackerTarget quota: {ht['used']}/{ht['limit']} used ({remaining} remaining) [{ht['date']}]"
    )


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "*Domain Hunter v2*\n\n"
        "/hunt <domain> <vertical> — discover related domains\n"
        "/status — check daily API quota\n"
        "/help — show this message",
        parse_mode="Markdown",
    )
