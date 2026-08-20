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


# ------------------------------------------------- interactions (amendment A)
FAMILY_PAIRS = [("act", "protects"), ("act", "purpose"),
                ("governs", "context"), ("governs", "protects"),
                ("act", "context")]


def add_interactions(rows, names):
    """pairwise product columns between feature families (RUN-2 amendment A).

    Screen (applied over ALL matrix rows, both behaviors' rows pooled, before
    any fitting): keep a product only if its support (rows where the product
    is 1) is >= 3 AND it differs from each parent on >= 2 rows.
    """
    def fam(n):
        return n.split("=", 1)[0]

    by_fam = {}
    for n in names:
        by_fam.setdefault(fam(n), []).append(n)
    sup = {n: set() for n in names}
    for i, r in enumerate(rows):
        for n in r["features"]:
            sup[n].add(i)
    labels = [r["label"] for r in rows]

    stats = {"candidates": 0, "dropped_support_lt_3": 0,
             "dropped_parent_diff_lt_2": 0,
             "dropped_duplicate_of_base_column": 0,
             "dropped_duplicate_of_earlier_interaction": 0, "kept": 0}
    base_sup = {frozenset(v): k for k, v in sup.items()}
    seen, kept, aliases = {}, [], {}
    for fa, fb in FAMILY_PAIRS:
        for a in sorted(by_fam.get(fa, [])):
            for b in sorted(by_fam.get(fb, [])):
                stats["candidates"] += 1
                inter = sup[a] & sup[b]
                if len(inter) < 3:
                    stats["dropped_support_lt_3"] += 1
                    continue
                if len(sup[a] - inter) < 2 or len(sup[b] - inter) < 2:
                    stats["dropped_parent_diff_lt_2"] += 1
                    continue
                key = frozenset(inter)
                name = f"x[{a}&{b}]"
                if key in base_sup:
                    stats["dropped_duplicate_of_base_column"] += 1
                    aliases.setdefault(base_sup[key], []).append(name)
                    continue
                if key in seen:
                    stats["dropped_duplicate_of_earlier_interaction"] += 1
                    aliases.setdefault(seen[key], []).append(name)
                    continue
                seen[key] = name
                kept.append((name, inter))
                stats["kept"] += 1
    detail = {}
    for name, inter in kept:
        for i in inter:
            rows[i]["features"].append(name)
        detail[name] = {"support": len(inter),
                        "label_positive_support":
                            int(sum(labels[i] for i in inter))}
    for r in rows:
        r["features"] = sorted(r["features"])
    names = sorted({n for r in rows for n in r["features"]})
    stats["post_screen_total_columns"] = len(names)
    stats["post_screen_interaction_columns"] = len(kept)
    stats["duplicate_column_aliases"] = aliases
    return rows, names, stats, detail


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
    return best, path, float(np.mean(base)), float(np.mean(inst)), folds


def fair_all_rows(rows_all, names, best_C, folds, brows, base_eng):
    """RUN-2 amendment B: accuracy / log-loss over ALL rows of the behavior,
    with adjudicated-defensible rows scored correct-for-both.

    Model probabilities: out-of-fold for the fitted (unmasked) rows, so the
    comparison is not in-sample; full-fit (trained on the unmasked rows) for
    the masked rows, which never entered any fit.
    Defensible rows are scored correct for BOTH predictors: each is credited
    with its own decision as the label, so neither is penalised for a
    disagreement the adjudication called defensible.
    """
    X, y = design(brows, names)
    oof = np.zeros(len(brows))
    for tr, te in folds:
        m = LogisticRegression(penalty="l1", solver="liblinear", C=best_C,
                               class_weight="balanced", max_iter=5000,
                               random_state=SEED).fit(X[tr], y[tr])
        oof[te] = m.predict_proba(X[te])[:, 1]
    full = LogisticRegression(penalty="l1", solver="liblinear", C=best_C,
                              class_weight="balanced", max_iter=5000,
                              random_state=SEED).fit(X, y)
    # instrument calibration on the unmasked rows (best case, as before)
    eng_tr = np.array([1 if r["node"] in base_eng else 0 for r in brows],
                      dtype=bool)
    p1 = (y[eng_tr].sum() + 1) / (eng_tr.sum() + 2)
    p0 = (y[~eng_tr].sum() + 1) / ((~eng_tr).sum() + 2)

    oof_by_node = {r["node"]: oof[i] for i, r in enumerate(brows)}
    Xa, ya = design(rows_all, names)
    pm_full = full.predict_proba(Xa)[:, 1]
    m_ll, i_ll, m_acc, i_acc = [], [], [], []
    for i, r in enumerate(rows_all):
        pmod = oof_by_node.get(r["node"], pm_full[i])
        eng = r["node"] in base_eng
        pinst = p1 if eng else p0
        if r["masked"]:
            m_acc.append(1.0)
            i_acc.append(1.0)
            m_ll.append(-np.log(max(pmod, 1 - pmod, 1e-6)))
            i_ll.append(-np.log(max(pinst, 1 - pinst, 1e-6)))
        else:
            lab = r["label"]
            m_acc.append(float((pmod >= 0.5) == (lab == 1)))
            i_acc.append(float(eng == (lab == 1)))
            m_ll.append(-np.log(max(1e-6, pmod if lab else 1 - pmod)))
            i_ll.append(-np.log(max(1e-6, pinst if lab else 1 - pinst)))
    return {"n_rows_scored": len(rows_all),
            "fitted_accuracy_all_rows_fair": round(float(np.mean(m_acc)), 4),
            "instrument_accuracy_all_rows_fair": round(float(np.mean(i_acc)), 4),
            "fitted_logloss_all_rows_fair": round(float(np.mean(m_ll)), 4),
            "instrument_logloss_all_rows_fair": round(float(np.mean(i_ll)), 4)}


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
    elif slot == "governs_conditional":
        # value is (quality, context); only the 'add' direction is expressible
        # in the instrument's own slot.
        q, c = value
        cur = copy.deepcopy(m.get("governs_conditional") or {})
        lst = list(cur.get(q) or [])
        if add:
            if c not in lst:
                lst.append(c)
        else:
            lst = [v for v in lst if v != c]
        cur[q] = lst
        m["governs_conditional"] = cur
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
                  base_correct, ctx_nodes, direct=False):
    """apply the proposed DISCRETE rule and count fixes/breaks."""
    base_eng = engaged_set(mod, br, corpus)
    if direct or slot == "contexts_concern":
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


def residual_targets(slug, census_rows, rows, names, masked):
    """RUN-2 amendment D: for every CURRENT UNRESOLVED mismatch (instrument
    disagrees with panel truth AND the disagreement is not adjudicated-
    defensible), which post-screen columns separate it from its census
    colliders? Zero separating columns => run-3 carving queue."""
    F = {r["node"]: set(r["features"]) for r in rows if r["behavior"] == slug}
    out, queue = {}, []
    for n, info in sorted(census_rows.items()):
        if (slug, n) in masked:
            continue                       # adjudicated defensible: resolved
        colliders = info["colliding_correct_nodes"]
        rec = {"verdict_needed": info["verdict_needed"],
               "census_status": info["status"],
               "colliders": colliders}
        if not colliders:
            rec["separating_columns"] = None
            rec["note"] = ("no census collider — already SEPARABLE at current "
                           "granularity; nothing to carve")
            out[n] = rec
            continue
        sep = [c for c in names
               if all((c in F[n]) != (c in F.get(m, set())) for m in colliders)]
        per = {m: sum(1 for c in names
                      if (c in F[n]) != (c in F.get(m, set())))
               for m in colliders}
        rec["separating_columns"] = sep
        rec["n_separating_columns"] = len(sep)
        rec["n_separating_interaction_columns"] = sum(
            1 for c in sep if c.startswith("x["))
        rec["columns_differing_per_collider"] = per
        if not sep:
            queue.append(n)
            rec["note"] = ("RUN-3 CARVING QUEUE: no post-screen column "
                           "separates this node from every collider")
        out[n] = rec
    return out, queue


def main():
    mods = json.load(open(P(CONTRACT)))["modules"]
    br = RBA.bridges()
    corpus = RBA.corpus_acts()
    pm = RBA.parent_map()
    sig, ap, pa, atoms = load_layers()
    masked, mask_src = defensible_mask()

    rows, names = build_matrix(mods, br, corpus, pm, sig, ap, pa, atoms, masked)
    n_base = len(names)
    rows, names, inter_stats, inter_detail = add_interactions(rows, names)

    json.dump({
        "_": ("feature matrix for L1 declaration search — one row per "
              "(behavior, node) panel-truth point. masked=true rows carry an "
              "adjudicated-defensible verdict and are EXCLUDED from fitting "
              "and from predicted fixes/breaks."),
        "inventory": {"contract": "v18", "run_seed": SEED,
                      "n_rows": len(rows), "n_features": len(names),
                      "n_base_features": n_base,
                      "n_interaction_features":
                          inter_stats["post_screen_interaction_columns"],
                      "n_masked": sum(1 for r in rows if r["masked"]),
                      "mask_sources": mask_src,
                      "status_classes": STATUS_CLASSES,
                      "act_relation_encodings": ["exact",
                                                 "mod_specific_beh_genus",
                                                 "mod_genus_beh_species"],
                      "act_encoding_note":
                          ("RUN-2 amendment C: 'exact' is behavior-blind "
                           "carries(A,s); the two relational encodings are "
                           "separate columns."),
                      "interaction_families":
                          ["%s x %s" % p for p in FAMILY_PAIRS],
                      "interaction_screen": inter_stats,
                      "interaction_screen_note":
                          ("RUN-2 amendment A. 'support' is read as the number "
                           "of rows where the product column is 1 (>=3 "
                           "required); label-positive support is reported per "
                           "column in 'interaction_columns' but was NOT used "
                           "as the screen. Screening is over all 836 matrix "
                           "rows, masked included, since column existence is a "
                           "property of the matrix, not of the fit. Exact "
                           "duplicate columns (identical support set) were "
                           "collapsed to one representative to keep stability "
                           "frequencies from splitting arbitrarily between "
                           "indistinguishable columns; the collapsed names are "
                           "listed under duplicate_column_aliases."),
                      "interaction_columns": inter_detail},
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
                  ("RUN-2 amendment B: 'fair_comparison_all_rows' scores ALL "
                   "rows of the behavior with adjudicated-defensible rows "
                   "credited correct for BOTH the instrument and the model, "
                   "which removes the mask's selection bias from the "
                   "head-to-head. The model's probabilities there are "
                   "out-of-fold on the fitted rows and full-fit on the masked "
                   "rows (which entered no fit); the instrument's are its "
                   "binary decision under best-case Laplace calibration. The "
                   "masked fit itself is unchanged."),
                  ("RUN-2 amendment A adds pairwise interaction columns. They "
                   "are still label-fitted: an interaction that survives "
                   "stability selection is a SUBTYPE HYPOTHESIS about the "
                   "document, and the fact that a conjunction predicts truth "
                   "better than either atom is exactly the kind of finding "
                   "that can be pure overfitting on ~200-350 rows."),
                  ("The two relational act encodings are behavior-dependent "
                   "by construction (they are defined against the behavior's "
                   "own performs set) but share a column namespace across "
                   "behaviors; fitting is per behavior, so no cross-behavior "
                   "mixing occurs."),
              ],
              "behaviors": {}}
    proposals, unmappable = [], []
    cen = sc.census(CONTRACT)     # pure function; the writing path is __main__

    for slug in SLUGS:
        mod = mods[slug]
        truth = sc.truth_all(slug)
        brows = [r for r in rows if r["behavior"] == slug and not r["masked"]]
        X, y = design(brows, names)
        base_eng = engaged_set(mod, br, corpus)
        eng_pred = np.array([1 if r["node"] in base_eng else 0 for r in brows])
        best, path, base_ll, inst_ll, folds = fit_behavior(X, y, eng_pred, grid)
        freq, med = stability(X, y, best["C"])
        rows_all = [r for r in rows if r["behavior"] == slug]
        fair = fair_all_rows(rows_all, names, best["C"], folds, brows, base_eng)
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
            "fair_comparison_all_rows": fair,
            "l1_path": path,
            "n_stable_features": sum(1 for v in stab.values() if v >= 0.7),
            "stability": stab,
            "median_coef": {k: round(float(med[names.index(k)]), 4)
                            for k in stab},
        }

        # ------------- RUN-2 amendment D: residual carving queue
        rt, queue = residual_targets(slug, cen.get(slug, {}), rows, names,
                                     masked)
        report["behaviors"][slug]["residual_targets"] = {
            "_": ("unresolved mismatches = instrument-vs-truth disagreements "
                  "that are NOT adjudicated-defensible; colliders are the "
                  "satisfiability census's colliding correct nodes of the "
                  "opposite verdict. A column separates only if it differs "
                  "from EVERY collider."),
            "_granularity_caveat": (
                "the collider relation comes from satisfiability_census, whose "
                "vector() reads assert_signature/protects/purpose_actor ONLY — "
                "it does not merge the definition_* lanes and does not include "
                "the consensus context atoms, both of which the instrument and "
                "this feature matrix do use. So some 'separating columns' "
                "reported here separate at the matrix's granularity while the "
                "census still calls the pair a collision; the census, not the "
                "matrix, is the stale side. The carving queue below is the "
                "conservative end: those nodes are identical to their "
                "colliders on EVERY post-screen column, interactions "
                "included."),
            "n_unresolved": len(rt),
            "n_with_no_collider": sum(
                1 for v in rt.values() if v["separating_columns"] is None),
            "n_with_separating_column": sum(
                1 for v in rt.values()
                if v["separating_columns"]),
            "n_carving_queue": len(queue),
            "carving_queue": queue,
            "targets": rt,
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
            kind = "add" if add else "wall"
            direct = False
            parents = None

            if feat.startswith("x["):
                # ---- RUN-2 amendment A: interaction column
                a, b = feat[2:-1].split("&", 1)
                fa, va = a.split("=", 1)
                fb, vb = b.split("=", 1)
                parents = {fa: va, fb: vb}
                if {fa, fb} == {"governs", "context"}:
                    q = va if fa == "governs" else vb
                    c = vb if fb == "context" else va
                    if add:
                        if q in gov_decl:
                            why = ("governs x context, but the quality is "
                                   "already declared UNCONDITIONALLY in "
                                   "governs_concern — the conditional adds "
                                   "nothing")
                        elif c in (gov_cond.get(q) or []):
                            why = ("governs x context already consumed by "
                                   "governs_conditional")
                        else:
                            slot = "governs_conditional"
                            delta = {"governs_conditional": {q: ["+" + c]}}
                            val = (q, c)
                    else:
                        # a conditional WALL is not expressible in the slot
                        # (governs_conditional only ever widens engagement), so
                        # the discrete rule is applied directly.
                        slot, schema_ext, direct = "governs_conditional", True, True
                        kind = "wall"
                        delta = {"governs_conditional": {q: ["!" + c]}}
                        val = (q, c)
                else:
                    kind = "subtype"
                    slot = {"protects": "protects_concern",
                            "purpose": "purpose_concern",
                            "context": "contexts_concern"}[
                        fb if fb != "act" else fa]
                    schema_ext, direct = True, True
                    delta = {"subtypes": [{
                        "direction": "engage" if add else "wall",
                        "target_slot": slot,
                        "parents": parents}]}
                    val = feat
            elif fam == "governs":
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
                                          truth, keep, base_correct, ctx_nodes,
                                          direct=direct)
            mech = None
            if direct:
                mech = ("no instrument slot expresses this rule today "
                        "(schema extension); predicted fixes/breaks were "
                        "computed by applying the stated discrete rule "
                        "directly — %s every node carrying the column — to "
                        "the current engaged set."
                        % ("engaging" if add else "dropping"))
            if add and slot in ("protects_concern", "governs_concern") \
                    and not (mod.get(slot) or []):
                mech = (f"{slot} is currently EMPTY for this behavior, which "
                        f"the instrument reads as fail-open (no wall). Adding "
                        f"the first value switches the wall on wholesale — the "
                        f"predicted breaks below are dominated by that "
                        f"activation, not by the value itself.")
            proposals.append({
                "behavior": slug,
                "kind": kind,
                "direction": "add" if add else "wall",
                "parent_atoms": parents,
                "slot": slot,
                "schema_extension": schema_ext,
                "delta": delta,
                "feature": feat,
                "stability": round(float(s), 3),
                "median_coef": round(coef, 4),
                "predicted": {"fixes": len(fixed), "breaks": len(broken),
                              "fixed_nodes": fixed, "broken_nodes": broken},
                "blind_justification_stub": stub(slug, slot, val, add, parents),
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


def stub(slug, slot, val, add, parents=None):
    verb = "should" if add else "should not"
    if parents:
        both = " and ".join(f"{k} '{v}'" for k, v in sorted(parents.items()))
        val = both
        return (f"HYPOTHESIS for 9b: read blind, would a document-side reader "
                f"say that a clause which is BOTH {both} {verb} bear on "
                f"'{slug}' — i.e. is the conjunction, not either atom alone, "
                f"the thing the behavior is about? The a-priori case would "
                f"have to come from the behavior's own definition, not from "
                f"the panel labels that produced this interaction column.")
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
