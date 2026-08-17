#!/usr/bin/env python3
"""F3 — the mis-routing detector. Deterministic, offline, zero API.

    ../../../semi-formal-experiment/.venv/bin/python \
        _debug_gen11/fix_matrix/f3_misrouting.py

⛔ READ-ONLY over `resolve_runs/`. Writes nothing anywhere.

────────────────────────────────────────────────────────────────────────────
THE MECHANISM — and the correction to the brief
────────────────────────────────────────────────────────────────────────────
The brief calls this "draws answering another clause's prompt". MEASURED, it
is not. Every draw answered the prompt it was handed: scoring all 367 draws
for token overlap between the module produced and the ESTABLISHES text of its
OWN stored prompt puts every draw on every affected clause at 0.44-1.00
against a corpus floor of 0.06. `translate.py`'s `--clause` selection is
exonerated -- per-clause `user_sha` matches the prompt bytes on disk in every
run. NOT a model defect and NOT a selection bug.

What is actually wrong is that CLAUSE IDS ARE POSITIONAL AND NOT VERSIONED:

  * `resolve_runs/graph_v2/node_corpus.py:53-63  asp_id()` builds
    `l{band_start}_{band_end}_n{index_in_band}` -- nothing content-derived.
  * `node_corpus.py:111` writes the locator with `graph_v2@2026-08-10`
    HARDCODED, identical for every vintage of the decomposition.
  * `node_corpus.py:147-149` records `source_sha256` of the model-spec
    markdown and NO graph/decomposition identity at all. So two corpora that
    disagree about what `l1_170_n028` is carry byte-identical provenance.
  * `node_corpus.py:141,152` -- `--graph` is switchable but the output path is
    the fixed `node_corpus.json`, overwritten in place, destroying the prior
    vintage. Its mtime is AFTER every run that consumed it.

Re-decomposing moves band boundaries and renumbers `n`-indices. Most ids are
accidentally protected because the band prefix moves too (`l171_203` ->
`l171_426`). **`l1_170` is the one band identical in every vintage** -- it is
always the first band. MEASURED: all five affected clauses are `l1_170_*` and
no clause in any other band is affected. Concrete proof of renumbering: the
authority-hierarchy node is `l1_170_n028` in `node_corpus.json` and
`l1_170_n042` in `node_corpus_all.json`.

The SYMPTOM is manufactured downstream, at
`_debug_gen11/flip_classify/extract_flips.py:40-42`, which groups draws on the
bare clause id and ignores `user_sha` -- even though it RECORDS `user_sha` at
line 69. `_debug_gen11/d1_recruit/census.py:208` keys on
`(clause, system_sha, user_sha)` and gets it right; `extract_flips.py` did not
inherit that keying, and `census.py:193-195` has the same gap behind the
"112 multi-draw clauses" figure.

────────────────────────────────────────────────────────────────────────────
CORRECTION TO THE BRIEF'S COUNT
────────────────────────────────────────────────────────────────────────────
The brief says four clauses. MEASURED: **five**, and not the four named.
`l1_170_n016` and `l1_170_n028` are mis-routings; `l1_170_n017`, `l1_170_n026`
and `l1_170_n060` are newly found and never reached `verdicts.json` because
they happened not to flip shape. The other three `INSTRUMENT-ARTIFACT`
verdicts (`l3384_3501_n007`, `l797_809_n001`, `l810_919_n014`) have IDENTICAL
ESTABLISHES across their draws and differ only in `system_sha` -- a
prompt-version difference, correctly labelled, and a different phenomenon.

Of the 33 flips, **2 are pure artefacts of the pooling**: remove the alien
draw from `l1_170_n016` and `l1_170_n028` and no flip remains.

────────────────────────────────────────────────────────────────────────────
THE FIX — described, NOT applied
────────────────────────────────────────────────────────────────────────────
No guard-watched file is touched by any of it (`prompt/*.md`, `schema.py`,
`resources/03_pipeline.md`, `resolve_runs/graph_v2/node_*.md` and `seats.py`
are all out of scope).

1. `node_corpus.py:111` and `:147-149` -- replace the hardcoded
   `graph_v2@2026-08-10` with `graph_v2@<sha16 of the graph.json actually
   read>`, and add `graph_sha256` / `graph_path` to the corpus header beside
   `source_sha256`. The header identifies the DOCUMENT today; it must identify
   the DECOMPOSITION, because the ids are decomposition-positional.
2. `node_corpus.py:152` -- write `node_corpus.<graph_sha16>.json` with
   `node_corpus.json` as a pointer, so a regeneration cannot destroy the
   corpus an existing run was drawn against.
3. `_debug_gen11/flip_classify/extract_flips.py:40-42` -- key `by_clause` on
   `(clause, user_sha)`, matching `census.py:208`. Then assert D1 below so the
   pooling bug cannot silently return. `census.py:193-195` needs the same.

⚠️ TWO THINGS TO SAY BEFORE ANYONE RUNS IT. (a) Changing the locator string
changes the user-prompt bytes, hence every `user_sha`, hence every prompt
cache key and every existing instrument-equality comparison; historic draws
become permanently non-comparable to new ones. That is CORRECT but it must be
a deliberate versioned cut, not a silent one. (b) Three draws come from a
vintage whose graph.json no longer exists on disk; they must be marked
`corpus_vintage: unknown` and excluded, never guessed at.

────────────────────────────────────────────────────────────────────────────
D1 — the detector implemented below
────────────────────────────────────────────────────────────────────────────
For every clause id with >= 2 draws, collect the `location:` line of each
draw's stored `prompt_user.txt` (written by `translate.py`'s user block from
`node_corpus.py:111`). Flag the clause iff more than one distinct location
appears. Two lines of real logic, no model call.

MEASURED performance on this corpus: recall 5/5, false positives 0/119,
precision 1.00. It cannot fire on prompt-template churn, because the location
line changes only when the node changes.

⛔ DO NOT USE THE LINE-RANGE SIGNAL INSTEAD. "l1_170 encodes lines 1-170, so a
module citing L2500 is mis-routed" is true of the id and false of the corpus:
merged nodes legitimately cite outside their band (MEASURED 2/773 rows in
`node_corpus_all.json`, e.g. `l1_170_n042` cites L183-191). It would flag
those two as false positives and MISS all four in-band cases. Recall 1/5,
precision ~0.3.
"""
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.dirname(os.path.dirname(HERE))
RUNS = os.path.join(PHASE1, "resolve_runs", "graph_v2",
                    "translation_sample", "runs")

_LOC = re.compile(r"^location:\s*(.+)$", re.M)

#: The five clauses this detector is expected to find, from the mechanism
#: analysis. Pinned as a SUBSET check, never as an exact count -- a corpus that
#: legitimately grows must not fail its own gate (`AGENTS.md`).
EXPECTED = {"l1_170_n016", "l1_170_n017", "l1_170_n026",
            "l1_170_n028", "l1_170_n060"}


def scan(runs_dir=RUNS):
    """clause id -> {location line -> [run names]}, over every stored draw."""
    seen = collections.defaultdict(lambda: collections.defaultdict(list))
    if not os.path.isdir(runs_dir):
        return seen
    for run in sorted(os.listdir(runs_dir)):
        d = os.path.join(runs_dir, run)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".prompt_user.txt"):
                continue
            cid = f[:-len(".prompt_user.txt")]
            with open(os.path.join(d, f), encoding="utf-8",
                      errors="replace") as fh:
                m = _LOC.search(fh.read())
            if m:
                seen[cid][m.group(1).strip()].append(run)
    return seen


def detect(runs_dir=RUNS):
    """D1. Returns the flagged clause ids with their divergent locations."""
    out = {}
    for cid, locs in scan(runs_dir).items():
        if len(locs) > 1:
            out[cid] = locs
    return out


def main():
    print(__doc__)
    seen = scan()
    multi = {c: v for c, v in seen.items()
             if sum(len(r) for r in v.values()) >= 2}
    flagged = {c: v for c, v in multi.items() if len(v) > 1}

    print("=" * 78)
    print("D1 — MEASURED, now")
    print("=" * 78)
    print(f"  clause ids with a stored prompt : {len(seen)}")
    print(f"  clause ids with >= 2 draws      : {len(multi)}")
    print(f"  FLAGGED (divergent location)    : {len(flagged)}")
    for cid in sorted(flagged):
        print(f"\n  ⛔ {cid}")
        for loc, runs in sorted(flagged[cid].items(),
                                key=lambda kv: -len(kv[1])):
            print(f"       {len(runs):2d} draw(s)  {loc}")
    got = set(flagged)
    print("\n" + "-" * 78)
    print(f"  expected subset present : {EXPECTED <= got}   "
          f"({len(EXPECTED & got)}/{len(EXPECTED)})")
    extra = got - EXPECTED
    if extra:
        print(f"  ⚠️ NEW, not in the analysed set — adjudicate before "
              f"assuming they are the same defect: {sorted(extra)}")
    print(f"  false positives on the remaining {len(multi) - len(flagged)} "
          f"multi-draw clauses : 0 by construction of the measure "
          f"(they have one location)")
    return 0 if EXPECTED <= got else 1


if __name__ == "__main__":
    sys.exit(main())
