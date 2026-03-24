"""End-to-end test med realistisk R50 mock-data.

Tester: analyzer, database, coaching (Claude API streaming).
"""
import asyncio
import json
import sys
sys.path.insert(0, ".")

from datetime import datetime, timedelta
from app.garmin.models import ShotData, Session, SessionSummary
from app.coaching.analyzer import compute_averages, categorize_shot, detect_patterns, compare_sessions
from app.coaching.coach import golf_coach
from app.database.db import database
from app.config import settings


# --- Realistisk R50-data: 7-iron økt ---
MOCK_7IRON_SHOTS = [
    ShotData(timestamp=datetime(2025, 3, 20, 14, 0), club="7 Iron",
             ball_speed=195.0, launch_angle=17.2, launch_direction=-1.5,
             spin_rate=6200, spin_axis=3.0, club_head_speed=135.0,
             club_face_angle=-0.5, club_path=-2.0, angle_of_attack=-3.5,
             smash_factor=1.44, carry_distance=148.0, total_distance=155.0,
             apex_height=28.0, total_deviation=-3.0),

    ShotData(timestamp=datetime(2025, 3, 20, 14, 2), club="7 Iron",
             ball_speed=190.0, launch_angle=18.5, launch_direction=2.0,
             spin_rate=6800, spin_axis=-2.0, club_head_speed=133.0,
             club_face_angle=1.0, club_path=0.5, angle_of_attack=-4.0,
             smash_factor=1.43, carry_distance=142.0, total_distance=150.0,
             apex_height=30.0, total_deviation=4.0),

    ShotData(timestamp=datetime(2025, 3, 20, 14, 4), club="7 Iron",
             ball_speed=188.0, launch_angle=16.0, launch_direction=0.5,
             spin_rate=5900, spin_axis=1.0, club_head_speed=132.0,
             club_face_angle=0.0, club_path=-1.0, angle_of_attack=-3.0,
             smash_factor=1.42, carry_distance=145.0, total_distance=153.0,
             apex_height=26.0, total_deviation=1.0),

    ShotData(timestamp=datetime(2025, 3, 20, 14, 6), club="7 Iron",
             ball_speed=180.0, launch_angle=20.0, launch_direction=5.0,
             spin_rate=7500, spin_axis=8.0, club_head_speed=128.0,
             club_face_angle=4.0, club_path=0.0, angle_of_attack=-5.0,
             smash_factor=1.41, carry_distance=132.0, total_distance=138.0,
             apex_height=32.0, total_deviation=12.0),

    ShotData(timestamp=datetime(2025, 3, 20, 14, 8), club="7 Iron",
             ball_speed=192.0, launch_angle=17.8, launch_direction=-0.5,
             spin_rate=6400, spin_axis=2.0, club_head_speed=134.0,
             club_face_angle=-0.2, club_path=-1.5, angle_of_attack=-3.2,
             smash_factor=1.43, carry_distance=146.0, total_distance=154.0,
             apex_height=29.0, total_deviation=-1.0),

    ShotData(timestamp=datetime(2025, 3, 20, 14, 10), club="7 Iron",
             ball_speed=185.0, launch_angle=19.0, launch_direction=3.5,
             spin_rate=7100, spin_axis=5.0, club_head_speed=130.0,
             club_face_angle=2.5, club_path=-0.5, angle_of_attack=-4.5,
             smash_factor=1.42, carry_distance=138.0, total_distance=145.0,
             apex_height=31.0, total_deviation=8.0),
]


async def test_analyzer():
    print("=" * 60)
    print("TEST 1: Analyzer")
    print("=" * 60)

    averages = compute_averages(MOCK_7IRON_SHOTS)
    print(f"\nGjennomsnitt (6 slag med 7-iron):")
    for k, v in averages.items():
        print(f"  {k}: {v}")

    print(f"\nKategorisering av hvert slag:")
    for i, shot in enumerate(MOCK_7IRON_SHOTS):
        cat = categorize_shot(shot, averages)
        print(f"  Slag {i+1}: carry={shot.carry_distance}m, smash={shot.smash_factor} → {cat}")

    patterns = detect_patterns(MOCK_7IRON_SHOTS)
    print(f"\nMønstre:\n{patterns}")

    # Simuler forrige økt
    prev_averages = {
        "avg_carry": 140.0,
        "avg_ball_speed": 185.0,
        "avg_smash_factor": 1.40,
    }
    comparison = compare_sessions(averages, prev_averages)
    print(f"\nSammenligning med forrige økt:\n{comparison}")

    return averages


async def test_database():
    print("\n" + "=" * 60)
    print("TEST 2: Database")
    print("=" * 60)

    settings.database_path = "test_golf_coach.db"
    await database.connect()

    # Lagre slag
    for i, shot in enumerate(MOCK_7IRON_SHOTS):
        cat = "god" if shot.carry_distance and shot.carry_distance > 145 else "middels"
        shot_id = await database.save_shot("test-session-1", shot, cat)
        print(f"  Lagret slag {i+1} med id={shot_id}")

    # Lagre økt
    summary = SessionSummary(
        session_id="test-session-1",
        date=datetime(2025, 3, 20, 14, 0),
        club="7 Iron",
        total_shots=len(MOCK_7IRON_SHOTS),
        avg_carry_distance=141.8,
        avg_ball_speed=188.3,
        avg_smash_factor=1.43,
        avg_spin_rate=6650,
    )
    await database.save_session(summary)
    print(f"  Lagret økt: {summary.session_id}")

    # Hent tilbake
    sessions = await database.get_sessions()
    print(f"\n  Økter i DB: {len(sessions)}")
    for s in sessions:
        print(f"    {s['id']}: {s['club']} - {s['total_shots']} slag, carry={s['avg_carry_distance']}m")

    shots = await database.get_shots_for_session("test-session-1")
    print(f"  Slag i økt: {len(shots)}")

    skill = await database.get_player_skill_level()
    print(f"  Spillernivå: {skill}")

    await database.close()
    print("  Database OK!")


async def test_coaching_single_shot():
    print("\n" + "=" * 60)
    print("TEST 3: Claude coaching - enkeltslag-analyse")
    print("=" * 60)

    # Bruk slag 4 (det dårligste - slice med høy spin)
    bad_shot = MOCK_7IRON_SHOTS[3]
    print(f"\n  Analyserer slag: carry={bad_shot.carry_distance}m, "
          f"smash={bad_shot.smash_factor}, spin={bad_shot.spin_rate}, "
          f"deviation={bad_shot.total_deviation}m")
    print(f"\n  Coaching-tips (streamet fra Claude):")
    print("  " + "-" * 50)

    full_response = ""
    async for chunk in golf_coach.analyze_shot(bad_shot, "middels"):
        print(chunk, end="", flush=True)
        full_response += chunk

    print(f"\n  " + "-" * 50)
    print(f"  Lengde: {len(full_response)} tegn")


async def test_coaching_session_summary():
    print("\n" + "=" * 60)
    print("TEST 4: Claude coaching - øktoppsummering")
    print("=" * 60)

    print(f"\n  Oppsummerer økt med {len(MOCK_7IRON_SHOTS)} slag...")
    print(f"\n  Øktoppsummering (streamet fra Claude):")
    print("  " + "-" * 50)

    full_response = ""
    async for chunk in golf_coach.summarize_session(MOCK_7IRON_SHOTS, "middels"):
        print(chunk, end="", flush=True)
        full_response += chunk

    print(f"\n  " + "-" * 50)
    print(f"  Lengde: {len(full_response)} tegn")


async def main():
    print("\n🏌️ Golf Coach R50 - End-to-end test")
    print("=" * 60)

    await test_analyzer()
    await test_database()

    if not settings.anthropic_api_key:
        print("\n⚠️  Ingen ANTHROPIC_API_KEY - hopper over Claude-tester")
        return

    await test_coaching_single_shot()
    await test_coaching_session_summary()

    print("\n\n✅ Alle tester fullført!")


asyncio.run(main())
