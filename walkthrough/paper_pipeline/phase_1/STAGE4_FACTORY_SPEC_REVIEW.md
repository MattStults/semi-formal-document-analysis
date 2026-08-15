# Adversarial review of the CLIENT FACTORY SPEC (§C of `STAGE4_DESIGN_REVIEW.md`)

Reviewer: clean-context adversarial pass over §C as a *specification*, before it is built.
§C is itself the output of an adversarial reviewer and has never been attacked. Method:
every claim below is `[RAN]` against the real modules, the real corpus, the real price
table and the real transport, or is marked `[READ]`. **No API call, no spend. No
implementation written.** Nothing under `runs/` or `translation_sample/runs/` touched;
`seats.py` not modified.

---

## VERDICT

**SOUND WITH AMENDMENTS — but the amendments are not cosmetic, and one of them reverses
the spec's central architectural move.**

* The spec's **mechanism** claim is TRUE and was reproduced (§1 below): nothing in
  `seats.py` scans what a transport puts on the wire.
* The spec's **justification** ("the absence of a parameter is the whole mechanism") is
  **overstated**, and the **remedy it derives from it — a restricted factory signature —
  does not work.** `[RAN]` A factory taking *exactly* the spec's arguments
  (`seat, config_path, *, ledger, run_dir`), violating no MUST and no MUST-NOT, puts the
  full read-back in front of 4c verbatim, renderer marks intact, and nothing refuses (§3).
  A signature fence cannot close a hole whose location is the wire.
* Three MUSTs are **internally contradictory or unbuildable as written**: MUST 5 requires
  an argument MUST-NOT 1 forbids (§4); MUST 7 names a module that does not do what it is
  said to do (§5); MUST 2's transport violates MUST 1 and MUST 6 by construction (§6).
* MUST 2 and `STEP_stage4.md` §7 are **jointly unsatisfiable**: the mandated frontier tier
  is not reachable through the mandated client (§7).
* MUST 4's budget fence reads a ledger that **structurally cannot see this stage's spend**
  (§8).

Ten amendments are listed in §14 and the corrected §C is written out in full in §15.

**Build order (§13): build the factory NOW, offline. Do not let it make a call until
A1–A4 land. F1/F2/F3 do not gate a reply-shape pilot; they gate any run that claims a
faithfulness number.**

---

## 1. Is the central claim TRUE? — the MECHANISM is true, traced in code

The spec (§C1) claims: a factory holding the plan/readback puts the rendering in lexical
scope at 4c's call site, and `_refuse` cannot catch what the transport appends because it
runs at prompt-construction time only.

**Traced.** `_refuse` (`seats.py:340`) has exactly nine call sites, `[RAN]` grep:

```
seats.py:748  build_4a_prompt   seats.py:774,775  build_4b_prompt
seats.py:811,812,813,815  build_4c_prompt      seats.py:861,862,864  build_4d_prompt
```

All nine are inside the four builders. `judge` (`seats.py:1507`) then does:

```python
client = client_factory()
raw = client.complete_messages(BRIEFS[seat],
                               [{"role": "user", "content": prompt}])
```

The list literal is handed to an object the caller supplied and is never read again.
`run_clause` (`seats.py:1575`) inspects only the returned judgements. There is no
post-construction scan anywhere in the module. **F13 of the parent review is correct and
the spec's reading of it is correct.**

`[RAN]` demonstration, `m0037`'s real plan, a transport that appends one turn:

```
messages the transport actually sent to 4c: 2 turns
extra turn: "for context, the rendering said: …"
raised: nothing.  judged: nothing refused.
```

⇒ **The mechanism claim survives. A seat prompt is a *suggestion* to the transport today.**

### 1b. But the JUSTIFICATION is overstated, in two ways that matter

**(i) "the absence of a parameter is the whole mechanism" is false today, before any
factory exists.** `plan_clause` (`seats.py:1538-1560`) already holds the readback in
lexical scope and builds `text_by_item = {r.item: r.text for r in rb.renderings}` **four
lines above** the `build_4c_prompt(items, …)` call. The rendering has always been in scope
at 4c's construction site. What actually keeps it out of 4c's prompt is two *content*
mechanisms, not a signature:

* `source_items` / `_item_text` (`seats.py:679, 698`) build 4c's material out of the
  module and `corpus_texts` — never out of `rb`;
* `build_4c_prompt` scans `it.text` and `it.cited_text` with `_RENDERING_PATTERNS`
  (`seats.py:812, 815`), which is a real content check with a real test
  (`test_seats.py:429`, *"a rendering smuggled through 4c's item text is refused"*).

The signature check that the spec leans on is `test_seats.py:419`, and it is a **name
scan** of `inspect.signature(build_4c_prompt).parameters` for the substrings `render` /
`readback`. Its docstring says *"the refusal is structural: there is no slot."* It is not
structural; it is a naming convention, and it says nothing whatever about the transport.

**(ii) The spec's own document refutes the anchor's strength one section earlier.** F2
(`STAGE4_DESIGN_REVIEW.md:89`) proves 48 % of 4c's judgeable items are shown *the same
words 4b sees*. `[RAN]`, independently reproduced over all 12 rendering modules:

```
4c items whose text CONTAINS 4b's rendering verbatim: 58/121 = 48%
```

So a spec section whose entire rationale is *"4c must never be shown what 4b is shown"* is
written in the same document that measures 4c already being shown it, verbatim, on half its
denominator. That is not a reason to abandon the fence — it is a reason to stop justifying
the fence with a property the repo has measured as half-lost, and to justify it instead by
what it does buy: **4c is not downstream of the RENDERER** (the parent review's own
correction at line 122 says exactly this, and §C ignores it).

**Finding 1 (MAJOR, justification).** §C1's prose must be rewritten to claim the smaller,
true property. A spec justified by *"4c cannot see the rendering"* will be implemented by
someone who believes that is currently true, and who will therefore trust the signature
fence instead of the wire fence. **A false premise in a security-shaped spec is worse than
no spec — the parent review's own words.**

---

## 2. Is the spec SUFFICIENT to build from? — no. Twelve open decisions, four break properties

An implementer handed §C must invent all of the following. `⛔` = a wrong choice breaks a
seat property; `⚠️` = a wrong choice costs money or correctness recoverably; `·` = merely
inefficient.

| # | decision §C leaves open | severity |
|---|---|---|
| 1 | **Provider selection args.** `translate.resolve_provider(cfg, args)` (`translate.py:418`) reads `args.provider`, `args.model`, `args.max_tokens` off a namespace §C never describes. `--provider` *reroutes* and drops the inline identity (`_IDENTITY_KEYS`). Getting this wrong attributes spend to a provider that was never called — the exact bug that docstring records. | ⚠️ |
| 2 | **Which config.** `config.json`'s `format_forcing` defaults to `json_schema` and `schema.response_format` is the **stage-1 module schema** (`translate.py:579`). §C says force `json_object` but does not say the stage-4 config is a *separate file*; editing `config.json` in place changes stage 1. | ⛔ (a mangled reply is an un-adjudicated paid call) |
| 3 | **Per-seat tier.** `STEP_stage4.md` §7 requires frontier on 4b/4c/4d and **the translator's own model on 4a**. §C3.3 says *"tier is a run-level decision"*. These read as contradictory; per-**seat** tier fixed for the run is what is meant, and it must be said. | ⛔ (4a on a frontier tier is not "the author") |
| 4 | **`max_tokens` wiring.** §C2 says `max_tokens = SEAT_MAX_TOKENS`, but `Client._body` reads `self.p.max_tokens` (`translate.py:574`) — it must arrive via `cfg["model"]["max_tokens"]` or `args.max_tokens`, never by setting an attribute post-hoc. providers.json rows all carry `16384`. | ⚠️ (4× the priced worst case) |
| 5 | **Temperature.** Unspecified; `resolve_provider` defaults `0.2`. A varying temperature makes the instrument record's *"the brief was under-informative"* rule-out un-runnable. | ⛔ |
| 6 | **Truncation vs transport failure.** `_check_envelope` (`translate.py:848`) **raises `ProviderError` on truncation**, the same class as an HTTP failure. §C2.6 says *retry on transport failure*. A truncated 4c batch would therefore be silently re-paid. See §9. | ⛔ + ⚠️ |
| 7 | **Resume semantics.** §C2.7 says *key the checkpoint*; it never says what resume DOES. Replaying a stored reply requires a transport that returns disk contents — the most leak-prone object in the design — and re-adjudicating a reply whose brief_sha has since changed is a silent floor breach. | ⛔ |
| 8 | **Call-record schema and location.** §C2.5 lists fields but not the file, the format, the write-ordering against the ledger append, or what happens when the record write fails after the call succeeded. | ⚠️ |
| 9 | **Failure semantics at the clause level.** §C3.6 says a transport failure is a recorded `not_run`, but `run_clause` has no `not_run` concept — that is F5's fix, and §C4 assigns only the `continue` half of it. Who writes `not_run` when `judge` *raises*? | ⛔ (F5's silent-pass route) |
| 10 | **Concurrency.** Unspecified. `translate.Client` carries mutable `_failed_body_hashes`, `spent_usd`, `calls`; a shared client across threads races the measured-spend ceiling. | ⚠️ |
| 11 | **4c batching.** §E requires ≤12-item batches; §C2.1 forbids the factory building prompts and `plan_clause` builds `prompts["4c"]` as one string. Nobody is assigned the change. See §11. | ⚠️ |
| 12 | **Ledger identity.** Which usage log; whether `model.usage_log` is on; whether the row is priced. See §8. | ⛔ |

**The four that break properties: 2, 5, 7, 9** (plus 3, 6, 12 which break a rule or a
budget rather than a seat property). Every one of them is invisible in a §C-conformant
implementation.

---

## 3. Does the MUST-NOT list cover the ways the anchor can be lost? — NO. Demonstrated counterexample

`[RAN]` — a factory with **exactly the spec's signature**, taking no module, readback,
plan, rendering or clause; building no prompt; varying no brief; enabling no tools;
swallowing no exception; not retrying; not defaulting a price. It satisfies C1, C2.1,
C3.1–C3.6 as written.

```python
class SpecCompliantLeak:
    def __init__(self, seat, config_path, *, ledger, run_dir):
        self.seat, self.run_dir = seat, run_dir
    def complete_messages(self, system, messages):
        # the innocent motivation §C itself names: "size max_tokens from the artifact"
        for path in sorted(glob.glob(os.path.join(self.run_dir, "*", "m*.json"))):
            mod = schema.validate(json.load(open(path)))
            rb  = readback.render_module(mod, clause_quote=quotes.get(mod.clause_id))
            ...
        return send(messages + [{"role": "user",
                                 "content": "Context from the read-back:\n" + …}])
```

Output actually placed in front of seat 4c:

```
Context from the read-back:
«a rule set by OpenAI that can be transmitted or overridden through system messages,
 but cannot be overridden by developers or users»
«the rule is set by OpenAI»
«the rule can be transmitted through system messages»
```

Full glosses, `«…»` marks intact — the exact strings `_RENDERING_PATTERNS`
(`seats.py:336`) exists to refuse — delivered past every fence in the module.

**Finding 2 (CRITICAL).** `run_dir` is a **capability**, not a scalar. Any factory that can
name the run directory can reconstruct every rendering in the corpus. `config_path` is the
same capability at one remove (a config names a run dir). **The MUST-NOT list fences the
call signature; the hole is at the wire. Restricting arguments is therefore necessary but
not remotely sufficient, and by itself it is a fence a reviewer will mistake for a
guarantee.**

Other routes checked, for completeness:

* **`corpus_texts` / `cited_text`** — closed. `build_4c_prompt` scans `cited_text` with
  `_RENDERING_PATTERNS` *and* `_UNIVERSAL_PATTERNS` (`seats.py:813-816`). Not a route.
* **Gloss tables** — not a *route*, but it is the F2 identity: 4c's concept text already
  *is* 4b's rendering minus the marks. No factory needed. Already open, 48 % `[RAN]`.
* **A shared client across seats** — nothing in §C forbids it, and `translate.Client`
  carries `_failed_body_hashes` (`translate.py:567`) and `spent_usd` across calls. A 4b
  failure therefore mutates a later 4c request (§6). Cross-seat state is real and
  unfenced.
* **A logging hook reading the caller's frame** — `sys._getframe(1).f_locals` inside
  `complete_messages` reaches `judge`'s frame (`prompt`, `denominator_ids`) and two frames
  up reaches `run_clause`'s `plan`, hence `plan.readback`. No argument required at all.
  This is a strictly stronger version of Finding 2 and is likewise unfenced.
* **A cache keyed on rendering content** — a *sha* key is one-way and harmless; a cache
  that stores prompt **text** under `run_dir` and is read by a later seat's transport is
  the replay hole of open decision 7.
* **Retries reusing a mutated message list** — real, and it is `_vary_identical_retry`
  (§6), which mutates the final user turn in place on the retry path.
* **The `judge` signature itself** — `judge(seat, prompt, denominator_ids,
  client_factory)` passes the prompt *as data*. The transport is trusted to send it. There
  is no return-path evidence of what was sent. This is the root cause and §15's A1 closes
  it.

⇒ **Amendment A1 (the reversal): the fence must move from the signature to the wire.**
`judge` must (a) re-scan the assembled outbound payload with the seat's own pattern set
before the call, and (b) require the transport to report the sha256 of the bytes it
actually sent and refuse if it differs from the sha of what `judge` handed it. That turns
an unverifiable MUST-NOT into a checkable invariant, and it closes F13 at the same time.
A closure-inspection test (`factory.__closure__` may hold only `str`/`int`/`None`) is
worth having as a lint, but it is a lint, not the fence.

---

## 4. MUST 5 requires an argument MUST-NOT 1 forbids

§C2.5: *"Append a call record … seat, provider name, model id, price, `brief_sha(seat)`,
**`rendering_sha(rb)`**, sha of the prompt, raw reply, usage, wall time."*

`rendering_sha` (`seats.py:459`) is `def rendering_sha(rb)` — it reads `rb.renderings`.
§C3.1: *"Must not accept a module, **readback**, plan, rendering or clause parameter."*

**Finding 3 (CRITICAL, internal contradiction).** As written the spec is unimplementable:
the record it mandates needs the object it forbids. An implementer will resolve this the
convenient way — pass `rb` — and the spec will have *caused* the failure it was written to
prevent.

Resolution: split the record. The **transport** writes call-level facts it can know
(`seat`, provider, model, price, `brief_sha(seat)`, sha of the system+messages **as sent**,
raw reply, usage, wall time, timestamp). The **driver** — which legitimately holds `rb` —
writes clause-level facts (`clause_id`, `rendering_sha(rb)`, readback outcome, denominator
sizes) and joins on the payload sha. One join key, two writers, and `rb` never crosses the
seam.

## 5. MUST 7 names a module that does not do what it is said to do

§C2.7: *"key the checkpoint on `(clause_id, seat, prompt_sha)` so a resumed run never
re-pays for an adjudicated seat. `resolve_runs/graph_v2/run_checkpoint.py` already exists —
reuse it, do not write a second one."*

`[READ]` `run_checkpoint.py` in full. Its entire public surface is
`checkpoint_config(cfg, section)` and `class Checkpoint` with `due/record/tick`
(`run_checkpoint.py:47, 61, 74, 108`). It appends progress rows
(`{"completed", "remaining", "spent_usd", "failures", "paused"}`) to a `health.jsonl` and
optionally raises `CheckpointPause`. **It has no key, no result store, no lookup, and no
resume path.** Its own docstring calls it *"periodic run checkpoints … STOPS TO SAY WHERE
IT IS."*

**Finding 4 (CRITICAL).** MUST 7 conflates two different things that share a word:
*progress checkpointing* (what exists) and *per-call idempotency* (what §E calls "required,
not optional"). An implementer obeying C2.7 literally gets periodic health lines and **zero
idempotency**, and re-pays for every seat on every resume — on the one project with a hard
cap. The instruction *"do not write a second one"* actively prevents the correct fix.

Resolution: keep `run_checkpoint.Checkpoint` for progress (it is the right module for
that, and `checkpoint_every`/`checkpoint_pause` are Matt's standing directive), and specify
a **separate append-only call ledger** keyed on `(clause_id, seat, payload_sha)` as the
idempotency store. They are different files with different jobs.

**Sub-finding 4b — the key is not available.** `judge` receives no `clause_id`, and
`run_clause` does not pass one. Under §C1 the factory cannot know which clause it is
serving, so the mandated key **cannot be constructed** on the specified signature. §C3.1's
blanket *"…or clause parameter"* reads as forbidding the fix. This must be ruled
explicitly: **`clause_id` is an opaque identifier, not clause text, and is permitted;
clause TEXT, module, readback, plan and rendering are forbidden.**

## 6. MUST 2's transport violates MUST 1 and MUST 6 by construction

§C2.1: the transport *"sends `system` and `messages` unmodified. It appends nothing."*
§C2.6: *"Retry only on TRANSPORT failure, with a **byte-identical prompt**."*
§C2.2: *"Resolve the provider from config (`translate.resolve_provider` + **`translate.Client`**)."*

`translate.Client._send` (`translate.py:657-660`) begins:

```python
body, payload = self._vary_identical_retry(body)
```

and `_vary_identical_retry` (`translate.py:620-651`) appends, to the **final user turn**,

```
[transport retry N: prior identical attempt failed]
```

whenever the body's sha matches one recorded in `self._failed_body_hashes`
(`translate.py:567`), which `_send`'s `except` populates on **every** raise —
transport, HTTP, truncation, emptiness, cost gate (`translate.py:709`).

**Finding 5 (HIGH).** The mandated transport (a) modifies `messages`, contradicting MUST 1;
(b) makes a byte-identical retry *structurally impossible*, contradicting MUST 6 — the
guard's docstring says so in those words; (c) breaks the payload sha that MUST 5 records
and MUST 7 keys on — the recorded sha would not be the sha of the bytes sent; and (d) is
arguably a §5.6 violation: it carries one bit (*your prior attempt failed*) back into a
seat's prompt, and §5.6's ruling is **zero bits carried**. It is contentless about the
denominator, so this is a rule breach rather than a leak — but the ruling is the ruling.

Resolution (A5): each stage-4 retry uses a **fresh `Client` instance**, so
`_failed_body_hashes` is empty and the guard cannot fire; and the payload sha in the record
is computed by the transport from the bytes it actually sent, never from the prompt string
it was handed. If those two disagree, `judge` refuses (A1).

## 7. MUST 2 and `STEP_stage4.md` §7 are jointly unsatisfiable

`STEP_stage4.md` §7: *"The first run uses a **frontier** tier on 4b, 4c and 4d."*
`most_expensive_provider` (`seats.py:1667`) returns the maximum-priced row, and §E prices
the frontier at `fable` ($10/$50).

`[READ]` `semi-formal-experiment/providers.json`: **`fable` has `"kind": "anthropic"`.**
`translate.Client.__init__` (`translate.py:556`) raises:

```python
if prov.kind != "openai-compatible":
    raise ProviderError(f"this client speaks openai-compatible only, not {prov.kind}")
```

**Finding 6 (HIGH).** The frontier tier §7 mandates cannot be reached through the client
§C2 mandates. The highest **reachable** frontier row is `sol`, `openai-compatible`,
$5/$30. `[RAN]`, same 12 plans, `sol` rates:

| | per clause | ×750 | ×593 |
|---|---:|---:|---:|
| sol, worst (every reply at the 4,096 cap) | **$0.5161** | $387 | $306 |
| sol, likely (40 out-tok/judgement) | $0.0648 | $48.6 | $38.5 |

So §E's `$651 worst / $87 likely` is the price of a configuration **that cannot be run**.
The runnable frontier is $387 / $48.6 — the conclusion (corpus scale is blocked) is
unchanged, and `most_expensive_provider` is right to be conservative, but the spec must say
which row it intends or the implementer discovers this at the first call.

Worse for the pilot: a **10-clause frontier pilot is $5.19 worst case**, against a remaining
ledger of **$5.05** (§8). §7's tier mandate does not exempt the pilot, and §C does not
notice. **A written ruling is required** — *a reply-shape pilot adjudicates nothing, so the
frontier-tier mandate does not attach to it* — and per the repo's own rules that ruling goes
in the cycle record, not the transcript.

## 8. MUST 4's budget fence reads a number that cannot see this stage

§C2.4: *"Check the ledger BEFORE each call against `spend.py`'s ceiling."*

`[RAN]` `spend.py` today:

```
TOTAL   2748 calls   $3.449 of $8.50  (41%)
  !! 2122 logged calls had no price entry
```

Two problems.

1. **The review's arithmetic is stale.** §E states *"$2.057 of $8.50 used ⇒ $6.44
   remaining."* The real remaining ledger is **$5.05**, and 2,122 rows are unpriced, so the
   true figure is *lower by an unknown amount*. Every budget sentence in §C/§E is computed
   against a headroom that no longer exists.
2. ⛔ **`spend.py` structurally cannot price this stage.** `spend.prices()`
   (`spend.py:27`) builds its table from `providers.json` alone. `config.json` defines the
   flash provider **inline** (`"_inline_why": "…not a row in providers.json…"`), and
   `translate.spend_invisibility_warning` (`translate.py:833`) exists solely to shout that
   *"`cost_of()` returns None for these rows, so `total()` SKIPS them and the hard cap is
   that much closer than it reports."*

**Finding 7 (CRITICAL for the budget property).** A stage-4 flash run gates itself on a
total that excludes stage-4 flash spend. The check passes forever. Ironically the
*frontier* rows (`sol`) **are** in `providers.json` and would be counted — so the cheap
tier is the invisible one.

Resolution (A7): the gate is the **maximum** of (i) `spend.py`'s total plus this run's own
measured `Client.spent_usd`, and (ii) `spend.py`'s total plus the worst-case estimate for
the calls not yet made; **and** `Client.max_cost_usd` (`translate.py:547`) must be set from
the run's ceiling so the measured backstop actually binds — §C never mentions it. The
durable fix is the four-line providers.json row that `spend_invisibility_warning` prints
verbatim; that is outside `walkthrough/` and needs Matt.

## 9. Truncation is not a transport failure, and §C treats it as one

`_check_envelope` (`translate.py:848-873`) raises `ProviderError("completion was
TRUNCATED…")` — including the `finish_reason: null` backstop that fires when
`completion_tokens >= requested_max_tokens`. It is the **same exception class** as an HTTP
error, and it is raised **after** `_log_usage` has billed the call (`translate.py:698`,
deliberately: *"a truncated or empty completion is billed exactly like a good one"*).

**Finding 8 (HIGH).** Under §C2.6, a truncated 4c batch is retried as a transport failure —
re-paid, near-certain to truncate again (the reply is long because the denominator is
long), and re-paid again, up to the bound. Two bonus consequences:

* §C's own **F4 table is wrong on one row** when `translate.Client` is the transport:
  *"reply truncated at the 4,096 cap → UNCAUGHT `JSONDecodeError`"* is false. The
  transport raises first. The correct statement is that truncation is a *paid, recoverable,
  loud* failure that §C mis-routes into the retry path.
* `SEAT_MAX_TOKENS = 4096` while every `providers.json` row carries `max_tokens: 16384`; if
  open decision 4 is got wrong, the truncation guard's cap moves and the priced worst case
  is 4× low.

Resolution (A6): retry **only** on `urllib` transport/HTTP-5xx errors. `ProviderError`
carrying `TRUNCATED` or `empty response`, and `CostGateError`, are terminal: record
`not_run` with the reason and the raw usage, do not re-send.

## 10. MUST 3 is where the forbidden parser will actually be written

§C2.3: *"Adapt the envelope to text… **Three lines**, and it must record the raw text
before parsing."* §C4: *"A factory that pre-cleans replies is a second, laxer adjudicator
living outside the module the tests fence."*

These two sit four paragraphs apart, and the first invites the second. `[RAN]` the failure
that motivates it: with a `translate.Client`-shaped envelope, `judge` raises

```
KeyError: 'judgements'
```

because `json.loads(raw) if isinstance(raw, str) else raw` (`seats.py:1520`) passes the
**envelope dict** straight through to `data["judgements"]`. The implementer meets an
uncaught `KeyError` inside the adapter, on turn one, and the shortest fix is to start
massaging text in the adapter — markdown fences next, then verdict case.

**Finding 9 (MEDIUM-HIGH).** MUST 3 needs a hard boundary, not a line count.
Resolution (A3): *the adapter's entire body is `return env["text"]`. It may not `strip`,
slice, regex, `json.loads` or branch on content. Any transformation of the reply string is
a change to `seats.judge`.* That is checkable by reading five lines.

## 11. The ≤12-item 4c batch is assigned to nobody

§E requires splitting 4c into ≤12-item batches (`[RAN]`: the largest stored denominator is
**18 items**, `m0014`; three modules exceed 12). But §C2.1 says *"Build a transport, never
a prompt. `plan_clause` is the only prompt source"* — and `plan_clause` (`seats.py:1552`)
builds `prompts["4c"]` as a single string from a single `build_4c_prompt` call.

**Finding 10 (MEDIUM).** The batching change is a `plan_clause` change (`prompts["4c"]`
becomes a tuple of prompts over id-ordered slices; `run_clause` concatenates the judgements
and validates once against the full `d4c.judgeable`). §C4 lists two `seats.py` changes and
this is a third. Unassigned, it lands in the factory, violating C2.1.

---

## 12. Attack on §C4 — is the split right?

**Yes on both, with two amendments.**

**`run_clause`'s skipped seat (F5) cannot live in the factory** — decisive. The `continue`
is at `seats.py:1580`, inside `run_clause`; the factory is never invoked on that path
(`factory is None` is precisely the case where there is no factory to ask). Likewise
`route` (`seats.py:258`). Correctly assigned.

**Reply parsing in `judge` is right, and does not create a second adjudicator** — three
grounds:

1. `judge` **already** normalises the other half of the reply: `_reply_item`
   (`seats.py:1470`) accepts the bare id, the stripped id, the `[bracketed]` id, and a
   seat-scoped digit fallback. Verdict normalisation is the same operation on the same
   reply in the same function; putting it elsewhere would leave the repo with **two**
   normalisers, which is the drift the module warns about for `_MODULE_PATTERNS`.
2. The adjudicator is `validate_judgements` (`seats.py:898`) plus the closed sets — both
   untouched. Normalisation runs strictly *before* adjudication and cannot widen it: an
   unknown string still refuses **by name**.
3. It is inside the fenced module, so `test_seats.py` can pin it. A parser in the factory
   is by definition outside every pin.

**Amendment A9 (the normalisation is under-specified in the direction it claims to fix).**
`strip().lower().rstrip(".")` does not catch the most likely live variants of the
hyphenated verdicts: `"not conveyed"`, `"not as meant"`, `"not‑conveyed"` (U+2011). Each
costs a whole clause's four calls. Normalise whitespace-and-dash-to-hyphen as well, over
the **closed set only** — that is still parsing, not floor-lowering.

**Amendment A10 (record what was changed).** If normalisation rewrites the string, the
`Judgement` must carry a stamp (`verdict-normalised:<raw>`) — `Judgement.stamps`
(`seats.py:888`) already exists for exactly this, and the module's own rule is *"beside,
never over"*. A rising normalisation rate is then a measurable **brief defect**; without
the stamp it is a free win nobody can see. This also preserves the raw verdict when the
call record and the adjudication disagree.

---

## 13. Coverage and honesty — what a stage-4 run could claim TODAY

With a working factory and nothing else changed, a live run produces:

* **4a** — advisory by construction (§4.3(2)); `route` gives it no route (`seats.py:258`).
  Evidence of nothing, by design.
* **4b, 4d** — F1(b): 3 of 12 stored modules carry `readback-check-failed`, stamping
  *everything* they say non-evidential. F1(a): the `non-evidential` echo stamp fires on
  **0 %** of the corpus while the condition holds on 6.6 % of items, so the residue is
  *over*-credited. F1(c): 4d's only non-model cross-check cannot be wired at all.
* **4c** — the only unstamped verdict, and F2 `[RAN]`-reconfirmed here at **48 %**: on half
  its denominator it is reading the same words as 4b, so the instrument check
  (`seats.py:1078`) is void there and the anchor does not anchor for the repo's own
  measured failure mode #4.
* **F3** — latent at 0/121 today; `[RAN]` reconfirmed: `build_4b_prompt("some clause",
  ("⟦ASP: «thing» :- «other»⟧",))` → `DisclosureRefused`, and because `plan_clause` builds
  all four prompts eagerly, **one layer-1 rendering refuses all four seats for that clause**.

**Plainly: a stage-4 run today can produce trustworthy numbers about ONE thing — the
instrument.** Reply shapes, the `unclear` rate, the truncation rate, the normalisation
rate, whether 4d answers in a shape `_reply_item` accepts. It cannot produce a
faithfulness number that anyone should trust, because the layer's evidential accounting is
the thing F1 says is broken.

### Build order — the recommendation

**BUILD the factory NOW, INDEPENDENTLY of F1/F2/F3. RUN it only after F4, F7, F5 and
amendment A1.**

* **Independently of F1/F2/F3**, because those govern what a run may *claim*, not whether
  the seam works, and because the factory is a multi-day offline build that can be
  stub-tested to completion while the three rulings are made. Serialising it behind three
  design decisions costs weeks and buys nothing.
* **Before any call**, land: **A1** (the wire fence — otherwise the first factory ever
  written is unaudited on the one property the layer exists for), **F4** (`judge` hardening
  — five of seven realistic replies crash today, after the money is spent), **F7** (4d's
  displayed ids — running 4d with a prompt known to teach the wrong id shape buys a
  guaranteed un-adjudicable seat at full price), and **F5** (otherwise a crashed seat is
  byte-identical to a clean pass in the artifact).
* **Before any EVIDENTIAL run**, land F1 and F2's rulings and F3's decision. A pilot that
  claims only §D's table does not need them; anything that says the word *faithful* does.

---

## 14. Cost / scale sanity — the arithmetic checks out, with one correction and one surprise

`[RAN]` over the 12 stored modules that reach a seat, `estimate_clause_usd` at
$0.14/$0.28:

```
n=12   mean worst $0.00527/clause   mean likely $0.001063/clause
10 × mean:  worst $0.0527   likely $0.0106
750 × mean: worst $3.96     likely $0.80
593 × mean: worst $3.13     likely $0.63
```

§E's `$0.0053 / clause` and `$3.98 at 750` are **confirmed**. A ≤10-clause flash pilot is
**$0.053 worst case** (`$0.0534` taking the ten most expensive plans) — 1 % of the
remaining ledger. §C's `~$0.05 worst` is right.

**Correction:** the remaining ledger is **$5.05, not $6.44** (§8), and 2,122 rows are
unpriced, so it is an over-statement of headroom. `$3.96 worst` at 750 is now **78 % of
everything left**, not 62 %.

**Surprise, and it changes the pilot design.** `[RAN]` the 12 plans cover only **6 distinct
clause ids** — `m0092`, `m0014`, `m0150`, `m0105`, `m0165`, `m0037` (several are repeat
translations of the same clause across runs). **A "≤10-clause pilot" is not available from
the stored corpus; the honest maximum is 6 distinct clauses.** A pilot that reports "10
clauses" while judging 6 clauses twice would be measuring the seats' test-retest agreement
and calling it coverage — worth doing, but as a *different, named* experiment.

### What the pilot's deliverable should be

A **measurement of the instrument**, not of any translation. Specifically:

1. `STAGE4_DESIGN_REVIEW.md` §D's mock-vs-live table, every row filled with an observed
   count: fenced replies, envelope shape, missing `reason`, verdict casing/punctuation,
   truncation, refusal prose, id shape per seat.
2. The `unclear` rate, split by rendering length (`unclear_split`, `seats.py:1166`).
3. **The A1 invariant's fire count**: payload-sha-as-sent vs payload-sha-as-handed, per
   call. A single mismatch is a factory defect and blocks everything downstream.
4. The verdict-normalisation rate per seat (A10's stamp) — the direct measure of whether
   the briefs teach the reply shape.
5. Whether 4d is adjudicable at all before F7 lands (predict: no — record the prediction
   before the run, per the sandwich rule).
6. Measured $ per clause per seat against `estimate_clause_usd`'s worst case, so the ×750
   projection stops being an assumption.

⛔ **Not** a faithfulness result, not a pass rate, not an `n_passed`. `build_report`
already refuses to hold one; the write-up must too.

---

## 15. THE CORRECTED §C — write this into the plan in place of the current §C

> ### C0 — What this fence is, stated honestly
>
> 4c is **not downstream of the RENDERER**: its material is built by `_item_text`
> (`seats.py:679`) out of the module and `corpus_texts`, and `build_4c_prompt` refuses
> renderer marks in both (`seats.py:812, 815`). That is the property, and it is smaller
> than *"4c cannot see the rendering"* — F2 measures 48 % of 4c's items carrying the same
> words 4b is shown. Do not justify anything below by the larger claim.
>
> ⛔ **The absence of a rendering parameter is NOT the mechanism.** `plan_clause` already
> holds the readback in scope four lines above the 4c builder, and `test_seats.py:419` is a
> *name scan* of a signature, not a structural guarantee. The mechanism is a **content
> scan**, and until A1 lands there is no content scan on the wire at all.
>
> ### C1 — Signature
>
> ```python
> def seat_client_factory(seat: str, clause_id: str, config_path: str, *,
>                         ledger, run_dir: str, records):
>     """seat + clause id + config -> a zero-arg callable returning a transport."""
> ```
>
> `clause_id` is an **opaque identifier** and is required — the idempotency key
> `(clause_id, seat, payload_sha)` cannot be built without it (C2.7). Clause **text**,
> module, readback, plan and rendering remain forbidden (C3.1).
>
> ### C2 — MUST
>
> 1. **A1 — THE WIRE FENCE, and it is the load-bearing one.** `seats.judge` must, before
>    the call, `_refuse` the **assembled outbound payload** (`system` + every message's
>    content, concatenated) with the seat's own pattern set — `_RENDERING_PATTERNS` +
>    `_UNIVERSAL_PATTERNS` for 4c; `_MODULE_PATTERNS` + `_UNIVERSAL_PATTERNS` for 4b and
>    4d; `_UNIVERSAL_PATTERNS` for 4a — and must record `sha256` of that payload. The
>    transport must return, alongside the reply, the `sha256` of the bytes it actually
>    sent; `judge` raises `SeatRefused` if the two differ. This closes F13, closes the
>    §3 counterexample, and converts C3's unverifiable prohibitions into one checkable
>    invariant. *A signature restriction alone is a lint and must not be relied on.*
> 2. **Build a transport, never a prompt.** `plan_clause` is the only prompt source. The
>    returned object exposes exactly `complete_messages(system, messages) -> (text, sha)`
>    and sends both unmodified.
> 3. **A3 — the adapter's entire body is `return env["text"], sha`.** No `strip`, no
>    slice, no regex, no `json.loads`, no branch on content. Any transformation of the
>    reply string is a change to `seats.judge` (C4).
> 4. **Resolve the provider from a SEPARATE stage-4 config** — never `config.json`, whose
>    `format_forcing` default (`json_schema`) forces the **stage-1 module schema** onto a
>    seat reply (`translate.py:579`). Stage-4 config sets `format_forcing: "json_object"`,
>    `max_tokens: 4096` (= `seats.SEAT_MAX_TOKENS`, delivered through
>    `cfg["model"]["max_tokens"]` so `Provider.max_tokens` carries it), and a fixed
>    `temperature`.
> 5. **Tier is fixed per SEAT for the whole run**, never per clause: `STEP_stage4.md` §7
>    requires frontier on 4b/4c/4d and **the translator's own model on 4a**. The reachable
>    frontier is `sol` ($5/$30): `fable` is `"kind": "anthropic"` and `translate.Client`
>    refuses it (`translate.py:556`). Record both tiers once, in the run record.
> 6. **A7 — the budget gate is `max(spend.py total + this run's measured
>    `Client.spent_usd`, spend.py total + worst case for calls not yet made)`**, checked
>    before each call, and `Client.max_cost_usd` (`translate.py:547`) is set from the run
>    ceiling so the measured backstop binds. ⛔ `spend.py` **cannot see** this stage's flash
>    spend — the provider is defined inline in `config.json` and
>    `spend.spend_invisibility_warning` says so (`translate.py:833`). Print that warning at
>    the end of every run until the providers.json row exists. An unpriced provider counts
>    as over budget (`seats.py:1626`).
> 7. **Two records, two writers, joined on the payload sha.** The **transport** appends,
>    before adjudication: seat, provider, model, price, `brief_sha(seat)`, payload sha,
>    raw reply, usage, wall time, timestamp. The **driver** appends, per clause:
>    `clause_id`, `rendering_sha(rb)`, readback outcome, denominator sizes. ⛔ Never pass
>    `rb` to the factory to obtain `rendering_sha` — that is the leak this section exists
>    to prevent (the current §C2.5 requires exactly that, and is wrong).
> 8. **A6 — retry ONLY on `urllib`/HTTP-5xx transport errors**, bounded at 2, with
>    backoff, from a **fresh `Client` instance** each time so `_failed_body_hashes` is
>    empty and `_vary_identical_retry` (`translate.py:620`) cannot mutate the prompt.
>    ⛔ `ProviderError` carrying `TRUNCATED` or `empty response`, and `CostGateError`, are
>    **terminal**: they are paid, recorded `not_run` with the reason and the usage, and
>    never re-sent. Truncation is not a transport failure.
> 9. **A4 — idempotency is a SEPARATE append-only store** keyed on
>    `(clause_id, seat, payload_sha)`, written before adjudication.
>    `resolve_runs/graph_v2/run_checkpoint.py` is a **progress reporter**, not a result
>    store — it has no key and no lookup — and must be used for progress
>    (`checkpoint_every` / `checkpoint_pause`) only. ⛔ Resume may replay a stored reply
>    **only** when `seat`, `clause_id`, `payload_sha`, `brief_sha` and `model id` all
>    match; any mismatch re-calls or refuses. A replay transport reads only the store, and
>    is subject to C2.1's wire fence like any other.
>
> ### C3 — MUST NOT (a lint layer over C2.1, not a substitute for it)
>
> 1. Must not accept a module, readback, plan, rendering, or clause **text** parameter, and
>    must not obtain one from `run_dir`, `config_path`, an import, or a caller frame.
>    ⚠️ Unenforceable by inspection — C2.1 is what actually holds. A closure lint
>    (`factory.__closure__` may hold only `str`/`int`/`None`) is worth having and is not the
>    fence.
> 2. Must not retry by re-prompting with the refusal message (`validate_judgements`' text
>    names the denominator ids). A failed adjudication is a new clean call or nothing —
>    §5.6, zero bits carried.
> 3. Must not vary the brief or the temperature. Must not share one `Client` across seats
>    or across retries: `_failed_body_hashes` and `spent_usd` are per-instance state that
>    would let one seat's failure alter another seat's request.
> 4. Must not enable tools, web access, or any retrieval.
> 5. Must not default a provider or a price; no literal fallback (`seats.py:1667`).
> 6. Must not swallow an exception into a verdict. A transport failure is a recorded
>    `not_run`, never an `unclear`.
>
> ### C4 — Changes that belong in `seats.py`, not the factory (now THREE)
>
> * **`judge` parses defensively** (F4): strip markdown fences; accept
>   `{"judgements": [...]}` or a bare list; unwrap the envelope dict; normalise `verdict`
>   with `strip().lower()`, trailing `.` removed, **and internal whitespace/en-dash mapped
>   to `-`** so `"not conveyed"` reaches `not-conveyed` (A9); raise `SeatError` — never
>   `KeyError`/`JSONDecodeError`/`TypeError`. The closed set is unchanged; an unknown
>   verdict still refuses by name. **A10: when normalisation rewrites the string, stamp the
>   judgement `verdict-normalised:<raw>`** (`Judgement.stamps` exists for exactly this) so
>   the rate is measurable and never a silent win.
> * **`run_clause` records a skipped seat** instead of `continue` (`seats.py:1580`), and
>   `route` must not return `none` when a denominator has no judgements. `judge` raising
>   must also produce a `not_run` record, not an omission.
> * **`plan_clause` splits 4c into ≤12-item batches** ordered by id (largest stored
>   denominator is 18): `prompts["4c"]` becomes a tuple, `run_clause` concatenates the
>   judgements and validates once against the full `d4c.judgeable`. `validate_judgements`
>   needs no change. ⛔ This may not be done in the factory — C2.2.
>
> ### C5 — Registration, same diff
>
> Per `AGENTS.md`: the new module goes into `test_no_reference_leak.QUERY_MODULES` /
> `FORBIDDEN` as its side dictates, and its tests into `conftest._OPTIONAL`, in the same
> commit. Registration, not documentation, fences a module.

---

## Appendix — what was `[RAN]`

All offline, zero spend, against the stored corpus (`runs/*/m*.json`, 74 artifacts,
12 reaching a seat over 6 distinct clause ids) via
`semi-formal-experiment/.venv/bin/python`.

| # | check | result |
|---|---|---|
| 1 | `_refuse` call sites | 9, all inside the four builders (`seats.py:748–864`) |
| 2 | transport appends a turn to 4c's messages | delivered, nothing raised |
| 3 | spec-compliant factory (`seat, config_path, ledger, run_dir`) reconstructs renderings from disk and appends them | full glosses with `«…»` marks delivered to 4c |
| 4 | `judge` given a `translate.Client` envelope | `KeyError: 'judgements'` (uncaught) |
| 5 | 4c item text containing 4b's rendering verbatim | **58/121 = 48 %** (F2 reconfirmed) |
| 6 | `build_4b_prompt` on a layer-1 `⟦ASP: … :- …⟧` span | `DisclosureRefused` (F3 reconfirmed) |
| 7 | `estimate_clause_usd`, flash | mean worst $0.00527/clause; 750 → $3.96 (§E confirmed) |
| 8 | `estimate_clause_usd`, `sol` frontier | mean worst $0.5161/clause; 750 → $387; 10-clause pilot $5.19 |
| 9 | `spend.py` | $3.449 of $8.50; 2,122 unpriced rows |
| 10 | `providers.json` kinds | `fable` is `"anthropic"` — unreachable via `translate.Client` |
| 11 | `run_checkpoint.py` public surface | `checkpoint_config`, `Checkpoint.due/record/tick` — no key, no store, no resume |
| 12 | distinct clause ids among the 12 plans | **6** |
