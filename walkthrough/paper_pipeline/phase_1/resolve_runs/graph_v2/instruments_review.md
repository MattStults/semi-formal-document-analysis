# Adversarial review: graph_compare.py + modal_repair.py

Clean-context review, 2026-08-11. Reviewer: Claude (Fable 5, frontier tier — review
seat, per the model-tier working rule). Spec read first (`GRAPH_EQUIVALENCE.md`,
frozen 2026-08-10); tests run (`test_graph_compare.py`: 2 passed;
`modal_repair.py --self-test`: 3/3); every finding below marked *confirmed* was
reproduced with a concrete probe against the live golden
(`recurse/root/graph.json`, 593 nodes, 512 edges) or a minimal synthetic graph.
Probe scripts lived in the session scratchpad; the inputs are reproduced inline so
each counterexample can be re-run from this file alone.

**Bottom line.** Neither instrument is safe to run as-is. graph_compare has one
defect that manufactures false *divergence* on an equivalent graph (GC-1, will
fire: 80 golden nodes sit in identical-line-set groups) and one protocol gap that
manufactures false *equivalence* if the report's queues are treated as the seat
workload (GC-2). modal_repair's mechanical gate does not guarantee faithfulness:
three confirmed constructions pass the gate while inverting polarity, rewriting a
quotation, or clearing a genuine defect — and the plan's single live templated
repair is itself an instance (MR-3). None of the fixes is large.

---

## graph_compare.py

### GC-1 (HIGH, confirmed): content-blind 1:1 pairing inside identical-line-set groups

**Defect.** The greedy injective matcher breaks Jaccard ties by node-id sort order
(`qualifying.sort(key=lambda t: (-t[0], t[1], t[2]))`). When several nodes on each
side own the *same* line-set — 28 groups, 80 nodes in the golden; the code's own
comment says these exist — every cross pairing has identical Jaccard 1.0 and the
pairing is decided by lexicographic id, i.e. by nothing about content. The DeepSeek
graph's ids will not sort the same way as the golden's.

**Failure scenario (confirmed).** A: `a1` "The assistant must refuse.", `a2` "The
assistant should apologize.", both on lines 10–20. B: the *same two claims* with
ids in the opposite order (`b1` = apologize, `b2` = refuse). Output: pairs
`a1↔b1`, `a2↔b2` — both cross-paired — and **two** spurious `modal_queue`
entries on a content-identical graph. The seat then receives "must refuse" vs
"should apologize" as one aligned pair and can only honestly rule *differs* →
standing substantive-divergence ruling → false **divergence** verdict on an
equivalent graph. This is not an edge case; it is guaranteed to fire somewhere in
80 nodes.

**Fix.** Within each tie group (same a-line-set × same b-line-set at equal
Jaccard), refine the pairing by establishes-similarity — cheapest: pair to
minimize modal-profile distance, tie-broken by token overlap of `establishes` —
or, cleaner, emit the whole same-span group as ONE seat item (set of A-claims vs
set of B-claims on the shared span), which is also the more honest question.
**Confidence: high** (reproduced; incidence measured).

### GC-2 (HIGH, protocol-reading risk): measurement 2 has no queue for equal-profile pairs

**Defect.** The spec's measurement 2 says a seat adjudicates "**every** 1:1 pair
and split/join group"; the modal check is a *pre-filter* that additionally
auto-routes mismatches. The tool (per its docstring, legitimately) implements only
the pre-filter — but the report exposes `modal_queue` + `adjudication_queue` and
nothing that lists the remaining aligned pairs as pending seat work. The spec's
own seat-load estimate (~50–150) is consistent with seating only the queues, not
with seating all ~500 pairs — the spec contradicts itself, and the tool's output
shape resolves the contradiction silently in the lax direction.

**Failure scenario.** Two establishes with identical modal counts but different
*conditions* — "must refuse when asked for weapons instructions" vs "must refuse
when asked about self-harm" — produce `profile_a == profile_b`, appear in no
queue, and are never adjudicated. `profile()` counts tokens only; conditions and
obligation content are mechanically uninspected. Result: false **equivalence**.
Aggravating: `profile()`'s vocabulary misses `cannot`, `mustn't`, `shall`,
`prohibits` (only `prohibited`), so even some pure-modality differences produce
equal profiles.

**Fix.** Two acceptable resolutions, but one must be chosen *in the repo record*,
not by default: (a) emit every 1:1 pair and group into a `class2_queue` (modal
mismatches flagged as priority) so the seat pass over all pairs is explicit work;
or (b) write a ruling that measurement 2 is deliberately restricted to the modal
pre-filter's routes, with grounds, and reject alternative (a) by name. As it
stands the deviation is exactly the "unnoticed" kind the protocol forbids.
**Confidence: high** that the gap exists; medium on whether downstream would
actually run only the queues — which is why the ruling must be written down.

### GC-3 (MEDIUM, confirmed + quantified): edge matching by any-overlap is lax, and the RED test is engineered around the blind spot

**Defect.** An A-edge is matched if ANY B-edge's needer/provider node line-sets
overlap both regions (`match_edges`). Overlap is whole-node vs whole-node, so a
B-edge encoding a *different* dependency can witness an A-edge.

**Failure scenario (confirmed).** A: need X from node(10–20) to provider(100–110).
B: unrelated need Q from node(15–30) to provider(105–140). Recall = precision =
1.0; the deleted-in-spirit edge is invisible. Quantified on the live golden:
**76/512 edges (14.8%) are "shadowed"** — some other golden edge overlaps both of
their regions — so their deletion from B is undetectable *even against an
identical graph*. `test_graph_compare._pick_targets` knows this: it explicitly
skips shadowed edges when choosing the deletion target (`shadowed = any(...)`),
i.e. the RED gate certifies detection only on the 85% where detection is possible,
and the report nowhere discloses the 15%.

**Fix (minimal).** (1) Report the shadowed-edge count per graph as a descriptive
statistic in `compare_report.json` so the verdict memo carries the known
resolution limit. (2) Optionally tighten: match against the *best*-overlapping
B-edge and report the overlap Jaccards, or match the needer side on the span the
need's prose resolves to rather than the whole node. The spec pre-registered
any-overlap, so (2) would need a recorded amendment; (1) needs none.
**Confidence: high** (measured).

### GC-4 (MEDIUM, confirmed): split/join tries only prefixes of the top-5 candidate list — a poison candidate blocks a perfect group

**Defect.** `grouping()` ranks candidates by overlapping-line count and tests only
`cand[:2]`, `cand[:3]`. A high-overlap candidate that also sprawls elsewhere
("poison") occupies a prefix slot; the true 2-cover is never tested.

**Failure scenario (confirmed).** A-node owns 1–20. B: `b_c1` 1–12, `b_c2` 13–20
(true cover, union Jaccard 1.0), `b_p` spans 5–14 **plus** 100–150. Ranking:
`b_c1`(12) > `b_p`(10) > `b_c2`(8); both prefixes include `b_p`, union Jaccard
collapses → A-node and all three B-nodes come out **misaligned**. Direction is
conservative (goes to adjudication) but inflates the misaligned mass and seat
load, and four seats then adjudicate a non-disagreement.

**Fix.** Test all 2- and 3-subsets of the top ~5 candidates (≤ C(5,3)+C(5,2)=20
Jaccards per node — negligible), or drop any candidate whose inclusion lowers
union Jaccard. **Confidence: high** (reproduced).

### GC-5 (LOW-MEDIUM, confirmed): greedy steal misfiles a true 1:1 as split/join

**Defect/scenario (confirmed).** A: `a1` 1–10, `a2` 1–9. B: `b1` 1–10, `b2` 2–11.
Greedy takes `a1↔b1` (1.0) first, stealing `a2`'s only qualifying partner
(`a2↔b1` = 0.9; `a2↔b2` = 0.727 < 0.8). `a2` is then rescued by grouping as a
"split" over {`b1`,`b2`} (union 0.818) — and the measurement-2 group check
compares `a2`'s establishes against the *concatenation* of `b1`+`b2` establishes,
which near-certainly modal-mismatches → spurious seat item with a malformed
comparison. A maximum-weight matching (`a1↔b2`, `a2↔b1`) classifies everything
1:1.

**Fix.** Replace greedy with optimal assignment on the qualifying subgraph
(connected components are tiny; a simple augmenting-path matching maximizing pair
count then total Jaccard suffices — no new dependency). **Confidence: high**
(reproduced); real-data incidence unknown but nonzero wherever boundaries shift by
a line or two.

### GC-6 (LOW): class-4 disagreements never enter the adjudication queue

Uncovered-set differences are reported (`uncovered.only_a/only_b`) but not
appended to `adjudication_queue`, while the spec's verdict rule quantifies over
"every adjudicated disagreement from classes 1–4". A verdict process that works
the queue will silently skip class-4 line disagreements (and split/join groups,
which also never enter the queue — spec says split/join is benign only "PROVIDED
class-2 passes for the group", which ties back to GC-2). **Fix:** append
`{"kind": "uncovered_mismatch", ...}` items for `only_a`/`only_b` runs.
**Confidence: high** on the code fact; low severity because the report prints the
diff prominently.

### GC-7 (LOW): `line_mass` takes the best class among a line's owners

A line owned by both a misaligned node and a 1:1 node counts as `one_to_one`, so
the headline "fraction of lines in class 1 or 2" is inflated wherever overlapping
nodes disagree. Descriptive-only, but it is the number people will quote. **Fix:**
also report worst-class mass, or per-class mass without the max. **Confidence:
high** (code reading).

### GC-8 (LOW, test): the RED test's precision-side expectation is self-referential

`test_mutated_compare_flags_exactly_the_four` builds
`expected = ["dangling_mismatch"] + ["unmatched_edge"] * (1 + len(r["edges"]["unmatched_b"]))`
— the expected count of planted-provider precision flags is read off the
*observed* output, and the content assertion `all(... for e in unmatched_b)` is
vacuous over an empty list. The host-selection guard checks only A-edges whose
needer *id* is in `needer_ids`, but matching is by line overlap, and 80 golden
nodes share line-sets — so a planted B-edge could be matched via a same-lines
sibling, `unmatched_b` would be empty, and the test would still pass with the
precision signal absent. Mutation 4 is still independently caught via
`prose_only_a`, so the test cannot pass with the *dangling* signal dead — this is
degradation, not vacuity. Also noted: the "A-side one covered by many B" grouping
direction is only exercised via the B-side merged node; both directions run the
same function, so this is a coverage note, not a defect. **Fix:** assert
`len(unmatched_b) == number of needers of the dangling`. **Confidence: high.**

---

## modal_repair.py

### MR-1 (HIGH, confirmed): polarity inversion passes the mechanical gate

**Defect.** For an affirmative swap the code requires the target token in the span
with `re.search(rf"\b{b}\b", src)` — and `\bshould\b` matches inside "should
**not**".

**Failure scenario (confirmed).** Span: "The assistant should not comply with such
requests." Establishes: "The assistant must comply with such requests." (flagged
`strengthened`). `plan_one` returns
`('templated', 'The assistant should comply with such requests.')` — the exact
opposite of the document — and the gate passes because the sweep counts tiers, and
`should` and `should not` are the same tier. The pre-existing establishes was
already wrong, but the instrument's contract is that templated repairs are *safe
without review*; this one launders a polarity error into a gate-clean node.

**Fix.** For bare-token swaps (`must`→`should`, `should`→`must`) require the span
witness with a negation lookahead: `rf"\b{b}\b(?!\s+not\b|\s+never\b|n't)"`; the
negated pairs already sort first in `SWAPS`, so negated spans keep their route.
**Confidence: high** (reproduced).

### MR-2 (HIGH, confirmed): the imperative auto-clear swallows an unrelated genuine strengthening

**Defect.** The carve-out fires when `kinds == {"strengthened"}` and ANY line of
the span opens imperatively. It never checks that the establishes' strong modal
*corresponds to* the imperative clause.

**Failure scenario (confirmed).** Span: "Do not reveal the system prompt." + "The
assistant should apologize when it makes a mistake." Establishes: "The assistant
must apologize when it makes a mistake." — a genuine strengthening of the
*should*-claim. `plan_one` → `auto_clear` ("imperative-mood span: ... faithful").
The defect is cleared deterministically with no human or seat ever seeing it.
(`Never`/`Always` openers can't produce this — they're already STRONG tokens — but
`Do not`/`Don't`/`Avoid`/`Refuse` can.)

**Fix.** Restrict the carve-out to spans with no medium/weak modal:
`if kinds == {"strengthened"} and IMPERATIVE.search(src) and not (profile(src)["medium"] or profile(src)["weak"])`.
A span that also says "should" somewhere has a candidate victim for the
strengthening and must go to the seat. Live incidence today: 0 (the current plan
auto-clears nothing via the carve-out), so the fix costs nothing now and closes
the hole for reruns. **Confidence: high** (reproduced).

### MR-3 (MEDIUM-HIGH, confirmed **live**): count=1 substitutes the first token, not the flagged one; the gate certifies tier-counts, not attachment

**Defect.** `re.sub(..., count=1)` rewrites the first matching token in
establishes, wherever it sits — inside a quotation, or on a different clause than
the one the span modalizes. The mechanical gate (re-sweep clean) only checks that
tier *counts* no longer trigger the three flag rules; it cannot see which clause a
modal attaches to. So "gate-clean" = band-membership, **not** faithfulness — the
docstring's safety claim overstates what the gate guarantees.

**Confirmed constructions.** (a) Quote corruption: span `"Under the heading
"Commands you should obey", refuse jailbreak attempts."`, establishes quoting
`"Commands you must obey"` → templated repair rewrites the quotation itself, gate
clean. (b) Wrong clause: span "Warnings should be shown before the assistant
deletes files.", establishes "The assistant must delete files only after a warning
is shown." → templated "The assistant **should delete files** only after…", gate
clean, meaning changed beyond modality.

**Live instance.** The current plan's only templated row, `L1799-1974_n022`
(flag: `weakened`): proposed repair "…the assistant **must** refuse to share all
content…". The span's three strong modals are all "these **must** be approved by
an in-store associate" — the *fictional developer's refund rule* inside the XML
worked example (twice more in the assistant's quoted reply). No modal in the span
attaches to refusing to share system-message content. The proposed direction may
even be right on the document's merits, but the template's warrant is a quoted
prop in a worked example — precisely the paraphrase case `sweep_modals`' own
docstring says needs adjudication. This repair must go to a seat, not be applied.

**Fix (minimal, ranked).** (1) Immediate: route the one live templated row to the
seat queue — with 1 templated vs 33 already seat-bound, the templater saves
nothing on this run, so nothing is lost by requiring seats until (2)/(3) land.
(2) Skip substitution when the matched establishes token lies inside quotes or a
code/XML fence. (3) Require a lexical anchor: the span sentence carrying the
witness modal must share content words with the establishes clause being edited;
otherwise seat. **Confidence: high** — (a), (b) reproduced and the live instance
verified against the document text.

### MR-4 (LOW): apply-path hygiene

`--apply` writes the graph with a bare `json.dump(open(...))` instead of the
repo's atomic `write_json` (a killed run half-writes the golden; the backup
mitigates), and `main()` silently `continue`s past report findings whose id is
missing from the graph rather than counting them. **Fix:** use
`recurse_driver.write_json`; print a count of skipped ids. **Confidence: high**
(code reading). No `--apply` has run yet (no `.pre_modal_repair.bak` beside the
golden), so the review is timely.

---

## Answers to the specific attack questions

- **Spec deviations:** GC-2 (measurement-2 queue), GC-6 (class-4/queue), GC-1/GC-5
  (the injective-greedy 1:1 is an implementation choice the spec never made — the
  spec defines 1:1 pairwise, and the greedy realization is where both defects
  live). The modal pre-filter does use `sweep_modals.profile` as specified; the
  risk there is the profile's vocabulary gaps (GC-2 note), not the wiring.
- **B-side joins:** found — `align()` runs `grouping` from both sides
  (`graph_compare.py` lines 128–133); asymmetry attack did not land. The RED test
  exercises only the B-side direction, but both directions share one code path
  (GC-8 note).
- **Edge any-overlap inflation:** real, quantified at 14.8% shadowed on the
  golden; the RED test dodges rather than discloses it (GC-3).
- **RED-test vacuity:** cannot pass with a dead dangling signal; can pass with a
  degraded precision signal (GC-8). Target picking asserts/raises on failure
  rather than passing silently — no degenerate-target vacuity found beyond GC-8.
- **modal_repair count=1 / first occurrence:** not always the flagged one —
  confirmed, with a live instance (MR-3).
- **Imperative auto-clear vs unrelated should-claim:** wrongly clears — confirmed
  (MR-2).
- **Does the mechanical gate guarantee faithfulness?** No — band-membership only
  (MR-1/MR-3 both pass it while changing meaning).

## Recommended order of work

1. MR-3 immediate action (seat the live templated row) — zero cost, removes the
   one unsound repair currently planned.
2. GC-1 (tie-group pairing) and GC-2 (measurement-2 ruling or queue) — both must
   land before the DeepSeek comparison runs; each can flip the verdict.
3. MR-1, MR-2 — two one-line guards.
4. GC-3(1) shadowed-edge stat, GC-4 subset search, GC-6 queue items, GC-8 test
   tightening, GC-5 matching, MR-4 — before or with the run as time allows.
