# Behaviour-vs-document contradiction with plain predicates + superiority

Probe run 2026-08-07. All code in this directory runs; `../deontic_probe/kernel.lp` is loaded
unchanged, acyclicity guard included. No model call, no API spend.

```
semi-formal-experiment/.venv/bin/python walkthrough/contradiction_probe/run.py
cd semi-formal-experiment && .venv/bin/python ../walkthrough/contradiction_probe/ctd_scan.py
cd semi-formal-experiment && PYTHONPATH=. .venv/bin/python ../walkthrough/contradiction_probe/panel_check.py
```

## Verdict

**The hypothesis as literally written derives zero conflicts on a case that plainly is one.**
Three of its four repairs are cheap and non-deontic. One is a genuine deontic axiom, and one is a
semantic commitment plain predicates make silently and cannot record.

| # | what broke | fix |
|---|---|---|
| 1 | `forbids(Policy, **Material**)` cannot join `behaviour_requires(B, **Act**)`. Silent — no conflict ever | act-index both sides. Free |
| 2 | once act-indexed, basic conflict works and `beats/2` carries the exception cleanly | ✅ hypothesis holds |
| 3 | ⛔ same content in opposite polarity — doc `permit produce(m)` vs behaviour `oblige refuse(m)` — is two unrelated ground terms. The corpus states prohibitions **both ways** | `O(¬a) ≡ F(a)`. The hand-written `complement/2` substitute is O(n²) **and was wrong on the first attempt, producing a false positive** |
| 4 | ⛔ `beats/2` is type-blind. One `beats(clause, behaviour)` fact **silently erases a real conflict**. Satisfiable; the acyclicity guard does not fire. That is compliance aggregation, which the standing ruling forbids | a type constraint. 2 lines, mandatory |
| 5 | ⭐ **CEPA/CNPA is real in this corpus, clause-local, and flips the verdict.** The plain form answers "no contradiction" by the *absence of a rule* | a **forced** per-act default-closure declaration |
| 6 | contrary-to-duty is not a problem — **no clause in 593 has a CTD antecedent** | — |

⇒ **One encoding of the document, one of the behaviour, two queries off them — with a namespace
separation the hypothesis does not state.**

## The behaviour representation

`behaviour.lp`, harm-avoidance-to-third-parties. Norm-shaped (two norms in one sentence), so written
in the same shape as a clause — deontic status × act — under a **different predicate name**, and it
**names no clause**:

```prolog
b_asserts(harm3p, oblige, weigh(A)) :- act(A), may_harm(A,W), outside_conversation(W).
b_asserts(harm3p, forbid, A)        :- act(A), harms(A,W),    outside_conversation(W).
```

Both questions come out of one file; **relevance is a projection, not extra input**:

```prolog
seed(B, A) :- b_asserts(B, _, A).
```

Running the prior probe's best relevance encoding (defeat reachability) off exactly these atoms
returns `{m0198, m0203, m0208, m0252, m0253}` — including `m0203`, reachable only because it
defeats a norm governing a seeded act.

⚠️ **Provenance:** the panel was not opened until every `.lp` was frozen, and the check feeds back
into nothing.

### ⭐ Finding 0 — the licence scheme has no slot for a second text

Invariant 2's `textual` / `assumed` / `world` are all defined **relative to the document**. The
behaviour statement is a *different* text and none of the three applies to a fact read out of it.
**A fourth licence class is needed, or Invariant 2 does not reach the behaviour side at all** — the
side that had never been represented before.

### Invented predicates, marked

- ⭐ **`outside_conversation/1` has no counterpart in the document.** "outside the conversation"
  occurs **0 times** in 593 clauses; "third part\*" 4 times; "non-users" once. The predicate
  carrying the entire behaviour is one the document never uses.
- **`averts/2`** and the obligation derived from it — the behaviour text is purely avoidance-shaped
  and never obliges a positive act. ⚠️ **The single most load-bearing unlicensed step in the
  probe**; T4 turns entirely on it.
- `complement/2`, superseded by the duality axiom.

## T1 — basic conflict, and the polarity break

The hypothesis exactly as written derives **zero conflicts**: `forbids/2`'s second argument is a
*material*, `behaviour_requires/2`'s is an *act*, the join can never fire, and ASP does not say so.
Act-indexing repairs it and the plain form then works with no modality.

⛔ **Then polarity breaks it again.** The corpus states the same prohibition both ways — `m0208`
*"must not generate restricted content"* → `F(produce(m))`; `m0270` *"should refuse to help"* →
`O(refuse(m))`. Write the behaviour in the refusal polarity and **the conflict vanishes**: same
content, contradictory, two unrelated ground terms.

⭐ The third duality rule written by symmetry was **wrong**, and is preserved as `dual=naive`: it
reports a conflict between a clause that *forbids* producing and a behaviour that *requires
refusing* — which agree. **Deontic logic derives `O(¬a) ≡ F(a)` from an axiom and cannot make this
mistake; a hand-written table can, and did, on the first attempt, by someone who knew exactly what
he was testing for.**

## T2 — the exception, and the type leak

`beats/2` carries the exception cleanly: without defeat the probe reports a conflict with a clause
the document has already overridden.

⛔ But read straight, the hypothesis puts the behaviour into `asserts/3` like any clause — it *is*
norm-shaped. Adding **one line**, `beats(m0252, harm3p).`, makes the conflict disappear. The program
is satisfiable and the acyclicity guard does not fire: the relation is perfectly acyclic, it is just
about the wrong kind of thing. **Ranking a clause above the behaviour is compliance aggregation.**

⭐ **A second defect:** `m0255` is the clause that *states* the superiority relation, and `beats/2`
has no argument for who said it — so `m0255` appears in no `beats` fact and relevance never reaches
it. Its panel score is **5/6**. ⇒ `beats/2` should be **`beats(Sayer, Winner, Loser)`**.

## T3 — contrary-to-duty: the corpus has none

Three filters over all 593 clauses find **zero clauses with the shape "if norm N was violated, then
Y."** The two closest are anticipatory (the antecedent is a norm *in force*, not one broken), and
`m0440` — *"if the assistant makes a significant error … acknowledge and course correct"* — has a
**factual** antecedent, so it works in plain predicates with nothing added.

⇒ **The obstacle to CTD here is not the absence of deontic operators. It is that the norms a CTD
clause would hang off are comparatives** — *"minimize side effects"*, *"favor approaches that are
minimally disruptive"* — which have no violation condition. Same wall the relevance probe hit.

⚠️ And a CTD clause is invisible in every compliant situation, so a probe enumerating only
well-behaved situations never reaches it. Witness search must be asked to construct *violating*
situations, which nothing currently does.

## T4 — ⭐ CEPA/CNPA confirmed, with a corpus case

A bystander — not the user — is visible on camera in imminent danger. `m0263`: *"If the user is
streaming video and the assistant identifies something on camera that could cause imminent bodily
harm or death **to the user**, it should interject."*

⭐ **The clause had the occasion to say "or anyone else on camera" and said "to the user".**
*Expressio unius*: the silence is **structured, and clause-local** — the same document is loud about
the user two words earlier.

```
closure=open    silent(interject(bystander_on_camera))   -- NO CONFLICT
closure=cepa    silent(interject(bystander_on_camera))   -- NO CONFLICT
closure=cnpa    conflict(cnpa_closure, harm3p, interject(bystander_on_camera))
```

**The verdict flips on the closure, and the plain form with no closure rule gives the CEPA answer
silently.** `closure=open` and `closure=cepa` are bit-identical — nothing records that a commitment
was made.

⚠️ CNPA is not a strawman: `m0260` (*must avoid overstepping*), `m0265` (*wait for sufficient
signal*) and `m0266`'s GOOD answer (literally *"[says nothing]"*) are the document telling the
assistant not to speak unbidden. Under that reading **the specification contradicts the behaviour**
— a finding the plain form cannot produce.

**Fix:** three plain rules with `silent/1` computed so the gap is listed rather than declared. Two
conditions: it must be **forced** (an optional declaration defaults to CEPA silently — the current
state), and it is **per-act-class, not global**.

⚠️ Structural warning: `mentioned/1` must exclude the closure passages or the program has no answer
set. First sign that a default closure is a different *kind* of object from a clause and cannot be
another module.

## The ontology ablation

Turning off the act-classification block — and nothing else — returns ∅ for **both** questions. The
relevance probe measured this; it holds identically for contradiction. **Neither output survives
without the ontological bridge, and no choice of representation changes that.**

## What is needed, minimally

| | fix | kind |
|---|---|---|
| 1 | act-index both sides | free repair |
| 2 | superiority relation + acyclicity | already ruled, already built |
| 2b | ⭐ `beats/2` → `beats(Sayer, Winner, Loser)` | one argument; `m0255` (5/6) unreachable without it |
| 3 | ⭐ type separation, enforced by constraint | 2 lines, mandatory |
| 4 | ⭐ explicit, **forced**, per-act default-closure declaration | 3 plain rules + a `link.py` check |
| 5 | ⭐ one deontic axiom: `O(¬a) ≡ F(a)` over act complements | **the only genuinely deontic item** |

**Not needed:** `O`/`P`/`F` as operators, a deontic library, violation lattices, paradox-robust CTD.

## Not tested

17 clauses of 593, one behaviour of three, hand-encoded. Whether a model can produce any of it.
Whether the closure declaration can be *derived* (`m0263`'s "to the user" is a narrowing qualifier
beside a broader sibling — a syntactic pattern, and a cheap next probe). And `averts/2` remains the
load-bearing unlicensed inference on which T4 entirely rests.
