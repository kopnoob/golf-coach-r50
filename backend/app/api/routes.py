from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.garmin.client import garmin_client

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
