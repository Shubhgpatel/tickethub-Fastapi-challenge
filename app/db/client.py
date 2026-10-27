from pymongo import AsyncMongoClient
from app.core.config import settings

client: AsyncMongoClient | None = None

def get_db():
    return client[settings.mongo_db]