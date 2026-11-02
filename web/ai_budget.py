"""
A ceiling on what the AI can cost.

Until now /api/course/chat would call three models for every message a learner
sent, with no limit of any kind. One person holding down the send key, or one
script, could run the bill up as far as they liked. That is the only part of
SYNAPSE that can lose money on its own, and it is also the reason a school
cannot be quoted a price: nobody signs a licence for unlimited AI.

What this does
--------------
Two sliding windows per learner, one per minute and one per day, plus a daily
ceiling for the whole site. A request is allowed or it is not, and the answer
comes back with a sentence a learner can read.

The shape is lifted from quiz/quiz_ai.py, which has had exactly this limiter
since the quiz shipped. The differences: the tier comes from the database, the
numbers come from the environment, and there is a global ceiling underneath the
per-learner one.

Tiers
-----
users.subscription_tier already exists and already defaults to 'free', so
nothing needs migrating. It was being read at login and then ignored. Anyone
with no account at all is counted by IP address and gets the smallest budget.

The numbers below are a SAFETY NET, not a price. They are set high enough that
a learner working hard all day never meets them, and low enough that a runaway
cannot cost more than a known amount. When the pricing is decided, change the
environment variables and the product changes with them. No code edit, no
deploy.

Known limits, stated rather than hidden
---------------------------------------
* The counters live in memory, so a restart forgives everybody. That is the
  same trade quiz_ai makes. It bounds the damage from a runaway, which is the
  job; it is not an accounting record.
* If the app is ever run as more than one worker process, each worker keeps its
  own counters and the real limit is multiplied by the number of workers.
* Counting messages is a proxy for counting money. It is a good proxy here
  because every message costs about the same, and it is far simpler than
  metering tokens.
"""
import os
import time
from collections import defaultdict

# How long a learner's tier is trusted before it is looked up again. A tier
# changes when somebody pays, so minutes of staleness are fine and a database
# round trip on every chat message is not.
TIER_CACHE_SECONDS = 300

DAY = 86400
MINUTE = 60


def _n(name, fallback):
    """Read a limit from the environment, falling back to the default."""
    try:
        return int(os.getenv(name, ""))
    except ValueError:
        return fallback


# Per learner. 'anon' is anybody without an account, counted by IP.
TIERS = {
    "anon":   (_n("AI_ANON_PER_MIN", 4),   _n("AI_ANON_PER_DAY", 10)),
    "free":   (_n("AI_FREE_PER_MIN", 8),   _n("AI_FREE_PER_DAY", 80)),
    "pro":    (_n("AI_PRO_PER_MIN", 15),   _n("AI_PRO_PER_DAY", 400)),
    "school": (_n("AI_SCHOOL_PER_MIN", 20), _n("AI_SCHOOL_PER_DAY", 600)),
}

# A tier that is allowed through without counting. Useful for her own account
# and for a demonstration, and the only way to switch the net off.
UNLIMITED = {"staff", "unlimited", "owner"}

# The whole site, per day. Per-learner limits do not bound the bill on their
# own: a hundred free accounts are a hundred free budgets. This is the number
# that decides the worst case.
GLOBAL_PER_DAY = _n("AI_GLOBAL_PER_DAY", 2000)

# Everybody without an account, together, per day. The tutor is open on /try
# with no sign-up, and an address is cheap to change, so ten a day per address
# does not bound what strangers can spend. This does, and it is kept well
# under the site ceiling so that a crowd on the public demo can never use up
# the questions of the people who made an account.
ANON_GLOBAL_PER_DAY = _n("AI_ANON_GLOBAL_PER_DAY", 300)

# Anything not recognised is treated as the free tier rather than waved
# through. An unknown tier is far more likely to be a typo than a gift.
DEFAULT_TIER = "free"


class Refused(Exception):
    """Raised when a learner has spent their budget.

    `message` is written to be read by a learner, not by a developer.
    `retry_after` is seconds, for the HTTP header of the same name.
    """

    def __init__(self, message, retry_after=None, scope="user"):
        super().__init__(message)
        self.message = message
        self.retry_after = retry_after
        self.scope = scope


class AIBudget:
    def __init__(self, clock=None):
        self._clock = clock or time.monotonic
        self._events = defaultdict(list)   # key -> [timestamps of real calls]
        self._global = []                  # timestamps, whole site
        self._anon = []                    # timestamps, everybody without an account
        self._tiers = {}                   # user_id -> (tier, looked up at)

    # ---------------------------------------------------------------- tier

    def tier_for(self, user_id):
        """The learner's tier, from the database, cached for a few minutes."""
        if not user_id:
            return "anon"

        now = self._clock()
        hit = self._tiers.get(user_id)
        if hit and now - hit[1] < TIER_CACHE_SECONDS:
            return hit[0]

        tier = DEFAULT_TIER
        try:
            # Imported here rather than at the top so that a missing or
            # unreachable database cannot stop this module loading, and so the
            # limiter can be tested without one.
            from sqlalchemy import text
            from database.config import SessionLocal

            with SessionLocal() as db:
                row = db.execute(
                    text("SELECT subscription_tier FROM users WHERE id = :id"),
                    {"id": user_id},
                ).fetchone()
            if row and row[0]:
                tier = str(row[0]).strip().lower()
        except Exception as e:
            # The database being unreachable must not open the taps, and it
            # must not take the chat down either. Fall back to the smallest
            # paid-for-nothing budget and carry on.
            print(f"AI budget: could not read tier for user {user_id} ({e})", flush=True)

        self._tiers[user_id] = (tier, now)
        return tier

    # --------------------------------------------------------------- spend

    def check(self, user_id=None, ip=None, tier=None):
        """Allow one AI call, or raise Refused.

        Call this immediately before the model call, never before the work that
        might fail for another reason. A request that never reaches a model
        must not be charged for one.
        """
        tier = (tier or self.tier_for(user_id)).lower()
        if tier in UNLIMITED:
            return tier

        per_min, per_day = TIERS.get(tier, TIERS[DEFAULT_TIER])
        key = f"u:{user_id}" if user_id else f"ip:{ip or 'unknown'}"
        now = self._clock()

        # The site ceiling is checked first. If the site is out, telling one
        # learner they personally have messages left would be a lie.
        self._global[:] = [t for t in self._global if now - t <= DAY]
        if len(self._global) >= GLOBAL_PER_DAY:
            raise Refused(
                "The tutor has reached its limit for today across the whole "
                "site. It comes back tomorrow. Everything else on SYNAPSE "
                "keeps working.",
                retry_after=DAY - int(now - self._global[0]),
                scope="site",
            )

        if tier == "anon":
            self._anon[:] = [t for t in self._anon if now - t <= DAY]
            if len(self._anon) >= ANON_GLOBAL_PER_DAY:
                raise Refused(
                    "Lots of people asked questions today, so the free ones "
                    "without an account have run out. Make a free account to "
                    "keep going. The lessons still work.",
                    retry_after=DAY - int(now - self._anon[0]),
                    scope="anon",
                )

        seen = self._events[key]
        seen[:] = [t for t in seen if now - t <= DAY]

        # The day is checked before the minute, and the order matters. Someone
        # who has spent the whole day has also, usually, spent the minute. Told
        # to "wait a moment" they would wait, try again, and only then find out
        # the day was gone. The daily limit is the truer answer, so it goes
        # first.
        if len(seen) >= per_day:
            raise Refused(
                self._daily_message(tier),
                retry_after=DAY - int(now - seen[0]),
            )

        recent = [t for t in seen if now - t <= MINUTE]
        if len(recent) >= per_min:
            raise Refused(
                "That is a lot of questions at once. Wait a moment and ask "
                "again.",
                retry_after=max(1, MINUTE - int(now - recent[0])),
            )

        seen.append(now)
        self._global.append(now)
        if tier == "anon":
            self._anon.append(now)
        return tier

    def _daily_message(self, tier):
        if tier == "anon":
            return ("You have used your 10 free questions for today. Make a "
                    "free account to keep going, and the tutor will remember "
                    "your chats.")
        return ("You have used today's questions to the tutor. It resets "
                "tomorrow. The lessons, the quiz and the flashcards do not "
                "use it, so they carry on as normal.")

    # ------------------------------------------------------------ reporting

    def snapshot(self):
        """What has been spent. For an admin page or a log line, not a learner."""
        now = self._clock()
        today = [t for t in self._global if now - t <= DAY]
        return {
            "calls_today": len(today),
            "site_limit": GLOBAL_PER_DAY,
            "learners_today": sum(
                1 for v in self._events.values()
                if any(now - t <= DAY for t in v)
            ),
        }


# One budget for the process. Import this, do not build another, or each
# importer gets its own counters and the limit stops meaning anything.
budget = AIBudget()


def client_ip(request):
    """The caller's address.

    X-Real-IP first. The app listens on 127.0.0.1 only, so every request has
    come through nginx, and nginx overwrites X-Real-IP with its $remote_addr.
    Since 1 November 2026 nginx resolves that to the real visitor through its
    realip module, trusting CF-Connecting-IP only from Cloudflare's own ranges.
    CF-Connecting-IP read here directly could be written by anybody who skips
    Cloudflare and talks to the server's address, and the first entry of
    X-Forwarded-For is whatever the client chose to put there, so neither is
    read before the header nginx owns.
    """
    for header in ("X-Real-IP", "CF-Connecting-IP"):
        v = request.headers.get(header)
        if v:
            return v.strip()
    peer = request.remote
    return peer or "unknown"
