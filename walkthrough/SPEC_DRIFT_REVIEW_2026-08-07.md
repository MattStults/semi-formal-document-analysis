# Adversarial spec-drift review — 2026-08-07

**Reviewer:** clean-context agent, no stake in the work. **Scope:** today's build — stage 3
(`probe.py`), the stage-4 renderer (`readback.py`), `STEP_stage4.md` §2.3 revision 2, and the two
`schema.py` ASP restrictions (one withdrawn, one kept).

**Claim under review:** *that all of this implements the design rather than quietly redefining it.*
**Verdict: the claim does not hold.** Eight confirmed drifts, three of them load-bearing. One is a
disproved-ground withdrawal that re-opens a failure mode the design classifies as *loud — crashes*;
one is a seat label crossing the leak perimeter under a `probe-structural` badge; one is an RB1
exemption that exists only in the code.

⚠️ **Environment note, recorded because it affects reproducibility of anything below.** While this
review was running, a concurrent process was mutating `walkthrough/paper_pipeline/phase_1/readback.py`
in the working tree (observed twice: `substitute` returning the bare name at ~23:5x, then
`_fallback` stamping `layer 2`). Every mutation experiment in §B was therefore run against an
**isolated copy** in a scratchpad, seeded from `HEAD`. I made no edit to any repo file.
`git diff --stat` for files I touched: **empty**.

---

## A. Confirmed drifts, ranked by how badly a wrong answer would mislead

### A1 ⛔ CONFIRMED — the withdrawn `_` guard was withdrawn on a ground that is not the design's ground, and the design's ground is still true

**Design sentence violated** (`walkthrough/resources/03_pipeline.md:33`):

> | | **7. Anonymous placeholders break the explainer** | Loud — crashes | `policy(P) :- policy_class(P,_)` is idiomatic ASP; **xclingo** cannot process it. ⚠️ A tool limitation, not a language property. |

and (`03_pipeline.md:239`), stage 2's deterministic-check node:

> `DET --> D1[compiles · no unresolved names<br/>· no anonymous placeholders]`

**The code that violates it.** `schema.py:133 _check_body` — the anonymous-variable rejection is
gone, with this comment block (`schema.py:97`, `:133-146`):

> `⭐ NO ANONYMOUS-VARIABLE REJECTION HERE, deliberately. … the renderer ground that used to justify
> rejecting it is disproved`

and `STEP_stage4.md:261` states the ground that was disproved:

> `both now removed (`_check_body`'s anonymous-variable rejection: *"the tool that renders a rule
> back into English cannot process it"*)`

**Why this is a drift and not a clean withdrawal.** The evidence produced (bare `clingo` derives
`p(a)` from `p(X) :- q(X,_).`; ASP2CNL skips hidden terms) refutes a **renderer** ground. The design
never gave a renderer ground. It named **xclingo** — the explainer — and `STEP_stage4.md:224` makes
xclingo load-bearing for stage 4's own R3 layer (*"every stage-3 covering-set situation … xclingo
explanation tree"*). Nothing in `STEP_stage3.md`, `STEP_stage4.md`, `DECISION_stage3_build.md`,
`DEBUGGING_TIPS.md` or the two withdrawal commits (`3759e55`, `0d930b4`) mentions xclingo. The
withdrawal was made without testing the tool the design names.

**Reproduction — the design's ground is still true, on the repo's own xclingo:**

```
$ printf 'p(X) :- q(X,_).\nq(a,b).\n' > /tmp/anon.lp
$ semi-formal-experiment/.venv/bin/xclingo --auto-tracing=facts /tmp/anon.lp
xclingo version 2.0b24
Answer: 1
<block>:7:1-56: error: unsafe variables in:
  _xclingo_sup(1,0,p(X),(X,#Anon0)):-[#inc_base];_xclingo_model(q(X,#Anon1)).
*** ERROR: (xclingo, explainer program) grounding stopped because of errors

$ printf 'p(X) :- q(X,Y).\nq(a,b).\n' > /tmp/ctl.lp   # control, no `_`
$ semi-formal-experiment/.venv/bin/xclingo --auto-tracing=facts /tmp/ctl.lp
  … no error
```

Verbatim failure mode #7: **loud, crashes**, and it takes the whole explainer program down, so it
takes the link set's entire R3 rendering with it. `STATE.md:169` records that `m0217` was rejected
by the validator for exactly this; it would now be admitted, pass stage 2, and break at stage 4.

**Which should change: the CODE.** Restore the `_check_body` rejection, restated on the xclingo
ground (which is measured, current, and independent of the renderer). Note the *other* half of the
re-examination — keeping the guard in `_check_term` because `_` in a rule **head** is unsafe to
clingo itself — is correct and well-grounded; only the body half is wrong. If the design instead
wants `_` admitted, the design must first say what renders R3, because xclingo cannot.

**Collateral:** `0d930b4` deleted the self-test check that pinned this rule. The commit message's
reasoning (*"a check that pins a deliberately-withdrawn rule is not a quality floor"*) is sound only
if the withdrawal was sound. It was not, so a real floor was removed.

---

### A2 ⛔ CONFIRMED — a model seat's label crosses the leak perimeter wearing a `probe-structural` badge

**Design sentence violated** (`STEP_stage3.md:395`, the `probe-structural` row):

> ⭐ **yes** — derived from the module and the solver alone, with **no expected verdict anywhere
> near them**, exactly as stage 2's are. Added to `DISCLOSABLE_ORIGINS`

**The code.** `probe.py:726 impossible_findings` builds a **`probe-structural`** finding from the
seat's `impossible` **label**, naming the situation *and its ground atoms*:

```python
for l in labellings:
    if l.label != "impossible":
        continue
    out.append(structural_finding(
        "probe-impossible-situation", where,
        f"the module admits a situation the clause treats as impossible: "
        f"{l.situation_id} ({_atoms_phrase(s)})"))
```

**Reproduction — it reaches a stage-1 repair prompt:**

```
$ cd walkthrough/paper_pipeline/phase_1
$ ../../../semi-formal-experiment/.venv/bin/python -c "
import probe, translate
S = probe.Situation('S3', 3, frozenset({'political_content(m)','exploits_individual(m)'}), frozenset())
f = probe.impossible_findings([S], [probe.Labelling('S3','impossible','incoherent')], 'm0217')
print(f[0].origin, f[0].origin in translate.DISCLOSABLE_ORIGINS)
print(probe.append_findings_to_transcript([], f)[0]['content'])"
probe-structural True

stage 3 failed these checks:
  - [probe-impossible-situation] m0217.lp: the module admits a situation the clause
    treats as impossible: S3 (exploits_individual(m), political_content(m))

Fix every one of them. Return the corrected module, complete.
```

`impossible` is one of the four labels in `SEAT_BRIEF` (`probe.py:~800`). Disclosing it tells the
translator the seat's answer for S3 and rules out the other three labels for it — which is the exact
argument `STEP_stage3.md:373` uses to refuse `probe-verdict`:

> *"Withholding the label while naming the situation is not a partial disclosure; it is the whole
> disclosure with a fig leaf."*

The remedy the translator is being steered toward (add an integrity constraint excluding S3) also
changes S3's derived status, i.e. it is hill-climbing against the answer key by another route.

**Which should change: BOTH, and the DESIGN first.** The design's `probe-structural` row lists this
finding *and* asserts a grounds sentence that is false of it. Either the grounds sentence narrows to
"solver-derived findings only" and `probe-impossible-situation` moves to a non-disclosable origin
routed to a human (like `probe-verdict`), or the design must argue in writing why *this* label is
different from the other three. `probe.py:726`'s own docstring gestures at the argument
(*"a finding naming the situation AND NO VERDICT"*) but that is precisely the fig leaf the same
document rejects two paragraphs earlier. This is a transcript-only justification sitting in a
docstring; per `CLAUDE.md`, it belongs in a cycle record with the alternative rejected by name.

---

### A3 ⛔ CONFIRMED — the act-term exemption to RB1 exists only in the code, and it is not a corner case

**Design sentence violated** (`STEP_stage4.md:415`, RB1, unamended by revision 2 which states
*"§2.4's five checks … stand as written"*):

> **RB1** | **no label survives.** No predicate name, functor, `/arity` signature or clause id from
> the module may appear in a rendered sentence **except as the explicit clause reference**

Exactly **one** exception is granted: the clause reference. `STEP_stage4.md:312`'s template line —
*"`act/1` renders the act term from the module's `acts` declaration"* — is a description of a
layer-2 template, not a grant of an RB1 exemption; §2.3 nowhere amends §2.4.

**The code.** `readback.py:600`, inside `_rb1`:

```python
# An act term rendered as itself is the ONE exempt span, and it is
# exempt because it is marked, not because it is quiet.
scan = _strip(r.text, ACT_MARK, ACT_CLOSE)
```

`_act_span` (`readback.py:453`) emits `⟨act produce(M)⟩` whenever nothing glosses the act functor —
which is **always**, since no schema field can hold an act gloss.

**Reproduction — scale.** Rendering every validated module in `runs/`:

```
$ cd walkthrough/paper_pipeline/phase_1
$ ../../../semi-formal-experiment/.venv/bin/python -c "
import json,glob,schema,readback
for p in sorted(glob.glob('runs/*/m0*.json')):
    try: m=schema.Module.model_validate(json.load(open(p)))
    except Exception: continue
    for r in readback.render_module(m).renderings:
        if r.kind=='asserts': print(r.text[:110])"
clause m0014 forbids ⟨act facilitate(H)⟩ when «mass surveillance is a critical high severity harm»
clause m0079 forbids ⟨act produce(M)⟩ when ⟨no gloss: new_material⟩ and ⟨no gloss: disallowed⟩
clause m0105 forbids ⟨act follow_instructions(I)⟩ when «the provenance of instruction I is unclear»
…  (19 of 19 `asserts` renderings; every one shows a bare functor, RB1-exempt)
```

**Assessment — asked for, so stated plainly.** *The exemption is a hole in Invariant 1, not a
legitimate implementation limit.* Three reasons:

1. It is not a fringe construct. It covers **the deontic head of every rule** — the single item a
   seat most needs rendered as a meaning. The clause's normative content (`facilitate`, `produce`,
   `notify_user`) is exactly the vocabulary Invariant 1 exists to stop being taken on faith.
2. The names are *the document's own words*, so they read faithful. That is failure mode **#5
   (hollow stubs)** and **#4 (imports a name without its content)** — §0(5) measures #4 in this
   repo's own output at 7.5 % — arriving inside the renderer, where §2.3a explicitly rejected
   ASP2CNL's naming model to keep it out. The renderer rejects the naming model for body atoms and
   then adopts it for acts.
3. The *marking* argument (`"exempt because it is marked, not because it is quiet"`) is the argument
   `DEFERRED.md` D-4 already rejects one level up: `schema.Licensed` enforces the *mark* on a `world`
   fact and D-4 records that this must not be read as closing the check. A `⟨act …⟩` bracket is a
   mark, not a definition.

**Which should change.** ⭐ **The DESIGN should change first, and the code follows.** The honest
statement is: *Invariant 1 cannot be satisfied for act terms today, because no artifact holds an act
gloss.* That is a **schema gap** (`Module.acts` is `list[str]`; nothing carries a meaning), and the
right fix is a gloss slot for acts — not a permanent RB1 carve-out. In the meantime the exemption
should be a **declared, counted outcome** (`readback-act-literal` is already emitted as a note —
count it, put the rate in the report, and stop calling RB1 "pass" on a module whose only assertion
renders as a label). Today RB1 reports `pass` on `m0014` and `m0105` while their whole deontic
content is a bare functor.

---

### A4 ⛔ CONFIRMED — revision 2 *did* weaken RB4, in the one place the amendment claimed it did not

Dig item 4 asked whether the amendment weakened anything RB1–RB5 depended on. It did, and the
amendment asserts the opposite (`STEP_stage4.md:331`):

> ⚠️ **Both layers are still subject to RB1–RB5 (§2.4).** Layer 1 … **buys no exemption from the
> checks.**

**The code.** `readback.py:684`, `echo_score`:

```python
have = _tokens(_strip(rendering_text, ASP_MARK, ASP_CLOSE))
if not have:
    return 0.0
```

Layer-1 content sits **inside** `⟦ASP: … ⟧` and is stripped out of the echo denominator entirely. A
rendering that is 100 % layer 1 scores 0.00 whatever it says, and is reported *evidential*.

**Reproduction:**

```
$ ../../../semi-formal-experiment/.venv/bin/python -c "
import readback
q='restricted content must not be produced for a broad audience'
t=readback.ASP_MARK+' '+q+readback.ASP_CLOSE
print(readback.echo_score(t,q))                                   # 0.0  -> 'evidential'
print(round(readback.echo_score('«restricted content» and «a broad audience»',q),2))  # 0.83"
0.0
0.83
```

A layer-1 rendering that is *verbatim the clause* — the exact condition RB4 exists to stamp — is
scored 0.00 and passes as evidential. RB1, RB2, RB3 and RB5 all survive the amendment intact (I
verified each; see §B); RB4 alone does not.

**Severity qualifier, stated so this is not overread:** across all 106 rendered items in `runs/`, the
layer-1 count is **0**. This is latent today. It becomes live the first time a construct with no
template appears — which is the amendment's whole purpose.

**Which should change: the CODE.** Either strip only the `⟦ASP:` delimiters and keep the tokens, or
report echo separately per layer. Do not leave a check that silently exempts the layer the amendment
was written to introduce.

---

### A5 ⛔ CONFIRMED — `readback-structural` was to be registered in `DISCLOSABLE_ORIGINS` *in the same diff*; it was not, and `readback.Finding` cannot carry an origin at all

**Design sentence violated** (`STEP_stage4.md:637`, and the §8 closing note):

> `readback-structural` … Added to `DISCLOSABLE_ORIGINS`

> ⚠️ **Three of these pin things that must be built in the same diff, not after:**
> `DISCLOSABLE_ORIGINS` gains `readback-structural` (test 14) … **Registration, not documentation,
> fences a module.**

**Reproduction:**

```
$ ../../../semi-formal-experiment/.venv/bin/python -c "
import dataclasses, readback, checks, translate
print([f.name for f in dataclasses.fields(readback.Finding)])
print([f.name for f in dataclasses.fields(checks.Finding)])
print(translate.DISCLOSABLE_ORIGINS)"
['check_id', 'severity', 'item', 'message']
['check_id', 'severity', 'where', 'message', 'origin']
('schema', 'link', 'probe-structural')
```

`readback.Finding` is a **different type** from `checks.Finding` with **no `origin` field**. So the
fence is not merely un-updated: a stage-4 finding cannot be classified by it in either direction.
Passing one to `translate.render_error_log` raises `AttributeError` rather than being withheld — a
crash is a safe failure, but it is not the designed one, and §8 row 14 requires the *positive* half
(`a readback-structural finding ⇒ rendered in full`) which cannot be satisfied today.

This is the exact shape `CLAUDE.md` names: *"New query-side module → registration … Same diff, every
time."*

**Which should change: the CODE.** Either give `readback.Finding` an `origin` (and reuse
`checks.Finding`), or state in `STEP_stage4.md` that stage-4 findings are structurally barred from
the repair loop and delete §5.5's `readback-structural` row.

---

### A6 ⛔ CONFIRMED — the layer-1 fraction is required in the report, printed even when zero. It is not printed

**Design sentences violated** (`STEP_stage4.md:323`, and §8 row 25 at `:790`):

> Per rendering: `layer: 1 | 2`. **Per clause and per run: the layer-1 fraction, printed even when
> zero** (§5.4's rule for the `unclear` rate, same reason).

> | 25 | the layer-1 fraction **absent** from the report ⇒ refused | fraction present and **zero** ⇒
> allowed | §2.3, on §5.4's rule: a number printed only when non-zero cannot be read as "we measured
> it" |

**The code.** `ModuleReadback.report()` (`readback.py:706`) prints the per-rendering stamp and
nothing else; `ModuleReadback` has no fraction field, and there is no run-level aggregate anywhere.
`grep -n "fraction" readback.py test_readback.py` → **no hits**. Test 25 does not exist.

**Reproduction:**

```
$ ../../../semi-formal-experiment/.venv/bin/python -c "
import json,glob,schema,readback
m=schema.Module.model_validate(json.load(open(sorted(glob.glob('runs/*/m0053.json'))[0])))
print(readback.render_module(m).report())"
readback m0053  outcome=readback-ungloss
  RB1=FIRED  RB2=pass  RB3=pass  RB5=pass  RB4=not-measured (no clause quote given)
  concepts[0]    [layer 2 · fluent]
      «the entity that the end user or developer interacts with»
  …
```

No fraction, per clause or per run.

⭐ **This is worse than cosmetic *because* the fraction is currently 0/106.** The design's stated
reason is §5.4's: *"a number printed only when non-zero cannot be read as 'we measured it'."* A
reader today cannot tell "the renderer is fully fluent on this corpus" from "the layer stamp was
never aggregated." Those are different claims and the second is the true one.

**Which should change: the CODE.** One field on `ModuleReadback`, one line in `report()`, one
run-level aggregate, one test.

---

### A7 ⛔ CONFIRMED — the stage-3 seat's *"and any behaviour"* denial is unenforced, and `b_asserts(` slips the existing pattern on a word boundary

**Design sentence violated** (`STEP_stage3.md:348`, §5's disclosure table):

> | the act, as an English phrase (`produce this material`) | ⛔ the derived status, the closure
> declaration, any other clause's verdict, **and any behaviour** |

**The code.** `probe.py:835 _DISCLOSURE` has nine patterns — signatures, `:-`, `asserts(`, `beats(`,
`cepa|cnpa`, `closure`, `derived:`, `CLAIMS:`, `%%|%!`. **None covers the behaviour namespace**, and
`schema.BEHAVIOUR_NS = {"b_asserts", "b_beats", "seed"}` — the canonical set that already exists — is
not imported. Worse, `re.compile(r"\basserts\s*\(")` does **not** match `b_asserts(`: the character
before `asserts` is `_`, a word character, so `\b` fails.

**Reproduction:**

```
$ ../../../semi-formal-experiment/.venv/bin/python -c "
import probe
for bad in ['b_asserts(m0255, forbid, produce(m))','seed(x)','b_beats(a,b,c)']:
    try: probe._refuse_disclosure(bad,'a situation'); print('LEAK PASSES:',bad)
    except Exception: print('refused  :',bad)"
LEAK PASSES: b_asserts(m0255, forbid, produce(m))
LEAK PASSES: seed(x)
LEAK PASSES: b_beats(a,b,c)
```

`STEP_stage4.md:783` (§8 row 13) already anticipates the *stage-4* half of this — *"`BEHAVIOUR_NS` at
generation has no counterpart at review"* — but stage 3's seat is **built**, its design row names the
denial, and the fence does not implement it. Note the consequence the design gives for a
namespace crossing (`schema.py:54`): *"one fact that crosses them can make a real conflict disappear
— satisfiably, with no error."*

**Which should change: the CODE.** Add `schema.BEHAVIOUR_NS` to `_DISCLOSURE` (import the set, do not
re-list it) and fix the `\basserts` boundary.

---

### A8 ⛔ CONFIRMED — §8's mutation bar for stage 4 is unmet, and the harness named cannot meet it

**Design sentence** (`STEP_stage4.md`, §8 "The bar"):

> Stage 4 ships with its **own mutation run at 0 survivors** or it does not ship.

**The code.** No `mutate_readback.py` exists and no mutation artifact for stage 4 is committed.
`mutate_schema.py` locates guards as `ast.Raise` nodes — and `readback.py` is *total by design*:

```
$ ../../../semi-formal-experiment/.venv/bin/python -c "
import ast
for f in ('readback.py','probe.py','schema.py'):
    print(f, sum(isinstance(n,ast.Raise) for n in ast.walk(ast.parse(open(f).read()))))"
readback.py 0
probe.py 16
schema.py 44
```

Pointing the harness at the renderer is a no-op:

```
$ ../../../semi-formal-experiment/.venv/bin/python mutate_schema.py --schema readback.py --tests test_readback.py
    …  20 guards: "0 matches for …"   (reports ERROR, not "no survivors" — the harness is honest)
```

⭐ **This is the direction that is easy to miss: the CODE is right and the DESIGN's bar is stale.**
A renderer with no failure branch is what the §2.3 amendment *asked for*; a "delete a raise" mutator
is structurally the wrong instrument for it, and the bar was written without noticing. The design
should restate the bar for stage 4 as *mutate the check predicates* (`_rb1`…`_rb5`, `substitute`,
`count_not`, `required_symbols`) rather than *delete a raise*. I ran that battery by hand — see §B —
and **all five checks plus the ungloss check are genuinely pinned**, so the *substance* of the bar
is met even though the named instrument cannot express it. Write the substitute harness; do not
weaken the bar.

---

## B. Mutation battery run by this review (isolated copy, no repo file touched)

Method: `cp -a walkthrough` to scratchpad, `readback.py` reset to `HEAD`, mutate one construct,
`pytest test_readback.py test_probe.py`. Baseline 131 passed.

| mutation | intent | tests killed | verdict |
|---|---|---:|---|
| `substitute` returns the bare name | layer 1 renders the LABEL, not the definition (Invariant 1) | 3 | ⭐ pinned |
| `_rb1`: `scan = ""` | RB1 dead | 4 | ⭐ pinned |
| `_rb2`: `g = None` | RB2 dead | 1 | ⭐ pinned (1:1) |
| `_rb3`: `want, got = 0, 0` | RB3 dead | 1 | ⭐ pinned (1:1) |
| `checks["RB5"] = True` | RB5 always passes | 1 | ⭐ pinned (1:1) |
| `required_symbols` returns `set()` | ungloss check dead | 1 | ⭐ pinned (1:1) |
| `probe._refuse_disclosure` returns immediately | seat disclosure fence dead | 5 | ⭐ pinned |

⚠️ **A retraction, recorded because a review that hides its own wrong turn is worse than none.**
Mid-review I ran `pytest walkthrough/ -q` and got **468 passed** while `substitute` was mutated on
disk by the concurrent process, and briefly concluded the mutation was uncaught. That was wrong: the
mutation was applied *after* that run. The controlled battery above kills it in 3 tests. The
renderer's checks are honestly pinned. Nothing else in this review depends on that run.

---

## C. Suspected — real, but I could not close them from the artifacts alone

### S1 — the layer-2 body template drops variable co-reference, and no check notices

`_render_symbolic` (`readback.py:246`) drops arguments that are plain variables — which
`STEP_stage4.md:305`'s template line sanctions (`p(X), q(X), not r(X) -> "«gloss(p)» and «gloss(q)» …"`).
The consequence is that two structurally different rules render **identically**:

```
$ ../../../semi-formal-experiment/.venv/bin/python -c "
import readback
g={'p':'is a document','q':'is harmful'}
for b in ['p(X), q(X)','p(X), q(Y)']:
    print(repr(b),'->',readback._join(readback.render_body(b,g)))"
'p(X), q(X)' -> «is a document» and «is harmful»
'p(X), q(Y)' -> «is a document» and «is harmful»
```

*"the same thing is a document and is harmful"* and *"some thing is a document and some other thing
is harmful"* are different claims, and every one of the four seats reads only the rendering. RB2
passes (both glosses present), RB3 passes (no `not`). This is a **faithfulness** hole in the one
artifact §2 says all four seats judge, and it is design-sanctioned, so it is a **DESIGN** question,
not a code bug: §2.3's template needs to say what happens to co-reference. Live today — `m0134`
`asserts[0]` and `m0150` `asserts[3]` both have multi-variable bodies. Marked SUSPECTED only because
I cannot rule out that a later section addresses it.

### S2 — `readback.py` shows no licence, so Invariant 2 is invisible in the stage-4 artifact

Dig item 2, answered by execution: `grep -c licence readback.py` → **0**. `Rendering` carries
`item/kind/text/layer/source/body` and no licence, no `cites`. Consequences:

- `STEP_stage4.md:576`'s **4b denominator** (*"the rendered set, minus items whose licence is
  `world`"*) and **4c's** licence-partitioned denominator (§5.2) cannot be computed from the
  renderer's output; a consumer must go back to the `Module`.
- Nothing in the renderer presents anything as *licensed*, so strictly it does not present unlicensed
  material as licensed. But it also gives a seat no way to see that a sentence rests on an `assumed`
  or `world` fact — which is what Invariant 2's *"a result resting on world knowledge is a different
  claim"* is for.
- `DEFERRED.md` D-1's *"Nothing computes it — verified 2026-08-07: not `schema.py`, not `link.py`,
  not `checks.py`"* remains **true**, and its enumeration is now **incomplete**: `readback.py` and
  `probe.py` exist and also do not. Worth one word in D-1 so the next reader does not re-derive it.
- Related and stale: `prompt/00_task.md:31` tells the model *"A conclusion inherits the weakest
  licence… This is what makes 'change one asserted fact and the answer disappears' **visible in the
  output**"*. It is visible in no output; and D-1 records stage-0 finding **F4** measuring that
  sentence's example **false** (the match survived through a second independent world fact). The
  prompt is teaching a claim the repo has already refuted. **DESIGN/PROMPT should change** — but it
  is a watched prompt file, so per D-4/`guard.py` it is a reviewed prompt change with its own
  held-out measurement, not a documentation edit.

### S3 — R2 and R3 are unbuilt, and §5.5 lists a finding neither can produce

`STEP_stage4.md:224` specifies **R2** (mechanical rendering diffed against the model's authored
`read_back`) and **R3** (xclingo derivation trees with glossed leaves). `readback.py` implements
**R1 only**: `grep -n read_back readback.py` → no hits; no xclingo import. §5.5 nonetheless lists
*"the R2 mechanical-vs-authored diff"* among `readback-structural`'s contents. Expected for a
document that says *"this document is the plan only"* — flagged so nobody reads §5.5 as describing
built behaviour, and because A1 (xclingo vs `_`) blocks R3 outright.

### S4 — `_coherent`'s declaration check and RB2 both miss 0-arity body atoms

Both `schema._coherent` (`:666`) and `readback._PRED_IN_BODY` match only `name(`. A propositional
body atom `p` (no arguments) is therefore **not** required to be declared and **not** checked by RB2.
Layer 2 still marks it `⟨no gloss: p⟩`, but `_label_set` would not list it, so RB1 does not fire on
it either. I found no live instance in `runs/`, hence SUSPECTED. Note this predates today's work.

### S5 — `dryrun.txt` is stale, and the green pytest run does not say so

```
$ ../../../semi-formal-experiment/.venv/bin/python translate.py --self-test
  ❌ dryrun.txt matches the current config and prompts (inputs-sha fdef1ecdebb0728c)
51 passed, 1 failed
$ semi-formal-experiment/.venv/bin/python -m pytest walkthrough/ -q
468 passed
```

`git log -- prompt/` shows five commits since `dryrun.txt` was last regenerated. The pytest wrapper
(`test_prompt_examples.py:193`) deliberately asserts only that the self-test *completes and reports*,
with a documented reason (DEBUGGING_TIPS entry 9 — do not pin a count). That reasoning is right, but
the current shape means **`pytest -q` is green while a self-test check is red**, which is this repo's
named signature failure in miniature. Tracked as Q-4 already; listed here because "468 passed" is
being used in the handoff as the state-of-health number and it is not one.

---

## D. Checked and found in step — coverage record

| # | check | result |
|---|---|---|
| 1 | Part 1's 17 failure modes vs `prompt/30_failure_modes.md` | ⭐ **agree**, 17 = 17 (the `**18.` grep hit is `18.4%`, prose) |
| 2 | `30_failure_modes.md` vs its three `eval_arms/prompt_*` mirrors | ⭐ **byte-identical** in all three; `00_task.md`, `10_output_format.md` also identical; `20_worked_example.md` differs **by design** (that is what the arms vary) |
| 3 | Failure mode #17 (cyclic `beats`) — design says *"needs a mechanical cycle check"* | ⭐ **built**: `link.py:586 _check_beats_cycle`, with its own self-test positive+negative pair (`link.py:1153-1166`) |
| 4 | `_check_term`'s retained `_` guard (rule **head**) | ⭐ **correctly regrounded** — clingo itself calls `p(_) :- q(X).` unsafe. Only the `_check_body` half (A1) is wrong |
| 5 | `build_seat_prompt` vs `STEP_stage3.md` §5 disclosure table, row by row | rows 1–3, 5 enforced (module/`:-`/`asserts`/`beats`/`%!`/signatures refused; `render_situation` refuses on a missing gloss rather than falling back to the name — correct); **row 4 partially unenforced → A7** |
| 6 | `probe.route` / `append_findings_to_transcript` — can a `probe-verdict` reach a stage-1 prompt? | ⭐ **no.** `append_findings_to_transcript` raises `DisclosureRefused`; `route` re-translates from a clean prompt. The fence works for the origin it fences — the leak is the mis-classification, A2 |
| 7 | RB1 on layer-1 output (unglossed names left bare inside `⟦ASP:…⟧`, not stripped) | ⭐ **correct** — RB1 scans layer-1 spans and fires |
| 8 | RB2 / RB3 under the layer-1 fallback | ⭐ **survive**: glosses stay inside the ASP span so RB2's substring test holds; `str(node)` carries its own `not` so `_markers` counts it. `_markers` strips glosses first, so a gloss containing the word "not" does not fire RB3 — verified |
| 9 | RB3 double negation | ⭐ correct: `not not q(X)` → sign 2 → two markers, `count_not` 2 |
| 10 | `_CONVERSE` (aggregate guard printed on the left) | ⭐ correct; an inverted table would silently flip every aggregate bound, and it is not inverted |
| 11 | RB4 as a stamp, never a gate | ⭐ correct — `checks["RB4"] = None` by design, `non_evidential` is a flag |
| 12 | `DEFERRED.md` D-3's *"`repair_loop` called without `concepts=`"* | ⭐ **still true**: `translate.py:1097` passes no `concepts=`; `_concepts` accumulates at `:1161` and is only written to disk |
| 13 | `DEFERRED.md` D-4's warning about `STEP_stage4.md:452` | claim moved — the *"already enforces both"* sentence is now at `STEP_stage4.md:594` (and `:783`). D-4's **line reference is stale**; its substance is intact. Minor, but it is the class of thing this repo has shipped before |
| 14 | `STEP_stage4.md` §5.5's `[RAN] translate.DISCLOSABLE_ORIGINS == ('schema','link')` | stale as of today's `probe-structural` addition. Reads as a historical `[RAN]` record, so noted not filed |
| 15 | `checks.SEVERITIES` not extended by stage 4 (§8 note) | ⭐ **honoured** — `readback.Finding` uses `error`/`note` only |
| 16 | full suite | `pytest walkthrough/ -q` → **468 passed** (matches the brief) |
| 17 | `MODULE_MAP.md` §11 anti-rules | none of the above is one of the six; checked before filing |

---

## E. What I would fix first

1. **A1** — restore `_check_body`'s `_` rejection on the xclingo ground, with the command above in
   the error message. It is the only finding here that can take a whole link set down.
2. **A2** — reclassify `probe-impossible-situation`, and write the ruling into the cycle record with
   *"disclose the situation but not the label"* rejected by name, per `CLAUDE.md`.
3. **A5 + A6 + A4** — one small diff on `readback.py`: an `origin` on `Finding`, the layer-1 fraction
   in `report()`, and `echo_score` no longer blind to layer 1. Three tests.
4. **A3** — decide the act question *in the design*. An RB1 carve-out covering every rule head is not
   an implementation detail, and today it makes RB1 report `pass` on modules whose entire deontic
   content is a label.
5. **A8** — write the renderer's mutation harness; do not lower the bar to the instrument.

---

*No repo file was modified by this review. `readback.py`'s working-tree diff at the time of writing
belongs to a concurrent process, not to me; I neither made nor reverted it.*
