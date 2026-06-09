import logging

from telegram.ext import Application, CommandHandler

from bot.handlers import handle_help, handle_hunt, handle_status
from domain_hunter.config import load_config
from domain_hunter.utils.logger import setup_logger

logger = logging.getLogger("domain_hunter.bot")


def main() -> None:
    config = load_config()
    setup_logger("domain_hunter", config.LOG_LEVEL, config.LOG_FILE)

    if not config.TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set in .env")

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("hunt", handle_hunt))
    app.add_handler(CommandHandler("status", handle_status))
    app.add_handler(CommandHandler("help", handle_help))
    app.add_handler(CommandHandler("start", handle_help))

    logger.info("Telegram bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
