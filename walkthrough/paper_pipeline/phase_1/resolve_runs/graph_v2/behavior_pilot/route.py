#!/usr/bin/env python3
"""route.py — THE ERROR-CALCULUS ROUTER (ERROR_CALCULUS.md §3, R1-R5).

Given a reported failure (behaviour_slug, node_id) plus recorded context
flags, compute the calculus route: truth tier (R1), faithfulness status
(R2), census verdict at a contract version (R3/R4/R5) — and emit

  {class, prescribed_move, judgment_port_or_none, trace}

where `class` is C-V | C-D | C-I(I1..I5) | C-T (Theorem 1's partition) and
`trace` is a list of steps in the calculus_model / calculus.lp state format

    s(Census, V, Panel, Aud, Retr, Built, Mints, Defens, Deltas)
    Census in {sep, reach, unsat}; V in {unaud, faith, unfaith}

each step carrying its rule name and an evidence pointer
{artifact_path, sha256, note} — the A6(c) trace-legality discipline, so
trace_check.check_trace can certify the emitted trace is a legal path of
the SAME clingo machine that verified the calculus.

REUSE (A6(d) reuse corrections — these components predate the calculus and
are its implementation base; route.py calls them, it does not re-implement):
  satisfiability_census.py  census verdicts (CURRENT + REACHABLE) and the
                            assembled truth ledger (truth_all)
  verify_terminal.py        exhaustive move-space enumeration / terminality
  trace_check.py            clingo trace legality (used by route_validate)
  probe.py                  charter arithmetic pattern for delta screening

DESIGN NOTE ON PORT OUTCOMES. The router is decidable, but R1's panel
outcome and R2's audit outcome are PORT events (Theorem 2, P1/P2): the
router cannot compute them. It therefore does one of two things at a port:
  * if the recorded outcome is supplied in ctx (retrospective REPLAY, §9),
    consume it and continue;
  * otherwise STOP at the port and prescribe the seat invocation, returning
    class "OPEN(P1)" / "OPEN(P2)".
This is what makes §9 replay honest: outcomes come from the record, routing
comes from the calculus.

Usage:
  route.py <behaviour_slug> <node_id> [modules_contract_vNN.json]
"""
import json, os, sys, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import satisfiability_census as SC          # census verdicts + truth_all
import verify_terminal as VT                # move-space exhaustion

GRAPH_V2 = os.path.dirname(HERE)
CORPUS_ALL = os.path.join(GRAPH_V2, "node_corpus_all.json")

DEFAULT_CONTRACT = "modules_contract_v19.json"

# ---------------------------------------------------------------- evidence

_SHA = {}


def sha(path):
    """Short sha256 of an artifact, for the trace's evidence pointer."""
    if path in _SHA:
        return _SHA[path]
    p = path if os.path.isabs(path) else os.path.join(HERE, path)
    try:
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()[:12]
    except OSError:
        h = None
    _SHA[path] = h
    return h


def ev(artifact_path, note):
    return {"artifact_path": artifact_path, "sha256": sha(artifact_path),
            "note": note}


# ------------------------------------------------------------------ state

def s(census, v, panel, aud, retr, built, mints, defens, deltas):
    return (f"s({census},{v},{panel},{aud},{retr},{built},"
            f"{mints},{defens},{deltas})")


# -------------------------------------------------------- R1: truth tier

# Provenance tiering (ERROR_CALCULUS §1 "T is the truth ledger: append-only
# rulings with provenance (seat-tier, brief-version)"). PANEL tier = rulings
# whose artifact records a multi-seat majority/unanimity; SINGLE tier =
# single-wave-only rulings. The R4 fresh_draw4 results self-describe as
# "FINAL panel-majority rulings ... 3-seat majorities"; panel_rerulings.json
# self-describes as "Panel re-adjudications ... REPLACE prior rulings".
PANEL_SOURCES = {
    "helpfulness": [os.path.join("panel_run1", "fresh_draw4", "HELP_R4_RESULT.json")],
    "harm-avoidance-to-third-parties": [os.path.join("panel_run1", "fresh_draw4", "HARM_R4_RESULT.json")],
    "avoiding-over-and-under-caution": [os.path.join("panel_run1", "fresh_draw4", "CAUTION_R4_RESULT.json")],
}
PANEL_RERULINGS = os.path.join("panel_run1", "panel_rerulings.json")
DEFENS_RULINGS = os.path.join("ruling_packets", "defensibility_rulings.json")

_TIER_CACHE = {}


def truth_tier(slug, node, exclude_defensibility=False):
    """-> (tier, artifact_path) with tier in {panel, single, absent}.

    exclude_defensibility: replay the tier as it stood BEFORE the 2026-08-24
    defensibility batch. Needed for §9 replay of that batch itself — the
    batch is what created those ledger entries, so scoring its own inputs
    against its own output would beg the question."""
    if exclude_defensibility:
        key = (slug, "pre_defens")
        if key not in _TIER_CACHE:
            panel, single = {}, {}
            for rel in PANEL_SOURCES.get(slug, []):
                p = os.path.join(HERE, rel)
                if os.path.exists(p):
                    for n in json.load(open(p))["truth"]:
                        panel[n] = rel
            p = os.path.join(HERE, PANEL_RERULINGS)
            if os.path.exists(p):
                for n in json.load(open(p))["rulings"].get(slug, {}):
                    panel[n] = PANEL_RERULINGS
            for n in SC.truth_all(slug):
                if n not in panel:
                    single[n] = "arm_ab.truth_for + truth_all fmap (single-wave)"
            _TIER_CACHE[key] = (panel, single)
        panel, single = _TIER_CACHE[key]
        if node in panel:
            return "panel", panel[node]
        if node in single:
            return "single", single[node]
        return "absent", None
    if slug not in _TIER_CACHE:
        panel, single = {}, {}
        for rel in PANEL_SOURCES.get(slug, []):
            p = os.path.join(HERE, rel)
            if os.path.exists(p):
                for n in json.load(open(p))["truth"]:
                    panel[n] = rel
        p = os.path.join(HERE, PANEL_RERULINGS)
        if os.path.exists(p):
            for n in json.load(open(p))["rulings"].get(slug, {}):
                panel[n] = PANEL_RERULINGS
        # defensibility overlay: rows carrying a "panel" field are panel tier,
        # single-seat defensibility rows are single tier.
        p = os.path.join(HERE, DEFENS_RULINGS)
        if os.path.exists(p):
            for r in json.load(open(p))["rulings"]:
                if r.get("behaviour") != slug:
                    continue
                (panel if r.get("panel") else single)[r["node"]] = DEFENS_RULINGS
        for n in SC.truth_all(slug):
            if n not in panel and n not in single:
                single[n] = "arm_ab.truth_for + truth_all fmap (single-wave)"
        _TIER_CACHE[slug] = (panel, single)
    panel, single = _TIER_CACHE[slug]
    if node in panel:
        return "panel", panel[node]
    if node in single:
        return "single", single[node]
    return "absent", None


# ------------------------------------------------- R2: faithfulness of V

_CORPUS_IDS = None
_REPAIRS = None


def _corpus_establishes():
    global _CORPUS_IDS
    if _CORPUS_IDS is None:
        cl = json.load(open(CORPUS_ALL))["clauses"]
        _CORPUS_IDS = {c["id"] for c in cl if "ESTABLISHES" in c.get("quote", "")}
    return _CORPUS_IDS


def _repair_records():
    """Node-level repair records: a translation repair that was REQUIRED
    (verdict other than APPROVE) is the 'repair record says otherwise'
    signal for R2."""
    global _REPAIRS
    if _REPAIRS is None:
        _REPAIRS = {}
        p = os.path.join(HERE, "t2_repair_verification.json")
        if os.path.exists(p):
            for v in json.load(open(p))["verdicts"]:
                if v.get("verdict") != "APPROVE" and v.get("node"):
                    _REPAIRS[v["node"]] = "t2_repair_verification.json"
    return _REPAIRS


def faithfulness(node):
    """-> (status, artifact_path, note). status in {faithful, unfaithful,
    unknown}. Rule: a node in the canonical corpus carrying an ESTABLISHES
    claim is audited-faithful unless a repair record says otherwise."""
    rep = _repair_records()
    if node in rep:
        return "unfaithful", rep[node], "repair record present"
    if node in _corpus_establishes():
        return "faithful", os.path.relpath(CORPUS_ALL, HERE), \
            "canonical corpus node carries an ESTABLISHES claim; no repair record"
    return "unknown", None, "node absent from the canonical ESTABLISHES corpus"


# -------------------------------------------------- R3/R4/R5: the census

_CENSUS_CACHE = {}


def census_at(contract, inventory="current"):
    """SC.census at a contract version. `inventory` selects the INVENTORY
    version I_k (ERROR_CALCULUS §8): "current" is the committed inventory;
    "pre_mint" replays the inventory BEFORE the Arc1-b act-refinement mint
    by suppressing SC.load_refinements — the same census code, one
    inventory feature withdrawn. Nothing is re-implemented and no artifact
    is mutated."""
    key = (contract, inventory)
    if key in _CENSUS_CACHE:
        return _CENSUS_CACHE[key]
    if inventory == "pre_mint":
        orig = SC.load_refinements
        SC.load_refinements = lambda: {}
        try:
            rep = SC.census(contract)
        finally:
            SC.load_refinements = orig
    else:
        rep = SC.census(contract)
    _CENSUS_CACHE[key] = rep
    return rep


def census_state(slug, node, contract, inventory="current"):
    """-> (census_token, detail). census_token in {sep, reach, unsat, none}
    where 'none' means the node is not a mismatch at this contract."""
    rep = census_at(contract, inventory)
    row = rep.get(slug, {}).get(node)
    if row is None:
        return "none", {"reason": "not a mismatch at this contract version"}
    cur, rch = row["status"], row["status_reachable"]
    if cur == "SEPARABLE":
        tok = "sep"
    elif rch == "SEPARABLE":
        tok = "reach"
    else:
        tok = "unsat"
    return tok, {"status": cur, "status_reachable": rch,
                 "addressable_by_declaration": row["addressable_by_declaration"],
                 "colliding_correct_nodes": row["colliding_correct_nodes"][:4]}


_TERMINALITY_CACHE = {}


def terminality(slug, node, contract):
    """verify_terminal.py's exhaustive move-space enumeration — the
    constructive counterpart to the census certificate (A6(d): route.py
    calls it, never re-implements R3/R5 exhaustion)."""
    if contract not in _TERMINALITY_CACHE:
        _TERMINALITY_CACHE[contract] = VT.main(contract)
    return _TERMINALITY_CACHE[contract].get(slug, {}).get(node)


# ------------------------------------------------------------- the router

CLASS_C_T = "C-T"
CLASS_C_V = "C-V"
CLASS_C_D = "C-D"


def route(slug, node, contract=DEFAULT_CONTRACT, ctx=None):
    """Compute the calculus route for the reported failure (slug, node).

    ctx (all optional; recorded port events for §9 replay):
      truth_tier       "panel" | "single"   override the provenance scan
      panel_outcome    "overturn" | "stands"
      audit_outcome    "faithful" | "unfaithful"
      retranslated     bool  (a recorded retranslation, R2b)
      census           "sep" | "reach" | "unsat"   override the census scan
      census_basis     str   why the override is the right certificate
      inventory        "current" | "pre_mint"      inventory version I_k
      delta_outcome    "validated" | "failed"      recorded R3 result
      deltas_used      int   prior R3 attempts already on the ledger
      mints_used       int
      defens_used      bool
      mint_outcome     "sep" | "reach" | "unsat" | "exhausted"
      build_outcome    "built"
      note             str   carried into the result
    """
    ctx = ctx or {}
    trace = []
    panel = aud = retr = built = defens = 0
    mints = int(ctx.get("mints_used", 0))
    deltas = int(ctx.get("deltas_used", 0))
    if ctx.get("defens_used"):
        defens = 1
    inventory = ctx.get("inventory", "current")

    # ---- census token (state slot 0). Computed lazily-but-materialised,
    # because the state tuple carries it from step 0; R1/R2 never read it.
    if ctx.get("census"):
        cen = ctx["census"]
        cen_ev = ev(ctx.get("census_artifact", contract),
                    ctx.get("census_basis", "census token supplied by the caller"))
        cen_detail = {"source": "ctx override",
                      "basis": ctx.get("census_basis")}
    else:
        cen, cen_detail = census_state(slug, node, contract, inventory)
        if cen == "none":
            cen = "sep"
            cen_detail["note"] = ("not a current mismatch; census slot carries "
                                  "SEPARABLE (no collision certificate exists)")
        cen_ev = ev(contract, f"SC.census({contract}, inventory={inventory}) "
                              f"-> {json.dumps(cen_detail)}")
    v = "unaud"

    def st():
        return s(cen, v, panel, aud, retr, built, mints, defens, deltas)

    def out(cls, move, port, terminal=None, extra=None):
        r = {"behaviour": slug, "node": node, "contract": contract,
             "inventory": inventory,
             "class": cls, "prescribed_move": move,
             "judgment_port_or_none": port,
             "predicted_terminal": terminal,
             "census": {"token": cen, **(cen_detail or {})},
             "trace": trace}
        if extra:
            r.update(extra)
        if ctx.get("note"):
            r["note"] = ctx["note"]
        return r

    def step(rule, nxt, evidence):
        trace.append({"state": st(), "rule": rule, "next": nxt,
                      "evidence": evidence})

    # ---------------- R1 TRUTH SOLIDITY -------------------------------
    tier = ctx.get("truth_tier")
    tier_art = None
    if tier is None:
        tier, tier_art = truth_tier(slug, node)
    if tier == "panel":
        # The R1 test PASSES on the record: no seat is spent, the premise is
        # discharged and the machine advances panel -> 1.
        nxt = s(cen, v, 1, aud, retr, built, mints, defens, deltas)
        step("r1", nxt, ev(tier_art or "(ctx)",
                           "R1 PASSES on the record: ruling is panel tier; "
                           "premise discharged without a seat"))
        panel = 1
    else:
        po = ctx.get("panel_outcome")
        if po is None:
            return out("OPEN(P1)",
                       "escalate the ruling: 3-seat panel wave under the "
                       "pinned lineage brief (or the pinned one-pass "
                       "defensibility brief)",
                       "P1",
                       extra={"truth_tier": tier, "truth_artifact": tier_art})
        if po == "overturn":
            step("r1", "resolved_t",
                 ev(ctx.get("panel_artifact") or tier_art or "(ctx)",
                    "R1 escalation OVERTURNED the ruling: truth error"))
            return out(CLASS_C_T,
                       "supersede the ledger entry with the panel ruling; "
                       "mismatch dissolves",
                       "P1", terminal="resolved_t",
                       extra={"truth_tier": tier, "truth_artifact": tier_art})
        nxt = s(cen, v, 1, aud, retr, built, mints, defens, deltas)
        step("r1", nxt, ev(ctx.get("panel_artifact") or tier_art or "(ctx)",
                           "R1 escalation run; the ruling STANDS"))
        panel = 1

    # ---------------- R2 FAITHFULNESS AUDIT ---------------------------
    ao = ctx.get("audit_outcome")
    if ao is None:
        ao, f_art, f_note = faithfulness(node)
        if ao == "unknown":
            return out("OPEN(P2)",
                       "run the pinned faithfulness audit (semantic-audit "
                       "lane, 85% gate) on the node's ESTABLISHES claim",
                       "P2", extra={"faithfulness": f_note})
    else:
        f_art = ctx.get("audit_artifact") or "(ctx)"
        f_note = "audit outcome supplied from the record"
    if ao == "faithful":
        nxt = s(cen, "faith", 1, 1, retr, built, mints, defens, deltas)
        step("r2", nxt, ev(f_art, f"R2 -> FAITHFUL: {f_note}"))
        v, aud = "faith", 1
    else:
        nxt = s(cen, "unfaith", 1, 1, retr, built, mints, defens, deltas)
        step("r2", nxt, ev(f_art, f"R2 -> UNFAITHFUL: {f_note}"))
        v, aud = "unfaith", 1
        # R2b: retranslate. The recorded resolution of a C-V is the
        # translation-layer repair itself.
        step("r2b", "resolved_v",
             ev(ctx.get("repair_artifact") or f_art,
                "R2b: re-translate + two-seat re-annotation; no new "
                "declarations"))
        return out(CLASS_C_V,
                   "re-translate the node/module rendering and re-annotate "
                   "(two seats); re-run the router",
                   "P2", terminal="resolved_v",
                   extra={"faithfulness": f_note})

    # ---------------- R3 CENSUS, CURRENT VIEW -------------------------
    if cen == "sep":
        term = terminality(slug, node, contract) if ctx.get("with_terminality") else None
        if deltas < 2:
            do = ctx.get("delta_outcome")
            if do == "validated":
                step("r3", "resolved_d",
                     ev(ctx.get("delta_artifact") or contract,
                        "R3 delta ADOPTED: charter-positive and V1-V5 clean"))
                return out(CLASS_C_D,
                           "mechanical delta (decl-search candidate, probe.py "
                           "L0 screen, V1-V5)", "P1", terminal="resolved_d",
                           extra={"terminality": term})
            if do == "failed":
                nxt = s(cen, v, 1, 1, retr, built, mints, defens, deltas + 1)
                step("r3", nxt, ev(ctx.get("delta_artifact") or contract,
                                   "R3 delta attempt FAILED validation; "
                                   "budget consumed, ledger entry recorded "
                                   "(A1 no-retry)"))
                deltas += 1
                return out(CLASS_C_D,
                           "delta candidate killed at validation; R3 budget "
                           f"now {deltas}/2 — next attempt or R3x (A1)",
                           "P1", terminal=None,
                           extra={"terminality": term,
                                  "open_after": "R3 budget partially consumed"})
            return out(CLASS_C_D,
                       "mechanical delta: enumerate candidates "
                       "(verify_terminal move space / decl-search), screen "
                       "with probe.py (L0), validate V1-V5",
                       "P1", terminal=None, extra={"terminality": term})
        # A1 R3x: separable but no principled delta -> missing intension
        if mints < 2:
            nxt = s(cen, v, 1, 1, retr, built, mints + 1, defens, 0)
            step("r3x", nxt, ev(contract,
                                "A1 R3x: census SEPARABLE but the R3 budget "
                                "is exhausted -> missing intension; mint"))
            return out("C-I(I3)",
                       "A1 R3x: mint the concept the separation needs "
                       "(blind criteria, M1-M4 gates)", "P3")
        term_ = "defensible" if not defens else "terminal_doc"
        step("r3x", term_, ev(contract, "A1 R3x with mints exhausted"))
        return out("C-I(I4)", "record terminal-by-document; surface as "
                              "instrument OUTPUT", "P4", terminal=term_)

    # ---------------- R4 CENSUS, REACHABLE VIEW -----------------------
    if cen == "reach":
        nxt = s("sep", v, 1, 1, retr, 1, mints, defens, deltas)
        step("r4", nxt, ev(contract,
                           "R4: CURRENT-UNSAT and REACHABLE-SEPARABLE — the "
                           "REACHABLE certificate names an unconsumed "
                           "feature (A4: builds are per-FEATURE)"))
        sub = "I1" if ctx.get("i_subclass") is None else ctx["i_subclass"]
        return out(f"C-I({sub})",
                   "build the consumer for the certifying feature (typed "
                   "gate, §6) OR run the annotation lane (I2); the row is "
                   "addressable_by_declaration",
                   None if sub == "I1" else "P2", terminal=None)

    # ---------------- R5 UNSAT BOTH VIEWS -----------------------------
    if mints < 2:
        mo = ctx.get("mint_outcome")
        if mo in ("sep", "reach", "unsat"):
            nxt = s(mo, v, 1, 1, retr, built, mints + 1, defens, 0)
            step("r5", nxt, ev(ctx.get("mint_artifact") or contract,
                               f"R5 mint executed; census -> {mo.upper()}"))
            return out("C-I(I3)",
                       "mint new vocabulary (census->mine->mint, blind "
                       "criteria, M1-M4 gates)", "P3", terminal=None,
                       extra={"post_mint_census": mo})
        nxt = s(cen, v, 1, 1, retr, built, mints + 1, defens, 0)
        step("r5", nxt, ev(contract,
                           "R5: UNSAT in BOTH views — no declaration over "
                           "I_k separates the node; mint"))
        return out("C-I(I3)",
                   "mint new vocabulary (census->mine->mint, blind criteria, "
                   "M1-M4 gates)", "P3", terminal=None)
    term_ = "defensible" if not defens else "terminal_doc"
    step("r5x", term_, ev(contract,
                          "R5x: minting attempts exhausted at this inventory"))
    return out("C-I(I4)",
               "record terminal-by-document; surface as instrument OUTPUT "
               "(not hidden)", "P4", terminal=term_)


def trace_tuples(result):
    """The trace in trace_check.check_trace's (state, rule, next) form."""
    return [(t["state"], t["rule"], t["next"]) for t in result["trace"]]


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    slug, node = sys.argv[1], sys.argv[2]
    contract = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_CONTRACT
    print(json.dumps(route(slug, node, contract), indent=1))
