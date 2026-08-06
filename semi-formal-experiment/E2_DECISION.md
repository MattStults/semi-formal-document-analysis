# E2 — how does the S4 gate get switched OFF? A decision document

**The question:** S4 adds a gate to the scorer. Old snapshots were made before the gate
existed and must still rebuild *exactly* as they were. So the rebuild path needs a way to
say "gate off". E2 decides **how that switch is plumbed**.

**Status:** analysis for a ruling. Nothing ruled, nothing implemented. Written 2026-08-05
after `S4_ADVERSARIAL_REVIEW_R2.md` found the design's current answer unbuildable.

---

## 1. The thirty-second version

The design says: add a constructor parameter to the scorer, default on, and pass it
explicitly as *off* when rebuilding an old snapshot. **That cannot work as written** — the
parameter would sit on a class that the rebuild path never constructs directly.

Three ways to fix it. All three are correct if implemented; they differ in how much of the
codebase the change touches and what it does to snapshot identity.

| | what changes | files added to the frozen set | main risk |
|---|---|---|---|
| **(a) thread the parameter** | add it to all three scorer classes and pass it down | `containment.py`, `patient.py` | three signatures to keep in sync; couples S3b |
| **(b) set it after construction** | the rebuild path sets the flag on the built object | none | flag lives outside the class contract |
| **(c) make it a `Weights` field** | rides the existing weights argument | none | **changes every snapshot's recorded config** |

My recommendation is **(a)** — see §5 for why I changed it from the reviewer's (b).

---

## 2. Why this is not cosmetic

Two guarantees depend on it:

1. **Old snapshots must rebuild bit-identically.** Every closed cycle's snapshot is
   reconstructed to check that its recorded scores still reproduce. If the gate silently
   applied to an old snapshot, that check would fail — or worse, quietly report the gated
   score as if it were the historical one.
2. **The manifest must name every file the cycle edits.** The driver freezes a
   `files_to_change` list at OPEN and refuses to close if reality disagrees — but *only*
   for files inside its closure set. `containment.py` is in neither the declared list nor
   the default closure, **so editing it undeclared would pass every gate silently.** The
   cycle would build wrong and still close clean.

That second point is why this can't be deferred to build time: `files_to_change` freezes
at OPEN, before anyone writes code.

---

## 3. Why the design's current answer doesn't work

The rebuild path picks a scorer class based on what the old snapshot recorded. There are
two copies of this ladder — `dossier.py:346–364` and `snapshot.py:181–192` — and both
have the same three rungs:

| snapshot recorded | class built | which snapshots take this rung |
|---|---|---|
| `pricing_version: "2.0"` | `patient.PatientIndex` | `patient-pricing` (the reverted cycle) |
| an overlay | `containment.ContainmentIndex` | **the entire current keep lineage** — `join-integrity-v2`, `patient-backfill`, `decoration-blind-join` |
| neither | `relevance.RelevanceIndex` | the older pre-overlay snapshots |

The design puts the parameter on `RelevanceIndex`. But the baseline S4 actually opens
against — `join-integrity-v2-2026-08-04` — takes the **middle** rung. And the middle rung's
constructor cannot forward it:

```python
# containment.py:452
def from_files(cls, clauses_path=…, annotations_path=None, weights=None, *, edges=()):
    base = relevance.RelevanceIndex.from_files(clauses_path=…, annotations_path=…,
                                               weights=weights)
    return cls(base.clauses, base.annotations, weights, edges=edges)

# containment.py:350
def __init__(self, clauses, annotations=None, weights=None, *, edges=()):
```

No `**kwargs`, no pass-through. `patient.py` (189, 229) is the same shape. A `gate=`
argument on `RelevanceIndex` is simply unreachable through the rungs that matter — so the
rebuild would fall through to the default (gate **on**), which is precisely the failure the
design says it must avoid.

---

## 4. The three options in full

### (a) Thread the parameter through all three classes

Add the parameter to `RelevanceIndex.__init__`/`from_files`, then to
`ContainmentIndex` and `PatientIndex` so each forwards it down. Both dispatch ladders pass
it explicitly on the absent-key rung.

- **Touches:** `relevance.py`, `containment.py`, `patient.py`, `dossier.py`, `snapshot.py`.
- **For:** the switch is a real, declared part of every scorer's interface. Anyone
  constructing a scorer anywhere sees it. It is visible in the manifest diff, which is
  where a reviewer looks.
- **Against:** widens the frozen file set by two scoring modules. Three signatures must
  stay in sync — if S5 or a later cycle adds a fourth rung and forgets, that rung silently
  gets the default. And S3b's `PatientIndex` rung has to carry it too, so the two cycles
  become a little more coupled.

### (b) Set the flag after construction (the reviewer's recommendation)

Leave the constructors alone. In both dispatch ladders, on the absent-key rung, build the
index as today and then set the attribute on the finished object before returning it.

- **Touches:** `dossier.py`, `snapshot.py` — **both already declared**, so the frozen file
  set doesn't change at all.
- **For:** the smallest possible diff, and it works through every rung at once because it
  operates on the built object rather than the constructor chain.
- **Against:** the flag isn't part of any class's declared interface, so a future caller
  who builds a scorer somewhere else gets the default with no signal. There are already
  five such direct constructions in `benchmark.py` (2043, 2863, 3404, 3449, 3683) — all
  diagnostic paths that legitimately want the gate on, so they're fine *today*. It's the
  next one nobody thinks about that's the risk.

### (c) Make the gate a field on `Weights`

`Weights` is the existing bundle of scoring knobs, already threaded through all three
`from_files(..., weights=...)` signatures.

- **Touches:** `relevance.py`, `dossier.py`, `snapshot.py`.
- **For:** propagates everywhere for free, and shows up automatically in
  `diff_snapshots`'s `weights_changed`.
- **Against — and this is disqualifying in my view, two reasons:**
  1. **It perturbs every snapshot.** `snapshot.py:240` records weights by reflecting over
     *every* field of the object. Adding a field adds a key to every snapshot written from
     now on, and `diff_snapshots` compares the union of keys — so **every** old-vs-new
     comparison would report a weights change that isn't one.
  2. **It puts the switch on the swept surface.** `Weights` is the tuning surface, and the
     class docstring already carries a correction disclosing that two of its constants were
     fitted to the panel. S4's single strongest anti-fitting argument is that it introduces
     *no* tunable number. Putting the gate in `Weights` weakens exactly that claim.

---

## 4b. The prior question: is this special-casing, or is there a convention?

There **is** a convention, it is mandatory, and S4 is its fifth instance — so the honest
framing is not "S4 needs a special case" but "the convention's dispatch has outgrown its
implementation."

**The convention (amendment F9, "the PRICING_VERSION pattern").** `cycle.py:622–630`
*refuses to open* any code-shaped cycle whose manifest lacks
`compatibility.version_key` + `compatibility.statement`, with this message:

> "the old behavior must remain reachable via a version recorded in snapshot config
> (the PRICING_VERSION pattern), or the baseline side cannot reconstruct."

That is exactly the design you described: the data carries a version, the reconstruction
reads it, the version selects the configuration. It is enforced by the driver, not by
convention alone.

**Prior instances, all already on disk:**

| version key | recorded in | values seen |
|---|---|---|
| `threshold_rule` | every snapshot | the rule, or the frozen-artifact opt-in |
| `pricing_version` | snapshots from containment-v1.1 onward | absent (legacy), `1.2`, `2.0` |
| `query_patients` | `patient-pricing` | declared patient sets |
| `join_version` | *census* config identity, deliberately **not** snapshot identity (F12) | 1, 2 |
| `section_gate_version` | S4 would add it | absent, `1.0` |

**What has actually outgrown itself.** The version→configuration mapping is a hand-written
`if/elif` ladder, and there are **two copies** of it — `dossier.py:346–364` and
`snapshot.py:181–192` — which have already drifted (the snapshot copy calls
`validate_query.load_query_patients`; the dossier copy reads `query_patients` off the
recorded config). Each new axis multiplies rungs rather than adding one: the pricing axis
has three live rungs today, so a gate axis means every rung needs a gate branch, and the
axis after that doubles it again. The S4 review independently flagged this as **E3** —
"the two-axis obligation is written for a future that has already arrived."

So the pain is real and it is not S4's fault; S4 is just the cycle where the ladder's
growth rate becomes visible.

### (d) Build the general machinery: one config-driven builder

One function — `build_index(config, paths)` — in one module, used by both the snapshot
writer and the dossier reconstructor. Each versioned feature registers three things: its
config key, the documented meaning of *absent*, and how it modifies construction. Adding a
future version becomes a registry entry plus its tests; no ladder edits anywhere, and the
two copies collapse into one.

* **For:** it is the machinery the F9 rule already presumes exists. It removes the
  duplicated ladder and its drift. It makes "absent is a defined dispatch value" — already
  the stated rule — enforced in one place instead of restated per branch. S4 and S3b would
  each add one entry instead of threading through three classes.
* **Against:** it refactors the reconstruction path, which is the most safety-critical code
  in the repo — it is what proves old snapshots still reproduce. And it must not ride
  inside S4: a cycle whose diff contains both a scorer change and a reconstruction refactor
  has two variables, which is what the ceremony exists to prevent.
* **Shape if you want it:** its own cycle, `shape: code`, **predicted flips: 0**, with the
  gate being that all 12 snapshots on disk reconstruct **bit-identically** before and
  after. That is an unusually clean cycle to run — the prediction is exact, mechanical, and
  falsifiable, and a noop is the success condition rather than a disappointment.

**Sequencing choice this creates:**

* *Refactor first* — S4 and S3b each become a one-line registry entry. Costs one cycle of
  delay before S4 opens, and pays back immediately because two consecutive cycles both need
  a new axis.
* *Refactor after* — S4 opens sooner on option (a); the refactor then has one more rung to
  absorb, and S3b still pays the threading cost.

---

## 5. Recommendation — (a), and why I differ from the reviewer

The reviewer recommended (b) on the ground that it is the smallest change and needs no new
declared files. That reasoning is sound and I'd have accepted it, except for what the same
review found one finding earlier.

**E1** was: the design claimed the driver mechanically enforces the revert, and it doesn't —
the enforcement is a *ceremony* obligation on a human signer. The pattern there is a
guarantee that looked mechanical but lived outside the code. **Option (b) is that same
shape**: a switch that is load-bearing for reconstruction correctness, but is not part of
any interface, enforced only by the two call sites remembering to set it.

Option (a) costs two more files in the frozen set and a threading chore. What it buys is
that the switch is *declared* — it appears in three signatures, in the manifest diff, and
in front of anyone who adds a fourth rung later. In a repo whose recurring failure mode is
"the contract was real but nothing enforced it", I'd rather pay two files.

**If you prefer (b)**, the mitigation is cheap and should be pre-registered with it: a test
asserting that reconstructing a pre-gate snapshot through *each* of the three rungs
produces the ungated score bit-for-bit. That converts the convention into something the
suite enforces, which recovers most of (a)'s advantage.

**Either way, reject (c) on the record** for the snapshot-identity reason in §4 — it is the
option that looks cleanest and quietly costs the most.

---

## 6. What this doesn't decide

- Whether the gate defaults on. The design says yes (unconditional once merged) and the
  review confirmed that reading is correctly stated; E2 is only about the off-switch.
- The other two S4 majors, **E1** (correct the "driver-enforced" claim) and **S1** (drop the
  unsound "4 of 30" arithmetic). Both are prose fixes with no options to choose between —
  I can apply them as written once you've ruled here.

---

## Appendix — verification

Every claim above was checked against the tree at `HEAD` (2026-08-05):

- Dispatch ladders: `dossier.py:346–364`, `snapshot.py:181–192`.
- Constructor signatures: `containment.py:350, 452–458`; `patient.py:189, 229`;
  `relevance.py` `RelevanceIndex.__init__`.
- Snapshot weights reflection: `snapshot.py:240–241`, `260`; diff key-union:
  `snapshot.py:451–455`.
- Closure/declaration behaviour: `cycle.py:120–121` (`CLOSURE_DEFAULTS` = three data
  artifacts only), `638–640` (OPEN refuses non-existent declared paths), `830–836`
  (IMPLEMENT refuses a declared file that didn't change).
- Direct scorer constructions outside the ladders: `benchmark.py:2043, 2863, 3404, 3449,
  3683`.
