"""THE ATTRIBUTION LADDER — where does the read-back's loss actually happen?

The read-back measured, over 125 pre-registered clauses, that 91 of them can
be picked out of nine same-section neighbours from their atoms alone while a
reader of those atoms would not know what the clause REQUIRES (faithful 0.46,
sufficient 0.16). Identification and representation have come apart. Four
components could be responsible — segmentation, assignment, vocabulary,
grammar — and no amount of staring at examples separates them.

This module separates them by re-annotating the SAME 125 clauses under
progressively weaker constraints and scoring each result with the read-back's
own renderer and its own judge. Everything between the rungs is held fixed, so
a rung's gain is attributable to the one constraint it released.

  rung  relaxes                                     isolates
  ----  ------------------------------------------  ---------------------
  0     nothing; the shipped annotations            baseline (F .46 S .16)
  1     one clause per request, whole 361-atom      ASSIGNMENT error
        vocabulary carried, nothing evicted
  1.5   + ordered principals on every `act`, and    PROMPT vs GRAMMAR
        polarity as a reserved parseable prefix
  2     + may coin atoms; per-occurrence glosses    VOCABULARY inadequacy
  3     + unlimited within the schema               the GRAMMAR ceiling
  4     + may invent structure (relations,          value of EXTENDING
        polarity, deontic) — new fields allowed     the grammar
  null  no atoms at all; `render([], kind)`         the render's constant

RUNG 1.5 IS THE LOAD-BEARING ONE, and not for the reason the plan gave.
Sufficiency is overwhelmingly a property of GLOSSES, and the contract-compliant
query modules (`structural`, `section`) match on atom NAMES and TYPES — only
`relevance`, the invariant-10-violating bag scorer, consumes glosses lexically.
So a rung that raises sufficiency by writing better prose improves the module
the contract is trying to retire. The one relaxation that plausibly reaches a
compliant operator is 1.5's POLARITY TYPING: `HANDOFF.md:449` records that 3-11
of every 19-28 query atoms earn a NEGATIVE weight "which our query cannot
express", and a reserved, parseable prefix is a label-free, document-derived
way to make that expressible. `polarity_readiness()` counts it.

WHAT MAKES THIS A MEASUREMENT RATHER THAN A DEMONSTRATION
---------------------------------------------------------
THE RATE CAP. Every rung is held to the encoding budget the shipped index
actually runs at: 2.78 atoms per clause and 211 characters of free text per
clause, both regenerable by `measured_shipped_budget()`. Without it every rung
above 1 wins trivially by writing more. Two details are load-bearing:

  - the cap prices FREE TEXT, not atom names. The withdrawn refinement design
    (`ONTOLOGY_REFINEMENT.md`) priced names and left glosses free, and its
    objective was satisfiable by moving every clause's content into prose. At
    rung 4 the annotator may invent fields, so a relation written as prose in
    an invented field is priced exactly like a gloss — see `text_chars`.
  - the ATOM REUSE PROFILE (df distribution, hapax share) is printed in the
    same table as the sufficiency numbers, and the table WARNS when a
    sufficiency gain arrives with a rising hapax share, which is memorisation.

THE COVERAGE GATE. `table()` refuses to print below 100% coverage, counted
against the DECLARED sample. This is not defensive programming; it is a defect
this repo has shipped. `readback.summarize` derives `unanswered` from the
results dict, which a rate-limited batch never enters, so it reported
`unanswered: 0` while a condition sat at 90/125 with losses concentrated in
whole clause-kind strata. `readback_coverage()` reports the true denominators
of a read-back artifact; `test_ladder.py` pins the defect.

TWO CONTROLS, NOT ONE. The NULL ARM (`render([], kind)`, which still emits a
kind label and a paragraph of boilerplate) bounds the RENDER. The POSITIVE and
NEGATIVE CONTROLS bound the JUDGE: it is shown a clause's own text (must come
back sufficient) and another clause's render (must come back insufficient).
All six of the read-back's pre-registered predictions were wrong and several
were inverted; nobody has checked that `sufficient` means what the word says,
and an unvalidated instrument makes every rung uninterpretable.

SYNTHETIC, FROZEN DEMONSTRATIONS. Rungs 1.5 and up SHOW the grammar.
Demonstration passages live in `ladder_prompt.md`, marked `DEMO>`, are about a
fictional community garden, and are FROZEN under a sha256 recorded in that
file. The freeze is the mitigation: the real leak channel is SELECTION — which
features get demonstrated, on what content, by an author who has seen
panel-conditioned analysis — and only a pre-commitment addresses that. The
substring check against both specs is a backstop against the syntactic case,
not the mitigation.

WHAT THIS DOES NOT MEASURE. Two limits, printed with the table rather than
buried here. (1) The renderer is held FIXED across rungs, so the ladder
measures annotation and rendering JOINTLY: a faithfulness failure caused by
the template over-asserting is charged to the ontology. (2) Fidelity and
sufficiency are read-back quantities; whether a rung RETRIEVES better is a
different question, answered offline and once by `relevance_diagnostic()`,
which is fenced diagnostic-only and may never inform the ontology.

Usage
-----
    .venv/bin/python ladder.py --cost                 # per-rung, per-model
    .venv/bin/python ladder.py --dry-run              # prompts + measured tokens
    .venv/bin/python ladder.py --live --model luna --resume ladder_luna.json
    .venv/bin/python ladder.py --report ladder_luna.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import time

import annotate
import extract_section as ex
import readback as rb

HERE = os.path.dirname(os.path.abspath(__file__))
ANNOTATIONS_PATH = os.path.join(HERE, "annotations_b8.json")
CLAUSES_PATH = os.path.join(HERE, "modelspec_clauses.json")
CONSTITUTION_PATH = os.path.join(HERE, "constitution_clauses.json")
LADDER_PROMPT_PATH = os.path.join(HERE, "ladder_prompt.md")
USAGE_PATH = os.path.join(HERE, "usage.jsonl")
READBACK_ARTIFACT = os.path.join(HERE, "readback_results.json")
PROVIDERS_PATH = os.path.join(HERE, "providers.json")

#: The read-back's sample, verbatim. The ladder is only interpretable against
#: rung 0, and rung 0 is the read-back's measured result on THESE clauses.
SEED = 20260802
PER_KIND = 25

RUNGS = ("0", "1", "1.5", "2", "3", "4")
NULL_ARM = "null"

# --------------------------------------------------------------------------
# THE RATE CAP
#
# Both figures are the shipped index's own spend, recomputed by
# `measured_shipped_budget()`; they are written here only so a reader can see
# them without running anything, and `test_ladder.py` fails if they drift.

CAP_ATOMS_PER_CLAUSE = 2.78
CAP_TEXT_CHARS_PER_CLAUSE = 211

#: The mean is what binds, but an unbounded single clause would let one
#: passage eat the whole run's budget. 5 is the shipped run's near-maximum
#: over the sample (its distribution is 0,1,2,3,4,5,8 with a single 8), so the
#: ceiling truncates one clause of 125 rather than reshaping the distribution.
PER_CLAUSE_ATOM_CEILING = 5

# --------------------------------------------------------------------------
# THE NAMING CONVENTION (rungs 1.5 and 2)
#
# Both features are expressible in the SHIPPED grammar as name conventions —
# that is the point of rung 1.5. Measured over annotations_b8: 3 of 361 names
# encode a role relation, 128 of 820 `act` atoms name any principal, and 53 of
# 361 carry polarity lexically but ad-hoc and unparseably. So "the grammar
# cannot represent role and polarity" is not established, and the ladder must
# price the prompt's silence before it prices the schema.

#: Reserved. `test_polarity_prefixes_are_reserved_against_the_shipped_vocabulary`
#: asserts no existing atom name begins with one, so the parse is unambiguous.
#: (`no_` was a candidate and was dropped: `no_authority_content` and
#: `no_moral_ambiguity` already exist.)
POLARITY_PREFIXES = ("must_", "mustnot_", "should_", "shouldnot_", "may_")

#: `__` separates the stem from the ordered principal chain. No shipped name
#: contains it, so it is free to mean this.
PRINCIPAL_SEP = "__"

#: Longest-first, because `third_party` contains the separator character and a
#: left-to-right split on "_" would tear it in half.
PRINCIPALS = ("third_party", "developer", "operator", "system", "model",
              "root", "user")

#:  (condition/exception/consequent/topic) is a CLOSED ENUM, not prose.
#: It belongs here and not in _extras: as free text it was priced against the
#: gloss budget and could be clipped "condition" -> "cond", destroying the
#: structure the grammar extension exists to add while the cap reported
#: success. A closed-enum value cannot be shortened without becoming invalid.
BASE_FIELDS = ("name", "kind", "gloss", "span_id", "role")
#: Never priced, never rendered, never returned: provenance, not content.
PROVENANCE_FIELDS = ("quote", "locator", "clause_id")
#: Written by the ladder itself from the name; not free text the model wrote.
DERIVED_FIELDS = ("polarity", "principals", "stem")

LADDER_REJECTIONS = ("off_vocabulary", "kind_mismatch", "missing_principals",
                     "bad_convention", "extra_field", "unknown_clause")

# --------------------------------------------------------------------------
# PROSPECTIVE GATES. Written before the run, checked by the harness, printed
# as one VERDICT line. A stop condition a human is trusted to notice is not a
# stop condition.

#: The judge must call a clause's own text sufficient at least this often.
CONTROL_POSITIVE_MIN = 0.80
#: ... and another clause's render sufficient at most this often.
CONTROL_NEGATIVE_MAX = 0.20
#: Rung 3 is "unlimited within the schema". If it does not beat rung 0 by at
#: least this, the grammar was never the constraint and Sol must not be run.
GRAMMAR_GATE_DELTA = 0.10


class LadderError(Exception):
    """Refusal to report. Never caught inside this module."""


class CoverageError(LadderError):
    """A table was asked for below 100% coverage."""


class DemonstrationLeak(LadderError):
    """A demonstration was found in a spec, or is not the frozen set."""


# --------------------------------------------------------------------------
# rungs
#
# `batch_size` and `eviction` are part of the spec because they are the two
# things that set the bill. "No eviction" means the whole 361-atom vocabulary
# rides on every request: 39k characters, ~8.5k input tokens, 125 times per
# rung, with no prompt caching anywhere in providers.py. That is the same
# costing error that killed the withdrawn refinement design, so it is declared
# where it is priced.

_SPECS = {
    "0": dict(relaxes="nothing; the shipped annotations",
              isolates="baseline", annotates=False, vocabulary="closed",
              require_conventions=False, per_occurrence_gloss=True,
              free_shape=False, capped=False, batch_size=8,
              text_is_chosen=True,
              eviction="shipped: 80 situations/entities carried, acts and "
                       "values never evicted"),
    "1": dict(relaxes="one clause per request; whole vocabulary, no eviction",
              isolates="assignment error", annotates=True,
              vocabulary="closed", require_conventions=False,
              per_occurrence_gloss=False, free_shape=False, capped=True,
              batch_size=1, text_is_chosen=False,
              eviction="none: all 361 atoms every call"),
    "1.5": dict(relaxes="+ ordered principals on every act; reserved "
                        "polarity prefix",
                isolates="prompt vs grammar", annotates=True,
                vocabulary="closed", require_conventions=True,
                per_occurrence_gloss=False, free_shape=False, capped=True,
                batch_size=1, text_is_chosen=False,
                eviction="none: all 361 atoms every call"),
    "2": dict(relaxes="+ may coin atoms; per-occurrence glosses",
              isolates="vocabulary inadequacy", annotates=True,
              vocabulary="open", require_conventions=True,
              per_occurrence_gloss=True, free_shape=False, capped=True,
              batch_size=1, text_is_chosen=True,
              eviction="none: all 361 atoms every call"),
    "3": dict(relaxes="+ unlimited within the schema",
              isolates="the grammar ceiling", annotates=True,
              vocabulary="open", require_conventions=False,
              per_occurrence_gloss=True, free_shape=False, capped=True,
              batch_size=1, text_is_chosen=True,
              eviction="none: all 361 atoms every call"),
    "4": dict(relaxes="+ may invent structure (relations, polarity, deontic)",
              isolates="value of extending the grammar", annotates=True,
              vocabulary="open", require_conventions=False,
              per_occurrence_gloss=True, free_shape=True, capped=True,
              batch_size=1, text_is_chosen=True,
              eviction="none: all 361 atoms every call"),
    NULL_ARM: dict(relaxes="no atoms at all", isolates="the render's constant",
                   annotates=False, vocabulary="closed",
                   require_conventions=False, per_occurrence_gloss=False,
                   free_shape=False, capped=False, batch_size=0,
                   text_is_chosen=False, eviction="n/a"),
}


def rung_spec(rung):
    try:
        return dict(_SPECS[str(rung)])
    except KeyError:
        raise LadderError(f"unknown rung {rung!r}; known: "
                          f"{', '.join(list(RUNGS) + [NULL_ARM])}")


def sample(rows=None, per_kind=PER_KIND, seed=SEED):
    """The read-back's own 125 clauses. Deterministic, and deliberately not a
    new draw: rung 0's numbers were measured on these."""
    rows = rows if rows is not None else rb.load_clauses()
    return rb.stratified_sample(rows, per_kind, seed)


#: If a rung ever has to run at reduced n for cost reasons, this is the subset
#: to run it on. `meta` is the worst retrieval stratum (+0.127 one-vs-rest)
#: and sits at 2/25 on sufficiency, so it has by far the most headroom; a
#: uniform subsample would spend the same money spread across strata that
#: cannot move. A reduced run is a PILOT and must be labelled one — it is not
#: comparable with a full rung.
PREFERRED_STRATA = ("meta",)


def reduced_sample(rows=None, n=25, prefer=PREFERRED_STRATA, seed=SEED):
    rows = rows if rows is not None else rb.load_clauses()
    ids = sample(rows, seed=seed)
    kind = {r["id"]: r.get("kind") for r in rows}
    ordered = ([c for c in ids if kind.get(c) in prefer]
               + [c for c in ids if kind.get(c) not in prefer])
    return ordered[:n]


# --------------------------------------------------------------------------
# vocabulary

def load_vocabulary(path=ANNOTATIONS_PATH):
    """`{name: {kind, gloss}}` — the whole 361-atom shipped vocabulary, in
    coin order, with NOTHING evicted. The shipped pass capped the carried
    vocabulary at 80 situations/entities, so a clause late in the document
    could not reuse an early atom it had never been shown. Removing that cap
    is half of what rung 1 relaxes — and all of what rung 1 costs."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    voc = data.get("vocabulary") or {}
    return {name: {"kind": v.get("kind"), "gloss": v.get("gloss") or ""}
            for name, v in voc.items()}


def vocabulary_block(vocab):
    return [{"name": n, "kind": v["kind"], "gloss": v["gloss"]}
            for n, v in vocab.items()]


# --------------------------------------------------------------------------
# the naming convention: parse, never guess

def parse_name(name):
    """`{polarity, stem, principals, error}` for one atom name.

    Total: an unparseable name yields an `error` string rather than a
    plausible-looking parse. A convention that silently half-parses is worse
    than none, because the render would then assert a polarity nobody wrote.
    """
    out = {"polarity": None, "stem": name, "principals": [], "error": None}
    if not isinstance(name, str) or not name:
        out["error"] = "not a name"
        return out
    parts = name.split(PRINCIPAL_SEP)
    if len(parts) > 2:
        out["error"] = f"more than one {PRINCIPAL_SEP!r} in {name!r}"
        return out
    head = parts[0]
    for p in POLARITY_PREFIXES:
        if head.startswith(p):
            out["polarity"] = p[:-1]
            head = head[len(p):]
            break
    if not head:
        out["error"] = f"{name!r} is a polarity prefix with no stem"
        return out
    out["stem"] = head
    if len(parts) == 2:
        chain, rest = [], parts[1]
        while rest:
            for pr in PRINCIPALS:
                if rest == pr or rest.startswith(pr + "_"):
                    chain.append(pr)
                    rest = rest[len(pr) + 1:]
                    break
            else:
                out["error"] = (f"{rest!r} in {name!r} is not one of "
                                f"{', '.join(PRINCIPALS)}")
                return out
        if not chain:
            out["error"] = f"{name!r} has an empty principal chain"
            return out
        out["principals"] = chain
    return out


def format_name(stem, polarity=None, principals=()):
    """The inverse, so the convention has exactly one spelling."""
    head = (f"{polarity}_" if polarity else "") + stem
    if principals:
        head += PRINCIPAL_SEP + "_".join(principals)
    return head


def stem_normalised(by_clause):
    """Strip the ladder's own notation back to the bare stem.

    Rung 1.5 renames `disclose_reasoning` to
    `must_disclose_reasoning__model_user`, which matches no query atom in
    `behavior_atoms.json`. Scoring that raw would report a retrieval collapse
    caused by the ladder's notation rather than by the annotation, so any
    retrieval-side comparison runs on the normalised view — and the polarity
    that was stripped is reported separately by `polarity_readiness`.
    """
    out = {}
    for cid, atoms in (by_clause or {}).items():
        rows = []
        for a in atoms or []:
            p = parse_name(a.get("name"))
            if not p["error"] and (p["polarity"] or p["principals"]):
                rows.append(dict(a, name=p["stem"]))
            else:
                rows.append(dict(a))
        out[cid] = rows
    return out


def polarity_readiness(by_clause):
    """How much of a rung's output a POLARITY-AWARE operator could consume.

    This is the number rung 1.5 exists to produce. `HANDOFF.md:449` records
    that 3-11 of every 19-28 query atoms earn a negative weight "which our
    query cannot express"; a reserved prefix makes the clause side of that
    expressible without a single label. Counting is all this does — building
    the operator is `structural.py`'s business, not the ladder's.
    """
    n = pol = pri = unparseable = 0
    by_pol = {}
    for atoms in (by_clause or {}).values():
        for a in atoms or []:
            n += 1
            p = parse_name(a.get("name"))
            if p["error"]:
                unparseable += 1
                continue
            if p["polarity"]:
                pol += 1
                by_pol[p["polarity"]] = by_pol.get(p["polarity"], 0) + 1
            if p["principals"]:
                pri += 1
    return {"atoms": n, "with_polarity": pol, "with_principals": pri,
            "unparseable": unparseable, "by_polarity": by_pol,
            "polarity_share": (pol / n) if n else 0.0}


# --------------------------------------------------------------------------
# prompts, and the frozen demonstrations

def load_rung_blocks(path=LADDER_PROMPT_PATH):
    """`{rung: block}` from ladder_prompt.md, split on `=== RUNG x ===`."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    marks = [(r, f"=== RUNG {r} ===") for r in RUNGS if r != "0"]
    out = {}
    for i, (rung, m) in enumerate(marks):
        if m not in text:
            raise LadderError(f"{path} has no block for rung {rung}")
        rest = text.split(m, 1)[1]
        nxt = marks[i + 1][1] if i + 1 < len(marks) else None
        out[rung] = (rest.split(nxt, 1)[0] if nxt else rest).strip()
    return out


_DEMO_RE = re.compile(r"^\s*DEMO>\s*(.+?)\s*$", re.M)
_SHA_RE = re.compile(r"DEMONSTRATIONS-SHA256:\s*([0-9a-f]{64})")


def demonstration_passages(blocks=None):
    """Every `DEMO>` line, in file order.

    Marked rather than inferred so the freeze has an exact, diffable target: a
    reviewer can see at a glance what the extractor is shown.
    """
    blocks = blocks if blocks is not None else load_rung_blocks()
    seen, out = set(), []
    for rung in RUNGS:
        for m in _DEMO_RE.finditer(blocks.get(rung, "")):
            p = m.group(1).strip()
            if p and p not in seen:
                seen.add(p)
                out.append(p)
    return out


def demonstrations_sha256(passages=None):
    passages = (passages if passages is not None
                else demonstration_passages())
    blob = "\n".join(_norm(p) for p in passages)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def declared_demonstrations_sha256(path=LADDER_PROMPT_PATH):
    """The hash the prompt file COMMITS to.

    The freeze, not the substring test, is the mitigation for the leak the
    review named: the channel is SELECTION — which features are demonstrated,
    on what content, by an author who has read panel-conditioned analysis — and
    only a pre-commitment made before that analysis lands addresses it. A
    demonstration edited later changes this hash and stops the run.
    """
    with open(path, encoding="utf-8") as f:
        m = _SHA_RE.search(f.read())
    return m.group(1) if m else None


def assert_demonstrations_frozen(path=LADDER_PROMPT_PATH, passages=None):
    declared = declared_demonstrations_sha256(path)
    got = demonstrations_sha256(passages)
    if not declared:
        raise DemonstrationLeak(
            f"{os.path.basename(path)} declares no DEMONSTRATIONS-SHA256. The "
            "demonstrations must be frozen before any panel-conditioned "
            "analysis, or the selection channel is open.")
    if declared != got:
        raise DemonstrationLeak(
            "the demonstrations are not the frozen set: prompt file declares "
            f"{declared[:12]}..., current demonstrations hash {got[:12]}.... "
            "Either the demonstrations changed or the freeze was not updated "
            "deliberately; both need a human.")
    return True


def _norm(s):
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def spec_texts(paths=(CLAUSES_PATH, CONSTITUTION_PATH)):
    """The two specs as one normalised string each. Read, never assumed: the
    spec must stay swappable."""
    out = []
    for p in paths:
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        rows = data["clauses"] if isinstance(data, dict) else data
        out.append(_norm(" ".join((r.get("quote") or "") for r in rows)))
    return out


#: A demonstration is a leak if it, or any long run of it, occurs in a spec.
LEAK_SHINGLE_WORDS = 8


def assert_demonstrations_synthetic(passages=None, specs=None):
    """BACKSTOP against the syntactic case: a demonstration copied out of a
    spec. It is not the mitigation — see `declared_demonstrations_sha256` —
    but a spec-sourced demonstration is a blocking defect on its own, so this
    runs before any prompt is built and raises rather than warns.
    """
    passages = (passages if passages is not None
                else demonstration_passages())
    specs = specs if specs is not None else spec_texts()
    bad = []
    for p in passages:
        np = _norm(p)
        hit = None
        for s in specs:
            if np and np in s:
                hit = "whole passage"
                break
            words = np.split()
            for i in range(len(words) - LEAK_SHINGLE_WORDS + 1):
                sh = " ".join(words[i:i + LEAK_SHINGLE_WORDS])
                if sh in s:
                    hit = f"shared {LEAK_SHINGLE_WORDS}-word run: {sh!r}"
                    break
            if hit:
                break
        if hit:
            bad.append((p, hit))
    if bad:
        raise DemonstrationLeak(
            "demonstration passages found inside a spec — a curated "
            "annotation of an evaluation-set passage is a leak channel:\n" +
            "\n".join(f"  - {why}: {p[:120]!r}" for p, why in bad))
    return True


def annotate_prompt_for(row, rung, vocab, all_rows=None, blocks=None):
    """`(system, user)` for ONE clause at one rung.

    The system prompt is `annotate_prompt.md`'s, unchanged, with the rung
    block appended. Unchanged is the point: rung 1 has to differ from the
    shipped pass only in the two things it relaxes, so every other word has to
    be the same word.
    """
    spec = rung_spec(rung)
    if not spec["annotates"]:
        raise LadderError(f"rung {rung} has no annotation stage")
    blocks = blocks if blocks is not None else load_rung_blocks()
    demos = demonstration_passages(blocks)
    assert_demonstrations_synthetic(demos)
    if demos:
        declared = declared_demonstrations_sha256()
        if declared != demonstrations_sha256(demos):
            raise DemonstrationLeak(
                "the demonstrations are not the frozen set: prompt file "
                f"declares {declared}, current hash "
                f"{demonstrations_sha256(demos)}")
    system, _ = annotate.load_template(
        annotate._p(annotate.PROMPT_TEMPLATE_PATH))
    _, user = annotate.render_prompt(
        [row], all_rows=all_rows, known_atoms=vocabulary_block(vocab),
        batch_index=1, n_batches=1, section_title=annotate.section_of(row))
    return system.rstrip() + "\n\n" + blocks[rung], user


# --------------------------------------------------------------------------
# verification — rung constraints are enforced, not merely requested

def _fail_sink(store):
    def fail(stage, reason, detail=None):
        store.append({"stage": stage, "reason": reason, "detail": detail})
    return fail


def _extras(atom):
    return {k: v for k, v in atom.items()
            if k not in BASE_FIELDS and k not in PROVENANCE_FIELDS
            and k not in DERIVED_FIELDS}


def verify_rung_atoms(obj, row, rung, vocab):
    """`(atoms, stats)` from one parsed response, for one clause, at one rung.

    Two stages, in this order. First the RUNG constraints (shape, vocabulary,
    naming convention) on the raw objects, because those are what the rung is
    about and their rejections have to be attributable. Then
    `annotate.verify_atoms` — the shipped validator, reused unchanged — for
    the identifier regex, the closed kind taxonomy and span resolution.
    """
    spec = rung_spec(rung)
    stats = {"atoms_seen": 0, "atoms_accepted": 0, "atoms_rejected": 0,
             "rejections": {r: 0 for r in
                            tuple(LADDER_REJECTIONS) + annotate.REJECTIONS},
             "notes": []}

    def reject(reason, detail):
        stats["atoms_rejected"] += 1
        stats["rejections"][reason] = stats["rejections"].get(reason, 0) + 1
        stats["notes"].append({"reason": reason, "detail": detail})

    entries = obj.get("clauses") if isinstance(obj, dict) else None
    if not isinstance(entries, list):
        return [], stats

    kept = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        cid = entry.get("clause_id") or entry.get("id")
        atoms = entry.get("atoms")
        atoms = atoms if isinstance(atoms, list) else []
        if cid != row["id"]:
            for _ in atoms:
                stats["atoms_seen"] += 1
                reject("unknown_clause", {"clause_id": cid})
            continue
        for a in atoms:
            stats["atoms_seen"] += 1
            if not isinstance(a, dict):
                reject("malformed_atom", {"clause_id": cid})
                continue
            name, kind = a.get("name"), a.get("kind")
            extras = _extras(a)
            if extras and not spec["free_shape"]:
                reject("extra_field", {"name": name, "fields": sorted(extras)})
                continue
            parsed = parse_name(name)
            if spec["require_conventions"]:
                if parsed["error"]:
                    reject("bad_convention", {"name": name,
                                              "why": parsed["error"]})
                    continue
                if kind == "act" and not parsed["principals"]:
                    reject("missing_principals", {"name": name})
                    continue
            if spec["vocabulary"] == "closed":
                stem = parsed["stem"] if not parsed["error"] else name
                if stem not in vocab:
                    reject("off_vocabulary", {"name": name, "stem": stem})
                    continue
                if vocab[stem]["kind"] != kind:
                    reject("kind_mismatch",
                           {"name": name, "kind": kind,
                            "vocabulary_kind": vocab[stem]["kind"]})
                    continue
            kept.append((a, parsed))

    # stage two: the shipped validator, on a schema-clean copy
    clean = {"clauses": [{"clause_id": row["id"], "atoms": [
        {k: a.get(k) for k in BASE_FIELDS} for a, _ in kept]}]}
    notes = []
    base, bstats = annotate.verify_atoms(clean, [row], _fail_sink(notes),
                                         vocab=None)
    for k, v in bstats.get("rejections", {}).items():
        stats["rejections"][k] = stats["rejections"].get(k, 0) + v
    stats["atoms_rejected"] += bstats.get("atoms_rejected", 0)
    stats["notes"] += notes

    raw_by_name = {}
    for a, parsed in kept:
        raw_by_name.setdefault(a.get("name"), (a, parsed))

    out = []
    for atom in base:
        raw, parsed = raw_by_name.get(atom["name"],
                                      ({}, parse_name(atom["name"])))
        rec = dict(atom)
        if not spec["per_occurrence_gloss"]:
            # Rungs 1 and 1.5 hold the vocabulary's own gloss. A per-occurrence
            # gloss is a rung-2 relaxation; letting it in earlier would mix
            # assignment with vocabulary and neither rung would isolate
            # anything.
            rec["gloss"] = vocab.get(parsed["stem"], {}).get("gloss", "")
        rec["polarity"] = parsed["polarity"]
        rec["principals"] = parsed["principals"]
        rec["stem"] = parsed["stem"]
        if spec["free_shape"]:
            rec.update(_extras(raw))
        out.append(rec)
    stats["atoms_accepted"] = len(out)
    return out, stats


# --------------------------------------------------------------------------
# THE RATE CAP

def _text_paths(value, prefix=()):
    """`[(path, string)]` for every string reachable inside a field value.

    Structure is free; prose is not. A relation recorded as
    `{"triggers": ["the user has asked twice"]}` is prose no matter how deeply
    it is nested, and — the defect this replaced — a truncator that only sees
    TOP-LEVEL strings prices that prose and cannot cut it. The binary search
    then drives its ceiling to zero trying to reach an amount it can never
    reach, emptying every legitimate gloss while the nested prose survives
    into the render the judge scores. Pricing and cutting must walk the SAME
    tree, so both now call this.
    """
    if isinstance(value, str):
        return [(prefix, value)]
    if isinstance(value, dict):
        return [p for k in sorted(value)
                for p in _text_paths(value[k], prefix + (k,))]
    if isinstance(value, (list, tuple)):
        return [p for i, v in enumerate(value)
                for p in _text_paths(v, prefix + (i,))]
    return []


def _atom_text_fields(atom):
    """`[(path, string)]` — every string the ANNOTATOR wrote for this atom."""
    out = []
    if isinstance(atom.get("gloss"), str):
        out.append((("gloss",), atom["gloss"]))
    for k, v in sorted(_extras(atom).items()):
        out += _text_paths(v, (k,))
    return out


def text_chars(atom):
    """The atom's FREE TEXT budget: its gloss plus every string it wrote in an
    invented field, at any depth.

    This is the whole lesson of the withdrawn refinement design, which priced
    atom names and left glosses free — an objective satisfiable by moving the
    content into prose. Rung 4 may invent fields, so the same escape hatch
    reopens one level up unless invented text is priced identically. Defined
    off `_atom_text_fields` so that WHAT IS PRICED IS EXACTLY WHAT CAN BE
    CUT; the two drifting apart is what let rung 4 out of the cap.
    """
    return sum(len(s) for _, s in _atom_text_fields(atom))


def name_chars(atom):
    return len(atom.get("name") or "")


def _to_lists(value):
    """Deep copy, tuples normalised to lists so a path is assignable."""
    if isinstance(value, dict):
        return {k: _to_lists(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_lists(v) for v in value]
    return value


def _set_path(obj, path, value):
    cur = obj
    for k in path[:-1]:
        cur = cur[k]
    cur[path[-1]] = value


def _clip(s, ceiling):
    """Truncate to `ceiling`, then back off to a word boundary.

    Cutting mid-word hands the judge a fragment that reads as a different
    claim than the one the annotator wrote, which is scored as the ontology's
    failure. The back-off only ever REMOVES characters, so the budget the
    binary search computed is still an upper bound.
    """
    if len(s) <= ceiling:
        return s
    cut = s[:ceiling]
    sp = cut.rfind(" ")
    if sp > ceiling // 2:            # keep a long unbroken token rather than
        cut = cut[:sp]               # deleting it entirely
    return cut.rstrip()


def _truncate_atom(atom, ceiling):
    out = _to_lists(atom)
    dropped = 0
    for path, s in _atom_text_fields(atom):
        if len(s) > ceiling:
            new = _clip(s, ceiling)
            dropped += len(s) - len(new)
            _set_path(out, path, new)
    return out, dropped


def _trim_key(cid):
    """A tie-break uncorrelated with the clause's stratum.

    Clause ids are contiguous WITHIN a kind (`m0001..` walks the document in
    order), so a lexicographic tie-break is a kind-sorted queue. In the modal
    outcome — every clause returning the instructed 3 atoms, so 28 must go —
    it deleted 9 atoms from `example` and 1 from `definitional`: nine times
    more content removed from one stratum than another for reasons with
    nothing to do with the annotation, and `by_kind` and
    `sufficient_headline` are read straight off that split. This is the same
    defect class as the read-back's losing whole clause-kind strata to 429s.
    Seed-pinned so it is reproducible, hashed so it is neutral.
    """
    return hashlib.sha256(f"{SEED}|{cid}".encode("utf-8")).hexdigest()


def enforce_rate_cap(by_clause, clause_ids,
                     max_atoms=CAP_ATOMS_PER_CLAUSE,
                     max_text=CAP_TEXT_CHARS_PER_CLAUSE,
                     per_clause_ceiling=PER_CLAUSE_ATOM_CEILING,
                     cap_text=True):
    """Hold a rung's annotations to the shipped encoding budget.

    Deterministic, and deliberately blunt. Atoms past the per-clause ceiling
    go first; then, while the run is over its mean atom budget, the clause
    with the most atoms loses its last one, ties broken on a hash of the
    clause id so the trim is not correlated with clause kind. Then one
    per-string character ceiling is binary-searched so the run's mean free
    text lands inside budget, and every longer string — at any depth — is
    truncated to it at a word boundary.

    THE BUDGET IS A PROPERTY OF THE SAMPLE, NOT OF THE SURVIVORS. `n` is
    `len(clause_ids)`, so a partial or resumed run is not trimmed to a
    partial budget. Failures cluster contiguously in a kind-sorted sample, so
    a survivor-sized budget would hand resumed and fresh clauses different
    allowances, correlated with kind.

    `cap_text=False` prices the text and reports it but does not cut it. That
    is for rungs whose gloss is a LOOKUP rather than a choice — see
    `text_is_chosen` in the rung spec.

    Returning the trim counts is not decoration: a rung whose numbers were
    produced after heavy trimming is a rung whose annotator ignored the cap,
    and that is a finding about the annotator.
    """
    ids = list(clause_ids)
    n = len(ids)
    out = {cid: [_to_lists(a) for a in (by_clause.get(cid) or [])]
           for cid in ids}
    stats = {"n_clauses": n, "atoms_dropped": 0, "gloss_chars_dropped": 0,
             "clauses_over_ceiling": 0, "text_field_ceiling": None,
             "text_capped": bool(cap_text)}

    for cid in ids:
        if len(out[cid]) > per_clause_ceiling:
            stats["clauses_over_ceiling"] += 1
            stats["atoms_dropped"] += len(out[cid]) - per_clause_ceiling
            out[cid] = out[cid][:per_clause_ceiling]

    keys = {cid: _trim_key(cid) for cid in ids}
    budget_atoms = int(math.floor(max_atoms * n))
    total = sum(len(v) for v in out.values())
    while total > budget_atoms:
        cid = max(ids, key=lambda c: (len(out[c]), keys[c]))
        if not out[cid]:
            break
        out[cid].pop()
        total -= 1
        stats["atoms_dropped"] += 1

    budget_text = int(math.floor(max_text * n))

    def total_text(ceiling):
        return sum(min(len(s), ceiling) for cid in ids for a in out[cid]
                   for _, s in _atom_text_fields(a))

    if cap_text and total_text(10 ** 9) > budget_text:
        lo, hi = 0, max((len(s) for cid in ids for a in out[cid]
                         for _, s in _atom_text_fields(a)), default=0)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if total_text(mid) <= budget_text:
                lo = mid
            else:
                hi = mid - 1
        stats["text_field_ceiling"] = lo
        for cid in ids:
            trimmed = []
            for a in out[cid]:
                a2, dropped = _truncate_atom(a, lo)
                stats["gloss_chars_dropped"] += dropped
                trimmed.append(a2)
            out[cid] = trimmed
    elif not cap_text:
        stats["why_text_not_capped"] = (
            "this rung's glosses are the vocabulary's own, substituted by the "
            "harness; the annotator wrote no text, so there is nothing here "
            "for a text cap to hold. The characters are still priced and "
            "reported.")

    realised = sum(text_chars(a) for cid in ids for a in out[cid])
    stats["text_chars_per_clause"] = realised / n if n else 0.0
    stats["atoms_per_clause"] = (sum(len(v) for v in out.values()) / n
                                 if n else 0.0)
    return out, stats


def _atoms_key(atoms):
    return json.dumps(atoms or [], sort_keys=True, ensure_ascii=False)


def recap_block(block, clause_ids, cap_text=True):
    """Re-apply the cap from the RAW answer, invalidating verdicts it moved.

    The stored `by_clause` is already capped, so re-capping a resumed run
    trims twice — the second pass sees an already-trimmed corpus and takes
    another 2.78/clause off it. Keeping `by_clause_raw` means the cap is
    applied ONCE, over the union of resumed and fresh clauses.

    The other half matters more: if the re-cap moves a clause's atoms, its
    stored verdict was made against a render that no longer exists. That
    verdict is dropped, the coverage gate then refuses to report until it is
    re-asked, and the re-ask is one batch rather than a whole rung.
    """
    ids = list(clause_ids)
    raw = block.get("by_clause_raw")
    if raw is None:
        raw = block.get("by_clause") or {}
    capped, cap = enforce_rate_cap(raw, ids, cap_text=cap_text)
    cap["applied"] = True
    seen = block.get("by_clause") or raw
    fid = dict(block.get("fidelity") or {})
    invalidated = []
    for cid in ids:
        if cid in seen and _atoms_key(seen.get(cid)) != _atoms_key(
                capped.get(cid)):
            if fid.pop(cid, None) is not None:
                invalidated.append(cid)
    out = dict(block)
    out.update({"by_clause_raw": {c: raw[c] for c in raw if c in set(ids)},
                "by_clause": capped, "cap": cap, "fidelity": fid,
                "recap_invalidated": invalidated})
    return out


def rate_profile(by_clause, clause_ids):
    """What the rung ACTUALLY spent — never what it was asked to spend."""
    ids = list(clause_ids)
    n = len(ids) or 1
    atoms = [a for cid in ids for a in (by_clause.get(cid) or [])]
    return {
        "n_clauses": len(ids),
        "n_atoms": len(atoms),
        "atoms_per_clause": len(atoms) / n,
        "text_chars_per_clause": sum(text_chars(a) for a in atoms) / n,
        "name_chars_per_clause": sum(name_chars(a) for a in atoms) / n,
    }


def measured_shipped_budget(path=ANNOTATIONS_PATH):
    """Regenerate the cap from the shipped artifact.

    `combined.MEASURED` and `section.MEASURED` are hand-transcribed constants
    with no in-repo generator. The ladder was told not to add a third.
    """
    with open(path, encoding="utf-8") as f:
        bc = (json.load(f) or {}).get("by_clause") or {}
    ids = sorted(bc)
    p = rate_profile(bc, ids)
    return {"source": os.path.basename(path), "n_clauses": p["n_clauses"],
            "atoms_per_clause": p["atoms_per_clause"],
            "text_chars_per_clause": p["text_chars_per_clause"]}


# --------------------------------------------------------------------------
# THE REUSE PROFILE — memorisation, made visible

def reuse_profile(by_clause, clause_ids):
    """df distribution and hapax share over the rung's own annotations.

    A rung that reaches sufficiency by giving every clause its own bespoke
    atom has memorised the corpus, not represented it: the atoms would carry
    no cross-clause structure and the index would be a lookup table. df is
    document frequency — how many of the sampled clauses use the name.
    """
    ids = list(clause_ids)
    df = {}
    for cid in ids:
        for name in {a.get("name") for a in (by_clause.get(cid) or [])}:
            df[name] = df.get(name, 0) + 1
    dist = {}
    for v in df.values():
        dist[str(v)] = dist.get(str(v), 0) + 1
    hapax = sum(1 for v in df.values() if v == 1)
    return {
        "distinct_names": len(df),
        "hapax": hapax,
        "hapax_share": (hapax / len(df)) if df else 0.0,
        "mean_df": (sum(df.values()) / len(df)) if df else 0.0,
        "df_distribution": dict(sorted(dist.items(),
                                       key=lambda kv: int(kv[0]))),
    }


# --------------------------------------------------------------------------
# THE RENDERER — reused from readback, never forked

#: readback.render's closing disclaimer, verbatim. TRUE of rungs 0 and 1 and
#: false of every rung whose names or fields carry polarity, principals or
#: relations — leaving it in place would make the render assert something the
#: index no longer holds, which is exactly the unfaithfulness the judge looks
#: for. `test_readbacks_closing_paragraph_is_still_what_ladder_splices` fails
#: the day readback.py rewords it, rather than silently skipping.
READBACK_CLOSING = (
    "THAT IS EVERYTHING THE INDEX HOLDS FOR THIS PASSAGE. It records no "
    "wording. The order above is the order the concepts were recorded and "
    "carries no meaning. It records no relation between the concepts: no "
    "condition, no exception, no priority, no polarity, and nothing about "
    "who is addressed or what is required.")

_CONVENTION_NOTE = (
    "Two things ARE recorded, inside the names. A name beginning must_, "
    "mustnot_, should_, shouldnot_ or may_ records that force and that "
    "polarity, and nothing weaker or stronger; a name with no such beginning "
    "records no force and no polarity at all. A name ending in a double "
    "underscore followed by parties records those parties IN ORDER: who acts "
    "first, then who is acted upon, then any third party.")

_CLOSING_CONVENTIONS = (
    "THAT IS EVERYTHING THE INDEX HOLDS FOR THIS PASSAGE. It records no "
    "wording. The order above is the order the concepts were recorded and "
    "carries no meaning. " + _CONVENTION_NOTE + " Nothing else is recorded: "
    "no condition, no exception, no priority, and no relation between one "
    "concept and another.")

_CLOSING_FREE = (
    "THAT IS EVERYTHING THE INDEX HOLDS FOR THIS PASSAGE. It records no "
    "wording. The order above is the order the concepts were recorded and "
    "carries no meaning. Anything the names and explanations do not say, the "
    "index does not hold.")

_CLOSING_STRUCTURE = (
    "THAT IS EVERYTHING THE INDEX HOLDS FOR THIS PASSAGE, INCLUDING THE "
    "STRUCTURE LISTED ABOVE. It records no wording. The order of the "
    "concepts carries no meaning, but the recorded structure does: read it "
    "as written. Anything neither the explanations nor the structure says, "
    "the index does not hold.")


def _uses_convention(atoms):
    """Did this annotation actually use the notation?

    Rungs 3 and 4 impose no convention, but a model is free to reach for one
    anyway — and judging `mustnot_disclose__model_user` against a closing that
    does not decode it scores an opaque string rather than the annotation.
    Rung 3 is the gate that authorises the Sol spend, so this is not a
    cosmetic case.
    """
    for a in atoms or []:
        p = parse_name(a.get("name"))
        if not p["error"] and (p["polarity"] or p["principals"]):
            return True
    return False


def closing_for(rung, atoms=()):
    spec = rung_spec(rung)
    used = _uses_convention(atoms)
    if spec["free_shape"]:
        return (_CLOSING_STRUCTURE + " " + _CONVENTION_NOTE if used
                else _CLOSING_STRUCTURE)
    if spec["require_conventions"]:
        return _CLOSING_CONVENTIONS
    if str(rung) == "3":
        return (_CLOSING_FREE + " " + _CONVENTION_NOTE if used
                else _CLOSING_FREE)
    return READBACK_CLOSING


def _structure_block(atoms):
    lines = []
    for a in atoms:
        extras = _extras(a)
        if not extras:
            continue
        lines.append(f"  {a.get('name')}:")
        for k, v in sorted(extras.items()):
            lines.append(f"    {k} = {json.dumps(v, ensure_ascii=False)}")
    if not lines:
        return ""
    return ("\nTHE INDEX ALSO RECORDS THIS STRUCTURE, WHICH IT WROTE ITSELF:\n"
            + "\n".join(lines) + "\n")


def render_for_rung(atoms, clause_kind, rung):
    """`readback.render`, plus exactly what the rung added.

    Rungs 0 and 1 are byte-identical to `readback.render` — the read-back's
    renderer is the instrument, and a modified instrument would make rung 0's
    measured baseline inapplicable. Above that, two edits, both forced: rung
    4's invented fields are printed (they are content, and hiding them would
    score rung 4 on a render that conceals what it bought), and the closing
    disclaimer is replaced wherever it has become false.

    NOTE, and it is printed with the table: the renderer is held FIXED across
    rungs, so what is measured is annotation and rendering JOINTLY.
    """
    txt = rb.render(atoms, clause_kind)
    spec = rung_spec(rung)
    if spec["free_shape"]:
        block = _structure_block(atoms or [])
        if block:
            txt = txt.replace("\n" + READBACK_CLOSING,
                              block + "\n" + READBACK_CLOSING)
    closing = closing_for(rung, atoms)
    if closing != READBACK_CLOSING:
        txt = txt.replace(READBACK_CLOSING, closing)
    return txt


# --------------------------------------------------------------------------
# the judge — the read-back's, unchanged — and its two controls

def fidelity_prompt(items):
    return rb.fidelity_prompt(items)


def fidelity_items(clause_ids, rows, by_clause, rung):
    by_id = {r["id"]: r for r in rows}
    out = []
    for cid in clause_ids:
        row = by_id.get(cid, {})
        out.append({
            "clause_id": cid,
            "clause_kind": row.get("kind"),
            "render": render_for_rung(by_clause.get(cid) or [],
                                      row.get("kind"), rung),
            "source_text": (row.get("quote") or "").strip(),
        })
    return out


def control_items(clause_ids, rows, which, annotations=None):
    """The JUDGE's controls. Deterministic, and cheap enough to be mandatory.

    positive — the description IS the clause's own text. A judge whose
               `sufficient` means what the word says must return true; one
               that does not is measuring something else and every rung above
               is uninterpretable.
    negative — the description is a DIFFERENT clause's render, paired by a
               fixed rotation through the sample. Must return false. Without
               it, a judge that says "sufficient" to anything plausible-looking
               would be indistinguishable from a good one.

    All six of the read-back's pre-registered predictions were wrong and
    several were inverted, which is the whole reason these exist.
    """
    if which not in ("positive", "negative"):
        raise LadderError(f"unknown control {which!r}")
    ids = list(clause_ids)
    by_id = {r["id"]: r for r in rows}
    ann = annotations if annotations is not None else rb.load_annotations()
    out = []
    for i, cid in enumerate(ids):
        row = by_id.get(cid, {})
        src = (row.get("quote") or "").strip()
        if which == "positive":
            render = src
        else:
            other = ids[(i + 1) % len(ids)] if len(ids) > 1 else cid
            orow = by_id.get(other, {})
            render = rb.render(ann.get(other, []), orow.get("kind"))
        out.append({"clause_id": cid, "clause_kind": row.get("kind"),
                    "render": render, "source_text": src, "control": which})
    return out


_RATE_LIMIT = re.compile(r"429|rate.?limit|too many requests", re.I)


def _call_with_retry(client, system, user, attempts, sleep, backoff=5.0):
    """`(text, error, retries)`. Transport failures are retried; a parsed but
    wrong answer is data and is not.

    A previous run lost 52 of 125 calls to 429s. `providers.LiveClient` does
    retry, but its counter is SHARED with the 400-parameter adaptation, so
    under rate-limiting the adaptation exhausted the budget and killed whole
    batches. A retry at this level is not redundant with that one.
    """
    last, retries = None, 0
    for i in range(max(1, attempts)):
        try:
            return rb._call(client, system, user), None, retries
        except Exception as e:                       # a dead call is data
            last = f"{type(e).__name__}: {e}"
            if i + 1 < max(1, attempts):
                retries += 1
                if sleep:
                    sleep(backoff * (i + 1)
                          * (3 if _RATE_LIMIT.search(last) else 1))
    return None, last, retries


def annotate_rung(clause_ids, rows, rung, vocab, client, attempts=3,
                  prior=None, sleep=time.sleep, progress=None, all_rows=None,
                  blocks=None, checkpoint=None):
    """Re-annotate the sample at one rung, ONE CLAUSE PER REQUEST.

    `prior` is a previous run's `by_clause`: an answered clause is never asked
    again and never re-billed. That discipline is `readback.py --resume`'s, and
    it exists because a rate-limited pass that re-bills its successes is waste
    while one that drops them shrinks the sample without saying so.
    """
    all_rows = all_rows if all_rows is not None else rows
    by_id = {r["id"]: r for r in rows}
    keep = set(clause_ids)
    out = {cid: list(v) for cid, v in (prior or {}).items() if cid in keep}
    stats = {"calls": 0, "retries": 0, "atoms_seen": 0, "atoms_accepted": 0,
             "atoms_rejected": 0, "rejections": {}, "parse_failures": 0,
             # `providers.make_client(..., log_dir=...)` is accepted and
             # IGNORED by LiveClient, so a live run writes NO prompt log.
             # Usage logging is untouched, so spend accounting survives; the
             # provenance of what was actually sent does not. A hash per call
             # restores it at 64 bytes rather than 46,000.
             "prompt_sha256": {}}
    errors = []
    todo = [c for c in clause_ids if c not in out]
    for i, cid in enumerate(todo, start=1):
        row = by_id[cid]
        system, user = annotate_prompt_for(row, rung, vocab, all_rows, blocks)
        stats["prompt_sha256"][cid] = hashlib.sha256(
            (system + "\n" + user).encode("utf-8")).hexdigest()
        text, err, retries = _call_with_retry(client, system, user, attempts,
                                              sleep)
        stats["calls"] += 1
        stats["retries"] += retries
        if progress:
            progress(i, len(todo))
        if err is not None:
            errors.append(f"{rung}/{cid}: {err}")
        else:
            obj, perr = ex.parse_response(text)
            if perr:
                stats["parse_failures"] += 1
                errors.append(f"{rung}/{cid}: {perr}")
            else:
                atoms, st = verify_rung_atoms(obj, row, rung, vocab)
                for k in ("atoms_seen", "atoms_accepted", "atoms_rejected"):
                    stats[k] += st[k]
                for k, v in st["rejections"].items():
                    if v:
                        stats["rejections"][k] = stats["rejections"].get(k, 0) + v
                out[cid] = atoms
        # CHECKPOINT AFTER EVERY PAID CALL, answered or not. Saving only at
        # the end of a rung means a crash at call 120 of 125 throws away 120
        # calls that were already billed.
        if checkpoint:
            checkpoint(out)
    return out, stats, errors


def judge_fidelity(items, client, batch_size=5, attempts=3, prior=None,
                   sleep=time.sleep, progress=None):
    """`(results, errors)` — faithful/sufficient per clause, readback's judge.

    Batched at 5 because that is the batch the read-back measured its judge
    at; a different batch size is a different judge.
    """
    ids = [it["clause_id"] for it in items]
    have = {cid: v for cid, v in (prior or {}).items()
            if cid in set(ids) and v is not None}
    todo = [it for it in items if it["clause_id"] not in have]
    errors = []
    batches = rb._batches(todo, batch_size)
    for bi, batch in enumerate(batches, start=1):
        system, user = fidelity_prompt(batch)
        text, err, _ = _call_with_retry(client, system, user, attempts, sleep)
        if progress:
            progress(bi, len(batches))
        if err is not None:
            errors.append(f"fidelity/{bi}: {err}")
            continue
        parsed, errs = rb.parse_fidelity(text, batch)
        errors += [f"fidelity/{bi}: {e}" for e in errs]
        for it, p in zip(batch, parsed):
            if p is not None:
                have[it["clause_id"]] = p
    return have, errors


# --------------------------------------------------------------------------
# COVERAGE — counted against the declared sample, never against the results

def coverage(artifact):
    """`{rung: {annotated: (k, n), judged: (k, n), missing_*: [...]}}`.

    The denominator is `artifact["clause_ids"]`. That is the entire fix for
    the defect this gate exists to close: a clause whose call died never
    appears as a key anywhere in the results, so any count derived from the
    results is a count of the survivors.
    """
    ids = list(artifact.get("clause_ids") or [])
    n = len(ids)
    out = {}
    for rung, block in (artifact.get("rungs") or {}).items():
        spec = rung_spec(rung)
        fid = block.get("fidelity") or {}
        if spec["annotates"]:
            answered = block.get("annotated")
            if answered is None:
                answered = list((block.get("by_clause") or {}).keys())
            answered = [c for c in ids if c in set(answered)]
        else:
            answered = list(ids)
        out[rung] = {
            "annotated": (len(answered), n),
            "judged": (sum(1 for c in ids if fid.get(c) is not None), n),
            "missing_annotated": [c for c in ids if c not in set(answered)],
            "missing_judged": [c for c in ids if fid.get(c) is None],
        }
    return out


def control_coverage(artifact):
    """`{which: (k, n)}` for the judge's controls, against the DECLARED sample.

    The controls were the one part of the harness with no coverage gate, and
    they are the part that certifies every rung above them: with 2 of 125
    control calls surviving a rate-limited pass, both answered perfectly, the
    instrument gate printed PROCEED. That is the survivors-denominator defect
    this module exists to close, sitting inside the gate that licenses the
    rest of the table.
    """
    ids = list(artifact.get("clause_ids") or [])
    n = len(ids)
    out = {}
    for which in ("positive", "negative"):
        per = (artifact.get("controls") or {}).get(which) or {}
        out[which] = (sum(1 for c in ids if per.get(c) is not None), n)
    return out


def readback_coverage(art):
    """The true denominators of a READ-BACK artifact.

    A DEFECT REPORT, in executable form. `readback.summarize` reports
    `unanswered` as the number of explicit `None`s in the results dict, so a
    batch lost to a 429 — which writes no key at all — is invisible: the run
    that motivated the ladder reported `unanswered: 0` with a condition at
    90/125. Nothing here edits readback.py; this recomputes what it should
    have said, and `test_ladder.py` pins the discrepancy so the day it is
    fixed we are told.
    """
    ids = list(art.get("clause_ids") or [])
    n = len(ids)
    fid = (art.get("results") or {}).get("fidelity") or {}
    out = {"fidelity": (sum(1 for c in ids if fid.get(c) is not None), n),
           "discrim": {}}
    for cond, per in ((art.get("results") or {}).get("discrim") or {}).items():
        out["discrim"][cond] = (sum(1 for c in ids if per.get(c) is not None),
                                n)
    return out


# --------------------------------------------------------------------------
# rung 0 and the null arm — both offline, both free

def build_rung_0(clause_ids, rows, annotations, fidelity=None):
    """The shipped annotations, UNTRIMMED.

    Rung 0 is not held to the cap: it IS the cap. Trimming it would move the
    baseline every other rung is read against, and the cap's own value is
    derived from it.
    """
    bc = {c: list(annotations.get(c) or []) for c in clause_ids}
    # `by_clause_raw` is the same object here: rung 0 is never capped, so what
    # the annotator produced and what the judge sees are the same thing. It is
    # present so every rung in the artifact has the same shape and a resumed
    # --report never has to guess which field to re-cap from.
    return {"by_clause": bc, "by_clause_raw": bc,
            "annotated": list(clause_ids),
            "fidelity": dict(fidelity or {}), "errors": [],
            "cap": {"applied": False,
                    "why": "rung 0 defines the budget; trimming it would move "
                           "the baseline"}}


def build_null_arm(clause_ids, fidelity=None):
    return {"by_clause": {c: [] for c in clause_ids},
            "by_clause_raw": {c: [] for c in clause_ids},
            "annotated": list(clause_ids),
            "fidelity": dict(fidelity or {}), "errors": [],
            "cap": {"applied": False, "why": "no atoms"}}


def rung_0_fidelity_from_readback(path=READBACK_ARTIFACT):
    """Rung 0's verdicts, free, from the read-back artifact — same clauses,
    same renderer, same judge, same prompt. Re-billing them would buy nothing
    but a second sample of judge noise."""
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        art = json.load(f)
    return {c: v for c, v in
            ((art.get("results") or {}).get("fidelity") or {}).items()
            if v is not None}


# --------------------------------------------------------------------------
# WHAT NO RUNG CAN FIX
#
# The segmentation attribution found 16 of the 125 STRUCTURALLY ORPHANED: list
# items severed from their "...:" lead-in, lower-case fragments, bare
# antecedents (`m0117` is item 3 of a list whose prohibition lives in `m0114`;
# `m0103` is a bare "If..." whose consequent is in `m0102`). Their content is
# genuinely not in the clause, so no atom set can make them sufficient and
# every rung scores the same on them. Left in the denominator they flatten
# rung 3 towards rung 0 on 13% of the sample — which is precisely the pattern
# the Sol gate reads as "the grammar was never the constraint". They are
# therefore excluded from the GATE and reported on BOTH sides of the table, so
# the exclusion is a visible number rather than a silent filter.
#
# Overall segmentation is only ~2.6% of the sufficiency loss (Wilson
# 0.8-10.2%): the rest is in the clause's own text, which is what rungs 1-3
# exist to separate.

_ORPHAN_CACHE = {}

#: The `example` stratum is a measurement hazard, not a clause kind like the
#: others: 20 of its 23 missing phrases point at content inside XML
#: transcripts, so its sufficiency answers "can atoms represent a rendered
#: dialogue" rather than "can atoms represent a rule". Reported, never folded
#: into the headline.
HAZARD_KINDS = ("example",)


def structurally_orphaned(rows=None):
    """`{ids, available, why}` from `segmentation_attr.structural_flags()`.

    Consumed, not reimplemented — that module owns the definition and is
    already built. If it is missing or mid-edit the answer is an explicit
    `available: False` with an empty set, never a silent zero: a gate computed
    on an accidentally empty exclusion is the failure this exclusion exists to
    prevent.
    """
    key = "default" if rows is None else id(rows)
    if key in _ORPHAN_CACHE:
        return _ORPHAN_CACHE[key]
    try:
        import segmentation_attr
        flags = segmentation_attr.structural_flags(rows)
        out = {"ids": sorted(c for c, f in flags.items()
                             if any((f or {}).values())),
               "available": True,
               "why": "segmentation_attr.structural_flags(): fragment_start, "
                      "orphan_item or bare_condition"}
    except Exception as e:
        out = {"ids": [], "available": False,
               "why": f"segmentation_attr unavailable ({type(e).__name__}: "
                      f"{e}); NO clause excluded, so the gate is computed on "
                      f"all 125 and will read orphans as rung-3 failures"}
    _ORPHAN_CACHE[key] = out
    return out


# --------------------------------------------------------------------------
# summary, gates, table

def _rate(fid, ids, key):
    vals = [fid[c][key] for c in ids if fid.get(c) is not None]
    k, n = sum(1 for v in vals if v), len(vals)
    lo, hi = rb.wilson(k, n)
    return {"k": k, "n": n, "rate": (k / n) if n else None,
            "ci95": (lo, hi)}


def unsupported_profile(fid, ids):
    """OVER-ASSERTION, as a first-class number.

    Step 1 measured that the read-back's connection to retrieval runs through
    this and not through omission: `>=1 unsupported phrase` correlates +0.157
    [+0.062, +0.250] with per-clause retrieval error, `sufficient` only -0.096
    [-0.182, -0.014], and missing-party / missing-deontic are indistinguishable
    from zero. 86% of retrieval errors are FALSE POSITIVES (312 of 361), which
    is the mechanism: an unsupported atom is extra surface for a query to match
    on. Rungs 2-4 relax exactly the freedom that produces it, so a rung that
    "wins" on sufficiency while asserting more has moved the number most
    associated with the dominant failure.

    (Effect sizes here sit at or below the study's MDE and ~20 splits were
    tested with 5 CIs excluding zero against ~1 expected by chance. The
    DIRECTION is worth designing around; the magnitudes are not results.)
    """
    recs = [fid[c] for c in ids if fid.get(c) is not None]
    counts = [len(r.get("unsupported") or []) for r in recs]
    k, n = sum(1 for c in counts if c), len(recs)
    lo, hi = rb.wilson(k, n)
    return {"k": k, "n": n, "rate": (k / n) if n else None,
            "ci95": (lo, hi), "total": sum(counts),
            "mean_count": (sum(counts) / n) if n else None}


def summarize(artifact):
    """Every rung, three denominators, never one.

      sufficient            all 125, the pre-registered sample;
      sufficient_standalone minus the structurally orphaned, which no rung can
                            fix — this is the one the Sol gate reads;
      sufficient_headline   minus the orphans AND minus the `example` stratum,
                            which is largely asking whether atoms can
                            represent an XML transcript.

    Printing one of the three would be a filter; printing all three is a
    finding.
    """
    ids = list(artifact.get("clause_ids") or [])
    orphan_info = artifact.get("structurally_orphaned")
    if orphan_info is None:
        orphan_info = structurally_orphaned()
    orphans = set(orphan_info.get("ids") or [])
    kinds = artifact.get("clause_kinds") or {}
    standalone = [c for c in ids if c not in orphans]
    headline = [c for c in standalone if kinds.get(c) not in HAZARD_KINDS]
    out = {}
    for rung, block in (artifact.get("rungs") or {}).items():
        bc = block.get("by_clause") or {}
        fid = block.get("fidelity") or {}
        out[rung] = {
            "faithful": _rate(fid, ids, "faithful"),
            "sufficient": _rate(fid, ids, "sufficient"),
            "sufficient_standalone": _rate(fid, standalone, "sufficient"),
            "sufficient_headline": _rate(fid, headline, "sufficient"),
            "faithful_standalone": _rate(fid, standalone, "faithful"),
            "unsupported": unsupported_profile(fid, ids),
            "by_kind": {
                k: _rate(fid, [c for c in ids if kinds.get(c) == k],
                         "sufficient")
                for k in sorted(set(kinds.values()))},
            "n_orphans": len([c for c in ids if c in orphans]),
            "rate": rate_profile(bc, ids),
            "reuse": reuse_profile(bc, ids),
            "polarity": polarity_readiness(bc),
            "cap": block.get("cap") or {},
            "errors": len(block.get("errors") or []),
        }
    return out


def _order(rungs):
    known = [r for r in RUNGS if r in rungs]
    return known + ([NULL_ARM] if NULL_ARM in rungs else [])


def gates(artifact):
    """The prospective stop conditions, checked mechanically.

    Written before the run and encoded here rather than left as prose: the
    plan claimed every step had a stop condition and only two did. Each gate
    is PROCEED, STOP or UNKNOWN, and `table()` prints one VERDICT line.
    """
    ids = list(artifact.get("clause_ids") or [])
    s = summarize(artifact)
    out = {}

    cov = coverage(artifact)
    short = [f"{r} {st} {cov[r][st][0]}/{cov[r][st][1]}"
             for r in _order(artifact.get("rungs") or {})
             for st in ("annotated", "judged") if cov[r][st][0] != cov[r][st][1]]
    ccov = control_coverage(artifact)
    ctrl = artifact.get("controls") or {}
    ctrl_started = any((ctrl.get(w) or {}) for w in ("positive", "negative"))
    ctrl_short = [f"control:{w} {k}/{n}" for w, (k, n) in sorted(ccov.items())
                  if ctrl_started and k != n]
    short += ctrl_short
    out["coverage"] = {
        "verdict": "STOP" if short else "PROCEED",
        "why": ("incomplete: " + "; ".join(short[:8])) if short else
               "every rung and every control answered every declared clause"}

    pos = _rate(ctrl.get("positive") or {}, ids, "sufficient")
    neg = _rate(ctrl.get("negative") or {}, ids, "sufficient")
    if not pos["n"] or not neg["n"]:
        out["instrument"] = {
            "verdict": "STOP",
            "why": "the judge has no positive/negative control. Its "
                   "`sufficient` label is unvalidated, and all six of the "
                   "read-back's pre-registered predictions were wrong."}
    elif ctrl_short:
        # A control is a denominator like any other. Two surviving calls,
        # both perfect, must not certify the instrument that certifies every
        # rung above it.
        out["instrument"] = {
            "verdict": "STOP",
            "why": ("the controls are incomplete (" + "; ".join(ctrl_short)
                    + "), so the instrument is certified by its survivors. "
                      "Re-run the controls before reading any rung.")}
    else:
        ok = (pos["rate"] >= CONTROL_POSITIVE_MIN
              and neg["rate"] <= CONTROL_NEGATIVE_MAX)
        out["instrument"] = {
            "verdict": "PROCEED" if ok else "STOP",
            "why": (f"positive control sufficient {pos['rate']:.2f} "
                    f"(need >= {CONTROL_POSITIVE_MIN}) at "
                    f"{ccov['positive'][0]}/{ccov['positive'][1]}, negative "
                    f"control {neg['rate']:.2f} (need <= "
                    f"{CONTROL_NEGATIVE_MAX}) at {ccov['negative'][0]}/"
                    f"{ccov['negative'][1]}")}

    base, null = s.get("0"), s.get(NULL_ARM)
    if not base or not null or base["faithful"]["rate"] is None \
            or null["faithful"]["rate"] is None:
        out["null_arm"] = {"verdict": "UNKNOWN",
                           "why": "no null arm scored"}
    else:
        gain = base["faithful"]["rate"] - null["faithful"]["rate"]
        out["null_arm"] = {
            "verdict": "PROCEED" if gain > 0 else "STOP",
            "why": (f"rung 0 faithful {base['faithful']['rate']:.2f} vs an "
                    f"EMPTY render's {null['faithful']['rate']:.2f} "
                    f"(delta {gain:+.2f}); a delta of zero means the number "
                    f"is a target-independent constant")}

    over, notes = [], []
    for rung in _order(artifact.get("rungs") or {}):
        spec = rung_spec(rung)
        if not spec["capped"]:
            continue
        r = s[rung]["rate"]
        if r["atoms_per_clause"] > CAP_ATOMS_PER_CLAUSE + 1e-9:
            over.append(f"{rung} {r['atoms_per_clause']:.2f} atoms/clause")
        if not spec["text_is_chosen"]:
            # Rung 1 and 1.5 write NO text: their glosses are the
            # vocabulary's own, substituted by the harness. 2.78 x the mean
            # shipped gloss (76.2 chars) is 211.3, a hair over the cap, so a
            # global text cap would chop exactly the rung whose contrast with
            # the exempt rung 0 IS the assignment-error measurement.
            notes.append(f"{rung} text is a vocabulary lookup, not written by "
                         f"the annotator: priced at "
                         f"{r['text_chars_per_clause']:.0f} chars/clause and "
                         f"reported, not capped")
        elif r["text_chars_per_clause"] > CAP_TEXT_CHARS_PER_CLAUSE + 1e-9:
            over.append(f"{rung} {r['text_chars_per_clause']:.0f} chars/clause")
    out["rate_cap"] = {
        "verdict": "STOP" if over else "PROCEED",
        "why": (("over budget: " + "; ".join(over)) if over else
                "every capped rung is inside the shipped encoding budget")
               + (("  [" + "; ".join(notes) + "]") if notes else "")}

    mem = []
    if base and base["sufficient"]["rate"] is not None:
        for rung in _order(artifact.get("rungs") or {}):
            if rung in ("0", NULL_ARM):
                continue
            d = s[rung]
            if d["sufficient"]["rate"] is None:
                continue
            if (d["sufficient"]["rate"] > base["sufficient"]["rate"]
                    and d["reuse"]["hapax_share"]
                    > base["reuse"]["hapax_share"]):
                mem.append(rung)
    out["memorisation"] = {
        "verdict": "STOP" if mem else "PROCEED",
        "why": (f"rung(s) {', '.join(mem)} gained sufficiency WITH a rising "
                f"hapax share; that is memorisation, not expressiveness")
               if mem else "no rung's gain is accompanied by a hapax rise"}

    # OVER-ASSERTION. Chosen as a GATE rather than as an extra term in the
    # rate cap, deliberately. A hard cap would have to delete the atoms the
    # judge called unsupported, which makes the fidelity number
    # self-referential (atoms selected by the scorer, then scored) and hands
    # the encoding budget to an instrument that has not yet passed its own
    # controls. A gate keeps the two separable: the rung is measured as it was
    # produced, and a gain bought by asserting more is refused rather than
    # silently trimmed away.
    over_assert = []
    if base and base["sufficient"]["rate"] is not None:
        b_un = base["unsupported"]["rate"] or 0.0
        for rung in _order(artifact.get("rungs") or {}):
            if rung in ("0", NULL_ARM):
                continue
            d = s[rung]
            if d["sufficient"]["rate"] is None:
                continue
            if (d["sufficient"]["rate"] > base["sufficient"]["rate"]
                    and (d["unsupported"]["rate"] or 0.0) > b_un):
                over_assert.append(
                    f"{rung} (sufficient {base['sufficient']['rate']:.2f}->"
                    f"{d['sufficient']['rate']:.2f}, unsupported "
                    f"{b_un:.2f}->{d['unsupported']['rate']:.2f})")
    out["over_assertion"] = {
        "verdict": "STOP" if over_assert else "PROCEED",
        "why": (("sufficiency gain bought with more unsupported content: "
                 + "; ".join(over_assert)
                 + ". Over-assertion is the channel that predicts retrieval "
                   "error (+0.157) and 86% of retrieval errors are false "
                   "positives, so this is a loss dressed as a gain.")
                if over_assert else
                "no rung's sufficiency gain is accompanied by more "
                "unsupported content")}

    three = s.get("3")
    orphan_info = (artifact.get("structurally_orphaned")
                   or structurally_orphaned())
    n_orph = len(set(orphan_info.get("ids") or []) & set(ids))
    if not base or not three \
            or three["sufficient_standalone"]["rate"] is None \
            or base["sufficient_standalone"]["rate"] is None:
        out["grammar_is_the_constraint"] = {
            "verdict": "UNKNOWN", "why": "rung 3 or rung 0 not scored"}
    else:
        # THE GATE READS THE STANDALONE SUBSET. On the 16 structurally
        # orphaned clauses every rung scores the same because the content is
        # not in the clause, so including them drags rung 3 towards rung 0 and
        # fires this gate for a reason that has nothing to do with grammar.
        d_stand = (three["sufficient_standalone"]["rate"]
                   - base["sufficient_standalone"]["rate"])
        d_all = three["sufficient"]["rate"] - base["sufficient"]["rate"]
        out["grammar_is_the_constraint"] = {
            "verdict": "PROCEED" if d_stand >= GRAMMAR_GATE_DELTA else "STOP",
            "why": (f"rung 3 vs rung 0 on the STANDALONE subset "
                    f"(125 minus {n_orph} structurally orphaned): "
                    f"{three['sufficient_standalone']['rate']:.2f} vs "
                    f"{base['sufficient_standalone']['rate']:.2f}, delta "
                    f"{d_stand:+.2f} against gate {GRAMMAR_GATE_DELTA:+.2f}. "
                    f"On all 125 the delta is {d_all:+.2f}. Rung 3 is "
                    f"unlimited within the schema: if it does not beat rung 0 "
                    f"where a rung COULD help, the grammar was never the "
                    f"constraint and the Sol run must NOT be paid for."
                    + ("" if orphan_info.get("available") else
                       "  !! " + orphan_info.get("why", "")))}
    return out


def verdict(g):
    return "STOP" if any(v["verdict"] == "STOP" for v in g.values()) \
        else "PROCEED"


def table(artifact, strict=True):
    """The rung table. REFUSES below 100% coverage, and refuses without the
    null arm.

    Both refusals are about the same thing: a table is a claim, and the two
    ways this experiment can silently make a false one are a shrunken
    denominator and an uncontrolled constant.
    """
    rungs = artifact.get("rungs") or {}
    ids = list(artifact.get("clause_ids") or [])
    if strict and NULL_ARM not in rungs:
        raise LadderError(
            "refusing to emit a table without the null-ontology arm: "
            "render([], kind) still emits a kind label and boilerplate, so "
            "without it no rung's fidelity can be told from a "
            "target-independent constant.")
    cov = coverage(artifact)
    if strict:
        short = []
        for rung in _order(rungs):
            c = cov[rung]
            for stage in ("annotated", "judged"):
                k, n = c[stage]
                if k != n:
                    miss = c["missing_" + stage][:5]
                    short.append(f"  rung {rung}: {stage} {k}/{n}"
                                 f"  missing e.g. {', '.join(miss)}")
        if short:
            raise CoverageError(
                "refusing to emit a rung table below 100% coverage — a "
                "shrunken denominator moves a number further than the effect "
                "being measured:\n" + "\n".join(short))

    s = summarize(artifact)
    prov = artifact.get("provenance") or {}
    s0_orphans = (s[_order(rungs)[0]]["n_orphans"] if _order(rungs) else 0)
    lines = [
        "",
        f"THE ATTRIBUTION LADDER   n={len(ids)}  seed={prov.get('seed')}  "
        f"model={prov.get('model')}",
        f"rate cap: <= {CAP_ATOMS_PER_CLAUSE} atoms/clause, "
        f"<= {CAP_TEXT_CHARS_PER_CLAUSE} chars of free text/clause "
        f"(rung 0 defines it and is not trimmed)",
        "this table measures ANNOTATION AND RENDERER JOINTLY: render() is "
        "held fixed across",
        "rungs, so a faithfulness failure caused by the template "
        "over-asserting is charged here",
        "to the ontology. No rung varies the renderer.",
        "`faithful` and `unsup` are ONE measurement, not two: unsup is exactly "
        "the complement of",
        "faithful (a clause is unfaithful iff the judge listed an unsupported "
        "phrase). unsup is",
        "shown because over-assertion, not omission, is the channel that "
        "predicts retrieval error",
        "(+0.157 [+0.062,+0.250]; 86% of retrieval errors are false "
        "positives), so a sufficiency",
        "gain arriving with a higher unsup is a loss dressed as a gain.",
        f"sufficiency is shown on all {len(ids)} and on the STANDALONE subset "
        f"(minus {s0_orphans} clauses",
        "the segmentation attribution flagged as unable to stand alone "
        "whatever their atoms).",
        "",
        f"{'rung':6s}{'faithful':>25s}{'sufficient (all)':>25s}"
        f"{'sufficient (stand)':>25s}{'unsup':>7s}{'unsup/cl':>9s}"
        f"{'atoms/cl':>10s}{'text/cl':>9s}{'names':>7s}{'hapax':>8s}"
        f"{'meandf':>8s}{'polar':>7s}  relaxes",
    ]

    def cell(r):
        if not r["n"]:
            return "-"
        return (f"{r['rate']:.2f} [{r['ci95'][0]:.2f},"
                f"{r['ci95'][1]:.2f}] n={r['n']}")

    for rung in _order(rungs):
        d = s[rung]
        un = d["unsupported"]
        lines.append(
            f"{rung:6s}{cell(d['faithful']):>25s}{cell(d['sufficient']):>25s}"
            f"{cell(d['sufficient_standalone']):>25s}"
            f"{(un['rate'] if un['rate'] is not None else 0):>7.2f}"
            f"{(un['mean_count'] if un['mean_count'] is not None else 0):>9.2f}"
            f"{d['rate']['atoms_per_clause']:>10.2f}"
            f"{d['rate']['text_chars_per_clause']:>9.0f}"
            f"{d['reuse']['distinct_names']:>7d}"
            f"{d['reuse']['hapax_share']:>8.2f}"
            f"{d['reuse']['mean_df']:>8.2f}"
            f"{d['polarity']['polarity_share']:>7.2f}  "
            + rung_spec(rung)["relaxes"])

    if any(s[r]["by_kind"] for r in _order(rungs)):
        lines += ["", "sufficiency per clause kind. The `example` stratum is "
                      "reported here and kept OUT",
                  "of the headline: 20 of its 23 missing phrases point at "
                  "content inside XML transcripts,",
                  "so it answers 'can atoms represent a rendered dialogue', "
                  "a different question."]
        kinds = sorted({k for r in _order(rungs) for k in s[r]["by_kind"]})
        lines.append(f"  {'rung':6s}" + "".join(f"{k:>14s}" for k in kinds)
                     + f"{'headline':>14s}")
        for rung in _order(rungs):
            row = []
            for k in kinds:
                c = s[rung]["by_kind"].get(k)
                row.append("-" if not c or not c["n"]
                           else f"{c['rate']:.2f} n={c['n']}")
            h = s[rung]["sufficient_headline"]
            row.append("-" if not h["n"] else f"{h['rate']:.2f} n={h['n']}")
            lines.append(f"  {rung:6s}" + "".join(f"{c:>14s}" for c in row))

    lines += ["", "batch size and eviction (what sets the bill):"]
    for rung in _order(rungs):
        sp = rung_spec(rung)
        lines.append(f"  {rung:6s}batch {sp['batch_size']}   "
                     f"vocabulary eviction: {sp['eviction']}")

    lines += ["", "df distribution (names by how many clauses use them):"]
    for rung in _order(rungs):
        lines.append(f"  {rung:6s}{s[rung]['reuse']['df_distribution']}")

    ctrl = artifact.get("controls") or {}
    if ctrl:
        ccov = control_coverage(artifact)
        lines += ["", "JUDGE CONTROLS (bounding the instrument, not the "
                      "ontology):"]
        for which in ("positive", "negative"):
            r = _rate(ctrl.get(which) or {}, ids, "sufficient")
            k, n = ccov[which]
            lines.append(f"  {which:9s}sufficient {cell(r)}"
                         f"   coverage {k}/{n}"
                         + ("   (must be high)" if which == "positive"
                            else "   (must be low)"))
    cerrs = artifact.get("control_errors") or []
    if cerrs:
        lines += ["", f"control_errors ({len(cerrs)}) — the instrument's own "
                      f"calls that failed:"]
        for e in cerrs[:6]:
            lines.append("   !! " + str(e))

    g = gates(artifact)
    lines += ["", "GATES"]
    for name in ("coverage", "instrument", "null_arm", "rate_cap",
                 "memorisation", "over_assertion",
                 "grammar_is_the_constraint"):
        if name in g:
            lines.append(f"  {g[name]['verdict']:8s}{name:26s}"
                         f"{g[name]['why']}")
    lines += ["", f"VERDICT: {verdict(g)}"
                  + ("  — do not proceed to the Sol run"
                     if verdict(g) == "STOP" else
                     "  — the Sol run is justified on these numbers")]

    caps = [(r, s[r]["cap"]) for r in _order(rungs)
            if s[r]["cap"].get("applied")]
    if caps:
        lines += ["", "rate-cap enforcement (what had to be trimmed):"]
        for r, c in caps:
            lines.append(f"  {r:6s}atoms dropped {c.get('atoms_dropped', 0)}, "
                         f"free-text chars dropped "
                         f"{c.get('gloss_chars_dropped', 0)}, per-field "
                         f"ceiling {c.get('text_field_ceiling')}")
    errs = [(r, s[r]["errors"]) for r in _order(rungs) if s[r]["errors"]]
    if errs:
        lines += ["", "errors: " + ", ".join(f"{r}={n}" for r, n in errs)]
    lines.append("")
    return "\n".join(lines)


# ==========================================================================
# FENCED DIAGNOSTIC — READS THE PANEL. NOTHING ABOVE THIS LINE MAY CALL IT.
#
# `weight_diag.py` established the pattern: a panel-reading measurement is
# allowed to exist as long as it cannot inform the thing it measures. Nothing
# on the build path (`annotate_rung`, `annotate_prompt_for`,
# `verify_rung_atoms`, `enforce_rate_cap`, `render_for_rung`, `run_ladder`)
# mentions this section, and `test_no_annotation_path_can_reach_the_relevance_hook`
# asserts it by reading their source.
# ==========================================================================

def relevance_diagnostic(artifact, clauses_path=CLAUSES_PATH,
                         annotations_path=ANNOTATIONS_PATH, normalise=True):
    """DIAGNOSTIC ONLY. Measured ONCE, NEVER fed back into the ontology.

    Fidelity and sufficiency are read-back quantities. They do not establish
    that a rung's atoms RETRIEVE better, which is the goal the project is
    actually held to, so this scores each rung's atoms against the panel under
    the shipped compliant query and the shipped operator. Invariant 9 bars
    FITTING to the panel, not measuring against it; this number may inform a
    write-up and may NEVER inform a prompt, a vocabulary, a threshold or a
    schema.

    Three caveats it prints with its numbers, because each of them could turn
    a null result into a false one:
      - only 125 of 587 clauses are re-annotated, so the corpus is 79% shipped
        and any delta is diluted by roughly a factor of five;
      - `structural`/`section` match on atom NAMES and TYPES, so a rung whose
        gain is in its GLOSSES cannot show up here at all — which is itself
        the finding, and the reason `polarity_readiness` exists;
      - rungs 1.5 and 2 rename atoms under the ladder's own convention, so the
        normalised view (stems only) is the comparable one.
    """
    fence = ("DIAGNOSTIC-ONLY, panel-reading. Measured once and NEVER fed "
             "back into any prompt, vocabulary, threshold or schema.")
    out = {"fence": fence, "rungs": {},
           "caveats": ["125 of 587 clauses re-annotated; deltas diluted ~5x",
                       "compliant modules match names and types, not glosses",
                       "stem-normalised view used for convention rungs"]}
    ids = list(artifact.get("clause_ids") or [])
    try:
        import benchmark
        base_ann = rb.load_annotations(annotations_path)
        clauses = benchmark.load_clauses()
        if isinstance(clauses, tuple):      # (rows, spec_text)
            clauses = clauses[0]
        panel = benchmark.load_panel()
    except Exception as e:                      # a missing artifact is data
        for rung in (artifact.get("rungs") or {}):
            out["rungs"][rung] = {"unavailable": f"{type(e).__name__}: {e}"}
        return out

    for rung, block in (artifact.get("rungs") or {}).items():
        bc = block.get("by_clause") or {}
        view = stem_normalised(bc) if normalise else bc
        merged = dict(base_ann)
        for cid in ids:
            if cid in view:
                merged[cid] = view[cid]
        try:
            qm = benchmark.build_query_module("structural", panel, clauses,
                                              merged)
            per = {}
            for slug in panel:
                ev = benchmark.evaluate(panel[slug], qm.predict(slug), clauses)
                vals = [t.get("mcc_full") for t in ev.get("per_target", ev).values()
                        if isinstance(t, dict) and t.get("mcc_full") is not None]
                if vals:
                    per[slug] = sum(vals) / len(vals)
            out["rungs"][rung] = {
                "mcc": (sum(per.values()) / len(per)) if per else None,
                "by_behaviour": per,
                "n_clauses_replaced": sum(1 for c in ids if c in view)}
        except Exception as e:
            out["rungs"][rung] = {"unavailable": f"{type(e).__name__}: {e}"}
    return out


# --------------------------------------------------------------------------
# COST — from measured tokens, never from a guess

def _usage_rows(path=USAGE_PATH):
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    pass
    return out


def calibrate_chars_per_token(usage_path=USAGE_PATH,
                              artifact=READBACK_ARTIFACT):
    """Characters per prompt token, MEASURED on this repo's own calls.

    There is no tokenizer in this environment, so the conversion has to come
    from somewhere real. The read-back's discrimination prompts are fully
    reconstructible offline (`build_trials` is seeded and deterministic) and
    their calls are in usage.jsonl with `prompt_tokens`, identifiable by their
    ~211-character JSON replies. Matching the two sorted distributions
    quantile by quantile gives the ratio without needing to pair individual
    calls, which the log does not allow.
    """
    rows = rb.load_clauses()
    ann = rb.load_annotations()
    ids = None
    if os.path.exists(artifact):
        with open(artifact, encoding="utf-8") as f:
            ids = (json.load(f) or {}).get("clause_ids")
    ids = ids or sample(rows)
    chars = []
    for n, mode in ((4, "random"), (10, "random"),
                    (4, "section"), (10, "section")):
        trials = rb.build_trials(ids, rows, ann, n, mode, SEED)
        for b in rb._batches(trials, 5):
            system, user = rb.discrim_prompt(b)
            chars.append(len(system) + len(user))
    # Fingerprint = reply size AND model. Measured 2026-08-18: 81 DeepSeek
    # classification calls (act/situation ontology batches) landed in the
    # 190-230 reply band and, with their much larger prompts, inflated the
    # quantile-matched ratio to 6.89. The discrimination campaign ran on
    # luna only; the model field separates the populations exactly (102/81).
    logged = [r["prompt_tokens"] for r in _usage_rows(usage_path)
              if r.get("prompt_tokens")
              and 190 <= (r.get("content_chars") or 0) <= 230
              and "luna" in (r.get("model") or "")]
    if not chars or len(logged) < 20:
        return {"chars_per_token": 4.6, "n_calls": len(logged),
                "source": usage_path, "method": "fallback (no usable log)"}
    chars.sort()
    logged.sort()
    ratios = []
    for q in (0.1, 0.25, 0.5, 0.75, 0.9):
        a = chars[min(len(chars) - 1, int(q * len(chars)))]
        b = logged[min(len(logged) - 1, int(q * len(logged)))]
        if b:
            ratios.append(a / b)
    ratios.sort()
    return {"chars_per_token": ratios[len(ratios) // 2],
            "n_calls": len(logged), "n_prompts": len(chars),
            "source": usage_path,
            "method": "quantile match, readback discrimination prompts"}


def measured_output_profile(usage_path=USAGE_PATH, ann_path=ANNOTATIONS_PATH):
    """Completion tokens an annotation call actually spent, from the b8 run.

    Reasoning is billed as completion and on this model it dominates (~65% of
    completion on the measured pass), so an estimate built from the JSON's
    size alone would be out by a factor of three. Reported per BATCH and per
    CLAUSE because the ladder's batch is 1 and reasoning does not scale down
    linearly — the honest estimate is the range between the two.
    """
    with open(ann_path, encoding="utf-8") as f:
        prov = (json.load(f) or {}).get("provenance") or {}
    created, model = prov.get("created"), prov.get("model")
    n_batches = prov.get("n_batches") or 0
    plan = prov.get("plan") or []
    per_batch = (sum(p.get("clauses", 0) for p in plan) / len(plan)
                 ) if plan else 8.0
    rows = _usage_rows(usage_path)
    if created:
        t = time.mktime(time.strptime(created, "%Y-%m-%dT%H:%M:%S"))
        rows = [r for r in rows if r.get("model") == model
                and r.get("ts") and t - 7200 <= r["ts"] <= t]
    rows = sorted(rows, key=lambda r: r.get("ts") or 0)[-n_batches:]
    if not rows:
        return {"n": 0, "completion_per_batch": 2347.0,
                "reasoning_per_batch": 1525.0, "clauses_per_batch": per_batch,
                "method": "fallback (no usable log)"}
    comp = sum(r.get("completion_tokens") or 0 for r in rows) / len(rows)
    reas = sum(r.get("reasoning_tokens") or 0 for r in rows) / len(rows)
    return {"n": len(rows), "completion_per_batch": comp,
            "reasoning_per_batch": reas, "clauses_per_batch": per_batch or 8.0,
            "method": f"{len(rows)} logged calls of the {model} b8 pass"}


def provider_for(name, path=PROVIDERS_PATH):
    from providers import ProviderConfig
    for p in ProviderConfig.load_all(path):
        if p.name == name:
            return p
    raise LadderError(f"no provider named {name!r} in {path}")


def _common_prefix_len(strings):
    if not strings:
        return 0
    a, b = min(strings), max(strings)
    i = 0
    while i < len(a) and i < len(b) and a[i] == b[i]:
        i += 1
    return i


#: Providers cache a request's constant prefix and bill it at a tenth WHEN
#: THEY DO IT AUTOMATICALLY; nothing in providers.py asks for it. Every
#: annotation call in a rung shares the system prompt and the whole 361-atom
#: vocabulary block, which is most of the request, so the two cases differ by
#: nearly an order of magnitude and quoting one number would be a guess
#: dressed as a measurement. Both are reported.
CACHED_INPUT_DISCOUNT = 0.1

#: Measured on the read-back's fidelity calls: a batch of 5 spends ~600
#: completion tokens including reasoning.
JUDGE_COMPLETION_PER_BATCH = 600


def estimate_cost(rungs=RUNGS, models=("luna", "sol"), clause_ids=None,
                  rows=None, vocab=None, fidelity_batch=5, controls=True,
                  max_tokens=4096, fidelity_max_tokens=4000):
    """`{model: {rung: {...usd...}}}` from prompts actually built and measured.

    Nothing here is assumed: the prompts are constructed exactly as the live
    run would construct them and their characters counted; the
    characters-per-token ratio and the completion-token profile both come from
    this repo's logged calls. This is the function the drift review's finding 2
    demanded, and it is what `--dry-run` prints.
    """
    rows = rows if rows is not None else rb.load_clauses()
    ids = list(clause_ids or sample(rows))
    vocab = vocab if vocab is not None else load_vocabulary()
    ann = rb.load_annotations()
    cal = calibrate_chars_per_token()
    cpt = cal["chars_per_token"]
    outp = measured_output_profile()
    blocks = load_rung_blocks()
    by_id = {r["id"]: r for r in rows}

    per_rung = {}
    todo = list(rungs) + (["controls"] if controls else [])
    for rung in todo:
        prompts, judge = [], []
        if rung == "controls":
            for which in ("positive", "negative"):
                items = control_items(ids, rows, which, ann)
                for b in rb._batches(items, fidelity_batch):
                    system, user = fidelity_prompt(b)
                    judge.append(system + "\n" + user)
        else:
            spec = rung_spec(rung)
            if spec["annotates"]:
                for cid in ids:
                    system, user = annotate_prompt_for(by_id[cid], rung, vocab,
                                                       rows, blocks)
                    prompts.append(system + "\n" + user)
            bc = ({c: ann.get(c, []) for c in ids} if rung == "0"
                  else {c: [] for c in ids})
            items = fidelity_items(ids, rows, bc, rung)
            for b in rb._batches(items, fidelity_batch):
                system, user = fidelity_prompt(b)
                judge.append(system + "\n" + user)

        ann_chars = sum(len(p) for p in prompts)
        judge_chars = sum(len(p) for p in judge)
        cached_chars = _common_prefix_len(prompts) * len(prompts)
        per_clause = outp["completion_per_batch"] / outp["clauses_per_batch"]
        content_per_clause = ((outp["completion_per_batch"]
                               - outp["reasoning_per_batch"])
                              / outp["clauses_per_batch"])
        per_rung[rung] = {
            "calls": len(prompts) + len(judge),
            "annotation_calls": len(prompts), "judge_calls": len(judge),
            "prompt_chars": ann_chars + judge_chars,
            "cached_prefix_chars": cached_chars,
            "in_tokens": (ann_chars + judge_chars) / cpt,
            "cached_tokens": cached_chars / cpt,
            # low: reasoning scales with clauses. high: reasoning is a fixed
            # per-CALL cost, which a batch of 1 pays 125 times.
            "out_tokens_low": (len(prompts) * per_clause
                               + len(judge) * JUDGE_COMPLETION_PER_BATCH),
            "out_tokens_high": (len(prompts)
                                * (content_per_clause
                                   + outp["reasoning_per_batch"])
                                + len(judge) * JUDGE_COMPLETION_PER_BATCH),
            # THE ACTUAL CEILING. `high` uses the batch-8 MEAN reasoning, but
            # the measured b8 completion distribution is p90 3202 / max 4060
            # against a 4096 cap — already brushing it at batch 8. A batch-1
            # call running to the cap is not a tail event, and a budget check
            # has to be made against what CAN be spent, not what is likely.
            "out_tokens_ceiling": (len(prompts) * max_tokens
                                   + len(judge) * fidelity_max_tokens),
        }

    out = {}
    for m in models:
        p = provider_for(m)
        pin, pout = p.price_per_mtok
        out[m] = {}
        for rung, d in per_rung.items():
            uncached = d["in_tokens"] - d["cached_tokens"]
            usd_in = d["in_tokens"] / 1e6 * pin
            usd_in_cached = ((uncached + d["cached_tokens"]
                              * CACHED_INPUT_DISCOUNT) / 1e6 * pin)
            out[m][rung] = dict(
                d, model=p.model,
                usd=usd_in + d["out_tokens_high"] / 1e6 * pout,
                usd_low=usd_in_cached + d["out_tokens_low"] / 1e6 * pout,
                usd_cached_input=(usd_in_cached
                                  + d["out_tokens_high"] / 1e6 * pout),
                usd_ceiling=usd_in + d["out_tokens_ceiling"] / 1e6 * pout)
        out[m]["_total_usd"] = sum(v["usd"] for k, v in out[m].items()
                                   if not k.startswith("_"))
        out[m]["_total_usd_low"] = sum(v["usd_low"] for k, v in out[m].items()
                                       if not k.startswith("_"))
        out[m]["_total_usd_ceiling"] = sum(
            v["usd_ceiling"] for k, v in out[m].items()
            if not k.startswith("_"))
    out["_calibration"] = {"chars_per_token": cal, "output": outp}
    return out


def cost_report(est):
    cal = est["_calibration"]
    lines = [
        "",
        "COST, from measured token counts. Prompts are built exactly as the "
        "live run would build",
        "them and counted; chars/token and the completion profile come from "
        "this repo's usage.jsonl.",
        f"  chars/token {cal['chars_per_token']['chars_per_token']:.2f} "
        f"({cal['chars_per_token']['method']}, "
        f"n={cal['chars_per_token']['n_calls']})",
        f"  completion/batch {cal['output']['completion_per_batch']:.0f} tok, "
        f"of which reasoning {cal['output']['reasoning_per_batch']:.0f} "
        f"({cal['output']['method']})",
        "  $ CEILING = every annotation call runs to --max-tokens. THE "
        "BUDGET CHECK USES THIS.",
        "    The b8 completion distribution is p90 3202 / max 4060 against a "
        "4096 cap, so a",
        "    batch-1 call hitting the cap is not a tail event.",
        "  $ likely = no caching, reasoning at the measured batch-8 mean.",
        "  $ cached = the same run if the provider caches the constant "
        "vocabulary prefix at 10%.",
        "",
        f"  {'model':7s}{'rung':9s}{'calls':>7s}{'in tok':>11s}"
        f"{'out tok':>10s}{'$ CEILING':>11s}{'$ likely':>10s}"
        f"{'$ cached':>10s}{'$ best':>9s}",
    ]
    for m, byr in est.items():
        if m.startswith("_"):
            continue
        for rung, d in byr.items():
            if rung.startswith("_"):
                continue
            lines.append(
                f"  {m:7s}{rung:9s}{d['calls']:>7d}{d['in_tokens']:>11.0f}"
                f"{d['out_tokens_high']:>10.0f}{d['usd_ceiling']:>11.3f}"
                f"{d['usd']:>10.3f}"
                f"{d['usd_cached_input']:>10.3f}{d['usd_low']:>9.3f}")
        lines.append(f"  {m:7s}{'TOTAL':9s}{'':7s}{'':11s}{'':10s}"
                     f"{byr['_total_usd_ceiling']:>11.3f}"
                     f"{byr['_total_usd']:>10.3f}{'':10s}"
                     f"{byr['_total_usd_low']:>9.3f}")
    lines.append("")
    return "\n".join(lines)


def preflight(rungs, model, budget=None, clause_ids=None, rows=None,
              max_tokens=4096, fidelity_max_tokens=4000, controls=True):
    """Refuse a run that COULD break the budget, before a client is built.

    Checked against the ceiling, not the likely case. The session budget is
    $7.50 and the plan's estimate for the whole luna ladder was $0.40-0.60;
    the measured ceiling for the same run is an order of magnitude above that,
    and the difference is entirely reasoning tokens on a batch of one.
    """
    import spend
    spent = spend.total()["total"]
    budget = spend.BUDGET if budget is None else budget
    est = estimate_cost(rungs=tuple(rungs), models=(model,),
                        clause_ids=clause_ids, rows=rows, controls=controls,
                        max_tokens=max_tokens,
                        fidelity_max_tokens=fidelity_max_tokens)
    proj = est[model]["_total_usd_ceiling"]
    ok = (spent + proj) <= budget
    return {
        "ok": bool(ok), "model": model, "rungs": list(rungs),
        "spent": spent, "budget": budget, "projected_ceiling_usd": proj,
        "projected_likely_usd": est[model]["_total_usd"],
        "why": (f"{model}: ceiling ${proj:.2f} on top of ${spent:.2f} already "
                f"spent is ${spent + proj:.2f} against a ${budget:.2f} "
                f"budget" + ("" if ok else " — REFUSED. Run fewer rungs per "
                             "invocation (--rungs), or reduce n "
                             "(reduced_sample), or get explicit approval."))}


# --------------------------------------------------------------------------
# the run

def run_ladder(rungs, model, live=False, clause_ids=None, rows=None,
               annotations=None, attempts=3, resume=None, out_path=None,
               max_tokens=4096, fidelity_max_tokens=4000, progress=None,
               client=None, fidelity_client=None, controls=True):
    """One command, one seed, model a parameter. `--model luna` and
    `--model sol` reach exactly this, differing only in the provider row."""
    rows = rows if rows is not None else rb.load_clauses()
    annotations = (annotations if annotations is not None
                   else rb.load_annotations())
    ids = list(clause_ids or sample(rows))
    vocab = load_vocabulary()
    blocks = load_rung_blocks()
    assert_demonstrations_synthetic(demonstration_passages(blocks))
    assert_demonstrations_frozen(passages=demonstration_passages(blocks))

    prior, prior_controls, prior_art = {}, {}, {}
    if resume and os.path.exists(resume):
        with open(resume, encoding="utf-8") as f:
            prior_art = json.load(f) or {}
        prior = prior_art.get("rungs") or {}
        prior_controls = prior_art.get("controls") or {}
        old_ids = prior_art.get("clause_ids")
        if old_ids and list(old_ids) != ids:
            raise LadderError(
                f"{resume} was run over a different sample "
                f"({len(old_ids)} clauses) than this invocation ({len(ids)}). "
                "Resuming across samples would mix two denominators.")

    if client is None and live:
        from providers import make_client
        cfg = provider_for(model)
        cfg.max_tokens = max_tokens
        client = make_client(cfg, live=True, log_dir="prompt_log_ladder")
        cfg2 = provider_for(model)
        cfg2.max_tokens = fidelity_max_tokens
        fidelity_client = fidelity_client or make_client(
            cfg2, live=True, log_dir="prompt_log_ladder")
    fidelity_client = fidelity_client or client

    art = {"provenance": {
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "seed": SEED, "per_kind": PER_KIND,
        "model": provider_for(model).model, "provider": model,
        "live": bool(live), "rungs": list(rungs),
        "cap_atoms": CAP_ATOMS_PER_CLAUSE,
        "cap_text_chars": CAP_TEXT_CHARS_PER_CLAUSE,
        "per_clause_ceiling": PER_CLAUSE_ATOM_CEILING,
        "renderer": "readback.render via ladder.render_for_rung",
        "demonstrations_sha256": demonstrations_sha256(),
        "measured_shipped_budget": measured_shipped_budget(),
    }, "clause_ids": ids,
        # WRITTEN BY THE RUN, not recomputed at report time. `summarize` reads
        # both: without `clause_kinds` the per-kind block silently vanishes
        # and `sufficient_headline` quietly equals `sufficient_standalone`
        # while the table's prose still claims the `example` stratum was
        # excluded. Freezing the orphan set stops a later --report, or a later
        # edit to segmentation_attr, scoring against a different denominator
        # than the run did.
        "clause_kinds": {r["id"]: r.get("kind") for r in rows
                         if r["id"] in set(ids)},
        "structurally_orphaned": structurally_orphaned(rows),
        # Rungs are meant to be runnable as separate invocations — the only
        # way a $5-ceiling run stays interruptible — so a rung this
        # invocation did not run is CARRIED, never erased. That also makes
        # `--out == --resume` safe, which is the natural way to use it.
        "rungs": {k: v for k, v in prior.items() if k not in set(rungs)},
        "controls": dict(prior_controls)}

    def save():
        if out_path:
            tmp = out_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(art, f, indent=1, ensure_ascii=False)
            os.replace(tmp, out_path)   # never leave a half-written artifact

    import spend
    try:
        spent0 = spend.total()["total"]
    except Exception:
        spent0 = None

    for rung in rungs:
        pri = prior.get(rung) or {}
        if rung == "0":
            block = build_rung_0(ids, rows, annotations,
                                 fidelity=(pri.get("fidelity")
                                           or rung_0_fidelity_from_readback()))
        elif rung == NULL_ARM:
            block = build_null_arm(ids, fidelity=pri.get("fidelity"))
        else:
            cap_text = rung_spec(rung)["text_is_chosen"]

            def _ckpt(bc, _r=rung, _p=pri, _t=cap_text):
                art["rungs"][_r] = recap_block(
                    {"by_clause_raw": bc, "annotated": [c for c in ids
                                                        if c in bc],
                     "fidelity": dict(_p.get("fidelity") or {}),
                     "errors": []}, ids, cap_text=_t)
                save()

            bc, stats, errors = annotate_rung(
                ids, rows, rung, vocab, client, attempts=attempts,
                prior=pri.get("by_clause_raw") or pri.get("by_clause"),
                progress=progress, blocks=blocks, checkpoint=_ckpt)
            # The cap is applied ONCE, from the raw answer, over the FULL
            # declared sample — not over the survivors, and not again on top
            # of an already-capped resumed block.
            block = recap_block(
                {"by_clause_raw": bc,
                 "annotated": [c for c in ids if c in bc],
                 "annotate_stats": stats, "errors": list(errors),
                 "fidelity": dict(pri.get("fidelity") or {})},
                ids, cap_text=cap_text)
        if client is not None:
            items = fidelity_items(ids, rows, block["by_clause"], rung)
            verdicts, ferrs = judge_fidelity(
                items, fidelity_client, prior=block.get("fidelity"),
                attempts=attempts, progress=progress)
            block["fidelity"] = verdicts
            block["errors"] = list(block.get("errors") or []) + ferrs
        art["rungs"][rung] = block
        save()
        if spent0 is not None and live:
            try:
                now = spend.total()["total"]
                print(f"  [spend] after rung {rung}: ${now:.3f} "
                      f"(+${now - spent0:.3f} this run)", flush=True)
            except Exception:
                pass

    if controls and client is not None:
        for which in ("positive", "negative"):
            items = control_items(ids, rows, which, annotations)
            got, errs = judge_fidelity(items, fidelity_client,
                                       prior=prior_controls.get(which),
                                       attempts=attempts, progress=progress)
            art["controls"][which] = got
            if errs:
                art.setdefault("control_errors", []).extend(errs)
            save()
    return art


# --------------------------------------------------------------------------
# CLI

def build_parser():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--live", action="store_true",
                    help="spend money. Off unless asked for.")
    ap.add_argument("--dry-run", action="store_true",
                    help="build every prompt, call nothing, price it")
    ap.add_argument("--model", default="luna",
                    help="a provider name from providers.json")
    ap.add_argument("--rungs", default=",".join(RUNGS) + "," + NULL_ARM)
    ap.add_argument("--attempts", type=int, default=3)
    ap.add_argument("--resume", help="artifact whose answers to keep")
    ap.add_argument("--report", help="re-print the table from an artifact")
    ap.add_argument("--relevance-diagnostic",
                    help="FENCED: score an artifact's rungs against the panel")
    ap.add_argument("--cost", action="store_true")
    ap.add_argument("--out", default="ladder_results.json")
    ap.add_argument("--limit", type=int, default=0,
                    help="pilot: keep only this many clauses")
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--fidelity-max-tokens", type=int, default=4000)
    ap.add_argument("--force-cost", action="store_true",
                    help="override the pre-flight budget refusal. Needs "
                         "explicit human approval; it is not a default.")
    ap.add_argument("--no-strict", action="store_true",
                    help="print a table below full coverage. Do not.")
    return ap


def main(argv=None):
    a = build_parser().parse_args(argv)

    if a.report:
        with open(a.report, encoding="utf-8") as f:
            print(table(json.load(f), strict=not a.no_strict))
        return 0

    if a.relevance_diagnostic:
        with open(a.relevance_diagnostic, encoding="utf-8") as f:
            print(json.dumps(relevance_diagnostic(json.load(f)), indent=1))
        return 0

    rungs = [r.strip() for r in a.rungs.split(",") if r.strip()]
    rows = rb.load_clauses()
    ids = sample(rows)
    if a.limit:
        ids = ids[:a.limit]

    if a.cost:
        print(cost_report(estimate_cost(rungs=tuple(rungs),
                                        models=("luna", "sol"),
                                        clause_ids=ids, rows=rows)))
        return 0

    if not a.live:
        # Dry run: build every prompt so a reviewer can diff them, call
        # nothing, and price what a live run would cost from those prompts.
        vocab = load_vocabulary()
        blocks = load_rung_blocks()
        assert_demonstrations_synthetic(demonstration_passages(blocks))
        assert_demonstrations_frozen(passages=demonstration_passages(blocks))
        by_id = {r["id"]: r for r in rows}
        d = os.path.join(HERE, "prompt_log_ladder")
        os.makedirs(d, exist_ok=True)
        for rung in rungs:
            if not rung_spec(rung)["annotates"]:
                continue
            system, user = annotate_prompt_for(by_id[ids[0]], rung, vocab,
                                               rows, blocks)
            p = os.path.join(d, f"rung{rung}_sample.prompt.txt")
            with open(p, "w", encoding="utf-8") as f:
                f.write(f"### SYSTEM\n{system}\n\n### USER\n{user}\n")
            print(f"  rung {rung}: {len(system) + len(user)} prompt chars "
                  f"x {len(ids)} clauses (batch "
                  f"{rung_spec(rung)['batch_size']}, eviction: "
                  f"{rung_spec(rung)['eviction']}) -> {p}")
        art = run_ladder([r for r in rungs if not rung_spec(r)["annotates"]],
                         a.model, live=False, clause_ids=ids, rows=rows,
                         out_path=a.out, controls=False)
        print(f"-> {a.out} (offline rungs only; no client was constructed)")
        print(cost_report(estimate_cost(rungs=tuple(rungs), models=("luna",
                                                                   "sol"),
                                        clause_ids=ids, rows=rows)))
        return 0

    # PRE-FLIGHT, before any client exists. Checked against the CEILING.
    pf = preflight(rungs, a.model, clause_ids=ids, rows=rows,
                   max_tokens=a.max_tokens,
                   fidelity_max_tokens=a.fidelity_max_tokens)
    print(f"  [preflight] {pf['why']}")
    if not pf["ok"] and not a.force_cost:
        raise SystemExit(
            f"REFUSING TO RUN: projected ceiling ${pf['projected_ceiling_usd']:.2f}"
            f" + ${pf['spent']:.2f} spent exceeds the ${pf['budget']:.2f} "
            f"budget. Run fewer rungs per invocation (--rungs, they resume "
            f"into one artifact), reduce n, or pass --force-cost with "
            f"explicit approval.")

    t0 = time.time()

    def progress(done, total):
        print(f"  [{done}/{total}] {time.time() - t0:.0f}s", flush=True)

    art = run_ladder(rungs, a.model, live=True, clause_ids=ids, rows=rows,
                     attempts=a.attempts, resume=a.resume, out_path=a.out,
                     max_tokens=a.max_tokens,
                     fidelity_max_tokens=a.fidelity_max_tokens,
                     progress=progress)
    print(f"-> {a.out}")
    print(table(art, strict=not a.no_strict))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
