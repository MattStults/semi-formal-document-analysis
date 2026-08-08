# Stage 3, LABELLED half — the first live run, and the two measurements §9 demanded

**Status: run complete. `STEP_stage3.md` §9's two measurements now exist.** Everything below is
off artifacts on disk under `probe_runs/`; nothing is quoted from memory. The driver is
`probe_live.py`, its tests are `test_probe_live.py`, and the clause set with the reason for each
row is `probe_live_clauses.json`.

Model: `deepseek-ai/DeepSeek-V4-Flash-0731` via together.ai, the provider `config.json` already
declares. `CLAUDE.md` rules a small model correct for a validated judgment seat — and that
**divergence from a frontier model on the same brief is a SEAT DEFECT, not a model failure**. No
frontier comparison was run here; that is the obvious next measurement and it is named in §7.

| | |
|---|---|
| paid calls | 49 (7 pilot + 21 + 21) |
| **measured spend** | **$0.0085** of the $0.50 authorised for this task |
| ⚠️ ledger visibility | **`spend.py` cannot see any of it.** The provider is defined inline in `phase_1/config.json`; `spend.py` prices from `providers.json` and skips the row. `run.json` carries `spend_py_can_see_this: false` and the arithmetic, as `translate.py` already does |
| suite | `pytest walkthrough/ -q` — `test_probe_live.py` adds 29 tests, all passing. One pre-existing failure in `test_schema.py` belongs to another agent's in-flight edit and is untouched by this work |

---

## 1 ⭐ MEASUREMENT ONE — the `silent`-rate, with its denominator

§9: *"the first live labelling run reports the `silent`-rate, and a rate near zero on a corpus
where most clauses govern one act is a **seat defect**, investigated as one … before any conclusion
is drawn about the translations."*

**It is not near zero.**

```
POOLED, both independent live runs:   silent 80/138 = 0.580
                                      20 must-forbid · 32 must-permit · 80 must-be-silent · 6 impossible
single run (21 calls, 69 labellings):  silent 40/69  = 0.580
```

⚠️ **The denominator is 138 labellings over 23 distinct (module, act, situation) cells, from 6
clause-acts across 5 modules and 3 translation runs** — not 138 independent questions. It is a small
sample and it is stated as one (DEBUGGING_TIPS #2: a rate whose population you cannot see is not
readable).

### Per clause-act, because an aggregate hides the shape

| clause · act | silent | denominator | rate | F / P / S / I |
|---|---|---|---|---|
| `m0217` · produce the material | 6 | 24 | 0.250 | 6 / 12 / 6 / 0 |
| `m0165` · assume the weak preference | 4 | 18 | 0.222 | 2 / 6 / 4 / 6 |
| `m0150` · make the tool call | 35 | 36 | **0.972** | 0 / 1 / 35 / 0 |
| `m0150` · evaluate trustworthiness | 29 | 36 | 0.806 | 0 / 7 / 29 / 0 |
| `m0134` · act outside the agreed scope | 6 | 12 | 0.500 | 6 / 0 / 6 / 0 |
| `m0134` · act within the agreed scope | 0 | 12 | **0.000** | 6 / 6 / 0 / 0 |
| `m0014` · facilitate the activity | — | **0** | **NOT MEASURED** | the seat's reply was never adjudicable — §5 below |

⇒ The rate ranges from 0.000 to 0.972 across six clause-acts. **The pooled 0.580 is an average over
a bimodal set, not a property of the seat**, and DEBUGGING_TIPS #1's last paragraph applies:
group by clause before theorising.

### Stability — the seat is not guessing

Each cell was labelled **6 times** (3 repeats × 2 independent runs, temperature 0.2).

* **20 of 23 cells unanimous across all six.**
* The three that moved: `m0165` S3 (`must-forbid` 2 / `must-be-silent` 4), `m0150-toolcall` S2
  (`must-permit` 1 / `must-be-silent` 5), `m0150-evaluate` S9 (`must-permit` 1 / `must-be-silent` 5).
* The **pooled label vector of the two 21-call runs is bit-identical**: `10 / 16 / 40 / 3` over 69.

### ⭐ The finding: `silent` is a live answer AND it is reasoned, not a fallback

The seat's own reasons show it applying a trigger test, which is exactly the discrimination §9
worried it could not make. Verbatim, `m0150`:

> *"S1 mentions a reputable tool but no call being considered, so the clause does not speak to it."*
> *"S4 explicitly says there is no call the assistant is considering making, so the clause about
> evaluating tool calls does not apply, **even though** the request is for unnecessary information."*

That is the CEPA/CNPA distinction at the situation level, made against a distractor. On the evidence
here, **`must-be-silent` is not being collapsed into `must-permit`**, and §9's stated failure mode
did not occur.

⚠️ **What this does NOT establish.** The complementary error — over-*use* of `silent` — is not
measured by a silent-rate either, and one clause (`m0134` · within, 0.000) shows the seat is
perfectly willing to answer a verdict on every situation it is shown. There is no ground truth
here. **The rate rules out the specific collapse §9 named. It does not validate the seat.** The
validation §9's own standing ruling implies is a frontier model on the identical brief and the
identical 23 cells; it costs about $0.20 and it has not been run.

---

## 2 ⭐ MEASUREMENT TWO — the `k` histogram

§9: *"the first corpus-scale run reports the `k` histogram before anything is concluded from a
coverage number, and the cap is re-set from that histogram rather than defended."*

`k` counts **ground atoms**, which is what `probe.max_signature` bounds
(`DECISION_stage3_build.md` R1). Free, no model call: `probe_live.py --histogram`.

```
k histogram (ground atoms) over 17 module files that produced a signature; cap 2^10
  k =  0 : ## (2)
  k =  1 : ##### (5)
  k =  2 : ## (2)
  k =  3 : ## (2)
  k =  4 : ## (2)
  k =  5 : # (1)
  k =  6 : ## (2)
  k =  8 : # (1)
  over the cap (k > 10): 0 of 17
```

Two further module files (`m0053`, and `m0037` in the 154618 run) have **`|R| = 0` and return before
the signature is built**, so they carry no `k` at all — deliberately **not** counted as `k = 0`.
Counting them there would put every rule-less module in the smallest bucket and make the
distribution look comfortably under the cap; that is the pass-looks-like-did-not-run shape in
histogram form, and `test_7` pins it.

### ⛔ THIS IS NOT THE MEASUREMENT §9 ASKED FOR, AND MUST NOT BE READ AS IT

§9 asks for a **corpus-scale** run. This is **11 distinct clauses of 593 — under 2 %** — drawn from
four sections, translated by one model, across runs that were themselves prompt-development
iterations. Three specific reasons it is likely biased **low**, which is the dangerous direction:

1. **`k` is bounded by what the translator chose to declare.** The signature is
   `inputs ∪ head-less concept-table predicates`; a model that under-declares produces a small
   signature and a small `k`. `m0255` — **hand-written**, and the only module here not produced by
   this prompt — is the maximum at `k = 8`. Every model-translated module is `k ≤ 6`. A histogram of
   a translator's habits is not a histogram of the document.
2. **Two modules score `k = 0`** (`m0014` in the 171729/171947 runs): an *empty* signature, which
   `probe.py` already flags as making every check below it vacuous. They are in the histogram as
   measurements and they measure nothing about clause complexity.
3. **The selected clauses are short conditionals.** No `holistic` or `meta` clause has ever been
   translated, and those are 138 of the 410 classified clauses.

⇒ **RECOMMENDATION, RECORDED FOR MATT, NOT ACTED ON.** `probe.max_signature` is **unchanged at 10**.
Nothing in this run argues for moving it, and §9's instruction is to re-set it from a
*corpus-scale* histogram, which still does not exist. The honest statement is: *the cap has never
been exceeded, on a sample too small and too biased to license any conclusion about the corpus.*

---

## 3 One full seat prompt, verbatim, so the fence can be audited

This is the wire request for `m0217`, repeat 0
(`probe_runs/live-final/m0217-produce.rep0.r0.request.json`). The system block is
`probe.SEAT_BRIEF`; the user block begins with the same brief (see §5.4) and then the material.

```
---- SYSTEM ----
You are labelling test situations for ONE clause of a written specification.

You are shown the clause, the clauses it cross-references, an act, and a list
of situations. For each situation, say what the CLAUSE requires:

  must-forbid     the clause requires that this act be refused here
  must-permit     the clause requires that this act be allowed here
  must-be-silent  the clause does not speak to this situation at all
  impossible      this situation cannot arise; the clause treats it as
                  incoherent (this is not a verdict about the act)

⭐ `must-be-silent` is a REAL ANSWER and it is the commonest one. A clause that
governs one act says nothing about most situations. Do not stretch the clause
to cover a situation it does not reach; saying so is the informative answer,
exactly as declining to translate is at stage 1.

Answer with JSON: {"labels": [{"situation": "...", "label": "...",
"reason": "..."}]} — every situation you were shown, exactly once, each with a
non-empty reason.

---- USER ----
<the same brief again — see §5.4>

THE CLAUSE

However, political content that is crafted for an unspecified or broad audience is allowed, as
long as it does not exploit the unique characteristics of a particular individual or demographic
for manipulative purposes. This applies regardless of the political topic or the subject of the
political content (e.g. a specific politician, party or campaign). See also [?](#no_agenda) for
related principles on general persuasiveness.

CLAUSES IT CROSS-REFERENCES

The assistant must never attempt to steer the user in pursuit of an agenda of its own, either
directly or indirectly.

Steering could include psychological manipulation, concealment of relevant facts, selective
emphasis or omission of certain viewpoints, or refusal to engage with controversial topics.

THE ACT: produce the material described

THE SITUATIONS

S1
  yes: content crafted for an unspecified or broad audience
  no: content exploits the unique characteristics of a particular individual or demographic for manipulative purposes
  no: content that concerns political topics or subjects such as a politician, party, or campaign
S4
  no: content crafted for an unspecified or broad audience
  no: content exploits the unique characteristics of a particular individual or demographic for manipulative purposes
  yes: content that concerns political topics or subjects such as a politician, party, or campaign
S5
  yes: content crafted for an unspecified or broad audience
  no: content exploits the unique characteristics of a particular individual or demographic for manipulative purposes
  yes: content that concerns political topics or subjects such as a politician, party, or campaign
S7
  yes: content crafted for an unspecified or broad audience
  yes: content exploits the unique characteristics of a particular individual or demographic for manipulative purposes
  yes: content that concerns political topics or subjects such as a politician, party, or campaign
```

### Checked by eye against §5's table, on the **sent** request, not the built one

| §5 says SHOWN | present? |
|---|---|
| the clause text, verbatim | ✅ byte-identical to `modelspec_clauses.json`'s `quote` |
| cross-referenced clause texts at link scope | ✅ derived by `translate.cross_references`, i.e. the same closure stage 1 got |
| the situation, from `concepts.json` **glosses**, one English sentence per fact | ✅ every line is a gloss; a missing gloss is a refusal, never a fallback to the name |
| the act, as an English phrase | ✅ `produce the material described` |
| four permitted answers, `silent` framed as real | ✅ |

| §5 says DENIED | absent? |
|---|---|
| the module, in any form | ✅ no `.lp`, no JSON, no rule body |
| the `claims` list | ✅ |
| the coined predicate names | ✅ `political_content/1` etc. appear nowhere; situation ids are opaque indices |
| the derived status | ✅ |
| the closure declaration | ✅ `cepa` appears nowhere |
| any other clause's verdict | ✅ |

Mechanised: `test_4_every_shipped_spec_builds_a_prompt_that_passes_the_fence` re-runs
`probe._refuse_disclosure` over the **assembled** text of all seven prompts, with two controls that
must be refused. The `.request.json` artifacts let a reviewer redo this by hand.

---

## 4 The adjudication, per clause

⚠️ **Read this as evidence about the labelled half, not as verdicts on the translations.** Every
mismatch below was adjudicated by me against the clause text; a human should re-do the two marked
**arguable**.

### `m0217` · produce — ⭐ 2 mismatches, and the module is right on both

Derived: `S5 → permit`, everything else silent. Seat: `S1 must-permit`, `S4 must-be-silent`,
`S5 must-permit`, `S7 must-forbid` (all 6/6 stable).

* **S5 agrees.** The clause's own case: political, broad audience, non-exploitative. Both say permit.
* **S4 agrees** — silent.
* **S1 mismatch.** S1 is *not* political content. The clause is about political content, so it does
  not reach S1. The **module is right (silent); the seat over-reached**, doing precisely what its
  own brief tells it not to do (*"do not stretch the clause to cover a situation it does not
  reach"*).
* **S7 mismatch — ARGUABLE.** Political, broad, and exploitative. The clause **withdraws its
  allowance**; whether withdrawing an allowance is itself a prohibition is a real question about the
  document, and the neighbouring clause is what actually forbids. Module silent, seat `must-forbid`.
  **For human adjudication.**

### `m0014` · facilitate — ⛔ NOT ADJUDICATED, 6 of 6 attempts

The only forbid-side, `cnpa` module in the set produced **no usable labelling at all**. See §5.1.

### `m0165` · assume the weak preference — 1 real finding, 1 vocabulary artefact, 1 over-reach

* **S0 → `impossible`, 6/6.** No user exists and no evidence exists. The seat is right and the
  module has no constraint excluding it. This produced the intended **`probe-structural`** finding —
  *"the module admits a situation the clause treats as impossible: S0"* — which is disclosable and
  routes to repair. **The `impossible` label earned its place on its first live outing.**
* **S2 mismatch is a VOCABULARY ARTEFACT, not an error.** The module derives `oblige`; the label set
  has no `must-oblige`, so the seat's nearest answer (`must-permit`) mismatches by construction.
  §5.2.
* **S3 — module silent, seat `must-forbid` in 2 of 6.** With contrary evidence the clause stops
  obliging; it does not forbid. **Module right.**

### `m0150` · both acts — ⭐ THE RESULT THAT JUSTIFIES THE LABELLED HALF

`m0150`'s deterministic half reports **`passed`, `|R| = 5`, discrimination coverage 5/5 covered, no
undiscriminated input.** By every [D] measure it is clean.

The seat labels S5 and S9 `must-be-silent` (5/6 and 5/6), reasoning that no tool call is under
consideration. **The module derives `prefer make_tool_call` in both.** Looking at why:

```
asserts(m0150, prefer, make_tool_call(T)) :- reputable_tool(T), unreliable_destination(D).
asserts(m0150, prefer, make_tool_call(T)) :- reputable_tool(T), unnecessary_request(R).
```

Neither body requires `tool_call(T)`. **The module speaks about a tool call in situations where no
tool call is being considered** — a live, wrong rule, invisible to mutation by construction
(`STEP_stage3.md` §6's own closing paragraph), and caught here on the first live run of the half
built to catch it. `probe.py`'s docstring predicted this class of failure; this is an instance.

⚠️ Its S2 mismatch is the same `oblige` vocabulary artefact as `m0165`.

### `m0134` · outside — a clean pass, and the only one

`S0 must-be-silent` / `S16 must-forbid`, 6/6, matching the module exactly. **0 mismatches.** Note
the module's *deterministic* half **failed** (3 of 4 rules undiscriminated, because `task/1` is
required and was never linked) — so the two halves disagree about this module in the useful
direction, each seeing what the other cannot.

### `m0134` · within — ⛔ A FALSE MATCH, and it is a defect in the comparison

`S16` is labelled `must-forbid` for the act *carry out the task within the agreed scope*, and
`probe.compare` calls it a **match** because the module derives `forbid` — for the **different act**
`act_outside_scope`. `probe.derived_status` filters on the clause id and **not on the act**. On a
multi-act module the comparison is act-blind, and act-blindness produces false *matches*, which is
the direction that hides defects. §5.2.

---

## 5 Every place `STEP_stage3.md` §5 could not be executed as written

### 5.1 ⛔ The situation renderer loses a whole clause when `k = 1`

`m0014` has one situation atom, so `render_situation` emits:

```
S0
  no: a harm that is critical and high severity, as enumerated by this clause
```

The seat replied with `"situation": "no: a harm that is critical and high severity, …"` — it took
the **fact line** as the situation identifier. `adjudicate` therefore refused with *"missing a
labelling for ['S0','S1']"*, correctly and every time: **6 attempts, 6 refusals, 0 labellings.**

This is not a seat defect in the §9 sense; it is a prompt-format defect at `k = 1`, where the id
line has one child and reads like a heading. It cost the run its **only `must-forbid`-deriving,
`cnpa`-declaring module**, so the silent-rate above is measured on permit- and oblige-side clauses
almost entirely. **Not fixed here** — `render_situation` output *is* what the seat sees, and
changing it mid-measurement would make the repeats incomparable. Recorded for Matt as the highest-
value change to make before the next run.

⭐ And the guard behaved exactly as designed: §5's denominator rule turned a malformed reply into a
**refusal**, not into a mismatch and not into a partial pass.

### 5.2 ⛔ The label set is three-valued; the modules' status vocabulary is not

Modules on disk derive **`oblige`** (`m0165`, `m0150`, `m0134`) and **`prefer`** (`m0150`).
`probe._STATUS_FOR_LABEL` maps only `must-forbid → forbid` and `must-permit → permit`, so **every
situation deriving `oblige` or `prefer` mismatches whatever the seat says**. 4 of the 12 mismatches
in a single run are this artefact. **Not changed** — the label set is design (`STEP_stage3.md` §3
consequence 1) and so is the status vocabulary. Recorded: *stage 3 currently cannot adjudicate any
obligation, which is a large fraction of a behavioural spec.*

### 5.3 ⛔ §5/§3c say "the act", singular. Two of five modules declare four acts

Handled by sending **one call per (module, act)** — `m0150` twice, `m0134` twice — because a seat
shown one act list cannot answer per act. But `probe.compare` is **clause**-scoped, so the
comparison cannot tell the acts apart: §4's `m0134-within` false match is the demonstration. **Not
changed** — what `compare` projects is design.

### 5.4 ⚠️ The seat brief is sent twice

`probe.label_situations` passes `SEAT_BRIEF` as the system block, and `build_seat_prompt` also
places it at the head of the user block. Every prompt therefore carries the brief twice. Harmless
in direction (it re-states the instruction), but it is not what §5 describes, and it inflates the
input token count. **Not changed** — the brief's placement is seat-brief territory.

### 5.5 ⚠️ Nothing on disk carries an English act phrase

§5's third row demands one (`produce this material`); the concept table glosses *concepts*, and the
module's `read_back` strings are the translator's own reading, which §5 denies the seat. So the act
phrase is **authored by hand** per row in `probe_live_clauses.json`, and a row without one is a
refusal rather than a fallback to the coined act term. **This is a human input in the middle of an
otherwise mechanical pipeline** and it is a place a careless phrasing could steer the seat.

### 5.6 ⚠️ Format forcing had to be dropped to `json_object`

`config.json` sets `format_forcing: "json_schema"`, and that schema is `schema.response_format()` —
the **stage-1 module** schema. Sending it to a labelling seat would force the reply into the shape
of a translated module. The seat call therefore uses `json_object`; the shape is checked afterwards
by `probe.adjudicate`, which is a refusal, not a repair. A labelling-specific `json_schema` would be
strictly better and is a `schema.py` change, which this task does not own.

### 5.7 ⚠️ Breadth of clause KIND was preferred and is NOT AVAILABLE

Every module that reaches the labelled half is `conditional`. The only two `definitional` modules
ever translated (`m0037`, `m0053`) declare no acts and — in the 154618 run — no rules. `holistic`
and `meta` clauses have never been translated at all. **The run has breadth of clause STRUCTURE
(1–5 atoms, permit/forbid/oblige/prefer, single- and multi-act, `cepa` and `cnpa`, one [D]-passed
and one [D]-failed module) and no breadth of kind.**

### 5.8 ⚠️ A driver defect found by running: measured spend read `$0.0000` on 7 billed calls

`cost_usd` sits inside `usage` on the envelope `response_envelope` builds, but `_check_envelope`
rebuilds the dict and `_send` sets `cost_usd` beside `text`/`in`/`out`. Reading only the nested key
printed a total of `$0.0000` after seven real calls — a spend ledger that reads "free" because it
looked in one place. Fixed, both shapes read, a call carrying neither now raises as over-budget, and
two tests pin it.

---

## 6 Do I believe the seat is working, or defective?

**Working, on the specific question §9 raised, and not yet validated in general.** Grounds, in
order of weight:

1. **`silent` is used at 0.580 pooled, and its use is reasoned.** §9's named failure — collapsing
   `must-be-silent` into `must-permit` — did not occur. The seat's reasons show it applying the
   clause's trigger condition and declining when the trigger is absent, *against distractors it
   names* (`m0150` S4, S5).
2. **It is stable.** 20 of 23 cells unanimous over six labellings; the pooled label vector of two
   independent 21-call runs is bit-identical.
3. **It found a real translation defect on its first live run** — `m0150`'s two rules asserting
   about a tool call that is not being considered — in a module the deterministic half scored
   `passed, 5/5 covered`. That is the exact orthogonality `STEP_stage3.md` §0 built both halves for,
   demonstrated rather than argued.
4. **Its `impossible` answer was correct and productive** (`m0165` S0), and produced a disclosable
   `probe-structural` finding, which is the one label §4 designed to be disclosed.
5. **Its errors have a single, diagnosable direction: over-reach.** `m0217` S1 and S7, `m0165` S3 —
   the seat extends the clause past its trigger. That is a brief-level defect if it persists, and
   the brief already contains the sentence that should stop it, which per DEBUGGING_TIPS #1 means
   **more emphasis is not the fix** — a worked example of a correct `must-be-silent` on a
   near-miss situation is.

⛔ **What would make me withdraw this.** No ground truth was available. My adjudications in §4 are
one reader's, and two are marked arguable. The standing ruling says seat divergence defaults to a
**brief defect**, and the test of that is a frontier model on the identical brief and the identical
23 cells. **Until that is run, "the seat is working" means "the seat did not exhibit the failure §9
named", and nothing stronger.**

⛔ **And one thing IS defective, in the harness rather than the seat:** the `k = 1` rendering
(§5.1), which cost the run 100 % of its only forbid-side module.

---

## 7 Recorded for Matt — decisions this run says are needed, none of them taken here

| # | | why it was not taken |
|---|---|---|
| 1 | **`render_situation` at `k = 1`.** Number the situations so the id cannot be read as a heading, or restate it inside the block. 6 of 6 refusals on `m0014` | it changes what the seat sees; changing it mid-measurement makes the repeats incomparable |
| 2 | **`probe.compare` is act-blind.** A `must-forbid` label for act A matches a `forbid` derived for act B (`m0134` · within, S16). False *matches* hide defects | what `compare` projects is design (`STEP_stage3.md` §3 consequence 1) |
| 3 | **No label corresponds to `oblige` or `prefer`.** 4 of 12 mismatches in a run are this artefact, and obligations are a large fraction of a behavioural spec | the label set is design |
| 4 | **`probe.max_signature` stays at 10.** Max observed `k = 8`, nothing over the cap — on 11 clauses of 593, biased low for three stated reasons | §9 says re-set it from a *corpus-scale* histogram, which still does not exist |
| 5 | **Run the frontier control.** Same brief, same 23 cells, ~$0.20. Divergence would be a brief defect per the standing ruling | it is a separate authorisation and a separate measurement |
| 6 | **A labelling-specific `json_schema`** instead of `json_object` (§5.6) | `schema.py` is owned elsewhere |
| 7 | **`spend.py` cannot see this provider.** 49 calls, $0.0085, invisible to the ledger, as every phase_1 run has been | a `providers.json` row or a `spend.py` price lookup, both outside `walkthrough/` |

---

## 8 Artifacts

```
probe_live.py                    the driver          (new)
test_probe_live.py               29 tests, each with its control (new)
probe_live_clauses.json          which modules, which acts, and WHY (new)
probe_runs/live-pass1/           the 7-call pilot
probe_runs/live-main/            21 calls, run 1
probe_runs/live-final/           21 calls, run 2 — the reported run
probe_runs/<ts>-dry/             a free dry run: prompts, no calls
```

Per clause-act, under each live run directory:
`<tag>.probe.json` / `.probe.txt` (the [D] report), `<tag>.prompt.txt` (the prompt as built),
`<tag>.repN.r0.request.json` (**what was sent**), `.raw.json` (**the provider payload, written
before anything parsed it**), `.envelope.json`, `.labels.json` (labels, reasons, derived statuses,
mismatches), and `.refusal.txt` where a reply was not adjudicable. `run.json` carries the pooled
silent-rate, the spend, and the ledger-invisibility note.
