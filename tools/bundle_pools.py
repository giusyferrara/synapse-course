#!/usr/bin/env python3
"""
Bundle the approved variant pools into the live game as `const VARIANT_POOLS`.

This is the ONLY supported way to (re)embed the pools — run it after regenerating
spotbug_variants/<deck>.json. It reads and writes EVERYTHING as explicit UTF-8, so
multibyte characters (e.g. the em-dash —) survive on any platform. Reading the JSON
without encoding='utf-8' on Windows decodes as cp1252 and mojibake-corrupts — that is
exactly the bug this script exists to prevent.

Usage:  python tools/bundle_pools.py
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "templates" / "spot_the_bug.html"
POOL_DIR = ROOT / "spotbug_variants"
DECKS = ["netmon", "api", "mobile", "dfir"]
KEEP = ("lang", "ctx", "code", "vuln", "category", "options", "why", "fixLines", "slots", "tokens", "fixWhy")


def build_blob():
    pools = {}
    for d in DECKS:
        path = POOL_DIR / f"{d}.json"
        if not path.exists():
            continue
        # explicit UTF-8 read — never rely on the platform default (cp1252 on Windows)
        items = json.loads(path.read_text(encoding="utf-8"))
        pools[d] = [{k: ex[k] for k in KEEP} for ex in items]
    blob = json.dumps(pools, ensure_ascii=False, separators=(",", ":"))
    # never let a string close the <script> tag
    blob = blob.replace("</", "<\\/")
    n = sum(len(v) for v in pools.values())
    return blob, n


def main():
    blob, n = build_blob()
    line = "    const VARIANT_POOLS = " + blob + ";"
    html = HTML.read_text(encoding="utf-8")
    new, count = re.subn(r"(?m)^    const VARIANT_POOLS = .*;$", lambda m: line, html, count=1)
    assert count == 1, f"expected exactly 1 VARIANT_POOLS line, found {count}"
    # explicit UTF-8 write, no newline translation
    HTML.write_text(new, encoding="utf-8", newline="")
    # self-check: no mojibake survived
    assert "â€" not in new, "mojibake detected after bundle — aborting"
    print(f"bundled {n} variants into {HTML.name} (UTF-8, mojibake-clean)")


if __name__ == "__main__":
    main()
