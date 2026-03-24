"""Offline capture-modus for R50.

Kobler til R50-hotspot, fanger rå meldinger til en lokal JSON-fil.
Når du kobler tilbake til internett, kan dataene sendes til Claude for analyse.

Bruk:
  1. På R50: Koble til → GSPro
  2. På Mac: Koble WiFi til R50-hotspot
  3. Kjør: python3 -m app.r50.capture
  4. Slå baller — data lagres lokalt
  5. Ctrl+C for å stoppe
  6. Koble tilbake til vanlig WiFi
  7. Kjør: python3 -m app.r50.capture --analyze
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

CAPTURE_DIR = Path(__file__).parent.parent.parent / "captures"


def get_capture_path() -> Path:
    """Returner sti for ny capture-fil."""
    CAPTURE_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return CAPTURE_DIR / f"r50-session-{ts}.json"


async def capture_session():
    """Koble til R50 og lagre alle meldinger til fil."""
    from app.r50.connector import R50Monitor, parse_shot_from_r50

    capture_path = get_capture_path()
    session_data = {
        "start_time": datetime.now().isoformat(),
        "raw_messages": [],
        "parsed_shots": [],
    }

    monitor = R50Monitor()
    logger.info("Søker etter R50 på nettverket...")
    logger.info("(Sørg for at Mac-en er koblet til R50 sitt hotspot-nettverk)")

    ok = await monitor.discover_and_connect(timeout=30)
    if not ok:
        logger.error("Fant ingen R50. Sjekk at:")
        logger.error("  1. R50 er i simulatormodus (Koble til → GSPro)")
        logger.error("  2. Mac-en er koblet til R50 sitt WiFi-hotspot")
        return

    logger.info("Tilkoblet R50! Slå baller — data lagres lokalt.")
    logger.info("Capture-fil: %s", capture_path)
    logger.info("Trykk Ctrl+C for å stoppe.\n")

    shot_count = 0
    try:
        async for shot in monitor.listen():
            shot_count += 1
            session_data["parsed_shots"].append({
                "shot_number": shot_count,
                "timestamp": datetime.now().isoformat(),
                **shot,
            })

            # Lagre etter hvert slag (i tilfelle krasj)
            capture_path.write_text(
                json.dumps(session_data, indent=2, default=str, ensure_ascii=False)
            )

            logger.info(
                "Slag #%d: %s carry=%.1fm ball_speed=%.1f km/t",
                shot_count,
                shot.get("club", "?"),
                shot.get("carry_distance") or 0,
                shot.get("ball_speed") or 0,
            )

    except KeyboardInterrupt:
        pass
    finally:
        await monitor.stop()
        session_data["end_time"] = datetime.now().isoformat()
        session_data["total_shots"] = shot_count
        capture_path.write_text(
            json.dumps(session_data, indent=2, default=str, ensure_ascii=False)
        )
        logger.info("\nFerdig! %d slag lagret til: %s", shot_count, capture_path)
        logger.info("Koble tilbake til WiFi og kjør:")
        logger.info("  python3 -m app.r50.capture --analyze %s", capture_path)


async def analyze_capture(filepath: str):
    """Analyser en tidligere capture-fil med Claude AI."""
    path = Path(filepath)
    if not path.exists():
        logger.error("Filen finnes ikke: %s", filepath)
        return

    data = json.loads(path.read_text())
    shots_raw = data.get("parsed_shots", [])

    if not shots_raw:
        logger.error("Ingen slag i filen")
        return

    logger.info("Analyserer %d slag fra %s", len(shots_raw), data.get("start_time", "?"))

    # Konverter til ShotData
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from app.garmin.models import ShotData
    from app.coaching.analyzer import compute_averages, detect_patterns
    from app.coaching.coach import golf_coach

    shots = []
    for s in shots_raw:
        shot = ShotData(
            timestamp=s.get("timestamp"),
            club=s.get("club", ""),
            ball_speed=s.get("ball_speed"),
            launch_angle=s.get("launch_angle"),
            launch_direction=s.get("launch_direction"),
            spin_rate=s.get("spin_rate"),
            spin_axis=s.get("spin_axis"),
            club_head_speed=s.get("club_head_speed"),
            club_face_angle=s.get("club_face_angle"),
            club_path=s.get("club_path"),
            angle_of_attack=s.get("angle_of_attack"),
            smash_factor=s.get("smash_factor"),
            carry_distance=s.get("carry_distance"),
            total_distance=s.get("total_distance"),
            apex_height=s.get("apex_height"),
            total_deviation=s.get("total_deviation"),
        )
        shots.append(shot)

    # Grupper etter klubb
    clubs: dict[str, list[ShotData]] = {}
    for s in shots:
        clubs.setdefault(s.club, []).append(s)

    for club, club_shots in clubs.items():
        avgs = compute_averages(club_shots)
        patterns = detect_patterns(club_shots)
        print(f"\n--- {club} ({len(club_shots)} slag) ---")
        print(f"  Carry snitt: {avgs.get('avg_carry', 'N/A')}m")
        print(f"  Ballhastighet: {avgs.get('avg_ball_speed', 'N/A')} km/t")
        print(f"  Mønstre:\n{patterns}")

    # AI-coaching
    print(f"\n{'='*60}")
    print("AI Coaching (Claude)")
    print(f"{'='*60}\n")

    async for chunk in golf_coach.summarize_session(shots, "middels"):
        print(chunk, end="", flush=True)
    print()


async def list_captures():
    """List alle capture-filer."""
    if not CAPTURE_DIR.exists():
        print("Ingen captures funnet.")
        return

    files = sorted(CAPTURE_DIR.glob("r50-session-*.json"))
    if not files:
        print("Ingen captures funnet.")
        return

    print(f"Captures i {CAPTURE_DIR}:\n")
    for f in files:
        data = json.loads(f.read_text())
        shots = data.get("total_shots", len(data.get("parsed_shots", [])))
        start = data.get("start_time", "?")
        print(f"  {f.name}: {shots} slag ({start})")


async def main():
    if "--analyze" in sys.argv:
        idx = sys.argv.index("--analyze")
        if idx + 1 < len(sys.argv):
            await analyze_capture(sys.argv[idx + 1])
        else:
            # Analyser siste capture
            files = sorted(CAPTURE_DIR.glob("r50-session-*.json"))
            if files:
                await analyze_capture(str(files[-1]))
            else:
                print("Ingen capture-filer funnet. Kjør først uten --analyze.")
    elif "--list" in sys.argv:
        await list_captures()
    else:
        await capture_session()


if __name__ == "__main__":
    asyncio.run(main())
