PROCEDURE 1 of 4 — IS THE RIGHT CONTENT IN THIS MODULE?

**Step 1. The claims ledger.**
List every entry in `claims`, in order. Beside each one write the `asserts`
entry (or `ontology` rule) that encodes it, naming its `act` and its `status` —
or write NONE.

* Where you wrote NONE: go to the SOURCE TEXT and decide whether the narrowed
  span states that claim. If the span does NOT state it, **DELETE the claim.**
  (The fix for an out-of-scope claim is to delete the claim, never to add an
  assert for it.) If the span DOES state it, add the assert that encodes it.
* Where you named an assert: read that assert's body and write down one
  situation in which the body is satisfied. If nothing a situation could ever
  supply satisfies the body, the claim is not encoded — it is unreachable.
  Fix the body, or delete the claim.

⚠️ `claims` and `asserts` can agree with each other and both be wrong. Read
each claim against the SPAN, not against your own asserts.

**Step 2. The coinage ledger.**
List every predicate name this module COINS — every entry in `concepts`,
`ontology` and `acts` that is not a name handed to you by the node header.
Beside each name write the exact substring of the NARROWED text it comes from,
or NONE. Then do the same for that entry's `gloss`: the exact substring the
gloss's content comes from, or NONE.

* NONE on the name → rename it to a name that traces to the span, or delete
  the item and record in `claims` what the span said that you could not name.
* NONE on the gloss while the name traces → this is the known blind spot: the
  gloss has imported material from a neighbouring sentence. Cut the imported
  material.
* A FUSED name (`exaggerated_or_stereotypical`) assembled from two or three
  separate legitimate substrings counts as NONE. It welds a disjunction into
  one opaque symbol. Split it into separate items.

⚠️ Vocabulary that appears in the node's own `PROVIDES`/`NEEDS` glosses is not
thereby "outside the narrowing". Check the source text, not your memory of the
node header.

**Step 3. The two-column comparison.**
Write column (a): everything `ESTABLISHES` says. Write column (b): everything
the narrowed `SOURCE TEXT` says. Then write the two differences:

* in (a) and not in (b) — `ESTABLISHES` is ADDING content the span does not
  state. It may direct WHICH claim of the span you express; it may not add.
  Keep it only as `assumed`, with the `inference` field naming `ESTABLISHES` as
  its source. Nothing is lost, only marked.
* in (b) and not in (a) — the span states a qualifier `ESTABLISHES` drops.
  **The narrowed SOURCE TEXT governs.** Encode the qualifier.

---

⛔ ANTI-RULE that applies to this procedure. Do NOT "fix" this; changing it is
itself an error. **A `requires` entry that no module here provides is CORRECT
on a single-clause module.** Moving the predicate into `inputs` to silence that
destroys a load-bearing distinction. This is the single most common false alarm
on this corpus. A `NEEDS` name sitting in `requires` and used nowhere is
CONTRACT-REQUIRED — leave it alone.

Where a step's remedy would violate one of the twelve rules in my first
message, **the rule wins** — say what you found in `claims` rather than
encoding a remedy the format cannot carry.

Return the complete module object and nothing else.
