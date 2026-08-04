"""Loader and scorer for the hand-authored REFERENCE translations.

WHAT THIS IS
------------
`golden_translations.json` holds twelve clauses of the Model Spec together with
the atom set a careful reader should produce for each under the notation in
`grammar.py`. It is a STANDARD, not a sample: when a later run says "the
extractor translated this clause correctly", correctness means agreement with
this file.

Three properties have to hold mechanically, because none of them survive good
intentions:

  THE FILE IS FROZEN. It carries its own sha256 over its own content, and
  `load` refuses a file whose content and hash disagree. Without that, the
  cheapest way to raise a score is to edit the reference, and the edit leaves
  no trace.

  THE HELD-OUT HALF STAYS HELD OUT. Six clauses may be looked at while
  iterating on a prompt; six may not. `dev()` can never return one of the six,
  and `entry()` and `score_all()` refuse them unless the caller passes
  `final_evaluation=True` — a flag whose only purpose is to make the decision
  appear in the diff of whoever ran the evaluation.

  ⚠️ HONEST LIMIT OF THAT GUARANTEE. The artifact is a readable JSON file, so
  this is not a secrecy mechanism and cannot be. What it protects is the
  ACCIDENTAL path: the loop that scores against "the golden set", widens to
  twelve without anyone noticing, and quietly burns the only clean measurement
  in the project. Deliberate reading is a decision a person makes; this makes
  sure it is one.

  THE COMPARISON MEANS SOMETHING. See LEVELS below.

WHAT "MATCHES" MEANS, AND WHY
-----------------------------
An extractor will rarely reproduce a reference atom exactly, so a single
boolean would report almost nothing: score by exact name and every system looks
equally bad; score by stem and a system that inverts every prohibition looks
perfect. So matching is GRADED, along two anchors.

THE SPAN ANCHOR, and why it is the headline. A two-author calibration measured
inter-author agreement at 0.29 at stem-name level, 0.79 at span level, and
10/11 on decoration over the span-matched pairs. Names do not canonicalize
between careful humans; WHERE the content is and WHAT structure it carries do.
So extractor iteration is scored on location + structure, and naming is scored
separately on its own axis rather than gating everything above it. Two levels,
anchored on the atom's cited `quote` (never the name — a span level that
consulted the stem would smuggle the 0.29 back in):

  span       the atoms cite overlapping text: one normalized quote CONTAINS
             the other, either direction. Empty quotes never match ("" is a
             substring of everything). Kind is IGNORED by default — this is
             the pure-location headline — see `kind_strict` below.
  span_deco  ... and the decoration is identical: same polarity, same ordered
             principal chain, same role (`grammar.parse_name` on both; absent
             equals absent, so two bare atoms on one span match).

`kind_strict` (compare/score_all, span levels ONLY, default False): extractor
kinds are part of what we measure, but a calibration author produced
out-of-vocabulary kinds, and a kind typo should degrade the score, not zero
the level. The headline is the default — pure location. Pass True to require
kind equality at the span levels; passing it with a name-anchored level is
refused rather than silently ignored.

THE NAME ANCHOR — the original six levels, unchanged. Every one is anchored on
the STEM, `grammar.stem_of`, which is also the key the rest of the pipeline
joins on. Two atoms that do not share a stem are about different concepts and
never match at any of these levels.

  stem       the concept was found. Ignores force, parties and role.
  deontic    ... and the force agrees. `must_x` vs `mustnot_x` is NOT a match;
             neither is `x` vs `must_x`, because "no force stated" is a real
             answer and must not act as a wildcard.
  principal  ... and the principal chain agrees AS AN ORDERED LIST.
             `__model_user` never matches `__user_model`; a two-link chain
             never matches a three-link one.
  role       ... and the `role` field agrees. Absent never equals `topic`.
  name       ... force AND parties agree (i.e. the whole name is equal).
  exact      ... name and role both agree.

`compare` also returns `agreement`, the per-feature accuracy over the pairs
that matched AT STEM LEVEL, whatever level was requested. That is the number
that separates "did not find the concept" from "found it and got the force
backwards" — two failures with completely different fixes, which a single F1
would blend into one mediocre score.

The assignment between candidate and reference atoms is a MAXIMUM matching, not
first-come: greedy pairing lets an early candidate consume the only reference
atom a later one could have matched, which understates a correct annotation for
reasons having nothing to do with the annotation.

NO API CALLS ANYWHERE IN THIS MODULE. The reference was written by hand; a
model asked to produce it would be grading its own homework.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import random

import grammar

_HERE = os.path.dirname(os.path.abspath(__file__))
ARTIFACT_PATH = os.path.join(_HERE, "golden_translations.json")

#: Ordered loosest-first WITHIN each anchor, span anchor first because `span`
#: is the loosest gate in the file (location only, no name at all). The order
#: is DESCRIPTIVE — nothing in the repo indexes into this tuple or compares
#: levels by position (verified before the span levels were inserted ahead of
#: `stem`). The name-anchored six all imply `stem`; the two span levels do not.
LEVELS = ("span", "span_deco",
          "stem", "deontic", "principal", "role", "name", "exact")

#: The levels anchored on the cited quote rather than the name — the only
#: levels `kind_strict` applies to.
SPAN_LEVELS = ("span", "span_deco")

#: The six structural pairs the twelve clauses were selected as. The split
#: sends one member of each pair to dev and the other to held-out, so both
#: halves cover every structure the grammar exists to encode — in particular
#: both halves keep one CONTROL, without which over-marking is unmeasurable.
STRATA = [
    ("obligation", ["m0079", "m0223"]),
    ("prohibition", ["m0242", "m0321"]),
    ("permission", ["m0206", "m0236"]),
    ("defeater", ["m0248", "m0530"]),
    ("explicit_parties", ["m0040", "m0340"]),
    ("control", ["m0053", "m0056"]),
]


class GoldenHashError(Exception):
    """The artifact's content and its recorded sha256 disagree."""


class HeldOutAccessError(Exception):
    """Something asked for a held-out entry without saying so out loud."""


# --------------------------------------------------------------------------
# the freeze

def compute_sha256(payload):
    """The hash over everything in the artifact EXCEPT the hash field.

    Canonical JSON — sorted keys, no incidental whitespace — so re-serializing
    or reformatting the file does not break the freeze. A freeze that a
    formatter can break is a freeze that gets switched off.
    """
    body = {k: v for k, v in payload.items() if k != "sha256"}
    blob = json.dumps(body, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def seeded_split(ids, seed, strata=STRATA):
    """The split, recomputable from the artifact's own seed.

    A hand-picked split can be picked to flatter, so this is the record that it
    was not: the strata come from how the twelve were selected (six structural
    pairs) and the seed makes every within-pair choice.
    """
    ids = set(ids)
    rng = random.Random(seed)
    dev, held = [], []
    for _, pair in strata:
        a, b = sorted(pair)
        if not {a, b} <= ids:
            raise ValueError(f"stratum {pair} is not in {sorted(ids)}")
        first, second = (a, b) if rng.random() < 0.5 else (b, a)
        dev.append(first)
        held.append(second)
    return sorted(dev), sorted(held)


class Golden:
    """The loaded artifact. Construct through `load`, which verifies the hash."""

    def __init__(self, payload):
        self.payload = payload
        self.entries = payload["entries"]
        self.sha256 = payload["sha256"]
        self.dev_ids = list(payload["split"]["dev"])
        self.held_out_ids = list(payload["split"]["held_out"])
        self._by_id = {e["clause_id"]: e for e in self.entries}

    # ---- the split gate ---------------------------------------------------

    def dev(self):
        """The six clauses a prompt may be iterated against. Deep copies, so a
        caller cannot edit the reference and then score against its own edit.

        Built by SELECTING the dev ids, never by returning `self.entries` and
        trusting the caller to filter. A filter that lives at the call site is
        a filter that is eventually forgotten, and the failure is silent.
        """
        return [copy.deepcopy(self._by_id[c]) for c in sorted(self.dev_ids)]

    def held_out(self, final_evaluation=False):
        """The other six. `final_evaluation=True` is the whole point: it makes
        the decision to spend the held-out set appear in the caller's code."""
        self._gate(self.held_out_ids, final_evaluation)
        return [copy.deepcopy(self._by_id[c]) for c in sorted(self.held_out_ids)]

    def entry(self, clause_id, final_evaluation=False):
        if clause_id in self.held_out_ids:
            self._gate([clause_id], final_evaluation)
        return copy.deepcopy(self._by_id[clause_id])

    def entries_unsafe(self):
        """All twelve, for STRUCTURAL checks over the artifact itself — schema,
        budget, span resolution. Named to be uncomfortable: nothing that
        iterates on a prompt should call it."""
        return copy.deepcopy(self.entries)

    def _gate(self, ids, final_evaluation):
        if not final_evaluation:
            raise HeldOutAccessError(
                f"{sorted(ids)} are HELD OUT. They may be scored once, as a "
                "final evaluation, and may never be used to iterate on a "
                "prompt. Pass final_evaluation=True if that is what this is.")

    def reference_atoms(self, clause_id):
        return copy.deepcopy(self._by_id[clause_id]["atoms"])


def load(path=ARTIFACT_PATH):
    """Read the artifact and REFUSE it if its hash does not match its content."""
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    recorded = payload.get("sha256")
    actual = compute_sha256(payload)
    if recorded != actual:
        raise GoldenHashError(
            f"{path} does not match its recorded sha256 "
            f"(recorded {recorded}, actual {actual}). The reference is frozen; "
            "if it genuinely needed to change, rebuild the hash in the same "
            "commit and say why the old translation was wrong.")
    return Golden(payload)


# --------------------------------------------------------------------------
# what "matches" means

def _features(atom):
    """`{stem, polarity, principals, role, ok}` for one atom.

    `ok` is False for a name the grammar cannot parse. An unparseable atom
    never matches anything: guessing a stem for it would let a malformed
    annotation score against a reference it does not actually name.
    """
    name = atom.get("name") if isinstance(atom, dict) else None
    p = grammar.parse_name(name)
    quote = atom.get("quote") if isinstance(atom, dict) else None
    kind = atom.get("kind") if isinstance(atom, dict) else None
    return {
        "stem": p["stem"],
        "polarity": p["polarity"],
        "principals": tuple(p["principals"]),
        "role": grammar.role_of(atom),
        "ok": p["error"] is None,
        "quote": _norm_ws(quote) if isinstance(quote, str) else "",
        "kind": kind if isinstance(kind, str) else None,
    }


def _norm_ws(text):
    """Whitespace collapsed to single spaces, stripped. Span containment must
    not fail because one author wrapped a line the other did not."""
    return " ".join(text.split())


def _span_ok(c, r, kind_strict):
    """Do the two atoms cite the same place in the clause?

    Containment either direction over NORMALIZED quotes: the calibration
    authors quoted at different granularities (one the sentence, one the
    phrase inside it), and that is agreement about location, not disagreement.
    An EMPTY quote never matches — "" is a substring of everything, and an
    atom that cites nothing must not match everywhere for free.
    """
    if not c["quote"] or not r["quote"]:
        return False
    if kind_strict and c["kind"] != r["kind"]:
        return False
    return c["quote"] in r["quote"] or r["quote"] in c["quote"]


def _deco_ok(c, r):
    """Identical decoration: polarity, ordered principal chain, role. Absent
    equals absent on every axis — a bare atom carries the empty structure, and
    two empty structures agree. The STEM is deliberately not consulted: the
    span levels exist because stem names do not canonicalize between authors
    (0.29 agreement), so reading the name back in would defeat the level."""
    return (_polarity_ok(c, r) and _principals_ok(c, r) and _role_ok(c, r))


def _polarity_ok(c, r):
    """`must` and `mustnot` are OPPOSITES, and None is not a wildcard.

    Plain equality, deliberately. Matching on the stem alone would score an
    extractor that inverted every prohibition as having understood the
    document, which is the exact defect `POLARITY_PREFIXES` was added to fix.
    And an unmarked name means "the clause states no force" — a real and common
    answer — so letting it match `must_` would give full marks to the cheapest
    possible annotation.
    """
    return c["polarity"] == r["polarity"]


def _principals_ok(c, r):
    """ORDERED tuple equality. Never sorted, never a set.

    `cause_harm__model_third_party` is the model harming someone;
    `__third_party_model` is someone harming the model. Comparing the chains as
    sets scores those two as the same claim about the document, which is worse
    than not comparing them at all — it reports agreement where the meanings
    are opposite. A short chain does not match a longer one either: a missing
    third party is a missing part of the relation.
    """
    return c["principals"] == r["principals"]


def _role_ok(c, r):
    return c["role"] == r["role"]


def _matches(c, r, level, kind_strict=False):
    if level in SPAN_LEVELS:
        # Location-anchored: the name is NOT consulted and an unparseable (or
        # absent) name is no obstacle — parse_name's cleared output reads as
        # "no decoration", and absent equals absent at span_deco.
        if not _span_ok(c, r, kind_strict):
            return False
        return level == "span" or _deco_ok(c, r)
    if not (c["ok"] and r["ok"]):
        return False
    if c["stem"] != r["stem"]:
        return False
    if level == "stem":
        return True
    if level == "deontic":
        return _polarity_ok(c, r)
    if level == "principal":
        return _principals_ok(c, r)
    if level == "role":
        return _role_ok(c, r)
    if level == "name":
        return _polarity_ok(c, r) and _principals_ok(c, r)
    if level == "exact":
        return (_polarity_ok(c, r) and _principals_ok(c, r)
                and _role_ok(c, r))
    raise ValueError(f"unknown match level {level!r}; expected one of {LEVELS}")


def _max_matching(cands, refs, level, kind_strict=False):
    """Maximum bipartite matching (Kuhn's augmenting paths).

    Small sets, so an exact algorithm costs nothing and removes a whole class
    of complaint: a greedy pairing makes the score depend on the ORDER the
    extractor happened to emit its atoms in.
    """
    pair_for_ref = {}

    def try_assign(ci, seen):
        for ri, r in enumerate(refs):
            if ri in seen or not _matches(cands[ci], r, level, kind_strict):
                continue
            seen.add(ri)
            if ri not in pair_for_ref or try_assign(pair_for_ref[ri], seen):
                pair_for_ref[ri] = ci
                return True
        return False

    for ci in range(len(cands)):
        try_assign(ci, set())
    return [(ci, ri) for ri, ci in sorted(pair_for_ref.items())]


def compare(candidate_atoms, reference_atoms, level="exact",
            kind_strict=False):
    """Score one clause's candidate annotation against the reference.

    Returns `{level, matched, n_candidate, n_reference, precision, recall, f1,
    pairs, agreement}`. `agreement` is per-feature accuracy over the pairs that
    match AT STEM LEVEL — reported at every level so that "found the concept,
    inverted the force" never hides inside a low F1.

    `kind_strict` applies to the span levels ONLY (see module docstring): the
    default False makes "span" pure location — the headline — and True adds a
    kind-equality requirement. With a name-anchored level it is refused rather
    than ignored, because a flag that silently does nothing reads as doing
    something.
    """
    if level not in LEVELS:
        raise ValueError(f"unknown match level {level!r}; expected one of "
                         f"{LEVELS}")
    if kind_strict and level not in SPAN_LEVELS:
        raise ValueError(
            f"kind_strict applies only to the span levels {SPAN_LEVELS}; "
            f"level {level!r} matches on the name and never on the kind")
    cands = [_features(a) for a in (candidate_atoms or [])]
    refs = [_features(a) for a in (reference_atoms or [])]

    pairs = _max_matching(cands, refs, level, kind_strict)
    matched = len(pairs)
    nc, nr = len(cands), len(refs)
    if nc == 0 and nr == 0:
        precision = recall = f1 = 1.0
    else:
        precision = matched / nc if nc else 0.0
        recall = matched / nr if nr else 0.0
        f1 = (2 * precision * recall / (precision + recall)
              if precision + recall else 0.0)

    stem_pairs = _max_matching(cands, refs, "stem")
    agreement = {"polarity": None, "principals": None, "role": None}
    if stem_pairs:
        n = len(stem_pairs)
        agreement = {
            "polarity": sum(cands[c]["polarity"] == refs[r]["polarity"]
                            for c, r in stem_pairs) / n,
            "principals": sum(cands[c]["principals"] == refs[r]["principals"]
                              for c, r in stem_pairs) / n,
            "role": sum(cands[c]["role"] == refs[r]["role"]
                        for c, r in stem_pairs) / n,
        }
    return {"level": level, "matched": matched, "n_candidate": nc,
            "n_reference": nr, "precision": precision, "recall": recall,
            "f1": f1, "pairs": pairs, "agreement": agreement,
            "stem_matched": len(stem_pairs)}


def score_all(candidates, golden_set=None, level="exact",
              final_evaluation=False, kind_strict=False):
    """Score a whole run: `{clause_id: [atom, ...]}` against the reference.

    Scored over the REFERENCE's clauses, not the candidate's keys, so a clause
    the extractor simply skipped counts as a miss rather than disappearing.
    Candidate ids the reference does not cover are ignored — this is a
    twelve-clause standard, not a filter on someone's output.
    """
    g = golden_set or load()
    leaked = sorted(set(candidates) & set(g.held_out_ids))
    if leaked and not final_evaluation:
        raise HeldOutAccessError(
            f"candidate annotations were supplied for held-out clauses "
            f"{leaked}. Scoring them is a final evaluation; say so with "
            "final_evaluation=True, or drop them.")
    scope = (sorted(g.dev_ids + g.held_out_ids) if final_evaluation
             else sorted(g.dev_ids))
    per_clause = {cid: compare(candidates.get(cid, []),
                               g.reference_atoms(cid), level=level,
                               kind_strict=kind_strict)
                  for cid in scope}
    tm = sum(r["matched"] for r in per_clause.values())
    tc = sum(r["n_candidate"] for r in per_clause.values())
    tr = sum(r["n_reference"] for r in per_clause.values())
    p = tm / tc if tc else 0.0
    r_ = tm / tr if tr else 0.0
    micro = {"precision": p, "recall": r_,
             "f1": 2 * p * r_ / (p + r_) if p + r_ else 0.0,
             "matched": tm, "n_candidate": tc, "n_reference": tr}
    return {"level": level, "n_clauses": len(scope), "per_clause": per_clause,
            "micro": micro, "final_evaluation": bool(final_evaluation)}
