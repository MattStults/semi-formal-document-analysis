# DRAFT — Post 2: The technical design, and why each piece exists

STATUS: campaign draft, not for publication. Written before the weekend
certification/generalization runs; scope-honesty check and artifact pointers
to be added before publish. Companion to Post 1 (the goal); Post 3 will carry
the results.

---

The product question is: *which passages of this document bear on behaviour
X?* The design constraint that shaped everything: the answer must be
**instant, offline, and auditable** — no model called at query time, and
every hit carrying the span of source text that licenses it. That rules out
both incumbent answers (human eyeballing; asking a frontier model) and it
rules out a certain kind of shortcut: the tool cannot be fitted to any
judge, because a fitted tool inherits the judge's blind spots and launders
them into a score.

So the system is built like an instrument, not a classifier. Four layers.

## 1. The document becomes a graph of typed objects

The spec is decomposed into passage nodes, and each node is translated once,
ahead of time, into a semi-formal module: the **acts** the passage performs,
with deontic status (must / may / should / forbids), the **qualities** those
acts govern, the **parties** they protect, the **actors** they bind, the
**purposes** they serve, and the **contexts** under which they hold. Every
translated claim cites the span of source text it came from. The translation
is governed by a written contract — what a module may say, what it must
cite, which annotation lanes exist, and who may declare what. The contract
exists because translation is where a tool like this can quietly drift: an
uncited inference here, a quietly widened act there, and the instrument is
no longer reading the document.

## 2. Behaviours are modules too

A behaviour — helpfulness, avoiding over- and under-caution, and so on — is
declared in the same vocabulary: which acts it *performs*, which protected
parties it *concerns*, which purposes it *serves*, which governed qualities
count for it. Matching a behaviour against the document is then a structural
operation: a passage engages the behaviour when the passage's typed objects
and the behaviour's declarations meet, through a small set of explicit
channels — the act channel, the beneficiary wall, the purpose channel, the
signature gate. Each channel is a gate, not a score: it either passes with a
stated reason or it doesn't, and every gate is inspectable.

The gates are deliberately restrictive, and that restrictiveness is load-
bearing. The beneficiary wall, for instance, exists because an earlier
version of the system priced clauses by the grammatical recipient of an act
rather than the party the harm falls upon — and an audit caught the tool
improving its score while deleting the document's guidance on de-escalating
a user's radicalization. The metric said ship it. The wall exists because
the metric was wrong.

## 3. The census: what's fixable, and what's terminal

Any instrument like this will disagree with adjudicated readings somewhere.
The design question is what to do with the disagreements — and the answer is
the **separability census**. For each disagreement it asks: could any
declaration in the design space separate this passage from the correctly-
handled passages it currently collides with? Two views: **CURRENT** — the
instrument exactly as frozen, per behaviour, with every feature no gate
reads masked out — and **REACHABLE** — the design space: everything the
schema would allow a declaration to consume. A disagreement that is
unsatisfiable in CURRENT but separable in REACHABLE is a design target;
unsatisfiable in both is terminal at current granularity, and the census
says so plainly instead of letting effort sink into it.

This part of the design has scars. Three successive defect classes — a
feature the instrument never consumes, features dead for a specific
behaviour, and a conditioning channel that can never bite because the
unconditional declaration wins — each produced false "fixable" verdicts
before it was found. The census today carries a standing probe that fails
loud if the vector and the instrument drift apart, because the census is
what tells the design round where to work, and a lying census is worse than
none.

## 4. The discipline is part of the architecture

The last layer is not code. Predictions are registered before measurement
and scored against once. Truth is a ledger of blind adjudications — rulings
made against the document without knowing what the instrument predicted —
with a hard conflict guard: a node ruled differently by two sources is an
error, never a silent overwrite. New features are justified from the
document *before* their arithmetic is looked at, and then measured; a
feature with beautiful document grounds and negative arithmetic is rejected
with the arithmetic attached. Every completed artifact gets a clean-context
adversarial review whose job is to attack it, and a confirmed positive
finding stops the lane until fixed.

None of this makes the instrument correct. It makes the instrument's errors
**findable** — which is the property the goal actually requires. A reading
you cannot audit is an opinion with extra steps; a reading you can audit is
a tool, even when it's wrong.

## What this post does not claim

That the design is minimal — it is where the defects have pushed it. That
the channels are final — the conditioning channel's inertness is on the
record, and the vocabulary has known gaps the held-out behaviours are about
to probe. And that any of it works on a behaviour it has never seen: that is
exactly what the next post measures.

---

END DRAFT.

Open items before publish:
1. The radicalization/de-escalation example (S3 revert) — verify the telling
   against the cycle record and decide how much detail is public-safe.
2. Artifact pointers for each scar (census defect classes, wall provenance).
3. Tone check with Matt; length ~1,150 words.
4. Post-3 dependency: the final paragraph's promise must match whatever the
   runs find, including failure.
