SKILL_LEVELS = {
    "nybegynner": {
        "label": "Nybegynner (hcp 25+)",
        "description": "Fokuser på grunnleggende: grip, stance, tempo og kontakt med ballen. "
        "Bruk enkelt språk uten teknisk sjargong. Gi én ting å jobbe med av gangen.",
        "reference": {
            "driver_carry": 140,  # meter
            "driver_ball_speed": 200,  # km/t
            "smash_factor": 1.30,
            "spin_7iron": 5500,
        },
    },
    "middels": {
        "label": "Middels (hcp 10-25)",
        "description": "Fokuser på konsistens og mønstergjenkjenning. "
        "Bruk datadrevne tips med referanse til tall. Gi 1-2 konkrete øvelser.",
        "reference": {
            "driver_carry": 190,
            "driver_ball_speed": 240,
            "smash_factor": 1.40,
            "spin_7iron": 6500,
        },
    },
    "avansert": {
        "label": "Avansert (hcp under 10)",
        "description": "Detaljert optimalisering med sammenligning mot tour-gjennomsnitt. "
        "Analyser spin axis, club path vs face angle, og angrepsvinkel. "
        "Gi presise justeringer og drills.",
        "reference": {
            "driver_carry": 240,
            "driver_ball_speed": 270,
            "smash_factor": 1.48,
            "spin_7iron": 7000,
        },
    },
}

SYSTEM_PROMPT = """Du er en erfaren PGA-golftrener som analyserer data fra en Garmin Approach R50 launch monitor. Du gir korte, praktiske tips på norsk.

Spillerens nivå: {skill_level_label}
{skill_level_description}

Referanseverdier for dette nivået:
- Driver carry: {ref_driver_carry}m
- Driver ballhastighet: {ref_driver_ball_speed} km/t
- Smash factor: {ref_smash_factor}
- 7-iron spin: {ref_spin_7iron} rpm

Regler:
- Maks 1-3 tips per analyse
- Fokuser på det viktigste først — én ting av gangen
- Tilpass språk og detaljeringsgrad til spillerens nivå
- Referer til konkrete tall fra slagdataene
- Gi øvelser eller drills spilleren kan prøve umiddelbart
- Sammenlign med spillerens gjennomsnitt når tilgjengelig
- Vær positiv og oppmuntrende, men ærlig
- Bruk metersystemet for avstander"""

SHOT_ANALYSIS_PROMPT = """Analyser dette siste slaget:

Klubb: {club}
Ballhastighet: {ball_speed} km/t
Launsjvinkel: {launch_angle}°
Spin rate: {spin_rate} rpm
Spin axis: {spin_axis}°
Klubbhodehastighet: {club_head_speed} km/t
Klubbflatvinkel (face): {club_face_angle}°
Klubbane (path): {club_path}°
Angrepsvinkel: {angle_of_attack}°
Smash factor: {smash_factor}
Carry: {carry_distance}m
Total avstand: {total_distance}m
Apeks høyde: {apex_height}m
Avvik: {total_deviation}m

Spillerens gjennomsnitt for denne klubben (siste 20 slag):
- Gjennomsnittlig carry: {avg_carry}m
- Gjennomsnittlig ballhastighet: {avg_ball_speed} km/t
- Gjennomsnittlig smash factor: {avg_smash_factor}

Gi en kort analyse av dette slaget og 1-3 praktiske tips for forbedring."""

SESSION_SUMMARY_PROMPT = """Oppsummer denne treningsøkten:

Klubb: {club}
Antall slag: {total_shots}
Gjennomsnittlig carry: {avg_carry}m
Gjennomsnittlig ballhastighet: {avg_ball_speed} km/t
Gjennomsnittlig smash factor: {avg_smash_factor}
Gjennomsnittlig spin rate: {avg_spin_rate} rpm
Beste slag (carry): {best_carry}m
Dårligste slag (carry): {worst_carry}m
Standardavvik carry: {std_carry}m

Mønster observert:
{patterns}

Sammenligning med forrige økt:
{comparison}

Gi en oppsummering av økten med:
1. Hva gikk bra
2. Hva kan forbedres
3. 2-3 spesifikke øvelser til neste treningsøkt"""


def build_system_prompt(skill_level: str) -> str:
    """Bygg system prompt tilpasset spillerens ferdighetsnivå."""
    level = SKILL_LEVELS.get(skill_level, SKILL_LEVELS["middels"])
    ref = level["reference"]
    return SYSTEM_PROMPT.format(
        skill_level_label=level["label"],
        skill_level_description=level["description"],
        ref_driver_carry=ref["driver_carry"],
        ref_driver_ball_speed=ref["driver_ball_speed"],
        ref_smash_factor=ref["smash_factor"],
        ref_spin_7iron=ref["spin_7iron"],
    )


def build_shot_prompt(shot_data: dict, averages: dict) -> str:
    """Bygg prompt for analyse av et enkelt slag."""
    return SHOT_ANALYSIS_PROMPT.format(
        club=shot_data.get("club", "Ukjent"),
        ball_speed=shot_data.get("ball_speed", "N/A"),
        launch_angle=shot_data.get("launch_angle", "N/A"),
        spin_rate=shot_data.get("spin_rate", "N/A"),
        spin_axis=shot_data.get("spin_axis", "N/A"),
        club_head_speed=shot_data.get("club_head_speed", "N/A"),
        club_face_angle=shot_data.get("club_face_angle", "N/A"),
        club_path=shot_data.get("club_path", "N/A"),
        angle_of_attack=shot_data.get("angle_of_attack", "N/A"),
        smash_factor=shot_data.get("smash_factor", "N/A"),
        carry_distance=shot_data.get("carry_distance", "N/A"),
        total_distance=shot_data.get("total_distance", "N/A"),
        apex_height=shot_data.get("apex_height", "N/A"),
        total_deviation=shot_data.get("total_deviation", "N/A"),
        avg_carry=averages.get("avg_carry", "N/A"),
        avg_ball_speed=averages.get("avg_ball_speed", "N/A"),
        avg_smash_factor=averages.get("avg_smash_factor", "N/A"),
    )


def build_session_prompt(summary: dict, patterns: str, comparison: str) -> str:
    """Bygg prompt for øktoppsummering."""
    return SESSION_SUMMARY_PROMPT.format(
        club=summary.get("club", "Ukjent"),
        total_shots=summary.get("total_shots", 0),
        avg_carry=summary.get("avg_carry", "N/A"),
        avg_ball_speed=summary.get("avg_ball_speed", "N/A"),
        avg_smash_factor=summary.get("avg_smash_factor", "N/A"),
        avg_spin_rate=summary.get("avg_spin_rate", "N/A"),
        best_carry=summary.get("best_carry", "N/A"),
        worst_carry=summary.get("worst_carry", "N/A"),
        std_carry=summary.get("std_carry", "N/A"),
        patterns=patterns,
        comparison=comparison,
    )
