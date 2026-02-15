from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from typing import Any, Iterable

CF_API = "https://codeforces.com/api"

def cf_get(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Calls Codeforces API and returns parsed JSON.
    """
    params = params or {}
    url = f"{CF_API}/{method}"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if data.get("status") != "OK":
        raise RuntimeError(f"Codeforces API FAILED: {data.get('comment')}")
    return data

def problem_url(contest_id: int | None, index: str | None) -> str:
    if contest_id is None or index is None:
        return ""
    return f"https://codeforces.com/problemset/problem/{contest_id}/{index}"

def tag_to_skills(cf_tags: Iterable[str]) -> list[str]:
    """
    Map CF tags -> your internal skill IDs.
    Start small; expand over time.
    """
    mapping = {
        "implementation": ["implementation"],
        "math": ["math"],
        "greedy": ["greedy_sorting", "math_greedy"],
        "sortings": ["greedy_sorting"],
        "two pointers": ["two_pointers"],
        "binary search": ["binary_search"],
        "data structures": ["data_structures"],
        "graphs": ["graphs"],
        "dfs and similar": ["dfs"],
        "trees": ["trees"],
        "strings": ["strings"],
        "prefix sums": ["prefix_sum"],  # (not a CF tag; you can keep this internal)
    }

    skills: list[str] = []
    for t in cf_tags:
        skills.extend(mapping.get(t, []))

    # de-duplicate while preserving order
    seen = set()
    out = []
    for s in skills:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out

def fetch_problems() -> list[dict[str, Any]]:
    """
    Fetches all problems via problemset.problems.
    """
    data = cf_get("problemset.problems")
    # result: { "problems": [...], "problemStatistics": [...] }
    return data["result"]["problems"]

def filter_problems(
    problems: list[dict[str, Any]],
    min_rating: int | None,
    max_rating: int | None,
    include_tags: set[str] | None,
    exclude_tags: set[str] | None,
) -> list[dict[str, Any]]:
    out = []
    for pr in problems:
        rating = pr.get("rating")
        tags = set(pr.get("tags", []))

        if rating is None:
            continue
        if min_rating is not None and rating < min_rating:
            continue
        if max_rating is not None and rating > max_rating:
            continue
        if include_tags and tags.isdisjoint(include_tags):
            continue
        if exclude_tags and not tags.isdisjoint(exclude_tags):
            continue

        out.append(pr)
    return out
