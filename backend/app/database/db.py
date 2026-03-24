from __future__ import annotations

import aiosqlite

from app.config import settings
from app.database.models import SCHEMA
from app.garmin.models import SessionSummary, ShotData


class Database:
    """Async SQLite database for Golf Coach R50."""

    def __init__(self) -> None:
        self._db: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._db = await aiosqlite.connect(settings.database_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(SCHEMA)
        # Opprett standardspiller hvis den ikke finnes
        cursor = await self._db.execute("SELECT id FROM players WHERE id = 1")
        if not await cursor.fetchone():
            await self._db.execute(
                "INSERT INTO players (id, name, skill_level) VALUES (1, 'Spiller', 'middels')"
            )
            await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()

    async def save_session(self, summary: SessionSummary) -> None:
        if not self._db:
            return
        await self._db.execute(
            """INSERT OR REPLACE INTO sessions
            (id, date, club, total_shots, avg_carry_distance, avg_ball_speed, avg_smash_factor, avg_spin_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                summary.session_id,
                summary.date.isoformat(),
                summary.club,
                summary.total_shots,
                summary.avg_carry_distance,
                summary.avg_ball_speed,
                summary.avg_smash_factor,
                summary.avg_spin_rate,
            ),
        )
        await self._db.commit()

    async def save_shot(self, session_id: str, shot: ShotData, category: str = "middels") -> int:
        if not self._db:
            return -1
        cursor = await self._db.execute(
            """INSERT INTO shots
            (session_id, timestamp, club, ball_speed, launch_angle, launch_direction,
             spin_rate, spin_axis, club_head_speed, club_face_angle, club_path,
             angle_of_attack, smash_factor, carry_distance, total_distance,
             apex_height, total_deviation, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                shot.timestamp.isoformat() if shot.timestamp else None,
                shot.club,
                shot.ball_speed,
                shot.launch_angle,
                shot.launch_direction,
                shot.spin_rate,
                shot.spin_axis,
                shot.club_head_speed,
                shot.club_face_angle,
                shot.club_path,
                shot.angle_of_attack,
                shot.smash_factor,
                shot.carry_distance,
                shot.total_distance,
                shot.apex_height,
                shot.total_deviation,
                category,
            ),
        )
        await self._db.commit()
        return cursor.lastrowid or -1

    async def save_coaching_tip(
        self,
        tip_type: str,
        content: str,
        skill_level: str,
        session_id: str | None = None,
        shot_id: int | None = None,
    ) -> None:
        if not self._db:
            return
        await self._db.execute(
            """INSERT INTO coaching_tips (session_id, shot_id, tip_type, content, skill_level)
            VALUES (?, ?, ?, ?, ?)""",
            (session_id, shot_id, tip_type, content, skill_level),
        )
        await self._db.commit()

    async def get_sessions(self, limit: int = 20) -> list[dict]:
        if not self._db:
            return []
        cursor = await self._db.execute(
            "SELECT * FROM sessions ORDER BY date DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_shots_for_session(self, session_id: str) -> list[dict]:
        if not self._db:
            return []
        cursor = await self._db.execute(
            "SELECT * FROM shots WHERE session_id = ? ORDER BY timestamp", (session_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_player_skill_level(self) -> str:
        if not self._db:
            return "middels"
        cursor = await self._db.execute("SELECT skill_level FROM players WHERE id = 1")
        row = await cursor.fetchone()
        return row["skill_level"] if row else "middels"

    async def set_player_skill_level(self, level: str) -> None:
        if not self._db:
            return
        await self._db.execute(
            "UPDATE players SET skill_level = ? WHERE id = 1", (level,)
        )
        await self._db.commit()

    async def get_club_averages(self, club: str, limit: int = 50) -> dict:
        """Hent gjennomsnittsverdier for en klubb basert på de siste N slagene."""
        if not self._db:
            return {}
        cursor = await self._db.execute(
            """SELECT
                AVG(carry_distance) as avg_carry,
                AVG(ball_speed) as avg_ball_speed,
                AVG(smash_factor) as avg_smash_factor,
                AVG(spin_rate) as avg_spin_rate,
                COUNT(*) as total_shots
            FROM shots WHERE club = ?
            ORDER BY created_at DESC LIMIT ?""",
            (club, limit),
        )
        row = await cursor.fetchone()
        return dict(row) if row else {}


database = Database()
