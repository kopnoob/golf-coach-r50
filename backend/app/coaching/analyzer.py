from __future__ import annotations

import statistics

from app.garmin.models import ShotData


def compute_averages(shots: list[ShotData]) -> dict:
    """Beregn gjennomsnittsverdier for en liste med slag."""
    if not shots:
        return {}

    def safe_avg(values: list[float]) -> float | None:
        return round(statistics.mean(values), 1) if values else None

    carry = [s.carry_distance for s in shots if s.carry_distance is not None]
    ball_speed = [s.ball_speed for s in shots if s.ball_speed is not None]
    smash = [s.smash_factor for s in shots if s.smash_factor is not None]
    spin = [s.spin_rate for s in shots if s.spin_rate is not None]
    launch = [s.launch_angle for s in shots if s.launch_angle is not None]
    deviation = [s.total_deviation for s in shots if s.total_deviation is not None]

    return {
        "avg_carry": safe_avg(carry),
        "avg_ball_speed": safe_avg(ball_speed),
        "avg_smash_factor": safe_avg(smash),
        "avg_spin_rate": safe_avg(spin),
        "avg_launch_angle": safe_avg(launch),
        "avg_deviation": safe_avg(deviation),
        "std_carry": round(statistics.stdev(carry), 1) if len(carry) > 1 else None,
        "best_carry": round(max(carry), 1) if carry else None,
        "worst_carry": round(min(carry), 1) if carry else None,
        "total_shots": len(shots),
    }


def categorize_shot(shot: ShotData, averages: dict) -> str:
    """Kategoriser et slag som 'god', 'middels' eller 'dårlig'."""
    if not shot.smash_factor or not shot.carry_distance:
        return "middels"

    avg_carry = averages.get("avg_carry")
    avg_smash = averages.get("avg_smash_factor")

    if avg_carry is None or avg_smash is None:
        return "middels"

    carry_ratio = shot.carry_distance / avg_carry if avg_carry > 0 else 1
    smash_ratio = shot.smash_factor / avg_smash if avg_smash > 0 else 1

    score = (carry_ratio + smash_ratio) / 2

    if score >= 1.05:
        return "god"
    elif score <= 0.92:
        return "dårlig"
    return "middels"


def detect_patterns(shots: list[ShotData]) -> str:
    """Identifiser mønstre i en serie slag."""
    if len(shots) < 3:
        return "For få slag til å identifisere mønstre."

    patterns = []

    # Sjekk for konsekvent slice/hook (avvik)
    deviations = [s.total_deviation for s in shots if s.total_deviation is not None]
    if len(deviations) >= 3:
        avg_dev = statistics.mean(deviations)
        if avg_dev > 5:
            patterns.append(
                f"Konsekvent avvik til høyre (gjennomsnitt {avg_dev:.1f}m) — mulig slice."
            )
        elif avg_dev < -5:
            patterns.append(
                f"Konsekvent avvik til venstre (gjennomsnitt {avg_dev:.1f}m) — mulig hook."
            )

    # Sjekk for fallende smash factor (trøtthet)
    smash_values = [s.smash_factor for s in shots if s.smash_factor is not None]
    if len(smash_values) >= 5:
        first_half = statistics.mean(smash_values[: len(smash_values) // 2])
        second_half = statistics.mean(smash_values[len(smash_values) // 2 :])
        if first_half - second_half > 0.03:
            patterns.append(
                "Smash factor faller mot slutten av økten — mulig trøtthet eller konsentrasjon."
            )

    # Sjekk for høy spin
    spins = [s.spin_rate for s in shots if s.spin_rate is not None]
    if spins:
        avg_spin = statistics.mean(spins)
        if avg_spin > 8000:
            patterns.append(
                f"Høy gjennomsnittlig spin ({avg_spin:.0f} rpm) — kan redusere carry."
            )

    # Sjekk for inkonsistens
    carries = [s.carry_distance for s in shots if s.carry_distance is not None]
    if len(carries) > 2:
        cv = statistics.stdev(carries) / statistics.mean(carries) * 100
        if cv > 15:
            patterns.append(
                f"Stor variasjon i carry-avstand (CV={cv:.0f}%) — jobb med konsistens."
            )

    # Sjekk club face vs club path (for slice/hook diagnose)
    face_angles = [s.club_face_angle for s in shots if s.club_face_angle is not None]
    paths = [s.club_path for s in shots if s.club_path is not None]
    if face_angles and paths:
        avg_face = statistics.mean(face_angles)
        avg_path = statistics.mean(paths)
        face_to_path = avg_face - avg_path
        if face_to_path > 3:
            patterns.append(
                f"Klubbflaten er åpen relativt til banen ({face_to_path:.1f}°) — gir fade/slice."
            )
        elif face_to_path < -3:
            patterns.append(
                f"Klubbflaten er lukket relativt til banen ({face_to_path:.1f}°) — gir draw/hook."
            )

    if not patterns:
        patterns.append("Ingen tydelige negative mønstre funnet — god konsistens!")

    return "\n".join(f"- {p}" for p in patterns)


def compare_sessions(current: dict, previous: dict | None) -> str:
    """Sammenlign nåværende økt med forrige økt."""
    if not previous:
        return "Ingen tidligere økt å sammenligne med."

    comparisons = []

    for key, label in [
        ("avg_carry", "Carry-avstand"),
        ("avg_ball_speed", "Ballhastighet"),
        ("avg_smash_factor", "Smash factor"),
    ]:
        curr_val = current.get(key)
        prev_val = previous.get(key)
        if curr_val is not None and prev_val is not None:
            diff = curr_val - prev_val
            direction = "opp" if diff > 0 else "ned"
            comparisons.append(f"- {label}: {curr_val} ({direction} {abs(diff):.1f})")

    return "\n".join(comparisons) if comparisons else "Kan ikke sammenligne — manglende data."
