# REVIEW LIST — v2 (absorbed 5 clauses)

Every entry is a **question to ask**, not a description. Each was MEASURED on
this corpus. A translator gets this list; an entry it did not check is worse
than one that found nothing.

Grow this file between waves. Each new entry names the clause that taught it.

---

## P1 — Polarity: does a `prefer` name the act to AVOID?
`status` has **no negative pole**. Faced with "avoid X" the model reliably emits
`prefer X` and writes a read-back that negates it, so the compiled rule states
the OPPOSITE of the document. Measured: `l1974_2125_n019` compiles to
`asserts(…, prefer, respond_with(R)) :- escalates_emotional_closeness(R)` from a
span marking that response **BAD**.
**Ask:** for each `prefer`, does the span want MORE of this act or LESS? If
less, name the avoidance as the act (`prefer minimize_redundant_phrases`), or
use `forbid` where the span is that strong. Never leave `status` and `read_back`
disagreeing.

## P2 — Deontic force on a non-norm: who is the subject of the main verb?
If it is OpenAI, the document, a message, or a section — it is a FACT, and a
fact rendered as `oblige`/`permit` asserts a rule the document never states.
Measured: *"**We** are committed to safeguarding privacy"* → `oblige
safeguard_privacy(I)`; *"a system or developer message **will list** the
available tools"* → `oblige list_tools(M)`.
**Ask:** is the bearer the assistant/model? If not, route to `ontology`.

## P3 — Dropped obligation with the exception retained
Measured: `l1_170_n056`, *"Models **should honor** user requests unless they
conflict…"* → only `forbid honor_request` on conflict; the obligation survives
nowhere. The module's own `claims` C1 carried it, unencoded.
**Ask:** check every entry in `claims` against the asserts. A claim present
there and encoded nowhere is the fingerprint.

## P4 — Disjunction encoded as conjunction
Measured: `l3147_3238_n003`, *"use a tool …, hedge …, **or** explain"* → three
`oblige` on one identical body, so an assistant that hedged violates two.
**Ask:** do several obliges share one body where the span says "or"?

## P5 — Scope drift, BOTH directions — and the counter-intuitive one
Measured: `l831_1000_n005` forbids every meth recipe (too wide) while permitting
every overview **including ones with specific ratios** (too narrow, in the
dangerous direction).
⚠️ **A body added to encode "regardless of context" WEAKENS the rule** — it
makes the prohibition fire only where that context fact exists.
**Ask:** does each body widen past the span's qualifier, or narrow a
prohibition the span states unconditionally?

## P6 — Content sourced OUTSIDE the narrowing
If `[node narrows this span to: "…"]` is present, the printed block around it is
context, not licence.
**Ask:** is every asserted predicate supported by the NARROWED text?
⚠️ See the PROVISIONAL ruling file before deciding — this interacts with
`ESTABLISHES` and the owner has not ratified a rule.

## P7 — Defeasibility is unencodable and must be RECORDED
`toggleable` is reserved for `world` facts, so "by default" / "generally" /
"unless" must be pushed into a body — and **an unconditional `oblige` is
byte-identical to one whose default was dropped.**
**Ask:** does the span hedge? If so, encode the defeater as a body condition if
you can, and say so explicitly in your notes if you cannot.

## P8 — Tautology
**Ask:** does any rule's head appear in its own body? Does a gloss restate the
predicate name instead of defining it?

## P9 — Declared and never used  ⚠️ CORRECTED 2026-08-16
⛔ **THE ORIGINAL FORM OF THIS ENTRY WAS WRONG and was the coordinator's
defect, not the translator's.** It said "does every name in
`ontology`/`requires`/`inputs` appear in some body?" — which **fires on every
CORRECT node module**, because the production prompt's contract 2 requires a
`NEEDS` name to be recorded in `requires` even when the module never uses it,
in bold, with a worked example. An entry that fires on correct work is how seat
4c reached 48/86 on known-good modules.
**Ask, narrowed to where it is true:** does every name YOU COINED — anything in
`ontology` or `inputs`, and any `requires` entry that is NOT a `NEEDS` name —
appear in some body? A coined name with no use is the fingerprint of dropped
content. **A NEEDS name in `requires` and unused is CONTRACT-REQUIRED and must
be left alone.**
*(corrected from `_debug_gen11/ds_opus_loop/FINDINGS.md`)*

## P10 — Both poles of a GOOD/BAD example must differ
Measured on a production module: one clause emitted the SAME `prefer` on the
SAME act for **both** `good_response(R)` and `bad_response(R)` — the compiled
program cannot tell the poles apart, which is the one thing the example exists
to say.
⛔ **CLAUSE ID DELIBERATELY WITHHELD (protocol fix R12, 2026-08-16).** This
entry previously named the clause. Some clauses in the run are CALIBRATION
clauses — carrying a known, independently-adjudicated defect so we can tell
whether the loop repairs something real rather than merely producing agreement.
The protocol has the adjudicator read this file at step 3, AFTER a blind pass
at step 2 — so naming a calibration clause here **hands over the answer and
destroys the blindness the blind pass exists to create.** It survived once by
luck of ordering, not by design. The example's teaching value is in the SHAPE,
which is preserved; the id is provenance and is recoverable from
`_debug_gen11/ds_opus_loop/` by the coordinator, who adjudicates after the
fact and is not blind.
**Ask:** if the span is a GOOD/BAD pair, do the two arms differ in `status` or
in act?

---

## ⛔ ANTI-RULES — do NOT "fix" these

* **`forbid X(R) :- X(R)` is SCHEMA-FORCED**, not a defect. An unconditional
  prohibition over a variable act requires the tautological binder.
* **`requires-unprovided` notes fire on every CORRECT single-clause module.**
  Moving the predicate into `inputs` to clear them destroys the distinction the
  design calls load-bearing.
* **Never make `status` and `read_back` agree by rewriting the read-back.** The
  two are written independently and that redundancy is the only place a wrong
  status is visible. Fix the status.

---
# ADDED IN FOLD 1 — v2, absorbed 5 clauses

## N1 — `ontology`: a BODIED RULE or a GROUND FACT?  ⭐ highest-value entry
**MEASURED, and two independent passes SPLIT on it.** `side_effect_examples(E) :- sends_email(E)` classifies any real situation where the assistant sends an email. `side_effect_examples(sending_email)` asserts a constant, and **nothing in a real situation can ever match it** — inert for behaviour matching, which is what this corpus exists to do.
**Ask:** will a situation fact ever unify with this atom? If the span names a KIND of thing, prefer the bodied rule over a coined constant. Reserve ground atoms for facts about the DOCUMENT (`root_authority(section_x)`), where there is no situation to match.
*(l461_608_n015. Absorbs "a ground constant is the only place its qualifier can live" and "naming a kind of action does not make it an act".)*

## N2 — Strip the MATRIX VERB before you read the span
**MEASURED: production emitted a permission from this span TWICE, under two different prompts, and P2's subject test did not stop it.** *"**We're exploring how to** let developers and users generate erotica and gore"* — matrix verb *exploring how to*, subject OpenAI, and its OBJECT is a rule. The embedded rule is fluent and carries its own condition, which is exactly why it reads as translatable.
**Ask:** what is the main verb and who is its subject? If its object is a rule, the span is ABOUT a rule and does not state one. A subordinate clause inherits the subject it elides — score it on the matrix subject. And where the hedge IS the main verb it has no body to be pushed into (P7's remedy fails): promote it to a predicate (`under_exploration(...)`) or it vanishes.
*(l1108_1367_n014. Absorbs 3 lessons.)*

## N3 — Diff `ESTABLISHES` against the span in BOTH directions
**MEASURED: it can DROP a qualifier as well as demand extra content.** Here it restated the permission with the span's own parenthetical deleted — following it faithfully reproduces exactly the over-permission previously measured on this clause.
**Ask:** what does `ESTABLISHES` say that the span does not — and what does the span say that `ESTABLISHES` drops?
*(l831_1000_n005. See PROVISIONAL.md: the narrowing governs.)*

## N4 — A qualifier in a list bounds ONE item
*"a general overview of methamphetamine, its chemical components **(without specific ratios or integration techniques)**, and highlight its dangers"* — the parenthetical binds the middle item only.
**Ask:** which item does it attach to? Propagating it "to be safe" invents an untraceable restriction; dropping it permits the unqualified case, which is the dangerous direction.
*(l831_1000_n005)*

## N5 — "without X" must be POSITIVE, never negation-as-failure
Under NAF, `not X` makes SILENCE license the act. Encode `omits_ratios_and_techniques(C)` as a thing to be established, not `not includes_ratios(C)`.
**Ask:** does any body rely on the ABSENCE of a fact to permit something?
*(l831_1000_n005)*

## N6 — "regardless of X" has a DESTINATION, and it is `forbid_body`
Body-absence alone is a half-encoding: it stops THIS module conditioning on X, but nothing stops a LATER module adding the exception the span forbids.
**Ask:** does the span exclude an exception? Then ban the term from the relevant head via `forbid_body`.
*(l831_1000_n005. Addendum to P5.)*

## N7 — The EXCEPTED branch is a hole, not a rule
The mirror of P3. *"should honor … **unless** it conflicts"* WITHDRAWS a requirement; it does not create a prohibition on the excepted branch. Adding `forbid` there asserts something the span never says. Same reasoning governs `closure`: a `cepa` closure re-asserts the silence you just declined to assert — use `unclear`.
**Ask:** does an "unless" arm carry its own assert, or a closure deciding what the span left open?
*(l1_170_n056)*

## N8 — A borrowed relation of arity >= 2 has an ARGUMENT ORDER the gloss does not fix
A total inversion — `authority_levels_hierarchy(higher, lower)` vs `(lower, higher)` — **passes every deterministic check we have.**
**Ask:** for each borrowed relation, is the argument order stated anywhere? If not, write your reading into the `concepts` gloss so a provider mismatch surfaces as a description disagreement rather than a silent inversion.
*(l1_170_n056)*

## N9 — Count the FINITE VERBS before drafting
**MEASURED: this is why two clauses burned every repair attempt and emitted nothing.** Asked to justify four propositions from a text containing two, each redraft MOVES the unanchored content instead of removing it. Repair-loop exhaustion on a short span is a SCOPE CONFLICT, not difficulty — and the two are indistinguishable in the findings log while wanting opposite remedies.
**Ask, before the first draft:** how many finite verbs does the narrowed text contain, and how many propositions does `ESTABLISHES` demand?
*(l2405_2473_n001)*

## N10 — Every coined symbol must trace to a SUBSTRING of the narrowed text
Caught a live near-miss: the constant `tiananmen_example` — fluent, obviously right to anyone who has read the section, and **unanchored**, because the narrowed text names no event.
**Ask:** for each name you coin, which substring of the NARROWED span does it come from? If none, you are importing knowledge the citation cannot support.
*(l2405_2473_n001)*
