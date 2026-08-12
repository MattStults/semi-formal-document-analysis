# Consolidated fix review — clean-context adversarial pass (2026-08-12)

Reviewer: clean-context agent, no design docs read, no prior verdicts consulted.
Scope: the UNREVIEWED fix set — the stage-4 wave (seats.py id-disclosure fix,
readback.clause_text/clause_texts, link_nodes merged_gloss/node_clause_texts/
provider_texts, readback_r3.hygienic_link_texts, test_stage4_node_plumbing.py),
the stage-2 inputs-gloss landing (schema.py requires+inputs loop, fixtures.py,
prompt/20_worked_example.md, test_link.py), and three small items
(recurse_driver.formatting_reason, Runner._health, classify_cap_overflow).
Method: every attack below was RUN, not argued — reproduction scripts against
the real modules, the live node corpus, the live graph, and the live merged
concept tables. No model call, no spend.

Suite status at review time: see §Suites at the bottom.

## VERDICT: NEGATIVE — two findings must be fixed before seats adjudicate real material (F0, F1).

---

## F0 — HIGH (gate integrity) — the fix set does not pass its own suite: 6 failures beyond the held one

The full phase_1 suite: **6 failed, 874 passed, 1 xfailed** (23:27) — all six
in the STAGED `resolve_runs/graph_v2/test_node_worked_example.py` (the
deliberately held test_link failure, F5, lives in `walkthrough/` and is
counted separately):

- `test_a_good_worked_example_passes_stage_2[l527_796_n012 / l3995_4164_n001 /
  l4251_4571_n029 / l1799_1974_n009]` — the worked example cites node ids that
  are **not in the checked-in node_corpus.json**;
- `test_translated_examples_render_to_loadable_asp` — KeyError on the same id;
- `test_full_corpus_mode_covers_every_node_and_sample_is_unchanged` — the
  default stratified sample no longer matches the checked-in corpus.

**Root cause (verified):** every cited id still exists in
`recurse/root/graph.json`, so this is not graph drift — `node_corpus.json` was
regenerated with explicit `--ids` (the 2026-08-12 translation-run sample:
`l426_610_n013, l1_170_n060, …`) while `node_corpus.py`'s default sample, the
node worked example, and the pin test still describe the earlier stratified 15.
The staged tree therefore ships a corpus its own gates reject.

**Live consequence.** Beyond the red suite: `link_nodes.node_clause_texts`
(the seats' clause-text source) is keyed off THIS corpus, and the worked
example the translator is shown cites nodes the corpus cannot ground — the
node-example gate (`the model told to imitate it would be imitating a
fiction`) is firing correctly.

**Minimal fix.** Decide which sample is canonical and make the three artifacts
agree: either regenerate `node_corpus.json` from the default sample (restores
byte-identical pin and the worked-example ids), or, if the run sample is now
canonical, regenerate as the UNION (`--ids` covering both sets) and re-pin.
Do not weaken the pin test — it just caught exactly what it exists to catch.

**Confidence:** high (reproduced, root cause verified). **Severity:** high as
a gate matter, mechanical to fix.

## F1 — HIGH — a 4d/4c seat reply naming an INDEX silently adjudicates against the wrong list

**Defect.** `seats._reply_item` accepts a bare digit for EVERY seat and maps it
positionally onto the denominator (`ids[int(s)]`). The back-compat rationale
("the pre-fix prompts taught `0.`, `1.`") is true only of 4a/4b, whose prompts
once numbered exactly the denominator entries. It was never true of 4c or 4d:

- **4d's prompt numbers a DIFFERENT list.** `build_4d_prompt` prints the claims
  unnumbered and the RENDERED SENTENCES as `0.`, `1.`, … A live seat that
  answers with those indices — the only numbers visible in its prompt — has its
  sentence verdicts silently re-attributed to claims, positionally. Reproduced:

  ```
  4d denominator: ('C1 political content ... is allowed', 'C2 exploitative material is excluded')
  reply [{"item":"0","verdict":"covered"},{"item":"1","verdict":"not-conveyed"}]
  -> VALIDATED: C1=covered, C2=not-conveyed        # the seat was talking about sentences
  ```

- **4c's prompt numbers nothing.** A digit reply there is the seat inventing an
  ordering; the positional map is a guess presented as adjudication. Also
  reproduced (digit replies validate against `('concepts[0]','concepts[1]','asserts[0]')`).

**Live consequence.** A confused live seat — the exact failure population the
READBACK_SMOKE fix exists for — produces a fully "adjudicated" 4d/4c record in
which verdict-to-item attribution is wrong. 4d's covered/not-conveyed drives
`route()` (re-translate / carry) and the stage-3 cross-check join; a
misattributed `not-conveyed` spends a stage-1 call on the wrong claim, and a
misattributed `covered` reads as coverage of a claim the seat never judged.
This is the silent direction — nothing refuses, nothing stamps.

**Minimal fix.** Restrict the 0-based-index fallback to the seats whose prompts
ever legitimately taught it: pass the seat into `_reply_item` (or a boolean
from `judge`) and take the `isdigit` branch only for `seat in ("4a", "4b")`.
For 4c/4d a digit falls through unchanged and `validate_judgements` refuses it
BY NAME, exactly as for any other unknown item — loud, per the module's own
discipline. `test_a_numeric_index_reply_maps_positionally_and_adjudicates`
pins 4b only, so it stays green; add the paired control (a digit reply on 4d
is NOT ADJUDICATED).

**Confidence:** high (mechanism reproduced end-to-end). **Severity:** high —
this is seat validity, the thing the wave exists to protect.

Non-finding, recorded so it is not re-attacked: the digit-vs-id collision
(`"1"` being both an index and a denominator id) is not live — 4a/4b ids are
`kind[i]` slots or `S<n>` situation ids, 4d ids are claim sentences; none is a
bare digit. Guarded by data, not by code; the F1 fix also closes it for 4c/4d.

## F2 — MEDIUM-HIGH (latent today, live in full-corpus mode) — `clause_text` drops un-narrowed spans of a partially-narrowed multi-span node

**Defect.** `readback.clause_text` prefers narrowed-span quotes GLOBALLY: if
ANY `[node narrows this span to: "…"]` bracket exists, it returns only the
narrow(s) and discards every other span's verbatim text. For a multi-span node
where only some spans carry a narrow, the seat's "clause" loses whole spans.
Reproduced synthetically (two spans, one narrowed → only `"narrow bit"`
returned), and the population is real: **the live graph has 18 multi-span
nodes, 5 of them with PARTIAL narrows** (`L1414-1610_n001/2/14, L1611-1798_n001,
L2821-3040_n003`). None is in the current 15-node sample, but
`node_corpus.py --all` (full-corpus mode, already built) emits them.

**Live consequence.** RB4 measures echo against a truncated clause; 4b/4d
judge sentences against a clause missing the text that licenses them — the
failure surfaces as unfair `unfaithful`/`not-conveyed` on a correct module, or
`unclear` inflation charged to the brief.

**Minimal fix.** Make the preference PER SPAN: split on the span heads first,
then for each span take its narrow if present else its stripped verbatim text,
and join. Add the mixed case to test_stage4_node_plumbing (the current tests
cover narrow-only and verbatim-only, never both).

**Confidence:** high. **Severity:** medium-high; upgrade to high before any
full-corpus seat run.

## F3 — MEDIUM — `merged_gloss` picks the alphabetically-first node's gloss, not the provider's, and its docstring claims otherwise

**Defect.** `link_nodes.merged_gloss` says the borrowed name gets "the
provider node's own gloss". The implementation is
`readback.gloss_from_rows(merged_concepts(selected))` — first-row-wins over
rows ordered by `sorted(selected.items())`, i.e. **alphabetical node id**,
which is not provider order and not even document order. Measured on the live
merged table: **10 names carry >1 distinct gloss**. For 8 of them no in-corpus
provider exists (first-wins is then as good as anything), but for
`stay_in_bounds_principles` the corpus HAS the provider (`l797_809_n001`) and
the winner is the borrower `l4572_4691_n011`'s assumption. (`higher_level_
instruction`'s winner is a provider only by alphabetical luck.)

**Live consequence.** A seat or R3 render defines a borrowed name by a
borrower's paraphrase instead of the defining node's meaning; whether the
right gloss wins depends on node-id sort order. Not silent at CORPUS scope —
`link.collect` records each collision as a `concept-multi-gloss` note in
link_nodes_report.json — but the render path never consults that note, and the
pick itself is unprincipled.

**Minimal fix.** In `merged_gloss`, order rows so that rows whose `clause_id`
provides the signature (from `link.defined_predicates`, as
`requires_resolution` already computes) come first; keep alphabetical order as
the tiebreak for provider-less names so the pick stays deterministic. One
sentence in the docstring either way: today it documents behaviour the code
does not have.

**Confidence:** high on facts (measured), medium on urgency — 9 of the current
10 collisions resolve identically or have no provider to prefer.

## F4 — LOW-MEDIUM — a claim with edge whitespace makes 4d permanently un-adjudicable live (fail-closed)

**Defect.** `schema` accepts claims with leading/trailing whitespace unchanged
(verified: `claims=['C1 x ', 'C1 x']` validates), 4d's ids ARE the claim
sentences, and `_reply_item` strips the reply. A claim with a trailing space is
displayed indistinguishably, the seat echoes the visible characters, the
stripped reply matches nothing, and the run is NOT ADJUDICATED — every time,
for every seat reply. Whitespace-twin claims likewise collapse to "judged
twice"/"missing". Reproduced.

**Live consequence.** Fail-closed, so no wrong verdict enters the record — but
a clause whose translator emitted one trailing space can never pass 4d, and the
refusal message ("no judgement for …") does not say why. Money spent on a
seat call whose adjudication was impossible before it was made.

**Minimal fix.** Normalise at the source of the id space: strip each `claims`
entry in `Module` validation (they are prose ids, `_check_text`-adjacent), and
have `denominator_4d` refuse whitespace-colliding claims the same way it
refuses a forbid_body name that matches nothing. No change to `_reply_item`.

**Confidence:** high (reproduced). **Severity:** low-medium (loud direction).

## F5 — the deliberately held test_link failure, characterised (NOT fixed, per instruction)

`test_d4b_no_table_and_no_concepts_declared_is_silent` fails because
`fixtures.m0255_module` now (correctly, under the inputs-gloss ruling) declares
concept rows for its borrows, so `render(tmp_path, "plain.lp")` no longer
builds the "declares no concepts at all" module the test needs — the stale
comment `# module_dict: concepts=[]` marks the drift. Two things worth saying
to whoever closes it: (1) the guard it held — `concept-table-absent` must stay
SILENT for a module declaring nothing — is currently unexercised, and it is the
guard that keeps that note from firing on every run; (2) the fixture shape
still exists: a defines-only module (`concepts=[], requires=[], inputs=[],
ontology=[]`, e.g. `definitional_module(concepts=[])`) is a translated module
with an empty concepts header. Rebuild the fixture; do not delete the test or
relax the note.

## F6 — LOW (latent) — `_NODE_SPAN_HEAD` assumes 4-digit line numbers

`readback._NODE_SPAN_HEAD` is `^L\d{4}-L\d{4}:\n`; `node_corpus.span_text`
emits `L{a:04d}` — at least four digits, MORE for a document over 9,999 lines.
On such a document the locator line survives into "clause text" for
un-narrowed node rows. The model spec is ~4,700 lines, so inert today.
Fix when touched: `\d{4,}`. Same file, same commit as F2 is the natural home.

## Small items — examined, no fix required

- **`recurse_driver.formatting_reason` attribute-tag regex**: cannot eat a
  content line. It is `fullmatch`, lowercase-tag-only, quoted-attribute-values
  only; ran the edge set — `<user> please help me`, `<a href=..>link</a>`,
  `<details open>` (valueless attribute), `<User>` all classify as CONTENT
  (None); only a bare structural tag matches. Failure direction is closed
  (unrecognised → content → must be covered or explained). Pre-existing and
  out of this fix set's scope but noted for completeness: `_FMT_BOLDLINE`
  fullmatch classifies an entirely-bold sentence (`**Never reveal secrets.**`)
  as `heading` — HEADINGISH semantics inherited from sweep_headings, pinned.
- **`Runner._health` unclaimed telemetry**: counting is sound (derived
  uncovered entries are dicts with a `reason` the `startswith` matches; unwind
  propagates children's uncovered). One aggregate caveat: because each unwind
  level re-emits its children's uncovered, a single unclaimed line appears in
  health.jsonl once per ancestor — a watcher summing the column overstates.
  Telemetry-only; note beside prerun review F3's "watch the aggregate".
- **`classify_cap_overflow` (D6 stage 1)**: inert (wired into nothing), pinned
  by test_recurse_driver. Its conservatism is by design; the only bias found is
  that `establishes` matching compares 80-char prefixes, so templated dense
  lists can misread as `malfunction` — the stated-safe direction.

## The rest of the attack surface — attacked and clean

- **`hygienic_link_texts`**: stripping stored `%!show_trace` cannot remove a
  trace the stage needs — `render_r3` appends its OWN directive per verdict
  atom under review, and the integration pin asserts exactly that one survives.
  Only the two exact `SHARED_PREAMBLE` lines are deduped; any other `#const`
  collision still errors (pinned both here and at link scope). `%!trace_rule`
  kept. A mid-line `%!show_trace` would survive the regex, but `render_lp`
  emits the directives on their own lines only.
- **`build_4c_prompt`** still has no rendering parameter; `_RENDERING_PATTERNS`
  and the world-item pass are intact; the ids= plumbing refuses a count
  mismatch (`_entry_lines`) rather than mispairing.
- **Packed-prompt leak through `clause_text`**: needs BOTH detection prongs to
  miss (`section_id != "graph_node"` AND a changed opening sentence);
  `node_corpus.row` always stamps both, and the live-artifact subset test pins
  the stored corpus. The narrow-bracket regex tolerates internal `"` (breaks
  only on a literal `"]` inside a narrow; 0 of 303 live span quotes contain
  one).
- **Stage-2 landing / the named suspect (`_supplement_borrow_glosses`)**: it
  does NOT weaken the missing-gloss tests. The two d4b partial-table tests were
  re-pointed the right way — the module under test is now `write_raw` (header
  declares both concepts, inputs carries one), and the TABLE-building module
  drops `broad_audience` from `inputs` entirely, so the omission the tests
  exist to catch is still real and still fires on exactly one signature.
  `test_d4_a_file_clingo_refuses_is_a_loud_failure`'s write_raw-style
  conversion preserves its point (schema now blocks the shape at creation, the
  link check still catches the hand-edited file) and guards its own fixture
  against render drift. The re-supplement stands aside whenever a test declares
  the name itself, so multi-gloss tests are unaffected; `broad_audience`'s
  gloss is byte-identical to `CONC_AUD` to avoid manufacturing
  `concept-multi-gloss` notes.
- **Worked-example addition**: gated three ways — every good module must pass
  stage 2 (`test_a_good_worked_example_passes_stage_2`, so the new concepts
  entries are schema-checked under the new borrow-gloss rule), both borrow
  fields must be DEMONSTRATED non-empty, and a document-side predicate in
  `inputs` fails by name. Style-consistent with the surrounding JSON blocks
  (JSON validity is separately gated).
- **`schema._coherent` collect-then-raise**: the dependent chain is handled
  (an acts failure suppresses the assert-declared and closure checks that read
  its output, with closure `governed` faked to the declared classes so no
  fabricated finding escapes); the borrow loop tolerates malformed
  `name/arity` entries without crashing; `MULTI_SEP` is consumed at both split
  sites; `mutate_schema.discover` now treats `errs.append(...)` as a guard so
  the collected form stays under mutation coverage.
- **`_reply_item` bracket path**: `[x]` stripping cannot mis-hit — no live id
  begins with `[`; a reply that strips to nothing known falls through to a
  named refusal.

## Suites

- `walkthrough/test_link.py`: **40 passed, 1 failed** — the failure is exactly
  the deliberately held `test_d4b_no_table_and_no_concepts_declared_is_silent`
  (F5). Left in place per instruction.
- `phase_1` full suite (recursively includes `resolve_runs/graph_v2`):
  **6 failed, 874 passed, 1 xfailed in 23:27** — the six F0 failures, nothing
  else. The stage-4 wave's own 23 pins (`test_stage4_node_plumbing.py`) all
  pass.
- A second run scoped to `resolve_runs/graph_v2/` alone: **6 failed, 114
  passed in 22:38** — all six in `test_node_worked_example.py` (the four
  worked-example ids, the loadable-ASP test, and the default-sample pin), i.e.
  exactly the F0 set; every other graph_v2 test passes. The failures were also
  reproduced directly against `test_node_worked_example.py` in this session.
