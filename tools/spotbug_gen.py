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

    # --- netmon seeds vetted from the netmon --ai pilot review (2026-06-04) ---
    {"id": "nmap_scantype", "deck": "netmon", "lang": "nmap",
     "ctxForms": ["scan for open TCP ports on {{HOST}}", "list the open TCP ports on {{HOST}}"],
     "code": ["nmap -sU -p {{RANGE}} {{HOST}}"], "vuln": 0, "category": "Wrong flag",
     "options": ["Wrong flag", "Wrong tool", "Wrong value", "Wrong syntax"],
     "why": "-sU runs a UDP scan, not a TCP scan, so it will not find open TCP ports.",
     "fixLines": ["nmap ___ -p {{RANGE}} {{HOST}}"], "slots": ["-sT"], "tokens": ["-sT", "-sU", "-sn", "-sA"],
     "fixWhy": "-sT does a TCP connect scan to find open TCP ports (-sS SYN scan also works but needs root).",
     "pools": {"HOST": ["127.0.0.1", "192.168.1.10", "10.0.0.5", "target.local"], "RANGE": ["1-1000", "1-65535", "22,80,443", "1-1024"]}},

    {"id": "tcpdump_timestamps", "deck": "netmon", "lang": "tcpdump",
     "ctxForms": ["capture traffic to/from {{HOST}} keeping timestamps", "capture packets on {{IF}} with timestamps"],
     "code": ["sudo tcpdump -i {{IF}} -v -t host {{HOST}}"], "vuln": 0, "category": "Wrong flag",
     "options": ["Wrong flag", "Wrong tool", "Wrong value", "Wrong syntax"],
     "why": "-t SUPPRESSES the timestamp on every line, which defeats the goal of capturing with timestamps.",
     "fixLines": ["sudo tcpdump -i {{IF}} -v ___ host {{HOST}}"], "slots": ["-tt"], "tokens": ["-tt", "-t", "-T", "-A"],
     "fixWhy": "-tt prints an unformatted (epoch) timestamp per packet; -t removes timestamps entirely.",
     "pools": {"IF": ["eth0", "wlan0", "ens33", "enp0s3"], "HOST": ["192.168.1.100", "10.0.0.5", "8.8.8.8", "172.16.0.9"]}},

    {"id": "tshark_capture_vs_display", "deck": "netmon", "lang": "tshark",
     "ctxForms": ["read {{FILE}} and keep only {{PROTO}} packets", "filter a saved capture {{FILE}} down to {{PROTO}}"],
     "code": ["tshark -r {{FILE}} -f {{PROTO}}"], "vuln": 0, "category": "Wrong flag",
     "options": ["Wrong flag", "Wrong tool", "Wrong value", "Wrong syntax"],
     "why": "-f is a capture (BPF) filter that only applies to a live capture; reading a file needs a display filter.",
     "fixLines": ["tshark -r {{FILE}} ___ {{PROTO}}"], "slots": ["-Y"], "tokens": ["-Y", "-f", "-R", "-d"],
     "fixWhy": "-Y applies a Wireshark display filter when reading a pcap; -f only works during live capture.",
     "pools": {"FILE": ["capture.pcap", "network.pcap", "traffic.pcap", "http.pcap"], "PROTO": ["dns", "http", "tcp", "tls"]}},

    {"id": "tshark_numeric", "deck": "netmon", "lang": "tshark",
     "ctxForms": ["read {{FILE}} and show HTTP requests without slow DNS lookups", "extract HTTP request host+URI from {{FILE}} without name resolution"],
     "code": ["tshark -r {{FILE}} -Y http.request -T fields -e http.host -e http.request.uri"], "vuln": 0, "category": "Missing flag",
     "options": ["Missing flag", "Wrong flag", "Wrong value", "Wrong syntax"],
     "why": "Without -n, tshark resolves addresses via DNS — slow, and it leaks lookups for the very hosts you are analysing.",
     "fixLines": ["tshark ___ -r {{FILE}} -Y http.request -T fields -e http.host -e http.request.uri"], "slots": ["-n"], "tokens": ["-n", "-N", "-d", "-q"],
     "fixWhy": "-n disables name resolution: faster analysis and no DNS leakage.",
     "pools": {"FILE": ["capture.pcap", "network.pcap", "traffic.pcap", "http.pcap"]}},

    {"id": "netstat_numeric", "deck": "netmon", "lang": "netstat",
     "ctxForms": ["list listening TCP ports with their process, without slow reverse-DNS", "show TCP listeners + PIDs fast (no name resolution)"],
     "code": ["netstat -tlp"], "vuln": 0, "category": "Missing flag",
     "options": ["Missing flag", "Wrong flag", "Wrong value", "Wrong syntax"],
     "why": "Without -n, netstat resolves addresses and ports via reverse DNS, which is slow and noisy.",
     "fixLines": ["netstat -___lp"], "slots": ["tn"], "tokens": ["tn", "tl", "tu", "ta"],
     "fixWhy": "-n shows numeric addresses/ports, avoiding slow reverse-DNS lookups.",
     "pools": {}},

    {"id": "dig_reverse", "deck": "netmon", "lang": "dig",
     "ctxForms": ["do a reverse DNS (PTR) lookup for {{IP}}", "find the hostname behind {{IP}}"],
     "code": ["dig -r {{IP}}"], "vuln": 0, "category": "Wrong flag",
     "options": ["Wrong flag", "Wrong tool", "Wrong value", "Wrong syntax"],
     "why": "-r only tells dig to skip ~/.digrc; it does NOT perform a reverse lookup.",
     "fixLines": ["dig ___ {{IP}}"], "slots": ["-x"], "tokens": ["-x", "-r", "-p", "-t"],
     "fixWhy": "-x builds the in-addr.arpa PTR query automatically for a reverse lookup.",
     "pools": {"IP": ["192.168.1.1", "8.8.8.8", "10.0.0.53", "1.1.1.1"]}},

    {"id": "tcpflow_bpf", "deck": "netmon", "lang": "tcpflow",
     "ctxForms": ["reconstruct TCP flows on port {{PORT}} into {{DIR}}", "reassemble streams on port {{PORT}} with tcpflow"],
     "code": ["sudo tcpflow -i {{IF}} -p {{PORT}} -o {{DIR}}"], "vuln": 0, "category": "Wrong syntax",
     "options": ["Wrong syntax", "Wrong flag", "Wrong tool", "Wrong value"],
     "why": "tcpflow takes its filter as a bare BPF expression (port {{PORT}}); -p is the no-promiscuous flag, so '-p {{PORT}}' is not a port filter.",
     "fixLines": ["sudo tcpflow -i {{IF}} ___ {{PORT}} -o {{DIR}}"], "slots": ["port"], "tokens": ["port", "-p", "-P", "dst"],
     "fixWhy": "Filters are bare BPF: 'port {{PORT}}'. (-o correctly sets the output directory.)",
     "pools": {"IF": ["eth0", "wlan0", "ens33", "enp0s3"], "PORT": ["80", "443", "53", "8080"], "DIR": ["/tmp/flows/", "./out/", "/var/tmp/cap/", "flows/"]}},

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

    {"id": "objdump_section", "deck": "malware", "lang": "objdump",
     "ctxForms": ["disassemble the executable code of {{FILE}}", "look at the runnable instructions inside {{FILE}}"],
     "code": ["objdump -d -j .data {{FILE}}"], "vuln": 0, "category": "Wrong value",
     "options": ["Wrong value", "Wrong flag", "Wrong tool", "Wrong syntax"],
     "why": "The .data section holds static data, not code; the runnable instructions live in .text, so this disassembles the wrong section.",
     "fixLines": ["objdump -d -j ___ {{FILE}}"], "slots": [".text"], "tokens": [".text", ".data", ".bss", ".rodata"],
     "fixWhy": "Disassemble .text, where the runnable code lives; .data is only static values.",
     "pools": {"FILE": ["sample.exe", "payload.bin", "dropper.exe", "loader.dll"]}},

    {"id": "entropy_tool", "deck": "malware", "lang": "binwalk",
     "ctxForms": ["check whether {{FILE}} is packed by measuring its entropy", "decide if {{FILE}} is packed or encrypted"],
     "code": ["hexdump -C {{FILE}}"], "vuln": 0, "category": "Wrong tool",
     "options": ["Wrong tool", "Wrong flag", "Wrong value", "Wrong approach"],
     "why": "A raw hex dump tells you nothing about packing; you need an entropy view to spot compressed or encrypted regions.",
     "fixLines": ["___ -E {{FILE}}"], "slots": ["binwalk"], "tokens": ["binwalk", "hexdump", "xxd", "cat"],
     "fixWhy": "binwalk -E plots entropy; a high, flat curve signals packing or encryption.",
     "pools": {"FILE": ["sample.exe", "packed.bin", "dropper.exe", "suspicious.exe"]}},

    {"id": "r2_analysis", "deck": "malware", "lang": "radare2",
     "ctxForms": ["open {{FILE}} in radare2 and run full auto-analysis", "analyse all functions and references in {{FILE}} with r2"],
     "code": ["r2 -qc aa {{FILE}}"], "vuln": 0, "category": "Wrong value",
     "options": ["Wrong value", "Wrong flag", "Wrong tool", "Wrong syntax"],
     "why": "aa runs only the basic analysis pass; it misses functions, strings and cross-references needed for malware triage.",
     "fixLines": ["r2 -qc ___ {{FILE}}"], "slots": ["aaa"], "tokens": ["aaa", "aa", "af", "pdf"],
     "fixWhy": "aaa runs the deeper auto-analysis (functions, refs, strings); aa is only the minimal pass.",
     "pools": {"FILE": ["sample.exe", "payload.bin", "trojan.exe", "loader.dll"]}},

    {"id": "upx_unpack", "deck": "malware", "lang": "upx",
     "ctxForms": ["unpack the UPX-packed sample {{FILE}} without destroying the original", "decompress {{FILE}} but keep the packed sample as evidence"],
     "code": ["upx -d {{FILE}}"], "vuln": 0, "category": "Missing flag",
     "options": ["Missing flag", "Wrong flag", "Wrong tool", "Wrong value"],
     "why": "upx -d unpacks in place and overwrites the original file, so the packed evidence sample is lost.",
     "fixLines": ["upx -d ___ unpacked.exe {{FILE}}"], "slots": ["-o"], "tokens": ["-o", "-k", "-q", "-f"],
     "fixWhy": "-o writes the unpacked copy to a new file, leaving the original packed sample intact.",
     "pools": {"FILE": ["trojan.exe", "packed.exe", "sample.exe", "dropper.exe"]}},

    {"id": "binwalk_entropy", "deck": "malware", "lang": "binwalk",
     "ctxForms": ["measure the entropy of {{FILE}} to judge if it is packed", "scan {{FILE}} for high-entropy packed regions"],
     "code": ["binwalk -e {{FILE}}"], "vuln": 0, "category": "Wrong flag",
     "options": ["Wrong flag", "Wrong value", "Wrong tool", "Wrong syntax"],
     "why": "-e extracts embedded files; it does not show entropy, so it will not tell you whether the sample is packed.",
     "fixLines": ["binwalk ___ {{FILE}}"], "slots": ["-E"], "tokens": ["-E", "-e", "-A", "-B"],
     "fixWhy": "-E (capital) plots an entropy curve; high and flat means packed or encrypted.",
     "pools": {"FILE": ["sample.exe", "payload.bin", "dropper.exe", "suspicious.bin"]}},

    {"id": "hash_ioc", "deck": "malware", "lang": "bash",
     "ctxForms": ["compute a reliable hash of {{FILE}} to share as an IOC", "fingerprint {{FILE}} for an indicator of compromise"],
     "code": ["md5sum {{FILE}}"], "vuln": 0, "category": "Wrong tool",
     "options": ["Wrong tool", "Wrong flag", "Wrong value", "Wrong approach"],
     "why": "MD5 is collision-prone: two different files can produce the same MD5, so it is unsafe as a unique malware identifier.",
     "fixLines": ["___ {{FILE}}"], "slots": ["sha256sum"], "tokens": ["sha256sum", "md5sum", "crc32", "base64"],
     "fixWhy": "Use sha256sum, which is collision-resistant and the standard for malware IOCs.",
     "pools": {"FILE": ["sample.exe", "payload.bin", "trojan.exe", "ransomware.exe"]}},

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
    "SELF-CONSISTENCY (critical): the line at index vuln MUST literally contain the described mistake; never say a flag is missing if it already appears in that line, and never flag a line that is actually correct; the fix MUST genuinely correct that exact line. "
    "VARIETY: vary the tool, technique and bug category widely across the deck's scope; do NOT default to missing- or wrong-flag puzzles. "
    "TOOLS (critical): if the request gives an allowed-tools list, use ONLY those tools and ONLY real, standard flags/options you are certain exist; NEVER invent a tool, flag, or subcommand. If you are unsure whether a flag or tool exists, choose a different idea rather than guess. "
    "Generate an exercise DIFFERENT from the seed (other tool/flag/scenario), not a mere rewrite."
)

# Per-deck constraints that keep the model on ground it actually knows — that is where
# hallucination (invented tools/flags/APIs) stops. Each value is a dict; supported keys:
#   "tools"      -> CLI decks: the ONLY commands allowed (use real flags, never invent).
#   "frameworks" -> code decks: the ONLY frameworks allowed (real mainstream APIs only).
#   "bugs"       -> the vulnerability classes the bug must belong to.
#   "note"       -> extra free-form guidance appended verbatim.
# A deck with no entry falls back to unconstrained generation.
DECK_ALLOWLIST = {
    "netmon": {
        "tools": ["tcpdump", "tshark", "nmap", "ss", "netstat", "ngrep", "tcpflow", "dig"],
    },
    "api": {
        "frameworks": ["Python Flask", "Python FastAPI", "Node.js Express"],
        "bugs": [
            "BOLA / IDOR (missing object-level ownership check)",
            "BFLA (missing role / function-level authorization)",
            "mass assignment (binding untrusted fields to a model)",
            "broken authentication (JWT alg/none, weak session handling)",
            "SSRF (server fetches a user-supplied URL)",
            "missing rate limiting / brute-force protection on auth",
            "excessive data exposure / verbose errors leaking internals",
        ],
        "note": ("Bugs MUST be CONCEPTUAL — a real line of code where a security check is missing or wrong "
                 "(the vuln line is that code line; the fix adds/repairs the check). Do NOT make CLI-flag trivia. "
                 "Use only real, mainstream APIs of the allowed frameworks; never invent decorators, methods, or libraries."),
    },
    # dfir (later): PIN Volatility 3 syntax (windows.pslist, no --profile) or avoid flag puzzles on it —
    #   vol2/vol3 differ and the malware-pilot volatility item was conceptually right but structurally broken.
}

def _allow_instruction(deck):
    """Build the per-deck constraint text appended to the generation request."""
    spec = DECK_ALLOWLIST.get(deck)
    if not spec:
        return ""
    parts = []
    if spec.get("tools"):
        parts.append("Use ONLY one of these tools, nothing else: " + ", ".join(spec["tools"]) +
                     ". Use only real, standard flags; never invent a tool or flag.")
    if spec.get("frameworks"):
        parts.append("Use ONLY these frameworks: " + ", ".join(spec["frameworks"]) +
                     ". Use only their real, mainstream APIs; never invent decorators, methods, or libraries.")
    if spec.get("bugs"):
        parts.append("The bug MUST be one of these vulnerability classes: " + "; ".join(spec["bugs"]) + ".")
    if spec.get("note"):
        parts.append(spec["note"])
    return " " + " ".join(parts)
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
    seed_ex = gen_mock(deck, 1) or gen_mock(DECKS[0], 1)
    seed = seed_ex[0] if seed_ex else {}
    seed_json = json.dumps({k: seed[k] for k in ("lang", "ctx", "code", "vuln", "category", "options", "why", "fixLines", "slots", "tokens", "fixWhy") if k in seed})
    out, seen, tries = [], set(), 0
    while len(out) < n and tries < n * 4:
        tries += 1
        nonce = random.randint(1000, 9999)
        used_tools = sorted({e.get("lang", "") for e in out})
        avoid = (" Avoid reusing these tools already used in this batch: " + ", ".join(used_tools) + ".") if used_tools else ""
        allow = _allow_instruction(deck)
        ask = (f"Deck: {deck}. Style example (do NOT copy it): {seed_json}. "
               f"Make it clearly different (variation #{nonce}).{allow}{avoid}")
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
