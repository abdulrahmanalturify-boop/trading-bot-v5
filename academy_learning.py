"""Learner activity and dashboard calculations. No market calls or shared user state."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

ACADEMY_REVISION = "2026-10-14.2"


def today():
    return datetime.now(ZoneInfo("Asia/Riyadh")).date()


def clean(raw, courses, now=None):
    """Bound browser data and ignore invalid IDs, dates, scores and lesson numbers."""
    now = now or today()
    catalog = {c["id"]: c for c in courses}
    valid = {f"{c['id']}:{i}" for c in courses for i in range(len(c["sections"]))}
    raw = raw if isinstance(raw, dict) else {}
    lessons = raw.get("lessons", [])
    lessons = sorted({x for x in lessons if isinstance(x, str) and x in valid}) if isinstance(lessons, list) else []
    result = {"lessons": lessons, "activity": {}, "quizzes": {}, "goal": 5, "last": None}
    if raw.get("goal") in (3, 5, 10) and type(raw.get("goal")) is int:
        result["goal"] = raw["goal"]
    if isinstance(raw.get("last"), str) and raw["last"] in catalog:
        result["last"] = raw["last"]
    activity = raw.get("activity", {})
    if isinstance(activity, dict):
        for day, value in activity.items():
            try:
                parsed = date.fromisoformat(day)
            except (ValueError, TypeError):
                continue
            if not 0 <= (now - parsed).days <= 90 or not isinstance(value, dict):
                continue
            reached = value.get("lessons", [])
            reached = sorted({x for x in reached if isinstance(x, str) and x in valid}) if isinstance(reached, list) else []
            result["activity"][day] = {"lessons": reached, "challenge": value.get("challenge") is True}
    quizzes = raw.get("quizzes", {})
    if isinstance(quizzes, dict):
        for cid, value in quizzes.items():
            if cid in catalog and isinstance(value, dict):
                score, total = value.get("score"), len(catalog[cid]["quiz"])
                if type(score) is int and 0 <= score <= total:
                    result["quizzes"][cid] = {"score": score, "total": total}
    return result


def visit(meta, cid):
    meta["last"] = cid


def lesson(meta, cid, step, now=None):
    """Count the first completion of a lesson; reviewing it does not inflate activity."""
    token = f"{cid}:{step}"
    visit(meta, cid)
    if token not in meta["lessons"]:
        meta["lessons"].append(token)
        day = (now or today()).isoformat()
        row = meta["activity"].setdefault(day, {"lessons": [], "challenge": False})
        row["lessons"].append(token)


def challenge(meta, now=None):
    day = (now or today()).isoformat()
    meta["activity"].setdefault(day, {"lessons": [], "challenge": False})["challenge"] = True


def stats(meta, courses, completed, steps, now=None):
    now = now or today()
    known = {c["id"] for c in courses}
    done = set(completed) & known
    learned = set(meta["lessons"])
    # Old course progress contributes to all-time totals, never to a fabricated activity date.
    for c in courses:
        count = len(c["sections"]) if c["id"] in done else min(max(steps.get(c["id"], 0), 0), len(c["sections"]))
        learned.update(f"{c['id']}:{i}" for i in range(count))
    days = [now - timedelta(days=i) for i in range(6, -1, -1)]
    activity = [{"day": d, **meta["activity"].get(d.isoformat(), {"lessons": [], "challenge": False})} for d in days]
    week_start = now - timedelta(days=now.weekday())
    weekly = sum(len(row["lessons"]) for day, row in meta["activity"].items() if week_start <= date.fromisoformat(day) <= now)
    active = {date.fromisoformat(day) for day, row in meta["activity"].items() if row["lessons"] or row["challenge"]}
    cursor = now if now in active else now - timedelta(days=1)
    streak = 0
    while cursor in active:
        streak += 1
        cursor -= timedelta(days=1)
    scores = list(meta["quizzes"].values())
    accuracy = round(sum(q["score"] for q in scores) / sum(q["total"] for q in scores) * 100) if scores else None
    return {"done": done, "lessons": len(learned), "total_lessons": sum(len(c["sections"]) for c in courses),
            "weekly": weekly, "activity": activity, "streak": streak, "accuracy": accuracy,
            "quiz_count": len(scores), "week_start": week_start}


def daily_question(courses, now=None):
    """A deterministic daily beginner question, shared across languages and refreshes."""
    now = now or today()
    choices = [(c, i, q) for c in courses if c["level"][0] == "Beginner" for i, q in enumerate(c["quiz"])]
    return choices[now.toordinal() % len(choices)] if choices else None
