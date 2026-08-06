# INDEX_BUILDER_REVIEW — clean-context adversarial code review

**Artifact:** branch `worktree-agent-a4a214c0140729246` (commits `fb38279`, `457a2cb`) on top of
`main` `50a54bd` — `index_builder.py`, `verify_reconstruction.py`,
`reconstruction_baseline.json`, `test_index_builder.py`, and the `dossier.py` / `snapshot.py`
call-site changes.
**Date:** 2026-08-05. No network/API calls. No file in either checkout modified; every probe
ran from the session scratchpad.

## VERDICT: REVISE

**BLOCKING 0 · MAJOR 4 · MINOR 7**

The refactor itself is sound and the noop property was independently confirmed on both
directions — read side and write side — by a route that does not use the author's harness.
**Nothing here says a historical number moved.** What needs revision is the *guarantee
apparatus* around it: two of the three mechanical claims the design makes for this cycle (the
anti-branch guard, and "the gate proves a snapshot still rebuilds") are weaker than stated,
with a reproduction for each; one downstream consumer of the registry was not made
registry-driven; and two documents carry pre-rebase numbers the second commit corrected in
only one place.

---

## 1. What is CORRECT (listed first, deliberately)

**1.1 The read-side noop, re-derived independently.** Not via the author's procedure:
`main`'s `dossier.py`/`snapshot.py` were extracted with `git show`, put ahead of the worktree
on `sys.path`, and the worktree's `verify_reconstruction.py` run against them with cwd still
inside the worktree (so `_git_bytes_matching`'s CWD-relative pathspec still fires). Every
field of every one of the 12 per-tag records: `tags equal: True, diffs 0`. Same replay
statuses, index classes, dispatch digests, refusal texts.

Leg B's digests are genuinely discriminating, not a tautology: the four distinct dispatch
outcomes on disk produce four distinct digests (`db14b596…` RelevanceIndex, `960753…`
ContainmentIndex pre-join, `3f121a…` ContainmentIndex at 1.2, `4ec94e…` PatientIndex), so a
mis-dispatch on any rung moves a digest.

**1.2 Second, independent route.** An 18-cell config matrix (`pricing_version` ∈ {absent, 1.0,
1.1, 1.2, 2.0, 2.0+patients, 2.0+`query_patients: null`, 9.9, whole config `null`} × {overlay,
no overlay}) through `dossier._index_for` in both trees, comparing class, `edges` and
`query_patients`. Every cell identical except the two intended `UnknownVersionError` cells.
This covers equivalences the diff quietly relies on — notably that dropping the old explicit
`edges=()` for a 2.0-without-overlay config is safe (`patient.py:230` defaults it), and that
`config: null`, `query_patients: null` and an absent key all reduce to the same thing.

**1.3 The write-side noop — which the gate does NOT cover, so it was checked separately.**
`verify_reconstruction.py` never calls `snapshot.build_snapshot`; it re-implements the
arithmetic. So the write half is unmeasured by the cycle's own gate. Running `build_snapshot`
on the real artifacts under both trees, on all three rungs plus the unlicensed-declaration
case, hashing the full returned dicts: **all four IDENTICAL**, whole-dict equal `True`.

**1.4 The `query_patients` direction fix — both halves hold.** Write side: with a licensed
declaration both trees record `pricing_version 2.0` + the patients; with an *unlicensed* one
both raise the identical `ValueError` naming the behaviour and the missing anchor. The safety
property is intact, reached through `index_builder._declare_pricing →
validate_query.load_query_patients`. Build side: `validate_query` is imported nowhere at
module scope — only inside `_declare_pricing` — and a test makes both loaders explode and
still builds a 2.0 index. (One narrow gap: MINOR-7.)

**1.5 Absent-key dispatch on every rung**, verified directly rather than via the author's
tests: absent everything → `RelevanceIndex`; absent `pricing_version` with an overlay →
`ContainmentIndex`; `2.0` with `query_patients` absent → `PatientIndex` with `{}`; whole
`config` null → legacy. Never a `KeyError`, never "current". `dossier._resolve_inputs` skips
explicitly-null inputs, so an `overlay: null` snapshot can never put `"overlay"` into `paths`.

**1.6 `UnknownVersionError` is unreachable on disk.** All 12 snapshots dispatch; the only
recorded values are `None`, `"1.1"`, `"1.2"`, `"2.0"`, all claimed by a registered rung. The
covering test re-checks over whatever is on disk rather than pinning a count — the right shape
per the repo's anti-rule. The tightening is a genuine improvement over `main`, which silently
reconstructed an unknown version through whatever the overlay axis had selected.

**1.7 Registrations** — all three in the same diff and correct: `conftest._OPTIONAL`,
`QUERY_MODULES` + a real driver, `MODULE_MAP` §1b/§1c rows. The three-rung driver is not
ceremony: `driven` resets per module, so `assert len({d for d in driven}) == 3` genuinely
asserts three distinct scorer classes were constructed under the spy, and a single-rung drive
would leave `PatientIndex` unbuilt — the "spy watching dead code" failure this repo has
measured twice.

**1.8 Suite** in the worktree venv: **2180 passed, 3 skipped** — exactly as reported.

**1.9 No third reconstruction ladder left behind.** `_index_for` is called only from
`dossier._side` and `verify_reconstruction`; `build_index` only from `dossier._index_for` and
`snapshot.build_snapshot`. No other module builds a scorer from a *recorded config*.

---

## 2. Findings

### MAJOR-1 — The anti-branch test does not catch the case it is written for

`test_emptying_the_registry_reduces_every_config_to_legacy` monkeypatches `FEATURES = ()` and
asserts three fixed configs reduce to `RelevanceIndex`. Its docstring and
`INDEX_BUILDER_DESIGN.md` §2 claim: *"An axis added as an `if` in a build function survives an
empty registry and fails that test."* **That is false for the case that matters** — a future
axis on a **new config key**. The three probe configs never carry the new key, so the new
branch never executes and the guard is silent.

Reproduced: a copy of `index_builder.py` with one hand-written branch keyed on `section_gate`
(the design's own worked example of the next axis), loaded under the name `index_builder` —
**15 passed**, while the branch is demonstrably live (`no key -> RelevanceIndex`,
`new key -> tuple`). So the one mechanical property this refactor exists to buy is not
enforced; the two `FEATURES`-emptying tests prove only that the *existing* two axes are
registry-driven.

**Fix:** an insensitivity check, not a config enumeration. Either (a) assert `build_index` is
invariant under unknown config keys by comparing against a config stripped to the registry's
declared keys — which needs MINOR-4's key declaration to be real — or, more robustly, (b) an
AST/source guard that `build_index`'s body contains no branching and no subscript of `config`
outside the `for feature in FEATURES` loop. (b) is ~8 lines and catches the arbitrary-key case.

### MAJOR-2 — The gate can print BASELINE MATCH while recorded snapshot numbers no longer reproduce

`verify_reconstruction.py`'s docstring: *"every snapshot on disk still rebuilds EXACTLY."*
`MODULE_MAP` §1b: *"strict sha-verified replay compared to the frozen numbers at exact float
equality."* What `_compare` actually compares is `("channels", "raw", "scores")`.
`build_snapshot` also freezes, per behaviour, `threshold`, `threshold_source` and
**`predicted`** (`snapshot.py:216-224`) — and `predicted` is the set every dossier, flip list
and adjudication runs on. None is recomputed or compared. Neither is `vocabulary.df`.

Reproduced: mutating `threshold.apply_rule` to return `0.0` for every input — invalidating the
recorded `threshold` and `predicted` of every snapshot on disk — and re-running the gate still
prints **`BASELINE MATCH: all 12 tags identical … the change is a no-op on every recorded
configuration.`**

Defensible as a scope choice ("this gates the *construction* path"), but it is not what the
docstring, the MODULE_MAP row, or the design say — and this is the artifact a future cycle
will trust when it claims historical results still reproduce.

**Fix, cheapest first:** extend `_recompute` to also recompute `threshold`/`predicted` (the
frozen-cuts path needs `paths["thresholds"]`, which `_resolve_inputs` already returns) and add
them to `_compare`'s field tuple — ~10 lines, and the whole gate runs in **9.9 s**, so cost is
not an argument. If the scope limit is intentional, say so explicitly in both places.

### MAJOR-3 — Two documents still carry the pre-rebase counts

Commit `457a2cb` re-measured leg A from 4/1/7 to **9 exact / 1 mismatch / 2 unreconstructable**
and corrected `verify_reconstruction.py`'s docstring only. Still asserting the superseded
numbers:

* `MODULE_MAP.md:127` — *"4 exact replays, 1 pre-existing mismatch … and 7 snapshots whose
  recorded inputs are unobtainable in a fresh checkout"*
* `INDEX_BUILDER_DESIGN.md` §6 fact 2 — *"Seven snapshots are UNRECONSTRUCTABLE … not
  obtainable from git history or any cycle `pre_change/` copy"* — the second half is now
  affirmatively false for five of them, since the `_git_bytes_matching` fix recovers exactly
  those bytes from git history.

Measured against the checked-in baseline: `Counter({'ok': 9,
'unreconstructable:StaleConfigError': 2, 'mismatch': 1})`. A reader taking MODULE_MAP at face
value will believe the gate covers 4 snapshots when it covers 9, and will mis-diagnose the
first deviation they see.

### MAJOR-4 — The registry is not the source of truth for the *other* consumer of these keys

`snapshot.diff_snapshots` hardcodes the scoring-rule identity keys:

```python
for key in ("pricing_version", "query_patients"):
    if a["config"].get(key) != b["config"].get(key):
        changed.append(key)
```

— with the comment that this was *"made a blocking precondition by the patient-pricing cycle …
must be surfaced in `config.changed`, or the diff is meaningless."* But
`INDEX_BUILDER_DESIGN.md` §5 tells the next author: *"Note what is NOT required: no edit to
`build_index`, none to `dossier._index_for`, none to `snapshot.build_snapshot`."* Following
that literally produces a diff that cannot name its own cause.

Reproduced on two snapshots differing only in a hypothetical future axis key:
`config.changed -> []`. (In a real case `noop` would be `False` because scores moved; the
damaging part is that the diff attributes a scoring-rule change to nothing.)

**Fix:** derive that tuple from the registry, and add "extend the diff identity" to §5's
add-an-axis checklist. Requires MINOR-4 first, because `PRICING` owns **two** config keys
while `VersionedFeature.config_key` holds one string.

### MINOR-1 — `rung_for` swallows every exception from `live_version()`

A genuine `ImportError` (a broken `containment.py`) is reported as *"pricing_version '1.5' …
which no registered rung claims"*, sending the reader to the registry instead of the broken
module. Severity genuinely low: the historical-values loop runs first and covers every value
on disk, and for any overlay config `_apply_overlay` imports `containment` first. **Fix:**
`except ImportError: continue`, which is the comment's stated intent.

### MINOR-2 — The `live_version` fallback defers a reconstruction failure onto frozen snapshots

Because `rung_for` resolves a bumped constant without an edit, a cycle can bump
`containment.PRICING_VERSION` to `"1.3"`, freeze snapshots at 1.3, and never add `"1.3"` to
`CONTAINMENT_RUNG.versions`. Everything works — until the next bump, at which point every 1.3
snapshot refuses. **Fix:** one test — for every rung with a `live_version`, assert
`live_version() in rung.versions` (skip on `ImportError`) — failing red at bump time, in the
cycle that introduces the version.

### MINOR-3 — Nothing runs the gate, and it can never exit 0 on this tree

`verify_reconstruction.py` is referenced only by two documents and its own docstring: no test
invokes it, `cycle.py` does not know it, it is in no CI path. A gate nobody runs rots — and it
takes 9.9 s. Second, because the `containment-v1-pricing` mismatch is pinned, `main()` returns
**2** on a clean tree, so "gate must exit 0" is not wireable as written. **Fix:** a
`test_verify_reconstruction.py` asserting the return is not 1, plus a docstring line saying 2
is the current expected clean-tree exit code.

### MINOR-4 — Most of the registry's declared metadata is inert, and one field is misleading

`config_key`, `absent_means` and `VersionedFeature.name` appear only in `index_builder.py` and
in one test asserting they are non-empty; `PricingRung.means` appears **nowhere** outside its
own definition. So the "declaration" is prose in a dataclass, not a mechanism. Two consequences:

* `OVERLAY.config_key = "inputs.overlay"` is not a config key at all — that axis dispatches on
  `paths`, never on `config`. A future author implementing an axis from the docstring's
  contract will key off `config` and be surprised by the one existing counterexample.
* `PRICING` owns two recorded keys but can declare one, which blocks the MAJOR-4 fix.

**Fix:** make `config_key` a tuple of owned keys, use it (MAJOR-1(a), MAJOR-4), and either
document that `OVERLAY` dispatches on the resolved path or drop the field for that axis.

### MINOR-5 — The gate re-implements the arithmetic it is gating

`_recompute` duplicates `build_snapshot`'s per-behaviour lines rather than calling shared code.
They match today, which is why 9 tags replay. The day `build_snapshot`'s normalization changes,
the gate keeps comparing frozen numbers against the *old* arithmetic and reports "ok" — the
same false-green class as MAJOR-2 by another route. **Fix:** factor the per-behaviour
computation out of `build_snapshot` into one function both call.

### MINOR-6 — Leg A is vacuously "ok" for a snapshot with no recorded behaviours

`_compare` iterates `recorded`; an empty `behaviours` block yields no failures and
`replay: "ok"` with `replay_values_compared: 0`. Latent, not live (every snapshot records
5337 values). **Fix:** refuse or mark `vacuous` when a successful replay compared zero values.

### MINOR-7 — "The build side never reads the live query file" is pinned only against two named functions

The test monkeypatches `validate_query.load_query_patients` and `check_patients`. A build-side
read that opened `behaviours_query.json` directly would pass it — and would also pass the
anti-cheat spy, since that file is correctly in `ALLOWED_ARTIFACTS` for `declare_config`'s
sake. **Fix:** a static assertion that `validate_query`/`behaviours_query` appear only inside
the `declare` path, or spy `open()` around a `build_index` call specifically.

---

## 3. Is the registry the right size?

**For the ceremony charge:** four of the ten dataclass fields are never read by any code path;
the two live fields are `apply` and `declare`, so the registry is really "a list of two
callables per axis" wearing a schema. `_apply_containment_pricing` is a documented `return` —
a rung whose entire behaviour is "do nothing." And 308 lines replace roughly 40 lines of
branches. Had the axis count stopped at two, two clear branches would have been cheaper to read.

**For the abstraction, and this is where the review lands:** the axis count has not stopped at
two — the design names two more incoming cycles, and the ladder was *already* duplicated and
*already* drifted on `query_patients`, which is the concrete harm the repo can point at. The
real win is not the data model; it is that `declare_config` and `build_index` are now the same
object seen from two directions, so the bytes a snapshot freezes and the scorer that produced
them are the same dict by construction. That property cannot drift, and two clear branches do
not give it. The rung table is also the right shape: versions are *facts on disk*, and a tuple
of frozen strings is a better home for a fact than an `elif` chain.

**So: right abstraction, oversized presentation.** The honest trim is to make the declared
metadata load-bearing (MAJOR-1, MAJOR-4, MINOR-4) or delete it. Documentation-as-data that
nothing reads goes stale silently — MAJOR-3 is the same failure mode in Markdown.

**One adjacent observation, not a finding.** `audit_disagreements.py:658-666` still carries an
overlay/no-overlay construction branch with no patient rung. It builds from CLI flags over
current inputs, not from a recorded config, so the docstring's "THE ONE PLACE A SCORER IS BUILT
FROM A RECORDED CONFIG" is literally true. But it is the next place this ladder will drift, and
a future registry axis will not reach it. Worth a line in §5's checklist.

---

## 4. Shortest list that would make this mergeable

1. **`MODULE_MAP.md:127` and `INDEX_BUILDER_DESIGN.md` §6 fact 2** — replace 4/1/7 with 9/1/2
   and drop the "not obtainable from git history" clause for the five recovered snapshots.
   (MAJOR-3)
2. **Make the anti-branch guard real** — an AST/source check that `build_index`'s body has no
   branch and no `config` subscript outside the feature loop; correct the two over-claiming
   docstrings. (MAJOR-1)
3. **Close the gate's blind spot or state it** — recompute and compare `threshold` +
   `predicted`, or write the scope limit into the docstring and the MODULE_MAP row. (MAJOR-2)
4. **Drive `snapshot.diff_snapshots`' identity keys from the registry**, and add "extend the
   diff identity" to the add-an-axis checklist. Requires `config_key` as a tuple. (MAJOR-4,
   MINOR-4)
5. **One test:** `rung.live_version() in rung.versions` for every rung that has one. (MINOR-2)
6. **`except ImportError`** instead of `except Exception` in `rung_for`. (MINOR-1)
7. **A `test_verify_reconstruction.py`** running the gate with `--expect` — 10 s, and it stops
   the gate rotting. (MINOR-3)

Items 5–7 are one-liners; 1–4 are the substance. **Nothing on this list implies a historical
number is wrong:** the reconstruction of all 12 snapshots is unchanged by this branch, verified
three independent ways.
