from datetime import UTC, datetime
from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase
from app.repositories.common import to_out


class BookingRepository:
    def __init__(self, db: AsyncDatabase):
        self.col = db["bookings"]

    async def insert(self, data: dict) -> dict:
        now = datetime.now(UTC)
        doc = {**data, "event_id": ObjectId(data["event_id"]), "user_id": ObjectId(data["user_id"]),
               "created_at": now, "updated_at": now}
        await self.col.insert_one(doc)
        return to_out(doc)

    async def get(self, booking_id: str) -> dict | None:
        return to_out(await self.col.find_one({"_id": ObjectId(booking_id)}))

    async def list_page(self, *, event_id=None, user_id=None, status=None,
                        limit: int, after: str | None = None) -> list[dict]:
        query: dict = {}
        if event_id:
            query["event_id"] = ObjectId(event_id)
        if user_id:
            query["user_id"] = ObjectId(user_id)
        if status:
            query["status"] = status
        if after:
            query["_id"] = {"$gt": ObjectId(after)}
        cursor = self.col.find(query).sort("_id", 1).limit(limit)
        return [to_out(d) async for d in cursor]

    async def transition(self, booking_id: str, from_status: str, to_status: str,
                         extra: dict | None = None) -> dict | None:
        return to_out(await self.col.find_one_and_update(
            {"_id": ObjectId(booking_id), "status": from_status},
            {"$set": {"status": to_status, "updated_at": datetime.now(UTC), **(extra or {})}},
            return_document=ReturnDocument.AFTER,
        ))