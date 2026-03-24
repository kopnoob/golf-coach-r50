from datetime import datetime
from pydantic import BaseModel


class ShotData(BaseModel):
    """Data fra et enkelt slag målt av Garmin Approach R50."""

    timestamp: datetime | None = None
    club: str = ""
    ball_speed: float | None = None  # mph
    launch_angle: float | None = None  # grader
    launch_direction: float | None = None  # grader (+ = høyre, - = venstre)
    spin_rate: float | None = None  # rpm
    spin_axis: float | None = None  # grader
    club_head_speed: float | None = None  # mph
    club_face_angle: float | None = None  # grader
    club_path: float | None = None  # grader
    angle_of_attack: float | None = None  # grader
    smash_factor: float | None = None  # ratio
    carry_distance: float | None = None  # meter
    total_distance: float | None = None  # meter
    apex_height: float | None = None  # meter
    total_deviation: float | None = None  # meter (+ = høyre, - = venstre)


class SessionSummary(BaseModel):
    """Oppsummering av en treningsøkt."""

    session_id: str
    date: datetime
    club: str
    total_shots: int
    avg_carry_distance: float | None = None
    avg_ball_speed: float | None = None
    avg_smash_factor: float | None = None
    avg_spin_rate: float | None = None


class Session(BaseModel):
    """Full treningsøkt med alle slag."""

    session_id: str
    date: datetime
    club: str
    shots: list[ShotData] = []
    summary: SessionSummary | None = None
