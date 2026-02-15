from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

import typer
from rich import print
from rich.table import Table

from .db import connect, init_db, DEFAULT_DB
from .bkt import bkt_update
from .recommender import score_problem
from .cf_sync import fetch_problems, filter_problems, problem_url, tag_to_skills


app = typer.Typer(add_completion=False)

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def schedule_next_due(p_mastery: float, correct: bool) -> str:
    now = datetime.now(timezone.utc)
    if not correct:
        return (now + timedelta(days=1)).isoformat()
    if p_mastery > 0.85:
        return (now + timedelta(days=14)).isoformat()
    if p_mastery > 0.70:
        return (now + timedelta(days=7)).isoformat()
    return (now + timedelta(days=3)).isoformat()

@app.command()
def init(db: Path = typer.Option(DEFAULT_DB, help="Path to SQLite DB")):
    conn = connect(db)
    init_db(conn)
    print(f"[green]Initialized[/green] {db}")

@app.command()
def load_data(
    problems: Path = typer.Option(Path(__file__).parent / "data" / "problems.json"),
    skills: Path = typer.Option(Path(__file__).parent / "data" / "skills.json"),
    db: Path = typer.Option(DEFAULT_DB),
):
    conn = connect(db)
    init_db(conn)

    skills_data = json.loads(skills.read_text())
    probs_data = json.loads(problems.read_text())

    with conn:
        for s in skills_data:
            conn.execute(
                "INSERT OR REPLACE INTO skills(skill_id, name) VALUES (?, ?)",
                (s["id"], s["name"]),
            )
            # ensure skill_state exists
            conn.execute(
                "INSERT OR IGNORE INTO skill_state(skill_id, p_mastery) VALUES (?, ?)",
                (s["id"], 0.2),
            )

        for p in probs_data:
            conn.execute(
                "INSERT OR REPLACE INTO problems(problem_id, title, url, difficulty) VALUES (?, ?, ?, ?)",
                (p["id"], p["title"], p.get("url", ""), int(p["difficulty"])),
            )
            conn.execute("DELETE FROM problem_skills WHERE problem_id = ?", (p["id"],))
            for sid in p.get("skills", []):
                conn.execute(
                    "INSERT OR IGNORE INTO problem_skills(problem_id, skill_id) VALUES (?, ?)",
                    (p["id"], sid),
                )

    print(f"[green]Loaded[/green] {len(skills_data)} skills and {len(probs_data)} problems into {db}")

@app.command()
def attempt(
    problem_id: str = typer.Argument(...),
    verdict: str = typer.Argument(..., help="AC/WA/TLE/RE/SKIP"),
    time_spent_sec: int = typer.Option(0, help="Time spent in seconds"),
    tries: int = typer.Option(1),
    hints_used: int = typer.Option(0),
    db: Path = typer.Option(DEFAULT_DB),
):
    verdict = verdict.upper()
    if verdict not in {"AC", "WA", "TLE", "RE", "SKIP"}:
        raise typer.BadParameter("verdict must be one of AC/WA/TLE/RE/SKIP")

    conn = connect(db)
    init_db(conn)

    row = conn.execute("SELECT 1 FROM problems WHERE problem_id = ?", (problem_id,)).fetchone()
    if not row:
        print(f"[red]Unknown problem_id[/red] {problem_id}. Load problems first.")
        raise typer.Exit(code=1)

    correct = (verdict == "AC")

    # record attempt
    with conn:
        conn.execute(
            """
            INSERT INTO attempts(problem_id, ts_utc, verdict, time_spent_sec, tries, hints_used)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (problem_id, now_iso(), verdict, time_spent_sec, tries, hints_used),
        )

    # get skills for the problem
    skills = [r["skill_id"] for r in conn.execute(
        "SELECT skill_id FROM problem_skills WHERE problem_id = ?", (problem_id,)
    ).fetchall()]

    # update each skill state with BKT
    with conn:
        for sid in skills:
            st = conn.execute(
                "SELECT p_mastery, attempts, corrects FROM skill_state WHERE skill_id = ?",
                (sid,)
            ).fetchone()
            p_old = float(st["p_mastery"]) if st else 0.2
            p_new = bkt_update(p_old, correct)

            attempts = (st["attempts"] if st else 0) + 1
            corrects = (st["corrects"] if st else 0) + (1 if correct else 0)

            next_due = schedule_next_due(p_new, correct)

            conn.execute(
                """
                INSERT INTO skill_state(skill_id, p_mastery, last_seen_utc, next_due_utc, attempts, corrects)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(skill_id) DO UPDATE SET
                  p_mastery=excluded.p_mastery,
                  last_seen_utc=excluded.last_seen_utc,
                  next_due_utc=excluded.next_due_utc,
                  attempts=excluded.attempts,
                  corrects=excluded.corrects
                """,
                (sid, p_new, now_iso(), next_due, attempts, corrects)
            )

    print(f"[green]Logged[/green] {verdict} for {problem_id}. Updated {len(skills)} skills.")

@app.command()
def skills(db: Path = typer.Option(DEFAULT_DB)):
    conn = connect(db)
    init_db(conn)

    rows = conn.execute(
        """
        SELECT s.skill_id, s.name, ss.p_mastery, ss.attempts, ss.corrects, ss.next_due_utc
        FROM skills s
        JOIN skill_state ss ON ss.skill_id = s.skill_id
        ORDER BY ss.p_mastery ASC, ss.attempts DESC
        """
    ).fetchall()

    table = Table(title="Skill Mastery (low → high)")
    table.add_column("Skill")
    table.add_column("P(mastered)", justify="right")
    table.add_column("Attempts", justify="right")
    table.add_column("Correct", justify="right")
    table.add_column("Next due", justify="left")

    for r in rows:
        table.add_row(
            f"{r['skill_id']} ({r['name']})",
            f"{float(r['p_mastery']):.2f}",
            str(r["attempts"]),
            str(r["corrects"]),
            r["next_due_utc"] or "-"
        )

    print(table)

@app.command()
def next(
    target_difficulty: int = typer.Option(900, help="Desired difficulty level"),
    db: Path = typer.Option(DEFAULT_DB),
):
    conn = connect(db)
    init_db(conn)

    # build skill state map
    ss_rows = conn.execute("SELECT * FROM skill_state").fetchall()
    skill_states = {r["skill_id"]: dict(r) for r in ss_rows}

    # avoid recently attempted problems
    recent = conn.execute(
        """
        SELECT problem_id, MAX(ts_utc) AS last_ts
        FROM attempts
        GROUP BY problem_id
        """
    ).fetchall()
    last_attempt = {r["problem_id"]: r["last_ts"] for r in recent}

    # fetch all problems + their skills
    probs = conn.execute("SELECT * FROM problems").fetchall()

    best = None
    best_score = -1e18

    for p in probs:
        pid = p["problem_id"]
        skills = [r["skill_id"] for r in conn.execute(
            "SELECT skill_id FROM problem_skills WHERE problem_id = ?", (pid,)
        ).fetchall()]

        s = score_problem(
            int(p["difficulty"]),
            target_difficulty,
            skill_states,
            skills
        )

        # small penalty if already attempted before
        if pid in last_attempt:
            s -= 0.5

        if s > best_score:
            best_score = s
            best = (p, skills)

    if not best:
        print("[red]No problems loaded.[/red] Run: cp load-data")
        raise typer.Exit(code=1)

    p, skills = best
    print("[bold]Next recommended:[/bold]")
    print(f"- ID: {p['problem_id']}")
    print(f"- Title: {p['title']}")
    print(f"- Difficulty: {p['difficulty']}")
    print(f"- Skills: {', '.join(skills) if skills else '(none)'}")
    if p["url"]:
        print(f"- URL: {p['url']}")
        


@app.command()
def sync_cf_problems(
    min_rating: int = typer.Option(800),
    max_rating: int = typer.Option(1200),
    include_tags: str = typer.Option("", help="Comma-separated CF tags to include (optional)"),
    exclude_tags: str = typer.Option("", help="Comma-separated CF tags to exclude (optional)"),
    limit: int = typer.Option(300, help="Max problems to import"),
    db: Path = typer.Option(DEFAULT_DB),
):
    """
    Fetch Codeforces problemset and import problems into local DB.
    """
    conn = connect(db)
    init_db(conn)

    inc = {t.strip() for t in include_tags.split(",") if t.strip()} or None
    exc = {t.strip() for t in exclude_tags.split(",") if t.strip()} or None

    # One API call; CF limits API to 1 request per 2 seconds. :contentReference[oaicite:1]{index=1}
    problems = fetch_problems()
    chosen = filter_problems(problems, min_rating, max_rating, inc, exc)
    chosen = chosen[:limit]

    inserted = 0
    with conn:
        for pr in chosen:
            contest_id = pr.get("contestId")
            index = pr.get("index")
            pid = f"cf-{contest_id}-{index}" if contest_id and index else f"cf-{pr.get('name','').strip()}"
            title = pr.get("name", "Untitled")
            difficulty = int(pr.get("rating", 0))
            url = problem_url(contest_id, index)

            conn.execute(
                "INSERT OR REPLACE INTO problems(problem_id, title, url, difficulty) VALUES (?, ?, ?, ?)",
                (pid, title, url, difficulty),
            )
            conn.execute("DELETE FROM problem_skills WHERE problem_id = ?", (pid,))

            skills = tag_to_skills(pr.get("tags", []))
            for sid in skills:
                # ensure skill exists + has skill_state
                conn.execute(
                    "INSERT OR IGNORE INTO skills(skill_id, name) VALUES (?, ?)",
                    (sid, sid.replace("_", " ").title()),
                )
                conn.execute(
                    "INSERT OR IGNORE INTO skill_state(skill_id, p_mastery) VALUES (?, ?)",
                    (sid, 0.2),
                )
                conn.execute(
                    "INSERT OR IGNORE INTO problem_skills(problem_id, skill_id) VALUES (?, ?)",
                    (pid, sid),
                )

            inserted += 1

    print(f"[green]Imported[/green] {inserted} Codeforces problems into {db}")



if __name__ == "__main__":
    app()

