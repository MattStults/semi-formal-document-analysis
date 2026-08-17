# The 23 known failure modes

Every one of these was found in real work on this document, not imagined. Each is marked with how it
announces itself: **silent** (nothing complains), **loud** (something errors), **misleading** (you
get a signal pointing the wrong way).

A reviewer told only *"is this faithful?"* passed a fabricated policy. Naming the failure is what
makes it visible, which is why you are given the whole list rather than a summary.

## ① Inside one clause's translation — these are yours to avoid

| | | |
|---|---|---|
| **1** | **Made-up things** | *silent.* The translation invents an entity the document never mentions. Everything downstream works and is about a fiction. ⇒ mark it `assumed`/`world`, or leave it out. |
| **2** | **Missing cross-references** | *silent.* A clause modifies rules defined in other clauses. Translating without reading them means guessing their content. ⇒ `requires`. |
| **3** | **Rules that can never fire** | *loud but ignorable.* A rule guarding a condition nothing can produce looks like it enforces something and enforces nothing. clingo warns every run; people read past it. |
| **4** | **Right answer, wrong stated reason** | *misleading.* "Forbidden, because the exception does not reach this" — with no account of why it does not reach. Caused by leaning on negation-as-failure. |
| **5** | **Hollow stubs** | *silent.* One opaque symbol echoing the document's own words reads correctly in every explanation while the referenced content is absent. **Survives a paraphrase check by construction.** |
| **6** | **Guessing forward from a backward statement** | *silent.* The clause said what an exception does *not* cover; the module encodes what it *does*. |
| **7** | **Anonymous placeholders break the explainer** | *loud — crashes.* `policy(P) :- policy_class(P,_)` is idiomatic ASP and the explanation tool cannot process it. |
| **18** | **A refusal or "unless" encoded on the wrong side** | *silent, and it INVERTS the norm.* "Should generally refuse to engage in X" became `prefer` on the act of engaging; "delegation must ensure every sub-agent respects the scope" became a `forbid` whose body lists the COMPLIANCE atoms — so compliant delegation was forbidden and non-compliant delegation unconstrained. ⇒ a prohibition-with-exception forbids on the **violation ground**: coin the positive violation predicate (rule 4 demands a positive *reason*, not a compliance guard), and an act the clause says to refuse never appears under `permit` or `prefer`. |
| **19** | **Modal strength quietly downgraded or dropped** | *silent.* "Our models WILL STILL provide safety-critical information…" became three `permit`s — doing none of the three now violates nothing; "every scope MUST include a shutdown timer" was claimed in `claims` and encoded nowhere. ⇒ must/will/never map to `oblige`/`forbid`; may/can to `permit`; should to `prefer`. A modal in the span with no assert carrying it is a dropped norm — check each one before returning. And a MUST encoded as an ontology derivation (`shutdown_timer(S) :- scope_of_autonomy(S)` for "every scope must include a shutdown timer") is not an obligation but an unviolatable fact — a requirement is an **assert**, never a definitional rule. |
| **20** | **A condition stated in the read-back but wired to nothing** | *silent.* The read-back said "when the scope of autonomy is negotiated per interaction"; no body checked it, so the preference fires in every planning context; an "until a new scope is confirmed" terminator was declared as a concept and used by no rule, making a cessation obligation unconditional. ⇒ every condition your read-back states appears as an atom in that assert's body, and a concept you declared that no body uses is your own warning sign — re-read the span before returning. |
| **21** | **A derivation that makes the condition free** | *silent, and it VOIDS the norm.* `negotiated_per_interaction(S) :- scope_of_autonomy(S)` turned "when negotiated per interaction" into a property of every scope; `confirmation_requested(P) :- proposed_plan(P)` made "asks for confirmation" underivable-to-fail; `no_agenda_section(S) :- model_spec(S)` declared the entire document to be one section. ⇒ an `ontology` rule may only encode a classification the span itself states. If a condition is a fact about the case, it belongs in `inputs` and is NOT derivable from anything — a single-literal rule rebranding one concept as another is almost always this failure. |
| **22** | **Importing a sibling node's claim** | *silent.* ESTABLISHES was the paragraph's last sentence only; the module also encoded the first sentence's prohibition and its taxonomy — content that belongs to sibling nodes, duplicated here where it will conflict with their modules at link time. ⇒ encode the ESTABLISHES claim and nothing else, however tempting the surrounding sentences are; the graph gave each of them to another node. |
| **23** | **"Only" encoded as its inclusion, exclusion dropped** | *silent, twice on real traffic.* "Should ONLY use the preset voice selected by the user" became a `prefer` FOR the selected voice with a cepa closure explicitly permitting other voices — the restriction the clause exists to state is gone; "instructions … are ONLY relevant to Advanced voice" kept the inclusion and lost the exclusion the same way. ⇒ an "only/solely/exclusively" clause is a **pair**: the permitted case AND the exclusion of everything else. Encode the exclusion as a `forbid` on the non-selected case, a `cnpa` closure, or `forbid_body` — one of the three, explicitly. A read-back that says "only" over an encoding that forbids nothing is failure 20 wearing failure 23's clothes. |

## ② Only visible across clauses — you cannot see these, so do not try to fix them

Note: You are translating **one** clause and cannot observe any of these. They are listed so you
understand why the interface headers matter. **Do not invent shared vocabulary to pre-empt them** —
that is a separate stage's job, and guessing at it from one clause makes it worse.

| | | |
|---|---|---|
| **8** | **Different names for the same thing** | *silent until you link.* One clause says `scope`, another `exception_applies`. Measured: 12 of 13 condition names used exactly once in one real run. |
| **9** | **Same name, different meanings** | *silent.* Two clauses both say `user`, meaning different things; they link cleanly and are wrong. Measured: 46 of 228 reused names carry more than one definition. |
| **10** | **Flat lists where structure was needed** | *silent.* `quoted_text_json`, `_yaml`, `_xml` and five more — eight symbols where one with a parameter was wanted. |
| **17** | **A cyclic priority relation** | *silent.* If A is declared to beat B and B to beat A, a defeat-based encoding gives a confident wrong answer rather than an error. |

## ③ In how the translation is tested — mostly not your stage. #11, #13 and #14 ARE yours

| | | |
|---|---|---|
| **11** | **Test cases describing impossible situations** | *silent.* A program that accepts an incoherent state produces a right answer from nowhere. ⇒ **this one you can partly prevent**: do not write an assertion whose conditions describe a state the document treats as impossible. (There is no field for an integrity constraint, so you cannot state the impossibility directly — say it in `claims` instead.) |
| **12** | **Testing one branch only** | *silent.* A clause with four claims tested with one case. ⇒ **this is why `claims` is a required field.** |
| **13** | **Only testing that it forbids** | *silent* — and **more than a testing gap.** Plain ASP's closed-world reading of `not forbidden(X)` silently commits the whole corpus to *"whatever is not forbidden is permitted"* (CEPA vs CNPA). No probe coverage surfaces a global semantic commitment, because it is not about any situation. ⇒ **this is what the forced `closure` declaration is for.** Measured on this corpus: the contradiction verdict FLIPS on the closure, and `open` and `cepa` are bit-identical — nothing records that a commitment was made. |
| **14** | **Claims no test case can demonstrate** | *silent.* "Purpose never creates an exemption" is about the *rule set*: no rule of a certain shape may exist. ⇒ **this is what `forbid_body` is for.** Do not write it as a constraint — it would be dead. |
| **15** | **"Never fired" has three causes** | *misleading.* Genuinely dead, or the tests do not reach it, or **it is waiting on a clause not yet linked in.** ⇒ declare `requires` honestly so the third can be told from the first. |

## ④ In the checking itself — why your headers and licences matter

| | | |
|---|---|---|
| **16** | **A reviewer cannot see invented entities** | *structurally silent.* Given the clause and a read-back containing an invented "deception policy", a clean reviewer answered **faithful, nothing unsupported** — then reasoned from the fiction. Not reviewer error: the clause says "policies other than restricted or sensitive" and never enumerates which exist. ⇒ **The licence on each fact is the only thing that makes this visible.** A fact marked `assumed` with its inference named can be checked. The same fact marked `textual` cannot. |
