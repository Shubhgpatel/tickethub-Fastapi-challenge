from typing import Annotated, Generic, TypeVar
from pydantic import BaseModel, StringConstraints

ObjectIdStr = Annotated[str, StringConstraints(pattern=r"^[0-9a-fA-F]{24}$")]

T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None