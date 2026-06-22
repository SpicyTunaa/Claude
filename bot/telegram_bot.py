import logging

from telegram.ext import Application, CommandHandler

from bot.handlers import handle_dashboard, handle_help, handle_hunt, handle_status
from domain_hunter.config import Config

logger = logging.getLogger("domain_hunter.bot")


def build_app(config: Config) -> Application:
    """Build and return the PTB Application without starting the event loop."""
    if not config.TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set in .env")

    app = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .build()
    )
    app.bot_data["config"] = config

    app.add_handler(CommandHandler("hunt", handle_hunt))
    app.add_handler(CommandHandler("status", handle_status))
    app.add_handler(CommandHandler("dashboard", handle_dashboard))
    app.add_handler(CommandHandler("help", handle_help))
    app.add_handler(CommandHandler("start", handle_help))

    logger.info("Telegram bot handlers registered")
    return app
