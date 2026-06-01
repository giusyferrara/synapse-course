#!/usr/bin/env python3
"""
Quiz AI helper — Milestone 3: on-demand "explain why" and "hint".

Reuses the existing AI pipeline (mcp_coordinator -> ClaudeClient). This module
holds the provider-agnostic logic so it is unit-testable without spending API
money: the actual model call is an injected `generate_fn(prompt) -> str`.

Cost & safety controls (requirement 2):
  * Per-question CACHE, content-addressed and SHARED across users. The
    explanation for a (question, chosen-option) is identical for everyone, so it
    is generated AT MOST ONCE and then served from cache forever. Repeated
    clicks cannot run up the bill.
  * Tight PER-USER RATE LIMIT on actual generations (cache hits are free and do
    not count). Sliding per-minute and per-day windows.
  * The STATIC correct answer + explanation are always returned as the
    authority; the AI text is supplementary and can never change the key.
  * HINT guardrail: if the model's hint leaks the correct option text, it is
    replaced with a safe generic nudge.
  * Fires ONLY when explicitly called by a handler (explain/hint button) —
    nothing here runs automatically.
"""
import datetime

from quiz.quiz_engine import correct_option_id

# Tight defaults — a single user cannot generate more than these MISSES.
DEFAULT_PER_MINUTE = 4
DEFAULT_PER_DAY = 30
MAX_TOKENS = 350  # short answers; bounds per-call cost

SAFE_HINT_FALLBACK = (
    "Trace the untrusted input: where does it enter, and where does it end up? "
    "The category of weakness usually follows from that data flow. You've got this."
)


class RateLimitError(Exception):
    """Raised when a learner exceeds the per-minute or per-day AI budget."""


def _opt_text(question, option_id):
    for o in question["options"]:
        if o["id"] == option_id:
            return o["text"]
    return "(no answer)"


def _code_block(question):
    cs = question.get("code_snippet")
    return f"\nCode:\n{cs}\n" if cs else "\n"


def build_explain_prompt(question, learner_choice):
    cid = correct_option_id(question)
    opts = "\n".join(f"{o['id']}. {o['text']}" for o in question["options"])
    return (
        "You are a kind, encouraging cybersecurity tutor for neurodivergent learners.\n"
        "The CORRECT answer below is FIXED and authoritative — you must NOT contradict, "
        "change, or cast doubt on it; only explain it.\n\n"
        f"Question: {question['prompt']}"
        f"{_code_block(question)}"
        f"Options:\n{opts}\n\n"
        f"Correct answer (authoritative): {cid}. {_opt_text(question, cid)}\n"
        f"Learner chose: {learner_choice}. {_opt_text(question, learner_choice)}\n\n"
        f"Reference explanation (ground truth — do not contradict or go beyond it): "
        f"{question['explanation']}\n"
        f"Source: {question['source_reference']}\n\n"
        "In 2-4 short, warm sentences, explain WHY the correct answer is correct and, "
        "if the learner chose differently, gently why their option does not fit. "
        "Reinforce the reference explanation. Do not introduce new facts. "
        "Do not change the correct answer."
    )


def build_hint_prompt(question):
    opts = "\n".join(f"{o['id']}. {o['text']}" for o in question["options"])
    return (
        "You are a kind cybersecurity tutor for neurodivergent learners giving a "
        "PRE-ANSWER hint. Do NOT reveal which option is correct and do NOT name the "
        "specific vulnerability or answer. Give ONE short, encouraging sentence that "
        "nudges the learner's thinking (e.g. what to look at: where does the data come "
        "from, where does it end up, what is missing?).\n\n"
        f"Question: {question['prompt']}"
        f"{_code_block(question)}"
        f"Options:\n{opts}\n\n"
        "Respond with only the hint sentence."
    )


class QuizAIService:
    def __init__(self, generate_fn, per_minute=DEFAULT_PER_MINUTE,
                 per_day=DEFAULT_PER_DAY, clock=None, cache=None):
        self._generate = generate_fn
        self.per_minute = per_minute
        self.per_day = per_day
        self._clock = clock or datetime.datetime.utcnow
        self._cache = cache if cache is not None else {}
        self._events = {}  # student_id -> [datetimes of actual generations]

    # -- rate limiting (counts ACTUAL generations only) --
    def _check_and_record(self, student_id):
        now = self._clock()
        ev = self._events.setdefault(student_id, [])
        ev[:] = [t for t in ev if (now - t).total_seconds() <= 86400]  # prune > 1 day
        minute = [t for t in ev if (now - t).total_seconds() <= 60]
        if len(minute) >= self.per_minute:
            raise RateLimitError("Too many AI requests this minute — please wait a moment.")
        if len(ev) >= self.per_day:
            raise RateLimitError("Daily AI help limit reached — the static explanations are always free.")
        ev.append(now)

    # -- explain (post-answer) --
    def explain(self, student_id, question, learner_choice):
        cid = correct_option_id(question)
        key = ("explain", question["id"], learner_choice)
        if key in self._cache:
            return {**self._cache[key], "cached": True}
        self._check_and_record(student_id)  # only on cache miss
        ai_text = (self._generate(build_explain_prompt(question, learner_choice)) or "").strip()
        payload = {
            "mode": "explain",
            "question_id": question["id"],
            "ai_text": ai_text,
            # STATIC authority — never derived from AI output:
            "correct_option_id": cid,
            "explanation": question["explanation"],
            "source_reference": question["source_reference"],
        }
        self._cache[key] = payload
        return {**payload, "cached": False}

    # -- hint (pre-answer) --
    def hint(self, student_id, question):
        key = ("hint", question["id"])
        if key in self._cache:
            return {**self._cache[key], "cached": True}
        self._check_and_record(student_id)
        ai_text = (self._generate(build_hint_prompt(question)) or "").strip()
        guarded = False
        correct_text = _opt_text(question, correct_option_id(question))
        if correct_text.lower() in ai_text.lower() or not ai_text:
            ai_text = SAFE_HINT_FALLBACK
            guarded = True
        payload = {"mode": "hint", "question_id": question["id"],
                   "ai_text": ai_text, "guarded": guarded}
        self._cache[key] = payload
        return {**payload, "cached": False}
