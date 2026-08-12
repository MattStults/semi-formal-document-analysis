# Pre-run adversarial review: ds4 fix chain vs the ds5 bet (2026-08-12)

Clean-context review of the shakeout fixes + the two post-divergence fixes, before the
uninterrupted ds5 build. Question reviewed: was each fix the RIGHT fix, and is its
verification sufficient to bet an unattended full build on? All probes deterministic
(`/tmp/roc_gate_probe.py` + inline replays), zero API spend. Both suites green under the
project venv: `test_recurse_driver.py` + `test_dispatch_core.py` = **89 passed**.

## VERDICT: **GO**, conditional on F1 (one-regex patch + pin) and the F2 expectation
being recorded before launch. Everything else is expectation management or post-ds5 work.

---

## F1 (HIGH, pre-run patch): the example-markup classifier is one attribute away from
## the exact ds4 failure class — and the instance is already in the document

`formatting_reason` (recurse_driver.py:353) recognizes only bare lowercase tags
(`</?[a-z_]+>`). Enumerating the actual document (`specs/openai-model-spec/model_spec.md`,
4692 lines) for structural lines still classified CONTENT:

| dialect | lines | classified | note |
|---|---|---|---|
| attribute-carrying tags (`<assistant recipient="python" end_turn="false">`) | **4** (L133, L728, L731, L3571) | CONTENT | same class as `<comparison>`, one variation away |
| tag + HTML comment (`<assistant> <!-- BAD -->`) | **396** | CONTENT | correct to keep as content: the GOOD/BAD judgment lives on this line; covered via the "extend the node's span over the example" instruction, which ds4 proved works (0 uncovered) |
| `~~~xml` language-tagged fences (183), indented fences, table rows, admonition bodies | — | covered / absent | no other dialect found |

The live risk: **L728 and L731 sit in one ds4 leaf ([699,795]) together with L736**
(`[... response text] [Read more](...)`, also structural-looking). If a ds5 leaf draw
leaves those 3 lines unclaimed, residue = 3 > the containment cap → hard failure → repair
rounds asking the model to cover markup — the exact 4-round non-convergence that cost
attempts in the shakeout. ds4 survived because the model covered them inside example
spans; that is a draw property, not a guarantee, and ds5's division may cut differently.

**Minimal fix** (one line + one pin, keeps `<tag> <!-- ... -->` as content):

```python
if re.fullmatch(r"</?[a-z_]+(\s[^<>!]*)?>", s):
    return "example-markup"
```
plus `assert R.formatting_reason('<assistant recipient="browser">') == "example-markup"`
in `test_admonition_marker_is_formatting`. Verified against the doc: this covers all 4
attr-tag lines and changes nothing else (free replay below stays 0-fail).

Assessment of the original fix: the admonition/example-markup additions were correct but
were **pattern-patches pinned on the observed instances**
(`test_admonition_marker_is_formatting` asserts the exact strings that failed live); the
class was never enumerated from the document until now. With F1 applied the enumeration
is closed: no further single-tag dialect exists in this document.

## F2 (HIGH, expectation — record before launch, no code): the 0.25 similarity gate
## effectively DISABLES the resolution pass; ds5 will finish with ~140 danglings, not ~5

Replayed the gate against the real ungated ds4 pass (150 renames recovered from
`runs/ds4/root_graph.pre_resolution.json` → `root_graph.json`; golden status via
`compare_vs_golden.json` unmatched_b; probe `/tmp/roc_gate_probe.py`):

- 150 renames → 150 new edges: 30 golden-matched ("good"), 120 unmatched ("bad").
- **At 0.25: 114/120 bad gated (95%) — but 28/30 good gated too (93%).** Kept: 8 renames
  (6 bad + 2 good).
- Threshold sweep (bad-gated / good-lost): 0.10 → 83/16, 0.15 → 104/21, 0.20 → 111/21,
  0.25 → 114/28, 0.30+ → plateau. **No threshold separates the classes** — the
  token-overlap feature is near-chance as a good/bad discriminator on this data.
- What 0.25 IS evidenced for: the motivating C3 class (`content_definition`, 38 edges)
  sits at sims 0.071–0.143, killed with ~2x margin. Any threshold in [0.15, 0.28] behaves
  identically on that class. So 0.25 is invented but not load-bearing.

Two mitigating facts, which is why this is GO-with-expectation rather than NO-GO:
(a) 27 of the 28 "good" renames lost are renames INTO `*_section_authority` coinages —
the exact names the extended convention bans, so in ds5 those providers should barely
exist and the loss class largely evaporates; (b) the ruling "absence > wrong" makes the
gated outcome the honest one. **But the ds4 headline "5 final danglings" cannot recur.**
Expected ds5: dangling count near the pre-pass level (~100–150). Whoever watches the run
must not treat that as a regression, and must not retune the gate mid-campaign.

The gate's pin (`test_resolution_pass_gates_dissimilar_renames`) tests only the gating
direction; `test_verified_fixes_are_integrated` (identical proses, sim 1.0) is the only
keep-direction pin. Adequate, but the keep side has never seen a realistic
partial-overlap case — post-ds5, sample the gated list for false gates.

## F3 (MEDIUM): the tiny-residue containment fires on ROUND 0, not "after repair
## non-convergence" — the artifact string is false and the pressure is gone

`validate_leaf` has no round awareness (no `repair_round` parameter; validator lambdas at
recurse_driver.py:1256 and the shared core path can't see it). The `<=2` containment
therefore triggers on the FIRST draw: a model that leaves 1–2 content lines unclaimed is
never asked to cover them, yet the recorded reason says "autofixed after repair
non-convergence". The pin (`test_tiny_unclaimed_residue_records_not_blocks`) tests the
mechanism as implemented — it never asserts a repair round happened first, so it pins the
overreach along with the fix.

**Abuse arithmetic**: cap is **per validate_leaf call = per leaf**, no global cap. ds4 had
33 leaves → systematic ceiling **66 silently unclaimed content lines** (~2.5% of content
lines) with zero warnings: `_health` warns only on zero-needs and density;
`graph_check.py` counts them as ordinary declared-uncovered; nothing aggregates. ds4
actual: 2 lines (L201, L203) — one leaf, benign. The recording IS visible in uncovered
reasons and health autofix rows, so "silent" means un-alarmed, not un-recorded.

**Minimal fixes** (either is enough for ds5; both are small):
1. Telemetry (2 lines, zero-risk): in `_health`, `if any("unclaimed" in a for a in
   row["autofixes"]): warns.append(...)`; optionally a post-build aggregate count over
   uncovered reasons in `post_build_checks`.
2. Correctness (defer if pressed): thread the round into the leaf validator (the state
   knows `repair_round`) and apply containment only at round >= 1, restoring one round of
   cover-or-explain pressure and making the artifact string true. Signature change
   touches both execution paths — do it with its own pin, not minutes before a launch.

## F4 (MEDIUM): the extended authority convention converts noise, it does not remove it —
## and the scoring collapse the divergence report called for was never implemented

`leaf_extra` now says "EVERY node's needs, not only headings". Grounds check: the 4/4
draw verification (2026-08-11) tested the HEADING wording on heading-dense spans; the
all-nodes extension has never been sampled live. What it will do, per the ds4 report's own
numbers: the 268-edge child-coinage class (C2) gets renamed to canonical names — but
golden's children carry needs=[], so those child→shared-definition edges remain unmatched
whatever they are called; and the heading class already MANUFACTURED 183 unmatched edges
under systematic instantiation. Expect ds5 needs/node ≥ ds4's 1.10 (golden 0.81) and
edges ≥ 970 (golden 512), with precision flat or down. Over-application wording risk is
real but bounded: "any node leaning on a section's authority level" invites every node in
a strongly-worded section to add the need — exactly the systematic-instantiation
mechanism the report documented.

The report's primary actionable — collapse/exclude the authority-plumbing equivalence
class in `graph_compare.py` (~59% of ds4-only divergence) — is **absent from the code**
(no collapse logic exists). Consequence for ds5: recall/precision will again be dominated
by a class already adjudicated as not-judgment-bearing. Not a build blocker (deterministic
re-scoring is free afterwards), but **do not read ds5's raw recall as the outcome
measure**; judge mechanical health + dangling honesty, and land the scoring collapse
before any accept/reject verdict on ds5. Implementing it before launch is fine too — it
is score-side only and cannot corrupt the build.

## F5 (LOW): the remaining shakeout fixes verify clean — mechanism-level notes

- **Null-finish_reason backstop** (dispatch_core.py:1046): pin constructs `_req_max`
  by hand, but the live wiring (set per custom_id at `_flush`:942, round-suffixed
  custom_ids so repair rounds can't cross-contaminate, `max_tokens` always present in the
  body) checks out by inspection AND ds4 itself ran batch mode end-to-end post-fix. A
  false-positive (provider counting quirk) costs a rerun, never corruption. Sound.
- **Lawful-field-omission** (`required` arrays in the grammars): pin asserts construction
  (`test_division_schema_requires_the_structural_fields`), which is the honest maximum —
  enforcement is provider-side, and `validate_division` still hard-fails a childless
  divide as defense in depth. Sound.
- **F17 carriage autofix**: pin exercises autofix→validate on the live shape; the fix is
  pure copy-through of a known entry (no judgment), shared by both execution paths. Sound.
- **Free regression replay run for this review**: all **33 ds4 leaf artifacts re-validated
  under current code (classifier + containment): 0 failures** — the fixes do not
  invalidate anything the live run accepted.

## F6 (LOW, hygiene): stale `runs/ds5/` from an interrupted start

`runs/ds5/` already holds c1/c2 partials, a `failed/` r1 artifact, and an **inflight
batch job manifest** (`inflight/job-1786551504137-1-3.*`), with an empty log. Launch ds5
into a fresh out dir (or clear this one first) so the manifest sweep / cache cannot mix a
dead job into the new run. Same model + brief_sha as ds4, so cache reuse is otherwise fine.

## What has never been tested end-to-end (Q5)

Never in one condition: **batch mode + enforced grammar + derived-uncovered + carriage
autofix + containment + all-nodes convention + gated resolution pass in one uninterrupted
run** — that is ds5 by definition. Everything testable for free first has now been done:
suites (89 green), ds4-leaf replay under current validators (33/33), and the gate replayed
against the real ds4 model reply (the ROC above — the gate's first contact with real
data). The one free test NOT possible: the all-nodes convention's effect on live draws
(prompt-side, needs spend). Residual accepted risk: F1's cluster if unpatched, and the
convention's edge inflation, both bounded and diagnosable from health.jsonl mid-run.

## GO / NO-GO

**GO** for the ds5 rerun, with: (1) F1 patch + pin landed first (one regex, suites
re-run); (2) F2 expectation recorded so a ~140-dangling finish is read correctly;
(3) fresh out dir (F6); (4) optionally F3's two-line telemetry warn. F3-correctness and
F4's scoring collapse are post-run work and must not be rushed in under launch pressure.
