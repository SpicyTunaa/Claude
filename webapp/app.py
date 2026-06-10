from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from webapp import db
from webapp.routes import domains, hunts, sse


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db(app.state.db_path)
    yield
    await db.close_db()


def create_app(db_path: str) -> FastAPI:
    app = FastAPI(title="Domain Hunter v2", lifespan=lifespan)
    app.state.db_path = db_path

    app.include_router(hunts.router, prefix="/api")
    app.include_router(domains.router, prefix="/api")
    app.include_router(sse.router, prefix="/api")

    static_dir = Path(__file__).parent / "static"
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app
