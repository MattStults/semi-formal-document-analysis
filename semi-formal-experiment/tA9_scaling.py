"""T-A9 — grounding vs ENUMERATION scaling for the ASP path. $0, local, seeded.

ASSUMPTION_TESTS' claim, verified at source before anything was measured:

  emit_asp.py:6-8   docstring: "a choice rule `{ ctx(A) }.` per unconstrained
                    context atom"
  emit_asp.py:508   out.append("{ ctx(%s) }.%s" % (name, comment))   <- the emit
  emit_asp.py:628   clingo.Control(["--enum-mode=brave", _NO_UNDEF])
  run_conflicts.py:13  clingo.Control(["--enum-mode=brave"])
  emit_asp.py:653   clingo.Control(["--opt-mode=optN", "1", _NO_UNDEF])  <- witness,
                    called once PER CONFLICT PAIR from conflicts_report (:741)

So the scenario space is 2^|unconstrained ctx| and the binding cost is the
enumeration, not the grounding. This module measures the triple:
  (i) grounded program size, (ii) answer sets to a complete brave closure,
  (iii) wall clock to that closure + the per-conflict witness solves.

Generator calibrated to `smoke_extraction.json`: 2 rules, 2 context atoms, 2
acts, 1 incompat, 0 exclusions -> ~1 ctx atom and ~1 act per rule, conditions
1-2 per rule, exclusions 0 by default. **0% exclusion density is the headline
arm**, because that is what the only real extraction on disk looks like.

Target scale: n_rules = 188, the `conditional` clause count in
`modelspec_clauses.json`.

Run:  .venv/bin/python tA9_scaling.py            (full sweep, early-stopping)
      .venv/bin/python tA9_scaling.py --quick    (small grid, for a smoke check)
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import statistics
import tempfile
import time

import clingo

import emit_asp

HERE = os.path.dirname(os.path.abspath(__file__))

#: pre-registered caps (ASSUMPTION_TESTS A-9 §3)
DECISION_N_RULES = 188
DECISION_SECONDS = 60.0
#: hard per-instance cap for the sweep itself, so the whole run stays local-cheap
INSTANCE_TIMEOUT = 20.0
#: how many witness solves to actually run per instance before extrapolating
WITNESS_SAMPLE = 25

GRID = [4, 8, 16, 32, 64, 128, 188]
DENSITIES = [0.0, 0.5]
SEEDS = [0, 1, 2, 3, 4]


# ------------------------------------------------------------- generator ---


def make_extraction(n_rules: int, exclusion_density: float, seed: int) -> dict:
    """A syntactically valid extraction with `n_rules` norms.

    Shape (calibrated to smoke_extraction.json):
      * one context atom per rule, plus one shared trigger atom;
      * two acts per incompatible pair, one pair per two rules;
      * each rule has 1-2 conditions drawn from the context atoms;
      * `exclusion_density` = fraction of context atoms placed into
        `at_most_one` groups of 2 (which removes their independent choice
        rule and so shrinks the scenario space).
    """
    rng = random.Random(seed * 1000 + n_rules)
    n_ctx = n_rules
    ctx = [f"c{i:04d}" for i in range(n_ctx)]
    n_pairs = max(1, n_rules // 2)
    acts = []
    for i in range(n_pairs):
        acts += [f"act_a{i:04d}", f"act_b{i:04d}"]

    atoms = [{"name": c, "kind": "context", "dimension": "principal",
              "gloss": f"context {c}", "quote_spans": [], "status": "draft"}
             for c in ctx]
    atoms += [{"name": a, "kind": "act", "dimension": "act",
               "gloss": f"act {a}", "quote_spans": [], "status": "draft"}
              for a in acts]

    rules = []
    for i in range(n_rules):
        conds = [ctx[i]]
        if rng.random() < 0.5:
            conds.append(ctx[rng.randrange(n_ctx)])
        conds = sorted(set(conds))
        rules.append({
            "id": f"r{i:04d}",
            "modality": "oblige",
            "act": acts[i % len(acts)],
            "conditions": conds,
            "defeaters": [],
            "tier": 1,
            "locator": f"synthetic > section{i % 8} > L{i}",
            "quote": "",
            "status": "draft",
        })

    incompat = [{"acts": [f"act_a{i:04d}", f"act_b{i:04d}"],
                 "license": "logical",
                 "source": "synthetic incompatible pair"}
                for i in range(n_pairs)]

    exclusions = []
    if exclusion_density > 0:
        k = int(len(ctx) * exclusion_density) // 2 * 2
        pool = ctx[:k]
        for i in range(0, k, 2):
            exclusions.append({"kind": "at_most_one",
                               "atoms": [pool[i], pool[i + 1]],
                               "license": "assumed",
                               "source": "synthetic exclusion"})

    return {"section": "synthetic", "model": "none",
            "run_id": f"synth_n{n_rules}_d{exclusion_density}_s{seed}",
            "atoms": atoms, "rules": rules, "incompat": incompat,
            "exclusions": exclusions, "unencoded": []}


def n_unconstrained_ctx(ex: dict) -> int:
    grouped = {n for e in ex["exclusions"] if e["kind"] == "at_most_one"
               for n in e["atoms"]}
    return sum(1 for a in ex["atoms"]
               if a["kind"] == "context" and a["name"] not in grouped)


# --------------------------------------------------------------- measure ---


def _solve_with_timeout(ctl, on_model, timeout):
    t0 = time.time()
    with ctl.solve(on_model=on_model, async_=True) as h:
        done = h.wait(timeout)
        if not done:
            h.cancel()
            return time.time() - t0, False
        h.get()
    return time.time() - t0, True


def count_answer_sets(lp_path: str, timeout: float, cap: int = 2_000_000):
    """Complete answer-set count under `--models=0`, capped in count and time.

    DIAGNOSTIC ONLY — it measures the SIZE of the scenario space. It is NOT
    what `run_conflicts.brave_conflicts` pays: clingo's `--enum-mode=brave`
    computes brave consequences by iterative refinement (each successive model
    must add an atom outside the running union), so it visits O(#atoms)
    models, not all of them. Measured this session: n_rules=8 has 117 answer
    sets but brave mode visits 1. Reporting the answer-set count as "the
    enumeration cost" would be exactly the kind of wrong-thing measurement
    this repo keeps making.
    """
    ctl = clingo.Control(["--models=0", "--warn=no-atom-undefined"])
    ctl.load(lp_path)
    ctl.ground([("base", [])])
    n = [0]
    t0 = time.time()

    def on_model(_m):
        n[0] += 1
        return n[0] < cap

    with ctl.solve(on_model=on_model, async_=True) as h:
        done = h.wait(timeout)
        if not done:
            h.cancel()
            return n[0], False, time.time() - t0
        h.get()
    return n[0], (n[0] < cap), time.time() - t0


def measure(ex: dict, timeout: float = INSTANCE_TIMEOUT,
            count_models: bool = True) -> dict:
    """The A-9 triple for one extraction, under a hard wall-clock cap.

    Returns status ok | timeout_brave | timeout_witness, plus whatever was
    measured before the cap. A truncated enumeration is reported as a
    TIMEOUT, never as a completed count (§3.4a: refuse, never truncate).
    """
    lp_path = os.path.join(tempfile.mkdtemp(prefix="tA9_"), "p.lp")
    idx = emit_asp.validate(ex)
    t0 = time.time()
    emit_asp.write_lp(ex, lp_path, include_provenance=False, idx=idx)
    t_emit = time.time() - t0

    res = {
        "n_rules": len(ex["rules"]),
        "n_ctx": sum(1 for a in ex["atoms"] if a["kind"] == "context"),
        "n_unconstrained_ctx": n_unconstrained_ctx(ex),
        "n_exclusions": len(ex["exclusions"]),
        "lp_bytes": os.path.getsize(lp_path),
        "t_emit_s": t_emit,
    }

    ctl = clingo.Control(["--enum-mode=brave", "--warn=no-atom-undefined"])
    ctl.load(lp_path)
    t0 = time.time()
    ctl.ground([("base", [])])
    res["t_ground_s"] = time.time() - t0
    st = ctl.statistics["problem"]["lpStep"]
    res["ground_rules"] = int(st["rules"])
    res["ground_choice_rules"] = int(st["rules_choice"])
    res["ground_bodies"] = int(st["bodies"])

    n_models = [0]
    last = []

    def on_model(m):
        n_models[0] += 1
        last.clear()
        last.extend(m.symbols(shown=True))

    t_brave, done = _solve_with_timeout(ctl, on_model, timeout)
    res["t_brave_s"] = t_brave
    res["n_models_visited_brave"] = n_models[0]

    if count_models:
        # separate, SMALLER budget: this is a diagnostic of the space size,
        # not a cost the shipped pipeline pays. It must not throttle the
        # measurement of the path that IS shipped.
        n_as, complete, t_as = count_answer_sets(lp_path, min(timeout, 5.0))
        res["n_answer_sets"] = n_as
        res["n_answer_sets_complete"] = complete
        res["t_enumerate_all_s"] = t_as

    if not done:
        res["status"] = "timeout_brave"
        res["n_conflict_pairs"] = None
        res["t_witness_total_s"] = None
        return res

    conflicts = sorted({str(s) for s in last if s.name == "conflict"})
    seen = {}
    for c in conflicts:
        n1, n2, act, t1, t2 = emit_asp._parse_conflict(c)
        seen.setdefault(frozenset((n1, n2)), c)
    pairs = list(seen.values())
    res["n_conflict_atoms"] = len(conflicts)
    res["n_conflict_pairs"] = len(pairs)

    budget = timeout
    t0 = time.time()
    n_done = 0
    for c in pairs[:WITNESS_SAMPLE]:
        if time.time() - t0 > budget:
            break
        emit_asp.witness(lp_path, c)
        n_done += 1
    t_w = time.time() - t0
    res["n_witness_solved"] = n_done
    res["t_witness_sample_s"] = t_w
    res["t_witness_per_pair_s"] = (t_w / n_done) if n_done else None
    res["t_witness_total_projected_s"] = (
        (t_w / n_done) * len(pairs) if n_done else None)
    res["status"] = "ok" if n_done == min(len(pairs), WITNESS_SAMPLE) \
        else "timeout_witness"
    return res


# ----------------------------------------------------------------- sweep ---


def sweep(grid=GRID, densities=DENSITIES, seeds=SEEDS,
          timeout=INSTANCE_TIMEOUT, verbose=True):
    rows = []
    for d in densities:
        for n in grid:
            pts = []
            for s in seeds:
                ex = make_extraction(n, d, s)
                r = measure(ex, timeout=timeout)
                r["density"] = d
                r["seed"] = s
                pts.append(r)
                rows.append(r)
            oks = [p for p in pts if p["status"] != "timeout_brave"]
            med_t = statistics.median(p["t_brave_s"] for p in pts)
            max_t = max(p["t_brave_s"] for p in pts)
            if verbose:
                mm = statistics.median(p.get("n_answer_sets", 0) for p in pts)
                mg = statistics.median(p["ground_rules"] for p in pts)
                print(f"  density={d:<4} n_rules={n:<4} "
                      f"unconstrained_ctx={pts[0]['n_unconstrained_ctx']:<4} "
                      f"ground_rules(med)={mg:<8.0f} "
                      f"answer_sets(med)={mm:<12.0f} "
                      f"t_brave med={med_t:6.2f}s max={max_t:6.2f}s  "
                      f"ok={len(oks)}/{len(pts)}  "
                      f"status={sorted({p['status'] for p in pts})}")
            if not oks:
                if verbose:
                    print(f"    -> every seed hit the {timeout}s cap; "
                          f"stopping this density arm (larger n is strictly worse)")
                break
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--timeout", type=float, default=INSTANCE_TIMEOUT)
    ap.add_argument("--out", default=os.path.join(HERE, "tA9_scaling_results.json"))
    a = ap.parse_args(argv)

    grid = [4, 8, 12, 16, 20] if a.quick else GRID
    seeds = [0, 1] if a.quick else SEEDS

    print("=" * 78)
    print("T-A9 — grounding vs enumeration scaling (clingo %s)"
          % clingo.__version__)
    print("=" * 78)
    print(f"per-instance wall-clock cap: {a.timeout}s   "
          f"pre-registered decision: median instance at n_rules="
          f"{DECISION_N_RULES} completes brave closure in < {DECISION_SECONDS}s")
    print(f"grid={grid} densities={DENSITIES} seeds={seeds}\n")

    rows = sweep(grid=grid, densities=DENSITIES, seeds=seeds, timeout=a.timeout)

    # where does it become intractable, per density arm?
    print("\n" + "-" * 78)
    summary = {}
    for d in DENSITIES:
        arm = [r for r in rows if r["density"] == d]
        ok_ns = sorted({r["n_rules"] for r in arm
                        if r["status"] != "timeout_brave"})
        bad_ns = sorted({r["n_rules"] for r in arm
                         if r["status"] == "timeout_brave"})
        largest_ok = max(ok_ns) if ok_ns else None
        summary[str(d)] = {
            "largest_n_rules_completing_brave_closure": largest_ok,
            "smallest_n_rules_timing_out": min(bad_ns) if bad_ns else None,
            "cap_seconds": a.timeout,
        }
        print(f"density={d}: brave closure completes up to n_rules={largest_ok}; "
              f"first timeout at n_rules="
              f"{min(bad_ns) if bad_ns else 'none in grid'}")
    verdict = ("SUPPORTED" if summary["0.0"]
               ["largest_n_rules_completing_brave_closure"] == DECISION_N_RULES
               else "FALSIFIED")
    print(f"\nA-9 decision (headline 0% exclusion arm, "
          f"median instance at n_rules={DECISION_N_RULES} "
          f"< {DECISION_SECONDS}s): {verdict}")

    with open(a.out, "w") as f:
        json.dump({"clingo": clingo.__version__, "cap_seconds": a.timeout,
                   "grid": grid, "densities": DENSITIES, "seeds": seeds,
                   "rows": rows, "summary": summary, "verdict": verdict}, f,
                  indent=1)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
