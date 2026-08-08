# `m0255` claim C3 is behaviourally inert

**Finding.** The two rules that encode `m0255`'s claim **C3 — "purpose never creates an
exemption"** can be deleted from `m0255.lp` without changing any answer set the example produces.
They are not dead code in the ordinary sense: they *fire*, so every rule-coverage criterion passes
them. What they conclude is already concluded by another rule, always.

The rules:

```prolog
binds(P, M) :- policy_class(P, K), K = restricted, forbids(P, M), new_material(M).
binds(P, M) :- policy_class(P, K), K = sensitive,  forbids(P, M), new_material(M).
```

⛔ Nothing here was changed. The mutant is written to a scratch copy; `m0255.lp` is untouched.

---

## What was measured

All commands run from `walkthrough/`, with

```bash
V=../semi-formal-experiment/.venv/bin/python
CL="clauses/m0200.lp clauses/m0201.lp clauses/m0203.lp"
```

Build the mutant by deleting exactly those two lines:

```bash
grep -v '^binds(P, M) :- policy_class(P, K), K = restricted, forbids(P, M), new_material(M)\.$' m0255.lp \
| grep -v '^binds(P, M) :- policy_class(P, K), K = sensitive,  forbids(P, M), new_material(M)\.$' \
> /tmp/m0255_noC3.lp
diff m0255.lp /tmp/m0255_noC3.lp        # -> exactly the two lines, nothing else
```

### 1. The rules fire

```bash
cat > /tmp/fires.lp <<'EOF'
c3_body(P,M) :- policy_class(P,K), K = restricted, forbids(P,M), new_material(M).
c3_body(P,M) :- policy_class(P,K), K = sensitive,  forbids(P,M), new_material(M).
:- not c3_body(_,_).
EOF
$V -m clingo witness.lp m0255.lp $CL /tmp/fires.lp 0
```

-> `SATISFIABLE`, **Models: 36** of the 144 the generator admits. A rule-coverage check — "is there
a situation in which this rule's body holds?" — passes both rules, 36 witnesses each way.

### 2. Deleting them changes nothing

```bash
$V -m clingo witness.lp m0255.lp           $CL 0   # -> SATISFIABLE, Models: 144
$V -m clingo witness.lp /tmp/m0255_noC3.lp $CL 0   # -> SATISFIABLE, Models: 144
```

Not merely the same count — the same answer sets. Compared as sets of atoms via `clingo`'s Python
API, the 144 original and 144 mutant answer sets are identical.

### 3. All five hand-written probe cases are unchanged

```bash
for c in a b c d e; do
  $V -m clingo m0255.lp            $CL m0255_case_$c.lp 0
  $V -m clingo /tmp/m0255_noC3.lp  $CL m0255_case_$c.lp 0
done
```

| case | original | mutant | identical |
|---|---|---|---|
| a | 1 answer set | 1 | yes |
| b | 1 | 1 | yes |
| c | 1 | 1 | yes |
| d | 1 | 1 | yes |
| e | 1 | 1 | yes |

Compared as *sets* of atoms. The raw stdout differs in two respects that are not the program's
behaviour: the mutant's file has different line numbers in clingo's `info:` warnings, and the atom
print order shifts. Case D is the one written specifically to exercise C3 — new disallowed
material offered for a research purpose — and its answer set is the same with the rules and
without them.

---

## Why: subsumption, not enumeration

This is the part that matters, because "no probe distinguished them" and "nothing can distinguish
them" are very different findings.

`m0255.lp` contains a coherence constraint added in its iteration 3:

```prolog
:- new_material(M), transformation_of_user_content(M).
```

and this rule, which is what C2 uses to catch anything the exception does not lift:

```prolog
unlifted(P, M, not_user_supplied) :- forbids(P, M), not transformation_of_user_content(M).
binds(P, M) :- unlifted(P, M, R).
```

Take any answer set in which a C3 body holds. It contains `new_material(M)` and `forbids(P, M)`.
The constraint means `transformation_of_user_content(M)` is absent, so `not_user_supplied` fires,
so `binds(P, M)` is already derived. C3's head is therefore never new — in *any* answer set of any
program containing those three lines, whatever facts or clauses are added.

That argument is a proof, not an enumeration, but it was checked mechanically as well. Ask the
mutant for a situation in which a C3 body holds and `binds` is **not** derived:

```bash
cat > /tmp/subsume.lp <<'EOF'
c3_body(P,M) :- policy_class(P,K), K = restricted, forbids(P,M), new_material(M).
c3_body(P,M) :- policy_class(P,K), K = sensitive,  forbids(P,M), new_material(M).
gap :- c3_body(P,M), not binds(P,M).
:- not gap.
EOF
$V -m clingo witness.lp /tmp/m0255_noC3.lp $CL /tmp/subsume.lp 0
```

-> **UNSATISFIABLE**. Repeated against a deliberately wider generator — two materials rather than
one, all three policies, `purpose/2` free — also **UNSATISFIABLE**, and a full answer-set
comparison over that generator's **331,776** models finds the original and the mutant identical.

=> **This is a property of the rules, not a limit of `witness.lp`.** Widening the enumeration does
not recover a difference, and the subsumption argument says widening it further never will.

### The mechanism, isolated

Delete the coherence constraint from both files and C3 stops being inert:

```bash
grep -v '^:- new_material(M), transformation_of_user_content(M)\.$' m0255.lp           > /tmp/o_nc.lp
grep -v '^:- new_material(M), transformation_of_user_content(M)\.$' /tmp/m0255_noC3.lp > /tmp/m_nc.lp
$V -m clingo witness.lp /tmp/o_nc.lp $CL 0   # -> Models: 180
$V -m clingo witness.lp /tmp/m_nc.lp $CL 0   # -> Models: 192
```

So C3 *would* do work — 12 models' worth — in a program that allowed material to be both new and a
transformation. Iteration 3's constraint rules exactly those worlds out beforehand, and in doing so
takes C3's job. The rules are inert **because of a later edit to the same file**, which is why
nothing flagged it at the time.

---

## What this means

* **Rule coverage is not enough, and this example proves it on itself.** Both C3 rules have 36
  witnesses. Every "does each rule fire?" criterion passes. The claim they encode is nonetheless
  carried entirely by a different rule, and deleting them is undetectable from behaviour. Only
  mutation — delete a rule, re-run, expect a difference — catches this class.
  This is `03_pipeline.md` Part 1 failure mode **#12**, on the pipeline's own flagship example.
* **A redundant encoding of a claim reads as an encoding of the claim.** Anyone auditing `m0255.lp`
  for "is C3 represented?" finds two rules with a `%!trace_rule` annotation naming it, and is
  right that they are there. They just do not decide anything.

## What this does **not** mean

* NOT that C3 is unrepresented or that `m0255.lp` is wrong. The module's verdicts are the same with
  the rules and without them. Nothing here shows a wrong answer.
* NOT that the rules should be deleted. They state the claim explicitly and locally; the constraint
  that subsumes them is a coherence assumption about the world, and a reader who removed the
  constraint would need them back. `m0255.lp` is deliberately unchanged.
* NOT anything about the `%% forbid-body: lifted <- purpose` declaration, which is the *other* half
  of C3 and is a static check on the rule set, not a behaviour. That half is not redundant and is
  not tested here.
* **n = 1 rule pair, 1 clause.** Nothing here estimates how often this happens.
