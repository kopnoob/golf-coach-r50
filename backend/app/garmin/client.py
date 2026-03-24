from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from garminconnect import Garmin

from app.config import settings
from app.garmin.models import Session, SessionSummary, ShotData

logger = logging.getLogger(__name__)

TOKEN_DIR = Path.home() / ".garth"


class GarminClient:
    """Klient for å hente golfdata fra Garmin Connect."""

    def __init__(self) -> None:
        self._client: Garmin | None = None
        self._last_activity_id: str | None = None

    async def login(self) -> bool:
        """Logg inn på Garmin Connect. Bruker cached tokens hvis tilgjengelig."""
        try:
            self._client = Garmin()
            self._client.login(TOKEN_DIR.as_posix())
            logger.info("Logget inn med cached Garmin-token")
            return True
        except Exception:
            logger.info("Cached token ugyldig, prøver med brukernavn/passord")

        try:
            self._client = Garmin(settings.garmin_email, settings.garmin_password)
            self._client.login()
            self._client.garth.dump(TOKEN_DIR.as_posix())
            logger.info("Logget inn på Garmin Connect med brukernavn/passord")
            return True
        except Exception as e:
            logger.error("Kunne ikke logge inn på Garmin Connect: %s", e)
            self._client = None
            return False

    @property
    def is_logged_in(self) -> bool:
        return self._client is not None

    async def get_golf_activities(self, days: int = 30) -> list[dict]:
        """Hent golfaktiviteter fra de siste N dagene."""
        if not self._client:
            raise RuntimeError("Ikke logget inn på Garmin Connect")

        start = datetime.now() - timedelta(days=days)
        end = datetime.now()

        try:
            activities = self._client.get_activities_by_date(
                start.strftime("%Y-%m-%d"),
                end.strftime("%Y-%m-%d"),
                "golf",
            )
            return activities or []
        except Exception as e:
            logger.error("Feil ved henting av golfaktiviteter: %s", e)
            return []

    async def get_activity_details(self, activity_id: str) -> dict | None:
        """Hent detaljer for en spesifikk aktivitet."""
        if not self._client:
            raise RuntimeError("Ikke logget inn på Garmin Connect")

        try:
            return self._client.get_activity_details(activity_id)
        except Exception as e:
            logger.error("Feil ved henting av aktivitet %s: %s", activity_id, e)
            return None

    def _parse_shot_data(self, raw_shot: dict) -> ShotData:
        """Konverter rå Garmin-data til ShotData-modell."""
        return ShotData(
            timestamp=raw_shot.get("startTimeLocal"),
            club=raw_shot.get("clubName", ""),
            ball_speed=raw_shot.get("ballSpeed"),
            launch_angle=raw_shot.get("launchAngle"),
            launch_direction=raw_shot.get("launchDirection"),
            spin_rate=raw_shot.get("spinRate"),
            spin_axis=raw_shot.get("spinAxis"),
            club_head_speed=raw_shot.get("clubHeadSpeed"),
            club_face_angle=raw_shot.get("clubFaceAngle"),
            club_path=raw_shot.get("clubPath"),
            angle_of_attack=raw_shot.get("angleOfAttack"),
            smash_factor=raw_shot.get("smashFactor"),
            carry_distance=raw_shot.get("carryDistance"),
            total_distance=raw_shot.get("totalDistance"),
            apex_height=raw_shot.get("apexHeight"),
            total_deviation=raw_shot.get("totalDeviation"),
        )

    def _build_session(
        self, activity: dict, shots_raw: list[dict]
    ) -> Session:
        """Bygg en Session fra aktivitetsdata og rådata for slag."""
        shots = [self._parse_shot_data(s) for s in shots_raw]
        club = shots[0].club if shots else "Ukjent"

        carry_distances = [s.carry_distance for s in shots if s.carry_distance]
        ball_speeds = [s.ball_speed for s in shots if s.ball_speed]
        smash_factors = [s.smash_factor for s in shots if s.smash_factor]
        spin_rates = [s.spin_rate for s in shots if s.spin_rate]

        summary = SessionSummary(
            session_id=str(activity.get("activityId", "")),
            date=activity.get("startTimeLocal", datetime.now()),
            club=club,
            total_shots=len(shots),
            avg_carry_distance=(
                sum(carry_distances) / len(carry_distances) if carry_distances else None
            ),
            avg_ball_speed=(
                sum(ball_speeds) / len(ball_speeds) if ball_speeds else None
            ),
            avg_smash_factor=(
                sum(smash_factors) / len(smash_factors) if smash_factors else None
            ),
            avg_spin_rate=(
                sum(spin_rates) / len(spin_rates) if spin_rates else None
            ),
        )

        return Session(
            session_id=str(activity.get("activityId", "")),
            date=activity.get("startTimeLocal", datetime.now()),
            club=club,
            shots=shots,
            summary=summary,
        )

    async def get_latest_sessions(self, limit: int = 10) -> list[Session]:
        """Hent de siste golføktene med slagdata."""
        activities = await self.get_golf_activities()
        sessions = []

        for activity in activities[:limit]:
            activity_id = str(activity.get("activityId", ""))
            details = await self.get_activity_details(activity_id)
            if not details:
                continue

            shots_raw = details.get("golfShots", details.get("shots", []))
            if not shots_raw:
                continue

            session = self._build_session(activity, shots_raw)
            sessions.append(session)

        return sessions

    async def poll_new_shots(self) -> list[ShotData] | None:
        """Sjekk om det finnes nye slag siden sist. Returnerer nye slag eller None."""
        activities = await self.get_golf_activities(days=1)
        if not activities:
            return None

        latest = activities[0]
        activity_id = str(latest.get("activityId", ""))

        if activity_id == self._last_activity_id:
            return None

        self._last_activity_id = activity_id
        details = await self.get_activity_details(activity_id)
        if not details:
            return None

        shots_raw = details.get("golfShots", details.get("shots", []))
        return [self._parse_shot_data(s) for s in shots_raw]


garmin_client = GarminClient()
