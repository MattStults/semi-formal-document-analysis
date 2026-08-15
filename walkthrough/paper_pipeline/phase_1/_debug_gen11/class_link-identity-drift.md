# M5 — cross-module identity drift, and loss propagating from an upstream module

**Mechanism, one sentence.** The graph names shared concepts **without arity**, so a
provider and its consumers each pick an arity independently and the names never join at
link stage; and when a provider module is itself lost, every consumer inherits a link
finding it cannot fix from inside its own module.

**15 repair rounds, $0.0226 (9% of repair spend), 4 clauses, 3 modules lost — the second
worst modules-lost rank on one twentieth of M1's round count.**

---

## How to recognise it

* The finding's `where` is a **`.lp` filename**, not `<root>` or an item index — these
  are `origin: "link"` findings, produced after the module has already passed schema.
* Four check ids, all in this class: `requires-unprovided`, `unresolved-reference`,
  `concept-declared`, `situation-input`, plus `clingo-error` when the whole file is
  refused.
* The module itself is internally consistent. Repairing it in isolation cannot succeed,
  which is why these chains run the full five attempts and change almost nothing.

## The exact finding texts

```
l1_170_n043.lp: `authority_levels_hierarchy/2` is declared in `%% requires:` and no
  module in this link scope defines it
l1_170_n047.lp: `conflict/3` is used in a body, defined nowhere in this link scope, and
  declared neither in `%% inputs:` nor in `%% requires:` nor in the concept table
l1_170_n047.lp: `root_authority/1` is head-less and declared in the concept table by
  l1_170_n047
l1_170_n087.lp: `adds_intelligence_to/2` is head-less and declared as a situation input
l1_170_n043.lp: clingo refused this program, so nothing below was actually analysed:
  …/l1_170_n043.lp:46:1-72: error: unsafe variables in: | …:46:16-17: note: 'R' is unsafe
```

---

## The three lost modules, with their verbatim spans

**`l1_170_n043` — 5 attempts, 4 of them `clingo-error` only.** Verbatim (L71):

> `Root: Fundamental root rules that cannot be overridden by system messages, developers
> or users.`

The clingo message is the whole-file refusal wrapper. `TRANSLATION_CENSUS_REVIEW.md` F-7
already flagged this shape: *"`asp-syntax-refused` is a cascade wrapper… the census
records a class whose actual cause is unknown."* Confirmed here — rounds 1-4 tell the
model only that clingo refused, with the real cause (an unsafe `R` at line 46) buried in
a temp-file path. The module's true defect is M4; only at round 5 does the
`requires-unprovided` on `authority_levels_hierarchy/2` surface.

**`l1_170_n047` — 5 attempts, 4 of them the identical `conflict/3` finding, module frozen
byte-identical all five.** Verbatim (L77):

> `When two root-level principles conflict, the model should default to inaction.`

This is a **genuinely normative root rule** and it is the clearest single loss in the run.
`conflict/3` is the model's own predicate for the clause's central relation; the checker
correctly says nothing declares it, and the model never moves.

**`l1_170_n087` — 5 attempts, 14 surviving findings.** Verbatim (L159):

> `Developer: a customer of the OpenAI API. Some developers use the API to add
> intelligence to their software applications, in which case the output of the assistant
> is consumed by an application, and is typically required to follow a precise format.
> Other developers use the API to create natural language interfaces that are then
> consumed by *end users* (or act as both developers and end users themselves).`

Round 5 reports the same five names **twice** — once as `concept-declared` (*head-less and
declared in the concept table*) and once as `situation-input` (*head-less and declared as
a situation input*). The model put `adds_intelligence_to/2`, `application/1`,
`creates_interface/2`, `end_user/1`, `interface_consumed_by/2` in both places. Two checks
firing on one act doubles the apparent finding count and the repair message's length.

---

## The two sub-causes, separated

### (a) Arity is not part of a graph concept's identity — a real defect

`root_graph.production.json` records needs and provides as `{"name": …, "prose": …}`.
No arity. Measured over the `requires` + `inputs` of the 69 modules this run actually
produced, **3 of 146 distinct borrowed names carry more than one arity**:

| name | arity chosen by |
|---|---|
| `message_role_definition` | `/1` in `n072`, `n073`, `n074`, `n077`, `n082`; `/2` in `n070`, `n071` |
| `chain_of_command_principle` | `/1` in `n034`, `n041`; `/2` in `n036`, `n068` |
| `authority_levels_hierarchy` | `/2` in 17 modules; `/1` in `n061` |

The lost modules add a fourth: `root_authority` is borrowed at `/0` by `l171_426_n005`
and at `/1` by `n046` and `n047`.

`l1_170_n047` requires `root_authority/1`; the graph says `L1-170_n043` provides
`root_authority`; `n043` is lost, and even had it survived, nothing in the pipeline
guarantees it would have emitted arity 1. **This is visible with no model call at all.**

### (b) Provider loss propagates — a scheduling and amplification effect

`n047` needs `root_authority` (provider `n043`, lost). `n087` needs
`assistant_definition` (provider `n065`, lost to M1). So two of the three link losses in
this class are **downstream of M1 losses**. The modules-lost ranking in `SUMMARY.md`
attributes them to M5 because that is the surviving finding, but the causal chain runs
back to M1. `l1_170_n087` translated at 2 attempts on the 08-15 retry — once the corpus
had filled in around it.

### (c) What is NOT a defect

The standing ruling, written into the cleared graveyard entries, is explicit
(`repair_graveyard/_cleared_l1_170_n003-20260814-163512/VERDICT.md`):

> `requires-unprovided` at this point in the FULL-CORPUS run is **expected by
> construction** — at ~45 of 773 modules most providers are simply not translated yet…
> It is incompleteness, not a defect… RECHECK AT CORPUS COMPLETION.

`customer_of_openai_api/1` in `n087` is a different case: it is a name the **model**
invented and put in `requires`, and **no node in the graph provides it**. That one is a
real under-export, not incompleteness.

---

## Recovery

Only `l171_426_n002` recovered inside this run (1 repair round, `api_use_case/0`
unresolved). The other three burned all five attempts. On the 08-15 retry, under a
byte-identical prompt but a **larger link scope**, all three translated:
`n043` 1 attempt, `n047` 1 attempt, `n087` 2 attempts. That is the clean demonstration
that the link half of this class is a scheduling artefact and not a translation defect —
and equally, that spending four repair rounds on it was pure loss.

---

## The paid cost of the class

| | |
|---|---|
| repair rounds in which it appears | **15 of 130 (12%)** |
| findings | 31 |
| clauses touched | 4 |
| **attributed spend** | **$0.0226** (9%) |
| **modules lost** | **3 of 19** |

Cost rank #3, modules-lost rank #2. Note the concentration: 4 clauses, $0.0226 — the
most expensive per-clause class in the run ($0.0057/clause against M1's $0.0040).

---

## FALSIFIER

*Arity drift is a real, corpus-wide join failure.* The measurement above (3 of 146 names,
2%) is the current estimate and it is **small enough that this sub-cause could be a
curiosity rather than a mechanism**. It is wrong — i.e. the sub-cause should be dropped —
if, extended over the full corpus, the disagreement rate stays at 2% *and* no
`requires-unprovided` survives corpus completion for a name whose provider exists.
Re-run the same measurement (parse `requires`/`inputs` against each provider's exported
heads) once all 773 modules exist; the recheck is already mandated by the graveyard
`VERDICT.md` files for a different reason and should be extended to cover arity.

*Provider-loss propagation is a real amplifier.* Wrong if re-running the three clauses
with their providers present still fails. **This has already been half-tested and the
hypothesis survived**: all three translated on 08-15 with a fuller corpus.

---

## Candidate solutions already on record

* **No candidate on record targets this class.** Fixes A-F are all schema-stage or
  autofix; none of them touches link scope, arity identity, or provider ordering.
  `TRANSLATION_REPAIR_CENSUS.md` §9 records the standing caution about
  `requires-unprovided` but proposes nothing.
* The closest adjacent item is **Fix B's `cite_ids` guard rail** — *"`cite_ids` must be
  the set the checker uses, not the whole corpus… If the two sets can drift, pass nothing
  rather than a wrong set"* — which the review found already violated in live code
  (**B-3**: `translate.py:1206` computes `known_ids` as the whole 773-id corpus). That is
  the same species of bug as arity drift: the pipeline holds two notions of an identity
  and does not reconcile them. Not fatal to B; it is a separate bug B's diff would have
  exposed.
* `class_repair-fixed-point.md` covers the wasted-rounds half.

---

## Graph-stage or translation-stage?

**Sub-cause (a) is squarely graph-stage.** A concept's identity in a logic program is
`name/arity`. The graph publishes only `name`. Fixing it means the graph deciding, once,
what arity each shared concept has — a decision the graph is better placed to make than
773 independent translations, and one that costs nothing to make.

**Sub-cause (b) is a pipeline-scheduling decision, neither graph nor translation.**
Translate providers before consumers, or defer link checks until the scope is closed.
Note that the repair loop currently pays a model to fix a finding that no rewrite of that
module can clear — which is a loop-design defect.

**Sub-cause (c) is not a defect** and must not be "fixed"; see the standing ruling above
and `MODULE_MAP.md` §11 discipline.

---

## Open question for the fix pass

Link findings reach the repair loop mixed in with schema findings and phrased identically
("Fix every one of them"). **Should a finding that the module cannot possibly fix from
inside itself be sent to the model at all?** `l1_170_n047` paid four rounds to be told
four times that another module does not exist yet. Answering this needs a rule for
partitioning findings by *who can act on them* — which does not exist anywhere in
`checks.py` today.
