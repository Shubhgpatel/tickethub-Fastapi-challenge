import base64
import json
from datetime import datetime
from bson import ObjectId
from app.core.errors import AppError


def encode_cursor(starts_at: datetime, id_: str) -> str:
    raw = json.dumps({"s": starts_at.isoformat(), "id": id_}).encode()
    return base64.urlsafe_b64encode(raw).decode()


def decode_cursor(cursor: str) -> tuple[datetime, str]:
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        starts_at, oid = datetime.fromisoformat(data["s"]), data["id"]
        if starts_at.tzinfo is None or len(oid) != 24 or not ObjectId.is_valid(oid):
            raise ValueError
        return starts_at, oid
    except (ValueError, KeyError, TypeError):
        raise AppError(422, "INVALID_CURSOR", "Cursor is malformed")