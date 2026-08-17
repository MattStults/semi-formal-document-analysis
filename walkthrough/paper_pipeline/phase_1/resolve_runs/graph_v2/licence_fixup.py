#!/usr/bin/env python3
"""Mechanical licence correction under DECISION_licence_textual.md (2026-08-16).

For every translated module whose borrowed NEEDS-name `concepts` glosses are
stamped `licence: "textual"` citing the module's own clause (the manufactured-
citation class — 260 hits on the first corpus_gate run, taught by the prompt's
own worked example until the ruling), rewrite exactly those entries to:

    licence   = "assumed"
    cites     = None
    inference = "the meaning is the one the node's NEEDS contract assigns
                 (mechanical licence correction under
                 DECISION_licence_textual.md, 2026-08-16)"

Nothing else in the module changes. The original run artifacts are NOT
mutated — corrected modules are written to a NEW run directory
(`20260816-130000-licence-fixup`) that `link_nodes.gather()`'s newest-wins
rule selects, with the span prompt copied so `corpus_gate.py` can score the
corrected artifact. Every corrected module is re-validated through
`schema.validate_all` (the same stage-2 surface as production) and refused on
any breach.

Deterministic; zero spend. Run:
    ../../../../../semi-formal-experiment/.venv/bin/python licence_fixup.py [--dry-run]
"""
import argparse, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, PHASE1)
sys.path.insert(0, HERE)

import schema            # noqa: E402
import corpus_gate       # noqa: E402

RUN_NAME = "20260816-130000-licence-fixup"
INFERENCE = ("the meaning is the one the node's NEEDS contract assigns "
             "(mechanical licence correction under "
             "DECISION_licence_textual.md, 2026-08-16)")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    rows = {c["id"]: c for c in json.load(
        open(os.path.join(HERE, "node_corpus_all.json")))["clauses"]}
    outdir = os.path.join(HERE, "translation_sample", "runs", RUN_NAME)
    gathered = corpus_gate.gather()

    fixed, skipped, refused = [], [], []
    for cid, (o, span, run) in sorted(gathered.items()):
        if o.get("outcome") != "translated":
            continue
        needs = set(corpus_gate.needs_names(span))
        touched = 0
        for e in o.get("concepts") or []:
            if not isinstance(e, dict):
                continue
            n = str(e.get("name", "")).split("/")[0]
            if (n in needs and e.get("licence") == "textual"
                    and e.get("cites") == cid):
                e["licence"] = "assumed"
                e["cites"] = None
                e["inference"] = INFERENCE
                touched += 1
        if not touched:
            continue
        if cid not in rows:
            skipped.append((cid, "old-segmentation id, not in node_corpus_all"))
            continue
        mod, breaches = schema.validate_all(o, clause_id=cid,
                                            known_clause_ids=set(rows))
        if breaches or mod is None:
            refused.append((cid, [str(b) for b in breaches]))
            continue
        fixed.append((cid, touched, o, run))

    print(f"{len(fixed)} module(s) to correct, {len(skipped)} skipped, "
          f"{len(refused)} refused by stage 2")
    for cid, why in skipped:
        print(f"  skip {cid}: {why}")
    for cid, brs in refused:
        print(f"  REFUSED {cid}: {brs[:2]}")
    if args.dry_run or not fixed:
        return 1 if refused else 0

    os.makedirs(outdir, exist_ok=True)
    for cid, touched, o, src_run in fixed:
        mod, _ = schema.validate_all(o, clause_id=cid,
                                     known_clause_ids=set(rows))
        with open(os.path.join(outdir, f"{cid}.json"), "w",
                  encoding="utf-8") as fh:
            fh.write(mod.model_dump_json(indent=1))
        lp = schema.render_lp(mod, rows[cid])
        with open(os.path.join(outdir, f"{cid}.lp"), "w",
                  encoding="utf-8") as fh:
            fh.write(lp + "\n% licence_fixup.py over "
                     + src_run + " (DECISION_licence_textual.md)\n")
        src = os.path.join(HERE, "translation_sample", "runs", src_run,
                           cid + ".prompt_user.txt")
        if os.path.exists(src):
            shutil.copy(src, os.path.join(outdir, cid + ".prompt_user.txt"))
    with open(os.path.join(outdir, "run.json"), "w") as fh:
        json.dump({"tool": "licence_fixup.py",
                   "ruling": "DECISION_licence_textual.md 2026-08-16",
                   "modules": [c for c, *_ in fixed],
                   "entries_corrected": sum(t for _, t, *_ in fixed)}, fh,
                  indent=1)
    print(f"wrote {len(fixed)} corrected module(s) to "
          f"translation_sample/runs/{RUN_NAME}/ "
          f"({sum(t for _, t, *_ in fixed)} concepts entries)")
    return 1 if refused else 0


if __name__ == "__main__":
    sys.exit(main())
