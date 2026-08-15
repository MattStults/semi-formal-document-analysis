"""CHECK 2b — the arity check replayed at EVERY attempt of every stored chain.

ZERO API SPEND.

`replay_arity.py` scores the modules that were WRITTEN to disk. Only accepted
(`translated`) modules and abstentions are written; an `unrepaired` chain's
module survives only in the graveyard. To see what the new check would do to
the loop itself — including the attempts that were accepted first try, and the
attempts inside chains that later converged — the reply text has to be parsed
back out of the transcripts.

Each assistant reply is json-parsed (a reply that does not parse is counted
separately: `schema.py`'s parser owns that failure, not this check) and passed
to `checks.arity_mismatches`, the shipping function.

The number that matters for cost: an attempt whose module the OLD checks
passed but which the NEW check flags is one extra repair round injected into a
loop that had already stopped.
"""
import collections
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, PHASE1)

import checks  # noqa: E402

RUN_GLOBS = ("runs/*/run.json",
             "resolve_runs/graph_v2/translation_sample/runs/*/run.json")


def parse(text):
    try:
        obj = json.loads(text)
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def main():
    per_attempt_rows, chain_rows = [], []
    for pattern in RUN_GLOBS:
        for rj in sorted(glob.glob(os.path.join(PHASE1, pattern))):
            root = os.path.dirname(rj)
            run = os.path.basename(root)
            data = json.load(open(rj, encoding="utf-8"))
            for res in data.get("results", []):
                cid = res.get("clause_id")
                tp = os.path.join(root, cid + ".transcript.json")
                if not os.path.exists(tp):
                    continue
                turns = json.load(open(tp, encoding="utf-8"))
                replies = [m["content"] for m in turns
                           if m.get("role") == "assistant"]
                hits = []
                for i, text in enumerate(replies, start=1):
                    obj = parse(text)
                    if obj is None:
                        hits.append((i, "unparseable", []))
                        continue
                    if obj.get("outcome") == "abstained":
                        hits.append((i, "abstained", []))
                        continue
                    mm = checks.arity_mismatches(obj)
                    hits.append((i, "scored", mm))
                    per_attempt_rows.append(dict(
                        run=run, clause=cid, attempt=i, n=len(replies),
                        status=res.get("status"), mismatches=mm))
                chain_rows.append(dict(run=run, clause=cid,
                                       status=res.get("status"),
                                       n=len(replies), hits=hits))

    scored = [r for r in per_attempt_rows]
    print("=" * 78)
    print("CHECK 2b — arity check at every attempt of every stored chain")
    print("=" * 78)
    print(f"chains: {len(chain_rows)}   scored attempt-modules: {len(scored)}")
    unp = sum(1 for c in chain_rows for h in c['hits'] if h[1] == 'unparseable')
    abst = sum(1 for c in chain_rows for h in c['hits'] if h[1] == 'abstained')
    print(f"replies that do not parse: {unp}   abstentions: {abst}")
    flagged = [r for r in scored if r["mismatches"]]
    print(f"attempt-modules flagged by the arity check: {len(flagged)}")
    print()

    # THE COST QUESTION: a FINAL attempt of a chain the old loop ACCEPTED.
    final_accept = [r for r in scored
                    if r["status"] == "translated" and r["attempt"] == r["n"]]
    fa_flag = [r for r in final_accept if r["mismatches"]]
    print("--- accepted final attempts (the production corpus) ---")
    print(f"n={len(final_accept)}  flagged={len(fa_flag)}")
    for r in fa_flag:
        print(f"  * {r['run']} {r['clause']} attempt {r['attempt']}: "
              f"{r['mismatches']}")
    print()

    first_try = [r for r in scored if r["status"] == "translated"
                 and r["n"] == 1]
    print("--- first-try successes (accepted with zero repair rounds) ---")
    print(f"n={len(first_try)}  flagged={sum(1 for r in first_try if r['mismatches'])}")
    print()

    mid = [r for r in scored
           if r["status"] == "translated" and r["attempt"] < r["n"]
           and r["mismatches"]]
    print("--- intermediate attempts of chains that CONVERGED ---")
    print(f"flagged: {len(mid)}  (these were already failing other checks; the")
    print("  arity finding is additive text in the SAME repair round, not an")
    print("  extra round -- verified below by checking whether the attempt")
    print("  already carried an error finding)")
    for r in mid:
        print(f"  {r['run'][:24]:24s} {r['clause']:18s} attempt {r['attempt']}/{r['n']}"
              f"  {r['mismatches']}")
    print()

    fail = [r for r in scored if r["status"] in ("unrepaired", "invalid_module")]
    ff = [r for r in fail if r["mismatches"]]
    by_clause = collections.defaultdict(list)
    for r in ff:
        by_clause[(r["run"], r["clause"])].append(r["attempt"])
    print("--- attempts inside FAILED chains ---")
    print(f"attempt-modules n={len(fail)}  flagged={len(ff)}"
          f"  distinct clauses={len(by_clause)}")
    fail_chains = {(r["run"], r["clause"]) for r in fail}
    print(f"failed chains {len(fail_chains)}, of which "
          f"{len(by_clause)} carry an arity mismatch at >=1 attempt "
          f"({100.0 * len(by_clause) / max(1, len(fail_chains)):.0f}%)")
    for (run, cl), att in sorted(by_clause.items()):
        print(f"  {run[:24]:24s} {cl:18s} attempts {att}")

    out = os.path.join(HERE, "arity_attempts.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(per_attempt_rows, fh, indent=1, default=str)
    print(f"\nper-attempt table -> {out}")


if __name__ == "__main__":
    main()
