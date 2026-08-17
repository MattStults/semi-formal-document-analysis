#!/usr/bin/env python3
"""The five candidate fixes, each as a detector with the SAME signature.

    detect(item, oracle=None) -> list[(where, why)]

so `matrix.py` can run any subset ALONE or CUMULATIVELY without knowing what
any of them do. `oracle` is a cached one-bit model judge (see `oracle.py`); a
detector that does not need it ignores it, and a detector that needs it and
does not get it RAISES rather than silently degrading to its offline twin —
an offline fallback that scores as the live variant is how a measurement
becomes a fiction.

⛔ THE ANTI-RULE THAT MUST SURVIVE F1 (`prefer-polarity`, and F4 when it lands)
──────────────────────────────────────────────────────────────────────────────
`checks.polarity_mismatches` works for exactly one reason: `status` and
`read_back` are written INDEPENDENTLY by the translator, so when they disagree
the disagreement is evidence. Any change that makes `read_back` a RENDERING of
`status` — a template, a formatter, a post-hoc regeneration, "why is the
read-back not derived from the program, it would always be consistent" —
destroys the check completely and replaces a loud defect with a silent one:
the module then ships a WRONG `status` with a read-back that agrees with it,
and nothing in the pipeline can ever see it again.

    Do not machine-render `read_back` from `status`. Not for consistency, not
    for tidiness, not as a repair action, not as an autofix.

MEASURED evidence that this is not hypothetical: golden items GS11 and GS12 are
inversions where the read-back was flipped TOGETHER with the status, and every
polarity detector in this file — regex and general-model alike — scores 0/2 on
them. That is not a detector weakness to be tuned away. It is the exact failure
mode a rendered read-back would create for the WHOLE corpus.

The same reasoning is already written at `checks.polarity_findings`' docstring
(origin `stage4-detector`, deliberately not disclosable) and at
`schema.py`'s missing negative pole. This file is the third place, because F1
is the change most likely to tempt someone into it.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.dirname(os.path.dirname(HERE))
for _p in (HERE, PHASE1):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import checks       # noqa: E402
import population   # noqa: E402


class NeedsOracle(RuntimeError):
    pass


# ───────────────────────────── F1 — polarity ──────────────────────────────
# Target classes. P-REF calls it `inverted-modality`, P-GOLD calls the
# read-back-disagreeing subtype `prefer-polarity`. Both are carried: a detector
# is credited for either, and the two are reported separately because only one
# of them is within any polarity detector's reach (see the anti-rule above).
F1_CLASSES = {"inverted-modality", "prefer-polarity"}


def f1_regex(item, oracle=None):
    """BASELINE. `checks.polarity_mismatches` exactly as production runs it.

    ⚠️ ITS RECALL ON THIS SET IS IN-SAMPLE. The pattern was widened on
    2026-08-16 after the reference set found it at 4/5 — it was one alternation
    short (`should be avoided` present, `is to be avoided` absent). Whatever it
    scores here it scores having already been fitted to these very sentences,
    so its number carries NO out-of-sample guarantee. That is the entire reason
    a general variant is worth measuring even if it detects nothing new.
    """
    mod = item.module()
    if mod is None:
        return []
    return [(w, f"read-back says '{p}' but status is prefer on {a}")
            for w, a, p in checks.polarity_mismatches(mod)]


def f1_general(item, oracle=None):
    """CANDIDATE. One bit per `prefer` assert, from a general polarity judge.

    The question asked is document-independent and contains no corpus wording:

        "Does this sentence present <ACT> as something to do MORE of or LESS
         of?"  ->  FAVOUR | DISFAVOUR | NEITHER

    A `prefer` status is a claim of FAVOUR. DISFAVOUR is the mismatch. NEITHER
    is not a finding — a read-back that takes no side is not evidence, and
    counting it would convert an abstention into an accusation.

    ⛔ Reads `read_back` ONLY. Never `status`, never the act's own name beyond
    the gloss the read-back gives it. Handing the judge the status is the
    rendering mistake in interrogative form: it would answer with the status.

    ⭐ THE RESULT, AND IT IS A NEGATIVE ONE. MEASURED on both populations, this
    detector's extension is IDENTICAL to `f1_regex`'s: 5/5 on P-REF, 2/4 on
    P-GOLD, 0 false positives on both control strata. It buys NOTHING in
    detection.

    On the 36 unadjudicated modules it fires ONE extra time, on
    `l2653_2820_n004.asserts[1]`:

        read_back: "asking the user % is preferred only when uncertainty
                    persists after attempting context and trusted external
                    sources"

    Adjudicated here by reading the clause: the status `prefer` is CORRECT and
    the restriction lives in the rule's body, where it belongs. The judge read
    "only when" as disfavour. So the one measurable difference between the
    general judge and the regex is a FALSE POSITIVE.

    That does not settle it, and the honest statement of what is still open is:
    the regex's 8/8 is IN-SAMPLE (it was widened onto these very sentences on
    2026-08-16), while the general judge's 8/8 is OUT-of-sample. Two detectors
    agreeing on the fitting set tells you nothing about the next corpus. The
    case for F1-general is robustness, it is not measurable with the anchors
    available, and it costs a live call per prefer-assert plus one measured
    false positive. On this evidence F1-general is NOT worth its cost, and the
    finding is REDUNDANCY -- which the brief asked for by name.
    """
    if oracle is None:
        raise NeedsOracle("f1_general needs --oracle; no offline fallback")
    mod = item.module()
    if mod is None:
        return []
    out = []
    for i, a in enumerate(mod.asserts or []):
        if a.status != "prefer":
            continue
        rb = str(a.read_back or "")
        if not rb.strip():
            continue
        verdict = oracle.polarity(rb)
        if verdict == "DISFAVOUR":
            out.append((f"asserts[{i}]",
                        f"general polarity judge reads the read-back as "
                        f"DISFAVOUR toward {a.act}, status is prefer"))
    return out


# ─────────────────────── F2 — the over-assertion check ────────────────────
# CRITERIA.md's mechanical test, which no seat currently runs:
#   "is the subject of the main verb the model/assistant?"
# A module that emits `asserts` from a span whose sentences are all ABOUT
# something else — a section, a commentary, OpenAI, users, a model generation,
# a list of examples — has invented the norm.
F2_CLASSES = {"fact-as-deontic", "invented-obligation"}

#: Bearers that can carry a norm in this document. Everything else is a
#: subject that reports rather than requires.
_BEARER = re.compile(
    r"\b(the )?(assistant|model|models|chatgpt|it)\b", re.I)

#: Deontic modals. `may`/`can` are NOT here: CRITERIA.md §2 invented-obligation
#: records that "may" in this corpus is usually possibility, not licence
#: ("the assistant may sometimes encounter questions"), and treating it as a
#: grant is precisely the defect being detected.
_DEONTIC = re.compile(
    r"\b(must not|must|should not|should|shall not|shall|"
    r"is required to|are required to|is obliged to|never|always|"
    r"is not allowed to|is not permitted to)\b", re.I)

#: Explicit permission wording, which IS a grant.
_PERMISSION = re.compile(
    r"\b(is allowed to|are allowed to|is permitted to|are permitted to|"
    r"may write|may share|may provide|may refuse|can celebrate)\b", re.I)

#: Hedges that look like a grant and are not (CRITERIA.md §2, §3.3).
_HEDGE = re.compile(
    r"\b(exploring how to|we're exploring|we are exploring|considering|"
    r"may sometimes|might sometimes|is an example of|examples of|"
    r"notes that|demonstrates that|explains|establishes|emphasi[sz]es|"
    r"describes|reports)\b", re.I)


def _span_sentences(clause_id):
    """The ESTABLISHES claim plus the narrowed SOURCE TEXT, as sentences.

    These two are what the translator was shown, so they are the only honest
    surface for a document-grounded check. Nothing outside the prompt file is
    read.
    """
    txt = population.span_of(clause_id)
    if not txt:
        return []
    est = ""
    m = re.search(r"ESTABLISHES[^\n]*\n(.*?)\n\s*\n", txt, re.S)
    if m:
        est = m.group(1).strip()
    src = ""
    m = re.search(r"SOURCE TEXT[^\n]*\n(.*?)(?:\n\s*Write the module|\Z)",
                  txt, re.S)
    if m:
        src = m.group(1).strip()
    body = est + "\n" + src
    # ⚠️ NOT split on ':'. Doing so turned "Example: the assistant should give
    # approximate estimates" into the fragment "Example:", and the live bearer
    # judge — which is handed sentence[0] — was answering about a colon. Caught
    # by diffing the offline and live variants on the unadjudicated stratum:
    # 4 of F2-live's 5 extra flags there were fragments, not findings.
    parts = re.split(r"(?<=[.;!?])\s+|\n+", body)
    return [p.strip() for p in parts if p.strip()]


def _establishes(clause_id):
    """The node's ESTABLISHES claim, whole. The live bearer question's subject.

    One sentence chosen by a splitter is not the claim; the decomposer wrote
    this line to BE the one claim the module must express, so it is what the
    bearer question is about.
    """
    txt = population.span_of(clause_id)
    m = re.search(r"ESTABLISHES[^\n]*\n(.*?)\n\s*\n", txt or "", re.S)
    return m.group(1).strip() if m else ""


def _norm_bearing(sent):
    """True iff this sentence can license an `asserts` entry.

    The test is CRITERIA.md's, made mechanical: a deontic (or an explicit
    permission) whose bearer is the model/assistant, or a passive/imperative
    with no competing subject. A hedge anywhere in the sentence disqualifies it.
    """
    if _HEDGE.search(sent):
        return False
    m = _DEONTIC.search(sent) or _PERMISSION.search(sent)
    if not m:
        return False
    head = sent[:m.start()]
    # bearer named before the modal -> it is the subject of the main verb
    if _BEARER.search(head):
        return True
    # passive with no agent named before the modal ("Profanity should only be
    # used", "should be avoided") -- the bearer is the assistant by default.
    tail = sent[m.end():m.end() + 60]
    if re.match(r"\s*(only\s+)?be\s+\w+ed\b", tail):
        return True
    # a subject that is plainly not the assistant kills it
    if re.match(r"\s*(the |a |an |this )?(commentary|section|example|heading|"
                r"guidelines?|openai|we|users?|developers?|website|"
                r"outcome|creativity)\b", head.strip(), re.I):
        return False
    return False


def f2_over_assertion(item, oracle=None):
    """CANDIDATE, offline. Flags a module that asserts from a span that states
    no norm the model bears.

    Clause-level, not site-level: the finding is "this module should be
    ontology-only / should abstain", which is how both `fact-as-deontic` and
    `invented-obligation` present. Firing per-assert would multiply one finding
    into three and flatter the recall.
    """
    mod = item.module()
    if mod is None or not (mod.asserts or []):
        return []
    sents = _span_sentences(item.clause_id)
    if not sents:
        return []          # no span on disk -> abstain, never assume clean
    if any(_norm_bearing(s) for s in sents):
        return []
    return [("module", "the module emits %d asserts but no sentence in the "
             "narrowed span carries a deontic whose bearer is the "
             "model/assistant" % len(mod.asserts))]


#: A GOOD/BAD-marked comparison. ⚠️ DISCLOSURE: this guard was added AFTER
#: seeing F2's 2 false positives on P-REF (`l1707_1973_n006`,
#: `l1974_2125_n019`), so its P-REF number is FITTED and must not be quoted as
#: a measurement. P-GOLD is its out-of-sample check and the only honest number
#: for it. The guard is not ad hoc, though: CRITERIA.md §3.4 records the
#: corpus convention independently and BEFORE this harness existed --
#: "ontology-only rendering of an example is a corpus convention, not a
#: defect", and the anchor rates two such modules FAITHFUL. A GOOD/BAD contrast
#: IS the grant; there is no sentence to find because the norm is carried by
#: the marking.
_WORKED_EXAMPLE = re.compile(r"<!--\s*(GOOD|BAD)\b|\bGOOD:|\bBAD:", re.I)


def f2_over_assertion_wx(item, oracle=None):
    """F2 with the worked-example guard. See `_WORKED_EXAMPLE`'s disclosure."""
    if _WORKED_EXAMPLE.search(population.span_of(item.clause_id) or ""):
        return []
    return f2_over_assertion(item, oracle)


def f2_over_assertion_live(item, oracle=None):
    """CANDIDATE, live. The same question, asked of a model instead of a regex.

    Exists so the offline variant's recall can be separated from its ENGLISH:
    if the live judge finds items the regex misses, F2's ceiling is higher than
    the offline number and the regex is the limit, not the criterion.
    """
    if oracle is None:
        raise NeedsOracle("f2_over_assertion_live needs --oracle")
    mod = item.module()
    if mod is None or not (mod.asserts or []):
        return []
    claim = _establishes(item.clause_id)
    if not claim:
        return []
    if oracle.bearer(claim) == "NO":
        return [("module", "live bearer judge: the subject of the main verb "
                 "is not the model/assistant, yet the module emits %d asserts"
                 % len(mod.asserts))]
    return []


# ────────────────── F4 — the negative pole, as a MEASURABLE proxy ──────────
# F4 is a schema change and `schema.py` is guard-watched, so nothing here
# applies it. What CAN be measured offline is F4's REACH: the set of items
# whose defect exists only because `status` has no negative pole. An item is in
# reach when the module says `prefer` on an act its own read-back disfavours —
# i.e. exactly F1's positive set — because with a `disprefer` the translator
# had a correct encoding available and the inversion would not have been the
# only legal move.
#
# ⚠️ THIS IS WHY F1 AND F4 ARE NOT INDEPENDENT, and the matrix reports it as an
# interaction rather than as two separate gains. F4 PREVENTS what F1 DETECTS.
F4_CLASSES = set(F1_CLASSES)


def f4_reach(item, oracle=None):
    """Not a fix — the population F4 would remove from the corpus.

    Identical extension to `f1_regex` by construction, which is the finding:
    ships F4 and F1's positives go to zero, so F1's detection value after F4 is
    whatever F1 catches that F4 does not PREVENT. See `matrix.py`'s interaction
    row; do not read this as F4 scoring what F1 scores.
    """
    return f1_regex(item, oracle)


# ───────────────────────────── the registry ───────────────────────────────
#: name -> (fn, target classes, one-line description)
FIXES = {
    "F1-regex":   (f1_regex, F1_CLASSES,
                   "current hand-tuned English disfavour regex (BASELINE)"),
    "F1-general": (f1_general, F1_CLASSES,
                   "one-bit general polarity judgement on the read-back"),
    "F2":         (f2_over_assertion, F2_CLASSES,
                   "over-assertion: no model/assistant-borne deontic in span"),
    "F2-wx":      (f2_over_assertion_wx, F2_CLASSES,
                   "F2 + worked-example guard (FITTED on P-REF -- see note)"),
    "F2-live":    (f2_over_assertion_live, F2_CLASSES,
                   "over-assertion, bearer question asked of a model"),
    "F4-reach":   (f4_reach, F4_CLASSES,
                   "population a negative pole in `status` would PREVENT"),
}

#: The cumulative order, mechanistically justified rather than by score:
#: F1 first because it is already in production and is the baseline everything
#: else is an increment over; F2 second because it is a NEW class with no
#: overlap; F3 is a pipeline defect measured separately (it changes the corpus,
#: not the checks) and so cannot enter this stack; F4 last because it PREVENTS
#: F1's class and must be evaluated against a corpus F1 has already been run on.
#: ⚠️ A LADDER OF STACKS, not a list of additions, because F1-general REPLACES
#: F1-regex rather than joining it (they answer the same question of the same
#: field) while F2-wx JOINS. Modelling a replacement as a union would report
#: the union's specificity and credit F1-general with the regex's catches.
CUMULATIVE = [
    ("F1-regex (baseline, in production)",   ["F1-regex"]),
    ("F1-general REPLACES F1-regex",         ["F1-general"]),
    ("  + F2-wx",                            ["F1-general", "F2-wx"]),
    ("  + F2-wx, keeping F1-regex too",      ["F1-regex", "F1-general",
                                              "F2-wx"]),
]
