"""CHAIN-AUDIT worksheet + validator.

Deterministic (no wall clock, sorted output). Two modes:

  python3 chain_audit_worksheet.py            # build chain_audit/worksheet.json
  python3 chain_audit_worksheet.py validate   # check chain_audit/verdicts.json

Worksheet: every atom in annotations_ext_v1_merged.json whose name carries a
non-empty principal chain (grammar.parse_name), with the agent-first reading
(grammar.describe) and the licensing clause text from modelspec_clauses.json.

Validator checks verdicts.json against the worksheet:
  * coverage — every (clause_id, name) worksheet instance appears exactly once;
  * closed vocabulary — verdict in {correct, agent_missing, reversed,
    unlicensed, unclear};
  * correction consistency — corrected_chain is null for correct/unclear;
    for unlicensed it is null (whole chain dropped) OR a strict shortening of
    the original chain (an unlicensed member removed, licensed part kept —
    adjudication surfaced this case on m0271); for agent_missing/reversed it
    is a non-empty list drawn from grammar.PRINCIPALS. Every non-null
    correction must round-trip clean through grammar.format_name /
    grammar.parse_name and differ from the original chain.
"""
from __future__ import annotations

import json
import os
import sys

import grammar

HERE = os.path.dirname(os.path.abspath(__file__))
ANNOTATIONS = os.path.join(HERE, "annotations_ext_v1_merged.json")
CLAUSES = os.path.join(HERE, "modelspec_clauses.json")
OUTDIR = os.path.join(HERE, "chain_audit")
WORKSHEET = os.path.join(OUTDIR, "worksheet.json")
VERDICTS = os.path.join(OUTDIR, "verdicts.json")

VERDICT_VOCAB = ("correct", "agent_missing", "reversed", "unlicensed",
                 "unclear")


def _load():
    with open(ANNOTATIONS) as f:
        ann = json.load(f)
    with open(CLAUSES) as f:
        clauses = json.load(f)["clauses"]
    clause_text = {c["id"]: c["quote"] for c in clauses}
    return ann, clause_text


def build():
    ann, clause_text = _load()
    rows = []
    for atom in ann["atoms"]:
        p = grammar.parse_name(atom.get("name"))
        if p["error"] or not p["principals"]:
            continue
        rows.append({
            "clause_id": atom["clause_id"],
            "name": atom["name"],
            "gloss": atom.get("gloss", ""),
            "polarity": p["polarity"],
            "stem": p["stem"],
            "principals": p["principals"],
            "chain_length": len(p["principals"]),
            "agent_first_reading": grammar.describe(atom),
            "atom_quote": atom.get("quote", ""),
            "clause_text": clause_text.get(atom["clause_id"], ""),
        })
    rows.sort(key=lambda r: (r["clause_id"], r["name"]))

    by_length, by_principal = {}, {}
    for r in rows:
        by_length[r["chain_length"]] = by_length.get(r["chain_length"], 0) + 1
        for pr in r["principals"]:
            by_principal[pr] = by_principal.get(pr, 0) + 1
    summary = {
        "total_instances": len(rows),
        "distinct_clauses": len({r["clause_id"] for r in rows}),
        "by_chain_length": {str(k): by_length[k] for k in sorted(by_length)},
        "by_principal": {k: by_principal[k] for k in sorted(by_principal)},
    }
    os.makedirs(OUTDIR, exist_ok=True)
    with open(WORKSHEET, "w") as f:
        json.dump({"summary": summary, "instances": rows}, f, indent=1,
                  sort_keys=True)
        f.write("\n")
    print(json.dumps(summary, indent=1, sort_keys=True))
    print(f"wrote {len(rows)} instances -> {WORKSHEET}")


def validate():
    with open(WORKSHEET) as f:
        ws = json.load(f)["instances"]
    with open(VERDICTS) as f:
        verdicts = json.load(f)

    errors = []
    ws_keys = [(r["clause_id"], r["name"]) for r in ws]
    ws_by_key = {(r["clause_id"], r["name"]): r for r in ws}
    seen = []
    for i, v in enumerate(verdicts):
        key = (v.get("clause_id"), v.get("name"))
        tag = f"verdicts[{i}] {key}"
        if key not in ws_by_key:
            errors.append(f"{tag}: not a worksheet instance")
            continue
        seen.append(key)
        vd = v.get("verdict")
        if vd not in VERDICT_VOCAB:
            errors.append(f"{tag}: verdict {vd!r} outside closed vocabulary")
            continue
        corr = v.get("corrected_chain")
        row = ws_by_key[key]
        if vd in ("correct", "unclear"):
            if corr is not None:
                errors.append(f"{tag}: {vd} requires corrected_chain null")
        elif vd == "unlicensed" and corr is None:
            pass  # whole chain dropped
        else:  # agent_missing / reversed / unlicensed-with-shortening
            if not isinstance(corr, list) or not corr:
                errors.append(f"{tag}: {vd} requires a non-empty "
                              "corrected_chain list (or null for unlicensed)")
                continue
            bad = [c for c in corr if c not in grammar.PRINCIPALS]
            if bad:
                errors.append(f"{tag}: non-principal members {bad}")
                continue
            if vd == "unlicensed":
                orig = row["principals"]
                if not (len(corr) < len(orig)
                        and all(c in orig for c in corr)):
                    errors.append(f"{tag}: unlicensed correction must be a "
                                  "strict shortening of the original chain")
                    continue
            new_name = grammar.format_name(row["stem"], row["polarity"], corr)
            p = grammar.parse_name(new_name)
            if p["error"]:
                errors.append(f"{tag}: correction {new_name!r} does not "
                              f"parse: {p['error']}")
            elif p["principals"] != list(corr):
                errors.append(f"{tag}: correction round-trip mismatch")
            elif corr == row["principals"]:
                errors.append(f"{tag}: correction equals original chain")
        if not v.get("reason") or len(str(v["reason"]).split()) > 25:
            errors.append(f"{tag}: reason missing or over 25 words")

    from collections import Counter
    counts = Counter(seen)
    for key in ws_keys:
        if counts[key] == 0:
            errors.append(f"worksheet instance {key} has no verdict")
        elif counts[key] > 1:
            errors.append(f"worksheet instance {key} has {counts[key]} "
                          "verdicts")
    # de-dup multi-reported keys
    errors = sorted(set(errors))

    if errors:
        for e in errors:
            print("FAIL:", e)
        print(f"validate: {len(errors)} error(s) over {len(verdicts)} "
              f"verdicts / {len(ws)} instances")
        sys.exit(1)
    dist = Counter(v["verdict"] for v in verdicts)
    print("validate: CLEAN —", len(verdicts), "verdicts cover",
          len(ws), "instances exactly once;",
          json.dumps(dict(sorted(dist.items()))))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        validate()
    else:
        build()
