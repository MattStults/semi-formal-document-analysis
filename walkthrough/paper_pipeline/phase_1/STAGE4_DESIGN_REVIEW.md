# Stage 4 — adversarial review of the DESIGN AS A WHOLE (2026-08-14)

Reviewer: clean-context adversarial pass over the four-seat layer as a *design*, not as a
diff. Prior passes reviewed pieces (the digit-index fallback, the id-disclosure bug, the
whitespace claims); the shape of the layer has never been attacked. Method: every claim
below was **RUN** against the real modules, the real corpus and the real price table, or is
marked `[READ]`. **No API call, no spend.** Suite state at review time: `test_seats.py +
test_stage4_node_plumbing.py + test_readback.py + test_readback_r3.py` = **359 passed**.

---

## VERDICT

**The four-blinding SKELETON is sound and should be kept. The EVIDENTIAL ACCOUNTING built
on top of it is not, and three things need a design decision — not a patch — before any
paid run larger than a pilot.**

Concretely:

* ✅ **Build the client factory.** Its specification is §C below and nothing in the seat
  design blocks it. The factory is not where the risk is.
* ⛔ **Do not run corpus-scale.** Two independent blocks: the tier contradiction (§7 of the
  plan mandates frontier until parity is measured; frontier at 750 modules is **$651
  worst / $87 likely**, against **$6.44 of ledger remaining**), and F1–F3 below, which
  determine what a paid run would actually be able to *claim*.
* ⚠️ **A pilot of ≤10 clauses at flash rates (~$0.05 worst) is the right next step**, and
  its purpose is to measure reply shapes and the `unclear` rate — **not** to produce
  faithfulness evidence, because today almost none of what it produces is countable (F1).

The single sentence: *stage 4 can currently ask four good questions and has no honest place
to write down the answers to three of them.*

---

## A. Findings, ranked by severity

### F1 — CRITICAL. The evidential output of a live run collapses to one seat, and that seat is not independent on half its items

Three mechanisms compound. Each is defensible alone; together they empty the stage.

**(a) RB4's `non-evidential` stamp is keyed on the CLAUSE MEAN and therefore never fires,
while the condition it exists for holds on 6.6 % of items.**
`readback.py:987` sets `non_evidential` from `clause_echo >= ECHO_LEVEL` (the *mean* over
items, `readback.py:869` + `statistics.fmean`), and `seats.stamp_evidential`
(`seats.py:968`) applies that single clause-level flag to *every* judgement of 4b and 4d.

`[RAN]` over the 12 stored modules that render (121 renderings, echo measured against the
real clause texts through `readback.clause_texts`):

| | |
|---|---:|
| renderings at per-item echo **≥ 0.90** (the declared level: *"the seats are comparing the clause to itself"*) | **8 (6.6 %)**, max 0.96 |
| clauses whose **mean** reaches 0.90 — the only thing that stamps | **0 of 12** |

So the eight items on which the design says 4b and 4d *cannot discriminate at all* are
recorded as fully evidential, and RB4's stamp fires on 0 % of the real corpus. The design
text (§2.4) says echo is *"reported per item and per clause"* — it is; the **stamp** is
per clause only, and that is the direction that over-credits.
*Concrete defective module:* a clause with one verbatim-echo concept (`broad_audience`,
measured 1.00) among seven freshly-worded ones. Mean 0.62 → no stamp → 4b's `faithful` on
the echoed item counts as evidence that the translation is faithful, which is exactly the
sentence §4.2 exists to forbid.

**(b) 3 of 12 stored modules already carry `readback-check-failed`,** which stamps
*everything* 4b and 4d say non-evidential (`seats.py:935`, RB1 fired 13 times over 12
modules). That is the correct behaviour — and it means a quarter of a paid run buys nothing
countable from two of the four seats before (a) is even considered.

**(c) 4d's only non-model cross-check cannot be wired.** `cross_check_4d`
(`seats.py:1015`) needs `discrimination` keyed on 4d's denominator ids, which are the
module's **claim sentences**; `probe.ClaimCoverage` (`probe.py:471`) is keyed on **claim
IDs** (`C1`, `C2`) *and* needs a `claims_map` (rule index → claim id) that nothing on disk
produces. `refuse_discrimination_join` (`seats.py:1303`) correctly refuses a total miss —
so passing stage 3's own object **refuses the whole report**, and passing `None` stamps
every `covered` as `unsupported`. Either way §4.3(3)'s *"the only place a seat verdict is
confirmed by something outside the seat system"* does not run. No adapter exists and none
is specified.

⇒ **Net.** After (a)–(c), the only unstamped, countable verdict in a live run is 4c's. And
F2 says 4c is not independent on 48 % of its items.

**What must change (design decision, not a patch):** stamp `evidential` **per judgement,
from the per-item echo**, not per clause; and either specify the claim-id↔sentence adapter
or state in the plan that 4d ships `unsupported`-only and say what that is worth. Do not
lower `ECHO_LEVEL` to make the stamp fire — that is a floor.

---

### F2 — CRITICAL. §6.2's premise — *"the only thing standing between 4b and 4c is the rendering"* — is FALSE for concept items, which are 48 % of 4c's denominator

`_item_text` (`seats.py:679`) presents a concept to 4c as
`the term \`X\` (arity n) means: <gloss>`; `readback.render_items` renders the same item to
4b as `«<gloss>»` — *the same string*. `[RAN]` on `m0092`:

```
concepts[0]   4c sees : the term `lower_level_content` (arity 1) means: content at a lower
                        level in the chain of command, including the assistant's own …
              4b sees : «content at a lower level in the chain of command, including the
                        assistant's own …»
```

`[RAN]` 4c's judgeable set over the stored corpus: **concepts 58, ontology 44, asserts 19**
— 48 % of what 4c judges is text 4b is shown verbatim.

Two consequences, both load-bearing:

1. **The instrument check (`instrument_defects`, `seats.py:1078`) is void on those items.**
   A 4b/4c disagreement about a concept is not evidence about the renderer; it is two seats
   given identical words and different questions. An `instrument-4b-4c` finding raised there
   routes a human to inspect a renderer that did nothing.
2. **The anchor does not anchor for the repo's own measured failure mode.** §4.1 claims 4c
   survives *"a mis-substituted gloss"* — true. It does not survive a gloss that is *wrong*,
   which is failure mode #4 measured in this repo at **7.5 %** (§0(5): 10 of 133 concepts
   add zero words beyond the predicate name). For `terrorism_act` → *"an act of terrorism"*,
   4b sees `«an act of terrorism»`, 4c sees `the term \`terrorism_act\` means: an act of
   terrorism`, both compare it to a clause that uses the word *terrorism*, and both pass.
   **Four seats, four passes, the design's own #4 defect.**

**What must change:** restrict the instrument check to items whose 4b text and 4c text are
not derived from one string (`asserts`/`ontology`-with-body), or record the item *kind* on
the defect so a human is not sent after a phantom. And stop describing 4c as unaffected by
the rendering — it is unaffected by the *renderer*, which is a smaller claim.

---

### F3 — HIGH. A layer-1 rendering cannot reach 4b or 4d: the totality ruling is defeated one level downstream

§2.3's amendment exists to stop the renderer being a gate on the logic: *"a construct nobody
has written a template for still reaches a seat, in layer-1 form."* It does not.
`_MODULE_PATTERNS` (`seats.py:308`) inherits `probe._DISCLOSURE`, which contains `:-`
(*"a rule from the module"*). A layer-1 span is `⟦ASP: … :- …⟧`. `[RAN]`:

```
build_4b_prompt("some clause", ("⟦ASP: «thing» :- «other»⟧",))
  -> DisclosureRefused: a rendering carries a rule from the module
```

`plan_clause` (`seats.py:1538`) builds all four prompts eagerly, so **one layer-1 rule
rendering refuses the entire clause — 4a, 4b, 4c and 4d together** — and it refuses it as a
*disclosure attack*, not as a fluency gap. The pressure the amendment removed from
`schema.py` reappears verbatim at the seat boundary: admitting an aggregate, a choice rule
or a conditional literal now requires a layer-2 template *or* the clause reaches no seat.

Latent today (`[RAN]` layer-1 fraction is **0/121** on the stored corpus) and live the
moment §2.3's twelve constructs are exercised — which is the whole point of admitting them.

**What must change:** the fence must distinguish *the module leaking in* from *the
renderer's own layer-1 output*. Either strip `⟦ASP:…⟧` spans before the module scan and
scan them under a rendering-specific rule, or exclude layer-1 items from 4b/4d's
denominator **by name and in the report** (the `no-derivation` precedent,
`seats.py:523`) rather than refusing the clause. Silently widening `_MODULE_PATTERNS` is
the wrong direction.

---

### F4 — HIGH. `judge` has no reply-shape hardening: five of seven realistic live replies raise an UNCAUGHT non-SeatError

`seats.py:1507` does `json.loads(raw)`, `data["judgements"]`, `r["item"]`, `r["verdict"]`
with no guard. `[RAN]` against the live seam:

| reply shape a live model produces | today |
|---|---|
| ```` ```json {...} ``` ```` (markdown fence) | **UNCAUGHT `JSONDecodeError`** |
| prose refusal (*"I cannot judge these without the program"*) | **UNCAUGHT `JSONDecodeError`** |
| reply truncated at the 4,096 cap | **UNCAUGHT `JSONDecodeError`** |
| top-level list instead of `{"judgements": …}` | **UNCAUGHT `TypeError`** |
| a row missing `"verdict"` | **UNCAUGHT `KeyError`** |
| `"Faithful"` (capitalised) | `NotAdjudicated` — whole clause lost |
| `"faithful."` (trailing period) | `NotAdjudicated` — whole clause lost |

Every mock in `test_seats.py` (`StubClient`, line 119) and
`test_stage4_node_plumbing.py` returns `json.dumps` of a well-formed dict, so **no test
exercises any row above**. A driver catching `SeatError` to record *"not adjudicated"* will
instead crash mid-run — after the money is spent and, without checkpointing, without the
raw reply on disk. The one live call ($0.0004) happened to return bare JSON; that is the
single data point.

The two `NotAdjudicated` rows are fail-closed and therefore acceptable in direction, but
they are *expensive*: one capitalised verdict discards a whole clause's four calls.
Normalising `verdict` to `strip().lower().rstrip(".")` against the closed set is parsing,
not floor-lowering — the closed set is unchanged and an unknown string still refuses by
name.

---

### F5 — HIGH. The coverage rule is enforced at the SEAM, never at the RECORD — and a zero-seat run routes identically to a clean pass

`validate_judgements` (`seats.py:898`) is called only from `judge`. `build_report` /
`validate_report` (`seats.py:1343`) never check judgements against denominators. `[RAN]`:

```
seats.build_report(cid, rb, {"4b": ()}, plan.denominators)   # 4c denominator: 16 items
  -> VALIDATES.  A report in which 16 items are unjudged and nothing says so.
```

And `run_clause` (`seats.py:1575`) silently skips any seat with no factory
(`if factory is None: continue`). `[RAN]` with `client_factories={}` on a real module:

```
routing = {'action': 'none', 'transcript': (), 'status': None}
```

— **byte-identical to the routing of a clause on which four seats found nothing wrong.**
`report_line` prints `4b=not-run`, so a human reading the line is safe; a driver keying on
`routing["action"]`, or any consumer reading `rep["seats"]`, is not. §5.3's *"a run failing
the coverage rule is NOT ADJUDICATED"* is true of a seat's reply and false of a stage-4
record.

*Concrete scenario:* the factory for 4c raises on a transport error, the driver logs and
continues, and the clause is written out with `routing: none` and three seats' verdicts.
Nothing in the artifact distinguishes it from a clean clause.

**What must change:** `validate_report` should require, for each seat present in
`denominators`, either a judgement set that covers it or an explicit `not_run` record with
a reason; and `route` must not return `none` when a denominator has no judgements.

---

### F6 — MEDIUM-HIGH. `allow_missing_citations=True` buys "an answer about nothing" with no stamp and no record

`build_4c_prompt` (`seats.py:787`) refuses an item whose cited clause text is empty —
*"asking whether an absent clause licenses an item buys an answer about nothing"* — unless
the caller passes `allow_missing_citations=True`, in which case the prompt prints
`(no text supplied)` and the item is judged anyway. `seats.survey` (`seats.py:1701`) passes
`True`, so it is the shape any factory driver will copy.

`[RAN]` **10 of 121** 4c-judgeable items across the stored modules have no cited clause
text. Nothing stamps those judgements, nothing counts them in the report, and 4c is the
seat F1 leaves as the only countable one. A `licensed` verdict on `(no text supplied)` is
uninterpretable and currently indistinguishable from a real one.

**Fix shape:** if the escape hatch stays, each such item's judgement must carry a
`no-cited-text` stamp (`Judgement.stamps` already exists) and the report a count — the same
discipline `echo-not-measured` already gets (`seats.py:935`).

---

### F7 — MEDIUM. 4d's prompt still shows the seat numbers that are not its ids

`build_4d_prompt` (`seats.py:835`) prints the claims as `  {c}` (unmarked) and the
sentences as `  {i}. {t}` — the *only* visible integers in the prompt — while 4d's brief
says `"item"` is *"the claim sentence itself, as listed"*. `_reply_item` (`seats.py:1470`)
correctly refuses a digit for 4d (the F1 fix of `consolidated_fix_review.md`), so the
failure is loud — but it is *predictable*: the READBACK_SMOKE live call showed a competent
model answering with the shape its prompt displayed, and 4d's prompt displays numbers next
to the wrong list. 4a and 4b were fixed by `_entry_lines` printing `[id]`; 4d was not.

Expect 4d to be un-adjudicable on its first live call, at full price. Bullet the sentences
(`  - {t}`) and bracket the claims, exactly as `_entry_lines` does.

---

### F8 — MEDIUM. `refuse_aggregate` has a key-name escape hatch at every depth

`_refused_strings` (`seats.py:1237`) skips value scanning under any key in
`_VERBATIM_VALUE_KEYS` (`seats.py:1226`) **anywhere in the tree**, and `build_report` ends
with `d.update(extra or {})`. `[RAN]`:

```
validate_report({… , "summary": {"item": "consensus: 4/4 agreed"}})   -> ACCEPTED
validate_report({… , "message": "4/4 seats agreed the module is faithful"}) -> ACCEPTED
validate_report({… , "reason": "consensus reached, 4/4 agreed"})     -> ACCEPTED
validate_report({… , "text": "unanimous agreement of all seats"})    -> ACCEPTED
```

(The two the test suite pins — a top-level `consensus` key and a nested `overall` value —
are correctly refused.) Test 20's standard is *"the route must not exist, not merely be
discouraged"*; the exemption is justified per-key but is applied by **name**, not by
**provenance**, so `extra=` can write an aggregate under a verbatim name. `extra` can also
overwrite `unclear_rate` and `seats` outright.

**Fix shape:** exempt values by *path* (`seats[*].reason`, `renderings[*].text`, …), not by
key name at arbitrary depth; and refuse an `extra` key that collides with
`REQUIRED_REPORT_KEYS`.

---

### F9 — MEDIUM (latent). §5.2's third branch is wired to nothing

`check_world_items` (`seats.py:648`) is called from **one test and nowhere else**
(`[RAN]` grep). `denominator_4c` drops `world` items from `judgeable`, `plan_clause` never
runs the deterministic check, and the report has no field for its result. A `world` item
therefore leaves no trace anywhere in a stage-4 record. Zero `world` items exist today, so
this is latent — but the branch was built specifically because *"retrofitting routing into
a brief that has already produced results invalidates those results"*, and a branch wired to
nothing has the same problem.

---

### F10 — MEDIUM (latent). R3 is unreachable from the live path

§2.1/§5.1 make the rendered set **R1 + R2 + R3**, and `denominator_4a` takes an `r3=`
argument (`seats.py:523`). `plan_clause` (`seats.py:1538`) has **no `r3` parameter**
(`[RAN]` confirmed on the signature) and calls `denominator_4a(rb)` — so every live 4a/4b/4d
denominator is R1+R2 only, permanently stamped `r3-not-supplied`. Worse, supplying it would
break: `plan_clause` builds its material from `text_by_item = {r.item: r.text for r in
rb.renderings}` and would `KeyError` on the situation ids R3 contributes.

So the derivation renderings — the layer §3b's `m0255` worked case is *about* — reach no
seat, and the three R3 tests (`test_seats.py:1595`) exercise `denominator_4a` directly,
never the seam. This is the same class of defect the R3 fixture comment already warns
about: a wiring that is a no-op against every object the repo builds.

---

### F11 — MEDIUM. Fence false positives make ordinary spec English unjudgeable, and the refusal misnames the cause

`[RAN]` over all **593** corpus clause texts through `readback.clause_texts`, scanned with
`_MODULE_PATTERNS + _UNIVERSAL_PATTERNS`: **3 clauses (0.5 %) would refuse their own 4b/4d
prompt**.

* `m0067` — *"…difficult or **impossible** to reverse (e.g., sending an email…)"* →
  matched as **"a stage-3 expected verdict"** (`probe.LABELS` contains `impossible`).
* `m0009` — a CC-0 URL containing `…/chooser-v1` → matched as **"a coined predicate
  signature"**.
* `[RAN]` synthetic control: a clause containing the ordinary word **"closure"** is refused
  as *"the closure declaration"*.

Fail-closed, so nothing wrong enters the record — but the clause reaches **no seat at all**
(`plan_clause` builds all four eagerly), and the message tells a debugging human that the
document leaked an answer key. At 750 modules that is ~4 clauses silently dropped under a
misleading diagnosis. The `LABELS` and `closure` patterns need word-boundary context that
distinguishes a stage-3 artifact from English prose, or the scan must be applied to
*rendered/module-derived* text only and not to the document's own words.

---

### F12 — LOW-MEDIUM (latent). 4d's claims bypass the module fence

`build_4d_prompt` scans renderings with `_UNIVERSAL_PATTERNS + _MODULE_PATTERNS` but scans
claims with `_UNIVERSAL_PATTERNS` only (`seats.py:835`). `[RAN]`:

```
build_4d_prompt(clause, ("«a rendering»",),
                ("C1 asserts(m0217, permit, produce(M)) :- political_content/1 holds",))
  -> ACCEPTED, and the rule is printed to 4d
```

Claims are model-authored free text, so this is a live route by which 4d — a seat that must
not see the logic — is shown it. `[RAN]` **0 of 261** stored claims currently trip a module
pattern, so it is latent, not live. One line: run `_MODULE_PATTERNS` over claims too.

---

### F13 — LOW. `_refuse` scans the *inputs*, never the assembled prompt

Every builder validates its text arguments and then concatenates ids, headings and
`(no text supplied)` placeholders **after** the scan. Nothing re-scans the final string, and
`judge` sends whatever it is handed. This matters mainly as the hole the client factory
must not widen — see §C.

---

## B. Are the four blindings the right four?

### What each seat uniquely catches

| seat | a defective module ONLY it catches | is it really unique? |
|---|---|---|
| **4c** | the design's own n=1: a translation of *"policies other than restricted or sensitive"* that invents `defines(m, policy_class, deception)`. The rendering is fluent and the clause supports "other policies" in the abstract; only *"does the cited clause introduce `deception`?"* fires. | ✅ **genuinely unique.** #1 and #6 have no other route. |
| **4b** | a *composed* rule whose parts are each licensed and whose combination is not — `asserts(m, permit, produce)` with body `political_content ∧ broad_audience` where the clause permits it only *subject to review*. 4c sees this as `clause m permits the act produce(M), when political_content(M), broad_audience(M)` — **raw predicate names**, from which the composed meaning is not readable. | ✅ unique, but only on the **19 of 121** `asserts` items; on `concepts` it duplicates 4c (F2). |
| **4d** | a clause with four claims of which the module encodes three. Every rendered sentence is faithful (4b passes), every item is licensed (4c passes), the author meant it (4a passes). Only the completeness question fires. | ✅ unique — **within the limits of §B2 below.** |
| **4a** | the mechanical rendering diverges from author intent: `_act_span` prints `⟨act produce(M)⟩` where the author meant *publish externally*. No other seat knows the intent. | ⚠️ **unique but structurally uncountable** — §4.3(2) puts 4a in `advisory`, `route` gives it no route (`seats.py:258`), and its findings are undisclosable. Its unique catches are, by construction, evidence of nothing. |

**Is any seat redundant?** 4a is the candidate, and the honest answer is *not redundant,
but not evidential either*: it costs one of four calls and carries the largest prompt (the
whole module JSON). If the budget binds — and §7 says it does at corpus scale — 4a is the
first call to drop, and keeping it must be argued on its value to a **human triager**, not
on detection. Recommend the plan say so explicitly rather than leaving the cost implicit.
4b is not redundant, but F2 means **half its work is duplicated by 4c**, and that half is
where the instrument check is void.

### B2 — the defect classes NONE of the four catches

These are all *faithful, complete, correctly cited and still wrong* modules.

1. ⭐ **UNDER-READING THE CLAUSE — the biggest one, and it is structural.** 4d's
   denominator is `mod.claims` (`denominator_4d`, `seats.py:616`): *the translator's own
   list of what it read out of the clause*. A claim the translator never wrote down is in
   no denominator, so 4d asks *"did you encode what you said you read?"*, never *"did you
   read what the clause says?"*. A translator that reads three claims out of a five-claim
   clause and encodes all three passes **all four seats unanimously**. §1's table credits
   4d with #12 (*one branch only*); it earns that only relative to the claims list.
   No seat is denominated on the *clause*.
2. **The act functor.** `_act_span` (`readback.py:618`) renders an act as itself —
   `⟨act produce(M)⟩` — because no schema field glosses an act; RB1 exempts it by name and a
   `readback-act-literal` **note** fires. `[RAN]` that note fired **19 times over 12
   modules**, i.e. on essentially every `asserts` item there is. A note that fires on
   everything is invisible — this repo's own recorded lesson (`link.py`, the
   `no %% provides:` warning). So an act named `produce` that the module uses to mean
   *publish* is unfalsifiable at every seat: 4b sees a bare token, 4c sees the same token,
   4d cannot tell, 4a wrote it.
3. **Quantification and scope.** Layer 2 renders a body as a gloss chain joined by *and*
   (`readback.render_body`); nothing renders a quantifier. `p(X) :- q(X)` and a rule that
   should have been existential or bounded render identically for a seat's purposes. A
   variable-vs-constant scope error is visible only in 4c's raw-body item text, where the
   question asked is *"does the cited clause contain this?"* — not *"does it mean this?"*.
4. **Modal strength.** `readback.STATUS` is a fixed four-entry table; the renderer can say
   *forbids/permits* and nothing between. A clause reading *"the assistant should generally
   avoid"* rendered as *"clause m forbids …"* gives every seat a sentence that cannot
   express the gradation, so no seat can report the gradation lost. RB3 counts negation
   markers; nothing counts modality.
5. **#5 hollow stub** — admitted in the plan (§1) and correctly not claimed.

⇒ **The four blindings are the right four axes** (own-work / rendering-only / source-only /
completeness). The gap is not a missing *fifth blinding* — it is that (1) is a missing
**denominator**: completeness is measured against the translator's reading, not the
document. Closing it needs a claims list produced independently of the translator, which is
a stage-1/stage-5 question, not a stage-4 one. **The plan should say this in §1's table
rather than letting 4d read as clause-completeness.**

---

## C. The client factory — specification

`seats.judge` refuses without a `client_factory` (`seats.py:1507`) and none exists: every
one in the repo is a test stub, and the one live call used a scratchpad synthesis
(`READBACK_SMOKE.md`, syntheses 2–4). This is the deliverable.

### C1 — Signature, and why this one

```python
def seat_client_factory(seat: str, config_path: str, *, ledger, run_dir: str):
    """seat name + config -> a zero-arg callable returning a transport.

    ⛔ The ONLY inputs are the SEAT NAME and configuration. Not the module, not
       the readback, not the plan, not the rendering, not the clause.
    """
```

**Why the natural implementation destroys 4c.** The obvious factory is
`make_factory(plan, seat)` or `make_factory(rb, seat)` — you want the readback to size
`max_tokens`, to key a cache on `rendering_sha`, or to write a per-clause log. Every one of
those puts **the rendering into lexical scope at 4c's call site**, and 4c's entire anchor
property is enforced by the *absence of a parameter* (`build_4c_prompt`, `seats.py:787`).
Once the rendering is in scope there is no fence left to cross: `_refuse` runs at **prompt
construction** over the item texts (F13), so anything the transport adds to the `messages`
list afterwards — a context preamble, a few-shot example, a retry turn quoting the sentence,
a "here is what the rendering said" clarification — is **never scanned by anything**. The
absence of a parameter is the whole mechanism; a factory that takes the plan reintroduces
the parameter one frame down, where no test looks.

### C2 — MUST

1. **Build a transport, never a prompt.** `plan_clause` is the only prompt source. The
   returned object exposes exactly `complete_messages(system, messages) -> str` and sends
   `system` and `messages` unmodified. It appends nothing, prepends nothing, and adds no
   system text of its own — `BRIEFS[seat]` is the entire system prompt.
2. **Resolve the provider from config** (`translate.resolve_provider` + `translate.Client`
   over a stage-4 config), with `max_tokens = seats.SEAT_MAX_TOKENS` and
   `format_forcing: json_schema → json_object`. The config's `json_schema` is the **stage-1
   module schema**; forcing it on a seat reply mangles it (measured in the smoke).
3. **Adapt the envelope to text.** `translate.Client.complete_messages` returns an envelope
   dict; `judge` expects text. Three lines, and it must record the raw text before parsing.
4. **Check the ledger BEFORE each call** against `spend.py`'s ceiling, using the *worst*
   case (`estimate_clause_usd`, every reply at the cap), and refuse rather than truncate.
   An unpriced provider counts as over budget (`seats.py:1626` already rules this).
5. **Append a call record before adjudication**, per call, to `run_dir`: seat, provider
   name, model id, price, `brief_sha(seat)`, `rendering_sha(rb)`, sha of the prompt, raw
   reply, usage, wall time. A `NotAdjudicated` run must still have its money accounted and
   its reply re-readable — F4 says the crash cases lose exactly this today.
6. **Retry only on TRANSPORT failure, with a byte-identical prompt.** Bounded (2), with
   backoff.
7. **Be per-seat idempotent**: key the checkpoint on `(clause_id, seat, prompt_sha)` so a
   resumed run never re-pays for an adjudicated seat. `resolve_runs/graph_v2/
   run_checkpoint.py` already exists — reuse it, do not write a second one.

### C3 — MUST NOT

1. **Must not accept a module, readback, plan, rendering or clause parameter** — C1.
2. **Must not retry by re-prompting with the refusal message.** `validate_judgements`'
   text names the denominator ids and which were missing (`seats.py:898`); handing that
   back to a seat teaches it the answer-key shape and, for 4d, discloses the claim list. A
   failed adjudication is a **new clean call or nothing**, on §5.6's own logic (*zero bits
   carried*).
3. **Must not vary the brief, temperature, or tier per clause.** A brief sha that changes
   mid-run makes the instrument record (`InstrumentDefect.brief_shas`) meaningless. Tier is
   a run-level decision recorded once.
4. **Must not enable tools, web access, or any retrieval.** A seat that can look up the
   spec is not blinded.
5. **Must not default a provider or a price**, and must not fall back to a literal
   (`most_expensive_provider`, `seats.py:1667`, already rules this for the price table).
6. **Must not swallow an exception into a verdict.** A transport failure is a recorded
   `not_run`, never an `unclear`.

### C4 — Two changes to `seats.py` the factory needs and must not work around

* **`judge` must parse defensively** (F4): strip markdown fences, accept `{"judgements":
  […]}` or a bare list, normalise `verdict` to `strip().lower().rstrip(".")` against the
  closed set, and raise `SeatError` — never `KeyError`/`JSONDecodeError`/`TypeError` — on
  anything else. The closed set does not change; an unknown verdict still refuses by name.
* **`run_clause` must record a skipped seat** (F5) instead of `continue`, and `route` must
  not return `none` when a denominator has no judgements.

Both belong in `seats.py`, not in the factory. A factory that pre-cleans replies is a
second, laxer adjudicator living outside the module the tests fence.

---

## D. Mock-vs-live inventory

The one live call ($0.0004) exposed a bug every mock hid. What the mocks still assume:

| mock assumption | where | a live model may instead | pin that would fail to catch it |
|---|---|---|---|
| reply is bare JSON | `StubClient`, `test_seats.py:119` | ```` ```json … ``` ```` fence | every `judge` test — all pass, F4 crashes |
| `{"judgements": [...]}` envelope | same | bare list, or `{"results": …}` | none |
| every row has `verdict` and `reason` | same | omits `reason` on an obvious item | `test_17_an_empty_reason…` pins empty, not **absent** (absent → `KeyError`) |
| verdict is exactly the closed lowercase string | same | `"Faithful"`, `"faithful."`, `"FAITHFUL"` | `test_17_a_verdict_outside_the_closed_set` pins the refusal, not the cost |
| the seat names the id the prompt displays | `test_stage4_node_plumbing.py:131` | **4d has no displayed ids** (F7) | the node-plumbing pins cover 4a/4b/4c ids; 4d's pin uses the claim sentence, which its prompt does not mark |
| reply fits in 4,096 tokens | `SEAT_MAX_TOKENS` | 18-item 4c batch × verbose reasons truncates | no test builds a reply near the cap |
| judgements arrive in denominator order | all | shuffled | `validate_judgements` is order-free ✅ — genuinely safe |
| the model answers at all | all | *"I can't judge this without seeing the program"* — the shape 4b's own brief invites | none; parses as `JSONDecodeError` |
| no duplicate/near-duplicate ids | all | echoes an id twice with different verdicts | `test_17_a_duplicate…` ✅ covered |

The pilot's purpose is to fill this table with measurements, not to produce verdicts.

---

## E. Cost and scale at ~750 modules × 4 seats

`[RAN]` `seats.py --cost` over the 12 stored modules that reach a seat (41 tried; **27 are
stage-2-invalid** and 2 halt at `readback-ungloss`):

| | per clause | × 750 |
|---|---:|---:|
| flash (0.14/0.28), **worst** (every reply at the 4,096 cap) | $0.0053 | **$3.98** |
| flash, likely (40 out-tok/judgement) | $0.0011 | $0.83 |
| frontier (`fable`, 10/50), **worst** | $0.8683 | **$651** |
| frontier, likely | $0.1162 | **$87** |

Against `spend.py`: **$2.057 of $8.50 used ⇒ $6.44 remaining.**

**The tier contradiction is the headline.** §7 rules that the first run uses a *frontier*
tier on 4b/4c/4d because the seats are unvalidated, and that the small-model parity run is
what would license dropping it. Frontier at corpus scale is **13× the remaining ledger at
the likely rate and 100× at the worst**. Flash worst-case fits ($3.98) but consumes **62 %
of everything left**, with no repair turn budgeted and no re-translation term
(`estimate_clause_usd` prices none — §5.6 re-translations are a *stage-1* cost on top).

⇒ **The parity measurement is a precondition for corpus scale, not an optimisation**, and
the plan should say so as a gate rather than as a preference.

**Batching and per-seat blowup.**
* **4c batches per clause** (correct) but its *output* grows linearly with item count: the
  largest stored module has **17 items / 18 renderings**. At a verbose 200 tok/judgement
  that is ~3,400 tokens against a 4,096 cap — inside it, with no headroom. A truncated 4c
  reply is unparseable (F4), unrecoverable, and paid for. **Split 4c into ≤12-item batches
  ordered by id, then validate the concatenated judgements against the FULL denominator** —
  `validate_judgements` is already parameterised and needs no change.
* **4d is per clause, not per claim** ✅ no blowup.
* **4a carries the whole module JSON** and is the largest single input, for the one seat
  whose output is never evidence (§B).

**Checkpointing (required, not optional).** Per `(clause_id, seat, prompt_sha)`, written
*before* adjudication, so that (i) an F4 crash does not lose a paid reply, (ii) a resumed
run re-pays for nothing, (iii) the ledger reconciles against call records rather than
against successful adjudications. A run that spends and cannot say what it bought is the
one failure a hard cap cannot survive.

---

## F. What to do, in order

1. **F4** (harden `judge`) and **F7** (4d's displayed ids) — small, mechanical, and both
   are certain to fire on the first live call.
2. **F5** (coverage at the record) and **F6** (`no-cited-text` stamp) — both are
   silent-pass routes and both are cheap.
3. **F1** and **F2** — the two that need a *ruling*, not a patch: per-item evidential
   stamping, the claim-id adapter (or an honest statement that 4d ships `unsupported`), and
   what the instrument check may claim on concept items.
4. **F3** — decide before any construct outside the layer-2 table is admitted.
5. Then the factory (§C), then a **≤10-clause flash pilot** whose stated deliverable is §D's
   table and the `unclear` rate split by length — **not** a faithfulness result.
6. Corpus scale stays blocked on the small-model parity run (§E).

**Nothing in this review is a reason to lower a floor.** `ECHO_LEVEL`, the closed verdict
sets, `readback-ungloss` and RB5 should all be left exactly where they are; every fix above
either moves a stamp to a finer grain, makes a silent path loud, or refuses earlier.
