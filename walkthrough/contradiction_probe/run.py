#!/usr/bin/env python3
"""Driver for the contradiction probe.

  semi-formal-experiment/.venv/bin/python walkthrough/contradiction_probe/run.py

Every run loads ../deontic_probe/kernel.lp UNCHANGED (including its acyclicity
guard on beats/2). No model call, no API spend, no panel access.
"""
import sys, os
import clingo

HERE = os.path.dirname(os.path.abspath(__file__))
KERNEL = os.path.join(HERE, "..", "deontic_probe", "kernel.lp")

SHOW = ("conflict", "conflict_h", "relevant", "silent", "because",
        "violation", "b_asserts", "status")


def solve(files, consts, want=SHOW, models=1):
    args = [f"-c{k}={v}" for k, v in consts.items()]
    msgs = []
    ctl = clingo.Control(args + [str(models)],
                         logger=lambda code, msg: msgs.append(msg))
    for f in files:
        ctl.load(f)
    ctl.ground([("base", [])])
    out = []
    with ctl.solve(yield_=True) as h:
        for m in h:
            out.append(sorted(str(a) for a in m.symbols(shown=True)
                              if a.name in want))
    return out, msgs


def show(title, files, consts, want=SHOW, note=""):
    print("=" * 72)
    print(title)
    if note:
        print(note)
    print("  consts:", ", ".join(f"{k}={v}" for k, v in consts.items()) or "(none)")
    print("  files :", " ".join(os.path.basename(f) for f in files))
    try:
        out, _ = solve(files, consts, want)
    except RuntimeError as e:
        print("  RUNTIME ERROR:", e)
        return
    if not out:
        print("  UNSATISFIABLE")
        return
    for m in out:
        if not m:
            print("  (satisfiable; none of the reported predicates derived)")
        for a in m:
            print("   ", a)


def F(*names):
    return [KERNEL] + [os.path.join(HERE, n) for n in names]


BASE = ("doc.lp", "behaviour.lp", "conflict.lp")

# --------------------------------------------------------------------- T1
show("T1a  the hypothesis EXACTLY as stated:  conflict(P,B) :- forbids(P,X), behaviour_requires(B,X)",
     F(*BASE, "t1_basic.lp"), dict(form="h"),
     want=("conflict_h", "conflict", "b_asserts"),
     note="  expected by the hypothesis: a conflict on the pasted bioweapon text")

show("T1b  act-indexed repair, no defeat",
     F(*BASE, "t1_basic.lp"), dict(form="act"), want=("conflict",))

show("T1c  act-indexed + defeat (the full plain form)",
     F(*BASE, "t1_basic.lp"), dict(form="defeat"), want=("conflict", "because"))

show("T1d  POLARITY: behaviour states the same content as an obligation to refuse",
     F(*BASE, "t1_basic.lp"), dict(form="defeat", bform="refuse_only"),
     want=("conflict", "b_asserts"),
     note="  m0270 and m0362 state prohibitions this way in the corpus itself")

show("T1e  ... same, with the hand-written complement/2 duality layer on",
     F(*BASE, "t1_basic.lp"), dict(form="defeat", bform="refuse_only", dual="on"),
     want=("conflict",))

show("T1f  ... the duality table as I FIRST wrote it (dual=naive)",
     F(*BASE, "t1_basic.lp"), dict(form="defeat", bform="refuse_only", dual="naive"),
     want=("conflict",),
     note="  m0198 forbids producing it and the behaviour requires refusing it.\n"
          "  They agree. The extra row is a false positive an axiom cannot make.")

# --------------------------------------------------------------------- T2
show("T2a  exception case, NO defeat refinement",
     F(*BASE, "t2_exception.lp"), dict(form="act"), want=("conflict",),
     note="  correct answer is: no conflict (m0252 is overridden by m0203 via m0255)")

show("T2b  exception case, defeat refinement on",
     F(*BASE, "t2_exception.lp"), dict(form="defeat"), want=("conflict", "because"))

show("T2c-0  the unified (one-namespace) reading, no leak file",
     F(*BASE, "t1_basic.lp", "t2_mirror.lp"), dict(form="unified"),
     want=("conflict",), note="  control: the conflict is found")

show("T2c  TYPE LEAK: unified namespace + one beats/2 fact",
     F(*BASE, "t1_basic.lp", "t2_mirror.lp", "t2_leak.lp"), dict(form="unified"),
     want=("conflict",),
     note="  same situation as T2c-0, which found a real conflict")

show("T2d  ... with the type guard on",
     F(*BASE, "t1_basic.lp", "t2_mirror.lp", "t2_leak.lp"),
     dict(form="unified", typed="on"), want=("conflict",))

show("T2e  Problem #17 control: a deliberately cyclic beats/2",
     F(*BASE, "t1_basic.lp", "t2_cycle.lp"), dict(form="defeat"), want=("conflict",),
     note="  kernel.lp's acyclicity constraint must reject this")

# --------------------------------------------------------------------- T3
show("T3a  CTD, primary norm encoded faithfully as a COMPARATIVE (prefer)",
     F(*BASE, "t3_ctd.lp"), dict(form="defeat", primary="prefer"),
     want=("conflict", "violation", "because"),
     note="  m0440 fires from a FACTUAL antecedent; x_ctd needs a violation/2")

show("T3b  ... same, primary norm collapsed to `forbid` (Problem #5)",
     F(*BASE, "t3_ctd.lp"), dict(form="defeat", primary="forbid"),
     want=("conflict", "violation", "because"))

show("T3c  CTD coverage: the same clauses with the misstep NOT yet made",
     F(*BASE, "t3_nodone.lp"), dict(form="defeat", primary="forbid"),
     want=("conflict", "violation", "status"))

# --------------------------------------------------------------------- T4
for c in ("open", "cepa", "cnpa"):
    show(f"T4  silence, closure={c}",
         F(*BASE, "t4_silence.lp"), dict(form="defeat", closure=c),
         want=("conflict", "silent"))

# --------------------------------------------------- both questions, one file
show("T5  RELEVANCE from the same behaviour file (E4 defeat reachability)",
     F(*BASE, "t1_basic.lp"), dict(form="defeat"), want=("relevant",))

show("T5-abl  ... with the act-classification ontology ablated",
     F(*BASE, "t1_basic.lp"), dict(form="defeat", onto="off"),
     want=("relevant", "conflict"))
