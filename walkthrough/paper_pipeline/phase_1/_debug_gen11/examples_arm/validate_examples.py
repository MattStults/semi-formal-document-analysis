#!/usr/bin/env python3
"""THE GATE THE `node_worked_example.md` REVIEW EARNED.

That file was found STALE on five counts, one of them a demonstration that
violated the file's own contract.  A demonstration is what the model imitates,
so an exemplar that does not pass the floor is worse than no exemplar.

Every ✅ fragment in `promptsC/40_worked_examples.md` is a VERBATIM slice of a
converged module on disk.  This script re-validates each of those whole modules
through `schema.validate_all` + `checks.run_checks`, and re-validates the ⛔
side too, so the record says exactly which defective exemplars the floor does
and does not catch.  It ALSO greps the prompt block for the literal fragment
strings, so a later edit to the prompt that drifts from the module on disk is
caught rather than shipped.

    validate_examples.py            print the table; exit 1 on any ✅ failure
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, PHASE1)

import schema                                                 # noqa: E402
import checks                                                 # noqa: E402

CORPUS = os.path.join(PHASE1, "resolve_runs", "graph_v2",
                      "node_corpus_all.json")
LOOP = os.path.join(HERE, "..", "ds_opus_loop", "out")
INSAMPLE = os.path.join(HERE, "..", "list_in_prompt_insample", "out")
BLOCK = os.path.join(HERE, "promptsC", "40_worked_examples.md")

#: (example number, node id, side, where the module comes from)
#:   good  -> `<loop>/<id>.json`         the CONVERGED module (the ✅ side)
#:   bad   -> `<loop>/<id>.turn1.raw.json`  the first draft (the ⛔ side)
#:   worse -> `<insample>/<id>.json`     the in-sample arm's vacuous-body draft
EXAMPLES = [
    (1, "l1368_1541_n019", "good"), (1, "l1368_1541_n019", "bad"),
    (2, "l3239_3382_n002", "good"), (2, "l3239_3382_n002", "bad"),
    (3, "l1368_1541_n019", "good"), (3, "l1368_1541_n019", "bad"),
    (4, "l1_170_n056", "good"),     (4, "l1_170_n056", "bad"),
    (5, "l2126_2404_n016", "good"), (5, "l2126_2404_n016", "bad"),
    (5, "l2126_2404_n016", "worse"),
    (6, "l1707_1973_n022", "good"), (6, "l1707_1973_n022", "bad"),
]

#: Literal strings the prompt block must contain, per example, so that a later
#: edit cannot silently drift from the module on disk.  Each is a substring of
#: the corresponding module's JSON as it appears in the file.
FRAGMENTS = {
    1: ["P is advice to the user to take steps that reduce the risk of harm",
        "S is a suggestion that the user take safety precautions"],
    2: ["avoid_overstepping(R), user_authority(R), overstepping(A)",
        "the narrowed span stops before 'without overstepping'"],
    3: ["the clause says what to do in a dangerous situation and takes no "
        "position on this act otherwise"],
    4: ["user_request(R), not overridden_by_higher_instruction(R)",
        "user_request(R), developer_instruction(I), conflicts_with(R, I)"],
    5: ["no_moral_ambiguity(S), no_valid_opposing_perspective(S), "
        "answer_in_scenario(A, S), straightforward_answer(A)",
        '"atom": "no_moral_ambiguity(S)", "body": "scenario(S)"'],
    6: ["rules in the protect_privileged_information section carry root "
        "authority",
        "the graph's NEEDS block states this, and another node establishes it"],
}


def load_module(cid, side):
    if side == "good":
        return json.load(open(os.path.join(LOOP, f"{cid}.json"),
                              encoding="utf-8"))
    if side == "worse":
        return json.load(open(os.path.join(INSAMPLE, f"{cid}.json"),
                              encoding="utf-8"))["module"]
    raw = open(os.path.join(LOOP, f"{cid}.turn1.raw.json"),
               encoding="utf-8").read()
    obj = json.loads(raw)
    if isinstance(obj, dict) and set(obj) == {"text"}:
        obj = json.loads(obj["text"])
    return obj


def floor(mod, clause, ids):
    m, breaches = schema.validate_all(mod, clause["id"], ids)
    out = {"breaches": [str(b) for b in breaches], "outcome": None,
           "findings": []}
    try:
        res = checks.run_checks(mod, clause, ids)
        out["outcome"] = res.outcome
        out["repair_needed"] = bool(res.repair_needed)
        out["findings"] = [f"[{f.severity}] {f.check_id}: {f.message}"
                           for f in res.findings]
    except Exception as exc:                                  # noqa: BLE001
        out["outcome"] = f"run_checks raised: {exc!r}"
    return out


def main():
    rows = json.load(open(CORPUS, encoding="utf-8"))["clauses"]
    by = {r["id"]: r for r in rows}
    ids = set(by)
    block = open(BLOCK, encoding="utf-8").read()

    bad_good = []
    print(f"{'ex':>3} {'node':<18} {'side':<6} {'outcome':<10} "
          f"{'breaches':>8} {'findings':>8}")
    for n, cid, side in EXAMPLES:
        mod = load_module(cid, side)
        f = floor(mod, by[cid], ids)
        print(f"{n:>3} {cid:<18} {side:<6} {str(f['outcome']):<10} "
              f"{len(f['breaches']):>8} {len(f['findings']):>8}")
        for b in f["breaches"]:
            print(f"        breach: {b}")
        for g in f["findings"]:
            print(f"        {g}")
        if side == "good" and (f["breaches"] or f["outcome"] != "translated"):
            bad_good.append((n, cid))

    print("\nFRAGMENT PRESENCE — the prompt block must quote the bytes on disk")
    missing = []
    for n, frags in sorted(FRAGMENTS.items()):
        for s in frags:
            ok = s in block
            print(f"  ex{n}: {'OK  ' if ok else 'MISS'} {s[:64]!r}")
            if not ok:
                missing.append((n, s))

    print(f"\nblock: {len(block)} chars")
    if bad_good:
        print(f"\nFAIL: ✅ exemplars that do not pass the floor: {bad_good}")
    if missing:
        print(f"FAIL: fragments not found in the prompt block: "
              f"{[m[0] for m in missing]}")
    return 1 if (bad_good or missing) else 0


if __name__ == "__main__":
    raise SystemExit(main())
