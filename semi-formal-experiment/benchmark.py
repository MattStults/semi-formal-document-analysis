"""Benchmark: does a tool find behavioural relevance in the Model Spec as well
as simply asking a frontier model?

The reference data is an LLM panel (three frontier judges) scoring Model Spec
passages 0-2 each for relevance to a behaviour; `score` is the sum, max 6.
Nothing here calls a model — it is arithmetic over data already on disk.

Four things this module insists on, because each one can silently manufacture
a favourable number if left out:

0. THE EVALUATION UNIVERSE IS THE ONE THE JUDGES ACTUALLY GRADED — all 589
   model-spec passages (374 for the constitution), not the 377/333/153 the site
   published. The publisher deleted every passage whose summed panel score was
   0; those are true negatives every judge earned, and deleting them cost the
   judges (+0.161 mean MCC) far more than the tool (+0.046). `load_true_panel`
   is the default for every metric, `load_panel` is the published comparison,
   and `check_universe_pairing` refuses to let a headline be emitted on one
   universe alone. See `panel_universe` for the reconstruction.

1. The relevance threshold is a PARAMETER. `reference(b, min_score=5)` is a
   choice, not a fact; every report also prints the strict unanimous-at-maximum
   set (score == 2 * n_judges) so the reader can see how much the headline
   moves when the cutoff does.

2. The bar is the PANEL'S OWN AGREEMENT, and specifically its leave-one-out
   number — one judge predicting the other two's consensus. That is what
   "just ask a frontier model" actually buys you. The 3-judge consensus is a
   committee and is not the thing we are competing with.

3. ZERO-MATCH ACCOUNTING. A reference passage that maps to no clause in our
   segmentation is neither a hit nor a miss; dropping it from the denominator
   inflates recall for free. Every report states how many were lost and why,
   split into `example_block` / `not_verbatim_in_source` /
   `verbatim_but_unsegmented`, and prints scores both over the matched subset
   and over the full reference set (unmatched counted as misses). The gap
   between those two numbers is the coverage cost, stated rather than hidden.

Judge names are read from the data, never hardcoded: the panel does not use
the same three judges for every behaviour (helpfulness has fable/kimi/sol,
harm-avoidance has kimi/opus/sol, over-under-caution has fable/kimi-k2/sol).

Clause source: `modelspec_clauses.json` if present, else the focus areas via
`inventory.load_all()`. Both are normalized to inventory's row shape and joined
with `inventory.match_passage`, whose quote-containment + normalization (drop
`[^xxxx]` footnote markers, collapse the source's hard-wrap whitespace) is
exactly the join this needs; see `load_clauses` for the one adaptation.

A judge is also a single (FPR, TPR) point while the tool is a curve, so every
thresholded comparison here is accompanied by a THRESHOLD-FREE one: the tool's
AUC and its TPR at each judge's own FPR (`roc_block`). And the MCC is reported
as a BAND over the sane threshold range plus the full curve (`mcc_band_block`),
never as the LOBO point estimate, whose n=3 95% CI contains zero.

Usage:
  .venv/bin/python benchmark.py            # panel agreement + zero-match report
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
from itertools import combinations

import inventory

HERE = os.path.dirname(os.path.abspath(__file__))
#: THE BAR. Was an absolute path into a THIRD repo (`ai_character_index-mvp`),
#: which meant this module only worked on one machine with three checkouts
#: side by side. Now vendored at `data/behaviours.json` in this repo.
#: NOTE there are three different files named `behaviours.json` in that
#: workspace and they are NOT interchangeable: this one is the panel WITH
#: citations (377/333/153); `data/behaviour-definitions.json` is the 11-entry
#: label/definition file; `site/spec-reader-test/data/behaviours.json` is
#: panel_v2's metadata. Loading the wrong one yields empty queries and a
#: silently de-behaviourised score.
PANEL = os.path.join(HERE, "..", "data", "behaviours.json")
CLAUSES = os.path.join(HERE, "modelspec_clauses.json")

#: Independent draws of the behaviour atoms. The stability rule re-queries with
#: each and asks which cut leaves the PREDICTED SET most agreed — a label-free
#: question about the scores, not about the panel.
ATOM_DRAWS = ("behavior_atoms_b8.json", "behavior_atoms_draw1.json",
              "behavior_atoms_draw2.json", "behavior_atoms_draw3.json",
              "behavior_atoms_draw4.json")

DEFAULT_MIN_SCORE = 5
THRESHOLDS = (1, 2)  # per-judge: >=1 "any relevance", ==2 handled as >=2 (max)

STRATA = ("example_block", "not_verbatim_in_source", "verbatim_but_unsegmented",
          "unknown")


# ---------------------------------------------------------------- panel data

def load_panel(path: str = PANEL) -> dict:
    """slug -> behaviour dict, EXACTLY AS PUBLISHED — the BROKEN universe.

    `build_site_data.keeps_citation` dropped every passage whose summed panel
    score was 0 before this file was written, so it holds 377/333/153 of the
    589 passages each judge actually graded. Use `load_true_panel` for any
    metric; this loader exists to reproduce the published numbers side by side
    with the corrected ones, never to stand alone.
    """
    with open(path) as f:
        data = json.load(f)
    return {b["slug"]: b for b in data["behaviours"]}


def load_true_panel(path: str = PANEL, spec_keys=("openai", "anthropic"),
                    with_provenance: bool = False):
    """slug -> behaviour dict on the TRUE judged universe. THE DEFAULT.

    Delegates to `panel_universe`, which rebuilds the passage list the judges
    were actually prompted with (589 for the model spec, 374 for the
    constitution) and restores every dropped passage as verdict 0 from every
    judge. See that module's docstring for why this is a restoration rather
    than an invention.
    """
    import panel_universe
    return panel_universe.load_universe(path, spec_keys, with_provenance)


#: Which universe the reporting layer treats as authoritative. "published" is
#: retained only for the side-by-side delta.
DEFAULT_UNIVERSE = "true"
UNIVERSE_LABEL = {"true": "TRUE universe (every passage the judges graded)",
                  "published": "published universe (score-0 passages deleted)"}


def load_universe_panel(universe: str = DEFAULT_UNIVERSE, path: str = PANEL) -> dict:
    """`load_true_panel` or `load_panel`, by name. One place decides."""
    if universe == "true":
        return load_true_panel(path)
    if universe == "published":
        return load_panel(path)
    raise ValueError(f"unknown universe {universe!r} — "
                     f"expected one of {sorted(UNIVERSE_LABEL)}")


#: Which spec's coverage to read. The panel file carries an `anthropic` side
#: too (1336 passages across both; openai alone is 863). Nothing here may
#: hardcode "openai" in a way that makes the constitution panel unreachable —
#: spec-swappability is the point of the whole tool.
DEFAULT_SPEC_KEY = "openai"


def spec_keys(behaviour) -> list:
    """Which specs this behaviour has coverage for."""
    return sorted((behaviour.get("coverage") or {}))


def passages(behaviour, spec_key: str = DEFAULT_SPEC_KEY) -> list:
    return ((behaviour.get("coverage") or {}).get(spec_key) or {}).get(
        "passages") or []


def judges(behaviour, spec_key: str = DEFAULT_SPEC_KEY) -> list:
    """Judge keys, read off the data. Sorted for stable output.

    THE PANEL DIFFERS PER BEHAVIOUR (helpfulness fable/kimi/sol, harm-avoidance
    kimi/opus/sol, over/under-caution fable/kimi-k2/sol), so this is derived,
    never hardcoded: a hardcoded panel scores the other two behaviours 0.000,
    which reads as a modelling failure rather than a parsing bug.
    """
    ks = set()
    for p in passages(behaviour, spec_key):
        ks.update(p.get("verdicts") or {})
    return sorted(ks)


def verify_verdicts(behaviour, spec_key: str = DEFAULT_SPEC_KEY) -> dict:
    """Data-integrity gate: `score` must equal `sum(verdicts.values())`.

    If this ever fails the panel file has changed shape and the benchmark must
    refuse to run rather than silently mis-score. Returns counts plus the
    offending passage ids.
    """
    ps = passages(behaviour, spec_key)
    bad = [p.get("id") for p in ps
           if p.get("score") != sum((p.get("verdicts") or {}).values())]
    missing = [p.get("id") for p in ps if not p.get("verdicts")]
    return {"total": len(ps), "ok": len(ps) - len(bad), "mismatch": bad,
            "missing_verdicts": missing}


def max_score(behaviour) -> int:
    """2 points per judge."""
    return 2 * len(judges(behaviour))


# ------------------------------------------------------- reference sets (1)

def reference(behaviour, min_score: int = DEFAULT_MIN_SCORE) -> list:
    """Passages whose summed panel score is at least `min_score`.

    The threshold is deliberately an argument. `min_score=5` is the working
    cutoff; `strict_reference` is the unanimous-at-maximum set.
    """
    return [p for p in passages(behaviour) if p.get("score", 0) >= min_score]


def strict_reference(behaviour) -> list:
    """Unanimous at maximum: every judge gave 2 (score == 2 * n_judges)."""
    return reference(behaviour, min_score=max_score(behaviour))


def reference_ids(behaviour, min_score: int = DEFAULT_MIN_SCORE) -> set:
    return {p["id"] for p in reference(behaviour, min_score)}


# ------------------------------------------------- panel self-agreement (2)

def judge_set(behaviour, judge: str, threshold: int = 1,
               spec_key: str = DEFAULT_SPEC_KEY) -> set:
    """Passage ids this judge rated at or above `threshold` (1 = any relevance,
    2 = maximum). Missing verdict counts as 0."""
    return {p["id"] for p in passages(behaviour, spec_key)
            if (p.get("verdicts") or {}).get(judge, 0) >= threshold}


def jaccard(a, b) -> float:
    a, b = set(a), set(b)
    union = a | b
    return len(a & b) / len(union) if union else 1.0


def prf(predicted, ref, extra_fn: int = 0) -> dict:
    """Precision/recall/F1 with the raw confusion counts.

    `extra_fn` are reference items the predictor structurally COULD NOT have
    produced (unmatched panel passages). They are added to fn so recall is
    computed over the full reference set. No division by zero anywhere: an
    empty predictor gets recall 0.0, not a crash.
    """
    predicted, ref = set(predicted), set(ref)
    tp = len(predicted & ref)
    fp = len(predicted - ref)
    fn = len(ref - predicted) + extra_fn
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) else 0.0)
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision,
            "recall": recall, "f1": f1}


def panel_agreement(behaviour) -> dict:
    """The bar to beat.

    `pairwise[t][a|b]`  Jaccard of two judges' relevant sets at per-judge
                        threshold t.
    `leave_one_out[t][j]` judge j scored against the CONSENSUS of the other
                        two (both of them at threshold t). This is the real
                        bar: it is what one frontier model gets you.

    Both are reported at t=1 (any relevance) and t=2 (maximum).
    """
    js = judges(behaviour)
    out = {"judges": js, "n_passages": len(passages(behaviour)),
           "pairwise": {}, "leave_one_out": {}}
    for t in THRESHOLDS:
        sets = {j: judge_set(behaviour, j, t) for j in js}
        out["pairwise"][t] = {
            f"{a}|{b}": jaccard(sets[a], sets[b]) for a, b in combinations(js, 2)
        }
        loo = {}
        for j in js:
            others = [o for o in js if o != j]
            consensus = set.intersection(*[sets[o] for o in others]) if others else set()
            m = prf(sets[j], consensus)
            m["jaccard"] = jaccard(sets[j], consensus)
            m["n_judge"] = len(sets[j])
            m["n_consensus"] = len(consensus)
            m["others"] = others
            loo[j] = m
        out["leave_one_out"][t] = loo
    return out


def loo_mean(agreement, threshold: int = 1, key: str = "f1") -> float:
    loo = agreement["leave_one_out"][threshold]
    return sum(m[key] for m in loo.values()) / len(loo) if loo else 0.0


# --------------------------------------------------------- clause inventory

def _clause_rows(raw) -> list:
    """Normalize any plausible clause-file shape into inventory row shape.

    Accepts a bare list, or a dict with a `clauses`/`rows`/`atoms` list.
    A row needs an id (`id`/`clause_id`/`focus_id`) and text
    (`quote`/`text`/`clause_text`); `marked_span` is optional and falls back to
    None, which `inventory.match_passage` already tolerates.
    """
    if isinstance(raw, dict):
        for k in ("clauses", "rows", "atoms", "items"):
            if isinstance(raw.get(k), list):
                raw = raw[k]
                break
        else:
            raise ValueError("clause file is a dict with no clause list")
    rows = []
    for i, r in enumerate(raw):
        rid = r.get("id") or r.get("clause_id") or r.get("focus_id")
        quote = r.get("quote") or r.get("text") or r.get("clause_text") or ""
        if rid is None or not quote:
            continue
        # Carry the WHOLE clause record forward, overriding only the two fields
        # this module normalizes. Rebuilding a row from a fixed key list silently
        # dropped `section_path`, which left RelevanceIndex with a single section
        # containing all 593 clauses: the section channel (0.45 of the weight)
        # degenerated into a constant added to every clause, pinning the minimum
        # normalized score at ~0.30 — exactly DEFAULT_THRESHOLD — so the tool
        # predicted 592/593 clauses and reported MCC ~0. Every test fixture
        # hand-built rows *with* section_path, so 631 tests passed with the
        # channel dead. Pass records through; do not enumerate keys.
        row = dict(r)
        row["id"] = str(rid)
        row["quote"] = quote
        row.setdefault("marked_span", None)
        row.setdefault("locator", "")
        rows.append(row)
    return rows


def load_clauses(path: str = CLAUSES, fallback=True):
    """(rows, source_label). Prefers `modelspec_clauses.json`; falls back to the
    focus areas if it is absent, unreadable, or yields no usable rows — another
    agent produces that file and it may not exist yet."""
    try:
        with open(path) as f:
            rows = _clause_rows(json.load(f))
        if rows:
            return rows, os.path.basename(path)
    except (OSError, ValueError, json.JSONDecodeError, KeyError, TypeError):
        pass
    if not fallback:
        raise FileNotFoundError(path)
    return inventory.load_all(), "modelspec_focus_areas.json"


def spec_text(path: str = inventory.SPEC_MD) -> str:
    try:
        return inventory.spec_text(path)
    except OSError:
        return ""


# -------------------------------------------- the join + zero-match ledger

def map_reference(behaviour, clauses, min_score: int = DEFAULT_MIN_SCORE,
                  spec: str | None = None) -> dict:
    """Map reference passages onto clause ids, and account for every failure.

    Uses `inventory.match_passage` unchanged — its normalization (footnote
    markers stripped, whitespace collapsed) and its containment-in-either-
    direction rule are precisely what this join needs; the only adaptation is
    upstream, in `_clause_rows`, coercing foreign clause files into the row
    shape it expects.

    Returns per-passage clause lists, the union clause set, and the zero-match
    strata. `strata` always sums to len(unmatched).
    """
    if spec is None:
        spec = spec_text()
    norm_spec = inventory._norm(spec) if spec else ""
    refs = reference(behaviour, min_score)
    per_passage, clause_ids, unmatched = {}, set(), []
    strata = {k: [] for k in STRATA}
    for p in refs:
        hits = [r["id"] for r in inventory.match_passage(p.get("quote", ""), clauses)]
        per_passage[p["id"]] = hits
        if hits:
            clause_ids.update(hits)
            continue
        unmatched.append(p["id"])
        if p.get("exampleBlock"):
            strata["example_block"].append(p["id"])
        elif not norm_spec:
            strata["unknown"].append(p["id"])
        elif inventory._norm(p.get("quote", "")) not in norm_spec:
            strata["not_verbatim_in_source"].append(p["id"])
        else:
            strata["verbatim_but_unsegmented"].append(p["id"])
    assert sum(len(v) for v in strata.values()) == len(unmatched)
    return {
        "min_score": min_score,
        "n_reference": len(refs),
        "n_matched": len(refs) - len(unmatched),
        "per_passage": per_passage,
        "clause_ids": clause_ids,
        "unmatched": unmatched,
        "strata": {k: len(v) for k, v in strata.items()},
        "strata_ids": strata,
    }


# ------------------------------------------------------ scoring a tool (3)

def score_tool(predicted_passages, behaviour, clauses=None,
               min_score: int = DEFAULT_MIN_SCORE, spec: str | None = None,
               mapping: dict | None = None) -> dict:
    """Score a set of predicted clause ids against a chosen reference set.

    `matched`  clause-level P/R/F1 over the reference passages we could map.
    `full`     same, with every unmatched reference passage added as a false
               negative — the score we are entitled to claim.
    `passage_level` a reference passage counts as recalled if ANY of its clause
               ids was predicted; reported over matched and full denominators.

    The `matched` -> `full` gap IS the coverage cost. Both are always returned;
    neither is optional.
    """
    if mapping is None:
        if clauses is None:
            clauses, _ = load_clauses()
        mapping = map_reference(behaviour, clauses, min_score, spec)
    predicted = set(predicted_passages)
    ref = mapping["clause_ids"]
    n_unmatched = len(mapping["unmatched"])

    matched = prf(predicted, ref)
    full = prf(predicted, ref, extra_fn=n_unmatched)

    hit_passages = sum(1 for pid, cids in mapping["per_passage"].items()
                       if predicted & set(cids))
    n_matched_p = mapping["n_matched"]
    n_ref_p = mapping["n_reference"]
    passage_level = {
        "hit": hit_passages,
        "recall_matched": hit_passages / n_matched_p if n_matched_p else 0.0,
        "recall_full": hit_passages / n_ref_p if n_ref_p else 0.0,
        "n_matched": n_matched_p,
        "n_reference": n_ref_p,
    }
    return {
        "behaviour": behaviour.get("slug"),
        "min_score": min_score,
        "n_predicted": len(predicted),
        "n_reference_passages": n_ref_p,
        "n_reference_clauses": len(ref),
        "matched": matched,
        "full": full,
        "passage_level": passage_level,
        "zero_match": {"total": n_unmatched, **mapping["strata"]},
        "coverage_cost_recall": matched["recall"] - full["recall"],
    }


# ====================================================================
#  THE PAIR-GOLD PROTOCOL  (the only basis on which tool and judge are
#  comparable, and the basis every headline number is computed on)
# ====================================================================
#
# The bar quoted throughout this project — 0.764 / 0.780 / 0.500 — is:
#
#   * judge j predicts RELEVANT iff its label is `core` OR `related` (>= 1);
#     core-only does NOT reproduce the numbers;
#   * gold for j = BOTH other judges predict relevant (not "either");
#   * F1(pred_j, gold_j) over that behaviour's FULL passage list;
#   * bar = max over j, "mean LOO" = mean over j.
#
# So the tool is scored against those SAME three pair-golds and its mean
# reported beside the judges' — same passages, same gold construction, no
# favouritism. `test_real_bar_reproduces_the_quoted_numbers` pins this.
#
# Two things this section refuses to let a report omit:
#
#   FLOOR. Marking everything relevant gives precision = base rate, recall 1,
#   F1 = 2p/(1+p). That, not 0.0, is the true zero. On one target here the
#   floor (0.646) is ABOVE the best judge (0.500) — a degenerate predictor
#   would "beat the bar". Any F1 quoted without its floor is uninterpretable.
#
#   FULL vs MATCHED. Gold lives on passages; the tool predicts clauses. A
#   passage that joins to no clause can never be predicted, so it is an
#   automatic miss on the full reference. Both numbers, always.

# The separator is a spaced em-dash. Requiring the surrounding whitespace
# matters: judge names contain hyphens (`Kimi-K3`, `Kimi-K2.6`), so a lenient
# `[—-]` splits `Kimi-K3` into `Kimi` and silently loses a judge.
JUDGE_LINE = re.compile(r"^[✓~✗x]\s*(.+?)\s+[—–-]\s+(.+)$")
LABEL_VALUE = {"core": 2, "not relevant": 0}      # anything else -> 1 (related)


def panel_judge_names(behaviour, spec_key: str = DEFAULT_SPEC_KEY) -> list:
    """Judge display names, parsed out of the `role` free text.

    Read dynamically because THE PANEL DIFFERS PER BEHAVIOUR — helpfulness uses
    Claude Fable 5, harm-avoidance Claude Opus 4.8, over/under-caution
    Kimi-K2.6. Hardcoding one panel silently scores the other two behaviours
    0.000, which reads as a modelling failure rather than a parsing bug.
    """
    names = set()
    for p in passages(behaviour, spec_key):
        for line in (p.get("role") or "").split("\n")[1:]:
            m = JUDGE_LINE.match(line.strip())
            if m:
                names.add(m.group(1).strip())
    return sorted(names)


def judge_labels(role: str, names) -> dict:
    """`{judge name: 2|1|0}` from one passage's `role` text.

    Three levels — core 2, related 1, not relevant 0 — which the published
    `score` sums over the three judges. `verify_role_parse` checks that.
    """
    out = {}
    for line in (role or "").split("\n")[1:]:
        line = line.strip().lstrip("✓~✗x ").strip()
        for j in names:
            if line.startswith(j):
                tail = line[len(j):].strip(" —-").lower()
                out[j] = LABEL_VALUE.get(
                    "core" if "core" in tail else
                    "not relevant" if "not relevant" in tail else "", 1)
    return out


def verify_role_parse(behaviour, spec_key: str = DEFAULT_SPEC_KEY) -> dict:
    """Do the parsed labels sum to the published `score`, for every passage?

    A parser that does not reproduce `score` exactly is wrong, and would move
    the bar without anyone noticing. Returns the counts plus the offending
    passage ids so a failure names itself.
    """
    names = panel_judge_names(behaviour, spec_key)
    ok, mismatch = 0, []
    ps = passages(behaviour, spec_key)
    for p in ps:
        lab = judge_labels(p.get("role"), names)
        if sum(lab.values()) == p.get("score"):
            ok += 1
        else:
            mismatch.append({"id": p.get("id"), "score": p.get("score"),
                             "parsed": lab})
    return {"total": len(ps), "reconstructed": ok, "mismatch": mismatch,
            "judges": names}


def align_judges(behaviour) -> dict:
    """`{verdicts key: role display name}`.

    The panel file carries the same judgements twice — a structured `verdicts`
    map keyed `fable`/`kimi`/`sol` and the `role` free text naming
    `Claude Fable 5`/`Kimi-K3`/`GPT-5.6 Sol`. Aligning them lets each be used
    as a check on the other; `test_role_labels_agree_with_the_structured_
    verdicts_field` asserts they never disagree.
    """
    names = panel_judge_names(behaviour)
    out = {}
    for key in judges(behaviour):
        for n in names:
            if key.lower() in n.lower():
                out[key] = n
                break
    return out


def pair_targets(behaviour, threshold: int = 1,
                 spec_key: str = DEFAULT_SPEC_KEY) -> dict:
    """`{held-out judge: {others, gold, pred}}` — passage-id sets.

    `gold` is the intersection (BOTH others), never the union. The union is a
    much easier target and does NOT reproduce the quoted bar.
    """
    js = judges(behaviour, spec_key)
    sets = {j: judge_set(behaviour, j, threshold, spec_key) for j in js}
    out = {}
    for j in js:
        others = [o for o in js if o != j]
        gold = set.intersection(*[sets[o] for o in others]) if others else set()
        out[j] = {"others": others, "gold": gold, "pred": sets[j]}
    return out


def judge_loo(behaviour, threshold: int = 1, restrict: set | None = None,
              spec_key: str = DEFAULT_SPEC_KEY) -> dict:
    """Each judge scored against its own pair-gold. `restrict` confines both
    sides to a passage subset, so the judges can be re-scored on exactly the
    matched subset the tool is confined to."""
    out = {}
    for j, t in pair_targets(behaviour, threshold, spec_key).items():
        pred, gold = t["pred"], t["gold"]
        if restrict is not None:
            pred, gold = pred & restrict, gold & restrict
        m = prf(pred, gold)
        m["others"] = t["others"]
        m["n_gold"] = len(gold)
        out[j] = m
    return out


def mcc(predicted, gold, universe) -> float:
    """Matthews correlation coefficient — THE PRIMARY METRIC.

    F1 is unquotable on this task: it ignores true negatives, so at a 24-47%
    positive rate the degenerate all-relevant predictor scores 0.44-0.64 and on
    `avoiding-over-and-under-caution` a CONSTANT beats the best single judge.
    Every F1 therefore has to be read against a floor that moves per behaviour.

    MCC is 0 BY CONSTRUCTION for both degenerate predictors (all-positive gives
    tn = fn = 0; all-negative gives tp = fp = 0), so its floor is 0 everywhere
    and a number can be read directly. It is also sensitive to true negatives,
    which is deliberate: if the invisible-clause selection effect is ever fixed
    by adding real negatives back, MCC will refuse to keep looking good.
    """
    u = set(universe)
    p, g = set(predicted) & u, set(gold) & u
    tp = len(p & g)
    fp = len(p - g)
    fn = len(g - p)
    tn = len(u) - tp - fp - fn
    denom = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
    if denom <= 0:
        return 0.0
    return (tp * tn - fp * fn) / math.sqrt(denom)


def floor_mcc(gold, universe) -> float:
    """The all-relevant predictor's MCC. Exactly 0.0, always — stated as a
    function so the report can print it rather than assert it."""
    return mcc(set(universe), gold, universe)


def floor_f1(gold, universe) -> float:
    """F1 of the degenerate predictor that marks EVERY candidate relevant:
    precision falls to the base rate p, recall is 1, so F1 = 2p/(1+p).

    This is the true zero of the scale. A method that does not clearly clear it
    has learned nothing, however respectable its F1 looks next to 0.0.
    """
    u = set(universe)
    if not u:
        return 0.0
    p = len(set(gold) & u) / len(u)
    return 2 * p / (1 + p) if p else 0.0


# ================================================================
#  THRESHOLD-FREE COMPARISON: ROC / AUC and the judge's own operating point
# ================================================================
#
# Every MCC and F1 in this file is a number AT A THRESHOLD, and this project's
# threshold was selected on these same three behaviours. That makes the tool's
# headline a hindsight number and makes "the tool loses to the judge" easy to
# wave away as a mis-set operating point.
#
# The threshold-free statement is: a judge is a SINGLE (FPR, TPR) point; the
# tool is a CURVE. Comparing them at the judge's own FPR asks the only fair
# question — "held to the same false-positive rate the judge chose, does the
# tool recall as much?" — and no threshold choice can flatter either side.
# AUC summarises the whole curve alongside it.
#
# On the true 589-passage universe the judge wins 9/9 cells.

def binary_scale_judges(behaviour, spec_key: str = DEFAULT_SPEC_KEY) -> list:
    """Judges that never emit the middle verdict `1` (related).

    `kimi-k2` is one: it ran a BINARY 0/2 scale where the others ran a
    three-point one, so `>= 1 = relevant` is not the same decision rule for it.
    That is a real caveat about scale comparability, and it is DERIVED here
    rather than hardcoded — but it is NOT on its own a reason to exclude a
    cell: on the true universe kimi-k2's MCC is +0.552.
    """
    ps = passages(behaviour, spec_key)
    out = []
    for j in judges(behaviour, spec_key):
        used = {(p.get("verdicts") or {}).get(j) for p in ps}
        if 1 not in used and len(used - {None}) > 1:
            out.append(j)
    return out


def passage_scores(clause_scores: dict, joins: dict) -> dict:
    """`{passage id: score}` — the tool's continuous score, lifted to passages.

    A passage scores the MAX over the clauses joining to it (the same rule
    `lift` uses for the binary decision: any clause firing fires the passage).
    A passage that joins to nothing scores 0.0 and STAYS IN THE DENOMINATOR;
    dropping it would hand the tool a free AUC improvement.
    """
    return {pid: max([clause_scores.get(c, 0.0) for c in cids], default=0.0)
            for pid, cids in joins.items()}


def auc(scores: dict, gold, universe) -> float | None:
    """Area under the ROC curve, as the Mann-Whitney statistic.

    P(random positive scores above random negative), ties counted 0.5. Missing
    scores are 0.0, not omissions. Returns None when one class is empty — AUC
    is undefined there, and returning 0.5 would quietly invent a result.
    """
    u = set(universe)
    g = set(gold) & u
    pos = [scores.get(x, 0.0) for x in u if x in g]
    neg = [scores.get(x, 0.0) for x in u if x not in g]
    if not pos or not neg:
        return None
    neg_sorted = sorted(neg)
    total = 0.0
    from bisect import bisect_left, bisect_right
    for p in pos:
        lo = bisect_left(neg_sorted, p)
        hi = bisect_right(neg_sorted, p)
        total += lo + 0.5 * (hi - lo)
    return total / (len(pos) * len(neg))


def roc_points(scores: dict, gold, universe) -> list:
    """`[(fpr, tpr)]` for every distinct score cutoff, ascending in fpr.

    Includes both endpoints, so a curve is always plottable and
    `tpr_at_fpr(...,1.0)` is 1.0.
    """
    u = set(universe)
    g = set(gold) & u
    n_pos, n_neg = len(g), len(u) - len(g)
    if not n_pos or not n_neg:
        return []
    ranked = sorted(u, key=lambda x: -scores.get(x, 0.0))
    pts, tp, fp, i = [(0.0, 0.0)], 0, 0, 0
    while i < len(ranked):
        cut = scores.get(ranked[i], 0.0)
        while i < len(ranked) and scores.get(ranked[i], 0.0) == cut:
            if ranked[i] in g:
                tp += 1
            else:
                fp += 1
            i += 1
        pts.append((fp / n_neg, tp / n_pos))
    return pts


def tpr_at_fpr(scores: dict, gold, universe, target_fpr: float) -> float:
    """The best TPR the tool reaches WITHOUT exceeding `target_fpr`.

    This is the apples-to-apples number against a judge: hold the tool to the
    judge's own false-positive rate and ask what it recalls.
    """
    pts = roc_points(scores, gold, universe)
    return max((tpr for fpr, tpr in pts if fpr <= target_fpr + 1e-12),
               default=0.0)


def operating_point(predicted, gold, universe) -> tuple:
    """`(fpr, tpr)` of a BINARY predictor — a judge is exactly one of these."""
    u = set(universe)
    g, p = set(gold) & u, set(predicted) & u
    n_pos, n_neg = len(g), len(u) - len(g)
    return (len(p - g) / n_neg if n_neg else 0.0,
            len(p & g) / n_pos if n_pos else 0.0)


def roc_targets(behaviour, scores: dict, threshold: int = 1,
                spec_key: str = DEFAULT_SPEC_KEY,
                universe=None) -> dict:
    """`{held-out judge: roc cell}` — the threshold-free head-to-head.

    Each cell carries the tool's AUC over the whole universe, the judge's own
    (FPR, TPR), and the tool's TPR at that FPR. `judge_wins` is the comparison
    that matters and is precomputed so no reader has to eyeball two columns.
    """
    if universe is None:
        universe = set(scores) or {p["id"] for p in passages(behaviour, spec_key)}
    universe = set(universe)
    out = {}
    for j, t in pair_targets(behaviour, threshold, spec_key).items():
        gold = t["gold"] & universe
        jfpr, jtpr = operating_point(t["pred"], gold, universe)
        tool_tpr = tpr_at_fpr(scores, gold, universe, jfpr)
        out[j] = {
            "auc": auc(scores, gold, universe),
            "judge_fpr": jfpr, "judge_tpr": jtpr,
            "tool_tpr_at_judge_fpr": tool_tpr,
            "judge_wins": bool(jtpr > tool_tpr),
            "n_gold": len(gold), "n_universe": len(universe),
        }
    return out


def roc_block(results: dict) -> str:
    """Markdown for the threshold-free comparison. Reads `per_target[j]['roc']`."""
    lines = [
        "## Threshold-free — AUC, and the tool at each judge's own operating "
        "point", "",
        "A judge is ONE (FPR, TPR) point; the tool is a curve. Every MCC/F1 "
        "elsewhere in this report is a number at a threshold that was selected "
        "on these same behaviours. This table is not: it holds the tool to the "
        "judge's own false-positive rate and asks what it recalls there. "
        "`AUC` is the whole curve; `None` means one class was empty on that "
        "gold.", "",
        "| behaviour | vs judge | tool AUC | judge FPR | judge TPR | "
        "tool TPR @ judge FPR | winner |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |"]
    wins = [0, 0]
    for slug, ev in results.items():
        for j, r in sorted(ev["per_target"].items()):
            c = r.get("roc")
            if not c:
                continue
            wins[0 if c["judge_wins"] else 1] += 1
            a = "n/a" if c["auc"] is None else f"{c['auc']:.3f}"
            lines.append(
                f"| {slug} | {j} | {a} | {c['judge_fpr']:.3f} "
                f"| {c['judge_tpr']:.3f} | {c['tool_tpr_at_judge_fpr']:.3f} "
                f"| {'**judge**' if c['judge_wins'] else 'tool'} |")
    lines.append("")
    lines.append(f"**judge wins {wins[0]} / {wins[0] + wins[1]} cells at its own "
                 f"operating point.**")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------- the MCC band
#
# The LOBO point estimate is not reportable on its own. With n=3 behaviours the
# leave-one-behaviour-out 95% CI is [-0.055, +0.466] — it CONTAINS ZERO — and a
# defensible reimplementation of the same protocol moves the point by 0.02. A
# single number from that procedure is a coin flip dressed as a result.

MCC_BAND = (0.10, 0.40)     #: the sane threshold band; nothing outside it is quotable
LOBO_CI_N3 = (-0.055, 0.466)
SWEEP = tuple(round(0.02 * i, 2) for i in range(51))


def mcc_curve(behaviour, clause_scores: dict, clauses, joins: dict | None = None,
              thresholds=SWEEP, threshold: int = 1,
              spec_key: str = DEFAULT_SPEC_KEY) -> list:
    """`[(threshold, mean MCC over the pair-golds)]` — the WHOLE curve.

    Returned rather than reduced, because reducing it to its argmax is exactly
    how the quoted operating point was chosen in the first place.
    """
    if joins is None:
        joins = clause_joins(behaviour, clauses, spec_key)
    universe = set(joins)
    golds = [t["gold"] for t in
             pair_targets(behaviour, threshold, spec_key).values()]
    out = []
    for t in sorted(thresholds):
        pred = lift({c for c, s in clause_scores.items() if s > 0 and s >= t},
                    joins)
        vals = [mcc(pred, g, universe) for g in golds]
        out.append((t, sum(vals) / len(vals) if vals else 0.0))
    return out


def mcc_band(curve, lo: float = MCC_BAND[0], hi: float = MCC_BAND[1]) -> dict:
    """min / median / max over the sane threshold band — the reportable form."""
    import statistics
    vals = sorted(v for t, v in curve if lo <= t <= hi)
    if not vals:
        return {"min": 0.0, "median": 0.0, "max": 0.0, "n": 0, "lo": lo, "hi": hi}
    return {"min": vals[0], "max": vals[-1], "median": statistics.median(vals),
            "n": len(vals), "lo": lo, "hi": hi}


def mcc_band_block(curves: dict, lo: float = MCC_BAND[0],
                   hi: float = MCC_BAND[1]) -> str:
    """The band, then the full threshold-vs-MCC curve. Never a point estimate."""
    lines = [
        "## MCC as a BAND, not a point", "",
        f"The leave-one-behaviour-out (LOBO) **point estimate is not "
        f"reportable**: at "
        f"n=3 its 95% CI is [{LOBO_CI_N3[0]:+.3f}, {LOBO_CI_N3[1]:+.3f}] and "
        f"**contains zero**, and a defensible reimplementation of the same "
        f"protocol moves it by 0.02. What is reportable is the band over the "
        f"sane threshold range [{lo:.2f}, {hi:.2f}] plus the whole curve "
        f"below.", "",
        "| behaviour | band min | band median | band max | n thresholds |",
        "| --- | ---: | ---: | ---: | ---: |"]
    for slug, curve in curves.items():
        b = mcc_band(curve, lo, hi)
        lines.append(f"| {slug} | {b['min']:+.3f} | {b['median']:+.3f} "
                     f"| {b['max']:+.3f} | {b['n']} |")
    lines += ["", "**Full threshold curve** — every point, so no reader has to "
              "take the argmax on trust.", "",
              "| behaviour | threshold | mean MCC | in band |",
              "| --- | ---: | ---: | --- |"]
    for slug, curve in curves.items():
        for t, v in curve:
            lines.append(f"| {slug} | {t:.2f} | {v:+.3f} "
                         f"| {'yes' if lo <= t <= hi else ''} |")
    lines.append("")
    return "\n".join(lines)


# ------------------------------------------- THE LABEL-FREE OPERATING POINT
#
# The largest gap in this project, and it costs nothing to close. The scorer
# RANKS well and DECIDES badly:
#
#     shipped tool, held-out (LOBO) threshold   +0.206
#     shipped tool, ORACLE threshold            +0.387    <- unreachable
#
# Same scores, same ranking, different cut. `relevance.DEFAULT_THRESHOLD = 0.18`
# closes that gap only by being the in-sample argmax over the panel, which is
# fitting to the measuring instrument.
#
# `threshold.py` picks a cut from the SCORE DISTRIBUTION alone. Such a rule may
# legitimately be MEASURED here — the panel was never one of its inputs — and
# the reporting below exists to keep the calibration gap visible beside the
# number, so no future reader can quote the operating point on its own.
#
# THE SELECTION HAZARD THIS CODE GUARDS. Trying eleven rules and quoting the
# best is the same error as trying 51 thresholds and quoting the best, one
# level up. Two mechanical defences: `threshold.PREFERRED` is pre-registered in
# that module's docstring and is the only row this report may mark as the
# headline, and `operating_point_block` prints EVERY rule, losers included.

def mean_mcc_at(behaviour, clause_scores: dict, joins: dict, cut: float,
                threshold: int = 1, spec_key: str = DEFAULT_SPEC_KEY) -> float:
    """Mean MCC over the pair-golds at an ARBITRARY cut.

    `mcc_curve` evaluates the fixed 51-point grid; a label-free rule returns a
    continuous number, so it needs this. Deliberately the same three lines as
    the curve's body — if the two ever disagree, every rule is being scored on
    a different protocol from the LOBO and oracle rows it is compared against,
    and `test_mean_mcc_at_agrees_with_the_curve_at_a_grid_point` pins that.
    """
    universe = set(joins)
    pred = lift({c for c, s in clause_scores.items() if s > 0 and s >= cut},
                joins)
    golds = [t["gold"] for t in
             pair_targets(behaviour, threshold, spec_key).values()]
    vals = [mcc(pred, g, universe) for g in golds]
    return sum(vals) / len(vals) if vals else 0.0


def lobo_cuts(curves: dict) -> dict:
    """`{slug: cut}` chosen leave-one-BEHAVIOUR-out — the honest fitted point.

    The cut for behaviour `s` maximises the summed curve of the OTHER
    behaviours, so `s`'s own labels never touch its own cut. This is still a
    fitted parameter (it reads other behaviours' labels); it is the baseline a
    label-free rule has to beat, not a label-free rule itself.
    """
    slugs = sorted(curves)
    grid = sorted({t for c in curves.values() for t, _ in c})
    out = {}
    for s in slugs:
        others = [dict(curves[o]) for o in slugs if o != s]
        if not others:
            out[s] = max(dict(curves[s]).items(), key=lambda kv: (kv[1], -kv[0]))[0]
            continue
        out[s] = max(grid, key=lambda t: (sum(o.get(t, 0.0) for o in others), -t))
    return out


def oracle_cuts(curves: dict) -> dict:
    """`{slug: cut}` at each behaviour's OWN argmax — the unreachable ceiling.

    Reported only as the top of the calibration gap. Nothing may ship at it.
    """
    return {s: max(c, key=lambda tv: (tv[1], -tv[0]))[0] for s, c in curves.items()}


def label_free_cuts(rule: str, clause_scores: dict) -> dict:
    """`{slug: cut}` from `threshold.RULES[rule]`, per behaviour.

    Reads only the score vectors. No panel, no gold, no file.
    """
    import threshold
    return {slug: threshold.apply_rule(rule, sc)
            for slug, sc in clause_scores.items()}


def paired_bootstrap_cuts(a_cuts: dict, b_cuts: dict, behaviours: dict,
                          clause_scores: dict, joins: dict,
                          resamples: int = 2000, seed: int = 17,
                          threshold: int = 1,
                          spec_key: str = DEFAULT_SPEC_KEY) -> tuple:
    """`(mean delta, lo, hi)` for cut-set A minus cut-set B, resampling
    PASSAGES with replacement and holding the resample common to both — the
    same paired protocol the structural comparisons use.

    Paired because the two cut-sets score the identical passages: an unpaired
    interval would be dominated by between-passage variance that cancels.
    """
    import random
    rng = random.Random(seed)
    slugs = sorted(behaviours)

    def cats(cuts):
        out = {}
        for s in slugs:
            universe = sorted(joins[s])
            lifted = lift({c for c, v in clause_scores[s].items()
                           if v > 0 and v >= cuts[s]}, joins[s])
            out[s] = [[(p in lifted, p in t["gold"]) for p in universe]
                      for _, t in sorted(pair_targets(behaviours[s], threshold,
                                                      spec_key).items())]
        return out

    A, B = cats(a_cuts), cats(b_cuts)
    n = len(joins[slugs[0]])

    def mcc_of(pairs, idxs):
        tp = fp = fn = tn = 0
        for i in idxs:
            p, g = pairs[i]
            tp, fp, fn, tn = (tp + (p and g), fp + (p and not g),
                              fn + (g and not p), tn + (not p and not g))
        d = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
        return 0.0 if d <= 0 else (tp * tn - fp * fn) / math.sqrt(d)

    deltas = []
    for _ in range(resamples):
        idxs = [rng.randrange(n) for _ in range(n)]
        deltas.append(sum(
            sum(mcc_of(p, idxs) for p in A[s]) / max(1, len(A[s]))
            - sum(mcc_of(p, idxs) for p in B[s]) / max(1, len(B[s]))
            for s in slugs) / len(slugs))
    deltas.sort()
    if not deltas:
        return (0.0, 0.0, 0.0)
    return (sum(deltas) / len(deltas), deltas[int(0.025 * len(deltas))],
            deltas[int(0.975 * len(deltas)) - 1])


#: Deltas smaller than this are noise on this data (paired passage bootstrap
#: over 589 passages, 9 cells). Stated so a table of eleven rules cannot be
#: read as a ranking of eleven distinguishable methods.
OPERATING_POINT_NOISE = 0.045


def operating_point_block(behaviours: dict, clause_scores: dict, joins: dict,
                          clauses, extra_cuts: dict | None = None,
                          resamples: int = 2000, threshold: int = 1,
                          spec_key: str = DEFAULT_SPEC_KEY,
                          thresholds=SWEEP) -> str:
    """THE operating-point table: every label-free rule, LOBO, oracle, floors.

    `extra_cuts` is `{rule name: {slug: cut}}` for rules that need more than one
    score vector (the stability rule wants all five behaviour-atom draws) or a
    corpus statistic the caller owns (a prediction budget set to the number of
    clauses sharing any atom with the query). They are label-free by the call
    site's obligation; this function cannot check that, which is stated here
    rather than assumed.

    Emits every rule tried, winners AND losers, with a paired bootstrap CI
    against LOBO — because selecting the best rule on this table is exactly the
    error the pre-registration exists to prevent.
    """
    import threshold as T

    slugs = sorted(behaviours)
    curves = {s: mcc_curve(behaviours[s], clause_scores[s], clauses,
                           joins=joins[s], thresholds=thresholds,
                           threshold=threshold, spec_key=spec_key)
              for s in slugs}
    lobo = lobo_cuts(curves)
    oracle = oracle_cuts(curves)

    rows = [("LOBO (held out — 1 fitted param)", lobo, "reference"),
            ("ORACLE (in-sample, UNREACHABLE)", oracle, "reference")]
    rows.append((f"`{T.PREFERRED}` — PRE-REGISTERED PREFERRED",
                 label_free_cuts(T.PREFERRED, clause_scores), "preferred"))
    for name in sorted(T.RULES):
        if name == T.PREFERRED:
            continue
        rows.append((f"`{name}`", label_free_cuts(name, clause_scores),
                     "comparator"))
    for name, cuts in sorted((extra_cuts or {}).items()):
        rows.append((f"`{name}`", cuts, "comparator"))

    def mean_of(cuts):
        per = {s: mean_mcc_at(behaviours[s], clause_scores[s], joins[s],
                              cuts[s], threshold, spec_key) for s in slugs}
        return per, sum(per.values()) / len(per)

    lines = [
        "## The operating point — chosen WITHOUT labels", "",
        "The scorer ranks far better than it decides. Everything below is the "
        "SAME ranking cut in different places, so the spread in this table is "
        "pure calibration.", "",
        "A rule that reads only the score distribution may legitimately be "
        "MEASURED on the panel — the panel was never one of its inputs. That "
        "is measurement, not fitting. The two rows marked *reference* are NOT "
        "label-free and are printed only to bound the gap: **LOBO** reads the "
        "other behaviours' labels, **ORACLE** reads its own and is "
        "unreachable.", "",
        f"The preferred rule is pre-registered in `threshold.py` "
        f"(`threshold.PREFERRED = {T.PREFERRED!r}`) and was fixed BEFORE any "
        f"row below was computed. Every rule tried is printed, losers "
        f"included: quoting the best row of this table would be the same error "
        f"as quoting the best of 51 thresholds, one level up.", "",
        f"Deltas under ~{OPERATING_POINT_NOISE:.3f} are noise on this data.", "",
        "| rule | kind | " + " | ".join(f"cut {s}" for s in slugs)
        + " | " + " | ".join(slugs) + " | mean MCC | Δ vs LOBO (95% CI) |",
        "| --- | --- | " + " ".join("---: |" for _ in slugs) * 1
        + " ".join("---: |" for _ in slugs) + " ---: | --- |",
    ]
    for label, cuts, kind in rows:
        per, m = mean_of(cuts)
        if resamples and kind != "reference":
            d, lo, hi = paired_bootstrap_cuts(cuts, lobo, behaviours,
                                              clause_scores, joins, resamples,
                                              threshold=threshold,
                                              spec_key=spec_key)
            sig = "**significant**" if (lo > 0 or hi < 0) else "n.s."
            ci = f"{d:+.3f} [{lo:+.3f}, {hi:+.3f}] {sig}"
        elif kind == "reference" and label.startswith("LOBO"):
            ci = "—  (the baseline)"
        else:
            ci = "—"
        lines.append(
            f"| {label} | {kind} | "
            + " | ".join(f"{cuts[s]:.3f}" for s in slugs) + " | "
            + " | ".join(f"{per[s]:+.3f}" for s in slugs)
            + f" | {m:+.3f} | {ci} |")

    fa = 0.0
    fb = {}
    for s in slugs:
        reachable = joinable(joins[s])
        vals = [mcc(reachable, t["gold"], set(joins[s]))
                for t in pair_targets(behaviours[s], threshold, spec_key).values()]
        fb[s] = sum(vals) / len(vals) if vals else 0.0
    lines += [
        f"| **floor A** — chance (all-positive) | floor | "
        + " | ".join("—" for _ in slugs) + " | "
        + " | ".join(f"{fa:+.3f}" for _ in slugs) + f" | {fa:+.3f} | — |",
        f"| **floor B** — chance minus coverage gap | floor | "
        + " | ".join("—" for _ in slugs) + " | "
        + " | ".join(f"{fb[s]:+.3f}" for s in slugs)
        + f" | {sum(fb.values())/len(fb):+.3f} | — |",
        "",
        "**Floor A** is MCC's definitional zero: predict everything and "
        "`tn = fn = 0`, the denominator vanishes. **Floor B** is all-positive "
        "over what the tool can REACH — the passages joining to no clause are "
        "forced misses for any method whatsoever, and the gap between the two "
        "floors is the join-coverage cost this project states rather than "
        "absorbs.", "",
    ]
    md = "\n".join(lines)
    check_operating_point_pairing(md)
    return md


def check_operating_point_pairing(md: str) -> bool:
    """An operating point may never be stated without the calibration gap.

    Standing invariant, same machinery as `check_universe_pairing`. The whole
    reason to have a label-free rule is that the honest held-out number is
    +0.206 and the unreachable ceiling is +0.387; a document that prints the
    rule's score alone has deleted the only context that makes it meaningful,
    and has re-created the exact defect — a number quoted without its selection
    protocol — that this module keeps having to retract.
    """
    low = md.lower()
    if "operating point" not in low:
        return True
    for token, why in (("lobo", "the held-out baseline it must beat"),
                       ("oracle", "the ceiling it cannot reach"),
                       ("floor a", "MCC's definitional zero"),
                       ("floor b", "chance minus the coverage gap")):
        assert token in low, (
            f"an operating point was stated without {token.upper()} — "
            f"{why}. The number is meaningless alone.")
    return True


# ------------------------------------------------ clause -> passage lifting

#: Content-addressed memo for `clause_joins`. The join is a pure function of
#: (clause quotes, passage quotes) and costs ~7s over the 589-passage universe;
#: on the true universe all three behaviours share the SAME passage list, so
#: without this every report and every test pays for the identical work again.
#: Keyed on content, never on `id()` — a rebuilt clause list must not hit a
#: stale entry.
_JOIN_CACHE: dict = {}


def clause_joins(behaviour, clauses, spec_key: str = DEFAULT_SPEC_KEY) -> dict:
    """`{passage id: [clause id, ...]}` over the behaviour's FULL passage list.

    Not just the reference passages: the denominator is the panel's own, so
    every passage it judged has to be joined, including the ones it judged
    irrelevant.
    """
    ps = passages(behaviour, spec_key)
    # marked_span IS part of the join: inventory.match_passage matches on it
    # as well as on quote. Omitting it from the key meant a second call with a
    # different marked_span returned the FIRST call's answer. Latent while both
    # loaders force marked_span=None, live the moment focus-area rows are used
    # — and _JOIN_CACHE is module-global and never cleared.
    key = (hash(tuple((str(r.get("id")), r.get("quote", ""), r.get("marked_span"))
                      for r in clauses)),
           hash(tuple((p["id"], p.get("quote", "")) for p in ps)))
    hit = _JOIN_CACHE.get(key)
    if hit is not None:
        return dict(hit)
    out = {p["id"]: [r["id"] for r in
                     inventory.match_passage(p.get("quote", ""), clauses)]
           for p in ps}
    _JOIN_CACHE[key] = out
    return dict(out)


def joinable(joins: dict) -> set:
    return {pid for pid, cids in joins.items() if cids}


def lift(predicted_clause_ids, joins: dict) -> set:
    """A passage is predicted relevant iff at least one clause joining to it is.

    Passages with no clause at all can never appear here — that is the
    structural recall ceiling, and it is why `full` must always be reported.
    """
    pred = set(predicted_clause_ids)
    return {pid for pid, cids in joins.items() if pred.intersection(cids)}


def _join_strata(behaviour, joins, spec, spec_key=DEFAULT_SPEC_KEY) -> dict:
    strata = {k: 0 for k in STRATA}
    norm_spec = inventory._norm(spec) if spec else ""
    for p in passages(behaviour, spec_key):
        if joins.get(p["id"]):
            continue
        if p.get("exampleBlock"):
            strata["example_block"] += 1
        elif not norm_spec:
            strata["unknown"] += 1
        elif inventory._norm(p.get("quote", "")) not in norm_spec:
            strata["not_verbatim_in_source"] += 1
        else:
            strata["verbatim_but_unsegmented"] += 1
    return strata


# ---------------------------------------------------------------- evaluate

def evaluate(behaviour, predicted_clause_ids, clauses, spec: str | None = None,
             joins: dict | None = None, threshold: int = 1,
             spec_key: str = DEFAULT_SPEC_KEY, scores: dict | None = None) -> dict:
    """Score a clause prediction against all three pair-golds.

    Returns per-target rows carrying, side by side and never separately:
      matched / full      tool P, R, F1 on the joinable subset and on the whole
                          panel passage list;
      judge_matched/full  the held-out judge's F1 on the same two universes —
                          THE BAR;
      floor_matched/full  the degenerate all-relevant F1 — THE TRUE ZERO.
    """
    if spec is None:
        spec = spec_text()
    if joins is None:
        joins = clause_joins(behaviour, clauses, spec_key)
    universe = set(joins)
    matched = joinable(joins)
    tool = lift(predicted_clause_ids, joins)

    per_target = {}
    for j, t in pair_targets(behaviour, threshold, spec_key).items():
        gold, jpred = t["gold"], t["pred"]
        f_full = floor_f1(gold, universe)
        b_full = prf(jpred, gold)["f1"]
        per_target[j] = {
            "others": t["others"],
            "n_full": len(universe), "n_matched": len(matched),
            "gold_full": len(gold), "gold_matched": len(gold & matched),
            "matched": prf(tool & matched, gold & matched),
            "full": prf(tool, gold),
            "judge_matched": prf(jpred & matched, gold & matched),
            "judge_full": prf(jpred, gold),
            "floor_matched": floor_f1(gold, matched),
            "floor_full": f_full,
            # --- MCC: primary. Floor is 0 by construction on every target.
            "mcc_full": mcc(tool, gold, universe),
            "mcc_matched": mcc(tool & matched, gold & matched, matched),
            "judge_mcc_full": mcc(jpred, gold, universe),
            "judge_mcc_matched": mcc(jpred & matched, gold & matched, matched),
            "floor_mcc_full": floor_mcc(gold, universe),
            # --- lift over floor: the only honest way to quote an F1 here
            "lift_full": prf(tool, gold)["f1"] - f_full,
            "judge_lift_full": b_full - f_full,
            # A target where a CONSTANT outscores the judge cannot host a
            # headline: "beats the bar" is achievable by predicting everything.
            "headline_usable": b_full > f_full,
        }

    # Threshold-free companion to every thresholded number above. Optional only
    # because a caller may have no continuous score (e.g. a hand-written
    # prediction set); when it is supplied the ROC cell is never omitted.
    if scores is not None:
        for j, cell in roc_targets(behaviour, scores, threshold, spec_key,
                                   universe).items():
            per_target[j]["roc"] = cell

    def mean(f):
        vals = [f(r) for r in per_target.values()]
        return sum(vals) / len(vals) if vals else 0.0

    best_judge = max(per_target.values(), key=lambda r: r["judge_full"]["f1"],
                     default=None)
    # SELECTION EFFECT. The panel list holds only passages >=1 judge flagged, so
    # clauses joining to nothing are unscored: the tool may fire on them at zero
    # precision cost, while no judge gains anything (F1 ignores true negatives).
    # Both counts are returned AND surfaced in the report, because returning
    # them was never enough to make anyone look.
    pred_clauses = set(predicted_clause_ids)
    liftable = {c for cids in joins.values() for c in cids}
    unliftable = pred_clauses - liftable
    return {
        "behaviour": behaviour.get("slug"),
        "n_predicted_clauses": len(pred_clauses),
        "n_predicted_passages": len(tool),
        "n_clauses_visible": len(liftable),
        "n_predicted_unliftable": len(unliftable),
        "unliftable_frac": (len(unliftable) / len(pred_clauses)
                            if pred_clauses else 0.0),
        # A behaviour can host a headline iff THE TARGET THAT SUPPLIES THE
        # QUOTED BAR beats its own floor. Keying on `all` would condemn
        # helpfulness for `sol` (F1 0.385 vs floor 0.389) — a true statement
        # about a degenerate judge, but not a reason to suppress a behaviour
        # whose bar comes from `kimi` at 0.764 against a floor of 0.461.
        "headline_usable": (best_judge["judge_full"]["f1"] > best_judge["floor_full"]
                            if best_judge else False),
        "bar_target": (max(per_target, key=lambda j: per_target[j]["judge_full"]["f1"])
                       if per_target else None),
        "unusable_targets": [j for j, r in per_target.items()
                             if not r["headline_usable"]],
        # Derived, not narrated: a judge that never emits the middle verdict
        # ran a different scale. Surfaced as a caveat wherever it applies, and
        # NOT used to suppress a cell (see `binary_scale_judges`).
        "binary_scale_judges": binary_scale_judges(behaviour, spec_key),
        "n_passages": len(universe),
        "per_target": per_target,
        "tool_mean_matched": mean(lambda r: r["matched"]["f1"]),
        "tool_mean_full": mean(lambda r: r["full"]["f1"]),
        "judge_mean_matched": mean(lambda r: r["judge_matched"]["f1"]),
        "judge_mean_full": mean(lambda r: r["judge_full"]["f1"]),
        "judge_best_full": best_judge["judge_full"]["f1"] if best_judge else 0.0,
        "judge_best_matched": max(
            (r["judge_matched"]["f1"] for r in per_target.values()), default=0.0),
        "tool_mcc_mean_full": mean(lambda r: r["mcc_full"]),
        "tool_mcc_mean_matched": mean(lambda r: r["mcc_matched"]),
        "judge_mcc_mean_full": mean(lambda r: r["judge_mcc_full"]),
        "judge_mcc_best_full": max(
            (r["judge_mcc_full"] for r in per_target.values()), default=0.0),
        "tool_lift_mean_full": mean(lambda r: r["lift_full"]),
        "judge_lift_mean_full": mean(lambda r: r["judge_lift_full"]),
        "floor_mean": mean(lambda r: r["floor_full"]),
        "floor_mean_matched": mean(lambda r: r["floor_matched"]),
        "join": {
            "n_passages": len(universe),
            "n_joinable": len(matched),
            "n_unjoinable": len(universe) - len(matched),
            "strata": _join_strata(behaviour, joins, spec, spec_key),
        },
    }


# --------------------------------------------------------------- report (5)

def _pct(x) -> str:
    return f"{x:.3f}"


def _flag(tool: float, bar: float, floor: float) -> str:
    if tool < floor:
        return "BELOW FLOOR"
    if tool < floor * 1.1:
        return "~ floor"
    return "BEATS BAR" if tool >= bar else "below bar"


def head_to_head_table(results: dict) -> str:
    """THE comparison. One row per gold, tool and judge on the identical gold.

    The old headline compared a MEAN-OF-THREE (tool, scored on all three golds)
    against a MAX-OF-ONE (each judge is scored on exactly the one gold that
    excludes it). Those are not commensurable, and the gap is large: the best
    judge's own predictions score 0.871 / 0.884 / 0.833 under the tool's
    mean-of-three protocol versus the 0.764 / 0.780 / 0.500 it is quoted at.
    The three golds also differ wildly in difficulty (over/under-caution floors
    run 0.271 / 0.640 / 0.271), so averaging over them hides which one is doing
    the work.

    So: three like-for-like head-to-heads per behaviour. Tool vs the held-out
    judge, same gold, same universe, MCC first.
    """
    lines = ["## Head-to-head — tool vs judge, one row per gold", "",
             "Each row is a single gold set: the held-out judge and the tool "
             "predict the SAME passages against the SAME target. **MCC is "
             "primary** (its floor is 0 for any degenerate predictor); F1 is "
             "shown with the floor it must be read against.", "",
             "| behaviour | gold = consensus of | vs judge | tool MCC | judge "
             "MCC | tool F1 | judge F1 | F1 FLOOR | tool lift | judge lift | "
             "usable |",
             "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
    for slug, ev in results.items():
        for j, r in sorted(ev["per_target"].items()):
            lines.append(
                f"| {slug} | {'+'.join(r['others'])} | {j} "
                f"| **{r['mcc_full']:+.3f}** | {r['judge_mcc_full']:+.3f} "
                f"| {_pct(r['full']['f1'])} | {_pct(r['judge_full']['f1'])} "
                f"| {_pct(r['floor_full'])} | {r['lift_full']:+.3f} "
                f"| {r['judge_lift_full']:+.3f} "
                f"| {'yes' if r['headline_usable'] else '**NO**'} |")
    lines.append("")
    return "\n".join(lines)


def headline_table(results: dict) -> str:
    """The one table to read. MCC primary, F1 only ever beside its floor.

    A behaviour whose bar sits BELOW its own floor is marked UNUSABLE FOR
    HEADLINE and refuses to contribute a verdict: on such a target "beats the
    bar" is achievable by a constant, so the comparison carries no information
    whatever the tool scores.
    """
    lines = [
        "## Headline — tool vs the panel, on the panel's own passage denominator",
        "",
        "Gold = both other judges rated the passage relevant (core or related). "
        "**MCC is the primary metric**: it is 0 by construction for both "
        "degenerate predictors, so it can be read without a floor. F1 is "
        "secondary and NEVER appears without its FLOOR (= 2p/(1+p), the "
        "all-relevant predictor) on the same line. The judge aggregate quoted "
        "is the MEAN LOO, not the best single judge — it is the only judge "
        "aggregate computed over the same three golds the tool is scored on.",
        "",
        "| behaviour | scope | **tool MCC** | judge MCC (mean) | tool F1 | "
        "F1 FLOOR | tool lift | judge F1 (mean LOO) | judge lift | verdict |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for slug, ev in results.items():
        for scope in ("matched", "full"):
            rows = list(ev["per_target"].values())
            n = max(1, len(rows))
            f1 = ev[f"tool_mean_{scope}"]
            floor = (ev["floor_mean_matched"] if scope == "matched"
                     else ev["floor_mean"])
            tool_mcc = ev[f"tool_mcc_mean_{'matched' if scope == 'matched' else 'full'}"]
            judge_mcc = (sum(r[f"judge_mcc_{scope}"] for r in rows) / n)
            judge_f1 = ev[f"judge_mean_{scope}"]
            verdict = ("**UNUSABLE FOR HEADLINE**" if not ev["headline_usable"]
                       else _flag(f1, judge_f1, floor))
            lines.append(
                f"| {slug} | {scope} | **{tool_mcc:+.3f}** | {judge_mcc:+.3f} "
                f"| {_pct(f1)} | {_pct(floor)} | {f1 - floor:+.3f} "
                f"| {_pct(judge_f1)} | {ev['judge_lift_mean_full']:+.3f} "
                f"| {verdict} |")
    lines.append("")

    unusable = {s: ev for s, ev in results.items() if not ev["headline_usable"]}
    if unusable:
        lines.append("> **REFUSED — these behaviours must not carry a headline "
                     "number.** On the targets listed the F1 floor exceeds the "
                     "judge bar, so a constant predictor outscores the judge "
                     "the tool is being compared to.")
        lines.append(">")
        for slug, ev in unusable.items():
            bad = ", ".join(ev["unusable_targets"])
            note = ""
            binary = [j for j in ev.get("binary_scale_judges") or []
                      if j in ev["unusable_targets"]]
            if binary:
                note = (f" Contributing: {', '.join(binary)} never emits "
                        f"`related`, so it ran a BINARY scale while the others "
                        f"ran a three-point one and `>=1 = relevant` is not the "
                        f"same decision rule for it. That is a scale caveat, "
                        f"not by itself a reason to refuse — the refusal here "
                        f"is the floor-over-bar check above.")
            lines.append(
                f"> - `{slug}`: gold(s) held out from {bad}, on a universe of "
                f"{ev.get('n_passages')} passages.{note}")
        lines.append("")
        lines.append("> If this fired on a universe smaller than the one the "
                     "judges actually graded, CHECK THE UNIVERSE FIRST: on the "
                     "published (score-0-deleted) universe the base rate is "
                     "inflated 3-5x and the F1 floor with it, which is what "
                     "produced the historical refusal of "
                     "`avoiding-over-and-under-caution`.")
        lines.append("")

    lines.append(SELECTION_CAVEAT)
    lines.append("")
    lines.append("| behaviour | predicted clauses | of which unscored | "
                 "clauses visible to the panel | passages predicted | "
                 "passages judged | joinable | unjoinable |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for slug, ev in results.items():
        j = ev["join"]
        lines.append(
            f"| {slug} | {ev['n_predicted_clauses']} "
            f"| {ev['n_predicted_unliftable']} ({ev['unliftable_frac']:.0%}) "
            f"| {ev['n_clauses_visible']} | {ev['n_predicted_passages']} "
            f"| {j['n_passages']} | {j['n_joinable']} | {j['n_unjoinable']} |")
    lines.append("")
    return "\n".join(lines)


def per_target_table(slug: str, ev: dict) -> str:
    lines = [f"### {slug} — per pair-gold (tool and judge on identical gold)",
             "",
             "| held-out judge | gold (full/matched) | tool F1 full | "
             "tool F1 matched | judge F1 full | judge F1 matched | FLOOR full |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for j, r in sorted(ev["per_target"].items()):
        lines.append(
            f"| {j} (vs {'+'.join(r['others'])}) "
            f"| {r['gold_full']}/{r['gold_matched']} "
            f"| {_pct(r['full']['f1'])} | {_pct(r['matched']['f1'])} "
            f"| {_pct(r['judge_full']['f1'])} | {_pct(r['judge_matched']['f1'])} "
            f"| {_pct(r['floor_full'])} |")
    lines.append("")
    return "\n".join(lines)


SELECTION_CAVEAT = (
    "> **Selection effect — only on the PUBLISHED universe.** The published "
    "panel file holds only passages at least one judge flagged (score 0 was "
    "deleted by `build_site_data.keeps_citation`), so on that universe the "
    "candidate pool is pre-filtered: a predicted clause joining to no listed "
    "passage is simply unscored, and the tool may fire on it at ZERO precision "
    "cost while no judge gains anything. Measured inflation for the "
    "all-relevant predictor, published set versus whole spec: +0.147 / +0.228 "
    "/ +0.429. On the TRUE universe (589 passages, 582 joinable) the shield is "
    "gone — every passage the judges graded is scored — and the `unscored` "
    "column below is the residue of the clause join alone."
)

CAVEATS = """**Read these before any number below.**

1. **THE UNIVERSE.** The panel graded EVERY passage of the spec in one prompt:
   589 for the model spec, 374 for the constitution. The published
   `behaviours.json` holds 377 / 333 / 153 of those 589, because
   `build_site_data.keeps_citation` dropped every passage whose summed score
   was 0 — 212 / 256 / 436 true negatives, gold-negative by construction AND
   correctly predicted negative by every judge. Deleting them removes credit
   the judges earned: restoring them is worth +0.046 mean MCC to the tool and
   **+0.161 to the judges**, widening the gap 0.120 -> 0.235. Every headline
   here is computed on the TRUE universe, with the published number printed
   beside it. It also voids the old defence of MCC on this project ("MCC is
   sensitive to true negatives, so it is robust here") as applied to published
   numbers: the true negatives had been deleted upstream.
2. **FLOOR, not 0.0, is the true zero.** Marking everything relevant scores
   2p/(1+p). On at least one target here that floor is ABOVE the best single
   judge, so "beats the bar" can be achieved by a predictor that has learned
   nothing. Both columns are printed for exactly this reason.
3. **Matched subset vs full reference.** Passages that join to no clause can
   never be predicted and are automatic misses on the full reference. The
   matched-subset number is never quoted alone; `check_report_pairing` enforces
   that mechanically on this document.
4. Judge verdicts are read from the structured `verdicts` field (0/1/2), whose
   sum reproduces the published `score` for all 863 published passages; the
   restored passages carry 0 from every judge by construction. The `role` free
   text is parsed only as a cross-check and nothing is scored off it.
5. **THE OPERATING POINT WAS FIT ON THIS PANEL.** `relevance.DEFAULT_THRESHOLD`
   is the argmax of a 51-point grid selected on the same three behaviours
   scored below, so every thresholded number here is a HINDSIGHT-THRESHOLD
   number and the in-sample mean MCC (+0.274 published / +0.320 true) is a
   CEILING, not a result. The leave-one-behaviour-out POINT ESTIMATE is not
   reportable: at n=3 its 95% CI is [-0.055, +0.466] and contains zero, and a
   defensible reimplementation of the same protocol moves it by 0.02. Read the
   BAND (min/median/max over the sane threshold range) and the full curve, both
   printed above, and the threshold-free ROC table, which no threshold choice
   can flatter.
6. **The `section_path` fix did not recover the method.** Best MCC *over the
   sweep* moved only +0.2637 → +0.2743 (Δ +0.011); the defect was a
   CALIBRATION bug that moved where the good threshold sits (0.36 → 0.18), not
   a signal bug. Like-for-like, pre-fix LOBO +0.1635 -> post-fix +0.1867 (delta +0.023).
   +0.1876 is NOT a pre-fix number: it is this scorer at the OLD threshold.
   The real pre-fix default was +0.1526. Do not narrate that fix as a recovery.
   ALL SIX of those figures are published-universe LOBO POINT estimates and
   are retained only as a record of that episode — none of them is reportable
   as a result (see 5), and none was recomputed on the true universe."""


def delta_table(true_results: dict, published_results: dict) -> str:
    """Both universes and the delta, on one line per behaviour.

    Never one alone. The published number is not a result and the true number
    is not a correction anyone should have to take on trust — the reader gets
    both and the size of the move.
    """
    lines = [
        "## Universe delta — TRUE universe vs published universe", "",
        "The published file deleted every passage all judges scored 0. Those "
        "are true negatives both sides earned; deleting them cost the judges "
        "far more than the tool, so the published numbers understate the gap. "
        "`delta` is TRUE minus published.", "",
        "| behaviour | n passages (true / published) | tool MCC true | "
        "tool MCC published | tool delta | judge MCC true | "
        "judge MCC published | judge delta | gap true | gap published |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    tots = {"t_true": [], "t_pub": [], "j_true": [], "j_pub": []}
    for slug, ev in true_results.items():
        pv = published_results.get(slug)
        if pv is None:
            continue
        tt, tp = ev["tool_mcc_mean_full"], pv["tool_mcc_mean_full"]
        jt, jp = ev["judge_mcc_mean_full"], pv["judge_mcc_mean_full"]
        for k, v in (("t_true", tt), ("t_pub", tp), ("j_true", jt), ("j_pub", jp)):
            tots[k].append(v)
        lines.append(
            f"| {slug} | {ev['join']['n_passages']} / {pv['join']['n_passages']} "
            f"| **{tt:+.3f}** | {tp:+.3f} | {tt - tp:+.3f} "
            f"| **{jt:+.3f}** | {jp:+.3f} | {jt - jp:+.3f} "
            f"| {jt - tt:+.3f} | {jp - tp:+.3f} |")
    if tots["t_true"]:
        n = len(tots["t_true"])
        m = {k: sum(v) / n for k, v in tots.items()}
        lines.append(
            f"| **mean** | | **{m['t_true']:+.3f}** | {m['t_pub']:+.3f} "
            f"| {m['t_true'] - m['t_pub']:+.3f} | **{m['j_true']:+.3f}** "
            f"| {m['j_pub']:+.3f} | {m['j_true'] - m['j_pub']:+.3f} "
            f"| {m['j_true'] - m['t_true']:+.3f} "
            f"| {m['j_pub'] - m['t_pub']:+.3f} |")
    lines.append("")
    return "\n".join(lines)


def check_universe_pairing(md: str) -> bool:
    """A headline may never be quoted on one universe alone.

    Same standing-invariant machinery as `check_report_pairing`, for the defect
    that motivated this module: for two months this project quoted
    published-universe numbers as results with no indication that 36-74% of the
    judged passages had been deleted before the file was written.
    """
    low = md.lower()
    if "headline" not in low and "tool mcc" not in low:
        return True
    assert "true universe" in low, (
        "a headline was emitted without naming the TRUE universe it must be "
        "computed on")
    assert "published universe" in low, (
        "a headline was emitted without its published-universe counterpart — "
        "both numbers and their delta, always")
    assert "delta" in low, "both universes are printed but the delta is not stated"
    return True


def dual_report(predictions=None, clauses=None, behaviours=None,
                published_behaviours=None, spec: str | None = None,
                scores=None, clause_source: str = "",
                curves: dict | None = None, provenance: dict | None = None) -> str:
    """THE report. TRUE universe first, published beside it, delta stated.

    `scores` is `{slug: {passage id: continuous tool score}}` and unlocks the
    threshold-free ROC block; `curves` is `{slug: [(threshold, mean MCC)]}` and
    unlocks the band block. Both are optional and both are printed when given —
    there is no mode of this function that emits a single-universe headline.
    """
    import panel_universe

    if clauses is None:
        clauses, clause_source = load_clauses()
    if spec is None:
        spec = spec_text()
    prov = provenance or {}
    if behaviours is None or published_behaviours is None:
        true_panel, loaded_prov = load_true_panel(with_provenance=True)
        behaviours = behaviours or true_panel
        published_behaviours = published_behaviours or load_panel()
        prov = prov or loaded_prov
    predictions = predictions or {}

    slugs = [s for s in behaviours if s in predictions]
    true_ev = {s: evaluate(behaviours[s], predictions[s], clauses, spec,
                           scores=(scores or {}).get(s))
               for s in slugs}
    pub_ev = {s: evaluate(published_behaviours[s], predictions[s], clauses, spec)
              for s in slugs if s in published_behaviours}

    out = ["# Behavioural-relevance benchmark", "",
           f"clause set: `{clause_source or 'provided'}` ({len(clauses)} clauses)",
           "",
           f"Headline universe: **{UNIVERSE_LABEL['true']}**. Every number is "
           f"printed beside its **{UNIVERSE_LABEL['published']}** counterpart "
           f"and the delta.", ""]
    if prov:
        out.append(panel_universe.provenance_block(prov))
    out.append(CAVEATS)
    out.append("")
    if true_ev:
        out.append(delta_table(true_ev, pub_ev))
        out.append("### TRUE universe — the headline")
        out.append("")
        out.append(headline_table(true_ev))
        out.append(head_to_head_table(true_ev))
        out.append("### published universe — the same tables on the broken "
                   "denominator, for comparison ONLY")
        out.append("")
        out.append(headline_table(pub_ev))
        if scores:
            out.append(roc_block(true_ev))
    if curves:
        out.append(mcc_band_block(curves))
    md = "\n".join(out)
    check_report_pairing(md)
    check_universe_pairing(md)
    return md


def check_report_pairing(md: str) -> bool:
    """A matched-subset number may never appear without its full-reference
    counterpart.

    Standing project invariant: an earlier iteration nearly published a
    matched-subset F1 as if it were the real number. This is the mechanical
    guard, and `report()` runs it on its own output before returning.
    """
    lines = md.split("\n")
    has_matched = any("matched" in l.lower() for l in lines)
    has_full = any(re.search(r"\bfull\b", l.lower()) for l in lines)
    assert not has_matched or has_full, (
        "report names a matched subset but never the full reference — "
        "the matched-subset number must never stand alone")
    for l in lines:
        low = l.lower()
        if low.lstrip().startswith("|") and "matched" in low and "---" not in low:
            assert "full" in low or has_full, f"unpaired matched row: {l}"
    return True


def _agreement_block(slug, agreement) -> list:
    lines = [f"### {slug} — panel self-agreement (THE BAR)", ""]
    lines.append(f"judges: `{'`, `'.join(agreement['judges'])}`  "
                 f"({agreement['n_passages']} passages scored)")
    lines.append("")
    lines.append("| threshold | pair | Jaccard |")
    lines.append("| --- | --- | ---: |")
    for t in THRESHOLDS:
        label = ">=1 (any)" if t == 1 else "==2 (max)"
        for pair, j in sorted(agreement["pairwise"][t].items()):
            lines.append(f"| {label} | {pair} | {_pct(j)} |")
    lines.append("")
    lines.append("**Leave-one-out — one judge vs the other two's consensus. "
                 "This is what 'just ask one frontier model' gets you; the tool "
                 "must beat this, not the committee.**")
    lines.append("")
    lines.append("| threshold | judge | vs consensus of | J | P | R | F1 | n(judge) | n(consensus) |")
    lines.append("| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for t in THRESHOLDS:
        label = ">=1" if t == 1 else "==2"
        for j, m in sorted(agreement["leave_one_out"][t].items()):
            lines.append(
                f"| {label} | {j} | {'+'.join(m['others'])} | {_pct(m['jaccard'])} "
                f"| {_pct(m['precision'])} | {_pct(m['recall'])} | {_pct(m['f1'])} "
                f"| {m['n_judge']} | {m['n_consensus']} |")
        lines.append(f"| {label} | **mean F1** | | | | | **{_pct(loo_mean(agreement, t))}** | | |")
    lines.append("")
    return lines


def _zero_match_block(mappings) -> list:
    lines = ["**Zero-match accounting** — reference passages that map to no "
             "clause at all. Neither hit nor miss; never dropped from a "
             "denominator.", ""]
    lines.append("| min_score | reference | matched | unmatched | example_block | not_verbatim_in_source | verbatim_but_unsegmented | unknown |")
    lines.append("| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for m in mappings:
        s = m["strata"]
        lines.append(
            f"| >={m['min_score']} | {m['n_reference']} | {m['n_matched']} "
            f"| {len(m['unmatched'])} | {s['example_block']} "
            f"| {s['not_verbatim_in_source']} | {s['verbatim_but_unsegmented']} "
            f"| {s['unknown']} |")
    lines.append("")
    return lines


def _score_block(results) -> list:
    lines = ["**Tool score** — matched subset vs full reference set. The gap is "
             "the coverage cost.", ""]
    lines.append("| min_score | scope | tp | fp | fn | P | R | F1 |")
    lines.append("| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for r in results:
        for scope in ("matched", "full"):
            m = r[scope]
            lines.append(
                f"| >={r['min_score']} | {scope} | {m['tp']} | {m['fp']} "
                f"| {m['fn']} | {_pct(m['precision'])} | {_pct(m['recall'])} "
                f"| {_pct(m['f1'])} |")
    for r in results:
        p = r["passage_level"]
        lines.append(
            f"| >={r['min_score']} | passage-level | {p['hit']} | | "
            f"| | {_pct(p['recall_matched'])} (matched) / "
            f"{_pct(p['recall_full'])} (full) | |")
    lines.append("")
    return lines


def report(behaviours=None, clauses=None, predictions=None,
           min_scores=None, clause_source: str = "", spec: str | None = None) -> str:
    """Markdown report.

    `behaviours`  {slug: behaviour} (default: the whole panel file).
    `predictions` {slug: set(clause ids)} — optional; without it the report is
                  the bar plus the zero-match ledger, which is exactly the
                  useful output before a tool exists.
    `min_scores`  defaults to (5, strict) per behaviour, so threshold
                  sensitivity is always visible.
    """
    if behaviours is None:
        behaviours = load_panel()
    if clauses is None:
        clauses, clause_source = load_clauses()
    if spec is None:
        spec = spec_text()
    predictions = predictions or {}

    out = ["# Behavioural-relevance benchmark", ""]
    out.append(f"clause set: `{clause_source or 'provided'}` ({len(clauses)} clauses)")
    out.append("")
    out.append("The tool has to beat the **leave-one-out** row, not the "
               "3-judge consensus. Every score is printed over the matched "
               "subset AND the full reference set; the zero-match block below "
               "each score bounds what the numbers can mean.")
    out.append("")
    out.append(CAVEATS)
    out.append("")

    if predictions:
        evals = {slug: evaluate(b, predictions[slug], clauses, spec)
                 for slug, b in behaviours.items() if slug in predictions}
        if evals:
            out.append(headline_table(evals))
            out.append(head_to_head_table(evals))
            for slug, ev in evals.items():
                out.append(per_target_table(slug, ev))

    for slug, b in behaviours.items():
        thresholds = min_scores or (DEFAULT_MIN_SCORE, max_score(b))
        thresholds = sorted(set(thresholds))
        out += _agreement_block(slug, panel_agreement(b))

        mappings = [map_reference(b, clauses, t, spec) for t in thresholds]
        results = []
        if slug in predictions:
            results = [score_tool(predictions[slug], b, clauses, t, spec, mapping=m)
                       for t, m in zip(thresholds, mappings)]
            out += _score_block(results)
        else:
            out.append("_no tool prediction supplied for this behaviour._")
            out.append("")
        out += _zero_match_block(mappings)
        out.append("---")
        out.append("")
    md = "\n".join(out)
    check_report_pairing(md)   # the guard runs on our own output, not just in tests
    return md


def sweep_report(behaviours, clauses, sweeps: dict, spec: str | None = None,
                 label: str = "tool") -> str:
    """The whole threshold curve, per behaviour.

    A single hand-picked operating point is not a result: it is the best of N
    tries on the test set. The curve is printed so the reader can see how the
    headline moves, and where on it the quoted threshold sits.
    """
    if spec is None:
        spec = spec_text()
    lines = [f"## Threshold sweep — `{label}`", "",
             "Every row is a threshold, not a result. The quoted operating "
             "point is one line of this table and is marked; a number taken "
             "from the best line without the rest of the column is a "
             "test-set-selected maximum.", "",
             "| behaviour | threshold | n clauses | n passages | P full | "
             "R full | F1 full | F1 matched | FLOOR full | bar |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for slug, b in behaviours.items():
        if slug not in sweeps:
            continue
        joins = clause_joins(b, clauses)
        for t, pred in sweeps[slug]:
            ev = evaluate(b, pred, clauses, spec, joins=joins)
            rows = ev["per_target"].values()
            n = max(1, len(rows))
            p = sum(r["full"]["precision"] for r in rows) / n
            rc = sum(r["full"]["recall"] for r in rows) / n
            lines.append(
                f"| {slug} | {t:.2f} | {len(pred)} | {ev['n_predicted_passages']} "
                f"| {_pct(p)} | {_pct(rc)} | {_pct(ev['tool_mean_full'])} "
                f"| {_pct(ev['tool_mean_matched'])} | {_pct(ev['floor_mean'])} "
                f"| {_pct(ev['judge_best_full'])} |")
    lines.append("")
    return "\n".join(lines)


def ablate(behaviours, clauses, queries, base_weights, annotations=None,
           spec: str | None = None) -> str:
    """Per-channel ablation: which signal is actually doing the work?

    With the atom channel inert, section-prior + Rocchio expansion are the only
    non-trivial signals, and a headline attributed to "the ontology" would in
    fact be a section prior. Each row switches ONE channel off and reports the
    change in mean F1, so the attribution is measured rather than assumed.
    """
    import relevance

    if spec is None:
        spec = spec_text()
    variants = [
        ("full", base_weights),
        ("-lex", relevance.replace_weights(base_weights, lex=0.0)),
        ("-atom", relevance.replace_weights(base_weights, atom=0.0)),
        ("-kind", relevance.replace_weights(base_weights, kind=0.0)),
        ("-section", relevance.replace_weights(base_weights, section=0.0)),
        ("-expansion", relevance.replace_weights(base_weights,
                                                 expansion_terms=0,
                                                 expansion_docs=0)),
        ("lex only", relevance.replace_weights(
            base_weights, atom=0.0, kind=0.0, section=0.0,
            expansion_terms=0, expansion_docs=0)),
    ]
    joins = {slug: clause_joins(b, clauses) for slug, b in behaviours.items()}

    # The FLOOR row is not decoration. Every cell below is a max over 51
    # thresholds, and the all-relevant point is inside that sweep — so
    # "best-F1 > floor" is true BY CONSTRUCTION and can never come out
    # negative. Without the floor printed on the same table, every row looks
    # like a result. Read each cell as its distance from this row.
    floors = {}
    for slug, b in behaviours.items():
        ev = evaluate(b, set(c["id"] for c in clauses), clauses, spec,
                      joins=joins[slug])
        floors[slug] = ev["tool_mcc_mean_full"]

    lines = ["## Channel ablation (each row switches ONE channel off)", "",
             "Best **MCC** over the whole threshold sweep, per behaviour. A "
             "channel whose removal costs nothing is not contributing, whatever "
             "weight it carries. Ranked on MCC rather than F1 because the "
             "all-relevant point sits inside the sweep and scores 0.44-0.59 on "
             "F1 — ranking channels on F1 rewards rescaling the score "
             "distribution rather than adding discrimination.", "",
             "**Every cell is a hindsight maximum over 51 thresholds. Read "
             "distance from the FLOOR row, not the absolute number. "
             "Differences of a few thousandths are noise: a gap this table "
             "once reported as evidence (+0.009) had a bootstrap CI spanning "
             "zero.**", "",
             "| variant | " + " | ".join(behaviours) + " | mean |",
             "| --- | " + " | ".join("---:" for _ in behaviours) + " | ---: |",
             "| _FLOOR (all-relevant)_ | "
             + " | ".join(f"_{floors[s]:+.3f}_" for s in behaviours)
             + f" | _{sum(floors.values()) / len(floors):+.3f}_ |"]
    for label, w in variants:
        idx = relevance.RelevanceIndex(clauses, annotations, w)
        cells, vals = [], []
        for slug, b in behaviours.items():
            # Rank on MCC, not F1. `mcc()`'s own docstring declares best-F1
            # unquotable here: the all-relevant point is inside the sweep and
            # F1's floor is 0.44-0.59, so best-F1 ranks channels on a metric
            # that a degenerate predictor already scores well on. MCC is 0 by
            # construction for that predictor, so a channel that only rescales
            # the score distribution cannot buy anything.
            best = None
            for _, pred in idx.sweep(queries[slug]):
                if not pred:
                    continue
                ev = evaluate(b, pred, clauses, spec, joins=joins[slug])
                m = ev["tool_mcc_mean_full"]
                if best is None or m > best:
                    best = m
            best = best if best is not None else 0.0
            cells.append(f"{best:+.3f}")
            vals.append(best)
        lines.append(f"| {label} | " + " | ".join(cells) +
                     f" | {_pct(sum(vals) / len(vals) if vals else 0.0)} |")
    lines.append("")
    return "\n".join(lines)


# ================================================================
#  PANEL v2 — 18 CELLS (9 behaviours x 2 specs), SMALL-MODEL judges
# ================================================================
#
# `panel_v2` loads a second panel: 9 behaviours against BOTH specs, judged by
# gpt-mini / haiku / qwen-small. It fixes the binding constraint on everything
# above — n=3 behaviours, one spec — but it is POWER, NOT A BAR. The bar this
# project has to clear is "as good as asking a FRONTIER model", and only the
# frontier panel (sol / kimi / fable / opus / kimi-k2) measures that.
#
# So the tier travels WITH THE DATA (`behaviour["panel"]`) and
# `check_bar_provenance` refuses to let a report quote a judge number off
# small-model behaviours without naming the roster and disclaiming the tier.
# A caveat in prose would have been forgotten; this one fails a test.

#: A behaviour with no `panel` block is the original frontier panel — that file
#: predates the field. Defaulting the OTHER way would silently label the
#: frontier bar "small".
DEFAULT_PANEL = {"id": "frontier-panel", "tier": "frontier",
                 "models": [], "label": "frontier panel"}

#: Clause inventory and spec markdown per spec key. Both sides must be
#: switchable from one place, or the constitution silently gets scored against
#: the model spec's clauses and every miss reads as a segmentation bug.
SPEC_CLAUSES = {
    "openai": CLAUSES,
    "anthropic": os.path.join(HERE, "constitution_clauses.json"),
}
SPEC_MARKDOWN = {
    "openai": inventory.SPEC_MD,
    "anthropic": os.path.abspath(os.path.join(
        HERE, "..", "specs", "claude-constitution", "20260120-constitution.md")),
}


def panel_of(behaviour) -> dict:
    return dict(DEFAULT_PANEL, **(behaviour.get("panel") or {}))


def panel_tier(behaviour) -> str:
    return panel_of(behaviour)["tier"]


def panel_roster(behaviour) -> list:
    return list(panel_of(behaviour)["models"])


def clauses_for_spec(spec_key: str):
    """`(clauses, source)` for a spec key. Raises on an unknown key rather than
    falling back to the model spec."""
    path = SPEC_CLAUSES[spec_key]
    return load_clauses(path, fallback=(spec_key == "openai"))


def spec_text_for(spec_key: str) -> str:
    return spec_text(SPEC_MARKDOWN[spec_key])


def bar_provenance_block(behaviours) -> str:
    """Names, in the document, whose judgements the 'bar' column is made of.

    Emitted by every panel-v2 report and checked by `check_bar_provenance`.
    """
    tiers = {}
    for b in (behaviours.values() if isinstance(behaviours, dict) else behaviours):
        p = panel_of(b)
        # A panel that does not declare its roster (the original file predates
        # the field) has it DERIVED from the verdicts, never left blank: an
        # unnamed bar is the thing this block exists to prevent.
        models = tuple(p["models"]) or tuple(sorted(
            {j for k in spec_keys(b) for j in judges(b, k)}))
        key = (p["tier"], models, p["id"])
        tiers[key] = tiers.get(key, 0) + 1
    lines = ["### Whose judgements is this table's bar made of?", ""]
    for (tier, models, pid), n in sorted(tiers.items()):
        roster = ", ".join(f"`{m}`" for m in models) or "(unnamed)"
        if tier == "frontier":
            lines.append(
                f"* **frontier panel** (`{pid}`, {n} behaviours): {roster}. "
                f"THE BAR — 'as good as just asking a frontier model' is the "
                f"question, and these are the frontier models.")
        else:
            lines.append(
                f"* **small-model panel** (`{pid}`, {n} behaviours): "
                f"{roster}. **NOT the frontier bar.** These judges are small "
                f"models; their agreement measures how well small models agree "
                f"with each other, which is not the standard this tool has to "
                f"meet. Use these cells for POWER and GENERALISATION — whether "
                f"an effect survives 9 behaviours and 2 specs — never as the "
                f"bar.")
    lines.append("")
    return "\n".join(lines)


#: The strings a bar-quoting document must contain when small-model cells are
#: in it. Kept as data so the test and the guard cannot drift apart.
BAR_TIER_MARKERS = ("small-model panel", "not the frontier bar")

#: The one marker that has to arrive BEFORE the first bar number: it is the
#: sentence that changes how the number is read.
BAR_DECISIVE_MARKER = "not the frontier bar"

#: Column headers / phrases that mean "a judge number is being quoted here".
#: Kept for callers that inspect it; `BAR_PATTERNS` is what the guard uses.
BAR_MARKERS = ("judge mcc", "judge f1", "the bar", "judge (mean loo)")

#: WHAT COUNTS AS QUOTING A BAR. Regexes, not substrings, because the substring
#: list above missed the paraphrases — a reviewer defeated the guard outright
#: with `judge agreement 0.83`, which hits none of the four strings. Any table
#: line naming a judge counts too: a bar column does not have to be spelled
#: `judge MCC` to be read as one.
BAR_PATTERNS = tuple(re.compile(p, re.I) for p in (
    r"judges?\s+(mcc|f1|agreement|score|number|column|accuracy|performance)",
    r"judges?\s*\(mean\s+loo\)",
    r"\bmean\s+loo\b",
    r"\bthe bar\b",
    r"panel\s+(self-)?agreement",
    r"inter-?judge",
    r"judges?\s+(agree|scored|reach|hit|achieve)",
    r"^\s*\|.*judge",
))

#: The tier vocabulary a bar-quoting SECTION has to contain. `small` and
#: `frontier` are the values `cell_table` prints in its own `panel` column, so
#: an honest table satisfies this from its data rather than from prose.
TIER_WORDS = tuple(re.compile(p, re.I) for p in (
    r"\bsmall[- ]model\b", r"\bsmall\b", r"\bfrontier\b"))

#: HTML comments render as nothing. Text a reader cannot see cannot discharge a
#: disclosure duty, and a substring scan cannot tell the difference — a
#: reviewer defeated the old guard by wrapping the disclaimer in one.
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)

#: "a number is being stated on this line", for the ordering rule.
_NUMBER = re.compile(r"[-+]?\d*\.\d+|\b\d+\s*%")


class BarProvenanceError(AssertionError):
    """A judge/bar number was quoted without saying whose judgement it is.

    Subclasses `AssertionError` so callers that already catch that keep
    working, but it is RAISED, never asserted: the old guard was built out of
    bare `assert`s and therefore compiled out entirely under `python -O` —
    the guard evaporated in exactly the runs nobody watches.
    """


def visible_text(md: str) -> str:
    """`md` with HTML comments removed — the text a reader actually sees."""
    return _HTML_COMMENT.sub(" ", md)


def _quotes_a_bar(line: str) -> bool:
    return any(p.search(line) for p in BAR_PATTERNS)


def _bar_number_line(lines, i: int):
    """Where the bar number quoted at line `i` actually lands.

    A table HEADER names the judge column and carries no number; the numbers
    are in the rows underneath. Returns the first line at or after `i`, within
    the same contiguous table block, that states a number — or `None` if this
    mention never reaches one (prose about the bar, not a bar number).
    """
    if _NUMBER.search(lines[i]):
        return i
    if not lines[i].lstrip().startswith("|"):
        return None
    for j in range(i + 1, len(lines)):
        if not lines[j].lstrip().startswith("|"):
            return None
        if _NUMBER.search(lines[j]):
            return j
    return None


def _section_bounds(lines) -> list:
    """`[(start, end)]` for each markdown section — a heading and everything
    under it until the next heading. A document with no headings is one
    section."""
    starts = [i for i, l in enumerate(lines) if l.lstrip().startswith("#")]
    if not starts or starts[0] != 0:
        starts = [0] + starts
    return [(s, starts[i + 1] if i + 1 < len(starts) else len(lines))
            for i, s in enumerate(starts)]


def check_bar_provenance(md: str, behaviours) -> bool:
    """A bar may never be quoted off small-model judges without saying so.

    Same standing-invariant machinery as `check_report_pairing` /
    `check_universe_pairing`, for the defect that this panel invites: its 18
    cells are six times the frontier panel's evidence, so its judge column is
    exactly the number someone will lift and quote as 'the bar'.

    ⚠️ THE VERSION THIS REPLACES WAS SELF-SATISFYING. Its only call site
    emitted `bar_provenance_block(...)` two lines earlier; that block contains
    the exact strings the guard scanned for, so the guard could not fail for
    ANY report the function produced. A reviewer walked through it three ways
    and `python -O` deleted it a fourth. Each hole is now a rule, and each rule
    is a test:

      1. VISIBILITY — the scan runs on `visible_text(md)`. A disclaimer inside
         an HTML comment renders as nothing and no longer counts.
      2. ORDERING — the decisive sentence must appear BEFORE the first bar
         number. A caveat the reader meets afterwards is not a caveat.
      3. ATTACHMENT — every SECTION that quotes a bar must itself name a tier.
         This is the rule the emitting block cannot satisfy on the guard's
         behalf: the block is one section and the tables are others, so the
         tables have to carry their own labels (`cell_table` prints a `panel`
         column, which is exactly this). It is what makes the guard capable of
         failing a report this module produces.
      4. COVERAGE — `BAR_PATTERNS` are regexes over the paraphrases, not four
         literal column headers.

    Raises `BarProvenanceError` rather than asserting, so `-O` cannot remove it.
    """
    vis = visible_text(md)
    lines = vis.split("\n")
    quoting = [i for i, l in enumerate(lines) if _quotes_a_bar(l)]
    if not quoting:
        return True
    bs = list(behaviours.values() if isinstance(behaviours, dict) else behaviours)
    small = [b for b in bs if panel_tier(b) != "frontier"]
    if not small:
        return True

    low = vis.lower()
    for marker in BAR_TIER_MARKERS:
        if marker not in low:
            raise BarProvenanceError(
                f"a judge/bar number was emitted off SMALL-MODEL judges "
                f"without {marker!r} in the VISIBLE text of the document — the "
                f"small-model panel is power, not the bar. (HTML comments are "
                f"stripped before this check: a caveat the reader cannot see "
                f"has not been made.)")
    for m in sorted({m for b in small for m in panel_roster(b)}):
        if m.lower() not in low:
            raise BarProvenanceError(
                f"the bar's roster is not named: judge {m!r} is missing from "
                f"the document. A bar has to name whose judgement it is.")

    # ORDERING is judged against the first bar NUMBER, not the first mention of
    # a bar: `bar_provenance_block` legitimately says "THE BAR" while
    # explaining what the bar is, one line above the small-model disclaimer.
    lows = [l.lower() for l in lines]
    numeric = sorted(filter(None, (_bar_number_line(lines, i)
                                   for i in quoting)))
    first_disclaimer = next((i for i, l in enumerate(lows)
                             if BAR_DECISIVE_MARKER in l), len(lines))
    if numeric and first_disclaimer > numeric[0]:
        raise BarProvenanceError(
            f"the tier disclaimer appears on line {first_disclaimer} but the "
            f"first bar number is quoted on line {numeric[0]} — it must come "
            f"BEFORE the number it qualifies. A reader who stops at the table "
            f"never reaches a caveat printed underneath it.")

    for start, end in _section_bounds(lines):
        hits = [i for i in quoting if start <= i < end]
        if not hits:
            continue
        if not any(p.search(l) for l in lines[start:end] for p in TIER_WORDS):
            head = lines[start].strip() or "(no heading)"
            raise BarProvenanceError(
                f"a bar number is quoted in the section {head!r} (line "
                f"{hits[0]}) and NOTHING in that section names a panel tier. "
                f"A disclaimer attached to a different section does not label "
                f"this table: `cell_table` prints a `panel` column for exactly "
                f"this reason, and a table that quotes a judge column without "
                f"one is an unlabelled bar.")
    return True


# ------------------------------------------------------ the 18-cell scoring

def floor_b_mcc(gold, universe, matched) -> float:
    """FLOOR B — the degenerate predictor that fires on every JOINABLE passage.

    Floor A is MCC's definitional zero (predict the literal universe: 0.000,
    chance). Floor B is that same do-nothing predictor once the coverage gap is
    imposed on it: it cannot reach a passage no clause joins to. The two are
    different numbers and conflating them is how a coverage cost gets absorbed
    into a headline, so both are printed on every row.
    """
    return mcc(set(matched), gold, universe)


def cell_evaluate(behaviour, predicted_clause_ids, spec_key: str,
                  clauses=None, spec: str | None = None, joins: dict | None = None,
                  threshold: int = 1, scores: dict | None = None) -> dict:
    """`evaluate` for one (behaviour, spec) cell, with the floors it needs.

    The clause inventory and the spec markdown default PER SPEC KEY: the
    constitution is scored against `constitution_clauses.json` and diagnosed
    against the constitution markdown, never against the model spec's.
    """
    if clauses is None:
        clauses, _ = clauses_for_spec(spec_key)
    if spec is None:
        spec = spec_text_for(spec_key)
    if joins is None:
        joins = clause_joins(behaviour, clauses, spec_key)
    ev = evaluate(behaviour, predicted_clause_ids, clauses, spec, joins=joins,
                  threshold=threshold, spec_key=spec_key, scores=scores)
    universe, matched = set(joins), joinable(joins)
    rows = ev["per_target"]
    for j, t in pair_targets(behaviour, threshold, spec_key).items():
        rows[j]["floor_a_mcc"] = 0.0            # chance, by construction
        rows[j]["floor_b_mcc"] = floor_b_mcc(t["gold"], universe, matched)
    n = max(1, len(rows))
    ev["spec_key"] = spec_key
    ev["panel"] = panel_of(behaviour)
    ev["floor_a_mcc"] = 0.0
    ev["floor_b_mcc_mean"] = sum(r["floor_b_mcc"] for r in rows.values()) / n
    return ev


def cell_results(behaviours, predictions, spec_keys=("openai", "anthropic"),
                 threshold: int = 1, clauses=None, specs=None,
                 joins=None) -> dict:
    """`{(slug, spec_key): ev}` over every cell that has both coverage and a
    prediction.

    `predictions` is keyed `(slug, spec_key)` — NOT by slug. A slug-keyed map
    would silently score the constitution with the model spec's predicted
    clause ids, which is a different document's clause namespace and would
    quietly produce an empty prediction rather than an error.
    """
    clauses = clauses or {}
    specs = specs or {}
    out = {}
    for slug in sorted(behaviours):
        b = behaviours[slug]
        for key in spec_keys:
            if key not in (b.get("coverage") or {}):
                continue
            if (slug, key) not in predictions:
                continue
            if key not in clauses:
                clauses[key] = clauses_for_spec(key)[0]
            if key not in specs:
                specs[key] = spec_text_for(key)
            out[(slug, key)] = cell_evaluate(
                b, predictions[(slug, key)], key, clauses=clauses[key],
                spec=specs[key], threshold=threshold,
                joins=(joins or {}).get((slug, key)))
    return out


def cell_table(results: dict, label: str = "tool") -> str:
    """The 18-cell table. One row per CELL, never a mean alone.

    MCC primary, with FLOOR A (chance) and FLOOR B (chance under the coverage
    gap) beside it, and the judge column labelled by tier so a small-model
    number cannot be mistaken for the bar.
    """
    lines = [
        f"## Per-cell — `{label}` on every (behaviour, spec) cell", "",
        "**MCC is primary.** FLOOR A = 0.000, the definitional chance level "
        "(predict the whole universe). FLOOR B = the same do-nothing predictor "
        "confined to the passages any clause joins to — chance, shifted by the "
        "coverage gap. A tool MCC that does not clear FLOOR B has bought "
        "nothing that the join did not already give it. The `judge MCC` column "
        "is the mean leave-one-out over that cell's own judges and is labelled "
        "with its panel tier.",
        "",
        "| behaviour | spec | panel | n | gold (mean) | **tool MCC** | FLOOR A "
        "| FLOOR B | judge MCC (mean LOO) | tool F1 | F1 floor |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for (slug, key), ev in sorted(results.items()):
        rows = list(ev["per_target"].values())
        n = max(1, len(rows))
        gold = sum(r["gold_full"] for r in rows) / n
        tier = ev.get("panel", DEFAULT_PANEL)["tier"]
        lines.append(
            f"| {slug} | {key} | {tier} | {ev['n_passages']} | {gold:.0f} "
            f"| **{ev['tool_mcc_mean_full']:+.3f}** | {ev['floor_a_mcc']:+.3f} "
            f"| {ev['floor_b_mcc_mean']:+.3f} "
            f"| {ev['judge_mcc_mean_full']:+.3f} "
            f"| {_pct(ev['tool_mean_full'])} | {_pct(ev['floor_mean'])} |")
    if results:
        n = len(results)
        agg = lambda k: sum(ev[k] for ev in results.values()) / n
        lines.append(
            f"| **mean of {n} cells** | | | | | "
            f"**{agg('tool_mcc_mean_full'):+.3f}** | +0.000 "
            f"| {agg('floor_b_mcc_mean'):+.3f} | {agg('judge_mcc_mean_full'):+.3f} "
            f"| {_pct(agg('tool_mean_full'))} | {_pct(agg('floor_mean'))} |")
    lines.append("")
    lines.append("_The mean is printed last and on purpose: it is the least "
                 "informative row of this table. Every per-cell row above it "
                 "is a separate result._")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------- bootstrap over 18 cells

def cell_vectors(behaviour, predicted_passages, spec_key: str,
                 universe=None, threshold: int = 1) -> list:
    """`[[(predicted, gold)] per passage] per held-out judge` for one cell.

    The bootstrap resamples PASSAGES, so the unit has to be a passage-aligned
    vector; building it once keeps every resample pure arithmetic.
    """
    ps = sorted(universe if universe is not None
                else {p["id"] for p in passages(behaviour, spec_key)})
    pred = set(predicted_passages)
    return [[(p in pred, p in t["gold"]) for p in ps]
            for _, t in sorted(pair_targets(behaviour, threshold,
                                            spec_key).items())]


def _mcc_of(pairs, idxs) -> float:
    tp = fp = fn = tn = 0
    for i in idxs:
        p, g = pairs[i]
        tp, fp, fn, tn = (tp + (p and g), fp + (p and not g),
                          fn + (g and not p), tn + (not p and not g))
    d = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
    return 0.0 if d <= 0 else (tp * tn - fp * fn) / math.sqrt(d)


def _cell_mean(vecs, idxs) -> float:
    return sum(_mcc_of(v, idxs) for v in vecs) / max(1, len(vecs))


def paired_bootstrap_cells(a: dict, b: dict, resamples: int = 2000,
                           seed: int = 17) -> tuple:
    """`(mean delta, lo, hi)` for A minus B over cells, resampling PASSAGES.

    The resample is drawn once per cell per replicate and used for BOTH sides,
    so between-passage variance cancels; cells are averaged with equal weight
    (a 589-passage cell does not outvote a 374-passage one, because the unit of
    generalisation here is the CELL).
    """
    import random
    rng = random.Random(seed)
    keys = sorted(set(a) & set(b))
    if not keys:
        return (0.0, 0.0, 0.0)
    sizes = {k: len(a[k][0]) if a[k] else 0 for k in keys}
    deltas = []
    for _ in range(resamples):
        idx = {k: [rng.randrange(sizes[k]) for _ in range(sizes[k])]
               for k in keys if sizes[k]}
        deltas.append(sum(_cell_mean(a[k], idx[k]) - _cell_mean(b[k], idx[k])
                          for k in keys if sizes[k]) / len(keys))
    deltas.sort()
    return (sum(deltas) / len(deltas), deltas[int(0.025 * len(deltas))],
            deltas[int(0.975 * len(deltas)) - 1])


def noise_floor(a: dict, resamples: int = 2000, seed: int = 17) -> dict:
    """RE-DERIVE the noise floor on THIS panel. Never import an old constant.

    The floor is the spread of a delta that is KNOWN TO BE ZERO: the SAME
    predictor scored on two INDEPENDENT passage resamples. Anything smaller
    than the 95% interval of that null delta is indistinguishable from
    resampling noise on this data, whatever the point estimates say.

    `OPERATING_POINT_NOISE = 0.045` was derived this way on the 3-behaviour,
    589-passage, 9-cell panel. It does NOT transfer: this panel has 18 cells,
    two universe sizes and a different gold base rate, and an expired noise
    constant is exactly how a false null gets published.
    """
    import random
    rng = random.Random(seed)
    keys = sorted(a)
    sizes = {k: len(a[k][0]) if a[k] else 0 for k in keys}
    deltas = []
    for _ in range(resamples):
        d = 0.0
        for k in keys:
            if not sizes[k]:
                continue
            i = [rng.randrange(sizes[k]) for _ in range(sizes[k])]
            j = [rng.randrange(sizes[k]) for _ in range(sizes[k])]
            d += _cell_mean(a[k], i) - _cell_mean(a[k], j)
        deltas.append(d / max(1, len(keys)))
    deltas.sort()
    lo = deltas[int(0.025 * len(deltas))]
    hi = deltas[int(0.975 * len(deltas)) - 1]
    return {"resamples": resamples, "cells": len(keys), "lo": lo, "hi": hi,
            "half_width": (hi - lo) / 2,
            "mean": sum(deltas) / len(deltas)}


def bootstrap_block(delta: tuple, a_name: str, b_name: str,
                    nf: dict | None = None) -> str:
    """One paired-bootstrap comparison, read against the RE-DERIVED noise floor.

    A point estimate above the floor with an interval that excludes zero is a
    result; anything else is printed as "not distinguishable" in the table
    itself rather than left to the reader.
    """
    mean, lo, hi = delta
    excl = (lo > 0) or (hi < 0)
    over = nf is None or abs(mean) > nf["half_width"]
    verdict = ("**distinguishable**" if excl and over else
               "**NOT distinguishable** (interval contains 0)" if not excl else
               "**NOT distinguishable** (below the re-derived noise floor)")
    return "\n".join([
        f"### Paired bootstrap — {a_name} minus {b_name}", "",
        "Passages resampled with replacement, the resample held COMMON to both "
        "sides, cells weighted equally.", "",
        f"* delta: **{mean:+.4f}**  95% CI **[{lo:+.4f}, {hi:+.4f}]**",
        (f"* noise floor (re-derived, same protocol): {nf['half_width']:.4f}"
         if nf else "* noise floor: not supplied"),
        f"* verdict: {verdict}", "",
    ])


def noise_floor_block(nf: dict, name: str = "panel v2 (18 cells)") -> str:
    return "\n".join([
        f"### Noise floor — RE-DERIVED on {name}", "",
        "The spread of a delta known to be zero: the same predictor scored on "
        "two INDEPENDENT passage resamples, averaged over cells. A difference "
        "smaller than this is not a result on this data.", "",
        f"* resamples: **{nf['resamples']}**, cells: **{nf['cells']}**",
        f"* null delta 95% interval: **[{nf['lo']:+.4f}, {nf['hi']:+.4f}]** "
        f"(mean {nf['mean']:+.4f})",
        f"* **noise floor (half-width): {nf['half_width']:.4f}**",
        "",
        f"The 3-behaviour panel's constant (`OPERATING_POINT_NOISE = "
        f"{OPERATING_POINT_NOISE}`) is NOT reused here; importing an expired "
        f"noise constant is how a false null gets published.", "",
    ])


def cell_delta_table(true_results: dict, pub_results: dict) -> str:
    """TRUE minus PUBLISHED, per cell. The pairing this project exists to keep.

    The panel-v2 export is truncated exactly as `behaviours.json` was, so the
    same failure is available: quoting the export's own passage list as if it
    were the judged universe. Both are computed and the delta is stated.
    """
    lines = ["## TRUE vs published universe — the delta, per cell", "",
             "`published` here is the export's own citation list (score >= 2 "
             "only); `true` is the full spec universe with every absent passage "
             "restored as verdict 0 from every judge.", "",
             # THE `panel` COLUMN IS NOT DECORATION. This table quotes two
             # judge-MCC columns and used to print them with no indication of
             # whose judgement they are; `check_bar_provenance` now refuses a
             # bar quoted in a section that names no tier, and this table was
             # the one real report section that failed the new rule.
             "| behaviour | spec | panel | tool MCC (true) | tool MCC "
             "(published) | delta | judge MCC (true) | judge MCC (published) "
             "| delta |",
             "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    tot = {k: [] for k in ("t_true", "t_pub", "j_true", "j_pub")}
    for key in sorted(set(true_results) & set(pub_results)):
        t, p = true_results[key], pub_results[key]
        vals = (t["tool_mcc_mean_full"], p["tool_mcc_mean_full"],
                t["judge_mcc_mean_full"], p["judge_mcc_mean_full"])
        for name, v in zip(("t_true", "t_pub", "j_true", "j_pub"), vals):
            tot[name].append(v)
        tier = t.get("panel", DEFAULT_PANEL)["tier"]
        lines.append(
            f"| {key[0]} | {key[1]} | {tier} | {vals[0]:+.3f} | {vals[1]:+.3f} "
            f"| {vals[0] - vals[1]:+.3f} | {vals[2]:+.3f} | {vals[3]:+.3f} "
            f"| {vals[2] - vals[3]:+.3f} |")
    if tot["t_true"]:
        n = len(tot["t_true"])
        m = {k: sum(v) / n for k, v in tot.items()}
        lines.append(
            f"| **mean** | | | **{m['t_true']:+.3f}** | {m['t_pub']:+.3f} "
            f"| {m['t_true'] - m['t_pub']:+.3f} | **{m['j_true']:+.3f}** "
            f"| {m['j_pub']:+.3f} | {m['j_true'] - m['j_pub']:+.3f} |")
    lines.append("")
    return "\n".join(lines)


def panel_v2_report(behaviours, true_results, pub_results, label: str = "tool",
                    nf: dict | None = None, prov: dict | None = None,
                    cost: dict | None = None, notes=(), tail_blocks=(),
                    frontier_results: dict | None = None,
                    frontier_behaviours: dict | None = None) -> str:
    """THE panel-v2 report. 18 cells, both universes, floors, re-derived noise.

    Runs all three standing guards on its own output before returning:
    `check_report_pairing`, `check_universe_pairing`, `check_bar_provenance`.
    """
    import panel_v2
    out = ["# Panel v2 — 9 behaviours x 2 specs, 18 cells", "",
           f"predictor: **{label}**", ""]
    # A LIST, not a merged dict: THREE SLUGS ARE IN BOTH PANELS (helpfulness,
    # harm-avoidance-to-third-parties, avoiding-over-and-under-caution), so a
    # dict update silently deletes three small-model behaviours and misreports
    # the roster counts in the block below.
    everyone = list(behaviours.values() if isinstance(behaviours, dict)
                    else behaviours)
    everyone += list((frontier_behaviours or {}).values())
    if prov:
        out.append(panel_v2.provenance_block(prov))
    out.append(bar_provenance_block(everyone))
    if cost:
        out.append(panel_v2.truncation_block(cost))
    for n in notes:
        out.append(n)
        out.append("")
    out.append(CAVEATS)
    out.append("")
    out.append("### TRUE universe — the headline")
    out.append("")
    out.append(cell_table(true_results, label))
    out.append("### published universe — the export's own truncated citation "
               "list, for comparison ONLY")
    out.append("")
    out.append(cell_table(pub_results, label + " (published universe)"))
    if frontier_results:
        # SEPARATE SECTION, ON PURPOSE. The frontier cells are the only ones
        # that can carry the bar; merging them into the 18-cell mean would
        # average the bar together with a number that is not the bar.
        out.append("### FRONTIER panel — the SAME predictor, scored against "
                   "the real bar. Reported SEPARATELY and never merged into "
                   "the 18-cell mean.")
        out.append("")
        out.append(cell_table(frontier_results, label + " (frontier panel)"))
    out.append(cell_delta_table(true_results, pub_results))
    for blk in tail_blocks:
        out.append(blk)
    if nf:
        out.append(noise_floor_block(nf))
    md = "\n".join(out)
    check_report_pairing(md)
    check_universe_pairing(md)
    check_bar_provenance(md, everyone)
    return md


# ================================================================
#  QUERY MODULES — every scorer on the same gold, or none of them
# ================================================================
#
# THE DEFECT THIS SECTION EXISTS FOR. For three cycles every mode of this file
# (`--tool`, `--ablate`, `--panel-v2`, `--sweep`, `--control`,
# `--operating-point`) built a `relevance.RelevanceIndex` and scored that.
# `structural.py` — zero fitted parameters, contract-invariant-10 compliant,
# a strictly better `explain()` — COULD NOT PRODUCE A HEADLINE NUMBER AT ALL,
# because nothing here could turn it into predictions and its own CLI emits no
# `{slug: [clause_id]}` file for the `preds.json` path to read. `section.py`
# likewise. So every number the project reported came from the one module the
# contract says violates invariant 10, and the compliant replacement sat
# unwired and unmeasured.
#
# The fix is deliberately thin: a uniform (predict, rank) surface, and NOTHING
# else. Gold construction, the evaluation universe and the clause->passage
# join stay where they were — in `cell_results` / `cell_evaluate` — so all
# three modules are scored by the identical code on the identical data and the
# comparison cannot become an artifact of two harnesses.
# `test_all_modules_score_through_the_identical_gold_universe_and_join` pins
# that: same `n_passages`, same FLOOR B, same judge column, same gold sets.
#
# LABEL-FREE, ALL THE WAY DOWN. `relevance` is queried through `predict(b)`
# with NO threshold argument, i.e. the Otsu cut taken from the query's own
# score distribution. `relevance.DEFAULT_THRESHOLD = 0.18` is the in-sample
# argmax of a 51-point grid ON THIS PANEL and is worth a spurious +0.042 mean
# MCC; it was retired from this file and must not come back through a wrapper.
# `structural` and `section` have no threshold to reintroduce — that is the
# whole point of them.

#: Independent draws of the PANEL-V2 behaviour atoms (9 behaviours). The
#: 3-behaviour draws live in `ATOM_DRAWS`; these are the ones that cover the
#: nine-behaviour panel, and a comparison quoted on ONE of them is an error
#: this project has already made twice.
ATOM_DRAWS_V2 = tuple(f"behavior_atoms_v2_draw{i}.json" for i in range(5))

#: The query modules a headline may be computed with.
# `combined` MUST be here: it carries the project's headline (+0.316) and was
# the only major result never produced by the guarded harness — which refuses
# single-draw tables, intervals without a re-derived noise floor, and the
# expired 0.045 by name. Every number this project has had to retract had
# exactly that shape.
QUERY_MODULES = ("relevance", "structural", "section", "combined")

#: The control is not a query module — it is the same bag scorer with the
#: ontology channels set to zero, so `tool - control` is exactly the ontology's
#: contribution and cannot drift into a difference between implementations.
CONTROL_MODULE = "control"
COMPARABLE_MODULES = QUERY_MODULES + (CONTROL_MODULE,)

DEFAULT_QUERY_MODULE = "relevance"

#: What each module IS, in the contract's terms, printed as the table's row
#: label so no reader has to be told separately which one is compliant.
QUERY_MODULE_CONTRACT = {
    "relevance": ("`relevance.py` — bag scorer",
                  "VIOLATES invariant 10 (a similarity score, not a "
                  "structural query); scheduled for replacement"),
    "structural": ("`structural.py` — typed ladder",
                   "invariant-10 COMPLIANT: zero fitted parameters, "
                   "`max_hops=0`, a named operator rather than a threshold"),
    "section": ("`section.py` — section quotient",
                "invariant-10 COMPLIANT; its decision rule is the "
                "PRE-REGISTERED majority election, which the module's own "
                "docstring records as a loser"),
    "combined": ("`combined.py` — typed core UNION elected sections",
                 "invariant-10 COMPLIANT: a set union of typed operations, no "
                 "weights and no threshold anywhere in `predict`. The only "
                 "compliant configuration measured ABOVE the bag scorer, and "
                 "only at the no-choice `any_atom` operator"),
    "control": ("lexical control", "the SAME bag scorer with `atom`, `kind` "
                "and `section` weights at 0 — bag-of-words and nothing else"),
}


class QueryModule:
    """One uniform `predict(slug) -> {clause_id}` / `rank(slug)` surface.

    Holds the module's own index and its own query objects, which are NOT
    interchangeable: `relevance` queries a `Behaviour` (name + definition +
    atoms), `structural`/`section` query a typed `Query` (atoms in slots, no
    prose by construction). Everything downstream sees only clause ids.
    """

    def __init__(self, name: str, index, queries: dict, predict, rank,
                 notes=()):
        self.name = name
        self.index = index
        self.queries = queries
        self._predict = predict
        self._rank = rank
        self.notes = list(notes)
        self.label, self.contract = QUERY_MODULE_CONTRACT[name]

    @property
    def slugs(self) -> list:
        return sorted(self.queries)

    @property
    def clause_ids(self) -> list:
        """The corpus this module actually indexed.

        Exposed so a test can prove every module was built over the SAME
        clauses rather than reaching for its own default file — `structural`
        and `section` both carry a `CLAUSES` constant of their own, and a
        module quietly scoring a different corpus is a comparison of two
        harnesses wearing one table.
        """
        idx = getattr(self.index, "index", self.index)   # SectionQuotient wraps
        return list(getattr(idx, "ids", []))

    def predict(self, slug: str) -> set:
        q = self.queries.get(slug)
        return set() if q is None else set(self._predict(q))

    def rank(self, slug: str) -> dict:
        q = self.queries.get(slug)
        return {} if q is None else dict(self._rank(q))

    def predictions(self, spec_key: str = DEFAULT_SPEC_KEY,
                    slugs=None) -> dict:
        """`{(slug, spec_key): {clause_id}}` — the shape `cell_results` reads."""
        return {(s, spec_key): self.predict(s)
                for s in (self.slugs if slugs is None else slugs)
                if s in self.queries}


def build_query_module(name: str, behaviours, clauses, annotations=None,
                       atoms=None) -> QueryModule:
    """Build any declared query module over ONE clause inventory.

    `annotations` is the CLAUSE-side atom map (a dict or a path); `atoms` is
    the QUERY-side behaviour-atom artifact (a path). Both are passed through
    unchanged to every module, so no module can be handed a different corpus
    than its rivals.

    ⚠️ The constitution (`anthropic`) has ZERO `c*` clause annotations. Handed
    an empty annotation map, `structural` and `section` fire on nothing and
    `relevance` degenerates to bag-of-words. That is a missing input, not a
    result: `compare_query_modules` records it in `missing` and the renderer
    prints it rather than showing a row of zeroes as a measurement.
    """
    import relevance
    if name not in QUERY_MODULE_CONTRACT:
        raise ValueError(f"unknown query module {name!r}; have "
                         f"{sorted(QUERY_MODULE_CONTRACT)}")
    ann = (annotations if isinstance(annotations, dict)
           else relevance.load_annotations(annotations))

    if name in ("relevance", CONTROL_MODULE):
        import lexical_control
        control = name == CONTROL_MODULE
        weights = (lexical_control.CONTROL_WEIGHTS if control
                   else relevance.Weights())
        # THE CONTROL GETS THE SAME QUERY AND NO ANNOTATIONS. Same tokenizer,
        # same clause join, same evaluation protocol, same behaviour atoms in
        # the query text — the ONLY difference is that the ontology channels
        # are multiplied by zero. Giving the control a poorer query as well
        # would make `tool - control` a sum of two effects and attribute the
        # query artifact's contribution to the ontology.
        batoms = relevance.load_behaviour_atoms(atoms) if atoms else {}
        idx = relevance.RelevanceIndex(clauses, {} if control else ann, weights)
        qs = {slug: relevance.behaviour_from_panel(b, batoms)
              for slug, b in behaviours.items()}
        # `idx.predict(q)` — NO THRESHOLD ARGUMENT. See the section header.
        return QueryModule(name, idx, qs, lambda q: idx.predict(q),
                           lambda q: dict(idx.rank(q)))

    import structural
    sidx = structural.StructuralIndex(clauses, ann)
    qs = {s: q for s, q in structural.load_queries(
        atoms or structural.BEHAVIOUR_ATOMS).items() if s in behaviours}
    if name == "structural":
        return QueryModule(name, sidx, qs, lambda q: sidx.predict(q),
                           lambda q: dict(sidx.rank(q)))

    if name == "combined":
        import combined
        ci = combined.CombinedIndex(sidx)
        # V1@any — typed core UNION majority-elected sections, at the NO-CHOICE
        # `any_atom` operator. This is the +0.316 configuration; routing it
        # through here is what finally puts the project's headline under the
        # guarded harness that refuses single-draw tables and floor-less
        # intervals. `variant()` takes (query, variant, operator).
        return QueryModule(name, ci, qs,
                           lambda q: ci.variant(q, "V1", "any_atom"),
                           lambda q: dict(ci.rank(q)))

    import section
    sq = section.SectionQuotient(sidx)
    return QueryModule(name, sq, qs, lambda q: sq.predict(q),
                       lambda q: dict(sq.rank(q)))


def resolve_atom_draws(draws=ATOM_DRAWS_V2) -> list:
    """The draws that are actually on disk, as absolute paths."""
    out = []
    for d in draws:
        p = d if os.path.isabs(d) else os.path.join(HERE, d)
        if os.path.exists(p):
            out.append(p)
    return out


def compare_query_modules(behaviours, spec_key: str = DEFAULT_SPEC_KEY,
                          clauses=None, annotations=None, spec: str | None = None,
                          atom_draws=None, modules=COMPARABLE_MODULES,
                          resamples: int = 1000) -> dict:
    """Score EVERY module on EVERY cell, on EVERY atom draw, one gold.

    Returns the measurement, not a rendering. The unit of every number is a
    (behaviour, spec) CELL — never the mean alone — and every module's cell is
    built from the same `clause_joins`, the same `pair_targets` and the same
    universe.

    THE BOOTSTRAP UNIT. `vectors[module][slug]` concatenates the per-judge
    passage-aligned vectors of all five draws, so `_cell_mean` averages MCC
    over (draw x held-out judge) inside a cell and `paired_bootstrap_cells`
    resamples PASSAGES with the resample held common to both sides. That uses
    all five draws without pretending five re-queries of one behaviour are five
    independent behaviours.
    """
    import relevance
    if clauses is None:
        clauses, _ = clauses_for_spec(spec_key)
    if spec is None:
        spec = spec_text_for(spec_key)
    ann = (annotations if isinstance(annotations, dict)
           else relevance.load_annotations(annotations))
    ann = annotations_for_spec(ann, spec_key)
    draws = resolve_atom_draws(atom_draws or ATOM_DRAWS_V2)
    if not draws:
        raise SystemExit(
            f"no behaviour-atom draw found (looked for {list(atom_draws or ATOM_DRAWS_V2)}). "
            "A comparison on zero draws is not a comparison.")

    slugs = sorted(s for s, b in behaviours.items()
                   if spec_key in (b.get("coverage") or {}))
    joins = {s: clause_joins(behaviours[s], clauses, spec_key) for s in slugs}

    mcc, judge, floor_a, floor_b, n_passages, tier = {}, {}, {}, {}, {}, {}
    vectors = {m: {s: [] for s in slugs} for m in modules}
    floor_vectors = {}
    missing = {}
    for draw in draws:
        built = {}
        for m in modules:
            built[m] = build_query_module(m, behaviours, clauses,
                                          annotations=ann, atoms=draw)
            absent = [s for s in slugs if s not in built[m].queries]
            if absent:
                missing.setdefault(m, set()).update(absent)
        for s in slugs:
            b = behaviours[s]
            for m in modules:
                ev = cell_evaluate(b, built[m].predict(s), spec_key,
                                   clauses=clauses, spec=spec, joins=joins[s])
                mcc[(m, os.path.basename(draw), s)] = ev["tool_mcc_mean_full"]
                vectors[m][s] += cell_vectors(
                    b, lift(built[m].predict(s), joins[s]), spec_key)
                if m == modules[0]:
                    judge[s] = ev["judge_mcc_mean_full"]
                    floor_a[s] = ev["floor_a_mcc"]
                    floor_b[s] = ev["floor_b_mcc_mean"]
                    n_passages[s] = ev["n_passages"]
                    tier[s] = ev.get("panel", DEFAULT_PANEL)["tier"]
            # FLOOR B as a PREDICTOR, repeated per draw so its vector list is
            # the same length as every module's and the bootstrap stays paired.
            floor_vectors.setdefault(s, [])
            floor_vectors[s] += cell_vectors(b, joinable(joins[s]), spec_key)

    nf = noise_floor(vectors[modules[0]], resamples=resamples)
    deltas = {}
    for a, b_ in combinations(modules, 2):
        deltas[(a, b_)] = paired_bootstrap_cells(vectors[a], vectors[b_],
                                                 resamples=resamples)
    for m in modules:
        deltas[(m, "FLOOR B")] = paired_bootstrap_cells(
            vectors[m], floor_vectors, resamples=resamples)

    return {
        "spec_key": spec_key, "slugs": slugs,
        "draws": [os.path.basename(d) for d in draws],
        "modules": tuple(modules), "mcc": mcc, "judge": judge,
        "floor_a": floor_a, "floor_b": floor_b, "n_passages": n_passages,
        "tier": tier,
        "roster": sorted({j for s in slugs
                          for j in panel_roster(behaviours[s])}),
        "noise_floor": nf, "deltas": deltas,
        "vectors": vectors, "floor_vectors": floor_vectors,
        "missing": {m: sorted(v) for m, v in missing.items()},
    }


# --------------------------------------------------------- the comparison

class ModuleComparisonError(AssertionError):
    """A module comparison was emitted without the context that makes it
    readable: both floors, the lexical control, every atom draw, or the
    re-derived noise floor. Raised, never asserted — see `BarProvenanceError`.
    """


def _mean(xs) -> float:
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def _sd(xs) -> float:
    xs = list(xs)
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def module_row_values(cmp: dict, module: str) -> dict:
    """`{slug: mean MCC over the draws}` for one module."""
    return {s: _mean(cmp["mcc"][(module, d, s)] for d in cmp["draws"])
            for s in cmp["slugs"]}


def module_comparison_table(cmp: dict) -> str:
    """THE TABLE. One ROW per module, one COLUMN per cell.

    Every module, the lexical control, BOTH floors and the judges are rows of
    the same table on the same cells, so which module is better is READ OFF
    rather than asserted in prose. The per-cell columns come first and the mean
    is last, because the mean is the least informative number here.
    """
    slugs, draws = cmp["slugs"], cmp["draws"]
    tiers = sorted(set(cmp["tier"].values()))
    head = ("| predictor | contract status | "
            + " | ".join(slugs) + " | **mean** |")
    lines = [
        f"## Query modules, side by side — {len(slugs)} cells, "
        f"{len(draws)} atom draws, spec `{cmp['spec_key']}`", "",
        f"**MCC is primary**, one column per CELL, the mean last. Each cell is "
        f"one (behaviour, `{cmp['spec_key']}`) pair on the TRUE universe; every "
        f"module is scored by the same `cell_evaluate` on the same gold, the "
        f"same universe and the same clause->passage join, so a difference "
        f"between rows is a difference between MODULES. Values are the mean "
        f"over **{len(draws)} draws** of the behaviour atoms; the per-draw "
        f"spread is in the next table and is not small.", "",
        "**FLOOR A** = 0.000, MCC's definitional chance level. **FLOOR B** = "
        "the same do-nothing predictor confined to passages some clause joins "
        "to — chance, shifted by the coverage gap. A row that does not clear "
        "FLOOR B has bought nothing the join did not already give it. The "
        "**lexical control** row is the same bag scorer with its ontology "
        "channels zeroed: a module that does not clear the control has not "
        "earned the cost of extraction.", "",
        f"The `judges` row is the panel's own mean leave-one-out agreement. "
        f"Panel tier(s) present: **{', '.join(tiers)}**. It is a BOUND ON THIS "
        f"TABLE'S EVIDENCE, not a target: see the bar-provenance section.", "",
        head,
        "| --- | --- | " + " | ".join("---:" for _ in slugs) + " | ---: |",
    ]
    for m in cmp["modules"]:
        label, contract = QUERY_MODULE_CONTRACT[m]
        vals = module_row_values(cmp, m)
        lines.append(
            f"| {label} | {contract} | "
            + " | ".join(f"{vals[s]:+.3f}" for s in slugs)
            + f" | **{_mean(vals.values()):+.3f}** |")
    lines.append(
        "| **FLOOR A** (chance) | MCC's definitional zero | "
        + " | ".join(f"{cmp['floor_a'][s]:+.3f}" for s in slugs)
        + f" | {_mean(cmp['floor_a'].values()):+.3f} |")
    lines.append(
        "| **FLOOR B** (chance minus the coverage gap) | predict every "
        "joinable passage | "
        + " | ".join(f"{cmp['floor_b'][s]:+.3f}" for s in slugs)
        + f" | {_mean(cmp['floor_b'].values()):+.3f} |")
    lines.append(
        "| judges (mean LOO) | "
        + f"{', '.join(tiers)} panel — the evidence bound, NOT a target | "
        + " | ".join(f"{cmp['judge'][s]:+.3f}" for s in slugs)
        + f" | {_mean(cmp['judge'].values()):+.3f} |")
    lines.append("")
    lines.append("| cell | " + " | ".join(slugs) + " |")
    lines.append("| --- | " + " | ".join("---:" for _ in slugs) + " |")
    lines.append("| passages in the universe | "
                 + " | ".join(str(cmp["n_passages"][s]) for s in slugs) + " |")
    lines.append("| panel tier | "
                 + " | ".join(cmp["tier"][s] for s in slugs) + " |")
    lines.append("")
    for m, absent in sorted(cmp.get("missing", {}).items()):
        lines.append(
            f"> `{m}` had NO QUERY for {len(absent)} cell(s) "
            f"({', '.join(absent)}) — a missing input, scored as an empty "
            f"prediction. Read those cells as absent, not as measured zeroes.")
    if cmp.get("missing"):
        lines.append("")
    return "\n".join(lines)


def module_draw_table(cmp: dict) -> str:
    """Every atom draw, per module. A single draw quoted as a constant is an
    error this project has made twice, and the draws are NOT interchangeable:
    the spread below is comparable to some of the differences between modules.
    """
    draws = cmp["draws"]
    lines = [
        f"### Per atom draw — all {len(draws)}, never one", "",
        "Each entry is the mean MCC over the cells for that draw. `sd` is the "
        "between-draw standard deviation; compare it with the module "
        "differences before believing any of them.", "",
        "| predictor | " + " | ".join(draws) + " | mean | sd |",
        "| --- | " + " | ".join("---:" for _ in draws) + " | ---: | ---: |",
    ]
    for m in cmp["modules"]:
        per = [_mean(cmp["mcc"][(m, d, s)] for s in cmp["slugs"]) for d in draws]
        lines.append(f"| {QUERY_MODULE_CONTRACT[m][0]} | "
                     + " | ".join(f"{v:+.3f}" for v in per)
                     + f" | **{_mean(per):+.3f}** | {_sd(per):.3f} |")
    lines.append("")
    return "\n".join(lines)


def module_bootstrap_block(cmp: dict) -> str:
    """Every pairwise difference, with a paired bootstrap CI, read against the
    noise floor RE-DERIVED on this panel.

    Passages are resampled with replacement and the resample is held COMMON to
    both sides, so between-passage variance cancels; cells are weighted
    equally. A difference smaller than the re-derived floor is not a result on
    this data whatever its point estimate says.
    """
    nf = cmp["noise_floor"]
    lines = [
        "### Paired bootstrap — every difference, with its interval", "",
        "Passages resampled with replacement, the resample held COMMON to both "
        "sides, cells weighted equally, all draws inside the cell.", "",
        f"**noise floor, RE-DERIVED on these {nf['cells']} cells "
        f"({nf['resamples']} resamples): {nf['half_width']:.4f}** — the spread "
        f"of a delta known to be zero (one predictor, two independent passage "
        f"resamples), 95% interval [{nf['lo']:+.4f}, {nf['hi']:+.4f}]. The "
        f"3-behaviour panel's expired constant is NOT reused: an imported noise "
        f"constant is how a false null gets published.", "",
        "| A | B | delta (A - B) | 95% CI | clears the noise floor? | verdict |",
        "| --- | --- | ---: | :---: | :---: | --- |",
    ]
    for (a, b_), (mean, lo, hi) in sorted(cmp["deltas"].items()):
        excl = (lo > 0) or (hi < 0)
        over = abs(mean) > nf["half_width"]
        verdict = ("**distinguishable**" if excl and over else
                   "not distinguishable (interval contains 0)" if not excl else
                   "not distinguishable (below the re-derived noise floor)")
        lines.append(f"| {a} | {b_} | **{mean:+.4f}** | "
                     f"[{lo:+.4f}, {hi:+.4f}] | {'yes' if over else 'no'} | "
                     f"{verdict} |")
    lines.append("")
    return "\n".join(lines)


def comparison_bar_block(cmp: dict) -> str:
    """Whose judgement the `judges` row of the comparison is. Separate from
    `bar_provenance_block` because the comparison carries its measurement in a
    dict rather than in behaviour objects."""
    tiers = sorted(set(cmp["tier"].values()))
    roster = ", ".join(f"`{m}`" for m in cmp["roster"]) or "(unnamed)"
    lines = ["### Whose judgements is this table's `judges` row made of?", ""]
    if "small" in tiers:
        lines.append(
            f"* **small-model panel**: {roster}. **NOT the frontier bar.** "
            f"These judges are small models, so their agreement measures how "
            f"well small models agree with each other, which is not the "
            f"standard this tool has to meet. Their column is additionally "
            f"INFLATED by the export's score-1 truncation (measured ~+0.09 on "
            f"the overlapping frontier cells). Use these cells for POWER and "
            f"GENERALISATION across 9 behaviours — never as the bar.")
    if "frontier" in tiers:
        lines.append(
            f"* **frontier panel**: {roster}. THE BAR — 'as good as just "
            f"asking a frontier model' is the question, and these are the "
            f"frontier models.")
    lines.append("")
    return "\n".join(lines)


#: What a module-comparison document may not be missing. Kept as data so the
#: guard and its test cannot drift apart.
COMPARISON_REQUIRED = (
    ("floor a", "FLOOR A — MCC's definitional chance level"),
    ("floor b", "FLOOR B — chance under the coverage gap"),
    ("lexical control", "the control the ontology has to beat"),
)


def check_module_comparison(md: str) -> bool:
    """A module comparison may never be emitted without its floors, its
    control, its draws or its noise floor.

    Standing-invariant machinery, same as `check_universe_pairing` /
    `check_bar_provenance`, for the failure this table invites: a row of
    per-module MCCs reads like a leaderboard, and a leaderboard with no floor
    lets a module that has learned nothing place second.
    """
    low = visible_text(md).lower()
    if "predictor |" not in low and "mcc" not in low:
        return True
    for token, why in COMPARISON_REQUIRED:
        if token not in low:
            raise ModuleComparisonError(
                f"a module comparison was emitted without {token.upper()} — "
                f"{why}. Every module number is uninterpretable without it.")
    counts = [int(n) for n in re.findall(r"(\d+)\s+(?:atom\s+)?draws", low)]
    if not counts:
        raise ModuleComparisonError(
            "a module comparison was emitted without saying how many ATOM "
            "DRAWS it averages. A single draw quoted as a constant is an error "
            "this project has already made twice.")
    if max(counts) < 2:
        raise ModuleComparisonError(
            f"a module comparison was emitted on {max(counts)} atom draw(s). "
            f"The behaviour atoms are a MODEL-DRAWN artifact and the "
            f"between-draw sd is comparable to some of the differences this "
            f"table reports; one draw is not a measurement of a module.")
    if "95% ci" in low or "bootstrap" in low:
        if "noise floor" not in low:
            raise ModuleComparisonError(
                "a bootstrap interval was printed without the RE-DERIVED noise "
                "floor. An interval that excludes zero but sits below the "
                "floor is not a result on this data.")
        if "0.045" in low:
            raise ModuleComparisonError(
                "`0.045` is the EXPIRED 3-behaviour, 9-cell noise constant. It "
                "does not transfer to this panel and must be re-derived, not "
                "imported.")
    return True


def module_comparison_report(cmp: dict, notes=()) -> str:
    """THE side-by-side report, guards run on its own output before it returns.
    """
    out = [f"# Query modules, side by side — which one is actually better?", "",
           f"spec: **{cmp['spec_key']}** · cells: **{len(cmp['slugs'])}** · "
           f"atom draws: **{len(cmp['draws'])}**", "",
           comparison_bar_block(cmp)]
    for n in notes:
        out.append(n)
        out.append("")
    out.append(module_comparison_table(cmp))
    out.append(module_draw_table(cmp))
    out.append(module_bootstrap_block(cmp))
    out.append(comparison_verdict_block(cmp))
    md = "\n".join(out)
    check_module_comparison(md)
    check_bar_provenance(md, [{"slug": s, "panel": {
        "id": "comparison", "tier": cmp["tier"][s], "models": cmp["roster"],
        "label": "comparison"}} for s in cmp["slugs"]])
    return md


def comparison_verdict_block(cmp: dict) -> str:
    """The reading, stated plainly, computed from the table rather than typed.

    If the contract-compliant module is WORSE that is a real finding and this
    block says so — an honest negative is the whole reason to wire the module
    up rather than continue reporting the incumbent's number.
    """
    nf = cmp["noise_floor"]
    means = {m: _mean(module_row_values(cmp, m).values())
             for m in cmp["modules"]}
    ranked = sorted(means.items(), key=lambda kv: -kv[1])
    best = ranked[0][0]
    lines = ["### The reading", "",
             "Ordered by mean MCC over the cells (all draws):", ""]
    for m, v in ranked:
        lines.append(f"* **{QUERY_MODULE_CONTRACT[m][0]}** {v:+.4f} — "
                     f"{QUERY_MODULE_CONTRACT[m][1]}")
    lines.append("")
    compliant = [m for m in QUERY_MODULES if m != "relevance"]
    for m in compliant:
        if m not in means:
            continue
        d = cmp["deltas"].get((m, "relevance")) or cmp["deltas"].get(
            ("relevance", m))
        if d is None:
            continue
        sign = 1 if (m, "relevance") in cmp["deltas"] else -1
        mean, lo, hi = (sign * d[0], sign * min(d[1], d[2]),
                        sign * max(d[1], d[2]))
        if sign < 0:
            lo, hi = -max(d[1], d[2]), -min(d[1], d[2])
        excl = (lo > 0) or (hi < 0)
        over = abs(mean) > nf["half_width"]
        if mean > 0 and excl and over:
            verdict = (f"BETTER than the incumbent bag scorer by {mean:+.4f}, "
                       f"CI [{lo:+.4f}, {hi:+.4f}], which clears the "
                       f"{nf['half_width']:.4f} noise floor.")
        elif mean < 0 and excl and over:
            verdict = (f"**WORSE** than the incumbent bag scorer by {mean:+.4f}, "
                       f"CI [{lo:+.4f}, {hi:+.4f}], and the difference CLEARS "
                       f"the {nf['half_width']:.4f} noise floor. That is a real "
                       f"finding and is reported as one: wiring the compliant "
                       f"module up did not produce a better number.")
        else:
            verdict = (f"{mean:+.4f} against the incumbent, CI "
                       f"[{lo:+.4f}, {hi:+.4f}] — NOT distinguishable from it "
                       f"on this panel.")
        lines.append(f"* `{m}.py` is {verdict}")
    lines.append("")
    lines.append(
        f"On the mean the best predictor here is **{QUERY_MODULE_CONTRACT[best][0]}**. "
        f"Read it against the per-cell columns: the mean is the least "
        f"informative row of the table and the modules do not agree cell by "
        f"cell.")
    lines.append("")
    return "\n".join(lines)


def run_module_comparison(annotations=None, spec_key: str = DEFAULT_SPEC_KEY,
                          atom_draws=None, resamples: int = 1000,
                          modules=COMPARABLE_MODULES) -> str:
    """`--compare-modules`: the 9-behaviour panel, every module, one gold."""
    import panel_v2
    panel = panel_v2.load_panel(spec_keys=(spec_key,))
    notes = []
    if spec_key != "openai":
        notes.append(
            f"> **`{spec_key}` CANNOT run the ontology tier.** That side has "
            f"zero clause annotations, so `structural` and `section` fire on "
            f"nothing and `relevance` degenerates to bag-of-words. Every row "
            f"below is therefore THE LEXICAL CONTROL under another name and is "
            f"labelled so.")
    cmp = compare_query_modules(panel, spec_key=spec_key,
                                annotations=annotations,
                                atom_draws=atom_draws, modules=modules,
                                resamples=resamples)
    return module_comparison_report(cmp, notes=notes)


#: Which clause namespace each annotation artifact belongs to. An annotation
#: file keyed `m0001...` says nothing about `c001...`; handing it to the
#: constitution index would leave every clause unannotated while the run
#: reported "annotations: ok".
ANNOTATION_PREFIX = {"openai": "m", "anthropic": "c"}


def annotations_for_spec(annotations: dict, spec_key: str) -> dict:
    """The subset of `annotations` that names clauses of THIS spec."""
    if not annotations:
        return {}
    pref = ANNOTATION_PREFIX.get(spec_key, "")
    return {k: v for k, v in annotations.items() if str(k).startswith(pref)}


def run_panel_v2(annotations=None, behaviour_atoms=None, threshold=None,
                 spec_keys=("openai", "anthropic"), resamples: int = 1000,
                 query_module: str = DEFAULT_QUERY_MODULE) -> str:
    """Score every cell of panel v2 and render the report.

    The predictor is the LABEL-FREE lexical control unless clause annotations
    AND behaviour atoms are supplied for the cells in question. That is not a
    preference: the 9 new behaviours have no behaviour-atom artifact and the
    constitution has no clause annotations, so the full ontology tier is
    UNAVAILABLE offline and running it anyway would report a de-ontologised
    scorer under the tool's name — the exact failure `lexical_control.compare`
    was corrected for.

    `query_module` selects WHICH module answers the query — `relevance`,
    `structural` or `section`. It used to be `relevance`, unconditionally and
    invisibly, which is why the compliant modules had no headline number.
    """
    import lexical_control
    import panel_v2
    import relevance

    panel, prov = panel_v2.load_panel(spec_keys=spec_keys, with_provenance=True)
    published = panel_v2.published_panel(panel)
    ann = relevance.load_annotations(annotations) if annotations else {}
    batoms = relevance.load_behaviour_atoms(behaviour_atoms) if behaviour_atoms else {}

    notes, preds, label = [], {}, "lexical control (label-free, definition text only)"
    missing_atoms = sorted(s for s in panel if s not in batoms)
    for key in spec_keys:
        clauses, _ = clauses_for_spec(key)
        ann_k = annotations_for_spec(ann, key)
        ontology_ok = bool(ann_k) and not missing_atoms
        if query_module != DEFAULT_QUERY_MODULE:
            # The typed modules have NO lexical fallback: with no clause
            # annotations they fire on nothing. Running them anyway would
            # report an empty predictor under the module's name.
            if not ontology_ok:
                notes.append(
                    f"> **`{key}` cannot run `{query_module}`** — clause "
                    f"annotations: {len(ann_k)}; behaviour atoms missing for "
                    f"{len(missing_atoms)} of {len(panel)} behaviours. The "
                    f"typed modules have no lexical fallback, so this side "
                    f"falls back to the labelled lexical control.")
            else:
                qm = build_query_module(query_module, panel, clauses,
                                        annotations=ann_k,
                                        atoms=behaviour_atoms)
                label = f"{qm.label} — {qm.contract}"
                for slug, b in panel.items():
                    if key in (b.get("coverage") or {}):
                        preds[(slug, key)] = qm.predict(slug)
                continue
        weights = (relevance.Weights() if ontology_ok
                   else lexical_control.CONTROL_WEIGHTS)
        idx = relevance.RelevanceIndex(clauses, ann_k if ontology_ok else {},
                                       weights)
        for slug, b in panel.items():
            if key not in (b.get("coverage") or {}):
                continue
            q = relevance.behaviour_from_panel(b, batoms if ontology_ok else None)
            preds[(slug, key)] = idx.predict(q, threshold)
        if ontology_ok and query_module == DEFAULT_QUERY_MODULE:
            label = "{} — {}".format(*QUERY_MODULE_CONTRACT["relevance"])
        if not ontology_ok:
            notes.append(
                f"> **`{key}` runs as the LEXICAL CONTROL, not the tool.** "
                f"clause annotations for this spec: "
                f"{len(ann_k)} clause(s); behaviour atoms missing for "
                f"{len(missing_atoms)} of {len(panel)} behaviours "
                f"({', '.join(missing_atoms) or 'none'}). With either input "
                f"absent the atom channel is multiplied by zero and the result "
                f"is a bag-of-words baseline; it is labelled as one rather than "
                f"reported as the tool.")

    true_ev = cell_results(panel, preds, spec_keys)
    pub_ev = cell_results(published, preds, spec_keys)

    vecs, floor_vecs = {}, {}
    for k in true_ev:
        b, key = panel[k[0]], k[1]
        joins = clause_joins(b, clauses_for_spec(key)[0], key)
        vecs[k] = cell_vectors(b, lift(preds[k], joins), key)
        # FLOOR B as a predictor, so the comparison is paired on the same
        # passages rather than being a difference of two summary numbers.
        floor_vecs[k] = cell_vectors(b, joinable(joins), key)
    nf = noise_floor(vecs, resamples=resamples)
    vs_floor = paired_bootstrap_cells(vecs, floor_vecs, resamples=resamples)
    cost = panel_v2.truncation_cost()
    tail = [bootstrap_block(vs_floor, label,
                            "FLOOR B (predict every joinable passage)", nf)]

    # The FRONTIER panel, same predictor, scored SEPARATELY. Its 3 behaviours
    # are the only ones that can carry the bar; the point of printing them here
    # is that the reader can see the small-model cells against the real one
    # without either being averaged into the other.
    frontier = load_true_panel()
    fpreds = {}
    for key in spec_keys:
        clauses, _ = clauses_for_spec(key)
        idx = relevance.RelevanceIndex(clauses, {},
                                       lexical_control.CONTROL_WEIGHTS)
        for slug, b in frontier.items():
            if key in (b.get("coverage") or {}):
                fpreds[(slug, key)] = idx.predict(
                    relevance.behaviour_from_panel(b), threshold)
    frontier_ev = cell_results(frontier, fpreds, spec_keys)

    return panel_v2_report(panel, true_ev, pub_ev, label, nf=nf, prov=prov,
                           cost=cost, notes=notes, tail_blocks=tail,
                           frontier_results=frontier_ev,
                           frontier_behaviours=frontier)


def lift_for_cell(behaviour, spec_key: str, predicted_clause_ids) -> set:
    """Predicted clause ids -> predicted PASSAGE ids, for one cell."""
    clauses, _ = clauses_for_spec(spec_key)
    return lift(predicted_clause_ids, clause_joins(behaviour, clauses, spec_key))


def vocabulary_block(index, top: int = 15) -> str:
    """Top atoms by clause count. If the head of this list covers most of the
    corpus the vocabulary has collapsed into stopwords and the atom channel is
    worthless — which is visible here and nowhere else in the report."""
    vocab = index.vocabulary(top)
    if not vocab:
        return ("_no annotation artifact loaded — the atom channel is inert and "
                "the tool is running as a pure lexical baseline._\n")
    n = len(index.ids) or 1
    lines = ["**Atom vocabulary — top %d by clause count.** An atom on a large "
             "fraction of clauses is a stopword; those above the cutoff are "
             "floored to zero weight." % top, "",
             "| atom | n_clauses | share | stopworded |",
             "| --- | ---: | ---: | --- |"]
    for name, df in vocab:
        lines.append(f"| `{name}` | {df} | {df / n:.1%} | "
                     f"{'yes' if name in index.atom_stopwords else ''} |")
    lines.append("")
    lines.append(f"distinct atoms: {len(index.atom_df)}; "
                 f"stopworded: {len(index.atom_stopwords)}")
    lines.append("")
    return "\n".join(lines)


USAGE = """Behavioural-relevance benchmark — tool vs the best single judge.

  benchmark.py                          panel bar + join ledger, no tool
  benchmark.py --tool                   run relevance.py and score it (THE table)
  benchmark.py --control                same, as the ontology-free lexical control
  benchmark.py --sweep                  threshold curve, every point
  benchmark.py --ablate                 per-channel ablation
  benchmark.py --operating-point        label-free cut vs LOBO vs oracle vs floors
  benchmark.py --panel-v2               ALL 18 CELLS of the small-model panel
                                        (9 behaviours x 2 specs). Label-free
                                        control unless BOTH --annotations and
                                        --behaviour-atoms are given for the
                                        cells being scored. This panel is POWER,
                                        NOT A BAR — see `panel_v2`.
  benchmark.py --compare-modules        relevance vs structural vs section vs
                                        the lexical control vs BOTH floors vs
                                        the judges, as ROWS on the same cells,
                                        every atom draw, paired-bootstrap CIs
  benchmark.py preds.json               score a prediction file {slug: [clause_id]}

Options (any mode):
  --query-module NAME  WHICH module answers the query: relevance | structural |
                       section  (default: relevance). Usable with --tool and
                       --panel-v2. Until this flag existed every mode routed
                       through relevance.py, so the two invariant-10-compliant
                       modules could not produce a headline number at all.
  --annotations PATH   clause annotations from annotate.py   (default: none)
  --behaviour-atoms PATH   query-side atoms from behavior_atoms.py
                       (default: behavior_atoms.json; without it the atom
                        channel is INERT and every score is a lexical baseline)
  --spec-key KEY       which spec the comparison runs on (default: openai).
                       The constitution has ZERO clause annotations, so on
                       `anthropic` every module IS the lexical control.
  --threshold X        operating point. DEFAULT: none — the cut is derived from
                       each query's own score distribution (Otsu). The fitted
                       constant is retired and is not the default.
  --spec PATH          spec markdown, for zero-match strata. Defaults to the
                       OpenAI Model Spec; MUST be set when scoring another spec
                       or misses are diagnosed against the wrong document.
  --clauses PATH       clause file (default: modelspec_clauses.json)
  --universe true|published
                       which judged universe the HEADLINE is computed on
                       (default: true — all 589 passages the panel graded).
                       Both are always printed with the delta; this flag only
                       chooses which one the headline tables lead with.
"""


#: Modes whose machinery is specific to the bag scorer: `--ablate` reads
#: per-CHANNEL weights, `--sweep` and `--operating-point` read a THRESHOLD
#: curve. `structural`/`section` have neither — that is what invariant-10
#: compliance costs them — so these modes REFUSE another module rather than
#: silently running relevance under its name.
RELEVANCE_ONLY_MODES = ("sweep", "ablate", "operating-point", "control")


def _parse_args(argv):
    opts = {"mode": "bar", "annotations": None, "behaviour_atoms": None,
            "threshold": None, "spec": None, "clauses": CLAUSES, "preds": None,
            "universe": DEFAULT_UNIVERSE, "query_module": DEFAULT_QUERY_MODULE,
            "spec_key": DEFAULT_SPEC_KEY}
    flags = {"--annotations": "annotations", "--behaviour-atoms": "behaviour_atoms",
             "--threshold": "threshold", "--spec": "spec", "--clauses": "clauses",
             "--universe": "universe", "--query-module": "query_module",
             "--spec-key": "spec_key"}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in flags:
            if i + 1 >= len(argv):
                raise SystemExit(f"{a} needs a value\n\n{USAGE}")
            opts[flags[a]] = argv[i + 1]
            i += 2
            continue
        if a in ("-h", "--help"):
            raise SystemExit(USAGE)
        if a.startswith("--"):
            mode = a[2:]
            if mode not in ("tool", "control", "sweep", "ablate",
                            "operating-point", "panel-v2", "compare-modules"):
                raise SystemExit(f"unknown mode {a!r}\n\n{USAGE}")
            opts["mode"] = mode
            i += 1
            continue
        opts["preds"] = a
        i += 1
    if opts["threshold"] is not None:
        opts["threshold"] = float(opts["threshold"])
    if opts["universe"] not in UNIVERSE_LABEL:
        raise SystemExit(f"--universe must be one of {sorted(UNIVERSE_LABEL)}\n\n{USAGE}")
    if opts["query_module"] not in QUERY_MODULES:
        raise SystemExit(f"--query-module must be one of {list(QUERY_MODULES)}\n\n"
                         f"{USAGE}")
    if (opts["query_module"] != DEFAULT_QUERY_MODULE
            and opts["mode"] in RELEVANCE_ONLY_MODES):
        raise SystemExit(
            f"--{opts['mode']} reads per-channel weights and threshold sweeps "
            f"that only relevance.py has, so it supports only "
            f"--query-module relevance. Score {opts['query_module']!r} with "
            f"--tool, --panel-v2 or --compare-modules.\n\n{USAGE}")
    if opts["spec_key"] not in SPEC_CLAUSES:
        raise SystemExit(f"--spec-key must be one of {sorted(SPEC_CLAUSES)}\n\n"
                         f"{USAGE}")
    return opts


def main(argv=None):
    import lexical_control
    import relevance

    opts = _parse_args(list(argv if argv is not None else sys.argv[1:]))
    if opts["mode"] == "compare-modules":
        print(run_module_comparison(annotations=opts["annotations"],
                                    spec_key=opts["spec_key"],
                                    atom_draws=([opts["behaviour_atoms"]]
                                                if opts["behaviour_atoms"]
                                                else None)))
        return
    if opts["mode"] == "panel-v2":
        print(run_panel_v2(annotations=opts["annotations"],
                           behaviour_atoms=opts["behaviour_atoms"],
                           threshold=opts["threshold"],
                           query_module=opts["query_module"]))
        return
    clauses, src = load_clauses(opts["clauses"])
    # THE DEFAULT IS THE TRUE UNIVERSE. `published` is reachable for the
    # side-by-side only; nothing here may emit a headline on it alone.
    published = load_panel()
    behaviours, provenance = load_true_panel(with_provenance=True)
    if opts["universe"] == "published":
        behaviours = published
    # The spec path is a PARAMETER. Hardcoding the OpenAI spec would make every
    # constitution miss read as `not_verbatim_in_source` against the wrong
    # document — a coverage bug disguised as a segmentation bug.
    spec = spec_text(opts["spec"]) if opts["spec"] else spec_text()

    for slug, b in behaviours.items():
        v = verify_verdicts(b)
        if v["mismatch"] or v["missing_verdicts"]:
            raise SystemExit(
                f"panel data integrity failure in {slug}: score != "
                f"sum(verdicts) for {v['mismatch'][:5]} — refusing to score")

    def emit(predictions, scores=None, curves=None, source=src):
        print(dual_report(predictions=predictions, clauses=clauses,
                          behaviours=behaviours,
                          published_behaviours=published, spec=spec,
                          scores=scores, curves=curves, clause_source=source,
                          provenance=provenance))

    if opts["preds"]:
        with open(opts["preds"]) as f:
            predictions = {k: set(v) for k, v in json.load(f).items()}
        emit(predictions)
        return

    if opts["mode"] == "bar":
        emit({slug: set() for slug in behaviours})
        return

    # ANY QUERY MODULE, THE SAME REPORT. `structural` and `section` reach the
    # headline table through here; before this branch existed they could not
    # produce a headline number at all, and every number the project reported
    # came from the module the contract calls scheduled for replacement.
    if opts["query_module"] != DEFAULT_QUERY_MODULE:
        import structural
        qm = build_query_module(
            opts["query_module"], behaviours, clauses,
            annotations=(relevance.load_annotations(opts["annotations"])
                         if opts["annotations"] else {}),
            atoms=opts["behaviour_atoms"] or structural.BEHAVIOUR_ATOMS)
        predictions = {slug: qm.predict(slug) for slug in qm.slugs}
        ranked = {slug: qm.rank(slug) for slug in qm.slugs}
        joins = {slug: clause_joins(b, clauses)
                 for slug, b in behaviours.items() if slug in ranked}
        emit(predictions,
             scores={s: passage_scores(ranked[s], joins[s]) for s in ranked},
             curves={s: mcc_curve(behaviours[s], ranked[s], clauses,
                                  joins=joins[s]) for s in ranked},
             source=f"{src} — {qm.label} ({qm.contract})")
        return

    weights = (lexical_control.CONTROL_WEIGHTS if opts["mode"] == "control"
               else relevance.Weights())
    ann = (relevance.load_annotations(opts["annotations"])
           if opts["annotations"] and opts["mode"] != "control" else {})
    queries = ({slug: relevance.behaviour_from_panel(b) for slug, b in behaviours.items()}
               if opts["mode"] == "control"
               else relevance.behaviours_from_panel(behaviours,
                                                    opts["behaviour_atoms"]))
    idx = relevance.RelevanceIndex(clauses, ann, weights)

    if opts["mode"] == "ablate":
        print(ablate(behaviours, clauses, queries, weights, ann, spec))
        print(vocabulary_block(idx))
        return

    if opts["mode"] == "operating-point":
        import threshold as T
        ranked = {slug: dict(idx.rank(q)) for slug, q in queries.items()}
        joins = {slug: clause_joins(b, clauses) for slug, b in behaviours.items()}
        # Two rules that need more than one score vector or a corpus statistic,
        # so they cannot live in `threshold.RULES`. Both are label-free: the
        # first re-queries with independently drawn behaviour atoms, the second
        # sets a prediction BUDGET to the number of clauses sharing any atom
        # with the query — a property of the annotation index, not of the panel.
        extra = {}
        draw_scores = []
        for path in ATOM_DRAWS:
            p = os.path.join(HERE, path)
            if not os.path.exists(p):
                continue
            qs = relevance.behaviours_from_panel(behaviours, p)
            draw_scores.append({s: dict(idx.rank(q)) for s, q in qs.items()})
        if len(draw_scores) >= 2:
            extra["stability(%d draws)" % len(draw_scores)] = {
                s: T.stability([d[s] for d in draw_scores if s in d])
                for s in ranked}
        budget = {}
        for slug, q in queries.items():
            names = {a["name"] for a in q.norm_atoms}
            k = sum(1 for cid in idx.ids if idx._names[cid] & names)
            budget[slug] = T.top_k(ranked[slug], k) if k else T.DEGENERATE_CUT
        extra["atom_support_budget"] = budget

        print(operating_point_block(behaviours, ranked, joins, clauses,
                                    extra_cuts=extra))
        return

    if opts["mode"] == "sweep":
        sweeps = {slug: idx.sweep(q) for slug, q in queries.items()}
        print(sweep_report(behaviours, clauses, sweeps, spec, label=opts["mode"]))
        print(vocabulary_block(idx))
        return

    # LABEL-FREE BY DEFAULT. This used to fall back to
    # `relevance.DEFAULT_THRESHOLD` = 0.18 — the in-sample argmax of a 51-point
    # grid ON THE PANEL THIS REPORT SCORES AGAINST, i.e. a live invariant-9
    # violation. Retiring it in `predict`'s default argument while this line
    # still passed the constant made the retirement COSMETIC: every number the
    # default `benchmark.py` path emitted was the fitted one, worth +0.042 mean
    # MCC (+0.320 vs +0.278) and +0.094 on harm-avoidance, under docs claiming
    # the constant was retired. `threshold=None` derives the cut from each
    # query's own score distribution (Otsu).
    thr = opts["threshold"]
    predictions = {slug: idx.predict(q, thr) for slug, q in queries.items()}
    # Threshold-free companions: the continuous score (for ROC/AUC at each
    # judge's own operating point) and the whole threshold curve (so the MCC is
    # reported as a band, never as a point estimate).
    ranked = {slug: dict(idx.rank(q)) for slug, q in queries.items()}
    joins = {slug: clause_joins(b, clauses) for slug, b in behaviours.items()}
    scores = {slug: passage_scores(ranked[slug], joins[slug])
              for slug in behaviours if slug in ranked}
    curves = {slug: mcc_curve(b, ranked[slug], clauses, joins=joins[slug])
              for slug, b in behaviours.items() if slug in ranked}
    emit(predictions, scores=scores, curves=curves,
         source=f"{src} @ threshold {thr} ({opts['mode']})")
    print(vocabulary_block(idx))
    if not idx.atom_df or not any(q.atoms for q in queries.values()):
        print("\n> **The atom channel was INERT for this run** — the numbers "
              "above are a lexical baseline, not an ontology result.\n")


if __name__ == "__main__":
    main()
