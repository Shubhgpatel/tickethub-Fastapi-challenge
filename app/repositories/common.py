from bson import ObjectId


def to_out(doc: dict | None) -> dict | None:
    if doc is None:
        return None
    out = {k: (str(v) if isinstance(v, ObjectId) else v) for k, v in doc.items() if k != "_id"}
    out["id"] = str(doc["_id"])
    return out
    