from datetime import UTC, datetime, timedelta
from enum import StrEnum
from app.core.config import settings
from app.core.errors import AppError, NotFound
from app.models.booking import BookingCreate, BookingRead, BookingStatus as S
from app.models.common import Page
from app.repositories.booking_repo import BookingRepository
from app.repositories.event_repo import EventRepository
from app.repositories.user_repo import UserRepository


class Actor(StrEnum):
    user = "user"        # attendee via API
    staff = "staff"      # door staff
    payment = "payment"  # payment webhook (Phase 6)
    system = "system"    # cron / jobs (Phase 5)


# (from, to) -> who may trigger it. Anything not listed is illegal.
TRANSITIONS: dict[tuple[S, S], set[Actor]] = {
    (S.pending_payment, S.confirmed): {Actor.payment},
    (S.pending_payment, S.cancelled): {Actor.user},
    (S.pending_payment, S.expired):   {Actor.system},
    (S.confirmed, S.checked_in):      {Actor.staff},
    (S.confirmed, S.cancelled):       {Actor.user},
    (S.confirmed, S.refunded):        {Actor.system},
}
RELEASES_SEATS = {S.cancelled, S.expired, S.refunded}


class BookingService:
    def __init__(self, bookings: BookingRepository, events: EventRepository, users: UserRepository):
        self.bookings, self.events, self.users = bookings, events, users

    async def create(self, data: BookingCreate) -> BookingRead:
        user = await self.users.get(data.user_id)
        if not user or not user["is_active"]:
            raise NotFound("User")
        event = await self.events.get(data.event_id)
        if not event:
            raise NotFound("Event")
        tier = next((t for t in event["ticket_tiers"] if t["name"] == data.tier), None)
        if tier is None:
            raise AppError(422, "UNKNOWN_TIER", f"Event has no tier named '{data.tier}'")
        now = datetime.now(UTC)
        if event["status"] != "published" or event["starts_at"] <= now:
            raise AppError(409, "EVENT_NOT_BOOKABLE", "Event is not open for booking")

        # Step 1: atomically take the seats (R1.2)
        if not await self.events.reserve_seats(data.event_id, data.tier, data.quantity):
            raise AppError(409, "SOLD_OUT", "Not enough seats left in this tier")

        # Step 2: record the booking; if that fails, give the seats back (compensation)
        try:
            doc = await self.bookings.insert({
                "event_id": data.event_id, "user_id": data.user_id, "tier": data.tier,
                "quantity": data.quantity,
                "amount_inr": tier["price_inr"] * data.quantity,   # price snapshot, server-side
                "status": S.pending_payment,
                "hold_expires_at": now + timedelta(minutes=settings.hold_minutes),
            })
        except Exception:
            await self.events.release_seats(data.event_id, data.tier, data.quantity)
            raise
        return BookingRead(**doc)

    async def get(self, booking_id: str) -> BookingRead:
        doc = await self.bookings.get(booking_id)
        if not doc:
            raise NotFound("Booking")
        return BookingRead(**doc)

    async def list_page(self, *, event_id, user_id, status, limit, cursor) -> Page[BookingRead]:
        docs = await self.bookings.list_page(event_id=event_id, user_id=user_id, status=status,
                                             limit=limit + 1, after=cursor)
        has_more = len(docs) > limit
        docs = docs[:limit]
        return Page(items=[BookingRead(**d) for d in docs],
                    next_cursor=docs[-1]["id"] if has_more else None)

    async def transition(self, booking_id: str, target: S, actor: Actor) -> BookingRead:
        current = await self.bookings.get(booking_id)
        if not current:
            raise NotFound("Booking")
        source = S(current["status"])
        if actor not in TRANSITIONS.get((source, target), set()):
            raise AppError(409, "ILLEGAL_TRANSITION", f"Cannot change booking from {source} to {target}")

        extra = {"hold_expires_at": None} if source == S.pending_payment else {}
        doc = await self.bookings.transition(booking_id, source, target, extra)
        if not doc:  # someone else changed it between our read and write
            raise AppError(409, "ILLEGAL_TRANSITION", "Booking changed concurrently; refetch and retry")

        # Only the caller whose conditional update succeeded releases seats → exactly once
        if target in RELEASES_SEATS:
            await self.events.release_seats(current["event_id"], current["tier"], current["quantity"])
        return BookingRead(**doc)