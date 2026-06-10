from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException

from domain_hunter.config import load_config
from domain_hunter.models import ProgressEvent
from domain_hunter.orchestrator import run_hunt
from webapp import db
from webapp.models import NewHuntRequest
from webapp.routes.sse import publish, publish_done

router = APIRouter()
_config = load_config()


async def _run_hunt_task(hunt_id: str, seed_domain: str, vertical: str, validate: bool) -> None:
    try:
        result = await run_hunt(
            seed_domain=seed_domain,
            vertical=vertical,
            config=_config,
            validate=validate,
            hunt_id=hunt_id,
            progress_callback=publish,
        )
        await db.insert_domains(hunt_id, result.records)
        live = sum(1 for r in result.records if r.is_live)
        all_sources = sorted({s for r in result.records for s in r.sources})
        await db.update_hunt_status(
            hunt_id, "complete",
            total=len(result.records), live=live,
            sources="|".join(all_sources),
            finished_at=result.finished_at or datetime.utcnow(),
        )
        await publish(ProgressEvent(
            hunt_id=hunt_id, event="complete",
            total_so_far=len(result.records),
            message=f"{len(result.records)} domains, {live} live",
        ))
    except Exception as e:
        await db.update_hunt_status(hunt_id, "failed", error=str(e))
        await publish(ProgressEvent(hunt_id=hunt_id, event="error", message=str(e)))
    finally:
        await publish_done(hunt_id)


@router.get("/hunts")
async def list_hunts(limit: int = 20, offset: int = 0):
    rows = await db.get_hunts(limit=min(limit, 100), offset=offset)
    return {"items": rows, "limit": limit, "offset": offset}


@router.post("/hunts", status_code=202)
async def create_hunt(body: NewHuntRequest, background_tasks: BackgroundTasks):
    hunt_id = str(uuid4())
    await db.insert_hunt(hunt_id, body.seed_domain, body.vertical, datetime.utcnow())
    background_tasks.add_task(_run_hunt_task, hunt_id, body.seed_domain, body.vertical, body.validate_domains)
    return {"hunt_id": hunt_id, "status": "running"}


@router.get("/hunts/{hunt_id}")
async def get_hunt(hunt_id: str):
    row = await db.get_hunt(hunt_id)
    if not row:
        raise HTTPException(404, "Hunt not found")
    return row


@router.delete("/hunts/{hunt_id}", status_code=204)
async def delete_hunt(hunt_id: str):
    if not await db.get_hunt(hunt_id):
        raise HTTPException(404, "Hunt not found")
    await db.delete_hunt(hunt_id)


@router.get("/stats")
async def global_stats():
    return await db.get_global_stats()
