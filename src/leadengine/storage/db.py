"""Database engine / session management (synchronous SQLAlchemy over SQLite).

DB writes are fast local operations, so the storage layer is synchronous while network
I/O stays async. This keeps the data flow simple and deterministic.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .schema import Base


def _ensure_sqlite_dir(url: str) -> None:
    prefix = "sqlite"
    if not url.startswith(prefix):
        return
    # e.g. sqlite+pysqlite:///data/leadengine.db -> path "data/leadengine.db"
    _, _, path_part = url.partition(":///")
    if path_part and path_part != ":memory:":
        Path(path_part).parent.mkdir(parents=True, exist_ok=True)


def make_engine(url: str) -> Engine:
    _ensure_sqlite_dir(url)
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, future=True, connect_args=connect_args)


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)
