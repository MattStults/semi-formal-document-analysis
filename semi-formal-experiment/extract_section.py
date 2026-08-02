"""Agent B: one-pass extraction of a Model Spec section into `extraction.json`.

Target: "The chain of command" — 62 focus areas, 42 of them conditional
(the encodable set), 13,924 characters of whole-clause text. It fits in one
prompt, so this is a single call per run, not a per-clause loop.

Contract (blog draft 2026-07-31-spec-ontology-tdd.md §3):

  {"section": ..., "model": ..., "run_id": ...,
   "atoms":   [<dsl.Atom shape>],
   "rules":   [<dsl.Rule shape, tier always 1>],
   "incompat":[{"acts": [a, b], "license": ..., "source": ...}],
   "exclusions":[{"atoms": [...], "kind": "at_most_one"|"excludes",
                  "license": ..., "source": ...}],
   "unencoded":[{"focus_id": ..., "reason": ...}]}

`incompat` constrains acts; `exclusions` constrains context atoms that cannot
co-occur. Both are mandatory keys. Omitting exclusions would leave every
context atom independently free, so the solver could satisfy a conflict in a
situation that cannot exist.

Design commitments:

* Nothing raises. A junk response, a missing key, a bad span, an unparseable
  field — each is recorded in a JSONL failure log and the run continues to
  produce a valid (possibly empty) artifact. In particular this module does
  NOT reproduce translate.py's pattern of referencing loop-local names after
  a loop that may never have bound them.
* The model is never trusted for provenance. `locator` and `quote` on a rule
  are overwritten from the inventory row; an atom quote span survives only if
  it resolves to a real provision and is a verbatim substring of that
  provision's text. Unverified atoms are kept, emptied, marked draft, and
  COUNTED — never dropped.
* `tier` is forced to 1. The section is uniformly root authority.
* Dry run is the default and makes no network call.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request

import dsl
from dsl import Atom, Axiom, Rule, Vocabulary

# --------------------------------------------------------------------------
# constants

SECTION_TITLE = "The chain of command"     # the original single-section target
ALL_SECTIONS = "all"
DEFAULT_SECTION = ALL_SECTIONS
FOCUS_AREAS_PATH = "modelspec_focus_areas.json"
PROMPT_TEMPLATE_PATH = "extract_section_prompt.md"
SPEC_TAG = "model_spec"

ENCODABLE_KIND = "conditional"
IDENT_RE = re.compile(r"^[a-z][a-z0-9_]*$")
ID_PREFIX = "fa_"
TIER = 1                      # uniformly root authority; no lattice in this spike

# Output batching. The section fits in one context as INPUT — that was never
# the problem. The blocker was OUTPUT: a reasoning model spent 8,000
# completion tokens (31,767 chars of reasoning, 339 of content) and truncated
# the JSON mid-object. 42 provisions / 14 = 3 requests.
DEFAULT_BATCH_SIZE = 14
DEFAULT_MAX_TOKENS = 16384

_HERE = os.path.dirname(os.path.abspath(__file__))


def _p(path):
    """Resolve a repo-relative path against this module's directory."""
    return path if os.path.isabs(path) else os.path.join(_HERE, path)


# --------------------------------------------------------------------------
# inventory access — THE ONLY PLACE that reads the focus-area file.
# Agent A owns inventory.py; swapping to inventory.load_section() is a
# one-line change inside this function.

ROW_KEYS = ("id", "source_id", "locator", "quote", "marked_span", "kind",
            "modality", "has_defeater")


def section_key(section):
    """Artifact `section` field. "The chain of command" -> "chain_of_command",
    matching contract §3; "all" stays "all"."""
    if section == ALL_SECTIONS:
        return ALL_SECTIONS
    slug = re.sub(r"[^a-z0-9]+", "_", (section or "").lower()).strip("_")
    return slug[4:] if slug.startswith("the_") else slug


def section_titles(path=FOCUS_AREAS_PATH):
    """Top-level section titles in document order."""
    with open(_p(path), encoding="utf-8") as f:
        raw = json.load(f)
    seen = []
    for r in sorted(raw, key=lambda x: x.get("line") or 0):
        t = r.get("top_level_section")
        if t and t not in seen:
            seen.append(t)
    return seen


def load_section(section=DEFAULT_SECTION, path=FOCUS_AREAS_PATH):
    """Return rows for one top-level section, or for the whole document when
    `section` is "all", as
    {id, source_id, locator, quote, marked_span, kind, modality, has_defeater,
     section, line}.

    `quote` is the whole clause (the instrument work found the truncated
    marked span is the wrong unit to show); `marked_span` is carried alongside.

    inventory.py (Agent A) is the owner of this mapping — in particular of the
    locator format, which must agree with the ASP emitter's. Use it when it is
    importable and produces the agreed shape; fall back to reading the focus
    areas directly so this module never blocks on A.
    """
    titles = section_titles(path) if section == ALL_SECTIONS else [section]
    rows = []
    for t in titles:
        got = _load_section_via_inventory(t)
        if got is None:
            got = _load_section_direct(t, path)
        rows.extend(got)
    rows.sort(key=lambda x: (x["line"], x["id"]))
    return rows


def _load_section_via_inventory(section_title):
    try:
        import inventory
        rows = inventory.load_section(section_title)
    except Exception:
        return None
    if not rows or not all(all(k in r for k in ROW_KEYS) for r in rows):
        return None
    out = []
    for r in rows:
        r = dict(r)
        if r.get("line") is None:
            m = re.search(r" > L(\d+)\b", r.get("locator") or "")
            r["line"] = int(m.group(1)) if m else 0
        # locator is "<spec> > <top level> > ... > L<line>"
        r.setdefault("section", (r.get("locator") or "").split(" > ")[1]
                     if " > " in (r.get("locator") or "") else section_title)
        out.append(r)
    out.sort(key=lambda x: (x["line"], x["id"]))
    return out


def _load_section_direct(section_title, path):
    """Fallback reader. `section_title` is always a concrete title here."""
    with open(_p(path), encoding="utf-8") as f:
        raw = json.load(f)
    rows = []
    for r in raw:
        if r.get("top_level_section") != section_title:
            continue
        rows.append({
            "id": fa_id(r["focus_id"]),
            "source_id": r["focus_id"],
            "locator": synth_locator(r),
            "quote": r["text"],
            "marked_span": r.get("marked_span", ""),
            "kind": r.get("kind", ""),
            "modality": list(r.get("modality") or []),
            "has_defeater": bool(r.get("has_defeater")),
            "line": r.get("line"),
            "section": r["top_level_section"],
        })
    rows.sort(key=lambda x: (x["line"] if x["line"] is not None else 0, x["id"]))
    return rows


def fa_id(focus_id):
    """13 of the 62 focus ids are digit-initial and illegal as bare ASP
    constants. Prefix unconditionally so the mapping stays total and 1:1."""
    return ID_PREFIX + str(focus_id).strip().lower()


def synth_locator(row):
    """Stable human-readable locator from section_path + line."""
    path = " > ".join(row.get("section_path") or [])
    return f"{SPEC_TAG} > {path} > L{row.get('line')}"


def encodable(rows):
    return [r for r in rows if r["kind"] == ENCODABLE_KIND]


# --------------------------------------------------------------------------
# prompt construction

def load_template(path=PROMPT_TEMPLATE_PATH):
    with open(_p(path), encoding="utf-8") as f:
        text = f.read()
    sys_marker, usr_marker = "=== SYSTEM ===", "=== USER ==="
    system = text.split(sys_marker, 1)[1].split(usr_marker, 1)[0].strip()
    user = text.split(usr_marker, 1)[1].strip()
    return system, user


def build_section_text(rows, omit=()):
    """Whole-clause section text in document order, grouped under subsection
    headings. 6 clauses carry more than one focus marker (17 duplicate rows);
    the clause is printed once, so the prose reads as prose.

    `omit` names provisions whose clause is reproduced in full further down the
    prompt (this request's own batch). They are replaced by a marker so the
    reading order is preserved without paying for the text twice.
    """
    omit_ids = {r["id"] for r in omit}
    # A clause carrying several markers is only elided when EVERY provision on
    # it is in this batch; otherwise a provision that is not being encoded here
    # would lose its text entirely.
    by_clause = {}
    for r in rows:
        by_clause.setdefault((r["line"], r["quote"]), []).append(r["id"])
    elide = {k for k, ids in by_clause.items() if set(ids) <= omit_ids}

    out, current, seen = [], None, set()
    for r in rows:
        head = r["locator"].split(" > L")[0]
        if head != current:
            current = head
            out.append(f"\n## {head}")
        key = (r["line"], r["quote"])
        if key in seen:
            continue
        seen.add(key)
        if key in elide:
            out.append(f"[{', '.join(by_clause[key])} — quoted in full below]")
        else:
            out.append(r["quote"])
    return "\n".join(out).strip()


MIN_SPAN_CHARS = 25
MAX_SPANS = 8
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")
_FRAG_SPLIT = re.compile(r"[,;:]\s+|\s+—\s+|\s+--\s+")


def candidate_spans(row, max_spans=MAX_SPANS, min_len=MIN_SPAN_CHARS):
    """Enumerate the spans an atom may cite for this provision, as
    [{"id": "s1", "text": ...}].

    Every candidate is produced by *slicing the provision's own quote*, so it
    is a verbatim substring by construction — which is the whole point: the
    model selects an id and never authors quote text, so a fabricated quote
    has no way to enter the artifact.

    Candidates, in priority order: the whole clause, the anchor (marked_span),
    each sentence, each comma/semicolon/dash-delimited fragment at least
    `min_len` long. Deduplicated on normalized whitespace, capped at
    `max_spans`.
    """
    quote = row.get("quote") or ""
    ordered = [(quote.strip(), "whole clause"),
               ((row.get("marked_span") or "").strip(), "anchor")]

    parts = [p.strip() for p in _SENT_SPLIT.split(quote)]
    if len(parts) > 1:
        ordered += [(p, "sentence") for p in parts]
    for sent in parts:
        frags = [f.strip(" \t\n,;:—-") for f in _FRAG_SPLIT.split(sent)]
        if len(frags) > 1:
            ordered += [(f, "fragment") for f in frags if len(f) >= min_len]

    out, seen = [], set()
    for text, role in ordered:
        if not text or len(out) >= max_spans:
            continue
        key = _norm_ws(text).lower()
        if key in seen:
            continue
        # the guarantee this whole design rests on
        if _norm_ws(text) not in _norm_ws(quote):
            continue
        seen.add(key)
        out.append({"id": f"s{len(out) + 1}", "text": text, "role": role})
    return out


def span_index(rows):
    """{provision id: {span id: verbatim text}} — the resolution table."""
    return {r["id"]: {s["id"]: s["text"] for s in candidate_spans(r)}
            for r in rows}


def build_provisions_block(rows):
    """One entry per provision. The whole clause is shown (the instrument work
    found the truncated span is the wrong unit to reason from), but 20 of the
    42 conditional provisions share a clause with another marker, so the
    anchor span is shown too — it is the only thing distinguishing them."""
    lines = []
    for r in rows:
        mods = ", ".join(r["modality"]) or "-"
        d = "defeasible" if r["has_defeater"] else "-"
        entry = f"{r['id']} | {r['locator']} | {mods} | {d}"
        for s in candidate_spans(r):
            tag = f" [{s['role']}]" if s["role"] in ("whole clause", "anchor") else ""
            entry += f"\n  {s['id']}{tag}: {s['text']}"
        lines.append(entry)
    return "\n\n".join(lines)


AXIOM_ASK = (
    "This is the only request that collects axioms, and they cover the WHOLE\n"
    "atom set — including atoms defined in earlier requests, not only the ones\n"
    "you added just now.\n\n"
    "Go through the declared ACT atoms pairwise and decide, for each pair that\n"
    "could plausibly clash, whether the two acts can both be performed in one\n"
    "situation. Emit an \"incompat\" for each pair that cannot, with a license;\n"
    "and an \"incompat_declined\" entry {\"acts\": [a, b], \"reason\": str} for\n"
    "each pair you considered and rejected. Then do the same for context atoms\n"
    "via \"exclusions\".\n\n"
    "Returning empty lists is allowed only if it is a conclusion you reached\n"
    "and recorded in \"incompat_declined\" — not if you skipped the step.")

AXIOM_DEFER = (
    "Do NOT emit axioms in this response. Send \"incompat\": [] and\n"
    "\"exclusions\": []. They are collected in the final request, once the\n"
    "full atom set exists, because an axiom needs atoms it cannot see yet.")

KNOWN_ATOMS_HEADER = (
    "===== ATOMS ALREADY DEFINED ({n}) =====\n"
    "Earlier requests in this run defined these, across this section and any\n"
    "sections already processed. Reuse one whenever it fits; define a new atom\n"
    "only when none of them captures the distinction. You may reuse an atom\n"
    "without re-listing it. Reuse ACROSS sections is expected and wanted: the\n"
    "same behaviour discussed in two parts of the document is one act.\n\n"
    "CONTEXT atoms — legal in a rule's \"conditions\" and in defeaters:\n"
    "{context}\n\n"
    "### ACT atoms already declared ({n_acts}) — REUSE THESE ###\n"
    "{acts}\n\n"
    "Every rule you write should name one of the acts above unless none of\n"
    "them denotes the behaviour your provision is about. Rules that share an\n"
    "act are the only rules that can ever conflict, so reusing an act is how\n"
    "this encoding acquires any value at all; minting a fresh act per\n"
    "provision guarantees zero conflicts and a wasted run. Reach for a new act\n"
    "only after checking every act above and finding none that fits.\n\n"
    "A rule's \"act\" must name an ACT atom: one of the act atoms listed here,\n"
    "or a new kind=\"act\" atom you declare in this response. Naming a context\n"
    "atom as an act is rejected — the two are different types and the rule is\n"
    "discarded, losing the provision.\n\n")


def batches(items, size):
    """Split provisions into output-sized batches. The INPUT is never split —
    every request carries the whole section — but a reasoning model spends its
    completion budget per rule, and that is what has to be bounded."""
    if size is None or size <= 0 or size >= len(items):
        return [list(items)]
    return [list(items[i:i + size]) for i in range(0, len(items), size)]


def section_order(rows):
    """Top-level sections present in `rows`, in document order."""
    seen = []
    for r in sorted(rows, key=lambda x: x.get("line") or 0):
        t = r.get("section") or ""
        if t not in seen:
            seen.append(t)
    return seen


def batch_plan(rows, batch_size=DEFAULT_BATCH_SIZE):
    """[(section_title, section_rows, batch_rows)] — one entry per request.

    Batching happens WITHIN a top-level section and each request carries only
    that section's clauses as context. Sending all 259 provisions of document
    text with every request would put ~50k characters in each of 13 prompts to
    no purpose: a provision's meaning is established by its own section.
    """
    plan = []
    for title in section_order(rows):
        srows = [r for r in rows if (r.get("section") or "") == title]
        prov = encodable(srows)
        if not prov:
            continue
        for group in batches(prov, batch_size):
            plan.append((title, srows, group))
    return plan


# Carried vocabulary is unbounded in principle (259 provisions could declare
# hundreds of atoms), and it is re-sent on every request. Acts are never
# dropped — cross-section act sharing is the entire point — but context atoms
# are capped at the most recently used, oldest evicted.
MAX_CARRIED_CONTEXT = 40


def cap_carried_atoms(atoms, max_context=MAX_CARRIED_CONTEXT):
    """Keep every act atom; keep the most recent `max_context` context atoms.

    `atoms` is in declaration order, so "most recent" is the tail. Returns
    (kept, n_dropped) with declaration order preserved.
    """
    ctx = [a for a in atoms if a.kind == "context"]
    if len(ctx) <= max_context:
        return list(atoms), 0
    keep = {id(a) for a in ctx[-max_context:]}
    kept = [a for a in atoms if a.kind != "context" or id(a) in keep]
    return kept, len(ctx) - max_context


def render_known_atoms(atoms):
    """Carried-forward vocabulary, split by kind so the act enum is explicit.
    The cross-batch case is where a context atom gets used as an act: within a
    batch the model can see what it just declared, but across batches it is
    working from this list, so the list has to say which is which."""
    if not atoms:
        return ""

    def render(kind):
        got = [a for a in atoms if a.kind == kind]
        if not got:
            return "  (none yet)"
        # Acts keep their glosses: judging "does this act already denote what
        # my provision is about?" is the reuse decision that matters, and it
        # cannot be made from a name. Context atoms are listed compactly once
        # the list is long — they are far more numerous and their reuse is
        # lower-stakes.
        if kind == "context" and len(got) > 20:
            return "\n".join(f"- {a.name} [{a.dimension}]" for a in got)
        return "\n".join(f"- {a.name} [{a.dimension}]: {a.gloss}" for a in got)

    return KNOWN_ATOMS_HEADER.format(
        n=len(atoms), context=render("context"), acts=render("act"),
        n_acts=sum(1 for a in atoms if a.kind == "act"))


def render_prompt(rows, batch_rows=None, known_atoms=(), batch_index=1,
                  n_batches=1, ask_axioms=True, section_title=None):
    """Return (system, user).

    `rows` is the whole SECTION whose text is sent as context — the one-pass
    justification was about input, and it holds per section. `batch_rows` is
    the slice of conditional provisions this request must encode; None means
    all of them.
    """
    system, user = load_template()
    prov = encodable(rows)
    batch_rows = list(batch_rows) if batch_rows is not None else prov
    title = section_title or (rows[0].get("section") if rows else None) \
        or "this section"

    if n_batches > 1:
        first = prov.index(batch_rows[0]) + 1 if batch_rows else 0
        last = prov.index(batch_rows[-1]) + 1 if batch_rows else 0
        batch_line = (
            f"This is request {batch_index} of {n_batches} in this run. The "
            f"section below is \"{title}\"; you are encoding provisions "
            f"{first}-{last} of its {len(prov)} conditional provisions. The "
            f"rest of this section, and the document's other sections, are "
            f"covered by other requests. Encode ONLY the {len(batch_rows)} "
            f"listed here.")
    else:
        batch_line = (f"All {len(prov)} conditional provisions in this section "
                      f"are listed here.")

    user = (user
            .replace("{{SECTION_TEXT}}", build_section_text(rows, omit=batch_rows))
            .replace("{{KNOWN_ATOMS_BLOCK}}", render_known_atoms(known_atoms))
            .replace("{{BATCH_LINE}}", batch_line)
            .replace("{{N_PROVISIONS}}", str(len(batch_rows)))
            .replace("{{PROVISIONS}}", build_provisions_block(batch_rows))
            .replace("{{AXIOM_BLOCK}}", AXIOM_ASK if ask_axioms else AXIOM_DEFER))
    return system, user


# --------------------------------------------------------------------------
# response parsing

_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.MULTILINE)

# finish/stop reasons that mean "the model was cut off", across providers
TRUNCATED_REASONS = {"length", "max_tokens", "max_output_tokens"}


def as_envelope(resp):
    """Normalize whatever a client returned into
    {text, finish_reason, reasoning, usage, raw}.

    Clients that return a bare string (providers.DryRunClient, providers.
    LiveClient) still work — they simply carry no finish_reason, so
    truncation is invisible for them and InstrumentedClient exists to fix
    that for live runs.
    """
    env = {"text": None, "finish_reason": None, "reasoning": None,
           "usage": {}, "raw": None}
    if resp is None:
        return env
    if isinstance(resp, dict):
        env["text"] = resp.get("text") if isinstance(resp.get("text"), str) else None
        fr = resp.get("finish_reason")
        env["finish_reason"] = fr.lower() if isinstance(fr, str) else None
        env["reasoning"] = (resp.get("reasoning")
                            if isinstance(resp.get("reasoning"), str) else None)
        env["usage"] = resp.get("usage") if isinstance(resp.get("usage"), dict) else {}
        env["raw"] = resp
        return env
    if isinstance(resp, str):
        env["text"] = resp
        return env
    env["raw"] = resp
    return env


def is_truncated(env):
    return (env.get("finish_reason") or "") in TRUNCATED_REASONS


def call_client(client, system, user):
    """Duck-typed call. A client exposing `complete_envelope` gives us
    finish_reason/reasoning; anything with plain `complete` still works."""
    if hasattr(client, "complete_envelope"):
        return as_envelope(client.complete_envelope(system, user))
    return as_envelope(client.complete(system, user))


def parse_response(text):
    """(obj, error). Never raises. Tolerates code fences and leading prose."""
    if text is None:
        return None, "no response (dry run or empty completion)"
    if not isinstance(text, str):
        return None, f"non-string response of type {type(text).__name__}"
    cleaned = _FENCE_RE.sub("", text)
    try:
        start = cleaned.index("{")
        end = cleaned.rindex("}") + 1
    except ValueError:
        return None, "no JSON object found in response"
    try:
        obj = json.loads(cleaned[start:end])
    except (ValueError, TypeError) as e:
        return None, f"unparseable JSON: {e}"
    if not isinstance(obj, dict):
        return None, f"top-level JSON is {type(obj).__name__}, expected object"
    return obj, None


def _as_list(obj, key):
    v = obj.get(key)
    if isinstance(v, list):
        return [x for x in v if isinstance(x, dict)]
    return []


# --------------------------------------------------------------------------
# verification

def _norm_ws(s):
    """Collapse whitespace runs. The source joins hard-wrapped lines with
    newlines, so a model quoting a sentence renders them as spaces; without
    this every multi-line clause would fail verification for a reason that has
    nothing to do with fidelity. Word content still has to match exactly."""
    return re.sub(r"\s+", " ", (s or "")).strip()


def resolve_span(span, by_id, spans):
    """(row, quote, reason). The model selects (focus_id, span_id); we look the
    text up. Nothing the model wrote ever becomes `quote`, so a fabricated
    quote is unrepresentable rather than merely detectable.

    Failure is a LOOKUP MISS with a specific cause — a different kind of defect
    from the old "authored text does not match", hence its own log stage.
    """
    if not isinstance(span, dict):
        return None, None, ("span is not an object", "span")
    fid = span.get("focus_id") or span.get("id")
    if not isinstance(fid, str) or not fid.strip():
        return None, None, ("span names no provision (focus_id missing)", "span")
    key = fid.strip().lower()
    row = by_id.get(key) or by_id.get(fa_id(key))
    if row is None:
        return None, None, (f"span cites no provision in this section "
                            f"(focus_id={fid!r})", "span_id")
    table = spans.get(row["id"], {})
    sid = span.get("span_id")
    if not isinstance(sid, str) or not sid.strip():
        return row, None, ("span has no span_id; quote text written by the "
                           "model is not accepted as provenance", "span_id")
    sid = sid.strip().lower()
    if sid not in table:
        return row, None, (f"unknown span_id {sid!r} for {row['id']} "
                           f"(offered: {', '.join(sorted(table)) or 'none'})",
                           "span_id")
    return row, table[sid], (None, None)


def verify_atoms(raw_atoms, rows, fail):
    """Return (atoms, stats). Atoms whose spans all fail verification are kept
    with empty spans and status draft, and counted. Nothing is dropped except
    objects with no usable name at all."""
    by_id = {}
    for r in rows:
        by_id[r["id"]] = r
        by_id[r["source_id"].lower()] = r
    spans = span_index(rows)

    atoms, seen = [], set()
    stats = {"atoms_total": 0, "atoms_verified": 0, "atoms_unverified": 0,
             "atoms_bad_identifier": 0, "atoms_bad_type": 0,
             "spans_total": 0, "spans_kept": 0, "spans_rejected": 0,
             "spans_authored_quote_ignored": 0,
             "atoms_malformed": 0, "atoms_duplicate": 0}

    for i, a in enumerate(raw_atoms):
        name = a.get("name")
        if not isinstance(name, str) or not name.strip():
            stats["atoms_malformed"] += 1
            fail("atom", "atom has no name", {"index": i})
            continue
        name = name.strip()
        if not IDENT_RE.match(name):
            stats["atoms_bad_identifier"] += 1
            fail("atom", "atom name violates ^[a-z][a-z0-9_]*$", {"name": name})
            continue
        if name in seen:
            stats["atoms_duplicate"] += 1
            fail("atom", "duplicate atom name; keeping the first", {"name": name})
            continue
        seen.add(name)

        kind = a.get("kind")
        dimension = a.get("dimension")
        bad_type = False
        if kind not in dsl.ATOM_KINDS:
            bad_type = True
            fail("atom", f"bad kind {kind!r}", {"name": name})
        if dimension not in dsl.DIMENSIONS:
            bad_type = True
            fail("atom", f"bad dimension {dimension!r}", {"name": name})
        if bad_type:
            stats["atoms_bad_type"] += 1

        kept = []
        for span in (a.get("quote_spans") or []):
            stats["spans_total"] += 1
            if isinstance(span, dict) and span.get("quote") is not None:
                # the model was told to select, not to write; whatever it wrote
                # is discarded, but the attempt is worth counting
                stats["spans_authored_quote_ignored"] += 1
            row, quote, (reason, stage) = resolve_span(span, by_id, spans)
            if quote is not None:
                stats["spans_kept"] += 1
                kept.append({"locator": row["locator"],
                             "focus_id": row["id"],
                             "quote": quote})          # looked up, never authored
            else:
                stats["spans_rejected"] += 1
                fail(stage, reason,
                     {"atom": name,
                      "focus_id": row["id"] if row else None,
                      "span_id": span.get("span_id")
                      if isinstance(span, dict) else None})

        stats["atoms_total"] += 1
        if kept:
            stats["atoms_verified"] += 1
        else:
            stats["atoms_unverified"] += 1

        atoms.append(Atom(
            name=name,
            kind=kind if kind in dsl.ATOM_KINDS else "context",
            dimension=dimension if dimension in dsl.DIMENSIONS else "situation",
            gloss=str(a.get("gloss") or ""),
            quote_spans=kept,
            status="draft",
        ))
    return atoms, stats


def normalize_rules(raw_rules, rows, fail):
    """Force tier, re-attach provenance from the inventory, enforce the
    identifier regex. Rules with unknown ids are kept only if their id is a
    legal identifier — provenance then stays whatever the model gave."""
    by_id = {r["id"]: r for r in rows}
    rules, seen = [], set()
    stats = {"rules_total": 0, "rules_bad_identifier": 0, "rules_bad_modality": 0,
             "rules_unknown_provision": 0, "rules_duplicate": 0,
             "rules_tier_corrected": 0}

    for i, r in enumerate(raw_rules):
        rid = r.get("id")
        if not isinstance(rid, str) or not IDENT_RE.match(rid.strip()):
            stats["rules_bad_identifier"] += 1
            fail("rule", "rule id missing or violates ^[a-z][a-z0-9_]*$",
                 {"index": i, "id": str(rid)})
            continue
        rid = rid.strip()
        if rid in seen:
            stats["rules_duplicate"] += 1
            fail("rule", "duplicate rule id; keeping the first", {"id": rid})
            continue
        seen.add(rid)

        modality = r.get("modality")
        if modality not in dsl.MODALITIES:
            stats["rules_bad_modality"] += 1
            fail("rule", f"bad modality {modality!r}", {"id": rid})
            modality = str(modality or "")

        base = by_id.get(rid) or by_id.get(rid.rsplit("_", 1)[0])
        if base is None:
            stats["rules_unknown_provision"] += 1
            fail("rule", "rule id maps to no provision in this section", {"id": rid})
            locator = str(r.get("locator") or "")
            quote = str(r.get("quote") or "")
        else:
            locator, quote = base["locator"], base["quote"]

        if r.get("tier") != TIER:
            stats["rules_tier_corrected"] += 1

        conditions = [c.strip() for c in (r.get("conditions") or [])
                      if isinstance(c, str) and c.strip()]
        defeaters = []
        for d in (r.get("defeaters") or []):
            if not isinstance(d, dict):
                continue
            dc = [c.strip() for c in (d.get("conditions") or [])
                  if isinstance(c, str) and c.strip()]
            defeaters.append({"conditions": dc, "source": str(d.get("source") or "")})

        stats["rules_total"] += 1
        rules.append(Rule(
            id=rid, modality=modality, act=str(r.get("act") or ""),
            conditions=conditions, defeaters=defeaters, tier=TIER,
            locator=locator, quote=quote, status="draft",
        ))
    return rules, stats


def _license_ok(ax, stage, label, fail):
    """Shared licensing discipline: a license is mandatory, `textual` requires
    a citation. Under uncertainty the axiom is omitted rather than guessed —
    omission produces reviewable noise, a wrong axiom prunes silently."""
    lic = ax.get("license")
    source = str(ax.get("source") or "").strip()
    if lic not in dsl.AXIOM_LICENSES:
        fail(stage, f"missing or bad license {lic!r}", label)
        return None, None
    if lic == "textual" and not source:
        fail(stage, "textual license requires a citation in source", label)
        return None, None
    return lic, source


def _legal_names(value, n_min, n_exact=None):
    if not isinstance(value, list):
        return None
    if n_exact is not None and len(value) != n_exact:
        return None
    if len(value) < n_min:
        return None
    if not all(isinstance(a, str) and IDENT_RE.match(a.strip()) for a in value):
        return None
    names = [a.strip() for a in value]
    return names if len(set(names)) == len(names) else None


def normalize_incompat(raw_incompat, act_names, fail):
    """incompat constrains ACTS: two acts that cannot both be performed."""
    out = []
    stats = {"incompat_total": 0, "incompat_rejected": 0}
    for i, ax in enumerate(raw_incompat):
        acts = _legal_names(ax.get("acts"), 2, n_exact=2)
        if acts is None:
            stats["incompat_rejected"] += 1
            fail("incompat", "incompat needs exactly 2 distinct legal act "
                             "identifiers", {"index": i, "acts": str(ax.get("acts"))})
            continue
        lic, source = _license_ok(ax, "incompat", {"acts": acts}, fail)
        if lic is None:
            stats["incompat_rejected"] += 1
            continue
        unknown = [a for a in acts if a not in act_names]
        if unknown:
            stats["incompat_rejected"] += 1
            fail("incompat", f"references undefined act atoms {unknown}",
                 {"acts": acts})
            continue
        stats["incompat_total"] += 1
        out.append({"acts": acts, "license": lic, "source": source})
    return out, stats


def normalize_exclusions(raw_exclusions, context_names, fail):
    """exclusions constrain CONTEXT atoms: situation features that cannot
    co-occur. Mandatory field (contract §3) — without it the emitter gives
    every context atom an independent choice rule and the solver can build
    impossible situations, so conflicts get found in worlds that cannot exist.

    `at_most_one` takes >= 2 atoms, `excludes` exactly 2. Same licensing
    discipline as incompat.
    """
    out = []
    stats = {"exclusions_total": 0, "exclusions_rejected": 0,
             "exclusions_at_most_one": 0, "exclusions_excludes": 0}
    for i, ax in enumerate(raw_exclusions):
        kind = ax.get("kind")
        if kind not in ("at_most_one", "excludes"):
            stats["exclusions_rejected"] += 1
            fail("exclusion", f"bad exclusion kind {kind!r} "
                              "(at_most_one | excludes)", {"index": i})
            continue
        names = _legal_names(ax.get("atoms"), 2,
                             n_exact=2 if kind == "excludes" else None)
        if names is None:
            need = "exactly 2" if kind == "excludes" else "at least 2"
            stats["exclusions_rejected"] += 1
            fail("exclusion", f"{kind} needs {need} distinct legal atom "
                              "identifiers", {"index": i,
                                              "atoms": str(ax.get("atoms"))})
            continue
        lic, source = _license_ok(ax, "exclusion", {"atoms": names}, fail)
        if lic is None:
            stats["exclusions_rejected"] += 1
            continue
        unknown = [a for a in names if a not in context_names]
        if unknown:
            stats["exclusions_rejected"] += 1
            fail("exclusion", f"references undefined context atoms {unknown} "
                              "(exclusions constrain context atoms only; acts "
                              "belong in incompat)", {"atoms": names})
            continue
        stats["exclusions_total"] += 1
        stats["exclusions_" + kind] += 1
        out.append({"atoms": names, "kind": kind, "license": lic,
                    "source": source})
    return out, stats


def reject_miskinded_acts(rules, atoms, fail):
    """Drop rules whose `act` names a declared atom of the wrong kind.

    This is the cross-batch failure mode (`fa_ag8e`): within a batch the model
    can see the atom it just declared, but a later batch works from the
    carried-forward list, and a context atom read as an act produces a rule the
    emitter cannot use. Dropped rather than reported, so the provision lands in
    `unencoded` with a specific reason and coverage stays honest.
    """
    by_name = {a.name: a for a in atoms}
    kept, reasons = [], {}
    for r in rules:
        a = by_name.get(r.act)
        if a is not None and a.kind != "act":
            fail("rule", f"rule act {r.act!r} is a {a.kind} atom, not an act; "
                         "rule discarded", {"id": r.id, "act": r.act,
                                            "actual_kind": a.kind})
            reasons[r.id] = (f"rule discarded: its act {r.act!r} is a "
                             f"{a.kind} atom, not an act atom")
            continue
        kept.append(r)
    return kept, reasons


def build_unencoded(raw_unencoded, rules, rows, fail, forced=None):
    """`unencoded` is the coverage measurement, so it is completed
    mechanically: every conditional provision with no rule appears, whether or
    not the model remembered to say so."""
    prov_ids = [r["id"] for r in encodable(rows)]
    covered = set()
    for rule in rules:
        covered.add(rule.id)
        covered.add(rule.id.rsplit("_", 1)[0])

    given = {}
    for u in raw_unencoded:
        fid = u.get("focus_id") or u.get("id")
        if not isinstance(fid, str):
            continue
        fid = fid.strip().lower()
        fid = fid if fid.startswith(ID_PREFIX) else fa_id(fid)
        given[fid] = str(u.get("reason") or "").strip()

    out = []
    for pid in prov_ids:
        if pid in covered:
            if pid in given:
                fail("unencoded", "provision reported unencoded but a rule was "
                                  "also emitted for it; rule kept", {"focus_id": pid})
            continue
        reason = (forced or {}).get(pid) or given.get(pid)
        if not reason:
            reason = ("not reported by the model; no rule was emitted for this "
                      "provision (reason unstated)")
            fail("unencoded", "provision produced no rule and no reason",
                 {"focus_id": pid})
        out.append({"focus_id": pid, "reason": reason})

    stray = sorted(set(given) - set(prov_ids))
    for s in stray:
        fail("unencoded", "unencoded entry names no conditional provision in "
                          "this section", {"focus_id": s})
    return out


# --------------------------------------------------------------------------
# conflict capability — can this extraction produce a conflict AT ALL?

CONFLICT_WARNING = (
    "CANNOT PRODUCE CONFLICTS: no act carries both an oblige and a forbid, and "
    "there are no incompat axioms. No clause of the conflict-detection block "
    "can fire in any scenario, so |C_tool| = 0 regardless of coverage and the "
    "delta comparison is vacuous. Cause is almost always one bespoke act per "
    "provision — rules only meet on a shared act.")


def conflict_capability(atoms, rules, incompat):
    """Structural diagnostic, computed at extraction time.

    A conflict needs two rules that meet: either the same act under opposing
    modalities, or two acts tied by an incompat. Neither is a coverage
    property — an extraction can be 100% complete and still incapable — so it
    has to be measured here rather than discovered three steps downstream.
    """
    by_act = {}
    for r in rules:
        by_act.setdefault(r.act, set()).add(r.modality)
    both = sorted(a for a, m in by_act.items()
                  if "oblige" in m and "forbid" in m)
    n_acts = len(by_act)
    declared_acts = sum(1 for a in atoms if a.kind == "act")
    return {
        "distinct_acts": n_acts,
        "declared_act_atoms": declared_acts,
        "rules_per_act": round(len(rules) / n_acts, 2) if n_acts else 0.0,
        "max_rules_on_one_act": max((len(v) for v in by_act.values()), default=0),
        "acts_with_both_oblige_and_forbid": len(both),
        "contested_acts": both,
        "incompat_count": len(incompat),
        "conflict_capable": bool(both or incompat),
    }


# --------------------------------------------------------------------------
# checker pass — report, never discard

def check_extraction(atoms, rules, incompat, exclusions=()):
    """Run checker.check_rule over every rule plus the vocabulary's own
    validation. Exclusions enter the vocabulary as axioms, so a rule whose
    trigger is impossible under them is caught here as a dead rule rather than
    downstream as a spurious conflict. Import is local so the module (and its
    tests) work without clingo installed; an import failure is reported, not
    raised."""
    report = {"vocabulary_errors": [], "rules": [],
              "rules_ok": 0, "rules_failed": 0, "checker_available": True}
    axioms = [Axiom(kind="incompat", atoms=list(ax["acts"]),
                    license=ax["license"], source=ax.get("source", ""))
              for ax in incompat]
    axioms += [Axiom(kind=ax["kind"], atoms=list(ax["atoms"]),
                     license=ax["license"], source=ax.get("source", ""))
               for ax in exclusions]
    vocab = Vocabulary(atoms=atoms, axioms=axioms, spec="modelspec")
    try:
        report["vocabulary_errors"] = vocab.validate()
    except Exception as e:                                   # pragma: no cover
        report["vocabulary_errors"] = [f"vocabulary validation raised: {e}"]
    try:
        from checker import check_rule
    except Exception as e:
        report["checker_available"] = False
        report["checker_error"] = f"{type(e).__name__}: {e}"
        return report
    for rule in rules:
        try:
            v = check_rule(rule, vocab)
            entry = {"id": rule.id, "ok": bool(v.ok), "stage": v.stage,
                     "errors": list(v.errors), "warnings": list(v.warnings)}
        except Exception as e:
            entry = {"id": rule.id, "ok": False, "stage": "exception",
                     "errors": [f"{type(e).__name__}: {e}"], "warnings": []}
        report["rules"].append(entry)
        report["rules_ok" if entry["ok"] else "rules_failed"] += 1
    return report


# --------------------------------------------------------------------------
# live client with an instrumented response envelope
#
# providers.LiveClient returns only the assistant text, which discards
# finish_reason (so truncation is invisible) and the separate reasoning
# channel (so a truncated run cannot be diagnosed without re-paying for it).
# providers.py is not mine to change, so this subclass overrides only the
# transport and keeps ProviderConfig as the single source of URL/key/model.
# If the provider layer's owner wants this folded in, complete_envelope() is
# the whole interface.

class InstrumentedClient:
    """Live client returning {text, finish_reason, reasoning, usage, raw}."""

    def __init__(self, provider, max_tokens=None):
        self.provider = provider
        if max_tokens:
            provider.max_tokens = max_tokens
        if not provider.key():
            raise RuntimeError(
                f"provider {provider.name}: no key in ${provider.api_key_env} — "
                "refusing to construct a live client")

    def _request(self, system, user):
        p = self.provider
        ua = "semi-formal-experiment/0.1"
        if p.kind == "openai-compatible":
            url = p.base_url.rstrip("/") + "/chat/completions"
            body = {"model": p.model, "max_tokens": p.max_tokens,
                    "temperature": p.temperature,
                    "messages": [{"role": "system", "content": system},
                                 {"role": "user", "content": user}]}
            headers = {"Authorization": f"Bearer {p.key()}",
                       "Content-Type": "application/json", "User-Agent": ua}
        elif p.kind == "anthropic":
            url = "https://api.anthropic.com/v1/messages"
            body = {"model": p.model, "max_tokens": p.max_tokens,
                    "system": system,
                    "messages": [{"role": "user", "content": user}]}
            headers = {"x-api-key": p.key(), "anthropic-version": "2023-06-01",
                       "Content-Type": "application/json", "User-Agent": ua}
        else:
            raise ValueError(f"unknown provider kind {p.kind}")
        return urllib.request.Request(
            url, json.dumps(body).encode(), headers=headers)

    def complete_envelope(self, system, user):
        req = self._request(system, user)
        data = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=300) as resp:
                    data = json.load(resp)
                break
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503) and attempt < 2:
                    time.sleep(5 * (attempt + 1))
                    continue
                raise
        env = self._envelope(data)
        # Without this the call is billed and invisible to spend.py, and the
        # session's hard budget is enforced against a number that is silently
        # low. Six live runs were already unaccounted when this was found.
        self._log_usage(env)
        return env

    def _envelope(self, data):
        if not isinstance(data, dict):
            return {"text": None, "finish_reason": None, "reasoning": None,
                    "usage": {}, "raw": data}
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        if self.provider.kind == "openai-compatible":
            choice = (data.get("choices") or [{}])[0]
            msg = choice.get("message") or {}
            # providers differ on where the reasoning channel lives
            reasoning = msg.get("reasoning") or msg.get("reasoning_content")
            if not reasoning and isinstance(msg.get("reasoning_details"), list):
                reasoning = "\n".join(
                    d.get("text", "") for d in msg["reasoning_details"]
                    if isinstance(d, dict))
            return {"text": msg.get("content"),
                    "finish_reason": choice.get("finish_reason"),
                    "reasoning": reasoning or None,
                    "usage": {"prompt_tokens": usage.get("prompt_tokens"),
                              "completion_tokens": usage.get("completion_tokens")},
                    "raw": None}
        blocks = data.get("content") or []
        text = "".join(b.get("text", "") for b in blocks
                       if isinstance(b, dict) and b.get("type", "text") == "text")
        thinking = "\n".join(b.get("thinking", "") for b in blocks
                             if isinstance(b, dict) and b.get("type") == "thinking")
        return {"text": text or None,
                "finish_reason": data.get("stop_reason"),
                "reasoning": thinking or None,
                "usage": {"prompt_tokens": usage.get("input_tokens"),
                          "completion_tokens": usage.get("output_tokens")},
                "raw": None}

    def complete(self, system, user):
        return self.complete_envelope(system, user).get("text")

    def _log_usage(self, env):
        """Route measured usage to the shared spend log.

        This client predates `providers.complete_envelope` and implements its
        own transport, so without this the calls are invisible to spend.py and
        the session's hard budget is an undercount. Failures here must never
        break an extraction run.
        """
        try:
            import providers
            # This client stores its config on `self.provider`. Reading a
            # `self.name`/`self.cfg` that never existed logged provider=None
            # and model=None, which spend.cost_of cannot price -- the row
            # would land in `unpriced` and be counted as $0.00.
            p = getattr(self, "provider", None)
            providers._append_usage("DEFAULT", {
                "provider": getattr(p, "name", None),
                "model": getattr(p, "model", None),
                "finish_reason": env.get("finish_reason"),
                "truncated": str(env.get("finish_reason") or "").lower() in
                             ("length", "max_tokens", "max_output_tokens"),
                "text": env.get("text") or "",
                "reasoning": env.get("reasoning") or "",
                "usage": env.get("usage") or {}})
        except Exception:
            pass


# --------------------------------------------------------------------------
# failure log

class FailureLog:
    """Append-only JSONL. Every recoverable defect lands here; the run
    continues. Writing failures must itself never raise."""

    def __init__(self, path, run_id="", model=""):
        self.path = path
        self.run_id = run_id
        self.model = model
        self.records = []

    def __call__(self, stage, error, detail=None):
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "run_id": self.run_id,
               "model": self.model, "stage": stage, "error": error,
               "detail": detail or {}}
        self.records.append(rec)
        if self.path:
            try:
                os.makedirs(os.path.dirname(os.path.abspath(self.path)) or ".",
                            exist_ok=True)
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            except OSError:
                pass
        return rec

    def count(self, stage=None):
        if stage is None:
            return len(self.records)
        return sum(1 for r in self.records if r["stage"] == stage)


# --------------------------------------------------------------------------
# the run

def make_run_id(model, seed, user_prompt):
    h = hashlib.sha1(f"{model}|{seed}|{user_prompt}".encode()).hexdigest()[:8]
    return f"s{seed}-{h}"


def _add_stats(into, more):
    for k, v in more.items():
        if isinstance(v, (int, float)):
            into[k] = into.get(k, 0) + v
        else:
            into[k] = v
    return into


def extract_batch(response, rows, fail, batch_rows=None, batch_no=1):
    """One response -> the pieces it contributed. Never raises.

    `rows` is the whole section (spans may cite any clause); `batch_rows` is
    what this request was asked to encode, so a rule for a provision outside
    the batch can be flagged as a scope violation without being thrown away.
    """
    env = as_envelope(response)
    truncated = is_truncated(env)
    obj, err = parse_response(env["text"])

    if truncated:
        # Truncation and malformed JSON are different defects with different
        # fixes (raise the cap / batch smaller vs. tighten the format
        # instruction). Never report one as the other.
        usage = env.get("usage") or {}
        fail("truncated_output",
             "model hit its output cap before finishing the JSON",
             {"batch": batch_no,
              "finish_reason": env.get("finish_reason"),
              "completion_tokens": usage.get("completion_tokens"),
              "prompt_tokens": usage.get("prompt_tokens"),
              "content_chars": len(env["text"] or ""),
              "reasoning_chars": len(env["reasoning"] or "")})
    elif err:
        fail("response", err, {"batch": batch_no,
                               "head": (env["text"] or "")[:300]
                               if isinstance(env["text"], str) else None})
    if err:
        obj = {}

    atoms, atom_stats = verify_atoms(_as_list(obj, "atoms"), rows, fail)
    rules, rule_stats = normalize_rules(_as_list(obj, "rules"), rows, fail)

    if batch_rows is not None:
        in_batch = {r["id"] for r in batch_rows}
        for r in rules:
            if r.id not in in_batch and r.id.rsplit("_", 1)[0] not in in_batch:
                rule_stats["rules_out_of_batch"] = \
                    rule_stats.get("rules_out_of_batch", 0) + 1
                fail("rule", "rule emitted for a provision outside this "
                             "batch; kept", {"id": r.id, "batch": batch_no})

    stats = {}
    _add_stats(stats, atom_stats)
    _add_stats(stats, rule_stats)
    stats["batches"] = 1
    stats["truncated_batches"] = 1 if truncated else 0
    stats["parsed_batches"] = 0 if err else 1
    stats["reasoning_chars"] = len(env["reasoning"] or "")
    return {"atoms": atoms, "rules": rules,
            "raw_incompat": _as_list(obj, "incompat"),
            "raw_exclusions": _as_list(obj, "exclusions"),
            "raw_declined": _as_list(obj, "incompat_declined"),
            "raw_unencoded": _as_list(obj, "unencoded"),
            "stats": stats, "parsed": err is None, "truncated": truncated,
            "envelope": env}


def merge_atoms(existing, new, fail):
    """First definition of a name wins; later ones are merged only for their
    quote spans. Cross-batch duplicates are avoided by showing each batch the
    atoms already defined, so a collision here means the model re-listed an
    atom (harmless) or redefined it (worth logging)."""
    by_name = {a.name: a for a in existing}
    order = list(existing)
    merged = 0
    for a in new:
        cur = by_name.get(a.name)
        if cur is None:
            # copy: the accumulator is also handed to the next batch's prompt,
            # and must not alias the per-batch results
            a = dataclasses.replace(a, quote_spans=list(a.quote_spans))
            by_name[a.name] = a
            order.append(a)
            continue
        merged += 1
        if (cur.kind, cur.dimension) != (a.kind, a.dimension):
            fail("atom", "atom redefined with a different kind/dimension "
                         "across batches; first definition kept",
                 {"name": a.name,
                  "first": f"{cur.kind}/{cur.dimension}",
                  "later": f"{a.kind}/{a.dimension}"})
        have = {(s.get("locator"), s.get("quote")) for s in cur.quote_spans}
        for s in a.quote_spans:
            if (s.get("locator"), s.get("quote")) not in have:
                cur.quote_spans.append(s)
    return order, merged


def per_section_stats(rows, rules, unencoded):
    """Coverage broken out per top-level section, plus the totals."""
    ruled = {r.id for r in rules}
    unenc = {u["focus_id"] for u in unencoded}
    out = {}
    for title in section_order(rows):
        prov = [r["id"] for r in encodable(rows)
                if (r.get("section") or "") == title]
        enc = [p for p in prov if p in ruled]
        out[title] = {
            "provisions": len(prov),
            "encoded": len(enc),
            "unencoded": len([p for p in prov if p in unenc]),
            "coverage": round(len(enc) / len(prov), 4) if prov else 0.0,
        }
    return out


def assemble(parts, rows, model, run_id, fail, section=DEFAULT_SECTION):
    """Merge batch results into one contract-shaped artifact. Never raises."""
    atoms, rules, stats = [], [], {}
    raw_incompat, raw_exclusions, raw_unencoded, raw_declined = [], [], [], []
    merged_atoms = 0
    for p in parts:
        atoms, m = merge_atoms(atoms, p["atoms"], fail)
        merged_atoms += m
        rules.extend(p["rules"])
        raw_incompat.extend(p["raw_incompat"])
        raw_exclusions.extend(p["raw_exclusions"])
        raw_unencoded.extend(p["raw_unencoded"])
        raw_declined.extend(p.get("raw_declined") or [])
        _add_stats(stats, p["stats"])

    seen, deduped = set(), []
    for r in rules:
        if r.id in seen:
            stats["rules_duplicate"] = stats.get("rules_duplicate", 0) + 1
            fail("rule", "duplicate rule id across batches; keeping the first",
                 {"id": r.id})
            continue
        seen.add(r.id)
        deduped.append(r)
    rules = deduped

    rules, forced = reject_miskinded_acts(rules, atoms, fail)
    stats["rules_miskinded_act"] = len(forced)

    act_names = {a.name for a in atoms if a.kind == "act"}
    ctx_names = {a.name for a in atoms if a.kind == "context"}
    incompat, ax_stats = normalize_incompat(raw_incompat, act_names, fail)
    exclusions, ex_stats = normalize_exclusions(raw_exclusions, ctx_names, fail)
    unencoded = build_unencoded(raw_unencoded, rules, rows, fail, forced=forced)

    prov = encodable(rows)
    _add_stats(stats, ax_stats)
    _add_stats(stats, ex_stats)
    stats["atoms_merged_across_batches"] = merged_atoms
    stats["rules_total"] = len(rules)
    stats["atoms_total"] = len(atoms)
    stats["provisions_total"] = len(prov)
    stats["provisions_encoded"] = len(prov) - len(unencoded)
    stats["coverage"] = round(stats["provisions_encoded"] / len(prov), 4) if prov else 0.0
    stats["unencoded_total"] = len(unencoded)
    stats["failures"] = fail.count()
    stats["response_parsed"] = stats.get("parsed_batches", 0) == stats.get("batches", 0)

    # incompat pairs the model considered and rejected: evidence the pairwise
    # pass happened. Recorded, but never a reason to add an axiom.
    stats["incompat_declined"] = len(raw_declined)
    for d in raw_declined:
        fail("incompat_declined", "act pair considered and rejected",
             {"acts": d.get("acts"), "reason": str(d.get("reason") or "")[:300]})

    stats["sections"] = per_section_stats(rows, rules, unencoded)
    stats["n_sections"] = len(stats["sections"])

    cap = conflict_capability(atoms, rules, incompat)
    stats.update(cap)
    warnings = []
    if not cap["conflict_capable"]:
        warnings.append(CONFLICT_WARNING)
        fail("conflict_capability", CONFLICT_WARNING,
             {k: cap[k] for k in ("distinct_acts", "rules_per_act",
                                  "acts_with_both_oblige_and_forbid",
                                  "incompat_count")})

    return {
        "warnings": warnings,
        "section": section_key(section),
        "model": model,
        "run_id": run_id,
        "atoms": [a.__dict__.copy() for a in atoms],
        "rules": [r.__dict__.copy() for r in rules],
        "incompat": incompat,
        "exclusions": exclusions,
        "unencoded": unencoded,
        "stats": stats,
        "check": check_extraction(atoms, rules, incompat, exclusions),
    }


def build_extraction(response, rows, model, run_id, fail,
                     section=DEFAULT_SECTION):
    """Single-response convenience path: one batch covering the whole section.

    A junk, truncated, or absent response yields a structurally valid artifact
    whose `unencoded` covers all conditional provisions — coverage 0, stated
    rather than crashed.
    """
    part = extract_batch(response, rows, fail)
    return assemble([part], rows, model, run_id, fail, section=section)


def log_reasoning(env, out_dir, run_id, batch_no):
    """Persist the reasoning channel. gpt-oss-20b spent 31,767 chars there and
    339 on content; without this a truncated run can only be diagnosed by
    paying for it again."""
    text = env.get("reasoning")
    if not text or not out_dir:
        return None
    try:
        d = os.path.join(out_dir, "reasoning")
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, f"{run_id}_b{batch_no:02d}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path
    except OSError:
        return None


def run_once(client, rows, model, seed, out_dir=".", log_path=None,
             batch_size=DEFAULT_BATCH_SIZE, section=DEFAULT_SECTION):
    """One independent extraction run, in sequential output batches.

    Batches are grouped by top-level section and each request carries only its
    own section's text; but the atom accumulator spans the WHOLE run, so an
    act declared while processing one section is offered to every later
    section. A vocabulary that restarts per section would reproduce the
    act-proliferation failure at document scale.

    Axioms are requested once, on the final request of the run, when the
    complete act set exists.
    """
    plan = batch_plan(rows, batch_size)
    if not plan:
        plan = [(section, rows, [])]
    _, first_rows, first_group = plan[0]
    system, first_user = render_prompt(first_rows, first_group, (), 1,
                                       len(plan), ask_axioms=len(plan) == 1)
    run_id = make_run_id(model, seed, first_user)
    log_path = log_path or os.path.join(out_dir, "extract_failures.jsonl")
    fail = FailureLog(log_path, run_id=run_id, model=model)

    parts, known, any_response = [], [], False
    dropped_ctx = 0
    for i, (title, srows, group) in enumerate(plan, start=1):
        last = i == len(plan)
        carried, dropped = cap_carried_atoms(known)
        dropped_ctx = max(dropped_ctx, dropped)
        system, user = render_prompt(srows, group, carried, i, len(plan),
                                     ask_axioms=last, section_title=title)
        try:
            resp = call_client(client, system, user)
        except Exception as e:
            fail("call", f"provider call failed: {type(e).__name__}: {e}",
                 {"batch": i, "section": title})
            resp = None
        env = as_envelope(resp)
        if env["text"] is not None:
            any_response = True
        log_reasoning(env, out_dir, run_id, i)
        part = extract_batch(resp, rows, fail, batch_rows=group, batch_no=i)
        part["section"] = title
        parts.append(part)
        known, _ = merge_atoms(known, part["atoms"], fail)

    art = assemble(parts, rows, model, run_id, fail, section=section)
    art["seed"] = seed
    art["batch_size"] = batch_size
    art["n_batches"] = len(plan)
    art["stats"]["carried_context_atoms_dropped"] = dropped_ctx
    art["plan"] = [{"request": i, "section": t, "context_provisions": len(sr),
                    "encoded": len(g)}
                   for i, (t, sr, g) in enumerate(plan, start=1)]
    art["dry_run"] = not any_response and fail.count("call") == 0

    os.makedirs(out_dir, exist_ok=True)
    safe_model = re.sub(r"[^A-Za-z0-9_.-]", "_", model)
    path = os.path.join(out_dir, f"extraction_{safe_model}_{run_id}.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(art, f, indent=1, ensure_ascii=False)
    except OSError as e:
        fail("write", f"could not write artifact: {e}", {"path": path})
        path = None
    return art, path, fail


def _summarize(art, path):
    s = art["stats"]
    print(f"[{art['model']} / {art['run_id']}] "
          f"atoms={s['atoms_total']} (unverified={s['atoms_unverified']}) "
          f"rules={s['rules_total']} incompat={s['incompat_total']} "
          f"exclusions={s['exclusions_total']} "
          f"unencoded={s['unencoded_total']} "
          f"coverage={s['coverage']:.2f} failures={s['failures']}"
          + (f" -> {path}" if path else " -> NOT WRITTEN"))
    print(f"    acts: {s.get('distinct_acts', 0)} distinct over {s.get('rules_total', 0)} rules "
          f"({s.get('rules_per_act', 0)} rules/act, max {s.get('max_rules_on_one_act', 0)}); "
          f"{s.get('acts_with_both_oblige_and_forbid', 0)} contested; "
          f"incompat={s.get('incompat_count', 0)} "
          f"(declined {s.get('incompat_declined', 0)})")
    for w in art.get("warnings", []):
        print("    !! " + w)
    print(f"    batches: {s.get('parsed_batches', 0)}/{s.get('batches', 0)} parsed, "
          f"{s.get('truncated_batches', 0)} truncated; "
          f"{s.get('atoms_merged_across_batches', 0)} atom reuses across batches; "
          f"{s.get('reasoning_chars', 0)} chars of reasoning captured")
    ch = art["check"]
    if ch.get("checker_available"):
        print(f"    checker: {ch['rules_ok']} ok / {ch['rules_failed']} failed; "
              f"{len(ch['vocabulary_errors'])} vocabulary errors")
    else:
        print(f"    checker unavailable: {ch.get('checker_error')}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--runs", type=int, default=2,
                    help="k independent runs (contract: k=2)")
    ap.add_argument("--models", default=None,
                    help="comma-separated provider names from providers.json; "
                         "defaults to the first --runs providers")
    ap.add_argument("--section", default=DEFAULT_SECTION,
                    help="top-level section title, or 'all' for the whole "
                         f"document (default {DEFAULT_SECTION!r})")
    ap.add_argument("--providers", default="providers.json")
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--log", default=None, help="failure JSONL path")
    ap.add_argument("--prompt-log", default="prompt_log")
    ap.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE,
                    help="conditional provisions per request; the whole "
                         "section is sent every time regardless "
                         f"(default {DEFAULT_BATCH_SIZE}: 42 -> 3 requests). "
                         "0 or >=42 means one request.")
    ap.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS,
                    help="output cap per request, overriding providers.json "
                         f"(default {DEFAULT_MAX_TOKENS}); needs room for the "
                         "reasoning channel as well as the JSON")
    ap.add_argument("--live", action="store_true",
                    help="make real API calls (default is dry run: prompts are "
                         "recorded, no network)")
    ap.add_argument("--print-prompt", action="store_true",
                    help="print the exact prompt(s) and exit")
    args = ap.parse_args(argv)

    rows = load_section(args.section)
    if not rows:
        print(f"no focus areas for section {args.section!r}; "
              f"known: {', '.join(section_titles())}")
        return 1
    prov = encodable(rows)
    plan = batch_plan(rows, args.batch_size)
    print(f"scope {section_key(args.section)!r}: {len(rows)} focus areas, "
          f"{len(prov)} conditional, {sum(len(r['quote']) for r in rows)} chars "
          f"of clause text, {len(section_order(rows))} section(s); "
          f"{len(plan)} request(s)")
    for i, (title, srows, group) in enumerate(plan, start=1):
        print(f"   {i:3}. {title:28} context {len(srows):3} provisions, "
              f"encode {len(group):3}")

    if args.print_prompt:
        for i, (title, srows, group) in enumerate(plan, start=1):
            system, user = render_prompt(srows, group, (), i, len(plan),
                                         ask_axioms=i == len(plan),
                                         section_title=title)
            print(f"########## REQUEST {i} of {len(plan)} — {title} ##########")
            print("### SYSTEM\n" + system + "\n\n### USER\n" + user)
        return 0

    from providers import ProviderConfig, make_client
    configs = ProviderConfig.load_all(_p(args.providers))
    by_name = {c.name: c for c in configs}
    if args.models:
        names = [n.strip() for n in args.models.split(",") if n.strip()]
    else:
        names = [c.name for c in configs][:args.runs]
    if not names:
        print("no providers configured")
        return 1

    for i in range(args.runs):
        name = names[i % len(names)]
        cfg = by_name.get(name)
        if cfg is None:
            print(f"unknown provider {name!r}; skipping")
            continue
        # distinct model per run where available, distinct seed otherwise
        cfg.temperature = 0.2 if i == 0 else 0.6
        cfg.max_tokens = max(cfg.max_tokens or 0, args.max_tokens)
        if args.live:
            client = InstrumentedClient(cfg, max_tokens=cfg.max_tokens)
        else:
            client = make_client(cfg, live=False, log_dir=_p(args.prompt_log))
        art, path, _ = run_once(client, rows, model=cfg.model, seed=i,
                                out_dir=args.out_dir, log_path=args.log,
                                batch_size=args.batch_size,
                                section=args.section)
        _summarize(art, path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
