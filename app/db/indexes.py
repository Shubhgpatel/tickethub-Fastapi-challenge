from pymongo.asynchronous.database import AsyncDatabase

async def create_indexes(db: AsyncDatabase) -> None:
    await db["users"].create_index("email", unique=True)