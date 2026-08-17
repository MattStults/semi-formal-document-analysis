# PREREG — ARM E, per-clause RETRIEVAL of the review list

⚠️ **Written and saved BEFORE any live call, and — for §3 and §4 — before the
selector's output was ever compared against any historical defect record.**
Nothing below may be edited after the first response arrives; corrections go in
`RESULT.md`, marked as such.

---

## 1. THE QUESTION ARMS A/B/C CANNOT ANSWER

Three arms shipped **all 20 entries** of `REVIEW_LIST.md` as static prose and
returned nulls (out-of-sample 0/15 defect-free, in-sample 0/17, and 83–87% of
conclusion-changing defects named by an entry the model was holding).

Those arms confound **two different failures**:

* **(a) content unreachable by instruction** — the model reads the entry that
  names its defect and commits the defect anyway;
* **(b) signal-to-noise** — for any given clause, 16–18 of the 20 entries are
  irrelevant, the 2–4 that matter are buried in 13.6 KB of prose appended to a
  53 KB system block, and the model never attends to them.

Arm E ships **only the entries a blind selector says are relevant to this
clause**. If (b) is the cause, the defect rate falls. If (a) is the cause, it
does not — **and this arm, unlike A/B/C, can say which**, because the selector's
retrieval is measured separately from the drafting.

## 2. THE SELECTOR IS THE EXPERIMENT

`selector.py` maps a clause to a ranked subset of entries. It is **blind by
construction**: its only inputs are fields of the corpus row —

* `kind`;
* the narrowed span text (`[node narrows this span to: "…"]`, falling back to
  `SOURCE TEXT` when the node does not narrow);
* the `ESTABLISHES`, `PROVIDES` and `NEEDS` blocks of the node header;
* derived counts over those strings (word count, approximate finite-verb count,
  parenthetical presence, lexical triggers, ESTABLISHES-vs-span token
  asymmetry);
* a fixed **prior weight per entry**, copied from
  `../list_in_prompt/ORDERING.md`'s *"distinct clauses on which the entry
  produced a finding"* column.

⛔ **It reads no historical adjudication, no `*.turns.md`, no `*.lessons.md`, no
prior arm's output, and no per-clause defect record.** The prior weights are an
aggregate over 17 clauses, given to this arm in its own brief, and are the
*same 20 numbers for every clause* — they cannot encode which defect this clause
had. `selector.py` imports nothing but `json`, `re`, `os`, `sys`, `hashlib`; a
self-test in `verify_blind.py` asserts the module never opens a file outside
`node_corpus_all.json` and `promptsE/entries/`, and asserts that permuting the
clause id changes nothing while permuting the span text changes the selection.

**k is adaptive and blind:** `k = 2 + (words ≥ 25) + (words ≥ 45)`, clamped to
[2, 4], over the narrowed span. Entries below the cut are **not shipped**.

**Fixed footer.** The three ANTI-RULES (A1, A2, A3) are shipped on **every**
clause, unselected. Grounds, stated in advance: they are not checks that find
defects, they are guards that *prevent false charges* — `ORDERING.md` scores A2
as preventing ~8 false charges and A3 as inverting two drafted remedies — and a
retrieval experiment that drops the guards would confound "fewer entries" with
"fewer brakes". They total ~120 words. **The retrieval claim is over the 18
substantive entries only** (15 numbered + 3 tail bullets), and is reported as
such.

## 3. ENTRY 5 — the manufactured-defect class, FIXED not shipped as written

Entry 5's *"prefer the bodied rule over a coined constant"* was **measured to
manufacture a defect class**: obeyed correctly it converted a harmless *inert*
constant into a **vacuous bodied rule** — `no_moral_ambiguity(S) :- scenario(S)`
makes a clause the span scoped to *"scenarios where there's no moral ambiguity"*
govern **all** scenarios. Inert wastes a symbol; vacuous rewrites the document.

**Decision: FIXED, not excluded.** Grounds: excluding it would remove the
highest-prior entry that fires on `ontology` shape (8/17) and would make a null
unattributable — we could not tell "retrieval did not help" from "we deleted a
useful entry". The fix, in `promptsE/entries/E05.md`, **adds** a STOP CONDITION
and two pre-tests and deletes nothing:

1. **Scope condition vs kind.** A scope condition of the clause belongs in the
   *body* of the rule it restricts, undefined, declared in `inputs`/`requires` —
   it is not an `ontology` entry to be given a definition. Only a KIND the span
   names in its own right may be converted.
2. **Would the body be true of everything?** If the body is a universal type
   predicate (`scenario(S)`, `situation(S)`, `case(S)`, `response(R)`,
   `act(A)`) with no further condition drawn from the span, **do not write the
   rule at all** — leave the atom undefined and use it as a condition.

⚠️ This is a **deliberate departure from byte-identity** with arms B/C and is
the *only* content change to any entry. It is scored: any draft that emits a
vacuous bodied rule anyway is recorded under H2 and reported even if everything
else improves. Rejected alternative, **by name**: shipping entry 5 unchanged and
"scoring around" the manufactured defects — refused, because the brief forbids
shipping a known defect into a drafting prompt, and because a manufactured
defect inflates the defect rate in the direction of the hypothesis being tested.

## 4. WHAT IS HELD BYTE-IDENTICAL

Everything except the list. Specifically:

* `00_task.md`, `10_output_format.md`, `node_worked_example.md`,
  `30_failure_modes.md` are **read from `../list_in_prompt/promptsB/`**, the
  exact files arms B and C sent, read-only and untouched. Arm E writes no file
  under `list_in_prompt/`.
* The four are concatenated by production code (`translate.build_system`) in the
  same order, with the same `\n\n---\n\n` joiner. Only the **fifth** part —
  `40_review_list.md` → `promptsE/<clause_id>/40_review_list.md` — differs.
* Every shipped entry body is a **verbatim byte slice** of arm B's
  `40_review_list.md`, cut mechanically by `split_entries.py`. The single
  exception is E05 (§3). The arm-E preamble is new (it has to be: it tells the
  model the list is a selection) and is **identical across all 17 clauses**.
* Model, temperature, `max_tokens`, `format_forcing`, corpus, cross-references,
  user template, and the floor (`schema.validate_all` → `checks.run_checks`)
  are the insample arm's, unchanged.
* **Turn 1 only, no feedback, 17 calls in parallel** — protocol identical to
  arms B and C, so the arms differ in the review-list block and nothing else.

⚠️ **The system-block sha256 differs per clause by construction — that is the
point of the arm.** Arms B/C could pin one sha; arm E pins instead the sha256 of
(i) each of the four unchanged prompt files, (ii) each entry file, (iii) the
per-clause selection, and (iv) each assembled system block. All are recorded in
`SHAS.json` before sending. A reader can reconstruct any clause's prompt exactly.

## 5. THE COMPARISON

Paired, on the **same 17 clauses**, against the in-sample arm
(`../list_in_prompt_insample/`), which sent all 20 entries on these same
clauses under the same protocol. That is a **true paired control** — same
clause, same model, same everything but the list block.

⚠️ **Arm B's claimed `asserts`/`ontology` mix shift did not survive pairing and
was retracted.** Every mix figure here is reported **paired, per clause**
(arm E minus insample on the same clause id), with the per-clause deltas shown,
never as two aggregate means.

## 6. RETRIEVAL QUALITY IS REPORTED FIRST, AND A NULL IS SPLIT IN TWO

⛔ **Selector recall is measured and reported BEFORE any drafting result.** For
each of the 17 clauses whose historical defect is on record, I record whether
the selected set contains the entry that names that clause's **actual**
conclusion-changing defect.

**The two nulls, named in advance:**

* **NULL-A (content unreachable).** Selector recall is **high** (≥ 70% of known
  CC defects had their naming entry retrieved) **and** the defect rate does not
  fall. Reading: the entries were in front of the model, uncrowded, and it
  committed the defect anyway. Instruction is not the instrument; the argument
  moves to the schema and the graph.
* **NULL-B (retrieval is the bottleneck).** Selector recall is **low**
  (< 70%) and the defect rate does not fall. Reading: this arm did not test the
  hypothesis — a better selector is the next instrument, and the result about
  signal-to-noise is **undetermined**, not negative.

A recall figure between the two is reported as such and the null is called
**ambiguous** rather than forced into a bucket.

## 7. PRE-REGISTERED OUTCOMES

Baselines, all on record before this arm ran:

| B# | baseline (in-sample arm, all 20 entries, same 17 clauses) | value |
|---|---|---|
| **B1** | turn-1 drafts defect-free | **0 of 17** |
| **B2** | turn-1 drafts carrying a conclusion-changing defect | **17 of 17** (arm B out-of-sample: 14 of 15) |
| **B3** | CC defects named by an entry the model held | **83–87%** |

### TRANSFER (retrieval helped)
Any of:
* **T1.** ≥ 2 of 17 turn-1 drafts carry no defect I would send an edit for
  (baseline 0 of 17).
* **T2.** CC-defect rate ≤ 12 of 17 (≤ 71%), against 17 of 17.
* **T3 (the mechanism claim).** Of the CC defects that do occur, ≤ 40% are named
  by a **retrieved** entry. Under the signal-to-noise hypothesis this fraction
  should COLLAPSE relative to 83–87%: the whole claim is that a retrieved entry
  is attended to and a buried one is not.

### NULL
* 0 or 1 defect-free, **and** CC-defect rate ≥ 13 of 17, **and** the paired
  `asserts`/`ontology` mix delta is not consistently signed.
  Reported as NULL-A or NULL-B per §6.

### MANUFACTURED HARM — scored separately and reported whatever else happens
* **H1 crowding-out, inverted.** ≥ 3 drafts carry a defect in a class an entry
  the *insample* arm shipped but arm E **did not retrieve** got right on the
  same clause. This is arm E's characteristic risk: dropping 14–16 entries can
  drop a guard that was working. It is the price of the experiment and is
  measured, paired, per clause.
* **H2 obedience harm.** ≥ 1 draft carries a defect that is the direct product
  of correctly obeying a **retrieved** entry. Scored per entry. E05's vacuous
  bodied rule is pre-named as the specific shape to watch (§3).
* **H3 invention.** ≥ 3 drafts coin machinery whose only motivation is a
  retrieved entry rather than the span.
* **H4 floor regression.** ≥ 3 drafts fail the floor (`breaches > 0`) where the
  paired insample draft passed.

## 8. PREDICTIONS, ON THE RECORD

* **P-a.** Headline is **NULL**. Confidence: moderate. Grounds: two arms already
  failed on this material, and 83–87% of defects were named by a held entry —
  which is already weak evidence for NULL-A, since a *held* entry that is also
  *retrieved* changes only attention, not content.
* **P-b.** Selector recall ≥ 70%, i.e. the null (if it comes) is **NULL-A**.
  Confidence: moderate. Grounds: the trigger conditions are lexical restatements
  of each entry's own stated trigger, and most of these spans wear their trigger
  on their face (`unless`, `or`, `by default`, a parenthetical).
* **P-c.** Mean output length **falls** vs the insample arm (a shorter prompt,
  fewer checks to narrate in `claims`). Scored as a token count, paired.
  ⚠️ If length falls *and* defects fall, length is a confound and is reported as
  one — a shorter list may simply be producing terser modules with fewer places
  to be wrong.
* **P-d.** H1 fires (≥ 3): the dropped entries include working guards.
  Confidence: low-moderate. This is the honest cost of retrieval and I expect to
  pay some of it.
* **P-e.** If any single entry transfers when retrieved, it is **E1/P8** (gloss
  restates its name) — purely local, purely syntactic, needs no reading of the
  span. Scored explicitly. Same prediction arm B made and lost.

## 9. PROTOCOL COMMITMENTS

1. **Turn 1 only. No repair turns. 17 calls in parallel.**
2. ⛔ **No selector tuning after seeing drafting results.** The selector is
   frozen by sha before the first call (`SHAS.json`). If a second selector is
   wanted it is **pre-registered as a second selector**, run separately, and
   **both** are reported with both sets of results.
3. **The floor runs first** on every draft, then my span-first adjudication on
   top of it, never instead.
4. **Span-first adjudication.** Read the narrowed `SOURCE TEXT` and enumerate
   what it says before reading the module.
5. ⚠️ **CONTAMINATION DISCLOSED.** I have read `ORDERING.md` and the arm-B
   `RESULT.md` header. I know these 17 clauses are the loop's clauses and that
   each has a historical defect on record. I have **not** read the per-clause
   defect records at the time of writing §2–§4, and the selector is frozen
   before I do. But my *adjudication* of arm E's drafts is not blind to these
   clauses' histories, and that cuts in the direction of finding defects I am
   primed to look for. Every charge is written span-first with the span quoted,
   so a reader can check each one against the document rather than trusting me.
6. **n = 17, single-digit cells throughout.** Every per-class count is reported
   as such, MEASURED vs INFERRED marked. A null is a real result.

## 10. SPEND

Hard cap **$0.08**, owner-set, enforced in `run_arme.py:CAP_USD` against the
on-disk ledger before any send. Estimate: 17 calls × (≈ 41 KB system + ≈ 2 KB
user) ÷ 4 chars/token ≈ 10.8 K input tokens each, at $0.14/Mtok = **$0.026**;
output worst case 4096 tok × 17 at $0.28/Mtok = **$0.0195**. **Worst case
≈ $0.046.** Measured rate from the insample arm predicts ≈ $0.032. Refuse over.

---

**Signed before the first call, and before the selector's output was compared
against any defect record.** — adjudicator, 2026-08-16
