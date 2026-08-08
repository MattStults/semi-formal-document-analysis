"""Stage 4 — the read-back renderer: a validated `schema.Module` into English.

`STEP_stage4.md` §2. All four seats judge ONE artifact, so the artifact is
composed deterministically and checked deterministically before any model is
called. Nothing here makes a network call or reads a label.

⭐ TWO LAYERS, and the order matters.

**Layer 1 — the total fallback.** Walk the rule with `clingo.ast.parse_string`.
For any node whatever, `str(node)` is defined, so a rendering always exists:
take the node's own source form and replace every predicate name with its gloss.
No node-type introspection, therefore no node type it cannot handle. It renders
aggregates, conditional literals, comparisons, intervals, pooling, arithmetic
and negation without knowing what any of them are.

⛔ **NO ASP CONSTRUCT MAY EVER BE INADMISSIBLE.** Matt's ruling, and it is the
point of the exercise: a construct with no fluent template gets layer 1 — never
an error, never a refusal. Restricting the ASP so the renderer can cope would
move the problem from the renderer, where it is visible, into the translation,
where it is not.

**Layer 2 — fluency.** Per-node-type templates for the shapes that recur, so a
reviewer reads English rather than glossed ASP. Absent template → layer 1.

⭐ **Every rendering records WHICH LAYER produced it, and the layer is visible in
the output.** A reader must be able to tell fluent English from ASP with the
glosses inlined, because the two carry different amounts of trust. `STEP_stage4`
RB4 sets the precedent: stamp, do not fail.

⚠️ **Polarity comes from the AST, never from prose** (§2.2). `m0217`'s body is
`not exploits_individual(M)` and its authored sentence happens to be right; a
renderer that walks the rule gets the sign by construction, a prose author gets
it by luck, and `WALKTHROUGH_REPORT.md` iteration 2 is the recorded case of that
luck running out.

⚠️ **Reference for template shapes only:** ASP2CNL
(https://ceur-ws.org/Vol-4117/short_rcra_3.pdf) — aggregates as *"the number of
X that have Y is at least Z"*. ⛔ Its NAMING model is deliberately not adopted:
it verbalises predicate names (`assignment(X,C1)` → *"an assignment with node
X"*), and Invariant 1 requires the definition, not the label. Rendering the name
would manufacture precisely the failure stage 4 exists to detect.
"""

from __future__ import annotations

import dataclasses
import re
import statistics
from typing import Optional

import clingo.ast as ast

import schema

# --------------------------------------------------------------------------
#  visible marks. Each one tells a reader something the sentence alone cannot.
# --------------------------------------------------------------------------
GLOSS_OPEN, GLOSS_CLOSE = "«", "»"
ASP_MARK = "⟦ASP:"                 # opens a layer-1 span: ASP with glosses in
ASP_CLOSE = "⟧"
ACT_MARK = "⟨act "                 # an act term rendered as itself — see below
ACT_CLOSE = "⟩"
UNGLOSS_MARK = "⟨no gloss: "       # ⛔ a MISSING GLOSS, never a missing template
UNGLOSS_CLOSE = "⟩"
NEG_MARK = "it is NOT the case that"

#: Above this clause-level echo, 4b/4d verdicts are stamped `non-evidential`.
#: ⭐ It is a STAMP, never a gate — a threshold used to fail a clause would be a
#: scoring instrument, which open question 3 forbids.
ECHO_LEVEL = 0.90

STATUS = {"forbid": "forbids", "permit": "permits",
          "oblige": "obliges", "prefer": "prefers"}

#: ASP words that are lowercase but are not predicate names.
KEYWORDS = {"not", "count", "sum", "min", "max", "true", "false"}

_CMP = {int(ast.ComparisonOperator.Equal): "equal to",
        int(ast.ComparisonOperator.NotEqual): "different from",
        int(ast.ComparisonOperator.LessThan): "less than",
        int(ast.ComparisonOperator.LessEqual): "at most",
        int(ast.ComparisonOperator.GreaterThan): "greater than",
        int(ast.ComparisonOperator.GreaterEqual): "at least"}

#: `g OP agg` is printed by clingo with the guard on the left. Read from the
#: aggregate's side the relation is the converse, and getting this backwards
#: inverts every aggregate bound silently.
_CONVERSE = {int(ast.ComparisonOperator.Equal): int(ast.ComparisonOperator.Equal),
             int(ast.ComparisonOperator.NotEqual): int(ast.ComparisonOperator.NotEqual),
             int(ast.ComparisonOperator.LessThan): int(ast.ComparisonOperator.GreaterThan),
             int(ast.ComparisonOperator.LessEqual): int(ast.ComparisonOperator.GreaterEqual),
             int(ast.ComparisonOperator.GreaterThan): int(ast.ComparisonOperator.LessThan),
             int(ast.ComparisonOperator.GreaterEqual): int(ast.ComparisonOperator.LessEqual)}

_AGG = {int(ast.AggregateFunction.Count): "number",
        int(ast.AggregateFunction.Sum): "total",
        int(ast.AggregateFunction.SumPlus): "total of the positive terms",
        int(ast.AggregateFunction.Min): "smallest",
        int(ast.AggregateFunction.Max): "largest"}

_NAME = re.compile(r"(?<![A-Za-z0-9_#])([a-z][A-Za-z0-9_]*)")
_PRED_IN_BODY = re.compile(r"(?<![A-Za-z0-9_])([a-z][A-Za-z0-9_]*)\s*\(")
_TOKEN = re.compile(r"[a-z0-9]+")


# ==========================================================================
#  LAYER 1 — the primitive everything else falls back to
# ==========================================================================

def substitute(text: str, gloss: dict) -> str:
    """Every predicate name in `text` replaced by its gloss, in «».

    ⭐ This is the whole of layer 1. It does not know what it is looking at, so
    there is nothing it can be handed that it refuses. A name with no gloss is
    left BARE and on purpose: that is a label surviving into the English, RB1
    catches it, and silently inventing a plausible phrase would hide the one
    defect stage 4 exists to find.
    """
    def one(m):
        name = m.group(1)
        if name in KEYWORDS or name not in gloss:
            return name
        return f"{GLOSS_OPEN}{gloss[name]}{GLOSS_CLOSE}"
    return _NAME.sub(one, text)


@dataclasses.dataclass(frozen=True)
class Span:
    """One rendered conjunct, with the layer that produced it."""

    text: str
    layer: int
    source: str

    @property
    def stamp(self) -> str:
        return LAYER_STAMP[self.layer]


LAYER_STAMP = {1: "layer 1 · asp-with-glosses", 2: "layer 2 · fluent"}


def _fallback(node, gloss) -> Span:
    src = str(node)
    return Span(f"{ASP_MARK} {substitute(src, gloss)}{ASP_CLOSE}", 1, src)


# ==========================================================================
#  parsing
# ==========================================================================

def _parse_body(body: str):
    """The body's literals as AST nodes, or None if clingo cannot parse it.

    ⚠️ An unparseable body is NOT an error here. `schema._check_body` is where
    parseability is enforced; the renderer's job is to render whatever it is
    given, so a parse failure degrades to layer 1 over the raw text.
    """
    stmts = []
    try:
        ast.parse_string(f"h_readback_head :- {body}.", stmts.append,
                         logger=lambda code, msg: None, message_limit=0)
    except Exception:
        return None
    # ⛔ MORE THAN ONE RULE MEANS THE BODY CARRIED A STATEMENT SEPARATOR, and
    # returning the first one's literals SILENTLY DROPS the rest. That is what
    # this did: `adult(P). N > 5, N != 9` rendered as "the person is an adult"
    # alone, with `outcome=rendered` and RB1-RB5 all green, and a seat was shown
    # one of three conditions. `schema._check_body` now rejects an internal full
    # stop, so this is defence in depth — but a renderer that drops content
    # silently is exactly the failure the read-back exists to prevent, so it
    # refuses here too rather than trusting the layer above.
    rules = [st for st in stmts if st.ast_type == ast.ASTType.Rule]
    if len(rules) > 1:
        return None            # -> layer 1 over the RAW text: nothing is lost
    for st in rules:
        return list(st.body)
    return None


def _walk(node):
    yield node
    for key in node.child_keys:
        val = getattr(node, key)
        if isinstance(val, ast.AST):
            yield from _walk(val)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, ast.AST):
                    yield from _walk(item)


def rule_bodies(text: str) -> list:
    """Every rule body in an `.lp` source, as source strings.

    Used to exercise layer-1 totality against real ASP off disk rather than
    against constructs someone remembered to think of.
    """
    stmts = []
    try:
        ast.parse_string(text, stmts.append,
                         logger=lambda code, msg: None, message_limit=0)
    except Exception:
        stmts = []
    out = [", ".join(str(lit) for lit in st.body)
           for st in stmts
           if st.ast_type == ast.ASTType.Rule and st.body]
    if out:
        return out
    # A file clingo refuses still has rules in it; read them textually rather
    # than reporting none, which would let a totality test pass vacuously.
    return [m.group(1).strip() for m in
            re.finditer(r":-\s*(.+?)\.\s*$", text, re.M)]


# ==========================================================================
#  LAYER 2 — the fluency templates
# ==========================================================================

def _terms(node):
    """A term's argument list, or [] — without asking what kind of term it is."""
    args = getattr(node, "arguments", None)
    return list(args) if args else []


def _gloss_slot(name: str, gloss: dict) -> str:
    """The written meaning of `name`, or a MARKED hole where one should be.

    ⛔ A missing gloss is NOT a missing template, and the two must not be
    conflated now that layer 1 makes templates optional. The template for `p(X)`
    exists and fits; what is absent is the definition, and saying so is the
    finding (`readback-ungloss`). Falling back to layer 1 here would report a
    renderer gap where the real gap is in the module — an earlier draft of this
    file did exactly that, and it made 10 of 106 real items look like
    unsupported ASP when every one of them was an ordinary unary atom nobody
    had written a meaning for.
    """
    if name in gloss:
        return f"{GLOSS_OPEN}{gloss[name]}{GLOSS_CLOSE}"
    return f"{UNGLOSS_MARK}{name}{UNGLOSS_CLOSE}"


def _render_symbolic(atom, gloss) -> Optional[Span]:
    """`p(X)` -> «what p means». ⛔ Never «p»: Invariant 1."""
    sym = atom.symbol
    if sym.ast_type != ast.ASTType.Function:
        return None                       # `-p(X)`, a term: no template today
    name = sym.name
    if not name:
        return None
    args = _terms(sym)
    text = _gloss_slot(name, gloss)
    # Arguments are dropped only when they are plain variables — §2.3's template
    # ("«gloss(p)» and «gloss(q)»"). A constant, interval or compound term
    # carries content, and dropping it would be silent under-rendering.
    if args and not all(a.ast_type == ast.ASTType.Variable for a in args):
        shown = ", ".join(substitute(str(a), gloss) for a in args)
        text += f" (of {shown})"
    return Span(text, 2, str(atom))


def _render_comparison(atom, gloss) -> Optional[Span]:
    parts = []
    left = substitute(str(atom.term), gloss)
    for guard in atom.guards:
        word = _CMP.get(int(guard.comparison))
        if word is None:
            return None
        parts.append(f"{left} is {word} {substitute(str(guard.term), gloss)}")
        left = substitute(str(guard.term), gloss)
    return Span(" and ".join(parts), 2, str(atom)) if parts else None


def _render_agg_element(el, gloss) -> tuple:
    terms = ", ".join(substitute(str(t), gloss) for t in el.terms)
    cond = _join([_render_literal(c, gloss) for c in el.condition])
    return terms, cond


def _render_body_aggregate(atom, gloss) -> Optional[Span]:
    """ASP2CNL's shape: *"the number of X such that Y is at least 3"*."""
    word = _AGG.get(int(atom.function))
    if word is None:
        return None
    pieces = []
    for el in atom.elements:
        terms, cond = _render_agg_element(el, gloss)
        pieces.append(f"{terms} such that {cond}" if cond else terms)
    phrase = f"the {word} of " + " or ".join(pieces)
    bounds = []
    if atom.left_guard is not None:
        op = _CMP.get(_CONVERSE[int(atom.left_guard.comparison)])
        if op is None:
            return None
        bounds.append(f"is {op} {substitute(str(atom.left_guard.term), gloss)}")
    if atom.right_guard is not None:
        op = _CMP.get(int(atom.right_guard.comparison))
        if op is None:
            return None
        bounds.append(f"is {op} {substitute(str(atom.right_guard.term), gloss)}")
    if bounds:
        phrase += " " + " and ".join(bounds)
    return Span(phrase, 2, str(atom))


def _render_conditional(node, gloss) -> Optional[Span]:
    head = _render_literal(node.literal, gloss)
    cond = _join([_render_literal(c, gloss) for c in node.condition])
    if not cond:
        return Span(head, 2, str(node))
    return Span(f"{head} for every case in which {cond}", 2, str(node))


def _render_literal(node, gloss) -> str:
    """One body element, fluent if a template fits and layer 1 if not."""
    return _render_element(node, gloss).text


def _render_element(node, gloss) -> Span:
    if node.ast_type == ast.ASTType.ConditionalLiteral:
        span = _render_conditional(node, gloss)
        return span if span is not None else _fallback(node, gloss)

    if node.ast_type != ast.ASTType.Literal:
        return _fallback(node, gloss)

    atom = node.atom
    span = None
    if atom.ast_type == ast.ASTType.SymbolicAtom:
        span = _render_symbolic(atom, gloss)
    elif atom.ast_type == ast.ASTType.Comparison:
        span = _render_comparison(atom, gloss)
    elif atom.ast_type == ast.ASTType.BodyAggregate:
        span = _render_body_aggregate(atom, gloss)
    if span is None:
        # ⚠️ The whole literal falls back, sign included — str(node) already
        # carries its own `not`, so polarity survives the fallback unchanged.
        return _fallback(node, gloss)

    # ⭐ Polarity from `Literal.sign`, never from prose (§2.2).
    text = span.text
    for _ in range(int(node.sign)):
        text = f"{NEG_MARK} {text}"
    return Span(text, span.layer, str(node))


def _join(spans_or_texts) -> str:
    parts = [s if isinstance(s, str) else s.text for s in spans_or_texts]
    return " and ".join(p for p in parts if p)


def render_body(body: Optional[str], gloss: dict) -> tuple:
    """A rule body as a tuple of `Span`s, one per conjunct. Never empty for a
    non-empty body, and never raises."""
    if not body or not body.strip():
        return ()
    nodes = _parse_body(body)
    if nodes is None:
        src = body.strip()
        return (Span(f"{ASP_MARK} {substitute(src, gloss)}{ASP_CLOSE}", 1, src),)
    return tuple(_render_element(n, gloss) for n in nodes)


def count_not(body: Optional[str]) -> int:
    """`not`s in the body, counted from the AST. Double negation counts twice."""
    nodes = _parse_body(body or "")
    if nodes is None:
        return len(re.findall(r"(?<![A-Za-z0-9_])not(?![A-Za-z0-9_])", body or ""))
    total = 0
    for node in nodes:
        for sub in _walk(node):
            if sub.ast_type == ast.ASTType.Literal:
                total += int(sub.sign)
    return total


# ==========================================================================
#  glosses
# ==========================================================================

def gloss_table(mod: schema.Module, extra: Optional[dict] = None) -> dict:
    """name -> written meaning. The module's own concepts and ontology first.

    `extra` is for the corpus-wide concept table (`concept_rows`), which is
    where a `requires` predicate defined by another clause gets its meaning.
    """
    out = dict(extra or {})
    for c in mod.concepts:
        out[c.name] = c.gloss
    for f in mod.ontology:
        out[f.atom.split("(")[0]] = f.gloss
    return out


def gloss_from_rows(rows) -> dict:
    """`schema.concept_rows()` output -> a gloss table keyed by bare name."""
    out = {}
    for row in rows:
        name = str(row["concept"]).split("/")[0]
        out.setdefault(name, row["gloss"])
    return out


def required_symbols(mod: schema.Module) -> set:
    """Every symbol a template must resolve to a written meaning.

    ⛔ Act functors are NOT in here. Nothing in the schema glosses one, and
    §2.3's template renders the act TERM from the `acts` declaration rather than
    a definition of it — see `_render_act`.
    """
    if mod.outcome != "translated":
        return set()
    need = {c.name for c in mod.concepts}
    need |= {f.atom.split("(")[0] for f in mod.ontology}
    for d in mod.defines:
        need.add(d.kind.split("(")[0])
        need.add(d.term.split("(")[0])
    for item in (*mod.asserts, *mod.beats, *mod.ontology):
        for name in _PRED_IN_BODY.findall(getattr(item, "body", None) or ""):
            need.add(name)
    return {n for n in need if n not in schema.RESERVED}


def unglossed_symbols(mod: schema.Module, extra: Optional[dict] = None) -> tuple:
    """The symbols this module needs a definition for and does not have.

    ⭐ A MISSING GLOSS, never a missing template. Layer 1 makes templates
    optional; nothing makes a written definition optional, because rendering the
    definition instead of the label is the entire mechanism (§2.3). `defines`
    has no field to hold a gloss for its `term`, so this fires on `m0053` today
    and that is the finding, not a bug in the renderer.
    """
    gloss = gloss_table(mod, extra)
    return tuple(sorted(n for n in required_symbols(mod) if n not in gloss))


# ==========================================================================
#  item renderings (§2.3)
# ==========================================================================

@dataclasses.dataclass(frozen=True)
class Rendering:
    item: str
    kind: str
    text: str
    layer: int
    source: str
    body: Optional[str] = None

    @property
    def stamp(self) -> str:
        return LAYER_STAMP[self.layer]


@dataclasses.dataclass(frozen=True)
class Finding:
    check_id: str
    severity: str
    item: Optional[str]
    message: str


def _act_span(act: str, gloss: dict, notes: list, item: str) -> Span:
    """The act term. ⚠️ Rendered as ITSELF when nothing glosses it.

    §2.3 says `act/1` renders the act term from the `acts` declaration; there is
    no gloss field for an act anywhere in the schema and no module in the corpus
    declares a concept for its own act functor. Verbifying `produce(M)` into
    *"producing the material"* needs morphology and a reading of `M` that no
    artifact supplies, so the honest rendering is the term, marked as a term and
    recorded as a note — never passed off as English.
    """
    name = act.split("(")[0]
    if name in gloss:
        return Span(f"{GLOSS_OPEN}{gloss[name]}{GLOSS_CLOSE}", 2, act)
    notes.append(Finding(
        "readback-act-literal", "note", item,
        f"act {act!r} is rendered as its own term: nothing in the module "
        f"gives {name!r} a written meaning, and the schema has no field for "
        f"one. RB1 exempts it by name rather than silently"))
    return Span(f"{ACT_MARK}{act}{ACT_CLOSE}", 2, act)


def _when(spans) -> str:
    body = _join(spans)
    return f" when {body}" if body else ""


def render_items(mod: schema.Module, gloss: dict, notes: list) -> tuple:
    out = []
    if mod.outcome != "translated":
        return ()

    for i, c in enumerate(mod.concepts):
        # The definition IS the item — there is nothing else to say about it.
        out.append(Rendering(f"concepts[{i}]", "concept",
                             f"{GLOSS_OPEN}{c.gloss}{GLOSS_CLOSE}", 2, c.sig))

    for i, f in enumerate(mod.ontology):
        name = f.atom.split("(")[0]
        args = _split_args(f.atom)
        g = f"{GLOSS_OPEN}{f.gloss}{GLOSS_CLOSE}"
        if len(args) == 1:
            head = f"{GLOSS_OPEN}{args[0]}{GLOSS_CLOSE} is {g}"
        elif not args:
            head = f"{g} holds"
        else:
            shown = ", ".join(f"{GLOSS_OPEN}{a}{GLOSS_CLOSE}" for a in args)
            head = f"{g} holds of {shown}"
        spans = render_body(f.body, gloss)
        out.append(Rendering(f"ontology[{i}]", "ontology",
                             head + _when(spans), _layer(spans), f.atom, f.body))

    for i, d in enumerate(mod.defines):
        term = _gloss_slot(d.term.split("(")[0], gloss)
        kind = _gloss_slot(d.kind.split("(")[0], gloss)
        text = f"clause {mod.clause_id} brings {term} under {kind}"
        out.append(Rendering(f"defines[{i}]", "defines", text, 2,
                             f"defines({mod.clause_id}, {d.kind}, {d.term})"))

    for i, a in enumerate(mod.asserts):
        item = f"asserts[{i}]"
        act = _act_span(a.act, gloss, notes, item)
        spans = render_body(a.body, gloss)
        text = (f"clause {mod.clause_id} {STATUS[a.status]} {act.text}"
                + _when(spans))
        out.append(Rendering(item, "asserts", text,
                             min(_layer(spans), act.layer),
                             f"asserts({mod.clause_id}, {a.status}, {a.act})",
                             a.body))

    for i, b in enumerate(mod.beats):
        spans = render_body(b.body, gloss)
        text = (f"clause {b.sayer} says clause {b.winner} outranks "
                f"clause {b.loser}" + _when(spans))
        out.append(Rendering(f"beats[{i}]", "beats", text, _layer(spans),
                             f"beats({b.sayer}, {b.winner}, {b.loser})", b.body))

    return tuple(out)


def _layer(spans) -> int:
    return min([s.layer for s in spans], default=2)


def _split_args(term: str) -> list:
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


# ==========================================================================
#  RB1 – RB5 (§2.4). Deterministic, before any model call.
# ==========================================================================

def _strip(text: str, open_mark: str, close_mark: str) -> str:
    out, i = [], 0
    while True:
        j = text.find(open_mark, i)
        if j < 0:
            out.append(text[i:])
            return "".join(out)
        k = text.find(close_mark, j)
        out.append(text[i:j])
        if k < 0:
            return "".join(out)
        i = k + len(close_mark)


def _label_set(mod: schema.Module) -> set:
    """Every name that must NOT survive into the English."""
    if mod.outcome != "translated":
        return set()
    names = {c.name for c in mod.concepts}
    names |= {f.atom.split("(")[0] for f in mod.ontology}
    names |= {p.split("/")[0] for p in mod.requires + mod.inputs}
    for d in mod.defines:
        names |= {d.kind.split("(")[0], d.term.split("(")[0]}
    return names


def _clause_ids(mod: schema.Module) -> set:
    ids = {mod.clause_id}
    for item in (*mod.concepts, *mod.ontology, *mod.asserts, *mod.beats,
                 *mod.defines):
        if getattr(item, "cites", None):
            ids.add(item.cites)
    for b in mod.beats:
        ids |= {b.sayer, b.winner, b.loser}
    return ids


def _rb1(mod, renderings) -> list:
    labels, ids = _label_set(mod), _clause_ids(mod)
    out = []
    for r in renderings:
        # An act term rendered as itself is the ONE exempt span, and it is
        # exempt because it is marked, not because it is quiet.
        scan = _strip(r.text, ACT_MARK, ACT_CLOSE)
        for cid in ids:                       # the explicit clause reference
            scan = scan.replace(f"clause {cid}", "clause")
        # ⚠️ Where the label sits changes what it MEANS, and both fire.
        # Outside a gloss, the renderer emitted a name it could not define —
        # Invariant 1's subject. Inside one, the author's own definition prose
        # reuses the word (`«a task that cannot be completed…»` for `task/1`),
        # which is a weaker finding about the gloss, not about the renderer.
        # Collapsing the two would make RB1's count unreadable: on the current
        # corpus the second kind is the majority.
        outside = _strip(scan, GLOSS_OPEN, GLOSS_CLOSE)
        for name in sorted(labels | ids):
            pat = rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])"
            if not re.search(pat, scan):
                continue
            in_gloss = not re.search(pat, outside)
            where = ("inside a gloss — the written definition reuses its own "
                     "predicate's name" if in_gloss else
                     "in the renderer's own text — no definition was available "
                     "to put there")
            out.append(Finding(
                "RB1-label-survives", "error", r.item,
                f"the label {name!r} survives into the rendering of {r.item}, "
                f"{where}. Invariant 1: a reviewer must be shown the "
                f"definition, never the name"))
    return out


def _rb2(mod, renderings, gloss) -> list:
    out = []
    for r in renderings:
        if not r.body:
            continue
        for name in sorted(set(_PRED_IN_BODY.findall(r.body))):
            g = gloss.get(name)
            if g and g not in r.text:
                out.append(Finding(
                    "RB2-missing-gloss", "error", r.item,
                    f"{r.item}: the body mentions {name!r} but its meaning is "
                    f"not in the rendering — a dropped condition reads as a "
                    f"weaker, passable sentence"))
    return out


def _markers(text: str) -> int:
    """Negation markers in the STRUCTURE of a rendering.

    ⚠️ Glosses are stripped first. A gloss reading *"text the user has not read
    carefully"* is prose about the world, not polarity about the rule, and
    counting its `not` makes RB3 fire on correct renderings.
    """
    bare = _strip(text, GLOSS_OPEN, GLOSS_CLOSE)
    n = bare.count(NEG_MARK)
    bare = bare.replace(NEG_MARK, "")
    n += len(re.findall(r"(?<![A-Za-z0-9_])not(?![A-Za-z0-9_])", bare))
    return n


def _rb3(renderings) -> list:
    out = []
    for r in renderings:
        if r.body is None:
            continue
        want, got = count_not(r.body), _markers(r.text)
        if want != got:
            out.append(Finding(
                "RB3-polarity", "error", r.item,
                f"{r.item}: body has {want} `not`, rendering shows {got} "
                f"negation marker(s). A sign lost here is a right verdict with "
                f"a reason the program cannot support"))
    return out


def _tokens(text: str) -> set:
    return set(_TOKEN.findall(text.lower()))


def echo_score(rendering_text: str, quote: str) -> float:
    """Fraction of the rendering's tokens that already occur in the clause.

    ⭐ REPORTED, NEVER USED TO FAIL. At ≈1.0 the seats are comparing the clause
    to itself and cannot discriminate at all; the honest use of that number is
    to mark their verdicts non-evidential, not to reject the clause.
    """
    have = _tokens(_strip(rendering_text, ASP_MARK, ASP_CLOSE))
    if not have:
        return 0.0
    return len(have & _tokens(quote)) / len(have)


# ==========================================================================
#  the entry point
# ==========================================================================

@dataclasses.dataclass(frozen=True)
class ModuleReadback:
    clause_id: str
    outcome: str
    renderings: tuple
    findings: tuple
    checks: dict
    echo: dict
    clause_echo: Optional[float]
    echo_level_declared: float
    non_evidential: bool

    def report(self) -> str:
        head = [f"readback {self.clause_id}  outcome={self.outcome}"]
        marks = []
        for key in ("RB1", "RB2", "RB3", "RB5"):
            val = self.checks[key]
            marks.append(f"{key}={'pass' if val else 'FIRED'}")
        if self.clause_echo is None:
            marks.append("RB4=not-measured (no clause quote given)")
        else:
            marks.append(f"RB4={self.clause_echo:.2f} vs declared "
                         f"{self.echo_level_declared:.2f} -> "
                         + ("non-evidential (4b/4d may not be counted as "
                            "evidence of faithfulness)" if self.non_evidential
                            else "evidential"))
        head.append("  " + "  ".join(marks))
        for r in self.renderings:
            echo = self.echo.get(r.item)
            tail = f"   echo={echo:.2f}" if echo is not None else ""
            head.append(f"  {r.item:<14} [{r.stamp}]{tail}\n      {r.text}")
        for f in self.findings:
            head.append(f"  {f.severity.upper():<5} {f.check_id}: {f.message}")
        return "\n".join(head)


def render_module(mod: schema.Module, *, extra_gloss: Optional[dict] = None,
                  clause_quote: Optional[str] = None,
                  echo_level: float = ECHO_LEVEL) -> ModuleReadback:
    """A validated module -> its read-back, its findings and its five checks."""
    gloss = gloss_table(mod, extra_gloss)
    notes: list = []
    renderings = render_items(mod, gloss, notes)

    findings = list(notes)
    for sym in unglossed_symbols(mod, extra_gloss):
        findings.append(Finding(
            "readback-ungloss", "error", None,
            f"no written meaning for {sym!r}. This is a MISSING GLOSS, not a "
            f"missing template — layer 1 can render any construct, but it "
            f"cannot render a definition nobody wrote. The clause does not "
            f"proceed to any seat"))

    findings += _rb1(mod, renderings)
    findings += _rb2(mod, renderings, gloss)
    findings += _rb3(renderings)

    echo, clause_echo = {}, None
    if clause_quote is not None:
        echo = {r.item: echo_score(r.text, clause_quote) for r in renderings}
        if echo:
            clause_echo = statistics.fmean(echo.values())

    checks = {
        "RB1": not any(f.check_id == "RB1-label-survives" for f in findings),
        "RB2": not any(f.check_id == "RB2-missing-gloss" for f in findings),
        "RB3": not any(f.check_id == "RB3-polarity" for f in findings),
        # ⭐ RB4 has no pass/fail by design. `None` is the value, not a gap.
        "RB4": None,
        "RB5": bool(renderings),
    }

    if not renderings:
        findings.append(Finding(
            "RB5-no-readable-content", "error", None,
            f"{mod.clause_id} rendered nothing. `no-readable-content` is an "
            f"OUTCOME, never a pass — a module with an empty read-back set "
            f"would otherwise be reported as faithful by four agreeing seats "
            f"that read nothing"))
        outcome = "no-readable-content"
    elif any(f.check_id == "readback-ungloss" for f in findings):
        outcome = "readback-ungloss"
    else:
        outcome = "rendered"

    return ModuleReadback(
        clause_id=mod.clause_id, outcome=outcome, renderings=renderings,
        findings=tuple(findings), checks=checks, echo=echo,
        clause_echo=clause_echo, echo_level_declared=echo_level,
        non_evidential=bool(clause_echo is not None
                            and clause_echo >= echo_level))
