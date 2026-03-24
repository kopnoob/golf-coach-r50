from __future__ import annotations

"""SQL-skjema og database-modeller for Golf Coach R50."""

SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL DEFAULT 'Spiller',
    skill_level TEXT NOT NULL DEFAULT 'middels',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    player_id INTEGER NOT NULL DEFAULT 1,
    date TIMESTAMP NOT NULL,
    club TEXT NOT NULL,
    total_shots INTEGER NOT NULL DEFAULT 0,
    avg_carry_distance REAL,
    avg_ball_speed REAL,
    avg_smash_factor REAL,
    avg_spin_rate REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(id)
);

CREATE TABLE IF NOT EXISTS shots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP,
    club TEXT,
    ball_speed REAL,
    launch_angle REAL,
    launch_direction REAL,
    spin_rate REAL,
    spin_axis REAL,
    club_head_speed REAL,
    club_face_angle REAL,
    club_path REAL,
    angle_of_attack REAL,
    smash_factor REAL,
    carry_distance REAL,
    total_distance REAL,
    apex_height REAL,
    total_deviation REAL,
    category TEXT DEFAULT 'middels',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS coaching_tips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    shot_id INTEGER,
    tip_type TEXT NOT NULL,
    content TEXT NOT NULL,
    skill_level TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    FOREIGN KEY (shot_id) REFERENCES shots(id)
);
"""
