# Does deolingo cover our use cases?

Assessment of [deolingo](https://github.com/ovidiomanteiga/deolingo) 1.0.3 as the target
representation for clause translation. Everything below was run; commands and raw output are
reproduced verbatim.

---

## Verdict

⛔ **Covers a minority of what we need, and the part it covers best is the part we already had.
Do not adopt it as the target representation.**

Three findings decide it.

1. **The deontic operators are unary over an act.** There is no room for the *policy* that forbids
   the act. m0255's claim C2 — *"if other policies forbid producing certain material, the assistant
   should still follow them"* — is a statement quantified over policies, and the natural deolingo
   encoding cannot state it. On a case with two policies (one inside the exception's scope, one
   outside) the natural encoding returns either **UNSATISFIABLE** or **silently over-permissive**,
   depending on one authoring choice made three files away. The hand-rolled program gets it right.
   Recovering the correct answer requires putting the policy inside the act term —
   `&forbidden{produce(M, P)}` — which is an invented entity of exactly the kind Problem #1 names,
   and which reduces the deontic layer to a display layer.

2. **There is no priority/superiority relation, and permission-vs-prohibition conflict is a
   strong-negation contradiction, not a defeat.** `&permitted{p}` *is* `-&forbidden{p}`. Asserting
   both from two modules is UNSAT with no diagnostic, and `--weak` does **not** rescue it (it only
   weakens the D axiom, which is a different conflict). So "an exception module defeats a general
   module" works only if the general module was authored defeasibly in the first place — the same
   anticipation plain ASP requires, with nothing added. And "a later amendment defeats an earlier
   exception, editing neither" — Invariant 3 in its hardest form — **cannot be expressed at all**.

3. **`--explain` is broken on a spec-compliant install, and the working pin forks our explainer.**
   deolingo declares `xclingo~=2.0b12`; the repo has xclingo 2.0b24, which satisfies that
   constraint and crashes `--explain` with a `TypeError`. Pinning `xclingo==2.0b12` fixes deolingo
   and **breaks the existing hand-written walkthrough programs** — the two versions use
   incompatible `%!` annotation dialects, in both directions. Explanation is load-bearing for us
   (Problems #4, #5, #16), and the two tools cannot currently coexist in one environment.

What deolingo genuinely gives us that is worth keeping in mind: **contrary-to-duty works cleanly**,
**obligation/prohibition conflict detection via `--weak` is a real feature we do not have**, and
`&default_prohibition` is a tidier spelling of a `not`-guard. None of those is worth the
dependency; the last two are ~5 lines of plain ASP.

⚠️ Independently of any of the above: **the corpus is mostly not deontic-shaped.** See §7.

---

## 1. Does it install and run?

Yes. Clean install against the repo's existing stack.

```
$ .venv/bin/pip install --no-deps deolingo clingox python-dotenv
Successfully installed clingox-1.2.1 deolingo-1.0.3 python-dotenv-1.2.2
$ .venv/bin/python -c "import clingo;print(clingo.__version__)"
5.8.0
$ .venv/bin/deolingo --help | head -1
deolingo version 1.0.3
```

`--no-deps` is not optional in practice. The declared dependency set
(`.venv/lib/python3.10/site-packages/deolingo-1.0.3.dist-info/METADATA`) is:

```
clingo>=5.7.1, clingox>=1.2.1, cffi>=1.16.0, pycparser>=2.21, prettytable>=2.2.0,
xclingo~=2.0b12, telingo~=2.1.2, python-dotenv~=1.0.1,
langchain~=0.1.0, openai~=1.30.1, langchain-openai~=0.1.7,
gpt4all~=2.6.0, transformers~=4.40.2, google-generativeai~=0.5.3
```

A plain `pip install deolingo` drags `transformers`, `gpt4all`, `openai`, `langchain 0.1.x`
(January-2024 vintage) and `google-generativeai` into this project's venv, for an optional
`--generate` feature we would never use. That is a supply-chain surface we do not want, and the
pins are old enough to conflict with anything else.

**Maintenance signals.** Single author (79 of 80 commits), 5 stars, 0 forks, 3 open / 11 closed
issues, MIT, CI present. PyPI classifier is `Development Status :: 3 - Alpha`. Latest release
1.0.3, 2025-10-21; releases 1.0.0 (2024-06-21), 1.0.1 (2025-07-02), 1.0.2 (2025-10-12), 1.0.3
(2025-10-21). It is a Master's thesis artifact — *"Deolingo: un sistema de resolución de lógica
deóntica basado en Answer Set Programming"*, Ovidio Manteiga Moar, Universidade da Coruña, June
2024, advisor Pedro Cabalar (https://ruc.udc.es/items/14ddc385-4ba0-41be-9eac-45864ec6671e), with
a DEON 2025 system paper (https://www.dc.fi.udc.es/~cabalar/deolingo.pdf). The theory is solid
(Cabalar, Ciabattoni & van der Torre, JELIA 2023, DOI 10.1007/978-3-031-43619-2_34); the
*implementation* is one person's thesis code.

Compatibility with clingo 5.8.0: **fine for solving**, broken for `--explain` (§5).

---

## 2. ⭐ m0255 re-encoded in deolingo

### 2a. The natural encoding (v1)

Clause modules assert prohibitions; m0255 asserts a permission when the exception reaches.

`deo_m0200.lp` / `deo_m0201.lp` (definitional, one per clause):
```prolog
policy_class(restricted_content, restricted).
scope(transformation, restricted).
&default_prohibition{produce(M)} :- forbids(restricted_content, M).
```

`deo_m0203_strict.lp` — m0203 says *"should never be produced ... including transformations"*, so
its prohibition is written strictly:
```prolog
policy_class(prohibited_content, prohibited).
out_of_scope(transformation, prohibited).
&forbidden{produce(M)} :- forbids(prohibited_content, M).
```

`deo_m0255.lp`:
```prolog
% bridge: the case files say `produced/1`; the deontic layer needs the act to HOLD.
produce(M) :- produced(M).

% C1 scope limited to {restricted,sensitive}; C4 information only.
&permitted{produce(M)} :-
    forbids(P, M), policy_class(P, K), scope(transformation, K),
    transformation_of_user_content(M), material_type(M, information).

% C3: a claim about the RULE SET. deolingo has no construct for it.
%% forbid-body: permitted <- purpose

:- new_material(M), transformation_of_user_content(M).
violation(M) :- &violated_prohibition{produce(M)}.
#show violation/1.
```

Output on the four existing probe cases (`walkthrough/m0255_case_{a,b,c,d}.lp`, copied unchanged):

```
===== CASE a =====        FACTS:               SATISFIABLE     (no violation — exception lifts)
===== CASE b =====        FACTS: violation(m2) SATISFIABLE
===== CASE c =====        FACTS: violation(m3) SATISFIABLE
===== CASE d =====        FACTS: violation(m4) SATISFIABLE
```

All four match the hand-written translation. On the probes that exist, deolingo passes.

⚠️ Two things this already shows.

- **The `produced` → `produce` bridge is load-bearing and silent.** My first run omitted it. The
  program ran, was satisfiable, and reported **no violations on any case** — which reads exactly
  like "the exception lifted everything". `&violated_prohibition{X}` is `forbidden(X) ∧ holds(X)`,
  and `holds` ranges over the deontic layer's own object atoms, not over our `produced/1`. This is
  a new instance of Problem #5/#11 that only exists because of the deontic layer.
- **`&permitted{...}` prints under the `PROHIBITIONS:` heading** in deolingo's grouped output.
  Cosmetic, but a read-back hazard.

### 2b. The case the four probes never reach — and where v1 fails

Problem #12 is *"testing one branch only"*. The four probes never put **two policies on one piece
of material**, which is precisely what C2 is about. Add:

`case_e.lp`
```prolog
% ONE piece of material that two policies forbid, one inside the exception's
% scope and one outside. Document answer: still forbidden.
transformation_of_user_content(m5).
material_type(m5, information).
forbids(restricted_content, m5).
forbids(prohibited_content, m5).
produced(m5).
```

```
=== deolingo v1, m0203 STRICT ===
UNSATISFIABLE

=== deolingo v1, m0203 written defeasibly instead ===
FACTS:            SATISFIABLE          ← no violation. SILENTLY OVER-PERMISSIVE.

=== hand-rolled plain ASP (walkthrough/m0255.lp + clauses/) ===
... lifted(restricted_content,m5) unlifted(prohibited_content,m5,out_of_scope)
    binds(prohibited_content,m5) violation(prohibited_content,m5)   SATISFIABLE
```

The hand-rolled program answers correctly **and names the policy and the reason**
(`walkthrough/m0255.lp:57`, `:69`, `:86`). deolingo gives a wrong answer in both directions:

- strict m0203 → UNSAT, because `&forbidden{produce(m5)}` and
  `&permitted{produce(m5)} = -&forbidden{produce(m5)}` are a direct strong-negation contradiction.
  A question the document answers in one sentence becomes "no model".
- defeasible m0203 → the exception's permission wipes **every** prohibition on `produce(m5)`,
  including the out-of-scope one. That is C2 violated, silently, which is Problem #13
  (over-permissiveness) arriving through the representation rather than through the tests.

**`--weak` does not help.** It relaxes the deontic D axiom (`obligatory ∧ forbidden`) into a weak
constraint; the permission/prohibition clash is a strong-negation contradiction on one literal and
has no weak mode:

```
$ deolingo --weak deo_m0203_strict.lp ... case_e.lp
UNSATISFIABLE
$ deolingo --weak <(&forbidden{produce(m1)}) <(&permitted{produce(m1)})
UNSATISFIABLE
```
(compare §4d, where `--weak` *does* diagnose an obligation/prohibition clash.)

**Root cause.** `&forbidden{·}` takes the act. Which policy forbids it has nowhere to go. C2
quantifies over policies, so it needs a per-policy deontic status, and the operator does not have
that arity.

### 2c. The rescue, and what it costs (v2)

Put the policy inside the act term:

```prolog
% v2: deontic atom indexed by policy
produce(M, P) :- produced(M), forbids(P, M).
&permitted{produce(M, P)} :-
    forbids(P, M), policy_class(P, K), scope(transformation, K),
    transformation_of_user_content(M), material_type(M, information).
violation(P, M) :- &violated_prohibition{produce(M, P)}.
```
with each clause module asserting `&default_prohibition{produce(M, <its policy>)}`.

```
== v2 CASE a ==  FACTS:                                   SATISFIABLE
== v2 CASE b ==  FACTS: violation(prohibited_content,m2)  SATISFIABLE
== v2 CASE c ==  FACTS: violation(restricted_content,m3)  SATISFIABLE
== v2 CASE d ==  FACTS: violation(restricted_content,m4)  SATISFIABLE
== v2 CASE E ==  FACTS: violation(prohibited_content,m5)  SATISFIABLE
```

Correct on all five, matching the hand-rolled program exactly. But note what `produce(M, P)` *is*:
not an act. "Producing m5 under restricted_content's authority" and "producing m5 under
prohibited_content's authority" are the same act; they are two different atoms only so that the
unary operator can be applied twice. That is a made-up entity in the sense of Problem #1, sitting
inside the operator we adopted the library for. And once the policy index is in the term, the only
thing the deontic layer still computes is
`violated_prohibition(X) ≡ forbidden(X) ∧ holds(X)` — one rule.

### 2d. Does it express the four claims more directly?

| claim | hand-rolled | deolingo |
|---|---|---|
| **C1** scope = {restricted, sensitive} | guard `scope(transformation,K)` in the `lifted` rule (`m0255.lp:40`) | identical guard, in the `&permitted` rule. **No gain.** |
| **C2** other policies still bind | `unlifted/3` + `binds/2` (`m0255.lp:57–69`), per-policy and reason-carrying | **v1 cannot state it** (§2b). v2 needs the invented `produce(M,P)`. **Loss.** |
| **C3** purpose never lifts | not a world-state claim; static check `%% forbid-body: lifted <- purpose` (`m0255.lp:78`, enforced at `link.py:47,108–119`) | **deolingo has nothing.** Same static check, and `link.py`'s `RULE` regex (`link.py:48`) does not match `&permitted{...}` heads, so the check needs rewriting to keep working. **Loss.** |
| **C4** information, not actions | guard `material_type(M,information)` (`m0255.lp:40`) | identical guard. **No gain.** |

Two of four unchanged, two worse. The claim that motivated the whole clause — C2, an exception
whose scope is limited relative to a *class of other rules* — is the one deolingo cannot carry.

---

## 3. The specific things we need

### 3a. Obligation / prohibition / permission as first-class ✅

Genuinely first-class: `&obligatory{p}`, `&forbidden{p}`, `&permitted{p}`, `&omissible{p}`,
`&optional{p}`, `&deontic{p}`, plus `&holds{p}` reification. The library-supplied axioms
(`.venv/lib/python3.10/site-packages/deolingo/deontic_rules.lp`) give you O/F duality, the D axiom,
violation/fulfilment, and default closures for free. Function terms with variables work
(`&forbidden{produce(M,P)}`), which is what our corpus needs.

This is the part deolingo does well. It is also the part we were never blocked on: the hand-rolled
`binds/2`, `violation/2` cover it in three rules, and the modal reading was never the hard bit.

### 3b. ⭐ Exception in its own module defeating a rule in another module ⛔ (partial, then no)

**Test 1 — naive.** `smoke.lp` = `&forbidden{produce(m1)}.` ; `perm.lp` = `&permitted{produce(m1)}.`
Two files, neither editing the other:

```
$ deolingo smoke.lp perm.lp
UNSATISFIABLE
```

Not a defeat. A contradiction, with no diagnostic and no `--weak` escape.

**Test 2 — general rule authored defeasibly.** If the general module writes
`&default_prohibition{produce(M)}`, a separate `&permitted{produce(m1)}` file *does* defeat it:

```
$ deolingo gen_default.lp                # material(m1;m2), &default_prohibition{produce(M)}
PROHIBITIONS: &forbidden{produce(m2)}, &forbidden{produce(m1)}
$ deolingo gen_default.lp exc.lp         # exc.lp = &permitted{produce(m1)}.
PROHIBITIONS: &permitted{produce(m1)}, &forbidden{produce(m2)}
```

The plain-ASP equivalent, `&forbidden{produce(M)} :- material(M), not &permitted{produce(M)}.`,
behaves identically. So `&default_prohibition` is a nicer spelling of a `not`-guard; the
anticipation requirement — the general clause must be authored knowing that exceptions may exist —
is **exactly the same as plain ASP**. deolingo adds no modularity here.

**Test 3 — the real Invariant-3 test: an amendment that defeats an *exception*, editing neither.**
Hypothetical clause m0299, *"the transformation exception does not apply to material about an
identifiable minor, whatever the policy class"*, added as a new file:

```prolog
% deo_m0299.lp
&forbidden{produce(M,P)} :- forbids(P,M), about_minor(M).
```
```
$ deolingo v2_m0200.lp v2_m0201.lp v2_m0203.lp v2_m0255.lp deo_m0299.lp case_f.lp
UNSATISFIABLE
```

**deolingo cannot express this at all.** There is no way to say "m0299 outranks m0255". Every
route back to satisfiability requires editing m0255 to guard against m0299 — i.e. amending the
clause the document did not amend, which is the isomorphism failure Invariant 3 exists to prevent.

The plain-clingo superiority pattern handles it by adding one file and editing nothing (§8).

### 3c. Contrary-to-duty ✅

Clean, and the best thing in the tool:

```prolog
&forbidden{disclose}.
disclose.
&obligatory{notify} :- &violated_prohibition{disclose}.
```
```
FACTS: disclose
OBLIGATIONS: &obligatory{notify}
PROHIBITIONS: &forbidden{disclose}
```

`&violated_obligation`, `&fulfilled_*`, `&non_violated_*`, `&undetermined_*` are all available, and
the Chisholm's-puzzle examples shipped with the package
(`.venv/lib/python3.10/site-packages/deolingo/examples/plato/`) show the paradox handled correctly.
This is real and the paper's main contribution.

It is also ~4 lines of plain ASP for the shape we need
(`violated(P,M) :- binds(P,M), produced(M).` is already in `walkthrough/m0255.lp:86`), and we have
no clause yet that needs the paradox-robust version.

### 3d. CEPA / CNPA ⚠️ explicit and selectable, but **per-atom, not global, and not open-world**

There is no `--cepa`/`--cnpa` flag; the closure is declared per deontic atom.

CEPA (not forbidden ⇒ permitted):
```prolog
act(park;smoke).
&forbidden{smoke}.
&permitted_by_default{park}.  &permitted_by_default{smoke}.
p(X) :- &permitted{X}, act(X).
```
```
FACTS: act(park), p(park), act(smoke)
PROHIBITIONS: &forbidden{smoke}, &permitted{park}
```

CNPA (not permitted ⇒ forbidden), via `&default_prohibition`:
```
FACTS: act(park), act(smoke)
PROHIBITIONS: &permitted{park}, &forbidden{smoke}
```

Both work and are legible. ⚠️ **But the closure only ranges over atoms that are already deontic.**
`deontic_rules.lp` line `deolingo_permitted_implicitly(X) :- not deolingo_forbidden(X),
deolingo_deontic(X).` — and `deolingo_deontic(X)` holds only if some rule already made X obligatory
or forbidden. So:

```prolog
act(dance).
q :- &permitted_implicitly{dance}.        →  FACTS: act(dance)          (q NOT derived)

&forbidden{smoke}.  act(dance).  &deontic{dance}.
q :- &permitted_implicitly{dance}.        →  FACTS: q, act(dance)       (q derived)
```

You cannot ask "is this proposed behaviour permitted?" of a behaviour no clause mentions unless you
first declare it deontic. For a spec-relevance tool whose whole job is to take an arbitrary
proposed behaviour and find which clauses bear on it, that is the wrong default and has to be
worked around by enumerating a behaviour universe.

### 3e. Model enumeration ✅

Unaffected. Alternative readings enumerate normally:

```prolog
{ reading_a; reading_b } = 1.
&forbidden{produce} :- reading_a.
&permitted{produce} :- reading_b.
```
```
$ deolingo 0 enum.lp
Answer: 1  FACTS: reading_a  PROHIBITIONS: &forbidden{produce}
Answer: 2  FACTS: reading_b  PROHIBITIONS: &permitted{produce}
Models : 2
```

⛔ One restriction that matters for **witness search**: a deontic atom may not appear in a choice
rule head.

```
$ deolingo '{ &forbidden{go} }.'
g4.lp:1:3-4: error: syntax error, unexpected &
```

`walkthrough/witness.lp` only chooses ordinary situation atoms, so it survives; but you cannot ask
the solver directly to "construct a situation in which some prohibition is asserted" — you must
choose over ordinary atoms that drive the deontic ones (which does work, verified).

### 3f. ⚠️ Explanation — **this is where it fails hardest**

**(i) `--explain` is broken on a spec-compliant install.** deolingo declares `xclingo~=2.0b12`
(i.e. `>=2.0b12,<2.1`). The repo has **xclingo 2.0b24**, which satisfies it:

```
$ deolingo --explain v2_*.lp case_e.lp
File ".../deolingo/xcontrol.py", line 24, in __init__
    super().__init__(n_solutions=n_solutions, n_explanations=..., auto_trace=...)
TypeError: XclingoControl.__init__() got an unexpected keyword argument 'n_solutions'
*** ERROR: (deolingo): no message
UNKNOWN
```

`XclingoControl.__init__` in 2.0b24 takes neither `n_solutions` nor `auto_trace`. deolingo is
written against an API two betas old and its own version range does not exclude the break.

**(ii) The pin that fixes it breaks our existing programs.** With `xclingo==2.0b12` (and clingo
5.8.0 — verified, no downgrade of clingo needed), `--explain` works:

```
$ deolingo --explain v2_m0200.lp v2_m0201.lp v2_m0203.lp v2_m0255_x.lp case_e.lp
Answer 1
  *
  |__producing m5 would violate prohibited_content
```

But the same xclingo 2.0b12 cannot read the annotation dialect the walkthrough already uses:

```
$ xclingo(2.0b12) m0255.lp clauses/m0200.lp clauses/m0201.lp clauses/m0203.lp m0255_case_c.lp
RuntimeError: syntax error
```

Minimised — the two versions are mutually exclusive in **both** directions:

| annotation form | xclingo 2.0b12 | xclingo 2.0b24 |
|---|---|---|
| `%!trace_rule {"..."}.` + `%!show_trace {b}.`  (**what `walkthrough/*.lp` uses**) | `RuntimeError: syntax error` | ✅ works |
| `%!trace_rule {"..."}` + `%!show_trace b.`  (**what deolingo's examples use**) | ✅ works | `*** ERROR: (xclingo, explainer program) syntax error` |

So adopting deolingo means either rewriting every annotation in the corpus to the older dialect and
freezing xclingo at a 2024 beta, or running two environments.

**(iii) Even when it works, the explanation is shallower than what we have.** Same clause, same
case C (an action inside the exception's scope), same explainer:

```
--- hand-rolled, xclingo 2.0b24 -------------------------------------------
  |__"producing m3 would violate restricted_content"
  |  |__"restricted_content still binds"
  |  |  |__"the exception covers information only, and m3 is an action"

--- deolingo v2, xclingo 2.0b12 -------------------------------------------
  |__producing m3 would violate restricted_content
  |  |__m3 is forbidden under restricted_content
```

The reason — *it is an action, so the exception does not reach it* — is absent. It cannot be
recovered: it lives inside the library rule
`deolingo_forbidden(X) :- not deolingo_permitted(X), deolingo_default_prohibition(X)`
(`deontic_rules.lp`), i.e. behind negation-as-failure inside `site-packages`, which you cannot
annotate without editing the installed library. This is **Problem #4 reintroduced by the
dependency** — and Problem #4 is what iteration 2 of `walkthrough/m0255.lp:52–69` was written to
fix, by turning each way of failing to be lifted into its own positive atom.

**(iv) `link.py` stops working as written.** Plain clingo rejects a deolingo file
(`error: no definition found for theory atom: permitted/0`), so `link.py:120` would have to invoke
`deolingo` instead of `clingo`. The L2 head-less-atom detector survives that (deolingo forwards
clingo's `info:` messages — verified). The L3 rule-shape check does not: `link.py:48`'s `RULE`
regex matches `head(args) :- body.` and will never match a `&permitted{...}` head, so
`%% forbid-body` — the only mechanism we have for C3-shaped claims — silently stops firing. Silent,
not loud.

xASP2 was **not** tested: it is not installed and pulls a further dependency set. Given that the
deontic layer's inference is exactly what xclingo cannot see, there is no reason to expect a
different explainer to see it either — the information is not in the program, it is in
`deontic_rules.lp`.

---

## 4. What it does not cover

Verified by running each. ✅ = works, ⛔ = rejected.

| construct | result |
|---|---|
| aggregate in a rule **body** driving a deontic head (`#count`, `#max`) | ✅ `&forbidden{go} :- many.` fine; deolingo's own UDC-library example uses `#count`/`#max` |
| aggregate **inside** the deontic braces | ⛔ `error: lexer error, unexpected #count` |
| arithmetic inside the deontic term | ✅ `&obligatory{pay(X+1)} :- n(X).` → `&obligatory{pay(2)}` |
| choice rule with a deontic head | ⛔ `error: syntax error, unexpected &` (see §3e) |
| choice over ordinary atoms driving deontic heads | ✅ enumerates |
| `not` inside a deontic atom (`&obligatory{not p}`) | ⛔ rejected; README gives rewrite equivalences |
| nested modalities (`&obligatory{&obligatory{p}}`) | ⛔ rejected; README gives collapse equivalences (S5-style) |
| explicit negation of a theory atom (`-&obligatory{p}`) | ⛔ rejected; use the dual atom |
| conjunction in a deontic head / disjunction in a deontic body | ⛔ rejected (README) |
| `#minimize` / optimisation | ✅ passes through |
| **priority / superiority between rules** | ⛔ **absent — no construct, not mentioned in README or theory** |
| temporal | `--temporal` delegates to telingo; **not tested** (extra dependency, and nothing in our corpus is temporal-shaped yet) |

The nested-modality and `not`-inside restrictions are principled (DELX restricts operators to
atoms) and we have no clause that needs them. The **missing priority relation** is not a syntax
detail; it is the single feature the corpus most needs (§7).

### 4d. One thing it covers that we do not have

Obligation/prohibition conflict as a *diagnosis* rather than an error:

```
$ deolingo g8.lp                 # &obligatory{go}.  &forbidden{go}.
UNSATISFIABLE
$ deolingo --weak g8.lp
FACTS: deolingo_inconsistency(go)
Optimization: 1
```

That maps directly onto the competency question *"do these two passages conflict?"* and it is
genuinely nice. It applies only to the O/F clash, **not** to permission-vs-prohibition (§2b), which
is the clash our corpus actually produces. And it is reproducible in plain ASP in one weak
constraint.

---

## 5. Version / environment record

| component | version | note |
|---|---|---|
| clingo | 5.8.0 | repo venv, unchanged |
| deolingo | 1.0.3 | installed `--no-deps` into `semi-formal-experiment/.venv` |
| clingox | 1.2.1 | new, required |
| python-dotenv | 1.2.2 | new, required (`deolingo/__main__.py:5`) |
| xclingo | 2.0b24 (repo) / 2.0b12 (throwaway venv) | mutually exclusive dialects, §3f |
| Python | 3.10.6 | |

Solving worked on every combination tried. `--explain` requires xclingo 2.0b12; clingo may stay at
5.8.0 (5.8.1 produces a wall of `AttributeError` tracebacks but still prints, 5.7.1 is clean —
5.8.0 is clean too).

To undo: `.venv/bin/pip uninstall deolingo clingox python-dotenv`. No repo file was modified.

---

## 6. On-distribution risk — can a model generate valid deolingo?

**Estimate: low reliability for correct-and-faithful output; moderate for syntactically valid
output.** Grounds:

*Corpus availability is close to zero.* 5 stars, 0 forks, one contributor, one repo. The entire
public body of deolingo code is the **54 `.lp` example files in the package itself**, all written
by the author, plus the README's ~15 snippets. No Stack Overflow questions, no tutorials, no blog
posts, no independent adopting repositories surfaced in search. The syntax is 3 years old
(first commit 2023-10-28) and post-dates or barely overlaps most pretraining cutoffs; the DEON 2025
system paper is 2025. Contrast with plain clingo/ASP, which has a textbook, a Potassco doc site, a
decade of ASP competition benchmarks, and thousands of GitHub repos.

*What that predicts.* A frontier model asked for deolingo will (a) produce plausible-looking
`&obligatory{}`/`&forbidden{}` — those names are guessable from the deontic-logic literature —
and (b) get the *non-guessable* parts wrong: `&default_prohibition` vs `&permitted_by_default` vs
`&permitted_implicitly` (three near-synonyms with different semantics), the `&holds` bridge, the
`|` deontic-conditional operator, and the head/body restrictions in the *restricted* theory. Most
of those failures are **loud** (syntax errors), which is survivable. But the `&holds` bridge
failure is **silent** — I hit it myself in §2a while having the README and all 54 examples open,
and the symptom was a satisfiable program reporting no violations. That is the worst failure shape
this project has.

*Direct evidence from this session, offered as such:* producing a correct m0255 encoding took
reading the README, the shipped `deontic_rules.lp`, and the library/Chisholm examples, and the
first attempt was silently wrong. No paid API call was made to test generation; this is an
argument from corpus availability plus one observed instance, not a measurement.

*The comparison that matters:* Part 5 of `03_pipeline.md` records that **stage 1 has never been
run** — no model has yet produced a logic module for a clause in *any* form. Choosing deolingo
means the first run of stage 1 is confounded by an out-of-distribution target language. If stage 1
fails, we will not know whether the format is wrong or the syntax was unlearnable. That is the
"measured the wrong thing" failure this project keeps having.

---

## 7. Does the corpus even want a deontic layer?

`semi-formal-experiment/modelspec_clauses.json`, 593 clauses:

| kind | n |
|---|---|
| conditional | 188 |
| example | 183 |
| definitional | 84 |
| meta | 72 |
| holistic | 66 |

Regex counts over the quote text (whole corpus / conditional-only):

| feature | all 593 | conditional 188 |
|---|---|---|
| modal verb (should/must/may/never) | 303 (51%) | 159 (85%) |
| **authority-level language** (root/system/developer/user/guideline) | **364 (61%)** | **88 (47%)** |
| defeasible marker (by default / generally / typically) | 49 (8%) | 22 (12%) |
| exception language (unless / except / other than) | 37 (6%) | 28 (15%) |
| **override / precedence language** | 34 (6%) | 17 (9%) |
| degree / vague terms (excessive, appropriate, seemingly) | 42 (7%) | 17 (9%) |

Sampled clauses (seed 7, 12 per kind):

- **Definitional clauses carry no deontic content at all.** `m0033` *"**Root**: Fundamental root
  rules that cannot be overridden by system messages, developers or users"*, `m0039` *"**Developer**:
  Instructions given by developers using our API"*, `m0053`, `m0072`, `m0549`. These are ontology.
  deolingo contributes nothing to 84 of 593 clauses, which are also — per Invariant 1 — the seed of
  the concept dictionary.
- **The largest structural feature of the corpus is an authority ordering**, and deolingo has no
  priority relation. `m0033` is literally a statement about which rules defeat which. So is
  `m0038` (*"System-level instructions can only be supplied by OpenAI"*, root > system > developer >
  user > guideline). `levels_of_authority` is the 4th-largest section (22 clauses) and 61% of the
  corpus mentions the levels. **This is the thing we need and the thing deolingo does not have.**
- **Many "should" clauses are about manner and degree, not about a boolean act.** `m0546`
  *"avoid excessive hedging ... disclaimers ... apologies (just once per context is appropriate)"*;
  `m0500` *"By default, the assistant should adopt a professional tone ... not overly casual"*;
  `m0106` *"err on the side of asking the user for confirmation"*; `m0170` *"should assume best
  intentions"*. `&forbidden{excessive_hedging}` is a hollow stub (Problem #5) that reads correctly
  because it echoes the document's own words. The operator adds nothing; all the content is in a
  concept whose definition is missing.
- **Some are epistemic/attitudinal, not deontic at all** — `m0170` (*assume* best intentions),
  `m0325` (*emphasise positions with the strongest scientific support*), `m0399` (*the assistant may
  face uncertainty*). O/F/P is the wrong modality.

So the deontic layer is a good fit for roughly the *content-policy* sections (which m0255 sits in)
and a poor-to-irrelevant fit for the majority of the document — while the feature the majority of
the document *does* need (priority) is the one it lacks.

---

## 8. The alternative: plain clingo + a hand-written superiority pattern

Written and run. A shared defeat kernel (once, corpus-wide — **not** a clause module):

```prolog
% sup_core.lp
opposite(forbid, permit).  opposite(permit, forbid).
%!trace_rule {"% is defeated by the superior rule %", R, R2}.
defeated(R, D, A) :- asserts(R, D, A), asserts(R2, D2, A),
                     opposite(D, D2), beats(R2, R), not defeated(R2, D2, A).
%!trace_rule {"% concludes % about %, and nothing superior overrides it", R, D, A}.
because(R, D, A) :- asserts(R, D, A), not defeated(R, D, A).
%!trace_rule {"doing % would violate the rule stated by %", A, R}.
violation(A, R) :- because(R, forbid, A), done(A).
%!show_trace {violation(A,R)}.
```

Each clause module asserts `asserts(<clause id>, forbid|permit, <act>)`. m0255 additionally
declares which *class* of rules it beats — naming no individual clause and editing no file:

```prolog
asserts(m0255, permit, produce(M, P)) :-
    forbids(P, M), policy_class(P, K), scope(transformation, K),
    transformation_of_user_content(M), material_type(M, information).
beats(m0255, R) :- content_policy_rule(R),
                   asserts(R, forbid, produce(M,P)), asserts(m0255, permit, produce(M,P)).
```

Results:

```
case a : (no violation)
case b : violation(produce(m2,prohibited_content),m0203)
case c : violation(produce(m3,restricted_content),m0200)
case d : violation(produce(m4,restricted_content),m0200)
case e : violation(produce(m5,prohibited_content),m0203)      ← the C2 case deolingo v1 fails
case f, no amendment    : (no violation)
case f, + m0299.lp      : violation(produce(m6,restricted_content),m0299)
                          violation(produce(m6,restricted_content),m0200)
```

where the whole amendment is a new two-line file that edits nothing:

```prolog
% sup_m0299.lp
asserts(m0299, forbid, produce(M, P)) :- forbids(P, M), about_minor(M).
beats(m0299, m0255).
```

and it explains, on the repo's current xclingo:

```
  |__"doing produce(m3,restricted_content) would violate the rule stated by m0200"
  |  |__"m0200 concludes forbid about produce(m3,restricted_content), and nothing superior overrides it"
  |  |  |__"the restricted-content policy forbids producing m3"
```

### What we lose versus deolingo

1. `&violated_obligation` / `&fulfilled_*` / `&undetermined_*` — the full violation lattice. We
   currently use one of the ten and can write it in one rule.
2. The D axiom and `--weak`'s `deolingo_inconsistency/1`. Worth reimplementing; ~3 lines.
3. Paradox-robust contrary-to-duty in the DELX sense (Chisholm). No clause we have needs it yet.
4. The operator names being *primitive* rather than a convention — which is a real Invariant-1
   benefit (`forbid` cannot drift into meaning something else). Recoverable by declaring the
   deontic vocabulary once in the kernel and having `link.py` enforce it.

### What we gain

1. **A priority relation** — the corpus's dominant structure, absent from deolingo, and the thing
   that broke plain ASP for us *only because we had not written this kernel*.
2. **Amendment without editing** — Invariant 3 in its hardest form (case f), impossible in deolingo.
3. **The explainer we already have keeps working**, at its current version, on the annotation
   dialect already in the repo.
4. **`link.py` keeps working unchanged** — including the `%% forbid-body` static check that carries
   C3-shaped claims.
5. No dependency, no LLM stack, no alpha-status single-author package in the trust boundary.

### Honest costs of the alternative

- ⚠️ **The `beats` relation must be acyclic and this is not checked.** My first version of the
  m0255 module declared `beats(m0255, R)` for *every* opposing rule, which created
  `beats(m0299,m0255)` and `beats(m0255,m0299)` — a two-cycle in which both attackers are defeated
  and the permission silently wins. Wrong answer, no warning. This is a new, mechanically
  detectable check (`link.py` should reject cycles in `beats/2` at link scope) and it belongs on
  the Part-1 list as a 17th problem.
- ⚠️ **`not defeated(...)` is negation-as-failure, so "nothing superior overrides it" is a
  reasonless leaf** — Problem #4 again. Note this is *equally* true of deolingo (§3f(iii)) and
  worse there, because the naf sits inside `site-packages`. The only encoding that gets this right
  is the existing hand-rolled one, which enumerates the failure reasons positively
  (`unlifted(P,M,out_of_scope)`, `walkthrough/m0255.lp:57`). **Keep that pattern**; the superiority
  kernel is for cross-clause defeat, not a replacement for reason-carrying atoms inside a clause.
- The kernel is a corpus-wide artefact, which is a mild tension with "one clause, one module" — but
  it is a *fixed* artefact, not a clause, and it is the same status as the concept dictionary.

⇒ **The priority relation is the only part we actually need, and it is not the part deolingo has.**

---

## 9. What I could not test, and why

- **xASP2 on a deolingo program.** Not installed; further dependencies. Reasoning above (§3f) says
  the deontic inference is not in the user program at all, so no external explainer can see it, but
  this is an argument, not a measurement.
- **`--temporal` / telingo.** Extra dependency; nothing in the corpus is temporal-shaped yet.
- **`--generate`.** Requires an LLM provider key and a paid call. Not run. (Its existence is itself
  a signal about the project's intended use — it ships an LLM stack to write its own programs.)
- **Whether a frontier model can produce valid deolingo.** Not tested — no paid API call, per the
  brief. §6 is an argument from corpus availability plus one observed silent failure by me.
- **Grounding/performance at corpus scale.** All programs here are tiny. deolingo's `--optimize`
  mode exists specifically because the naive translation grounds badly (the translation of one
  20-line module expands to 174 lines before grounding); at 593 clauses this could matter and was
  not measured.
- **Whether the repo's ~2,156-test suite still passes with deolingo installed.** Only `--no-deps`
  packages were added (deolingo, clingox, python-dotenv) and clingo was untouched, so the risk is
  low, but the suite was not run.

---

## Appendix — reproducing

Working files are under
`/private/tmp/claude-501/.../scratchpad/deo/t/` (session-scoped; regenerate from the listings
above). The four probe cases were copied unmodified from `walkthrough/m0255_case_*.lp`; `case_e.lp`
and `case_f.lp` are new and are the two cases the existing probe set does not reach — they are
worth adding to the walkthrough regardless of which representation is chosen, since **the existing
four cases cannot distinguish a translation that satisfies C2 from one that does not** (Problem
#12, on our own worked example).
