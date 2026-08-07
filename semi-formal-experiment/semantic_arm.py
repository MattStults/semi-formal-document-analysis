"""semantic_arm.py — IS THE MISSING RULE DERIVABLE FROM THE DOCUMENT'S MEANING?

⚠️ THIS MODULE IS A ONE-SHOT DIAGNOSTIC. NOTHING IT COMPUTES MAY EVER SHIP. ⚠️
=============================================================================
Pre-registration: `SEMANTIC_ARM_PREREGISTRATION.md`, written and frozen BEFORE
any number here was computed. Read it first; the predictions are the point.

WHY THIS EXISTS
---------------
`HANDOFF.md` closes the label-free leads and says the residual +0.278 -> +0.591
is not derivable from "anything the corpus supplies". That rests on an
enumeration — 54 re-weighting variants, eight passage priors, a regression of
the learned per-atom coefficient on five surface statistics (R^2 = 0.039) —
which contains NO distributional semantics at all. `relevance.py:4` forbids
loading an embedding model BY CONTRACT, so the space was excluded by design and
never measured. "We tried thirteen ways to re-weight exact name matches" does
not answer "is there meaning in the text we never mined".

The near-injectivity of the atom index (534 classes / 589 passages) and the
supervised ceiling together prove the atoms DISTINGUISH the passages and that a
rule over them exists. Neither shows the DOCUMENT cannot supply that rule. This
module tests exactly that gap in the argument.

TWO ARMS, AND WHY BOTH ARE NEEDED
---------------------------------
  A. document-internal — LSA over this spec's own text, no external corpus.
     Tests "the meaning was in the document, unmined".
  B. pretrained — `text-embedding-3-small`, an outside corpus.
     Tests "the knowledge came from outside".

A alone is not decisive: 589 passages is thin, so an A-null is confounded with
power. Only the PATTERN across A and B separates the two readings.

WHAT AN EMBEDDING BUYS THAT A RE-WEIGHTING CANNOT
-------------------------------------------------
The shipped query fires on EXACT atom-name overlap: a passage atom either is a
query atom or contributes nothing. Every one of the 54 prior variants changed
only the WEIGHT on an exact match. A semantic space allows SOFT matching — a
passage atom merely NEAR a query atom can contribute — which is a different
functional form, not a re-parameterisation. That is scorer 2 below, and it is
the real content of this arm.
"""

from __future__ import annotations

import json
import math
import os
import sys
import urllib.request
from collections import defaultdict

REPO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)

import threshold as T
import weight_diag as W

EMBED_MODEL = "text-embedding-3-small"
EMBED_PRICE_PER_1M = 0.02
DIMS = (25, 50, 100, 200)


# --------------------------------------------------------------- text units

def behaviour_text(D, slug) -> str:
    b = D.panel[slug]
    return f"{b.get('name', '')}. {b.get('definition', '')}".strip()


def atom_text(D, name) -> str:
    """An atom's own words: its name and the longest gloss recorded for it."""
    gloss = D.atom_gloss.get(name, "")
    pretty = name.replace("_", " ").replace("-", " ")
    return f"{pretty}. {gloss}".strip()


def clause_text(D) -> dict:
    return {c["id"]: (c.get("quote") or "") for c in D.clauses}


def atom_contexts(D) -> dict:
    """atom -> the concatenated text of every clause it appears on.

    This is the document-internal definition of an atom's meaning: not its
    name, but the company it keeps. It is what LSA can actually exploit.
    """
    ct = clause_text(D)
    out = defaultdict(list)
    for cid, names in D.clause_names.items():
        t = ct.get(cid, "")
        if not t:
            continue
        for n in names:
            out[n].append(t)
    return {n: " ".join(v) for n, v in out.items()}


# ------------------------------------------------------------------- arm A

def arm_a_vectors(D, k):
    """LSA over the spec's own text ONLY. Returns (atom_vecs, passage_vecs, beh_vecs).

    The vectorizer is fitted on the 589 passages plus every clause quote — the
    document and nothing else. Atom and behaviour strings are TRANSFORMED by
    that fitted vectorizer, never added to the fit, so no query-side text can
    leak into the corpus statistics.
    """
    import numpy as np
    from sklearn.decomposition import TruncatedSVD
    from sklearn.feature_extraction.text import TfidfVectorizer

    ct = clause_text(D)
    corpus = [D.text[l] for l in D.locs] + [ct[c] for c in sorted(ct) if ct[c]]
    vec = TfidfVectorizer(stop_words="english", sublinear_tf=True, min_df=2)
    Xc = vec.fit_transform(corpus)
    svd = TruncatedSVD(n_components=k, random_state=20260806)
    svd.fit(Xc)

    def embed(strings):
        if not strings:
            return np.zeros((0, k), dtype=np.float32)
        return svd.transform(vec.transform(strings)).astype(np.float32)

    ctx = atom_contexts(D)
    names = sorted(D.vocab)
    # an atom's document-internal meaning = its contexts + its own gloss
    atom_strings = [f"{ctx.get(n, '')} {atom_text(D, n)}" for n in names]
    A = embed(atom_strings)
    P = embed([D.text[l] for l in D.locs])
    B = embed([behaviour_text(D, s) for s in D.slugs])
    return ({n: A[i] for i, n in enumerate(names)},
            {l: P[i] for i, l in enumerate(D.locs)},
            {s: B[i] for i, s in enumerate(D.slugs)})


# ------------------------------------------------------------------- arm B

def _openai_key() -> str:
    """From the env, or parsed out of ~/.zshrc WITHOUT sourcing it.

    The value is never printed, logged, or written to any artifact.
    """
    k = os.environ.get("OPENAI_API_KEY")
    if k:
        return k.strip()
    path = os.path.expanduser("~/.zshrc")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8", errors="replace"):
            line = line.strip()
            if line.startswith("export OPENAI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no OPENAI_API_KEY available; run with --arm a")


def _embed_batch(strings, key):
    body = json.dumps({"model": EMBED_MODEL, "input": strings}).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/embeddings", data=body,
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        payload = json.loads(r.read())
    rows = sorted(payload["data"], key=lambda d: d["index"])
    return [d["embedding"] for d in rows], payload.get("usage", {}).get("total_tokens", 0)


def arm_b_vectors(D, cache=os.path.join(REPO, "semantic_arm_embeddings.json")):
    """`text-embedding-3-small` over the same three string sets. Cached on disk.

    The cache exists so a re-run costs $0 and is bit-identical — this project's
    determinism rule applies to paid calls too.
    """
    import numpy as np

    names = sorted(D.vocab)
    want = {}
    for n in names:
        want[f"atom::{n}"] = atom_text(D, n)
    for l in D.locs:
        want[f"passage::{l}"] = D.text[l]
    for s in D.slugs:
        want[f"beh::{s}"] = behaviour_text(D, s)

    have = {}
    if os.path.exists(cache):
        have = json.load(open(cache))
    todo = [k for k in want if k not in have]
    spent_tokens = 0
    if todo:
        key = _openai_key()
        for i in range(0, len(todo), 128):
            chunk = todo[i:i + 128]
            vecs, tok = _embed_batch([want[c][:8000] for c in chunk], key)
            spent_tokens += tok
            have.update(dict(zip(chunk, vecs)))
        json.dump(have, open(cache, "w"))
        cost = spent_tokens / 1e6 * EMBED_PRICE_PER_1M
        print(f"[arm B] embedded {len(todo)} strings, {spent_tokens} tokens, "
              f"${cost:.5f}")
    else:
        print("[arm B] all embeddings served from cache, $0.00000")

    def arr(prefix, keys):
        return {k: np.asarray(have[f"{prefix}::{k}"], dtype=np.float32) for k in keys}

    return arr("atom", names), arr("passage", D.locs), arr("beh", D.slugs)


# ------------------------------------------------------------------ scoring

def _unit(v):
    import numpy as np
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


def soft_scores(D, slug, atom_vecs, use_idf, floor=0.0):
    """score(passage) = sum over query atoms of the BEST match in that passage.

    `floor` clips negative cosines to 0: LSA components are signed and a
    negative cosine is not evidence of anti-relevance, it is noise.
    """
    import numpy as np

    q = sorted(D.query_atoms(slug) & set(atom_vecs))
    if not q:
        raise ValueError(f"{slug}: no query atom has a vector")
    Q = np.stack([_unit(atom_vecs[n]) for n in q])
    if use_idf:
        qw = np.array([W._idf(D.clause_df.get(n, 0), D.n_clauses) for n in q],
                      dtype=np.float32)
    else:
        qw = np.ones(len(q), dtype=np.float32)

    out = []
    for l in D.locs:
        pa = sorted(D.atoms[l] & set(atom_vecs))
        if not pa:
            out.append(0.0)
            continue
        Pm = np.stack([_unit(atom_vecs[n]) for n in pa])
        sim = Q @ Pm.T                      # |q| x |passage atoms|
        best = np.clip(sim.max(axis=1), floor, None)
        out.append(float((best * qw).sum()))
    return out


def text_cosine_scores(D, slug, passage_vecs, beh_vecs):
    import numpy as np
    b = _unit(beh_vecs[slug])
    return [float(np.dot(b, _unit(passage_vecs[l]))) for l in D.locs]


def exact_scores(D, slug):
    """The SHIPPED functional form: IDF over EXACT atom-name overlap."""
    return W.query_scores(D, slug, W.LABEL_FREE_VARIANTS()["idf (SHIPPED)"])


# ----------------------------------------------------------------- measuring

def evaluate(D, score_fn):
    """Mean MCC at the label-free Otsu cut, and mean AUC, over the 9 cells."""
    mccs, aucs, per_cell = [], [], []
    for slug, judge in D.cells():
        s = score_fn(slug)
        y = D.golds[(slug, judge)]
        cut = T.otsu(s)
        pred = [1 if v > cut else 0 for v in s]
        m = W.mcc_pred(pred, y)
        a = W.auc(s, y)
        mccs.append(m)
        aucs.append(a)
        per_cell.append({"slug": slug, "judge": judge, "mcc": m, "auc": a})
    return {"mcc": sum(mccs) / len(mccs), "auc": sum(aucs) / len(aucs),
            "cells": per_cell}


def run(arm, D, results):
    if arm == "a":
        for k in DIMS:
            av, pv, bv = arm_a_vectors(D, k)
            results[f"A/lsa-{k}/soft-match"] = evaluate(
                D, lambda s, av=av: soft_scores(D, s, av, use_idf=False))
            results[f"A/lsa-{k}/soft-match x idf"] = evaluate(
                D, lambda s, av=av: soft_scores(D, s, av, use_idf=True))
            results[f"A/lsa-{k}/passage-text cosine"] = evaluate(
                D, lambda s, pv=pv, bv=bv: text_cosine_scores(D, s, pv, bv))
            print(f"  [arm A] k={k} done")
    else:
        av, pv, bv = arm_b_vectors(D)
        results["B/openai/soft-match"] = evaluate(
            D, lambda s: soft_scores(D, s, av, use_idf=False))
        results["B/openai/soft-match x idf"] = evaluate(
            D, lambda s: soft_scores(D, s, av, use_idf=True))
        results["B/openai/passage-text cosine"] = evaluate(
            D, lambda s: text_cosine_scores(D, s, pv, bv))
        print("  [arm B] done")


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", choices=("a", "b", "both"), default="both")
    ap.add_argument("--out", default=os.path.join(REPO, "semantic_arm_results.json"))
    args = ap.parse_args(argv)

    D = W.data()
    results = {"ANCHOR/exact idf (SHIPPED FORM)": evaluate(D, lambda s: exact_scores(D, s))}
    print("  [anchor] done")

    for arm in (("a", "b") if args.arm == "both" else (args.arm,)):
        run(arm, D, results)

    print(f"\n{'scorer':<38} {'mean MCC':>9} {'mean AUC':>9}")
    print("-" * 58)
    anchor = results["ANCHOR/exact idf (SHIPPED FORM)"]
    for name, r in results.items():
        d = r["mcc"] - anchor["mcc"]
        flag = "" if name.startswith("ANCHOR") else f"   (d={d:+.3f})"
        print(f"{name:<38} {r['mcc']:>+9.3f} {r['auc']:>9.3f}{flag}")
    print("\nnoise floor 0.045 | falsification bar +0.400 mean MCC")

    json.dump(results, open(args.out, "w"), indent=1, sort_keys=True)
    print(f"\nwrote {args.out}")
    return results


if __name__ == "__main__":
    main()
