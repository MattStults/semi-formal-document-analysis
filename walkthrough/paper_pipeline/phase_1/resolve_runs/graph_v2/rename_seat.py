"""The rename-adjudication seat (Matt's ruling 2026-08-12, option c).

BRIEF = baseline + H1 (referent test) + H2 (text-over-wording), ADOPTED per
the 2026-08-13 sweep (sens 0.57->0.82; ruling + audit in EXPERIMENTS.md).

The resolution pass PROPOSES renames of dangling needs to provided names;
the 0.25 similarity gate auto-accepts the lexically obvious ones; every
proposal below the gate comes HERE instead of being auto-rejected. One
seat call per proposal, one-shot, order-blind -- a seat has no transcript
to continue and each judgment must stand alone.

⛔ BLIND ON NAMES, by construction: the prompt carries only the two
concept DESCRIPTIONS (prose + establishes + span text). Predicate names
never appear -- name similarity is the documented failure mode
(rename_candidates measured the true provider lexically absent ~1 in 10),
so the seat is never shown the thing it must not judge by.

⛔ DEFAULT DIFFERENT: a missing link is an honest dangling; a wrong link
corrupts silently (the content_definition case attached 38 edges to the
wrong concept). The brief says so explicitly.
"""

BRIEF = """You adjudicate ONE proposed identification between two concept
descriptions taken from the same policy document.

Description A is a concept some passage NEEDS (relies on without defining).
Description B is a concept some passage ESTABLISHES (defines or introduces).
The proposal claims A and B are the SAME concept.

Judge ONLY on meaning: do the two descriptions, read with their source
text, denote the same thing -- same subject, same scope, same role in the
document? Paraphrase and different wording of one concept -> same_concept.
Related-but-distinct (one contains, causes, or merely mentions the other;
different scope; different bearer of the obligation) -> different_concept.

When uncertain, answer different_concept: an unlinked concept is recorded
honestly as unresolved, while a wrong identification silently corrupts
every edge built on it.

The document often describes ONE named concept from different facets: a
rule and the authority level it carries, a mechanism and its product, a
principle and the section that houses it. Descriptions capturing different
facets of the SAME referent are still the same concept. The test is not
"do these descriptions describe the same kind of entity?" but "do the two
passages engage the same named thing in the document -- the same tier of
the hierarchy, the same section's rule, the same defined object?"

The two descriptions were written independently by different annotators
who each saw only their own passage. Their WORDING will differ even when
the referent is identical -- weigh the passages' quoted text above the
description phrasing.

Reply with ONE JSON object and nothing else:
{"verdict": "same_concept" | "different_concept", "grounds": "<one or two
sentences citing the decisive wording>"}"""

SCHEMA = ("rename_verdict", {
    "type": "object",
    "properties": {
        "verdict": {"type": "string",
                    "enum": ["same_concept", "different_concept"]},
        "grounds": {"type": "string"}},
    "required": ["verdict", "grounds"]})


def _span_text(node, lines, cap=12):
    out = []
    for s in (node or {}).get("spans", [])[:2]:
        a, b = s.get("lines", [0, 0])
        if 1 <= a <= b <= len(lines):
            out.append("\n".join(lines[a - 1:min(b, a - 1 + cap)]))
    return "\n---\n".join(out)


def build_prompt(need_prose, needer_node, prov_prose, provider_node, lines):
    """The one-shot user prompt. NO predicate names anywhere."""
    return (
        "DESCRIPTION A (a concept the first passage RELIES ON):\n"
        f"{need_prose or '(no prose recorded)'}\n\n"
        "THE PASSAGE THAT RELIES ON IT:\n"
        f"claim: {(needer_node or {}).get('establishes', '')}\n"
        f"text:\n{_span_text(needer_node, lines)}\n\n"
        "DESCRIPTION B (a concept the second passage ESTABLISHES):\n"
        f"{prov_prose or '(no prose recorded)'}\n\n"
        "THE PASSAGE THAT ESTABLISHES IT:\n"
        f"claim: {(provider_node or {}).get('establishes', '')}\n"
        f"text:\n{_span_text(provider_node, lines)}\n\n"
        "Is the proposal that A and B are the same concept correct? "
        "Reply with the JSON object only.")


def judge(complete, prompt, schema_slot=None):
    """One verdict. `complete(system, user) -> {'text': ...}` is the only
    seam -- the caller decides what spends. Any reply that is not exactly
    a valid verdict object is DIFFERENT_CONCEPT (fail-closed), recorded
    with the parse problem as grounds."""
    import json
    import time
    if schema_slot is not None:
        schema_slot(SCHEMA)
    # bounded transient tolerance (pre-ds6 review finding 2): the seat runs
    # LAST in a paid build -- one 429/timeout crashing run_resolution_pass
    # would lose the whole paid finale. Two short retries, then fail-closed
    # to different_concept: a rename lost to an outage is an honest
    # dangling; an aborted finale is re-paid work.
    env = None
    for attempt in range(3):
        try:
            env = complete(BRIEF, prompt)
            break
        except Exception as exc:                # noqa: BLE001
            if attempt == 2:
                return {"verdict": "different_concept",
                        "grounds": f"(fail-closed: seat transport error "
                                   f"after 3 attempts: {exc!r:.120})"}
            time.sleep(5 * (attempt + 1))
    text = env.get("text", "") if isinstance(env, dict) else str(env)
    try:
        o = json.loads(text)
        v = o.get("verdict")
        if v not in ("same_concept", "different_concept"):
            raise ValueError(f"verdict {v!r}")
        return {"verdict": v, "grounds": str(o.get("grounds", ""))[:400]}
    except Exception as exc:                    # noqa: BLE001
        return {"verdict": "different_concept",
                "grounds": f"(fail-closed: unparseable seat reply: "
                           f"{exc!r:.120})"}
