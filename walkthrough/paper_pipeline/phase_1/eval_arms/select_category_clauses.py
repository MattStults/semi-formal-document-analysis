#!/usr/bin/env python3
"""Draw the "introduces a named category" eval set — deterministically, and
BEFORE any outcome is looked at.

⭐ WHY THIS FILE EXISTS. `RESULT_bad_example_6.md` measured a change to bad
worked example #6 ("imports a name without its content") on a clause set drawn
blind, and the control arm scored 0.000 — the set did not exhibit the failure,
so there was nothing to improve and the delta was unreadable. A fix for a
failure can only be measured where the failure can OCCUR. Bad example #6 is
about a concept that names a category and glosses it with its own name, so the
eval set has to hold clauses that INTRODUCE NAMED CATEGORIES.

⛔ THE TRAP THIS AVOIDS. "Pick the clauses where the failure shows up" is
fitting if the picking happens after the run. So the rule is mechanical, it is
written here before any call is made, and the drawn ids are frozen in a
provenance sidecar with the exclusion sets that produced them. A later reader
can re-run this file and get the same six ids.

The rule, in one sentence: a clause is eligible if it is long enough to yield
concepts at all, has never been sent to the model or named in a prompt, and
either **enumerates at least three short items in a row** or **bolds a term** —
the document's two ways of introducing a named category.

⚠️ THE RULE WAS DERIVED FROM DATA, AND HERE IS THE SEARCH. Six candidate rules
were scored against the empty-gloss counts already on disk (see
`PREREG_bad_example_6_rerun.md` for the table). The first rule tried — an
"e.g./such as/including" marker word — did NOT discriminate (4.9% positive vs
6.4% negative) and was discarded. Every clause used to derive the rule is in
the exclusion set below, so the drawn set is held out from the derivation.

Usage:
    python3 select_category_clauses.py --salt eval-categories-v1 --n 6 \
        --out heldout_categories.txt
"""

import argparse
import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P1 = os.path.dirname(HERE)
CORPUS = os.path.join(P1, "..", "..", "..", "semi-formal-experiment",
                      "modelspec_clauses.json")

#: ⭐ THE TWO SIGNALS. Both are the DOCUMENT's own way of introducing a name,
#: and both were checked against the empty glosses already on disk.
#:
#: S1 — a RUN OF ENUMERATED ITEMS: three or more consecutive comma-separated
#:      segments, each short enough to be a noun phrase rather than a clause.
#:      This is the shape bad example #6 is literally drawn from — "acts of
#:      violence ..., terrorism, child abuse ..." — and it is what the observed
#:      empty glosses come off: `file_attachment`, `tool_output`,
#:      `multimodal_data`, `system_message`, `terrorism_act`. The model turns
#:      each listed item into its own unary predicate and glosses it by
#:      repeating the item's name.
#: S2 — a BOLDED TERM. "**Conversation**: valid input to the model is a
#:      **conversation** ..." is the spec naming a category outright; it
#:      produced `message_role` -> "the role of a message".
#:
#: ⛔ NOT a marker word ("such as", "e.g.", "including"). That was the first
#: rule tried and it does not discriminate — the marker is common in clauses
#: that introduce nothing, and the two worst offenders on disk (m0293, m0177)
#: enumerate without one.
_BOLD = re.compile(r"\*\*[^*\n]{2,40}\*\*")
_SENTENCE = re.compile(r"(?<=[.:;])\s")

#: An item in an enumeration is a noun phrase, not a clause. Both bounds are
#: needed: a long segment is prose, and a many-worded one is a sentence with
#: an aside in it.
_ITEM_CHARS, _ITEM_WORDS, _RUN = 60, 8, 3

#: ⚠️ A GUARD AGAINST FRAGMENTS, NOT A TUNED THRESHOLD. A one-line clause
#: yields one or two concepts and a rate over a denominator of two is the
#: "metric read 0.0000 because it measured NOTHING" failure of
#: `DEBUGGING_TIPS.md` §2. It is set below every clause that has ever been run
#: here, so it excludes nothing the prior data speaks about.
MIN_CHARS = 100

#: ⛔ EVERY id that carries a worked answer or a previous outcome.
PROMPT_GLOBS = ["prompt/*.md", "eval_arms/prompt_*/*.md"]
SENT_GLOBS = ["runs/*/*.raw.txt", "runs/*/*.transcript.json",
              "eval_arms/*_raw/*/*/*.raw.txt"]
HELDOUT_FILES = ["heldout.txt", "heldout_v2.txt", "heldout_v3.txt",
                 "diagnosis_set.txt"]
_ID = re.compile(r"m[0-9]{4}")


def exclusions():
    """(set, provenance dict). Each source is recorded separately so a reader
    can see which fence caught which id rather than one anonymous blob."""
    out = {}
    ids = set()
    for label, globs in (("named_in_prompt", PROMPT_GLOBS),):
        found = set()
        for g in globs:
            for path in glob.glob(os.path.join(P1, g)):
                with open(path, encoding="utf-8") as fh:
                    found |= set(_ID.findall(fh.read()))
        out[label] = sorted(found)
        ids |= found
    found = set()
    for g in SENT_GLOBS:
        for path in glob.glob(os.path.join(P1, g)):
            base = os.path.basename(path)
            found |= set(_ID.findall(base))
    out["ever_sent_to_the_model"] = sorted(found)
    ids |= found
    found = set()
    for name in HELDOUT_FILES:
        path = os.path.join(HERE, name)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                found |= set(_ID.findall(fh.read()))
    out["previous_eval_sets"] = sorted(found)
    ids |= found
    return ids, out


def longest_item_run(text):
    """Longest run of consecutive short comma-separated segments.

    Reset at sentence boundaries: two one-item sentences in a row are not a
    list, and without the reset every long clause scores as an enumeration.
    """
    best = 0
    for chunk in _SENTENCE.split(text or ""):
        run = 0
        for seg in (s.strip() for s in chunk.split(",")):
            if 0 < len(seg) <= _ITEM_CHARS and len(seg.split()) <= _ITEM_WORDS:
                run += 1
                best = max(best, run)
            else:
                run = 0
    return best


def signals(text):
    """Which category-introduction signals this clause carries."""
    hits = []
    if longest_item_run(text) >= _RUN:
        hits.append("enumerated_items")
    if _BOLD.search(text):
        hits.append("bold_term")
    return hits


def eligible(clauses, excluded):
    out = []
    for c in clauses:
        if c["id"] in excluded:
            continue
        if c.get("kind") not in ("definitional", "conditional"):
            continue
        text = c.get("quote") or ""
        if len(text) < MIN_CHARS:
            continue
        sig = signals(text)
        if not sig:
            continue
        out.append((c["id"], c.get("kind"), sig))
    return out


def rank(cid, salt):
    return hashlib.sha256(f"{salt}:{cid}".encode()).hexdigest()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--salt", required=True)
    p.add_argument("--n", type=int, default=6)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)

    with open(os.path.abspath(CORPUS), encoding="utf-8") as fh:
        clauses = json.load(fh)["clauses"]
    excl, excl_prov = exclusions()
    pool = eligible(clauses, excl)
    if len(pool) < a.n:
        print(f"⛔ pool holds {len(pool)} clauses, fewer than the {a.n} asked "
              f"for. Widening the rule after seeing this is fitting; say so "
              f"in the pre-registration if you do it.", file=sys.stderr)
        return 2
    picked = sorted(pool, key=lambda t: rank(t[0], a.salt))[:a.n]

    out = a.out if os.path.isabs(a.out) else os.path.join(HERE, a.out)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(cid for cid, _, _ in picked) + "\n")
    with open(out + ".provenance.json", "w", encoding="utf-8") as fh:
        json.dump({
            "generated_by": "eval_arms/select_category_clauses.py",
            "salt": a.salt,
            "rule": "kind in {definitional, conditional}; len(quote) >= "
                    f"{MIN_CHARS}; and at least one of: a run of >= {_RUN} "
                    f"consecutive comma-separated segments each <= "
                    f"{_ITEM_CHARS} chars and <= {_ITEM_WORDS} words, or a "
                    "bolded term",
            "rule_validation_on_prior_data":
                "over the 24 clauses with responses already on disk, "
                "rule-positive clauses hold 22 empty glosses in 226 concepts "
                "(9.7%) and rule-negative 8 in 267 (3.0%). ALL 24 are in the "
                "exclusion set, so this draw is held out from the derivation.",
            "why": "bad worked example #6 is about a concept that names a "
                   "category and glosses it with its own name. A clause that "
                   "introduces no named category cannot exhibit that failure, "
                   "and the first A/B measured the change on a set that did "
                   "not — the control scored 0.000.",
            "ids": [cid for cid, _, _ in picked],
            "picked": [{"id": c, "kind": k, "signals": s} for c, k, s in picked],
            "pool_size": len(pool),
            "corpus_size": len(clauses),
            "excluded_n": len(excl),
            "excluded": excl_prov,
        }, fh, indent=1)
    print(f"✓ {os.path.relpath(out, HERE)} — {a.n} of {len(pool)} eligible "
          f"({len(excl)} ids excluded)")
    for cid, kind, sig in picked:
        print(f"    {cid}  {kind:12s} {','.join(sig)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
