import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.api.websocket import manager, websocket_endpoint
from app.config import settings
from app.database.db import database

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Oppstart
    await database.connect()
    await manager.start_polling(settings.polling_interval_seconds)
    yield
    # Nedstengning
    await manager.stop_polling()
    await database.close()


app = FastAPI(title="Golf Coach R50", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.add_api_websocket_route("/ws", websocket_endpoint)


@app.get("/")
async def root():
    return {"app": "Golf Coach R50", "status": "running"}
