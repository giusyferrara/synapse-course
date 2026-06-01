#!/usr/bin/env python3
"""
Quiz bank generator.

Reads the two editable stores:
  - quiz/quiz_templates/*.json   (template definitions)
  - quiz/hand_authored/*.json    (hand-authored concrete questions)

Expands every template into deterministic, always-correct concrete questions
and writes them, together with the hand-authored questions, to:
  - static/quiz_content/<name>.json   (one file per template / hand-authored set)
  - static/quiz_content/_index.json   (manifest + counts)

Determinism:
  * Variable combinations are enumerated in a fixed key order.
  * Placeholders are substituted globally (repeatedly) so a variable value may
    itself contain another {placeholder} (e.g. {fetch} contains {param}).
  * Distractor selection and option shuffle are seeded from a stable MD5 of
    (template_id, variant index) -> reproducible across runs and machines.
  * Grading is by option "id" with "correct": true -- never by position.

No live AI is used: every question is fully resolved here, offline.
"""
import hashlib
import itertools
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TPL_DIR = os.path.join(HERE, "quiz_templates")
HAND_DIR = os.path.join(HERE, "hand_authored")
OUT_DIR = os.path.join(ROOT, "static", "quiz_content")

NUM_OPTIONS = 4  # 1 correct + up to 3 distractors

# Fields copied onto a concrete question (NO template logic travels with it)
CONCRETE_PASSTHROUGH = ["category", "skill_tag", "owasp", "severity", "difficulty"]


def stable_seed(*parts):
    h = hashlib.md5(":".join(str(p) for p in parts).encode("utf-8")).hexdigest()
    return int(h, 16) % (2 ** 32)


def subst(text, mapping):
    """Replace every {key} with its value, repeatedly, until stable.
    Supports nested placeholders (a value containing another {key})."""
    if text is None:
        return None
    cur = text
    for _ in range(12):
        prev = cur
        for k, v in mapping.items():
            cur = cur.replace("{" + k + "}", v)
        if cur == prev:
            break
    return cur


def variable_combos(variables):
    """Yield mapping dicts for the cartesian product, in fixed key order."""
    if not variables:
        yield {}
        return
    keys = list(variables.keys())
    for combo in itertools.product(*(variables[k] for k in keys)):
        yield dict(zip(keys, combo))


def build_options(template_id, idx, correct_text, distractor_pool):
    """Deterministically pick distractors, add the correct option, shuffle,
    and assign A/B/C/D ids."""
    rng = random.Random(stable_seed(template_id, idx))
    pool = [d for d in distractor_pool if d != correct_text]
    k = min(NUM_OPTIONS - 1, len(pool))
    chosen = rng.sample(pool, k) if k > 0 else []
    texts = [correct_text] + chosen
    rng.shuffle(texts)
    options = []
    for i, t in enumerate(texts):
        options.append({"id": chr(ord("A") + i), "text": t, "correct": t == correct_text})
    # exactly one correct
    assert sum(1 for o in options if o["correct"]) == 1, f"{template_id}#{idx}: not exactly one correct"
    return options


def expand_template(tpl):
    tid = tpl["template_id"]
    questions = []
    for idx, mapping in enumerate(variable_combos(tpl.get("variables", {})), start=1):
        prompt = subst(tpl["prompt"], mapping)
        code = subst(tpl.get("code_template"), mapping)
        correct = subst(tpl["correct_option"], mapping)
        distractors = [subst(d, mapping) for d in tpl["distractor_pool"]]
        explanation = subst(tpl["explanation_template"], mapping)
        q = {
            "id": f"{tid}_{idx:04d}",
            "generated_from_template": tid,
        }
        for f in CONCRETE_PASSTHROUGH:
            q[f] = tpl.get(f)
        q["linked_deck"] = None
        q["prompt"] = prompt
        q["code_snippet"] = code
        q["options"] = build_options(tid, idx, correct, distractors)
        q["explanation"] = explanation
        q["source_reference"] = tpl["source_reference"]
        questions.append(q)
    return questions


def validate_hand(q):
    assert q.get("generated_from_template") is None, f"{q.get('id')}: hand-authored must have null template"
    opts = q["options"]
    assert sum(1 for o in opts if o.get("correct")) == 1, f"{q['id']}: needs exactly one correct option"
    ids = [o["id"] for o in opts]
    assert ids == [chr(ord("A") + i) for i in range(len(opts))], f"{q['id']}: option ids must be A,B,C,..."
    for req in ("category", "skill_tag", "prompt", "explanation", "source_reference"):
        assert q.get(req), f"{q['id']}: missing {req}"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    cat_counts = {}
    skill_counts = {}
    diff_counts = {}
    files = []
    total = 0
    mismatches = []

    # --- templates ---
    for fn in sorted(os.listdir(TPL_DIR)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(TPL_DIR, fn), encoding="utf-8") as f:
            tpl = json.load(f)
        qs = expand_template(tpl)
        exp = tpl.get("variants_expected")
        if exp is not None and exp != len(qs):
            mismatches.append((tpl["template_id"], exp, len(qs)))
        out = os.path.join(OUT_DIR, tpl["template_id"] + ".json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(qs, f, indent=2, ensure_ascii=False)
        size = os.path.getsize(out)
        files.append((tpl["template_id"] + ".json", len(qs), size))
        for q in qs:
            total += 1
            cat_counts[q["category"]] = cat_counts.get(q["category"], 0) + 1
            skill_counts[q["skill_tag"]] = skill_counts.get(q["skill_tag"], 0) + 1
            diff_counts[q["difficulty"]] = diff_counts.get(q["difficulty"], 0) + 1

    # --- hand-authored ---
    for fn in sorted(os.listdir(HAND_DIR)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(HAND_DIR, fn), encoding="utf-8") as f:
            qs = json.load(f)
        for q in qs:
            validate_hand(q)
        out = os.path.join(OUT_DIR, fn)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(qs, f, indent=2, ensure_ascii=False)
        size = os.path.getsize(out)
        files.append((fn, len(qs), size))
        for q in qs:
            total += 1
            cat_counts[q["category"]] = cat_counts.get(q["category"], 0) + 1
            skill_counts[q["skill_tag"]] = skill_counts.get(q["skill_tag"], 0) + 1
            diff_counts[q["difficulty"]] = diff_counts.get(q["difficulty"], 0) + 1

    index = {
        "total_questions": total,
        "by_category": cat_counts,
        "by_difficulty": diff_counts,
        "by_skill": skill_counts,
        "files": [{"file": n, "questions": c, "bytes": b} for n, c, b in files],
    }
    with open(os.path.join(OUT_DIR, "_index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    # --- report ---
    print("=" * 60)
    print("QUIZ BANK GENERATED ->", OUT_DIR)
    print("=" * 60)
    print(f"Total questions: {total}")
    print("\nBy category:")
    for c in ("detect", "understand", "remediate", "severity", "tooling"):
        print(f"  {c:<11}: {cat_counts.get(c, 0)}")
    print("\nBy difficulty:")
    for d in ("beginner", "intermediate", "advanced"):
        print(f"  {d:<13}: {diff_counts.get(d, 0)}")
    print(f"\nDistinct skill tags: {len(skill_counts)}")
    print(f"Output files: {len(files)} (+ _index.json)")
    idx_size = os.path.getsize(os.path.join(OUT_DIR, '_index.json'))
    total_bytes = sum(b for _, _, b in files) + idx_size
    print(f"Total size: {total_bytes/1024:.1f} KiB")
    if mismatches:
        print("\n!! variants_expected mismatches:")
        for tid, exp, got in mismatches:
            print(f"   {tid}: expected {exp}, got {got}")
    else:
        print("\nAll templates matched variants_expected. OK")


if __name__ == "__main__":
    main()
