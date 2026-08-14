"""The splice-adjudication seat (repaired_verification.md, 2026-08-14).

⛔ THE DEFECT THIS SEAT EXISTS FOR. promise_repair's guards all answer
WHERE to aim a splice -- span coverage (`_covers`/`_node_covers`),
citation sites (`is_citation_site`), authority-assignment nodes
(`_is_authority_assignment`), same-referent duplication
(`same_referent_provider`). NOTHING asked whether the RECEIVING NODE'S
CONTENT actually establishes the concept. 4 of ds7's 26 splices were
wrong claims, and one of them (`assume_objective_pov` on
`L2126-2404_n031`, span L2151) spliced prose asserting the NEGATION of
the document's own principle onto a commentary line. Every mechanical
check passed on all four. A mechanical check CANNOT catch this: the
question "does this passage establish this concept?" is a meaning
judgment, so it gets a seat.

⛔ BLIND ON NAMES, by construction (rename_seat's discipline, verbatim):
the prompt carries the concept's PROSE and the receiving node's
`establishes` + span text. The predicate NAME never appears -- the ds7
failures are exactly the cases where a plausible-sounding name papered
over a passage that says something else, so the seat is never shown the
thing it must not judge by.

⛔ DEFAULT DIFFERENT (fail-closed): an un-spliced concept stays an
honest dangling need, recorded in the report and re-repairable; a
wrong splice is a FALSE CLAIM the graph then makes about a span of the
document, and every downstream edge is built on it. Unparseable reply,
uncertainty, exhausted transient retries -> `does_not_establish`.

⛔ THE NEGATION/MENTION RULE is the brief's load-bearing sentence. A
passage that CONTRADICTS the concept, or merely MENTIONS or comments on
it, does not establish it. R1 (negation, on a `!!! meta "Commentary"`
line) and R2/R4 (the concept is real but established by a DIFFERENT
passage, 1,300 lines away / one node over) are exactly those two shapes.
"""
import json
import time

from rename_seat import _span_text          # noqa: F401  (one function,
#: reused rather than copied so the two seats' evidence window cannot
#: drift apart; the seats' PROMPTS differ, their span-quoting does not.

BRIEF = """You adjudicate ONE claim about a policy document: whether a
particular passage ESTABLISHES a particular concept.

You are given a CONCEPT DESCRIPTION and a PASSAGE (the passage's own
one-line claim, plus its text as it appears in the document). Someone
proposes to record, permanently, that THIS passage is where the document
establishes THIS concept.

Judge ONLY on meaning, and only on what the passage's own text says.

A passage ESTABLISHES a concept when its text DEFINES, ASSERTS, STATES or
INTRODUCES it -- the concept is the substance of what the passage says.

A passage DOES NOT ESTABLISH a concept when:
  * the text asserts the NEGATION of the concept, or contradicts it, or
    restricts or qualifies it into something else. A description saying
    the assistant should NOT do X, set against a passage saying it
    SHOULD do X, is does_not_establish -- not a wording difference;
  * the text merely MENTIONS, cites, cross-references, comments on, or
    discusses the reception of the concept without stating it. A remark
    ABOUT a principle ("this principle may be controversial", "see the
    section below") is commentary, not establishment;
  * the text states a DIFFERENT, neighbouring rule -- same section, same
    topic, adjacent sentence -- while the concept itself is stated
    somewhere else;
  * the concept's substance lies OUTSIDE the quoted text, even if the
    surrounding section would support it. You judge the passage you were
    given, not the section it sits in.

When uncertain, answer does_not_establish. An unestablished concept stays
an honest unresolved reference; a wrong establishment is a false claim
the document is then recorded as making, and everything built on it
inherits the error.

The description and the passage were written independently, so their
WORDING will differ even when the passage does establish the concept.
Weigh the passage's quoted text above the description's phrasing --
but a difference in what is ASSERTED is not a difference in wording.

Reply with ONE JSON object and nothing else:
{"verdict": "establishes" | "does_not_establish", "grounds": "<one or two
sentences citing the decisive wording>"}"""

SCHEMA = ("splice_verdict", {
    "type": "object",
    "properties": {
        "verdict": {"type": "string",
                    "enum": ["establishes", "does_not_establish"]},
        "grounds": {"type": "string"}},
    "required": ["verdict", "grounds"]})


def build_prompt(concept_prose, node, lines):
    """The one-shot user prompt. NO predicate names anywhere -- callers
    pass the concept's PROSE, never its `name`."""
    return (
        "THE CONCEPT (as described by whoever relies on it):\n"
        f"{concept_prose or '(no prose recorded)'}\n\n"
        "THE PASSAGE PROPOSED AS ITS ESTABLISHMENT:\n"
        f"claim: {(node or {}).get('establishes', '')}\n"
        f"text:\n{_span_text(node, lines) or '(no span text)'}\n\n"
        "Does this passage's text establish that concept? "
        "Reply with the JSON object only.")


def judge(complete, prompt, schema_slot=None):
    """One verdict. `complete(system, user) -> {'text': ...}` is the only
    seam -- the caller decides what spends. Any reply that is not exactly
    a valid verdict object is DOES_NOT_ESTABLISH (fail-closed), recorded
    with the parse problem as grounds.

    Transport discipline is rename_seat.judge's, verbatim and for the
    same reasons: two bounded retries for transients, but CostGateError
    and TERMINAL transport (402/401/403, key resolution) PROPAGATE --
    fail-closing those would turn a paid stage into a silent all-reject
    run instead of stopping loudly."""
    if schema_slot is not None:
        schema_slot(SCHEMA)
    env = None
    for attempt in range(3):
        try:
            env = complete(BRIEF, prompt)
            break
        except Exception as exc:                # noqa: BLE001
            if type(exc).__name__ == "CostGateError":
                raise
            if attempt == 2:
                msg = str(exc)
                if (any(m in msg for m in ("HTTP 402", "HTTP 401",
                                           "HTTP 403"))
                        or "no key for $" in msg
                        or "Refusing to build a live client" in msg):
                    raise
                return {"verdict": "does_not_establish",
                        "grounds": f"(fail-closed: seat transport error "
                                   f"after 3 attempts: {exc!r:.120})"}
            time.sleep(5 * (attempt + 1))
    text = env.get("text", "") if isinstance(env, dict) else str(env)
    try:
        o = json.loads(text)
        v = o.get("verdict")
        if v not in ("establishes", "does_not_establish"):
            raise ValueError(f"verdict {v!r}")
        return {"verdict": v, "grounds": str(o.get("grounds", ""))[:400]}
    except Exception as exc:                    # noqa: BLE001
        return {"verdict": "does_not_establish",
                "grounds": f"(fail-closed: unparseable seat reply: "
                           f"{exc!r:.120})"}


class Seat:
    """The bound seat promise_repair.splice calls: one object carrying
    the transport seam, the document lines and the schema slot, so
    `splice` takes ONE optional argument and the stage decides once
    whether the gate is live.

    `splice(seat=None)` skips the gate -- that is the MECHANICAL-unit
    path (the direct-call pins), not a production path: run_repair
    builds a Seat whenever `promise_repair.splice_seat` is true, and
    that config DEFAULTS TO TRUE because this is a correctness gate."""

    def __init__(self, complete, lines, schema_slot=None):
        self.complete, self.lines = complete, lines
        self.schema_slot = schema_slot
        self.calls = 0
        self.verdicts = []

    def adjudicate(self, concept_prose, node):
        self.calls += 1
        v = judge(self.complete, build_prompt(concept_prose, node,
                                              self.lines),
                  schema_slot=self.schema_slot)
        self.verdicts.append({"node": (node or {}).get("id"),
                              "verdict": v["verdict"],
                              "grounds": v["grounds"]})
        return v
