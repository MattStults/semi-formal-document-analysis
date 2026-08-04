# Blind open-coder brief

You are one of two independent coders inducing a taxonomy over a frozen
corpus of read-back loss phrases. This protocol has run twice, successfully:
once over the `missing` channel (268 records — HOLES: content of the clause
the atoms did not carry) producing `hole_taxonomy_coder_{a,b}.json`, and once
over the `unsupported` channel (95 records — FABRICATION: content the atoms
asserted that the clause did not say) producing
`fabrication_taxonomy_coder_{a,b}.json`.

## Why this seat exists

A loss corpus read once yields one person's framing, and this project has
already been burned by exactly that: a single-annotator lexical categoriser
put the missing-party share at 23%, the grammar's principal chain was partly
sold on that figure, and two independent blind coders later put the true share
at 2.2–3.0% (see the retraction preserved in `annotate.py`'s docstring). So
the rule is structural: a taxonomy over this corpus is evidence only where two
coders, working blind to each other and to the hypothesis the taxonomy will be
used to test, carve the corpus the same way. One coder's category is a
framing; a cross-coder-stable category is a finding.

## Input

Exactly one artifact: `hole_corpus.json`, produced by `prep_hole_corpus.py`.
It is frozen and flat so that both coders provably see byte-identical input —
never a hand-pasted sample. Its shape:

```json
{"artifact": "hole_corpus",
 "derived_from": "readback_results.json",
 "run": "fidelity",
 "clauses": <n>,
 "with_source_text": <n>,
 "missing":     [{"id": "m0001#m0", "clause_id": "m0001",
                  "phrase": "...", "clause_text": "..."}, ...],
 "unsupported": [{"id": "m0021#u0", ...}],
 "caveat": "..."}
```

You code ONE channel per run — `missing` or `unsupported` — and your output
declares which. The two channels answer different questions (a hole is not a
fabrication; a grammar feature would not fix a fabrication) and must never be
mixed in one taxonomy. Read the corpus's own `caveat` field and carry it: every
phrase is the read-back judge's paraphrase, not the document's wording, so your
taxonomy describes what that judge noticed and how it chose to say so.

## The task

**Bottom-up induction.** Read every record — phrase together with its
`clause_text` — and let the categories come from the corpus. You are not
handed a candidate list, and you must not import one: no pre-existing
linguistic taxonomy, no scheme from another project, and above all not the
grammar's own feature list (see blindness, below).

**Kinds, not topics.** A category names the KIND of content that was lost —
the semantic slot the lost fragment fills in its passage (a triggering
condition, an exception carve-out, a rationale, a manner qualifier, a list
member) — never the TOPIC of the clause it was lost from ("erotica",
"medical advice", "copyright"). A topic taxonomy of this corpus would just
reproduce the document's table of contents and say nothing about the
representation. Coder B's method note from the hole run is the standard:
"grouping by the semantic slot the lost fragment fills in its passage, then
tightening boundaries until the pairwise tests decided the hard cases."

**Category definitions carry their own boundaries.** Each category gets a
one-or-two-sentence definition, an explicit boundary note naming the
neighbouring categories it excludes and the test that decides the line, and a
few example phrases. A category whose boundary you cannot state is not ready.

**Assignment: one primary, optional secondary.** Every record gets exactly one
`primary` category; a `secondary` is allowed where a record genuinely
straddles a boundary, and null otherwise. Do not use secondary as a hedge on
every hard call — it is for records that are truly about two things.

**Explicit unclassified.** A record you cannot place without guessing goes in
`unclassified`, with the reason in your notes. Forcing it into the
least-bad category blunts that category's boundary test; three honest
unclassified records are worth more than a residual bucket. Both runs used
this (B left 3 dispositional-character phrases unclassified in the hole run
rather than coin a category of three; A left 1, B left 2 in the fabrication
run).

**Programmatic coverage self-check.** Before returning, verify by script — not
by eye — that every corpus id for your channel appears exactly once across
`assignments` + `unclassified`, no id is duplicated, none is missing, none is
outside the corpus, every category name used is declared, and each declared
`count` equals the actual assignment count. State in `notes` that you did
this. It will be re-derived independently, so a false claim here is
self-exposing.

**Notes are part of the output.** Record what surprised you, the judgement
calls on the hard boundaries, and the categories you considered and rejected
(with why). In both runs these notes carried findings the counts alone did not
(list-shattering inflation of raw counts; the fabrication corpus's systematic
stock-vocabulary reuse).

## Output schema

One JSON file:

```json
{"coder": "a" | "b",
 "channel": "missing" | "unsupported",
 "categories": [{"name": "snake_case_kind_name",
                 "definition": "...", "boundary": "...",
                 "examples": ["...", "..."], "count": <n>}, ...],
 "assignments": {"<record_id>": {"primary": "<category>",
                                 "secondary": "<category>" | null}, ...},
 "unclassified": ["<record_id>", ...],
 "notes": "verification statement + judgement calls + rejected categories"}
```

(`channel` may be absent on the original hole-run artifacts;
`check_taxonomy.py` defaults it to `missing` so those keep verifying.)

## What this seat may never see

The coder runs as a fresh-context agent whose ONLY repo input is
`hole_corpus.json`. Blind to, and why:

- **Every panel file and panel-reading module** — `behaviours.json`,
  `../data/panel-coverage.json`, `panel_universe.py`, `panel_v2.py`,
  `benchmark.py`, `DISAGREEMENT_REPORT.md`, `diagnose_disagreement.py` and its
  `case_fn.json`/`case_fp.json`. The taxonomy's conclusions are advertised as
  panel-free (MODULE_MAP §6b), and that property is only real if no coder
  could have been steered by what the panel rewards.
- **Every hypothesis-bearing file about the grammar** — `grammar.py`,
  `annotate_prompt.md`, `annotate.py`, `hole_rollup.py`, `LADDER_PLAN.md`,
  `ONTOLOGY_REFINEMENT.md`, `readback.py`, `HANDOFF.md`. The taxonomy exists
  to test which grammar features would recover the loss; a coder who has read
  the feature list (force prefixes, principal chains, role fields) will find
  categories shaped like it. `hole_rollup.py`'s banner states the design:
  the coders induce "bottom-up and blind to the grammar", and mapping
  categories onto grammar features is a SECOND, editorial step that
  "reintroduces exactly the prior the blind coding was designed to exclude".
- **The other coder's file, and any conversation about it.** Agreement
  between copies measures nothing.

## What validates the output

Run after both coders return, in this order:

1. **`check_taxonomy.py <coder_file> ...`** — independent re-derivation of
   coverage and counts from the corpus, channel-aware. Duplicated ids, missing
   ids, ids outside the corpus, undeclared categories, or a wrong `count`
   field each fail it. A coder file that does not come back `clean` is not
   data.
2. **Transcript blindness grep** — grep each coder's session transcript for
   the panel tokens and the blinded filenames above. The hole-run precedent:
   a review grepped the diagnostics for every panel token and found zero
   (MODULE_MAP §6b). A hit means the run is contaminated and is discarded,
   not patched.
3. **`taxonomy_agreement.py <file_a> <file_b>`** — chance-corrected partition
   agreement (adjusted Rand + NMI, both relabelling-invariant), plus the
   cross-tab and per-category purity so the score can be read rather than
   trusted. Name-matching across coders is meaningless; the partition is what
   is compared. Hole run measured: ARI +0.608 over 268 records.
4. **The reporting rule.** Only findings stable across both coders are
   reportable: a category (or merge of categories) with high cross-coder
   purity, or a corpus-level observation both coders' notes independently
   record. A category that exists in one partition only is one coder's
   framing and may be mentioned only as such. Any further mapping of
   categories onto grammar features (`hole_rollup.py`) is editorial, is
   applied to BOTH partitions, and is labelled as a judgement call wherever
   its numbers are quoted.
