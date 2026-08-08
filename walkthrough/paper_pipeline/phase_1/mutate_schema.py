#!/usr/bin/env python3
"""⚠️ Guards are located by a distinctive PHRASE from their error message,
not by line number — line numbers drift on every edit. The trade is that
rewording an error message breaks the anchor, which the tool reports as an
ERROR (never as "no survivors"), so the coupling fails loudly rather than
silently under-reporting holes.

Mutation verifier for `test_schema.py`.

    semi-formal-experiment/.venv/bin/python \
        walkthrough/paper_pipeline/phase_1/mutate_schema.py

WHY THIS EXISTS. `test_schema.py`'s docstring says its 47 tests "were written
AFTER the fixes they cover, so they were never RED-in-time. Each one is instead
verified by MUTATION". Until this file existed that sentence described an
intention, not a fact — and a test that still passes when the code it pins is
deleted is pinning nothing.

`03_pipeline.md` Part 4 stage 9 is the same technique: corrupt a known-good
translation and check every check catches its class. ⭐ **The survivors are the
finding.**

HOW IT WORKS. For each guard — located STRUCTURALLY, as an `ast.Raise` node,
never by line number — we copy `schema.py` to a temp directory, delete that one
raise (replacing it with `pass`, so the surrounding `if` still evaluates and
does nothing), and run `test_schema.py` against the COPY. The real file is
never touched, and the run asserts its bytes are unchanged at the end.

Pointing the import at the copy is done with a one-line pytest plugin that
registers the mutated module in `sys.modules` before collection, so
`test_schema.py`'s own `import schema` resolves to it. `sys.path` order is not
relied on: `test_schema.py` inserts its own directory at position 0.

⚠️ THE FAILURE MODE THIS IS DESIGNED AGAINST. A mutator whose "every guard is
pinned" result is indistinguishable from "no mutation was actually applied".
This project has shipped that exact shape three times. So:

  * every mutation records the EXACT source text it expects to delete, and
    re-verifies it before deleting — a drifted anchor is a MutationError;
  * a mutation that cannot be applied, or whose run does not collect the same
    number of tests as the baseline, is reported as ERROR — a third status,
    never folded into "no tests died";
  * the baseline must be green through the SAME isolation path before any
    mutation runs;
  * ERRORs and SURVIVORs both make the process exit non-zero.

READING THE OUTPUT.
  ⭐ SURVIVOR — a guard nothing pins. The finding.
  killed by MANY tests — the guard may be load-bearing for the fixtures rather
    than for any assertion; entanglement, not coverage.
  a TEST that dies under many unrelated mutations — suspect: it may be failing
    for a reason other than the one it names. That is the defect that made
    sixteen checks in the sibling harness pass for the wrong reason, seen from
    the other side.
"""

import argparse
import ast
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_SCHEMA = HERE / "schema.py"
DEFAULT_TESTS = HERE / "test_schema.py"


class MutationError(RuntimeError):
    """A mutation could not be applied, or the harness itself is untrustworthy.

    Deliberately NOT a quiet skip. An unapplied mutation kills no test, and a
    tool that counted that as "no survivors" would report a hole as a pin.
    """


#: The floor from the brief: twenty guards that must each resolve to exactly
#: one `raise` site. Each value is a distinctive fragment of that raise's
#: SOURCE — reworded messages break loudly here rather than silently dropping
#: a mutation from the run.
#:
#: ⚠️ Guard 1 was REGROUNDED on 2026-08-07, not removed: its renderer
#: justification was disproved, but `_` in a term slot is a rule HEAD and clingo
#: calls that unsafe whatever the body binds. Its twin in `_check_body` — which
#: had the renderer ground and no other — IS gone; see the note in `ALSO`.
REQUIRED = {
    "1  _check_term / anonymous variable in a HEAD term slot":
        "contains an anonymous variable",
    "2  _check_term / variable with no body to bind it":
        "there are no conditions to bind",
    "3  Licensed / textual without a citation":
        "licence `textual` with no citation",
    "4  Licensed / assumed without a named inference":
        "licence `assumed` with no named inference",
    "5  Licensed / world that is not toggleable":
        "licence `world` but not toggleable",
    "6  Concept / no gloss":
        "concept {self.name!r} has no gloss",
    "7  OntologyFact / no gloss":
        "ontology atom {atom!r} has no gloss",
    "8  Module / requires and inputs overlap":
        "appear in BOTH",
    "9  Module / requires+inputs name/arity":
        "is not name/arity",
    "10 Module / body name nothing declares":
        "but nothing declares it",
    "11 Module / forced closure missing":
        "no default-closure declaration for act class",
    "12 Module / closure for an act class not governed":
        "closure declared for act class",
    "13 _check_body / BEHAVIOUR namespace":
        "crosses the two namespaces",
    "14 OntologyFact / RESERVED relation schema":
        "This block holds classification only",
    "15 ReadBack / slot count vs arg count":
        "`%` slot(s) but",
    "16 ReadBack / _BAD_IN_TEXT":
        "contains a newline, quote,",
    "17 validate / clause_id mismatch":
        "would carry two identities",
    "18 validate / citation not in known_clause_ids":
        "cites {item.cites!r}, which is not a clause",
    "19 Superiority / winner == loser":
        "a clause cannot beat itself",
    "20 Module / abstention carrying content":
        "abstained but `{name}` is non-empty",
}

#: Guards found beyond the brief's floor. The list was a floor, not a ceiling;
#: every one of these is also mutated, and these labels just make the table
#: readable. Anything discovered and not named here still gets mutated.
ALSO = {
    "_check_term / not a term at all": "is not a term. It must be a functor",
    "_check_body / empty body": "body is present but empty",
    "_check_body / newline or brace": "contains a newline or brace",
    "_check_body / trailing full stop": "carries a trailing full stop",
    # ⛔ RESTORED 2026-08-07, hours after being removed. The removal's ground
    # ("the renderer can cope") was evidenced against plain clingo and against
    # ASP2CNL, and was true of both — but the tool the design actually names is
    # xclingo, which dies on `_` in a body with an unsafe `#Anon` variable and
    # takes the whole link set's explanation with it. `test_schema.py`'s
    # replacement test RUNS xclingo rather than asserting the validator
    # complains, so the ground is now pinned instead of merely stated.
    "_check_body / anonymous variable": "anonymous variable",
    "Licensed / toggleable on a non-world fact": "toggleable is for `world` facts only",
    "ReadBack / empty read-back": "no read-back annotation",
    "Superiority / slot is not a clause id": "is not a clause id or a",
    "Concept / name is not a predicate name": "concept name {self.name!r} is not",
    "Concept / redeclares a reserved name": "belongs to the relation schema or the",
    "Concept / negative arity": "negative arity",
    "OntologyFact / BEHAVIOUR namespace": "is in the BEHAVIOUR namespace",
    "OntologyFact / gloss has a quote or brace": "ontology gloss for {atom!r} contains",
    "Concept / gloss has a quote or brace": "gloss contains a quote, ",
    "Closure / no reason": "has no reason — an unreasoned",
    "ForbidBody / not a bare predicate name": "is not a bare ",
    "Module / abstained with no reason": "abstained with no reason",
    "Module / translated but emitted nothing": "abstention that did not say so",
    "Module / translated with no claims": "translated with no `claims`",
    "Module / acts entry is not an act term": "is not an act term",
    "Module / assertion names an undeclared act": "which is not in `acts`",
    "Module / two closures for one act class": "two closure declarations for one",
    "Module / beats sayer is not this clause": "is not this clause and no body",
    "validate / pydantic errors re-raised": "join(parts)) from exc",
    "validate / beats slot not in the corpus": "beats {slot} {val!r} is not a clause",
    "json_schema / recursive $ref": "recursive $ref to",
}


# ==========================================================================
#  Locating guards
# ==========================================================================

@dataclass
class Mutation:
    name: str
    qual: str
    lineno: int          # 1-based, inclusive
    end_lineno: int      # 1-based, inclusive
    segment: str         # the EXACT source lines this mutation deletes
    label: str = ""

    def __str__(self):
        return self.label or self.name


def _qualnames(tree):
    """Map every node id to the dotted name of the scope containing it."""
    out = {}

    def walk(node, path):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                  ast.ClassDef)):
                walk(child, path + (child.name,))
            else:
                out[id(child)] = ".".join(path)
                walk(child, path)
        out[id(node)] = ".".join(path)
    walk(tree, ())
    return out


def _slug(segment):
    """A short human label from the raise's message text."""
    strings = re.findall(r'"([^"]*)"|\'([^\']*)\'', segment)
    text = " ".join(a or b for a, b in strings)
    text = re.sub(r"\s+", " ", text).strip()
    return (text[:52] + "…") if len(text) > 52 else (text or "<no message>")


def discover(src):
    """Every `raise` in `src`, as an applicable Mutation. Structural, not lines.

    Raises MutationError for any raise that does not sit alone on its own
    lines — deleting one would then take unrelated code with it, and a
    mutation that removes more than its guard proves nothing.
    """
    tree = ast.parse(src)
    quals = _qualnames(tree)
    lines = src.splitlines()
    muts, seen = [], Counter()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Raise):
            continue
        lo, hi = node.lineno, node.end_lineno
        head, tail = lines[lo - 1], lines[hi - 1]
        if head[:node.col_offset].strip():
            raise MutationError(
                f"line {lo}: `raise` shares its line with other code; "
                f"deleting it would remove more than the guard")
        if tail[node.end_col_offset:].strip():
            raise MutationError(
                f"line {hi}: code follows the `raise` on its last line")
        segment = "\n".join(lines[lo - 1:hi])
        if not segment.lstrip().startswith("raise "):
            raise MutationError(f"line {lo}: segment is not a raise: {segment!r}")
        qual = quals.get(id(node), "") or "<module>"
        seen[qual] += 1
        muts.append(Mutation(name=f"{qual}#{seen[qual]}", qual=qual,
                             lineno=lo, end_lineno=hi, segment=segment,
                             label=f"{qual}: {_slug(segment)}"))
    return muts


def label_for(mut):
    """Prefer the brief's own name for a guard, then ours, then the message."""
    for name, phrase in REQUIRED.items():
        if phrase in mut.segment:
            return name
    for name, phrase in ALSO.items():
        if phrase in mut.segment:
            return name
    return mut.label


def apply(src, mut):
    """Return `src` with `mut`'s raise replaced by `pass`.

    The anchor is re-verified against the source before anything is removed.
    A drifted anchor, an out-of-range span, a no-op edit or an unparseable
    result are all MutationError — never a silent pass-through.
    """
    lines = src.splitlines()
    if not (1 <= mut.lineno <= mut.end_lineno <= len(lines)):
        raise MutationError(
            f"{mut.name}: lines {mut.lineno}-{mut.end_lineno} are outside a "
            f"{len(lines)}-line file — the anchor has drifted")
    found = "\n".join(lines[mut.lineno - 1:mut.end_lineno])
    if found != mut.segment:
        raise MutationError(
            f"{mut.name}: the source at lines {mut.lineno}-{mut.end_lineno} is "
            f"not what this mutation expects.\n  expected: {mut.segment!r}\n"
            f"  found:    {found!r}\nThe guard moved or was reworded; the "
            f"mutation was NOT applied and this run proves nothing about it")
    indent = re.match(r"\s*", lines[mut.lineno - 1]).group()
    out_lines = (lines[:mut.lineno - 1]
                 + [f"{indent}pass  # MUTATED: guard deleted by mutate_schema.py"]
                 + lines[mut.end_lineno:])
    out = "\n".join(out_lines) + ("\n" if src.endswith("\n") else "")
    if out == src:
        raise MutationError(f"{mut.name}: the mutation changed nothing")
    try:
        ast.parse(out)
    except SyntaxError as exc:
        raise MutationError(f"{mut.name}: mutated source does not parse: {exc}")
    if mut.segment.strip() in out:
        raise MutationError(f"{mut.name}: the guard is still present after the "
                            f"edit — it appears more than once")
    return out


# ==========================================================================
#  Running the suite against a mutated copy
# ==========================================================================

_PLUGIN = '''\
"""Point `import <modname>` at a mutated copy, before pytest collects.

Registered with `-p`, so it runs before the test module is imported and
therefore before its own `sys.path.insert(0, HERE)` can win.
"""
import importlib.util
import os
import sys

_path = os.environ["MUTATE_TARGET"]
_name = os.environ["MUTATE_MODNAME"]
_spec = importlib.util.spec_from_file_location(_name, _path)
_mod = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _mod
_spec.loader.exec_module(_mod)
'''

_COUNT = re.compile(r"(\d+) (passed|failed|error|errors|skipped|xfailed|xpassed)")
_SUMMARY = re.compile(r"^(FAILED|ERROR)\s+(\S+)")


@dataclass
class Run:
    returncode: int
    counts: dict
    dead: list
    output: str

    @property
    def total(self):
        return (self.counts.get("passed", 0) + self.counts.get("failed", 0)
                + self.counts.get("error", 0) + self.counts.get("errors", 0)
                + self.counts.get("skipped", 0) + self.counts.get("xfailed", 0)
                + self.counts.get("xpassed", 0))


def _pytest(src, schema_path, test_path, workdir):
    """Write `src` as the module under test and run the suite against it."""
    target = workdir / schema_path.name
    target.write_text(src)
    (workdir / "_mutplugin.py").write_text(_PLUGIN)

    env = dict(os.environ)
    env["MUTATE_TARGET"] = str(target)
    env["MUTATE_MODNAME"] = schema_path.stem
    env["PYTHONPATH"] = os.pathsep.join(
        [str(workdir)] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    r = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_path), "-q", "--tb=no",
         "-rfE", "-p", "no:cacheprovider", "-p", "_mutplugin"],
        capture_output=True, text=True, env=env, cwd=str(workdir))
    out = r.stdout + r.stderr
    counts = {kind: int(n) for n, kind in _COUNT.findall(out)}
    if "errors" in counts:
        counts["error"] = counts.pop("errors")
    dead = []
    for line in out.splitlines():
        m = _SUMMARY.match(line.strip())
        if m:
            nodeid = m.group(2).split(" ")[0]
            dead.append(nodeid.split("::", 1)[-1] if "::" in nodeid else nodeid)
    return Run(r.returncode, counts, sorted(set(dead)), out)


@dataclass
class Result:
    mutation: Mutation
    status: str              # "killed" | "survivor" | "error"
    killed: list = field(default_factory=list)
    detail: str = ""


@dataclass
class Report:
    results: list
    baseline_n: int
    schema_path: Path

    @property
    def n_survivors(self):
        return sum(r.status == "survivor" for r in self.results)

    @property
    def n_errors(self):
        return sum(r.status == "error" for r in self.results)

    @property
    def exit_code(self):
        return 1 if (self.n_survivors or self.n_errors) else 0


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run_all(schema_path, test_path, mutations=None):
    """Mutate each guard in turn and record which tests die.

    `schema_path` is READ ONLY. Its digest is checked before and after.
    """
    schema_path, test_path = Path(schema_path), Path(test_path)
    src = schema_path.read_text()
    before = _sha(schema_path)
    muts = list(discover(src)) if mutations is None else list(mutations)
    if not muts:
        raise MutationError(f"no guards found in {schema_path}")

    workdir = Path(tempfile.mkdtemp(prefix="mutate_schema."))
    try:
        base = _pytest(src, schema_path, test_path, workdir)
        if base.returncode != 0 or base.counts.get("passed", 0) == 0:
            raise MutationError(
                f"baseline is not green through the isolation path — every "
                f"mutation result would be meaningless.\nrc={base.returncode} "
                f"counts={base.counts}\n{base.output[-2500:]}")
        baseline_n = base.total

        results = []
        for mut in muts:
            try:
                mutated = apply(src, mut)
            except MutationError as exc:
                results.append(Result(mut, "error", [], str(exc)))
                continue
            run = _pytest(mutated, schema_path, test_path, workdir)
            if run.returncode in (2, 3, 4, 5) or run.total != baseline_n:
                results.append(Result(
                    mut, "error", [],
                    f"the suite did not run comparably (rc={run.returncode}, "
                    f"collected {run.total} vs baseline {baseline_n}) — this is "
                    f"NOT evidence the guard is pinned\n{run.output[-1500:]}"))
                continue
            results.append(Result(mut, "killed" if run.dead else "survivor",
                                  run.dead))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    if _sha(schema_path) != before:
        raise MutationError(
            f"{schema_path} was MODIFIED IN PLACE. Every result in this run is "
            f"untrustworthy and the working tree needs restoring")
    return Report(results, baseline_n, schema_path)


# ==========================================================================
#  Reporting
# ==========================================================================

def format_report(rep, applied_only=False):
    lines = []
    w = max(len(label_for(r.mutation)) for r in rep.results)
    w = min(w, 56)
    lines.append(f"baseline: {rep.baseline_n} tests, all green "
                 f"({rep.schema_path.name} unmodified)")
    lines.append("")
    lines.append(f"{'#':>3}  {'guard (mutation applied)':<{w}}  {'result':<9}  tests killed")
    lines.append(f"{'':->3}  {'':-<{w}}  {'':-<9}  {'':-<12}")
    for i, r in enumerate(rep.results, 1):
        lab = label_for(r.mutation)[:w]
        if r.status == "killed":
            mark, dead = "killed", ", ".join(r.killed)
            if len(r.killed) > 4:
                dead = f"{len(r.killed)} tests: " + ", ".join(r.killed[:4]) + ", …"
        elif r.status == "survivor":
            mark, dead = "SURVIVOR", "⭐ NOTHING — this guard is pinned by no test"
        else:
            mark, dead = "ERROR", "‼ " + r.detail.splitlines()[0]
        lines.append(f"{i:>3}  {lab:<{w}}  {mark:<9}  {dead}")

    lines.append("")
    survivors = [r for r in rep.results if r.status == "survivor"]
    errors = [r for r in rep.results if r.status == "error"]
    killed = [r for r in rep.results if r.status == "killed"]

    lines.append(f"{len(killed)} killed · {len(survivors)} SURVIVORS · "
                 f"{len(errors)} errors  (of {len(rep.results)} guards)")

    if survivors:
        lines += ["", "⭐ SURVIVORS — guards that no test pins. These are the finding:"]
        for r in survivors:
            lines.append(f"   • {label_for(r.mutation)}   "
                         f"[{r.mutation.qual}, line {r.mutation.lineno}]")
            lines.append(f"     {r.mutation.segment.strip().splitlines()[0]} …")
    if errors:
        lines += ["", "‼ ERRORS — the mutation could not be applied or the run "
                       "was not comparable. NOT evidence of anything:"]
        for r in errors:
            lines.append(f"   • {label_for(r.mutation)}")
            for ln in r.detail.splitlines()[:4]:
                lines.append(f"     {ln}")

    # Guards that kill a lot: entanglement, or load-bearing for the fixtures.
    broad = [r for r in killed if len(r.killed) >= 5]
    if broad:
        lines += ["", "guards whose deletion kills MANY tests — entangled, or "
                       "load-bearing for the fixtures rather than for one assertion:"]
        for r in sorted(broad, key=lambda x: -len(x.killed)):
            lines.append(f"   • {len(r.killed):>2} tests — {label_for(r.mutation)}")

    # Tests that die under many unrelated mutations: suspect. Counted over the
    # NARROW mutations only — a broad one is global by construction and would
    # otherwise add a point to every test's score and hide the real signal.
    narrow = [r for r in killed if len(r.killed) < 5]
    counts = Counter(t for r in narrow for t in r.killed)
    lines += ["", f"tests killed by ≥3 different NARROW mutations "
                  f"({len(narrow)} of {len(killed)} counted; the "
                  f"{len(broad)} broad one(s) above excluded, being global by "
                  f"construction) — suspect: they may be failing for a reason "
                  f"other than the one they name:"]
    suspect = [(t, n) for t, n in counts.most_common() if n >= 3]
    if suspect:
        for t, n in suspect:
            lines.append(f"   • {n:>2} mutations — {t}")
    else:
        lines.append("   (none)")

    only_one = [t for t, n in counts.items() if n == 1]
    lines.append("")
    lines.append(f"{len(only_one)} of {len(counts)} tests killed by a narrow "
                 f"mutation are killed by exactly one (a clean 1:1 pin).")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--schema", default=str(DEFAULT_SCHEMA), type=Path)
    ap.add_argument("--tests", default=str(DEFAULT_TESTS), type=Path)
    ap.add_argument("--only", default=None,
                    help="substring: mutate only guards whose source matches")
    args = ap.parse_args(argv)

    src = Path(args.schema).read_text()
    muts = discover(src)

    # The floor from the brief must resolve, or the run is silently short.
    missing = {n: p for n, p in REQUIRED.items()
               if len([m for m in muts if p in m.segment]) != 1}
    if missing:
        print("‼ REQUIRED guards did not resolve to exactly one raise site.\n"
              "  The messages were reworded, or the guard is gone. Refusing to "
              "run: a short run reports fewer holes than exist.", file=sys.stderr)
        for n, p in missing.items():
            hits = len([m for m in muts if p in m.segment])
            print(f"    {n}: {hits} matches for {p!r}", file=sys.stderr)
        return 2

    if args.only:
        muts = [m for m in muts if args.only in m.segment or args.only in m.name]
        if not muts:
            print(f"‼ --only {args.only!r} matched no guard", file=sys.stderr)
            return 2

    print(f"mutating {len(muts)} guards in {args.schema} against {args.tests}",
          file=sys.stderr)
    try:
        rep = run_all(args.schema, args.tests, muts)
    except MutationError as exc:
        print(f"‼ {exc}", file=sys.stderr)
        return 2
    print(format_report(rep))
    if rep.exit_code:
        print("\nexit 1: a guard nothing pins, or a mutation that did not apply.")
    else:
        print("\nexit 0: every guard is pinned by at least one test.")
    return rep.exit_code


if __name__ == "__main__":
    sys.exit(main())
