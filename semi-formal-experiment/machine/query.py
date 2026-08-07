"""machine/query.py — ask the governance model a question instead of grepping.

    python3 machine/query.py <question> [arg]

Questions:
    seats                      every seat: tier, scaling unit, producer, validator
    human-seats                which seats are human (or human-or-frontier)?
    model-seats                which seats a model may operate
    scaling <unit>             seats whose scaling unit is <unit> (per_flip,
                               per_cycle, per_document, per_dossier, ...)
    gate <name>                what does gate <name> bind, read, refuse on?
    gates [phase]              every gate, or every gate of one phase
    phases [shape]             phase order + overridability
    constant <name>            value, source file:line, provenance, derivation
    constants                  every constant with its provenance
    artifacts [phase]          what each phase produces and consumes
    contradictions             everything rules.lp can prove is inconsistent
    disagreements              recorded prose/code disagreements
    source <fact-prefix>       the file:line behind any fact
    raw "<asp>"                run an arbitrary ASP query against the model

Everything answered here is a solve over machine/facts.lp + machine/scanned.lp
(+ machine/rules.lp for contradictions). Nothing is computed in Python.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FACTS = os.path.join(HERE, "facts.lp")
SCANNED = os.path.join(HERE, "scanned.lp")
RULES = os.path.join(HERE, "rules.lp")

BASE = [FACTS, SCANNED]


def solve(files, program: str, show: str):
    import clingo
    ctl = clingo.Control(["--warn=none"])
    for f in files:
        # strip the files' own #show directives: this call names what it wants
        text = "\n".join(l for l in open(f, encoding="utf-8").read().splitlines()
                         if not l.strip().startswith("#show"))
        ctl.add("base", [], text)
    ctl.add("base", [], program + f"\n#show {show}.\n")
    ctl.ground([("base", [])])
    out = []

    def on_model(m):
        out.clear()
        out.extend(sorted(str(s) for s in m.symbols(shown=True)))
    ctl.solve(on_model=on_model)
    return out


def _fmt(atoms, prefix="  "):
    if not atoms:
        print("  (nothing matches)")
    for a in atoms:
        print(prefix + a)


def _ans(files, program, show, header=None):
    if header:
        print(header)
    _fmt(solve(files, program, show))


# ------------------------------------------------------------- questions

def q_seats(_):
    print("seat | tier(s) | scaling unit | producer -> validator\n")
    tiers = solve(BASE, "", "seat_tier/2")
    units = solve(BASE, "", "seat_scaling_unit/2")
    prods = solve(BASE, "", "seat_producer/2")
    vals = solve(BASE, "", "seat_validator/2")
    miss = solve(BASE, "", "seat_validator_missing/1")

    def index(atoms, arity_last=True):
        d = {}
        for a in atoms:
            body = a[a.index("(") + 1:a.rindex(")")]
            k, _, v = body.partition(",")
            d.setdefault(k.strip(), []).append(v.strip().strip('"'))
        return d
    T, U, P, V = index(tiers), index(units), index(prods), index(vals)
    missing = {a[a.index("(") + 1:a.rindex(")")] for a in miss}
    for seat in sorted(set(T) | set(U) | set(P) | set(V) | missing):
        v = ", ".join(V.get(seat, [])) or (
            "*** NO VALIDATOR ***" if seat in missing else "(none recorded)")
        print(f"  {seat:22s} {'/'.join(sorted(T.get(seat, ['?']))):16s} "
              f"{','.join(U.get(seat, ['?'])):18s} "
              f"{', '.join(P.get(seat, ['-']))[:34]:36s} -> {v}")


def q_human_seats(_):
    _ans(BASE + [RULES], "", "human_seat/1",
         "seats a human occupies (a repo statement places a human in them):")


def q_model_seats(_):
    _ans(BASE + [RULES], "", "model_seat/1",
         "seats no repo statement reserves for a human (model-operable):")


def q_scaling(args):
    unit = args[0] if args else "per_flip"
    _ans(BASE, f"hit(S) :- seat_scaling_unit(S,{unit}).", "hit/1",
         f"seats scaling {unit}:")


def q_gate(args):
    if not args:
        return q_gates([])
    g = args[0]
    print(f"gate {g}\n")
    for label, show, prog in (
            ("binds (refusing it blocks this phase)", "b/1",
             f"b(P) :- gate_blocks({g},P)."),
            ("reads", "r/1", f'r(X) :- gate_reads({g},X).'),
            ("reads constant", "rc/2",
             f"rc(C,Prov) :- gate_reads_constant({g},C), provenance(C,Prov)."),
            ("refuses on", "ro/1", f"ro(X) :- gate_refuses_on({g},X)."),
            ("overridable", "ov/1",
             f"ov(yes) :- gate_blocks({g},P), overridable(P). "
             f"ov(no) :- gate_blocks({g},P), not overridable(P), phase(P)."),
            ("escape path (NOT --override)", "ep/1",
             f"ep(X) :- escape_path({g},X)."),
            ("escape validates only", "ev/1",
             f"ev(X) :- escape_validates_only({g},X)."),
            ("escape UNVERIFIED", "eu/1",
             f"eu(X) :- escape_unverified({g},X).")):
        atoms = solve(BASE + [RULES], prog, show)
        if atoms:
            print(f"  {label}:")
            _fmt(atoms, "    ")


def q_gates(args):
    if args:
        _ans(BASE, f"hit(G) :- gate_blocks(G,{args[0]}).", "hit/1",
             f"gates in front of {args[0]}:")
    else:
        _ans(BASE, "", "gate_blocks/2", "every gate and the phase it binds:")


def q_phases(args):
    shape = args[0] if args else "code"
    _ans(BASE + [RULES],
         f"p(N,P,overridable) :- phase_order({shape},P,N), overridable(P). "
         f"p(N,P,non_overridable) :- phase_order({shape},P,N), "
         f"not overridable(P).", "p/3", f"phase order for shape {shape}:")


def q_constant(args):
    if not args:
        return q_constants([])
    c = args[0]
    _ans(BASE, f"v(V) :- constant({c},V).", "v/1", f"constant {c}\n  value:")
    _ans(BASE, f"p(P) :- provenance({c},P).", "p/1", "  provenance:")
    _ans(BASE, f"d(D) :- derivation({c},D).", "d/1", "  derivation:")
    _ans(BASE, f'src(F,L) :- source(constant({c},_),F,L). '
               f'src(F,L) :- source(provenance({c},_),F,L).', "src/2",
         "  cited at:")


def q_constants(_):
    _ans(BASE, "c(C,V,P) :- constant(C,V), provenance(C,P).", "c/3",
         "constants (name, value, provenance):")


def q_artifacts(args):
    if args:
        _ans(BASE, f'x(produces,A) :- produces({args[0]},A). '
                   f'x(consumes,A) :- consumes({args[0]},A).', "x/2",
             f"artifacts of phase {args[0]}:")
    else:
        _ans(BASE, "x(P,produces,A) :- produces(P,A). "
                   "x(P,consumes,A) :- consumes(P,A).", "x/3",
             "artifacts by phase:")


def q_contradictions(args):
    kind = args[0] if args else None
    prog = f"hit(K,A,B) :- contradiction(K,A,B)." if not kind else \
        f"hit(K,A,B) :- contradiction(K,A,B), K = {kind}."
    atoms = solve(BASE + [RULES], prog, "hit/3")
    by = {}
    for a in atoms:
        k = a[a.index("(") + 1:].split(",")[0]
        by.setdefault(k, []).append(a)
    for k in sorted(by):
        print(f"\n{k}  ({len(by[k])})")
        for a in by[k][:40]:
            print("  " + a)
        if len(by[k]) > 40:
            print(f"  ... and {len(by[k]) - 40} more")
    print(f"\ntotal: {len(atoms)}")


def q_disagreements(_):
    _ans(BASE, "d(I,Prose,Code) :- disagreement(I,Prose,Code).", "d/3",
         "recorded prose/code disagreements:")


def q_source(args):
    if not args:
        print("usage: query.py source <fact-prefix>")
        return
    pre = args[0]
    atoms = solve(BASE, "s(K,F,L) :- source(K,F,L).", "s/3")
    hits = [a for a in atoms if pre in a]
    print(f"source citations matching {pre!r}:")
    _fmt(hits[:60])
    if len(hits) > 60:
        print(f"  ... and {len(hits) - 60} more")


def q_raw(args):
    prog = args[0] if args else ""
    show = args[1] if len(args) > 1 else "hit/1"
    _fmt(solve(BASE + [RULES], prog, show))


QUESTIONS = {
    "seats": q_seats, "human-seats": q_human_seats,
    "model-seats": q_model_seats, "scaling": q_scaling,
    "gate": q_gate, "gates": q_gates, "phases": q_phases,
    "constant": q_constant, "constants": q_constants,
    "artifacts": q_artifacts, "contradictions": q_contradictions,
    "disagreements": q_disagreements, "source": q_source, "raw": q_raw,
}


def main(argv) -> int:
    if len(argv) < 2 or argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    q = argv[1]
    if q not in QUESTIONS:
        print(f"unknown question {q!r}. Known: {', '.join(sorted(QUESTIONS))}")
        return 2
    QUESTIONS[q](argv[2:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
