"""Link-check a clause translation: is it MISSING A REFERENCE, and does it
keep the claims it makes about its own rule set?

⭐ REWRITTEN 2026-08-07 for the fixed stage-1 vocabulary (`phase_1/schema.py`).
Stage 1 no longer emits free-form ASP with arbitrary rule heads. Every head is
now `asserts/3`, `beats/3`, `defines/3` or an ontology atom, and the deontic
STATUSES (`forbid`, `permit`, `oblige`, `prefer`) are ARGUMENTS of `asserts/3`,
never heads. Several checks here were written against the old shape and had
gone silently vacuous; see CHECKS below and `test_link.py` for the failing case
each one is pinned by.

The question this answers, with no reasoning capability at all:

    "This clause's translation uses a predicate. Does anything define it?
     If not, which clause should have?"

TWO LAYERS, both mechanical.

  L1  ANCHOR GRAPH (free, high precision, incomplete). The spec's own text
      carries its cross-references as markdown anchors -- `[restricted](#restricted_content)`
      -- and `section_id` values match those anchors. 45 of 46 distinct targets
      in the corpus resolve. So the referenced sections are readable straight
      off the source with a regex. Only ~13% of clauses carry anchors, so this
      is a LOWER BOUND on dependencies, never the whole set.

  L2  UNRESOLVED PREDICATES (mechanical, complete for what the code uses).
      clingo already emits `info: atom does not occur in any rule head: p/n`.
      That IS the missing-reference detector. It needs two things to become
      useful: a way to tell a genuine SITUATION INPUT (`forbids`, `produced` --
      facts about the case being judged) from an unresolved reference, and a
      way to tell either from a declared dependency on ANOTHER CLAUSE. The
      module declares all three: `%% inputs:`, `%% requires:`, and everything
      else.

      ⭐ This is the check that was already firing and being ignored.
      `lifted_by_purpose/2` sat in a constraint body with no provider, making
      that constraint dead, and clingo said so on every single run.

      ⭐ L2 HAS A THIRD DECLARATION SITE: the CONCEPT TABLE. A clause's concepts
      are declared in `concepts.json` — written per run beside the `.lp` files
      by `phase_1/translate.py` (`schema.concept_rows`) — and the `.lp` carries
      only a POINTER header naming the signatures. A concept row declares its
      predicate exactly as `%% inputs:` and `%% requires:` do, so `collect()`
      takes the parsed rows AS DATA (`collect(paths, concepts=rows)`).

      ⛔ NOT by parsing the `%% concepts:` header. That was considered and
      rejected: it re-creates the regex-the-comments pattern the split exists
      to avoid (`resources/05_practice_from_ontology_projects.md` §2.3 — a
      published legal ontology put 60+ clause citations in `rdfs:comment`
      prose, and *"you cannot ask which classes derive from Article 5 without
      regexing English"*), and it throws away the gloss, the licence and the
      citation, which are the fields that make the table worth having.

      ⚠️ Running with NO table is the failure mode to avoid, not a neutral
      default: every declared concept then reads as undeclared and the tool
      floods with false positives that look exactly like real findings. That is
      what it did on the first live run — 7 UNRESOLVED REFERENCE(S), all seven
      declared. So the absence is itself reported (`concept-table-absent`) and
      the CLI says which table it loaded, or that it loaded none.

CHECKS, and the id each Finding carries

  clingo-error         the program does not COMPILE. Must be loud: link()
                       used to print `✅ no unresolved references` on a file
                       clingo had refused outright.
  unresolved-reference head-less, and declared neither as an input, nor as a
                       requirement, nor as a row in the concept table. error.
  concept-declared     head-less and declared by the concept table. note --
                       the counterpart of `situation-input`, so a name that
                       stops being an error stays VISIBLE.
  concept-table-absent modules declare concepts and no table was supplied.
                       note.
  concept-not-in-table D4b-3 / problem #1: a module points at a concept the
                       table has no row for, so its gloss, licence and citation
                       cannot be recovered. error.
  concept-multi-gloss  D4b-3 / problem #9: one signature, two definitions.
                       note, and a CANDIDATE by construction -- 03_pipeline.md
                       Part 1 #9 measures 46 of 228 reused names (20%) carrying
                       more than one definition, so a second gloss is the
                       ORDINARY rate for this task, not a defect.
  requires-unprovided  declared in `%% requires:`, no provider in this link
                       scope. NOT an error -- at single-module scope a
                       `requires` predicate is head-less BY DESIGN.
  rule-shape           a `%% forbid-body: X <- Y` declaration is broken.
  closure-missing      an act class governed with no `%% closure:` declaration.
  closure-conflict     two modules commit the same act class to CEPA and CNPA.
  beats-cycle          Problem #17: a cyclic superiority relation.

Usage:
    python3 link.py <clause.lp> [more.lp ...]        # link-check
    python3 link.py --self-test                      # no network, no cost
    python3 link.py --suggest m0255                  # what does the anchor graph say?
"""

import contextlib
import dataclasses
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
EXP = os.path.join(REPO, "semi-formal-experiment")
PY = os.path.join(EXP, ".venv", "bin", "python")
CLAUSES_JSON = os.path.join(EXP, "modelspec_clauses.json")
#: the concept dictionary, written per run beside the `.lp` files.
#: ⚠️ Kept in step with `phase_1/translate.py`'s `CONCEPT_TABLE` by name only;
#: link.py must not import the phase_1 tree (it would drag pydantic into a
#: module whose whole point is that it needs nothing).
CONCEPT_TABLE = "concepts.json"

ANCHOR = re.compile(r"\]\(#([a-zA-Z0-9_\-]+)\)")
FORBID = re.compile(r"^%%\s*forbid-body\s*:\s*(\w+)\s*<-\s*(\w+)\s*$", re.M)
# clingo's "atom does not occur in any rule head" prints the atom as it would be
# WRITTEN -- `forbids(P,M)`, not `forbids/2` -- so this captures name + raw args
# and _atom_id() below turns that into a name/arity identity, matching header().
# The message can wrap across the colon; the `\n?` already tolerated that.
NO_HEAD = re.compile(
    r"atom does not occur in any rule head:\s*\n?\s*"
    r"([a-z_][A-Za-z0-9_]*)(\([^)]*\))?"
)
#: Header lines. `requires` was missing from this alternation, which made every
#: legitimate cross-clause dependency read as an unresolved reference; `acts`,
#: `concepts` and `closure` were missing, which made the forced per-act closure
#: declaration unenforceable. `provides` is GONE -- see the note on
#: defined_predicates().
#
# ⚠️ `[^\S\n]` (blank-but-not-newline), never `\s`. With `\s*` after the colon
# an EMPTY header — `%% requires:` on a module that needs nothing, which is
# most of them — matched across the line break and captured the NEXT header's
# value, so `%% requires:\n%% inputs: new_material/1` read as
# `requires = {new_material/1}`. Found by the self-test's own control case.
HDR = re.compile(
    r"^%%[^\S\n]*(inputs|requires|acts|concepts|closure|clause)"
    r"[^\S\n]*:[^\S\n]*(.*)$", re.M)
#: `%% clause: m0255   section: transformation_exception   kind: conditional`
#: is one line carrying three fields. Parsing it as one opaque value put the
#: whole string under `clause` and left `section` and `kind` unreadable.
CLAUSE_HDR = re.compile(
    r"^%%[^\S\n]*clause[^\S\n]*:[^\S\n]*(\S+)"
    r"(?:[^\S\n]+section[^\S\n]*:[^\S\n]*(\S+))?"
    r"(?:[^\S\n]+kind[^\S\n]*:[^\S\n]*(\S+))?", re.M)
#: `%% closure: produce = cepa   % <reason>`
CLOSURE_HDR = re.compile(
    r"^%%[^\S\n]*closure[^\S\n]*:[^\S\n]*([a-z][A-Za-z0-9_]*)"
    r"[^\S\n]*=[^\S\n]*(cepa|cnpa|unclear)\b", re.M)
#: a name/arity signature, as `requires` / `inputs` / `concepts` write it
SIG = re.compile(r"[a-z][A-Za-z0-9_]*/\d+")
#: clingo's own refusals. `python -m clingo` ALWAYS exits 0 -- pyclingo's
#: __main__ catches the RuntimeError and prints `*** ERROR:` -- so the return
#: code alone cannot be trusted and the text has to be read as well.
#: `note:` lines carry the diagnosis ("'A' is unsafe") that the error
#: line only points at; dropping them fed the repair loop a message with
#: the location but not the cause (adversarial review 2026-08-10).
CLINGO_ERR = re.compile(r"^.*\b(?:error|note)\b\s*:.*$", re.M)
CLINGO_OK_RC = (0, 10, 20, 30)
#: ⭐ THE SHARED PREAMBLE, and every line of it. `phase_1/schema.py`'s
#: `render_lp` emits exactly these two lines into EVERY module that carries an
#: ontology fact (the ablation guard for deontic_probe/FINDINGS.md §4.6). At
#: single-module scope they are inert; at CORPUS scope clingo refuses the
#: second `#const onto = on.` as a constant REDEFINITION and analyses NOTHING
#: — first measured on the 14-module graph-node corpus, 2026-08-11
#: (`resolve_runs/graph_v2/STEPS34_READINESS.md` gap 1). Both lines are
#: idempotent by construction — N identical copies mean exactly what one
#: means — so a corpus link keeps the first copy and drops the repeats.
#: ⛔ ONLY these exact lines. A `#const` collision that is NOT this preamble
#: is a genuine cross-module redefinition and must still surface as the
#: clingo error it is; dedupe_shared_preamble() never touches it.
#: ⚠️ Kept in step with `render_lp` by TEXT, not by import — link.py must not
#: import the phase_1 tree (see CONCEPT_TABLE above). `test_link.py` pins the
#: correspondence by rendering real modules through the contract.
SHARED_PREAMBLE = ("#const onto = on.", "o :- onto = on.")


# ==========================================================================
#  Findings
# ==========================================================================

@dataclasses.dataclass(frozen=True)
class Finding:
    """One structured result from `collect()`.

    ⛔ DELIBERATELY CARRIES NO SUGGESTED FIX AND NO EXPECTED VALUE.
    These findings feed a stage-2 repair prompt, and stage 1 is denied the
    expected verdicts. A `fix=` or `expected=` field would put the answer into
    the prompt that is supposed to produce it, and every later measurement of
    whether the repair worked would be measuring the hint instead. A Finding
    says WHAT IS THE CASE and WHERE; what to do about it is not its business.
    """

    check_id: str          #: stable id -- `checks.py` will key off this
    severity: str          #: "error" (exit 1) or "note" (visible, exit 0)
    where: str             #: file basename, or a comma-joined list for set-wide
    message: str           #: one human sentence, no fix in it


# ==========================================================================
#  A small ASP reader
# ==========================================================================
#
# ⚠️ The regexes this replaced could not read a single rule stage 1 emits.
# `RULE = r"^\s*([a-z_]\w*)\s*\(([^)]*)\)\s*:-(.*?)\.\s*$"` fails on
#
#     asserts(m0255, forbid, produce(M)) :- new_material(M).   % [T] m0255
#
# twice over: `[^)]*` stops at the first `)`, which is the one inside the
# compound act term, and the trailing licence comment defeats the `\.\s*$`
# anchor. `RULE.findall` returned the EMPTY LIST on real output, so every
# head-shaped check downstream was vacuous rather than wrong. Still
# regex-free-ish and still not a real ASP parser -- but it is paren-aware and
# comment-aware, which is what this corpus needs.

def _strip_comment(line):
    """Drop `% ...` to end of line, respecting quoted constants."""
    out, quoted = [], False
    for ch in line:
        if ch == '"':
            quoted = not quoted
        if ch == "%" and not quoted:
            break
        out.append(ch)
    return "".join(out)


def _split_top(s, sep):
    """Split on `sep` at paren/brace/bracket depth 0, outside quotes."""
    parts, buf, depth, quoted, i = [], [], 0, False, 0
    while i < len(s):
        ch = s[i]
        if ch == '"':
            quoted = not quoted
        if not quoted:
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            elif depth == 0 and s.startswith(sep, i):
                parts.append("".join(buf))
                buf = []
                i += len(sep)
                continue
        buf.append(ch)
        i += 1
    parts.append("".join(buf))
    return parts


def statements(text):
    """Comment-free ASP statements, one per `.` at depth 0."""
    clean = "\n".join(_strip_comment(ln) for ln in text.splitlines())
    return [s.strip() for s in _split_top(clean, ".") if s.strip()]


def _parse_atom(s):
    """`asserts(m0255, forbid, produce(M))` -> ('asserts', [3 args])."""
    s = s.strip()
    m = re.match(r"^([a-z_][A-Za-z0-9_]*)\s*(\(.*\))?$", s, re.S)
    if not m:
        return None, []
    name, argstr = m.group(1), m.group(2)
    if not argstr:
        return name, []
    return name, [a.strip() for a in _split_top(argstr[1:-1], ",")]


def rules(text):
    """(head_name, head_args, body) for every rule. Constraints (`:- body.`)
    and directives (`#const ...`) are skipped -- neither derives anything."""
    out = []
    for st in statements(text):
        if st.startswith("#"):
            continue
        parts = _split_top(st, ":-")
        if len(parts) < 2:
            continue
        head, body = parts[0], ":-".join(parts[1:])
        if not head.strip():
            continue
        name, args = _parse_atom(head)
        if name:
            out.append((name, args, body.strip()))
    return out


def facts(text):
    """(name, args) for every unconditional fact."""
    out = []
    for st in statements(text):
        if st.startswith("#") or len(_split_top(st, ":-")) > 1:
            continue
        name, args = _parse_atom(st)
        if name:
            out.append((name, args))
    return out


def body_predicates(body):
    """Predicate names a body DEPENDS ON.

    Both forms: `p(X)` in predicate position, and a bare 0-arity atom standing
    as its own conjunct. Deliberately NOT every lowercase token -- the old
    `re.search(r"\\b%s\\b" % banned, body)` also matched a constant sitting in
    an argument slot, so `policy_class(P, restricted)` counted as a dependency
    on `restricted`.
    """
    names = set(re.findall(r"(?<![A-Za-z0-9_])([a-z][A-Za-z0-9_]*)\s*\(", body))
    for conj in _split_top(body, ","):
        c = conj.strip()
        if c.startswith("not "):
            c = c[4:].strip()
        if re.fullmatch(r"[a-z][A-Za-z0-9_]*", c):
            names.add(c)
    return names


def _arity(args):
    return len(args)


def _atom_id(name, parens):
    """`('forbids', '(P,M)')` -> `'forbids/2'`. Mirrors the `%% inputs:` /
    `%% requires:` header format so the two can be compared by identity."""
    inner = parens[1:-1] if parens else ""
    return f"{name}/{0 if not inner.strip() else len(_split_top(inner, ','))}"


def defined_predicates(text):
    """name/arity for every predicate this file's rule heads or facts define.

    ⚠️ NO LONGER checked against a `%% provides:` declaration -- see collect().
    It is now the PROVIDER INDEX: what a link set can satisfy a `%% requires:`
    entry with.
    """
    out = set()
    for name, args, _body in rules(text):
        out.add(f"{name}/{_arity(args)}")
    for name, args in facts(text):
        out.add(f"{name}/{_arity(args)}")
    return out


# ==========================================================================
#  Headers
# ==========================================================================

def _split_top_level(text, sep=","):
    """Split on `sep` only at parenthesis depth zero.

    A term list is not a comma-separated string: `f(a, b), g` is two items, not
    three. See the `%% acts:` comment in `header` for what the flat split cost.
    """
    out, depth, buf = [], 0, []
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == sep and depth == 0:
            if "".join(buf).strip():
                out.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if "".join(buf).strip():
        out.append("".join(buf).strip())
    return out


def header(path):
    """Parse a module's `%%` headers.

    Signature sets (`inputs`, `requires`, `concepts`) are kept as
    `name/arity`, not just `name` -- a declared input at one arity must NOT
    swallow a mismatch at any other arity of the same name. See STATE.md / the
    link.py bugfix note: this used to strip the arity and matched by name only,
    so `%% inputs: forbids/2` silently absorbed a body's `forbids/3`.
    """
    txt = open(path, encoding="utf-8").read()
    out = {"inputs": set(), "requires": set(), "acts": set(),
           "concepts": set(), "closure": {}, "forbid_body": []}

    m = CLAUSE_HDR.search(txt)
    if m:
        out["clause"] = m.group(1)
        if m.group(2):
            out["section"] = m.group(2)
        if m.group(3):
            out["kind"] = m.group(3)

    for key, val in HDR.findall(txt):
        if key in ("inputs", "requires"):
            out[key] = {t.strip() for t in val.split(",") if t.strip()}
        elif key == "concepts":
            # `%% concepts: a/1, b/2   (glosses in the concept table, not here)`
            # -- the trailing parenthetical is prose, so take the signatures.
            out["concepts"] = set(SIG.findall(val))
        elif key == "acts":
            # ⛔ NOT a flat comma split. An act may carry arguments, and
            # `respond(CoT, Input, Outputs, Seq)` split on every comma became
            # four act classes. Three were fragments, none had a closure
            # declaration, and `closure-missing` is an ERROR -- so the model
            # was sent back to fix acts it never wrote, under a message reading
            # `governs act class(es) CoT), Input), Outputs), Seq)`. Found on a
            # held-out run; a spurious error is indistinguishable from a real
            # one from inside the repair loop.
            out["acts"] = set(_split_top_level(val))

    for act_class, closure in CLOSURE_HDR.findall(txt):
        out["closure"][act_class] = closure
    out["forbid_body"] = FORBID.findall(txt)
    return out


# ==========================================================================
#  The concept table — DATA, not a comment
# ==========================================================================
#
# `schema.concept_rows()` writes one row per concept:
#
#     {"concept": "political_content/1", "clause_id": "m0217", "gloss": "...",
#      "licence": "textual", "cites": "m0217", "inference": null}
#
# `concept` is already a name/arity signature, so it compares by identity
# against `%% inputs:` / `%% requires:` and against `_atom_id()`.

def load_concept_table(path):
    """Read one `concepts.json`. Malformed is LOUD, never an empty table.

    ⚠️ Returning `[]` on a file that failed to parse would put this module
    straight back into the defect it exists to close: no declarations, so every
    concept reads as an unresolved reference, with nothing saying why.
    """
    rows = json.load(open(path, encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError(f"{path}: expected a list of concept rows, "
                         f"got {type(rows).__name__}")
    for i, r in enumerate(rows):
        if not isinstance(r, dict) or not str(r.get("concept") or "").strip():
            raise ValueError(f"{path}: row {i} has no `concept` signature")
    return rows


def discover_concept_table(paths):
    """Find `concepts.json` beside the `.lp` files.

    Returns `(rows_or_None, loaded_paths, dirs_with_no_table)`. `None` — not
    `[]` — when nothing was found, so a caller can tell "no table" from "a
    table declaring nothing".
    """
    dirs = []
    for p in paths:
        d = os.path.dirname(os.path.abspath(p))
        if d not in dirs:
            dirs.append(d)
    rows, loaded, missing = [], [], []
    for d in dirs:
        f = os.path.join(d, CONCEPT_TABLE)
        if os.path.isfile(f):
            rows.extend(load_concept_table(f))
            loaded.append(f)
        else:
            missing.append(d)
    return (rows if loaded else None), loaded, missing


def load_clauses():
    d = json.load(open(CLAUSES_JSON, encoding="utf-8"))
    rows = d if isinstance(d, list) else d["clauses"]
    return {r["id"]: r for r in rows}


def suggest(clause_id):
    """L1: which sections does this clause's own TEXT point at?"""
    rows = load_clauses()
    r = rows.get(clause_id)
    if not r:
        print(f"no such clause: {clause_id}")
        return 1
    targets = sorted(set(ANCHOR.findall(r["quote"])))
    secs = {}
    for c in rows.values():
        secs.setdefault(c["section_id"], []).append(c["id"])
    print(f"{clause_id}  [section: {r['section_id']}]")
    print(f"  text: {r['quote'][:150]}...")
    if not targets:
        print("  L1: no anchor references in the text "
              "(does NOT mean no dependencies -- see L2)")
        return 0
    print(f"  L1: {len(targets)} anchor reference(s):")
    for t in targets:
        ids = secs.get(t)
        print(f"    #{t:28} -> " +
              (f"section exists, {len(ids)} clauses: {', '.join(ids[:8])}"
               if ids else "⛔ UNRESOLVED: no section with this id"))
    return 0


# ==========================================================================
#  The checks
# ==========================================================================

def _check_rule_shape(paths, texts):
    """`%% forbid-body: X <- Y` -- no rule deriving X may depend on Y.

    ⛔ THIS WAS SILENTLY VACUOUS. The old test was `if h == head`, comparing
    the declaration's X against the rule's HEAD PREDICATE. Under the fixed
    vocabulary the head predicate is always `asserts` / `beats` / `defines`, so
    X (a STATUS like `permit`) could never match one and a module that plainly
    violated its own declaration reported ZERO violations and exited 0.

    X is therefore read TWO ways, and either satisfies the declaration:
      * a STATUS  -- the second argument of `asserts/3`, the new contract
      * a RELATION name -- the head predicate, which is what the hand-written
        m0255.lp means by `lifted <- purpose`

    Scope is the whole link set, not one file: a forbid-body declaration is a
    claim about the RULE SET, and a rule in another linked module derives the
    same status just as effectively.
    """
    out = []
    declarations = []
    for p in paths:
        for head, banned in header(p)["forbid_body"]:
            declarations.append((p, head, banned))
    for decl_path, head, banned in declarations:
        for p in paths:
            for name, args, body in rules(texts[p]):
                derived = {name}
                if name == "asserts" and len(args) >= 2:
                    derived.add(args[1].strip())        # the STATUS argument
                if head not in derived:
                    continue
                if banned not in body_predicates(body):
                    continue
                where = os.path.basename(p)
                origin = ("" if p == decl_path
                          else f" (declared in {os.path.basename(decl_path)})")
                out.append(Finding(
                    "rule-shape", "error", where,
                    f"a rule deriving `{head}` depends on `{banned}` in its "
                    f"body, which `%% forbid-body: {head} <- {banned}` "
                    f"declares it may not{origin}"))
    return out


def _check_closure(paths):
    """The FORCED per-act default-closure declaration.

    03_pipeline.md open question 1, CLOSED: *"a forced, per-act default-closure
    declaration, enforced in link.py"*. Two conditions:

      closure-missing   an act class the module governs with no declaration.
                        An absent declaration reads as CEPA silently, and
                        `open` and `cepa` are bit-identical, so nothing records
                        that a commitment was made.
      closure-conflict  one module commits an act class to CEPA and another to
                        CNPA. The contradiction probe found the verdict FLIPS
                        on this, so a disagreement is a substantive finding.

    ⚠️ TWO LIMITS, stated rather than hidden.

    * `schema.py` already forces a declaration per generated module, so
      `closure-missing` can only fire on hand-written or pre-contract modules.
    * It reads the `%% acts:` HEADER, which is where the contract declares an
      act class. `contradiction_probe/doc.lp` governs nine act classes through
      `act/1` FACTS and declares no closure for any of them, and this check
      does not see that. Reading `act/1` would conflate a clause's scope with
      the CASE's act inventory, which is exactly the separation render_lp's
      comment insists on -- so the gap is left open and named.
    """
    out, declared = [], {}
    for p in paths:
        h = header(p)
        governed = {a.split("(")[0].strip() for a in h["acts"] if a.strip()}
        missing = sorted(governed - set(h["closure"]))
        if missing:
            out.append(Finding(
                "closure-missing", "error", os.path.basename(p),
                f"governs act class(es) {', '.join(missing)} with no "
                f"`%% closure:` declaration; a module that declares none is "
                f"read as CEPA -- silence permits -- without recording it"))
        for act_class, closure in h["closure"].items():
            declared.setdefault(act_class, {}).setdefault(closure, []).append(
                os.path.basename(p))

    for act_class, byval in sorted(declared.items()):
        if len(byval) < 2:
            continue
        detail = "; ".join(f"{v} in {', '.join(sorted(f))}"
                           for v, f in sorted(byval.items()))
        hard = {"cepa", "cnpa"} <= set(byval)
        out.append(Finding(
            "closure-conflict", "error" if hard else "note",
            ", ".join(sorted({f for fs in byval.values() for f in fs})),
            f"act class `{act_class}` is declared with more than one default "
            f"closure across this link set: {detail}"))
    return out


def _check_beats_cycle(paths, texts):
    """Problem #17 -- a cyclic `beats` relation is silently WRONG.

    03_pipeline.md Part 1 #17: *"If clause A is declared to beat B and B to
    beat A, a defeat-based encoding produces a confident wrong answer rather
    than an error."* `deontic_probe/kernel.lp:68-70` carries the transitive
    closure guard, but a bare module never loads it, and `schema.py` rejects
    only the trivial self-loop `winner == loser`. Nothing else detects this.

    Reads GROUND `beats` facts in both arities: `beats(W, L)` (kernel/doc.lp)
    and `beats(Sayer, W, L)` (the fixed vocabulary).

    ⚠️ LIMIT, stated rather than hidden: a `beats` RULE with a variable winner
    -- m0255's `beats(m0255, R, m0252) :- content_policy_rule(R)` -- is not
    resolved here. Its edges depend on what grounds, which is a solving
    question, not a static one. The check is a lower bound on cycles.
    """
    edges, origin = {}, {}
    for p in paths:
        for name, args in facts(texts[p]):
            if name != "beats" or len(args) not in (2, 3):
                continue
            w, l = (args[0], args[1]) if len(args) == 2 else (args[1], args[2])
            w, l = w.strip(), l.strip()
            if re.match(r"^[A-Z_]", w) or re.match(r"^[A-Z_]", l):
                continue                       # not ground -- see the note
            edges.setdefault(w, set()).add(l)
            origin.setdefault((w, l), set()).add(os.path.basename(p))

    out, seen, stack, on_stack = [], set(), [], set()

    def walk(node):
        seen.add(node)
        stack.append(node)
        on_stack.add(node)
        for nxt in sorted(edges.get(node, ())):
            if nxt in on_stack:
                cyc = stack[stack.index(nxt):] + [nxt]
                where = sorted({f for i in range(len(cyc) - 1)
                                for f in origin.get((cyc[i], cyc[i + 1]), ())})
                out.append(Finding(
                    "beats-cycle", "error", ", ".join(where),
                    f"the `beats` relation is cyclic: "
                    + " beats ".join(cyc)
                    + " -- a defeat-based encoding returns a confident answer "
                      "on a cyclic superiority relation rather than an error"))
            elif nxt not in seen:
                walk(nxt)
        stack.pop()
        on_stack.discard(node)

    for node in sorted(edges):
        if node not in seen:
            walk(node)
    return out


def _check_concepts(paths, headers, concepts):
    """The concept table's own checks. Returns `(findings, sig -> clause_ids)`.

    ⭐ The second return value is the DECLARATION SET the unresolved-name check
    subtracts. That is the whole point of passing the table as data: a row
    declares its predicate, exactly as a `%% inputs:` entry does.

    Three conditions, all keyed off the table and none off the `%% concepts:`
    header's content:

      concept-table-absent  modules declare concepts, no table was supplied.
      concept-not-in-table  D4b-3 / problem #1. A module's header points at a
                            signature the table has no row for. The pointer is
                            the only thing the `.lp` carries, so a dangling one
                            means the gloss, the licence and the citation are
                            unrecoverable for that name.
      concept-multi-gloss   D4b-3 / problem #9. One signature, two definitions.

    ⚠️ SCOPE, stated rather than hidden. The multi-gloss check ranges over the
    table AS SUPPLIED — for the CLI, the union of every `concepts.json` beside
    the linked files. It is therefore a LOWER BOUND: two runs that disagree
    about `user/1` are only caught if both tables are in the same link. The
    corpus-wide half is `DEFERRED.md` D-3 level 3 and is still deferred.

    ⚠️ SECOND LIMIT. `concept-not-in-table` assumes the supplied table covers
    the whole link set. Linking files from two directories where only one
    carries a `concepts.json` would fire it on every concept of the uncovered
    modules; the CLI names the directories it found no table in, for exactly
    that reason.
    """
    out = []
    if concepts is None:
        declaring = [os.path.basename(p) for p in paths
                     if headers[p]["concepts"]]
        if declaring:
            out.append(Finding(
                "concept-table-absent", "note", ", ".join(declaring),
                f"{len(declaring)} module(s) in this link declare concepts in "
                f"a `%% concepts:` header and no concept table "
                f"(`{CONCEPT_TABLE}`) was supplied, so every concept they "
                f"declare is read below as undeclared"))
        return out, {}

    where = {}
    glosses = {}
    for row in concepts:
        sig = str(row.get("concept") or "").strip()
        if not sig:
            continue
        cid = str(row.get("clause_id") or "?")
        where.setdefault(sig, []).append(cid)
        glosses.setdefault(sig, {}).setdefault(
            " ".join(str(row.get("gloss") or "").split()), []).append(cid)

    for sig, by_gloss in sorted(glosses.items()):
        if len(by_gloss) < 2:
            continue
        cids = sorted({c for cs in by_gloss.values() for c in cs})
        detail = "; ".join(
            f"{', '.join(sorted(cs))} define{'' if len(set(cs)) > 1 else 's'} "
            f"it as \"{g}\"" for g, cs in sorted(by_gloss.items()))
        out.append(Finding(
            "concept-multi-gloss", "note", ", ".join(cids),
            f"`{sig}` carries {len(by_gloss)} different definitions in the "
            f"concept table supplied to this link — {detail} — which is "
            f"problem #9, same name different meanings. ⚠️ A CANDIDATE, not a "
            f"defect: 03_pipeline.md Part 1 #9 measures 46 of 228 reused names "
            f"(20%) carrying more than one definition, so a second definition "
            f"is the ordinary rate for this task"))

    for p in paths:
        missing = sorted(headers[p]["concepts"] - set(where))
        if not missing:
            continue
        out.append(Finding(
            "concept-not-in-table", "error", os.path.basename(p),
            "declares " + ", ".join(f"`{m}`" for m in missing)
            + f" in its `%% concepts:` header, and the concept table supplied "
              f"to this link has no row for "
            + ("it" if len(missing) == 1 else "them")
            + " — the header is a pointer, so the gloss, the licence and the "
              "cited clause cannot be recovered"))
    return out, where


def dedupe_shared_preamble(paths, tmpdir):
    """Copies of `paths` keeping only the FIRST copy of each SHARED_PREAMBLE
    line across the whole set. Returns `(new_paths, lines_removed)`.

    This is the corpus-assembly half of the emission contract: `render_lp`
    serves the single-module path (checks.py stage 2, per-module run
    artifacts, byte-identical), and the link layer owns making N modules
    loadable as ONE program. Basenames are preserved so findings still name
    the module; each copy sits in its own numbered subdir so equal basenames
    from different run directories cannot collide.

    ⛔ Nothing else is touched. A non-preamble `#const` redefinition — real
    cross-module link glue can write one; stage 1 cannot — passes through
    unchanged and still errors in clingo.
    """
    out, removed, seen = [], 0, set()
    for i, p in enumerate(paths):
        kept = []
        for ln in open(p, encoding="utf-8").read().splitlines(True):
            s = ln.strip()
            if s in SHARED_PREAMBLE:
                if s in seen:
                    removed += 1
                    continue
                seen.add(s)
            kept.append(ln)
        d = os.path.join(tmpdir, str(i))
        os.makedirs(d, exist_ok=True)
        q = os.path.join(d, os.path.basename(p))
        with open(q, "w", encoding="utf-8") as f:
            f.writelines(kept)
        out.append(q)
    return out, removed


def _check_clingo(paths):
    """Does the program COMPILE?

    ⛔ On a file clingo REFUSES (`error: unsafe variables in ...`) this used to
    print `✅ no unresolved references` and return 0 -- a silent pass on a file
    that does not run at all.

    ⚠️ `python -m clingo` ALWAYS exits 0: pyclingo's `__main__` catches the
    grounding RuntimeError and prints `*** ERROR: (pyclingo): ...`. So checking
    the return code alone -- the obvious fix -- would have changed NOTHING.
    Both the return code and the error text are read.
    """
    r = subprocess.run([PY, "-m", "clingo"] + list(paths) + ["--outf=3"],
                       capture_output=True, text=True, cwd=EXP)
    blob = r.stdout + r.stderr
    errs = [ln.strip() for ln in CLINGO_ERR.findall(blob)]
    findings = []
    if errs or r.returncode not in CLINGO_OK_RC:
        findings.append(Finding(
            "clingo-error", "error",
            ", ".join(os.path.basename(p) for p in paths),
            "clingo refused this program, so nothing below was actually "
            "analysed: " + (" | ".join(errs[:4]) if errs
                            else f"exit code {r.returncode}")))
    return findings, blob


def collect(paths, concepts=None):
    """Run every check and return structured `Finding` records. Prints nothing.

    This is the data half of the old `link()`. `checks.py` will consume it;
    `report()` below is the only presentation.

    `concepts` is the parsed CONCEPT TABLE — the rows of a run's
    `concepts.json`, as `schema.concept_rows()` writes them — or None when no
    table was supplied. A row DECLARES its predicate for the unresolved-name
    check, exactly as `%% inputs:` and `%% requires:` do.

    ⛔ The `%% concepts:` header is used only as a POINTER (which signatures
    this module claims), never as the declaration itself. Reading the
    declaration off the header would re-create the regex-the-comments pattern
    the table exists to avoid, and would throw away the gloss, the licence and
    the citation — the three fields the D4b-3 checks below are built on.
    """
    paths = list(paths)
    texts = {p: open(p, encoding="utf-8").read() for p in paths}
    headers = {p: header(p) for p in paths}
    findings = []

    # ---- 3. `provides` REMOVED, not repurposed -------------------------
    # `Module` has no `provides` field and `render_lp` emits no such header,
    # so the "declared-but-undefined provides" check could not fire on any
    # stage-1 output -- and its companion warning ("no `%% provides:` header --
    # cannot tell its interface from its internals") fired on EVERY module,
    # training the reader to ignore the tool's warnings. The contract now
    # states the interface in two directions instead: `%% requires:` says what
    # this module needs, `%% inputs:` says what the CASE supplies, and what it
    # provides is simply what it defines. defined_predicates() survives as the
    # provider index for the `requires` check.

    declared_inputs = set().union(*(h["inputs"] for h in headers.values())) \
        if paths else set()
    declared_requires = set().union(*(h["requires"] for h in headers.values())) \
        if paths else set()

    # ---- 1. requires: a dependency, not an unresolved reference --------
    # At single-module scope a `requires` predicate is head-less BY DESIGN.
    # Reporting it as unresolved destroys 03_pipeline.md Part 4 §2's three-way
    # diagnosis -- linkage / not yet translated / genuinely dead -- by folding
    # the first two into the third.
    #
    # ⚠️ HONEST LIMIT: link.py sees only the files it was given, so it can
    # separate "provided in this link scope" from "not provided here". Telling
    # `linkage` from `not yet translated` needs a provider index over the whole
    # translated corpus, which does not exist yet. So this is reported as one
    # non-error status naming the scope it was decided in, rather than as a
    # diagnosis it cannot actually make.
    provided = set()
    for p in paths:
        provided |= defined_predicates(texts[p])
    for sig in sorted(declared_requires - provided):
        findings.append(Finding(
            "requires-unprovided", "note",
            ", ".join(os.path.basename(p) for p in paths
                      if sig in headers[p]["requires"]),
            f"`{sig}` is declared in `%% requires:` and no module in this "
            f"link scope defines it"))

    concept_findings, concept_where = _check_concepts(paths, headers, concepts)
    findings += concept_findings
    declared_concepts = set(concept_where)

    findings += _check_rule_shape(paths, texts)
    findings += _check_closure(paths)
    findings += _check_beats_cycle(paths, texts)

    # ---- 2. corpus assembly: one program from N modules ----------------
    # At corpus scope the SHARED_PREAMBLE (see its comment) is deduped to one
    # copy before clingo sees the set; at single-module scope the file is
    # passed exactly as rendered. Only the clingo subprocess reads the deduped
    # copies — every static check above reads the artifacts as emitted.
    if len(paths) > 1:
        tmp = tempfile.mkdtemp(prefix="link_corpus_")
        try:
            clingo_paths, _removed = dedupe_shared_preamble(paths, tmp)
            clingo_findings, blob = _check_clingo(clingo_paths)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    else:
        clingo_findings, blob = _check_clingo(paths)
    findings += clingo_findings

    headless = {_atom_id(name, parens) for name, parens in NO_HEAD.findall(blob)}
    for sig in sorted(headless - declared_inputs - declared_requires
                      - declared_concepts):
        findings.append(Finding(
            "unresolved-reference", "error",
            ", ".join(os.path.basename(p) for p in paths),
            f"`{sig}` is used in a body, defined nowhere in this link scope, "
            f"and declared neither in `%% inputs:` nor in `%% requires:` nor "
            f"in the concept table"))
    # A name that stops being an error must not simply VANISH -- the same rule
    # that gives `%% inputs:` its `situation-input` note.
    for sig in sorted(headless & declared_concepts):
        findings.append(Finding(
            "concept-declared", "note",
            ", ".join(os.path.basename(p) for p in paths),
            f"`{sig}` is head-less and declared in the concept table by "
            f"{', '.join(sorted(set(concept_where[sig])))}"))
    for sig in sorted(headless & declared_inputs):
        findings.append(Finding(
            "situation-input", "note",
            ", ".join(os.path.basename(p) for p in paths),
            f"`{sig}` is head-less and declared as a situation input"))
    return findings


def report(findings, paths=None):
    """Print `collect()`'s findings. The only presentation in this module."""
    if paths is not None:
        print(f"linked {len(paths)} file(s): "
              f"{', '.join(os.path.basename(p) for p in paths)}")
    else:
        where = sorted({f.where for f in findings if f.where})
        print(f"linked: {', '.join(where) if where else '(no files)'}")

    def of(check_id):
        return [f for f in findings if f.check_id == check_id]

    inputs_seen = of("situation-input")
    if inputs_seen:
        sigs = sorted(f.message.split("`")[1] for f in inputs_seen)
        print(f"  situation inputs (expected head-less): {', '.join(sigs)}")

    concepts_seen = of("concept-declared")
    if concepts_seen:
        sigs = sorted(f.message.split("`")[1] for f in concepts_seen)
        print(f"  declared in the concept table (expected head-less): "
              f"{', '.join(sigs)}")

    for check_id, banner in (
            ("concept-table-absent",
             "⚠️  {n} MISSING CONCEPT TABLE — declared concepts will read as "
             "undeclared below:"),
            ("clingo-error", "⛔ {n} CLINGO ERROR(S) — the program does not compile:"),
            ("concept-not-in-table",
             "⛔ {n} module(s) POINTING AT A CONCEPT THE TABLE DOES NOT CARRY:"),
            ("concept-multi-gloss",
             "▫️  {n} CANDIDATE(S) — one name, more than one definition "
             "(problem #9; 20% is the measured ordinary rate):"),
            ("rule-shape", "⛔ {n} RULE-SHAPE violation(s):"),
            ("closure-missing", "⛔ {n} MISSING default-closure declaration(s):"),
            ("closure-conflict", "⛔ {n} CONFLICTING default-closure declaration(s):"),
            ("beats-cycle", "⛔ {n} CYCLIC `beats` relation(s) — problem #17:"),
    ):
        hits = of(check_id)
        if hits:
            print("  " + banner.format(n=len(hits)))
            for f in hits:
                print(f"      {f.where}: {f.message}")

    reqs = of("requires-unprovided")
    if reqs:
        print(f"  ▫️  {len(reqs)} DECLARED REQUIREMENT(S) with no provider in "
              f"this link scope (not an error — a `requires` predicate is "
              f"head-less by design):")
        for f in reqs:
            print(f"      {f.where}: {f.message}")

    unresolved = of("unresolved-reference")
    if not unresolved:
        if not of("clingo-error"):
            print("  ✅ no unresolved references")
    else:
        print(f"  ⛔ {len(unresolved)} UNRESOLVED REFERENCE(S) — "
              f"used in a body, defined nowhere, and not declared:")
        for f in unresolved:
            print(f"      {f.message}")
        print("\n  Each one is either (a) a missing `%% inputs:` or "
              "`%% requires:` declaration, or")
        print("  (b) a clause this translation depends on and does not include.")
        print("  A constraint whose body holds an unresolved atom is DEAD: it "
              "can never fire.")
    return 1 if any(f.severity == "error" for f in findings) else 0


def link(paths, concepts=None):
    """Backwards-compatible entry point: find the concept table, collect, report.

    ⚠️ THE TABLE STATUS IS ALWAYS PRINTED. Proceeding without one is not a
    neutral default — it is the defect this function was fixed for — so the
    output says which `concepts.json` it loaded, or that it loaded none.

    ⚠️ ... but the LOUD form is reserved for the case where it matters: a link
    set in which some module actually declares a concept. A warning that fires
    on every run trains the reader to ignore the tool's warnings, which is
    exactly how the old `no %% provides: header` message became invisible.
    """
    paths = list(paths)
    if concepts is None:
        concepts, loaded, missing = discover_concept_table(paths)
    else:
        loaded, missing = ["(supplied by the caller)"], []

    if loaded:
        print(f"concept table: {len(concepts)} row(s) from "
              f"{', '.join(loaded)}")
        if missing:
            print(f"  ⚠️  no {CONCEPT_TABLE} in {', '.join(missing)} — "
                  f"concepts declared by modules there will read as undeclared")
    elif any(header(p)["concepts"] for p in paths):
        print(f"⚠️  NO CONCEPT TABLE: no {CONCEPT_TABLE} beside these files "
              f"(looked in {', '.join(missing)}), and modules here declare "
              f"concepts. A concept is declared in the TABLE, not in the "
              f"`.lp`, so every one of them reads as undeclared below.")
    else:
        print(f"concept table: not found beside these files, and no module "
              f"declares a concept, so nothing in this link needs one")
    return report(collect(paths, concepts=concepts), paths=paths)


# ==========================================================================
#  Self-test
# ==========================================================================

def _run_captured(paths):
    """Call link() with stdout captured, for self-test assertions."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = link(paths)
    return rc, buf.getvalue()


#: A module in the shape `schema.render_lp` emits. ⚠️ The authoritative
#: fixtures are in `test_link.py`, where every module is built by validating a
#: dict through `phase_1/schema.py` and rendering it, so it cannot drift from
#: what stage 1 actually produces. These are hand-written copies of that shape
#: so `--self-test` stays a zero-dependency smoke check (no pydantic, no
#: import of the phase_1 tree).
def _module(clause_id, *, acts="", concepts="", requires="", inputs="",
            closure="", forbid_body="", body=""):
    hdr = [f"%% clause: {clause_id}   section: test   kind: conditional"]
    if acts:
        hdr.append(f"%% acts: {acts}")
    if concepts:
        hdr.append(f"%% concepts: {concepts}   (glosses in the concept table, "
                   f"not here)")
    hdr.append(f"%% requires: {requires}")
    hdr.append(f"%% inputs: {inputs}")
    if closure:
        hdr.append(f"%% closure: {closure}   % a test reason")
    if forbid_body:
        hdr.append(f"%% forbid-body: {forbid_body}")
    return "\n".join(hdr) + "\n" + body


def self_test():
    """No network, no API cost. Writes fixtures to a temp dir, runs the checks
    against them, and prints each check's condition and the reason it is
    supposed to fire -- per README.md's evidence discipline, a check that has
    never gone red is not a check. Exit 0 if every check passed, 1 otherwise."""
    tmp = tempfile.mkdtemp(prefix="link_selftest_")
    results = []

    def check(name, condition, reason):
        status = "PASS" if condition else "FAIL"
        print(f"  [{status}] {name}\n         reason: {reason}")
        results.append(bool(condition))

    def write(name, content):
        path = os.path.join(tmp, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def hit(paths, check_id, concepts=None):
        return [f for f in collect(paths, concepts=concepts)
                if f.check_id == check_id]

    def row(sig, clause_id, gloss):
        """One `concepts.json` row, in `schema.concept_rows()`'s shape."""
        return {"concept": sig, "clause_id": clause_id, "gloss": gloss,
                "licence": "textual", "cites": clause_id, "inference": None}

    try:
        # (a) ⭐ THE ORIGINALLY-VERIFIED BUG, KEPT DELIBERATELY. This is the
        # only surviving OLD-CONTRACT fixture. It is kept because what it
        # proves is contract-independent: `%% inputs:` is matched by
        # name/ARITY, so a declaration at one arity cannot swallow a mismatch
        # at another. That identity rule is unchanged by the new vocabulary,
        # and this is the shape in which it was originally caught. Its free-form
        # head `violation/1` is not something stage 1 can emit any more.
        p = write("a_swallowed.lp",
                  "%% clause: t003   section: test   kind: conditional\n"
                  "%% requires:\n"
                  "%% inputs: forbids/2\n"
                  "violation(M) :- forbids(P, M, urgent).\n")
        f = hit([p], "unresolved-reference")
        check("(a) forbids/3 in the body is not swallowed by declared forbids/2",
              len(f) == 1 and "forbids/3" in f[0].message,
              "body calls forbids(P,M,urgent) [arity 3]; header only declares "
              "forbids/2 -- name-only matching absorbs this, arity-aware "
              "matching must report forbids/3 unresolved")

        # (b) DEFECT 1. A declared `%% requires:` is head-less BY DESIGN at
        # single-module scope.
        p = write("b_requires.lp", _module(
            "t010", acts="produce(M)", closure="produce = cepa",
            requires="policy_class/2", inputs="new_material/1",
            body="asserts(t010, forbid, produce(M)) :- "
                 "new_material(M), policy_class(P, K).   % [T] t010\n"))
        check("(b1) a declared `requires` is NOT an unresolved reference",
              not hit([p], "unresolved-reference"),
              "policy_class/2 is declared in `%% requires:`; calling it "
              "unresolved collapses `linkage` and `not yet translated` into "
              "`genuinely dead` (03_pipeline.md Part 4 §2)")
        f = hit([p], "requires-unprovided")
        check("(b2) ... but it IS reported, as a distinct non-error status",
              len(f) == 1 and f[0].severity == "note"
              and "policy_class/2" in f[0].message,
              "an unmet requirement that is invisible is a link the reader "
              "never makes; it must be visible and must not be an error")

        p2 = write("b_provider.lp", _module(
            "t011", requires="", inputs="",
            body="policy_class(restricted_content, restricted).   % [T] t011\n"))
        check("(b3) ... and the status CLEARS once a provider is linked in",
              not hit([p, p2], "requires-unprovided"),
              "the control: a status that fires regardless of the link set "
              "pins nothing")

        # (c) DEFECT 2. The status is an ARGUMENT of asserts/3, never a head.
        p = write("c_shape.lp", _module(
            "t020", acts="produce(M)", closure="produce = cepa",
            inputs="new_material/1, purpose/2",
            forbid_body="permit <- purpose",
            body="asserts(t020, permit, produce(M)) :- "
                 "new_material(M), purpose(M, research).   % [T] t020\n"))
        f = hit([p], "rule-shape")
        check("(c1) forbid-body fires when the STATUS is derived from the ban",
              len(f) == 1 and "permit" in f[0].message
              and "purpose" in f[0].message,
              "`permit` is the 2nd argument of asserts/3, never a rule head; "
              "comparing it against the head predicate (always asserts/beats/"
              "defines) can NEVER match, and a plain violation reported zero")
        p = write("c_clean.lp", _module(
            "t021", acts="produce(M)", closure="produce = cepa",
            inputs="new_material/1", forbid_body="permit <- purpose",
            body="asserts(t021, permit, produce(M)) :- "
                 "new_material(M).   % [T] t021\n"))
        check("(c2) ... and stays silent on the same declaration, clean body",
              not hit([p], "rule-shape"),
              "the guard that must kill (c1): if deleting the rule-shape check "
              "leaves both green, the check is a constant")

        # (d) DEFECT 3. No `provides` machinery may survive.
        # ⚠️ NOT named `d_no_provides.lp`: report() echoes the file name, so a
        # fixture with `provides` in its name passes `"provides" not in out`
        # only by luck and fails once the name is printed. Match the MESSAGE.
        p = write("d_interface.lp", _module(
            "t030", acts="produce(M)", closure="produce = cepa",
            inputs="new_material/1",
            body="asserts(t030, forbid, produce(M)) :- "
                 "new_material(M).   % [T] t030\n"))
        rc, out = _run_captured([p])
        check("(d) a new-contract module produces no `provides` output at all",
              rc == 0 and "provides" not in out,
              "`Module` has no provides field and render_lp emits no such "
              "header, so the check could not fire on real input while its "
              "warning fired on every module")

        # (e) DEFECT 4. clingo refuses the file.
        p = write("e_unsafe.lp", _module(
            "t040", acts="produce(M)", closure="produce = cepa",
            inputs="new_material/1",
            body="asserts(t040, forbid, produce(M)) :- "
                 "new_material(X).   % [T] t040\n"))
        f = hit([p], "clingo-error")
        rc, out = _run_captured([p])
        check("(e) a file clingo REFUSES is a loud failure, not a clean report",
              len(f) == 1 and "unsafe" in f[0].message
              and rc == 1 and "no unresolved references" not in out,
              "M is unsafe, so clingo rejects the whole file; link() used to "
              "print `✅ no unresolved references` and return 0. ⚠️ `python -m "
              "clingo` exits 0 even then, so the return code alone is not the "
              "fix")

        # (f) DEFECT 5. Closure declarations.
        p = write("f_no_closure.lp", _module(
            "t050", acts="interject(W)", inputs="on_camera/1",
            body="asserts(t050, oblige, interject(W)) :- "
                 "on_camera(W).   % [T] t050\n"))
        f = hit([p], "closure-missing")
        check("(f1) an act class governed with no closure declaration",
              len(f) == 1 and "interject" in f[0].message,
              "an absent declaration reads as CEPA silently, and `open` and "
              "`cepa` are bit-identical, so nothing records the commitment")
        a = write("f_cepa.lp", _module(
            "t051", acts="produce(M)", closure="produce = cepa",
            inputs="new_material/1",
            body="asserts(t051, forbid, produce(M)) :- "
                 "new_material(M).   % [T] t051\n"))
        b = write("f_cnpa.lp", _module(
            "t052", acts="produce(M)", closure="produce = cnpa",
            inputs="new_material/1",
            body="asserts(t052, forbid, produce(M)) :- "
                 "new_material(M).   % [T] t052\n"))
        f = hit([a, b], "closure-conflict")
        check("(f2) two modules commit one act class to CEPA and to CNPA",
              len(f) == 1 and "produce" in f[0].message
              and "cepa" in f[0].message and "cnpa" in f[0].message,
              "the contradiction probe found the verdict FLIPS on the closure, "
              "so a disagreement is a substantive finding, not bookkeeping")
        check("(f3) ... and agreeing declarations stay silent",
              not hit([a, a], "closure-conflict"),
              "the guard that must kill (f2)")

        # (g) DEFECT 6. Problem #17.
        a = write("g_cycle_a.lp", _module(
            "t060", body="beats(t060, t060, t061).   % [T] t060\n"))
        b = write("g_cycle_b.lp", _module(
            "t061", body="beats(t061, t061, t060).   % [T] t061\n"))
        f = hit([a, b], "beats-cycle")
        check("(g1) a cyclic `beats` relation is detected",
              len(f) >= 1 and "t060" in f[0].message and "t061" in f[0].message,
              "problem #17: A beats B and B beats A produces a confident WRONG "
              "answer rather than an error; kernel.lp's guard is not loaded by "
              "a bare module and schema.py rejects only winner == loser")
        c = write("g_chain.lp", _module(
            "t062", body="beats(t062, t062, t060).   % [T] t062\n"))
        check("(g2) ... and an acyclic chain stays silent",
              not hit([a, c], "beats-cycle"),
              "the guard that must kill (g1)")

        # (i) ⭐ DEFECT 8, verified on the first live run. Seven concepts,
        # every one of them DECLARED in its module's `concepts` list — hence
        # in `concepts.json` — reported as UNRESOLVED REFERENCES, because the
        # `.lp` carries only a pointer header and link.py never read the table.
        p = write("i_concepts.lp", _module(
            "t070", acts="produce(M)", closure="produce = cepa",
            concepts="political_content/1, broad_audience/1",
            body="asserts(t070, permit, produce(M)) :- "
                 "political_content(M), broad_audience(M).   % [T] t070\n"))
        full = [row("political_content/1", "t070", "content that is political"),
                row("broad_audience/1", "t070", "for an unspecified audience")]
        check("(i1) a concept declared in the CONCEPT TABLE is not unresolved",
              not hit([p], "unresolved-reference", concepts=full),
              "the concept dictionary is `concepts.json`, not the `.lp`; "
              "without reading it every declared concept reads as undeclared "
              "and the tool floods with false positives")
        f = hit([p], "unresolved-reference", concepts=full[:1])
        check("(i2) ... and one the table does NOT carry still is",
              len(f) == 1 and "broad_audience/1" in f[0].message,
              "the guard that must kill (i1), and the one that kills the "
              "rejected fix as well: reading the `%% concepts:` HEADER would "
              "resolve this name too, because the header claims both")
        f = hit([p], "concept-not-in-table", concepts=full[:1])
        check("(i3) a header pointing at a concept with no table row is a "
              "finding of its own",
              len(f) == 1 and "broad_audience/1" in f[0].message
              and not hit([p], "concept-not-in-table", concepts=full),
              "D4b-3 / problem #1: the header is only a pointer, so a dangling "
              "one means the gloss, licence and citation are unrecoverable. "
              "The second clause is its control")
        f = hit([p], "concept-table-absent")
        check("(i4) running with NO table at all is reported, not silent",
              len(f) == 1 and not hit([write("i_bare.lp", _module(
                  "t071", body="defines(t071, a, b).\n"))],
                  "concept-table-absent"),
              "silently proceeding is the defect: every concept then reads as "
              "undeclared. The control is a module declaring no concepts, "
              "which must NOT acquire a warning -- a warning on every run is "
              "how the old `no %% provides:` message became invisible")

        # (j) D4b-3 / problem #9 -- same name, two definitions.
        f = hit([p], "concept-multi-gloss", concepts=[
            row("user/1", "t080", "the person interacting with the assistant"),
            row("user/1", "t081", "the party below the developer")])
        check("(j) one signature with two definitions is a CANDIDATE",
              len(f) == 1 and f[0].severity == "note" and "user/1" in f[0].message
              and "t080" in f[0].message and "t081" in f[0].message
              and not hit([p], "concept-multi-gloss", concepts=[
                  row("user/1", "t080", "the person interacting"),
                  row("user/1", "t081", "the person interacting")]),
              "problem #9, the dangerous twin of #8: two clauses say `user` "
              "and mean different things, and they link cleanly. ⚠️ note, not "
              "error -- 46 of 228 reused names (20%) carry more than one "
              "definition, so this is the ORDINARY rate. The control is the "
              "same name declared identically, which is reuse working")

        # (k) THE SHARED-PREAMBLE COLLISION, measured on the graph-node
        # corpus (STEPS34_READINESS.md gap 1). render_lp emits
        # `#const onto = on.` into every module carrying ontology facts, so
        # at corpus scope clingo refused the redefinition and analysed
        # NOTHING. collect() now dedupes exactly the SHARED_PREAMBLE lines
        # at multi-file scope — and nothing else.
        preamble = "\n".join(SHARED_PREAMBLE) + "\n"
        a = write("k_onto_a.lp", _module(
            "t090", inputs="raw/1",
            body=preamble + "cls_a(M) :- o, raw(M).   % [T] t090\n"))
        b = write("k_onto_b.lp", _module(
            "t091", inputs="raw/1",
            body=preamble + "cls_b(M) :- o, raw(M).   % [T] t091\n"))
        check("(k1) two modules sharing render_lp's ontology preamble link "
              "cleanly at corpus scope",
              not hit([a, b], "clingo-error"),
              "every ontology-bearing module carries `#const onto = on.`; "
              "without corpus-scope dedup clingo refuses the redefinition "
              "and the whole link analyses nothing")
        c = write("k_const_a.lp", _module(
            "t092", body=preamble + "#const depth = 1.\n"
            "defines(t092, term, x).   % [T] t092\n"))
        d = write("k_const_b.lp", _module(
            "t093", body=preamble + "#const depth = 2.\n"
            "defines(t093, term, y).   % [T] t093\n"))
        f = hit([c, d], "clingo-error")
        check("(k2) ... and a GENUINE non-preamble `#const` collision still "
              "errors",
              len(f) == 1 and "redefinition" in f[0].message,
              "the guard that must kill (k1): only the exact SHARED_PREAMBLE "
              "lines are idempotent by construction; deduping any other "
              "`#const` would silently paper over a real cross-module "
              "contradiction")

        # (h) DEFECT 7. collect() / report() split.
        fields = set(getattr(Finding, "__dataclass_fields__", {}))
        check("(h) a Finding carries no suggested fix and no expected value",
              fields == {"check_id", "severity", "where", "message"},
              "these findings feed a stage-2 repair prompt, and stage 1 is "
              "denied the expected verdicts; a `fix` or `expected` field puts "
              "the answer into the prompt meant to produce it")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    passed = sum(results)
    print(f"\n{passed}/{len(results)} self-test checks passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        raise SystemExit(2)
    if a[0] == "--self-test":
        raise SystemExit(self_test())
    if a[0] == "--suggest":
        raise SystemExit(suggest(a[1]))
    raise SystemExit(link([os.path.abspath(x) for x in a]))
