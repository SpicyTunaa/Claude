import asyncio
import json
from dataclasses import asdict
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from domain_hunter.models import ProgressEvent

router = APIRouter()

# hunt_id → list of subscriber queues
_subscribers: dict[str, list[asyncio.Queue]] = {}


async def publish(event: ProgressEvent) -> None:
    for q in _subscribers.get(event.hunt_id, []):
        await q.put(event)


async def publish_done(hunt_id: str) -> None:
    for q in _subscribers.get(hunt_id, []):
        await q.put(None)


async def _stream(hunt_id: str) -> AsyncGenerator[str, None]:
    q: asyncio.Queue = asyncio.Queue()
    _subscribers.setdefault(hunt_id, []).append(q)
    try:
        while True:
            try:
                event = await asyncio.wait_for(q.get(), timeout=25.0)
                if event is None:
                    yield "event: done\ndata: {}\n\n"
                    break
                yield f"event: progress\ndata: {json.dumps(asdict(event))}\n\n"
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
    finally:
        subs = _subscribers.get(hunt_id, [])
        if q in subs:
            subs.remove(q)
        if hunt_id in _subscribers and not _subscribers[hunt_id]:
            del _subscribers[hunt_id]


@router.get("/sse/{hunt_id}")
async def sse_endpoint(hunt_id: str):
    return StreamingResponse(
        _stream(hunt_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
