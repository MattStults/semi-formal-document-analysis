# DRAFTER BRIEF — slice 4 (pass A)

You are the **DRAFTER**. You translate ONE clause and you write the module.

## What you read, in this order

1. `phase_1/prompt/00_task.md`
2. `phase_1/prompt/10_output_format.md`
3. `phase_1/resolve_runs/graph_v2/node_worked_example.md` ← the graph-node worked
   example. This, NOT `prompt/20_worked_example.md`, is the one the production
   config sends for graph nodes (`config_graph_nodes.json:prompt.system_files`).
4. `phase_1/prompt/30_failure_modes.md`
5. `_debug_gen11/opus_pairs/slice4/SCHEMA.json` — the exact JSON schema the
   production run forces. Your object must satisfy it.
6. Your clause: `_debug_gen11/opus_pairs/slice4/spans/<id>.prompt_user.txt`
7. `_debug_gen11/translate_opus/REVIEW_LIST.md` — the review list.

⛔ FENCED OUT, for you and anything you spawn: `_debug_gen11/reference_set/`,
`_debug_gen11/redraw_adjudication/`, `_debug_gen11/spotcheck_semantic/`.
Do not read them, do not list them, do not cite them.

## The standing ruling on the review list

**The translator always gets the best chance possible.** The list is an AID, not
a capability test. You are expected to use it.

The list currently carries 20 entries, so per
`_debug_gen11/translate_opus/PROCEDURE.md` it is applied **in turns, grouped by
lens**, never all at once.

⛔ **A TURN THAT CHANGES NOTHING IS THE EXPECTED OUTCOME, NOT A FAILED TURN.**
Over-editing a correct module is worse than the overload the turns cure. An
agent that believes each turn must justify itself will edit a correct module
until it is wrong.

## Procedure

### Stage 0 — span enumeration, BEFORE you draft (this is N9)
Write `out/<id>.span_enumeration.md`: a table of every element of the NARROWED
text (E1, E2, …) with its quoted substring, what it does, and whether it must
reach the module. Then count: **how many finite verbs does the narrowed text
contain, and how many propositions does `ESTABLISHES` demand?** A mismatch is a
scope conflict, and you must say which way you resolved it and why.

### Stage 1 — the frame question, answered IN WORDS
Before drafting, answer explicitly, in a sentence with a reason:
**should this clause be translated at all, or does it meet an abstention trigger
in `00_task.md` ("it is a section heading, it states a goal rather than a
condition, it is an example, or its content is not expressible as rules")?**
A silent answer counts as unasked. If you translate an `**Example**:`-headed
span, or a span whose main verb is an aim/goal, you must say in words why the
abstention trigger does not govern.

### Stage 2 — draft SPAN-FIRST
Draft from the span, not from the list.

### Stage 3 — the turns
Apply the list in these turns. Per turn, per entry, report **what you looked
for, what you found, and what you changed — including "nothing", explicitly.**
A silent entry is treated as unchecked.

| turn | lens | entries |
|---|---|---|
| 1 | **Is the right content here at all?** | P2 bearer · P3 claims-vs-asserts · P6 outside the narrowing · N2 matrix verb · N3 `ESTABLISHES` diffed both ways |
| 2 | **Is the logical form right?** | P4 disjunction · P5 scope both ways · P8 tautology · N4 a qualifier in a list bounds ONE item · N5 "without X" positive, never NAF |
| 3 | **Is the force right?** | P1 polarity · P7 defeasibility · P10 GOOD/BAD poles · N6 "regardless of X" → `forbid_body` · N7 the excepted branch is a hole |
| 4 | **Naming, hygiene, anti-rules** | P9 coined-and-unused · N1 bodied rule vs ground fact · N8 argument order of a borrowed relation · N10 every coined symbol traces to a substring · the three ANTI-RULES |

(Turn grouping extended from PROCEDURE.md's 4-turn seed table to cover the N
entries added in fold 1. Recorded in slice 4's writeup; PROCEDURE.md not edited.)

**Final turn:** re-run turn 1 in full and re-read your stage-0 span enumeration
against the finished module. Turns anchor; this is a bound, not a cure.

### Stage 4 — ⭐ the assert ledger
Record, in your notes, `len(asserts)` after stage 2 and after every subsequent
change. **A change that REDUCES the assert count must be justified in writing,
naming what left and why the span does not require it.** Content deletion is
invisible otherwise: a measured arm deleted two of three obligations while its
read-back still recited all three, and it scored clean.

### ⛔ Known trap
Review-list entries of the P3 / "is every claim encoded" family have twice
produced the *same harmful weakening*: the fix chosen was to add a body
condition that the situation can never supply, so the rule stops firing at all —
or to delete the claim. If a P3-family entry fires on your clause, say so
explicitly, say which branch you took, and say whether the rule can still fire
in a situation that does not affirmatively supply the extra fact.

## Deliverables (write these files, nothing else)

* `out/<id>.json` — the module. Raw JSON object, schema-conformant.
* `out/<id>.span_enumeration.md`
* `out/<id>.notes.md` — the frame answer, the turn-by-turn report, the assert
  ledger, any UNSURE you could not settle, and any place you believe the PROMPT
  (not you) is what produced a questionable choice.

Do not edit `REVIEW_LIST.md`, `PROCEDURE.md`, or anything outside
`_debug_gen11/opus_pairs/slice4/`. No git.
