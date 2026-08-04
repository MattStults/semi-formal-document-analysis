"""Behaviour-agnostic clause annotation: 593 clauses -> a reusable atom index.

WHY THIS TIER EXISTS
--------------------
extract_section.py encodes only `conditional` clauses, because its job is to
build deontic rules for a solver. But the panel's relevance signal is not
concentrated there. On high-consensus passages (score >= 5) the relevance-
weighted hits break down as:

    conditional 38.2%  example 39.1%  holistic 14.5%
    definitional 4.5%  meta 3.6%

so a conditional-only tool has a hard ~38% recall ceiling that no amount of
model quality can lift. This module annotates ALL 593 clauses of every kind
(conditional 188, example 183, definitional 84, meta 72, holistic 66).

THE VALUE PROPOSITION, AND THE CONSTRAINT IT IMPOSES
----------------------------------------------------
The spec is annotated ONCE; behaviour queries are then answered offline and
instantly by overlap against this index. That only works if the annotation is
behaviour-agnostic. If a behaviour description ever reached the annotation
prompt, the tool would collapse into "ask a frontier model per query" — which
is the baseline we are trying to beat — and the fast-iteration property would
be gone. So: nothing in this module, and nothing in annotate_prompt.md, may
mention a behaviour, a query, or a question. There are tests for that.

THE ATOM KIND TAXONOMY (closed, four members)
---------------------------------------------
    situation — a circumstance that may or may not obtain
                ("the user's request is ambiguous")
    act       — something someone does, visible in a transcript
                ("refuse the request", "ask a clarifying question")
    entity    — a party, role, or artifact the document names
                ("operator", "system message", "minor user")
    value     — a good being promoted or traded off
                ("honesty", "user autonomy", "safety of third parties")

Justification. A behaviour description is a sentence of the form "in SITUATION,
the model performs ACT toward/about ENTITY, at the expense of VALUE" — those
four slots are what a query and a clause have to agree on for the clause to be
relevant, so they are exactly the dimensions worth indexing. Splitting further
(topic, modality, severity, principal-vs-patient) buys resolution a cheap model
will not apply consistently, and every inconsistently applied kind is a
matching failure. Merging further (one undifferentiated "concept") loses the
kind-scoped alias guard below, which is what keeps `refuse_request` the act
distinct from `request_refused` the situation. Four is the smallest set that
keeps that distinction.

THE GRAMMAR EXTENSION (2026-08-02) — A VALIDITY FIX, NOT A PERFORMANCE FIX
---------------------------------------------------------------------------
The read-back measured `sufficient` = 0.16: 91 of 125 clauses are identifiable
from their atoms among nine same-section neighbours while a reader of those
atoms would NOT know what the clause requires. Conditionals sit at 1/25 because
"if X then Y", "Y unless X" and "never Y" all rendered as the same unordered
set {X, Y}.

⚠️ RETRACTED RATIONALE, kept so the correction is visible: this docstring
previously said the missing content concentrated in "the obligated party (23%
of missing phrases), the deontic force (15%) and the trigger (10%)". Those
figures came from a single-annotator lexical categoriser whose exact-set match
is 0.600 — and two independent blind coders of the same 268 phrases
(hole_taxonomy_coder_{a,b}.json, ARI +0.608) put the party share at 2.2-3.0%,
roughly a tenth of the figure this feature was sold on. Deontic force remains
the largest grammar-shaped share (20.9%/29.8% under one contested mapping —
see hole_rollup.py's banner), condition/exception 6-8%. The principal chain
stays because order-of-parties is required for the conflict representation
(`__model_user` != `__user_model`), NOT because it recovers much measured
loss. It doesn't.

So an atom may now carry, all OPTIONAL (see `grammar.py` for the notation and
for why `role` is a field rather than a re-use of the span grouping):

    force       a reserved name prefix        `mustnot_disclose_reasoning`
    parties     an ORDERED chain after `__`   `..__model_user`
    role        condition / exception / consequent / topic

EXPECT NO MCC MOVEMENT, and do not read a null as failure. The capacity bound
(534 equivalence classes over 589 passages, ceiling +0.972 against a +0.555
bar) says representation was never the relevance ceiling, and a supervised
readout of IDENTICAL atoms already reaches +0.591. What this buys is that a
representation of a normative document can now distinguish "must" from "must
not" — without which the conflict half of the project cannot proceed at all.

TWO THINGS HELD FIXED SO THE EXTENSION CANNOT PAY FOR ITSELF IN BUDGET
----------------------------------------------------------------------
* THE RATE CAP. <=2.78 atoms/clause and <=211 gloss characters, the shipped
  distribution, enforced on the output by `apply_rate_cap` (which is
  `ladder.enforce_rate_cap`, not a copy). Every "better atoms" idea in this
  project has degenerated into "more atoms"; a richer name is not a licence to
  emit more of them.
* THE DEMONSTRATIONS ARE FROZEN AND SYNTHETIC. The extractor is SHOWN the
  features, not merely told — but the demonstration clauses are made up, are
  not passages of either spec, and are sha256-pinned in the prompt file. The
  leak channel is SELECTION, not substring overlap.

SHARED VOCABULARY IS THE CENTRAL DESIGN PROBLEM
------------------------------------------------
If clause A coins `user_request_ambiguous` and clause B coins
`ambiguous_user_query`, overlap matching fails and the tool fails. Three
defences, in order of how much they are trusted:

  1. Carry the vocabulary forward. Every request after the first is shown the
     atoms already coined, with their glosses, and told to reuse rather than
     re-coin. (extract_section.cap_carried_atoms does the eviction.)
  2. Collapse near-duplicates mechanically. `vocab_key()` reduces a name to a
     sorted, stop-word-stripped, synonym-normalised token set; two names with
     the same key AND the same kind are the same atom, and the later one is
     rewritten to the earlier. Every rewrite is recorded in the artifact.
  3. Measure it. The artifact reports reused-vs-coined per batch and overall.
     A reuse rate that stays near zero across 43 batches means convergence
     failed and the index is worthless regardless of coverage — that number is
     the health metric to read first.

DESIGN COMMITMENTS (inherited from extract_section.py)
-------------------------------------------------------
* Nothing raises. Junk, truncation, a missing key, a dead span — each is
  recorded in a JSONL failure log and the run continues to produce a valid
  (possibly empty) artifact.
* The model never authors provenance. It selects a span id from a list of
  spans that were produced by slicing the clause's own quote, so a cited quote
  is verbatim BY CONSTRUCTION and a fabricated quote is unrepresentable rather
  than merely detectable.
* An atom citing an unresolvable span is REJECTED and COUNTED, never silently
  dropped, and coverage is computed after rejection. A silent drop would make
  coverage a lie in the direction that flatters the tool.
* Dry run is the default and makes no network call.

    .venv/bin/python annotate.py --limit 28 --live --provider luna --out smoke_atoms.json
    .venv/bin/python annotate.py --live --provider luna --out annotations.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time

import extract_section as ex
import grammar as gr

# --------------------------------------------------------------------------
# constants

CLAUSES_PATH = "modelspec_clauses.json"
PROMPT_TEMPLATE_PATH = "annotate_prompt.md"

# THE DOCUMENT-FACTS SPLIT (REPRODUCIBILITY.md, "Document-agnostic vs
# document-specific"). annotate_prompt.md is the PROCEDURE — how to annotate
# any document — and must never state one document's ontology. The facts of
# the document under annotation (its authority levels, its principal names,
# its terminology corrections) live in a per-document docfacts file whose
# blocks are spliced in at {{DOCFACTS:<key>}} markers. The default is the
# Model Spec's file, and the default composition is pinned BYTE-IDENTICAL to
# the pre-split prompt: annotation is paid, and a silent prompt change would
# make every new artifact incomparable with the shipped b8 pass.
DOCFACTS_PATH = "docfacts_model_spec.md"

_DOCFACTS_MARKER_RE = re.compile(r"\{\{DOCFACTS:([a-z_]+)\}\}")
_DOCFACTS_BLOCK_RE = re.compile(
    r"<!-- DOCFACTS:([a-z_]+) BEGIN -->\n(.*?)\n<!-- DOCFACTS:\1 END -->",
    re.DOTALL)

ATOM_KINDS = ("situation", "act", "entity", "value")
IDENT_RE = ex.IDENT_RE

# THE ENCODING BUDGET, unchanged by the grammar extension. These are the
# SHIPPED distribution (`annotations_b8.json`), and `ladder.py` declares the
# same two numbers; `test_annotate.py` pins the pair equal. Every "better
# atoms" idea in this project has degenerated into "more atoms" — a richer name
# must not become a licence to emit more of them, so the cap is applied to the
# output rather than merely asked for in the prompt.
CAP_ATOMS_PER_CLAUSE = 2.78
CAP_TEXT_CHARS_PER_CLAUSE = 211

# Output batching. The INPUT was never the problem. A reasoning model bills
# reasoning as completion tokens and spends whatever budget it is granted: a
# prior run at a 16k cap produced 71,964 chars of reasoning and ZERO content.
# The fix is a small budget and a small batch, not a bigger cap.
DEFAULT_BATCH_SIZE = 14
DEFAULT_MAX_TOKENS = 4096

# Carried vocabulary is re-sent on every request, so it has to be bounded.
# Acts and values are never evicted — they are few, and cross-section reuse of
# them is the entire point. Situations and entities are capped at the most
# recently coined, oldest evicted. Higher than extract_section's 40 because
# this prompt carries no section text and can afford the room.
MAX_CARRIED_SITUATION = 80

_HERE = os.path.dirname(os.path.abspath(__file__))


def _p(path):
    return path if os.path.isabs(path) else os.path.join(_HERE, path)


# --------------------------------------------------------------------------
# clause loading — ALL kinds, no filtering anywhere in this module

def load_clauses(path=CLAUSES_PATH, limit=None):
    """Every clause in the segmentation, in document order.

    There is deliberately no `kinds` parameter. Filtering by kind is the defect
    this module exists to remove; a caller that wants a subset can slice the
    result and own that decision explicitly.

    `marked_span` is set to None because clauses carry no anchor (that is a
    focus-area artifact); ex.candidate_spans reads it with .get and simply
    offers one fewer candidate.
    """
    with open(_p(path), encoding="utf-8") as f:
        data = json.load(f)
    raw = data["clauses"] if isinstance(data, dict) else data
    rows = [dict(r, marked_span=None) for r in raw]
    rows.sort(key=lambda r: (r.get("line") or 0, r["id"]))
    return stratified(rows, limit)


def spec_meta(path=CLAUSES_PATH):
    """{spec, source_sha256} for the provenance block, when the file carries
    them. The spec must be swappable, so this is read, never assumed."""
    try:
        with open(_p(path), encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {"spec": None, "source_sha256": None}
    if not isinstance(data, dict):
        return {"spec": None, "source_sha256": None}
    return {"spec": data.get("spec"), "source_sha256": data.get("source_sha256")}


def stratified(rows, limit=None):
    """`--limit N` for cheap smoke tests, sampled round-robin across kinds.

    Taking the first N in document order would hand a 28-clause smoke test
    almost nothing but Overview meta clauses, and the one property a smoke test
    has to exercise is that all five kinds survive the pipeline. Document order
    is restored afterwards so the prompt still reads as prose.
    """
    if not limit or limit >= len(rows):
        return list(rows)
    by_kind = {}
    for r in rows:
        by_kind.setdefault(r["kind"], []).append(r)
    out, i = [], 0
    while len(out) < limit:
        added = False
        for bucket in by_kind.values():
            if i < len(bucket):
                out.append(bucket[i])
                added = True
                if len(out) >= limit:
                    break
        if not added:
            break
        i += 1
    out.sort(key=lambda r: (r.get("line") or 0, r["id"]))
    return out


def section_of(row):
    path = row.get("section_path") or []
    return path[0] if path else ""


def section_order(rows):
    seen = []
    for r in rows:
        t = section_of(r)
        if t not in seen:
            seen.append(t)
    return seen


def batch_plan(rows, batch_size=DEFAULT_BATCH_SIZE):
    """[(section_title, batch_rows)] — one entry per request.

    Batching happens WITHIN a top-level section, so every request's clauses
    share a context, and reuse.batches does the splitting. Unlike
    extract_section.batch_plan this drops nothing: every clause of every kind
    appears in exactly one batch.
    """
    plan = []
    for title in section_order(rows):
        srows = [r for r in rows if section_of(r) == title]
        for group in ex.batches(srows, batch_size):
            if group:
                plan.append((title, group))
    return plan


# --------------------------------------------------------------------------
# vocabulary convergence

# Tokens that carry no distinguishing content in an atom name.
# Directional prepositions are DELIBERATELY absent. Dropping them, then
# comparing as an unordered set, merged agency-inverted names:
#     model_defers_to_operator == operator_defers_to_model
#     user_overrides_operator  == operator_overrides_user
#     harm_to_user             == harm_by_user
# The first two invert the chain of command -- the most load-bearing
# distinction in this document -- into a single atom, and the merge was
# reported as a success ("near-duplicate resolved to an existing atom").
# Keeping "to"/"by"/"of"/"from"/"for" as content preserves direction.
_STOP = {"the", "a", "an", "in", "on", "is", "are",
         "be", "being", "was", "that", "this", "it", "its", "and", "or",
         "with", "has", "have"}

# Surface variants that name the same thing in this document. Deliberately
# small and conservative: every entry here is a claim that two words are
# interchangeable, and a wrong claim merges two real concepts (which is worse
# than leaving a near-duplicate, because a merge is invisible downstream while
# a duplicate is visible in the vocabulary index).
_SYNONYMS = {
    "query": "request", "prompt": "request", "ask": "request",
    "question": "request", "message": "request",
    "unclear": "ambiguous", "vague": "ambiguous", "ambiguity": "ambiguous",
    "underspecified": "ambiguous",
    "assistant": "model", "ai": "model", "chatbot": "model",
    "human": "user", "person": "user",
    "reply": "response", "answer": "response", "output": "response",
    "decline": "refuse", "refusal": "refuse", "refused": "refuse",
    "harmful": "harm", "unsafe": "harm", "danger": "harm",
    "dangerous": "harm", "risky": "harm",
    "truthful": "honest", "honesty": "honest", "truthfulness": "honest",
    "instruction": "instruction", "directive": "instruction",
    "command": "instruction",
}


def _singular(tok):
    if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
        return tok[:-1]
    return tok


# Principals in this document's authority lattice. When a name mentions two or
# more of them, their ORDER carries the direction of the relation and must not
# be normalised away — see vocab_key.
_PRINCIPALS = {"user", "operator", "developer", "model", "assistant", "system",
               "root", "guideline", "platform", "human", "third_party", "party"}


def vocab_key(name):
    """A name reduced to its meaning-bearing tokens, with agency preserved.

    Word order among *modifiers* is arbitrary and is the commonest source of
    accidental near-duplicates, so `user_request_ambiguous` and
    `ambiguous_user_query` produce the same key and the second resolves to the
    first instead of splitting the concept.

    Word order among *principals* is not arbitrary — it is the direction of the
    relation. A pure token set merged `model_defers_to_operator` with
    `operator_defers_to_model` and `user_overrides_operator` with
    `operator_overrides_user`, inverting the chain of command into a single
    atom and reporting it as a successful near-duplicate resolution. So when
    two or more principals appear, their sequence is part of the key.

    Opposites (`..._present` / `..._absent`) stay distinct because the negation
    token survives normalisation. Collapsing opposites, like collapsing
    inversions, is far worse than leaving a duplicate: a duplicate is visible
    in the vocabulary index, a merge is invisible everywhere downstream.
    """
    toks = []
    for t in str(name or "").lower().split("_"):
        if not t:
            continue
        t = _SYNONYMS.get(t) or _SYNONYMS.get(_singular(t)) or _singular(t)
        if t in _STOP:
            continue
        toks.append(t)
    base = " ".join(sorted(set(toks)))
    order = [t for t in toks if t in _PRINCIPALS]
    if len(order) >= 2:
        return base + " | " + ">".join(order)
    return base


class Vocabulary:
    """The run's accumulated atom names, with kind-scoped alias resolution.

    Aliasing is scoped by kind on purpose: `refuse_request` (act) and
    `request_refused` (situation) share a token set but are a behaviour and a
    circumstance, and merging them would put an act in the situation slot of
    every query that matched it.
    """

    def __init__(self):
        self.atoms = []                  # [{name, kind, gloss}] in coin order
        self.by_name = {}
        self.canonical = {}              # (kind, vocab_key) -> canonical name
        self.aliases = []                # [{from, to, kind}]
        self.clauses = {}                # name -> [clause ids]

    def __contains__(self, name):
        return name in self.by_name

    def resolve(self, name, kind):
        """(canonical_name, was_aliased). Does not add anything."""
        if name in self.by_name:
            return name, False
        canon = self.canonical.get((kind, vocab_key(name)))
        if canon and canon != name:
            return canon, True
        return name, False

    def add(self, name, kind, gloss, clause_id=None):
        """Record a use. Returns True if this coined a NEW name."""
        new = name not in self.by_name
        if new:
            rec = {"name": name, "kind": kind, "gloss": gloss}
            self.atoms.append(rec)
            self.by_name[name] = rec
            self.canonical.setdefault((kind, vocab_key(name)), name)
        if clause_id is not None:
            seen = self.clauses.setdefault(name, [])
            if clause_id not in seen:
                seen.append(clause_id)
        return new

    def index(self):
        """name -> {kind, gloss, n_clauses, clauses} in coin order."""
        return {a["name"]: {"kind": a["kind"], "gloss": a["gloss"],
                            "n_clauses": len(self.clauses.get(a["name"], [])),
                            "clauses": list(self.clauses.get(a["name"], []))}
                for a in self.atoms}


class _CapShim:
    """Adapter so extract_section.cap_carried_atoms — the proven eviction
    policy — can be reused unchanged. It knows two kinds ("act" is never
    evicted, "context" is capped); acts and values map to the first, situations
    and entities to the second."""
    __slots__ = ("kind", "dimension", "name", "gloss")

    def __init__(self, atom):
        self.name = atom["name"]
        self.gloss = atom.get("gloss", "")
        self.kind = "act" if atom["kind"] in ("act", "value") else "context"
        self.dimension = atom["kind"]


def cap_carried(atoms, max_context=MAX_CARRIED_SITUATION):
    """(kept, n_dropped) — keep every act and value, keep the most recent
    `max_context` situations and entities."""
    shims = [_CapShim(a) for a in atoms]
    kept, dropped = ex.cap_carried_atoms(shims, max_context=max_context)
    keep = {id(s) for s in kept}
    return [a for a, s in zip(atoms, shims) if id(s) in keep], dropped


KNOWN_ATOMS_HEADER = (
    "===== ATOMS ALREADY DEFINED ({n}) =====\n"
    "Earlier requests in this run defined these, across this section and any\n"
    "sections already processed. REUSE one whenever it fits the clause in\n"
    "front of you — same spelling, exactly — and coin a new atom only when\n"
    "none of them captures the distinction. Reuse ACROSS sections is expected\n"
    "and wanted: the same idea discussed in two parts of the document is ONE\n"
    "atom, and a near-duplicate under a new name splits it in two so neither\n"
    "clause can be found through the other's name.\n\n")


def render_known_atoms(atoms):
    """The carried-forward vocabulary, grouped by kind.

    extract_section.render_known_atoms is not reused verbatim here: its header
    is written around rules, acts and conflicts, and instructing a model about
    rule modality in a prompt that emits no rules would be noise the model has
    to ignore. The eviction policy it depends on IS reused, via cap_carried().

    Glosses are always shown. Deciding "does this atom already denote what my
    clause is about?" is the reuse decision that matters and it cannot be made
    from a name alone — that is exactly the judgement that produces
    `ambiguous_user_query` when `user_request_ambiguous` was right there.
    """
    if not atoms:
        return ""
    out = [KNOWN_ATOMS_HEADER.format(n=len(atoms))]
    for kind in ATOM_KINDS:
        got = [a for a in atoms if a["kind"] == kind]
        out.append(f"{kind.upper()} atoms ({len(got)}):")
        if not got:
            out.append("  (none yet)")
        else:
            out += [f"  - {a['name']}: {a.get('gloss', '')}" for a in got]
        out.append("")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------
# prompt construction

class DocfactsError(Exception):
    """The docfacts file cannot supply the prompt's document-facts blocks.
    Never caught here: a prompt with a hole (or a literal marker) in it must
    not be sent, priced, or hashed into a run id."""


def load_docfacts(path=DOCFACTS_PATH):
    """{key: block_text} from a per-document facts file.

    A block is everything between `<!-- DOCFACTS:<key> BEGIN -->` and
    `<!-- DOCFACTS:<key> END -->`, exclusive of the marker lines' newlines,
    so the file round-trips byte-exactly into the template. Text outside the
    blocks is commentary (sources, locators, open questions) and is never
    sent.
    """
    with open(_p(path), encoding="utf-8") as f:
        text = f.read()
    blocks = dict((m.group(1), m.group(2))
                  for m in _DOCFACTS_BLOCK_RE.finditer(text))
    if not blocks:
        raise DocfactsError(
            f"{path} defines no DOCFACTS blocks; the procedure prompt's "
            "{{DOCFACTS:...}} markers cannot be filled")
    return blocks


def splice_docfacts(text, blocks, docfacts_path=DOCFACTS_PATH):
    """Replace every {{DOCFACTS:<key>}} marker with its block, loudly."""
    def sub(m):
        key = m.group(1)
        if key not in blocks:
            raise DocfactsError(
                f"the prompt template needs DOCFACTS block {key!r} and "
                f"{docfacts_path} does not define it (it defines: "
                f"{', '.join(sorted(blocks))})")
        return blocks[key]
    return _DOCFACTS_MARKER_RE.sub(sub, text)


def load_template(path=PROMPT_TEMPLATE_PATH, docfacts_path=DOCFACTS_PATH):
    """(system, user), COMPOSED: the document-agnostic procedure in `path`
    with `docfacts_path`'s document-facts blocks spliced in. Every consumer
    of the annotation prompt goes through here, so the composition — not the
    bare procedure file — is what the prompt tests bind on."""
    verify_demonstrations(path)
    blocks = load_docfacts(docfacts_path)
    system, user = ex.load_template(path)
    return (splice_docfacts(system, blocks, docfacts_path),
            splice_docfacts(user, blocks, docfacts_path))


# --------------------------------------------------------------------------
# THE FROZEN DEMONSTRATIONS
#
# The extractor has to be SHOWN the grammar's features, not merely told about
# them. Format demonstrations are not the labelled examples invariant 9 bars —
# that bars examples of behaviour->passage judgements — but there is a real
# leak path and it is closed in the design rather than policed afterwards.
#
# The channel is SELECTION, not substring overlap. A substring test never fires
# on hand-written prose; what leaks is WHICH clauses an author who has read
# panel-conditioned analysis chose to demonstrate on. So: the demonstrations
# are synthetic (a made-up ticket terminal), and the block is frozen behind a
# sha256 recorded in the prompt file, written before any output of this pass
# exists. An edit is then a visible diff of the text AND the hash.

DEMO_BEGIN = "<!-- DEMONSTRATIONS-BEGIN -->"
DEMO_END = "<!-- DEMONSTRATIONS-END -->"
DEMO_SHA_KEY = "DEMONSTRATIONS-SHA256:"


class DemonstrationLeak(Exception):
    """The demonstration block is not the frozen one. Never caught here."""


def _prompt_text(path=PROMPT_TEMPLATE_PATH):
    with open(_p(path), encoding="utf-8") as f:
        return f.read()


def demonstrations(path=PROMPT_TEMPLATE_PATH):
    """The frozen block, verbatim, without its markers."""
    text = _prompt_text(path)
    if DEMO_BEGIN not in text or DEMO_END not in text:
        raise DemonstrationLeak(
            f"{path} has no demonstration block; the extractor would be told "
            "about the grammar's features and never shown them")
    return text.split(DEMO_BEGIN, 1)[1].split(DEMO_END, 1)[0]


def demonstration_sha(path=PROMPT_TEMPLATE_PATH):
    return hashlib.sha256(
        demonstrations(path).encode("utf-8")).hexdigest()


def declared_demonstration_sha(path=PROMPT_TEMPLATE_PATH):
    for line in _prompt_text(path).splitlines():
        if DEMO_SHA_KEY in line:
            return line.split(DEMO_SHA_KEY, 1)[1].strip().split()[0]
    return None


def demonstration_prose(path=PROMPT_TEMPLATE_PATH):
    """The synthetic clause TEXTS, one string per demonstration.

    These are what a leak test compares against the specs. They are extracted
    rather than re-declared in Python so that the thing checked is the thing
    sent — a second copy would drift and the check would pass on the copy.
    """
    out, cur = [], None
    for raw in demonstrations(path).splitlines():
        line = raw.strip()
        if line.startswith("CLAUSE:"):
            if cur:
                out.append(" ".join(cur))
            cur = [line[len("CLAUSE:"):].strip()]
        elif cur is not None:
            if not line or line.startswith("["):
                out.append(" ".join(cur))
                cur = None
            else:
                cur.append(line)
    if cur:
        out.append(" ".join(cur))
    return [ex._norm_ws(s) for s in out if s]


def verify_demonstrations(path=PROMPT_TEMPLATE_PATH):
    """Raise unless the block on disk is the one that was frozen."""
    declared = declared_demonstration_sha(path)
    actual = demonstration_sha(path)
    if declared is None:
        raise DemonstrationLeak(
            f"{path} declares no {DEMO_SHA_KEY} — the demonstrations are not "
            "frozen and an edit to them would leave no trace")
    if declared != actual:
        raise DemonstrationLeak(
            f"the demonstration block in {path} is not the frozen one "
            f"(declared {declared[:12]}..., found {actual[:12]}...). If the "
            "change is intended, run `annotate.py --demo-sha` and record the "
            "new value with a reason.")
    return actual


# --------------------------------------------------------------------------
# THE RATE CAP — reused from ladder.py, not reimplemented

def apply_rate_cap(atoms, rows, max_atoms=CAP_ATOMS_PER_CLAUSE,
                   max_text=CAP_TEXT_CHARS_PER_CLAUSE):
    """Hold a pass to the shipped encoding budget. `(atoms, stats)`.

    `ladder.enforce_rate_cap` is the implementation: it is built, tested and
    mutation-verified, and a second copy here would be one more hand-maintained
    constant of the kind this repo has been bitten by twice.

    TWO FIELDS ARE HELD OUT OF THE TEXT BUDGET, and both for the same reason —
    clipping them CORRUPTS rather than shortens:

      `quote`  is verbatim provenance, looked up from the clause's own span
               table and never authored. `ladder` already excludes it.
      `role`   is a closed four-member enum. `ladder._extras` does not know
               about it yet and would price it as free text, so a run near the
               ceiling could see "condition" truncated to "cond" — which
               `grammar.role_of` then discards, silently deleting exactly the
               structure this change exists to add. It is stripped before the
               call and re-attached after, so the atom and gloss budgets bind
               exactly as they do on the shipped pass.

    ⚠️ REPORT: the clean fix is one line in `ladder.py` — add `role` to
    `BASE_FIELDS` — which this agent does not own.
    """
    from ladder import enforce_rate_cap

    ids = [r["id"] for r in rows]
    by_clause, held = {}, {}
    for i, a in enumerate(atoms):
        a = dict(a)
        a["_ix"] = i
        if gr.ROLE_FIELD in a:
            held[i] = a.pop(gr.ROLE_FIELD)
        by_clause.setdefault(a.get("clause_id"), []).append(a)

    capped, stats = enforce_rate_cap(by_clause, ids, max_atoms=max_atoms,
                                     max_text=max_text)
    out = []
    for cid in ids:
        for a in capped.get(cid) or []:
            ix = a.pop("_ix", None)
            if ix in held:
                a[gr.ROLE_FIELD] = held[ix]
            out.append(a)
    stats["role_chars"] = sum(len(v) for v in held.values())
    stats["atoms_kept"] = len(out)
    return out, stats


def preceding_context(row, all_rows):
    """The nearest earlier clause in the same section that is not itself an
    example — or None.

    An example clause read alone ("**Example**: the assistant declines") says
    nothing about which rule it illustrates, and examples are 39% of the
    relevance signal, so the annotation of an example is only as good as the
    context it is given.
    """
    if not all_rows:
        return None
    if not (row.get("in_example_block") or row.get("kind") == "example"):
        return None
    sect = section_of(row)
    best = None
    for r in all_rows:
        if r["id"] == row["id"] or section_of(r) != sect:
            continue
        if (r.get("line") or 0) > (row.get("line") or 0):
            continue
        if r.get("kind") == "example":
            continue
        if best is None or (r.get("line") or 0) > (best.get("line") or 0):
            best = r
    return best


def build_clauses_block(batch_rows, all_rows=None):
    """One entry per clause: header, optional context line, candidate spans."""
    in_batch = {r["id"] for r in batch_rows}
    entries = []
    for r in batch_rows:
        entry = [f"{r['id']} | {r.get('locator', '')} | kind={r.get('kind', '')}"]
        ctx = preceding_context(r, all_rows)
        if ctx is not None and ctx["id"] not in in_batch:
            entry.append(f"  [preceding context — {ctx['id']}, NOT to be "
                         f"annotated] {ex._norm_ws(ctx['quote'])[:400]}")
        for s in ex.candidate_spans(r):
            tag = " [whole clause]" if s["role"] == "whole clause" else ""
            entry.append(f"  {s['id']}{tag}: {s['text']}")
        entries.append("\n".join(entry))
    return "\n\n".join(entries)


def render_prompt(batch_rows, all_rows=None, known_atoms=(), batch_index=1,
                  n_batches=1, section_title=None, docfacts_path=DOCFACTS_PATH):
    """Return (system, user).

    Note what this signature does NOT take: a behaviour, a query, a question.
    Annotation is produced once and reused across every behaviour, so nothing
    behaviour-specific may enter it. There is a test asserting that.

    `docfacts_path` names the document-facts file for the document under
    annotation (see load_template); the default composes the exact shipped
    Model Spec prompt.
    """
    system, user = load_template(docfacts_path=docfacts_path)
    batch_rows = list(batch_rows)
    title = section_title or (section_of(batch_rows[0]) if batch_rows
                              else "this section")
    if n_batches > 1:
        batch_line = (
            f"This is request {batch_index} of {n_batches} in this run. These "
            f"{len(batch_rows)} clauses are from \"{title}\". The rest of the "
            f"document is covered by other requests. Annotate ONLY the clauses "
            f"listed here, and emit one entry for each of them.")
    else:
        batch_line = (f"All {len(batch_rows)} clauses in this run are listed "
                      f"here (section: \"{title}\"). Emit one entry for each.")

    user = (user
            .replace("{{KNOWN_ATOMS_BLOCK}}", render_known_atoms(known_atoms))
            .replace("{{BATCH_LINE}}", batch_line)
            .replace("{{N_CLAUSES}}", str(len(batch_rows)))
            .replace("{{CLAUSES}}", build_clauses_block(batch_rows, all_rows)))
    return system, user


# --------------------------------------------------------------------------
# verification — reject and COUNT, never silently drop

REJECTIONS = ("unknown_clause", "malformed_entry", "malformed_atom",
              "bad_name", "bad_kind", "missing_span", "unresolvable_span",
              "duplicate_in_clause",
              # added with the grammar extension
              "bad_notation", "bad_role")


def _zero_rejections():
    return {r: 0 for r in REJECTIONS}


def verify_atoms(obj, batch_rows, fail, vocab=None):
    """(atoms, stats) from one parsed response object. Never raises.

    Every atom is verified against the clause it was filed under: the name
    against the identifier regex, the kind against the closed taxonomy, the
    span id against that clause's own span table. A failure at any stage
    rejects the atom and increments a named counter — the counters exist so
    that a low coverage number can be attributed to a cause instead of being
    shrugged at.
    """
    by_id = {r["id"]: r for r in batch_rows}
    spans = ex.span_index(batch_rows)
    stats = {"atoms_seen": 0, "atoms_accepted": 0, "atoms_rejected": 0,
             "atoms_reused": 0, "atoms_coined": 0, "atoms_aliased": 0,
             "authored_quote_ignored": 0, "missing_gloss": 0,
             "atoms_with_role": 0, "atoms_with_polarity": 0,
             "atoms_with_principals": 0,
             "rejections": _zero_rejections()}
    out = []

    entries = obj.get("clauses") if isinstance(obj, dict) else None
    if not isinstance(entries, list):
        if isinstance(obj, dict) and obj:
            fail("response", "response has no \"clauses\" list",
                 {"keys": sorted(k for k in obj if isinstance(k, str))[:10]})
        return out, stats

    def reject(reason, detail, stage="atom"):
        stats["atoms_rejected"] += 1
        stats["rejections"][reason] = stats["rejections"].get(reason, 0) + 1
        fail(stage, reason, detail)

    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            stats["rejections"]["malformed_entry"] += 1
            fail("clause", "clause entry is not an object", {"index": i})
            continue
        cid = entry.get("clause_id") or entry.get("id")
        cid = cid.strip() if isinstance(cid, str) else None
        atoms = entry.get("atoms")
        atoms = atoms if isinstance(atoms, list) else []
        row = by_id.get(cid) if cid else None
        if row is None:
            # Counted per ATOM, not per entry: these atoms are lost, and the
            # rejection ledger has to add up against atoms_seen.
            for a in atoms:
                stats["atoms_seen"] += 1
                reject("unknown_clause",
                       {"clause_id": cid, "atom": (a or {}).get("name")
                        if isinstance(a, dict) else None},
                       stage="clause")
            if not atoms:
                stats["rejections"]["malformed_entry"] += 1
                fail("clause", "clause entry names no clause in this batch",
                     {"clause_id": cid, "index": i})
            continue

        table = spans.get(row["id"], {})
        seen_names = set()
        for a in atoms:
            stats["atoms_seen"] += 1
            if not isinstance(a, dict):
                reject("malformed_atom", {"clause_id": cid, "index": i})
                continue
            name = a.get("name")
            if not isinstance(name, str) or not IDENT_RE.match(name.strip()):
                reject("bad_name", {"clause_id": cid, "name": str(name)})
                continue
            name = name.strip()
            # The identifier regex accepts `a__b__c` and `must_`, which LOOK
            # like the notation and are not it. Accepting them would put an
            # undecodable string into the index, where every render prints it
            # raw and every stem-aware join keys on the wrong thing.
            if gr.parse_name(name)["error"]:
                reject("bad_notation",
                       {"clause_id": cid, "name": name,
                        "why": gr.parse_name(name)["error"]})
                continue
            kind = a.get("kind")
            if kind not in ATOM_KINDS:
                reject("bad_kind", {"clause_id": cid, "name": name,
                                    "kind": str(kind)})
                continue
            if a.get("quote") is not None:
                # the model was told to select, not to write; whatever it wrote
                # is discarded, but the attempt is worth counting
                stats["authored_quote_ignored"] += 1
            sid = a.get("span_id")
            if not isinstance(sid, str) or not sid.strip():
                reject("missing_span", {"clause_id": cid, "name": name},
                       stage="span_id")
                continue
            sid = sid.strip().lower()
            if sid not in table:
                reject("unresolvable_span",
                       {"clause_id": cid, "name": name, "span_id": sid,
                        "offered": ", ".join(sorted(table)) or "none"},
                       stage="span_id")
                continue

            gloss = a.get("gloss")
            gloss = gloss.strip() if isinstance(gloss, str) else ""
            if not gloss:
                stats["missing_gloss"] += 1

            # THE ROLE FIELD. Optional — absent is the common and correct
            # answer, and absent must stay absent rather than defaulting, or
            # every clause would assert a conditional structure nobody wrote.
            # A value outside the closed set is REJECTED rather than coerced:
            # a typo silently becoming "condition" is an assertion about the
            # document's trigger structure that no one made.
            role = a.get(gr.ROLE_FIELD)
            if role is not None and not gr.valid_role(role):
                reject("bad_role", {"clause_id": cid, "name": name,
                                    "role": str(role),
                                    "allowed": ", ".join(gr.ROLES)})
                continue
            role = gr.role_of(a)

            if vocab is not None:
                canon, aliased = vocab.resolve(name, kind)
                if aliased:
                    stats["atoms_aliased"] += 1
                    vocab.aliases.append({"from": name, "to": canon,
                                          "kind": kind,
                                          "clause_id": row["id"]})
                    fail("vocabulary", "near-duplicate atom name resolved to "
                                       "an existing atom",
                         {"from": name, "to": canon, "kind": kind})
                    name = canon
            if name in seen_names:
                reject("duplicate_in_clause", {"clause_id": cid, "name": name})
                continue
            seen_names.add(name)

            if vocab is not None:
                if vocab.add(name, kind, gloss, clause_id=row["id"]):
                    stats["atoms_coined"] += 1
                else:
                    stats["atoms_reused"] += 1

            stats["atoms_accepted"] += 1
            rec = {"name": name, "kind": kind, "gloss": gloss,
                   "span_id": sid,
                   "quote": table[sid],            # looked up, never authored
                   "clause_id": row["id"],
                   "locator": row.get("locator", "")}
            if role is not None:
                rec[gr.ROLE_FIELD] = role
                stats["atoms_with_role"] = stats.get("atoms_with_role", 0) + 1
            p = gr.parse_name(name)
            if p["polarity"]:
                stats["atoms_with_polarity"] = stats.get(
                    "atoms_with_polarity", 0) + 1
            if p["principals"]:
                stats["atoms_with_principals"] = stats.get(
                    "atoms_with_principals", 0) + 1
            out.append(rec)
    return out, stats


def annotate_batch(response, batch_rows, fail, vocab=None, batch_no=1):
    """One response -> the atoms it contributed. Never raises."""
    env = ex.as_envelope(response)
    truncated = ex.is_truncated(env)
    obj, err = ex.parse_response(env["text"])

    if truncated:
        # Truncation and malformed JSON are different defects with different
        # fixes (smaller batch vs. tighter format instruction). Never report
        # one as the other.
        usage = env.get("usage") or {}
        fail("truncated_output",
             "model hit its output cap before finishing the JSON",
             {"batch": batch_no, "finish_reason": env.get("finish_reason"),
              "completion_tokens": usage.get("completion_tokens"),
              "content_chars": len(env["text"] or ""),
              "reasoning_chars": len(env["reasoning"] or "")})
    elif err:
        fail("response", err,
             {"batch": batch_no,
              "head": (env["text"] or "")[:300]
              if isinstance(env["text"], str) else None})
    if err:
        obj = {}

    atoms, stats = verify_atoms(obj, batch_rows, fail, vocab=vocab)
    stats["batches"] = 1
    stats["truncated_batches"] = 1 if truncated else 0
    stats["parsed_batches"] = 0 if err else 1
    stats["reasoning_chars"] = len(env["reasoning"] or "")
    return {"atoms": atoms, "stats": stats, "truncated": truncated,
            "parsed": err is None, "envelope": env}


# --------------------------------------------------------------------------
# assembly

def _add_stats(into, more):
    for k, v in more.items():
        if isinstance(v, dict):
            sub = into.setdefault(k, {})
            for kk, vv in v.items():
                sub[kk] = sub.get(kk, 0) + vv
        elif isinstance(v, (int, float)):
            into[k] = into.get(k, 0) + v
        else:
            into[k] = v
    return into


def coverage(atoms, rows):
    """Clause coverage, computed POST-rejection: `atoms` here is the accepted
    set, so a clause whose only atom cited a dead span counts as uncovered."""
    have = {a["clause_id"] for a in atoms}
    ids = [r["id"] for r in rows]
    missing = [i for i in ids if i not in have]
    by_kind, covered_by_kind = {}, {}
    for r in rows:
        by_kind[r["kind"]] = by_kind.get(r["kind"], 0) + 1
        if r["id"] in have:
            covered_by_kind[r["kind"]] = covered_by_kind.get(r["kind"], 0) + 1
    return {
        "clauses_total": len(ids),
        "clauses_with_atoms": len(have & set(ids)),
        "coverage": round(len(have & set(ids)) / len(ids), 4) if ids else 0.0,
        "clause_ids_without_atoms": missing,
        "by_kind": {k: {"clauses": n,
                        "with_atoms": covered_by_kind.get(k, 0),
                        "coverage": round(covered_by_kind.get(k, 0) / n, 4)}
                    for k, n in sorted(by_kind.items())},
    }


TRUNCATION_WARNING = (
    "{n} of {total} batches hit the model's output cap before finishing their "
    "JSON — every atom in those batches is lost. Reduce --batch-size; do NOT "
    "raise --max-tokens, a reasoning model spends whatever budget it is given "
    "on reasoning and the last run at 16k produced zero content.")

VOCAB_WARNING = (
    "VOCABULARY DID NOT CONVERGE: only {rate:.0%} of atom uses reused an "
    "existing name ({coined} distinct names over {uses} uses). Overlap "
    "matching between a behaviour and a clause needs shared names; at this "
    "rate almost every clause has a private vocabulary and the index cannot "
    "match anything it was not asked about verbatim.")

VOCAB_MIN_REUSE = 0.25          # below this the index is not usable
VOCAB_MIN_USES = 40             # ... but not judgeable on a smoke test


def assemble(parts, rows, model, run_id, fail, vocab, plan=(), **prov):
    """Merge batch results into one artifact. Never raises."""
    atoms, stats = [], {}
    # A caller may pass measured batch outcomes explicitly (run() does, and so
    # do the partial-failure tests). Seed from those so the lost-batch warning
    # below sees the real counts rather than only what the surviving parts
    # happen to report — a run whose batches FAILED contributes no parts at
    # all, which is exactly the case that used to produce `warnings: []`.
    _seed = prov.get("stats")
    if isinstance(_seed, dict):
        stats.update({k: v for k, v in _seed.items()
                      if not isinstance(v, dict)})
    per_batch = []
    for i, p in enumerate(parts, start=1):
        atoms.extend(p["atoms"])
        _add_stats(stats, p["stats"])
        per_batch.append({"batch": i,
                          "clauses": p.get("n_clauses", 0),
                          "atoms": len(p["atoms"]),
                          "coined": p["stats"].get("atoms_coined", 0),
                          "reused": p["stats"].get("atoms_reused", 0),
                          "aliased": p["stats"].get("atoms_aliased", 0),
                          "rejected": p["stats"].get("atoms_rejected", 0),
                          "truncated": bool(p.get("truncated"))})

    cov = coverage(atoms, rows)
    coined = stats.get("atoms_coined", 0)
    reused = stats.get("atoms_reused", 0)
    uses = coined + reused
    vocabulary = {
        "coined": coined,
        "reused": reused,
        "aliased": stats.get("atoms_aliased", 0),
        "reuse_rate": round(reused / uses, 4) if uses else 0.0,
        "distinct_names": len(vocab.by_name),
        "atoms_per_clause": round(len(atoms) / len(rows), 2) if rows else 0.0,
        "aliases": list(vocab.aliases),
        "per_batch": per_batch,
    }

    warnings = []
    trunc = stats.get("truncated_batches", 0)
    if trunc:
        warnings.append(TRUNCATION_WARNING.format(
            n=trunc, total=stats.get("batches", 0)))

    # A RUN THAT LOST BATCHES MUST NOT LOOK COMPLETE IN ITS OWN ARTIFACT.
    # Truncation and vocabulary were warned about; CALL and PARSE failures were
    # not. A simulated 593-clause run losing 9 of 47 batches to HTTP 500s wrote
    # `warnings: []` with coverage 0.0. The stdout summary showed it, but the
    # artifact — the thing a later reader actually consumes — looked clean.
    # That matters most on a paid comparison run: an artifact missing a fifth
    # of its batches reads as "the expensive model is barely better", which is
    # the conclusion such a run exists to draw.
    n_batches = stats.get("batches", 0) or 0
    parsed = stats.get("parsed_batches", n_batches)
    failures = stats.get("call_failures", 0) or 0
    if failures:
        warnings.append(
            f"!! {failures} of {n_batches} batches FAILED their model call — "
            "every clause in them is unannotated. Coverage below is computed "
            "over what survived; do NOT compare this artifact against one with "
            "a different failure count.")
    if n_batches and parsed < n_batches:
        warnings.append(
            f"!! only {parsed} of {n_batches} batches parsed — "
            f"{n_batches - parsed} produced no usable atoms.")
    if uses >= VOCAB_MIN_USES and vocabulary["reuse_rate"] < VOCAB_MIN_REUSE:
        w = VOCAB_WARNING.format(rate=vocabulary["reuse_rate"],
                                 coined=coined, uses=uses)
        warnings.append(w)
        fail("vocabulary", w, {"reuse_rate": vocabulary["reuse_rate"]})

    by_clause = {}
    for a in atoms:
        by_clause.setdefault(a["clause_id"], []).append(a)

    counts = {k: v for k, v in stats.items() if not isinstance(v, dict)}
    counts["atoms_total"] = len(atoms)
    counts["failures"] = fail.count()
    counts.setdefault("call_failures", 0)

    provenance = {
        "model": model,
        "run_id": run_id,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_batches": len(parts),
        "plan": [{"request": i, "section": t, "clauses": len(g)}
                 for i, (t, g) in enumerate(plan, start=1)],
        "counts": counts,
        "rejections": stats.get("rejections", _zero_rejections()),
        "coverage": cov,
        "vocabulary": vocabulary,
    }
    provenance.update(prov)
    return {"warnings": warnings,
            "provenance": provenance,
            "atoms": atoms,
            "by_clause": by_clause,
            "vocabulary": vocab.index()}


# --------------------------------------------------------------------------
# the run

def make_annotate_client(cfg, live=False, log_dir="prompt_log"):
    """providers.make_client, with dry run as the default.

    The live path is providers.LiveClient rather than
    extract_section.InstrumentedClient: LiveClient.complete_envelope appends
    every call to usage.jsonl by default, and this session runs under a hard
    budget where a missing row is an invisible undercount. InstrumentedClient
    defines a _log_usage helper but never calls it from complete_envelope, so
    using it here would make this tier's spend invisible.
    """
    from providers import make_client
    return make_client(cfg, live=live, log_dir=log_dir)


def provider_config(name, path="providers.json"):
    from providers import ProviderConfig
    configs = ProviderConfig.load_all(_p(path))
    by_name = {c.name: c for c in configs}
    if name not in by_name:
        raise SystemExit(f"unknown provider {name!r}; known: "
                         f"{', '.join(sorted(by_name))}")
    return by_name[name]


def run(client, rows, model, batch_size=DEFAULT_BATCH_SIZE, out_dir=".",
        out=None, log_path=None, seed=0, return_path=False,
        max_tokens=DEFAULT_MAX_TOKENS, provider=None, clauses_path=CLAUSES_PATH,
        rate_cap=True, docfacts_path=DOCFACTS_PATH):
    """One annotation pass over `rows`, in sequential output batches.

    The vocabulary accumulator spans the WHOLE run: an atom coined in the first
    section is offered to every later one. A vocabulary that restarted per
    section would guarantee the near-duplicate failure at document scale.
    """
    rows = list(rows)
    plan = batch_plan(rows, batch_size) or [("", rows)]
    system, first_user = render_prompt(plan[0][1], rows, (), 1, len(plan),
                                       section_title=plan[0][0],
                                       docfacts_path=docfacts_path)
    run_id = ex.make_run_id(model, seed, first_user)
    log_path = log_path or os.path.join(out_dir, "annotate_failures.jsonl")
    fail = ex.FailureLog(log_path, run_id=run_id, model=model)

    vocab = Vocabulary()
    parts, any_response, dropped_ctx = [], False, 0
    for i, (title, group) in enumerate(plan, start=1):
        carried, dropped = cap_carried(vocab.atoms)
        dropped_ctx = max(dropped_ctx, dropped)
        system, user = render_prompt(group, rows, carried, i, len(plan),
                                     section_title=title,
                                     docfacts_path=docfacts_path)
        try:
            resp = ex.call_client(client, system, user)
        except Exception as e:
            fail("call", f"provider call failed: {type(e).__name__}: {e}",
                 {"batch": i, "section": title})
            resp = None
        env = ex.as_envelope(resp)
        if env["text"] is not None:
            any_response = True
        ex.log_reasoning(env, out_dir, run_id, i)
        part = annotate_batch(resp, group, fail, vocab=vocab, batch_no=i)
        part["n_clauses"] = len(group)
        part["section"] = title
        parts.append(part)

    # THE RATE CAP, applied to the whole run rather than per batch: the budget
    # is a property of the SAMPLE, not of the survivors, so a run that lost
    # batches is not handed a smaller allowance for the ones that landed.
    cap_stats = {"applied": False}
    if rate_cap:
        flat = [a for p in parts for a in p["atoms"]]
        kept, cap_stats = apply_rate_cap(flat, rows)
        cap_stats["applied"] = True
        # (clause_id, name) is unique: `duplicate_in_clause` already rejects a
        # repeat within one clause, so this is a total re-keying, not a lossy
        # match — and it carries the TRUNCATED gloss through, not the original.
        by_key = {(a["clause_id"], a["name"]): a for a in kept}
        for p in parts:
            p["atoms"] = [by_key[(a["clause_id"], a["name"])]
                          for a in p["atoms"]
                          if (a["clause_id"], a["name"]) in by_key]

    art = assemble(parts, rows, model, run_id, fail, vocab, plan=plan,
                   provider=provider, batch_size=batch_size,
                   max_tokens=max_tokens,
                   seed=seed,
                   docfacts=docfacts_path,
                   carried_atoms_evicted=dropped_ctx,
                   rate_cap=cap_stats,
                   **spec_meta(clauses_path))
    art["provenance"]["counts"]["call_failures"] = fail.count("call")
    art["provenance"]["dry_run"] = not any_response and fail.count("call") == 0

    os.makedirs(out_dir, exist_ok=True)
    if out is None:
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", str(model))
        out = os.path.join(out_dir, f"annotations_{safe}_{run_id}.json")
    try:
        with open(out, "w", encoding="utf-8") as f:
            json.dump(art, f, indent=1, ensure_ascii=False)
    except OSError as e:
        fail("write", f"could not write artifact: {e}", {"path": out})
        out = None
    return (art, out) if return_path else art


# --------------------------------------------------------------------------
# COST — from MEASURED prompts, priced through spend.py
#
# This project has mispriced the same operation THREE times, always toward
# spending: ONTOLOGY_REFINEMENT.md priced the open-vocabulary pass while
# eviction was what made it cheap; LADDER_PLAN.md repeated it; and the ladder's
# own first estimate was out by 10-45x on Sol. So nothing here is arithmetic on
# a remembered figure. The prompts are BUILT — every batch, with the carried
# vocabulary the run would actually send — and their characters counted.

def estimate_cost(clauses_path=CLAUSES_PATH, limit=None,
                  batch_size=DEFAULT_BATCH_SIZE, provider="luna",
                  providers_path="providers.json",
                  max_tokens=DEFAULT_MAX_TOKENS, rows=None,
                  docfacts_path=DOCFACTS_PATH):
    """MEASURED token counts and a price for one annotation pass.

    Two conversions are not measurable offline and each is taken from this
    repo's own logged calls rather than a guess:

      chars -> input tokens  `ladder.calibrate_chars_per_token()`, a quantile
                             match of reconstructed prompts against
                             usage.jsonl's `prompt_tokens`.
      output tokens          `ladder.measured_output_profile()`, the completion
                             (reasoning included — it is billed as completion
                             and is ~65% of it on this model) actually spent by
                             the shipped b8 pass.

    The carried vocabulary is the single biggest term and cannot be known
    before the run, so it is taken at STEADY STATE: the shipped 361-atom
    vocabulary, capped by the same `cap_carried` eviction the run applies. That
    over-states the first batches and is right for the rest, which is the
    conservative direction.

    `usd_ceiling` assumes every call runs to `--max-tokens`. The b8 completion
    distribution is p90 3202 / max 4060 against a 4096 cap, so that is not a
    tail event and it is the number to check a budget against.
    """
    import ladder as L
    import spend

    rows = list(rows) if rows is not None else load_clauses(clauses_path,
                                                            limit=limit)
    plan = batch_plan(rows, batch_size) or [("", rows)]

    try:
        carried, _ = cap_carried([
            {"name": n, "kind": v.get("kind"), "gloss": v.get("gloss") or ""}
            for n, v in (_shipped_vocabulary() or {}).items()])
    except (OSError, ValueError, KeyError):
        carried = []

    chars = 0
    for i, (title, group) in enumerate(plan, start=1):
        system, user = render_prompt(group, rows, carried if i > 1 else (),
                                     i, len(plan), section_title=title,
                                     docfacts_path=docfacts_path)
        chars += len(system) + len(user)

    cal = L.calibrate_chars_per_token()
    cpt = cal["chars_per_token"]
    outp = L.measured_output_profile()
    per_clause = outp["completion_per_batch"] / max(outp["clauses_per_batch"],
                                                    1.0)
    in_tokens = chars / cpt
    # Two honest bounds, because reasoning does not scale linearly with batch
    # size: per-BATCH holds if reasoning is fixed overhead, per-CLAUSE holds if
    # it scales. The truth is between them and both are printed.
    # ... and both are clamped at `max_tokens`, which the provider enforces:
    # extrapolating per-clause past the cap prices output the model cannot
    # emit, and would put the "expected" figure ABOVE the ceiling.
    out_low = len(plan) * min(outp["completion_per_batch"],
                              per_clause * batch_size, max_tokens)
    out_high = len(plan) * min(max(outp["completion_per_batch"],
                                   per_clause * batch_size), max_tokens)

    px = spend.prices(_p(providers_path))
    cfg_model = _provider_model(provider, providers_path)

    def price(out_tok):
        row = {"model": cfg_model, "prompt_tokens": int(in_tokens),
               "completion_tokens": int(out_tok)}
        c = spend.cost_of(row, px)
        if c is None:
            raise SystemExit(f"no price for {provider!r} in {providers_path}")
        return c

    return {
        "provider": provider, "model": cfg_model,
        "clauses": len(rows), "calls": len(plan), "batch_size": batch_size,
        "prompt_chars": chars,
        "chars_per_token": cpt,
        "chars_per_token_method": cal.get("method"),
        "output_profile": outp.get("method"),
        "in_tokens": in_tokens,
        "out_tokens_low": out_low, "out_tokens_high": out_high,
        "out_tokens_ceiling": len(plan) * max_tokens,
        "usd_low": price(out_low),
        "usd": price(out_high),
        "usd_ceiling": price(len(plan) * max_tokens),
        "spent_so_far": spend.total()["total"],
        "budget": spend.BUDGET,
    }


def _shipped_vocabulary(path="annotations_b8.json"):
    with open(_p(path), encoding="utf-8") as f:
        return (json.load(f) or {}).get("vocabulary") or {}


def _provider_model(name, path="providers.json"):
    for p in json.load(open(_p(path))):
        if p.get("name") == name or p.get("model") == name:
            return p.get("model")
    raise SystemExit(f"unknown provider {name!r}")


def print_cost(est, live=False):
    print(f"DRY RUN COST — {est['clauses']} clauses, {est['calls']} call(s) of "
          f"{est['batch_size']} on {est['provider']} ({est['model']})")
    print(f"  prompt chars MEASURED {est['prompt_chars']:,} "
          f"-> {est['in_tokens']:,.0f} input tokens "
          f"at {est['chars_per_token']:.2f} chars/token "
          f"({est['chars_per_token_method']})")
    print(f"  output tokens {est['out_tokens_low']:,.0f}-"
          f"{est['out_tokens_high']:,.0f} from {est['output_profile']}; "
          f"ceiling {est['out_tokens_ceiling']:,.0f} if every call runs to "
          f"--max-tokens")
    print(f"  $ {est['usd_low']:.3f} (low) / {est['usd']:.3f} (expected) / "
          f"{est['usd_ceiling']:.3f} (CEILING — check the budget against this)")
    print(f"  spent so far ${est['spent_so_far']:.3f} of "
          f"${est['budget']:.2f}; after the ceiling "
          f"${est['spent_so_far'] + est['usd_ceiling']:.3f}")
    over = est["spent_so_far"] + est["usd_ceiling"] > est["budget"]
    if over and not live:
        #: a dry run spends nothing, so it must still cost a run you have not
        #: been approved for. Warn, do not refuse.
        print("  !! THE CEILING WOULD EXCEED THE BUDGET.")
    elif over:
        #: ⚠️ THIS USED TO PRINT AND FALL THROUGH, and the next statements
        #: spent the money. On luna the ceiling is arithmetically bounded so it
        #: never bit; the same command with `--provider sol` prices at $13.79
        #: against an $8.50 hard cap and would have run anyway. A guard that
        #: reports and proceeds is not a guard. `ladder.main` raises on the
        #: identical condition — this was the divergence.
        raise SystemExit(
            f"REFUSING TO SPEND: ceiling ${est['usd_ceiling']:.3f} on top of "
            f"${est['spent_so_far']:.3f} already spent would exceed the "
            f"${est['budget']:.2f} BUDGET. Lower --batch-size, use --limit, "
            f"pick a cheaper --provider, or raise spend.BUDGET deliberately "
            f"(it is a decision, not a workaround).")


def _summarize(art, path):
    p = art["provenance"]
    c, cov, v = p["counts"], p["coverage"], p["vocabulary"]
    print(f"[{p['model']} / {p['run_id']}] "
          f"atoms={c.get('atoms_accepted', 0)} accepted, "
          f"{c.get('atoms_rejected', 0)} rejected of {c.get('atoms_seen', 0)} "
          f"seen; coverage={cov['coverage']:.2f} "
          f"({cov['clauses_with_atoms']}/{cov['clauses_total']} clauses) "
          + (f"-> {path}" if path else "-> NOT WRITTEN"))
    print("    coverage by kind: " + "  ".join(
        f"{k} {d['with_atoms']}/{d['clauses']}" for k, d in
        sorted(cov["by_kind"].items())))
    print(f"    vocabulary: {v['distinct_names']} distinct names, "
          f"{v['reused']} reuses / {v['coined']} coinages "
          f"(reuse rate {v['reuse_rate']:.2f}), {v['aliased']} aliased, "
          f"{v['atoms_per_clause']} atoms/clause")
    rej = {k: n for k, n in p["rejections"].items() if n}
    print(f"    rejections: {rej or 'none'}")
    print(f"    batches: {c.get('parsed_batches', 0)}/{c.get('batches', 0)} "
          f"parsed, {c.get('truncated_batches', 0)} truncated, "
          f"{c.get('call_failures', 0)} call failures; "
          f"{c.get('reasoning_chars', 0)} chars of reasoning captured")
    for w in art.get("warnings", []):
        print("    !! " + w)


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--clauses", default=CLAUSES_PATH,
                    help="clause segmentation JSON (the spec is swappable; "
                         "nothing here is OpenAI-specific)")
    ap.add_argument("--docfacts", default=DOCFACTS_PATH,
                    help="per-document facts file spliced into the "
                         "document-agnostic prompt at its {{DOCFACTS:...}} "
                         f"markers (default {DOCFACTS_PATH}). MUST match the "
                         "document in --clauses: the Model Spec facts are "
                         "false teaching on any other document.")
    ap.add_argument("--provider", default="luna",
                    help="provider name from providers.json (default luna)")
    ap.add_argument("--providers", default="providers.json")
    ap.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE,
                    help=f"clauses annotated per request (default "
                         f"{DEFAULT_BATCH_SIZE}); the OUTPUT is what has to fit")
    ap.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS,
                    help=f"output cap per request (default {DEFAULT_MAX_TOKENS}). "
                         "Reasoning is billed as completion tokens and expands "
                         "to fill the budget: a bigger cap is actively harmful.")
    ap.add_argument("--limit", type=int, default=None,
                    help="annotate only N clauses, sampled across all five "
                         "kinds, for a cheap smoke test")
    ap.add_argument("--out", default=None, help="artifact path")
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--log", default=None, help="failure JSONL path")
    ap.add_argument("--prompt-log", default="prompt_log")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true", default=True,
                    help="record prompts, make no network call (the default)")
    ap.add_argument("--live", action="store_true",
                    help="make real API calls; without this nothing leaves the "
                         "machine")
    ap.add_argument("--print-prompt", action="store_true",
                    help="print the first request's prompt and exit")
    ap.add_argument("--demo-sha", action="store_true",
                    help="print the sha256 of the demonstration block and exit "
                         "(what DEMONSTRATIONS-SHA256 in the prompt must say)")
    ap.add_argument("--no-rate-cap", action="store_true",
                    help="do NOT hold the output to the shipped encoding "
                         "budget. Recorded in the artifact; a pass run this "
                         "way is not comparable with one that was not.")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.demo_sha:
        print(demonstration_sha())
        return 0
    rows = load_clauses(args.clauses, limit=args.limit)
    if not rows:
        print(f"no clauses in {args.clauses}")
        return 1
    plan = batch_plan(rows, args.batch_size)
    kinds = {}
    for r in rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print(f"{len(rows)} clauses ({', '.join(f'{k} {n}' for k, n in sorted(kinds.items()))}) "
          f"over {len(section_order(rows))} section(s); {len(plan)} request(s)")

    if args.print_prompt:
        system, user = render_prompt(plan[0][1], rows, (), 1, len(plan),
                                     section_title=plan[0][0],
                                     docfacts_path=args.docfacts)
        print("### SYSTEM\n" + system + "\n\n### USER\n" + user)
        return 0

    # ALWAYS priced, live or not: the estimate is what a reviewer approves, and
    # printing it only on the dry-run path means the live path never shows it.
    try:
        print_cost(estimate_cost(clauses_path=args.clauses, rows=rows,
                                 batch_size=args.batch_size,
                                 provider=args.provider,
                                 providers_path=args.providers,
                                 max_tokens=args.max_tokens,
                                 docfacts_path=args.docfacts),
                   live=args.live)
    except (OSError, ValueError, KeyError) as e:
        #: ⚠️ A PRICING FAILURE MUST NOT BECOME PERMISSION TO SPEND. This
        #: except used to print and fall through on the live path too, so a
        #: malformed price table or a missing usage log meant the run went
        #: ahead UNPRICED against a hard cap. Unknown cost is not low cost.
        msg = f"could not price this run: {type(e).__name__}: {e}"
        if args.live:
            import spend as _sp
            raise SystemExit(
                f"REFUSING TO SPEND: {msg}. A run that cannot be priced "
                f"cannot be checked against the ${_sp.BUDGET:.2f} budget. "
                f"Fix the pricing path or use --dry-run.")
        print(f"  !! {msg}")

    cfg = provider_config(args.provider, args.providers)
    cfg.max_tokens = args.max_tokens
    client = make_annotate_client(cfg, live=args.live,
                                  log_dir=_p(args.prompt_log))
    if not args.live:
        print("DRY RUN (no network). Pass --live to make real calls.")
    art, path = run(client, rows, model=cfg.model, provider=cfg.name,
                    batch_size=args.batch_size, out_dir=args.out_dir,
                    out=args.out, log_path=args.log, seed=args.seed,
                    max_tokens=args.max_tokens, clauses_path=args.clauses,
                    rate_cap=not args.no_rate_cap,
                    docfacts_path=args.docfacts,
                    return_path=True)
    _summarize(art, path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
