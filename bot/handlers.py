import asyncio
import logging
import uuid
from datetime import datetime, timezone

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import ContextTypes

from domain_hunter.config import Config
from domain_hunter.exporter import to_csv
from domain_hunter.orchestrator import run_hunt
from domain_hunter.rate_limiter import RateLimiter
from webapp import db
from webapp.routes.sse import publish, publish_done

logger = logging.getLogger("domain_hunter.bot")


def _config(context: ContextTypes.DEFAULT_TYPE) -> Config:
    return context.application.bot_data["config"]


def _authorized(update: Update, config: Config) -> bool:
    if not config.TELEGRAM_ALLOWED_CHAT_IDS:
        return True
    return update.effective_chat.id in config.TELEGRAM_ALLOWED_CHAT_IDS


async def handle_hunt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config = _config(context)
    if not _authorized(update, config):
        await update.message.reply_text("Unauthorized.")
        return

    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: /hunt <domain> <vertical>\nExample: /hunt example.com adtech"
        )
        return

    seed_domain = args[0].lower().strip().strip("<>")
    vertical = args[1].lower().strip().strip("<>")
    hunt_id = str(uuid.uuid4())

    await db.insert_hunt(
        hunt_id=hunt_id,
        seed_domain=seed_domain,
        vertical=vertical,
        started_at=datetime.now(timezone.utc),
    )

    progress_msg = await update.message.reply_text(
        f"Starting hunt for {seed_domain} ({vertical})...\n"
        f"Hunt ID: {hunt_id[:8]}\nThis may take 2-5 minutes.",
    )

    asyncio.create_task(
        _run_and_notify(
            update=update,
            context=context,
            config=config,
            hunt_id=hunt_id,
            seed_domain=seed_domain,
            vertical=vertical,
            progress_msg_id=progress_msg.message_id,
        )
    )


async def _run_and_notify(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    config: Config,
    hunt_id: str,
    seed_domain: str,
    vertical: str,
    progress_msg_id: int,
) -> None:
    chat_id = update.effective_chat.id
    try:
        result = await run_hunt(
            seed_domain=seed_domain,
            vertical=vertical,
            config=config,
            validate=True,
            hunt_id=hunt_id,
            progress_callback=publish,
        )

        await db.insert_domains(hunt_id, result.records)
        live = sum(1 for r in result.records if r.is_live)
        elapsed = (result.finished_at - result.started_at).total_seconds()
        sources = sorted({s for r in result.records for s in r.sources})

        await db.update_hunt_status(
            hunt_id=hunt_id,
            status="complete",
            total=len(result.records),
            live=live,
            sources=",".join(sources),
            finished_at=result.finished_at,
        )

        csv_path = to_csv(result, config.OUTPUT_DIR)

        webapp_url = f"{config.WEBAPP_URL}?hunt={hunt_id}"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                text="Open Dashboard",
                web_app=WebAppInfo(url=webapp_url),
            )
        ]])

        summary = (
            f"Hunt complete for {seed_domain}\n"
            f"Domains: {len(result.records)} | Live: {live}\n"
            f"Sources: {', '.join(sources)}\n"
            f"Elapsed: {elapsed:.0f}s"
        )

        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_msg_id,
            text=summary,
            reply_markup=keyboard,
        )

        with open(csv_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=csv_path.name,
                caption=f"Results for {seed_domain}",
            )

    except Exception as e:
        logger.exception("Hunt %s failed: %s", hunt_id, e)
        await db.update_hunt_status(
            hunt_id=hunt_id,
            status="failed",
            error=str(e),
            finished_at=datetime.now(timezone.utc),
        )
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_msg_id,
            text=f"Hunt failed: {e}",
        )
    finally:
        await publish_done(hunt_id)


async def handle_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config = _config(context)
    if not _authorized(update, config):
        await update.message.reply_text("Unauthorized.")
        return

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="Open Domain Hunter Dashboard",
            web_app=WebAppInfo(url=config.WEBAPP_URL),
        )
    ]])
    await update.message.reply_text(
        "Open the Domain Hunter dashboard:",
        reply_markup=keyboard,
    )


async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config = _config(context)
    if not _authorized(update, config):
        await update.message.reply_text("Unauthorized.")
        return

    rl = RateLimiter(config.HACKERTARGET_QUOTA_FILE)
    ht = rl.get_quota_status("hackertarget")
    remaining = (ht["limit"] or 0) - ht["used"]
    await update.message.reply_text(
        f"HackerTarget quota: {ht['used']}/{ht['limit']} used "
        f"({remaining} remaining) [{ht['date']}]"
    )


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Domain Hunter v2\n\n"
        "/hunt <domain> <vertical> — discover related domains\n"
        "/dashboard — open the web dashboard\n"
        "/status — check daily API quota\n"
        "/help — show this message",
    )
