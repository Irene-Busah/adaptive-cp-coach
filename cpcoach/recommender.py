# libraries
from __future__ import annotations
from datetime import datetime, timezone
from math import fabs


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    return datetime.fromisoformat(s)


def score_problem(
    problem_difficulty: int,
    target_difficulty: int,
    skill_states: dict[str, dict],
    problem_skills: list[str] 
) -> float:
    """
    Compute a recommendation score for a problem.

    The score favors:
      - Problems targeting low-mastery (weak) skills
      - Skills that are due for review
      - Difficulty close to the target difficulty

    Higher score means the problem is a better recommendation
    
    :param problem_difficulty: Difficulty rating of the problem
    :type problem_difficulty: int
    :param target_difficulty: Desired difficulty level for the student
    :type target_difficulty: int
    :param skill_states: Mapping of skill_id to its state (p_mastery, next_due_utc)
    :type skill_states: dict[str, dict]
    :param problem_skills: List of skill IDs required by the problem
    :type problem_skills: list[str]
    :return: Recommendation score (higher is better)
    :rtype: float
    """

    if not problem_skills:
        return -1e9
    
    now = datetime.now(timezone.utc)

    mastery_vals = []
    overdue_count = 0

    for sid in problem_skills:
        st = skill_states.get(sid)
        p = st["p_mastery"] if st else 0.2
        mastery_vals.append(p)

        due = parse_iso(st["next_due_utc"]) if st and st["next_due_utc"] else None
        if due and due <= now:
            overdue_count += 1
    
    weakness = sum(1.0 - p for p in mastery_vals) / len(mastery_vals)
    difficult_match = -fabs(problem_difficulty - target_difficulty)

    return 2.0 * weakness + 1.5 * overdue_count + 0.002 * difficult_match

