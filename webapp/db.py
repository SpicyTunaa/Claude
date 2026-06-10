import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import Any

from domain_hunter.models import DomainRecord

_db: aiosqlite.Connection | None = None

SCHEMA = [
    """CREATE TABLE IF NOT EXISTS hunts (
        id          TEXT PRIMARY KEY,
        seed_domain TEXT NOT NULL,
        vertical    TEXT NOT NULL,
        status      TEXT NOT NULL DEFAULT 'running',
        total       INTEGER DEFAULT 0,
        live        INTEGER DEFAULT 0,
        sources     TEXT DEFAULT '',
        error       TEXT,
        started_at  TEXT NOT NULL,
        finished_at TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS domains (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        hunt_id          TEXT NOT NULL REFERENCES hunts(id) ON DELETE CASCADE,
        domain           TEXT NOT NULL,
        root_domain      TEXT NOT NULL DEFAULT '',
        is_subdomain     INTEGER NOT NULL DEFAULT 0,
        sources          TEXT NOT NULL DEFAULT '',
        confidence_score REAL NOT NULL DEFAULT 0.0,
        is_live          INTEGER,
        status_code      INTEGER,
        final_url        TEXT,
        discovered_at    TEXT NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS idx_domains_hunt_id ON domains(hunt_id)",
    "CREATE INDEX IF NOT EXISTS idx_domains_domain ON domains(domain)",
    "CREATE INDEX IF NOT EXISTS idx_hunts_started ON hunts(started_at)",
]


async def init_db(path: str) -> None:
    global _db
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    _db = await aiosqlite.connect(path)
    _db.row_factory = aiosqlite.Row
    await _db.execute("PRAGMA journal_mode=WAL")
    await _db.execute("PRAGMA foreign_keys=ON")
    for stmt in SCHEMA:
        await _db.execute(stmt)
    await _db.commit()


async def close_db() -> None:
    if _db:
        await _db.close()


async def insert_hunt(hunt_id: str, seed_domain: str, vertical: str, started_at: datetime) -> None:
    await _db.execute(
        "INSERT INTO hunts (id, seed_domain, vertical, status, started_at) VALUES (?,?,?,'running',?)",
        (hunt_id, seed_domain, vertical, started_at.isoformat()),
    )
    await _db.commit()


async def update_hunt_status(
    hunt_id: str,
    status: str,
    total: int = 0,
    live: int = 0,
    sources: str = "",
    finished_at: datetime | None = None,
    error: str | None = None,
) -> None:
    await _db.execute(
        "UPDATE hunts SET status=?,total=?,live=?,sources=?,finished_at=?,error=? WHERE id=?",
        (status, total, live, sources, finished_at.isoformat() if finished_at else None, error, hunt_id),
    )
    await _db.commit()


async def insert_domains(hunt_id: str, records: list[DomainRecord]) -> None:
    rows = [
        (
            hunt_id, r.domain, r.root_domain, int(r.is_subdomain),
            "|".join(sorted(r.sources)), r.confidence_score,
            int(r.is_live) if r.is_live is not None else None,
            r.status_code, r.final_url, r.discovered_at.isoformat(),
        )
        for r in records
    ]
    await _db.executemany(
        """INSERT INTO domains
           (hunt_id,domain,root_domain,is_subdomain,sources,confidence_score,
            is_live,status_code,final_url,discovered_at)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )
    await _db.commit()


async def get_hunts(limit: int = 20, offset: int = 0) -> list[dict]:
    async with _db.execute(
        "SELECT * FROM hunts ORDER BY started_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ) as cur:
        return [dict(r) for r in await cur.fetchall()]


async def get_hunt(hunt_id: str) -> dict | None:
    async with _db.execute("SELECT * FROM hunts WHERE id=?", (hunt_id,)) as cur:
        row = await cur.fetchone()
    return dict(row) if row else None


async def get_domains(
    hunt_id: str,
    search: str = "",
    live_only: bool = False,
    sort: str = "confidence_score",
    order: str = "desc",
    limit: int = 50,
    offset: int = 0,
) -> tuple[int, list[dict]]:
    SAFE_SORT = {"confidence_score", "domain", "status_code", "is_live"}
    safe_sort = sort if sort in SAFE_SORT else "confidence_score"
    safe_order = "DESC" if order.lower() == "desc" else "ASC"

    conds: list[str] = ["hunt_id = ?"]
    params: list[Any] = [hunt_id]
    if search:
        conds.append("domain LIKE ?")
        params.append(f"%{search}%")
    if live_only:
        conds.append("is_live = 1")
    where = " AND ".join(conds)

    async with _db.execute(f"SELECT COUNT(*) FROM domains WHERE {where}", params) as cur:
        total = (await cur.fetchone())[0]

    async with _db.execute(
        f"SELECT * FROM domains WHERE {where} ORDER BY {safe_sort} {safe_order} LIMIT ? OFFSET ?",
        params + [limit, offset],
    ) as cur:
        rows = [dict(r) for r in await cur.fetchall()]

    return total, rows


async def delete_hunt(hunt_id: str) -> None:
    await _db.execute("DELETE FROM hunts WHERE id=?", (hunt_id,))
    await _db.commit()


async def get_global_stats() -> dict:
    async with _db.execute(
        "SELECT COUNT(*) as hunts, COALESCE(SUM(total),0) as domains, COALESCE(SUM(live),0) as live "
        "FROM hunts WHERE status='complete'"
    ) as cur:
        row = await cur.fetchone()
    return dict(row) if row else {"hunts": 0, "domains": 0, "live": 0}
