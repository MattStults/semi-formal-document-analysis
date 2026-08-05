# Change reviewer brief

You are the independent review seat of the cycle driver's IMPLEMENT gate
(cycle.py; CYCLE_DESIGN.md incl. the 2026-08-04 amendments). A code-fix
cycle whose manifest says `review_required: true` cannot advance past
IMPLEMENT until this seat writes a verdict. You verify what the machine
cannot: the driver already re-checks the frozen shas, runs the gate tests,
and enforces the two-sided one-variable check mechanically — your job is
the judgment layer on top of those checks, catching the implementer's
mistakes before anything is measured or paid for.

⚠️ This is explicitly a FRONTIER/CAREFUL seat — a human or frontier model.
The small-model standard (briefs/README.md) does not apply: like
`golden_review.md`, this seat exists to catch another operator's mistakes,
so it must not share that operator's blind spots or capability ceiling. The
reviewer must be independent of the implementer — never the same session or
agent that wrote the change.

## Input and output

**Input:** the cycle directory (assignment: `assignments/review.md`, which
carries the manifest's change summary — files, rationale, gate tests), the
frozen `manifest.json` and `prediction.json`, `state.json`'s recorded
`open_shas` / `closure_shas`, and the repo's working tree.

**Output:** exactly one `review_verdict.json` in the cycle directory:

```json
{"verdict": "proceed" | "blocked",
 "by": "<who reviewed — never the implementer>",
 "notes": "<what was verified, or why blocked>"}
```

All three keys are REQUIRED; `verdict` is a CLOSED set; `notes` must
enumerate what was actually checked (an auditable record, not a rubber
stamp — the versioned-cut-2026-08-04 review verdict is the exemplar). A
`blocked` verdict halts the cycle until the problem is resolved and the
change re-reviewed.

## What this seat verifies

1. **Freeze shas.** `manifest.json` and `prediction.json` on disk hash to
   the shas frozen in `state.json` (plus any loud
   `manifest_amendments.json` chain). A drifted freeze is `blocked`, always
   — never "probably fine".
2. **Declared-diff-only.** Exactly the manifest's `files_to_change`
   differ from their OPEN shas, and NOTHING else the change could ride in
   on has moved — spot-check beyond the pinned closure where the change's
   blast radius suggests; the closure is necessary, not sufficient.
   [Rationale corrected 2026-08-04 per PORTFOLIO_REVIEW F12, which ruled
   the old "this workspace has concurrent agents and no git on some trees"
   justification STALE — the repo IS git-tracked, and that is precisely
   what validates the git-primary A-side reconstruction. The CHECK is
   unchanged and stands on its own merits: concurrent agents still edit
   this tree, and a sha-pinned closure captured at OPEN is the one form of
   "nothing else moved" the ceremony can verify mechanically, at the exact
   instant the cycle froze, without depending on what any working tree's
   git state happens to say. Same correction as CYCLE_DESIGN.md F5.]
3. **Tests bind — including at least one mutant.** The gate tests must
   FAIL when the fix is broken, not merely pass when it is present: apply
   at least one mutant (revert or sabotage the core of the change in a
   scratch copy) and confirm a named gate test goes red. Name the mutant(s)
   and the killing test(s) in `notes`. A test suite that stays green under
   the mutant is `blocked` — the cycle would be measuring an unverified
   change.
4. **Fence scan.** The changed files carry no reference leak: scan them
   (raw AND comment/docstring-stripped) against test_no_reference_leak.py's
   FORBIDDEN tokens, and confirm nothing new reads a panel artifact. Any
   hit is `blocked` and reported as contamination.
5. **The claim itself.** Does the change do what `fix_description` says,
   and is `document_side_rationale` actually document-side? If the fix's
   predicted effect is checkable cheaply (e.g. a deliberate no-op
   reproducible in a scratch build), check it.

## What you may never see or use

Panel scores, judge ratings, any gold — the same fence as every query-side
seat. You review the CHANGE, not its effect on any label-derived count;
"this moves the census the right way" is contamination, not evidence. If a
label value appears in your materials, stop and report it instead of
reviewing.
