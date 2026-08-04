# VOCAB_GAPS_DESIGN — closing the `fn_family_absent_from_vocabulary` class (design, 2026-08-04, for review)

## 0. What this fixes, and the disclosure that comes first

The census over `audit_dossiers/ext_v1_merged__audit_v1/` (verdicts_merged.json)
assigns **26 FN dossiers** the cause `fn_family_absent_from_vocabulary`: the
clause is panel-relevant to the behaviour, the atom channel is zero, there is
no exact-name intersection and no stem-family adjacency — the concept that
makes the clause relevant **was never atomized on either side**. These 26
dossiers name **26 distinct clauses** (m0015, m0030, m0096, m0151, m0170,
m0198, m0202, m0203, m0205, m0207, m0215, m0236, m0238, m0241, m0242, m0244,
m0245, m0246, m0253, m0255, m0270, m0273, m0303, m0322, m0444, m0528).

**Label-hygiene disclosure (ITERATION_LOOP.md policy §1, recorded plainly):**
this worklist was DISCOVERED by a census over panel-labelled FN dossiers.
Labels directed attention here. Labels play NO role in what follows: every
atom added under this design must be licensed by the clause's own text (a
verbatim quote requirement, mechanically checked), its keep/revert decision
cites document-side evidence only, and no panel number appears in any
worksheet, verdict, or decision file. The provenance block of every artifact
this design produces repeats this paragraph.

## 1. The missing families, read from the dossiers

Grounded in the 26 dossiers (clause text + current atoms + the behaviour's
query atoms), the absent concepts cluster into nine families. Per family: the
clauses, and what the clause text licenses.

1. **Hateful content / protected groups** — m0242, m0244, m0245, m0246 (and
   m0528's refusal-style example). m0242 says "must not generate hateful
   content targeting protected groups… slurs, insults… demeans or
   dehumanizes"; its ONLY atom today is the generic
   `mustnot_generate_disallowed_content`. Nothing in either vocabulary names
   `hateful_content` or `protected_group`.
2. **Extremist content** — m0236, m0238, m0241. m0236 ("must not create
   content that praises, endorses, or aids extremist agendas that promote
   violence") carries only generic disallowed-content atoms; clause-side
   `user_requests_extremist_propaganda` exists on m0241 but no
   `extremist_content` situation/entity exists anywhere.
3. **Prohibited/disallowed content as a query-meetable concept** — m0198,
   m0202, m0203, m0253, m0255. The clause side has the family
   (`prohibited_content`, `restricted_content`, `disguised_disallowed_content`,
   `shouldnot_generate_disallowed_content`) but the harm behaviour's query
   atoms contain NO member and no licensable relative (all the polarity-
   prefixed members are containment-ineligible by design).
4. **Transformation exception** — m0253, m0255 (also class 3):
   `mustnot_transform_prohibited_content`, `mustnot_infer_missing_content`
   have no situation-kind counterpart (`user_provided_content`,
   `content_transformation_request`) the query side could meet.
5. **CSAM** — m0205, m0207. `sexual_content_involving_minors` exists
   clause-side on m0205 only; m0207 (the direct-request example) carries only
   generic refusal atoms.
6. **Reversibility / minimal disruption** — m0151: `irreversible_actions`,
   `should_prefer_reversible_actions` clause-side; the harm query's
   `minimize_unintended_consequences` shares no head with either.
7. **Instruction-conflict / chain of command as harm-relevant** — m0096,
   m0030, m0303: `instruction_priority_conflict`, `must_follow_chain_of_command`,
   `goals_conflict` exist clause-side but the harm and helpfulness queries
   carry no member of the conflict family.
8. **Human control / disempowerment** — m0015: `human_control_of_ai`,
   `mustnot_facilitate_human_disempowerment` — a two-atom island no query
   atom can reach.
9. **Non-judgment / overstepping / steering** — m0170, m0444, m0322, m0528:
   `positive_user_intent`, `shouldnot_overstep_or_prescribe`,
   `conceal_relevant_facts`, `steer_user`, `judgmental_refusal`,
   `neutral_refusal` — present clause-side in fragments; the relevant
   behaviours' query vocabularies have no meetable member.

Two distinct failure shapes fall out, and they take different fixes:

* **Shape A — the concept is atomized NOWHERE** (families 1, 2, 4, 6 in part,
  9 in part): the clause text licenses an atom nobody coined. Fix = add
  clause-side atoms.
* **Shape B — the concept exists clause-side but the query cannot meet it**
  (families 3, 5, 7, 8): the fix is NOT annotation — it is query-side
  selection (the select_audit sweep judges every vocabulary atom against the
  definition; a sweep that rates `prohibited_content` or
  `sexual_content_involving_minors` score-3 for harm-avoidance repairs these
  with zero annotation edits) and/or containment (see
  CONTAINMENT_WIDENING_DESIGN.md). This design MUST NOT add duplicate atoms
  for Shape-B concepts; the worksheet validator enforces reuse-first (§3.3).

## 2. Fix options considered

**(a) Targeted re-annotation** of the 26 clauses through `annotate.py` with a
vocabulary-gap-aware prompt. Rejected as the primary instrument, for three
contract reasons: (i) `annotate_prompt.md` is behaviour-agnostic by test — a
prompt that hints "attend to hate/extremism/privacy categories" imports the
census's direction of attention into annotation CONTENT, which is exactly the
leak the policy forbids; a prompt that doesn't hint reproduces the same gaps
(these atoms were missed under the current prompt once already). (ii)
Re-annotation REDRAWS the whole atom set per clause: the diff is
adds+drops+renames across 26 clauses, an unbounded flip surface that
ITERATION_LOOP.md §4 says is too coarse to adjudicate. (iii) The merged
artifact's migration-log lineage (`vocabulary_migrations.json` replay
contract) has no way to express "this clause's atoms were wholesale replaced"
— re-annotation forks the artifact version rather than extending the log.

**(b) Worksheet + seat pass (chain-audit pattern), additions only.**
RECOMMENDED. Mirror `chain_audit_worksheet.py`: a deterministic builder emits
one worksheet row per affected clause (clause text, existing atoms with
glosses, the CURRENT full vocabulary index for reuse); a blinded seat
proposes zero or more ADDITIONAL atoms per clause; a mechanical validator
accepts or rejects the verdict file whole. Additions are surgical: existing
atoms are untouched, the artifact diff is pure insertion, and the flip set is
exactly the clauses whose channels change — small enough to adjudicate
exhaustively.

Fallback trigger, falsifiable: if the seat pass finds ≥3 clauses whose
EXISTING atoms it flags as wrong (not merely incomplete), those clauses
escalate to option (a) re-annotation as a separate, named cycle. Additions
never silently repair a wrong atom.

## 3. The worksheet + seat pass, as a contract

### 3.1 Worksheet (deterministic, label-free)

`vocab_gap_worksheet.py` (new; chain_audit_worksheet.py is the template)
builds `vocab_gap/worksheet.json`: one row per clause in a FROZEN clause list
(§0's 26 clauses, recorded with the census provenance paragraph), carrying
`clause_id`, full clause text, existing atoms (name/kind/gloss/quote), and
nothing else. The worksheet MUST NOT carry: behaviour names, panel scores,
dossier fields, or the census cause strings. The seat sees a clause and a
vocabulary; it never sees why the clause was selected.

### 3.2 Seat brief

`briefs/vocab_gap_seat.md` (new): "List every concept this clause's text
asserts that has no covering atom, under the four-kind taxonomy of
annotate.py. For each, REUSE an existing vocabulary atom if one covers it;
otherwise coin a name under grammar.py notation. Every proposal cites a
verbatim quote from the clause text." Run blind, one clause per item, small
model (Haiku-operability contract: worksheet in → verdicts out, no repo
exploration).

### 3.3 Validator (closed schema, mechanical)

A verdict file is accepted only if ALL hold, else rejected whole:
* coverage — every worksheet clause appears exactly once (additions may be
  the empty list; "no gap" is a recordable answer);
* every proposed atom has `{name, kind, gloss, quote, reuse: bool}`;
* `quote` is a verbatim substring of the clause text (the span license — this
  is the "content licensed by clause text only" guarantee, enforced, not
  promised);
* `name` round-trips clean through `grammar.parse_name` (polarity, principal
  chain, stem all legal); `kind` is one of the four;
* reuse-first — if `stem_of(name)` equals an existing vocabulary stem, the
  proposal MUST set `reuse: true` and use the existing name exactly (the
  kind-scoped alias guard annotate.py already enforces at draw time applies
  here too); a coined near-duplicate is a validation failure;
* per-clause addition cap of 4 — a seat proposing more is miscalibrated;
  refuse the file, re-run the seat (select_audit.py's over-budget rule, not
  truncation).

### 3.4 Gloss review before apply

Every COINED atom (not reuses) gets a blinded gloss review under the
`briefs/golden_review.md` pattern: is the gloss a faithful reading of the
quoted span, and is the name a licensed rendering of the gloss? Document-side
question only. A rejected atom is dropped from the batch; the drop is
recorded.

## 4. Artifact mechanics — name the extension

`atom_refactor.py` ops are `rename | merge | rechain | split`. **There is no
`add` op**, and this design needs one, because additions must ride the same
replay contract (an old artifact migrated forward by applying the log in
order) that makes every other vocabulary change refactor-safe.

**Extension: op `add`** in `vocabulary_migrations.json`, one entry per
applied batch:

```
{"op": "add", "atoms": [{"clause_id", "name", "kind", "gloss", "quote",
  "role"}...], "date", "reason", "worksheet_sha", "verdicts_sha",
  "artifacts": {<path>: {sha_before, sha_after, n_added}}}
```

Replay semantics, falsifiable: applying an `add` entry to an artifact inserts
exactly the listed atom records into artifacts that contain the target
clause, is idempotent-checked (an atom already present under the same
(clause_id, name, kind) is a replay error, not a silent skip), and leaves
every other record byte-identical. `atom_refactor.replay_artifact` learns the
op; `usages` already finds the new names once present. If extending the op
vocabulary is judged too invasive for Unit 3, the DECIDED alternative is
option (a) re-annotation with a version fork — but then §2(a)'s costs are
accepted by name, not by drift.

Golden interaction: `golden_translations.json` is a frozen STANDARD for the
extractor and is not edited by annotation additions. Two affected clauses ARE
golden entries — m0242 (split: dev) and **m0236 (split: held_out)**. The seat
pass shows only clause TEXT, which is public; nobody consults m0236's golden
reference atoms, and no golden re-freeze occurs. If any future step would
touch a golden entry, it follows Unit 3's re-freeze-with-history discipline
explicitly.

## 5. Validation and evaluation

1. **Mechanical**: validator clean (§3.3); migration entry replays clean;
   `test_containment.py`-style vocabulary pins re-verified.
2. **Golden span/deco on affected clauses**: for the two golden-covered
   clauses, score the POST-ADD atom sets against golden at `span` and
   `span_deco` — dev clause m0242 now; m0236 only at a final evaluation with
   `final_evaluation=True` (the flag exists to make that decision visible).
   Added atoms carry quotes, so span scoring applies to them directly.
   Prediction, falsifiable: additions can only raise span recall on m0242;
   any span-level regression on an existing atom means the batch edited what
   it must not, and reverts.
3. **Sweeps as label-free uptake check**: rebuild rosters
   (`select_audit.py rosters` — rosters carry the FULL vocabulary, so new
   atoms appear automatically), re-run the sweep seats blind, mechanical
   re-selection. Prediction, falsifiable: for harm-avoidance, at least the
   Shape-A families (hateful content, extremist content) yield score-3
   verdicts and enter the query; if a family's new atoms sweep at ≤2
   everywhere, the family did not close its gap and says so at the checkpoint.
4. **Snapshot → diff → dossier → adjudicate** the complete flip set against
   the document (both directions; >30 flips ⇒ split the batch by family).
   Keep/revert cites document-side reasons only.
5. **Outcome measurement at checkpoints only**: whether the 26 census FNs
   actually flip is a LABELLED question — it is read once, at the next
   declared census checkpoint on DEV cells, never steered on per-batch.
   Success criterion, pre-stated: ≥ the Shape-A subset (≈14 dossiers)
   resolved at checkpoint, with the fp_promiscuous_atom class NOT grown by
   more than the new atoms' own fair share (new generic atoms that fire
   everywhere are the known failure mode of gap-filling; the sweep strata and
   the FP census measure it).

## 6. Order of operations

1. Freeze the clause list + provenance paragraph. 2. Build worksheet. 3. Seat
pass. 4. Validate; gloss-review coined atoms. 5. Extend atom_refactor with
`add` (TDD, verify-RED). 6. Apply as one migration entry per family batch.
7. Golden span check (dev only). 8. Sweeps + re-selection. 9. Snapshot, diff,
dossier, adjudicate, decide. 10. Census checkpoint reads the FN class once.

$0 until step 3; steps 3+8 are small-model seat runs; nothing touches the
panel at any step.
