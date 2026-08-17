# FINDINGS — DeepSeek drafts, Opus adjudicates, feedback continues the transcript

⚠️⚠️ **NOT A CAPABILITY MEASUREMENT.** Every advantage was deliberately given:
a frontier critic read each draft against the span and wrote bespoke findings
into DeepSeek's own transcript. The modules in `out/` are DeepSeek's ceiling
WITH a strong critic. **The unaided output is turn 1, and both turn-1 drafts
are defective.**

**Spend $0.0190, 8 live calls**, cap $0.15. Reconciled two ways — the turn
records and the last 8 rows of `usage.jsonl` agree at $0.01903.

**Why not `repair_loop`** (read first, as briefed): `look()` calls
`checks.run_checks` INLINE between turns and does not return until the chain
terminates. The adjudicator here is a model in the harness's context, not a
callable — there is nothing to hand it in place of `look`, and no way to
suspend mid-chain. `loop.py` reimplements ONLY the turn boundary; transcript
shape is `repair_loop`'s exactly, and the system prompt sha1 plus both
`prompt_user.txt` were verified byte-identical to production run
`20260816-094505` BEFORE the first call.

| clause | turns | converged | turn-1 defect |
|---|---|---|---|
| `l3147_3238_n003` | **3** of 5 | yes | the known one, exactly |
| `l1_170_n056` | **5** of 5 | yes, on the last turn | a DIFFERENT one |

**`l3147_3238_n003` reproduced its known defect on a fresh draw** — *"use a
tool …, hedge …, **or** explain"* came back as three `oblige` on the identical
body, so hedging violates two — **and it passed production's entire stage-2
floor**: `translated`, `repair_needed=False`, zero breaches.

**`l1_170_n056`'s known defect did NOT reproduce; a different one did.**
Production's failure is obligation-dropped-exception-kept. This draw KEPT
`oblige honor_request(R) :- user_request(R)` and failed to ATTACH the exception
— unconditional obligation plus three `permit refuse_request(R)` on an act the
span never names. On a conflicting request it obliges honoring AND permits
refusing. **Three distinct wrong answers are now on record for one 18-word
span** (production's dropped obligation, N7's invented `forbid`, this run's
unattached exception): **the prompt never says WHERE AN EXCEPTION GOES.**

⭐ **THE FREEZE, AND WHAT BROKE IT — the run's biggest result.**
`l1_170_n056` returned **byte-identical modules on turns 1, 2 and 3** (sha1
`fb9db6f61c`) under two different **3,900-character** critiques — the second
opening by stating the previous reply was byte-identical and must not be
reproduced. Transcript formation was verified, not assumed. A **62-word**
message — three numbered mechanical edits, "change nothing else" — broke the
freeze on the next turn and performed all three exactly.
⛔ `repair_loop`'s docstring records the repair MESSAGE as REFUTED as the cause,
by varying the READER (4 stand-ins repaired 4/4). **This run held the reader
fixed and varied the message's LENGTH and IMPERATIVENESS, and the freeze
moved.** Sufficiency and leverage are different properties. **n = 1; a rate is
owed before any production change.**

**Stage 2's measured blindness: 3 of 8 drafts scored `translated /
repair_needed=False / 0 breaches` while carrying a defect that changes what the
module concludes.**

**Survived to the final artifact:** `l1_170_n056`'s borrowed `user_authority/1`
gloss still describes a *request* rather than the authority level the node
handed it, and is used in no body while a coined `user_request/1` with the same
gloss does its work — **failure mode #9 manufactured inside one module, in the
shipped module.**

**FRESH vs FROM-LIST** (adjudicated with the list CLOSED, then opened):
* **FRESH, not on the list:** the unattached exception (the decisive defect);
  borrowed-gloss/coined-name duplication; `instruction_level/2` in `requires`
  though not a NEEDS name; read-back/item mismatch; and that
  `l3147_3238_n003`'s `claims` **carried** the disjunction error rather than
  catching it — **the case P3 is structurally blind to, since claims and
  asserts agreed and both were wrong.**
* **FRESH and independently on the list:** the disjunction (P4), invented
  `refuse_request` (N10), no assert on the excepted branch (N7).
* ⭐ **FROM-LIST, MISSED BLIND — the list earning its keep, once in two
  clauses:** N7's second half, that a `cepa` closure on an excepted branch
  re-asserts the silence the span declined to break. Turn 5 now declares
  `unclear`.
* **Checked and CLEAN, recorded so the list is not overstated:** N8 (argument
  order WAS in the gloss); P3 on `l1_170_n056`; P6/N3 and N10 on
  `l3147_3238_n003`.

⛔ **P9 CONFLICTS WITH THE PRODUCTION PROMPT and is my defect, not the
translator's.** It fires on every correct NODE module, because contract 2
requires unused `NEEDS` names in `requires` — in bold, with a worked example.
Corrected in the list.

**Non-convergence: none.** Both clauses were reachable, so neither joins the
population arguing for a schema or graph fix. Every recommendation is therefore
a PROMPT fix except **R9** — a GRAPH defect: `user_authority` arrives with two
materially different definitions on the two clauses (instructions-from-a-source
vs rules-in-a-section) and **no per-clause check can see it.** The one schema
question raised (`asserts` cannot hold a disjunctive act) is adequately served
by the existing `ontology` route, so **R8 records the gap and proposes no
change.**

⚠️ **PRACTICAL:** `l1_170_n056` needed all five turns and four went to the
freeze. Under production's `max_attempts: 5`, **this clause reaches the
graveyard.**
