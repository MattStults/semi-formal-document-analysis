# PROMPT FINDINGS — slice 1

⭐ **These are defects that belong to the PROMPT or to the NODE CONTRACT, not to the
translator.** The measured gap this file closes: the previous critic rejected the
borrowed-gloss fix BY NAME on the grounds that `10_output_format.md` line 66 requires it and
*"the worked example does exactly this"* — and it was probably right about the prompt. That
case was then filed as **a clean module**, which loses the finding entirely. A clean module
and a prompt defect are two different verdicts and are kept apart here.

Every finding below is stated as a question a later reader can apply. Where it is
**MECHANICALLY CHECKABLE** the check is named and the measurement is given.

---

## ⭐ PF1 — a node can be contractually required to both define and borrow the same name

**MECHANICALLY CHECKABLE. MEASURED: 16 nodes of the graph corpus.**

The user block hands the translator two instructions that cannot both be obeyed when one
name appears in both blocks:

* `PROVIDES (use EXACTLY these names as the predicates this module defines)`
* `NEEDS — … every one of them belongs in this module's requires … **never in ontology,
  never defined here**`

`l1001_1107_n001` lists `root_authority` in **both**. Its drafter resolved for `PROVIDES`
(define in `ontology`, `requires: []`) and named the conflict as its top UNSURE; its
independent critic reached the same conclusion and filed it as a prompt finding. Both are
right and neither had a rule to cite.

**The check** (few lines, nobody had written it):

```python
P, N = provides_block(node), needs_block(node)
assert not (set(P) & set(N)), f"{node_id}: {sorted(set(P)&set(N))} in BOTH"
```

Measured over the node corpus: **16 nodes** hit, on `root_authority`,
`authority_levels_hierarchy`, `applicable_instruction`, `candidate_instruction`,
`developer_authority`, `user_authority`.

⚠️ **This will get worse, not better.** `REVIEW_LIST.md` P9's corrected form hardens the
NEEDS side (*"a NEEDS name in `requires` and unused is CONTRACT-REQUIRED and must be left
alone"*), so a future reader applying P9 mechanically will charge this clean module — the
same class of error P9 was itself corrected for on 2026-08-16.

**Repair the prompt, not the modules:** one tie-break sentence in `node_worked_example.md`
contract 2 — a name appearing in both blocks is OWNED by the node, goes to `ontology`, and
`requires` does not repeat it. Or fix the graph so the two blocks are disjoint.

---

## ⭐ PF2 — what licence does a borrowed `NEEDS` gloss carry? The prompt answers twice, differently.

**MECHANICALLY CHECKABLE. MEASURED: a 2–2 split across four of my five clauses.**

Three of five independent critics raised this without being prompted to
(`l1001_1107_n007`, `l1001_1107_n012`, `l1108_1367_n004`), and `SWEEP.md` S1 shows the four
modules split 2–2 on the identical borrowed name `root_authority`.

The two instructions:

* **`10_output_format.md`** (the `requires`-gloss contract): a `requires` gloss records
  *"what you are assuming it is"*, and — in bold — *"⚠️ **You are not defining the term.**
  You are recording what this clause has to assume about it."* An assumption about another
  clause's term is, by construction, not something the citing clause's text says.
* **`node_worked_example.md`** contract 2 and its worked modules: the good example licenses
  the borrowed `authority_levels_hierarchy` gloss as `"licence": "textual", "cites": "<the
  citing node>"`, and the third example repeats it with `voice_turn_taking_rule`.

So the prose says *assumed* and the worked example demonstrates *textual*, and the worked
example is what translators copy. `00_task.md` is unambiguous about which side is dangerous:
*"Do not manufacture a citation to make a fact look textual… the single worst failure
available here"*, and failure mode #16 says the licence is the ONLY thing that makes an
imported meaning checkable.

⭐ **The sweep contributes a discriminator neither file has.** On `l1001_1107_n001` the
`textual` licence is *correct* — `root_authority` is also a `PROVIDES` name there and the
word `root` is literally in the cited narrowed text. On `l1001_1107_n012` it is *wrong* —
purely borrowed, and the cited text is a real-estate dialog with no authority vocabulary.

**The check:**

```python
# for each concepts entry whose name is in the node's NEEDS block and NOT in PROVIDES:
#   licence == "textual" is a dressed-up citation unless the narrowed span
#   contains a substring supporting the gloss
```

**Ruling wanted from the owner**, because the fix direction is contested and I did not edit
any module on my own authority: *a `concepts` gloss for a name that is in `NEEDS` and not in
`PROVIDES` is `assumed`, with the inference naming the node contract as the source.* If the
owner rules that way, `node_worked_example.md`'s own examples must change in the same
commit — otherwise the file keeps teaching the opposite, which is `DEBUGGING_TIPS` 19's
shape in a different field.

⛔ **Open and unrepaired:** `l1001_1107_n012` ships a `textual` licence I judge to be a
dressed-up citation, pending that ruling.

---

## ⭐ PF3 — the graph pipeline drops three quarters of the document's own cross-references, and `cross_references` is structurally inert

**MECHANICALLY CHECKABLE. MEASURED, two independent ways.**

**(a) The config's cross-reference machinery can never resolve on this corpus.**
`translate.cross_references` matches a clause's markdown anchors against other records'
`section_id`. In `node_corpus_all.json` **every record has `section_id == "graph_node"`** —
one constant for the whole corpus. So of the 46 distinct anchors the corpus carries, **zero**
can ever match, and `config_graph_nodes.json` sets `cross_references.enabled: true` while the
feature is dead. Two of my five spans carry the visible symptom:

```
⚠️ referenced but not resolvable in the corpus: assume_objective_pov
⚠️ referenced but not resolvable in the corpus: no_erotica_or_gore, transformation_exception
```

**(b) The `NEEDS` block does not compensate.** Of **172 anchor occurrences** in node source
texts, **131 appear nowhere in their node's `NEEDS` block.** `l1108_1367_n009` is a live
instance: its sentence points at `#no_erotica_or_gore` and `#transformation_exception`,
`NEEDS` is *(none)*, and the module correctly ships `requires: []` — so the document's own
statement that a transformation exception exists is invisible to the module that most needs
it. That is failure mode #2 ("missing cross-references — *silent*") occurring **upstream of
the translator**, where no translator-side check can reach it.

**Also measured, same family:** **15 of 97** distinct `NEEDS` names are provided by no node
in the corpus — including `objective_point_of_view`, which `l1108_1367_n004` borrows. Its
`requires-unprovided` note is therefore not a single-clause-scope artifact; it is dangling
corpus-wide, and the anti-rule that says such notes fire on every correct module hides that
distinction.

---

## ⭐ PF4 — a carve-out has no field it can land in

**MECHANICALLY CHECKABLE. MEASURED: 3 of 5 clauses carry the connective; `beats` is empty in 5 of 5.**

`00_task.md` rule 8b: *"A superiority claim goes in `beats`, with this clause as the sayer."*
`beats` needs the loser's clause id. **A node is never given the id of the sibling node its
`However` / `BAD[#anchor]` / `may only` carves out from.** Guessing one would violate rule 2
and could seed failure mode #17 (a cyclic priority relation).

Consequence, stated unsoftened: `l1108_1367_n004` is a permission that exists solely as an
exception to a prohibition in the *same sentence*, and a downstream query will find **no
ordering at all** between them. The relation survives only as English inside a `closure`
reason. The n004 critic named this; two other clauses have the same hole and their critics
did not.

**The check:** span carries an exception connective ∧ `beats == []` ∧ no counterpart id in
the user block ⇒ unrecordable relation, log it rather than pretending the module is complete.

---

## PF5 — `claims` carries two incompatible jobs, so P3's check fires on prompt-compliant work

**MECHANICALLY CHECKABLE.**

* `00_task.md` rule 3 and the schema: `claims` holds the clause's distinct claims, and
  `REVIEW_LIST.md` P3 says *"a claim present there and encoded nowhere is the fingerprint"*
  of a dropped obligation.
* `30_failure_modes.md` row 11: *"There is no field for an integrity constraint, so you
  cannot state the impossibility directly — **say it in `claims` instead**."*

`l1108_1367_n009` obeyed row 11 and carries two claims explicitly marked `META, deliberately
not encoded`. P3 then fires on a module that did exactly what it was told, and a critic
applying P3 mechanically would either raise false findings or "repair" them by adding the
`permit` its own analysis shows must not exist — which is the harmful direction.

**Remedy for the owner:** narrow P3 to *norm-stating* claims, and/or give deliberate
non-encoding notes their own field so `claims` stops being two lists in a trench coat.

---

## PF6 — `00_task.md` says an example is a reason to abstain; `node_worked_example.md` says the kind of passage is not the test

**MECHANICALLY CHECKABLE (a grep), and it is the most consequential finding in this file
because it is the probable CAUSE of the measured gap this whole run was built around.**

* `00_task.md`: *"If you cannot translate this clause faithfully — it is a section heading,
  it states a goal rather than a condition, **it is an example**, or its content is not
  expressible as rules — abstain and give the reason."*
* `node_worked_example.md`: translates a good/bad example node in full, and states the
  discriminator in bold — *"What decides between them is whether the node establishes
  anything the document says — **not what KIND of passage it is**."*

Both files are concatenated into the same system block, in that order.

⚠️ **This is a live contradiction and it is not the one already repaired.** The
2026-08-16 repair of `node_worked_example.md` fixed a self-contradiction *inside* that file;
the contradiction *between* it and `00_task.md` survives.

⭐ **Why it matters more than it looks.** The previously measured failure was a clause headed
`**Example**:` translated with **zero occurrences of "abstain" in its entire transcript**. The
natural reading was translator negligence. It is at least as likely to be this: the worked
example tells the translator that the KIND of passage is not the test, which makes the
abstention question feel **pre-answered** — and a pre-answered question is never asked aloud.
That reframes the remedy. Forcing the critic to answer the frame question in words (which
this run did, on all five clauses, and it was answered explicitly every time, including on
the `**Example**:` clause `l1001_1107_n012`) works — but it is treating a symptom of a
one-sentence prompt defect.

**Repair:** state the rule once. If the worked example's discriminator is the intended one,
delete "it is an example" from `00_task.md`'s trigger list and replace it with *"it
establishes nothing the document says"*.

---

## PF7 — the corpus reuses five authority predicate names across mutually inconsistent section-scoped meanings

**MECHANICALLY CHECKABLE. MEASURED.**

Distinct `PROVIDES` glosses per name, over the node corpus:

| name | providing nodes | distinct glosses |
|---|---:|---:|
| `guideline_authority` | 13 | 13 |
| `root_authority` | 11 | 10 |
| `user_authority` | 11 | 10 |
| `system_authority` | 4 | 4 |
| `developer_authority` | 3 | 3 |

The glosses are section-scoped and mutually exclusive — *"Rules in the
#assume_best_intentions section carry root authority"* vs *"Rules in the
#ignore_untrusted_data section carry root authority"* vs *"The root authority level, the
highest in the authority hierarchy"*. My `l1001_1107_n001` defines `root_authority/1` for
`#respect_creators`; `l1001_1107_n007`, `l1001_1107_n012` and `l1108_1367_n004` all borrow
the same name meaning `#protect_privacy` and `#avoid_extremist_content`.

⇒ At link time these unify cleanly and are wrong. **This is failure mode #9 ("same name,
different meanings — *silent*; measured 46 of 228 reused names") reproduced in the graph
layer**, and `30_failure_modes.md` §2 explicitly tells the translator it cannot see or fix
it. Nothing else is looking either. The predicate wants an argument for the section, or the
graph wants section-qualified names.

**The check:** group `PROVIDES` entries by name; any name with >1 distinct gloss is a
collision. Five lines.
