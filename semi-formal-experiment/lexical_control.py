"""CONTROL: how far does a dumb lexical baseline get, with no ontology at all?

This is the number the ontology has to beat. Score each clause by IDF-weighted
token overlap between the behaviour's own definition text and the clause quote —
no atoms, no query expansion, no section proximity, no extraction. Whatever F1
that reaches is the floor any ontology must clear to have earned its cost.
Reporting an ontology F1 without this control would let an unimpressive result
read as a success.

The control is deliberately implemented as a WEIGHT SETTING of the very same
scorer (`relevance.RelevanceIndex`), not as a second scoring script. Same
tokenizer, same stemmer, same clause join, same evaluation protocol — so the
control-vs-tool difference is exactly the ontology's contribution and cannot
drift into an artifact of two divergent implementations.

Everything is measured on the pair-gold protocol from `benchmark.py`:
gold = both other judges rated the passage relevant; the tool and each judge
are scored against the identical three pair-golds, at passage level, on the
behaviour's full passage list.

    .venv/bin/python lexical_control.py            # control vs tool vs bar
"""
from __future__ import annotations

import benchmark
import relevance

#: No atoms, no kinds, no section smoothing, no pseudo-relevance feedback.
#: Bag-of-words against the clause quote, and nothing else.
CONTROL_WEIGHTS = relevance.Weights(
    lex=1.0, atom=0.0, kind=0.0, section=0.0,
    expansion_docs=0, expansion_terms=0,
)


def control_index(clauses, weights: relevance.Weights = CONTROL_WEIGHTS):
    """The control explicitly gets NO annotations — that is what makes it the
    control."""
    return relevance.RelevanceIndex(clauses, annotations={}, weights=weights)


def best_point(index, behaviour, evaluator, budget: int | None = None,
               key: str = "mcc") -> dict:
    """Best point over the threshold sweep, ranked by `key`.

    Two corrections over the naive version, both load-bearing:

    BUDGET. Swept freely on F1, BOTH lexical controls select the DEGENERATE
    threshold — the minimum, in 5 of 6 cells — and collapse into the
    predict-everything predictor, adding exactly 0.000 over the floor. At a
    24-47% positive rate no lexical filter's precision gain pays for its recall
    loss under F1, so "best F1" is a synonym for "predict everything". Capping
    the predicted-positive count at the tool's own budget makes the degenerate
    point unreachable and the comparison a real one.

    KEY. Ranking on MCC rather than F1 by default, because MCC's floor is 0 for
    the degenerate predictor and F1's is not.
    """
    best = None
    for t, pred in index.sweep(behaviour):
        if not pred:
            continue
        if budget is not None and len(pred) > budget:
            continue
        ev = evaluator(pred)
        row = {"threshold": t, "n": len(pred), **ev}
        if best is None or row[key] > best[key]:
            best = row
    return best or {"threshold": 1.0, "n": 0, "f1_full": 0.0, "mcc": 0.0,
                    "f1_matched": 0.0, "floor": 0.0, "bar": 0.0, "lift": 0.0,
                    "precision": 0.0, "recall": 0.0, "judge_mean": 0.0}


def compare(clauses=None, annotations=None, spec: str | None = None,
            behaviour_atoms=None) -> list:
    """One row per behaviour: control (oracle threshold) vs tool (oracle
    threshold) vs FLOOR vs bar. Returns dicts; `render` formats them.

    ⚠️ `behaviour_atoms` is REQUIRED for the "tool" row to mean anything.
    This function used to call `relevance.behaviour_from_panel(b)` with no
    atoms, so every "tool" row ran with an EMPTY query-atom set — the atom
    channel contributed 0.0 and the row was a de-ontologised scorer. The
    module docstring claims the control-vs-tool difference "is exactly the
    ontology's contribution"; with no atoms it was only the clause-side gloss
    text folded into the lexical vectors, plus the section channel. The
    ATOM-CHANNEL-DISABLED warning fired three times per run and the table was
    rendered anyway.
    """
    if clauses is None:
        clauses, _ = benchmark.load_clauses()
    if spec is None:
        spec = benchmark.spec_text()
    # THE TRUE UNIVERSE. This was `benchmark.load_panel()` — the PUBLISHED
    # universe — while `benchmark.DEFAULT_UNIVERSE == "true"`. It was the only
    # production module still on the truncated universe, and it produces a
    # headline-bearing table ("the ontology's contribution"), so it printed a
    # mixed-universe result indefinitely. The sign of that contribution FLIPS
    # between universes on harm-avoidance: published control +0.371 beats tool
    # +0.358; on the true universe the control LOSES, +0.418 vs +0.444.
    behaviours = benchmark.load_universe_panel()

    # Refuse rather than mislead. The CONTROL side legitimately has no atoms —
    # that is what makes it a control — so we cannot key this off the global
    # warning list, which the control's own ranking populates. Check the TOOL
    # side's inputs directly instead.
    batoms = relevance.load_behaviour_atoms(behaviour_atoms)
    if not batoms or not annotations:
        raise SystemExit(
            "REFUSING TO RUN: the 'tool' column needs BOTH clause annotations "
            "and behaviour atoms. Without them it is a de-ontologised scorer "
            "and the control-vs-tool difference is NOT the ontology's "
            "contribution — which is the only thing this table exists to show. "
            f"(annotations={'ok' if annotations else 'MISSING'}, "
            f"behaviour_atoms={'ok' if batoms else 'MISSING'})")

    ctrl = control_index(clauses)
    tool = relevance.RelevanceIndex(clauses, annotations)

    rows = []
    for slug, b in behaviours.items():
        joins = benchmark.clause_joins(b, clauses)
        q = relevance.behaviour_from_panel(b, batoms)

        def ev(pred, b=b, joins=joins):
            e = benchmark.evaluate(b, pred, clauses, spec, joins=joins)
            n = max(1, len(e["per_target"]))
            return {
                "mcc": e["tool_mcc_mean_full"],
                "judge_mcc": e["judge_mcc_mean_full"],
                "lift": e["tool_mean_full"] - e["floor_mean"],
                "usable": e["headline_usable"],
                "f1_full": e["tool_mean_full"],
                "f1_matched": e["tool_mean_matched"],
                "precision": sum(r["full"]["precision"]
                                 for r in e["per_target"].values()) / n,
                "recall": sum(r["full"]["recall"]
                              for r in e["per_target"].values()) / n,
                "floor": e["floor_mean"],
                "bar": e["judge_best_full"],
                "judge_mean": e["judge_mean_full"],
            }

        # The control gets the TOOL's prediction budget, so it cannot win by
        # collapsing into the all-relevant predictor.
        tool_pt = best_point(tool, q, ev)
        rows.append({"behaviour": slug,
                     "tool": tool_pt,
                     "control": best_point(ctrl, q, ev,
                                           budget=tool_pt["n"] or None)})
    return rows


def render(rows) -> str:
    out = ["## Control vs tool (pair-gold protocol, passage level)", "",
           "Computed on the **TRUE universe** (589 passages — every passage the "
           "panel actually graded), not the published 377/333/153 subset. This "
           "table was on the published universe until it was caught: the sign "
           "of the ontology's contribution FLIPS between them on "
           "harm-avoidance (published: control +0.371 beats tool +0.358; true: "
           "control +0.418 loses to tool +0.444 — a **delta** of +0.047 on the "
           "control and +0.086 on the tool, and a sign change on the "
           "contribution itself).", "",
           "**MCC is primary** — 0 by construction for a degenerate predictor. "
           "F1 appears only as LIFT OVER FLOOR, never as an absolute: swept "
           "freely on absolute F1 both controls select the degenerate "
           "threshold and add exactly 0.000 over the floor, so an absolute "
           "control F1 of 0.45-0.56 measures the base rate and nothing else. "
           "The control is capped at the tool's own prediction budget so it "
           "cannot reach the degenerate point.", "",
           "| behaviour | method | thr | n | MCC | judge MCC | F1 lift over "
           "floor | F1 (abs) | FLOOR | judge F1 (mean LOO) | headline usable |",
           "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
    for r in rows:
        for method in ("control", "tool"):
            m = r[method]
            out.append(
                f"| {r['behaviour']} | {method} | {m['threshold']:.2f} | {m['n']} "
                f"| **{m.get('mcc', 0.0):+.3f}** | {m.get('judge_mcc', 0.0):+.3f} "
                f"| {m.get('lift', 0.0):+.3f} "
                f"| {m['f1_full']:.3f} | {m['floor']:.3f} "
                f"| {m.get('judge_mean', 0.0):.3f} "
                f"| {'yes' if m.get('usable') else '**NO**'} |")
    out.append("")
    out.append("If the tool cannot clearly beat the FLOOR it has learned "
               "nothing; if it cannot beat the CONTROL it has not earned the "
               "cost of extraction.")
    out.append("")
    return "\n".join(out)


def main(argv=None):
    import sys
    import os
    argv = list(argv if argv is not None else sys.argv[1:])
    here = os.path.dirname(os.path.abspath(__file__))
    ann_path = argv[0] if argv else os.path.join(here, "annotations_b8.json")
    batoms_path = (argv[1] if len(argv) > 1
                   else os.path.join(here, "behavior_atoms_b8.json"))
    ann = relevance.load_annotations(ann_path)
    md = render(compare(annotations=ann, behaviour_atoms=batoms_path))
    benchmark.check_report_pairing(md)
    # This table emits a headline; it must name the universe it was computed
    # on. `check_universe_pairing` existed and simply was not called here,
    # which is how the published-universe numbers above went unnoticed.
    benchmark.check_universe_pairing(md)
    print(md)


if __name__ == "__main__":
    main()
