from __future__ import annotations
import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "cpcoach.db"

def connect(db_path: Path = DEFAULT_DB) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS skills (
            skill_id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS problems (
            problem_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT,
            difficulty INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS problem_skills (
            problem_id TEXT NOT NULL,
            skill_id TEXT NOT NULL,
            PRIMARY KEY (problem_id, skill_id),
            FOREIGN KEY (problem_id) REFERENCES problems(problem_id) ON DELETE CASCADE,
            FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS attempts (
            attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id TEXT NOT NULL,
            ts_utc TEXT NOT NULL,              -- ISO string
            verdict TEXT NOT NULL,             -- AC/WA/TLE/RE/SKIP
            time_spent_sec INTEGER NOT NULL,
            tries INTEGER NOT NULL DEFAULT 1,
            hints_used INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (problem_id) REFERENCES problems(problem_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS skill_state (
            skill_id TEXT PRIMARY KEY,
            p_mastery REAL NOT NULL,           -- 0..1
            last_seen_utc TEXT,
            next_due_utc TEXT,
            attempts INTEGER NOT NULL DEFAULT 0,
            corrects INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_attempts_problem ON attempts(problem_id);
        """
    )
    conn.commit()
