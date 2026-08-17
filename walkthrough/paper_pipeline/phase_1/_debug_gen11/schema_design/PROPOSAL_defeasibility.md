# PROPOSAL — one schema element, proposed as text, applied to nothing

⛔ **`schema.py` IS GUARD-WATCHED (`walkthrough/model/watch.json`). Nothing in this file has
been applied.** Every diff below is text. Every blast-radius claim is grepped or `[RAN]`, and the
two that could not be settled by reading were settled by running them (§4.1, §4.2).

**Zero API spend.** Everything here is deterministic re-analysis of data already on disk.

**Denominators are single digit to low double digit and are stated everywhere.** 17 loop modules
(33 asserts), 25 reference modules (25 asserts), 42-item golden set, 892 stored module JSONs on
disk. No claim below rests on more than that.

---

## 1. RANKING — by evidence, not by fixability

Silence is the multiplier: a defect indistinguishable from a correct module cannot be found by
any reader, any seat, or any check.

| # | failure to express | instances MEASURED | modules | silent? | verdict |
|---|---|---|---|---|---|
| **1** | **E-2 defeasibility** | **6 of 17** loop modules carry a hedged claim (`by default` / `generally` / `unless` / `in most cases`); **1 of 17** carries any defeating condition in any assert body. Reference: 3 of 25 hedged, 2 of 25 with a defeater — **one of those two was ADDED by the Opus reference edit and marked "ARGUABLE how to encode it"**. R57 measured the prescribed remedy *inverting* a default. | 9 of 42 | ⭐ **YES, twice over.** An unconditional `oblige` is byte-identical to one whose default was dropped (P7's own words); and the body-branch failure is silent in the other direction — a rule that fires on no situation is failure mode #15. | **PROPOSE** |
| 2 | E-1 no negative pole | 5 of 26 reference clauses. The reference set resolved **all five without a new status**: 3 with `forbid`, 2 removed on independent span grounds. `checks.polarity_mismatches` recall measured 4/5 pre-widening; the widening on 2026-08-16 was written against the one miss. | 5 of 26 | **NO.** The read-back contradicts the status, which is exactly why the detector works. | **CHANGE NOTHING** — §3.1 |
| 3 | N1 `ontology`: bodied rule vs ground atom | 1 clause; two independent Opus passes SPLIT | 1 | YES (an inert atom validates) | **NOT A SCHEMA GAP.** Both forms are legal and both are needed. This is a prompt + check gap. Decline. |
| 4 | `forbid X(R) :- X(R)` forced tautology | anti-rule; ≥2 clauses | 2 | NO — visible, and already documented as forced | **CHANGE NOTHING.** The alternative (a variable act with a null body) is refused by clingo, not by us. |
| 5 | `closure` carries no `licence` (R21); vacuous on an obliged act (R79) | 1 each | 2 | partly | **PARK, NAMED** — §3.7 |
| 6 | R80 (no licence for a graph-supplied gloss), R73 (no home for a document-layout fact), R39 (obligation to PRODUCE), E-3 (non-exhaustiveness), E-4 (hedged facts) | 1 each | 1 each | mixed | **PARK, NAMED** — all singletons. §3.7 |

**Why #1 wins and it is not close.** It is the only entry where *both* available encodings are
measured broken:

* **Route A — push the defeater into a body** (P7's remedy). `[MEASURED, R57, l2821_3040_n017]`
  The draft obeyed P7 *and* N5 correctly and produced
  `oblige express_uncertainty_naturally(A) :- assistant_definition(A), default_context.`
  where `default_context` is a query-time **input**. A situation that does not affirmatively
  declare itself default derives nothing. *"By default"* — which by definition holds **unless**
  displaced — now holds **only when explicitly supplied.** One request switched the module off.
* **Route B — record it in notes** (P7's other branch). Leaves the module knowingly
  indefeasible. The shipped `l2821_3040_n017` took this branch: "by default" lives in `claims` C1
  and in the read-back and **in no rule**.

`[MEASURED]` The corpus shows Route B winning by default across the board: 6 of 17 loop modules
hedge, 1 of 17 has any defeating condition. Nothing in the schema or the checks reports the gap.

---

## 2. THE PROPOSED CHANGE — one element, two fields, cross-validated

The pair is one design element in this repo's existing idiom: a **discriminator** plus a
**payload**, cross-validated in one `model_validator`, exactly as `licence` / `cites` /
`inference` / `toggleable` already are in `Licensed._licence_obligations`.

### 2.1 Text diff to `schema.py` — `Assertion` (currently lines 424–449)

```diff
     status: Literal["forbid", "permit", "oblige", "prefer"]
     act: str = Field(
         description="the ACT TERM, e.g. produce(M) or interject(user). Acts "
                     "are indexed: an act, never a material")
     body: Optional[str] = Field(
         description="the ASP conditions under which this assertion holds, one "
                     "line — or null when it holds unconditionally. Null, never "
                     "an empty string: an empty string is rejected")
+    defeasibility: Literal["none", "named", "unnamed"] = Field(
+        default="none",
+        description="whether the clause states this as a DEFAULT rather than "
+                    "flatly. `none` — the clause states it flatly. `named` — "
+                    "the clause hedges AND names what displaces it; put that "
+                    "atom in `defeater`. `unnamed` — the clause hedges and "
+                    "names nothing that displaces it; `defeater` stays null "
+                    "and this module is recorded as knowingly indefeasible. "
+                    "Answered on EVERY assertion, like the closure "
+                    "declaration: an absent answer and `none` render the same "
+                    "bytes, so an optional field here would be no field")
+    defeater: Optional[str] = Field(
+        default=None,
+        description="the ATOM whose presence displaces this assertion — "
+                    "non-null exactly when defeasibility is `named`. Rendered "
+                    "as a NEGATED body literal, so the rule fires when the "
+                    "case says NOTHING. That direction is the whole point: a "
+                    "positive condition standing for a default makes the rule "
+                    "fire only where a case remembers to declare itself "
+                    "default, which is the default's own opposite")
 
     @model_validator(mode="after")
     def _assertion_ok(self):
         where = f"assertion {self.status}/{self.act!r}"
         self.act = _check_term(self.act, where, allow_vars=bool(self.body))
         _check_head_bound(self.act, self.body, where)
         _check_body(self.body, where)
+        if self.defeasibility == "named":
+            if not (self.defeater or "").strip():
+                raise ValueError(
+                    f"{where}: defeasibility `named` with no `defeater`. "
+                    f"Either name the atom the clause says displaces this, or "
+                    f"declare `unnamed` — which records that the module is "
+                    f"knowingly indefeasible instead of leaving that "
+                    f"indistinguishable from a clause that never hedged")
+            self.defeater = _check_term(self.defeater, f"{where} `defeater`",
+                                        allow_vars=True)
+            if self.status == "permit":
+                raise ValueError(
+                    f"{where}: a `permit` may not carry a `defeater`. A "
+                    f"negated defeater fires on SILENCE. Under an obligation "
+                    f"that is what a default MEANS; under a permission it "
+                    f"licenses the act in every case that forgot to mention "
+                    f"the exception, which is the dangerous direction. A "
+                    f"permission's limit is a POSITIVE body condition")
+            if _VAR.search(self.defeater) and not (self.body or "").strip():
+                raise ValueError(
+                    f"{where}: `defeater` {self.defeater!r} carries a variable "
+                    f"and renders as the ONLY body literal, negated, so "
+                    f"nothing binds it. `[RAN]` clingo: "
+                    f"`asserts(c,oblige,act(R)) :- not q(R).` -> `unsafe "
+                    f"variables in: ...; note: 'R' is unsafe`, and the WHOLE "
+                    f"FILE is refused. Give the assertion a positive body, or "
+                    f"write a ground defeater")
+        elif (self.defeater or "").strip():
+            raise ValueError(
+                f"{where}: `defeater` is set but defeasibility is "
+                f"{self.defeasibility!r}, so the atom is never rendered and "
+                f"the assertion is unconditional in the program while reading "
+                f"as defeasible in the record")
         return self
```

### 2.2 Text diff — `Module._coherent`, the D4b level-1 declaration scan (lines 867–880)

A `defeater` is a body literal in everything but syntax, so it must reach the existing
declaration check. **No new message, no new failure class** — it reuses the one that is there.

```diff
         for item in (*self.asserts, *self.beats, *self.ontology):
             body = getattr(item, "body", None) or ""
+            # a `defeater` renders INTO the body, so it is subject to the same
+            # rule: a name nothing declares cannot be told apart from a typo
+            if getattr(item, "defeasibility", "none") == "named":
+                body = f"{body}, not {item.defeater}" if body else \
+                       f"not {item.defeater}"
             for name in re.findall(
                     r"(?<![A-Za-z0-9_])([a-z][A-Za-z0-9_]*)\s*\(", body):
```

### 2.3 Text diff — rendering, `schema.render_lp`

```diff
+def _conditions(a):
+    """An assertion's rendered conditions: its `body`, plus its `defeater`
+    NEGATED. Empty string when it is unconditional.
+
+    ⭐ THE NEGATION IS THE POINT, and it is not negation-as-failure by
+    accident. A default holds UNLESS displaced, so the rule must fire when the
+    case says NOTHING. `[MEASURED]` the positive form does the opposite:
+    `_debug_gen11/ds_opus_loop/RECOMMENDATIONS.md` R57 records a module whose
+    default became a query-time input, so it fired only where a situation
+    affirmatively declared itself default, and was inert everywhere else.
+    ⚠️ This does NOT reopen N5. N5's ban on negation-as-failure stands for
+    every ordinary body literal and for every `permit`; the validator refuses
+    a defeater on a `permit` for exactly N5's reason.
+    """
+    parts = [a.body] if a.body else []
+    if a.defeasibility == "named":
+        parts.append(f"not {a.defeater}")
+    return ", ".join(parts)
+
+
 def render_lp(mod: Module, clause: dict) -> str:
```

in the header block, beside `%% closure:` and `%% forbid-body:` (lines 1249–1252):

```diff
     for fb in mod.forbid_body:
         out.append(f"%% forbid-body: {fb.head} <- {fb.banned}")
+    for i, a in enumerate(mod.asserts):
+        if a.defeasibility == "unnamed":
+            out.append(f"%% indefeasible-default: asserts[{i}] {a.act} — the "
+                       f"clause hedges and names nothing that displaces it")
```

and in the assertions block (lines 1288–1295):

```diff
         for a in mod.asserts:
             args = ", ".join(a.read_back_slots)
             out.append(f'%!trace_rule {{"{a.read_back}"'
                        + (f", {args}}}." if args else "}."))
             head = f"asserts({mod.clause_id}, {a.status}, {a.act})"
-            out.append(_line(a, head + (f" :- {a.body}." if a.body else ".")))
+            cond = _conditions(a)
+            out.append(_line(a, head + (f" :- {cond}." if cond else ".")))
```

### 2.4 What each of the three values buys

| value | rendered | what it fixes |
|---|---|---|
| `none` | unchanged, byte-for-byte | nothing — and that is the point: §5 B1 pins it |
| `named` | `... :- <body>, not <defeater>.` | the default now **fires on silence** and is **displaced by the named fact** — the R57 defect is structurally unreachable |
| `unnamed` | a `%% indefeasible-default:` header line, logic unchanged | the knowingly-indefeasible module stops being byte-identical to one that never hedged. **Visibility, not expressibility** — see §5, and it is the honest description |

---

## 3. ALTERNATIVES REJECTED BY NAME

### 3.1 A `disprefer` status — REJECTED

**(i) Grepped blast radius, and it is the failure a prior proposal caught.**
`resolve_runs/graph_v2/behavior_pilot/behavior_match.py:315` contains **exactly one status rule**:

```
conflict(S, A) :- does(B, A), asserts(S, forbid, A), behavior(B).
```

(`:314` is `relevant(S) :- asserts(S, _, _).`, status-blind; `:318` is `#show asserts/3`.) A fifth
status would be **silently ignored by behaviour matching**, which is the thing this corpus exists
to do. Further enumerations of the four, all grepped: `schema.py:50` `STATUSES`, `schema.py:434`
the `Literal`, `readback.py:73` `STATUS`, `translate_autofix.py:242`, `link.py:6-7` and `:517`,
`concept_map_probe.py:136`, `test_readback.py:335`, `seats.py:432` and the 4c presentation at
`seats.py:743`.

**(ii) The evidence says it is not needed.** `[MEASURED]` The Opus reference set resolved **all
five** of its inverted-modality edits with existing vocabulary — 3 with `forbid`
(`l1974_2125_n019`, `l1707_1973_n006`, `l4252_4482_n016`), 2 removed on independent
out-of-span grounds (`l2405_2473_n001`, `l1108_1367_n027`). The sixth encoding it produced,
`prefer minimize_redundant_phrases(R)`, is a positively-named avoidance act, and
`checks._AVOIDANCE_ACT` **already treats that as CORRECT** — added 2026-08-16 after the check
fired 3/3 on a module an adjudicator had just judged correct for applying that very remedy.

**(iii) Already rejected by name, on independent grounds.** `RECOMMENDATIONS.md` R40: *"Do not
'fix' this by adding a fifth `Status` … every downstream query, the closure semantics and `beats`
all assume the current four."*

**⭐ RECOMMENDATION ON THE POLE: CHANGE NOTHING.** The residue is real — `forbid` over-strengthens
*"should avoid"*, and PASS1 #23 says *"neither is clean."* But it is **VISIBLE**: the read-back
disagrees with the status, and that disagreement is what `checks.polarity_mismatches` reads.
Recall was measured at 4 of 5 real inversions before the 2026-08-16 widening, which was written
against the one miss. **A visible over-strength beats a silent one**, and the reference set
over-strengthening five soft directives is a cost paid in an artifact a reader can dispute.

### 3.2 A sign field on `prefer` (`polarity: +/-`) — REJECTED

It is `disprefer` with an extra step, and worse: the sign lives only in the JSON, so the rendered
`.lp` still says `asserts(C, prefer, A)` and every ASP consumer — `behavior_match.py`,
`link.py:534` (which reads `args[1]` as the status for the forbid-body scope check),
`readback_r3.py:187`'s xclingo program — reads an unmodified preference **for** the act. It moves
the defect out of the one artifact where it is currently visible. That is the shape of the
review list's own anti-rule (*"never make `status` and `read_back` agree by rewriting the
read-back"*), run in the other direction.

### 3.3 A two-act comparative form (`prefer A over B`) — REJECTED ON COST, NOT ON MERIT

This is the semantically right form for a comparative and would clean up `l1974_2125_n019` and
`l1707_1973_n006` as single paired items. **Grepped cost:** it makes `asserts` arity-4 for one
status, which breaks `behavior_match.py:314` (`relevant/1`), `:315` (`conflict/2`), `:318`
(`#show asserts/3`), `schema.render_lp:1306` (`%!show_trace {asserts(P,D,A)}`), `link.py:534`,
and every stored `.lp` under `runs/` and `resolve_runs/`. It also does not touch the top-ranked
failure. **Parked, named, with grounds; revisit only if the pole is reopened.**

### 3.4 A `defeasible: bool` flag alone — REJECTED as insufficient, and RETAINED as the fallback

A bool records that a default was dropped and leaves it dropped: the rule still fires
unconditionally, the corpus still concludes the stronger thing, and R57's measured inversion is
untouched. **It becomes the right answer if §5's pre-registered falsifier trips** — if almost no
hedge in the corpus names its own defeater, the `named` branch is unearned and this proposal
should shrink to exactly this bool.

### 3.5 Widening `toggleable` to non-`world` licences — REJECTED

The obvious cheap fix, and the one PASS1 #13 reaches for. `toggleable` is **the switch the
world-knowledge ablation flips**: `schema.Licensed`'s docstring, `test_schema.py:796–807` which
pins it, and `STEP_stage4.md:594` / `:898` which make *marked + toggleable* the deterministic
stand-in for the `world` licence at seat 4c. Overloading it would make an ablation that removes
world knowledge also remove every defeasible norm, and the two results would be
indistinguishable. Same objection the `ontology` block already rests on: two concepts on one
switch cannot be told apart.

### 3.6 Leaving defeasibility as-is — REJECTED, with the strongest measurement against it

Both routes are measured broken (§1). `[MEASURED]` 6 of 17 loop modules hedge; 1 of 17 encodes
any defeating condition. Route A inverts the default (R57). Route B leaves an `oblige`
byte-identical to one whose default was dropped (P7). There is no third option today, which is
R57's own conclusion: *"The schema has no third option, which is the honest underlying gap."*

### 3.7 Bundling R21 (`closure` licence) or R79 (vacuous closure on an obliged act) — NOT PROPOSED

Both are real and measured, at 1 instance each. Bundling them would make §5's byte-identity test
(B1) unable to attribute a diff to a cause. **Recorded as the next two candidates, in that
order.** Same ruling for R73, R80, R39, E-3 and E-4 — every one is a singleton.

---

## 4. BLAST RADIUS — GREPPED AND `[RAN]`, NOT REMEMBERED

Two claims could not be settled by reading and were settled by running them.

### 4.1 `[RAN]` A pydantic default is still REQUIRED on the wire

This is the migration mechanism and the whole proposal rests on it.

```
properties:      ['a', 'b', 'c']
pydantic required: ['a']
forced required:   ['a', 'b', 'c']
```

`json_schema()`'s `out["required"] = list(out["properties"])` (schema.py:1011) forces every
property required **regardless of a pydantic default**. So the two new fields are **mandatory for
the model on every call** — the `closure`-style forcing this repo insists on — while **892 stored
module JSONs still validate unchanged.** Verified against the live `Module` schema: the current
`Assertion` wire `required` is all 9 of its properties.

### 4.2 `[RAN]` A bare negated defeater on a variable act is refused by clingo

```
asserts(c, oblige, act(R)) :- not q(R).      -> error: unsafe variables in: ...
                                                note: 'R' is unsafe  (whole file refused)
asserts(c, oblige, act(R)) :- p(R), not q(R).
  with p(a). q(b).                           -> derives asserts(c,oblige,act(a))
```

The second line is the behaviour the field exists to produce: it **fires on `a`, about which the
case is silent**, and **does not fire on `b`, which the case defeats**. The first line is why
§2.1's third validator exists. `schema._check_head_bound` does **not** catch it today — its own
docstring admits the approximation (*"a head variable bound only inside `not …` may still be
unsafe for clingo"*), and I confirmed it passes `not q(R)` as a body.

### 4.3 Every consumer, enumerated

| consumer | grepped location | impact | must change? |
|---|---|---|---|
| `schema.Assertion` | `schema.py:424–449` | two fields + three validator arms | **YES** — §2.1 |
| `schema.Module._coherent` D4b scan | `schema.py:867–880` | a `defeater` name must be declared | **YES** — §2.2, reuses the existing message |
| `schema.render_lp` | `schema.py:1288–1295`, `:1249–1252` | conditions + header marker | **YES** — §2.3 |
| `schema.json_schema` | `schema.py:1011` | none — auto-forces required | no `[RAN]` §4.1 |
| `schema.STATUSES`, `Literal` | `schema.py:50`, `:434` | **untouched — no new status** | no |
| `schema.validate` / `validate_all` | `schema.py:1034`, `:1133` | none — no new `Licensed` field, corpus/citation loops unchanged | no |
| `schema.render_lp` trace directive | `schema.py:1306` `%!show_trace {asserts(P,D,A)}` | **arity 3 preserved** — this is why the defeater goes in the BODY | no |
| **`readback.py`** | `:689–698` renders each assert to the sentence a seat reads; `:73` `STATUS` | ⚠️ **must render the defeater and the `unnamed` marker.** Otherwise the sentence omits the module's own hedge and every seat is blind to it by construction — the exact defect shape of `reference_set/CRITERIA.md` §3.1 | **YES** |
| **`readback_r3.py`** | `:184–188` rebuilds `asserts(...) :- body` for the xclingo program | ⚠️ **must use the same conditions**, or the R3 program and the `.lp` disagree | **YES** |
| **`seats.py`** 4c presentation | `:743` `f"clause {cid} {item.status}s the act {item.act}"` + `", when {item.body}"` | same blindness as `readback.py` | **YES** |
| `checks.py` `polarity_mismatches` | `:319–363` | reads `status`/`act`/`read_back` only — unaffected. **A new check is not part of this proposal** | no |
| `checks.py` arity/schema checks | `:270–283` | operate on `ontology`/`requires`/`inputs` — unaffected | no |
| **`walkthrough/link.py`** | `_parse_atom` `:260`; forbid-body scope `:534` (`name == "asserts" and len(args) >= 2`) | **NO CHANGE.** The defeater renders into the body, so `asserts/3` is preserved. This is the single reason for that encoding choice | no |
| **`behavior_match.py`** | `:314` `relevant/1`, `:315` the ONE status rule, `:318` `#show asserts/3` | **NO CHANGE.** ⚠️ But the *semantics* of `conflict/2` genuinely move: a defeasible `forbid` now derives a conflict only where the case does not supply the defeater. **That is the intended change and §5 B7 is the test for it** | no (code) / **YES** (test) |
| `translate_autofix.py` | `:242` status regex over the four | unaffected | no |
| `eval.py:481`, `readback.py:763`, `translate.py:1533` | licence/citation iteration over all items | unaffected — no new `Licensed` field | no |
| **`prompt/20_worked_example.md`** | 4 `"status"` occurrences (grepped) | GOOD examples must carry the new keys or `test_prompt_examples.py` fails — it runs every GOOD example through `schema.validate` | **YES — guard-watched** |
| **`resolve_runs/graph_v2/node_worked_example.md`** | 4 `"status"` occurrences (grepped) | ⚠️ **this is the file the production corpus run actually uses.** `watch.json`'s own entry records that config assembles the system prompt from `00_task` + `10_output_format` + `node_worked_example` + `30_failure_modes`, and lists `20_worked_example.md` as unused. Missing it makes the change invisible to the live run | **YES — guard-watched** |
| **`prompt/10_output_format.md`** | `test_ssot_prompt_schema.ENFORCED` | SSOT-enforced: the field text must live in `schema.py` and the prompt may only POINT. The cross-field invariant (`status` ↔ `defeasibility` ↔ `defeater`) is explicitly permitted to live in the prompt by that file's own rules | **YES — guard-watched** |
| `prompt/00_task.md`, `prompt/30_failure_modes.md` | `test_ssot_prompt_schema.PENDING` | not SSOT-enforced, still guard-watched | probably |
| **`test_ssot_prompt_schema.py`** | `_N = 6` word n-gram | the two new descriptions must not share a 6-content-word run with any prompt sentence | **verify** |
| `test_prompt_examples.py` | GOOD/bad split on the `## The N bad ones` heading | the five bad examples must still fail | **verify** |
| **`fixtures.py`** | `assertion()` `:333`, `module()` `:86`, `module_json()` `:170`, `module_with_beat()` `:292`, `module_with_quantified_beat()` `:297` | one edit each. ⚠️ **`fixtures.py` deliberately imports nothing from the pipeline** (so `mutate_schema.py` can swap a mutated schema in before collection) — the values must be written out literally | **YES** |
| test files constructing asserts | grepped: `test_schema.py`, `test_checks.py`, `test_readback.py`, `test_readback_r3.py`, `test_seats.py`, `test_translate_autofix.py`, `test_stage4_node_plumbing.py` (60 `status=`/`"status":` sites repo-wide) | most route through `fixtures.py`; the rest need the defaults | **survey** |
| `mutate_schema.py` / `test_mutate.py` | anchors are source phrases re-verified before deletion (`:291`); a drifted anchor is a `MutationError` | three new `raise` sites are three new mutation anchors and must be registered | **YES** |
| `STEP_stage4.md:103` | documents `Assertion [act, body, cites, …]` | goes stale — documentation, not a test | note |
| **892 stored module JSONs** | `runs/` 30, `_debug_gen11/` 353, `resolve_runs/` 509 `[RAN]` | all still validate via the pydantic defaults `[RAN]` §4.1 | **no migration needed** |

**Registration, not documentation, fences a module.** Three new `raise` sites ⇒ three
`mutate_schema.py` anchors, same diff.

---

## 5. THE TEST — and this is the half that matters

We are unusually well supplied, and the strongest available test is that **we have concrete
recorded failures to express.** The pass criterion has two halves and **both are required**: a
test that only shows the new form is possible is not a test.

### HALF A — the recorded failures become expressible

Re-encode by hand (no API calls), then `schema.validate` → `checks.run_checks` → `render_lp` →
clingo ground/solve.

**⚠️ Per `CRITERIA.md` §3.6, the re-encoding must be BLIND-FIRST:** write the predicted
`defeasibility` value from the **narrowed span alone**, save the file, and only then open the
module. Reading order is not a preference; it is what made the reference set work.

| id | the recorded failure | target | PASS iff | FALSIFIED if |
|---|---|---|---|---|
| **A1** | `l2821_3040_n017` — knowingly indefeasible. Span: *"**By default**, the assistant should express uncertainty naturally, using conversational language."* | ⚠️ **`unnamed`, not `named`** — I read the span and it names **no** defeater | the `.lp` carries `%% indefeasible-default: asserts[0] express_uncertainty(A, E)`, the module's `claims` C1 hedge now has a formal counterpart, and the rendered sentence a seat reads says so | the marker does not reach `readback.py`'s sentence — then the change is invisible where it matters (B6) |
| **A2** | `l2474_2554_n004` — *"should not lie by commission … **unless** the user explicitly instructs"* | `named`, defeater `explicit_user_instruction(A)` | the rule **grounds**, **fires** on a case asserting only `third_party_interaction`/`on_behalf_of_user`, and **does not fire** on a case that adds the defeater | the defeater name has no substring anchor in the narrowed span (N10) ⇒ downgrade to `unnamed` |
| **A3** | `l1_170_n056` — *"should honor … **unless** they conflict"*. Already carries a NAF condition in a body today | `named`, and **the rendered `.lp` must be equivalent to today's** | the structural fact moves from an ad-hoc body literal into a declared field, with the `.lp` unchanged or trivially reordered | it is not equivalent — then the field is not a re-expression of a form that already works |
| **A4** | `l3041_3146_n006` (reference) — the Opus edit **coined** `contrary_indication_about_user_goals` and marked it *"ARGUABLE how to encode it"* | `unnamed` | the coined, unanchored name is **removed** and the hedge survives as a declaration | the reference adjudication is re-run and prefers the coinage |
| **A5** | the forced tautology `forbid X(R) :- X(R)` | **unchanged** | it still validates and still renders identically — this proposal must not disturb an anti-rule | any change to it |
| **A6** | the unattachable limit (R23 / R79 class) | **unchanged, and recorded as still unexpressible** | the proposal does not silently claim to fix it | — |

**⭐ THE PRE-REGISTERED FALSIFIER, and it is the one I most expect to trip.** Across the **9
hedged modules** in the two corpora (6 loop + 3 reference), I predict from the spans:
**~2 `named`, ~7 `unnamed`.** If **fewer than 2** hedged assertions can take `named` with a
span-anchored defeater, then the `named` branch is unearned, the field is a bookkeeping marker
only, and **the proposal must collapse to the `defeasible: bool` of §3.4.** Denominator 9. Say so.

I am stating the likely result up front: **for `l2821_3040_n017`, the module that motivated this,
the change buys VISIBILITY, not EXPRESSIBILITY.** That is a smaller claim than "the failure
becomes expressible" and it is the honest one.

### HALF B — nothing previously expressible becomes harder

| id | test | PASS criterion | cost |
|---|---|---|---|
| **B1** ⭐ | **Byte-identity round trip.** Re-validate all **892** stored module JSONs and re-render every one through `render_lp` | **892/892 validate, and every `.lp` is BYTE-IDENTICAL to today's.** Any diff on a module with `defeasibility="none"` is a regression, full stop | one script, seconds, $0 |
| **B2** | **Mutation survival.** `mutate_schema.py` + `test_mutate.py` | every existing anchor still caught; the three new `raise` sites registered and caught. **The catch rate must not fall** | existing tooling |
| **B3** | **Golden-set non-regression.** Re-score the 42-item anchored golden set | **UNCHANGED.** ⚠️ An *improvement* here is a **leak signature**, not a win — the golden set contains no defeasibility items, so there is nothing for this change to legitimately improve | existing tooling |
| **B4** | **Prompt-example gate.** `test_prompt_examples.py`, both worked-example files | the 4 GOOD examples in each of `20_worked_example.md` and `node_worked_example.md` validate; the five bad ones still fail | existing test |
| **B5** | **SSOT gate.** `test_ssot_prompt_schema.py` | passes at `_N = 6` — the new descriptions share no 6-content-word run with any prompt sentence | existing test |
| **B6** ⭐ | **Seat-visibility control.** Render every re-encoded module through `readback.py` and `seats.py:743` | every `defeasibility != "none"` assertion has its hedge **visible in the sentence the seat reads**. **FALSIFIED if the rendering is unchanged** — a field a seat is not shown is a defect it cannot see (`CRITERIA.md` §3.1), and the change should not ship | ~1 h |
| **B7** ⭐ | **Downstream reach.** For each `named` re-encoding, build two situations and run `behavior_match.py`: one omitting the defeater, one supplying it | `conflict/2` fires in the first and not the second. **FALSIFIED if `conflict/2` is identical in both** — then the field is inert in the only place the corpus is used | ~2 h |
| **B8** | **Turn-1 drafts as a difficulty control.** Re-read the 15 unaided turn-1 drafts and ask, per assert, whether the new field would have been answerable from the span | no assert becomes *harder* to state. ⚠️ **This is a judgment, not a measurement**, and I mark it as such | ~1 h |

**Total cost: one working day, $0.00, no API call.** The only judgment-bearing steps are the
~9 hand re-encodings (A1–A4) and B8; everything else is deterministic re-analysis of data on
disk. The re-encodings must be written blind-first and saved before any module is opened.

---

## 6. WHAT WOULD MAKE ME WITHDRAW THIS

1. **Half A's falsifier trips** (fewer than 2 of 9 hedged assertions take a span-anchored
   `named`) ⇒ collapse to the `defeasible: bool` of §3.4.
2. **B1 shows any byte diff** on a `none` module ⇒ the change is not additive and the proposal is
   wrong as written.
3. **B6 or B7 fails** ⇒ the field is recorded and unread, which is worse than the note in a
   lessons file it replaces, because it looks like a fix.
4. **B3 shows an improvement** on the golden set ⇒ a leak, and the cause must be found before
   anything else happens.

**And the standing alternative for every element in §1 except #1 is: change nothing.** That is the
recommendation for the negative pole (§3.1), for the forced tautology, for the `ontology`
two-forms split, and for all five singletons.
