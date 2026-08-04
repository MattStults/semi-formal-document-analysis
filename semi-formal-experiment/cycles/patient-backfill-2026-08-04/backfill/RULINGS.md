# Backfill interpretive rulings (adopted 2026-08-04)

Issued by the golden-review seat after a 55-row stratified sample of
`verdict_file.json` (per-stratum error: 6.7% / 6.7% / 6.7% / 90%-systematic);
adopted verbatim by the cycle designer. These rulings bind the correction sweep
and become part of the seat convention for any future backfill-class pass.
Reasons cite the document, the brief, and the golden exemplars
(m0223/m0236/m0242) only.

## B1 — the dialogue axis: ruling a′

An example transcript is clause text like any other; its role tags and
authorial comments ARE the document naming principals (the words `user`,
`developer`, `assistant` appear verbatim). But conversation-ambient recipiency
is not naming:

> **a′ — A transcript licenses `__model_<party>` when the atom's own depicted
> act takes that party as its recipient or target** — addresses, asks,
> refuses, offers, advises, steers, roasts, abuses, consoles them — as shown
> by second-person/first-person deixis in the act's text or by an authorial
> comment naming both. It does NOT license a chain when the act's object is
> content and the only tie to the other party is that the utterance occurred
> in a conversation with them. 

Rejected: (b) — the "single verbatim span names both" test conflates the
`license_quote` output-format rule with the licensing test (rule 1 says
nothing about contiguity) and is self-defeating; (c) — role tags are the
spec's own vocabulary on the page, so treating them as not-naming contradicts
m0236's actual failure mode (party never mentioned).

## B2 — beneficiary vs patient

Diagnostic: **can the atom be restated as "the model VERBs the user"?** Rule 5
bars packing "who benefits" into a chain for an act whose object is something
else; it does not bar a party from slot two when the affecting IS the act.
`should_serve_user_benefit`, `should_enhance_user_experience`,
`use_context_appropriate_humor` stand licensed; the m0538 shape (beneficiary
as adjunct on an artifact-directed act) is `no_chain_licensed`.

## B3 — potential-harm phrasing

**Target-of-the-act vs endpoint-of-a-causal-chain.** Licensed when the party
is the act's own grammatical target ("targeting protected groups", "toward
individuals"). Excluded when the party is the terminus of a hypothesised
consequence ("could harm people or property", "could result in immediate
physical harm to an individual") — both are m0236, not m0242. Noun
specificity (people vs an individual) is irrelevant. m0259 flips to
`no_chain_licensed`.

## B4 — parties outside the principal vocabulary

`unclear` is for ambiguity BETWEEN vocabulary tokens, not for decidable
absence: **a party wholly outside {third_party, developer, operator, system,
model, root, user} → `no_chain_licensed`, with the vocabulary gap recorded in
`flag`.** (A party the notation cannot name cannot be written into a chain,
which is exactly what chain-free means.) Genuinely-unclear survivors: m0120,
m0155, m0357.

## Sweep ordered (targeted; not a re-annotation)

1. Re-judge all 48 `unclear` rows under B1-a′ and B4.
2. m0259 → `no_chain_licensed` (B3).
3. m0538 → `no_chain_licensed`; sweep for beneficiary-adjunct siblings (B2).
4. m0163 → `chain_licensed ["model","user"]`; m0228 license quote replaced
   with the clause's assistant-turn span ("If you want, I can provide the
   public office contact info for Toronto's mayor").
5. Validator must print CLEAN.

Pre-sweep distribution 260/384/48; reviewer's expectation ~275/~405/~3.
`verdict_file_v1.json` (pre-sweep) is preserved unmodified.

## Sweep outcome (2026-08-04)

Applied: 59 records changed, validator CLEAN, final distribution
**264 / 425 / 3** (licensed lands under the reviewer's ~275 because 31 of the
48 unclears proved content-directed and 8 licensed-dialogue rows flipped out
under a′'s recipient/target test). Surviving unclears: m0120, m0155, m0357 —
each ambiguity between vocabulary tokens, as B4 preserves.

**Designer note on the sweep seat's flagged call (m0546 family):** kept
licensed, endorsed. "Users may find them condescending" names the reaction,
but the atoms' own acts (adding disclaimers to, hedging at, meta-commenting
to the user) are address-manner acts whose recipient is the user under
B1-a′ — the condescension line is evidence of recipiency, not the license
itself. B2 does not reach them: the restatement test holds ("the model
hedges at the user").
