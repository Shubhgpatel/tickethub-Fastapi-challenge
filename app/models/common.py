from typing import Annotated, Generic, TypeVar
from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

ObjectIdStr = Annotated[str, StringConstraints(pattern=r"^[0-9a-fA-F]{24}$")]

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None


class PatchModel(BaseModel):
    """Base for PATCH bodies: no unknown fields, no empty body, no explicit nulls."""
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _check(self):
        if not self.model_fields_set:
            raise ValueError("at least one field is required")
        for f in self.model_fields_set:
            if getattr(self, f) is None:
                raise ValueError(f"{f} cannot be null")
        return self