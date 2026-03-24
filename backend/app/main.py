from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.api.websocket import manager, websocket_endpoint
from app.config import settings
from app.database.db import database

logging.basicConfig(level=logging.INFO)


async def _r50_listener():
    """Bakgrunnsoppgave: Koble til R50 direkte og stream slagdata."""
    from app.r50.connector import R50Monitor
    from app.garmin.models import ShotData
    from datetime import datetime

    monitor = R50Monitor()
    while True:
        try:
            logger.info("Søker etter Garmin R50 på nettverket...")
            ok = await monitor.discover_and_connect(timeout=30)
            if not ok:
                logger.info("Ingen R50 funnet, prøver igjen om 10s...")
                await asyncio.sleep(10)
                continue

            logger.info("Koblet til R50! Lytter på slagdata...")
            async for shot_dict in monitor.listen():
                shot = ShotData(
                    timestamp=datetime.now(),
                    **{k: v for k, v in shot_dict.items() if v is not None}
                )
                await manager._process_new_shot(shot)

        except Exception as e:
            logger.error("R50-lytter feil: %s", e)
        finally:
            await monitor.stop()

        logger.info("R50-tilkobling tapt, prøver igjen om 5s...")
        await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Oppstart
    await database.connect()
    # Start R50 direkte tilkobling (primær) + Garmin Cloud polling (fallback)
    r50_task = asyncio.create_task(_r50_listener())
    await manager.start_polling(settings.polling_interval_seconds)
    yield
    # Nedstengning
    r50_task.cancel()
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
