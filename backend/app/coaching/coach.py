import logging
from collections.abc import AsyncGenerator

import anthropic

from app.coaching.analyzer import (
    categorize_shot,
    compare_sessions,
    compute_averages,
    detect_patterns,
)
from app.coaching.prompts import (
    build_session_prompt,
    build_shot_prompt,
    build_system_prompt,
)
from app.config import settings
from app.garmin.models import ShotData

logger = logging.getLogger(__name__)


class GolfCoach:
    """AI-golftrener som bruker Claude til å analysere slagdata."""

    def __init__(self) -> None:
        self._client: anthropic.AsyncAnthropic | None = None
        self._shot_history: list[ShotData] = []
        self._previous_session_averages: dict | None = None

    def _get_client(self) -> anthropic.AsyncAnthropic:
        if self._client is None:
            self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        return self._client

    def add_shot(self, shot: ShotData) -> None:
        """Legg til et slag i historikken."""
        self._shot_history.append(shot)
        if len(self._shot_history) > 100:
            self._shot_history = self._shot_history[-100:]

    def get_recent_shots(self, club: str | None = None, limit: int = 20) -> list[ShotData]:
        """Hent de siste slagene, valgfritt filtrert på klubb."""
        shots = self._shot_history
        if club:
            shots = [s for s in shots if s.club == club]
        return shots[-limit:]

    async def analyze_shot(
        self, shot: ShotData, skill_level: str = "middels"
    ) -> AsyncGenerator[str, None]:
        """Analyser et enkelt slag og stream coaching-tips."""
        self.add_shot(shot)

        recent = self.get_recent_shots(club=shot.club)
        averages = compute_averages(recent)
        category = categorize_shot(shot, averages)

        shot_dict = shot.model_dump()
        system_prompt = build_system_prompt(skill_level)
        user_prompt = build_shot_prompt(shot_dict, averages)

        # Legg til kategorisering i prompten
        user_prompt += f"\n\nDette slaget er kategorisert som: {category}"

        client = self._get_client()

        async with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def summarize_session(
        self,
        shots: list[ShotData],
        skill_level: str = "middels",
        previous_averages: dict | None = None,
    ) -> AsyncGenerator[str, None]:
        """Oppsummer en hel treningsøkt og stream coaching-tips."""
        if not shots:
            yield "Ingen slag å analysere."
            return

        averages = compute_averages(shots)
        patterns = detect_patterns(shots)
        comparison = compare_sessions(
            averages, previous_averages or self._previous_session_averages
        )

        summary = {
            "club": shots[0].club if shots else "Ukjent",
            **averages,
        }

        system_prompt = build_system_prompt(skill_level)
        user_prompt = build_session_prompt(summary, patterns, comparison)

        client = self._get_client()

        async with client.messages.stream(
            model="claude-opus-4-20250514",
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text

        # Lagre gjennomsnitt for neste sammenligning
        self._previous_session_averages = averages

    async def quick_tip(self, shot: ShotData, skill_level: str = "middels") -> str:
        """Få et raskt tips (ikke-streamende) for et slag."""
        full_response = ""
        async for chunk in self.analyze_shot(shot, skill_level):
            full_response += chunk
        return full_response


golf_coach = GolfCoach()
