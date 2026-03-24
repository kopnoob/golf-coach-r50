from __future__ import annotations

import asyncio
import json
import logging

from fastapi import WebSocket, WebSocketDisconnect

from app.coaching.analyzer import categorize_shot, compute_averages
from app.coaching.coach import golf_coach
from app.database.db import database
from app.garmin.client import garmin_client
from app.garmin.models import ShotData

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Håndterer WebSocket-tilkoblinger."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []
        self._polling_task: asyncio.Task | None = None

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("Ny WebSocket-tilkobling (%d aktive)", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)
        logger.info("WebSocket frakoblet (%d aktive)", len(self.active_connections))

    async def broadcast(self, message: dict) -> None:
        """Send melding til alle tilkoblede klienter."""
        data = json.dumps(message, default=str)
        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception:
                pass

    async def broadcast_text(self, text: str) -> None:
        """Send ren tekst til alle tilkoblede klienter."""
        for connection in self.active_connections:
            try:
                await connection.send_text(text)
            except Exception:
                pass

    async def start_polling(self, interval_seconds: int = 30) -> None:
        """Start polling av Garmin Connect for nye slag."""
        if self._polling_task and not self._polling_task.done():
            return
        self._polling_task = asyncio.create_task(self._poll_loop(interval_seconds))

    async def stop_polling(self) -> None:
        if self._polling_task:
            self._polling_task.cancel()

    async def _poll_loop(self, interval: int) -> None:
        """Poller Garmin Connect for nye slag."""
        logger.info("Starter Garmin-polling (hvert %ds)", interval)
        while True:
            try:
                if garmin_client.is_logged_in:
                    new_shots = await garmin_client.poll_new_shots()
                    if new_shots:
                        logger.info("Fant %d nye slag", len(new_shots))
                        for shot in new_shots:
                            await self._process_new_shot(shot)
            except Exception as e:
                logger.error("Feil i polling: %s", e)
            await asyncio.sleep(interval)

    async def _process_new_shot(self, shot: ShotData) -> None:
        """Prosesser et nytt slag: lagre, analyser, og send til klienter."""
        # Beregn gjennomsnitt og kategoriser
        recent = golf_coach.get_recent_shots(club=shot.club)
        averages = compute_averages(recent)
        category = categorize_shot(shot, averages)

        # Lagre i database
        shot_id = await database.save_shot("current", shot, category)

        # Send slagdata til frontend
        await self.broadcast({
            "type": "new_shot",
            "shot": shot.model_dump(),
            "category": category,
            "averages": averages,
        })

        # Stream coaching-tips
        skill_level = await database.get_player_skill_level()

        await self.broadcast({"type": "coaching_start"})

        full_tip = ""
        async for chunk in golf_coach.analyze_shot(shot, skill_level):
            full_tip += chunk
            await self.broadcast({
                "type": "coaching_chunk",
                "text": chunk,
            })

        await self.broadcast({"type": "coaching_end"})

        # Lagre tip i database
        await database.save_coaching_tip(
            tip_type="shot",
            content=full_tip,
            skill_level=skill_level,
            shot_id=shot_id,
        )


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket-endepunkt for sanntidsoppdateringer."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "request_analysis":
                # Manuell forespørsel om analyse av et slag
                shot = ShotData(**message.get("shot", {}))
                skill_level = message.get("skill_level", "middels")

                await websocket.send_text(
                    json.dumps({"type": "coaching_start"})
                )
                async for chunk in golf_coach.analyze_shot(shot, skill_level):
                    await websocket.send_text(
                        json.dumps({"type": "coaching_chunk", "text": chunk})
                    )
                await websocket.send_text(
                    json.dumps({"type": "coaching_end"})
                )

            elif message.get("type") == "request_session_summary":
                # Forespørsel om øktoppsummering
                skill_level = message.get("skill_level", "middels")
                shots = [
                    ShotData(**s) for s in message.get("shots", [])
                ]
                await websocket.send_text(
                    json.dumps({"type": "coaching_start"})
                )
                async for chunk in golf_coach.summarize_session(shots, skill_level):
                    await websocket.send_text(
                        json.dumps({"type": "coaching_chunk", "text": chunk})
                    )
                await websocket.send_text(
                    json.dumps({"type": "coaching_end"})
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
