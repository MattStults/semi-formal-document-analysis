# SWEEP — every class any clause raised, re-asked of ALL FIVE

**Measured gap 2.** The previous loop NAMED a licence-inheritance class, called it
*"mechanically checkable; nothing checks it"*, and left it in 12 of 17 clauses **because the
loop was per-clause with no end-of-run sweep**. This file is the step that was missing.

The sweep is `sweep.py` — 17 mechanical screens, run by the coordinator over
`out/*.json` × `spans/*.prompt_user.txt`. Raw output: `SWEEP_RAW.txt`.

⚠️ **The screens are SCREENS, not verdicts.** Several fire on correct modules by
construction and are marked anti-rule-adjacent. Their job is to hand a short list to
adjudication, not to grade. Every hit below was adjudicated against the span by hand.

---

## ⭐ THE PRIMARY RESULT — what the sweep caught that the per-clause pass missed

### The borrowed-gloss manufactured citation (screen O)

**A `concepts` gloss written for a borrowed `NEEDS` name, marked `licence: "textual"` and
citing this node, for content the narrowed span never states.**

`prompt/10_output_format.md` line 66 forces the gloss to exist; the node contract makes its
content another node's; `00_task.md` says *"Do not manufacture a citation to make a fact
look textual"* and calls it **"the single worst failure available here."**

**Per-clause result — the five drafters SPLIT, and every one of them passed its own review:**

| clause | borrowed glosses | drafter's licence | caught in its own per-clause pass? |
|---|---|---|---|
| `l1001_1107_n002` | 1 | `assumed` ✅ | **yes — unprompted.** Found it alone and filed it as a prompt finding. |
| `l1001_1107_n008` | 2 | `textual` ❌ | **no.** Saw it, and deliberately followed the worked example to keep the arm measuring the prompt. Filed the prompt finding. |
| `l1001_1107_n013` | 2 | `textual` ❌ | **no.** Not raised at all in the per-clause pass. |
| `l1108_1367_n005` | 1 | `assumed` ✅ | yes — but its brief had been primed (see the confound below). |
| `l1108_1367_n010` | 1 | `assumed` ✅ | yes — same priming. |

**Every one of these five modules scored `translated`, `repair_needed: False`, zero schema
breaches, zero error-severity findings, before and after any change.** The defect and its
repair are byte-indistinguishable in every deterministic instrument the pipeline runs. That
is the class the licence field exists for, and nothing in stage 2 can see it.

**What the sweep caught that the per-clause pass did not:** `l1001_1107_n013`. Its drafter
never raised the question and its per-clause pass closed clean; the screen found it in one
run over the finished artifacts. That is the exact shape of the 12-of-17 failure, reproduced
and then caught, at slice scale.

### The licence-inheritance rule, and where it is actually taught (screen B, and PF-C)

Screen B (a `textual` conclusion resting on an `assumed` fact or a borrowed name) returned
**zero hits on all five modules** — the modules are clean. The class is nonetheless live,
and the sweep relocated it: `resolve_runs/graph_v2/node_worked_example.md` lines 184–201, the
prompt's own model heading node, marks `guideline_authority(R) :- rule_under_heading(R, …)`
as `textual` while the `rule_under_heading` concept it derives through is `assumed`.
Verified by the coordinator against the file.

⭐ **This upgrades the previous loop's finding.** It is not "mechanically checkable and
nothing checks it" — **it is taught, in the model answer, on the corpus's largest node
class.** Filed as PF-C in `PROMPT_FINDINGS.md`.

---

## ⚠️ A CONFOUND IN MY OWN INSTRUMENTATION — stated because it bounds the result above

The five drafter briefs were **not identical**. The last two dispatched (`l1108_1367_n005`,
`l1108_1367_n010`) carried an explicit "Stage 5b — the licence on every borrowed gloss"
instruction that the first three did not; it was added after the class surfaced on the
earlier clauses. So "3 of 5 clean" is **not** a clean base rate.

Reading the table with that removed: of the **three unprimed** drafters, **one** caught the
class unprompted (`n002`), one saw it and deliberately kept the defect to measure the prompt
(`n008`), and one never raised it (`n013`). The honest statement is **1 of 3 unprimed
drafters caught it**, and priming appears to work — which is itself a usable result, since
the fix is a REVIEW_LIST entry, i.e. priming.

---

## Full screen results — 5 modules

Screens returning **zero hits on all five**: B (licence-inheritance), C (inert ground atom,
N1), E (negation-as-failure, N5), F (tautology, P8), G (gloss restates name), H (undeclared
body name), I (closure coverage), J (polarity, P1), L (NEEDS/requires/inputs contract),
M (requires without gloss), N (citation id).

Zero on eleven screens is a real result on a five-module set, not a null: those eleven
encode `REVIEW_LIST` entries the drafters were given, and the drafters applied them. The
screens that DID fire are the ones no list entry covers.

### A — translated with zero `asserts` · 1 hit
`l1108_1367_n010`. **ADJUDICATED CORRECT.** The node's `ESTABLISHES`/`PROVIDES` scope it to
the authority assignment; the heading's own text (*"Don't respond with erotica or gore"*) is
the section body's content, owned by sibling nodes. Encoding it here would emit the same
`forbid` under two citations, and a duplicated prohibition is invisible in every downstream
check. The module carries its claim in `ontology`, which
`node_worked_example.md` line 211 explicitly endorses (*"`outcome` is still `translated`,
because the `ontology` entry says something the document says"*).

### D — coined symbol unanchored in the narrowed span (N10) · 2 hits
Both **ADJUDICATED CORRECT, and they expose a hole in N10 as written.**
`responds_to/2` (`l1001_1107_n013`) and `rule_under_heading/2` (`l1108_1367_n010`) are
binder relations: the span ranks a reply *against the request it answers*, and scopes a label
*to the rules under a heading*, without ever naming the relation. Both are marked `assumed`
with a named inference, which is the correct disposal.
⭐ **N10 currently supplies the diagnosis without the remedy** — applied literally it deletes
the binder, and an ontology entry with an unbound variable and no body makes the solver
reject the whole file. Candidate list entry L-4 in `LESSONS.md`.

### K — a `claims` entry carried by nothing formal (P3) · 2 hits
Both on `l1001_1107_n002`, and both **ADJUDICATED as a screen artifact of a real ambiguity**,
not as dropped content:
* C4 ("helpfulness is held alongside the obligation, not a condition on it") IS carried — by
  the `prefer be_helpful_to(U)` assert plus the *absence* of a helpfulness literal in the
  three `oblige` bodies. The screen cannot see a proposition encoded as an absence.
* C5 ("the span attaches no trigger, no exception and no defeater") is a claim **about the
  module's own shape**. `30_failure_modes.md` #11 explicitly sends unencodable structural
  statements to `claims`, so this is the field working as designed.

⭐ Both are worth a list entry anyway, from the other end: a `claims` string that is *about
the encoding* rather than *about the document* is unfalsifiable by any span comparison, and
this screen is the only thing that surfaced it. Candidate L-5.

### P — a borrowed relation's arity is uncorroborated (N8) · 2 hits
`privacy_context_dependence/2` (`l1001_1107_n008`) and `authority_levels_hierarchy/2`
(`l1108_1367_n010`). The `NEEDS` block gives these names **with no arity**; the module
invents one, never uses the predicate, and nothing in the module or the span constrains the
choice. **ADJUDICATED as N8-mitigated, not clean:** both modules state the argument order in
the gloss, which is N8's prescribed remedy and is what makes a provider mismatch surface as
a description disagreement. But N8 is about ORDER and is silent about ARITY, and an arity
mismatch is the coarser failure. Candidate L-3.

### Q — one act functor bound by disjoint sorts · 1 hit
`l1001_1107_n002`: `respect(X)` is asserted three times with `X` bound by `creator(X)`, by
`work_of(X, C)`, and by `intellectual_property_right_of(X, C)` — a person, a work, and a
legal right, all as the same argument of the same act.
**ADJUDICATED AS A REAL FINDING, and the sweep is the only thing that found it.** Neither
the drafter's four-turn review nor any REVIEW_LIST entry asks it. It is faithful to the span
(*"must respect creators, their work, and their intellectual property rights"* really does
coordinate three sorts under one verb) but the query side supplies one sort per variable, so
at most one of the three rules can ever fire against a given situation fact. This is failure
mode #3 (rules that can never fire) arriving through a route no entry names.
⭐ **Not repaired.** The repair is a schema-level question (does `respect/1` want an indexed
act, `respect(X, Sort)`?) and is above a translator's pay grade; recorded as an UNSURE and as
candidate L-1, which is the highest-value new entry this slice produced.

---

## What the sweep cost and what it is worth

`sweep.py` is ~430 lines and ran in under a second. It found one class the per-clause passes
missed on a clause that had closed clean (screen O on `l1001_1107_n013`), one class no
existing list entry covers at all (screen Q), and two holes in existing entries (N10's
missing remedy, N8's silence on arity). **Every one of the four is decidable from the module
JSON plus the span text, in a few lines of Python, and none of them is decidable by
`schema.validate_all` or `checks.run_checks`.**

The generalisable form of the finding: *the deterministic floor checks the SHAPE of a module
and the review list checks the READING of a span, and the classes that survive both are the
ones that live in the JOIN — a field whose correctness depends on text that is not in the
module.* Licence-vs-span is the type case. That join is exactly what a cross-clause sweep can
mechanise and a per-clause reader cannot.
