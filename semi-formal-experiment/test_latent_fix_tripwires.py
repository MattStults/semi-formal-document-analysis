"""LATENT-FIX TRIPWIRES — the mechanical half of `LATENT_FIX_REGISTRY.md`.

The registry parks designs that are deliberately NOT built (LF-1, the example-kind
taint rule; LF-2, the interpretation layer). Each entry names a TRIGGER that should
promote it to active work, and each entry specifies DETECTION tripwires so the latent
case fails LOUDLY instead of being silently mispriced. Neither entry's tripwires were
implemented, which the registry itself flags:

    "A registry of parked designs whose tripwires never fire is a filing cabinet, not a
    safety net: the entries would be found only by someone already reading this file,
    which is exactly the person who does not need the reminder."
    -- LATENT_FIX_REGISTRY.md, IMPLEMENTATION DEBT (coordinator, 2026-08-05)

This module is that safety net. It is test-only and deterministic: it reads
`modelspec_clauses.json`, the closed cycle records under `cycles/`, and the reader
prototype directory. It makes no model call and writes nothing.

SCOPE IS DELIBERATELY MINIMAL. LF-1's REVISIT note ("keep the DETECTION check MINIMAL
for now ... revisit the tripwire strategy if it costs more than it is worth, or if it is
not catching enough") governs this file. Do not grow it into a framework; grow it on
evidence that it missed something.

WHAT IS HERE
  LF-1.1  population pin over the example-kind clause set (digest, not 183 inline ids)
  LF-1.2  load-bearing pin (m0176/m0300/m0467) -- SKIPPED, needs the S3b artifact
  LF-1.3  adjudication shape-flag: example-kind flips need an explicit disposition
  LF-2.1  ambiguity-language scan over cycle records
  LF-2.2  reader-surface pin over the reader prototype
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
CYCLES = os.path.join(HERE, "cycles")
REPO_ROOT = os.path.dirname(HERE)
#: the reader prototype named by LF-2 trigger 1.
READER_PROTOTYPE = os.path.join(REPO_ROOT, "site", "spec-reader-test")

REGISTRY = "LATENT_FIX_REGISTRY.md"


def _rel(path: str) -> str:
    return os.path.relpath(path, REPO_ROOT)


# --------------------------------------------------------------------------
# Is there an interpretation artifact yet?
# --------------------------------------------------------------------------
# LF-2 is parked precisely because there is none. Several tripwires below are
# conditioned on its absence, so they retire themselves the day it lands rather
# than sitting here as stale assertions about a world that moved on.
_INTERPRETATION_ARTIFACT_CANDIDATES = (
    "interpretations.json",
    "interpretation_set.json",
    "interpretations",
)


def _interpretation_artifact() -> str | None:
    for name in _INTERPRETATION_ARTIFACT_CANDIDATES:
        p = os.path.join(HERE, name)
        if os.path.exists(p):
            return _rel(p)
    return None


# ==========================================================================
# LF-1 -- example-kind distinct taint rule (designer ruling D3)
# ==========================================================================

#: sha256 over "\n".join(sorted(ids)) of every clause with kind == "example" in
#: `modelspec_clauses.json`, as vetted by D3_EXAMPLE_CLAUSE_ENUMERATION.md
#: (2026-08-05): 183 clauses, 0 wrong-result cases, 0 undefined compositions.
#:
#: A DIGEST, not the 183 ids -- LF-1's REVISIT note says explicitly "NOT the full
#: 183-clause pin". The digest fails on exactly the same events (a new or
#: re-annotated example clause) at one line of maintenance.
LF1_EXAMPLE_POPULATION_SHA256 = (
    "2d85e187e7abe1b39698c2af52080d3a811657715bf38d49a22182642c1ff0af"
)

#: The three clauses whose correct outcome requires the seat to attribute the
#: PROTECTED party rather than the chain recipient (D3 enumeration §1).
LF1_LOAD_BEARING = ("m0176", "m0300", "m0467")


def _clauses() -> list:
    with open(os.path.join(HERE, "modelspec_clauses.json")) as fh:
        return json.load(fh)["clauses"]


def _example_ids() -> list:
    return sorted(c["id"] for c in _clauses() if c.get("kind") == "example")


def test_lf1_example_kind_population_is_the_enumerated_one():
    """LF-1 DETECTION 1 -- POPULATION PIN.

    Catches a FUTURE example-kind instance that the D3 enumeration never vetted.
    """
    ids = _example_ids()
    got = hashlib.sha256("\n".join(ids).encode()).hexdigest()
    assert got == LF1_EXAMPLE_POPULATION_SHA256, (
        "example-clause population changed since the D3 enumeration -- re-run the "
        "enumeration before trusting example-clause pricing (see "
        f"{REGISTRY} LF-1). Now {len(ids)} example-kind clauses, digest {got}; the "
        f"enumerated set digests to {LF1_EXAMPLE_POPULATION_SHA256}. D3 vetted 183 "
        "clauses and found uniform attribution produced 0 wrong results over exactly "
        "that set; a clause outside it has been vetted by nobody. Re-running the "
        "enumeration and updating this digest is the fix; editing the digest alone "
        "is not."
    )


def test_lf1_load_bearing_examples_are_still_example_kind():
    """LF-1 DETECTION 2, the half that is checkable today.

    The surfacing assertion needs S3b (see the skip below); that these three
    clauses are still in the population the rule applies to does not.
    """
    ids = set(_example_ids())
    missing = [c for c in LF1_LOAD_BEARING if c not in ids]
    assert not missing, (
        f"attribution-load-bearing example clauses {missing} are no longer "
        f"kind == 'example' -- the D3 finding that these three need the PROTECTED "
        f"party attributed (not the chain recipient) was made about example-clause "
        f"pricing. See {REGISTRY} LF-1."
    )


def test_lf1_load_bearing_examples_surface_via_the_attributed_protected_party():
    """LF-1 DETECTION 2 -- LOAD-BEARING PIN. NOT IMPLEMENTABLE YET.

    The assertion is: m0176/m0300/m0467 surface for a third-party query via the
    attributed PROTECTED party rather than the chain recipient. Evaluating it
    requires per-atom harm-bearer attribution, which lives in S3b's FROZEN
    ATTRIBUTION ARTIFACT (`S3B_REDESIGN.md` §5.3, §7.1; task spec in
    `S3B_ATTRIBUTION_TASK_DESIGN.md`). That build does not exist and the artifact
    is not on disk, so there is nothing to assert against.

    This skip is deliberate and named. A silently absent test would leave LF-1's
    second tripwire looking implemented when it is not.
    """
    pytest.skip(
        "S3b frozen attribution artifact not built -- no per-atom harm-bearer "
        "attribution on disk, so the LF-1 load-bearing surfacing pin "
        "(m0176/m0300/m0467 via the attributed protected party) cannot be "
        f"evaluated. Implement it WITH the S3b build; see {REGISTRY} LF-1 "
        "DETECTION 2 and S3B_REDESIGN.md §5.3."
    )


#: LF-1 DETECTION 3 -- ADJUDICATION SHAPE-FLAG.
#:
#: Registered dispositions for cycles that already carry example-kind flips. The
#: registry wants each such flip explicitly disposed of (confirm-uniform, or promote
#: LF-1 to active work) rather than silently absorbed. This is keyed by CYCLE rather
#: than per flip because the disposition below is genuinely one ruling covering all of
#: them, and because closed cycle directories are frozen records.
#:
#: ⚠️ ADDING AN ENTRY HERE IS A RULING, NOT A SILENCER. A new cycle that produces
#: example-kind flips must have those flips dispositioned -- against the document, by a
#: seat -- and the disposition recorded in the CYCLE, with this entry pointing at it.
#: If the answer is "uniform attribution mispriced this one", that is LF-1's TRIGGER
#: firing: promote LF-1 to OUTSTANDING_WORK.md. Never add an entry to make this test
#: green.
LF1_EXAMPLE_FLIP_DISPOSITIONS = {
    "decoration-blind-join-2026-08-04": (
        "PRE-D3. Closed 2026-08-04, before the D3 ruling (2026-08-05) fixed uniform "
        "attribution, and its one example-kind flip (m0207) is inside the 183-clause "
        "population that D3_EXAMPLE_CLAUSE_ENUMERATION.md then vetted end-to-end: 0 "
        "wrong-result cases, 0 undefined compositions. Disposition: confirm-uniform, "
        "by the enumeration rather than per-flip."
    ),
    "patient-pricing-2026-08-04": (
        "PRE-D3, and the cycle that MOTIVATED D3. Closed 2026-08-04 (REVERT). Its "
        "example-kind flips include m0275 and m0466, the two dossiers the D3 "
        "enumeration read for atom/chain shape; all of them sit inside the vetted "
        "183. Disposition: confirm-uniform, by the enumeration. The separate "
        "m0108 boundary finding is an LF-2 interpretation (I-01), not an LF-1 "
        "attribution defect."
    ),
}


def _flip_index_rows():
    """(cycle_name, row) for every recorded flip in every cycle."""
    for path in sorted(glob.glob(os.path.join(CYCLES, "*", "flip_dossiers",
                                              "index.jsonl"))):
        cycle = os.path.basename(os.path.dirname(os.path.dirname(path)))
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    yield cycle, json.loads(line)


def test_lf1_example_kind_flips_carry_an_explicit_disposition():
    """LF-1 DETECTION 3 -- ADJUDICATION SHAPE-FLAG.

    Flags example-kind flips whose cycle has no registered LF-1 disposition. This
    is a SUPERSET of the registry's "finding-(i) shape" (>=1 situation atom + >=1
    chained act): computing that shape needs the annotation corpus and
    `grammar.parse_name`, which is more machinery than LF-1's REVISIT note allows
    today. Over-flagging is the safe direction -- it asks for a disposition on a
    few extra flips; under-flagging misses the case the tripwire exists for.
    """
    example = set(_example_ids())
    unregistered = sorted({
        (cycle, row["clause_id"])
        for cycle, row in _flip_index_rows()
        if row.get("clause_id") in example
        and cycle not in LF1_EXAMPLE_FLIP_DISPOSITIONS
    })
    assert not unregistered, (
        "example-kind flip(s) with no registered LF-1 disposition: "
        + ", ".join(f"{c}/{cid}" for c, cid in unregistered)
        + ". An example-kind flip is an LF-1 candidate and must be explicitly "
        "disposed of -- confirm-uniform against the document, or promote LF-1 to "
        f"active work -- never silently absorbed (see {REGISTRY} LF-1 DETECTION 3). "
        "Record the disposition in the cycle, then add the cycle to "
        "LF1_EXAMPLE_FLIP_DISPOSITIONS citing it."
    )


def test_lf1_dispositions_still_describe_live_cycles():
    """A disposition for a cycle that no longer exists is dead weight that would
    hide the day someone re-uses the name. Fail rather than rot."""
    live = {c for c, _ in _flip_index_rows()}
    stale = sorted(set(LF1_EXAMPLE_FLIP_DISPOSITIONS) - live)
    assert not stale, (
        f"LF1_EXAMPLE_FLIP_DISPOSITIONS names cycles with no recorded flips: "
        f"{stale}. Remove the entry (and say why in the diff) rather than leaving a "
        "disposition covering nothing."
    )


# ==========================================================================
# LF-2 -- the interpretation layer
# ==========================================================================

#: The definitional-ambiguity markers named by LF-2 DETECTION 1, verbatim.
LF2_MARKERS = (
    "under-determines",
    "genuine ambiguity",
    "both readings",
    "boundary",
    "seat defect",
)


def _lf2_scan_paths() -> list:
    """The three record classes LF-2 names, and only those.

    `decision.json` and `flip_verdicts*.json` are scanned WHOLE rather than
    field-by-field: the registry says "justifications" and "reasons", but a ruling
    written into an adjoining free-text field is exactly as unregistered, and a
    field allowlist is one rename away from scanning nothing.
    """
    paths = []
    paths += glob.glob(os.path.join(CYCLES, "*", "decision.json"))
    paths += glob.glob(os.path.join(CYCLES, "*", "flip_verdicts*.json"))
    paths += glob.glob(os.path.join(CYCLES, "**", "*_SEAT_DEFECT_REVIEW.md"),
                       recursive=True)
    return sorted(set(paths))


def _lf2_hits() -> dict:
    """{key: excerpt} for every ambiguity-marker hit in the scanned records.

    The key is `<repo-relative path>::<marker>::<sha12 of the containing line>`.
    Path + marker alone would let an edited line keep its registration; the line
    digest means a re-worded ruling comes back for a fresh look. These records are
    frozen once their cycle closes, so the digest is stable in practice.
    """
    hits = {}
    for path in _lf2_scan_paths():
        rel = _rel(path)
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                low = line.lower()
                for marker in LF2_MARKERS:
                    if marker in low:
                        sha = hashlib.sha256(
                            line.strip().encode()).hexdigest()[:12]
                        key = f"{rel}::{marker}::{sha}"
                        hits.setdefault(key, _excerpt(line, marker))
    return hits


def _excerpt(line: str, marker: str, width: int = 90) -> str:
    low = line.lower()
    i = low.index(marker)
    start = max(0, i - width // 2)
    text = re.sub(r"\s+", " ", line[start:i + len(marker) + width // 2]).strip()
    return ("..." if start else "") + text + "..."


# ⚠️⚠️ THIS IS NOT A FLOOR, AND IT DOES NOT GET LOWERED. ⚠️⚠️
#
# Every entry below is a definitional-ambiguity marker in a cycle record that is
# KNOWN and accounted for. The test fails on anything NOT here, which is the point:
# a NEW ruling made on a definitional boundary is LF-2 trigger 4, "the sharpest
# signal available", and it should stop someone.
#
# Adding an entry means exactly one of two things, and you must say which in the WHY:
#   (a) the interpretation is REGISTERED -- cite its id (once an interpretation
#       artifact exists, cite the id in it; until then, cite the OUTSTANDING_WORK.md
#       backlog entry, e.g. I-01), or
#   (b) it is CONSCIOUSLY DEFERRED -- and the deferral is a ruling someone signed.
# It never means "the test went red so I quieted it". If entries start accumulating
# for reason (b), LF-2's trigger has fired and the layer wants building; that is the
# finding, not a maintenance chore.
#
# `LF2_KNOWN_HITS_PIN` below must be edited in the same diff as any addition, so
# growth appears in the diff as a deliberate number change rather than a new line in
# a long dict. (It pins THIS hand-maintained allowlist -- never the corpus scanned,
# which is live and legitimately grows. Pinning a live artifact's count has bitten
# this repo twice; see AGENTS.md.)
LF2_KNOWN_HITS = {
    # --- m0108's representation boundary. This is interpretation I-01, the very
    # instance LF-2's PROTOCOL NOTE cites: "ruled in prose, M0108_SEAT_DEFECT_REVIEW".
    # Registered as (a): backlog id I-01, tracked in OUTSTANDING_WORK.md, awaiting the
    # interpretation artifact that LF-2 parks. All six lines below are that one review
    # arguing that one ruling.
    "semi-formal-experiment/cycles/patient-pricing-2026-08-04/"
    "M0108_SEAT_DEFECT_REVIEW.md::seat defect::877f0170527d":
        "I-01. §2's heading -- the ambiguity determination itself: 'GENUINE "
        "DEFINITION AMBIGUITY (seat defect)'.",
    "semi-formal-experiment/cycles/patient-pricing-2026-08-04/"
    "M0108_SEAT_DEFECT_REVIEW.md::boundary::4b6d27a911a3":
        "I-01. §2 states the representation reading: 'the boundary tracks whose "
        "interests are voiced' -- the endorsed alternative of the pair.",
    "semi-formal-experiment/cycles/patient-pricing-2026-08-04/"
    "M0108_SEAT_DEFECT_REVIEW.md::under-determines::3db8a4d9d3cc":
        "I-01. The finding sentence: the definition under-determines the "
        "user's-organisation case.",
    "semi-formal-experiment/cycles/patient-pricing-2026-08-04/"
    "M0108_SEAT_DEFECT_REVIEW.md::seat defect::3db8a4d9d3cc":
        "I-01. Same finding sentence, second marker ('-- a seat defect').",
    "semi-formal-experiment/cycles/patient-pricing-2026-08-04/"
    "M0108_SEAT_DEFECT_REVIEW.md::boundary::3b9ba6d354cb":
        "I-01. The subsidiary finding: leg 1's misreading is real but not the root "
        "cause -- 'the org-boundary question itself was genuinely open'.",
    "semi-formal-experiment/cycles/patient-pricing-2026-08-04/"
    "M0108_SEAT_DEFECT_REVIEW.md::boundary::ba6588a922d0":
        "I-01. §3's endorsed reading stated as a rule: 'the boundary is "
        "representation, not mere participant-set membership'.",
    "semi-formal-experiment/cycles/patient-pricing-2026-08-04/"
    "M0108_SEAT_DEFECT_REVIEW.md::boundary::96ea6589eab8":
        "I-01. The accounting ruling: a boundary split is flagged, never silently "
        "resolved in either direction (P3 precedent); the `unclear` verdict stands.",
    "semi-formal-experiment/cycles/patient-pricing-2026-08-04/"
    "M0108_SEAT_DEFECT_REVIEW.md::boundary::4dc5d7ba58dd":
        "I-01. The referral of §3's clarification to a future query-side cycle, and "
        "the standing instruction to treat such boundary cases as knife-edge.",

    # --- NOT AN INTERPRETATION AT ALL. Registered as (a)-by-exclusion: this is the
    # scan's known false positive, kept so the whole-file scope above stays honest
    # about what it costs.
    "semi-formal-experiment/cycles/join-integrity-v2-2026-08-04/"
    "decision.json::boundary::5712e4d371a8":
        "NOT a definitional ruling: 'boundary' here is a substring of the test name "
        "test_floor_boundary_is_14_normalized inside the review verdict's notes. "
        "A join-floor calibration, no document term interpreted.",
}

#: Edit in the same diff as any LF2_KNOWN_HITS change. See the block comment above.
LF2_KNOWN_HITS_PIN = 9


def test_lf2_allowlist_is_pinned_and_every_entry_says_why():
    """The allowlist is hand-maintained and static; pinning it is what makes growth
    show up in a diff as a decision. (The scanned corpus is NOT pinned.)"""
    assert len(LF2_KNOWN_HITS) == LF2_KNOWN_HITS_PIN, (
        f"LF2_KNOWN_HITS has {len(LF2_KNOWN_HITS)} entries, pin says "
        f"{LF2_KNOWN_HITS_PIN}. Adding a known hit means registering an "
        "interpretation or consciously deferring one -- update the pin in the same "
        "diff and say which, in the entry's WHY."
    )
    thin = sorted(k for k, why in LF2_KNOWN_HITS.items()
                  if len(why.strip()) < 40)
    assert not thin, (
        f"LF2_KNOWN_HITS entries with no real reason recorded: {thin}. This repo "
        "does not accept a bare list of exceptions."
    )


def test_lf2_no_unregistered_ambiguity_language_in_cycle_records():
    """LF-2 DETECTION 1 -- AMBIGUITY-LANGUAGE SCAN.

    Triggers 3 and 4 made mechanical: a second seat-defect review, or a flip
    adjudicated on a definitional boundary rather than on document text.
    """
    hits = _lf2_hits()
    new = sorted(set(hits) - set(LF2_KNOWN_HITS))
    assert not new, (
        "UNREGISTERED definitional-ambiguity language in a cycle record:\n"
        + "\n".join(f"  {k}\n      {hits[k]}" for k in new)
        + f"\n\nThis is {REGISTRY} LF-2 (triggers 3 and 4): a judgement call the "
        "analysed document does not settle, recorded as prose and invisible in the "
        "tool's output. Either register the interpretation (endorsed reading + named "
        "alternative + grounds + approver, per INTERPRETATION_LAYER_DESIGN.md) and "
        "cite its id here, or consciously defer it and say so. Do NOT add the hit to "
        "LF2_KNOWN_HITS just to get green -- if these are accumulating, LF-2 has "
        "fired and the layer wants building."
    )


def test_lf2_allowlist_entries_still_match_the_records():
    """Anti-rot. An allowlisted key whose line was re-worded or removed no longer
    silences anything real -- and if it silenced a line that changed meaning, we want
    to know. Fail rather than let the allowlist drift away from the corpus."""
    hits = _lf2_hits()
    dead = sorted(set(LF2_KNOWN_HITS) - set(hits))
    assert not dead, (
        "LF2_KNOWN_HITS entries that match nothing on disk (the record was edited, "
        f"moved, or removed): {dead}. Re-read the record and re-register the hit, or "
        "drop the entry and lower LF2_KNOWN_HITS_PIN in the same diff."
    )


#: File types that would make the reader prototype a SCORING surface rather than a
#: static data drop.
_READER_CODE_EXTS = (".py", ".js", ".mjs", ".cjs", ".ts", ".jsx", ".tsx",
                     ".html", ".htm", ".wasm")


def test_lf2_reader_prototype_has_no_scoring_path_while_interpretations_are_parked():
    """LF-2 DETECTION 2 -- READER-SURFACE PIN (trigger 1, mechanical).

    Today `site/spec-reader-test/` holds ONE static file, `data/behaviours.json`:
    a data drop, no code, nothing that computes or displays a score. The moment it
    gains executable code it is a user-facing reader with a scoring path, and LF-2's
    absence stops being internal -- a reader sees answers with no way to see which
    judgement calls they rest on, or what a different reading would cost.

    Pinned on what is actually there (no code files), not on a filename that may
    change: a rewritten prototype with a different data file must not slip past.
    """
    artifact = _interpretation_artifact()
    if artifact is not None:
        pytest.skip(f"interpretation artifact {artifact} exists -- LF-2 has been "
                    "promoted; this pin has done its job.")
    if not os.path.isdir(READER_PROTOTYPE):
        pytest.skip(f"{_rel(READER_PROTOTYPE)} is absent -- nothing to pin.")

    code = sorted(
        _rel(os.path.join(root, name))
        for root, _dirs, files in os.walk(READER_PROTOTYPE)
        for name in files
        if os.path.splitext(name)[1].lower() in _READER_CODE_EXTS
    )
    assert not code, (
        f"the reader prototype {_rel(READER_PROTOTYPE)} gained executable code "
        f"while NO interpretation artifact exists: {code}. That is "
        f"{REGISTRY} LF-2 TRIGGER 1 -- 'a reader consumer ships'. A user-facing "
        "reader that scores must be able to show which registered interpretations an "
        "answer depended on (INTERPRETATION_LAYER_DESIGN.md: an empty "
        "`interpretations` field means licensed by document text alone -- that is the "
        "distinction carrying the value). Promote LF-2 to OUTSTANDING_WORK.md and "
        "build the layer, or keep the prototype code-free."
    )
