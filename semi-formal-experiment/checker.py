"""Deterministic checker: the shared validation layer for both translation
profiles (clause->rule and behavior->derived predicate).

Check ladder, in order, cheapest first:
  1. existence  — every referenced atom exists in the vocabulary
  2. typing     — kinds/dimensions used correctly (context vs act)
  3. coherence  — the definition/rule trigger is satisfiable under the
                  vocabulary's composability axioms (via clingo); a
                  definition true in no coherent world is VACUOUS

Verdicts are structured so the translation repair loop (and eventually the
user-facing CLI) can act on them mechanically.
"""
from __future__ import annotations

import clingo

from dsl import Vocabulary, DerivedPredicate, Rule


def _axioms_to_asp(vocab: Vocabulary):
    """Compile composability axioms to ASP integrity constraints over ctx/1
    and act/1 choice atoms."""
    lines = []
    for name, atom in vocab.atoms.items():
        fn = "ctx" if atom.kind == "context" else "act"
        lines.append(f"{{ {fn}({name}) }}.")
    for ax in vocab.axioms:
        if ax.kind == "incompat":
            a, b = ax.atoms
            lines.append(f":- act({a}), act({b}).")
        elif ax.kind == "excludes":
            a, b = ax.atoms[0], ax.atoms[1]
            lines.append(f":- ctx({a}), ctx({b}).")
        elif ax.kind == "requires":
            a, b = ax.atoms
            lines.append(f":- ctx({a}), not ctx({b}).")
        elif ax.kind == "at_most_one":
            group = "; ".join(f"ctx({a})" for a in ax.atoms)
            lines.append(f":- 2 {{ {group} }}.")
    return lines


def _expr_to_asp(expr, vocab, counter=None):
    """Compile a derived-predicate expression to ASP rules defining holds_0."""
    if counter is None:
        counter = [0]
    lines = []

    def emit(e):
        counter[0] += 1
        head = f"holds_{counter[0]}"
        if isinstance(e, str):
            atom = vocab.atom(e)
            fn = "ctx" if atom and atom.kind == "context" else "act"
            lines.append(f"{head} :- {fn}({e}).")
        elif "all" in e:
            subs = [emit(x) for x in e["all"]]
            lines.append(f"{head} :- {', '.join(subs)}.")
        elif "any" in e:
            subs = [emit(x) for x in e["any"]]
            for s in subs:
                lines.append(f"{head} :- {s}.")
        elif "not" in e:
            sub = emit(e["not"])
            lines.append(f"{head} :- not {sub}.")
        return head

    top = emit(expr)
    return lines, top


class Verdict:
    def __init__(self, ok, stage, errors=None, warnings=None, witness=None):
        self.ok = ok
        self.stage = stage          # existence | typing | coherence | pass
        self.errors = errors or []
        self.warnings = warnings or []
        self.witness = witness      # satisfying world for coherent definitions

    def __repr__(self):
        s = "OK" if self.ok else f"FAIL@{self.stage}"
        return f"<Verdict {s} errors={self.errors} warnings={self.warnings}>"


def check_definition(defn: DerivedPredicate, vocab: Vocabulary) -> Verdict:
    # 1. existence — unmapped concepts are the deterministic inexpressibility signal
    missing_concepts = [c for c, a in defn.concept_map.items() if a is None]
    unknown = [a for a in defn.atoms_used() if vocab.atom(a) is None]
    if unknown or missing_concepts:
        errs = [f"unknown atom: {a}" for a in unknown]
        errs += [f"unmapped concept: {c}" for c in missing_concepts]
        return Verdict(False, "existence", errors=errs)

    # 2. typing — expression must reference at least one atom; kinds all valid
    used = defn.atoms_used()
    if not used:
        return Verdict(False, "typing", errors=["definition references no atoms"])

    # 3. coherence — satisfiable under axioms?
    lines = _axioms_to_asp(vocab)
    expr_lines, top = _expr_to_asp(defn.expr, vocab)
    lines += expr_lines
    lines.append(f":- not {top}.")
    ctl = clingo.Control(["1"])
    ctl.add("base", [], "\n".join(lines))
    ctl.ground([("base", [])])
    witness = {}

    def on_model(m):
        witness["atoms"] = sorted(
            str(s) for s in m.symbols(atoms=True) if s.name in ("ctx", "act")
        )

    res = ctl.solve(on_model=on_model)
    if not res.satisfiable:
        return Verdict(False, "coherence",
                       errors=["definition is unsatisfiable under the axioms (vacuous)"])
    w = witness.get("atoms")
    warnings = []
    if not w:
        # Satisfied by the empty world — typical of negation-heavy definitions
        # ("behavior = NOT(bad thing)"). Formally fine, useless as a query:
        # it selects no scenario and will flag no rules.
        warnings.append(
            "definition is satisfied by the empty world (no atom need be true) — "
            "usually a negation-only definition; it will match no scenario and "
            "flag no rules. Restate positively.")
    return Verdict(True, "pass", warnings=warnings, witness=w)


def check_rule(rule: Rule, vocab: Vocabulary) -> Verdict:
    errs = rule.validate(vocab)
    if errs:
        stage = "existence" if any("unknown" in e for e in errs) else "typing"
        return Verdict(False, stage, errors=errs)
    # coherence: the trigger must be satisfiable under the axioms
    lines = _axioms_to_asp(vocab)
    body = ", ".join(f"ctx({c})" for c in rule.conditions) or "#true"
    lines.append(f"trigger :- {body}.")
    lines.append(":- not trigger.")
    ctl = clingo.Control(["1"])
    ctl.add("base", [], "\n".join(lines))
    ctl.ground([("base", [])])
    res = ctl.solve()
    if not res.satisfiable:
        return Verdict(False, "coherence",
                       errors=[f"rule {rule.id}: trigger unsatisfiable under axioms (dead rule)"])
    warnings = []
    for d in rule.defeaters:
        dconds = d.get("conditions", [])
        if set(dconds) <= set(rule.conditions):
            warnings.append(
                f"rule {rule.id}: defeater {dconds} fires on the rule's own trigger — "
                "rule can never be active (adversarial-review finding 9 pattern)")
    return Verdict(True, "pass", warnings=warnings)
