# Ruling — the two bad worked examples the prompt dropped (`REVIEW_QUEUE.md` §2.2)

**Decided 2026-08-07 by Matt, on the evidence below. CLOSED.**

The design (`03_pipeline.md` "What a bad one looks like") lists five failure modes. The prompt kept
three and swapped two for act-indexing and missing-sayer cases — failures of the fixed relation
vocabulary, which did not exist when the design wrote its list. The queue asked: restore, or record
the swap as deliberate?

⇒ **They are not alike, and they get different answers.**

---

## #4 "imports a name without its content" — RESTORED

**It is live in our own output, at 7.5 %, and nothing detects it.** `[RAN]` Across 133 distinct
concepts (263 rows) from every stored run and eval, **10 have a gloss adding zero words beyond the
predicate name**:

| gloss adds | concept | gloss |
|---|---|---|
| 0 | `terrorism_act` | "an act of terrorism" |
| 0 | `mass_surveillance_act` | "an act of mass surveillance" |
| 0 | `persecution_act` | "an act of persecution" |

`terrorism_act(X)` stands for whatever the reader already thinks terrorism means. The document's
content about it is not in the module. It reads correctly in every explanation — which is exactly
what the design says about this mode.

This independently corroborates `STEP_stage4.md` finding (5) ("glosses are 71–100 % verbatim clause
vocabulary"), measured on one module against its clause; this measures 133 concepts against their
own names, and the two agree.

⇒ Restored as **bad example #6** in `prompt/20_worked_example.md`.

## #2 "translates in isolation" — DROP RECORDED AS DELIBERATE

**The harness now prevents the mechanism.** When the design wrote this, a clause was translated with
nothing but its own text, so a model had to guess what a referenced clause said. The stage-1 user
block now supplies **the full text of every cross-referenced clause**, resolved from the document's
own markdown anchors. `[RAN]` 77 clauses (13 %) carry a resolvable anchor and all 77 get the
referenced text.

⚠️ **This is a mitigation, not a proof.** Only ~13 % of clauses carry anchors at all, and
`03_pipeline.md` records finding the rest as an open problem. If a clause depends on another without
an anchor, the failure is still reachable and nothing supplies the text. The drop is justified by
the mechanism existing, not by the mode being impossible.

⛔ **Reopen this if** the unanchored-dependency work lands and shows real dependency density, or if
a stage-4 seat reports a module that assumed content it was never given.

---

## ⛔ Rejected by name: a stage-2 check for #4

Tempting, because the concept table makes glosses available **as data**. Two candidates, both tested:

1. **"Gloss adds no content beyond the name."** A proxy. Misfires on legitimate primitives —
   `system_message` → "C is a system message" is correct, because the document treats it as
   primitive.
2. **"The document elaborates this term elsewhere, but the module collapsed it into one symbol."**
   `[RAN]` **The signal is inverted.** Clauses mentioning the term: `system_message` **12** (8
   definitional) versus `terrorism` **2** (1 definitional). The check would flag the legitimate
   primitive hardest and the actual failure least.

⇒ No stage-2 check. #4 is a **semantic** question — "does this symbol carry what the document
means?" — and `README.md` already rules that those need a reader, which is stage 4.

**A note-level check was rejected explicitly**, on Matt's challenge: *"If it's just note level, who
sees it and how do we act on it? Why is this better than ignoring it?"* Nobody sees notes; they
drive no repair. This repo has already watched the `no %% provides:` warning fire on every module
until it became invisible. A note here would be that mistake made knowingly.

## Where detection actually lives

`STEP_stage4.md` seat **4r**, already named as "the whole point" for concept identity, and already
carrying finding (5) as the bound on how far it can be trusted. The measurement above is recorded
there.

⚠️ **Teaching against a failure does not detect it.** Bad example #6 changes what the model writes;
only 4r can tell whether a given symbol is hollow. Both are needed and neither substitutes.
