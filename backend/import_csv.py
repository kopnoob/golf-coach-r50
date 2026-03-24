"""Importer R50-data fra Garmin Connect CSV-eksport."""
from __future__ import annotations

import asyncio
import csv
import json
import sys
sys.path.insert(0, ".")

from datetime import datetime
from pathlib import Path
from app.garmin.models import ShotData
from app.coaching.analyzer import compute_averages, categorize_shot, detect_patterns
from app.coaching.coach import golf_coach
from app.database.db import database
from app.config import settings


def parse_garmin_csv(filepath: str) -> list[ShotData]:
    """Parse en norsk Garmin Connect CSV-eksport til ShotData-objekter."""
    shots = []

    with open(filepath, "r", encoding="utf-8") as f:
        # Les header og enhetsrad
        lines = f.readlines()

    header = lines[0].strip().split(",")
    # Hopp over enhetsrad (linje 2)
    data_lines = lines[2:]

    for line in data_lines:
        if not line.strip():
            continue

        # Parse CSV-linje (håndter komma i felter)
        reader = csv.reader([line])
        values = next(reader)

        if len(values) < len(header):
            continue

        row = dict(zip(header, values))

        def safe_float(key: str) -> float | None:
            val = row.get(key, "").strip()
            if not val or val == "0.0":
                return None
            try:
                return float(val)
            except ValueError:
                return None

        # Parse dato
        date_str = row.get("Dato", "").strip()
        timestamp = None
        if date_str:
            try:
                timestamp = datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
            except ValueError:
                pass

        club = row.get("Type golfkølle", "").strip()
        if not club:
            club = row.get("Navn på kølle", "").strip()

        shot = ShotData(
            timestamp=timestamp,
            club=club,
            club_head_speed=safe_float("Køllehast."),
            angle_of_attack=safe_float("Angrepsvinkel"),
            club_path=safe_float("Køllebane"),
            club_face_angle=safe_float("Oversiden av køllen"),
            ball_speed=safe_float("Ballhastighet"),
            smash_factor=safe_float("Slagfaktor"),
            launch_angle=safe_float("Slagvinkel"),
            launch_direction=safe_float("Slagretning"),
            spin_rate=safe_float("Skruhastighet"),
            spin_axis=safe_float("Skruakse"),
            carry_distance=safe_float("Carry-distanse"),
            total_distance=safe_float("Total avstand"),
            apex_height=safe_float("Toppunktshøyde"),
            total_deviation=safe_float("Total avviksavstand"),
        )
        shots.append(shot)

    return shots


async def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else None
    if not csv_path:
        # Finn CSV-filer i prosjektmappen
        csvs = list(Path(".").parent.glob("*.csv"))
        if csvs:
            csv_path = str(csvs[0])
        else:
            print("Bruk: python import_csv.py <sti-til-csv>")
            return

    print(f"Importerer: {csv_path}")
    shots = parse_garmin_csv(csv_path)
    print(f"Fant {len(shots)} slag\n")

    # Grupper etter klubb
    clubs: dict[str, list[ShotData]] = {}
    for s in shots:
        clubs.setdefault(s.club, []).append(s)

    for club, club_shots in clubs.items():
        print(f"--- {club} ({len(club_shots)} slag) ---")
        avgs = compute_averages(club_shots)
        print(f"  Carry snitt: {avgs.get('avg_carry', 'N/A')}m")
        print(f"  Ballhastighet snitt: {avgs.get('avg_ball_speed', 'N/A')} km/t")
        print(f"  Smash factor snitt: {avgs.get('avg_smash_factor', 'N/A')}")
        print(f"  Spin snitt: {avgs.get('avg_spin_rate', 'N/A')} rpm")
        patterns = detect_patterns(club_shots)
        print(f"  Mønstre:\n{patterns}\n")

    # Lagre i database
    settings.database_path = "golf_coach.db"
    await database.connect()

    session_id = f"import-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    for shot in shots:
        avgs = compute_averages([s for s in shots if s.club == shot.club])
        cat = categorize_shot(shot, avgs)
        await database.save_shot(session_id, shot, cat)

    print(f"Lagret {len(shots)} slag i database (session: {session_id})")

    # AI-coaching for hvert klubbsett
    if settings.anthropic_api_key:
        for club, club_shots in clubs.items():
            print(f"\n{'='*60}")
            print(f"AI Coaching — {club}")
            print(f"{'='*60}")
            async for chunk in golf_coach.summarize_session(club_shots, "middels"):
                print(chunk, end="", flush=True)
            print()

    await database.close()


asyncio.run(main())
