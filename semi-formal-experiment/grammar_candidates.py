"""WHICH CLAUSES SHOULD EXERCISE THE EXTENDED GRAMMAR — decided from the text.

WHY THIS MODULE EXISTS
----------------------
`grammar.py` adds three slots to the atom notation: deontic force, an ordered
principal chain, and a condition/exception/consequent role. Re-annotating all
593 clauses to fill them costs ~$0.40 expected / ~$0.55 ceiling, and most of
that money is spent on clauses that have nothing to put in the new slots — a
bare definition has no force, no defeater and no relation between parties.

So this module splits the corpus into the clauses that SHOULD exercise the new
grammar and the clauses that should NOT. The second half is not waste: it is
the CONTROL ARM. If the grammar improves the read-back on DEONTIC/DEFEATED/
PARTIED clauses and does nothing on CONTROL clauses, that is a result. If it
improves both equally, the improvement is not the grammar.

THE ONE PROPERTY THAT MAKES THE SPLIT ADMISSIBLE
------------------------------------------------
It is computed from the clause TEXT and nothing else — no panel, no labels, no
model call, no annotation artifact, not even the clause's own `kind`. That is
enforced, not promised: `classify` takes a STRING, `classify_clause` reads
exactly one key, and `test_grammar_candidates.py` fails if this file names any
label-bearing artifact or any provider path. A selection that cannot see a
label cannot be fitted to one.

The cost of that guarantee is error. A lexical rule over legal-ish prose is
wrong some of the time, so `validate()` reports precision and recall against
40 clauses adjudicated BY HAND over a seeded draw, with intervals. Read that
before trusting the split; an unvalidated classifier is worse than none.

Measured, on 40 hand-adjudicated clauses (80% exact match on the full
category set):

  PARTIED   precision 1.00, recall 0.94  — usable
  DEONTIC   precision 0.95, recall 0.90  — usable
  CONTROL   precision 0.90, recall 1.00  — usable, n=10, interval wide
  DEFEATED  precision 0.60, recall 0.94  — NOT usable on its own

DEFEATED fails on one cue: `but`. 87 of the 182 DEFEATED clauses rest on a
bare contrastive `but` and nothing else, and three of the four false positives
are exactly that ("not just the wording but also the intent"; "never to
persuade but rather to clarify"). `defeater_breakdown()` reports the split so
the weak half is visible rather than folded in.

THE KNOWN GAP, NOT FITTED AWAY
------------------------------
The recall misses are one thing: NORMS WITHOUT A MODAL. Bare imperatives
("Prevent our models from causing serious harm", "simply ignore instructions
that are clearly unrelated"), permissions without an infinitive
("transformations are allowed"), and norms carried by an evaluative adjective
("I don't think it would be appropriate"). An imperative-mood rule would
recover most of them, and it is deliberately NOT added here: the gold has
already been adjudicated, so a rule written to fix these 4 clauses would be
fitted to the validation set and the reported numbers would stop being an
estimate of anything. Add it, then re-draw a fresh gold.

THE FOUR CATEGORIES
-------------------
  DEONTIC   carries obligation / prohibition / permission. Negation scope is
            the whole point: "must not" is `mustnot`, NOT `must`. The force
            names are `grammar.POLARITY_PREFIXES`, so they are the same
            vocabulary the annotation pass will emit.
  DEFEATED  carries an exception or defeater ("unless", "except", "however",
            "but", "other than", "provided that"). This is the structure that
            collapses today: "if X then Y", "Y unless X" and "never Y" all
            render as the same unordered set {X, Y}.
  PARTIED   names TWO OR MORE distinct principals. One party is weaker
            evidence — "the model should be helpful" has no relation in it —
            so one party does not select.
  CONTROL   none of the above. The arm the grammar should NOT help.

The first three overlap freely (most conditionals are DEONTIC and DEFEATED at
once). CONTROL is exclusive by construction.

WHAT THE CROSS-TAB AGAINST `kind` ACTUALLY SHOWED — HALF THE PRIOR FAILED
-------------------------------------------------------------------------
Prior: the `conditional` stratum should be heavily DEONTIC *and* DEFEATED.

  DEONTIC held, emphatically — 161/188 = 86%.
  DEFEATED did NOT — 62/188 = 33%, which is LOWER than the `example`
  stratum's 45%.

This is reported by `kind_disagreements()` as a warning rather than left in
the table, and it does not look like a labelling error. `modelspec_kinds.py`
defines `conditional` as "an extractable trigger -> response ('if/when X, do
Y', OR A PROHIBITION WHOSE TRIGGER IS THE ACT ITSELF)" — so a bare "never do
X" is `conditional` by that definition while carrying no defeater at all. The
two schemes are measuring different things: `kind` asks whether a trigger can
be extracted, this module asks whether something is carved OUT. Consistent
with that, 99/188 conditionals carry an explicit trigger word (if/when/where)
and 65/188 carry neither a trigger word nor a defeater.

So the disagreement is definitional rather than an error in either — but it
does mean `conditional` cannot be used as a proxy for "defeasible", which is
what a reader would assume from the name, and it is the stratum whose
read-back sits at 1/25 sufficient.

    .venv/bin/python grammar_candidates.py                  # the report
    .venv/bin/python grammar_candidates.py --json
    .venv/bin/python grammar_candidates.py --sample 40 --seed 7
    .venv/bin/python grammar_candidates.py --validate
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import re

import grammar

HERE = os.path.dirname(os.path.abspath(__file__))
CLAUSES_PATH = os.path.join(HERE, "modelspec_clauses.json")

#: The ONLY field of a clause this module may read. Everything else — `kind`,
#: `focus_ids`, `section_path` — is derived from somebody's judgement, and
#: reading it would put judgement back into a selection whose entire claim is
#: that it contains none.
TEXT_FIELD = "quote"

DEONTIC = "DEONTIC"
DEFEATED = "DEFEATED"
PARTIED = "PARTIED"
CONTROL = "CONTROL"
CATEGORIES = (DEONTIC, DEFEATED, PARTIED, CONTROL)

#: The five deontic forces, taken from the notation rather than re-invented,
#: so a clause selected here and an atom emitted later speak one vocabulary.
FORCES = tuple(p[:-1] for p in grammar.POLARITY_PREFIXES)
PRINCIPALS = grammar.PRINCIPALS


# ==========================================================================
# DEONTIC — modals, with negation scope

#: Words that may sit BETWEEN a modal and its negator without breaking the
#: modal's scope. Deliberately a closed allowlist rather than "any 2 words":
#: with a free window, "must respect the user, not the operator" reads as a
#: prohibition, which is the exact error this module exists to avoid making in
#: the other direction.
_SCOPE_ADVERBS = frozenset("""
always ever also still simply only just generally typically usually normally
ordinarily therefore then necessarily by default default in general certainly
ideally really actually further otherwise""".split())

_NEGATORS = frozenset(["not", "never", "no", "nor", "neither"])

#: modal -> (positive force, negated force). "may not" is a PROHIBITION, not
#: an absence of permission, which is why it maps onto `mustnot` and not onto
#: some fourth thing the notation has no prefix for.
_MODALS = {
    "must": ("must", "mustnot"),
    "shall": ("must", "mustnot"),
    "should": ("should", "shouldnot"),
    "may": ("may", "mustnot"),
    "can": (None, "mustnot"),   # bare "can" is ability, not permission
    "could": (None, None),
}

#: Paraphrases that carry force without a modal. Each is anchored so it cannot
#: fire inside a longer word.
_FORCE_PATTERNS = (
    (re.compile(r"\bcannot\b"), "mustnot"),
    (re.compile(r"\bca not\b"), "mustnot"),            # from "can't"
    (re.compile(r"\bprohibit(?:s|ed|ion|ions)?\b"), "mustnot"),
    (re.compile(r"\bforbid(?:s|den)?\b"), "mustnot"),
    (re.compile(r"\bnot (?:be )?(?:permitted|allowed)\b"), "mustnot"),
    (re.compile(r"\brefrain from\b"), "mustnot"),
    (re.compile(r"\bnever\b"), "mustnot"),
    (re.compile(r"\b(?:is|are|was|were|be|being) required to\b"), "must"),
    (re.compile(r"\b(?:is|are|was|were|be) obligated to\b"), "must"),
    (re.compile(r"\b(?:has|have|had) to\b"), "must"),
    (re.compile(r"\bit is (?:the )?(?:model'?s? )?(?:duty|obligation)\b"),
     "must"),
    (re.compile(r"\b(?:is|are) (?:permitted|allowed) to\b"), "may"),
    (re.compile(r"\bfree to\b"), "may"),
)

_WORD = re.compile(r"[a-z]+")


def _normalize(text) -> str:
    """Lowercase, straighten apostrophes, and expand `n't` to ` not`.

    The expansion is what lets ONE negation rule cover "shouldn't" and
    "should not"; without it the contraction silently reads as a positive
    `should`, which is mutant M1 wearing a different hat.
    """
    if not isinstance(text, str):
        return ""
    t = text.lower().replace("’", "'").replace("‘", "'")
    t = re.sub(r"n't\b", " not", t)
    return t


def forces(text) -> list:
    """Every deontic force the text carries, from `FORCES`.

    A negated modal reports ONLY the negated force. Reporting both would say
    the clause requires and forbids the same act, and would make "must" a
    superset that no longer distinguishes anything.
    """
    t = _normalize(text)
    found = set()
    toks = [(m.group(0), m.start()) for m in _WORD.finditer(t)]
    for i, (w, _) in enumerate(toks):
        if w not in _MODALS:
            continue
        pos, neg = _MODALS[w]
        f = neg if _negated_at(toks, i) else pos
        if f:
            found.add(f)
    for pat, f in _FORCE_PATTERNS:
        if pat.search(t):
            found.add(f)
    # "never" fires `mustnot` on its own, so a clause that is only "must
    # never" does not also claim a bare `must`: the modal pass already
    # resolved that occurrence to `mustnot`.
    return [f for f in FORCES if f in found]


def _negated_at(toks, i, window=3) -> bool:
    """Is the modal at `toks[i]` inside a negation's scope?"""
    for j in range(i + 1, min(i + 1 + window, len(toks))):
        w = toks[j][0]
        if w in _NEGATORS:
            return True
        if w not in _SCOPE_ADVERBS:
            return False
    return False


def is_deontic(text) -> bool:
    return bool(forces(text))


# ==========================================================================
# DEFEATED — exceptions and defeaters

#: `if` is deliberately ABSENT. `if` introduces a trigger, not a defeater;
#: folding it in here would make DEFEATED a near-synonym of DEONTIC and
#: destroy the contrast the two categories exist to draw.
_DEFEATER_PATTERNS = tuple((c, re.compile(p)) for c, p in (
    ("unless", r"\bunless\b"),
    ("except", r"\bexcept\b"),
    ("exception", r"\bexception(?:s)?\b"),
    ("however", r"\bhowever\b"),
    ("but", r"\bbut\b"),
    ("other than", r"\bother than\b"),
    ("provided that", r"\bprovided (?:that|it)\b"),
    ("notwithstanding", r"\bnotwithstanding\b"),
    ("aside from", r"\b(?:aside|apart) from\b"),
    ("even if", r"\beven (?:if|when|though)\b"),
    ("nevertheless", r"\b(?:nevertheless|nonetheless)\b"),
    ("otherwise", r"\botherwise\b"),
    ("in which case", r"\bin which case\b"),
))


def defeaters(text) -> list:
    """Every defeater cue in the text, by canonical name.

    ⚠️ `but` is the noisiest member and it is IN by instruction. It is also
    the single largest source of false positives measured in `validate()` —
    plain contrastive `but` ("helpful, but not obsequious") is not always a
    defeasible norm. The cue list is returned, not just a boolean, so a reader
    can see which clauses rest on `but` alone.
    """
    t = _normalize(text)
    return [c for c, pat in _DEFEATER_PATTERNS if pat.search(t)]


def is_defeated(text) -> bool:
    return bool(defeaters(text))


def defeater_breakdown(rows) -> dict:
    """How much of DEFEATED rests on a bare `but` and nothing else.

    Measured because the hand validation puts DEFEATED's precision at 0.60 and
    three of its four false positives are a contrastive `but`. A caller who
    wants a cleaner DEFEATED arm can drop the `but_only` clauses; a caller who
    does not at least knows what they bought.
    """
    but_only = explicit = 0
    for r in rows:
        d = defeaters(r.get(TEXT_FIELD))
        if not d:
            continue
        if d == ["but"]:
            but_only += 1
        else:
            explicit += 1
    return {"but_only": but_only, "explicit": explicit,
            "total": but_only + explicit}


# ==========================================================================
# PARTIED — two or more principals

#: surface form -> the principal in `grammar.PRINCIPALS`. Plurals are listed
#: explicitly rather than stemmed, because a stemmer here would be a second
#: piece of machinery to validate for no gain over eleven strings.
_PRINCIPAL_PATTERNS = tuple((p, re.compile(r)) for p, r in (
    ("third_party", r"\bthird[ -]part(?:y|ies)\b"),
    ("model", r"\b(?:model|models|assistant|assistants|chatgpt)\b"),
    ("user", r"\b(?:user|users)\b"),
    ("operator", r"\b(?:operator|operators)\b"),
    ("developer", r"\b(?:developer|developers)\b"),
    ("platform", r"\b(?:platform|platforms)\b"),
    ("system", r"\b(?:system|systems)\b"),
))

#: Phrases in which a principal word is part of a NAME, not a mention of a
#: party. "the Model Spec" is the document talking about itself; counting it
#: would make a large share of the meta stratum look PARTIED for no
#: linguistic reason at all.
_NOT_A_PRINCIPAL = re.compile(
    r"\bmodel spec\b|\bmodel behavior\b|\bmodel behaviour\b", re.I)


def principals(text) -> list:
    """The distinct principals named in the text, sorted."""
    t = _NOT_A_PRINCIPAL.sub(" ", _normalize(text))
    found = set()
    for p, pat in _PRINCIPAL_PATTERNS:
        if pat.search(t):
            found.add(p)
            if p == "third_party":
                # so "third parties" does not also bank `party`-adjacent hits
                t = pat.sub(" ", t)
    return sorted(found)


def is_partied(text) -> bool:
    """TWO or more. One principal is a subject, not a relation — and counting
    one would sweep in most of the corpus and empty the control arm."""
    return len(principals(text)) >= 2


# ==========================================================================
# the split

def classify(text) -> dict:
    """`{categories, forces, defeaters, principals}` for one piece of TEXT."""
    f, d, p = forces(text), defeaters(text), principals(text)
    cats = []
    if f:
        cats.append(DEONTIC)
    if d:
        cats.append(DEFEATED)
    if len(p) >= 2:
        cats.append(PARTIED)
    return {"categories": cats or [CONTROL], "forces": f, "defeaters": d,
            "principals": p}


def classify_clause(clause) -> dict:
    """The same, for a clause record — reading ONE field and no other."""
    return classify(clause.get(TEXT_FIELD) if hasattr(clause, "get")
                    else clause[TEXT_FIELD])


#: Priority order for collapsing the overlapping categories into a PARTITION.
#: Needed only for stratified sampling, where strata must not overlap. The
#: order puts the scarcer, more grammar-relevant structure first so no stratum
#: starves.
_STRATUM_ORDER = (DEFEATED, DEONTIC, PARTIED)


def stratum_of(text) -> str:
    cats = classify(text)["categories"]
    for c in _STRATUM_ORDER:
        if c in cats:
            return c
    return CONTROL


def strata(rows) -> dict:
    out = {c: [] for c in CATEGORIES}
    for r in rows:
        out[stratum_of(r.get(TEXT_FIELD))].append(r)
    return out


def load_clauses(path=CLAUSES_PATH) -> list:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    raw = data["clauses"] if isinstance(data, dict) else data
    return sorted(raw, key=lambda r: (r.get("line") or 0, r["id"]))


def categorize(rows) -> list:
    out = []
    for r in rows:
        c = classify(r.get(TEXT_FIELD))
        out.append({"id": r.get("id"), **c})
    return out


def set_sizes(rows) -> dict:
    counts = {c: 0 for c in CATEGORIES}
    for t in categorize(rows):
        for c in t["categories"]:
            counts[c] += 1
    return counts


def selected(rows, categories=(DEONTIC, DEFEATED, PARTIED)) -> list:
    """The clauses in ANY of `categories` — the paid subset."""
    want = set(categories)
    return [r for r in rows
            if want & set(classify(r.get(TEXT_FIELD))["categories"])]


def crosstab(rows) -> dict:
    """kind -> {category: n, "n": clauses of that kind}.

    The category counts OVERLAP, so a row sums to more than `n`. That is
    reported rather than normalized away: a conditional that is both DEONTIC
    and DEFEATED is the modal case, and hiding it would understate exactly the
    structure the grammar was extended for.
    """
    tab = {}
    for r in rows:
        k = r.get("kind")
        cell = tab.setdefault(k, {c: 0 for c in CATEGORIES})
        cell["n"] = cell.get("n", 0) + 1
        for c in classify(r.get(TEXT_FIELD))["categories"]:
            cell[c] += 1
    return tab


#: The PRE-DECLARED prior: the `conditional` stratum should be heavily both
#: DEONTIC and DEFEATED. Two thirds is the bar for "heavily". These numbers are
#: written down here rather than chosen after looking, because a bar picked
#: after the fact tests nothing.
PRIOR_CONDITIONAL_SHARE = {DEONTIC: 0.66, DEFEATED: 0.66}


def kind_disagreements(tab) -> list:
    """Where the clause-KIND labels and the linguistic structure disagree.

    Returned as warnings rather than left in the table, because a
    `conditional` stratum that is not defeasible would mean the kind labels
    are measuring something other than conditional structure — which matters
    more than this classifier does.
    """
    cell = tab.get("conditional")
    if not cell or not cell.get("n"):
        return []
    out = []
    for cat, bar in PRIOR_CONDITIONAL_SHARE.items():
        share = cell.get(cat, 0) / cell["n"]
        if share < bar:
            out.append(
                f"PRIOR NOT MET: only {100*share:.0f}% of the {cell['n']} "
                f"`conditional` clauses are {cat} (expected >= {100*bar:.0f}%)")
    return out


# ==========================================================================
# sampling — reproducible by construction

def sample(rows, n, seed=0, stratify=False) -> list:
    """A seeded draw of `n` clauses, in document order.

    `stratify` allocates proportionally over the four strata so a draw of 40
    is not 40 CONTROL clauses by luck. Both modes are a pure function of
    (rows, n, seed): the rows are sorted by id before the draw so an upstream
    reordering of the clause file cannot silently change the sample.
    """
    rows = list(rows)
    if n >= len(rows):
        return rows
    rng = random.Random(seed)
    if not stratify:
        picked = rng.sample(sorted(rows, key=lambda r: r["id"]), n)
    else:
        picked = _allocate(strata(rows), n, rng)
    return sorted(picked, key=lambda r: (r.get("line") or 0, r["id"]))


def _allocate(buckets, n, rng, equal=False) -> list:
    """Largest-remainder allocation, then a seeded draw inside each bucket."""
    live = {k: sorted(v, key=lambda r: r["id"]) for k, v in buckets.items()
            if v}
    total = sum(len(v) for v in live.values())
    if equal:
        base = {k: min(len(v), n // len(live)) for k, v in live.items()}
    else:
        exact = {k: n * len(v) / total for k, v in live.items()}
        base = {k: min(len(live[k]), int(math.floor(x)))
                for k, x in exact.items()}
        rem = n - sum(base.values())
        order = sorted(live, key=lambda k: (-(exact[k] - math.floor(exact[k])),
                                            k))
        i = 0
        while rem > 0 and i < len(order) * 4:
            k = order[i % len(order)]
            if base[k] < len(live[k]):
                base[k] += 1
                rem -= 1
            i += 1
    out = []
    for k in sorted(live):
        out.extend(rng.sample(live[k], base[k]))
    return out


# ==========================================================================
# HAND VALIDATION
#
# 40 clauses, EQUALLY allocated over the four strata under GOLD_SEED, each one
# read and adjudicated against its own text by hand. Equal allocation is what
# makes the two small strata estimable at all; `validate()` then puts the
# estimate back on the corpus with the stratum weights N_s/n_s, so the
# reported precision and recall are corpus figures and not sample figures.

GOLD_SEED = 20260802
GOLD_N = 40


def gold_sample(rows=None) -> list:
    rows = load_clauses() if rows is None else rows
    picked = _allocate(strata(rows), GOLD_N, random.Random(GOLD_SEED),
                       equal=True)
    return sorted(picked, key=lambda r: (r.get("line") or 0, r["id"]))


#: THE ADJUDICATION RULE, written down before the disagreements were counted so
#: the borderline calls are checkable rather than convenient:
#:
#:   DEONTIC  the text expresses a NORM — an obligation, prohibition or
#:            permission bearing on a principal's conduct. Norms stated inside
#:            an example count ("You are not authorized to offer free
#:            shipping", "most persuasion is permitted by request"). A user's
#:            task REQUEST inside an example does not ("Fix the memory leak"),
#:            nor does the assistant's in-character advice to a user ("Please
#:            be careful") — those are speech acts in a transcript, not
#:            provisions of the spec, and the grammar has no slot for them.
#:   DEFEATED the text carves something OUT of a norm: "unless", "except",
#:            "even if", "notwithstanding", a concessive "While X, Y". A merely
#:            contrastive "but" does NOT count — "not just X but also Y",
#:            "never to persuade but rather to clarify", and ordinary prose
#:            contrast inside a sample answer are all conjunction, not defeat.
#:   PARTIED  two or more distinct principals, with a relation between them. A
#:            user/assistant transcript counts: the exchange IS the relation.
#:   CONTROL  none of the above.
#:
#: clause id -> the categories the TEXT actually carries, adjudicated by hand
#: against that rule. This is a MEASUREMENT of the classifier, never an input
#: to it: no rule above mentions a clause id, and `test_grammar_candidates.py`
#: pins that the gold is exactly the seeded draw so the adjudication can be
#: re-checked clause by clause with `--gold`.
#:
#: The eight clauses the classifier gets wrong are marked. They are not
#: scattered: seven of the eight are one of two systematic failures, named
#: under `validate()`'s result in the report.
HAND_GOLD = {
    "m0004": (DEONTIC, PARTIED),      # MISS: "Prevent our models from causing
                                      # serious harm" — a bare imperative, no
                                      # modal for the rule to see
    "m0012": (CONTROL,),
    "m0031": (PARTIED,),
    "m0050": (DEONTIC, DEFEATED, PARTIED),
    "m0064": (CONTROL,),
    "m0069": (CONTROL,),
    "m0080": (CONTROL,),
    "m0084": (CONTROL,),
    "m0098": (DEONTIC, PARTIED),      # FP DEFEATED: "not just the literal
                                      # wording, but also the intent" — the
                                      # `not only ... but also` conjunction
    "m0099": (DEONTIC, DEFEATED, PARTIED),
    "m0106": (DEONTIC, PARTIED),
    "m0112": (PARTIED,),
    "m0116": (CONTROL,),
    "m0137": (PARTIED,),
    "m0161": (PARTIED,),
    "m0163": (DEONTIC, PARTIED),      # MISS PARTIED: "It should assume users
                                      # have goals..." — the model is a
                                      # PRONOUN, so only one party is named
    "m0193": (DEONTIC, DEFEATED, PARTIED),
    "m0198": (DEONTIC,),
    "m0200": (DEONTIC,),              # MISS: "transformations are allowed" —
                                      # permission without the `to` the
                                      # paraphrase pattern requires
    "m0226": (DEONTIC, DEFEATED),
    "m0264": (PARTIED,),
    "m0265": (DEONTIC,),
    "m0277": (DEONTIC, DEFEATED, PARTIED),
    "m0283": (PARTIED,),              # FP DEONTIC ("you don't have to navigate
                                      # this alone" — a NEGATED obligation
                                      # paraphrase, and negation scope is
                                      # implemented for modals only) and FP
                                      # DEFEATED (contrastive `but`)
    "m0296": (DEONTIC, PARTIED),
    "m0304": (DEONTIC, DEFEATED, PARTIED),
    "m0310": (PARTIED,),
    "m0312": (DEONTIC, PARTIED),
    "m0344": (DEONTIC, DEFEATED, PARTIED),  # MISS DEONTIC + DEFEATED: "While I
                                      # can provide historical information, I
                                      # don't think it would be appropriate" —
                                      # concessive `While`, and a norm carried
                                      # by `appropriate` rather than a modal
    "m0345": (DEONTIC, PARTIED),      # MISS DEONTIC ("most persuasion is
                                      # permitted by request"); FP DEFEATED
                                      # (contrastive `but` in a sample answer)
    "m0378": (CONTROL,),
    "m0403": (CONTROL,),
    "m0407": (DEONTIC,),
    "m0427": (DEONTIC, PARTIED),      # FP DEFEATED: "never to persuade the
                                      # user but rather to ensure clarity"
    "m0441": (PARTIED,),
    "m0506": (DEONTIC, PARTIED),
    "m0511": (PARTIED,),
    "m0521": (DEONTIC, PARTIED),
    "m0540": (DEONTIC,),
    "m0577": (CONTROL,),
}


def wilson(k, n, z=1.96):
    """Wilson score interval — used instead of the normal approximation
    because several of these cells have n < 15, where the normal interval
    runs off the end of [0, 1] and stops meaning anything."""
    if not n:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def validate(gold=None, rows=None) -> dict:
    """Per-category precision and recall of the classifier against HAND_GOLD.

    Weighted: each sampled clause stands for N_s/n_s clauses of its stratum,
    so an error in the tiny DEFEATED stratum does not count as much as an
    error in the big CONTROL one. The Wilson intervals are computed on the RAW
    sample counts and are therefore an approximation to the interval of the
    weighted estimate — stated here rather than left to be assumed.
    """
    gold = HAND_GOLD if gold is None else gold
    rows = load_clauses() if rows is None else rows
    by_id = {r["id"]: r for r in rows}
    st = strata(rows)
    n_s = {}
    for cid in gold:
        r = by_id.get(cid)
        if r is not None:
            n_s[stratum_of(r.get(TEXT_FIELD))] = n_s.get(
                stratum_of(r.get(TEXT_FIELD)), 0) + 1
    weight = {s: (len(st[s]) / n_s[s]) if n_s.get(s) else 0.0 for s in st}

    out = {}
    for cat in CATEGORIES:
        tp = fp = fn = 0.0
        rtp = rfp = rfn = 0
        for cid, truth in gold.items():
            r = by_id.get(cid)
            if r is None:
                continue
            w = weight.get(stratum_of(r.get(TEXT_FIELD)), 0.0)
            pred = cat in classify_clause(r)["categories"]
            true = cat in truth
            if pred and true:
                tp += w
                rtp += 1
            elif pred:
                fp += w
                rfp += 1
            elif true:
                fn += w
                rfn += 1
        out[cat] = {
            "precision": tp / (tp + fp) if tp + fp else 0.0,
            "recall": tp / (tp + fn) if tp + fn else 0.0,
            "ci_precision": wilson(rtp, rtp + rfp),
            "ci_recall": wilson(rtp, rtp + rfn),
            "n_pred": rtp + rfp, "n_gold": rtp + rfn,
            # The UNWEIGHTED sample figures, reported beside the weighted ones
            # because the intervals belong to these and not to those.
            "raw_precision": rtp / (rtp + rfp) if rtp + rfp else 0.0,
            "raw_recall": rtp / (rtp + rfn) if rtp + rfn else 0.0,
            "raw": {"tp": rtp, "fp": rfp, "fn": rfn},
        }
    agree = sum(1 for cid, truth in gold.items()
                if cid in by_id
                and set(classify_clause(by_id[cid])["categories"]) == set(truth))
    out["_exact_match"] = agree / len(gold) if gold else 0.0
    out["_n"] = len(gold)
    return out


# ==========================================================================
# cost — the SAME estimator as the full-corpus quote, never a re-derivation

def cost(rows, batch_size=8, provider="luna") -> dict:
    """What annotating exactly these clauses would cost.

    Routed through `annotate.estimate_cost` so the number is comparable, term
    for term, with the full-corpus $0.402 expected / $0.552 ceiling quote. A
    second costing path here would be a second set of assumptions and the
    comparison would stop being one.
    """
    import annotate
    return annotate.estimate_cost(rows=list(rows), batch_size=batch_size,
                                  provider=provider)


# ==========================================================================
# report

def report(rows=None, do_cost=True) -> str:
    rows = load_clauses() if rows is None else rows
    sizes = set_sizes(rows)
    tab = crosstab(rows)
    L = [f"GRAMMAR CANDIDATES — {len(rows)} clauses, classified from the "
         f"clause text alone", ""]
    L.append("SET SIZES (DEONTIC/DEFEATED/PARTIED overlap; CONTROL is "
             "exclusive)")
    for c in CATEGORIES:
        L.append(f"  {c:9s} {sizes[c]:4d}  ({100*sizes[c]/max(len(rows),1):.1f}%)")
    sel = selected(rows)
    L.append(f"  {'SELECTED':9s} {len(sel):4d}  (union of the first three)")
    b = defeater_breakdown(rows)
    L.append(f"  of DEFEATED, {b['but_only']} rest on a bare contrastive "
             f"`but` and {b['explicit']} on an explicit cue — and `but` is "
             f"where DEFEATED's false positives are")
    L.append("")
    L.append("CROSS-TAB vs clause_kind")
    L.append(f"  {'kind':14s} {'n':>4s} " +
             " ".join(f"{c:>9s}" for c in CATEGORIES))
    for k in sorted(tab, key=lambda k: -tab[k]["n"]):
        cell = tab[k]
        L.append(f"  {str(k):14s} {cell['n']:4d} " +
                 " ".join(f"{cell[c]:4d} {100*cell[c]/cell['n']:4.0f}%"
                          for c in CATEGORIES))
    warn = kind_disagreements(tab)
    if warn:
        L.append("")
        for w in warn:
            L.append("  !! " + w)
    L.append("")
    if do_cost:
        L.append("COST of annotating each set (annotate.estimate_cost, "
                 "batch 8)")
        L.append(f"  {'set':10s} {'clauses':>7s} {'calls':>6s} {'expected':>9s}"
                 f" {'ceiling':>8s}")
        for name, sub in (("FULL", rows), ("SELECTED", sel),
                          (DEONTIC, [r for r in rows if DEONTIC in
                                     classify_clause(r)["categories"]]),
                          (DEFEATED, [r for r in rows if DEFEATED in
                                      classify_clause(r)["categories"]]),
                          (PARTIED, [r for r in rows if PARTIED in
                                     classify_clause(r)["categories"]]),
                          (CONTROL, [r for r in rows if CONTROL in
                                     classify_clause(r)["categories"]])):
            if not sub:
                continue
            e = cost(sub)
            L.append(f"  {name:10s} {e['clauses']:7d} {e['calls']:6d} "
                     f"${e['usd']:8.3f} ${e['usd_ceiling']:7.3f}")
        L.append("")
    if HAND_GOLD:
        v = validate(rows=rows)
        L.append(f"HAND VALIDATION — {v['_n']} clauses adjudicated by hand "
                 f"over seed {GOLD_SEED}; exact-match "
                 f"{100*v['_exact_match']:.0f}%")
        L.append("  precision/recall are CORPUS estimates (stratum-weighted); "
                 "`raw` is the same on the 40 sampled clauses, and the "
                 "intervals belong to `raw`.")
        L.append(f"  {'category':10s} {'prec':>5s} {'raw':>5s} {'95% CI':>13s} "
                 f"{'recall':>6s} {'raw':>5s} {'95% CI':>13s} "
                 f"{'tp':>3s} {'fp':>3s} {'fn':>3s}")
        for c in CATEGORIES:
            r = v[c]
            L.append(f"  {c:10s} {r['precision']:5.2f} {r['raw_precision']:5.2f} "
                     f"[{r['ci_precision'][0]:.2f},{r['ci_precision'][1]:.2f}] "
                     f"{r['recall']:6.2f} {r['raw_recall']:5.2f} "
                     f"[{r['ci_recall'][0]:.2f},{r['ci_recall'][1]:.2f}] "
                     f"{r['raw']['tp']:3d} {r['raw']['fp']:3d} "
                     f"{r['raw']['fn']:3d}")
    else:
        L.append("HAND VALIDATION — not yet adjudicated (HAND_GOLD is empty). "
                 "The split is UNVALIDATED; do not spend against it.")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sample", type=int, default=None,
                    help="draw N clauses (stratified) and print them")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--category", default=None, choices=CATEGORIES,
                    help="restrict --sample to one category")
    ap.add_argument("--gold", action="store_true",
                    help="print the hand-adjudication draw, with its text")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-cost", action="store_true")
    # `argv=None` must fall through to sys.argv — passing [] here silently
    # ignored every command-line flag and printed the default report instead.
    a = ap.parse_args(argv)

    rows = load_clauses()

    if a.gold:
        for r in gold_sample(rows):
            c = classify_clause(r)
            print(f"--- {r['id']}  kind={r.get('kind')}  "
                  f"pred={','.join(c['categories'])}")
            print(f"    forces={c['forces']} defeaters={c['defeaters']} "
                  f"principals={c['principals']}")
            print(f"    {r[TEXT_FIELD]}")
        return

    if a.sample is not None:
        pool = rows
        if a.category:
            pool = [r for r in rows
                    if a.category in classify_clause(r)["categories"]]
        drawn = sample(pool, a.sample, seed=a.seed, stratify=not a.category)
        if a.json:
            print(json.dumps([r["id"] for r in drawn]))
        else:
            for r in drawn:
                c = classify_clause(r)
                print(f"{r['id']}  {','.join(c['categories']):28s} "
                      f"{r[TEXT_FIELD][:90]}")
        return

    if a.validate:
        print(json.dumps(validate(rows=rows), indent=1, sort_keys=True,
                         default=list))
        return

    if a.json:
        payload = {
            "clauses": len(rows),
            "sizes": set_sizes(rows),
            "crosstab": crosstab(rows),
            "selected": [r["id"] for r in selected(rows)],
            "gold_seed": GOLD_SEED,
        }
        if not a.no_cost:
            payload["cost"] = {
                "FULL": cost(rows), "SELECTED": cost(selected(rows))}
        if HAND_GOLD:
            payload["validation"] = validate(rows=rows)
        print(json.dumps(payload, default=list))
        return

    print(report(rows, do_cost=not a.no_cost))


if __name__ == "__main__":
    main()
