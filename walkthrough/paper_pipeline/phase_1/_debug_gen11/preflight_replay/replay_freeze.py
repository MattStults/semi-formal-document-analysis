"""CHECK 1 — offline replay of the restart-on-repeat chain policy.

ZERO API SPEND. Reads only stored artifacts; writes nothing outside this
directory (it writes nothing at all — output is stdout + optional --json).

Run from phase_1/:
    ../../../semi-formal-experiment/.venv/bin/python \
        _debug_gen11/preflight_replay/replay_freeze.py

What it does: for every stored chain (one clause in one run) it walks the
assistant turns of `<clause>.transcript.json` in order and applies the EXACT
rule from `translate.repair_loop`:

    seen = {_reply_hash(attempt_1_reply)}
    for each later reply r:
        if _reply_hash(r) not in seen: seen.add(...); continue
        -> FIRE.  first fire = restart (chain discarded, redrawn at attempt 1)
        -> second fire in the same chain = refreeze (abandon, flag `frozen`)

`_reply_hash` is imported from translate.py, not re-implemented, so the
normalisation is whatever the shipping code does (sha1 of exact utf-8 bytes,
no normalisation at all).

IMPORTANT SEMANTIC NOTE, stated once and relied on everywhere below:
a stored chain has NO restart in it (the policy did not exist when it ran).
So the replay can only ever observe the FIRST fire directly. Everything after
the first fire in a stored chain is what the OLD policy did with a chain that
the NEW policy would have thrown away. That is why:
  * "would restart" is MEASURED,
  * "would then refreeze" is NOT measurable offline (the redraw is a new
    sample from a live model) and is reported as `post_restart_unknown`,
  * a chain that fires TWICE in the stored transcript is evidence about the
    old continued chain, not about the new one; it is reported separately as
    `repeat_fires_in_stored_chain` and is the closest offline proxy for the
    refreeze population.
"""
import argparse
import collections
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, PHASE1)

import translate  # noqa: E402  (the shipping implementation, not a copy)

RUN_GLOBS = (
    "runs/*/run.json",
    "resolve_runs/graph_v2/translation_sample/runs/*/run.json",
)


def chains():
    """Yield one dict per stored chain, in run order."""
    for pattern in RUN_GLOBS:
        for rj in sorted(glob.glob(os.path.join(PHASE1, pattern))):
            root = os.path.dirname(rj)
            run = os.path.basename(root)
            corpus = "runs" if "/translation_sample/" not in rj else "sample"
            data = json.load(open(rj, encoding="utf-8"))
            for res in data.get("results", []):
                cid = res.get("clause_id")
                tp = os.path.join(root, cid + ".transcript.json")
                if not os.path.exists(tp):
                    yield dict(run=run, corpus=corpus, clause=cid,
                               status=res.get("status"),
                               attempts=res.get("attempts"),
                               replies=None, truncated=None,
                               reason="no stored transcript")
                    continue
                turns = json.load(open(tp, encoding="utf-8"))
                replies = [m["content"] for m in turns
                           if m.get("role") == "assistant"]
                # Pre-9388554 runs ended the transcript on our question, so
                # the final assistant reply was never stored. Detect by
                # comparing against the recorded attempt count.
                trunc = (res.get("attempts") is not None
                         and len(replies) < res["attempts"])
                yield dict(run=run, corpus=corpus, clause=cid,
                           status=res.get("status"),
                           attempts=res.get("attempts"),
                           replies=replies, truncated=trunc, reason=None)


def replay(replies):
    """Apply repair_loop's repeat rule. Returns (first_fire_at, all_fires).

    `first_fire_at` is the 1-based attempt NUMBER of the reply that repeats an
    earlier one (i.e. the attempt whose result is discarded), or None.
    `all_fires` lists every attempt number in the stored chain that repeats an
    earlier reply -- see the module docstring for why the 2nd+ entries are
    proxy evidence only.
    """
    if not replies:
        return None, [], None
    seen = {translate._reply_hash(replies[0])}
    fires, repeated_of = [], None
    for i, r in enumerate(replies[1:], start=2):
        h = translate._reply_hash(r)
        if h in seen:
            fires.append(i)
            if repeated_of is None:
                # which earlier attempt did it repeat?
                repeated_of = 1 + next(
                    j for j, p in enumerate(replies[:i - 1])
                    if translate._reply_hash(p) == h)
        else:
            seen.add(h)
    return (fires[0] if fires else None), fires, repeated_of


SUCCESS = ("translated",)
FAILURE = ("unrepaired", "invalid_module")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="write the full per-chain table here")
    args = ap.parse_args()

    rows = []
    for ch in chains():
        first, fires, of = replay(ch["replies"] or [])
        ch = dict(ch)
        ch.pop("replies")
        ch.update(n_replies=None if ch["reason"] else None,
                  fire_at=first, fires=fires, repeated_attempt=of)
        rows.append(ch)
    # re-walk to record reply counts + the repeated text, needed for reporting
    detail = {}
    for ch in chains():
        if ch["replies"] is None:
            continue
        first, fires, of = replay(ch["replies"])
        detail[(ch["run"], ch["clause"])] = dict(
            n_replies=len(ch["replies"]),
            distinct=len({translate._reply_hash(r) for r in ch["replies"]}),
            repeated_text=(ch["replies"][first - 1] if first else None))
    for r in rows:
        r.update(detail.get((r["run"], r["clause"]), {}))

    usable = [r for r in rows if r["reason"] is None]
    notrans = [r for r in rows if r["reason"]]
    trunc = [r for r in usable if r["truncated"]]

    print("=" * 78)
    print("CHECK 1 — restart-on-repeat replay over every stored transcript")
    print("=" * 78)
    print(f"stored results:            {len(rows)}")
    print(f"  with a transcript:       {len(usable)}")
    print(f"  no transcript on disk:   {len(notrans)}  "
          f"(statuses: {dict(collections.Counter(r['status'] for r in notrans))})")
    print(f"  transcript truncated:    {len(trunc)}  "
          "(pre-9388554: last reply never stored; a fire could be MISSED)")
    print()

    multi = [r for r in usable if (r["n_replies"] or 0) > 1]
    fired = [r for r in multi if r["fire_at"]]
    print("--- 1. BLAST RADIUS ---")
    print(f"chains with >1 attempt:              {len(multi)}")
    print(f"  would restart (>=1 repeat):        {len(fired)}"
          f"  = {100.0 * len(fired) / max(1, len(multi)):.1f}%")
    print(f"as a fraction of ALL {len(usable)} chains: "
          f"{100.0 * len(fired) / max(1, len(usable)):.1f}%")
    extra_calls = sum(r["fire_at"] for r in fired)  # discarded calls, lower bd
    print(f"calls the restart DISCARDS (sum of fire attempt no.): {extra_calls}")
    print()

    print("--- 2. RESTARTS ON CHAINS THAT EVENTUALLY SUCCEEDED (blocking) ---")
    fp = [r for r in fired if r["status"] in SUCCESS]
    print(f"count: {len(fp)}")
    for r in sorted(fp, key=lambda r: (r["corpus"], r["run"], r["clause"])):
        print(f"  * {r['corpus']}/{r['run']} {r['clause']}: "
              f"fires at attempt {r['fire_at']} (repeat of attempt "
              f"{r['repeated_attempt']}), chain ran {r['n_replies']} attempts "
              f"({r['distinct']} distinct), FINAL OUTCOME {r['status']}")
    print()

    print("--- 3. RESTARTS ON CHAINS THAT FAILED (the upside) ---")
    for st in FAILURE + ("abstained_under_repair",):
        pop = [r for r in multi if r["status"] == st]
        f = [r for r in pop if r["fire_at"]]
        print(f"  {st:24s} multi-attempt {len(pop):4d}  would restart {len(f):4d}"
              f"  ({100.0 * len(f) / max(1, len(pop)):.0f}%)")
    print()
    print("  CHAIN_ANALYSIS 9%/98% replication, all multi-attempt chains:")
    rep = [r for r in multi if r["fire_at"]]
    dis = [r for r in multi if not r["fire_at"]]
    for name, pop in (("repeats an earlier reply", rep),
                      ("all replies distinct", dis)):
        ok = [r for r in pop if r["status"] in SUCCESS]
        print(f"    {name:26s} n={len(pop):4d}  translated {len(ok):4d}"
              f"  ({100.0 * len(ok) / max(1, len(pop)):.0f}%)")
    print()

    print("--- 4. SECOND FIRE IN THE STORED CHAIN (refreeze proxy) ---")
    twice = [r for r in fired if len(r["fires"]) > 1]
    print(f"chains whose stored continuation repeats again: {len(twice)}"
          f" of {len(fired)} fired")
    print("  NB: this is the OLD policy's continuation, not the new policy's")
    print("  redraw. The true refreeze rate needs a live redraw and CANNOT be")
    print("  measured offline. Reported as an upper bound on 'sticky' clauses.")
    print()

    print("--- by corpus ---")
    for corpus in ("runs", "sample"):
        m = [r for r in multi if r["corpus"] == corpus]
        f = [r for r in m if r["fire_at"]]
        print(f"  {corpus:8s} multi-attempt {len(m):4d}  fire {len(f):4d}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=1, default=str)
        print(f"\nper-chain table -> {args.json}")


if __name__ == "__main__":
    main()
