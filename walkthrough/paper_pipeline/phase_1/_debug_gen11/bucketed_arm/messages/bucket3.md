PROCEDURE 3 of 4 — IS THE FORCE RIGHT?

**Step 1. The polarity ledger.**
List every entry in `asserts` whose `status` is `prefer`. **If that list is
empty, write "none" and go straight to step 2** — this step then has nothing to
do and that is the expected outcome on most modules.

For each `prefer` you listed, write its act name, and beside it quote the verb
in the SOURCE TEXT that governs that act.

* If the quoted verb is an AVOIDANCE — "avoid", "minimize", "refrain from",
  "should not", "don't" — and the act names the thing to be avoided, then the
  compiled rule states the OPPOSITE of the document. `status` has no negative
  pole, so the fix is to **name the avoidance as the act**: rename the act in
  `acts` and in every assert that uses it (`repeat_user_prompt` →
  `minimize_redundant_phrases`), keep `prefer`, keep every body exactly as it
  stands, and keep every `read_back` word for word.
* Where the span is that strong and the thing is not a gradient, use `forbid`
  instead of `prefer`.
* Never leave `status` and `read_back` disagreeing.

**Step 2. The hedge ledger.**
Quote every hedge in the span: "by default", "generally", "typically",
"usually", "should", "may", "might want to", "where possible", "in most cases".
For each hedge, write the assert it qualifies and the body condition that
carries that hedge — or NONE.

* `toggleable` is reserved for `world` facts, so a hedge has nowhere to live
  except a body condition. **An unconditional `oblige` is byte-identical to one
  whose default was dropped.**
* NONE, and the span NAMES the defeater → encode it as a body condition.
* NONE, and the span names NO defeater → ⛔ **do not invent one.** Say so
  explicitly in `claims` and in the `read_back`: the span hedges and the module
  cannot carry the hedge.

**Step 3. The hole ledger.**
Find every "unless", "except", "other than", "outside of" in the span. For each,
write the arm it excepts, and then write the assert you placed ON that excepted
arm — or NONE.

**NONE is the correct answer.** *"should honor … **unless** it conflicts"*
**WITHDRAWS** a requirement on the excepted branch. It does not create a
prohibition there. An "unless" arm is a HOLE, not a rule. If you placed a
`forbid` or an `oblige` on an excepted arm, **DELETE it** — it asserts something
the span never says.

Then, for every entry in `closure`: write the question it answers, and quote the
words of the span that decide that question — or NONE.

* NONE → set it to `unclear`. If the clause states a duty inside one trigger and
  takes no position outside it, reading its silence as blanket permission
  (`cepa`) is a commitment the clause never made. Measured: `cepa` was the wrong
  value on four separate clauses.
* Check where each `reason` is drawn from. A reason drawn from the module rather
  than the span is circular — *"it does not forbid other answers, so silence
  permits them"* is `cepa` justifying `cepa`. Circular reason → `unclear`.

---

⛔ ANTI-RULE that applies to this procedure. Do NOT do this; doing it is itself
an error. **Never make `status` and `read_back` agree by REWRITING THE
READ-BACK.** The two are written independently and that redundancy is the only
place a wrong status is visible. **Fix the formal item.** The mechanism
generalises: wherever two independently written fields disagree — body vs
read-back, gloss vs body, `claims` vs assert — the honest prose is usually the
evidence and the formal item is usually the defect. Repair the formal item
first, then update the prose's slots, preserving its wording.

Where a step's remedy would violate one of the twelve rules in my first
message, **the rule wins** — say what you found in `claims` rather than
encoding a remedy the format cannot carry.

Return the complete module object and nothing else.
