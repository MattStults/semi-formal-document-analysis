# Deterministic script vs. model context — where each check belongs

Companion to `00_established_practice.md`. Splits the eight checks into what runs for free and
what needs a model, and — for the model work — what must and must not be in context.

**Ordering principle: every free check gates every paid one.** All deterministic checks run first.
A translation that does not link, or contains a rule that can never fire, does not get a judge
call. With ~$6.44 of budget this is not a nicety.

---

## A. Deterministic — scripts, no model, $0

| check | mechanism | status |
|---|---|---|
| **Link resolution** | clingo's `atom does not occur in any rule head`, minus predicates declared in a `%% inputs:` header | ✅ built (`link.py` L2) |
| **Anchor closure** | regex for `](#anchor)` over the clause text; `section_id` values are the targets | ✅ built (`link.py` L1) |
| **Rule-shape bans** | `%% forbid-body: head <- predicate`, static scan | ✅ built (`link.py` L3) |
| ⭐ **Vacuity / interesting witness** | ⚠️ **scope-relative — see §F.** Inputs become choice atoms; ask the solver to *construct* a situation where the rule fires (brave consequences), rather than checking whether hand-written probes hit it. No witness → classify per §F | ⬜ buildable, one solve per rule |
| **Isomorphism conformance** | one file per clause; filename ↔ `%% clause:` header ↔ a real clause id; no file defining two clauses | ⬜ trivial |
| **Provenance completeness** | every fact carries `%% from: mXXXX`; every cited id exists; every id is in the anchor closure or flagged | ⬜ trivial |
| **Probe execution** | run must-violate / must-permit sets, diff against expected verdicts | ⬜ trivial |
| **Determinism & set identity** | same input → same answer set; ordering changes never change membership | ⬜ trivial |
| ⭐ **Opaque-stub detection** | a predicate standing for an anchor-referenced section that has *no defining rules* and appears only as an uninterpreted constant — the name was imported, the content was not | ⬜ buildable |

⚠️ **Provenance completeness is a script; provenance *correctness* is not.** A script can verify
that a fact cites `m0203` and that `m0203` exists. Whether `m0203` actually says it is a judgement.

---

## B. Model at GENERATION time

**Context it must have:**

1. **The clause text**, verbatim.
2. ⭐ **The anchor-closure clauses' text.** A clause that modifies machinery defined elsewhere
   cannot be translated correctly in isolation — this is the single highest-value context item.
3. ⭐ **The existing predicate vocabulary**, with signatures and glosses. Without it, one clause
   emits `scope/2` and another emits `exception_applies/2` and **they never link**. Linking only
   works if translations converge on shared predicate names, so the vocabulary is a hard input,
   not a nicety.
4. **The isomorphism instruction** — one clause, one module; do not merge, even where merging is
   logically equivalent (Bench-Capon & Coenen).
5. **The interface convention** — `%% provides:`, `%% inputs:`, `%% from:` headers.
6. **The known-hard constructions**, as authoring rules rather than discovered defects:
   - failure conditions must be *positive atoms*, never bare `not …` — negation-as-failure carries
     no trace and produces read-backs whose stated reason is unverifiable;
   - claims about the rule set (*"purpose never lifts"*) are `%% forbid-body` declarations, not
     constraints — a constraint on an underivable atom is vacuous.

**Context it must NOT have:**

- ⛔ the behaviour being matched, or any behaviour;
- ⛔ any panel label, gold, or downstream relevance verdict;
- ⛔ the probe cases and their expected verdicts — otherwise the translation is fitted to the test.

---

## C. Model at VERIFICATION time — three distinct seats, not one

The literature's shape is *independent judges with consensus, calibrated against human judgement
on a sample* (arXiv 2606.31002). These are three different questions needing three different
contexts; collapsing them into one prompt is what produces a judge that passes fabricated facts.

### C1 — Faithfulness judge (blind)
**Gets:** the clause text + the xclingo verbalisation.
**Not:** the `.lp` source — a judge shown the code grades the code, not the meaning.
**Asks:** does the paraphrase assert anything the clause does not support?
**Blind spot, structural:** entities imported from other clauses. The clause does not enumerate
what exists, so nothing in this context can reveal a fabricated one. C2 exists for that.

### C2 — ⭐ Provenance judge (per fact, not per clause)
**Gets:** one fact + the text of the clause that fact cites.
**Asks:** does *this* clause license *this* fact?
**Catches:** the fabrication class C1 cannot. A made-up fact has no clause to cite, so it fails
the deterministic completeness check; a *miscited* fact fails here.
This is the per-fact half of DO-178C-style bidirectional traceability.

### C3 — Sufficiency judge
**Gets:** the clause + the *set* of verbalisations across all probe cases.
**Asks:** could a reader recover what the clause requires?
**Why the set:** a multi-branch conditional cannot be conveyed by one branch's trace. Sufficiency
is a property of the probe set.

### C4 — Probe author (generative, adversarial)
**Gets:** the clause + the translation's interface.
**Produces:** a **must-violate** set and a **must-permit** set (Verus-SpecGym's accept/reject
pairing). The must-permit half is what detects over-permissiveness and is the half usually
omitted.
**Should be a different seat from the translator** — a translator writing its own reject set
tests what it already thought of.

### Optional C5 — Author-facing paraphrase loop
ACE's own design: show the verbalisation back to the *translating* model and let it revise.
Catches misunderstanding rather than unfaithfulness, and costs one call. Distinct from C1, which
must stay blind.

---

## D. Pipeline order

```
1. GENERATE          model, context per §B
2. link + shape      script  ── fail → back to 1, with the specific unresolved predicate
3. probe authoring   model, C4
4. run probes        script  ── expected vs actual
5. vacuity/witness   script  ── any rule that never fired → back to 1
6. provenance        script (completeness) ── missing citation → back to 1
7. C2 provenance     model, per fact ── miscited → back to 1
8. C1 faithfulness   model, blind, n judges + consensus
9. C3 sufficiency    model, over the probe set
```

Steps 2, 4, 5, 6 are free and reject most defects. Steps 7–9 are the paid ones and only ever see
translations that already survived the free checks.

---

## F. ⭐ When to run vacuity, and why "never fired" is three different findings

A rule that never fires is **not** thereby vacuous. Demonstrated: `unlifted(…, out_of_scope)` in
`m0255` yields 5 witnesses with `m0203` linked and 0 without it. Run on the clause alone, a
perfectly good rule reads as vacuous — the condition is a *linker* one.

**Vacuity is only meaningful at a declared link scope**, and it runs *after* linking is clean, at
the clause's transitive anchor closure. It does not need the whole corpus, so it stays per-clause
incremental.

When a rule has no witness, classify deterministically:

| condition | diagnosis | fix |
|---|---|---|
| a body predicate has no provider in scope, but one exists elsewhere in the corpus | **linker error** | name the clause, link it |
| no provider anywhere in the corpus | **unresolved reference** | that clause is not translated yet |
| all providers present, still no witness | **genuine vacuity** | the rule is broken |

⇒ **Consequence for C4.** If the solver constructs witnesses it can also *enumerate* reachable
situations. That displaces most of the probe-author seat: rather than a model inventing cases, the
solver enumerates and the model only judges *"would the text permit or forbid this one?"* — work
moves from a generative seat to a deterministic one, which is what the budget wants, and it is
closer to Verus-SpecGym's accept/reject-the-right-concrete-cases framing.

---

## E. Two open design questions

1. **Predicate vocabulary growth.** Generation needs the existing vocabulary, but the first clause
   has none and every clause may need a new predicate. Is there a merge/refactor step, and who
   adjudicates when two clauses coin different names for the same relation? This is the atom
   vocabulary problem one level up, and linking depends entirely on solving it.
2. **Anchor closure is a lower bound.** Only ~13% of clauses carry explicit anchors, so implicit
   dependencies rely on surfacing at step 2 as unresolved predicates.

   ⚠️ **A plainly omitted dependency is NOT the risk here — C3 catches it.** Measured: given a
   clause and a verbalisation covering only some of its claims, the sufficiency judge named the
   uncovered claims correctly, with no access to the source. If the clause text mentions the
   dependency, the paraphrase's silence on it shows up as a `MISSING` item.

   The residual case is the **faithful-but-hollow stub**: a clause naming a cross-referenced
   concept (*"follow the chain of command"*), translated as a bare uninterpreted predicate. The
   verbalisation echoes the clause's own words, so it reads as both faithful and sufficient —
   while the formal object carries none of the referenced section's content. The clause is the
   wrong reference point for a dependency whose substance lives elsewhere, so no judge comparing
   against it can help. Opaque-stub detection (§A) is the answer, and it is deterministic.
