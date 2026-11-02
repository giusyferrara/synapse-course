"""
Proof that the AI budget actually refuses.

Run it with:  python tools/test_ai_budget.py

No database, no network, no API key. The clock is faked, so a day passes in a
line of code instead of a day.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Set before the module is imported: the limits are read once, at import.
os.environ.setdefault("AI_FREE_PER_MIN", "3")
os.environ.setdefault("AI_FREE_PER_DAY", "5")
os.environ.setdefault("AI_ANON_PER_MIN", "2")
os.environ.setdefault("AI_ANON_PER_DAY", "2")
os.environ.setdefault("AI_GLOBAL_PER_DAY", "9")

from web.ai_budget import AIBudget, Refused  # noqa: E402

PASS, FAIL = [], []


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- " + detail) if detail else ""))


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def forward(self, seconds):
        self.t += seconds


def budget_with(clock, tier="free"):
    b = AIBudget(clock=clock)
    b.tier_for = lambda user_id: ("anon" if not user_id else tier)
    return b


def refused(fn):
    """Returns the Refused raised, or None if the call was allowed."""
    try:
        fn()
        return None
    except Refused as r:
        return r


# --- a signed-in learner gets their tier's per-minute allowance -------------
clock = Clock()
b = budget_with(clock)
for i in range(3):
    check("free tier allows call %d of 3 in a minute" % (i + 1),
          refused(lambda: b.check(user_id=7)) is None)

r = refused(lambda: b.check(user_id=7))
check("free tier refuses the 4th call in the same minute", r is not None)
check("the per-minute refusal says to wait, not that the day is over",
      r is not None and "moment" in r.message.lower(), r.message if r else "")
check("the refusal carries a retry_after inside the minute",
      r is not None and 0 < r.retry_after <= 60, str(r.retry_after) if r else "")

# --- the minute window really slides ---------------------------------------
clock.forward(61)
check("a minute later the same learner is allowed again",
      refused(lambda: b.check(user_id=7)) is None)
clock.forward(61)
check("and again", refused(lambda: b.check(user_id=7)) is None)

# --- but the daily allowance still bites -----------------------------------
clock.forward(61)
r = refused(lambda: b.check(user_id=7))
check("the 6th call in a day is refused even with the minute clear", r is not None)
check("the daily refusal tells them the rest of SYNAPSE still works",
      r is not None and "quiz" in r.message.lower(), r.message if r else "")

# --- a day passes -----------------------------------------------------------
clock.forward(86401)
check("the next day the learner starts fresh",
      refused(lambda: b.check(user_id=7)) is None)

# --- one learner's limit is not another's ----------------------------------
clock = Clock()
b = budget_with(clock)
for _ in range(5):
    b.check(user_id=1)
    clock.forward(61)
check("learner 1 is now out for the day", refused(lambda: b.check(user_id=1)) is not None)
check("learner 2 is untouched by learner 1", refused(lambda: b.check(user_id=2)) is None)

# --- somebody with no account is counted by address, and gets less ---------
clock = Clock()
b = budget_with(clock)
check("anonymous call 1 allowed", refused(lambda: b.check(ip="1.2.3.4")) is None)
check("anonymous call 2 allowed", refused(lambda: b.check(ip="1.2.3.4")) is None)
r = refused(lambda: b.check(ip="1.2.3.4"))
check("anonymous call 3 refused", r is not None)
check("the anonymous refusal invites them to make an account",
      r is not None and "account" in r.message.lower(), r.message if r else "")
check("a different address has its own allowance",
      refused(lambda: b.check(ip="5.6.7.8")) is None)

# --- an unlimited tier is never counted ------------------------------------
clock = Clock()
b = budget_with(clock, tier="staff")
allowed = all(refused(lambda: b.check(user_id=99)) is None for _ in range(50))
check("a staff account is not rate limited", allowed)

# --- an unknown tier is treated as free, not as unlimited ------------------
clock = Clock()
b = budget_with(clock, tier="platinum-deluxe")
for _ in range(5):
    b.check(user_id=3)
    clock.forward(61)
check("an unrecognised tier gets the free allowance, not a free pass",
      refused(lambda: b.check(user_id=3)) is not None)

# --- the site ceiling holds even when every learner is inside theirs -------
clock = Clock()
b = budget_with(clock)
spent, hit_site = 0, None
for learner in range(1, 20):
    for _ in range(5):
        r = refused(lambda: b.check(user_id=learner))
        if r:
            hit_site = r
            break
        spent += 1
        clock.forward(61)
    if hit_site:
        break
check("the site ceiling stops the run", hit_site is not None)
check("it stops at the configured number, not later",
      spent == 9, "spent %d, ceiling 9" % spent)
check("the site refusal is marked as a site refusal",
      hit_site is not None and hit_site.scope == "site",
      hit_site.scope if hit_site else "")
check("the site refusal does not blame the learner",
      hit_site is not None and "whole" in hit_site.message.lower(),
      hit_site.message if hit_site else "")

# --- a refused call must not be charged for -------------------------------
clock = Clock()
b = budget_with(clock)
for _ in range(3):
    b.check(user_id=42)
for _ in range(10):
    refused(lambda: b.check(user_id=42))       # ten refusals in the same minute
clock.forward(61)
check("refusals do not eat the daily allowance",
      refused(lambda: b.check(user_id=42)) is None)

# --- the snapshot reports what was really spent ---------------------------
snap = b.snapshot()
check("snapshot counts only successful calls",
      snap["calls_today"] == 4, str(snap))

print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
if FAIL:
    for f in FAIL:
        print("  failed: " + f)
    sys.exit(1)
