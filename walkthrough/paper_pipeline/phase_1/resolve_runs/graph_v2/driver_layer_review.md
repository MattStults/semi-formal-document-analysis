# Clean-context adversarial review — driver autofix/validator layer + GOLDEN_PROTOCOL accuracy

Date: 2026-08-11. Reviewer: clean-context agent (Fable tier). Scope per dispatch:
recurse_driver.py's autofix/validator layer (NOT the call()/build() plumbing) and
GOLDEN_PROTOCOL.md against EXPERIMENTS.md / AUDIT_KEY.md / adjudication/DISPOSITION.json.
Method: full read of the layer, the 36-test suite (all pass, 90s), and nine executable
probes (scratchpad `probe_attacks.py`); every Part-1 finding below was **demonstrated by
running code**, not inferred. Confidence: CERTAIN = probe output shown; HIGH = read-only
but unambiguous.

---

## PART 1 — the autofix/validator layer

### F1. A self-merge (`survivor == retired`) silently deletes the node — CERTAIN, rank 1

**Defect.** `apply_decisions` accepts `{"survivor": "a", "retired": "a"}`. Both lookups
hit the same node, `merge_loss(blob, own_establishes)` is trivially empty (a text always
contains itself), spans are doubled, then `nodes.remove(r)` removes the node entirely.
Probe: `errs: [] | log: ['merged a into a'] | surviving ids: ['b']` — node `a` and its
establishes are gone with a success log line. No mid-build step re-checks coverage after
an unwind (unwind() writes graph.json without leaf-grade validation), so the loss
surfaces only at post-build `graph_check` as unaccounted lines — or, if another node
co-covers those lines, never.

**Evidence.** recurse_driver.py:398–417; probe P1.

**Minimal fix.** In the merge loop: `if m.get("survivor") == m.get("retired"):
errs.append(f"merge names the same node twice: {m}"); continue`. One-line pin:
self-merge is RED.

### F2. `merge_loss` is blind to lowercase prose — a merge can delete an entire claim — CERTAIN, rank 2

**Defect.** `MERGE_EL` only extracts enumerated items `(N) …`, Capitalized Multi-Word
phrases, and `"quoted"` terms. A retired establishes written as ordinary lowercase prose
yields **zero elements**, so `merge_loss` returns `[]` and the merge passes the F19
check. Probe: survivor "the sky is blue", retired "users must never be deceived about
billing practices" → `errs: []`, retired node removed, its establishes deleted.
`merge_check.py` (the downstream instrument GOLDEN §6 relies on before applying repairs)
uses the **same three regexes**, so the post-hoc net has the same hole. The historical
RED case (n028/n008 "No Authority") passes only because tier names are capitalized.

**Evidence.** recurse_driver.py:332–344; merge_check.py:11–22; probe P2.

**Minimal fix.** Add a floor beneath the heuristic: if `elements(retired_text)` is empty,
require the retired establishes' content words (say, tokens ≥5 chars minus stopwords) to
appear in the survivor blob at ≥ some fraction, else flag for adjudication. Do not lower
anything — this only adds a trigger. Pin with a lowercase-loss RED test.

### F3. The provenance validator is DEAD after autofix, and the claimed backstop is false — CERTAIN, rank 3

**Defect.** `autofix_division`'s docstring: "established_around itself is never altered,
so a genuinely misplaced seed still fails validation." False in both directions:

- **ea in-span, wrong child:** after the contiguity fix, children tile `[lo,hi]`, so any
  in-span ea lands in SOME child and the provider link is reassigned to it — the F17
  provenance error can never fire (probe P5/d3: `errs: []` always).
- **ea out-of-span (the hallucinated seed):** validate_division's guard
  `lo <= ea_lo and ea_hi <= hi` makes it SKIP the check entirely, so it validates clean
  (probe: ea `[950,960]` in span 1–900 → `errs: []`). Nothing anywhere checks that
  established_around lies inside the span.
- The suite's `test_provenance_autofix_repairs_the_live_root_failure` carries the comment
  "still fails validation" on exactly this d2 case **but only asserts
  `"driver_autofixes" not in d2`** — it never calls validate_division, so the false claim
  is pinned as a comment, not tested.

Consequence: when established_around is the lie, a CORRECT `provides_side_child` is
silently overwritten to match the lie (probe P5: correct link 1 → flipped to 2, validates
clean), and the model never receives a repair prompt about the inconsistency it emitted.
The one live incident that motivated the autofix had ea right and the link wrong; the
opposite case is now unrecoverable until (at best) the unwind's cross_link_report.

**Evidence.** recurse_driver.py:116–172, 219–232; test_recurse_driver.py:385–410; probes
P5 + follow-up.

**Minimal fix.** (a) validate_division: error when a seed's established_around falls
outside `[lo,hi]` (it is derived from the parent's own text — an out-of-span ea is always
a hallucination). (b) Fix the test to assert what its comment claims. (c) Log the
provenance reassignment as a WARNING in health.jsonl too, so a run with many flips is
visible — the reassignment is a coin-flip between two model statements and currently
leaves no aggregate trace.

### F4. Exact-duplicate structure nodes pass validation via dedupe, then BOTH get appended — CERTAIN, rank 4

**Defect.** In `apply_decisions`, structure nodes are validated by building a probe graph
and calling `validate_leaf`, which runs `dedupe_nodes` FIRST — so two byte-identical
structure nodes (same id) are deduped inside the probe, the duplicate-id check sees one,
validation passes. The append loop then iterates the ORIGINAL `sns` list and checks
`sn["id"] in by_id`, but `by_id` is never updated as structure nodes are appended.
Probe: `errs: [] | appended ids: ['L1-10_dup', 'L1-10_dup']` — duplicate ids in the
merged artifact. At the next level up, `apply_decisions` hits "duplicate node id across
children" — an error in a CACHED child artifact the model cannot repair, so the build
dies after max_repairs (manual artifact deletion required). At the root there is no next
level; only post-build graph_check's `!! duplicate ids` catches it. This is precisely the
review's target shape: an autofix (dedupe) running before a validator masks the error
that validator exists to catch.

**Evidence.** recurse_driver.py:418–431, 245–267; probe P3.

**Minimal fix.** In the append loop, add `by_id[sn["id"]] = sn` after appending (makes
the existing check catch the second copy), or dedupe/duplicate-check `sns` itself before
the probe.

### F5. Self-satisfying resolutions are mechanically checkable but unchecked — CERTAIN, rank 5

**Defect.** A resolution renaming a needer's need to a name **the needer itself
provides** applies cleanly (probe P8: `errs: []`, need resolved against its own node).
The pre-registered c21/root keys both list "self-satisfying chain_of_command" as the
failure mode to watch, and the prompt forbids it — but the code path that could enforce
the mechanical subcase (sole provider == needer) doesn't. The audit's stratum B is the
only net, and it samples.

**Evidence.** recurse_driver.py:377–397; EXPERIMENTS.md pre-registered c21 key; probe P8.

**Minimal fix.** In the resolution loop: if `provides[newname] == [n["id"]]`, error
("resolution would self-satisfy: sole provider is the needer").

### F6. No health telemetry for unwind artifacts — HIGH, rank 6

**Defect.** `_health` is called only from `leaf()`. `unwind()` writes its merged
graph.json with no health row (probe P9: rows = `['leaf','leaf']`, no unwind row). The
2026-08-11 postmortem's damage propagated **up two unwinds**; the doc (GOLDEN §2) claims
telemetry is "emitted per artifact". A degenerate merge outcome (e.g. F1's deletion, or
a duplicate flood surviving into an unwind) produces no density/needs row at exactly the
levels where bulk aggregates.

**Evidence.** recurse_driver.py:744–766, 783–836; probe P9.

**Minimal fix.** Call `self._health(g, lo, hi, "unwind", wdir)` before returning from
`unwind()`.

### F7. Cross-link child indices are never range-checked — HIGH, rank 7

**Defect.** `provides_side_child: 7` with 2 children validates clean when the seed lacks
established_around (probe P4: `errs: []`) — the provenance check is guarded by
`1 <= pi <= len(spans)` and simply skips out-of-range values; `needs_side_child` is never
looked at anywhere. A division whose model dropped a child (shifting its own indices)
sails through. The division is later fed verbatim into the unwind prompt as authority.

**Minimal fix.** In the cross-link loop: error when either `*_side_child` is an int
outside `1..len(children)`.

### F8. Gap-closing can swallow a dropped MIDDLE child; the extended child may never re-divide — MEDIUM, rank 8

**Defect (bounded).** Intended `[1,100],[101,300],[301,500]` emitted without the middle
child becomes `[1,300],[301,500]` via gap-close (probe P6), and `[1,300]` at
leaf_max=300 goes **straight to Phase L** — the "re-divided at the next level, so no cut
information is lost" justification (docstring) fails exactly at spans ≤ leaf_max. Leaf
coverage identity still guarantees no CONTENT loss, so this is a granularity/attribution
defect, not a data-loss one — but it is invisible: the autofix log says "gap closed",
which reads as a blank-line repair, not a possible dropped child. Also note gap lines are
always assigned to the EARLIER child, an arbitrary choice with seed-provenance
consequences (F3 interacts: the reassignment target depends on which side absorbed the
gap).

**Minimal fix.** Log a louder marker when a closed gap exceeds a few lines (e.g. >10):
that is dropped-child-shaped, not blank-line-shaped; surface it in health.jsonl.

### F9. Minor (LOW, ranked last, fixes optional)

- **dedupe key omits unknown fields**: two nodes identical on
  (establishes, spans, needs, provides) but differing in an extra annotation field lose
  the second node's annotation silently (probe P7). Schemas are non-strict, so extras are
  legal. Acceptable trade; worth a docstring line.
- **`_span_lo`/`_span_hi` leak into the persisted artifact** (probe P9:
  division.json keys include both) and thence into the unwind prompt JSON. Hygiene:
  `d.pop(...)` before write, or accept and document.
- **Validator paths deliberately deadened by autofix** (first-child-start,
  last-child-end, gap errors in validate_division) now fire only for overlaps and
  malformed spans in production; they remain reachable in tests only. Intentional per the
  extend-only design — noted so nobody mistakes the tests for evidence the repair-round
  path exercises them.

**Not findings (attacks that failed):** overlap masking (extend-only never creates or
hides overlaps — probed reversed/overlapping children, all still RED); repair-round
contamination by mutated spans (each repair re-parses the model's fresh reply; the
transcript carries the model's ORIGINAL text); partial application persistence (unwind
validates decisions on a deep copy first, applies only a clean set); chained/duplicate
retired merges (ValueError is caught by `_attempt` and becomes a repair); dedupe losing
provider references (needs reference names, not ids). The 969-dup→dedupe→pass path is
working as designed: the deduped remainder must still pass coverage identity on its own.

---

## PART 2 — GOLDEN_PROTOCOL.md vs the record

**Verified accurate** (checked against EXPERIMENTS.md, AUDIT_KEY.md, DISPOSITION.json,
and the filesystem): 76 candidates = 40 repair + 36 false_positive (verdicts_0..3.json
reconcile exactly); 2/40 instrument artifacts (ids match); ~6 expected unsampled
instances; density band 0.7 ≈ 2× the 0.13–0.35 healthy range; 969 duplicates / 5.3
nodes-per-line incident; stratum thresholds A ≥90/80–90/<80 and B ≥90 match the key;
auditor-material list matches the key's clean-context rules; graph_stripped.json,
audit/AUDIT_RESULTS.md, adjudication/verdicts_*.json, and the pre-sweep backup
(recurse/root/graph.pre_sweep_2026-08-10.json) all exist; both sweeps carry --self-test;
the never-do rules each trace to a recorded incident (leaf-dodge, c1 pre-answer flag,
zero-dangling R5, line-count dispute, garbled n026 repair, false completion reports).

### G1. §1 describes the golden's generation as something it wasn't — HIGH, rank 1

**Defect.** §1 says the procedure is "distilled from the 2026-08-10/11 build" and
prescribes `recurse_driver.py` with schema forcing, accumulating repair, dedupe, and
health bands. The actual golden graph (593 nodes) was built by the **Haiku subagent
recursion** with manual repair turns; the driver's DeepSeek build (ds1/ds2) was the run
that produced the degenerate-leaf failure and, per EXPERIMENTS.md's last entry, was
still incomplete (c1 re-drawing at 128K). dedupe_nodes, LEAF_DENSITY_MAX, and
health.jsonl were built **after** the golden existed, in response to the driver build's
failure — they have never produced a golden. A new-document runner following §1 would
believe the driver path is golden-proven; it is probe-proven and partial-build-proven.

**Fix.** One honest sentence in §1: "The existing golden was produced by the subagent
recursion; the driver is the productionized path, validated by phase probes (D/L/U) and
a partial build, not yet by a completed golden."

### G2. The pre-registered unwind keys — the record's actual scoring mechanism — are omitted — HIGH, rank 2

**Defect.** §1 claims "each unwind is scored in-flight." The record shows exactly TWO
unwinds scored against **pre-registered keys written before the unwind ran** (c21: 6/6;
root: R1–R6), and the remaining ~16 checked mechanically. The pre-registration step —
arguably the strongest verification act in the whole build, and the reason R4's
chain-of-command gap and the R1 restatement merge are trustworthy — appears nowhere in
the protocol. A new-document run following this doc would skip it, and "scored
in-flight" (unqualified) overstates what happened at the other 16 unwinds.

**Fix.** Add to §1: "Before each STRUCTURALLY LOADED unwind (root; any unwind whose
division predicted cross-links), write a pre-registered key — expected resolutions,
merges, escalations, and the failure modes to watch — before the unwind runs; score
against it." State that mechanical checks alone covered the routine unwinds.

### G3. §7's closed-loop pass rule would FAIL the actual golden — MEDIUM, rank 3

**Defect.** §7: "Pass = the flag set equals the adjudicated-keep set exactly: every
accepted false positive still flags, zero unexpected flags." The record's residual is 36
accepted FPs **+ 2 instrument artifacts** = 38 flags. Under the doc's rule as written,
the 2 artifact flags are "unexpected" and the golden fails its own closed loop. The
record handled them correctly (hand-inspected, recorded in DISPOSITION); the doc dropped
the category.

**Fix.** §7: "…equals the adjudicated-keep set (accepted false positives PLUS recorded
instrument artifacts) exactly."

### G4. Step-4 sampling is not reproducible: `audit_sample.py` does not exist — MEDIUM, rank 4

**Defect.** AUDIT_KEY.md: "Deterministic, seed=42, drawn by script (`audit_sample.py`)."
The script exists nowhere in the tree (searched walkthrough/ recursively). Likewise §3's
"the id-diff across unwinds (caught the one deletion violation)" names an instrument
with no packaged script. GOLDEN_PROTOCOL says "instruments and worked artifacts
referenced below live in this directory" — for these two, false. A new-document run
cannot re-execute step 4's sampling or step 3's id-diff as documented.

**Fix.** Either commit the scripts (the sample_*.json files pin what they must
reproduce) or amend the doc: "sampling script must be written per document and committed
with the key; the id-diff is a one-liner over pre/post unwind node-id sets — commit it."

### G5. §1's "Leaves" list promises artifacts the driver does not save — MEDIUM, rank 5

**Defect.** §1 leaves: "the run directory tree (per-node dispatches, replies, repairs)."
The driver persists division.json/graph.json per node plus failed/ replies; **successful
dispatches, raw replies, and repair transcripts are not written anywhere**. The subagent
build had transcripts; a driver build does not. This matters downstream: §4's
clean-context rule ("auditors never see build transcripts") and §1's "never let a seat
see build transcripts" presuppose artifacts a driver run wouldn't have — harmless — but
an operator expecting per-dispatch replay material (as probe_node.py uses) will find only
final artifacts.

**Fix.** Either add optional dispatch/reply logging to the driver, or correct the leaves
list to "per-node artifacts (division.json/graph.json), failed replies, health.jsonl."

### G6. Smaller record mismatches — LOW, rank 6

- §4 omits AUDIT_KEY's pre-registered D escalation (">2 of 15 → coverage rule needs
  work") and C's disposition ("individually adjudicated; each a finding, not a rate") —
  both are thresholds a new run needs; and the doc's "sampled deterministically" drops
  the seed=42 pin that makes it deterministic.
- §6 says verify proposals with "`merge_check`"; the record used the driver's
  `merge_loss` — same regexes either way, which per Part-1 F2 means this verification
  is weaker than the sentence implies. Worth a caveat until F2 is fixed.
- Preamble "every instrument is RED-verified before first use": true for the sweeps,
  merge_check, and graph_check (calibrated on v1's failures); no RED record exists for
  the sampling arithmetic or the id-diff — consistent with G4.

---

## Suggested order of fixes

Driver (all are add-only, no floor lowered): F1 + F4 + F7 are three small guards with
RED pins; F3's validator hole (out-of-span established_around) plus its mis-asserting
test; F2's empty-elements floor in both merge_loss and merge_check; F5's sole-provider
check; F6's one-line health call. Protocol doc: G1/G2 are two short paragraphs; G3 is a
one-clause edit; G4 requires either two small commits or two honest sentences; G5 one
list correction.
