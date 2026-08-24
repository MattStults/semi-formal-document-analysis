#!/usr/bin/env python3
"""iteration1_triage.py — STEP 1 (TRIAGE) of CALCULUS_RUNBOOK iteration 1.

Batch: the 12 indefensible engaged-FPs of how-to-approach-tradeoffs
(GEN_BLOCK1_SCORED.json, results.how-to-approach-tradeoffs.misses.engaged_FP)
— attempt-2 repair routing under the signed generalization prereg.

WHY THIS DRIVER EXISTS (recorded as an iteration-1 runbook erratum): the
runbook's STEP 1 command `route.py <slug> <node>` assumes the slug is known
to the maintained truth assembly (SC.truth_all's fmap). The generalization
behaviours' truth lives in the attempt-1 lineage-venue artifacts
(GEN_BLOCK1_SCORED.json + panel_run1/fresh_draw4/gen_*_rulings.json), which
truth_all does not read — route.py bare therefore KeyErrors. Precedent:
route_validate.py case (e) routes generalization slugs via route()'s ctx
port-record mechanism. This driver does the same, but keeps the census REAL
rather than ctx-asserted:

  1. derives a single-module contract (iteration1_tradeoffs_contract.json)
     by projecting how-to-approach-tradeoffs out of
     modules_contract_GENERALIZATION.json (same wrapper schema as v19);
  2. injects the FROZEN attempt-1 truth (40 verdicts) into SC.truth_all for
     exactly this slug — attempt-1 verdicts are read, never written
     (the transfer claim is frozen; this is consumption, not revision);
  3. runs SC.census unmodified on the derived contract (real SEPARABLE /
     UNSAT certificates over the 40-node truth set);
  4. calls route.route() per batch node with ctx.truth_tier taken from the
     committed ruling artifacts (panel = a gen_*_panel_{A,B,C} 3-seat
     majority exists; single = wave-seat only);
  5. emits ITERATION1_ROUTED_QUEUE.json with the A5 batch grouping
     (inventory-level moves sequenced before dependent C-D deltas).

Deterministic; $0; no seat is invoked.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import satisfiability_census as SC
import route as R

SLUG = "how-to-approach-tradeoffs"
SCORED = "GEN_BLOCK1_SCORED.json"
GEN_CONTRACT = "modules_contract_GENERALIZATION.json"
DERIVED_CONTRACT = "iteration1_tradeoffs_contract.json"
FD4 = os.path.join("panel_run1", "fresh_draw4")

# R2 (post-escalation): the R1 escalation panel's majorities supersede the
# single-wave entries FOR THE REPAIR LEDGER (the attempt-1 transfer claim
# stays frozen). When the result file exists the driver overlays it, routes
# only the still-standing FPs, and writes the r2 queue.
ESCALATION_RESULT = os.path.join(FD4, "ITER1_TRADEOFFS_ESCALATION_RESULT.json")
QUEUE_OUT = ("ITERATION1_ROUTED_QUEUE_R2.json"
             if os.path.exists(os.path.join(HERE, ESCALATION_RESULT))
             else "ITERATION1_ROUTED_QUEUE.json")


def derive_contract():
    src = json.load(open(os.path.join(HERE, GEN_CONTRACT)))
    entry = src["modules"][SLUG]
    out = {
        "_provenance": (
            "iteration1_triage.py: projection of " + SLUG + " out of "
            + GEN_CONTRACT + " (sha " + (R.sha(GEN_CONTRACT) or "?") + ") so "
            "SC.census can run single-module with attempt-1 truth injected. "
            "The module dict is byte-identical to the source entry."),
        "modules": {SLUG: entry},
    }
    p = os.path.join(HERE, DERIVED_CONTRACT)
    json.dump(out, open(p, "w"), indent=1)
    return p


def attempt1_truth():
    d = json.load(open(os.path.join(HERE, SCORED)))
    t = dict(d["results"][SLUG]["verdicts"])
    p = os.path.join(HERE, ESCALATION_RESULT)
    if os.path.exists(p):
        t.update(json.load(open(p))["truth"])
    return t


def batch():
    d = json.load(open(os.path.join(HERE, SCORED)))
    fps = list(d["results"][SLUG]["misses"]["engaged_FP"])
    p = os.path.join(HERE, ESCALATION_RESULT)
    if os.path.exists(p):
        esc = json.load(open(p))["truth"]
        # OVERTURN -> C-T resolved: no longer a mismatch, drops from the queue
        fps = [n for n in fps if esc.get(n) != "relevant"]
    return fps


def truth_tier_gen(node):
    """(tier, artifact, detail) from the committed attempt-1 ruling files."""
    panels = {}
    for L in "ABC":
        f = os.path.join(FD4, f"gen_{SLUG}_panel_{L}_rulings.json")
        panels[L] = json.load(open(os.path.join(HERE, f)))["rulings"]
    wave_f = os.path.join(FD4, f"gen_{SLUG}_wave_rulings.json")
    wave = json.load(open(os.path.join(HERE, wave_f)))["rulings"]
    if os.path.exists(os.path.join(HERE, ESCALATION_RESULT)):
        esc = json.load(open(os.path.join(HERE, ESCALATION_RESULT)))
        if node in esc["truth"]:
            row = next(r for r in esc["panel"] if r["node"] == node)
            return "panel", ESCALATION_RESULT, \
                {"panel_verdicts": row["seat_verdicts"]}
    if node in panels["A"]:
        vs = [panels[L][node]["verdict"] for L in "ABC"]
        art = os.path.join(FD4, f"gen_{SLUG}_panel_A_rulings.json")
        return "panel", art, {"panel_verdicts": vs}
    if node in wave:
        return "single", wave_f, {"wave_verdict": wave[node]["verdict"]}
    return "absent", None, {}


def main():
    contract_path = derive_contract()
    contract = os.path.basename(contract_path)

    # truth injection: frozen attempt-1 verdicts, read-only consumption
    frozen = attempt1_truth()
    orig_truth_all = SC.truth_all

    def truth_all(slug):
        if slug == SLUG:
            return dict(frozen)
        return orig_truth_all(slug)

    SC.truth_all = truth_all

    census = SC.census(contract)  # real certificates over the 40-node set
    rows = census.get(SLUG, {})

    queue = []
    for node in batch():
        tier, art, detail = truth_tier_gen(node)
        ctx = {
            "truth_tier": tier,
            "note": ("iteration-1 tradeoffs FP batch; truth = frozen "
                     "attempt-1 lineage venue; tier from " + str(art)),
        }
        res = R.route(SLUG, node, contract, ctx)
        res["truth_tier"] = tier
        res["truth_tier_artifact"] = art
        res["truth_tier_detail"] = detail
        res["census_row"] = rows.get(node)
        queue.append(res)

    # A5 grouping: inventory-level moves (I1/I3) sequence before C-D deltas
    order = {"C-I(I1)": 0, "C-I(I2)": 1, "C-I(I3)": 2, "C-D": 3,
             "C-V": 3, "C-T": 3}
    groups = {}
    for r in queue:
        groups.setdefault(r["class"], []).append(r["node"])
    phases = sorted(groups, key=lambda c: order.get(c, 4))

    out = {
        "_": ("ITERATION 1 STEP-1 ROUTED QUEUE — 12 engaged-FPs of " + SLUG
              + " (attempt-2 repair; attempt-1 transfer verdicts frozen). "
              "Produced by iteration1_triage.py; census real (derived "
              "contract + injected frozen truth); A5 ordering: "
              "inventory-level classes first."),
        "contract": contract,
        "truth_source": SCORED + " results." + SLUG + ".verdicts (frozen)",
        "census_mismatch_count": len(rows),
        "a5_class_order": phases,
        "classes": groups,
        "queue": queue,
    }
    p = os.path.join(HERE, QUEUE_OUT)
    json.dump(out, open(p, "w"), indent=1)
    print("mismatches in census:", len(rows))
    for r in queue:
        cr = r["census_row"] or {}
        print(f"{r['node']}: tier={r['truth_tier']} class={r['class']} "
              f"census={r['census'].get('token')} "
              f"cur={cr.get('status')} reach={cr.get('status_reachable')} "
              f"port={r['judgment_port_or_none']}")
    print("wrote", p)


if __name__ == "__main__":
    main()
