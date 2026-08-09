#!/usr/bin/env python3
"""Score the CLAUSE-BLIND grounding runs against the five pre-registered predictions.

THE EXPERIMENT. `extension_id.py` found that extensional concept identity, computed
over `solver_v4.json`, was measuring **which clause borrowed a predicate** rather
than what the predicate means: every pair above 0.5 character-Jaccard shared a
borrowing clause, against a 13% baseline. The cause was that the resolver had been
TOLD the borrowing clause, so it cited that clause's home passage for every name the
clause borrows.

This run removes the cause. The model gets `DOCUMENT_CLEAN.txt` and a shuffled list of
names with no clause id, no section of origin, no grouping.

⛔ `DOCUMENT_CLEAN.txt`, NOT `DOCUMENT.txt`. The latter carries a `needs_block` under
every one of its 78 section markers listing that section's borrowed predicates — a
complete name-to-section answer key. Three runs were dispatched against it and voided.
See `DEBUGGING_TIPS` §18; the corpus assertion below exists so it cannot happen twice.

⭐ THE CONFOUND BECOMES THE CONTROL. Predicates borrowed by the SAME clause that are
plainly different conditions are a ready-made negative key: nothing about clause-blind
retrieval should put them on the same text.

PRE-REGISTERED PREDICTIONS (written before the run, `ITERATION_LOG.md` §7):

  P1  same-clause pairs fall from 100% of the high-similarity band toward 13%   FALSIFIER
  P2  interactable_entity/1 and interaction_entity/1 land on overlapping text
  P3  transformation_of_user_content/1 and translation_of_user_content/1 overlap
      despite belonging to different clauses
  P4  unnecessary_request/1 and unreliable_destination/1 (both m0150) SEPARATE   FALSIFIER
  P5  the 6 known coinages resolve to no span

⚠️ P5 IS A BAD PREDICTION AND IT IS REPORTED WITH THAT LABEL. The "6 known coinages"
key is NAME-level — those are names whose words appear nowhere in the document. But
§3 of the iteration log already established that all six have their CONCEPT present
(`interactable_entity` is the document's `**Assistant**: the entity that the end user
or developer interacts with`). Under extensional identity a name whose concept is in
the document SHOULD get a span, so P5 predicts the opposite of what the design wants.
It is scored because it was pre-registered, and its failure does not count against the
design. Recording a flawed prediction as flawed is cheaper than quietly dropping it.
"""

import argparse
import glob
import itertools
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PANEL = os.path.join(HERE, "resolve_runs", "panel")
sys.path.insert(0, HERE)
from iter_score import normalise, load_document          # noqa: E402
from extension_id import chars, sim                      # noqa: E402

#: Name-level coinages: words absent from the document. ⚠️ See the P5 caveat above.
COINAGES = ["policy_class/2", "pasted_text/1", "interactable_entity/1",
            "interaction_entity/1", "delegated_authority_to_webpage/1",
            "conflicts_with_later_same_authority/1"]

HIGH = 0.5


def assert_corpus_clean(doc_path, names):
    """⛔ THE CHECK THAT DID NOT EXIST WHEN IT WAS NEEDED (`DEBUGGING_TIPS` §18).

    If the corpus contains any string the model was asked to locate, the task was a
    lookup and not a search, and the run is void. This must fail loudly rather than
    warn: the leaked runs looked like a strong positive.

    ⚠️ TEST THE ANNOTATION FORM, NOT THE BARE WORD. The first version of this
    check substring-matched `n.split("/")[0]` and reported a 9-name leak in a
    corpus that has none: `scope`, `instruction`, `applicable`, `produced` and
    `disallowed` are ordinary English the document uses as prose, and
    `refusal_style` is one of the document's own markdown anchors. A name being
    coined FROM document vocabulary is the normal case — it is why the name
    exists — and flagging it makes the check fire on every real corpus.

    What actually leaked was the `needs_block`: a header plus a bullet list of
    `name/arity` tokens. `policy_class/2` with its arity is a notation the
    specification never uses, so its presence means an annotation survived.
    """
    with open(doc_path, encoding="utf-8") as fh:
        raw = fh.read()
    hits = [n for n in names if n in raw]                 # full `name/arity`
    bullets = re.findall(r"^\s*[-*]\s*[a-z_]+/[0-9]\s*$", raw, re.M)
    header = re.findall(r"BORROWED PREDICATES", raw, re.I)
    if hits or bullets or header:
        raise SystemExit(
            f"⛔ CORPUS LEAK in {os.path.basename(doc_path)} — "
            f"{len(hits)} name/arity tokens {hits[:5]}, "
            f"{len(bullets)} predicate bullets, {len(header)} annotation headers.\n"
            f"   The run this would score is a lookup, not a search. Void it.")
    return True


def extension(run, secs):
    """name -> {section: [(start, end)]}, plus bookkeeping."""
    ext, missed, ungrounded = {}, 0, set()
    for c in run.get("concepts", []):
        n = c.get("name")
        got = {}
        for sp in c.get("spans") or []:
            sid, t = sp.get("section_id"), normalise(sp.get("excerpt", ""))
            if not t or sid not in secs:
                missed += 1
                continue
            i = secs[sid].find(t)
            if i < 0:
                missed += 1
                continue
            got.setdefault(sid, []).append((i, i + len(t)))
        if got:
            ext[n] = got
        else:
            ungrounded.add(n)
    return ext, missed, ungrounded


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runs", default=os.path.join(PANEL, "blind_run[1-9].json"))
    p.add_argument("--document", default=os.path.join(PANEL, "DOCUMENT_CLEAN.txt"))
    p.add_argument("--names", default=os.path.join(PANEL, "BLIND_NAMES.json"))
    a = p.parse_args(argv)

    paths = sorted(glob.glob(a.runs))
    if not paths:
        print(f"⛔ no run files matched {a.runs} — nothing measured", file=sys.stderr)
        return 2
    with open(a.names, encoding="utf-8") as fh:
        names_all = json.load(fh)
    assert_corpus_clean(a.document, names_all)
    print(f"✅ corpus assertion passed — none of {len(names_all)} names appear in "
          f"{os.path.basename(a.document)}")

    secs, _ = load_document(a.document)
    clause = {p_["predicate"]: p_["clause_id"]
              for p_ in json.load(open(os.path.join(PANEL, "PREDICATES.json")))}

    print(f"\n{'='*76}\nCLAUSE-BLIND GROUNDING — {len(paths)} runs\n{'='*76}")
    per_run = []
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            run = json.load(fh)
        ext, missed, ung = extension(run, secs)
        per_run.append((os.path.basename(path), ext, ung))
        print(f"  {os.path.basename(path):18} grounded {len(ext):>3}   "
              f"ungrounded {len(ung):>3}   excerpts not found {missed:>3}")

    # ---------------- P1 ---------------------------------------------------
    print(f"\nP1 · ⭐ FALSIFIER — does similarity still track the BORROWING CLAUSE?")
    print(f"     leaked-design baseline: 100% of pairs >= {HIGH}. "
          f"chance baseline: 13%.")
    for name, ext, _ in per_run:
        ch = {n: chars(v) for n, v in ext.items()}
        ns = sorted(ch)
        hi = [(x, y) for x, y in itertools.combinations(ns, 2)
              if sim(ch[x], ch[y]) >= HIGH]
        same = sum(1 for x, y in hi
                   if clause.get(x) and clause.get(x) == clause.get(y))
        base_n = [(x, y) for x, y in itertools.combinations(ns, 2)
                  if clause.get(x) and clause.get(y)]
        base = sum(1 for x, y in base_n if clause[x] == clause[y])
        print(f"  {name:18} pairs >= {HIGH}: {len(hi):>3}   "
              f"share a clause: {same:>3} "
              f"({(same/len(hi) if hi else 0):.0%})   "
              f"chance {(base/len(base_n) if base_n else 0):.0%}")

    # ---------------- P2, P3, P4 -------------------------------------------
    tests = [("P2", "interactable_entity/1", "interaction_entity/1", True,
              "the case the proposal exists for"),
             ("P3", "transformation_of_user_content/1",
              "translation_of_user_content/1", True,
              "cross-clause synonymy detectable at all"),
             ("P4", "unnecessary_request/1", "unreliable_destination/1", False,
              "⭐ FALSIFIER — same clause, different conditions, must SEPARATE")]
    print("\nP2–P4 · NAMED PAIRS")
    for tag, x, y, want, why in tests:
        print(f"  {tag}  {x} vs {y}")
        print(f"       want {'OVERLAP' if want else 'SEPARATE'} — {why}")
        for name, ext, ung in per_run:
            if x not in ext or y not in ext:
                miss = [n for n in (x, y) if n not in ext]
                print(f"       {name:18} n/a — ungrounded: {miss}")
                continue
            s = sim(chars(ext[x]), chars(ext[y]))
            ok = (s > 0) == want
            print(f"       {name:18} similarity {s:.2f}   "
                  f"{'✅' if ok else '⛔'} {'as predicted' if ok else 'AGAINST'}")

    # ---------------- P5 ---------------------------------------------------
    print("\nP5 · ⚠️ SCORED BUT FLAWED — 'the 6 known coinages get no span'")
    print("     The key is NAME-level; all six have their CONCEPT in the document")
    print("     (log §3), so under extensional identity a span is the RIGHT answer.")
    print("     Failure here does not count against the design.")
    for name, ext, ung in per_run:
        got = [c for c in COINAGES if c in ext]
        print(f"  {name:18} grounded {len(got)} of {len(COINAGES)}: "
              f"{[c.split('/')[0] for c in got]}")

    # ---------------- cross-run stability ----------------------------------
    print("\nSTABILITY · do the runs put the same names on overlapping text?")
    common = set.intersection(*[set(e) for _, e, _ in per_run]) if per_run else set()
    agree = tot = 0
    for x, y in itertools.combinations(sorted(common), 2):
        verdicts = [sim(chars(e[x]), chars(e[y])) > 0 for _, e, _ in per_run]
        tot += 1
        if all(verdicts) or not any(verdicts):
            agree += 1
    print(f"  {len(common)} names grounded in every run; "
          f"of {tot} pairs, {agree} ({agree/tot if tot else 0:.0%}) get the same "
          f"overlap/no-overlap verdict in all runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
