#!/usr/bin/env python3
"""Automated stage-4 semantic gate — DeepSeek two-pass critique with an
alarm queue for frontier audit. owner directive (2026-08-16, unattended block):
step 4 must run fully automated on the cheap tier, using disagreement /
volume / truncation across parallel runs as the routing signal (logprobs
are unavailable for this model on this provider), putting suspects into a
graveyard-like queue that Fable-tier auditors drain asynchronously.

Per translated module (newest artifact per node, corpus_gate.gather):
  * TWO independent unforced critique passes (unforced deliberately:
    reasoning_chars was a perfect format-forcing discriminator in the arm
    series — forcing removes the thing that diagnoses). Same prompt, fresh
    draws; provider sampling gives independence.
  * Signals per pass: FIX-line count; truncation (a critique that overflows
    the cap is itself an alarm, recorded as count 99, never retried).
  * score = max(count_1, count_2); disagreement = |count_1 - count_2|.
  * score >= THRESHOLD -> write-once queue entry in semantic_queue/
    (one JSON per module, graveyard shape: never overwritten, drained by
    a frontier auditor who appends its verdict to the same file).

HONESTY BLOCK — what this gate is and is not:
  * The arm series measured single-pass cheap-critic identification at
    ~21% against a frozen key. Two-pass volume routing is calibrated on
    n=20 labeled modules (3 defective) via cheap_alarm_probe.py — weak
    power. This gate is a ROUTER, not a verdict.
  * The per-chunk RANDOM Fable sample (RUNTIME_WATCH.md watcher 1)
    therefore stays: it is the measurement of this gate's miss rate, and
    the 85% floor rides on it, not on this gate.
  * Every call is billed to usage.jsonl under run tag semantic_gate.

Resumable: modules with a row in semantic_gate_report.jsonl are skipped, so
a polling loop can call this repeatedly while translation lands.

Usage:
  .../.venv/bin/python semantic_gate.py --all-ungated [--limit N]
  .../.venv/bin/python semantic_gate.py --ids l1_170_n003 ...
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, PHASE1)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "behavior_pilot"))

import corpus_gate      # noqa: E402
import live_pilot       # noqa: E402
import translate        # noqa: E402

REPORT = os.path.join(HERE, "semantic_gate_report.jsonl")
QUEUE = os.path.join(HERE, "semantic_queue")
PASSES = 2
MAX_TOKENS = 3000
#: ⛔ CALIBRATION VERDICT (cheap_alarm_probe.json, 2026-08-17): NOT USABLE.
#: Under the pre-stated rule (all 3 known-defective modules in the top 8 by
#: FIX volume), volume routing caught 1/3. The ranking is worse than a
#: miss: the top two scores were FAITHFUL modules whose critiques overflowed
#: the token cap, while all three defective modules drew 1-2 FIX lines —
#: the cheap critic says MORE about good modules than broken ones. Third
#: independent confirmation of the same lesson (free mechanical flags:
#: 14/20 flagged, 2/3 defects missed; arm-series cheap-critic ID ~21%;
#: triage arm's shared-alarm inversion). THRESHOLD therefore stays None and
#: this gate stays UNDEPLOYED; the per-chunk random Fable sample is the
#: only stage-4 instrument.
#:
#: Recalibration path, not a dead end: every per-chunk random audit adds ~6
#: labeled modules, so the bulk run itself grows the labeled set to ~60.
#: Re-run cheap_alarm_probe.py against that set (same pre-stated rule,
#: proportional review budget) before considering deployment again.
THRESHOLD = None   # NOT USABLE per calibration; the gate refuses to run

BRIEF = (
 "You review one ASP translation of a specification clause. Compare the "
 "MODULE against the SPAN it translates. List every discrepancy you find "
 "as its own line starting with 'FIX:', covering: normative content the "
 "span states that the module does not encode; content the module asserts "
 "that the span does not state; a status/polarity that mis-renders the "
 "span (preference vs prohibition, conditional vs unconditional, an "
 "exclusivity or exception lost). Quote the decisive words. If the module "
 "is faithful, output exactly 'NO FINDINGS'. Do not propose remedies; "
 "findings only.")

_FIX = re.compile(r"^\s*(?:[-*\d.\s]*)FIX:", re.M)


def gated_ids():
    if not os.path.exists(REPORT):
        return set()
    out = set()
    for ln in open(REPORT):
        if ln.strip():
            out.add(json.loads(ln)["id"])
    return out


def one_pass(complete, span, o):
    user = ("SPAN (what the module must be faithful to):\n" + span[:6000]
            + "\n\nMODULE:\n" + json.dumps(
                {k: o.get(k) for k in ("claims", "acts", "concepts",
                                       "ontology", "asserts", "beats",
                                       "defines", "closure", "requires",
                                       "inputs", "forbid_body")},
                indent=1)[:8000]
            + "\n\nList discrepancies.")
    try:
        env = complete(BRIEF, user)
        text = env.get("text", "") if isinstance(env, dict) else str(env)
        return {"fix_count": len(_FIX.findall(text)), "truncated": False,
                "text": text[:2000]}
    except Exception as ex:                        # noqa: BLE001
        if "TRUNCATED" not in repr(ex):
            raise
        return {"fix_count": 99, "truncated": True, "text": repr(ex)[:300]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--all-ungated", action="store_true")
    g.add_argument("--ids", nargs="*")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args(argv)

    if THRESHOLD is None:
        raise SystemExit("THRESHOLD is None — the gate refuses to run "
                         "uncalibrated. Set it from cheap_alarm_probe.json.")

    done = gated_ids()
    gathered = corpus_gate.gather()
    if args.ids:
        todo = [(c, gathered[c]) for c in args.ids if c in gathered]
    else:
        todo = [(c, v) for c, v in sorted(gathered.items())
                if c not in done and v[0].get("outcome") == "translated"]
    if args.limit:
        todo = todo[:args.limit]
    if not todo:
        print("nothing ungated")
        return 0

    os.makedirs(QUEUE, exist_ok=True)
    complete = live_pilot.seat_client(max_tokens=MAX_TOKENS)
    complete.client.cfg["model"]["format_forcing"] = "none"
    complete.client.forcing = "none"
    translate.set_run_tag("semantic_gate")

    n_q = 0
    for cid, (o, span, run) in todo:
        passes = [one_pass(complete, span, o) for _ in range(PASSES)]
        score = max(p["fix_count"] for p in passes)
        row = {"id": cid, "run": run, "score": score,
               "disagreement": abs(passes[0]["fix_count"]
                                   - passes[1]["fix_count"]),
               "queued": score >= THRESHOLD,
               "fix_counts": [p["fix_count"] for p in passes]}
        with open(REPORT, "a") as f:
            f.write(json.dumps(row) + "\n")
        if row["queued"]:
            qp = os.path.join(QUEUE, cid + ".json")
            if not os.path.exists(qp):      # write-once, graveyard rule
                with open(qp, "w") as f:
                    json.dump({"id": cid, "run": run, "score": score,
                               "passes": passes,
                               "frontier_verdict": None}, f, indent=1)
                n_q += 1
        print(f"  {cid:20s} fixes={row['fix_counts']} "
              f"{'-> QUEUED' if row['queued'] else 'pass'}")
    c = complete.client
    print(f"gated {len(todo)} module(s), queued {n_q}, "
          f"spent ${c.spent_usd:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
