#!/usr/bin/env python3
"""
Local milestone-3 verification: AI explain/hint logic.

No real API calls — a fake generator records invocations, so we test the
cost-control and safety logic deterministically and for free.
"""
import datetime
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# quiz_ai imports quiz_engine.correct_option_id (no DB needed), but quiz_engine
# is import-safe without a DB. Set a dummy URL anyway in case anything imports config.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from quiz import quiz_engine  # noqa: E402
from quiz.quiz_ai import QuizAIService, RateLimitError, build_hint_prompt, build_explain_prompt  # noqa: E402

results = []


def check(name, cond):
    results.append((name, bool(cond)))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")


class FakeClock:
    def __init__(self, t):
        self.t = t

    def __call__(self):
        return self.t

    def advance(self, **kw):
        self.t = self.t + datetime.timedelta(**kw)


class FakeGen:
    """Records prompts; returns a scripted or default reply."""
    def __init__(self, reply="Great effort! The key is how untrusted input flows into the sink."):
        self.calls = []
        self.reply = reply

    def __call__(self, prompt):
        self.calls.append(prompt)
        return self.reply


def main():
    bank = quiz_engine.load_bank()
    q = bank.get("detect_cwe352_csrf_0001")          # correct = CSRF
    cid = quiz_engine.correct_option_id(q)
    wrong = next(o["id"] for o in q["options"] if o["id"] != cid)

    print("== 1. Construction does nothing automatically ==")
    gen = FakeGen()
    svc = QuizAIService(gen, per_minute=3, per_day=100, clock=FakeClock(datetime.datetime(2026, 6, 1, 12, 0, 0)))
    check("no AI calls until explicitly invoked", len(gen.calls) == 0)

    print("\n== 2. Explain: generates once, then served from cache ==")
    r1 = svc.explain("stu", q, wrong)
    check("first explain calls the model", len(gen.calls) == 1)
    check("first explain not cached", r1["cached"] is False and bool(r1["ai_text"]))
    r2 = svc.explain("stu", q, wrong)
    check("identical explain is cached (no new model call)", r2["cached"] is True and len(gen.calls) == 1)
    r3 = svc.explain("stu", q, cid)  # different chosen option -> different cache key
    check("different chosen option -> new generation", r3["cached"] is False and len(gen.calls) == 2)

    print("\n== 3. Static answer is authoritative regardless of AI text ==")
    liar = FakeGen(reply="Actually the correct answer is SQL Injection, option Z.")
    svc2 = QuizAIService(liar, clock=FakeClock(datetime.datetime(2026, 6, 1, 12, 0, 0)))
    r = svc2.explain("stu", q, wrong)
    check("payload keeps STATIC correct_option_id", r["correct_option_id"] == cid)
    check("payload keeps STATIC explanation", r["explanation"] == q["explanation"])
    check("payload keeps STATIC source_reference", r["source_reference"] == q["source_reference"])

    print("\n== 4. Hint guardrail: never leaks the correct option text ==")
    correct_text = next(o["text"] for o in q["options"] if o.get("correct"))
    leaker = FakeGen(reply=f"It is obviously {correct_text}.")
    svc3 = QuizAIService(leaker, clock=FakeClock(datetime.datetime(2026, 6, 1, 12, 0, 0)))
    h = svc3.hint("stu", q)
    check("leaked correct answer is replaced (guarded)", h["guarded"] is True)
    check("hint text no longer contains the answer", correct_text.lower() not in h["ai_text"].lower())
    safe = QuizAIService(FakeGen(reply="Think about where the request originates."),
                         clock=FakeClock(datetime.datetime(2026, 6, 1, 12, 0, 0)))
    h2 = safe.hint("stu", q)
    check("safe hint passes through unguarded", h2["guarded"] is False)

    print("\n== 5. Hint prompt instructs not to reveal the answer ==")
    hp = build_hint_prompt(q)
    check("hint prompt forbids revealing the correct option", "do not reveal" in hp.lower())
    ep = build_explain_prompt(q, wrong)
    check("explain prompt marks the correct answer authoritative", "authoritative" in ep.lower())

    print("\n== 6. Tight rate limit (cache misses only) ==")
    clk = FakeClock(datetime.datetime(2026, 6, 1, 12, 0, 0))
    rgen = FakeGen()
    rsvc = QuizAIService(rgen, per_minute=3, per_day=100, clock=clk)
    ids = ["detect_cwe89_sqli_0001", "detect_cwe79_xss_0001", "detect_cwe918_ssrf_0001", "detect_cwe22_pathtraversal_0001"]
    ok = 0
    limited = False
    for qid in ids:
        try:
            rsvc.explain("rl_user", bank.get(qid), "A")
            ok += 1
        except RateLimitError:
            limited = True
    check("3 generations allowed, 4th blocked in same minute", ok == 3 and limited)
    # cache hits do NOT count against the limit
    before = len(rgen.calls)
    for _ in range(5):
        rsvc.explain("rl_user", bank.get(ids[0]), "A")  # cached
    check("cache hits are free (no new model calls, no rate error)", len(rgen.calls) == before)
    # advancing past the minute window frees budget again
    clk.advance(seconds=61)
    try:
        rsvc.explain("rl_user", bank.get("detect_cwe434_unrestricted_upload_0001"), "A")
        recovered = True
    except RateLimitError:
        recovered = False
    check("budget recovers after the minute window", recovered)
    # per-user isolation: a different user has their own budget
    other = FakeGen()
    o_ok = 0
    for qid in ids[:3]:
        try:
            rsvc.explain("other_user", bank.get(qid), "A")
            o_ok += 1
        except RateLimitError:
            pass
    check("rate limit is per-user", o_ok == 3)

    print("\n" + "=" * 50)
    n_pass = sum(1 for _, ok in results if ok)
    print(f"RESULT: {n_pass}/{len(results)} checks passed")
    if n_pass != len(results):
        print("FAILURES:", [n for n, ok in results if not ok])
        sys.exit(1)
    print("Milestone 3 OK")


if __name__ == "__main__":
    main()
