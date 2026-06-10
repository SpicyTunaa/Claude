"""
Unified entry point: runs the Telegram bot and FastAPI web server concurrently
on the same asyncio event loop using asyncio.TaskGroup.

Usage:
    python main.py
    DB_PATH=./data/dh.db WEB_PORT=8080 WEBAPP_URL=https://your.ngrok.io python main.py
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path

import uvicorn

from bot.telegram_bot import build_app
from domain_hunter.config import load_config
from domain_hunter.utils.logger import setup_logger
from webapp.app import create_app


async def _run_bot(bot_app, stop_event: asyncio.Event) -> None:
    """Run PTB bot until stop_event is set."""
    async with bot_app:
        await bot_app.start()
        await bot_app.updater.start_polling(drop_pending_updates=True)
        logging.getLogger("domain_hunter.bot").info("Bot polling started")
        await stop_event.wait()
        await bot_app.updater.stop()
        await bot_app.stop()


async def _run_web(web_app, config, stop_event: asyncio.Event) -> None:
    """Run uvicorn on the current event loop until stop_event is set."""
    cfg = uvicorn.Config(
        web_app,
        host="0.0.0.0",
        port=config.WEB_PORT,
        loop="none",          # reuse the running asyncio event loop
        log_level="warning",
    )
    server = uvicorn.Server(cfg)
    # Disable uvicorn's own signal handlers so our TaskGroup owns shutdown
    server.install_signal_handlers = lambda: None

    serve_task = asyncio.create_task(server.serve())
    await stop_event.wait()
    server.should_exit = True
    await serve_task


async def main() -> None:
    config = load_config()
    setup_logger("domain_hunter", config.LOG_LEVEL, config.LOG_FILE)
    logger = logging.getLogger("domain_hunter")

    db_dir = Path(config.DB_PATH).parent
    db_dir.mkdir(parents=True, exist_ok=True)

    web_app = create_app(db_path=config.DB_PATH)
    bot_app = build_app(config)

    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    logger.info(
        "Starting Domain Hunter v2 — web on :%d  webapp_url=%s",
        config.WEB_PORT,
        config.WEBAPP_URL,
    )

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(_run_web(web_app, config, stop_event))
            tg.create_task(_run_bot(bot_app, stop_event))
    except* Exception as eg:
        for exc in eg.exceptions:
            logger.error("Fatal error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
