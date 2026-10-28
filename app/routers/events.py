from fastapi import APIRouter, Depends, Header, Query, Response
from fastapi import status as http
from pydantic import AwareDatetime
from app.core.errors import AppError
from app.db.client import get_db
from app.models.common import ObjectIdStr, Page
from app.models.event import EventCreate, EventRead, EventStatus, EventUpdate
from app.repositories.event_repo import EventRepository
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["events"])


def get_event_service() -> EventService:
    return EventService(EventRepository(get_db()))


def if_match_version(if_match: str | None = Header(default=None)) -> int:
    if if_match is None:
        raise AppError(428, "PRECONDITION_REQUIRED", "If-Match header with the event version is required")
    try:
        return int(if_match.strip().strip('"'))
    except ValueError:
        raise AppError(422, "INVALID_IF_MATCH", "If-Match must be the integer event version")


@router.post("", response_model=EventRead, status_code=http.HTTP_201_CREATED)
async def create_event(body: EventCreate, svc: EventService = Depends(get_event_service)):
    return await svc.create(body)


@router.get("", response_model=Page[EventRead])
async def list_events(
    city: str | None = None,
    status: EventStatus | None = None,
    starts_from: AwareDatetime | None = None,
    starts_to: AwareDatetime | None = None,
    q: str | None = Query(default=None, min_length=2, max_length=100),
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = None,
    svc: EventService = Depends(get_event_service),
):
    return await svc.list_page(city=city, status=status, starts_from=starts_from,
                               starts_to=starts_to, q=q, limit=limit, cursor=cursor)


@router.get("/{event_id}", response_model=EventRead)
async def get_event(event_id: ObjectIdStr, response: Response,
                    svc: EventService = Depends(get_event_service)):
    event = await svc.get(event_id)
    response.headers["ETag"] = f'"{event.version}"'  # client echoes this back in If-Match
    return event


@router.patch("/{event_id}", response_model=EventRead)
async def update_event(event_id: ObjectIdStr, body: EventUpdate,
                       version: int = Depends(if_match_version),
                       svc: EventService = Depends(get_event_service)):
    return await svc.update(event_id, version, body)


@router.delete("/{event_id}", status_code=http.HTTP_204_NO_CONTENT)
async def delete_event(event_id: ObjectIdStr, svc: EventService = Depends(get_event_service)):
    await svc.delete(event_id)


@router.post("/{event_id}/publish", response_model=EventRead)
async def publish_event(event_id: ObjectIdStr, svc: EventService = Depends(get_event_service)):
    return await svc.publish(event_id)


@router.post("/{event_id}/complete", response_model=EventRead)
async def complete_event(event_id: ObjectIdStr, svc: EventService = Depends(get_event_service)):
    return await svc.complete(event_id)


@router.post("/{event_id}/cancel", response_model=EventRead)
async def cancel_event(event_id: ObjectIdStr, svc: EventService = Depends(get_event_service)):
    return await svc.cancel(event_id)