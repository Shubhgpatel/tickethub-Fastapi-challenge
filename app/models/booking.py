from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field
from app.models.common import ObjectIdStr


class BookingStatus(StrEnum):
    pending_payment = "pending_payment"
    confirmed = "confirmed"
    checked_in = "checked_in"
    cancelled = "cancelled"
    expired = "expired"
    refunded = "refunded"


class BookingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: ObjectIdStr
    tier: str = Field(min_length=1, max_length=40)
    quantity: int = Field(ge=1, le=6)
    user_id: ObjectIdStr  # TEMPORARY: comes from the JWT in Phase 3


class BookingUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: BookingStatus


class BookingRead(BaseModel):
    id: str
    event_id: str
    user_id: str
    tier: str
    quantity: int
    amount_inr: int
    status: BookingStatus
    hold_expires_at: datetime | None
    created_at: datetime
    updated_at: datetime