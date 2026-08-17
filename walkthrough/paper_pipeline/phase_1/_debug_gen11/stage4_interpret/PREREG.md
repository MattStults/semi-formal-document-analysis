# Pre-registration — stage-4 baseline interpretability (two jobs)

Written before any classification was computed and before any new model call.
Artifact under test: `_debug_gen11/stage4_baseline/out/` (81 clauses, judge
`deepseek-ai/DeepSeek-V4-Flash-0731`, the same model that wrote the
translations).

## JOB 1 — the PROVIDES-aware split of 4c's 264 `unlicensed`

**The question 4c is asked:** "does the *cited clause* license this item?"
**The question it cannot ask:** "is this name established by a *different*
node of the graph and handed to this node on purpose?"

### Decision rule, fixed before running

For every `unlicensed` judgement, extract the predicate name(s) the item is
about, from the module's own JSON (never from the reply text):

* `concepts[i]` → `concepts[i].name`
* `ontology[i]` → head atom functor of `.atom`, plus every functor in `.body`
* `asserts[i]` → `.act` functor, plus every functor in `.body`
* `defines[i]` / `beats[i]` → no predicate name is at stake; never BORROWED

A judgement is classified **BORROWED** iff **both** hold, by exact name match
against `resolve_runs/graph_v2/runs/ds7/root_graph.production.json`:

* **B1 — the graph told this node to borrow it.** The name appears in the
  judged node's own `needs` list.
* **B2 — a provider exists.** Some *other* node's `provides` list carries the
  same name.

Tiering, decided now:

* **tier BORROWED-STRICT** — B1 ∧ B2 ∧ the provider node is also in the
  81-clause in-run corpus (so `link_nodes.requires_resolution` resolves it and
  `provider_texts` could have carried the defining span).
* **tier BORROWED-DANGLING** — B1 ∧ B2 but the provider was not translated in
  this run. Still legitimate borrowing at graph level; the seat had no
  supporting text.
* **tier UNLICENSED-REAL** — everything else. This includes an invented name,
  a name the node itself was told to `provide`, and a gloss drift on a name
  that is not in `needs`.

For an `ontology`/`asserts` item, the item is BORROWED only if **every**
predicate name it mentions that is not defined by the judged node's own
`concepts` rows is a borrowed name — i.e. a mixed item where some name is
invented stays UNLICENSED-REAL. Rationale: one invented name is enough to make
the verdict a real defect.

### A secondary, weaker signal, declared now so it cannot be invented later

**gloss fidelity**: for a BORROWED `concepts[i]`, compare the module gloss to
the graph's `needs[].prose` for that name, after lowercasing, stripping
punctuation and collapsing whitespace. Report exact-match / high-overlap
(Jaccard over word sets ≥ 0.6) / drifted. A *drifted* borrowed gloss is
reported separately and is NOT counted as exonerated: the node changed the
meaning it was handed.

### What will be reported

`264 = BORROWED-STRICT + BORROWED-DANGLING + UNLICENSED-REAL`, the corrected
4c count (= UNLICENSED-REAL, with drifted-borrowed added back), and the
corrected clause-level headline over the same 81.

### What can make this fail honestly

If the module's concept names do not join to graph `needs` names by exact
match at a decent rate, the join is not sound and the answer is "cannot be
corrected with the data on disk". Threshold fixed now: if fewer than **60%**
of the modules that have a non-empty graph `needs` list carry at least one
concept row whose name exactly matches a `needs` name, the join is declared
unsound and no split is reported.

## JOB 2 — is the judge biased by being the author?

Re-judge a sample of the **byte-identical stored seat prompts** with a
different model. Nothing is rebuilt; `out/raw/<clause>.<seat>.json:prompt` is
the user message and `seats.SYSTEM`/brief is the system message, read from the
same `seats.py` the baseline ran under.

### Sample, fixed before any call

> ⚠️ **AMENDMENT, written before the first paid call and before any new
> judgement existed.** The measured cost estimate for n = 24 (below) came to
> **$0.58 on `claude-sonnet-4-5`** — over the $0.25 cap. The sample is
> therefore cut to **n = 10 clauses** (est. $0.243, printed and gated by the
> runner), keeping Sonnet rather than dropping to Haiku. The reason for that
> choice and not the other: a cheaper judge would let the sample stay at 24,
> but a disagreement would then be unreadable — "the other model found fewer
> defects" and "the other model is out of its depth" are the two hypotheses
> this measurement exists to separate, and a weaker judge confounds them by
> construction. n is the cheaper thing to give up. 10 clauses × 2 seats is
> ≈ 160 item-level judgements, which is the unit κ is computed over, and it is
> the slice size `stage4_baseline/BASELINE.md` §6.4 itself proposed. Nothing
> else in this section is changed.

* Seats: **4b and 4c** only. 4a is advisory and 4d refused on 70% of clauses
  in this artifact, so its verdicts are format-selected and not a fair parity
  target.
* n = **24 clauses**, drawn by a fixed deterministic rule — sorted clause ids,
  every k-th so the sample spans the id space — not hand-picked. 24 clauses ×
  2 seats ≈ 190 item-level judgements, which is the unit κ is computed over;
  that is enough for a κ standard error near 0.07 and comfortably enough to
  separate κ ≈ 0.2 from κ ≈ 0.6, which is the decision this measurement has to
  make. Cost governs the ceiling, not power.

### Criteria, fixed before any new judgement is looked at

* **Agreement** = fraction of items where the two models return the same
  verdict from the seat's 3-way set (`licensed`/`unlicensed`/`unclear`, and
  `faithful`/`unfaithful`/`unclear`). Computed per seat.
* **κ** = Cohen's κ over the 3-way verdict, per seat and pooled.
* **Direction** = (defect verdicts by the new model) − (defect verdicts by
  DeepSeek) on the same items. Positive ⇒ DeepSeek was lenient on its own
  work. Negative ⇒ DeepSeek was over-strict or the new model is out of its
  depth.
* **Reading of κ, fixed now:** κ < 0.4 ⇒ the baseline's verdicts are a
  property of the judge and the 66/81 headline must not be quoted at all.
  0.4 ≤ κ < 0.6 ⇒ quotable only with the κ printed beside it. κ ≥ 0.6 ⇒ the
  same-model-as-author objection is not supported by this test.
* An item where either model refused / returned no verdict is dropped from κ
  and **counted and reported** as a drop, never imputed.

### Spend

Hard cap $0.25. A cost estimate is printed before the first call and the run
refuses over the cap. Model: `claude-sonnet-4-5` (faithfulness adjudication
against a source span is the harder end of the seat's work). If no Claude
credential exists, that is stated plainly and a *different Together* model is
used instead.
