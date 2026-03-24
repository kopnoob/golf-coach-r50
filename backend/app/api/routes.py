from __future__ import annotations

import csv
import io
from datetime import datetime

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.coaching.analyzer import categorize_shot, compute_averages, detect_patterns
from app.coaching.coach import golf_coach
from app.config import settings
from app.database.db import database
from app.garmin.client import garmin_client
from app.garmin.models import ShotData

router = APIRouter(prefix="/api")


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str


class PlayerSettings(BaseModel):
    skill_level: str  # "nybegynner", "middels", "avansert"


# In-memory spillerinnstillinger (flyttes til DB i fase 3)
_player_settings = PlayerSettings(skill_level="middels")


@router.post("/auth/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """Logg inn på Garmin Connect."""
    settings.garmin_email = req.email
    settings.garmin_password = req.password
    success = await garmin_client.login()
    if success:
        return LoginResponse(success=True, message="Innlogget på Garmin Connect")
    raise HTTPException(status_code=401, detail="Kunne ikke logge inn på Garmin Connect")


@router.get("/auth/status")
async def auth_status():
    """Sjekk om vi er logget inn."""
    return {"logged_in": garmin_client.is_logged_in}


@router.get("/sessions")
async def get_sessions(limit: int = 10):
    """Hent de siste golføktene."""
    if not garmin_client.is_logged_in:
        raise HTTPException(status_code=401, detail="Ikke logget inn")
    sessions = await garmin_client.get_latest_sessions(limit=limit)
    return {"sessions": [s.model_dump() for s in sessions]}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Hent en spesifikk økt med alle slag."""
    if not garmin_client.is_logged_in:
        raise HTTPException(status_code=401, detail="Ikke logget inn")
    sessions = await garmin_client.get_latest_sessions(limit=50)
    for session in sessions:
        if session.session_id == session_id:
            return session.model_dump()
    raise HTTPException(status_code=404, detail="Økten ble ikke funnet")


def _parse_csv_shot(row: dict) -> ShotData:
    """Parse én rad fra norsk Garmin Golf CSV-eksport."""
    def sf(key: str) -> float | None:
        val = row.get(key, "").strip()
        if not val or val == "0.0":
            return None
        try:
            return float(val)
        except ValueError:
            return None

    date_str = row.get("Dato", "").strip()
    timestamp = None
    if date_str:
        try:
            timestamp = datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
        except ValueError:
            pass

    club = row.get("Type golfkølle", "").strip() or row.get("Navn på kølle", "").strip()

    return ShotData(
        timestamp=timestamp, club=club,
        club_head_speed=sf("Køllehast."), angle_of_attack=sf("Angrepsvinkel"),
        club_path=sf("Køllebane"), club_face_angle=sf("Oversiden av køllen"),
        ball_speed=sf("Ballhastighet"), smash_factor=sf("Slagfaktor"),
        launch_angle=sf("Slagvinkel"), launch_direction=sf("Slagretning"),
        spin_rate=sf("Skruhastighet"), spin_axis=sf("Skruakse"),
        carry_distance=sf("Carry-distanse"), total_distance=sf("Total avstand"),
        apex_height=sf("Toppunktshøyde"), total_deviation=sf("Total avviksavstand"),
    )


@router.post("/import/csv")
async def import_csv(file: UploadFile = File(...)):
    """Importer slagdata fra Garmin Golf CSV-eksport."""
    content = await file.read()
    text = content.decode("utf-8")
    lines = text.strip().split("\n")

    if len(lines) < 3:
        raise HTTPException(status_code=400, detail="CSV-filen har for få rader")

    header = lines[0].strip().split(",")
    # Hopp over enhetsrad (linje 2)
    data_lines = lines[2:]

    shots: list[ShotData] = []
    for line in data_lines:
        if not line.strip():
            continue
        reader = csv.reader([line])
        values = next(reader)
        if len(values) < len(header):
            continue
        row = dict(zip(header, values))
        shots.append(_parse_csv_shot(row))

    if not shots:
        raise HTTPException(status_code=400, detail="Ingen slag funnet i CSV-filen")

    # Lagre i database
    session_id = f"csv-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    for shot in shots:
        avgs = compute_averages([s for s in shots if s.club == shot.club])
        cat = categorize_shot(shot, avgs)
        await database.save_shot(session_id, shot, cat)
        golf_coach.add_shot(shot)

    # Grupper etter klubb og beregn stats
    clubs: dict[str, list[ShotData]] = {}
    for s in shots:
        clubs.setdefault(s.club, []).append(s)

    club_stats = []
    for club, club_shots in clubs.items():
        avgs = compute_averages(club_shots)
        patterns = detect_patterns(club_shots)
        club_stats.append({
            "club": club,
            "shots": len(club_shots),
            "averages": avgs,
            "patterns": patterns,
        })

    # Bygg response med slagdata for frontend
    all_shots_response = []
    for shot in shots:
        avgs = compute_averages([s for s in shots if s.club == shot.club])
        cat = categorize_shot(shot, avgs)
        all_shots_response.append({
            "shot": shot.model_dump(),
            "category": cat,
            "averages": avgs,
        })

    return {
        "session_id": session_id,
        "total_shots": len(shots),
        "clubs": club_stats,
        "shots": all_shots_response,
    }


@router.post("/import/csv/coaching")
async def import_csv_coaching(file: UploadFile = File(...)):
    """Importer CSV og få AI-coaching for hele økten."""
    # Parse CSV
    content = await file.read()
    text = content.decode("utf-8")
    lines = text.strip().split("\n")
    header = lines[0].strip().split(",")
    data_lines = lines[2:]

    shots: list[ShotData] = []
    for line in data_lines:
        if not line.strip():
            continue
        reader = csv.reader([line])
        values = next(reader)
        if len(values) >= len(header):
            row = dict(zip(header, values))
            shots.append(_parse_csv_shot(row))

    if not shots:
        raise HTTPException(status_code=400, detail="Ingen slag funnet")

    # Generer coaching (ikke-streaming for enkel respons)
    coaching = ""
    async for chunk in golf_coach.summarize_session(shots, _player_settings.skill_level):
        coaching += chunk

    return {"coaching": coaching, "total_shots": len(shots)}


@router.get("/settings/player")
async def get_player_settings():
    """Hent spillerinnstillinger."""
    return _player_settings.model_dump()


@router.put("/settings/player")
async def update_player_settings(req: PlayerSettings):
    """Oppdater spillerinnstillinger."""
    global _player_settings
    _player_settings = req
    return _player_settings.model_dump()
