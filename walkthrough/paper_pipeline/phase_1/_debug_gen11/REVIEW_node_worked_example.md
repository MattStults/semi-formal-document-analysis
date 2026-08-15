# Clean review — `resolve_runs/graph_v2/node_worked_example.md`

Reviewer: clean-context agent (Opus 5). Commissioned by the staleness guard, which reports this
file **NEVER REVIEWED** (added to `model/watch.json` in `39b464c`). Conducted under
`walkthrough/model/REVIEW_BRIEF.md`. Zero API spend; no file edited; `guard.py --accept` NOT run
(acceptance is a human act recorded with a name).

**Verdict: the file is STALE in five specified respects, listed most consequential first.**

Everything below is quoted from bytes on disk. Where I inferred rather than verified, I say so.

---

## Finding 1 — the file violates its own contract #2, in a demonstration, and nothing catches it

This is the most consequential finding and it was not in the suspicion I was asked to test.

The file states, at `node_worked_example.md:12-15`:

> 2. **Every `NEEDS` name goes in `requires`, spelled exactly as given** (you choose the
>    arity: `authority_levels_hierarchy` becomes `authority_levels_hierarchy/2`). Never
>    define a NEEDS name in your `ontology` — another node owns it. Give it a `concepts`
>    entry carrying the meaning the node text hands you.

The third good exemplar is node `l4251_4571_n029` (`node_worked_example.md:187-235`). Its module,
at `node_worked_example.md:231`, reads:

```json
  "requires": [],
```

But that node's actual contract, in `resolve_runs/graph_v2/node_corpus.json` (the corpus the test
validates against), is:

> NEEDS — these concepts are established by OTHER nodes of the graph, so every one of them belongs
> in this module's `requires`, spelled EXACTLY as given …
>   - voice_turn_taking_rule: voice responses must align with iterative, turn-taking conversation
>     structure and adapt to conversational shifts

**The demonstrated module drops a NEEDS name.** The prose that introduces the node
(`node_worked_example.md:189-190`) does not mention the NEEDS line at all, whereas the flagship's
introduction lists them verbatim (`node_worked_example.md:22-24`) — so a reader of the file alone
cannot see the violation. I found it only by reading the node record.

A demonstration is what the model imitates, and this one demonstrates the exact failure the file's
own contract #2 forbids and that `30_failure_modes.md:15` calls out as #2 *Missing cross-references*
(*"silent. A clause modifies rules defined in other clauses. Translating without reading them means
guessing their content. ⇒ `requires`."*).

**Nothing detects it.** Verified:
- `phase_1/checks.py` contains no reference to `NEEDS` or `PROVIDES` (`grep -n "NEEDS\|PROVIDES"`
  returns only prose in comments at lines 19 and 129). Stage 2 does not read the node contract.
- `test_node_worked_example.py:107-113` pins NEEDS→`requires` **for `l527_796_n012` only**:
  `flagship = next(m for m in _good_modules() if m["clause_id"] == "l527_796_n012")`. The other
  three modules are unchecked on this contract.

---

## Finding 2 — the abstain-vs-translate contradiction is REAL, but the file is the *less* stale side of it

I confirm the contradiction and I refine the account in two ways that change who should yield.

### 2a. The conflicting passages, quoted

`prompt/00_task.md:111-113`:

> If you cannot translate this clause faithfully — it is a section heading, it states a goal rather
> than a condition, it is an example, or its content is not expressible as rules — **abstain and give
> the reason**.

`node_worked_example.md:144-148`:

> ## A heading-authority node — small is correct
>
> Node `l3995_4164_n001` establishes only that the rules under a heading carry
> guideline authority. The module is tiny, and that is right — a node that establishes
> section metadata yields a classification, not obligations. Do not inflate it.

…followed by `"outcome": "translated"` at line 152.

`node_worked_example.md:187`:

> ## A worked-example node — translate the lesson, not the dialog

…followed by `"outcome": "translated"` at line 193, for a node the file itself describes at line 189
as *"a document example (a good/bad response pair)"*.

`node_worked_example.md:255-257`:

> Many graph nodes are commentary, headings, or document examples. A hollow-but-honest
> module (like the heading node above) or a clean abstention (like this one) are both
> better than an invented obligation.

The operative test the suspicion referred to is real, at `node_worked_example.md:299-300` (inside
bad example 4):

> Pick: if the node establishes an obligation, translate it; if it establishes none, abstain with
> every list empty.

**The conflict is airtight for the heading exemplar, and it is internal to the file under review.**
Line 148 says the heading node *"yields a classification, **not obligations**"*; line 300 says a node
that establishes no obligation should abstain; line 152 shows it translated. The file contradicts
itself, before 00_task.md is even brought into the room.

For the document-example node the conflict is with `00_task.md:112` (*"it is an example"* is named
grounds to abstain) against `node_worked_example.md:187` (*"translate the lesson, not the dialog"*).
That one is a cross-file conflict, and it is a genuine one, though a charitable reader can construe
00_task's list as illustrative of unfaithfulness rather than as sufficient triggers.

### 2b. ⭐ The four-trigger list is not licensed by the design — the file is closer to the design than 00_task.md is

Per REVIEW_BRIEF §1 I searched for the sentence that licenses each side.

`grep -n -i "section heading\|goal rather\|not expressible\|it is an example"` over
`resources/03_pipeline.md` returns **nothing**. The list at `00_task.md:111-112` appears in no other
file in the pipeline. What the design actually says, at `resources/03_pipeline.md:635-638`:

> #### Abstention is a real answer
>
> A model that cannot faithfully translate a clause should **say so**, with a reason, rather than
> produce something that passes the checks.

and at `resources/03_pipeline.md:417`:

> Q -->|no| AB[["ABSTAIN with a reason<br/>— a real answer, and the<br/>rate is a reliability signal"]]

The design's criterion is *faithfulness*, full stop. It never names a clause KIND as grounds to
abstain. **`00_task.md:111`'s four triggers are an unlicensed elaboration** — they convert a
capability test into a taxonomy test. `node_worked_example.md`'s position (a heading node yields a
classification, and a classification is translatable content) is the one the design licenses.

I report this and do not resolve it; the decision is the owner's. But the framing in `watch.json`
("`00_task.md:110` makes a section heading grounds to abstain; this file shows a heading node
translated") should not be read as establishing that this file is the erroneous side.

### 2c. The DeepSeek run evidence — substantially confirmed, with the causal claim withdrawn

Verified against `resolve_runs/graph_v2/translation_sample/runs/`. Nine runs produced a module for
this node:

| run | exemplar in system prompt | outcome |
|---|---|---|
| `20260810-203553` | **no** | translated |
| `20260810-205513` | **no** | translated |
| `20260810-212409` | yes | translated (`raw.txt`; no `.json` written) |
| `20260810-213043` | yes | translated |
| `20260810-214437` | yes | translated |
| `20260810-215527` | yes | translated |
| `20260810-225427` | yes | **abstained** |
| `20260810-234100` | yes | translated |
| `20260812-133317` | yes | translated |

So: **the model gave both answers, 7 exemplar-bearing runs split 6 translated / 1 abstained.** The
reported "six runs, 5 translated, 1 abstained" is close but not the number on disk.

The cleanest form of the instability: `20260810-225427/prompt_system.txt`,
`20260810-234100/prompt_system.txt` and `20260812-133317/prompt_system.txt` are **byte-identical**
(all md5 `9a74c4f4c4b3ca372cf0739a1c1613cbe70`, verified by `md5 -q`), same model
(`together-deepseek-v4-flash`), and 225427 abstained while the other two translated. The abstention
reason, from `20260810-225427/l3995_4164_n001.json`:

> The clause is a heading that assigns guideline authority to the rules beneath it. It does not
> itself impose an obligation, permission, or prohibition on any act, and it does not define a class
> of acts. Encoding it as an assertion would misrepresent its normative force.

That is `00_task.md:111` and `node_worked_example.md:300` being followed, verbatim in substance, on
the one node the same prompt shows translated.

**⚠️ Refutation of the causal half of the earlier analysis.** The two runs *without* the exemplar
(`203553`, `205513`) also translated, 2/2. The run set therefore does **not** show that the
translated exemplar drives translation — it shows the model mostly translates this node with or
without it, and flips once with it. I would not report "the exemplar overrides the prose" as an
established fact; what is established is that the assembled prompt leaves the answer underdetermined
and the model has taken both branches under identical bytes.

---

## Finding 3 — the heading exemplar's only rule can never fire, and it silently drops the node's PROVIDES obligation

Two verified facts the file does not carry.

**(a) The file states no rule about `PROVIDES` at all.** Line 4 names the field —
*"it arrives with `ESTABLISHES` … `PROVIDES` / `NEEDS` (assigned predicate names with their
meanings)"* — and the "Three contracts the node shape adds" list (lines 7-17) covers `cites`, `NEEDS`
and `inputs`. There is no contract for PROVIDES anywhere in the 308 lines.

That omission is exactly the missing half of the abstention argument. `l3995_4164_n001`'s contract
reads:

> PROVIDES (use EXACTLY these names as the predicates this module defines):
>   - guideline_authority: Guideline-level authority designation for the
>     #make_no_presumptions section (L3997+) regarding unprompted personal comments only

In the corpus the full run actually translates (`node_corpus_all.json`), **126 nodes NEED
`guideline_authority` and 13 provide it** (counted by exact-match on the `  - guideline_authority:`
line inside each node's NEEDS / PROVIDES block). Abstaining on a provider node strands its
dependents. That is the strongest available ground for translating a heading node, it is verifiable
from the node contract alone, and **the file demonstrates the right answer without stating the
reason** — which is precisely what lets a model take the other branch under pressure from
`00_task.md:111`.

**(b) The demonstrated module does not actually discharge the PROVIDES obligation.** The heading
module's sole ontology entry, `node_worked_example.md:172-177`:

```json
  "ontology": [
    { "atom": "guideline_authority(R)",
      "body": "rule_under_heading(R, unprompted_personal_comments_heading)", … } ],
  "requires": ["rule_under_heading/2"],
```

`rule_under_heading` is declared in `requires` — i.e. *another node must define it* — and **no node
does**: `grep` for `  - rule_under_heading:` across all 773 nodes of `node_corpus_all.json` returns
zero providers, and the node's own contract says `NEEDS: (none)`. So the head can never be derived,
and the 126 dependents get nothing even though the node was translated. That is
`30_failure_modes.md:16` #3 verbatim:

> **3** | **Rules that can never fire** | *loud but ignorable.* A rule guarding a condition nothing
> can produce looks like it enforces something and enforces nothing.

and #15 at `30_failure_modes.md:43` (*"it is waiting on a clause not yet linked in"*).

**On the ontology point I was asked not to foreclose:** a body-less ground atom is legal here and
nothing in the file forbids it. The file's warning at lines 102-106 (*"An atom with an unbound
variable and no body makes the solver refuse the whole file"*) and `10_output_format.md:53-55` are
about **unbound variables**, not about ground atoms — `10_output_format.md:33-34` explicitly allows
*"A ground atom, or one with a body that binds its variables."* So "which authority this heading
carries" is a structural fact that belongs in `ontology` as a fact, and the demonstrated
conditional-rule form is a different thing that happens not to work. I am not proposing an edit; I am
reporting that the exemplar as written does not deliver what the node's contract promises, and that
the file's only ontology guidance is a warning that a reader may over-generalize into "always write a
body".

---

## Finding 4 — all four exemplars cite node ids that do not exist in the corpus the run translates

`node_worked_example.md:5`:

> The examples below are real nodes of this corpus.

`config_corpus_all.json` sets `corpus.path = "node_corpus_all.json"` — 773 rows, and I traced it to
`resolve_runs/graph_v2/runs/ds7/graph.json` (773 nodes; the only graph on disk with that count).
**None of the four exemplar ids exist in it.** The same content is there under different ids, because
the segmentation moved:

| exemplar id in the file | live id in `node_corpus_all.json` |
|---|---|
| `l527_796_n012` | `l609_698_n008` |
| `l3995_4164_n001` | `l3954_4251_n009` |
| `l4251_4571_n029` | `l4252_4482_n025` |
| `l1799_1974_n009` | `l1707_1973_n022` |

(Matched on verbatim source text: the L0618 best-intentions sentence, the
`#do_not_make_unprompted_personal_comments authority=guideline` heading, the 30th-birthday
GOOD/BAD pair, and the customer-service-manual analogy.)

The four ids *do* exist in `recurse/root/graph.json` (593 nodes) and in the frozen 15-node
`node_corpus.json`, which is what `test_node_worked_example.py:49` loads — so the test passes and
cannot see this. That split is deliberate and documented in `config_corpus_all.json`'s
`_split_note` (*"a live artifact and a test fixture must not be the same file"*), and I am not
reporting the split as a defect; I am reporting that the consequence is an unfenced gap.

Severity: contract #1 (lines 9-11) tells the model to cite the id it was handed, so a well-behaved
model is unaffected. But line 5's claim is now false, and the ESTABLISHES/NEEDS text quoted in the
prose is a description of nodes the run will never see. Concretely, it compounds Finding 1: the live
birthday node `l4252_4482_n025` NEEDS `guideline_authority`, not `voice_turn_taking_rule` — so the
demonstrated `"requires": []` is wrong against both the old and the new corpus, for different names.

**This is the direction REVIEW_BRIEF calls "the direction that matters most": the design moved and
nobody edited the file.**

---

## Finding 5 — a design/file divergence I report but would not act on (REVIEW_BRIEF §4)

`resources/03_pipeline.md:403`, inside the stage-1 cached-block diagram:

> I2[worked examples: one good, five bad]

`node_worked_example.md:1`: *"# Worked examples — four good ones, then six bad"*, with
`## The six bad ones` at line 259. (The watched sibling `prompt/20_worked_example.md:1` says *"the
good ones, then five bad"* with `## The five bad ones` at line 282, so the design's label is stale
against both files, not just this one.)

A diagram label counting examples is not a rule, and the file growing an abstention exemplar and an
extra bad case is plainly an improvement over the count. Reported, not resolved.

---

## What `test_node_worked_example.py` pins, and what it does not

**Pins** (all 8 tests pass):
- the bad-examples heading still exists, shape-matched so the count may change (`:26`, `:57`);
- at least 4 good modules parse out of the good region (`:61`);
- every good module passes `checks.run_checks` with no errors, and stage 2 agrees with the declared
  `outcome` (`:67-78`) — this is the real workhorse;
- every translated good module validates through `schema.validate_all` and renders non-empty ASP
  (`:81-89`);
- at least 3 conditional ontology entries exist and at least one atom head repeats with different
  bodies (`:92-98`);
- some module carries both `requires` and `inputs`; some module abstains (`:101-104`);
- the flagship's `requires` names are exactly the node's two NEEDS names (`:107-113`);
- `node_corpus.py --all` emits one row per graph node and the default 15-sample is byte-stable
  (`:116-133`) — correctly written as a subset/identity pin, not a count pin.

**Does not pin, and plausibly should** (ordered by what it would have caught above):
1. **NEEDS→`requires` for any module but the flagship.** Would have caught Finding 1 outright. The
   generalization is one line: parse the NEEDS block from `corpus[cid]["quote"]` and assert
   containment for every good module.
2. **PROVIDES→actually-defined.** Nothing asserts that a module for a node with a PROVIDES name
   defines it derivably. Would have caught Finding 3(b).
3. **A reachability / dead-rule check.** Nothing asserts that a body predicate in `requires` has a
   provider anywhere. Failure mode #3 is on the failure-mode list the same prompt ships and is
   untested against the examples that teach it.
4. **That the exemplar `clause_id`s exist in the corpus `config_corpus_all.json` actually runs.**
   The test deliberately reads the frozen fixture; nothing reads the live one. Finding 4 is invisible
   to it by construction.
5. **Any cross-file consistency assertion at all.** No test anywhere assembles
   `00_task.md + 10_output_format.md + node_worked_example.md + 30_failure_modes.md` and checks that
   the demonstrations obey the prose. Finding 2 is a property of the assembled prompt and no artifact
   in the repo represents the assembled prompt except the run logs.

**Cosmetic:** the module docstring at `:6` says the split heading is `'## The five bad ones'`; the
file says six. The regex at `:26` is shape-matched (`The\s+\w+\s+bad\s+ones`) so it still passes.
Stale comment only.

---

## Checks I ran that came back CLEAN

Recorded so the owner knows what was covered and does not re-do it.

- **Internal consistency against `10_output_format.md`** — all four exemplars obey: one JSON object;
  status values in `forbid/permit/oblige/prefer`; every `requires` entry has a matching `concepts`
  entry with a non-restating gloss (`:66-82`); `requires` and `inputs` disjoint (`:92-94`); acts
  declared once then referred to (`:98-103`); `read_back`/`read_back_slots` counts match (`:123-141`,
  checked by hand on both asserts); a `closure` entry for every functor in `acts`, and none where
  `acts` is empty (`:143-152`, and the file says so explicitly at line 185); the abstention has
  every list empty (`:154-157`).
- **Rule 5b / `prefer` for comparatives** (`00_task.md:62-65`, `03_pipeline.md` relation section):
  the birthday exemplar correctly uses `prefer` and says why at line 190 (*"collapsing it into
  `forbid` would be a hollow stub"*), matching `10_output_format.md:22-24` and failure mode #5.
- **`provides` removal** (`03_pipeline.md`: *"⛔ `provides` was REMOVED"*): no exemplar module emits a
  `provides` field. The `PROVIDES` at line 4 is the node's *input* contract, a different thing, and
  is not a violation.
- **The ESTABLISHES text quoted in prose** at lines 21-26, 145-146, 189, 239-240 matches the node
  records for all four, and the L0618 SOURCE TEXT quoted at lines 24-26 is verbatim. The *content*
  transcription is faithful; the ids and the NEEDS lists are what moved.
- **The six bad examples** (lines 259-308) each correspond to a real rule stated elsewhere in the
  assembled prompt: #0 to the three-notations table and `00_task.md:91-96`; #1 to
  `10_output_format.md:53-55`; #2 to `10_output_format.md:50-51`; #3 to `10_output_format.md:99-103`;
  #4 to `10_output_format.md:154-157`; #5 to contract #1. None invents a rule.

---

## Run output (REVIEW_BRIEF §5)

```
$ python3 guard.py                      # from walkthrough/model
GUARD — 7 watched file(s), review points in model/reviewed.json
⛔ NEVER REVIEWED — 1 watched file(s) have no review point at all:
   paper_pipeline/phase_1/resolve_runs/graph_v2/node_worked_example.md   39f67e149cae8f46
EXIT=1
```

```
$ python3 guard.py --self-test
  [PASS] the guard watches something at all   (7 files)
  [PASS] an empty watch list is a loud ERROR, not a pass          exit 2
  [PASS] an unreadable watch list is a loud ERROR, not a pass     exit 2
  [PASS] a pattern matching no file is an error
  [PASS] staleness fires when a digest differs
  [PASS] staleness does NOT fire when digests match
  [PASS] every watched file states why it is watched
EXIT=0
```

```
$ .venv/bin/python -m pytest test_node_worked_example.py model/test_model.py -q
41 passed in 4.84s
```

The `guard.py` exit 1 is the commissioning condition, not a failure. Notably, no other watched file
is stale — `model/reviewed.json` carries review points for `03_pipeline.md`, all four `prompt/*.md`
and `schema.py`, dated 2026-08-12 (30_failure_modes.md: 2026-08-07), all matching current bytes.
**So the design document has not moved since 2026-08-12; the divergences in Findings 1, 3 and 4 are
against artifacts the guard does not watch** — `node_corpus.json`, `node_corpus_all.json`, and the
graph the corpus is generated from. The failures found here were out of reach of the watch list, in
the same structural way `watch.json`'s `_history` describes for 2026-08-07.

---

## Verdict

**The file is STALE**, in these respects, most consequential first:

1. **`node_worked_example.md:231`** — the `l4251_4571_n029` exemplar has `"requires": []` while the
   node's contract carries a NEEDS name, violating the file's own contract #2 at lines 12-15. A
   demonstration teaching the failure the prose forbids; undetected by stage 2 and by the test.
2. **Lines 148 / 152 / 299-300** — the file states an operative test ("no obligation ⇒ abstain"),
   says of the heading exemplar that it yields *"a classification, not obligations"*, and then shows
   it translated. Internally contradictory before `00_task.md:111` is considered. The model has taken
   both branches under byte-identical prompts (`20260810-225427` vs `20260810-234100`).
   ⚠️ On the cross-file half: `00_task.md:111`'s four-trigger list is licensed by **no sentence** in
   `resources/03_pipeline.md`; the design's criterion is faithfulness alone (`:635-638`). If a file
   yields here, the evidence points at `00_task.md`, not this one.
3. **Lines 4-17 and 172-181** — no PROVIDES contract is stated anywhere in the file, and the heading
   exemplar's sole rule is guarded by `rule_under_heading/2`, which zero nodes in the live corpus
   provide. The node is a provider of `guideline_authority` for 126 dependents and the demonstrated
   module derives nothing. Failure mode #3, demonstrated.
4. **Line 5** — *"real nodes of this corpus"* is false for the corpus `config_corpus_all.json` runs;
   all four ids were re-segmented away, and the test cannot see it because it reads the frozen
   fixture.
5. **`03_pipeline.md:403`** — the design's *"one good, five bad"* label no longer describes this file
   (four/six) or `20_worked_example.md` (good ones/five). Reported, not resolved; low consequence.

I could review this confidently. Nothing in the design was unclear enough to block me; the one place
I stopped short of a judgment — whether the four-trigger abstention list should govern — I stopped
because the decision is the owner's, not because the writing defeated me. I have proposed no edits.
