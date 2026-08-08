# Adversarial review — stage 4's four seats and the R3 derivation layer, 2026-08-08

**Reviewer:** clean-context agent, no stake in this code. **Scope:** `29e018c` and everything after
`b7c663e` touching `seats.py` / `test_seats.py` / `mutate_seats.py`, `readback_r3.py` /
`test_readback_r3.py`, and the R3→seats wiring in `beb8531`.

**REVIEW ONLY.** No repo file outside this one was modified. Every mutation was run against an
isolated copy in a scratchpad, or applied and restored with the restore asserted.
`git diff --stat` at the end: only `semi-formal-experiment/usage.jsonl`, which was already
modified in the working tree before this review began (its added rows are timestamped
2026-08-07 23:18–23:23, file mtime 23:23, i.e. before this session). **No API call was made, no
money was spent, `guard.py --accept` was not run, nothing was pushed.**

Baseline confirmed: `semi-formal-experiment/.venv/bin/python -m pytest walkthrough/ -q` →
**673 passed, 1 xfailed** (40 s). xclingo 2.0b24 and clingo 5.8.0 present.

**Verdict: not clean.** Fourteen confirmed findings, three of them high. The three highs are all
the same shape and all of it is the shape this repo names as its signature failure — *a check that
cannot run, exiting like a check that passed*:

* **§6's divergence machinery cannot fire at all**, and the five tests that pin it construct a
  state `validate_judgements` refuses;
* **the R3→seats wiring is a no-op against the real `readback_r3` type**, and the failure direction
  is the silent one — the state that reads as "R3 accounted for" is exactly the state where R3 was
  dropped;
* **`mutate_seats.py`, the instrument that certifies everything else, reports `0 survivors` with a
  RED test suite.** The documented pyc trap *is* fixed; a larger hole of the same class was left
  behind it.

Prior-pass findings were re-checked; the two that were re-tested and hold are listed in §D. The
prior `SPEC_DRIFT_REVIEW` findings **A2** and **A5** are still live and stage 4 now inherits or
works around them — see F11 and §D.

---

## A. CONFIRMED, ranked by how badly a wrong answer would mislead

### F1 · HIGH — `divergences()` can never fire. §6 is dead code, and every test that pins it feeds a state the system refuses

`seats.py:100-116` (`VERDICTS`, `CONTRADICTIONS`), `seats.py:969-1009` (`divergences`).

Each seat's closed verdict set is **disjoint** from every other's. Every pair in `CONTRADICTIONS`
has **both** members inside **one** seat's vocabulary. `divergences` groups by item **across
seats**, one judgement per seat per item (`validate_judgements` refuses a duplicate), and
`judge` → `validate_judgements` enforces `j.verdict in VERDICTS[seat]`. So the two members of a
contradiction pair can never both appear in `vals`.

```
$ cd walkthrough/paper_pipeline/phase_1
$ ../../../semi-formal-experiment/.venv/bin/python -c "
import sys, itertools; sys.path.insert(0,'.'); import seats
hits=total=0
for combo in itertools.product(*[seats.VERDICTS[s] for s in seats.SEATS]):
    js={s:(seats.Judgement(s,'x',v,'r'),) for s,v in zip(seats.SEATS,combo)}
    _r,d = seats.divergences(js,{s:'sha' for s in seats.SEATS},'r')
    total+=1; hits+=bool(d)
print(hits,'divergence records over',total,'legal combinations')"
0 divergence records over 81 legal combinations
```

Pairwise overlap of the verdict sets, minus `unclear`: **DISJOINT for all six pairs**. Contradiction
owners: `{faithful,unfaithful}→['4b']`, `{licensed,unlicensed}→['4c']`,
`{covered,not-conveyed}→['4d']`, `{as-meant,not-as-meant}→['4a']`.

**Why the tests do not see it.** `test_seats.py:776`, `:789`, `:800`, `:806`, `:1135` all build
judgements like `Judgement("4d", "asserts[0]", "unfaithful", …)` and
`Judgement("4c", "x", "unfaithful", …)`. `unfaithful` is not in `VERDICTS["4d"]` or
`VERDICTS["4c"]`; `validate_judgements` raises `NotAdjudicated` on it. So §6 is tested only in a
state no seat can legally produce.

**Everything downstream is therefore unreachable in production:** `seat-divergence` stamps, the
`unclear` resolution, the brief-sha/rendering-sha record, `promote`, `Triage`, and
`report_line`'s *"N seat-divergence(s), NOT ADJUDICATED until triaged"* branch. §6's headline is
*"Divergence — enforced, not stated"*; as built it is neither.

⭐ **This may be a DESIGN question, not only a code one, and that is why it ranks first.**
`03_pipeline.md` §6's divergence is between two judgements of *the same question*. Four seats asking
four different questions cannot contradict each other by construction — 4b saying `faithful` and 4d
saying `not-conveyed` about one item is not a contradiction and correctly is not treated as one.
The design owes an answer to *"which two judgements are supposed to be able to diverge?"*. The two
candidates visible from the code are (a) the same seat run at two model tiers — which §7's
small-model parity run needs anyway, and which `divergences` would actually support if keyed
`"4b@flash"` / `"4b@frontier"` — and (b) nothing, in which case §6 should say so and the machinery
should be deleted rather than left passing.

Confidence: **high** (proved by exhaustion).

---

### F2 · HIGH — the R3→seats wiring is a no-op against the real `readback_r3.ModuleR3`, and it fails in the silent direction

`seats.py:464-489` (`denominator_4a`), `:492-512` (`denominator_4b`), `:1283-1317`
(`plan_clause`). Commit `beb8531`.

`denominator_4a` reads `getattr(r3, "derivations", ())` and, per element, `d.item` and
`d.nodes`. **`readback_r3.ModuleR3` has none of that.** Its fields are
`(clause_id, program, situations, findings, outcome, covering, with_derivation)`; derivations hang
off `ModuleR3.situations[i].derivations`, and `readback_r3.Derivation` is
`(label, verdict, roots)` — no `item`, no `nodes`.

```
$ ../../../semi-formal-experiment/.venv/bin/python -c "
import sys; sys.path.insert(0,'.')
import fixtures, schema, readback, readback_r3 as r3mod, probe, seats
mod = schema.validate(fixtures.political_module())
S = probe.Situation('S3',3,frozenset(['political_content(x)','broad_audience(x)']),
                    frozenset(['asserts(m0217,permit,produce(x))']))
out = r3mod.render_r3(mod,[S]); rb = readback.render_module(mod)
print('R3:', out.outcome, out.with_derivation, 'of', out.covering)
print('with a real ModuleR3 :', seats.denominator_4a(rb,out).ids, seats.denominator_4a(rb,out).excluded)
print('with r3=None         :', seats.denominator_4a(rb).ids)"
R3: rendered 1 of 1
with a real ModuleR3 : ('concepts[0]','concepts[1]','asserts[0]') None
with r3=None         : ('concepts[0]','concepts[1]','asserts[0]')
```

A module that **has** a rendered derivation produces a 4a denominator **identical** to the
`r3=None` one — and with `excluded=None`, i.e. **without even the `r3-not-supplied` marker**. The
docstring's guarantee (*"so 'R3 was not supplied' can never read as 'this module has no
derivations'"*) is inverted: the only state that carries a marker is the one where R3 was honestly
absent, and the state where R3 was supplied and silently dropped carries nothing at all.

Three further consequences, each independently reproducible:

1. **`excluded=None` breaks the very membership test the tests perform.**
   `denominator_4a(rb, r3_with_all_derived).excluded` is `None`, so
   `"r3-not-supplied" in d.excluded` → `TypeError: argument of type 'NoneType' is not iterable`.
   `Denominator.excluded` has `default_factory=dict`, which an explicit `None` bypasses
   (`seats.py:489`).
2. **`plan_clause` has no `r3` parameter** (`seats.py:1283`) and calls
   `denominator_4a(rb)` / `denominator_4b(rb, mod)` at `:1291-1292`. There is no path by which a
   derivation reaches a seat prompt. And if one were added, `:1301` and `:1309`
   (`text_by_item[i] for i in d4a.ids`) would `KeyError`: `text_by_item` is built from
   `rb.renderings` only, so a derivation id has no seat-facing text anywhere. **R3 has no defined
   rendering for a seat at all** — `Derivation.verdict` is a raw ASP atom.
3. **`excluded` never reaches the report.** `build_report` (`seats.py:1165`) writes
   `{s: list(getattr(dn, "judgeable", dn.ids))}` and drops `excluded` entirely. Even when the
   marker *is* set, nothing a human reads carries it.

**Why the tests miss all of it:** `test_seats.py:1428-1433` defines `_D`/`_R3` duck types that
match `denominator_4a`'s `getattr` contract exactly. **No code in the repository builds an object
of that shape.** The three tests at `:1436`, `:1448`, `:1459` — including the one explicitly named
*"the vacuous-pass shape"* — are pinned entirely against a fixture invented to fit the accessor.
This is the same defect class the commit message claims to have closed.

Confidence: **high** (ran it).

---

### F3 · HIGH — `mutate_seats.py` reports `83 mutants applied, 0 survivor(s)` against a RED test suite

`mutate_seats.py:279-314`. The kill rule is `killed = r.returncode != 0` and **nothing else**.
There is no baseline run, no return-code triage, and no collected-count comparison.

Verified in an isolated copy of `walkthrough/`, with one always-failing test appended to
`test_seats.py`:

```
$ PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest test_seats.py -x -q
1 failed, 137 passed in 0.48s
$ SEATS_PY=.venv/bin/python .venv/bin/python mutate_seats.py | tail -2
83 mutants applied, 0 survivor(s)          # and exit 0
```

Every guard "pinned", a clean sweep, exit 0 — and not one mutation was actually discriminated.
Same copy, a mutant that breaks the import (`SEATS = (((((`):

```
$ pytest test_seats.py -x -q  ->  returncode 2   # collection error
   mutate_seats.py:301  killed = (returncode != 0)   =>  reported KILLED
```

`mutate_schema.py`, the sibling in the same directory, guards **all three** of these explicitly and
says so in its own docstring: *"the baseline must be green through the SAME isolation path before
any mutation runs"*, *"a mutation … whose run does not collect the same number of tests as the
baseline is reported as ERROR — a third status, never folded into 'no tests died'"*, and
`run.returncode in (2,3,4,5) or run.total != baseline_n` → `error` (`mutate_schema.py:415-435`).
`mutate_seats.py` has only `killed`/`survivor`/`unapplied`; there is no `error` status at all.

**The documented pyc trap itself IS fixed and I verified it.** `shutil.rmtree(__pycache__)` plus
`PYTHONDONTWRITEBYTECODE=1` (`:295-296`) removes the (mtime-seconds, size) invalidation window
entirely — no `.pyc` is written, so the second-mutant-in-the-same-second case cannot arise. The
finding is that the file fixed the narrow instance and left the general shape — which is
`DEBUGGING_TIPS.md` §8a's own instruction (*"sweep for the shape, do not fix the instance"*)
applied to the file that quotes §8.

Two smaller notes on the same instrument:

* `-x` stops at the first failure, so a mutant killed by an unrelated flake is indistinguishable
  from a mutant killed by its named guard. `mutate_schema.py` records **which** tests died and
  reports entanglement; `mutate_seats.py` records nothing.
* It runs `test_seats.py` only. **`readback_r3.py` has no committed mutation harness of any kind**
  (`ls mutate*` → `mutate_schema.py`, `mutate_seats.py`). `21813f2`'s claimed *"mutation sweep
  21/21 killed, 0 survivors"* is not reproducible by anyone but its author, and §8's bar
  (*"stage 4 ships with its own mutation run at 0 survivors or it does not ship"*) is met for the
  seats and unmet for R3.

Reproduced the shipped sweep as-is on the real tree first: **83 mutants applied, 0 survivor(s)**,
restore verified. The result is real; the instrument that produced it cannot tell that result from
a broken suite.

Confidence: **high** (ran both experiments).

---

### F4 · MEDIUM-HIGH — the stage-3 discrimination cross-check has no join-key guard: a mismatched key makes every `covered` `unsupported` while the report says the number was available

`seats.py:890-926` (`cross_check_4d`), `:1187` (`stage3_discrimination_available`),
`:1215-1217` (`report_line`).

4d's denominator ids are the module's **claim sentences** (`denominator_4d` → `mod.claims`).
Stage 3 computes discrimination **per claim id** (`C1`, `C2`, `C3` — `STEP_stage3.md` §6,
`STEP_stage4.md` §3b). Nothing checks that the two key spaces meet.

```
$ ../../../semi-formal-experiment/.venv/bin/python -c "
import sys; sys.path.insert(0,'.')
import fixtures, schema, readback, seats
mod=schema.validate(fixtures.political_module()); d4d=seats.denominator_4d(mod)
print('4d id:', d4d.ids[0])
js=[seats.Judgement('4d',c,'covered','r') for c in d4d.ids]
out,f = seats.cross_check_4d(js, {'C1':3,'C2':0,'C3':0})
print('verdict',out[0].verdict,'evidential',out[0].evidential,'stamps',out[0].stamps,'inert',len(f))
rb=readback.render_module(mod)
dn={'4a':seats.denominator_4a(rb),'4b':seats.denominator_4b(rb,mod),
    '4c':seats.denominator_4c(mod),'4d':d4d}
rep=seats.build_report('m0217',rb,{'4d':out},dn,discrimination={'C1':3,'C2':0,'C3':0})
print('available:',rep['stage3_discrimination_available'],
      '| line warns:', 'UNAVAILABLE' in seats.report_line(rep))"
4d id: C1 political content for a broad audience is allowed
verdict covered evidential False stamps ('unsupported',) inert 0
available: True | line warns: False
```

Stage 3 ran, the numbers were supplied, **zero** of them were consulted, and the report asserts
`stage3_discrimination_available: True` with no warning on the line a human reads. §4.3(3) calls
this cross-check *"the only place a seat verdict is confirmed by something outside the seat
system"*; §3b requires *"where it is unavailable, the verdict says so"* — the *verdict* says so,
the *report* says the opposite, and nothing counts the misses.

The discipline exists one function above: `denominator_4d` (`seats.py:559-564`) **refuses** a
`forbid_body_claims` name that matches nothing, on precisely this ground — *"a name that matches
nothing excludes nothing while looking like it did"*. `cross_check_4d` needed the same guard and
does not have it.

Confidence: **high** (ran it).

---

### F5 · MEDIUM-HIGH — `report_line` is NOT byte-identical under a flipped 4a verdict; the pooled `unclear` rate it prints is computed over 4a

`seats.py:1154` (`pooled = [j for s, js in judgements.items() for j in js]`), `:1213`
(`report_line` prints `render_unclear_rate(d["unclear_rate"]["pooled"])`).

```
4a = as-meant : … 4d=[3 covered]/3   ·   unclear-rate: 0/12 = 0.000   ·   layer 1: 0.00 …
4a = unclear  : … 4d=[3 covered]/3   ·   unclear-rate: 3/12 = 0.250   ·   layer 1: 0.00 …
BYTE-IDENTICAL? False
```

(Same module, same renderings, same 4b/4c/4d verdicts; only 4a's answers changed.)

`report_line`'s docstring — *"⛔ It does not read `advisory`"* — is literally true and
operationally false: it does not read the *key*, but it prints a number derived from it. §4.3(2)
requires 4a's verdict to sit *"in a separate `advisory` block that the pass/fail line does not
read"*. The advisory seat moves the one line a human reads.

Substantively worse than cosmetic: §5.4 makes the `unclear` rate evidence about the **brief or the
artifact**. Pooling the author's self-grading seat into it means a defensive or an unusually candid
4a shifts the run-level diagnostic that is supposed to be about the other three.

**Unpinned in both directions.** My hand-written mutant S1 — changing `pooled` to exclude `4a`,
i.e. to the design's own rule — **SURVIVED all 137 tests**.

Confidence: **high** (ran it).

---

### F6 · MEDIUM-HIGH — 4c is anchored against `readback.py`, not against a rendering bug: `_item_text` is a second, unchecked renderer, and dropping a rule body from it survives the whole suite

`seats.py:607-623` (`_item_text`), reached from `source_items` → `build_4c_prompt`.

§4.1's answer to shared reason A is *"one seat is not downstream of it… if 4r is systematically
wrong — a mis-substituted gloss, a dropped condition, a flipped polarity — 4a, 4b and 4d can all be
wrong together and **4c is unaffected**"*. True of `readback.py`. But 4c's material is composed by
`_item_text`, which is itself a renderer — and it has **no RB1–RB5 equivalent, no polarity count,
no gloss-presence check, and no mutation coverage**.

Hand-written mutant S7, run against an isolated copy:

```
_item_text, kind == "asserts":
-   base = f"clause {clause_id} {item.status}s the act {item.act}"
-   return base + (f", when {item.body}" if item.body else "")
+   return f"clause {clause_id} {item.status}s the act {item.act}"

SURVIVED   137 passed in 0.43s
```

Under that mutant 4c is asked *"does the clause license `clause m0217 permits the act
produce(M)`?"* with every condition deleted — a strictly weaker, more-licensable claim that the
clause **does** support. That is RB2's named failure (*"a dropped condition renders as a weaker,
TRUE sentence"*) occurring in the one seat RB1–RB5 structurally cannot see, because RB1–RB5 run
over renderings and 4c does not read renderings.

⇒ The anchor property should be restated honestly: 4c is anchored against `readback.py`'s
composition, **not** against a rendering bug in general. Either `_item_text` gets its own
deterministic checks, or §4.1 stops claiming 4c survives *"a dropped condition"*.

Confidence: **high** (ran the mutant).

---

### F7 · MEDIUM — `refuse_aggregate` scans top-level key NAMES only; a nested consensus field, and a key whose VALUE says "4/4 agreed", both pass

`seats.py:1097-1121`, `probe.refuse_pass_rate` (same shape: `for k in mapping`).

```
ACCEPTED: {'summary': {'consensus': '4/4 agreed', 'n_passed': 4}}
ACCEPTED: {'verdict_rollup': ['4/4 seats agree the translation is faithful']}
ACCEPTED: {'overall': 'ALL FOUR SEATS AGREE'}
refused : seat_agreement_score
```

(via `build_report(..., extra=…)`, which `d.update`s into the report and then validates.)

§4.3(1) is *"there is nowhere to write '4/4 agreed'"* and §6's test 20 sets the standard for this
family — *"the route must not exist, not merely be discouraged"*. As built, the route exists one
nesting level down. Two lines fix it (recurse into `dict`/`list` values; scan stringified values as
well as keys), and the refusal message is already good.

Confidence: **high** (ran it).

---

### F8 · MEDIUM — RB4's `non-evidential` stamp cannot fire on this corpus, and nothing says so. §4.2's whole structural answer is inert

`readback.py:70` `ECHO_LEVEL = 0.90`; `seats.readback_stamps` (`seats.py:860`) reads
`rb.non_evidential`.

```
$ ../../../semi-formal-experiment/.venv/bin/python -c "
import sys; sys.path.insert(0,'.'); import seats
rows, planned = seats.survey()
e=[r['echo'] for r in planned if r['echo'] is not None]
print(sorted(round(x,2) for x in e), 'max', round(max(e),2), 'any >= 0.90?', any(x>=0.9 for x in e))"
[0.37, 0.55, 0.58, 0.62, 0.63, 0.73, 0.74] max 0.74 any >= 0.90? False
```

Every clause that reaches a seat scores **well below** the declared level, so **not one verdict in
the corpus is stamped `non-evidential`**. §4.2's answer to shared reason B (*"the rendering echoes
the clause"*) therefore never fires, while §0(5) measures the glosses that cause it at 71–100 %
verbatim.

⭐ **This is also a design-vs-code drift, in the direction the brief asks to be flagged.**
`STEP_stage4.md` §3a — the design's own **PASSING worked example** — states that patched `m0217`
*"reports 0.88 mean echo — high, verdict stamped `non-evidential`"*. At the shipped
`ECHO_LEVEL = 0.90` it would **not** be stamped. Either the constant or §3a is wrong, and §3a is
the document a reader uses to understand what the stamp is for.

The honest minimum is `DEBUGGING_TIPS` §2's rule applied to the stamp itself: print how many
clauses were **at or above** the level beside the count of clauses measured, so *"nothing echoed"*
is distinguishable from *"the level is above everything we can produce."*

Confidence: **high** (ran it).

---

### F9 · MEDIUM — the third Invariant-1 escape of the shape the build already fixed twice: `%!` in a model-authored gloss is silently rewritten by xclingo's own preprocessor, and `TRACE_SAFE` does not cover it

`readback_r3.py:88` (`TRACE_SAFE = {'"', '\\', '{', '}', '\n', '\r'}`), `:111-129`
(`trace_safe`, `_annotation`).

The build reports two live escapes it fixed (`o` leaking as a leaf; two xclingo labels joined by
`;` read as one string). Here is a third, and it is silent — **no `readback-r3-trace-unsafe` note
fires**:

```
$ ../../../semi-formal-experiment/.venv/bin/python -c "
import sys; sys.path.insert(0,'.')
import fixtures, schema, readback_r3 as r3, probe
mod=schema.validate(fixtures.political_module())
S=probe.Situation('S3',3,frozenset(['political_content(x)','broad_audience(x)']),
                  frozenset(['asserts(m0217,permit,produce(x))']))
out=r3.render_r3(mod,[S],gloss={'political_content':'content about politics %!x here'})
print('trace_safe flagged:', r3.trace_safe('content about politics %!x here')[1])
print('findings:', [f.check_id for f in out.findings])
for n in out.nodes: print('  ', n.text)"
trace_safe flagged: ()
findings: ['readback-act-literal']
   clause m0217 permits ⟨act produce(M)⟩ when «content about politics &x here» and «…»
   «content about politics %!x here»
   «content crafted for an unspecified or broad audience»
```

xclingo turns `%!` into `&` when it lifts the annotation dialect into theory atoms, and it does so
**inside the quoted literal**. Result: the **rule node** a seat reads says `«… &x here»` while the
**leaf node** for the same concept says `«… %!x here»` — two different sentences for one
definition, in one tree, with nothing recorded. `TRACE_SAFE` covers every character that would
break the literal and misses the one character the dialect is built on.

The gloss is **model-authored** and `schema._BAD_IN_TEXT` fences `read_back` and nothing else —
`readback_r3.py:85-87` says so itself. The `readback-r3-trace-unsafe` note exists for exactly
this class and does not fire.

⚠️ **Stated so it is not overread: this is text corruption, not injection.** I tried
`%!show_trace {broad_audience(M)}` in a gloss; the rewrite stays inside the string literal and does
not become a directive, so the program's semantics are unaffected.

Confidence: **high** (ran it).

---

### F10 · MEDIUM — five more surviving hand-written mutants, in the areas the two sweeps cover least

Run against an isolated copy of `walkthrough/`; each restored and the restore asserted.
20 hand-written mutants, **14 killed, 6 survived** (S1 and S7 are F5 and F6 above).

| mutant | file | result |
|---|---|---|
| **S2** `LICENSED_KINDS` drops `"defines"` | `seats.py:417` | **SURVIVED 137** |
| **S3** `source_items` ignores `judgeable_only` (returns `denominator.ids`) | `seats.py:628` | **SURVIVED 137** |
| **S5** `rendering_sha` returns the sha of `""` | `seats.py:401` | **SURVIVED 137** |
| **S6** `unclear_split`'s length bucket is a constant `'<=80'` | `seats.py:1077` | **SURVIVED 137** |
| **R10** `layer1_fraction` returns `0.0` instead of `None` when there are no nodes | `readback_r3.py:552` | **SURVIVED 36** |
| **R11** `module_program` stops annotating `defines` | `readback_r3.py:167` | **SURVIVED 36** |

Why each matters:

* **S2** — §5.1's 4c denominator is *every licensed item*. The `concepts` exclusion has an explicit
  `raise` and a test (row 16); the other four kinds have neither, so the denominator can be shrunk
  silently through the constant. `m0053`'s only content item is a `defines`.
* **S3** — §5.2 routes `world` items away from 4c. That is pinned at `build_4c_prompt` (the shipped
  mutant `4c-admits-a-world-item` dies) using hand-built `SourceItem`s, but the composition
  `source_items → build_4c_prompt` on a module that actually **has** a `world` item is exercised by
  nothing. `check_world_items` is pinned (my S4 died), so a `world` fixture exists — it just never
  reaches this seam.
* **S5** — §6(2) requires a divergence record to carry *"the sha of each seat's brief **and of the
  rendering**"*, so *"under-informative dossier"* is checkable against the artifact. `brief_sha` is
  pinned (`brief-sha-is-not-per-seat` dies); `rendering_sha` is not, and a constant one makes the
  record unable to distinguish two renderings. (Moot while F1 stands, and it will stop being moot
  the moment F1 is fixed.)
* **S6** — §9's mitigation is the split *by length*: *"a rate that rises with length is a renderer
  finding"*. The shipped mutant `unclear-rate-is-not-split-by-length` sets `lb = None` and dies; a
  **constant** bucket survives. The test pins that a key exists, not that the bucketing
  discriminates — so the measurement §9 rests on is unpinned as a measurement.
* **R10** — `report()` prints `not-measured (no derivation)` from `frac is None`. Under the mutant
  it prints `0.00 of 0`. That is `DEBUGGING_TIPS` §2 verbatim — a rate reading 0.0000 when it
  measured nothing — in the field §2.3 requires *"printed even when zero"*.
* **R11** — `module_program`'s own docstring: *"`defines` and `ontology` are annotated too… an
  unannotated rule is INVISIBLE to xclingo, so leaving them bare would silently flatten a
  derivation… a shorter tree that reads like a simpler explanation."* The **`ontology`** half is
  pinned (`test_an_ontology_step_becomes_an_INTERIOR_node_with_its_own_sentence`). The **`defines`**
  half is not — no fixture puts a `defines` inside a derivation. `DEBUGGING_TIPS` §8 again: *"when a
  guard is deliberately redundant, each arm needs its own RED test."*

The other 14 hand mutants died, several 1:1 — the R3 block-on-empty machinery is genuinely well
pinned (see §D).

Confidence: **high** (ran them).

---

### F11 · MEDIUM-LOW — `structural_finding` is used by no production path; the disclosable half of §5.5 is proven only against a synthetic object, and prior finding A5 is still open with a second fence now beside it

`seats.py:154-159`, `:175-223`. `grep -rn structural_finding *.py` → defined in `seats.py`,
**called only from `test_seats.py`** (`:582`, `:603`, `:636`, `:649`).

Every read-back finding the pipeline actually produces is a `readback.Finding`
`(check_id, severity, item, message)` with **no `origin`** — RB1–RB5, `readback-ungloss`,
`readback-act-literal`, and all of `readback_r3`'s. Nothing converts them:

```
$ ../../../semi-formal-experiment/.venv/bin/python -c "
import sys; sys.path.insert(0,'.')
import fixtures, schema, readback, seats
rb = readback.render_module(schema.validate(fixtures.module()))
print(rb.outcome, [(f.check_id,f.severity) for f in rb.findings])
try: seats.route(rb.findings)
except Exception as e: print('route  ->', type(e).__name__, e)
try: seats.append_findings_to_transcript([], rb.findings)
except Exception as e: print('append ->', type(e).__name__, e)"
readback-ungloss [('readback-act-literal','note'), ('readback-ungloss','error'), ('RB1-label-survives','error'), …]
route  -> AttributeError 'Finding' object has no attribute 'origin'
append -> AttributeError 'Finding' object has no attribute 'origin'
```

So §8's test-14 **positive** half (*"a `readback-structural` finding ⇒ rendered in full"*) is
satisfied by an object the system never builds, and the repair route §5.5 grants to
`readback-structural` does not exist. A crash is the safe direction, but it is not the designed one.

**Prior `SPEC_DRIFT_REVIEW` A5 is unfixed**: `translate.DISCLOSABLE_ORIGINS` is still
`('schema','link','probe-structural')`. This build **documented** the gap
(`seats.py:143-153`) rather than closing it and stood up a second constant plus a second renderer
(`seats.DISCLOSABLE_ORIGINS`, `render_findings_log`). The comment argues the copy cannot drift
because a test pins agreement on a stage-2 finding; that pins the *shared* rows, not the divergent
one. `CLAUDE.md`'s rule is *"registration, not documentation, fences a module"*, and the file's own
`_MODULE_PATTERNS` comment says *"the one that drifts is always the copy."*

⚠️ **And the extension inherits a live hole.** `seats.DISCLOSABLE_ORIGINS` is built from
`translate.DISCLOSABLE_ORIGINS`, which still contains `probe-structural` — prior finding **A2**,
re-verified today as still live: `probe.impossible_findings` emits a **seat label** wearing a
`probe-structural` badge, disclosable, naming the situation and its ground atoms. Stage 4 now widens
that perimeter by inheritance rather than narrowing it.

Confidence: **high** (ran it).

---

### F12 · MEDIUM-LOW — the frontier price is a hard-coded literal, and it is below the most expensive entry in the repo's own price table

`seats.py:1396` `frontier=(5.0, 30.0)`. `STEP_stage4.md` §7: *"Frontier-tier seats are priced from
`providers.json` at run time"*. Nothing in `seats.py` reads `providers.json`.

```
sol   gpt-5.6-sol      [5.0, 30.0]
fable claude-fable-5   [10.0, 50.0]   <- the maximum, 2.0x input / 1.67x output
```

`estimate_clause_usd` refuses an **unpriced** provider on the ground that *"an unpriced call counts
as OVER budget, never as free"* (`seats.py:1373-1376`) — correct, and then it silently uses a
below-maximum price for a priced one. On `fable` the printed worst case moves from $0.5112 to
roughly $0.87 per clause.

Confidence: **high** (ran it; read `providers.json`).

---

### F13 · MEDIUM-LOW — ⭐ CODE RIGHT, DESIGN STALE: `--cost` falsifies §7's corpus-scale numbers by an order of magnitude, and §7 is what a budget decision would be read from

I re-derived the arithmetic independently and it is **correct**:

```
in_tok = in_chars / 4.0 ; out_tok = 4096 * 4 = 16384
usd    = in_tok/1e6 * p_in + 16384/1e6 * p_out
m0014 (18 items, 6357 in-tok), flash:    6357e-6*0.14 + 16384e-6*0.28 = $0.005478  -> printed 0.0055 ✓
m0014, frontier(5,30):                   0.031785 + 0.49152          = $0.523305  -> printed 0.5233 ✓
```

Measured over the 7 stored clauses that reach a seat: **$0.0051/clause worst flash,
$0.5112/clause worst frontier, $0.0568/clause "likely" frontier.**

`STEP_stage4.md` §7 states: four-clause frontier run **$0.10–$0.20**; 593 clauses **~$0.7 flash,
~$25 frontier — "over the ceiling"**. Against the measured numbers:

| | §7 says | measured by `seats.py --cost` |
|---|---|---|
| 4 clauses, frontier, worst | $0.10–$0.20 | **$2.04** |
| 593 clauses, flash, worst | ~$0.7 | **$3.02** |
| 593 clauses, frontier, worst | ~$25 | **$303** |
| 593 clauses, frontier, "likely" | — | **$33.7** |

Even the *likely* frontier corpus run is **4× the entire $8.50 cap**, and the worst case is 35×.
§7's *"~$25 — over the ceiling"* understates by an order of magnitude, and §7 quotes the
**optimistic** number as the estimate while the tool's own header says *"WORST is the number a
budget decision uses"*. The code is right and honest; **§7 should be restated from the measurement
it now has**, and the four-clause line should say $2.04, not $0.10–$0.20.

One declared omission, recorded so it is not read as a defect: `estimate_clause_usd` prices no
re-translation, while §7's per-clause figure includes *"at most one re-translation… ($0.001085 for
m0217)"*. `render_survey` says so in its footer. The survey total is therefore **not** §7's total,
and the two should not be compared without adding the stage-1 term.

Confidence: **high** (re-derived and re-ran).

---

### F14 · LOW-MEDIUM — the 4b/4d module fence catches JSON with double quotes and misses the same module one quote-character away

`seats.py:266-274`. The added pattern requires `"key"\s*:`.

```
REACHES 4b : {'clause_id': 'm0217', 'asserts': [{'status': 'permit', 'act': 'produce(M)',
                                                 'body': 'political_content(M)'}]}     # python repr
REACHES 4b : clause_id: m0217\nasserts:\n  - status: permit\n    body: …               # YAML
REACHES 4b : the rule fires on political_content and broad_audience and not exploits_individual
refused    : asserts (m0217, permit, produce(M)).
refused    : {"clause_id" : "m0217"}
```

The pattern was added as *"ONE ADDITION, and it is a real hole in the stage-3 list"* — the hole is
re-opened by `repr()`, `yaml.dump`, or any prose paraphrase of the body. Not live today
(`plan_clause` uses `json.dumps` and 4b is not shown the module at all), which is why this is LOW-
MEDIUM rather than higher; but `build_4b_prompt` is a public fence and the shipped mutant
(`module-fence-loses-the-json-pattern`) pins only the double-quoted form.

Confidence: **high** (ran it).

---

## B. SUSPECTED — real, but I could not close them from the artifacts alone

* **S-a — `_freeze` keeps only the first bare term.** `readback_r3.py:437`,
  `atom=bare[0] if bare else ""`. A node carrying two auto-traced atoms loses one from the leaf
  rendering silently — the same *drop* shape as the `;` defect the build fixed, one field over. I
  could not produce a live two-bare-atom node, so SUSPECTED.
* **S-b — the layer lookup misses on any multi-label rule node.** `_gloss_tree` keys
  `layers.get(node.text, 1)` on the trace-safe sentence, but `_freeze` sets
  `text = " / ".join(said)` when a node carries **two** quoted labels. The lookup then misses and
  the node defaults to **layer 1**, inflating `layer1_fraction`. Conservative direction, but
  unpinned, and the fraction is a required reported number.
* **S-c — `gloss_leaf` silently drops nested-function arguments.** `_CONST` is
  `^([a-z][A-Za-z0-9_]*|\d+)$`, so `harm_category(f(terrorism))` renders with **no**
  `(concerning: …)` at all. `test_a_LEAFS_CONSTANT_survives_into_its_rendering` pins the flat case
  and says why it matters (*"it drops which harm the derivation rested on"*); the nested case drops
  it and stays silent.
* **S-d — `ASP_MARK` inside a gloss survives into node text.** A gloss containing `[ASP:` renders
  as `«content [ASP: hi ]»`. Prior finding **A4** established that `readback.echo_score` strips
  `⟦ASP: … ⟧` content out of its denominator; a gloss can therefore hide itself from RB4. A4 said
  the layer-1 blind spot was latent because layer-1 count is 0; this is a second, gloss-reachable
  route to the same place. `readback.marker_safe` neutralises `«»` (verified — prior F5's fix
  **holds**) but not the ASP markers.
* **S-e — ⭐ §8's registration requirement names machinery that does not exist here.** §8's closing
  note requires the new module to register in *"`test_no_reference_leak.QUERY_MODULES`-equivalent
  fencing and `conftest._OPTIONAL` for its tests"*. Both live in `semi-formal-experiment/`;
  `walkthrough/paper_pipeline/phase_1/conftest.py` has no `_OPTIONAL` and there is no
  `test_no_reference_leak` anywhere under `walkthrough/`. So the requirement is unfulfillable as
  written — **design stale, code not at fault** — and it should either name the walkthrough-side
  equivalent or be struck, because as it stands "not registered" is indistinguishable from
  "nothing to register against".
* **S-f — no committed mutation harness for `readback_r3.py`** (see F3). `21813f2`'s *"21/21
  killed"* cannot be reproduced or re-run by a reviewer or by CI.

---

## C. Dig-item answers, stated directly

**1. Can four seats agree and be wrong together with nothing saying so?** Partly protected, and the
protections are weaker than §4 claims. Running the four seats end-to-end on patched `m0217` with a
scripted all-agree client, the line does carry `(NON-EVIDENTIAL)` on 4d and *"stage-3 discrimination
UNAVAILABLE"*. But: 4c's independence is real only against `readback.py` and not against a rendering
bug (**F6**); RB4's stamp cannot fire on any stored clause (**F8**); the discrimination cross-check
degrades to "unsupported for everything" while claiming availability if the join key is wrong
(**F4**); consensus language has a route into the report one nesting level down (**F7**); and 4a is
not actually walled off from the pass line (**F5**).

**2. Can a seat verdict reach a stage-1 or stage-2 prompt?** **No — I tried and could not.** See §D.

**3. Break R3.** Every named path blocks correctly (§D). The one thing I got through is **F9**.

**4/5. The sweeps.** `mutate_seats.py` reproduced at 83/0 on the real tree — the number is real, the
instrument that produced it is not trustworthy (**F3**). 20 hand-written mutants, **6 survivors**
(**F5, F6, F10**).

**6. The R3 wiring.** **F2** — it does not work against the real type, and the tests miss it by
inventing a fixture that fits the accessor.

**7. Cost.** Arithmetic verified correct; **F12** and **F13** are the findings.

---

## D. Checked and found SOUND — so the coverage of this review is auditable

**The leak perimeter (dig item 2) — tried and could not get one through.**

| attempt | result |
|---|---|
| `seat_finding('4b',…)` → `translate.render_error_log` | withheld; hole visible and counted |
| the same → `seats.render_findings_log` | withheld, **byte-identical** wording to `translate`'s |
| the same → `seats.append_findings_to_transcript` | `DisclosureRefused` |
| `route()` on a seat finding | `Routing("re-translate", (), None)` — **zero bits** carried |
| `route()` past `max_retranslations` | `Routing("carry", (), "readback-4b")` — no finding text |
| `inert_finding` (`covered-but-inert`) | not in `DISCLOSABLE_ORIGINS`; refused |
| `seat_finding` with a bad seat name | `SeatRefused` (mutant dies) |

The seat-origin fence itself is sound. The two real perimeter problems are **F11** (the *disclosable*
side is unreachable from any production finding, and the constant is still unregistered) and the
inherited **A2** (`probe-structural` carries a seat label and stage 4 extends that tuple).

**R3's block-on-empty machinery is genuinely well pinned.** 12 of my 20 hand mutants were aimed at
`readback_r3.py`; **10 died**, most 1:1:

| mutant | died to |
|---|---|
| `anonymous_variables` reads comments | the `m0255.lp`-comment test |
| `anonymous_variables` reads strings | the string-constant test |
| `_refuse_anonymous` skips the LINK texts | `…link_scope_is_REFUSED_BY_NAME` |
| the two-answer-set guard removed | `test_two_answer_sets_BLOCK` |
| `gloss_leaf` drops the leaf's constant | `test_a_LEAFS_CONSTANT_survives…` |
| `gloss_leaf` shows the placeholder | same test's second half — a real paired control |
| `verdict_atoms` accepts any derived atom | the no-derivation test |
| `trace_safe` neutralises nothing | the bad-character test |
| every node stamped layer 2 | the layer-1 pooling test |
| `no-derivation` situations dropped | the counted-not-dropped test |

The three redundant xclingo detectors (return code / stderr `error:` / missing `DONE_MARK`) each
have their own RED test **and** its `if True:` control, with the premise asserted inside the test
and a scripted fake interpreter rather than "a python that happens to lack xclingo" — this is
`DEBUGGING_TIPS` §8 followed properly, and it is the best work in the range.

**Also checked and sound:**

* **The pyc-invalidation fix in `mutate_seats.py`** — `rmtree(__pycache__)` +
  `PYTHONDONTWRITEBYTECODE=1` removes the window entirely. Verified; the documented trap is closed.
  (The instrument's *other* holes are F3.)
* **4c is never echo-stamped** — `stamp_evidential` returns early for any seat outside
  `ECHO_STAMPED`, `cross_check_4d` touches only 4d, and `divergences` leaves `evidential` alone.
  Confirmed by execution: a 4c judgement comes back `evidential=True, stamps=()` through every path.
* **RB1 residue in R3's live output: zero.** I scanned every node text produced by `readback_r3.py`
  over the whole `runs/` corpus, stripping `«»`, `⟨act …⟩` and `⟨no gloss: …⟩` spans, for any
  declared concept/ontology predicate name or any `name(` pattern surviving outside a gloss:
  **0 flagged nodes**. Invariant 1 holds on today's material.
* **Prior F5's fix holds.** `readback.marker_safe` neutralises `«` / `»` inside a gloss; the
  guillemet, semicolon, percent, bracket and pre-existing-curly-quote cases all render cleanly
  through R3. (The gap is the ASP markers — S-d — and `%!` — F9.)
* **`_UNIVERSAL_PATTERNS` closes prior A7's stage-4 half.** `schema.BEHAVIOUR_NS` is **imported**
  rather than re-listed, with a `(?<![A-Za-z0-9_])` lookbehind, so `b_asserts(` is caught here even
  though `probe._DISCLOSURE`'s `\basserts\s*\(` still misses it. `panel`, `reviewed.json` and
  `probe.LABELS` are all fenced, and every one of those fences dies under mutation. §8 row 13 is
  genuinely met.
* **`_MODULE_PATTERNS` reuses `probe._DISCLOSURE` rather than copying it** — right call, and the
  comment gives the right reason.
* **The `world` routing (§5.2)** — `build_4c_prompt` refuses a `world` item in a **separate pass**
  before the per-item loop, with the reason stated (order-independence of the refusal). Correct and
  well-motivated. `check_world_items` is pinned.
* **`ClaimDenominator.__post_init__`** refuses a claim counted both as `forbid_body` and in 4d's
  denominator; `denominator_4d` refuses a `forbid_body` module with no named claim and refuses a
  name that matches nothing. Three real guards, all pinned. (The same discipline is what F4 is
  missing.)
* **`judge` refuses to run without an explicit `client_factory`** — no default path to the network,
  same shape as `probe.label_situations`. Pinned.
* **No pinned live counts.** I swept `test_seats.py` and `test_readback_r3.py` for `== <n>` against
  live artifacts. `test_at_least_one_stored_module_yields_a_NON_EMPTY_derivation` is written as
  `>= 1` with an explicit note about why it is not an exact count, and asserts `seen >= 1` first so
  it cannot pass vacuously. `CLAUDE.md`'s twice-bitten rule is honoured.
* **`checks.SEVERITIES` not extended**; stage-4 findings are `error`/`note` only. §8's note honoured.
* **`MODULE_MAP.md` §11** — read before filing. None of the fourteen findings touches any of the six
  contracts; all six are in `semi-formal-experiment/` and everything here is in `walkthrough/`.
* **Full suite re-run after all restores: 673 passed, 1 xfailed.**

---

## E. What I would fix first

1. **F2** — the R3 wiring. Either make `denominator_4a` read `ModuleR3.situations[*].derivations`
   with a real seat-facing text for each, or revert `beb8531` and record R3 as unwired. What must
   not stand is a wiring that silently drops R3 and reports nothing. Delete `_D`/`_R3` and build
   the fixture through `render_r3`.
2. **F3** — `mutate_seats.py` gets `mutate_schema.py`'s three guards (green baseline through the
   same path, rc triage, collected-count comparison) and an `error` status. Until it does, no
   mutation number from it means anything. Then write the R3 harness (S-f).
3. **F1** — decide in the design what two judgements are allowed to diverge, and either key
   `divergences` on that or delete §6's machinery. Fix the five tests to use legal verdicts either
   way, because as written they would keep passing over a deleted function.
4. **F4 + F5 + F7** — three small diffs on `seats.py`: refuse a `discrimination` key not in 4d's
   denominator (and count the misses in the report); drop `4a` from `pooled`; make
   `refuse_aggregate` recurse and scan values.
5. **F6** — give `_item_text` deterministic checks, or stop claiming in §4.1 that 4c survives a
   dropped condition.
6. **F13 + F8** — restate §7's corpus-scale numbers and §3a's echo figure from the measurements the
   code now produces. Both are the design lagging honest code, and both are the direction that has
   already bitten this repo twice.

---

*No repo file was modified by this review except this one. `git diff --stat` at completion:
`semi-formal-experiment/usage.jsonl` only, which was already dirty when the review began.*
