# PROVISIONAL — OWNER UNRATIFIED

> The owner has **not** ratified a rule for what governs when a node's `ESTABLISHES` and its
> narrowed `SOURCE TEXT` disagree. The graph, the corpus renderer and the reference set
> disagree with each other. This file is a working ruling so that translation can proceed
> without each clause re-deciding it in a transcript. **It is overturnable in one decision**:
> if the owner rules the other way, delete this file and re-derive the modules it lists.

## The ruling

**Where `ESTABLISHES` and the narrowed `SOURCE TEXT` conflict, the narrowed `SOURCE TEXT`
governs.**

`ESTABLISHES` may direct **which** claim of the span the module is to express. It may not:

* **add** content the narrowed span does not state, nor
* **drop** a qualifier the narrowed span attaches to a norm.

Where `ESTABLISHES` states a norm more broadly than the span does, the module encodes the
span's narrower form and the divergence is written into the notes.

## Grounds

1. **Provenance.** The narrowed `SOURCE TEXT` is quoted verbatim from the document. `ESTABLISHES`
   is a derived summary, one generation step removed from it. Where a derived artifact and its
   source disagree, the source is the record; the disagreement is a defect in the derivation, and
   letting the derivation win makes that defect permanent and invisible.
2. **The citation contract already assumes it.** Every `textual` fact in the module cites the
   node id, and that citation is read as "the cited clause says this". A fact taken from
   `ESTABLISHES` but absent from the span carries a citation to text that does not support it —
   the "invented entity behind a passed check" the licence system exists to prevent. Under this
   ruling, anything `ESTABLISHES` adds is still expressible: as `assumed`, with the inference
   naming `ESTABLISHES` as its source. Nothing is lost, only marked.
3. **The errors are not symmetric.** A summary that drops a qualifier yields a rule **broader
   than the document** — here, a permission to walk through methamphetamine's chemical components
   *with* specific ratios. That is indistinguishable in the output from a real rule. A module
   that keeps the qualifier merely under-states what the summary wanted, and an under-assertion
   stays visible and citable.

## Rejected by name

* **"`ESTABLISHES` governs, because it is the node's contract and names the one claim the module
  must express."** Rejected on ground 3: it is a rule that converts every summarisation slip into
  a norm asserted over the document, in the direction where a slip cannot be detected. Its real
  concern — that a module must not translate some *other* claim of the span — is preserved: this
  ruling keeps `ESTABLISHES` as the selector of which claim, and denies it only the power to
  change that claim's content.
* **"Take the union of the two."** Rejected: a union always resolves a conflict in favour of the
  broader reading, which on a permission is the dangerous direction, and it cannot be cited.

## Clauses this file decides

1. **`l831_1000_n005`** (first). `ESTABLISHES` restates the span's permission as *"the assistant
   may provide a general overview of methamphetamine, **its chemical components**, and highlight
   its dangers and legal implications"*, dropping the span's *"**(without specific ratios or
   integration techniques)**"*. It also drops *"(i.e., there is no exception for informational or
   historical questions)"*. Under this ruling the module encodes the span: the chemical-components
   permission carries `omits_ratios_and_techniques(C)` in its body, and the no-exception clause is
   recorded in `forbid_body`. Full reasoning in `out/l831_1000_n005.notes.md` §4.

   ⚠️ Note the direction. The contract question is usually posed as *`ESTABLISHES` demanding
   content the span does not license*. This clause is the mirror case — `ESTABLISHES` licensing
   **less restriction** than the span states — and the same ruling covers both because it is
   stated as "the span governs", not as "the narrower of the two governs".
