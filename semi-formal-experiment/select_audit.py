"""The SELECT step's missing instrument: roster builder + verdict validator.

Two directional tests for a behaviour's query-atom selection (the sandwich's
deterministic legs; the judgment seat is briefs/select_audit.md, run by a
small model):

  SWEEP  (sufficient direction): every vocabulary atom is judged against the
         behaviour definition — "is this an instance of what the definition
         describes?" — WITHOUT seeing the current selection. The validator
         then diffs sweep verdicts against the actual query atoms. An atom
         judged in-scope but unselected is a selection-recall finding; a
         selected atom judged out-of-scope is an over-selection finding.
         Reconstruction tests cannot catch the first class: a definition's
         text does not enumerate its own extension, so the only way to find
         a missing instance is to sweep the vocabulary, not re-read the
         definition.
  READBACK (faithful direction): the selected atoms alone, rendered as a
         list, compared against the definition text for over-assertion and
         for stated definition content with no covering atom. (Seat 2 in the
         same brief.)

DIAGNOSTIC-ONLY and panel-free: reads the annotation artifact, the query-side
behaviour definitions and the behaviour-atom artifact. Never a panel file.
Tested by test_select_audit.py (debt paid 2026-08-03, same day).
"""
from __future__ import annotations

import argparse
import collections
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ANNOTATIONS = os.path.join(HERE, "annotations_ext_v1_merged.json")
QUERIES = os.path.join(HERE, "behaviours_query.json")
BEHAVIOUR_ATOMS = os.path.join(HERE, "behavior_atoms_ext_v1.json")


def build_rosters(annotations_path=ANNOTATIONS, queries_path=QUERIES,
                  out_dir="select_audit"):
    """One roster file per behaviour: definition + the FULL vocabulary.

    Deliberately does NOT include the current query selection — the sweep
    seat must judge scope blind to what was chosen, or its verdicts anchor.
    """
    raw = json.load(open(annotations_path))
    vocab = {}
    for a in raw["atoms"]:
        v = vocab.setdefault(a["name"], {"name": a["name"],
                                         "kinds": set(), "gloss": a["gloss"]})
        v["kinds"].add(a.get("kind", ""))
    atoms = [{"name": v["name"], "kinds": sorted(v["kinds"]),
              "gloss": v["gloss"]} for v in vocab.values()]
    atoms.sort(key=lambda x: x["name"])

    os.makedirs(out_dir, exist_ok=True)
    q = json.load(open(queries_path))
    paths = []
    for b in q["behaviours"]:
        roster = {"behaviour": b["slug"], "definition": b.get("definition", ""),
                  "n_atoms": len(atoms), "atoms": atoms}
        p = os.path.join(out_dir, f"roster_{b['slug']}.json")
        json.dump(roster, open(p, "w"), indent=1)
        paths.append(p)
        assert len(roster["atoms"]) == len({a["name"] for a in atoms})
    return paths


def _score_of(v):
    """v2 verdicts carry {"score": 0|1|2|3}; the 2026-08-03 legacy files carry
    {"in_scope": bool}, mapped to 3/0 so the recorded run stays loadable.
    Returns None for malformed. (bool is an int subclass — reject it as a
    score explicitly.)"""
    if "score" in v:
        s = v["score"]
        return s if (isinstance(s, int) and not isinstance(s, bool)
                     and 0 <= s <= 3) else None
    if isinstance(v.get("in_scope"), bool):
        return 3 if v["in_scope"] else 0
    return None


def validate_sweep(roster_path, verdict_path, atoms_path=BEHAVIOUR_ATOMS,
                   budget=None):
    """Coverage-check a sweep verdict file, then diff against the selection.

    v2 CALIBRATION CONTRACT (2026-08-03: binary self-calibrated sweeps
    returned 32-47% of the vocabulary in-scope — unusable as a worklist):
    the seat SCORES each atom 0-3; only score 3 ("would belong in the query")
    is actionable; scores 1-2 are reported as strata, never as findings. With
    `budget=K`, a file carrying more than K score-3 verdicts is a MEASURED
    SEAT MISCALIBRATION: reported loudly, worklist refused — never silently
    truncated to an arbitrary subset.
    """
    roster = json.load(open(roster_path))
    verd = json.load(open(verdict_path))
    names = [v.get("name") for v in verd]
    dupes = [n for n, c in collections.Counter(names).items() if c > 1]
    roster_names = {a["name"] for a in roster["atoms"]}
    missing = sorted(roster_names - set(names))
    unknown = sorted(set(names) - roster_names)
    scores = {v.get("name"): _score_of(v) for v in verd}
    bad = [n for n, s in scores.items() if s is None]
    ok = not (dupes or missing or unknown or bad)
    print(f"--- sweep {roster['behaviour']}: {len(verd)} verdicts; "
          f"dupes {len(dupes)}, missing {len(missing)}, unknown {len(unknown)}, "
          f"malformed {len(bad)} -> {'CLEAN' if ok else 'INVALID'}")
    if not ok:
        return None
    strata = {str(k): sum(1 for s in scores.values() if s == k)
              for k in (3, 2, 1, 0)}
    core = {n for n, s in scores.items() if s == 3}
    over = budget is not None and len(core) > budget
    ba = json.load(open(atoms_path))
    sel = {a["name"] for a in ba[roster["behaviour"]]["atoms"]}
    findings = {
        "behaviour": roster["behaviour"],
        "strata": strata, "n_score3": len(core), "n_selected": len(sel),
        "budget": budget, "over_budget": over,
        "in_scope_unselected": [] if over else sorted(core - sel),
        "selected_marked_out_of_scope": [] if over else sorted(sel - core),
    }
    if over:
        print(f"    OVER BUDGET: {len(core)} score-3 verdicts against a "
              f"budget of {budget} — the seat is miscalibrated; worklist "
              f"REFUSED (re-run the seat, do not truncate).")
    else:
        print(f"    score-3 {len(core)} | selected {len(sel)} | "
              f"CORE BUT UNSELECTED {len(findings['in_scope_unselected'])} | "
              f"selected-but-not-core "
              f"{len(findings['selected_marked_out_of_scope'])}")
    return findings


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("rosters")
    v = sub.add_parser("validate")
    v.add_argument("--roster", required=True)
    v.add_argument("--verdict-file", required=True)
    v.add_argument("--out", default=None)
    v.add_argument("--budget", type=int, default=None)
    args = ap.parse_args()
    if args.cmd == "rosters":
        for p in build_rosters():
            print("wrote", p)
    else:
        f = validate_sweep(args.roster, args.verdict_file,
                           budget=args.budget)
        if f and args.out:
            json.dump(f, open(args.out, "w"), indent=1)
            print("findings ->", args.out)


if __name__ == "__main__":
    main()
