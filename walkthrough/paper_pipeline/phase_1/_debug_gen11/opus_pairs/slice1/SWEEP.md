# SWEEP — every class any slice-1 clause raised, run back across all 5

**Why this file exists.** The measured gap: the previous loop NAMED a licence-inheritance
class, called it *"mechanically checkable; nothing checks it"*, and left it in 12 of 17
clauses because the loop was per-clause with no end-of-run pass. A class found on clause 4
never reaches clause 1.

The sweep is `sweep.py` in this directory. Every check below is a **question a later reader
can apply mechanically** — that was the design constraint, and it paid: two of the eight
checks found something no per-clause critic could have seen, because *the finding is the
disagreement BETWEEN clauses and no single-clause reviewer is shown a second clause.*

Run it:
```
../../../semi-formal-experiment/.venv/bin/python _debug_gen11/opus_pairs/slice1/sweep.py
```

---

## ⭐ THE DELTA — what the sweep caught that the per-clause pass missed

### S1 — the borrowed-gloss licence SPLIT. **Primary result.**

**Q: for each `NEEDS` name, what licence does its `concepts` gloss carry?**

| clause | borrowed name | licence |
|---|---|---|
| `l1001_1107_n001` | `root_authority` | **`textual`** |
| `l1001_1107_n007` | `root_authority` | **`assumed`** |
| `l1001_1107_n012` | `root_authority` | **`textual`** |
| `l1108_1367_n004` | `root_authority` | **`assumed`** |
| `l1001_1107_n012` | `privacy_protection_rule` | `textual` |
| `l1108_1367_n004` | `objective_point_of_view` | `textual` |

**One borrowed name, four clauses, a 2–2 licence split.** Every one of the four independent
critics inspected this field. Three of them raised it — and each could only file it as *"a
prompt ambiguity, my module is defensible"*, because **each critic was shown exactly one
module and the defect is a disagreement between two.** The per-clause pass is structurally
incapable of seeing this, and that is the whole finding.

⭐ **And the sweep does more than flag it — it localises it, which no critic could.** Putting
the four side by side shows the split is not arbitrary:

* On `l1001_1107_n001`, `root_authority` is **also a `PROVIDES` name**, and the node's own
  narrowed text is `{#respect_creators authority=root}` — the word `root` is *in the cited
  text*. `textual` is correct there, on grounds that do not generalise.
* On `l1001_1107_n012`, `root_authority` is **purely borrowed**, and the node's narrowed text
  is a user/assistant dialog about real-estate agents containing no authority vocabulary
  whatsoever. `textual` there cites a clause that does not say it — the shape `00_task.md`
  calls *"the single worst failure available here"*.

⇒ **The discriminator is not "is it a NEEDS name" but "is the name ALSO in PROVIDES".** That
is a new rule, it is one line of Python, and neither the per-clause passes nor
`REVIEW_LIST.md` has it. It is `LESSONS.md` L1.

⛔ **UNREPAIRED, and reported unsoftened.** `l1001_1107_n012` ships with a `textual` licence
I judge to be a dressed-up citation. I did not edit it: `PROCEDURE.md` says the coordinator
does not edit a module, the n012 critic already filed it as a PROMPT FINDING under the
correct heading, and the repair direction is contested by the production prompt itself
(`node_worked_example.md` licenses NEEDS glosses `textual` by worked example). It needs the
owner ruling in `PROMPT_FINDINGS.md` PF2 before it is touched, not a coordinator's edit.

### S4 — inert ontology heads, and the check that P9 should have been

**Q: is a predicate an ontology HEAD that appears in no assert body and no other body?**

Raw form fires on **4 of 5** modules — which is the P9 failure all over again (an entry that
fires on correct work is how seat 4c reached 48/86 on known-good modules). Sharpened with one
extra clause, it fires on exactly the right two:

| clause | inert head | is it a `PROVIDES` name? | verdict |
|---|---|---|---|
| `l1001_1107_n001` | `root_authority` | **yes** | correct — it IS the deliverable |
| `l1001_1107_n007` | `privacy_context_dependence` | **yes** | correct — it IS the deliverable |
| `l1001_1107_n012` | `not_private_information` | **no** (`PROVIDES: (none)`) | coined and inert |
| `l1108_1367_n009` | `specific_circumstance` | **no** (`PROVIDES: sensitive_content`) | coined and inert |
| `l1108_1367_n004` | — | — | no inert head |

⭐ **The sharpened rule reproduces exactly the two findings the critics reached by reading,
and drops the two false positives.** Both critics that raised theirs (n012 F1, n009 F2)
declined the repair, and the sweep agrees with both declines — but the two clauses whose
inert head is *correct* were never at risk under the sharpened form. `LESSONS.md` L2.

### S7 — an open class closed in code, on 2 of 5

**Q: does the narrowed span carry `such as` / `e.g.` / `contexts like` / `including`? If so,
is the class it opens derivable ONLY from the members named?**

| clause | markers | class closed at |
|---|---|---|
| `l1108_1367_n004` | `contexts like` | `qualifying_discussion_context` — 3 members |
| `l1108_1367_n009` | `such as`, `e.g.` | `sensitive_content` — 2 · `specific_circumstance` — 4 |

Both critics found their own instance independently, which is what makes it a class rather
than an accident; the sweep adds that `l1108_1367_n009` carries it **twice**, which its own
critic reported once. In every instance the module's own `concepts` gloss says the class is
open while the compiled program closes it — **prose and code disagree in the module's own
words, and the read-back renders the prose.** `LESSONS.md` L3.

### S8 — the carve-out with nowhere to land, on 3 of 5

**Q: does the span carry an exception connective whose counterpart clause id was never
supplied?**

`l1001_1107_n012` (`BAD[#chain_of_command]`), `l1108_1367_n004` (`However`),
`l1108_1367_n009` (`may only` / `except`). **`beats` is empty in all five modules**, and no
module could have filled it: rule 8b requires the loser's clause id and no node contract
ever supplies one. Only the n004 critic named it. It is not a translator defect at all —
`PROMPT_FINDINGS.md` PF4.

### S5 — the document's own cross-references, dropped before the translator sees them

**Q: does the SOURCE TEXT carry a markdown anchor the `NEEDS` block never mentions?**

`l1108_1367_n004` drops `assume_objective_pov`; `l1108_1367_n009` drops **both**
`no_erotica_or_gore` and `transformation_exception` and consequently ships `requires: []`
while its source sentence points at two other sections. Its drafter flagged this as an
UNSURE against failure mode #2; its critic did not raise it. **Corpus-wide the sweep measures
131 of 172 anchor occurrences absent from their node's `NEEDS` block** — this is a corpus
property, not a property of my five. `PROMPT_FINDINGS.md` PF3.

### S2 — the self-loop

**Q: does the node NEED a name it also PROVIDES?** `l1001_1107_n001` does, on
`root_authority`, and its two contracts are then unsatisfiable together. The drafter flagged
it as its top UNSURE and the critic independently filed it as a prompt finding — so this one
the per-clause pass DID catch. The sweep's contribution is the denominator: **the same shape
occurs on 16 nodes of the graph corpus**, so it is a systematic contract defect, not one
node's quirk. `PROMPT_FINDINGS.md` PF1.

### S6 — `claims` overloaded

**Q: how many `claims` are encoded in no assert and no ontology entry?** `l1108_1367_n009`
carries 8 claims of which 2 are explicitly labelled `META, deliberately not encoded`, on the
instruction of `30_failure_modes.md` row 11. P3's fingerprint therefore fires on a
prompt-compliant module. Raised by the n009 critic only. `PROMPT_FINDINGS.md` PF5.

---

## What the sweep did NOT change

⛔ **No module was edited as a result of this sweep, and no `asserts` count moved.** Two of
the four sweep classes (S1, S4) identify real MINOR defects in shipped modules; both are
recorded unrepaired above with the reason. A sweep that quietly rewrites four modules on a
class discovered on the fifth is exactly the over-editing risk the turn structure was built
to avoid, and the repairs at issue turn on prompt contradictions an owner has to settle
first.

## Honest limits of this sweep

* Five clauses is a small denominator. S1's split is 2–2 on **one** borrowed name.
* S7 and S8 fire on 2 and 3 of 5 respectively; both are strongly corroborated by two
  independent critics reaching them separately, which is better evidence than the count.
* The corpus-wide figures (16 self-loops, 131/172 dropped anchors, 5 names carrying multiple
  section-scoped meanings) are measurements taken at this run's date. They are reported as
  measurements. **Nothing here pins an exact count of a live artifact as a gate.**
