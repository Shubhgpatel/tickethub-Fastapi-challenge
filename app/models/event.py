from datetime import datetime
from enum import StrEnum
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator
from app.models.common import ObjectIdStr, PatchModel


class EventStatus(StrEnum):
    draft = "draft"
    published = "published"
    completed = "completed"
    cancelled = "cancelled"


class Venue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    city: str = Field(min_length=1, max_length=80)


class TicketTierIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=40)
    price_inr: int = Field(ge=0, le=1_000_000)
    quota: int = Field(ge=1)


class TicketTierRead(BaseModel):
    name: str
    price_inr: int
    quota: int
    remaining: int


def validate_event_shape(starts_at, ends_at, capacity: int, tiers: list[dict]) -> None:
    """Cross-field rules. Used by EventCreate AND by the service on PATCH (merged doc)."""
    if starts_at >= ends_at:
        raise ValueError("starts_at must be before ends_at")
    names = [t["name"].lower() for t in tiers]
    if len(names) != len(set(names)):
        raise ValueError("tier names must be unique")
    if sum(t["quota"] for t in tiers) > capacity:
        raise ValueError("sum of tier quotas exceeds capacity")


class EventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=5, max_length=120)
    venue: Venue
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    capacity: int = Field(ge=1, le=50_000)
    ticket_tiers: list[TicketTierIn] = Field(min_length=1, max_length=10)
    organizer_id: ObjectIdStr  # TEMPORARY: comes from the JWT in Phase 3

    @model_validator(mode="after")
    def _shape(self):
        validate_event_shape(self.starts_at, self.ends_at, self.capacity,
                             [t.model_dump() for t in self.ticket_tiers])
        return self


class EventUpdate(PatchModel):
    title: str | None = Field(default=None, min_length=5, max_length=120)
    venue: Venue | None = None
    starts_at: AwareDatetime | None = None
    ends_at: AwareDatetime | None = None
    capacity: int | None = Field(default=None, ge=1, le=50_000)
    ticket_tiers: list[TicketTierIn] | None = Field(default=None, min_length=1, max_length=10)


class EventRead(BaseModel):
    id: str
    title: str
    venue: Venue
    starts_at: datetime
    ends_at: datetime
    capacity: int
    ticket_tiers: list[TicketTierRead]
    status: EventStatus
    organizer_id: str
    version: int
    created_at: datetime
    updated_at: datetime