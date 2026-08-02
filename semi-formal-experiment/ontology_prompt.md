# `ontology.py` — the relation-annotation prompt

The prompt that would build the relation layer over the atom vocabulary, plus
the record of why it **has not been run** and what it would have to beat to be
worth running.

Rendered by `ontology.render_prompt`; print the real thing with

```
.venv/bin/python ontology.py --print-prompt
```

---

## ⚠️ READ THIS BEFORE SPENDING ANYTHING

**This pass is specified, tested, costed — and NOT recommended.** It exists so
that the option is buildable and the decision is reversible, not because the
evidence supports it.

The relation layer was going to be the fix for a sparse ontology. It was
measured first. A one-hop relation layer makes the typed query **worse on every
behaviour**:

| behaviour | precision, no relations | precision, 1 hop |
|---|---|---|
| helpfulness | 0.348 | 0.309 |
| harm-avoidance-to-third-parties | 0.850 | 0.631 |
| avoiding-over-and-under-caution | 0.433 | 0.367 |

Passage-level MCC over the same clauses: **+0.123 → +0.088**.

The mechanism is not subtle. Relation expansion pulls in *siblings that share a
parent but not a subject*. `refuse_answer` and `engaging_answer` sit under the
same genus and are about opposite things. Every edge you add is a new way for a
clause to be dragged in by association, which is precisely the failure mode a
typed ontology was supposed to avoid.

So `structural.CONSTANTS["max_hops"]` is **0**, and this pass is parked.

**The gate is SUSPENDED.** SUSPENDED — the gate was defending a null that does not exist. It was quoted as +0.340, which is DRAW0, the MAXIMUM of a 5-draw spread whose mean is +0.310 ± 0.021. Do not run a relation layer against it until the typing verdict is re-derived per behaviour with a correctly-scaled noise floor (draw-level SE is 0.0041, not the 0.06 that was used).

For reference only, the shipped operator scored **+0.340 on draw0**. A relation
layer earns its place only by beating that, measured the same way, on the
589-passage universe. Anyone running this pass should state that number first
and hold themselves to it.

---

## What the pass does

Input is the **vocabulary only**: 361 atom names with their kind and gloss, from
`annotations_b8.json`. Not the corpus. Not any behaviour. Not the panel.

That is what keeps contract §5 invariants 8 and 9 *structural* rather than
promised — a prompt that never sees a label cannot be fitted to one, and a pass
that never sees a behaviour cannot be re-run per query.

Output is typed relation triples over pairs **both already in the vocabulary**.
This is the same anti-fabrication device `annotate.py` uses for span ids: the
model *selects*, it does not *coin*. A triple naming anything outside the list
is rejected and counted (`unknown_atom`), so fabrication shows up as a number
rather than as a plausible-looking edge.

### Why four calls, and why they split the RELATIONS rather than the vocabulary

Each call sees the **whole** 361-atom list and is asked for **one** relation
type.

Batching the vocabulary instead would be the obvious economy and it destroys
the pass: the pairs worth having are exactly the ones that straddle a split.
`harm_prevention` and `third_party_harm` are two hundred names apart
alphabetically, and no vocabulary-batched call can ever see both. Splitting the
relation space also gives each call the full output budget for one relation
instead of rationing one budget across four.

| pass | asks for |
|---|---|
| `situation_subsumption` | `subsumes` where both concepts are `situation` |
| `act_subsumption` | `subsumes` where both concepts are `act` |
| `act_situation_correspondence` | `entails` from an act to the situation it brings about, or the value it serves — the only cross-kind relation |
| `contrariety` | `contrary` pairs (same kind), plus `same_as` for genuine synonyms |

### The relation set

| relation | direction | kinds | role in the query |
|---|---|---|---|
| `same_as` | symmetric | same | synonyms the vocabulary failed to merge |
| `subsumes` | directed, acyclic | **same only** | broader → narrower |
| `entails` | directed, acyclic | **may cross** | the only bridge between act and situation |
| `contrary` | symmetric | same | **defeater** — blocks a match |

`subsumes` is same-kind-only on purpose: a taxonomy is a partition per kind, and
a situation that "subsumes" an act is a type error that would let a circumstance
be counted as conduct. `entails` carries the cross-kind traffic, explicitly and
auditably.

A fifth relation (`related_to`, "co-occurs", "both about safety") was
deliberately **not** included. An untyped association edge is a similarity score
in an ontology's clothing, and re-introducing it is how this project drifted the
first time.

---

## Guardrails — all counted, never silent

Applied by `ontology.validate` to *both* derivation paths, identically:

| rejection | meaning |
|---|---|
| `unknown_atom` | an endpoint outside the vocabulary — nothing invented |
| `self_loop` | `a == b` |
| `cross_kind_subsumes` / `_same_as` / `_contrary` | type error |
| `cycle` | the edge would close a subsumption or entailment cycle |
| `contradictory_pair` | a pair asserted both contrary and connected — **contrary wins**, because a false contrary costs only recall while a false subsumption manufactures matches |
| `duplicate` | same triple twice |
| `bad_relation` | a relation name outside the four |
| `unparseable` / `malformed` | the reply was not usable JSON |

Every surviving relation carries `via` (which rule or which pass) and
`evidence` (the material it fired on), so `structural.explain()` can print a
path a reader checks by hand rather than a number they must trust.

---

## The mechanical baseline — a null result, kept

`ontology.derive_mechanical` derives the same relations with **no model at
all**, from names, glosses and kinds. On this spec it is nearly empty:

| rule | edges |
|---|---|
| `contrary_negation` (X vs `avoid_X`) | **0** |
| `entails_nominalisation` (act ↔ situation) | **0** |
| `same_as_key` | **0** |
| `contrary_antonym` | 1 |
| `subsumes_name_tokens` | 14 |
| `subsumes_gloss_names` | 5 |
| **total** | **20 edges over 361 atoms — 7.2% of the vocabulary touched** |

Two of the three headline rules fire **zero** times, and not by accident:

- 22 atoms carry an `avoid_` prefix and **not one** has its un-negated partner
  in the vocabulary, so there is no polarity pair to find.
- All 361 names have **exactly one kind**, so there is no act/situation pair to
  bridge.

The vocabulary is flat and morphologically *parallel* — the annotator produced
siblings (`refuse_answer`, `good_answer`, `engaging_answer`) rather than nested
concepts — so containment morphology has nothing to bite on.

Pinned by `test_ontology.py::test_mechanical_path_is_a_measured_null_result`
against the real artifact, so the null result is asserted rather than described.

**The one relation this data has in bulk is shared name tokens** (1,625 pairs,
317/361 atoms). That is lexical overlap relabelled as structure, and using it
would rebuild the bag-of-atoms scorer this work replaces. It is deliberately not
a rule.

---

## Cost, and the exact command

Four calls, whole vocabulary each (~6k input tokens), 8k output cap.
At luna's $0.20 / $1.20 per Mtok:

```
input   ~41,000 tok  x $0.20/Mtok  =  $0.008
output  ~32,000 tok  x $1.20/Mtok  =  $0.038
                                      -------
                                      ~$0.047   (worst case: assumes every
                                                 call fills its 8k output cap)
```

Dry run first — this writes the four prompts to `prompt_log/` and calls nothing:

```
.venv/bin/python ontology.py --annotations annotations_b8.json
```

**GATE SUSPENDED: +0.340 is DRAW0, the MAXIMUM of a 5-draw spread (mean +0.310 +/- 0.021), and it was defending a typing null that has since been RETRACTED. Re-derive per behaviour with the correct noise floor (draw-level SE 0.0041) before gating anything on it.**

The live pass, **which is not recommended and was formerly gated at +0.340 to be worth
keeping**:

```
.venv/bin/python ontology.py --live --provider luna \
    --annotations annotations_b8.json --out ontology.json
```

`--live` is the only thing that opens a socket. Without it the whole path —
prompt rendering, parsing, validation, agreement reporting — still executes
against a null response, so a dry run exercises more than argparse.

Then re-measure before believing anything:

```
.venv/bin/python test_structural.py          # the full ladder report
```

`structural.py` picks up `ontology.json` automatically but still traverses
**0 hops** by default. Turning expansion on is a deliberate act:

```
.venv/bin/python structural.py helpfulness --hops 1
```

and it prints a warning when you do, because the last time it was measured it
made things worse everywhere.
