"""Stage 4 — R3, the DERIVATION layer of the read-back (`STEP_stage4.md` §2.1).

`readback.py` produces R1 (one rendering per licensed item) and R2 (one per
rule, mechanical and authored, diffed). §2.1 specifies a third:

    R3 | one per stage-3 covering-set situation with a non-empty derivation
       | xclingo explanation tree, every leaf replaced by its R1 rendering

Without it no *derivation* reaches any seat: the seats judge items and rules,
never **why a verdict followed in a particular situation**. This module is that
layer. It makes no network call, reads no label and costs nothing — xclingo is
local.

⭐ FOUR THINGS THIS FILE IS, IN THE ORDER THEY MATTER.

**1. The annotation is composed by the RENDERER, never taken from the model.**
`schema.render_lp` emits `%!trace_rule {"{read_back}"}` from the model's
authored `read_back` field. §2.2 demotes that field to a second opinion — 11 of
12 licensed items in the last run have no authored sentence at all, and the one
that does gets its polarity right by luck. So R3 builds its own `.lp`, with a
`%!trace_rule` per rule generated from `readback.render_items` — the same R1/R2
machinery, over the same gloss table. The authored string never enters the
program R3 runs.

**2. Every leaf is replaced by its R1 rendering.** `[RAN]` today xclingo's
leaves are raw ASP terms (`forbids(restricted_content,m3)`), which
`STEP_stage4.md` §0 finding (3) records as one of the two places the read-back
fails Invariant 1. `gloss_leaf` substitutes the written meaning. ⛔ **A leaf
with no written meaning is REPORTED, never passed through**: printing the
predicate name where a definition belongs IS the design's failure mode #4, and
`readback.readback-ungloss` already rules on it one level up.

**3. ⛔ EVERY EMPTY RESULT BLOCKS.** A missing xclingo, an `_` in the link
scope, an unparseable tree, a verdict stage 3 says is derived but xclingo roots
no tree at — each of those yields zero derivations, and zero derivations
rendered without complaint reads as *"this clause has no derivations"*, which
is a substantive claim about the translation made by a tool that did not run.
This repo names that shape as its recurring failure (`DEBUGGING_TIPS.md` §8).
Nothing here returns an empty R3 set quietly. A situation that genuinely
derives nothing is stamped `no-derivation` and **counted**, with its
denominator printed beside it (`DEBUGGING_TIPS.md` §2).

**4. ⛔ `_` kills the WHOLE link set's explanation, not one rule.** `[RAN]`
xclingo 2.0b24 on `p(X) :- q(X,_).` prints *"error: unsafe variables in:
`_xclingo_sup(...#Anon0)`"*, emits no explanation at all — **and exits 0**.
`schema.py` rejects `_` in a module body for exactly this reason (commit
`b7c663e`), but a hand-written `.lp` at link scope is under no such contract,
so R3 scans its whole program and refuses BY NAME rather than rendering a
partial tree. The return code cannot see this; the stderr scan can. Both arms
are kept and both are pinned.

⚠️ ONE DEPARTURE FROM THE BRIEF, RECORDED RATHER THAN SMOOTHED OVER.
`STEP_stage4.md` §2.1 and the build brief say `--output ascii-trees -n 0 0`.
`[RAN]` that alone produces a tree with **no leaves**: xclingo only shows a
node it has a label for, and an unlabelled fact is invisible. Since R3's entire
substance is *"every leaf replaced by its R1 rendering"*, `--auto-tracing=facts`
is added — the same flag §0 finding (3) used to produce the four-line tree it
quotes. Without it R3 would be a layer whose defining requirement is vacuous.
"""

import dataclasses
import os
import re
import subprocess
import sys
import tempfile
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import probe                                                   # noqa: E402
import readback                                                # noqa: E402

#: ⚠️ `--auto-tracing=facts` is load-bearing, not decoration — see the module
#: docstring's recorded departure. The rest is `STEP_stage4.md` §2.1 verbatim.
XCLINGO_ARGS = ("--auto-tracing=facts", "--output", "ascii-trees",
                "-n", "0", "0")

#: xclingo's own completion sentinel. Its ABSENCE is how "the tool did not run"
#: is told apart from "the tool ran and found nothing".
DONE_MARK = "##Total Explanations:"

#: Characters that break the `%!trace_rule {"..."}` literal. ⛔ `schema
#: ._BAD_IN_TEXT` fences the model's `read_back` and NOTHING ELSE — a *gloss*
#: may hold any of these, and R3 interpolates glosses.
TRACE_SAFE = {'"': "”", "\\": "/", "{": "(", "}": ")",
              "\n": " ", "\r": " "}

_ERROR_LINE = re.compile(r"(^|\s)(\*\*\* ERROR|error:)", re.MULTILINE)
_ANSWER = re.compile(r"^Answer:\s*\d+", re.MULTILINE)
_EXPLANATION = re.compile(r"^##Explanation:\s*(\S+)", re.MULTILINE)
_STRINGS = re.compile(r'"[^"\n]*"')
_COMMENT = re.compile(r"%.*$", re.MULTILINE)
_ANON = re.compile(r"(?<![A-Za-z0-9_])_(?![A-Za-z0-9_])")
_CONST = re.compile(r"^([a-z][A-Za-z0-9_]*|\d+)$")
_VERDICT = re.compile(r"^(asserts|beats)\(")


class R3Error(RuntimeError):
    """⛔ Always a BLOCK. R3 has no degraded mode: a partial derivation set and
    a complete one are the same bytes to a seat, and the difference is exactly
    what a seat would be judging."""


# ==========================================================================
#  the program R3 runs — composed here, from the RENDERER's sentences
# ==========================================================================

def trace_safe(text):
    """`(safe_text, offending_characters)` for a `%!trace_rule` literal."""
    bad = sorted({c for c in text if c in TRACE_SAFE})
    out = text
    for ch in bad:
        out = out.replace(ch, TRACE_SAFE[ch])
    return out, tuple(bad)


def _annotation(sentence, notes, item):
    safe, bad = trace_safe(sentence)
    if bad:
        notes.append(readback.Finding(
            "readback-r3-trace-unsafe", "note", item,
            f"the rendering of {item} contains {bad!r}, which cannot appear "
            f"inside the %!trace_rule string literal xclingo parses. It is "
            f"rewritten to a plain equivalent — recorded because the sentence "
            f"a seat reads is then not byte-for-byte the R1/R2 rendering"))
    return '%%!trace_rule {"%s"}.' % safe


def module_program(mod, renderings, notes):
    """The module's logic with a MECHANICAL `%!trace_rule` on every rule.

    ⛔ The authored `read_back` never appears. That is §2.2's ruling and the
    whole reason this function exists rather than `schema.render_lp` being
    reused: `render_lp` interpolates `a.read_back`, and R3 needs the renderer's
    sentence in the same slot.

    ⚠️ `defines` and `ontology` are annotated too, though `render_lp` annotates
    neither. An unannotated rule is INVISIBLE to xclingo, so leaving them bare
    would silently flatten a derivation that passes through an ontology fact —
    a shorter tree that reads like a simpler explanation.
    """
    sentence = {r.item: r.text for r in renderings}
    out = []
    if mod.ontology:
        # ⛔ THE `o` ABLATION GUARD IS DROPPED HERE, DELIBERATELY, and this is
        # the one place R3's program differs from `schema.render_lp`'s.
        # `render_lp` emits `#const onto = on. o :- onto = on.` and hangs every
        # ontology rule off `o` so `deontic_probe/FINDINGS.md` §4.6 can ablate
        # the non-deontic layer. `onto = on` has no positive body atom, so
        # clingo simplifies `o` into a FACT, `--auto-tracing=facts` labels it,
        # and it surfaces as a LEAF of every ontology-backed derivation —
        # `[RAN]` on `m0079`, where it was reported as `readback-ungloss` for a
        # symbol that is renderer scaffolding and has no meaning to write down.
        # ⇒ Excluding `o` from the ungloss check was REJECTED BY NAME: a
        # hard-coded name skipped by a check is exactly how a real missing
        # gloss would later hide. R3 never ablates, so `o` is always true and
        # `a :- o, B` ≡ `a :- B`; the guard is removed rather than exempted,
        # and the equivalence is checked where it matters (every verdict stage
        # 3 derives must root a tree).
        for i, f in enumerate(mod.ontology):
            item = f"ontology[{i}]"
            out.append(_annotation(sentence[item], notes, item))
            out.append(f.atom + (f" :- {f.body}." if f.body else "."))
    for i, d in enumerate(mod.defines):
        item = f"defines[{i}]"
        out.append(_annotation(sentence[item], notes, item))
        out.append(f"defines({mod.clause_id}, {d.kind}, {d.term}).")
    for i, a in enumerate(mod.asserts):
        item = f"asserts[{i}]"
        out.append(_annotation(sentence[item], notes, item))
        head = f"asserts({mod.clause_id}, {a.status}, {a.act})"
        out.append(head + (f" :- {a.body}." if a.body else "."))
    for i, b in enumerate(mod.beats):
        item = f"beats[{i}]"
        out.append(_annotation(sentence[item], notes, item))
        head = f"beats({b.sayer}, {b.winner}, {b.loser})"
        out.append(head + (f" :- {b.body}." if b.body else "."))
    return "\n".join(out)


def situation_facts(situation):
    """The situation's true inputs as ground facts. False inputs are ABSENT —
    the enumeration is closed-world and stage 3 read the derived set off the
    same closure."""
    return "\n".join(f"{a}." for a in sorted(situation.true_atoms))


def anonymous_variables(text):
    """Every line of `text` carrying a genuine `_`, comments and strings out.

    ⚠️ Strings first, then comments. `m0255.lp` line 30 is a COMMENT that
    contains `` `_` `` — written by the author to record that the construct was
    avoided on purpose — and a scan that reads comments refuses the one file in
    the repo that took the trouble. A `%` inside a quoted constant is not a
    comment, so the order is not interchangeable.
    """
    out = []
    for line in text.splitlines():
        scrubbed = _COMMENT.sub("", _STRINGS.sub('""', line))
        if _ANON.search(scrubbed):
            out.append(line.strip())
    return tuple(out)


def _refuse_anonymous(sources):
    for where, text in sources:
        hits = anonymous_variables(text)
        if hits:
            raise R3Error(
                f"{where} contains an anonymous variable `_`: "
                + " / ".join(hits[:3])
                + ". xclingo lifts every body variable into a supporting term "
                  "and `#Anon` is unsafe there, so the explainer program fails "
                  "to ground and returns NO tree for ANY rule in the link "
                  "scope — not just this one. R3 refuses rather than render a "
                  "partial derivation set that would read as a complete one")


# ==========================================================================
#  running xclingo, and the TWO independent detectors
# ==========================================================================

def _default_xclingo():
    return [sys.executable, "-m", "xclingo"]


def run_xclingo(program, xclingo=None, timeout=120):
    """xclingo's stdout, or `R3Error`. ⛔ Never a quiet empty string.

    THREE detectors, deliberately redundant, each pinned by its own test:

      * a non-zero exit — what a MISSING xclingo looks like;
      * `error:` / `*** ERROR` on stderr — `[RAN]` what an `_` in the program
        looks like, and it **exits 0**, so the return code cannot see it;
      * the absence of xclingo's own completion sentinel — what a crash or a
        truncated stream looks like.

    `DEBUGGING_TIPS.md` §8: a check that cannot run must not exit like a check
    that passed, and a redundant guard whose second arm is untested is
    decoration.
    """
    cmd = list(xclingo or _default_xclingo()) + list(XCLINGO_ARGS)
    fd, path = tempfile.mkstemp(suffix=".lp", prefix="r3_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(program if program.endswith("\n") else program + "\n")
        try:
            proc = subprocess.run(cmd + [path], capture_output=True, text=True,
                                  timeout=timeout)
        except FileNotFoundError as exc:
            raise R3Error(
                f"xclingo could not be executed ({cmd[0]!r}: {exc}). R3 has no "
                f"fallback: with no explainer there are no derivations to "
                f"render, and reporting none would be indistinguishable from "
                f"a clause that has none") from exc
        except subprocess.TimeoutExpired as exc:
            raise R3Error(f"xclingo did not finish within {timeout}s") from exc
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass

    if proc.returncode != 0:
        raise R3Error(
            f"xclingo exited {proc.returncode}. stderr: "
            f"{(proc.stderr or '').strip()[:400]}")
    if _ERROR_LINE.search(proc.stderr or ""):
        raise R3Error(
            "xclingo reported an error and STILL EXITED 0 — the case the "
            "return code cannot see. stderr: "
            + (proc.stderr or "").strip()[:400])
    if DONE_MARK not in proc.stdout:
        raise R3Error(
            f"xclingo produced no completion marker ({DONE_MARK!r}); its "
            f"output cannot be parsed and an empty derivation set must never "
            f"be inferred from it. stdout: {proc.stdout.strip()[:400]!r}")
    answers = len(_ANSWER.findall(proc.stdout))
    if answers > 1:
        raise R3Error(
            f"xclingo found {answers} answer sets for one situation. A "
            f"situation IS a single answer set (`probe.enumerate_situations` "
            f"refuses a module with two), so the explanation program is not "
            f"the program stage 3 enumerated")
    return proc.stdout


# ==========================================================================
#  the tree — structured, never a blob
# ==========================================================================

@dataclasses.dataclass(frozen=True)
class Node:
    """One line of an xclingo tree, with its R1 rendering in `text`."""

    raw: str                     #: what xclingo printed, verbatim
    text: str                    #: what a seat reads
    kind: str                    #: "rule" (a `%!trace_rule` label) | "fact"
    depth: int
    children: tuple = ()
    #: The bare ASP term xclingo printed for this node, when it printed one.
    atom: str = ""
    #: ⭐ §2.3: "Every rendering records the layer that produced it, and the
    #: layer is visible in the report." A rule node inherits the layer of the
    #: R1/R2 rendering that composed its sentence; a leaf is layer 2 when a
    #: leaf is layer 2 whenever the template fitted — including when the gloss
    #: it wanted was missing, because that is `readback-ungloss`, not a
    #: fluency gap (§2.3 forbids blurring the two).
    layer: int = 1

    @property
    def stamp(self):
        return readback.LAYER_STAMP[self.layer]

    @property
    def is_leaf(self):
        return not self.children


@dataclasses.dataclass(frozen=True)
class Derivation:
    label: str                   #: xclingo's explanation id, e.g. "1.1"
    verdict: str                 #: the ground `asserts`/`beats` atom explained
    roots: tuple


def _payload(line):
    idx = line.find("__")
    if idx < 0:
        return None
    prefix = line[:idx]
    if prefix.replace("|", "").strip(" ") != "":
        return None
    depth = prefix.count("|")
    if depth < 1:
        return None
    return depth, line[idx + 2:].rstrip()


def parse_ascii_trees(text):
    """`[(label, roots)]` from `--output ascii-trees`. Pure parser, no I/O.

    ⛔ It raises rather than skipping a line it cannot place. A tree silently
    missing a branch is a shorter, simpler-looking explanation of the same
    verdict, and nothing downstream could tell.
    """
    out = []
    label, stack, roots = None, [], []

    def close():
        if label is not None:
            out.append((label, tuple(roots)))

    for line in text.splitlines():
        m = _EXPLANATION.match(line.strip()) if line.strip().startswith("##") \
            else None
        if m:
            close()
            label, stack, roots = m.group(1), [], []
            continue
        if label is None:
            continue
        if line.strip().startswith("##"):
            close()
            label, stack, roots = None, [], []
            continue
        parsed = _payload(line)
        if parsed is None:
            if line.strip() in ("", "*"):
                continue
            if line.strip().startswith(("Answer:", "Models:", "xclingo ",
                                        "Reading from ")):
                continue
            raise R3Error(
                f"tree line {line!r} is not an xclingo ascii-tree line and R3 "
                f"will not skip it: a line dropped from a derivation makes the "
                f"explanation look simpler than it is")
        depth, raw = parsed
        node = {"raw": raw, "depth": depth, "children": []}
        if depth == 1:
            roots.append(node)
            stack = [node]
            continue
        # A node at depth d needs an ancestor at depth d-1 on the stack. It may
        # go exactly ONE deeper than the last line and no further.
        if depth > len(stack) + 1:
            raise R3Error(
                f"tree line {line!r} sits at depth {depth} under a parent at "
                f"depth {len(stack)}: it has no parent, and inventing one "
                f"builds a tree xclingo did not print")
        del stack[depth - 1:]
        stack[-1]["children"].append(node)
        stack.append(node)
    close()
    return tuple((lab, tuple(_freeze(r) for r in rs)) for lab, rs in out)


def node_labels(payload):
    """`(sentences, bare_terms)` — one xclingo node can carry SEVERAL labels.

    ⛔ FOUND ON LIVE MATERIAL, and it leaked a raw ASP term into seat-facing
    text. A body-less `asserts` fact carries R3's own `%!trace_rule` label AND
    the one `--auto-tracing=facts` adds, and xclingo prints them joined by
    `;`: `"clause m0079 obliges <act produce_response>";asserts(m0079,oblige,
    produce_response)`. Treating the whole payload as one quoted sentence put
    the predicate name in front of a seat — Invariant 1's exact failure, from
    the layer written to fix it.
    """
    parts, cur, in_str = [], "", False
    for ch in payload:
        if ch == '"':
            in_str = not in_str
        elif ch == ";" and not in_str:
            parts.append(cur)
            cur = ""
            continue
        cur += ch
    parts.append(cur)
    parts = [p.strip() for p in parts if p.strip()]
    said = tuple(p[1:-1] for p in parts
                 if len(p) >= 2 and p.startswith('"') and p.endswith('"'))
    bare = tuple(p for p in parts
                 if not (len(p) >= 2 and p.startswith('"') and p.endswith('"')))
    return said, bare


def _freeze(node):
    raw = node["raw"]
    said, bare = node_labels(raw)
    # A node with a composed sentence IS the rule; the auto-added atom beside
    # it is xclingo's fallback label and is exactly what R1 replaces.
    kind = "rule" if said else "fact"
    return Node(raw=raw, text=" / ".join(said) if said else raw, kind=kind,
                depth=node["depth"], atom=bare[0] if bare else "",
                children=tuple(_freeze(c) for c in node["children"]))


def walk_nodes(node):
    """`node` and every descendant, pre-order."""
    yield node
    for c in node.children:
        yield from walk_nodes(c)


def walk(derivation):
    for r in derivation.roots:
        yield from walk_nodes(r)


# ==========================================================================
#  §2.1's substance — every leaf replaced by its R1 rendering
# ==========================================================================

def _split_args(term):
    if "(" not in term:
        return []
    inner = term[term.index("(") + 1:term.rindex(")")]
    args, depth, cur = [], 0, ""
    for ch in inner:
        if ch == "," and depth == 0:
            args.append(cur.strip())
            cur = ""
            continue
        depth += (ch == "(") - (ch == ")")
        cur += ch
    if cur.strip():
        args.append(cur.strip())
    return args


def gloss_leaf(atom, gloss, placeholder=None):
    """`(text, glossed)` — the R1 rendering of one raw ASP leaf.

    ⛔ `glossed=False` is a FINDING, not a fallback. Printing `terrorism_act`
    where a definition belongs is failure mode #4 ("imports a name without its
    content"), measured in our own output at 7.5 %, and `readback-ungloss`
    already rules that a symbol with no written meaning stops the clause.
    """
    placeholder = placeholder or probe.PROBE_DEFAULTS["placeholder"]
    name = atom.split("(")[0].strip()
    written = gloss.get(name)
    if not written:
        return f"{readback.UNGLOSS_MARK}{name}{readback.UNGLOSS_CLOSE}", False
    text = (readback.GLOSS_OPEN + readback.marker_safe(written)
            + readback.GLOSS_CLOSE)
    shown = [a for a in _split_args(atom)
             if _CONST.match(a) and a != placeholder]
    if shown:
        text += f" (concerning: {', '.join(shown)})"
    return text, True


def _gloss_tree(node, gloss, placeholder, missing, layers):
    text, layer = node.text, layers.get(node.text, 1)
    if node.kind != "rule":
        text, ok = gloss_leaf(node.atom or node.raw, gloss, placeholder)
        # ⛔ LAYER 2 EVEN WHEN THE GLOSS IS MISSING, and the two must not be
        # blurred (§2.3). The layer stamp tracks whether a TEMPLATE existed;
        # `«meaning» (concerning: …)` is that template and it fitted. What is
        # absent is the written definition, and that is `readback-ungloss` —
        # an ERROR that stops the clause, not a fluency note that does not.
        # Folding it into the layer stamp would demote a hole in the
        # TRANSLATION into a gap in OUR renderer.
        layer = 2
        if not ok:
            missing.add((node.atom or node.raw).split("(")[0].strip())
    return Node(raw=node.raw, text=text, kind=node.kind, depth=node.depth,
                atom=node.atom, layer=layer,
                children=tuple(_gloss_tree(c, gloss, placeholder, missing,
                                           layers)
                               for c in node.children))


# ==========================================================================
#  the entry point
# ==========================================================================

@dataclasses.dataclass(frozen=True)
class SituationR3:
    situation_id: str
    true_atoms: tuple
    verdicts: tuple
    derivations: tuple
    findings: tuple
    outcome: str                 #: rendered | no-derivation | readback-ungloss


@dataclasses.dataclass(frozen=True)
class ModuleR3:
    clause_id: str
    program: str                 #: the annotated logic, verbatim and auditable
    situations: tuple
    findings: tuple
    outcome: str
    covering: int
    with_derivation: int

    @property
    def nodes(self):
        return tuple(n for s in self.situations for d in s.derivations
                     for n in walk(d))

    @property
    def layer1_fraction(self):
        """⭐ §2.3: printed EVEN WHEN ZERO. A run mostly at layer 1 is a
        finding about the renderer's fluency coverage, routed to whoever writes
        templates — never a finding about the modules, and never a refusal."""
        nodes = self.nodes
        if not nodes:
            return None
        return sum(1 for n in nodes if n.layer == 1) / len(nodes)

    def report(self):
        frac = self.layer1_fraction
        head = [f"readback-R3 {self.clause_id}  outcome={self.outcome}",
                f"  derivations: {self.with_derivation} of {self.covering} "
                f"covering-set situation(s) have a non-empty derivation",
                "  layer-1 nodes: "
                + ("not-measured (no derivation)" if frac is None
                   else f"{frac:.2f} of {len(self.nodes)}")]
        for s in self.situations:
            head.append(f"  {s.situation_id}  [{s.outcome}]  "
                        f"verdicts: {', '.join(s.verdicts) or '(none)'}")
            for d in s.derivations:
                head.append(f"    explanation {d.label} of {d.verdict}")
                for n in walk(d):
                    head.append("      " + "   " * (n.depth - 1)
                                + f"{'·' if n.kind == 'fact' else '-'} "
                                + n.text + f"   [{n.stamp}]")
        for f in self.findings:
            head.append(f"  {f.severity.upper():<5} {f.check_id}: {f.message}")
        return "\n".join(head)


def proceeds_to_a_seat(out):
    """⛔ Only a fully rendered set does. `readback-ungloss` stops the clause
    (§2.3), and a run where nothing derives has no derivation to judge."""
    return out.outcome == "rendered"


def verdict_atoms(situation):
    """The ground `asserts`/`beats` atoms this situation derives — the things a
    derivation can be *of*."""
    return tuple(sorted(a.replace(" ", "") for a in situation.derived
                        if _VERDICT.match(a.replace(" ", ""))))


def render_r3(mod, situations, *, extra_gloss=None, gloss=None, link_texts=(),
              placeholder=None, xclingo=None):
    """R3 over one module and its stage-3 covering set.

    `situations` is `probe.ProbeReport.covering` (anything with `id`,
    `true_atoms` and `derived`). `link_texts` is `[(name, text)]` — the same
    scope stage 3 solved over. `gloss` overrides the module's own table; a
    `None` value REMOVES a gloss, which is how the missing-definition path is
    exercised without editing a module.
    """
    situations = tuple(situations)
    if not situations:
        raise R3Error(
            f"{mod.clause_id}: R3 was asked for a derivation set over ZERO "
            f"situations. An empty result here is byte-identical to 'this "
            f"clause has no derivations', which is a claim about the "
            f"translation. Pass the covering set, or do not call R3")

    table = readback.gloss_table(mod, extra_gloss)
    for name, written in (gloss or {}).items():
        if written is None:
            table.pop(name, None)
        else:
            table[name] = written

    notes = []
    renderings = readback.render_items(mod, table, notes)
    # §2.3's stamp, carried from the rendering that composed the sentence.
    # Keyed on the trace-safe form, which is what xclingo prints back.
    layers = {trace_safe(r.text)[0]: r.layer for r in renderings}
    program = module_program(mod, renderings, notes)
    sources = [(f"{mod.clause_id} (module)", program)] + list(link_texts)
    _refuse_anonymous(sources)
    link_blob = "\n".join(t for _n, t in link_texts)

    out_situations, findings = [], list(notes)
    for s in situations:
        verdicts = verdict_atoms(s)
        if not verdicts:
            out_situations.append(SituationR3(
                s.id, tuple(sorted(s.true_atoms)), (), (), (), "no-derivation"))
            continue
        derivations, missing, s_findings = [], set(), []
        for atom in verdicts:
            text = "\n".join([program, link_blob, situation_facts(s),
                              "%%!show_trace {%s}." % atom])
            trees = parse_ascii_trees(run_xclingo(text, xclingo=xclingo))
            rooted = [(lab, rs) for lab, rs in trees if rs]
            if not rooted:
                raise R3Error(
                    f"{mod.clause_id} situation {s.id}: stage 3 derives "
                    f"{atom} but xclingo rooted NO explanation tree at it. The "
                    f"explanation program and the enumerated program disagree; "
                    f"rendering the trees that did appear would show a seat a "
                    f"derivation for a verdict other than the one under review")
            for lab, roots in rooted:
                derivations.append(Derivation(
                    lab, atom,
                    tuple(_gloss_tree(r, table, placeholder, missing, layers)
                          for r in roots)))
        for name in sorted(missing):
            s_findings.append(readback.Finding(
                "readback-ungloss", "error", s.id,
                f"leaf {name!r} in {s.id}'s derivation has no written meaning. "
                f"§2.1 requires every leaf to be replaced by its R1 rendering; "
                f"a label printed where a definition belongs is failure mode "
                f"#4, and the clause proceeds to no seat"))
        findings.extend(s_findings)
        out_situations.append(SituationR3(
            s.id, tuple(sorted(s.true_atoms)), verdicts, tuple(derivations),
            tuple(s_findings),
            "readback-ungloss" if missing else "rendered"))

    with_derivation = sum(1 for s in out_situations if s.derivations)
    if any(s.outcome == "readback-ungloss" for s in out_situations):
        outcome = "readback-ungloss"
    elif with_derivation == 0:
        outcome = "no-derivation"
    else:
        outcome = "rendered"
    return ModuleR3(clause_id=mod.clause_id, program=program,
                    situations=tuple(out_situations),
                    findings=tuple(findings), outcome=outcome,
                    covering=len(out_situations),
                    with_derivation=with_derivation)


# ==========================================================================
#  CLI — free, deterministic, and it prints its denominator
# ==========================================================================

def main(argv=None):
    import glob
    import json

    import link
    import schema

    argv = list(sys.argv[1:] if argv is None else argv)
    # ⚠️ `m*.json` also matches `m0014.transcript.json`. Those are not modules
    # and reporting them as `stage-2-invalid` buries the real rows.
    paths = argv or sorted(p for p in
                           glob.glob(os.path.join(HERE, "runs", "*", "m*.json"))
                           if re.fullmatch(r"m\d+\.json", os.path.basename(p)))
    total = covered = 0
    for path in paths:
        if not path.endswith(".json"):
            continue
        lp = path[:-5] + ".lp"
        try:
            mod = schema.validate(json.load(open(path, encoding="utf-8")))
        except Exception as exc:                               # noqa: BLE001
            print(f"{path}: stage-2-invalid ({str(exc)[:60]})")
            continue
        if not os.path.exists(lp):
            print(f"{path}: no .lp on disk")
            continue
        rows, _l, _m = link.discover_concept_table([lp])
        rep = probe.probe_clause(lp, [], rows or [])
        if not rep.covering:
            print(f"{mod.clause_id}: covering set empty ({rep.outcome})")
            continue
        try:
            out = render_r3(mod, rep.covering,
                            extra_gloss=readback.gloss_from_rows(rows or []))
        except R3Error as exc:
            print(f"{mod.clause_id}: BLOCKED — {exc}")
            continue
        total += out.covering
        covered += out.with_derivation
        print(out.report())
        print()
    print(f"TOTAL: {covered} of {total} covering-set situations have a "
          f"non-empty derivation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
