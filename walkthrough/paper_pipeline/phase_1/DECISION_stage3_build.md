# Step X (build record) — stage 3 as built, and the eight things `STEP_stage3.md` did not say

**Written BEFORE the code, per the repo's binding method.** Three times in this project a check was
built that measured the wrong thing and reported success; in each case the mechanism was describable
and the failing case was not. So: the passing example, the failing example, the evidence each
produces, and the cost — then the code.

`STEP_stage3.md` revision 3 is the specification. This file records **only what the specification
left open or got wrong**, and the ruling taken on each, with the alternative rejected by name. It is
not a summary of the plan.

---

## 1 The specific PASSING example

`m0217` from `runs/20260807-154618-together-deepseek-v4-flash/`, at link scope (itself alone — it
`requires` nothing).

* **3a.** Signature = `inputs ∪ head-less predicates declared in the concept table` =
  `broad_audience/1, exploits_individual/1, political_content/1`. Ground atoms:
  `broad_audience(x), exploits_individual(x), political_content(x)`. 2³ = 8 candidates, 8 coherent
  (the module declares no constraints), 0 suppressed.
* **3b.** `|R| = 1`. Deleting the single `asserts` rule changes the derived projection of exactly
  one situation ⇒ `rule 1: covered — 1 discriminating situation(s)`. Covering set = the firing
  situation plus its three single-flip neighbours = 4 of 8.
* **3c/3d.** Labels `must-permit` on `(pc,ba,¬ex)`, `must-be-silent` on the three neighbours;
  derived statuses `permit`, `silent`, `silent`, `silent` ⇒ 0 mismatches.
* **Evidence produced:** `1 must-permit · 0 must-forbid · 3 must-be-silent · 0 impossible` over a
  covering set of 4, `discriminating situations: 1`, `closure declared: produce = cepa (NOT TESTED
  HERE)`, outcome `passed`.
* **Cost:** deterministic half — 2 solves per mutant over ≤ 2^10 assignments, milliseconds.
  Labelled half — **nothing is spent by this build.** No `--live`, no API call, no key read. The
  labelled half is driven exclusively through the `client_factory` seam and every test supplies a
  stub.

## 2 The specific FAILING example

The same clause with its only rule deleted — an empty module that `link.py` still passes clean.

* Under the naive **closure-resolved** comparison the emptied module scores **8 of 8** (`cepa` ⇒
  silence permits), and stage 3 reports success on a worthless translation.
* Under the **derived-atom** comparison built here it loses `asserts(m0217,permit,produce(x))` on
  the one firing situation, the `must-permit` label no longer matches, and the module **fails**.
* `test_probe.py` test 4 pins this, with the unmutated module as the control.

And the second vacuous pass, in the other half: `m0037` — 4 claims, zero rules — is scored
`0 uncovered of 0` by any natural formulation of coverage and **passes**. Refused as
`no-testable-content`, keyed on `|R| = 0` *separately* from the empty-`acts` path (tests 14 and 17,
which must not collapse into each other).

---

## 3 Eight rulings the specification did not make (or got wrong)

### R1 — `k` counts GROUND ATOMS, not predicates, and the report prints both

`STEP_stage3.md` §6/§7 write `signature: k predicates · 2^k candidates`. On `m0217` these coincide
(3 unary predicates over one material = 3 atoms) and the conflation is invisible. It is **not** an
identity: `m0255` declares `purpose/2`, which occurs in no rule and yields **zero** ground atoms,
and declares `material_type/2`, which yields **two** (`information`, `action`). Predicate count and
candidate count are different numbers and the cost the cap exists to bound is driven by the atom
count.

⇒ The report line is `signature: P predicate(s) · A ground atom(s) · 2^A candidates · cap 2^10`, and
`probe.max_signature` bounds **A**. **Rejected by name:** *"cap the predicate count"* — it is not
the quantity that grows the enumeration, the covering set, or the seat prompt.

### R2 — the grounding domain, and its honest limit

The plan never says how a predicate becomes a ground atom. As built: for each free predicate
occurrence in a rule body, each argument position takes the constants observed there; a variable
takes the constants of any position it is bound to by a predicate with ground facts at link scope
(`forbids(P,M)` with `policy_class(P,K)` in the same body ⇒ `P ∈ {restricted_content,
sensitive_content, prohibited_content}`); a variable with no such binding takes the single
placeholder constant `x`.

⚠️ **The limit, stated rather than discovered later: one placeholder individual per unbound
position.** The enumeration therefore cannot see any situation that needs *two* distinct materials.
Every clause in the four-clause run governs one material, so nothing here is affected — and a
clause that needs two is a `signature`-level under-reach, not a mismatch. Recorded because a
coverage number that is honest per clause can still be unrepresentative in aggregate
(`STEP_stage3.md` §9, second item).

### R3 — enumeration is CHOICE RULES, one solve, not a ground-and-solve loop

`STEP_stage3.md` §7 measured the two forms at 17× apart on the same example and said 3a *should* be
built in the `witness.lp` form. It is: one `{ atom }.` per ground situation atom, one solve with
`--models 0`, and the answer sets *are* the coherent situations. A candidate the module's own
integrity constraints reject simply produces no answer set, so `suppressed = 2^A − |models|` needs
no separate well-formedness language — which is where failure mode #11 came from.

### R4 — claim→rule mapping is SUPPLIED, never inferred

§6 wants `C3: uncovered — 2 rules, 0 discriminating situations`. Nothing in a `.lp` file says which
rule carries which claim: `render_lp` emits `% [T] m0217` (a licence citation), not a claim index,
and `m0255` is hand-written. Inferring the map from `%!trace_rule` text would be a string-similarity
guess presented as structure.

⇒ `claims_map` is an explicit argument (rule index → claim id). Absent, the report carries
**rule-level** coverage only and says so. **Rejected by name:** *"match claims to rules by
trace-annotation similarity"* — a wrong map produces a confidently-named uncovered claim, which is
worse than no claim line at all.

### R5 — `probe.max_signature` lives in `probe.py`, overridable from config, not added to `config.json`

§7 says the cap is "a config constant, printed in every report, not a magic number in code". It is a
named module constant `PROBE_DEFAULTS`, read from `cfg["probe"]` when present, and printed on
**every** report including when well under. It was **not** added to `config.json`, because that file
has arm variants (`config_arm_*.json`) used by an eval harness this task is forbidden to touch, and
a key added to one side of an arm pair is a diff nobody asked for. The constant is one place, named,
and printed.

### R6 — `|R|` counts rules with a head and a body; facts and integrity constraints are counted separately

Deleting a fact is a *situation* change, and deleting an integrity constraint changes the coherent
set rather than a derived status — neither is what discrimination coverage measures. Both are
reported as their own counts so that `|R| = 0` on a module made entirely of facts is visible as
such, and refused, rather than reading as "nothing here".

### R7 — ⛔ `no acts` and `|R| = 0` gate DIFFERENT THINGS. §7 folds them into one, and that is wrong

`STEP_stage3.md` §7: *"`no-testable-content` (no acts, or `|R| = 0`)"*, one outcome for both. Its
only case is `m0037`, which carries **both**, so the difference was invisible — which is exactly why
§8 test 17 insists the two paths "must not collapse".

⛔ **`m0255` separates them in the other direction, and the plan does not notice.** It has nine
mutable rules and **no `%% acts:` header at all**: it is hand-written under the superseded contract,
with a private `lifted / binds / violation` vocabulary and no `asserts/3`. Under §7 as written,
stage 3 returns `no-testable-content` and computes nothing — so the **flagship finding §6 is built
on**, C3 being behaviourally dead, would never be reported by the tool that found it. §6 and §7 of
the same document cannot both be executed.

⇒ **`|R| = 0` stops everything** (nothing to mutate). **`no acts` stops the LABELLED half only** —
no act means no must-forbid/must-permit to compare. The outcome stays `no-testable-content`
(non-aggregating, never a pass), and the deterministic evidence is **computed and carried**, under a
`limits:` line. Discarding a real finding on a header technicality is not a refusal, it is a loss.
**Rejected by name:** *"give `m0255` a synthetic `acts` header so it reaches the [D] half"* — that
edits the artifact under test to fit the tool.

### R8 — the covering set must actually REDUCE, and the first implementation did not

⚠️ **Found by running it, not by review, and no test caught it.** `covering_set` was first written
as *"every situation belonging to some discriminating pair"*. On `m0217` that gives 4 of 8 and looks
right. On `m0255` it returned **180 of 180 coherent situations** — the enumeration, renamed.

The covering set is what the labelling **seat is shown** and what the **[L] half is priced on**, so a
reduction that reduces nothing turns one cheap call into a 180-row situation table and reports it as
a covering set. MC/DC takes **one** discriminating pair per input; bounded by 2k. `m0255` now
reduces to **9**, against `STEP_stage3.md` §6's hand-run figure of 8. Pinned by `test_7b`, with the
no-reduction version as the mutant that must kill it.

---

## 3b What the tool reproduces on `m0255`, independently of the plan

```
|R| = 9 rule(s) mutated · coverage: discrimination = 7/9 covered
  rule 7: uncovered — 0 discriminating situation(s)      ← C3
  rule 8: uncovered — 0 discriminating situation(s)      ← C3
candidates 256 · coherent 180 · suppressed 76 · covering set 9
inputs with no discriminating pair: new_material(x)
```

Both of `STEP_stage3.md` §6's measured claims come back from an implementation that was not told
about them: the two C3 rules are uncovered, and `new_material` has no discriminating pair.

⚠️ **The counts differ from §6's and the reason is the grounding (R1/R2), not a disagreement.** §6
enumerated a hand-chosen 7-predicate signature (128 candidates, 92 coherent, 36 suppressed); this
grounds `forbids/2` over the three policies the linked clauses actually declare and `material_type/2`
over both of its constants, giving 8 ground atoms (256 / 180 / 76). Same finding, larger enumeration.

---

## 4 The leak perimeter, restated as what this build may and may not emit

| origin | disclosable | why |
|---|---|---|
| `probe-structural` | ⭐ **yes** — added to `translate.DISCLOSABLE_ORIGINS` | derived from the module and the solver alone. No label, no expected verdict, is reachable from one |
| `probe-verdict` | ⛔ **no** — never added | naming the situation IS the answer key when the verdict space is two-valued in practice |

⇒ **RULING, from `STEP_stage3.md` §5, implemented here:** a `probe-verdict` mismatch **discards the
transcript and re-runs stage 1 from a clean prompt**, up to `max_retranslations` (default 1), then
the clause is carried as `probe-mismatch`. `append_findings_to_transcript` **raises** on a
`probe-verdict` finding — the refusal is a guard in code, not a convention. Rejected by name:
appending the mismatch to the transcript; disclosing the situation without the label; passing a
mismatch *count*.

⚠️ **No stage-3 label is reachable from any stage-1 or stage-2 prompt.** The labels exist only
inside `Labelling` objects and `Mismatch` objects; neither is constructible into a repair log
(`render_error_log` filters on `origin`), and the re-translation path carries an empty transcript by
construction, asserted by test 10.

## 5 What is NOT built, deliberately

* **No live labelling run.** The `[L]` half is complete and exercised against stubs. Running it
  costs money and is a separate decision (`STEP_stage3.md` §7, last line).
* **No corpus-scale run**, so the `k` histogram §9 asks for does not exist and the cap is still set
  from a cost model rather than from the corpus. Unchanged, and still the thing to measure first.
* **No `03_pipeline.md` edit.** The two departures are recorded in `STATE.md`; folding them into the
  design is a decision for its owner.
* **`xclingo` explanation-granularity projection** — `STEP_stage3.md` §0 records it as an
  observation, not adopted. Not adopted here either.
