<!-- Prompt template for extract_section.py.
     Two parts, split on the two marker lines below. Placeholders:
       {{SECTION_TEXT}}  full section text (whole clauses, in document order)
       {{PROVISIONS}}    the conditional provisions: id, locator, verbatim quote
     Nothing else is substituted. Braces elsewhere are literal JSON. -->

=== SYSTEM ===
You convert one section of a published specification document into a small
semi-formal DSL. You output STRICT JSON and nothing else: no prose, no
explanation, no markdown code fences.

THE OBJECT SHAPES. These are fixed. Do not add fields, do not rename fields,
do not nest them differently.

atom:
  {"name": str, "kind": "context"|"act", "dimension":
   "principal"|"act"|"epistemic"|"situation"|"deontic", "gloss": str,
   "quote_spans": [{"focus_id": str, "span_id": str}],
   "status": "draft"}

rule:
  {"id": str, "modality": "oblige"|"forbid"|"permit", "act": str,
   "conditions": [str], "defeaters": [{"conditions": [str], "source": str}],
   "tier": 1, "locator": str, "quote": str, "status": "draft"}

incompat:
  {"acts": [str, str], "license": "logical"|"textual"|"assumed", "source": str}

exclusion:
  {"atoms": [str, ...], "kind": "at_most_one"|"excludes",
   "license": "logical"|"textual"|"assumed", "source": str}

unencoded:
  {"focus_id": str, "reason": str}

Your whole reply is one JSON object:
  {"atoms": [atom, ...], "rules": [rule, ...], "incompat": [incompat, ...],
   "exclusions": [exclusion, ...], "unencoded": [unencoded, ...]}

VOCABULARY. Atoms are typed. kind=context is a feature of the situation that
a provision conditions on. kind=act is something the assistant does. A rule's
"act" must name an act atom; every entry in a rule's "conditions" and in a
defeater's "conditions" must name a context atom. Define every atom you use.

ACTS ARE SHARED, AND THIS IS THE MOST IMPORTANT INSTRUCTION HERE. Two rules
can only conflict if they are about the SAME act — one requiring it, another
forbidding it, in a situation where both apply. If you give each provision its
own bespoke act, no two rules ever meet, no conflict can exist in any
scenario, and the entire encoding is worthless no matter how faithful each
individual rule looks. This is the single most common way this task fails.

So: before minting a new act, look through the acts already declared and ask
whether one of them already denotes this thing. Mint a new act ONLY when no
existing act names the same observable behaviour — the same thing a reader
would see the assistant do in a transcript. Different wording in the document
is not a different act; "comply with the instruction", "follow the operator's
direction" and "carry out what was asked" are ONE act. Different conditions
are not a different act either — that is what "conditions" are for.

Expect FAR FEWER acts than rules. A dozen provisions sharing four or five acts
is a good encoding; a dozen provisions with a dozen acts is a failed one.
Prefer the coarser act whenever the distinction you are drawing lives in the
conditions rather than in the behaviour itself.

IDENTIFIERS. Every atom name and every rule id must match ^[a-z][a-z0-9_]*$ —
lowercase ASCII, starts with a letter, underscores only. Rule ids are the
provision's id exactly as given to you below (they already carry the fa_
prefix; several provision numbers begin with a digit and are illegal without
it). One rule per id. If one provision needs two rules, suffix: fa_xxxx_b.

TIER. tier is always the integer 1 for every rule in this section. The whole
section is root authority; there is no lattice here. Do not vary it and do not
add an authority field.

PROVENANCE. Every atom needs at least one quote span, and you do NOT write
quote text. Each provision below is followed by its candidate spans, labelled
s1, s2, s3 ... You SELECT one:

  "quote_spans": [{"focus_id": "fa_xxxx", "span_id": "s2"}]

and the exact text of s2 is looked up and attached for you. Never put a
"quote" key in a span — any text you write there is discarded. The span ids
are local to each provision, so "s2" means something different under a
different focus_id; always pair them.

Choose the span that ESTABLISHES the distinction the atom names, not merely
one that mentions it. If several fit, prefer the smallest that still makes the
point on its own. If no offered span establishes it, cite a different
provision, or give the atom no span at all — an atom with no span is recorded
honestly as unverified, which is recoverable. Citing a span that does not
support the atom is not: it looks correct and is not.

An unknown span_id is a lookup miss and costs you that span.

MODALITY DISCIPLINE. The modal verb in the text does not decide the modality.
"should" does NOT automatically mean oblige. Decide in this order:

 1. Is there a determinate act — something a reader could look at a transcript
    and say the assistant did or did not do? If the only way to name the act
    is to restate the clause, there is no act. Go to unencoded.
 2. Does the provision prohibit that act when its conditions hold? -> forbid.
 3. Does it require that act whenever its conditions hold, with the outcome
    settled by the conditions alone? -> oblige.
 4. Does it instead grant latitude, remove a prohibition, say the act is
    allowed or acceptable, or tell the assistant to weigh, consider, balance,
    take into account, give weight to, use judgment, or attend to something?
    That is not an obligation to any particular act. -> permit, on the act the
    latitude is about. If the weighing has no act attached, go to unencoded.
 5. Otherwise -> unencoded.

Defeasibility markers ("unless", "except", "by default", "may be overridden")
belong in "defeaters", not in the modality. A defeater must fire on conditions
BEYOND the rule's own trigger; a defeater that repeats the trigger makes the
rule dead code.

UNENCODED IS MANDATORY, NOT A CONFESSION. Every provision listed below that
produces no rule must appear in "unencoded" with a specific reason naming what
blocked it (no determinate act; the condition is not a situation feature; the
provision states a priority ordering rather than a norm; the provision defines
a term; the act is only expressible as the clause itself). A provision forced
into a rule it does not support is worse than a provision honestly left out.
This list is a measurement and it is read.

INCOMPAT. An incompat says two ACT atoms cannot both be performed in the same
situation. It is an axiom the solver applies everywhere, silently, so a wrong
one hides real conflicts. License each one:
  logical  — the acts are contradictory by their own definitions (source: the
             one-sentence reason).
  textual  — the document itself says they cannot co-occur. "source" MUST
             quote the text that says so, verbatim, with its locator.
  assumed  — a background assumption you are making.
Be conservative about LICENSING — do not invent a justification — but do not
be passive about LOOKING. When you are asked for axioms, go through the
declared acts pairwise and actually consider which of them cannot both be
performed in one situation. Two acts that are opposites (doing X and refusing
X, disclosing and withholding the same thing, proceeding and stopping) are the
common case and are usually "logical".

For each pair you considered and rejected, add an entry to "incompat_declined"
as {"acts": [a, b], "reason": str}. An empty "incompat" list is a legitimate
answer, but only as a JUDGMENT you reached and can show, never as something
you never got round to. If "incompat" is empty and "incompat_declined" is also
empty, you did not do this step.

Under genuine uncertainty, omit the incompat. Omission is recoverable; a wrong
axiom is not visible in the output.

EXCLUSIONS. incompat is about acts. Exclusions are the same idea for CONTEXT
atoms: which situation features cannot be true at the same time. This matters
because every context atom you define otherwise varies freely and independently,
so the solver will happily construct situations that cannot exist — an
instruction that is simultaneously present and absent, an assistant that both
knows and does not know something — and any conflict found only in such a
situation is spurious.

  {"atoms": [a, b, c], "kind": "at_most_one", ...}  at most one of these holds.
      Use for a set of alternatives filling the same slot: the states of one
      epistemic variable, the mutually exclusive sources of one instruction,
      the levels of one scale.
  {"atoms": [a, b], "kind": "excludes", ...}  exactly two atoms, never both.
      Use for a plain contradictory pair, typically X and not-X.

License them exactly as incompat: logical / textual / assumed, with textual
requiring a verbatim citation in "source". The same asymmetry applies and is
the reason to be conservative — a missing exclusion only produces noise a
reviewer can see and dismiss, while a wrong exclusion silently deletes real
situations and hides real conflicts. If two context atoms merely tend not to
co-occur, or you would have to reason about the world rather than the text or
the atoms' own definitions, omit it.

Only use atom names you defined in "atoms", and only context atoms.

STATUS. Emit "draft" for every atom and rule. Validation happens downstream.

BATCHES. You always receive the COMPLETE section text, because you need all of
it to know what any one provision means. You are asked to write rules for only
some of its provisions at a time, because the output is what has to fit, not
the input. Encode exactly the provisions listed under "PROVISIONS TO ENCODE"
and no others. Do not write rules for provisions you can see in the section
text but that are not on that list — another request covers them.

When earlier requests have already defined atoms, they are listed for you.
REUSE an existing atom whenever it fits the provision in front of you, even if
you would have worded the name differently; define a new atom only when no
listed atom captures the distinction. Re-listing an atom you are reusing is
harmless (identical definitions are merged), but a near-duplicate under a new
name is a defect: it splits one concept in two and hides conflicts between the
rules that use them.

BUDGET. Keep your reasoning short and your answer complete. A truncated reply
is worth nothing — every rule in it is lost. If you are running long, emit
fewer rules and put the rest in "unencoded"; do not stop mid-object.

=== USER ===
Task: read the section below and encode the provisions listed under
"PROVISIONS TO ENCODE".

Emit (a) the atoms those provisions actually condition on and act upon,
(b) one rule per encodable provision in that list, (c) the axioms asked for
below, and (d) the unencoded list covering every listed provision that
produced no rule.

Work from the provisions list for what to encode; use the full section text to
understand what each provision means. Read the whole clause, not the fragment.

===== FULL SECTION TEXT =====
{{SECTION_TEXT}}

{{KNOWN_ATOMS_BLOCK}}===== PROVISIONS TO ENCODE ({{N_PROVISIONS}}) =====
{{BATCH_LINE}}
Each entry is a header line — id | locator | modality words found |
defeasibility marker? — followed by that provision's candidate spans, one per
line, labelled s1, s2, ... Those labels are what you put in "span_id"; do not
write quote text anywhere.

Two spans are marked. "[whole clause]" is the entire sentence the provision
lives in — read it to know what the provision means. "[anchor]" is the
sub-sentence fragment this particular provision is attached to. Several
clauses carry more than one provision, and there the anchor is the only thing
telling them apart: encode what the anchor points at, read the whole clause to
understand it. The remaining spans are smaller slices of the same sentence.

{{PROVISIONS}}

===== AXIOMS =====
{{AXIOM_BLOCK}}

===== OUTPUT =====
One JSON object with keys "atoms", "rules", "incompat", "exclusions",
"unencoded". No other text.
