#!/usr/bin/env python3
"""route_validate.py — ERROR_CALCULUS.md §9 HISTORICAL VALIDATION (v0).

Runs route.py retrospectively over five WELL-RECORDED historical case
classes and compares the predicted class / prescribed move against the
recorded resolution. Deterministic replay, no seats, ~$0.

  (a) the 29-row defensibility batch      ruling_packets/defensibility_rulings.json
  (b) the round-4 helpfulness canary      ROUND4_HELP_CANARY_RESULT.json
      misses + their separability         R4_FP_SEPARABILITY.json
  (c) the 9b purpose deltas               9B_DESIGN_ROUND.md /
                                          panel_run1/convergence/ARITHMETIC_9B_RESULT.json
  (d) the subtype-mint colliders          test_satisfiability_census.py pins
  (e) the F1 generalization build repair  GENERALIZATION_BUILD_SPEC.md erratum

Each case emits its trace in the calculus_model / calculus.lp state format;
trace_check.check_trace (imported, NOT re-implemented) certifies every trace
is a legal path of the same clingo machine that verified the calculus.

MISMATCHES ARE FINDINGS. Routing is never adjusted to force a match; a
divergence between the calculus's prescription and what history did is
exactly what §9 was built to surface ("failures of (a)-(c) are calculus
bugs, found for free").

Usage: .../.venv/bin/python route_validate.py
"""
import json, os, sys, copy

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)                     # trace_check.py opens calculus.lp by name
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import route as R
import satisfiability_census as SC
import relevance_by_act as RBA
import trace_check as TC           # clingo trace-legality checker

OUT = os.path.join(HERE, "ROUTE_VALIDATION_V0.json")

ROWS = []
FINDINGS = []


def emit(case_id, case_class, result, recorded, match, basis, extra=None):
    """Record one validated case: route, certify its trace, compare."""
    viols = TC.check_trace(R.trace_tuples(result)) if result["trace"] else []
    row = {
        "case_id": case_id,
        "case_class": case_class,
        "behaviour": result["behaviour"],
        "node": result["node"],
        "contract": result["contract"],
        "predicted_class": result["class"],
        "predicted_move": result["prescribed_move"],
        "judgment_port": result["judgment_port_or_none"],
        "predicted_terminal": result["predicted_terminal"],
        "recorded_resolution": recorded,
        "match": "MATCH" if match else "MISMATCH",
        "match_basis": basis,
        "trace_certified": not viols,
        "trace_violations": viols,
        "census": result["census"],
        "trace": result["trace"],
    }
    # carry through anything the router attached beyond the standard fields
    # (terminality receipts, truth tier, faithfulness note, post-mint census)
    std = {"behaviour", "node", "contract", "inventory", "class",
           "prescribed_move", "judgment_port_or_none", "predicted_terminal",
           "census", "trace"}
    rd = {k: v for k, v in result.items() if k not in std}
    if rd:
        row["router_detail"] = rd
    if extra:
        row.update(extra)
    ROWS.append(row)
    return row


# ===================================================================== (a)
def case_a():
    """The 29-row defensibility batch. Recorded resolution: ONE rescue
    (helpfulness::l427_460_n003 -> truth flip, C-T) and 28 stands.

    Replay premise: the batch IS the R1 truth-solidity check (the pinned
    one-pass defensibility brief is a P1 seat). Truth tiers are therefore
    read PRE-batch (exclude_defensibility=True) — scoring the batch's own
    output as its input would beg the question.

    MATCH criterion: the router's FIRST move is the P1 truth check, and the
    class follows the recorded port outcome (C-T iff rescued)."""
    art = os.path.join("ruling_packets", "defensibility_rulings.json")
    d = json.load(open(os.path.join(HERE, art)))
    rescued = {u["node"] for u in d["truth_ledger_updates"]}
    for r in d["rulings"]:
        slug, node = r["behaviour"], r["node"]
        tier, tier_art = R.truth_tier(slug, node, exclude_defensibility=True)
        overturned = node in rescued
        ctx = {
            "truth_tier": tier,
            "panel_outcome": "overturn" if overturned else "stands",
            "panel_artifact": art,
            # the row is a break CREATED by a candidate delta: the delta
            # demonstrably separated this node, so SEPARABLE is the correct
            # certificate for the census slot (it is never read — R1 decides).
            "census": "sep",
            "census_artifact": art,
            "census_basis": ("break created by candidate delta "
                             f"'{r['delta']}'; the delta is the constructive "
                             "separability certificate (§2)"),
        }
        res = R.route(slug, node, "modules_contract_v19.json", ctx)
        if overturned:
            recorded = ("RESCUE: blind-Fable defensibility ruling RELEVANT "
                        "supersedes the 9b-arithmetic break classification "
                        "-> truth ledger update (C-T truth flip)")
            match = res["class"] == "C-T"
            basis = "predicted class C-T == recorded truth flip"
        else:
            recorded = (f"STANDS: ruling {r['ruling']} upheld; the "
                        f"'{r['delta']}' delta stays rejected (no rescue)")
            # first move must be the P1 truth check, and NO truth flip
            match = (res["trace"][0]["rule"] == "r1"
                     and tier != "panel"
                     and res["class"] != "C-T")
            basis = ("router prescribed the P1 truth check first and did not "
                     "predict a truth flip")
        emit(f"a:{slug}::{node}", "a_defensibility_batch", res, recorded,
             match, basis,
             extra={"delta": r["delta"], "seat_ruling": r["ruling"],
                    "panel_row": bool(r.get("panel")),
                    "truth_tier_pre_batch": tier,
                    "truth_tier_artifact": tier_art})


# ===================================================================== (b)
def case_b():
    """Round-4 helpfulness canary indefensible misses, routed at v19 with
    the R4 rulings in the ledger (panel tier -> R1 passes with no seat).

    Recorded per-node separability is already computed in
    R4_FP_SEPARABILITY.json; the recorded dispositions are:
      CURRENT-SEPARABLE  -> addressable by a declaration delta (C-D)
      CURRENT-UNSAT / REACHABLE-SEPARABLE -> addressable_by_declaration
                            (I-class, the reachable-only row)
      UNSAT both views   -> the two terminal canary nodes (I4 in §4's table)
    """
    art = "R4_FP_SEPARABILITY.json"
    rows = json.load(open(os.path.join(HERE, art)))["rows"]
    canary = json.load(open(os.path.join(HERE, "ROUND4_HELP_CANARY_RESULT.json")))
    fns = set(canary["indefensible_misses"]["not_engaged_FN"])
    for node, rec in sorted(rows.items()):
        cur = "SEPARABLE" if "CURRENT=SEPARABLE" in rec else "UNSAT"
        rch = "SEPARABLE" if "REACHABLE=SEPARABLE" in rec else "UNSAT"
        ctx = {}
        if cur == "UNSAT" and rch == "UNSAT":
            # the two terminal canary nodes: the Arc1-b act-refinement mint
            # is a recorded, inventory-level mint attempt that did NOT
            # separate them (they remain REACHABLE-UNSAT with the minted
            # marks in the vector). Replay with that one attempt consumed.
            ctx["mints_used"] = 1
        res = R.route("helpfulness", node, "modules_contract_v19.json", ctx)
        side = "FN" if node in fns else "FP"
        if cur == "SEPARABLE":
            recorded = ("CURRENT-SEPARABLE: addressable by a declaration "
                        "delta (declaration error, C-D)")
            match = res["class"] == "C-D"
            basis = "predicted C-D == recorded CURRENT-SEPARABLE disposition"
        elif rch == "SEPARABLE":
            recorded = ("CURRENT-UNSAT / REACHABLE-SEPARABLE: "
                        "addressable_by_declaration = True (inventory "
                        "insufficiency addressable by declaration; I-class)")
            match = res["class"].startswith("C-I(I")
            basis = "predicted an I-class == recorded addressable-by-declaration row"
        else:
            recorded = ("UNSAT in BOTH views: recorded as a terminal canary "
                        "node (§4 I4 historical instance, '2 terminal canary "
                        "nodes')")
            match = res["class"] == "C-I(I4)"
            basis = "predicted C-I(I4) == recorded terminal-by-document"
        emit(f"b:helpfulness::{node}", "b_round4_canary", res, recorded,
             match, basis,
             extra={"recorded_separability": rec, "canary_side": side})

    # SENSITIVITY (finding support, not scored): the same two UNSAT-both
    # rows with the mint budget fully exhausted.
    sens = {}
    for node, rec in sorted(rows.items()):
        if "CURRENT=UNSAT REACHABLE=UNSAT" not in rec:
            continue
        r2 = R.route("helpfulness", node, "modules_contract_v19.json",
                     {"mints_used": 2})
        sens[node] = {"class": r2["class"], "terminal": r2["predicted_terminal"],
                      "trace_certified": not TC.check_trace(R.trace_tuples(r2))}
    if sens:
        FINDINGS.append({
            "id": "F-b1",
            "title": "I4 requires an EXHAUSTED mint budget; the record "
                     "declared the two canary nodes terminal with one "
                     "inventory-level mint attempt on the books",
            "detail": "Routed with mints_used=1 (the Arc1-b act-refinement "
                      "mint, which left both rows REACHABLE-UNSAT) the "
                      "calculus prescribes R5 -> C-I(I3): mint again before "
                      "declaring terminal. With mints_used=2 it reaches "
                      "C-I(I4), matching the record. This is the §8 "
                      "inventory-qualifier rule biting: 'terminal' without "
                      "an inventory qualifier — and without a recorded mint "
                      "exhaustion — is a review finding. Either the record "
                      "should carry the exhaustion ruling (port P4) "
                      "explicitly, or MINT_BUDGET is mis-set at 2.",
            "sensitivity_mints_exhausted": sens})


# ===================================================================== (c)
def _charter(slug, base_contract, field, add):
    """probe.py's charter-arithmetic PATTERN applied at a chosen base
    contract: exact fixes/breaks of a candidate delta against the assembled
    truth ledger, plus the fix set (used to pick the delta's representative
    mismatch). Recomputed at TODAY's ledger — the recorded 9b numbers are
    reported alongside, never overwritten."""
    mods = json.load(open(os.path.join(HERE, base_contract)))["modules"]
    truth = SC.truth_all(slug)
    br, corpus = RBA.bridges(), RBA.corpus_acts()
    _, rel0 = RBA.relevance(mods[slug], br, corpus)
    m = copy.deepcopy(mods[slug])
    m[field] = sorted(set(m.get(field) or []) | {add})
    _, rel1 = RBA.relevance(m, br, corpus)
    e0, e1 = set(rel0), set(rel1)
    lost, gained = e0 - e1, e1 - e0
    fx = sorted([n for n in lost if truth.get(n) == "not_relevant"]
                + [n for n in gained if truth.get(n) == "relevant"])
    bk = sorted([n for n in lost if truth.get(n) == "relevant"]
                + [n for n in gained if truth.get(n) == "not_relevant"])
    return fx, bk


DELTAS_9B = [
    # (id, slug, field, value, disposition, recorded 9b arithmetic)
    ("PC-1 empowerment", "helpfulness", "purpose_concern", "empowerment",
     "ADOPTED", "TP+13 / FP+3 charter POSITIVE; adoption_consequence "
     "'ADOPTED FINAL (13/2 after rescue of l427_460_n003)'"),
    ("PC-2 harm-prevention", "avoiding-over-and-under-caution",
     "purpose_concern", "harm-prevention", "ADOPTED",
     "TP+3 / FP+1 charter POSITIVE; adoption_consequence "
     "'ADOPTED FINAL (3/1, no rescues)'"),
    ("PC-4 trust", "helpfulness", "purpose_concern", "trust", "REJECTED",
     "TP+7 / FP+9 charter NEGATIVE; 'FINALLY REJECTED (7/9, zero rescues)'"),
    ("PC-5 predictability-and-reliability", "helpfulness", "purpose_concern",
     "predictability-and-reliability", "REJECTED",
     "TP+6 / FP+12 charter NEGATIVE; 'FINALLY REJECTED (6/12, zero rescues)'"),
    ("PC-3 epistemic-autonomy", "avoiding-over-and-under-caution",
     "purpose_concern", "epistemic-autonomy", "REJECTED",
     "TP+3 / FP+4 charter NEGATIVE; 'FINALLY REJECTED (3/4, zero rescues)'"),
]


def case_c():
    """The 9b purpose deltas. Recorded: empowerment + harm-prevention adopted
    (C-D resolutions); trust, predictability-and-reliability and
    epistemic-autonomy killed at validation (C-D candidates that failed V1).

    The routing UNIT here is the delta; each is routed through a
    REPRESENTATIVE mismatch drawn from its measured fix set — a node the
    delta actually corrects, so the delta itself is that node's constructive
    SEPARABLE certificate (§2: 'SEPARABLE status IS the certificate that
    such a D exists')."""
    base = "modules_contract_v18.json"
    ordering_divergence = []
    for did, slug, field, val, disp, recorded_arith in DELTAS_9B:
        fx, bk = _charter(slug, base, field, val)
        if not fx:
            FINDINGS.append({"id": f"F-c-{did}", "title": "no fix set at "
                             "today's ledger; delta not routable",
                             "detail": recorded_arith})
            continue
        node = fx[0]
        tier, tier_art = R.truth_tier(slug, node, exclude_defensibility=True)
        if tier != "panel":
            ordering_divergence.append(f"{did}@{node}")
        ctx = {
            "truth_tier": tier,
            # history ran the delta FIRST and adjudicated the flips after
            # (9b V4 per-flip adjudication + the 2026-08-24 defensibility
            # batch, which upheld 28 of 29). Replayed as: ruling STANDS.
            "panel_outcome": "stands",
            "panel_artifact": os.path.join("panel_run1", "convergence",
                                           "ARITHMETIC_9B_RESULT.json"),
            "census": "sep",
            "census_artifact": base,
            "census_basis": (f"delta {field}+={val} corrects this node: "
                             f"measured at today's ledger fixes={len(fx)} "
                             f"breaks={len(bk)} on base {base}"),
            "delta_outcome": "validated" if disp == "ADOPTED" else "failed",
            "delta_artifact": os.path.join("panel_run1", "convergence",
                                           "ARITHMETIC_9B_RESULT.json"),
            # A6(d): attach verify_terminal.py's exhaustive move-space
            # enumeration as the constructive counterpart to the census
            # certificate. route.py calls it; nothing is re-implemented.
            "with_terminality": True,
        }
        res = R.route(slug, node, base, ctx)
        if disp == "ADOPTED":
            recorded = f"ADOPTED as a declaration delta (C-D). {recorded_arith}"
            match = (res["class"] == "C-D"
                     and res["predicted_terminal"] == "resolved_d")
            basis = "predicted C-D terminating at resolved_d == recorded adoption"
        else:
            recorded = (f"REJECTED at validation — charter-negative, zero "
                        f"rescues (C-D candidate killed at V1/V4). {recorded_arith}")
            match = (res["class"] == "C-D"
                     and res["predicted_terminal"] is None)
            basis = ("predicted C-D candidate consuming R3 budget without a "
                     "terminal == recorded kill at validation")
        emit(f"c:{did}", "c_9b_deltas", res, recorded, match, basis,
             extra={"delta_id": did, "delta": {field: f"+{val}"},
                    "representative_node": node,
                    "recomputed_charter_today": {"fixes": len(fx),
                                                 "breaks": len(bk)},
                    "recorded_charter_9b": recorded_arith,
                    "truth_tier_at_9b": tier,
                    "truth_tier_artifact": tier_art})
    if ordering_divergence:
        FINDINGS.append({
            "id": "F-c1",
            "title": "ORDERING DIVERGENCE: the 9b round executed R3 deltas "
                     "before discharging the R1 truth premise",
            "detail": "The calculus (§3 R1-first, amendment A5's EAGER "
                      "ordering theorem) requires the truth premise to be "
                      "discharged before any move that costs more than it "
                      "does. The 9b round ran the deltas first and "
                      "adjudicated the flips afterwards (V4 per-flip "
                      "adjudication, then the 2026-08-24 defensibility "
                      "batch). The record vindicates the calculus: that "
                      "deferred P1 pass overturned one ruling "
                      "(l427_460_n003), which changed the empowerment "
                      "delta's charter arithmetic AFTER adoption. A5's "
                      "'lazy also destroys the cheap best case' is the "
                      "measured form of the same point.",
            "deltas_whose_representative_node_was_single_tier":
                ordering_divergence})


# ===================================================================== (d)
COLLIDERS = [("helpfulness", "l797_830_n011"),
             ("harm-avoidance-to-third-parties", "l831_1000_n001"),
             ("harm-avoidance-to-third-parties", "l831_1000_n011")]


def case_d():
    """The subtype-mint colliders, pinned in test_satisfiability_census.py
    (test_m2_colliders_addressable_via_refinements). Recorded resolution:
    the Arc1-b I3 MINT (act_refinements_FINAL.json — provide:forbid.
    form_equivalence, exhibit:illustrate).

    Routed at v18 on the PRE-MINT inventory I_(k-1) (SC.load_refinements
    suppressed — same census code, one inventory feature withdrawn), which
    is the inventory state the mint decision was actually taken in."""
    for slug, node in COLLIDERS:
        tier, tier_art = R.truth_tier(slug, node, exclude_defensibility=True)
        ctx = {"inventory": "pre_mint",
               "truth_tier": tier,
               "panel_outcome": "stands",
               "panel_artifact": os.path.join("panel_run1", "convergence",
                                              "act_refinements_FINAL.json"),
               "mint_outcome": "reach",
               "mint_artifact": os.path.join("panel_run1", "convergence",
                                             "act_refinements_FINAL.json")}
        res = R.route(slug, node, "modules_contract_v18.json", ctx)
        recorded = ("I3 MINT (Arc1-b act refinements): the minted subtype "
                    "marks are declarable vocabulary, so the row becomes "
                    "addressable_by_declaration — pinned at v18 as "
                    "CURRENT-UNSAT / REACHABLE-SEPARABLE")
        match = res["class"] == "C-I(I3)" and res["judgment_port_or_none"] == "P3"
        emit(f"d:{slug}::{node}", "d_subtype_colliders", res, recorded, match,
             "predicted C-I(I3) at port P3 == recorded act-refinement mint",
             extra={"pin": "test_satisfiability_census.py::"
                           "test_m2_colliders_addressable_via_refinements",
                    "truth_tier": tier, "truth_tier_artifact": tier_art})

    # A4 CORROBORATION (finding support, not scored): the same three nodes
    # on the POST-mint inventory route to R4 (build the consumer) — exactly
    # the per-FEATURE re-entry amendment A4 was written to define.
    post = {}
    for slug, node in COLLIDERS:
        tier, _ = R.truth_tier(slug, node, exclude_defensibility=True)
        r2 = R.route(slug, node, "modules_contract_v18.json",
                     {"truth_tier": tier, "panel_outcome": "stands"})
        post[f"{slug}::{node}"] = {
            "class": r2["class"], "census": r2["census"]["token"],
            "trace_certified": not TC.check_trace(R.trace_tuples(r2))}
    FINDINGS.append({
        "id": "F-d1",
        "title": "A4 confirmed on the record: after the I3 mint the same "
                 "colliders re-enter at census=REACHABLE and route to R4 "
                 "(build the consumer), not back to R5",
        "detail": "Amendment A4 was added because a mint can produce a "
                  "distinction that is annotated but unconsumed. The three "
                  "colliders exhibit exactly that transition — pre-mint "
                  "UNSAT-both -> R5/I3, post-mint REACHABLE -> R4/I1 — so "
                  "A4 is not a modelling artefact but a recorded campaign "
                  "state.",
        "post_mint_routes": post})


# ===================================================================== (e)
GEN_MODULES = [("how-to-approach-tradeoffs", "tradeoffs"),
               ("user-autonomy", "user-autonomy"),
               ("proportionate-risk-mitigation", "proportionate-risk")]


def case_e():
    """The F1 generalization build repair. GENERALIZATION_BUILD_SPEC.md
    erratum (2026-08-22, adversarial review F1): 'Three builds (tradeoffs,
    user-autonomy, proportionate-risk) used bespoke names and engaged
    nothing; all repaired 2026-08-22 by canonical translation (rationale
    REPAIR ADDENDUMs; no new declarations).'

    The erratum IS the repair record, so R2 -> UNFAITHFUL -> R2b -> C-V.
    R1 is discharged without a seat: a module that engages ZERO nodes is a
    defect independent of any ruling, so the truth premise cannot be the
    cause."""
    art = "GENERALIZATION_BUILD_SPEC.md"
    for slug, name in GEN_MODULES:
        ctx = {
            "truth_tier": "panel",
            "audit_outcome": "unfaithful",
            "audit_artifact": art,
            "repair_artifact": art,
            "census": "sep",
            "census_artifact": "modules_contract_GENERALIZATION.json",
            "census_basis": "not reached: R2b terminates before the census",
            "note": ("R1 discharged without a seat: the build engaged ZERO "
                     "nodes, a defect independent of any ruling"),
        }
        res = R.route(slug, None, "modules_contract_GENERALIZATION.json", ctx)
        recorded = ("C-V translation-layer repair: bespoke `does` names "
                    "replaced by canonical translation (behavior_acts()-"
                    "accepted names); rationale REPAIR ADDENDUMs; NO new "
                    "declarations")
        match = (res["class"] == "C-V"
                 and res["predicted_terminal"] == "resolved_v")
        emit(f"e:{slug}", "e_f1_generalization_repair", res, recorded, match,
             "predicted C-V terminating at resolved_v == recorded "
             "translation-layer repair with no new declarations",
             extra={"module_as_named_in_erratum": name,
                    "erratum": art})
    FINDINGS.append({
        "id": "F-e1",
        "title": "C-V as written in Theorem 1 covers only the NODE vector "
                 "V(n); the F1 defect lives in the MODULE's does-name "
                 "rendering",
        "detail": "§2 defines C-V as 'V(n) is unfaithful — the translation "
                  "mis-states what the node claims'. The F1 erratum is a "
                  "translation defect on the other side of f: the "
                  "behaviour module's `does` entries were bespoke functor "
                  "names the canonical vocabulary does not accept, so the "
                  "module engaged nothing. The recorded resolution was a "
                  "translation repair with no new declarations — a C-V "
                  "move, not a C-D one. PROPOSED ERRATUM: C-V should read "
                  "'the TRANSLATION LAYER is unfaithful — the node vector "
                  "V(n) mis-states the node's claim, or the declaration "
                  "D(b) is rendered in names f cannot consume'. Without "
                  "that widening the partition mis-files this case as C-D "
                  "(a declaration error), whose prescribed move — a "
                  "mechanical delta — would have been wrong.",
        "affected_modules": [s for s, _ in GEN_MODULES]})


# =================================================================== main
def corpus_coverage_finding():
    """Surfaced for free by the replay: every OPEN(P2) row is a node the
    router refused to auto-discharge at R2 because it is not in the
    canonical ESTABLISHES corpus. Quantify it."""
    ids = R._corpus_establishes()
    absent = set()
    for slug in ("helpfulness", "harm-avoidance-to-third-parties",
                 "avoiding-over-and-under-caution"):
        absent |= {n for n in SC.truth_all(slug) if n not in ids}
    total = len({n for slug in ("helpfulness",
                                "harm-avoidance-to-third-parties",
                                "avoiding-over-and-under-caution")
                 for n in SC.truth_all(slug)})
    hit = sorted(r["node"] for r in ROWS if r["predicted_class"] == "OPEN(P2)")
    FINDINGS.append({
        "id": "F-r1",
        "title": "Truth-ledger nodes absent from node_corpus_all.json — R2 "
                 "cannot be auto-discharged for them",
        "detail": "route.py's R2 rule (a canonical-corpus node carrying an "
                  "ESTABLISHES claim is audited-faithful absent a repair "
                  "record) cannot fire for ledger nodes that are not in the "
                  "corpus at all, so the router correctly stops at port P2 "
                  "and prescribes the faithfulness audit rather than "
                  "assuming fidelity. The absent ids come from a SUPERSEDED "
                  "CHUNKING (e.g. l426_610_* and l1799_1973_* against the "
                  "corpus's l427_460_* and l1707_1973_*), i.e. the "
                  "assembled ledger carries rulings keyed to node ids the "
                  "current corpus no longer defines. This is a campaign "
                  "hygiene defect the §9 replay found for free; it is NOT a "
                  "calculus bug — the router's behaviour is the correct "
                  "one.",
        "ledger_nodes_total": total,
        "ledger_nodes_absent_from_corpus": len(absent),
        "absent_ids": sorted(absent),
        "cases_that_stopped_at_P2": hit})


def verify_terminal_finding():
    """A6(d) requires route.py to call verify_terminal.py for move-space
    exhaustion rather than re-implement it. Exercising it on the 9b rows
    exposes two defects in that component, both computed here."""
    import verify_terminal as VT
    ledger = {}
    for slug in ("helpfulness", "harm-avoidance-to-third-parties",
                 "avoiding-over-and-under-caution"):
        a, b = VT.truth_all(slug), SC.truth_all(slug)
        ledger[slug] = {
            "verify_terminal_nodes": len(a),
            "satisfiability_census_nodes": len(b),
            "missing_from_verify_terminal": len(set(b) - set(a)),
            "verdict_disagreements_on_shared_nodes":
                sorted(n for n in set(a) & set(b) if a[n] != b[n])}
    # which module fields verify_terminal.moves_for can enumerate at all
    fields = sorted({f for rows in
                     [VT.main("modules_contract_v18.json")[s]
                      for s in ("helpfulness",)]
                     for r in rows.values()
                     for rec in r.get("receipts", [])
                     for f in rec["move"]})
    contradicted = [r["case_id"] for r in ROWS
                    if r["case_class"] == "c_9b_deltas"
                    and (r.get("router_detail", {}).get("terminality") or {})
                    .get("verdict", "").startswith("TERMINAL")]
    FINDINGS.append({
        "id": "F-r2",
        "title": "verify_terminal.py — the component A6(d) designates as the "
                 "move-space authority — has a STALE LEDGER and an "
                 "INCOMPLETE MOVE SPACE",
        "detail": "(1) STALE LEDGER: verify_terminal.truth_all's fmap stops "
                  "at fresh_draw3 and carries no defensibility overlay, so "
                  "it misses the round-4 rulings entirely and still holds "
                  "the pre-rescue verdict for l427_460_n003 — it disagrees "
                  "with satisfiability_census.truth_all, which route.py's "
                  "census uses. Two components of the same router therefore "
                  "answer to two different T. (2) INCOMPLETE MOVE SPACE: "
                  "moves_for() enumerates only protects_concern and "
                  "governs_concern. It has NO purpose_concern move — the "
                  "exact slot the entire 9b round operated on. Consequence, "
                  "measured here: nodes the adopted empowerment / "
                  "harm-prevention deltas demonstrably FIXED are stamped "
                  "TERMINAL-STRUCT ('no declaration move can flip it') by "
                  "verify_terminal. A TERMINAL verdict from an enumerator "
                  "that cannot express the winning move is unsound, and §2's "
                  "partition leans on exactly that exhaustion certificate "
                  "to separate C-D from C-I. REQUIRED before route.py's R3/"
                  "R5 exhaustion may be trusted: re-point truth_all at "
                  "SC.truth_all and extend moves_for with purpose_concern "
                  "(and contexts_concern).",
        "ledger_comparison": ledger,
        "move_fields_verify_terminal_can_enumerate": fields,
        "9b_rows_stamped_TERMINAL_despite_an_adopted_fixing_delta":
            contradicted})


def main():
    case_a(); case_b(); case_c(); case_d(); case_e()
    corpus_coverage_finding()
    verify_terminal_finding()

    per_class = {}
    for r in ROWS:
        c = r["case_class"]
        d = per_class.setdefault(c, {"rows": 0, "match": 0, "mismatch": 0,
                                     "certified": 0, "predicted_classes": {}})
        d["rows"] += 1
        d["match" if r["match"] == "MATCH" else "mismatch"] += 1
        d["certified"] += 1 if r["trace_certified"] else 0
        d["predicted_classes"][r["predicted_class"]] = \
            d["predicted_classes"].get(r["predicted_class"], 0) + 1

    per_predicted = {}
    for r in ROWS:
        per_predicted[r["predicted_class"]] = \
            per_predicted.get(r["predicted_class"], 0) + 1

    n = len(ROWS)
    nm = sum(1 for r in ROWS if r["match"] == "MATCH")
    nc = sum(1 for r in ROWS if r["trace_certified"])
    doc = {
        "_": "ERROR_CALCULUS.md §9 historical validation of route.py "
             "(v0, deterministic replay, no seats, $0). Mismatches are "
             "FINDINGS, not failures: routing was never adjusted to force "
             "a match.",
        "generated_by": "route_validate.py",
        "router": "route.py (ERROR_CALCULUS.md §3 R1-R5 + amendments A1-A7)",
        "trace_checker": "trace_check.check_trace -> calculus.lp (clingo); "
                         "the same machine calculus_model.py and "
                         "mutate_calculus.py verified",
        "case_classes": {
            "a_defensibility_batch": "29-row blind-Fable defensibility batch "
                                     "(ruling_packets/defensibility_rulings.json)",
            "b_round4_canary": "round-4 helpfulness canary indefensible "
                               "misses (ROUND4_HELP_CANARY_RESULT.json + "
                               "R4_FP_SEPARABILITY.json)",
            "c_9b_deltas": "the five 9b purpose_concern deltas "
                           "(9B_DESIGN_ROUND.md / ARITHMETIC_9B_RESULT.json)",
            "d_subtype_colliders": "the three subtype-mint colliders pinned "
                                   "in test_satisfiability_census.py",
            "e_f1_generalization_repair": "the F1 build erratum "
                                          "(GENERALIZATION_BUILD_SPEC.md)",
        },
        "summary": {
            "total_cases": n,
            "matches": nm,
            "mismatches": n - nm,
            "match_rate": round(nm / n, 4) if n else None,
            "traces_certified": nc,
            "traces_uncertifiable": n - nc,
            "totals_per_case_class": per_class,
            "totals_per_predicted_class": per_predicted,
            "mismatch_list": [
                {"case_id": r["case_id"], "predicted_class": r["predicted_class"],
                 "predicted_move": r["predicted_move"],
                 "recorded_resolution": r["recorded_resolution"],
                 "match_basis": r["match_basis"]}
                for r in ROWS if r["match"] == "MISMATCH"],
            "uncertifiable_traces": [
                {"case_id": r["case_id"], "violations": r["trace_violations"]}
                for r in ROWS if not r["trace_certified"]],
        },
        "findings": FINDINGS,
        "cases": ROWS,
    }
    json.dump(doc, open(OUT, "w"), indent=1)
    s = doc["summary"]
    print(f"cases {s['total_cases']} | MATCH {s['matches']} "
          f"MISMATCH {s['mismatches']} | rate {s['match_rate']}")
    print(f"traces certified {s['traces_certified']}/{s['total_cases']}")
    for c, d in sorted(per_class.items()):
        print(f"  {c}: {d['rows']} rows, {d['match']} match, "
              f"{d['mismatch']} mismatch, {d['certified']} certified, "
              f"classes {d['predicted_classes']}")
    for m in s["mismatch_list"]:
        print("  MISMATCH", m["case_id"], "->", m["predicted_class"])
    print("findings:", [f["id"] for f in FINDINGS])
    print("wrote", OUT)


if __name__ == "__main__":
    main()
