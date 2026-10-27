from contextlib import asynccontextmanager
from fastapi import FastAPI
from pymongo import AsyncMongoClient
from app.core.config import settings
from app.db import client as db

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.client = AsyncMongoClient(settings.mongo_uri)
    # later: await create_indexes(db.get_db())
    yield
    await db.client.close()

app = FastAPI(title="TicketHub", lifespan=lifespan)

@app.get("/health")
async def health():
    await db.get_db().command("ping")
    return {"status": "ok"}