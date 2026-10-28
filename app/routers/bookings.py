from fastapi import APIRouter, Depends, Query
from fastapi import status as http
from app.db.client import get_db
from app.models.booking import BookingCreate, BookingRead, BookingStatus, BookingUpdate
from app.models.common import ObjectIdStr, Page
from app.repositories.booking_repo import BookingRepository
from app.repositories.event_repo import EventRepository
from app.repositories.user_repo import UserRepository
from app.services.booking_service import Actor, BookingService

router = APIRouter(prefix="/bookings", tags=["bookings"])


def get_booking_service() -> BookingService:
    db = get_db()
    return BookingService(BookingRepository(db), EventRepository(db), UserRepository(db))


@router.post("", response_model=BookingRead, status_code=http.HTTP_201_CREATED)
async def create_booking(body: BookingCreate, svc: BookingService = Depends(get_booking_service)):
    return await svc.create(body)


@router.get("", response_model=Page[BookingRead])
async def list_bookings(event_id: ObjectIdStr | None = None, user_id: ObjectIdStr | None = None,
                        status: BookingStatus | None = None,
                        limit: int = Query(20, ge=1, le=100), cursor: ObjectIdStr | None = None,
                        svc: BookingService = Depends(get_booking_service)):
    return await svc.list_page(event_id=event_id, user_id=user_id, status=status,
                               limit=limit, cursor=cursor)


@router.get("/{booking_id}", response_model=BookingRead)
async def get_booking(booking_id: ObjectIdStr, svc: BookingService = Depends(get_booking_service)):
    return await svc.get(booking_id)


@router.patch("/{booking_id}", response_model=BookingRead)
async def update_booking(booking_id: ObjectIdStr, body: BookingUpdate,
                         svc: BookingService = Depends(get_booking_service)):
    return await svc.transition(booking_id, body.status, Actor.user)


@router.delete("/{booking_id}", status_code=http.HTTP_204_NO_CONTENT)
async def cancel_booking(booking_id: ObjectIdStr, svc: BookingService = Depends(get_booking_service)):
    await svc.transition(booking_id, BookingStatus.cancelled, Actor.user)


@router.post("/{booking_id}/check-in", response_model=BookingRead)
async def check_in(booking_id: ObjectIdStr, svc: BookingService = Depends(get_booking_service)):
    return await svc.transition(booking_id, BookingStatus.checked_in, Actor.staff)