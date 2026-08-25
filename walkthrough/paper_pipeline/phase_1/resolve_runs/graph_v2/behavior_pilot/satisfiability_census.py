#!/usr/bin/env python3
"""SATISFIABILITY CENSUS (Matt's design, 2026-08-19) — deterministic, $0.

For each behavior, build every node's FEATURE VECTOR as the instrument sees it:
the set of (canonical act, status) pairs it can engage through, plus the union
of its asserts' governs / protects / contexts / actor values. Two nodes with
identical vectors CANNOT be separated by any wall or bridge configuration —
the instrument is a function of the vector. So:

  * a MISMATCH whose vector collides with a correctly-handled node of the
    OPPOSITE verdict is UNSAT at current granularity (fixing it must break
    the other node);
  * a mismatch with NO collision is SEPARABLE — some configuration handles it,
    and it should never be declared terminal.

This makes the terminal/fixable boundary a computation instead of a judgment.

VECTOR FAITHFULNESS (Arc1-e fix, 2026-08-21, prereg panel_run1/convergence/
CENSUS_VECTOR_FIX_PREREG.md incl. addenda 1-3): the FULL vector carries
every feature relevance() can consume — assert layers merged with the
definition_* lanes (keys nid|c{i}; lane-scope jurisdiction: definitional
purpose credits excluded, definitional actor credits included), functor
argument sorts, authority-plumbing flags, and contexts. Channels census()
cannot represent (party_concern, governs_conditional) fail it LOUD if any
module ever declares them; remaining latent gaps are registered in
semi-formal-experiment/LATENT_FIX_REGISTRY.md.

TWO VIEWS, per addendum-3 scope ruling:
- CURRENT: the instrument AS FROZEN, per behavior — slots a behavior never
  consumes are MASKED before grouping (contexts always, because its only
  consumer governs_conditional is undeclared and guarded; protects unless the
  module declares protects_concern; purposes unless it declares
  purpose_concern). Three defects in this file's history were exactly
  unmasked inert features (addenda 2-3); the standing dead-slot probe test
  guards the class.
- REACHABLE: the DESIGN SPACE — every slot the schema allows a declaration
  to consume (protects_concern / purpose_concern / governs_conditional are
  all declarable), plus consensus context-atom credits (annotated but
  undeclared vocabulary). Inventory-relative terminality per contract 9g.
9b consumes the gap between the views: CURRENT-UNSAT and REACHABLE-SEPARABLE
rows are addressable by new declarations; CURRENT-UNSAT and REACHABLE-UNSAT
rows are terminal at current granularity.
Usage: .../.venv/bin/python satisfiability_census.py modules_contract_v18.json
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import relevance_by_act as RBA
import arm_ab as AB


def load_refinements():
    """Arc1-b mint consensus (panel_run1/convergence/act_refinements_FINAL.json):
    node -> frozenset of act-refinement subtype marks. Span-form annotations
    (rule-vs-exhibit; form-equivalence). No declaration consumes them yet —
    under addendum-3 semantics they are REACHABLE-view vocabulary: the slot
    is dead-masked in CURRENT until a subtype-conditional declaration exists."""
    p = os.path.join(HERE, "panel_run1", "convergence", "act_refinements_FINAL.json")
    if not os.path.exists(p):
        return {}
    out = {}
    for st, rec in json.load(open(p))["subtypes"].items():
        for n in rec["consensus"]:
            out.setdefault(n, set()).add(st)
    return {n: frozenset(v) for n, v in out.items()}


def load_layers():
    def merged(assert_name, lane_name):
        p = os.path.join(HERE, assert_name)
        d = json.load(open(p)) if os.path.exists(p) else {}
        lp = os.path.join(HERE, lane_name)
        if os.path.exists(lp):
            d = {**d, **json.load(open(lp))}     # mirrors relevance(): {**assert, **definition}
        return d
    sig = merged("assert_signature.json", "definition_signature.json")
    ap = merged("assert_protects.json", "definition_protects.json")
    pa = merged("assert_purpose_actor.json", "definition_purpose_actor.json")
    # vector faithfulness with the 9b instrument: relevance() merges consensus
    # context-atom credits into signature contexts (consumption stays
    # declaration-gated there). Mirror it here; the REACHABLE union below is
    # idempotent with this merge.
    cp = os.path.join(HERE, "panel_run1", "convergence", "context_atoms_consensus.json")
    ctx = {}
    if os.path.exists(cp):
        ctx = json.load(open(cp))["credits"]
        for nid, idxs in ctx.items():
            for i, atoms in idxs.items():
                k = f"{nid}|{i}"
                if k in sig and atoms:
                    sig[k] = {**sig[k], "contexts":
                              sorted(set(sig[k].get("contexts", [])) | set(atoms))}
    return sig, ap, pa, ctx


def vector(nid, corpus, br, sig, ap, pa, ctx=None, asorts=None, ref=None):
    # layer-independent key sets: relevance() looks each layer up by node
    # prefix on its own; a node annotated in one layer but not another must
    # still contribute the layers it has.
    skeys = sorted(k for k in sig if k.startswith(nid + "|"))
    pkeys = sorted(k for k in ap if k.startswith(nid + "|"))
    akeys = sorted(k for k in pa if k.startswith(nid + "|"))
    # (canonical act, functor arg-sort). Assert STATUS is deliberately absent:
    # relevance() never consumes it (engagement gates on verb_hit/arg_ok/
    # party_ok/walls; status only rides as reason text), and carrying it
    # over-refines vectors into false SEPARABLEs (prereg addendum 2).
    # Sorts none/other/missing collapse to None: arg_ok fails open
    # identically for all three.
    def _sort(f):
        s = (asorts or {}).get(f)
        return None if s in (None, "none", "other") else s
    acts = frozenset((br.get(f), _sort(f))
                     for f, s in corpus.get(nid, []) if br.get(f))
    governs = frozenset(g for k in skeys for g in sig[k]["governs"])
    contexts = frozenset(c for k in skeys for c in sig[k].get("contexts", []))
    protects = frozenset(p for k in pkeys for p in ap.get(k, []))
    actors = frozenset(pa[k]["actor"] for k in akeys)
    # lane-scope ruling (2026-08-20): definitional keys (|c{i}) never feed
    # the purpose OR-channel, so their purposes are not instrument-visible
    purposes = frozenset(e for k in akeys
                         if not k.split("|")[1].startswith("c")
                         for e in pa[k]["purpose"])
    # all-plumbing exclusion (signature_ok) is instrument-visible
    plumbing = frozenset(k.split("|")[1] for k in skeys
                         if sig[k].get("authority_plumbing"))
    refinements = (ref or {}).get(nid, frozenset())
    # Arc1-e extension (2026-08-24, iteration-3 maintenance; ITERATION_NOTES
    # 0015): four appended slots so the census can express every channel in
    # RBA.DECLARABLE_MOVES. APPEND-ONLY — indices 0-7 are pinned by
    # test_dead_slot_probe and unchanged.
    #  8 gc_pairs: per-assert (governs quality, frozenset(contexts)) pairs —
    #    the exact feature governs_conditional consumes (flattened slots 1-2
    #    cannot express the pairing; the old census guard's reason).
    #  9 arb: the ARBITRATES mark (arb_marks_final.json), consumed by
    #    arbitrates_wall / arbitrates_channel.
    # 10 mach: the machinery feature — the node's canonical act heads IF it
    #    is structurally excluded (all-plumbing or all-non-assistant-actor),
    #    else empty; consumed by machinery_concern.
    # 11 party_pairs: (canonical act, act-party) pairs, consumed by
    #    party_concern.
    _load_ext_layers()
    gc_pairs = frozenset((g, frozenset(sig[k].get("contexts", [])))
                         for k in skeys for g in sig[k]["governs"])
    arb = bool((_ARB or {}).get(nid))
    struct_excluded = (
        (skeys and all(sig[k]["authority_plumbing"] for k in skeys))
        or (akeys and not any(pa[k]["actor"] == "assistant" for k in akeys)))
    heads = frozenset(br.get(f) for f, s in corpus.get(nid, []) if br.get(f))
    mach = heads if struct_excluded else frozenset()
    party_pairs = frozenset((br.get(f), (_PARTY or {}).get(f, "unspecified"))
                            for f, s in corpus.get(nid, []) if br.get(f))
    cur = (acts, governs, contexts, protects, actors, purposes, plumbing,
           refinements, gc_pairs, arb, mach, party_pairs)
    if ctx is None:
        return cur
    catoms = frozenset(a for vs in (ctx.get(nid) or {}).values() for a in vs)
    return (acts, governs, contexts | catoms, protects, actors, purposes,
            plumbing, refinements, gc_pairs, arb, mach, party_pairs)


# layers for the appended slots, loaded once (empty-safe: absent files make
# the slots constant, which masking already treats as uninformative)
_ARB = None
_PARTY = None


def _load_ext_layers():
    global _ARB, _PARTY
    if _ARB is None:
        p = os.path.join(HERE, "arb_marks_final.json")
        _ARB = json.load(open(p)).get("marks", {}) if os.path.exists(p) else {}
    if _PARTY is None:
        try:
            _PARTY = RBA.act_party()
        except Exception:
            _PARTY = {}
    return _ARB, _PARTY


def truth_all(slug):
    t = dict(AB.truth_for(slug))
    fmap = {"helpfulness": [("fresh_draw", "HELP_RESULT"), ("fresh_draw2", "HELP_R2_RESULT"), ("fresh_draw3", "HELP_R3_RESULT"), ("fresh_draw4", "HELP_R4_RESULT")],
            "harm-avoidance-to-third-parties": [("fresh_draw2", "HARM_R2_RESULT"), ("fresh_draw4", "HARM_R4_RESULT")],
            "avoiding-over-and-under-caution": [("fresh_draw2", "CAUTION_R2_RESULT"), ("fresh_draw4", "CAUTION_R4_RESULT")]}
    for rd, f in fmap[slug]:
        p = os.path.join(HERE, "panel_run1", rd, f + ".json")
        if os.path.exists(p):
            t.update(json.load(open(p))["truth"])
    # DEFENSIBILITY OVERLAY (2026-08-24, highest precedence): the blind Fable
    # defensibility batch's rulings supersede the 9b-arithmetic break
    # classifications for exactly the nodes listed in the artifact
    # (DEFENSIBILITY_BATCH_PROTOCOL.md — ONE batch, one pass, no iteration;
    # currently one rescue: helpfulness::l427_460_n003 -> relevant).
    dp = os.path.join(HERE, "ruling_packets", "defensibility_rulings.json")
    if os.path.exists(dp):
        for u in json.load(open(dp)).get("truth_ledger_updates", []):
            if u["behaviour"] == slug:
                t[u["node"]] = u["truth"]
    return t


# slot indices of the vector tuple
SLOT_CONTEXTS, SLOT_PROTECTS, SLOT_PURPOSES, SLOT_REFINEMENTS = 2, 3, 5, 7
SLOT_GC_PAIRS, SLOT_ARB, SLOT_MACH, SLOT_PARTY = 8, 9, 10, 11


def current_mask(mod):
    """Slots the FROZEN behavior never consumes (addendum-3 ruling). Masking
    them is what makes CURRENT mean 'the instrument as frozen': a feature no
    gate reads cannot separate two nodes for this behavior."""
    dead = set()
    # contexts + gc_pairs: consumed only via governs_conditional
    if not mod.get("governs_conditional"):
        dead.add(SLOT_CONTEXTS)
        dead.add(SLOT_GC_PAIRS)
    # Arc1-b refinement marks: no subtype-conditional declaration exists yet,
    # so the slot is dead for every frozen behavior. When one is declared,
    # update this and DEAD_SLOTS_PINNED in the same reviewed commit.
    dead.add(SLOT_REFINEMENTS)
    if not mod.get("protects_concern"):
        dead.add(SLOT_PROTECTS)
    if not mod.get("purpose_concern"):
        dead.add(SLOT_PURPOSES)
    if not (mod.get("arbitrates_wall") or mod.get("arbitrates_channel")):
        dead.add(SLOT_ARB)
    if not mod.get("machinery_concern"):
        dead.add(SLOT_MACH)
    if not mod.get("party_concern"):
        dead.add(SLOT_PARTY)
    return dead


def masked(vec, dead):
    return tuple(None if i in dead else slot for i, slot in enumerate(vec))


def census(modules_file):
    mods = json.load(open(os.path.join(HERE, modules_file)))["modules"]
    # Arc1-e extension 2026-08-24: the party_concern and governs_conditional
    # guards are LIFTED — vector() now carries party_pairs and gc_pairs (plus
    # arb and mach for the iteration-2/3 channels); current_mask consumes the
    # declarations. The guards' reasons are discharged, not bypassed.
    br = RBA.bridges(); corpus = RBA.corpus_acts()
    sig, ap, pa, ctx = load_layers()
    asorts = RBA.arg_sorts()
    ref = load_refinements()
    report = {}
    for slug, m in mods.items():
        _, rel = RBA.relevance(m, br, corpus)
        eng = set(rel)
        t = truth_all(slug)
        dead = current_mask(m)
        vecs, groups_cur, groups_rch = {}, {}, {}
        for n in t:
            vc = masked(vector(n, corpus, br, sig, ap, pa, None, asorts, ref), dead)
            vr = vector(n, corpus, br, sig, ap, pa, ctx, asorts, ref)
            vecs[n] = (vc, vr)
            groups_cur.setdefault(vc, []).append(n)
            groups_rch.setdefault(vr, []).append(n)

        def view(n, groups, idx):
            twins = [m for m in groups[vecs[n][idx]]
                     if m != n and ((t[m] == "relevant") == (m in eng)) and t[m] != t[n]]
            return ("UNSAT" if twins else "SEPARABLE"), twins

        rows = {}
        for n, v in t.items():
            correct = (v == "relevant") == (n in eng)
            if correct:
                continue
            sc, tc = view(n, groups_cur, 0)
            sr, tr = view(n, groups_rch, 1)
            rows[n] = {"verdict_needed": v, "status": sc, "colliding_correct_nodes": tc,
                       "status_reachable": sr, "colliding_correct_nodes_reachable": tr,
                       "addressable_by_declaration": sc == "UNSAT" and sr == "SEPARABLE"}
        report[slug] = rows
    return report


if __name__ == "__main__":
    mf = sys.argv[1] if len(sys.argv) > 1 else "modules_contract_v18.json"
    rep = census(mf)
    for slug, rows in rep.items():
        unsat = [n for n, r in rows.items() if r["status"] == "UNSAT"]
        sep = [n for n, r in rows.items() if r["status"] == "SEPARABLE"]
        runsat = [n for n, r in rows.items() if r["status_reachable"] == "UNSAT"]
        print(f"== {slug}: {len(rows)} mismatches -> CURRENT UNSAT {len(unsat)}, SEPARABLE {len(sep)}"
              f" | REACHABLE UNSAT {len(runsat)}, SEPARABLE {len(rows) - len(runsat)}")
        for n in unsat:
            print(f"   UNSAT {n} collides with {rows[n]['colliding_correct_nodes'][:4]}")
    # contract-stamped output name: earlier runs (v17-era, cited by
    # decl_search_proto) live in satisfiability_census.json and stay untouched
    stem = os.path.splitext(os.path.basename(mf))[0]
    out = os.path.join(HERE, "panel_run1", "convergence", f"satisfiability_census_{stem}.json")
    json.dump({"_": __doc__.strip().splitlines()[0], "contract": mf, "report": rep}, open(out, "w"), indent=1)
    print("wrote", out)
