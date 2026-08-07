# The Relational Turn — findings, decisions, rejected alternatives (2026-08-06)

Session record for a design conversation that changed the direction of the project. Written per
the standing rule that rulings go in the repo with their grounds, and tempting alternatives are
rejected **by name**. Nothing here is a cycle; no measurement was frozen; two things were spent
(one DeepSeek call, $0.00097; several web searches). No code changed.

---

## 1. VERIFIED THIS SESSION (evidence, not argument)

**V1 — DeepSeek-V4-Flash is real, cheap, and roughly Opus-equivalent on judge verdicts.**
`deepseek-ai/DeepSeek-V4-Flash-0731` on together.ai, **$0.14 / $0.28 per Mtok** (cheaper than the
`deepseek` entry in `providers.json`, which points at V3.2 on deepinfra). Ran the five-item judge
prompt: 1,398 in / 2,775 out = **$0.00097**, vs ~$0.0295 for the same task on Opus 5 API pricing
(**≈30×**). Verdicts matched Opus 4/5; both strong panel signals (H005 6/6, H006 5/6) correct.
Its single divergence (H002) sided with the **tool** against panel and all other judges, taking
the permissive OR reading. Artifacts in the session scratchpad.

**V2 — Judge errors are correlated across tiers.** Haiku/Sonnet/Opus matched the human 4/4 on
determinate verdicts; V4-Flash matched Opus 4/5 and its one miss reproduced the tool's own error
direction. Four tiers spanning ~30× price are not independent estimators.

**V3 — The atom vocabulary is a versioned artifact but a non-reproducible measurement.**
`behavior_atoms.json`: 65 atoms, **all** `source: "definition"` (none derived from passages).
13/50 distinct names appear in >1 behaviour; pairwise Jaccard 0.05–0.25. Across independent draws
**57% (v1, 4 draws) / 63% (v2, 5 draws)** of atoms appear in *every* draw; ~16 singletons
regardless of vocabulary size. Stable as an artifact (`vocabulary_migrations.json`,
`atom_refactor.py`); ~40% draw-dependent as a measurement.

**V4 — The representation is relational for norms and propositional for situations.**
`rules.lp` (212 lines): `active(NormID, Modality, Act, Tier)` and `conflict(N1,N2,A,T1,T2)` are
relational. But the scenario space is `{ ctx(deception_real_harm) }` etc. — **`ctx/1` over bare
constants** — and `emit_asp.py` only ever emits `"ctx(%s)" % name`. Acts are constants too
(`comply_restrict` does not say to whom, about what). No party argument exists anywhere in
`rules.lp`.

**V5 — The party argument is smuggled into the atom NAME.** `patient.py`: principal chains are
agent-first name decorations (`..__model_user`), and the join is **decoration-blind — every
principal chain is stripped from the match**. An entire module plus `grammar.PRINCIPALS` and
`_license_edge` exists to parse and police a field that is encoded as a string suffix.

**V6 — The S3B review churn is dominated by that exact gap.** At least 8 adversarial rounds
(`S3B_ADVERSARIAL_REVIEW{,_R3,_R4,_R6,_R8}.md`, ~150KB, over a ~90KB design). Two findings recur
verbatim across rounds:
- M-1 → E-3: *"the `harm_bearers` value space and the text→principal mapping are **STILL**
  unpinned, and two mechanical checks now depend on them"*
- M-2 → E-2: *"attribution keying granularity is **STILL** unspecified"*; R1 names the cause —
  *"**atom-name keying** would corrupt a §7.2 control"*
- R4-E2: *"never re-specifies the **subsumption composition** … inherits from `patient.py`"*

Cost of this churn, per Matt: **$60–100 of frontier review**. "Has an implied impact on an unnamed
party" is `harm_bearers` + `text→principal mapping`; four rounds were spent trying to pin a party
argument in prose.

**V7 — Monotonicity already holds; the +0.0003 is a reachability failure.**
`cycles/CYCLE_LOG.jsonl`: six cycles, **five `keep`, one `revert`** (patient-pricing, a deliberate
adjudication catch). No cycle silently regressed a prior fix. All six closed **on the same day**.
So the cycle ceremony is cheap and monotone; the expense is upstream, in prose design review.

**V8 — Churn decomposition — ⚠️ SUPERSEDED, see `S3B_FINDING_RECLASSIFICATION.md`.**
V8 classified findings by *subject matter*; the correct test is *whether the fix was stateable at
the time*. Re-run on finding bodies (34 occurrences): `INEXPR` **~6%**, `EXPR-UNVER` ~32%,
`PROCESS` ~42%, `DOC` ~20%. Both `INEXPR` findings are the same defect — an **implied bearer that
a verbatim-quote license regime cannot express** — fixed by a **license taxonomy for facts**, not
by relational arguments. **Relational encoding's exclusive churn attribution ≈ 0%.** The
capability arguments (multi-hop subsumption for H006; cheap hypothesis expression) are untouched;
the *churn* argument is not supported. Original (wrong) table retained below for the record:
| cause | share | fixed by |
|---|---|---|
| representation / semantics underspecification | ~45% | relational encoding |
| process / falsifiability / pre-registration | ~40% | typed hypothesis record + mechanical gates |
| document self-consistency | ~15% | normalized design object (single source of truth) |

---

## 2. DECIDED

**D1 — The frame is oracle-driven convergence (CEGIS / CEGAR / exact learning), not aggregation.**
Grounds: V2. We are not building truth from agreeing judges; we are building a verifiable artifact
refined against an oracle, where the generator's bias affects rate and not limit.

**D2 — The situation layer moves from propositional constants to typed relational predicates.**
Grounds: V4, V5, V6. Every concept needing an argument (party, recipient, information item)
currently costs bespoke code, and that cost is the dominant review-churn driver.

**D3 — The hypothesis space is expressed as ILP-style language bias (mode declarations), not a
hand-written edit-type enum.** Grounds: it is the off-the-shelf named concept; ILASP compiles the
induction task to a meta-level ASP program, and we already depend on clingo.

**D4 — Behaviour AND/OR is a user decision recorded at extraction, not something the system
infers.** Grounds: Matt, this session. The system's job is to honour the recorded choice
consistently and dutifully; it never needs to resolve the ambiguity itself.

**D5 — Labels select which cases get a hypothesis generated; labels never appear in a generation
prompt.** Grounds: existing anti-cheat perimeter ("labels direct ATTENTION, never TRUTH"). Without
this the replay test is circular.

**D6 — Process failure classes are to be made structurally impossible, not reviewed for.**
Three mechanical properties: (a) required-field schema for a pre-registration record
`{metric, denominator, direction, threshold, procedure, trigger}`; (b) **a hypothesis is a pair
(change, gate), well-formed only if `gate(baseline) = FAIL`** — vacuity becomes a validation error
rather than finding B-3/S-2; (c) threshold hash frozen before the measurement exists (extend
`cycle.py`'s PREDICT discipline upward to cover designs). Grounds: V7 — the typed ceremony is
cheap, the prose is expensive, and the difference is typing.

**D7 — Pre-registration is derived mechanically from replay, not written by a human.** Apply the
edit, replay, freeze the resulting flip set before consulting labels. Note which part carries the
information: cases that *proposed* the edit flipping is near-tautological; **no-regression across
all other cases** and **collateral flips** are the real predictions, and no human pre-registration
has ever enumerated the latter.

**D8 — The design document becomes a rendered view of a structured object.** Grounds: V8's 15%
are update anomalies from duplicate storage; normalization removes them by construction.

**D9 — Sequencing: typed hypothesis record + normalized design object FIRST; relational encoding
second, and only after a paper version passes.** Grounds: the process fix is cheap, independent,
carries no migration risk, and covers ~55% of churn; doing it first means the relational work is
designed under the new process rather than being the last thing built the old way.

**D10 — Acceptance test for the relational encoding is the recurring review findings, not the
relevance items.** If M-1/E-3 and M-2/E-2 do not become answerable by inspection, the encoding
does not earn its migration cost. Grounds: V6 — that is where the money went.

---

## 3. REJECTED, BY NAME

- **Aggregation of unreliable judges** — von Neumann redundancy, majority vote, Dawid–Skene,
  Snorkel / data programming, debate, self-consistency. All require conditionally independent
  errors; V2 falsifies that locally. *Not* rejected as bad science — rejected as inapplicable here.
- **OWL / open-world semantics.** A coverage report must be able to assert non-coverage; OWA can
  only return "unknown," and constraining OWL back to closed-world means fighting the formalism.
  Closed-world is correct; the fix is making vocabulary-insufficiency *visible* rather than
  silently rendering it as `not_relevant`.
- **Canons of statutory construction as an interpretive policy.** Superseded by D4 — the user
  records the reading at extraction; the system needs no interpretive engine.
- **Round-trip-to-English equivalence judged by a second LLM.** Maximally correlated with the
  generator, and a decoder test masquerading as an encoder test.
- **A hand-written edit-type enum for representation changes.** Superseded by D3.
- **Retention / version-space failure as the explanation of +0.0003.** Falsified by V7. It applies
  *prospectively* to any future loop with an LLM proposing vocabularies unsupervised; it does not
  describe the history.
- **Entropy-over-interpreters as a certificate.** Usable as a *targeting* diagnostic (high entropy
  = definitely ambiguous) but invalid as a negative — correlated blind spots produce confident
  agreement on a shared misreading (V2).

## 4. CORRECTIONS MADE (errors this session, recorded so they are not re-derived)

1. Claimed the API keys were missing. They were present; Claude Code's Bash tool runs a
   non-interactive shell that does not load `~/.zshrc`.
2. Claimed AutoCedar's "LLM has no version space" failure explained our +0.0003. Falsified by
   `CYCLE_LOG.jsonl` (V7). Same symptom, different disease.
3. Framed PNAS/arXiv:2509.01186 as a "scoop." Wrong frame for a tool — the right questions are
   what is reusable and what is the deficit. Its entropy diagnostic and refinement loop are
   usable; its output is prose and its output object is behavioural consistency, not coverage.
4. Proposed canons of statutory construction; superseded by D4 the same session.
5. Said "the DSL is propositional." Half right — norms are relational (V4). Overstated.
6. Adopted "8 iterations" from Matt's prose as established fact before checking. It later
   *verified* (R8 exists), but the check should have preceded the claim.

## 5. OPEN

- **O1** — Do act constants also need arguments (`comply_restrict` → `comply(Restriction, Party)`),
  or is parameterising the situation layer sufficient? Decide during the paper translation.
- **O2** — Oracle self-consistency `p`, measurable with a held-back duplicate item. ExPairT-LLM
  guarantees hold for `p > 0.5`; we currently assume rather than measure.
- **O3** — Is blame localization rich enough *before* subsumption lands? Bag-overlap yields only
  "no atom matched," which supports `add_atom`/`attach_atom` proposals but not edge or formula
  proposals.
- **O4** — Adjudication seat should move from absolute membership queries to **pairwise** queries
  (ExPairT-LLM, AAAI 2026); not yet designed.

## 6. NEXT

Paper (no-code) relational translation of the existing representation, drafted against the S3B
harm-bearer / attribution-keying case — the one with four documented rounds of failure to pin it
in prose. See `RELATIONAL_PAPER_ENCODING.md`.
