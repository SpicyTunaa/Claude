from fastapi import APIRouter, HTTPException
from webapp import db

router = APIRouter()


@router.get("/hunts/{hunt_id}/domains")
async def list_domains(
    hunt_id: str,
    search: str = "",
    live: str = "",
    sort: str = "confidence_score",
    order: str = "desc",
    limit: int = 50,
    offset: int = 0,
    exclude_source: str = "",
):
    if not await db.get_hunt(hunt_id):
        raise HTTPException(404, "Hunt not found")

    live_only = live.lower() == "true"
    total, rows = await db.get_domains(
        hunt_id=hunt_id,
        search=search,
        live_only=live_only,
        sort=sort,
        order=order,
        limit=min(limit, 200),
        offset=offset,
        exclude_source=exclude_source,
    )
    return {"hunt_id": hunt_id, "total": total, "items": rows}
