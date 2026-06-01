#!/usr/bin/env python3
"""
Quiz engine — Milestone 1: content loader + grading + attempt/review persistence.

Design notes:
  * Pure application logic. NO live AI here (AI explain/hint arrives in a later
    milestone and reuses mcp_coordinator).
  * The bank is loaded from the pre-generated static JSON (static/quiz_content/)
    into an immutable in-memory structure at startup.
  * Grading is by option "id" + "correct" flag — never by position.
  * DB models are imported LAZILY inside persistence functions so the loader and
    grading logic can be imported and unit-tested without a database connection.
  * QuizAttempt / QuizReview are ordinary app telemetry (like CourseProgress),
    deliberately separate from any research-participant data.
"""
import datetime
import hashlib
import json
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONTENT_DIR = os.path.join(ROOT, "static", "quiz_content")

REQUIRED_FIELDS = ("id", "category", "skill_tag", "prompt", "options",
                   "explanation", "source_reference")
VALID_CATEGORIES = {"detect", "understand", "remediate", "severity", "tooling"}

# Spaced-repetition (SM-2 "lite") tuning
INITIAL_EASE = 2.5
MIN_EASE = 1.3
MAX_EASE = 3.0
WRONG_RESURFACE_MINUTES = 10


# --------------------------------------------------------------------------
# Bank loading + validation
# --------------------------------------------------------------------------
class QuizBank:
    def __init__(self, questions):
        self._by_id = {q["id"]: q for q in questions}
        self._order = [q["id"] for q in questions]

    def __len__(self):
        return len(self._order)

    def get(self, question_id):
        return self._by_id.get(question_id)

    def all(self):
        return [self._by_id[i] for i in self._order]

    def by_category(self):
        out = {}
        for q in self.all():
            out.setdefault(q["category"], []).append(q)
        return out

    def by_skill(self):
        out = {}
        for q in self.all():
            out.setdefault(q["skill_tag"], []).append(q)
        return out


def validate_question(q):
    """Raise ValueError if a question is not safely gradable."""
    for f in REQUIRED_FIELDS:
        if not q.get(f):
            raise ValueError(f"{q.get('id', '<no id>')}: missing/empty field '{f}'")
    if q["category"] not in VALID_CATEGORIES:
        raise ValueError(f"{q['id']}: invalid category '{q['category']}'")
    opts = q["options"]
    if len(opts) < 2:
        raise ValueError(f"{q['id']}: needs at least 2 options")
    ids = [o["id"] for o in opts]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{q['id']}: duplicate option ids")
    texts = [o["text"] for o in opts]
    if len(texts) != len(set(texts)):
        raise ValueError(f"{q['id']}: duplicate option texts")
    correct = [o for o in opts if o.get("correct")]
    if len(correct) != 1:
        raise ValueError(f"{q['id']}: must have exactly one correct option (has {len(correct)})")


def load_bank(content_dir=None):
    """Load and validate every question file under content_dir into a QuizBank."""
    content_dir = content_dir or DEFAULT_CONTENT_DIR
    questions = []
    seen = set()
    for fn in sorted(os.listdir(content_dir)):
        if not fn.endswith(".json") or fn.startswith("_"):
            continue
        with open(os.path.join(content_dir, fn), encoding="utf-8") as f:
            data = json.load(f)
        for q in data:
            validate_question(q)
            if q["id"] in seen:
                raise ValueError(f"duplicate question id across files: {q['id']}")
            seen.add(q["id"])
            questions.append(q)
    if not questions:
        raise ValueError(f"no questions found in {content_dir}")
    return QuizBank(questions)


# --------------------------------------------------------------------------
# Grading (pure)
# --------------------------------------------------------------------------
def correct_option_id(question):
    for o in question["options"]:
        if o.get("correct"):
            return o["id"]
    raise ValueError(f"{question['id']}: no correct option")


def grade(question, chosen_option_id):
    """Grade a single answer. Returns the immediate (static) feedback payload."""
    valid_ids = {o["id"] for o in question["options"]}
    if chosen_option_id not in valid_ids:
        raise ValueError(f"{question['id']}: invalid option '{chosen_option_id}'")
    cid = correct_option_id(question)
    return {
        "question_id": question["id"],
        "is_correct": chosen_option_id == cid,
        "chosen_option": chosen_option_id,
        "correct_option_id": cid,
        "explanation": question["explanation"],
        "source_reference": question["source_reference"],
        "skill_tag": question["skill_tag"],
    }


# --------------------------------------------------------------------------
# Spaced repetition (SM-2 lite) — pure state transition
# --------------------------------------------------------------------------
def sm2_update(state, is_correct, now):
    """Given the prior review state, return the next state dict.

    state keys: consecutive_correct, ease, interval_days (None/0 for new).
    Returns: consecutive_correct, ease, interval_days, next_due_at, last_result.
    """
    cc = int(state.get("consecutive_correct") or 0)
    ease = float(state.get("ease") or INITIAL_EASE)
    interval = float(state.get("interval_days") or 0.0)

    if is_correct:
        cc += 1
        if cc == 1:
            interval = 1.0
        elif cc == 2:
            interval = 3.0
        else:
            interval = round(max(interval, 1.0) * ease, 2)
        ease = min(MAX_EASE, ease + 0.1)
        next_due = now + datetime.timedelta(days=interval)
    else:
        cc = 0
        interval = 0.0
        ease = max(MIN_EASE, ease - 0.2)
        next_due = now + datetime.timedelta(minutes=WRONG_RESURFACE_MINUTES)

    return {
        "consecutive_correct": cc,
        "ease": round(ease, 3),
        "interval_days": interval,
        "next_due_at": next_due,
        "last_result": bool(is_correct),
    }


# --------------------------------------------------------------------------
# Persistence (DB models imported lazily)
# --------------------------------------------------------------------------
def record_answer(session, bank, student_id, question_id, chosen_option,
                  time_ms=None, now=None):
    """Grade an answer, persist a QuizAttempt, and upsert the QuizReview.

    Returns the feedback payload from grade(). Caller is responsible for
    session.commit().
    """
    from database.models import QuizAttempt, QuizReview  # lazy: needs DB config

    now = now or datetime.datetime.utcnow()
    question = bank.get(question_id)
    if question is None:
        raise ValueError(f"unknown question_id: {question_id}")

    result = grade(question, chosen_option)

    session.add(QuizAttempt(
        student_id=student_id,
        question_id=question_id,
        template_id=question.get("generated_from_template"),
        skill_tag=question["skill_tag"],
        category=question["category"],
        severity=question.get("severity"),
        chosen_option=chosen_option,
        is_correct=result["is_correct"],
        time_ms=time_ms,
        created_at=now,
    ))

    review = (session.query(QuizReview)
              .filter_by(student_id=student_id, question_id=question_id)
              .one_or_none())
    prior = {} if review is None else {
        "consecutive_correct": review.consecutive_correct,
        "ease": review.ease,
        "interval_days": review.interval_days,
    }
    nxt = sm2_update(prior, result["is_correct"], now)
    if review is None:
        review = QuizReview(student_id=student_id, question_id=question_id,
                            skill_tag=question["skill_tag"])
        session.add(review)
    review.consecutive_correct = nxt["consecutive_correct"]
    review.ease = nxt["ease"]
    review.interval_days = nxt["interval_days"]
    review.next_due_at = nxt["next_due_at"]
    review.last_result = nxt["last_result"]
    review.updated_at = now

    result["next_due_at"] = nxt["next_due_at"].isoformat()
    return result


# --------------------------------------------------------------------------
# Adaptive selection (Milestone 2)
# --------------------------------------------------------------------------
DUE_FRACTION = 0.4               # at most this share of a quiz comes from due reviews
RECENT_WINDOW = 10               # attempts considered for the difficulty ramp
MIN_ATTEMPTS_FOR_ADVANCED = 8    # don't surface advanced until enough signal
RAMP_HIGH = 0.8                  # recent accuracy needed to unlock advanced
CATEGORIES = ["detect", "understand", "remediate", "severity", "tooling"]


def _stable_seed(*parts):
    h = hashlib.md5(":".join(str(p) for p in parts).encode("utf-8")).hexdigest()
    return int(h, 16) % (2 ** 32)


def _history(session, student_id):
    """Return (seen_qids, skill_accuracy, recent_accuracy, total_attempts)."""
    from database.models import QuizAttempt  # lazy
    rows = (session.query(QuizAttempt)
            .filter_by(student_id=student_id)
            .order_by(QuizAttempt.created_at.asc())
            .all())
    seen = set()
    skill = {}  # skill -> [correct, total]
    for a in rows:
        seen.add(a.question_id)
        s = skill.setdefault(a.skill_tag, [0, 0])
        s[1] += 1
        if a.is_correct:
            s[0] += 1
    total = len(rows)
    recent = rows[-RECENT_WINDOW:] if rows else []
    recent_acc = (sum(1 for a in recent if a.is_correct) / len(recent)) if recent else None
    skill_acc = {k: c / t for k, (c, t) in skill.items()}
    return seen, skill_acc, recent_acc, total


def skill_accuracy(session, student_id):
    """Public helper (used later by /progress): {skill_tag: accuracy_0_1}."""
    return _history(session, student_id)[1]


def allowed_difficulties(total_attempts, recent_acc):
    """Difficulty ramp gate. Beginner/intermediate always allowed; advanced
    unlocks only with enough signal AND strong recent accuracy."""
    if total_attempts < MIN_ATTEMPTS_FOR_ADVANCED or recent_acc is None:
        return {"beginner", "intermediate"}
    if recent_acc >= RAMP_HIGH:
        return {"beginner", "intermediate", "advanced"}
    return {"beginner", "intermediate"}


def _weight(q, skill_acc, seen):
    """Selection weight: weaker (or unseen) skills score higher; already-seen
    questions are strongly de-prioritised (spaced repetition handles resurfacing)."""
    acc = skill_acc.get(q["skill_tag"])
    base = 1.0 if acc is None else max(0.05, 1.0 - acc)  # unseen skill = top priority
    if q["id"] in seen:
        base *= 0.25
    return base


def select_quiz(session, bank, student_id, n=10, now=None, seed=0):
    """Adaptively select ~n questions for a learner.

    Order of construction:
      1. Surface DUE reviews (cap DUE_FRACTION of the quiz).
      2. Fill the rest with category balance (round-robin) + weak-skill weighting,
         gated by the difficulty ramp.
      3. Relax constraints only if a category/difficulty is exhausted.
    Deterministic for a given (student_id, seed). Returns full question dicts.
    """
    from database.models import QuizReview  # lazy
    now = now or datetime.datetime.utcnow()
    rng = random.Random(_stable_seed(student_id, seed))

    seen, skill_acc, recent_acc, total = _history(session, student_id)
    allowed = allowed_difficulties(total, recent_acc)

    chosen, chosen_set = [], set()

    # 1. due reviews (most overdue first), capped
    max_due = round(DUE_FRACTION * n)
    due_rows = (session.query(QuizReview)
                .filter(QuizReview.student_id == student_id,
                        QuizReview.next_due_at.isnot(None),
                        QuizReview.next_due_at <= now)
                .order_by(QuizReview.next_due_at.asc())
                .all())
    for r in due_rows:
        if len(chosen) >= max_due:
            break
        q = bank.get(r.question_id)
        if q and q["id"] not in chosen_set:
            chosen.append(q)
            chosen_set.add(q["id"])

    # 2. fill remaining with category balance + weak-skill weighting
    bycat = bank.by_category()
    cats = CATEGORIES[:]
    rng.shuffle(cats)
    guard = 0
    while len(chosen) < n and guard < n * 20:
        progressed = False
        for cat in cats:
            if len(chosen) >= n:
                break
            pool = [q for q in bycat.get(cat, [])
                    if q["id"] not in chosen_set and q["difficulty"] in allowed]
            if not pool:  # 3. relax difficulty for this category if needed
                pool = [q for q in bycat.get(cat, []) if q["id"] not in chosen_set]
            if not pool:
                continue
            weights = [_weight(q, skill_acc, seen) for q in pool]
            pick = rng.choices(pool, weights=weights, k=1)[0]
            chosen.append(pick)
            chosen_set.add(pick["id"])
            progressed = True
        guard += 1
        if not progressed:
            break

    # final fallback (tiny banks only)
    if len(chosen) < n:
        rest = [q for q in bank.all() if q["id"] not in chosen_set]
        rng.shuffle(rest)
        for q in rest[: n - len(chosen)]:
            chosen.append(q)
            chosen_set.add(q["id"])

    rng.shuffle(chosen)  # gentle: don't always lead with due reviews
    return chosen


if __name__ == "__main__":
    b = load_bank()
    cats = {k: len(v) for k, v in b.by_category().items()}
    print(f"Loaded and validated {len(b)} questions.")
    print("By category:", cats)
    print("Distinct skills:", len(b.by_skill()))
