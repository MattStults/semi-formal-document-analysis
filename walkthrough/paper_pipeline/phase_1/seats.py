"""Stage 4's four review seats — 4a, 4b, 4c, 4d — and 4v, which validates them.

`STEP_stage4.md` §§4–6. `readback.py` composes the ONE artifact all four seats
judge; this module decides who is shown what, computes the four denominators,
adjudicates the replies, and writes a report in which four agreeing seats
cannot read as confirmation.

⭐ THE PROBLEM THIS MODULE IS SHAPED AROUND (§4). Four seats reading one
artifact fail together when the artifact is wrong, and unanimity then reads as
evidence. §4 names three shared reasons and this file answers each one
structurally rather than in prose:

  A. *they all read the same rendering* → **4c does not.** `build_4c_prompt`
     takes licensed items and cited clause text and HAS NO PARAMETER a
     rendering could arrive through. Renderer marks smuggled through the item
     text are refused. 4c is the anchor because it is not downstream of 4r.

  B. *the rendering echoes the clause* → **RB4's stamp.** Above the declared
     echo level, 4b's and 4d's verdicts are marked `non-evidential`: still
     asked, still recorded, and not countable as evidence. Never a gate — a
     threshold used to fail a clause would be a scoring instrument.

  C. *unanimity is read as confirmation* → **there is nowhere to write it.**
     `build_report` refuses a consensus field, an `n_passed`, a pass fraction;
     4a's verdict lives in `advisory` and `report_line` does not read it; and
     4d's `covered` is confirmed against stage 3's discrimination count — the
     only cross-check in stage 4 that is not itself a model judgement — with
     `unsupported` stamped wherever that number does not exist.

⛔ WHAT NONE OF THAT REACHES, stated rather than left for a reviewer: seats
agreeing CORRECTLY about a rendering faithful to a module faithful to a clause
the pipeline has misread at the document level. That is stage 5 / stage 9 work.

⛔ NOTHING HERE SPENDS. `judge` raises without an explicit `client_factory`,
exactly as `probe.label_situations` does and for the same reason: a default
that quietly reaches the network is the one mistake a revert cannot undo.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import re
import sys
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
WALKTHROUGH = os.path.dirname(os.path.dirname(HERE))
for _p in (HERE, WALKTHROUGH):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import checks                                                   # noqa: E402
import probe                                                    # noqa: E402
import readback                                                 # noqa: E402
import schema                                                   # noqa: E402
import translate                                                # noqa: E402


# ==========================================================================
#  refusals. A refusal is never a verdict and never a silent skip.
# ==========================================================================

class SeatError(RuntimeError):
    """Stage 4 declined to proceed. Never a verdict about a translation."""


class SeatRefused(SeatError):
    """A construction that would produce an unreadable result."""


class DisclosureRefused(SeatRefused, probe.DisclosureRefused):
    """Something carrying an expected answer tried to reach a seat prompt.

    ⭐ Subclasses `probe.DisclosureRefused` on purpose: stage 3 and stage 4
    defend the same perimeter, and a caller that catches one must catch the
    other.
    """


class NotAdjudicated(SeatRefused):
    """§5.3. A run failing the coverage rule is NOT ADJUDICATED — never
    hand-fixed, which is where results quietly change."""


# ==========================================================================
#  the closed verdict sets (seat-contract element 3)
# ==========================================================================

SEATS = ("4a", "4b", "4c", "4d")

UNCLEAR = "unclear"

#: ⭐ CLOSED, and `unclear` is in every one of them. §5.4: a judge that can
#: only answer yes or no answers yes; the abstention is what makes the
#: `unclear` RATE readable, and the rate is evidence about the brief or the
#: artifact, never about the document.
VERDICTS = {
    "4a": ("as-meant", "not-as-meant", UNCLEAR),
    "4b": ("faithful", "unfaithful", UNCLEAR),
    "4c": ("licensed", "unlicensed", UNCLEAR),
    "4d": ("covered", "not-conveyed", UNCLEAR),
}

#: ⭐ §6, AMENDED 2026-08-08. The two seats the one cross-seat check compares,
#: and the ONLY two. See `instrument_defects` for why these two and no others.
CROSS_CHECKED = ("4b", "4c")

#: ⭐ POLARITY, NOT VERDICT STRINGS. 4b and 4c answer different questions in
#: different words, so a check keyed on shared strings is a check that cannot
#: fire — which is exactly what the deleted `CONTRADICTIONS` was. What they do
#: share is a SIGN: each seat's closed set is one affirmative, one negative and
#: one abstention.
#:
#: ⛔ `unclear` maps to `None` and `None` is never a disagreement (§6's own
#: note). This project's standing position is that `unclear` gets the same
#: framing abstention gets at stage 1; making it fire an instrument review
#: prices honest hedging, and the pressure that creates is toward false
#: confidence — worse than a missed divergence because it is invisible.
POLARITY = {
    "faithful": True, "unfaithful": False,
    "licensed": True, "unlicensed": False,
    UNCLEAR: None,
}

#: The seats whose verdicts RB4 can stamp. 4c never reads a rendering, so an
#: echo score says nothing about it; 4a is advisory and is never evidence.
ECHO_STAMPED = ("4b", "4d")


# ==========================================================================
#  §5.5 — origins, and which side of the leak fence each sits on
# ==========================================================================

READBACK_STRUCTURAL = "readback-structural"
INERT_ORIGIN = "covered-but-inert"
SEAT_ORIGIN = {s: f"seat-{s}" for s in SEATS}

#: ⭐ §6. The 4b-vs-4c disagreement, and it is its OWN origin rather than a
#: `seat-4b`/`seat-4c` one, because it is not a finding about the translation
#: at all: it accuses the RENDERING. It is on the withheld side of the fence
#: for two reasons, and the second is the stronger:
#:   1. it names the item and the direction of the error, exactly like a seat
#:      finding;
#:   2. ⛔ sending it back would ask the MODEL to fix OUR renderer. There is
#:      nothing a re-translation can do about it, so a route that spends a
#:      stage-1 call on it spends money to learn nothing.
#: It goes to a human. See `route`.
INSTRUMENT_ORIGIN = "instrument-4b-4c"

#: ⭐ WHAT MAY REACH A TRANSLATOR. `readback-structural` is derived from the
#: module and the concept table alone: RB1–RB5, `readback-ungloss`, the
#: mechanical-vs-authored diff. No seat has spoken and no expected verdict
#: exists near it, exactly as for a stage-2 finding.
#:
#: ⛔ `seat-4b`/`4c`/`4d` and `covered-but-inert` are NOT here and must never
#: be: each one names what the right answer would have been. *"C2 is not
#: conveyed"* handed to a translator is an instruction to encode C2.
#: `seat-4a` is excluded for a different reason — it does not leak, it is the
#: seat the design calls never-evidence, and feeding it back is the model
#: grading itself into a loop.
#:
#: ⚠️ RECORDED GAP, and it is a real one. §8 requires `readback-structural` to
#: be added to `translate.DISCLOSABLE_ORIGINS` in this same diff. This build is
#: not permitted to edit `translate.py`, so the constant is EXTENDED here from
#: the canonical tuple rather than restated — a copy would drift — and
#: `render_findings_log` below renders the stage-4 log locally. Until the
#: canonical tuple is amended, `translate.render_error_log` WITHHOLDS a
#: readback-structural finding. That error is in the survivable direction (too
#: little disclosed, never too much) and it is visible in the log rather than
#: silent. ⛔ Do NOT "fix" it by relabelling the finding's origin as `schema`
#: or `link`: laundering an origin is precisely what `Finding.origin` being
#: required and never defaulted exists to prevent.
DISCLOSABLE_ORIGINS = tuple(translate.DISCLOSABLE_ORIGINS) + (READBACK_STRUCTURAL,)


def structural_finding(check_id, where, message, severity="error"):
    return checks.Finding(check_id, severity, where, message,
                          READBACK_STRUCTURAL)


def seat_finding(seat, where, message, severity="error"):
    if seat not in SEATS:
        raise SeatRefused(f"{seat!r} is not one of {SEATS}")
    return checks.Finding(f"readback-{seat}", severity, where, message,
                          SEAT_ORIGIN[seat])


def inert_finding(where, message):
    """⛔ `covered-but-inert` is a 4d verdict wearing a structural coat."""
    return checks.Finding("readback-covered-but-inert", "error", where,
                          message, INERT_ORIGIN)


def instrument_finding(where, message):
    """⛔ An accusation against the APPARATUS, withheld from every transcript.

    Same withholding as a seat finding, and one extra reason: there is no
    edit to the module that answers it.
    """
    return checks.Finding("readback-instrument-4b-4c", "error", where,
                          message, INSTRUMENT_ORIGIN)


def render_findings_log(attempts):
    """The stage-4 error log, with the SAME shape `translate.render_error_log`
    produces — shown errors, a count of notes, and a VISIBLE HOLE for anything
    withheld.

    ⚠️ It exists only because `translate.DISCLOSABLE_ORIGINS` cannot be amended
    in this build (see the constant above). `test_seats.py` pins that the two
    agree on a stage-2 finding, so this cannot drift into a second, laxer
    fence without a test dying.
    """
    out = []
    for label, findings in attempts:
        out.append(f"{label} failed these checks:")
        withheld = notes = shown = 0
        for f in findings:
            if f.origin not in DISCLOSABLE_ORIGINS:
                withheld += 1
                continue
            if f.severity != "error":
                notes += 1
                continue
            shown += 1
            out.append(f"  - [{f.check_id}] {f.where}: {f.message}")
        if not shown:
            out.append("  (no error-severity findings — nothing here is yours "
                       "to fix)")
        if notes:
            out.append(f"  ({notes} note(s) not shown: they are true of a "
                       f"correct module at this scope and are not faults)")
        if withheld:
            out.append(f"  - ({withheld} finding(s) withheld: they come from a "
                       f"later stage and would disclose an expected answer)")
        out.append("")
    out.append("Fix every one of them. Return the corrected module, complete.")
    return "\n".join(out)


def append_findings_to_transcript(transcript, findings):
    """⛔ THE FENCE, IN CODE RATHER THAN IN A CONVENTION (§5.5, §5.6)."""
    bad = [f for f in findings if f.origin not in DISCLOSABLE_ORIGINS]
    if bad:
        raise DisclosureRefused(
            f"{len(bad)} finding(s) of origin "
            f"{sorted({f.origin for f in bad})} may not enter a repair "
            f"transcript: they name what the right answer would have been")
    out = list(transcript)
    out.append({"role": "user",
                "content": render_findings_log([("stage 4", list(findings))])})
    return out


def route(findings, retranslations_used=0, max_retranslations=1):
    """⭐ RULING (§5.6): a SEAT finding discards the transcript and
    re-translates from a clean prompt, up to `max_retranslations`; then the
    clause is recorded `readback-<seat>` and carried, unrepaired, to a human.

    Rejected by name, all three as in `STEP_stage3.md` §5: *append the finding
    to the transcript* (the transcript is persistent per clause, so one
    appended finding lives there for the rest of that clause's life);
    *disclose the item but not the verdict* (for a binary-shaped item, naming
    it IS the verdict); *pass a count back* (a count plus an unchanged module
    is hill-climbing against a hidden answer key).

    ⛔ 4a routes NOWHERE. It is not withheld because it leaks.

    ⭐ AND THE INSTRUMENT BRANCH GOES FIRST, which is not a stylistic ordering.
    Whichever of 4b/4c returned the negative verdict ALSO emits its own seat
    finding, and a seat finding on its own routes `re-translate`. If the
    instrument branch did not win, every 4b-vs-4c disagreement would be handed
    straight back to the translator — a stage-1 call asking a model to fix a
    defect in OUR renderer, which it cannot see and cannot touch.
    """
    instrument = [f for f in findings if f.origin == INSTRUMENT_ORIGIN]
    if instrument:
        return probe.Routing("carry", (), "instrument-4b-4c")
    driving = [f for f in findings
               if f.origin in (SEAT_ORIGIN["4b"], SEAT_ORIGIN["4c"],
                               SEAT_ORIGIN["4d"], INERT_ORIGIN)]
    if driving:
        if retranslations_used < max_retranslations:
            # ⭐ zero bits carried: one stage-1 call from a clean prompt.
            return probe.Routing("re-translate", (), None)
        origin = sorted(f.origin for f in driving)[0]
        seat = origin.split("-")[-1] if origin != INERT_ORIGIN else "4d"
        return probe.Routing("carry", (), f"readback-{seat}")
    if any(f.origin == READBACK_STRUCTURAL and f.severity == "error"
           for f in findings):
        return probe.Routing("repair", (), None)
    return probe.Routing("none", (), None)


# ==========================================================================
#  §4.1 / §5 — the fences. Reused from stage 3 where the shape is the same.
# ==========================================================================

#: ⭐ REUSED, not restated. `probe._DISCLOSURE` is the wire-verified list of
#: patterns that must never reach a seat shown only the document: a coined
#: predicate signature, a rule, `asserts(`/`beats(`, the closure, the derived
#: status, a module header. 4b and 4d are exactly that kind of seat. Copying
#: the list would give the repo two fences to keep in step, and the one that
#: drifts is always the copy.
_MODULE_PATTERNS = tuple(probe._DISCLOSURE) + (
    # ⚠️ ONE ADDITION, and it is a real hole in the stage-3 list: a module
    # handed over as JSON matches none of those patterns. `{"outcome":
    # "translated", "clause_id": "m0217"}` carries the whole translation and
    # sails through every one of them.
    (re.compile(r'"(outcome|clause_id|claims|acts|concepts|ontology|asserts|'
                r'beats|defines|closure|requires|inputs|forbid_body)"\s*:'),
     "the module as JSON"),
)

#: Applies to EVERY seat, 4a and 4c included. `schema.BEHAVIOUR_NS` fences the
#: two namespaces at GENERATION; test 13's point is that it had no counterpart
#: at review, and this is it.
_UNIVERSAL_PATTERNS = (
    (re.compile(r"(?<![A-Za-z0-9_])(" + "|".join(sorted(schema.BEHAVIOUR_NS))
                + r")(?![A-Za-z0-9_])"),
     "a name from the BEHAVIOUR namespace"),
    (re.compile(r"\bbehaviou?rs?\b\s*:", re.I), "a behaviour"),
    (re.compile(r"\bpanel\b", re.I), "a panel label"),
    (re.compile(r"\breviewed\.json\b", re.I), "a panel label file"),
    (re.compile(r"(?<![A-Za-z0-9_])(" + "|".join(probe.LABELS)
                + r")(?![A-Za-z0-9_])"),
     "a stage-3 expected verdict"),
)

#: Only 4c. The marks are the renderer's own and nothing else emits them.
_RENDERING_PATTERNS = tuple(
    (re.compile(re.escape(mark)), "a rendering") for mark in
    (readback.GLOSS_OPEN, readback.ASP_MARK, readback.ACT_MARK,
     readback.UNGLOSS_MARK))


def _refuse(text, where, patterns):
    for pat, what in patterns:
        if pat.search(str(text)):
            raise DisclosureRefused(
                f"{where} carries {what}; stage 4 shows each seat exactly what "
                f"its question needs and nothing that names the answer")


# ==========================================================================
#  the briefs (seat-contract elements 1–3)
# ==========================================================================

#: ⭐ THE LIVE SHAPE (READBACK_SMOKE.md, gap 1). The prompt is the ONLY thing a
#: seat sees, so the brief must name the id `validate_judgements` will demand —
#: the first live call failed on exactly this: the prompt numbered the
#: sentences `0.`, `1.`, the brief said `"item": "..."`, and the seat echoed
#: the sentence text while the denominator held `concepts[0]`-style ids. Every
#: mock passed because mocks are written with the internal ids the live seat
#: is never shown. Each brief now SAYS what `item` is, and each prompt SHOWS
#: it (`build_4a_prompt`/`build_4b_prompt` print `[<id>]` beside each entry;
#: 4c already printed its ids; 4d's ids ARE the claim sentences).
_ANSWER = ('Answer with JSON: {{"judgements": [{{"item": "...", "verdict": '
           '"...", "reason": "..."}}]}} — EVERY item you were shown, exactly '
           'once, each with a non-empty reason. "item" is {item_rule} — copy '
           'it EXACTLY as shown. Verdicts: {verdicts}.')

BRIEFS = {
    "4a": """\
You wrote a formal module for one clause of a written specification. You are
shown the clause, your own module, and a MECHANICAL rendering of that module
back into English composed by a program from your module's own structure.

For each rendering, say whether it is what you meant:

  as-meant      the rendering says what your module was written to say
  not-as-meant  the rendering says something you did not mean
  unclear       you cannot tell from what you were shown

⚠️ Your answer is ADVISORY. It is recorded for a human and is never counted as
evidence that the translation is faithful, so answer honestly rather than
defensively; agreeing with yourself buys nothing here.

""" + _ANSWER.format(verdicts="as-meant, not-as-meant, unclear",
                     item_rule="the id shown in [brackets] beside each "
                               "rendering"),

    "4b": """\
You are shown ONE clause of a written specification and a set of English
sentences. You are NOT shown the program the sentences were rendered from, and
you must not speculate about it.

For each sentence, ask ONLY: does it assert anything the clause does not
support?

  faithful    everything the sentence asserts is supported by the clause
  unfaithful  the sentence asserts something the clause does not support
  unclear     you cannot tell from the clause alone

⭐ `unclear` is a real answer. A sentence you cannot judge against the clause is
not a faithful one, and saying so is more useful than a guess.

⚠️ The sentences are composed mechanically and read awkwardly. Awkward is not
unfaithful. Judge the content.

""" + _ANSWER.format(verdicts="faithful, unfaithful, unclear",
                     item_rule="the id shown in [brackets] beside each "
                               "sentence"),

    "4c": """\
You are shown items taken from a formal translation of a written
specification, each with the text of the clause it cites as its source.

For each item, ask ONLY whether that cited clause licenses it:

  licensed    the cited clause supports this item
  unlicensed  the cited clause does not support this item
  unclear     you cannot tell from the cited text

Two kinds of item are asked about differently, and each says which it is:

  TEXTUAL  does the cited clause CONTAIN this?
  ASSUMED  does the cited clause LICENSE this inference, and is the inference
           named?

⭐ An item naming an entity, category or sibling policy the cited clause never
introduces is `unlicensed`, however reasonable it sounds. That is the whole
question you are here for.

""" + _ANSWER.format(verdicts="licensed, unlicensed, unclear",
                     item_rule='the id printed after "item " in each entry'),

    "4d": """\
You are shown ONE clause of a written specification, a list of the distinct
claims someone read out of that clause, and ALL the English sentences a formal
translation of it renders back.

For each claim, ask ONLY: do the sentences convey it?

  covered       some sentence conveys this claim
  not-conveyed  no sentence conveys this claim
  unclear       you cannot tell

⚠️ You are judging whether the claim is CONVEYED, not whether it does any work.
A sentence can restate a claim without the underlying program ever depending on
it, and you have no way to see that from here; it is checked elsewhere.

""" + _ANSWER.format(verdicts="covered, not-conveyed, unclear",
                     item_rule="the claim sentence itself, as listed"),
}


def brief_sha(seat):
    """§6(2): an instrument-defect record carries the sha of each seat's brief,
    so *"the brief was under-informative"* is checkable against the brief that
    actually produced the two answers — and is ruled out before *"the renderer
    is wrong"* is believed."""
    return hashlib.sha256(BRIEFS[seat].encode("utf-8")).hexdigest()


def rendering_sha(rb):
    blob = "\n".join(f"{r.item}\t{r.layer}\t{r.text}" for r in rb.renderings)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ==========================================================================
#  §5.1 — the four denominators. Computed from the translation, NEVER
#          supplied by the judge.
# ==========================================================================

#: ⭐ RULING (§5.1): `Concepts` ARE in 4c's denominator. A concept row carries
#: `licence: textual, cites: m0037` — that is an assertion that the clause says
#: the term means this, judgeable under exactly the `textual` question.
#: ⛔ REJECTED BY NAME: *"concepts assert nothing, so exclude them"* — true of
#: the logic and false of the licence. `[RAN]` excluding them makes the whole
#: run's 4c denominator 12 → 1, and the two modules whose entire content is
#: vocabulary pass the provenance seat vacuously.
LICENSED_KINDS = ("concepts", "ontology", "asserts", "beats", "defines")


@dataclasses.dataclass(frozen=True)
class Denominator:
    seat: str
    ids: tuple
    excluded: dict = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True)
class LicensedDenominator:
    seat: str
    ids: tuple
    by_licence: dict
    judgeable: tuple


@dataclasses.dataclass(frozen=True)
class ClaimDenominator:
    seat: str = "4d"
    ids: tuple = ()
    #: ⛔ #14, and it is excluded BY NAME rather than by being forgotten. A
    #: `forbid_body` claim has no derivation and no read-back, so 4d would be
    #: asked whether a rendering that cannot exist conveys it. It is reported
    #: separately so that a clause whose only gap is a `forbid_body` claim
    #: cannot read as full coverage.
    excluded_forbid_body: tuple = ()

    def __post_init__(self):
        overlap = set(self.ids) & set(self.excluded_forbid_body)
        if overlap:
            raise SeatRefused(
                f"{sorted(overlap)} counted BOTH as a forbid_body claim and in "
                f"4d's denominator; a claim no case can demonstrate is not "
                f"judgeable against a rendering and must be excluded from it")


def _item_index(mod):
    """`concepts[0]` -> the item. One place, so every denominator agrees."""
    out = {}
    for kind in LICENSED_KINDS:
        for i, item in enumerate(getattr(mod, kind)):
            out[f"{kind}[{i}]"] = item
    return out


def denominator_4a(rb, r3=None):
    """The rendered set — R1 + R2 + R3, as §5.1 specifies.

    ⭐ R3 arrives as an optional argument rather than off `rb`, because
    `readback_r3` needs a stage-3 covering set and a solver run that plain
    rendering does not. A caller with no stage-3 result gets R1+R2 and the
    denominator SAYS SO in `excluded`, so "R3 was not supplied" can never read
    as "this module has no derivations" — the distinction §2.1 depends on.

    ⚠️ A situation that derives no verdict atom is NOT a derivation. It is
    carried as `no-derivation` and counted, never dropped: 8 of 18 covering-set
    situations across the stored modules derive a verdict, and reporting the
    other 10 as absent would overstate coverage by more than a third.
    """
    items = [r.item for r in rb.renderings]
    if r3 is None:
        return Denominator("4a", tuple(items),
                           {"r3-not-supplied": ("no stage-3 covering set was "
                                                "given, so no derivation is in "
                                                "this denominator",)})
    # ⛔ READ `readback_r3`'s REAL SHAPE. The first version of this read
    # `r3.derivations` / `d.item` / `d.nodes` — none of which exist. `ModuleR3`
    # carries `situations`; a `SituationR3` carries `derivations`; a
    # `Derivation` is (label, verdict, roots). So it was a NO-OP against every
    # object the repo builds, and it failed in the SILENT direction: a module
    # with real derivations produced ids identical to `r3=None`.
    #
    # ⚠️ Worse, the tests pinned a hand-written duck type nothing constructs —
    # including the one named "the vacuous-pass shape". A fixture that models
    # the type wrongly tests the fixture. `test_seats.py` now builds this from
    # an actual `render_r3` result.
    derived, empty = [], []
    for sit in getattr(r3, "situations", ()) or ():
        sid = getattr(sit, "situation_id", None)
        if sid is None:
            continue
        (derived if (getattr(sit, "derivations", ()) or ()) else empty).append(sid)
    excluded = {"no-derivation": tuple(empty)} if empty else {}
    return Denominator("4a", tuple(items) + tuple(derived), excluded)


def denominator_4b(rb, mod, r3=None):
    """The rendered set (R1+R2+R3), minus items whose licence is `world`.

    A `world` item does not rest on the clause, so *"does the rendering assert
    anything the clause does not support?"* has no answer for it and any answer
    a seat gives is noise.
    """
    index = _item_index(mod)
    keep, dropped = [], []
    # 4a already decides what R3 contributes and what it excludes; 4b filters
    # that set rather than re-deriving it, so the two cannot drift apart.
    base = denominator_4a(rb, r3)
    for name in base.ids:
        item = index.get(name)
        if item is not None and getattr(item, "licence", None) == "world":
            dropped.append(name)
        else:
            keep.append(name)
    excluded = {"world": tuple(dropped)}
    excluded.update(base.excluded or {})
    return Denominator("4b", tuple(keep), excluded)


def denominator_4c(mod, kinds=LICENSED_KINDS):
    """Every licensed item, partitioned by licence class (§5.2)."""
    if "concepts" not in kinds:
        raise SeatRefused(
            "a 4c denominator excluding `concepts` is refused: a concept row "
            "carries `licence: textual` and a citation, which IS an assertion "
            "that the clause says the term means this. Excluding them makes a "
            "module whose entire content is vocabulary pass the provenance "
            "seat vacuously")
    unknown = [k for k in kinds if k not in LICENSED_KINDS]
    if unknown:
        raise SeatRefused(f"{unknown} is not a licensed item kind")
    by_licence = {lic: [] for lic in schema.LICENCES}
    ids = []
    for kind in kinds:
        for i, item in enumerate(getattr(mod, kind)):
            iid = f"{kind}[{i}]"
            ids.append(iid)
            by_licence[item.licence].append(iid)
    by_licence = {k: tuple(v) for k, v in by_licence.items()}
    # ⛔ `world` is NOT judged by 4c (§5.2). It is checked deterministically for
    # marked-and-toggleable, which `schema.Licensed` already enforces, and a
    # seat asked *"does the cited clause contain this?"* about an item with no
    # citation would wrongly reject it — `m0255`'s working derivation rests on
    # exactly such an item.
    judgeable = by_licence["textual"] + by_licence["assumed"]
    return LicensedDenominator("4c", tuple(ids), by_licence, judgeable)


def denominator_4d(mod, forbid_body_claims=()):
    """The module's `claims` list, minus the `forbid_body` claims.

    ⚠️ ONE PLACE `STEP_stage4.md` CANNOT BE EXECUTED AS WRITTEN. §1 says
    `forbid_body` claims are excluded from the denominator *by name*, and
    NOTHING ON DISK LINKS a `claims` entry to a `forbid_body` entry: `claims`
    is a list of sentences, `forbid_body` a list of `(head, banned)` pairs, and
    no field joins them. So the mapping is SUPPLIED per clause — the same
    departure `probe_live.py` records for the act phrase — and a module that
    declares `forbid_body` without one is REFUSED. Guessing the join either
    drops a judgeable claim or admits an unjudgeable one, and both read as
    coverage.
    """
    claims = tuple(mod.claims)
    excluded = tuple(forbid_body_claims)
    unknown = [c for c in excluded if c not in claims]
    if unknown:
        raise SeatRefused(
            f"{unknown} named as forbid_body claim(s) but not in `claims`; the "
            f"exclusion is BY NAME and a name that matches nothing excludes "
            f"nothing while looking like it did")
    if mod.forbid_body and not excluded:
        raise SeatRefused(
            f"{mod.clause_id} declares {len(mod.forbid_body)} forbid_body "
            f"entr(ies) and no claim was named as one. A forbid_body claim has "
            f"no derivation and no read-back, so 4d would be asked whether a "
            f"rendering that cannot exist conveys it. Name the claim(s), or "
            f"say there are none")
    return ClaimDenominator("4d", tuple(c for c in claims if c not in excluded),
                            excluded)


def check_world_items(mod):
    """§5.2's third branch: the deterministic half, run rather than assumed."""
    out = []
    for iid, item in _item_index(mod).items():
        if getattr(item, "licence", None) != "world":
            continue
        out.append({"item": iid, "marked": True,
                    "toggleable": bool(item.toggleable)})
    return tuple(out)


# ==========================================================================
#  what each seat is shown
# ==========================================================================

@dataclasses.dataclass(frozen=True)
class SourceItem:
    """One licensed item as 4c sees it: the item, its licence, its citation.

    ⛔ NOT a rendering. 4c is the anchor precisely because it is not downstream
    of 4r (§4.1).
    """

    item: str
    licence: str
    cites: Optional[str]
    text: str
    cited_text: str = ""
    inference: Optional[str] = None


def _item_text(kind, item, clause_id):
    """The item in plain words — the module's own content, no renderer marks."""
    if kind == "concepts":
        return f"the term `{item.name}` (arity {item.arity}) means: {item.gloss}"
    if kind == "ontology":
        base = f"{item.atom} — {item.gloss}"
        return base + (f", when {item.body}" if item.body else "")
    if kind == "defines":
        return (f"clause {clause_id} brings {item.term} under {item.kind}")
    if kind == "asserts":
        base = f"clause {clause_id} {item.status}s the act {item.act}"
        return base + (f", when {item.body}" if item.body else "")
    if kind == "beats":
        base = (f"clause {item.sayer} says clause {item.winner} outranks "
                f"clause {item.loser}")
        return base + (f", when {item.body}" if item.body else "")
    raise SeatRefused(f"no 4c presentation for item kind {kind!r}")


def source_items(mod, denominator, corpus_texts, judgeable_only=True):
    index = _item_index(mod)
    ids = denominator.judgeable if judgeable_only else denominator.ids
    out = []
    for iid in ids:
        item = index[iid]
        kind = iid.split("[")[0]
        out.append(SourceItem(
            item=iid, licence=item.licence, cites=item.cites,
            text=_item_text(kind, item, mod.clause_id),
            cited_text=(corpus_texts or {}).get(item.cites, ""),
            inference=item.inference))
    return tuple(out)


def _entry_lines(renderings, ids, seat):
    """⭐ THE ID THE SEAT ANSWERS WITH, PRINTED BESIDE THE ENTRY IT NAMES.

    `ids`, when supplied, are the DENOMINATOR ids for these entries, in order —
    the live path (`plan_clause`) always supplies them, so what the prompt
    displays is exactly what `validate_judgements` accepts. Without them the
    entries are numbered `0.`, `1.` (the pre-fix shape, kept for direct
    callers) and `judge` maps a numeric reply back positionally.
    """
    renderings = tuple(renderings)
    if ids is None:
        return [f"  {i}. {t}" for i, t in enumerate(renderings)]
    ids = tuple(ids)
    if len(ids) != len(renderings):
        raise SeatRefused(
            f"{seat}: {len(ids)} item id(s) supplied for "
            f"{len(renderings)} entr(ies); a prompt whose displayed ids do "
            f"not pair one-to-one with its entries teaches the seat a "
            f"denominator that does not exist")
    return [f"  [{i}] {t}" for i, t in zip(ids, renderings)]


def build_4a_prompt(clause_text, module_json, renderings,
                    cross_reference_texts=(), ids=None):
    """The author, shown its own module and the mechanical rendering.

    ⚠️ The module fence deliberately does NOT run here. 4a IS the author; a
    fence that hid the module from it would leave no seat at all. The universal
    fence still runs: no behaviour, no panel label, no stage-3 verdict reaches
    any seat.
    """
    parts = [("the clause", clause_text), ("the module", module_json)]
    parts += [("a rendering", t) for t in renderings]
    parts += [("a cross-reference", t) for t in cross_reference_texts]
    for where, text in parts:
        _refuse(text, where, _UNIVERSAL_PATTERNS)
    if not renderings:
        raise SeatRefused("4a with no rendering to judge is a vacuous pass")
    out = ["THE CLAUSE", "", clause_text.strip(), ""]
    if cross_reference_texts:
        out += ["CLAUSES IT CROSS-REFERENCES", ""]
        out += [t.strip() + "\n" for t in cross_reference_texts]
    out += ["YOUR MODULE", "", module_json, "",
            "THE MECHANICAL RENDERING", ""]
    out += _entry_lines(renderings, ids, "4a")
    return "\n".join(out)


def build_4b_prompt(clause_text, renderings, cross_reference_texts=(),
                    ids=None):
    """⛔ 4b MUST NEVER SEE THE LOGIC. A reviewer shown the code grades the
    code, and 4b's whole value is that it has only the clause to judge against.

    ⚠️ An item id (`concepts[0]`) is NOT the logic: it names a slot, never a
    predicate, a rule or a gloss, and every `_MODULE_PATTERNS` shape needs the
    content the id deliberately omits. 4c has always shown its ids.
    """
    parts = [("the clause", clause_text)]
    parts += [("a rendering", t) for t in renderings]
    parts += [("a cross-reference", t) for t in cross_reference_texts]
    for where, text in parts:
        _refuse(text, where, _UNIVERSAL_PATTERNS)
        _refuse(text, where, _MODULE_PATTERNS)
    if not renderings:
        raise SeatRefused("4b with no rendering to judge is a vacuous pass")
    out = ["THE CLAUSE", "", clause_text.strip(), ""]
    if cross_reference_texts:
        out += ["CLAUSES IT CROSS-REFERENCES", ""]
        out += [t.strip() + "\n" for t in cross_reference_texts]
    out += ["THE SENTENCES", ""]
    out += _entry_lines(renderings, ids, "4b")
    return "\n".join(out)


def build_4c_prompt(items, allow_missing_citations=False):
    """⭐ THE ANCHOR SEAT. Note the signature: there is NO PARAMETER through
    which a rendering could be passed (§4.1, enforced not stated). If 4r is
    systematically wrong — a mis-substituted gloss, a dropped condition, a
    flipped polarity — 4a, 4b and 4d can be wrong together and 4c is
    unaffected.

    ⭐ BATCHED PER CLAUSE, not per item (§7): the coverage rule requires the
    seat to see the whole denominator anyway, and per-item calls would multiply
    the clause context by the item count.
    """
    if not items:
        raise SeatRefused("4c with an empty denominator is a vacuous pass")
    # ⚠️ A SEPARATE PASS, on purpose. Folded into the loop below, WHICH refusal
    # a caller sees would depend on item order, and a `world` item at index 3
    # would hide behind a missing citation at index 0.
    world = [it.item for it in items if it.licence == "world"]
    if world:
        raise SeatRefused(
            f"{world} is `world`-licensed and may not enter 4c's judgeable "
            f"set (§5.2): it rests on no clause, so *does the cited clause "
            f"contain this?* would reject a correct item. It is checked "
            f"deterministically for marked-and-toggleable")
    for it in items:
        _refuse(it.text, f"{it.item}'s presentation", _UNIVERSAL_PATTERNS)
        _refuse(it.text, f"{it.item}'s presentation", _RENDERING_PATTERNS)
        _refuse(it.cited_text, f"{it.item}'s cited clause text",
                _UNIVERSAL_PATTERNS)
        _refuse(it.cited_text, f"{it.item}'s cited clause text",
                _RENDERING_PATTERNS)
        if not allow_missing_citations and not it.cited_text.strip():
            raise SeatRefused(
                f"{it.item} cites {it.cites!r} and no text for it was "
                f"supplied; asking whether an absent clause licenses an item "
                f"buys an answer about nothing")
    out = ["THE ITEMS AND THEIR SOURCES", ""]
    for it in items:
        q = "TEXTUAL" if it.licence == "textual" else "ASSUMED"
        out.append(f"  item {it.item}   [{q}]")
        out.append(f"    the item: {it.text}")
        if it.licence == "assumed":
            out.append(f"    the named inference: {it.inference or '(none)'}")
        out.append(f"    cited clause {it.cites}:")
        out.append(f"      {it.cited_text.strip() or '(no text supplied)'}")
        out.append("")
    return "\n".join(out)


def build_4d_prompt(clause_text, renderings, claims,
                    cross_reference_texts=()):
    """⛔ THE CLAIMS LIST IS THE DENOMINATOR, NEVER THE MATERIAL (§3b, third
    instance). Handed the claims as though they were the renderings, 4d finds
    every claim self-evidently conveyed — `m0037` renders zero rules and would
    pass its own completeness check on its own claims list.
    """
    claims = tuple(claims)
    renderings = tuple(renderings)
    if not claims:
        raise SeatRefused("4d with no claims has no denominator")
    if not renderings:
        raise SeatRefused(
            "4d with no rendering to read is refused: `do these zero sentences "
            "convey the clause's claims?` is the one stage-4 question that "
            "fires on an empty module, and it fires for the wrong reason")
    overlap = sorted(set(renderings) & set(claims))
    if overlap:
        raise SeatRefused(
            f"{overlap} appears BOTH as a rendering and in the claims list; "
            f"handing 4d the claims as the material makes every claim "
            f"self-evidently conveyed")
    parts = [("the clause", clause_text)]
    parts += [("a rendering", t) for t in renderings]
    parts += [("a cross-reference", t) for t in cross_reference_texts]
    for where, text in parts:
        _refuse(text, where, _UNIVERSAL_PATTERNS)
        _refuse(text, where, _MODULE_PATTERNS)
    for c in claims:
        _refuse(c, "a claim", _UNIVERSAL_PATTERNS)
    out = ["THE CLAUSE", "", clause_text.strip(), ""]
    if cross_reference_texts:
        out += ["CLAUSES IT CROSS-REFERENCES", ""]
        out += [t.strip() + "\n" for t in cross_reference_texts]
    out += ["THE CLAIMS READ OUT OF IT", ""]
    out += [f"  {c}" for c in claims]
    out += ["", "EVERY SENTENCE THE TRANSLATION RENDERS BACK", ""]
    out += [f"  {i}. {t}" for i, t in enumerate(renderings)]
    return "\n".join(out)


# ==========================================================================
#  §5.3 — the validator, parameterised by how its denominator is computed
# ==========================================================================

@dataclasses.dataclass(frozen=True)
class Judgement:
    seat: str
    item: str
    verdict: str
    reason: str
    #: ⭐ RB4 / the stage-3 cross-check write HERE, never over the verdict. A
    #: design that dropped a stamped verdict would hide the measurement that
    #: produced the stamp.
    evidential: bool = True
    stamps: tuple = ()

    def to_json(self):
        return {"seat": self.seat, "item": self.item, "verdict": self.verdict,
                "reason": self.reason, "evidential": self.evidential,
                "stamps": list(self.stamps)}


def validate_judgements(seat, denominator_ids, judgements):
    """⭐ THE COVERAGE RULE. A run failing any of these is NOT ADJUDICATED."""
    ids = tuple(denominator_ids)
    if not ids:
        raise NotAdjudicated(
            f"{seat}: the denominator is empty. A vacuous 100 % is the failure "
            f"this whole stage is about — see RB5")
    got = [j.item for j in judgements]
    missing = [i for i in ids if i not in got]
    if missing:
        raise NotAdjudicated(
            f"{seat}: no judgement for {missing}; the denominator is computed "
            f"from the translation, not supplied by the judge, and the skipped "
            f"items are the hard ones")
    extra = [i for i in got if i not in ids]
    if extra:
        raise NotAdjudicated(
            f"{seat}: {extra} is not in the denominator — a hallucinated item, "
            f"or a mispaired artifact")
    if len(set(got)) != len(got):
        raise NotAdjudicated(f"{seat}: an item was judged twice")
    for j in judgements:
        if j.verdict not in VERDICTS[seat]:
            raise NotAdjudicated(
                f"{seat}: verdict {j.verdict!r} is not one of "
                f"{VERDICTS[seat]}")
        if not str(j.reason or "").strip():
            raise NotAdjudicated(
                f"{seat}: {j.item} carries no reason — an `unclear` with no "
                f"reason is a skip in disguise")
    return tuple(judgements)


# ==========================================================================
#  §2.4 RB4 and §3b — the two stamps
# ==========================================================================

def readback_stamps(rb):
    """Every reason a rendering-reading seat's verdict may not count.

    ⭐ THREE OF THEM, and the second and third were found by reviewing this
    file against `DEBUGGING_TIPS` §8 rather than by writing it:

      `non-evidential`  RB4 is at or above the declared echo level — the seat
                        is comparing the clause to itself.
      `echo-not-measured`  ⛔ NO CLAUSE QUOTE WAS SUPPLIED, so RB4 never ran.
                        Without this, a run with no quotes reports every
                        verdict as evidential — *a check that could not run
                        must not exit like a check that passed*, and RB4 is
                        exactly the check whose absence is invisible.
      `readback-check-failed`  RB1, RB2 or RB3 fired. A label survived into
                        the English, a condition was dropped, or a sign was
                        lost — and `readback.py` records those as FINDINGS
                        without changing the outcome, so the clause still
                        reaches a seat. It may still be worth asking; the
                        answer may not be counted.

    ⭐ Same discipline as RB4 throughout: STAMP, DO NOT FAIL. A threshold used
    to reject a clause is a scoring instrument, which open question 3 forbids.
    """
    out = []
    if rb.non_evidential:
        out.append("non-evidential")
    if rb.clause_echo is None:
        out.append("echo-not-measured")
    if not all(rb.checks[k] for k in ("RB1", "RB2", "RB3", "RB5")):
        out.append("readback-check-failed")
    return tuple(out)


def stamp_evidential(seat, judgements, rb):
    """⭐ RB4 IS REPORTED, NEVER USED TO FAIL. Above the declared echo level the
    seat is comparing the clause to itself, so its verdicts may not be counted
    as evidence that the translation is faithful — they still run and are still
    recorded, which is the honest use of a number that says *the two texts I am
    comparing are the same text*.

    ⭐ 4c is never stamped, and that is §4.1 paying off rather than an
    oversight: every stamp here is a defect in THE RENDERING, and 4c does not
    read the rendering. The anchor seat's verdict survives a bad read-back.
    """
    if seat not in ECHO_STAMPED:
        return tuple(judgements)
    marks = readback_stamps(rb)
    if not marks:
        return tuple(judgements)
    return tuple(dataclasses.replace(j, evidential=False,
                                     stamps=tuple(j.stamps) + marks)
                 for j in judgements)


def cross_check_4d(judgements, discrimination):
    """⭐ 4d's `covered` against stage 3's discrimination count (§3b).

    The one place a seat verdict is confirmed by something outside the seat
    system. `m0255`'s C3 is the worked case: two rules encode it, both fire,
    every rule-coverage criterion passes them, deleting them changes 0 of 144
    answer sets — and four seats correctly report the claim conveyed. *A
    redundant encoding of a claim reads as an encoding of the claim.*

    ⛔ Where stage 3 did not run there is no number, and an unavailable check
    must never read as a passed one: the verdict is stamped `unsupported`.
    ⛔ An ABSENT KEY is not a zero. A claim stage 3 never reached would
    otherwise be reported `covered-but-inert` — a finding about the module
    manufactured out of a missing measurement.
    """
    out, findings = [], []
    for j in judgements:
        if j.verdict != "covered":
            out.append(j)
            continue
        n = None if discrimination is None else discrimination.get(j.item)
        if n is None:
            out.append(dataclasses.replace(
                j, evidential=False,
                stamps=tuple(j.stamps) + ("unsupported",)))
            continue
        if n == 0:
            out.append(dataclasses.replace(
                j, stamps=tuple(j.stamps) + ("covered-but-inert",)))
            findings.append(inert_finding(
                j.item, f"4d reports {j.item!r} covered and stage 3 discriminates "
                        f"it in 0 situations: the claim is conveyed by a "
                        f"rendering and carried by no rule any case can tell "
                        f"apart"))
            continue
        out.append(j)
    return tuple(out), tuple(findings)


# ==========================================================================
#  §6 — the ONE cross-seat check: 4b vs 4c, on the same item
# ==========================================================================
#
# ⛔ WHAT USED TO BE HERE, AND WHY IT IS GONE (2026-08-08). A general
# cross-seat divergence machinery — `divergences`, `Divergence`, `Triage`,
# `promote`, `CONTRADICTIONS` — and it could never fire. `[RAN]` 0 records
# over all 81 legal verdict combinations, and 0 over all 255 combinations
# across every seat SUBSET. Each seat's closed verdict set is DISJOINT from
# every other's (all six pairs) and both members of every contradiction pair
# sat inside ONE seat, so the two halves of a pair could never appear in one
# item's verdict set. The five tests that pinned it built judgements
# `validate_judgements` refuses.
#
# ⭐ THE ROOT CAUSE IS A TRANSPOSITION, NOT A CODING ERROR. `03_pipeline.md`
# §6's divergence is between TWO REVIEWERS ANSWERING THE SAME QUESTION — its
# own example is *"one reviewer saying the paraphrase is faithful and another
# saying it is not"*. This file imported it as a mechanism across four seats
# asking DIFFERENT questions, which do not even share a unit: 4a and 4b judge
# the whole rendering, 4c judges one licensed item, 4d judges one claim. Two
# seats answering different questions differently is not a contradiction.
# `4b: faithful` and `4c: unlicensed` can both be true — a rendering can
# faithfully render an item that lacks a valid citation.


@dataclasses.dataclass(frozen=True)
class InstrumentDefect:
    """One item on which 4b and 4c disagree ⇒ an accusation against the
    RENDERING, carrying the provenance the accusation rests on.

    ⭐ THE PROVENANCE IS THE POINT, not bookkeeping. The diagnosis is *"the
    apparatus is wrong"*, so the two briefs and the rendering that produced
    the two answers are the artifacts a human has to be able to re-read.
    """

    item: str
    verdicts: dict
    reasons: dict
    brief_shas: dict
    rendering_sha: str
    origin: str = INSTRUMENT_ORIGIN

    def to_json(self):
        return {"item": self.item, "verdicts": dict(self.verdicts),
                "reasons": dict(self.reasons),
                "brief_shas": dict(self.brief_shas),
                "rendering_sha": self.rendering_sha,
                "origin": self.origin}


def instrument_defects(judgements_by_seat, brief_shas, rendering_sha):
    """⭐ 4b and 4c, opposite POLARITIES, one item ⇒ an INSTRUMENT defect.

    ⭐ WHY THIS PAIR AND NO OTHER, and it is a difference in kind rather than
    in degree. 4b is anchored to the RENDERING and never sees the code
    (`build_4b_prompt` refuses every `_MODULE_PATTERNS` shape). 4c is composed
    from the MODULE — `_item_text` builds it out of the module's own content
    and `build_4c_prompt` refuses any renderer mark — and 4c is never echo-
    stamped, which `stamp_evidential` and its test already pin. The two seats
    are looking at the same item through two different windows, and **the only
    thing standing between them is the rendering**. So a disagreement here is
    evidence that the INSTRUMENT is wrong, not that the translation is — which
    is why it routes to a human (`route`) and never back to the translator.

    ⛔ REJECTED BY NAME — *"compare every seat pair"*. 4a/4b judge the whole
    rendering, 4c one licensed item, 4d one claim. They ask different
    questions and do not share a unit; `4b: faithful` beside `4d:
    not-conveyed` is two true statements about one artifact, not a
    contradiction. That transposition is what made the deleted machinery dead.

    ⛔ REJECTED BY NAME — *"treat `unclear` as a divergence"*. See `POLARITY`.

    ⛔ NEITHER VERDICT IS REWRITTEN. The deleted machinery replaced both with
    `unclear` and stamped them `seat-divergence`. That destroys the one thing
    §4.1 buys: 4c is the anchor precisely because it is not downstream of the
    rendering, and erasing its verdict because a rendering-reading seat
    disagreed makes the anchor answerable to the thing it exists to be
    independent of. The disagreement is recorded ALONGSIDE both verdicts.
    """
    by_item = {}
    for seat in CROSS_CHECKED:
        for j in judgements_by_seat.get(seat, ()) or ():
            by_item.setdefault(j.item, {})[seat] = j
    out = []
    for item, per_seat in sorted(by_item.items()):
        if len(per_seat) != len(CROSS_CHECKED):
            continue
        pol = {}
        for seat, j in per_seat.items():
            if j.verdict not in POLARITY:
                raise SeatRefused(
                    f"{seat} returned {j.verdict!r} on {item!r} and POLARITY "
                    f"does not map it. An unmapped verdict read as an "
                    f"abstention is a check that silently stops firing — say "
                    f"which sign it carries or take it out of VERDICTS[{seat}]")
            pol[seat] = POLARITY[j.verdict]
        vals = [pol[s] for s in CROSS_CHECKED]
        if None in vals or vals[0] == vals[1]:
            continue
        out.append(InstrumentDefect(
            item=item,
            verdicts={s: j.verdict for s, j in per_seat.items()},
            reasons={s: j.reason for s, j in per_seat.items()},
            brief_shas={s: (brief_shas or {})[s] for s in per_seat
                        if s in (brief_shas or {})},
            rendering_sha=rendering_sha))
    return tuple(out)


# ==========================================================================
#  §5.4 — the `unclear` rate, with its denominator, printed even when zero
# ==========================================================================

def unclear_rate(judgements):
    js = list(judgements)
    n = len(js)
    u = sum(1 for j in js if j.verdict == UNCLEAR)
    return {"unclear": u, "denominator": n,
            "rate": (None if n == 0 else u / n)}


def render_unclear_rate(rate):
    if rate["denominator"] == 0:
        return "unclear-rate: NOT MEASURED — 0 judgements"
    return (f"unclear-rate: {rate['unclear']}/{rate['denominator']} = "
            f"{rate['rate']:.3f}")


_LENGTH_BUCKETS = ((80, "<=80"), (160, "81-160"), (320, "161-320"))


def _bucket(n, table, over):
    for edge, name in table:
        if n <= edge:
            return name
    return over


def unclear_split(judgements, rb):
    """⭐ §9's mitigation, and it is a measurement rather than an argument.

    Gluing glosses together with *"and"* and *"it is NOT the case that"*
    produces prose that is correct and ugly, and a seat may answer `unclear`
    because the SENTENCE is hard to parse. §5.4 would then read that as a brief
    defect when it is a RENDERER defect, and the pooled rate cannot tell them
    apart. A rate that rises with length is a renderer finding, investigated as
    one before any conclusion is drawn about a brief or a translation.
    """
    by_item = {r.item: r for r in rb.renderings}
    by_len, by_cond = {}, {}
    for j in judgements:
        r = by_item.get(j.item)
        if r is None:
            continue
        lb = _bucket(len(r.text), _LENGTH_BUCKETS, ">320")
        cb = str(len(readback.render_body(r.body, {})))
        for table, key in ((by_len, lb), (by_cond, cb)):
            slot = table.setdefault(key, {"unclear": 0, "denominator": 0})
            slot["denominator"] += 1
            slot["unclear"] += int(j.verdict == UNCLEAR)
    for table in (by_len, by_cond):
        for slot in table.values():
            slot["rate"] = slot["unclear"] / slot["denominator"]
    return by_len, by_cond


# ==========================================================================
#  §4.3 — the report. Four per-seat verdicts and NO aggregate.
# ==========================================================================

#: ⛔ Everything a reader could mistake for "the seats agreed, so it is right".
#: `probe.refuse_pass_rate` already covers pass rates and scores; this adds the
#: consensus family and the document-side fields §6 says must have nowhere to
#: be written.
_REFUSED_KEY = re.compile(
    r"consensus|unanim|agree|majorit|n_passed|quorum|"
    r"ambigu|interpretation|document[_ ]?(side[_ ]?)?finding", re.I)

REQUIRED_REPORT_KEYS = ("clause_id", "seats", "advisory", "unclear_rate",
                        "layer1_fraction", "forbid_body_claims_excluded",
                        "readback_stamps")


class ReportRefused(SeatRefused):
    pass


#: ⛔ THE ONLY VALUES THE SCAN BELOW DOES NOT READ, and each one is here for
#: the same reason: the report carries it VERBATIM from the module, the model
#: or the document, and refusing a report because someone else's words matched
#: would corrupt the record rather than protect it. `[RAN]` `m0134` declares a
#: concept called `agreed_scope`, so an unexempted value scan refuses that
#: clause's whole report on the word *agreed* — a live false positive, and the
#: kind that gets a fence disabled rather than fixed.
#:
#: ⚠️ None of these is a place an AGGREGATE could be written: every one is
#: per-item and attributed. Widening this tuple is a review finding — the
#: refusal's whole point is that `extra=` has nowhere to put "4/4 agreed".
_VERBATIM_VALUE_KEYS = (
    "reason", "reasons",          # a judge's own words, per item
    "text",                       # a rendering, composed from the module
    "message", "where",           # a finding, composed from an item id
    "item",                       # 4d's item ids ARE claim sentences
    "denominators",               # ditto — 4d's denominator is the claims list
    "forbid_body_claims_excluded",
    "clause_id", "quote", "gloss", "claims",
)


def _refused_strings(node, path="<root>", scan_values=True):
    """Every key name, and every non-verbatim string VALUE, anywhere in `node`.

    ⭐ §6 test 20's standard is *the route must not exist, not merely be
    discouraged*, and the first version of this scanned TOP-LEVEL KEY NAMES
    only. `{"summary": {"consensus": "4/4 agreed"}}` was accepted, and so was
    `{"overall": "ALL FOUR SEATS AGREE"}` — the words a reader would actually
    read, one nesting level down and in the value rather than the key.

    Keys are scanned at EVERY depth with no exemption. Values are scanned at
    every depth except under `_VERBATIM_VALUE_KEYS`.
    """
    if isinstance(node, dict):
        for k, v in node.items():
            yield f"{path}.{k}", str(k)
            yield from _refused_strings(
                v, f"{path}.{k}",
                scan_values and str(k) not in _VERBATIM_VALUE_KEYS)
    elif isinstance(node, (list, tuple)):
        for i, v in enumerate(node):
            yield from _refused_strings(v, f"{path}[{i}]", scan_values)
    elif isinstance(node, str) and scan_values:
        yield path, node


def refuse_aggregate(mapping):
    bad = sorted({where for where, text in _refused_strings(mapping)
                  if _REFUSED_KEY.search(text)})
    if bad:
        raise ReportRefused(
            f"{bad} is refused at construction: there is nowhere in a stage-4 "
            f"report to write `4/4 agreed`, and nowhere to write a claim about "
            f"the document. §3b's worked case is four correct verdicts on a "
            f"worthless module")
    try:
        probe.refuse_pass_rate(mapping)
    except ValueError as exc:
        raise ReportRefused(str(exc)) from exc


def validate_report(d):
    refuse_aggregate(d)
    missing = [k for k in REQUIRED_REPORT_KEYS if k not in d]
    if missing:
        raise ReportRefused(
            f"the report is missing {missing}. A field printed only when it is "
            f"non-zero cannot be read as `we measured it` — the `unclear` rate "
            f"and the layer-1 fraction are REQUIRED, and required means "
            f"present at zero")
    rate = d["unclear_rate"]
    if not isinstance(rate, dict) or "pooled" not in rate:
        raise ReportRefused("the `unclear` rate must carry a pooled entry")
    for key in ("rate", "denominator"):
        if key not in rate["pooled"]:
            raise ReportRefused(
                f"the `unclear` rate has no {key}: a rate with no population "
                f"size is unreadable, and 0.0000 over nothing is "
                f"indistinguishable from 0.0000 over a corpus")
    if "4a" in d["seats"]:
        raise ReportRefused(
            "4a's verdict may not appear among the evidential seats: it is the "
            "seat the design calls never-evidence, and the pass line must not "
            "be able to read it")
    return d


def refuse_discrimination_join(item_ids, discrimination):
    """⛔ THE JOIN KEY, CHECKED. Returns the supplied keys that match no item.

    4d's denominator ids are the module's CLAIM SENTENCES; stage 3 counts
    discrimination per claim ID (`C1`, `C2`, `C3`). Nothing joined the two key
    spaces, and a mismatched key is silent in the worst possible direction:
    every `covered` comes back `unsupported` — byte-identical to *"stage 3
    never ran"* — while the report asserts `stage3_discrimination_available:
    True` and the line a human reads carries no warning at all. `[RAN]` on
    `m0217`: 3 numbers supplied, 0 consulted, `available: True`.

    ⚠️ A TOTAL miss is refused; a PARTIAL one is counted and printed. Stage 3
    may legitimately not have reached a claim, and refusing that would be a
    check tightened past what it can know. A map that joins NOTHING is a
    mispaired artifact.

    ⛔ The guard is here rather than in `cross_check_4d`: that function is
    per-item, and an absent key for one item is correctly not a zero
    (`test_a_claim_missing_from_the_stage3_map_is_unsupported_not_inert`).
    Only the report sees the whole map beside the whole denominator. Same
    discipline as `denominator_4d`'s refusal of a `forbid_body` name that
    matches nothing — *a name that matches nothing excludes nothing while
    looking like it did*.
    """
    if not discrimination:
        return ()
    ids = set(item_ids)
    unmatched = tuple(sorted(k for k in discrimination if k not in ids))
    if ids and len(unmatched) == len(discrimination):
        raise ReportRefused(
            f"stage-3 discrimination was supplied for {sorted(discrimination)} "
            f"and NOT ONE of those keys is in 4d's denominator, so the join "
            f"produced nothing and every `covered` was stamped `unsupported` "
            f"— the same bytes as `stage 3 never ran`, under a report saying "
            f"the number was available. 4d is keyed on the claim SENTENCES "
            f"({sorted(ids)[:1]}…); re-key the map or pass "
            f"`discrimination=None` and say the check did not run")
    return unmatched


def build_report(clause_id, rb, judgements, denominators, extra=None,
                 instrument_defect_records=(), findings=(), discrimination=None):
    """⭐ FOUR PER-SEAT VERDICTS, 4a IN `advisory`, AND NO CONSENSUS FIELD."""
    judgements = dict(judgements or {})
    # ⛔ 4a IS NOT POOLED. §4.3(2) requires 4a's verdict to sit in a block the
    # pass/fail line does not read, and `report_line` prints the pooled
    # `unclear` rate: pooling 4a in made the one line a human reads move when
    # only 4a's answers changed — the docstring's *"it does not read
    # `advisory`"* was true of the KEY and false of the NUMBER. §5.4 also makes
    # the rate evidence about the brief or the artifact, and 4a is the author
    # grading itself. Its own rate is kept, per seat, in `by_seat`.
    pooled = [j for s, js in judgements.items() if s != "4a" for j in js]
    by_len, by_cond = unclear_split(pooled, rb)
    d4d = denominators.get("4d") if denominators else None
    unmatched = refuse_discrimination_join(
        [j.item for j in judgements.get("4d", ())], discrimination)
    layer1 = ([r.layer for r in rb.renderings] or [])
    d = {
        "clause_id": clause_id,
        "readback_outcome": rb.outcome,
        "seats": {s: [j.to_json() for j in judgements[s]]
                  for s in ("4b", "4c", "4d") if s in judgements},
        # ⭐ 4a is HERE and nowhere else. `report_line` does not read this key.
        "advisory": {"4a": [j.to_json() for j in judgements.get("4a", ())]},
        "denominators": {s: list(getattr(dn, "judgeable", dn.ids))
                         for s, dn in (denominators or {}).items()},
        "forbid_body_claims_excluded": list(
            getattr(d4d, "excluded_forbid_body", ()) or ()),
        "unclear_rate": {
            "pooled": unclear_rate(pooled),
            "by_seat": {s: unclear_rate(js) for s, js in judgements.items()},
            "by_rendering_length": by_len,
            "by_condition_count": by_cond,
        },
        "layer1_fraction": (0.0 if not layer1
                            else sum(1 for l in layer1 if l == 1) / len(layer1)),
        "echo": {"clause_mean": rb.clause_echo,
                 "declared_level": rb.echo_level_declared,
                 "per_item": dict(rb.echo)},
        "non_evidential": bool(rb.non_evidential),
        # ⭐ WHY a verdict is stamped, printed beside the stamp. RB1–RB3 fire as
        # findings without changing `readback.py`'s outcome, so a clause with a
        # surviving label still reaches a seat; without this the report would
        # carry the stamp and not the reason for it.
        "readback_checks": dict(rb.checks),
        "readback_stamps": list(readback_stamps(rb)),
        "stage3_discrimination_available": discrimination is not None,
        # ⭐ DEBUGGING_TIPS §2: the denominator printed beside the number. A
        # supplied key that joins no claim consulted nothing, and *available*
        # said otherwise.
        "stage3_discrimination_keys_unmatched": list(unmatched),
        # ⭐ §6. Recorded BESIDE both verdicts, never in place of them.
        "instrument_defects": [x.to_json() for x in instrument_defect_records],
        "findings": [dataclasses.asdict(f) for f in findings],
        "renderings": [{"item": r.item, "layer": r.layer, "stamp": r.stamp,
                        "text": r.text} for r in rb.renderings],
    }
    d.update(extra or {})
    return validate_report(d)


def report_line(d):
    """The one line a human reads. ⛔ It does not read `advisory`."""
    bits = [f"stage4 {d['clause_id']}  readback={d['readback_outcome']}"]
    for seat in ("4b", "4c", "4d"):
        js = d["seats"].get(seat)
        if js is None:
            bits.append(f"{seat}=not-run")
            continue
        counts = {}
        for j in js:
            counts[j["verdict"]] = counts.get(j["verdict"], 0) + 1
        vec = " ".join(f"{n} {v}" for v, n in sorted(counts.items()))
        ev = "" if all(j["evidential"] for j in js) else " (NON-EVIDENTIAL)"
        bits.append(f"{seat}=[{vec}]/{len(js)}{ev}")
    if d["readback_stamps"]:
        bits.append("READ-BACK STAMPS: " + ", ".join(d["readback_stamps"]))
    bits.append(render_unclear_rate(d["unclear_rate"]["pooled"]))
    bits.append(f"layer 1: {d['layer1_fraction']:.2f} of renderings")
    if not d["stage3_discrimination_available"]:
        bits.append("stage-3 discrimination UNAVAILABLE — every 4d `covered` "
                    "is `unsupported`")
    elif d.get("stage3_discrimination_keys_unmatched"):
        bits.append(f"{len(d['stage3_discrimination_keys_unmatched'])} stage-3 "
                    f"discrimination key(s) match no claim and confirmed "
                    f"nothing")
    if d["forbid_body_claims_excluded"]:
        bits.append(f"{len(d['forbid_body_claims_excluded'])} forbid_body "
                    f"claim(s) NOT JUDGEABLE HERE and excluded from 4d's "
                    f"denominator")
    if d["instrument_defects"]:
        # ⛔ NOT "the run is not adjudicated". Nothing here stops the run being
        # read: both verdicts stand and both are printed above. What it says is
        # WHERE the defect is and WHO it goes to — a human, because there is no
        # edit to the module that answers it.
        bits.append(f"{len(d['instrument_defects'])} 4b/4c INSTRUMENT "
                    f"defect(s) — the rendering is accused, routed to a human, "
                    f"never to the translator")
    return "   ·   ".join(bits)


# ==========================================================================
#  the seam — one seat, one call, driven from outside
# ==========================================================================

#: A judgement reply is a short JSON array, not a module. The stage-1 cap
#: (16,384) prices a whole translation.
SEAT_MAX_TOKENS = 4096


def proceeds_to_a_seat(rb):
    """⛔ RB5 and `readback-ungloss` are gates BEFORE any model is called.

    `no-readable-content` is an OUTCOME, never a pass; a module with an empty
    read-back set would otherwise be reported faithful by four agreeing seats
    that read nothing. And a symbol with no written meaning cannot have its
    definition rendered, which is the whole mechanism.

    ⚠️ On the modules stored today this blocks half of them, and the number is
    reported rather than relaxed (`OPEN_QUESTIONS.md` Q-6 is Matt's to rule
    on). Relaxing `readback-ungloss` to get more modules through would put
    predicate NAMES in front of the seats, which is failure mode #4 inside the
    artifact all four of them read.
    """
    return rb.outcome == "rendered"


def _reply_item(raw, ids, seat=None):
    """The denominator id a reply names — in any shape the prompt displays.

    ⭐ THE LIVE SHAPE, second half (READBACK_SMOKE.md gap 1). The prompt is the
    only thing a seat sees, so anything it legitimately displays as an id must
    adjudicate: the id itself (what every mock speaks), the id wrapped in the
    `[brackets]` the prompt prints it in, or — FOR 4a/4b ONLY — the 0-based
    index of the entry, the shape their pre-fix prompts taught, kept so a
    stored reply replayed through `judge` still adjudicates.

    ⛔ The digit fallback is SCOPED BY SEAT (consolidated_fix_review.md F1,
    2026-08-12): 4d's prompt numbers the SENTENCES, not the claims — a digit
    reply mapped positionally onto the claims denominator silently
    re-attributes every verdict to the wrong claim; 4c's prompt displays real
    item ids and never numbers anything, so a digit there is the seat
    inventing a shape it was never taught. For both, the digit is returned
    unchanged and `validate_judgements` refuses it BY NAME.
    """
    s = str(raw).strip()
    if s in ids:
        return s
    # a denominator id with edge whitespace (a `claims` sentence ending in a
    # space) can never round-trip: this function strips the reply, so the
    # exact match above misses FOREVER (consolidated_fix_review.md F4,
    # 2026-08-12). Stripped-to-stripped matching closes it, guarded to fire
    # only while stripping keeps the denominator unambiguous.
    stripped = {i.strip(): i for i in ids}
    if len(stripped) == len(ids) and s in stripped:
        return stripped[s]
    if len(s) >= 2 and s[0] == "[" and s[-1] == "]" and s[1:-1].strip() in ids:
        return s[1:-1].strip()
    if (seat in ("4a", "4b")
            and s.isdigit() and int(s) < len(ids) and s not in ids):
        return ids[int(s)]
    return s


def judge(seat, prompt, denominator_ids, client_factory=None):
    """One seat, one batched call. ⛔ `client_factory` is REQUIRED."""
    if seat not in SEATS:
        raise SeatRefused(f"{seat!r} is not one of {SEATS}")
    if client_factory is None:
        raise SeatError(
            f"seat {seat} needs an explicit `client_factory`; stage 4 is not "
            f"authorised to spend and must be driven through the seam")
    client = client_factory()
    raw = client.complete_messages(BRIEFS[seat],
                                   [{"role": "user", "content": prompt}])
    data = json.loads(raw) if isinstance(raw, str) else raw
    ids = tuple(denominator_ids)
    js = tuple(Judgement(seat, _reply_item(r["item"], ids, seat),
                         str(r["verdict"]),
                         str(r.get("reason", "")))
               for r in data["judgements"])
    return validate_judgements(seat, ids, js)


@dataclasses.dataclass(frozen=True)
class ClausePlan:
    clause_id: str
    module: object
    readback: object
    denominators: dict
    prompts: dict
    items: tuple
    ids: dict


def plan_clause(mod, rb, clause_text, corpus_texts, forbid_body_claims=(),
                cross_reference_texts=(), allow_missing_citations=False):
    """Everything four seats need, built and fenced. NO MODEL CALL."""
    if not proceeds_to_a_seat(rb):
        raise SeatRefused(
            f"{mod.clause_id}: read-back outcome {rb.outcome!r} — the clause "
            f"reaches no seat. Paying for a judgement of nothing and reporting "
            f"it as a pass is what RB5 exists to stop")
    d4a = denominator_4a(rb)
    d4b = denominator_4b(rb, mod)
    d4c = denominator_4c(mod)
    d4d = denominator_4d(mod, forbid_body_claims)
    text_by_item = {r.item: r.text for r in rb.renderings}
    items = source_items(mod, d4c, corpus_texts)
    prompts = {
        "4a": build_4a_prompt(clause_text,
                              json.dumps(json.loads(mod.model_dump_json()),
                                         indent=1, ensure_ascii=False),
                              tuple(text_by_item[i] for i in d4a.ids),
                              cross_reference_texts, ids=d4a.ids),
        "4b": build_4b_prompt(clause_text,
                              tuple(text_by_item[i] for i in d4b.ids),
                              cross_reference_texts, ids=d4b.ids),
        "4c": build_4c_prompt(items,
                              allow_missing_citations=allow_missing_citations),
        "4d": build_4d_prompt(clause_text,
                              tuple(text_by_item[i] for i in d4a.ids),
                              d4d.ids, cross_reference_texts),
    }
    return ClausePlan(
        clause_id=mod.clause_id, module=mod, readback=rb,
        denominators={"4a": d4a, "4b": d4b, "4c": d4c, "4d": d4d},
        prompts=prompts, items=items,
        ids={"4a": d4a.ids, "4b": d4b.ids, "4c": d4c.judgeable,
             "4d": d4d.ids})


def run_clause(plan, client_factories, discrimination=None,
               max_retranslations=1, retranslations_used=0):
    """The four seats, then 4v: validate, cross-check, diverge, report."""
    rb = plan.readback
    judgements, findings = {}, []
    for seat in SEATS:
        factory = (client_factories or {}).get(seat)
        if factory is None:
            continue
        js = judge(seat, plan.prompts[seat], plan.ids[seat],
                   client_factory=factory)
        js = stamp_evidential(seat, js, rb)
        if seat == "4d":
            js, inert = cross_check_4d(js, discrimination)
            findings.extend(inert)
        judgements[seat] = js
    for seat, js in judgements.items():
        for j in js:
            if j.verdict in ("unfaithful", "unlicensed", "not-conveyed",
                             "not-as-meant"):
                # ⚠️ A STAMPED verdict still emits its finding and still routes.
                # The stamp says the verdict may not count as evidence that the
                # translation is FAITHFUL; it does not make a negative verdict
                # safe to ignore. The stamps ride along so the human triaging
                # the re-translation can see what the seat was working from.
                mark = f" [{', '.join(j.stamps)}]" if j.stamps else ""
                findings.append(seat_finding(
                    seat, f"{plan.clause_id}.lp",
                    f"{seat} returned {j.verdict} on {j.item}{mark}"))
    # ⭐ §6. AFTER the seat findings, and it does not touch `judgements`: an
    # instrument defect is recorded beside both verdicts, never over them.
    defects = instrument_defects(
        judgements, {s: brief_sha(s) for s in SEATS}, rendering_sha(rb))
    for d in defects:
        findings.append(instrument_finding(
            d.item, f"4b returned {d.verdicts['4b']} and 4c returned "
                    f"{d.verdicts['4c']} on {d.item}. 4b reads only the "
                    f"rendering and 4c reads only the module, so the rendering "
                    f"is the only thing between them"))
    rep = build_report(plan.clause_id, rb, judgements, plan.denominators,
                       instrument_defect_records=defects, findings=findings,
                       discrimination=discrimination)
    rep["routing"] = dataclasses.asdict(route(
        findings, retranslations_used, max_retranslations))
    return validate_report(rep)


# ==========================================================================
#  §7 — cost, measured off the real prompts rather than guessed
# ==========================================================================

def estimate_clause_usd(plan, price_per_mtok, chars_per_token,
                        max_tokens=SEAT_MAX_TOKENS):
    """Worst case for ONE clause: every input char billed at the full rate,
    every reply at its cap.

    ⚠️ There is no repair turn here and therefore no triangular term — a seat
    is asked once and its answer is adjudicated or refused, never argued with.
    That is the one place `DEBUGGING_TIPS` #14's under-charge cannot arise.
    ⛔ An unpriced provider counts as OVER budget, never as free.
    """
    if not price_per_mtok:
        raise SeatRefused(
            "no price_per_mtok: an unpriced call counts as OVER budget, never "
            "as free")
    pin, pout = price_per_mtok
    in_chars = sum(len(BRIEFS[s]) + len(p) for s, p in plan.prompts.items())
    in_tok = in_chars / float(chars_per_token)
    out_tok = max_tokens * len(plan.prompts)
    return {"clause_id": plan.clause_id, "calls": len(plan.prompts),
            "input_chars": in_chars, "input_tokens": int(in_tok),
            "output_tokens_worst": out_tok,
            "usd": (in_tok / 1e6) * pin + (out_tok / 1e6) * pout}


# ==========================================================================
#  the offline driver. ⛔ It cannot spend: there is no --live and no client.
# ==========================================================================

def _load_corpus_quotes():
    """`{clause_id: judgeable clause text}` — through `readback.clause_text`,
    so a node-corpus row yields its narrowed span text and never the packed
    translator prompt (READBACK_SMOKE.md gap 3). Verbatim for plain rows."""
    import link
    return readback.clause_texts(link.load_clauses())


#: Where `config.json` says the price table lives, resolved from HERE.
PROVIDERS_JSON = os.path.join(HERE, "..", "..", "..", "semi-formal-experiment",
                              "providers.json")


def most_expensive_provider(path=None):
    """⭐ `(name, (in, out))` — the MAXIMUM priced row, read rather than typed.

    `STEP_stage4.md` §7 says *"frontier-tier seats are priced from
    `providers.json` at run time"*, and the frontier price was a hard-coded
    `(5.0, 30.0)` literal — `sol`'s price, while the table's maximum is `fable`
    at `(10.0, 50.0)`. So the printed worst case was BELOW the worst case, on
    the one project with a hard ledger ceiling. `estimate_clause_usd` already
    rules that *an unpriced call counts as OVER budget, never as free*; this is
    the same rule applied to a priced one.

    ⛔ An unreadable or unpriced table REFUSES rather than falling back to a
    literal. A guessed price on a budget number is the anti-conservative
    direction `DEBUGGING_TIPS` #14 cost this repo a run to learn.

    ⚠️ Ranked on the OUTPUT rate, tie-broken on input: every seat reply is
    billed at the 4096-token cap and output dominates the worst case.
    """
    path = path or PROVIDERS_JSON
    try:
        rows = json.load(open(path, encoding="utf-8"))
    except Exception as exc:                                   # noqa: BLE001
        raise SeatRefused(
            f"no price table at {path} ({exc}); stage 4 will not print a "
            f"frontier cost from a literal typed into this file — that is how "
            f"a printed worst case ends up below the real one") from exc
    priced = [(r["name"], tuple(r["price_per_mtok"])) for r in rows
              if isinstance(r, dict) and r.get("price_per_mtok")]
    if not priced:
        raise SeatRefused(f"{path} prices nothing; an unpriced call counts as "
                          f"OVER budget, never as free")
    return max(priced, key=lambda nv: (nv[1][1], nv[1][0]))


def survey(runs_dir=None, price_per_mtok=(0.14, 0.28), chars_per_token=4.0,
           frontier=None, max_tokens=SEAT_MAX_TOKENS,
           per_judgement_tokens=40):
    """⭐ THE MEASURED COST OF A LIVE RUN, off the artifact that actually
    renders — `OPEN_QUESTIONS.md` Q-3 wants a number, not a guess.

    ⛔ It also reports how many stored modules never reach a seat, and why.
    §7's honest picture: a pipeline reporting *"3 of 4 passed stage 4"* over
    the last run would be reporting that three clauses had nothing to read
    back. Reported, never relaxed.
    """
    import glob
    runs_dir = runs_dir or os.path.join(HERE, "runs")
    frontier_name = "(supplied)"
    if frontier is None:
        frontier_name, frontier = most_expensive_provider()
    quotes = _load_corpus_quotes()
    rows, planned = [], []
    # ⛔ THIS GLOB USED TO BE `m*.json` AND WAS SILENTLY BLIND TO THE ENTIRE
    # GRAPH CORPUS (2026-08-15). Clause ids are `m0217`; GRAPH NODE ids are
    # `l1_170_n056`. Measured on
    # `resolve_runs/graph_v2/translation_sample/runs`: `m*.json` matched 0
    # modules and this function reported "TOTAL 0 (0 reach a seat)" — which
    # reads as "nothing to review", not as "I cannot see your corpus". Stage 4
    # had therefore never judged a single graph node, and `--cost` priced a
    # live run at zero. With the ids admitted: 722 modules, 323 reaching a
    # seat.
    #
    # ⭐ Matched by ID SHAPE, not by a widened wildcard, and the difference
    # matters: `l*.json` would also swallow `<id>.version.json` and
    # `<id>.transcript.json`, which are sidecars rather than modules — they
    # fail `schema.validate` and would be counted as `stage-2-invalid`,
    # inflating the "never reach a seat" figure this function exists to report
    # honestly. The pattern below admits exactly the two module namings and
    # nothing else. A third naming needs a line here; that is deliberate, so
    # the next corpus cannot go unseen in silence.
    module_globs = ("m*.json", "l*_n*.json")
    paths = sorted(
        p for pat in module_globs
        for p in glob.glob(os.path.join(runs_dir, "*", pat))
        if not p.endswith((".version.json", ".transcript.json")))
    for path in paths:
        try:
            obj = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(obj, dict):
            continue
        try:
            mod = schema.validate(obj)
        except Exception as exc:                              # noqa: BLE001
            rows.append({"path": path, "outcome": "stage-2-invalid",
                         "why": str(exc)[:70]})
            continue
        rb = readback.render_module(
            mod, clause_quote=quotes.get(mod.clause_id))
        row = {"path": path, "clause_id": mod.clause_id, "outcome": rb.outcome,
               "renderings": len(rb.renderings),
               "layer1": sum(1 for r in rb.renderings if r.layer == 1),
               "echo": rb.clause_echo}
        if proceeds_to_a_seat(rb):
            try:
                plan = plan_clause(mod, rb, quotes.get(mod.clause_id, ""),
                                   quotes, allow_missing_citations=True)
            except SeatRefused as exc:
                row["outcome"] = "plan-refused"
                row["why"] = str(exc)[:90]
                rows.append(row)
                continue
            flash = estimate_clause_usd(plan, price_per_mtok, chars_per_token,
                                        max_tokens)
            front = estimate_clause_usd(plan, frontier, chars_per_token,
                                        max_tokens)
            judgements = sum(len(v) for v in plan.ids.values())
            row.update({"frontier_provider": frontier_name,
                        "frontier_price_per_mtok": list(frontier),
                        "input_chars": flash["input_chars"],
                        "input_tokens": flash["input_tokens"],
                        "judgements": judgements,
                        "usd_worst_flash": flash["usd"],
                        "usd_worst_frontier": front["usd"],
                        # ⚠️ AN ASSUMPTION, labelled as one: reply length is
                        # not measured because nothing has been run. The worst
                        # case above is the number a budget decision uses.
                        "usd_likely_flash":
                            (flash["input_tokens"] / 1e6) * price_per_mtok[0]
                            + (judgements * per_judgement_tokens / 1e6)
                            * price_per_mtok[1],
                        "usd_likely_frontier":
                            (flash["input_tokens"] / 1e6) * frontier[0]
                            + (judgements * per_judgement_tokens / 1e6)
                            * frontier[1]})
            planned.append(row)
        rows.append(row)
    return rows, planned


def render_survey(rows, planned):
    out = ["stage 4 — what the stored modules can actually pay for", ""]
    by_outcome = {}
    for r in rows:
        by_outcome[r["outcome"]] = by_outcome.get(r["outcome"], 0) + 1
    for k, v in sorted(by_outcome.items()):
        out.append(f"  {k:<20} {v}")
    out.append(f"  {'TOTAL':<20} {len(rows)}   "
               f"({len(planned)} reach a seat)")
    out.append("")
    out.append(f"{'clause':<8}{'items':>6}{'judg':>6}{'in tok':>8}"
               f"{'echo':>7}{'lay1':>6}   worst flash / frontier"
               f"   ·   likely flash / frontier")
    for r in planned:
        echo = "n/a" if r["echo"] is None else f"{r['echo']:.2f}"
        out.append(
            f"{r['clause_id']:<8}{r['renderings']:>6}{r['judgements']:>6}"
            f"{r['input_tokens']:>8}{echo:>7}{r['layer1']:>6}   "
            f"${r['usd_worst_flash']:.4f} / ${r['usd_worst_frontier']:.4f}"
            f"   ·   ${r['usd_likely_flash']:.5f} / "
            f"${r['usd_likely_frontier']:.4f}")
    if planned:
        for key, label in (("usd_worst_flash", "WORST, flash"),
                           ("usd_worst_frontier", "WORST, frontier"),
                           ("usd_likely_flash", "likely, flash"),
                           ("usd_likely_frontier", "likely, frontier")):
            tot = sum(r[key] for r in planned)
            out.append(f"  {label:<18} ${tot:.4f} over {len(planned)} clause(s)"
                       f"   ⇒ ${tot / len(planned):.4f}/clause")
        out.append("")
        out.append(f"⛔ `frontier` is the MOST EXPENSIVE row in "
                   f"providers.json — {planned[0].get('frontier_provider')} at "
                   f"{tuple(planned[0].get('frontier_price_per_mtok') or ())} "
                   f"$/Mtok — read at run time, never a literal. A printed "
                   f"worst case below the real worst case is the one error a "
                   f"hard ledger cap cannot survive.")
        out.append("⚠️ WORST is the number a budget decision uses: every reply "
                   "at its 4096-token cap. `likely` assumes 40 output tokens "
                   "per judgement and is an ASSUMPTION — nothing has been run, "
                   "so no reply length has been measured.")
        out.append("⛔ No repair turn exists at stage 4, so there is no "
                   "triangular transcript term (DEBUGGING_TIPS #14). A "
                   "re-translation under §5.6 is a STAGE-1 cost.")
    return "\n".join(out)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cost", action="store_true",
                    help="what a live stage-4 run would cost, measured off "
                         "the modules on disk. Free; makes no call.")
    ap.add_argument("--runs", default=None)
    a = ap.parse_args(argv)
    rows, planned = survey(a.runs)
    print(render_survey(rows, planned))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
