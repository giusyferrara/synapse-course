#!/usr/bin/env python3
"""
Spot the Bug — offline variant generator (B1: pre-generate a pool, zero runtime AI cost).

Pipeline (correctness first — nothing is published blind):
    generate  ->  structural-validate  ->  (AI verify pass)  ->  write to a PENDING pool
                                                                  ^ a human approves before it goes live

Two modes, SAME validator and SAME output schema:
    --mock   fill exercises from {{placeholder}} pools. No AI, no keys. Works today.
    --ai     ask the model (reuses ai.router.AIRouter -> Claude Sonnet-4) to author NEW
             exercises, then a second AI pass verifies technical correctness.

Output:  spotbug_variants/<deck>.pending.json   (list of validated exercises, status="pending_review")
Approve: review the file, then:  python tools/spotbug_gen.py --approve --deck <deck>
         -> moves verified items into spotbug_variants/<deck>.json  (the pool the game serves)

Usage:
    python tools/spotbug_gen.py --mock --deck all --n 20
    ANTHROPIC_API_KEY=...  python tools/spotbug_gen.py --ai --deck netmon --n 30 --verify
    python tools/spotbug_gen.py --approve --deck netmon

The whole platform is ENGLISH: all generated content must be English.
"""
import argparse, json, os, re, sys, random, asyncio
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "spotbug_variants"

# ---------------------------------------------------------------- seeds (one per deck; expand freely)
# Each seed anchors the style for --ai and provides the {{hole}} templates for --mock.
TEMPLATES = [
    {"id": "tcpdump_w", "deck": "netmon", "lang": "tcpdump",
     "ctxForms": ["capture traffic on {{IF}} to a file", "save packets from {{IF}} to analyse later"],
     "code": ["sudo tcpdump -i {{IF}} -o {{FILE}}"], "vuln": 0, "category": "Wrong flag",
     "options": ["Wrong flag", "Wrong tool", "Wrong value", "Wrong syntax"],
     "why": "-o is not how tcpdump writes to a file.",
     "fixLines": ["sudo tcpdump -i {{IF}} ___ {{FILE}}"], "slots": ["-w"], "tokens": ["-w", "-o", "-f", "-r"],
     "fixWhy": "-w writes the raw packets; you read them back with -r.",
     "pools": {"IF": ["eth0", "wlan0", "ens33", "enp0s3"], "FILE": ["capture.pcap", "traffic.pcap", "dump.pcap", "wire.pcap"]}},

    {"id": "bola", "deck": "api", "lang": "Python",
     "ctxForms": ["an endpoint returns a {{RES}} by id", "the API reads a {{RES}} given its id"],
     "code": ['@app.get("/api/{{RES}}/<id>")', "def get(id):", "    return db.{{RES}}(id)"], "vuln": 2,
     "category": "BOLA (IDOR)", "options": ["BOLA (IDOR)", "BFLA", "Mass assignment", "SSRF"],
     "why": "Any authenticated user can read someone else's {{RES}} by changing the id — the ownership check is missing.",
     "fixLines": ["row = db.{{RES}}(id)", "if row.owner != ___.id: abort(403)", "return row"], "slots": ["current_user"],
     "tokens": ["current_user", "id", "db", "request"],
     "fixWhy": "Verify the resource belongs to the caller (BOLA = #1 API risk).",
     "pools": {"RES": ["invoices", "orders", "tickets", "documents"]}},

    {"id": "store", "deck": "mobile", "lang": "Java",
     "ctxForms": ["the app stores the {{SECRET}}", "where the app keeps the {{SECRET}}"],
     "code": ['prefs.edit().putString("{{SECRET}}", value).apply()   // SharedPreferences, plaintext'], "vuln": 0,
     "category": "Insecure storage", "options": ["Insecure storage", "Weak crypto", "Exported component", "Hardcoded secret"],
     "why": "Plaintext SharedPreferences are readable on rooted devices or in backups.",
     "fixLines": ["store the {{SECRET}} via ___ / EncryptedSharedPreferences"], "slots": ["Keystore"],
     "tokens": ["Keystore", "SD card", "logcat", "clipboard"],
     "fixWhy": "Use the Android Keystore (EncryptedSharedPreferences); never store secrets in plaintext.",
     "pools": {"SECRET": ["token", "refresh_token", "PIN", "api_key"]}},

    {"id": "mw_strings", "deck": "malware", "lang": "strings",
     "ctxForms": ["extract readable strings (including Windows wide/UTF-16) from {{FILE}}",
                  "pull strings from {{FILE}}, including the wide ones"],
     "code": ["strings {{FILE}}"], "vuln": 0, "category": "Missing flag",
     "options": ["Missing flag", "Wrong flag", "Wrong tool", "Wrong value"],
     "why": "By default strings finds 7-bit ASCII only; it misses UTF-16 (wide) strings common in Windows malware.",
     "fixLines": ["strings -e ___ {{FILE}}"], "slots": ["l"], "tokens": ["l", "s", "b", "a"],
     "fixWhy": "strings -e l extracts UTF-16LE (wide) strings; -e b for big-endian.",
     "pools": {"FILE": ["sample.exe", "payload.bin", "dropper.exe", "loader.dll"]}},

    {"id": "volatility", "deck": "dfir", "lang": "acquisition",
     "ctxForms": ["order of collection during live acquisition of {{HOST}}", "on compromised {{HOST}}: what do you collect first"],
     "code": ["image the {{HOST}} disk first, then capture RAM", "(RAM is far more volatile than disk)"],
     "vuln": 0, "category": "Wrong approach", "options": ["Wrong approach", "Wrong tool", "Wrong value", "Wrong field"],
     "why": "The order of volatility says collect what disappears first.",
     "fixLines": ["capture ___ first (order of volatility)"], "slots": ["memory"],
     "tokens": ["memory", "the disk", "the logs", "the backups"],
     "fixWhy": "Order of volatility: CPU/cache -> RAM -> network state -> disk -> archives. RAM dies on power-off.",
     "pools": {"HOST": ["WS-014", "SRV-DC1", "LAPTOP-07", "HOST-22"]}},
]
DECKS = sorted({t["deck"] for t in TEMPLATES})

# ---------------------------------------------------------------- the strict validator (mirror of the deck validator)
def validate(ex):
    """Raise AssertionError with a reason if the exercise is malformed."""
    assert isinstance(ex, dict), "not an object"
    assert isinstance(ex.get("code"), list) and ex["code"], "code must be a non-empty list"
    assert isinstance(ex.get("vuln"), int) and 0 <= ex["vuln"] < len(ex["code"]), "vuln out of range"
    opts = ex.get("options")
    assert isinstance(opts, list) and len(opts) == 4 and len(set(opts)) == 4, "options must be 4 distinct"
    assert opts[0] == ex.get("category"), "options[0] must equal category"
    blanks = sum(l.count("___") for l in ex.get("fixLines", []))
    assert blanks >= 1 and blanks == len(ex.get("slots", [])), "blank count must equal len(slots)"
    toks = ex.get("tokens", [])
    assert 3 <= len(toks) <= 6 and len(set(toks)) == len(toks), "tokens must be 3-6 distinct"
    assert all(s in toks for s in ex["slots"]), "every slot must be in tokens"
    for k in ("lang", "ctx", "why", "fixWhy"):
        assert isinstance(ex.get(k), str) and ex[k].strip(), f"missing {k}"
    for s in ex["code"] + ex["fixLines"]:
        assert "</script>" not in s, "literal </script> not allowed"
    return ex

def canon(ex):
    """Stable key for dedupe (the bug line + the fix)."""
    return "|".join(ex["code"]) + "##" + "|".join(ex["fixLines"]) + "##" + "|".join(ex["slots"])

# ---------------------------------------------------------------- MOCK generation (no AI)
def gen_mock(deck, n):
    pool = [t for t in TEMPLATES if t["deck"] == deck]
    if not pool:
        return []
    out, seen, tries = [], set(), 0
    while len(out) < n and tries < n * 40:
        tries += 1
        t = random.choice(pool)
        pick = {k: random.choice(v) for k, v in t.get("pools", {}).items()}
        sub = lambda s: re.sub(r"\{\{(\w+)\}\}", lambda m: pick.get(m.group(1), m.group(0)), s)
        ex = {"lang": t["lang"], "ctx": sub(random.choice(t["ctxForms"])),
              "code": [sub(x) for x in t["code"]], "vuln": t["vuln"], "category": sub(t["category"]),
              "options": [sub(x) for x in t["options"]], "why": sub(t["why"]),
              "fixLines": [sub(x) for x in t["fixLines"]], "slots": [sub(x) for x in t["slots"]],
              "tokens": [sub(x) for x in t["tokens"]], "fixWhy": sub(t["fixWhy"])}
        try:
            validate(ex)
        except AssertionError:
            continue
        k = canon(ex)
        if k in seen:
            continue
        seen.add(k)
        ex["_origin"] = "mock"
        out.append(ex)
    return out

# ---------------------------------------------------------------- AI generation (reuses ai.router.AIRouter)
GEN_PROMPT = (
    "You are an exercise author for a cybersecurity game called Spot the Bug. "
    "Produce ONE new exercise for the given deck, on a realistic command/tool/code snippet, "
    "where EXACTLY one line is wrong or dangerous. Teach the correct usage and explain WHY. "
    "Language: ENGLISH (the whole platform is English). "
    "Reply with VALID JSON ONLY, no extra text, in this exact schema:\n"
    '{"lang":str,"ctx":str,"code":[str],"vuln":int,"category":str,'
    '"options":[str,str,str,str],"why":str,"fixLines":[str],"slots":[str],"tokens":[str],"fixWhy":str}\n'
    "Rules: options[0] MUST equal category and the 4 options MUST be distinct; "
    "the number of '___' in fixLines MUST equal len(slots); every slot MUST be in tokens; "
    "tokens has 3-4 distinct entries (the right one + plausible distractors); "
    "0 <= vuln < len(code); no backticks, no markdown, no '</script>'. "
    "Generate an exercise DIFFERENT from the seed (other tool/flag/scenario), not a mere rewrite."
)
VERIFY_PROMPT = (
    "You are a senior security engineer reviewing one Spot the Bug exercise for TECHNICAL CORRECTNESS. "
    "Check: is the flagged line (index 'vuln') really the wrong/dangerous one? Is 'category' accurate? "
    "Is the fix in fixLines+slots actually correct and the 'why'/'fixWhy' factually right? "
    'Reply with JSON ONLY: {"correct": true|false, "reason": "<short>"}. Be strict — if unsure, say false.'
)

def _extract_json(raw):
    m = re.search(r"\{.*\}", raw, re.S)
    return json.loads(m.group(0)) if m else None

async def gen_ai(deck, n, verify):
    from ai.router import AIRouter
    router = AIRouter()
    seed = next((t for t in TEMPLATES if t["deck"] == deck), TEMPLATES[0])
    seed_json = json.dumps({k: seed[k] for k in ("lang", "ctx", "code", "vuln", "category",
                            "options", "why", "fixLines", "slots", "tokens", "fixWhy")})
    out, seen, tries = [], set(), 0
    while len(out) < n and tries < n * 4:
        tries += 1
        nonce = random.randint(1000, 9999)
        ask = (f"Deck: {deck}. Style example (do NOT copy it): {seed_json}. "
               f"Make it clearly different (variation #{nonce}).")
        try:
            raw = await router.get_chat_response(GEN_PROMPT, [{"role": "user", "content": ask}])
            ex = _extract_json(raw)
            validate(ex)
        except (AssertionError, json.JSONDecodeError, TypeError) as e:
            print(f"  · rejected (schema): {e}")
            continue
        k = canon(ex)
        if k in seen:
            continue
        if verify:
            try:
                vraw = await router.get_chat_response(VERIFY_PROMPT,
                        [{"role": "user", "content": json.dumps(ex)}])
                verdict = _extract_json(vraw) or {}
                if not verdict.get("correct"):
                    print(f"  · rejected (verify): {verdict.get('reason', '?')}")
                    continue
            except Exception as e:
                print(f"  · verify error, skipping: {e}")
                continue
        seen.add(k)
        ex["_origin"] = "ai-verified" if verify else "ai"
        out.append(ex)
        print(f"  · accepted {len(out)}/{n}: {ex['lang']} — {ex['ctx'][:48]}")
    return out

# ---------------------------------------------------------------- IO / CLI
def write_pending(deck, items):
    OUT_DIR.mkdir(exist_ok=True)
    path = OUT_DIR / f"{deck}.pending.json"
    existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    seen = {canon(e) for e in existing}
    added = [e for e in items if canon(e) not in seen]
    for e in added:
        e["status"] = "pending_review"
    existing.extend(added)
    path.write_text(json.dumps(existing, indent=1, ensure_ascii=False), encoding="utf-8")
    return path, len(added), len(existing)

def approve(deck):
    pend = OUT_DIR / f"{deck}.pending.json"
    if not pend.exists():
        print(f"no pending file for {deck}")
        return
    items = [e for e in json.loads(pend.read_text(encoding="utf-8")) if e.get("status") != "rejected"]
    for e in items:
        for junk in ("status", "_origin"):
            e.pop(junk, None)
        validate(e)  # final gate
    live = OUT_DIR / f"{deck}.json"
    live.write_text(json.dumps(items, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"approved {len(items)} -> {live}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", default="all", help="deck id or 'all'")
    ap.add_argument("--n", type=int, default=20, help="exercises per deck")
    ap.add_argument("--mock", action="store_true", help="generate from {{placeholder}} pools, no AI")
    ap.add_argument("--ai", action="store_true", help="generate with the AI model")
    ap.add_argument("--verify", action="store_true", help="add the AI correctness-verification pass (with --ai)")
    ap.add_argument("--approve", action="store_true", help="move pending -> live pool")
    args = ap.parse_args()

    decks = DECKS if args.deck == "all" else [args.deck]

    if args.approve:
        for d in decks:
            approve(d)
        return

    if not (args.mock or args.ai):
        ap.error("choose --mock or --ai (or --approve)")

    for d in decks:
        print(f"[{d}] generating {args.n} ({'mock' if args.mock else 'ai'})...")
        items = gen_mock(d, args.n) if args.mock else asyncio.run(gen_ai(d, args.n, args.verify))
        path, added, total = write_pending(d, items)
        print(f"[{d}] +{added} new (pool now {total}) -> {path.name}")

if __name__ == "__main__":
    main()
