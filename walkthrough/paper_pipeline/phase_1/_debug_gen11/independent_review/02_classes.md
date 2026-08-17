# Mechanically detectable classes — MEASURED over all 17 signed modules
Script: scan.py / scan2.py in this directory. Reproducible, no model call.

| class | instances | modules affected |
|---|---|---|
| A. borrowed NEEDS name self-cited as `licence:textual, cites:<this node>` | 20 of 23 borrowed names | 12 / 17 |
| B. `licence:textual` entry whose body rests on `assumed`/`world` predicates | 32 | 12 / 17 |
| C. `requires` entry that appears in no rule body ("dead requires") | 18 | 14 / 17 |
| D. arity-0 concept used as a constant TERM | 3 | 2 / 17 |
| E. read-back carries a hedge the formal item does not ("generally", "by default") | 4 | 3 / 17 |
| — undeclared body predicates | 0 | 0 |
| — read_back `%` / slot-count mismatches | 0 | 0 |
| — requires/inputs overlaps | 0 | 0 |

Class A reproduces the figure already known (20 of 23, 12 of 17) — my instrument agrees with the
existing one, which is the point of running it.

## Class B is the answer to "what else looks like class A"
00_task.md states: "**A conclusion inherits the weakest licence in its derivation.** If a rule
depends on one `world` fact, everything it concludes rests on that fact. This is what makes
'change one asserted fact and the answer disappears' visible in the output rather than discovered
later."

32 entries across 12 of 17 modules are stamped `textual` while their bodies rest on predicates the
same module declared `assumed`. The weak licence is therefore NOT visible in the output — it is
discovered later, which is the exact failure the sentence names.

Worst instance, l1_170_n056: `overridden_by_higher_instruction(R)` is `licence:"textual"` with
body `user_request(R), developer_instruction(I), conflicts_with(R, I)` — where `conflicts_with` is
the module's own `assumed` concept ("the clause's exception turns on a conflict relation"). The
whole defeater, and therefore the whole clause, rests on an assumption that the record shows as
textual. Seven of the module's eight rule-bearing entries are in this state.

That the intended behaviour was achievable is proved inside the set: l2474_2554_n004 marks
`aligns_with_social_norms` as `world`/`toggleable`, and marks the `permit lie_by_omission` assert
that rests on it `world`/`toggleable` too. One module out of seventeen propagated.

Honest caveat, stated because it weakens my own finding: the prompt also says "A rule is not a
fact. Rules encode what the clause says and are traced by their read-back annotation. Licences are
for the facts your module asserts." An `ontology` entry WITH a body is a rule, so what its
`licence` field means is genuinely underdetermined by the prompt. Part of class B is a prompt
defect, not a module defect. But (i) the schema forces a licence onto those entries anyway, (ii)
`asserts` entries are affected too, and (iii) one module did it the other way — so the class is
real even after the caveat is granted.

## Class C — dead requires, 18 in 14 of 17
A `requires` entry names a predicate another clause must define. 18 of them are referenced by no
rule in their own module. They satisfy the header's "every NEEDS name belongs in requires" and
contribute nothing: nothing will ever link through them, and failure mode 15 ("'never fired' has
three causes ... declare `requires` honestly") cannot be told apart from a genuine dead rule.

Honest caveat: most dead entries are section-authority markers (`root_authority`,
`user_authority`, `guideline_authority`) which plausibly have no role in any rule body — the
defect may sit in the graph's NEEDS assignment rather than in the module. But the loop is
internally inconsistent about it: l2821_3040_n017 and l3239_3382_n002 DO put
`assistant_definition(A)` in a body, and l3239_3382_n004 does use
`interactive_vs_programmatic_setting(S, interactive)`. Same construction, opposite treatment,
one loop.

## Class E — the hedge that survives only in the read-back
Four asserts state a hedge in the read-back that the formal item does not carry:
- l1707_1973_n022 `forbid`   "keeping underlying prompt % private is **the assistant's default**"
- l171_426_n022   `forbid` ×2 "... is **generally** refused"
- l2821_3040_n017 `oblige`   "**by default**, assistant % should express uncertainty naturally"
The read-back is defined as "the English sentence a reviewer sees **instead of** the formal item".
A reviewer reads a defeasible default and signs an absolute prohibition. Small class (3 modules),
but it is the one that most directly defeats human review, and in l1707_1973_n022 it is paired
with a claims entry that misstates the span.
