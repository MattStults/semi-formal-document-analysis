#!/usr/bin/env python3
"""DECLARATION-SEARCH PROTOTYPE (execution of decl_search_proto/PROMPT.md).

L1-based declaration search on the OpenAI-spec instrument: build the feature
matrix from the existing annotation layers, fit per-behavior sparse logistic
models against panel truth, run stability selection, emit declaration
proposals in the contract vocabulary as HYPOTHESES.

Run from the behavior_pilot directory:
    python3 decl_search_proto/build.py
Outputs go only into decl_search_proto/.
"""
import json, os, sys, copy, glob, re
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PILOT = os.path.dirname(HERE)
sys.path.insert(0, PILOT)

import relevance_by_act as RBA
import satisfiability_census as sc

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import log_loss

SEED = 20260820
SLUGS = ["helpfulness", "harm-avoidance-to-third-parties",
         "avoiding-over-and-under-caution"]
STATUS_CLASSES = ["oblige", "forbid", "permit", "prefer", "example", "described"]
CONTRACT = "modules_contract_v18.json"


def P(*a):
    return os.path.join(PILOT, *a)


# ---------------------------------------------------------------- layers
def load_layers():
    sig = json.load(open(P("assert_signature.json")))
    d = P("definition_signature.json")
    if os.path.exists(d):
        sig = {**sig, **json.load(open(d))}
    ap = json.load(open(P("assert_protects.json")))
    d = P("definition_protects.json")
    if os.path.exists(d):
        ap = {**ap, **json.load(open(d))}
    pa = json.load(open(P("assert_purpose_actor.json")))
    d = P("definition_purpose_actor.json")
    if os.path.exists(d):
        pa = {**pa, **json.load(open(d))}
    atoms = json.load(open(P("panel_run1", "convergence",
                            "context_atoms_consensus.json")))["credits"]
    return sig, ap, pa, atoms


def status_class(s):
    s = str(s or "")
    if s.startswith("example"):
        return "example"
    return s if s in STATUS_CLASSES else None


# ---------------------------------------------------------------- mask
def _walk_verdicts(obj):
    """yield (key, verdict_text) from the several verdict-file shapes."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and "::" in str(k):
                yield k, v
            elif isinstance(v, dict):
                if "verdict" in v and isinstance(v["verdict"], str):
                    yield k, v["verdict"]
                else:
                    for kk, vv in _walk_verdicts(v):
                        yield kk, vv


def defensible_mask():
    """(behavior, node) pairs carrying an adjudicated-defensible verdict."""
    files = sorted(set(
        glob.glob(P("panel_run1", "convergence", "*verdicts*.json")) +
        [P("panel_run1", "convergence", "flip_adjudication_verdicts.json")] +
        glob.glob(P("panel_run1", "convergence", "LEDGER*.json"))))
    masked, src = set(), {}
    for f in files:
        if not os.path.exists(f):
            continue
        try:
            obj = json.load(open(f))
        except Exception:
            continue
        n = 0
        for k, verdict in _walk_verdicts(obj):
            if "defensible" not in verdict.lower():
                continue
            if "::" not in k:
                continue
            slug, nid = k.split("::", 1)
            if slug not in SLUGS:
                continue
            masked.add((slug, nid))
            n += 1
        if n:
            src[os.path.basename(f)] = n
    return masked, src


# ---------------------------------------------------------------- features
def node_layer_values(nid, sig, ap, pa, atoms):
    keys_sig = [k for k in sig if k.startswith(nid + "|")]
    keys_ap = [k for k in ap if k.startswith(nid + "|")]
    keys_pa = [k for k in pa if k.startswith(nid + "|")]
    governs = {g for k in keys_sig for g in sig[k].get("governs", [])}
    contexts = {c for k in keys_sig for c in sig[k].get("contexts", [])}
    for _i, lst in (atoms.get(nid) or {}).items():
        contexts |= set(lst)
    protects = {v for k in keys_ap for v in ap[k]}
    has_assistant = any(pa[k].get("actor") == "assistant" for k in keys_pa)
    purposes = {e for k in keys_pa for e in pa[k].get("purpose", [])}
    return governs, contexts, protects, has_assistant, purposes


def node_acts(nid, corpus, br):
    """set of (canonical act, status class) the node asserts."""
    out = set()
    for f, s in corpus.get(nid, []):
        A = br.get(f)
        cls = status_class(s)
        if A and cls:
            out.add((A, cls))
    return out


def act_features(acts_on_node, performs, pm):
    """three encodings per (A, s) — see PROMPT §DATA."""
    feats = set()
    for A, s in acts_on_node:
        feats.add(f"act={A}|{s}|exact")
        if pm.get(A, set()) & performs:
            feats.add(f"act={A}|{s}|mod_specific_beh_genus")
        if any(A in pm.get(a, set()) for a in performs):
            feats.add(f"act={A}|{s}|mod_genus_beh_species")
    return feats


def build_matrix(mods, br, corpus, pm, sig, ap, pa, atoms, masked):
    rows = []
    for slug in SLUGS:
        mod = mods[slug]
        performs, _canon = RBA.behavior_acts(mod)
        truth = sc.truth_all(slug)
        for nid in sorted(truth):
            governs, contexts, protects, has_asst, purposes = \
                node_layer_values(nid, sig, ap, pa, atoms)
            f = set()
            f |= act_features(node_acts(nid, corpus, br), performs, pm)
            f |= {f"governs={g}" for g in governs}
            f |= {f"context={c}" for c in contexts}
            f |= {f"protects={p}" for p in protects}
            f |= {f"purpose={e}" for e in purposes}
            if has_asst:
                f.add("actor=has_assistant")
            rows.append({
                "behavior": slug, "node": nid,
                "label": 1 if truth[nid] == "relevant" else 0,
                "masked": (slug, nid) in masked,
                "features": sorted(f),
            })
    names = sorted({n for r in rows for n in r["features"]})
    return rows, names


# ---------------------------------------------------------------- fitting
def design(rows, names):
    idx = {n: i for i, n in enumerate(names)}
    X = np.zeros((len(rows), len(names)), dtype=float)
    for i, r in enumerate(rows):
        for n in r["features"]:
            X[i, idx[n]] = 1.0
    y = np.array([r["label"] for r in rows], dtype=int)
    return X, y


def _ll(y, p):
    return log_loss(y, np.clip(p, 1e-6, 1 - 1e-6), labels=[0, 1])


def fit_behavior(X, y, eng_pred, grid):
    """returns (best_C, path, cv losses for fitted/baseline/instrument)"""
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    folds = list(skf.split(X, y))
    path = []
    for C in grid:
        losses = []
        for tr, te in folds:
            m = LogisticRegression(penalty="l1", solver="liblinear", C=C,
                                   class_weight="balanced", max_iter=5000,
                                   random_state=SEED)
            m.fit(X[tr], y[tr])
            losses.append(_ll(y[te], m.predict_proba(X[te])[:, 1]))
        full = LogisticRegression(penalty="l1", solver="liblinear", C=C,
                                  class_weight="balanced", max_iter=5000,
                                  random_state=SEED).fit(X, y)
        path.append({"C": float(C), "cv_logloss": float(np.mean(losses)),
                     "n_nonzero_full_fit": int(np.sum(np.abs(full.coef_[0]) > 1e-6))})
    best = min(path, key=lambda d: d["cv_logloss"])
    # trivial baseline: train-fold class prior
    base = []
    for tr, te in folds:
        p = float(y[tr].mean())
        base.append(_ll(y[te], np.full(len(te), p)))
    # current instrument: its binary decision, calibrated on the train fold
    # (Laplace-smoothed P(relevant | engaged) / P(relevant | not engaged));
    # the instrument emits no probability, so this is its best-case calibration.
    inst = []
    for tr, te in folds:
        e = eng_pred[tr].astype(bool)
        p1 = (y[tr][e].sum() + 1) / (e.sum() + 2)
        p0 = (y[tr][~e].sum() + 1) / ((~e).sum() + 2)
        pte = np.where(eng_pred[te].astype(bool), p1, p0)
        inst.append(_ll(y[te], pte))
    return best, path, float(np.mean(base)), float(np.mean(inst))


def stability(X, y, C, n_boot=100):
    rng = np.random.default_rng(SEED)
    n = len(y)
    coefs = []
    for _ in range(n_boot):
        while True:
            b = rng.integers(0, n, n)
            if len(np.unique(y[b])) == 2:
                break
        m = LogisticRegression(penalty="l1", solver="liblinear", C=C,
                               class_weight="balanced", max_iter=5000,
                               random_state=SEED)
        m.fit(X[b], y[b])
        coefs.append(m.coef_[0])
    Cf = np.array(coefs)
    freq = (np.abs(Cf) > 1e-6).mean(axis=0)
    med = np.median(Cf, axis=0)
    return freq, med


# ---------------------------------------------------------------- proposals
def engaged_set(mod, br, corpus):
    _acts, rel = RBA.relevance(mod, br, corpus)
    return set(rel)


def score(eng, truth, keep):
    """node -> correct?  over kept (unmasked) truth nodes"""
    return {n: ((truth[n] == "relevant") == (n in eng)) for n in keep}


def mutate(mod, slot, value, add):
    m = copy.deepcopy(mod)
    if slot in ("governs_concern", "protects_concern", "purpose_concern",
                "party_concern"):
        cur = list(m.get(slot) or [])
        if add:
            if value not in cur:
                cur.append(value)
        else:
            cur = [v for v in cur if v != value]
        m[slot] = cur
    elif slot == "performs_acts":
        does = list((m.get("module") or {}).get("does", []))
        if add:
            does = does + [value]
        else:
            def head(r):
                m2 = re.match(r"\s*(?:not\s+|-)?([a-z_][A-Za-z0-9_]*)", str(r))
                return m2.group(1) if m2 else None
            does = [r for r in does if head(r) != value]
        m.setdefault("module", {})["does"] = does
    return m


def predict_delta(slot, value, add, mod, br, corpus, truth, keep,
                  base_correct, ctx_nodes):
    """apply the proposed DISCRETE rule and count fixes/breaks."""
    base_eng = engaged_set(mod, br, corpus)
    if slot == "contexts_concern":
        # schema extension: no instrument slot exists, so the discrete rule is
        # applied directly — add: engage every node carrying the context;
        # wall: drop every node carrying it.
        if add:
            eng = base_eng | set(ctx_nodes)
        else:
            eng = base_eng - set(ctx_nodes)
    else:
        eng = engaged_set(mutate(mod, slot, value, add), br, corpus)
    new_correct = score(eng, truth, keep)
    fixed = sorted(n for n in keep if new_correct[n] and not base_correct[n])
    broken = sorted(n for n in keep if base_correct[n] and not new_correct[n])
    return fixed, broken


def main():
    mods = json.load(open(P(CONTRACT)))["modules"]
    br = RBA.bridges()
    corpus = RBA.corpus_acts()
    pm = RBA.parent_map()
    sig, ap, pa, atoms = load_layers()
    masked, mask_src = defensible_mask()

    rows, names = build_matrix(mods, br, corpus, pm, sig, ap, pa, atoms, masked)

    json.dump({
        "_": ("feature matrix for L1 declaration search — one row per "
              "(behavior, node) panel-truth point. masked=true rows carry an "
              "adjudicated-defensible verdict and are EXCLUDED from fitting "
              "and from predicted fixes/breaks."),
        "inventory": {"contract": "v18", "run_seed": SEED,
                      "n_rows": len(rows), "n_features": len(names),
                      "n_masked": sum(1 for r in rows if r["masked"]),
                      "mask_sources": mask_src,
                      "status_classes": STATUS_CLASSES,
                      "act_relation_encodings": ["exact",
                                                 "mod_specific_beh_genus",
                                                 "mod_genus_beh_species"]},
        "feature_names": names,
        "rows": rows,
    }, open(os.path.join(HERE, "feature_matrix.json"), "w"), indent=1)

    grid = np.logspace(-3, 2, 11)
    report = {"_": ("L1 declaration search, per behavior. Every fitted "
                    "coefficient and every downstream proposal is a "
                    "truth-fitted HYPOTHESIS pending blind justification (9b) "
                    "and fresh-pool certification (9e) — nothing here is "
                    "adopted, validated, or an improvement."),
              "inventory": {"contract": "v18", "run_seed": SEED,
                            "C_grid": [float(c) for c in grid],
                            "cv": "StratifiedKFold(5, shuffle, seed 20260820)",
                            "bootstrap_resamples": 100,
                            "instrument_logloss_note":
                                ("the current instrument emits a binary "
                                 "decision; its log-loss is computed after "
                                 "best-case Laplace-smoothed calibration of "
                                 "P(relevant|engaged) on each training fold")},
              "_caveats": [
                  ("SELECTION BIAS in the instrument comparison: the mask "
                   "removes rows with an adjudicated-defensible verdict, and "
                   "those rows are overwhelmingly the instrument's own "
                   "mismatches. On the surviving rows the instrument is "
                   "near-ceiling, so 'fitted vs instrument' log-loss is not a "
                   "fair head-to-head — read it as 'what is left to explain "
                   "after the defensible disagreements are set aside'."),
                  ("The model is fitted ON panel truth, so every coefficient "
                   "is label-derived. Labels direct ATTENTION, never TRUTH: "
                   "nothing here may be adopted without a document-side "
                   "justification written blind (9b) and a fresh-pool "
                   "measurement (9e)."),
                  ("The two relational act encodings are behavior-dependent "
                   "by construction (they are defined against the behavior's "
                   "own performs set) but share a column namespace across "
                   "behaviors; fitting is per behavior, so no cross-behavior "
                   "mixing occurs."),
              ],
              "behaviors": {}}
    proposals, unmappable = [], []

    for slug in SLUGS:
        mod = mods[slug]
        truth = sc.truth_all(slug)
        brows = [r for r in rows if r["behavior"] == slug and not r["masked"]]
        X, y = design(brows, names)
        base_eng = engaged_set(mod, br, corpus)
        eng_pred = np.array([1 if r["node"] in base_eng else 0 for r in brows])
        best, path, base_ll, inst_ll = fit_behavior(X, y, eng_pred, grid)
        freq, med = stability(X, y, best["C"])
        stab = {names[i]: round(float(freq[i]), 3)
                for i in range(len(names)) if abs(med[i]) > 1e-6}
        report["behaviors"][slug] = {
            "n_rows_total": sum(1 for r in rows if r["behavior"] == slug),
            "n_rows_fitted": len(brows),
            "n_masked": sum(1 for r in rows
                            if r["behavior"] == slug and r["masked"]),
            "positive_rate": round(float(y.mean()), 4),
            "chosen_C": best["C"],
            "baseline_logloss": round(base_ll, 4),
            "fitted_logloss": round(best["cv_logloss"], 4),
            "instrument_logloss": round(inst_ll, 4),
            "instrument_accuracy": round(float(
                ((eng_pred == 1) == (y == 1)).mean()), 4),
            "l1_path": path,
            "n_stable_features": sum(1 for v in stab.values() if v >= 0.7),
            "stability": stab,
            "median_coef": {k: round(float(med[names.index(k)]), 4)
                            for k in stab},
        }

        # ------------- proposals
        keep = [r["node"] for r in brows]
        base_correct = score(base_eng, truth, keep)
        gov_decl = set(mod.get("governs_concern") or [])
        gov_cond = mod.get("governs_conditional") or {}
        prot_decl = set(mod.get("protects_concern") or [])
        purp_decl = set(mod.get("purpose_concern") or [])
        performs, _c = RBA.behavior_acts(mod)
        rowmap = {r["node"]: set(r["features"]) for r in brows}

        for feat, s in sorted(stab.items(), key=lambda kv: -kv[1]):
            if s < 0.7:
                continue
            coef = float(med[names.index(feat)])
            add = coef > 0
            fam, _, val = feat.partition("=")
            slot = None
            schema_ext = False
            delta = None
            why = None
            ctx_nodes = [n for n, fs in rowmap.items() if feat in fs]

            if fam == "governs":
                consumed = val in gov_decl or val in gov_cond
                if add and not consumed:
                    slot, delta = "governs_concern", {"governs_concern": ["+" + val]}
                elif (not add) and consumed:
                    slot, delta = "governs_concern", {"governs_concern": ["-" + val]}
                else:
                    why = ("positive but already consumed by governs_concern"
                           if add else
                           "negative but the behavior does not declare it")
            elif fam == "protects":
                consumed = val in prot_decl
                if add and not consumed:
                    slot, delta = "protects_concern", {"protects_concern": ["+" + val]}
                elif (not add) and consumed:
                    slot, delta = "protects_concern", {"protects_concern": ["-" + val]}
                else:
                    why = ("positive but already consumed by protects_concern"
                           if add else
                           "negative but the behavior does not declare it")
            elif fam == "purpose":
                consumed = val in purp_decl
                if add and not consumed:
                    slot, delta = "purpose_concern", {"purpose_concern": ["+" + val]}
                elif (not add) and consumed:
                    slot, delta = "purpose_concern", {"purpose_concern": ["-" + val]}
                else:
                    why = ("positive but already consumed by purpose_concern"
                           if add else
                           "negative but the behavior does not declare it")
            elif fam == "context":
                # no context slot exists in the instrument today
                consumed = any(val in v for v in gov_cond.values())
                engaged_here = any(n in base_eng for n in ctx_nodes)
                if add and not consumed:
                    slot, schema_ext = "contexts_concern", True
                    delta = {"contexts_concern": [val]}
                elif (not add) and engaged_here:
                    slot, schema_ext = "contexts_concern", True
                    delta = {"contexts_concern": ["!" + val]}
                else:
                    why = "context value already consumed / nothing to wall"
            elif fam == "act":
                A, sc_, rel = val.split("|")
                consumed = (A in performs or bool(pm.get(A, set()) & performs)
                            or any(A in pm.get(a, set()) for a in performs))
                if add and not consumed:
                    slot, delta = "performs_acts", {"performs_acts": ["+" + A]}
                    val = A
                elif (not add) and consumed:
                    slot, delta = "performs_acts", {"performs_acts": ["-" + A]}
                    val = A
                else:
                    why = ("positive but the act relation is already inside "
                           "the performs set" if add else
                           "negative on an act relation the behavior does not "
                           "engage through")
            elif fam.startswith("actor"):
                why = ("the assistant-actor gate is universal in the "
                       "instrument (actor_ok), not a per-behavior "
                       "declaration slot; already consumed")
            else:
                why = "no contract slot for this feature family"

            if slot is None:
                unmappable.append({"behavior": slug, "feature": feat,
                                   "stability": round(float(s), 3),
                                   "median_coef": round(coef, 4),
                                   "why_unmappable": why})
                continue

            fixed, broken = predict_delta(slot, val, add, mod, br, corpus,
                                          truth, keep, base_correct, ctx_nodes)
            mech = None
            if add and slot in ("protects_concern", "governs_concern") \
                    and not (mod.get(slot) or []):
                mech = (f"{slot} is currently EMPTY for this behavior, which "
                        f"the instrument reads as fail-open (no wall). Adding "
                        f"the first value switches the wall on wholesale — the "
                        f"predicted breaks below are dominated by that "
                        f"activation, not by the value itself.")
            proposals.append({
                "behavior": slug,
                "kind": "add" if add else "wall",
                "slot": slot,
                "schema_extension": schema_ext,
                "delta": delta,
                "feature": feat,
                "stability": round(float(s), 3),
                "median_coef": round(coef, 4),
                "predicted": {"fixes": len(fixed), "breaks": len(broken),
                              "fixed_nodes": fixed, "broken_nodes": broken},
                "blind_justification_stub": stub(slug, slot, val, add),
                "mechanism_note": mech,
            })

    proposals.sort(key=lambda p: -(p["predicted"]["fixes"] -
                                   p["predicted"]["breaks"]))
    json.dump({
        "_": ("declaration-search output: truth-fitted HYPOTHESES only. No "
              "proposal here is adopted, validated, or shown to be an "
              "improvement; each awaits blind justification (9b) and "
              "fresh-pool certification (9e). Predicted fixes/breaks are "
              "counted by re-running the instrument with the delta applied "
              "(contexts_concern, which has no instrument slot, uses the "
              "stated discrete rule) over unmasked truth rows only."),
        "inventory": {"contract": "v18", "run_seed": SEED},
        "proposals": proposals,
        "unmappable": unmappable,
    }, open(os.path.join(HERE, "declaration_proposals.json"), "w"), indent=1)

    json.dump(report, open(os.path.join(HERE, "fit_report.json"), "w"), indent=1)
    print(f"rows {len(rows)} features {len(names)} masked "
          f"{sum(1 for r in rows if r['masked'])} proposals {len(proposals)} "
          f"unmappable {len(unmappable)}")


def stub(slug, slot, val, add):
    verb = "should" if add else "should not"
    human = {"governs_concern": f"a clause governing '{val}'",
             "protects_concern": f"a clause protecting '{val}'",
             "purpose_concern": f"a clause serving the end '{val}'",
             "contexts_concern": f"a clause carrying the context '{val}'",
             "performs_acts": f"a clause asserting a status on the act '{val}'",
             "party_concern": f"a clause about party '{val}'"}[slot]
    return (f"HYPOTHESIS for 9b: read blind, would a document-side reader say "
            f"{human} {verb} bear on '{slug}'? The a-priori case would have to "
            f"come from the behavior's own definition and the spec's use of "
            f"'{val}', not from the panel labels that produced this feature.")


if __name__ == "__main__":
    main()
