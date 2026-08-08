"""Tests for the repair loop — written before the loop exists.

    ../../../semi-formal-experiment/.venv/bin/python -m pytest \
        walkthrough/paper_pipeline/phase_1/test_repair.py -q

A translation that fails a check is sent back to be repaired. What the repair
attempt is allowed to SEE is the whole design of this loop, and getting it wrong
does not look like a failure — it looks like a rising pass rate.

⚠️ A RECORDED DEPARTURE from `resources/03_pipeline.md`, which says repair runs
in a "FRESH conversation". Repair here is a real accumulating transcript:
system, the clause, the model's own module, the findings, its next module, and
so on. The design's reason for freshness is that "after one round-trip a
continued conversation has seen every expected answer" — but STAGE 2 HAS NO
EXPECTED ANSWERS. Its findings are derived from the module itself. The answer
key enters at stage 3 (probe cases carry must-forbid/must-permit labels) and
stage 4 (the review seats), and the design wrote one rule covering all three
because all three feed the same repair node.

So the constraint that carries over is not freshness — it is `origin`. A finding
from a later stage must never enter the transcript, and that matters MORE here
than under a flattened log, because a persistent conversation is somewhere a
leak can live permanently rather than for one call.

What the transcript buys: the model repairs in its native turn structure rather
than from a prose summary of its own past output; its own turns carry the
reasoning a findings list cannot reconstruct; and the message prefix is
byte-identical as it grows, so every turn after the first is a cache hit.

Every test below exists because one of these can be broken without any visible
symptom.
"""

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import fixtures  # noqa: E402  ⭐ the shared stage-1 fixtures
import schema  # noqa: E402
import translate as T  # noqa: E402


# --------------------------------------------------------------------------
#  A stub model. Returns a scripted sequence of responses, and RECORDS what it
#  was sent — which is the thing under test.
# --------------------------------------------------------------------------

class ScriptedModel:
    """Returns scripted responses and RECORDS the message list it was sent.

    ⚠️ The script supplies attempts 2 ONWARD. Attempt 1 is passed to
    `repair_loop` directly, because the caller has already made that call —
    `run()` obtains it before deciding whether repair is needed at all.

    The message list is the thing under test: what the repair attempt can see.
    """

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []          # [(system, messages), ...] — the evidence

    def complete_messages(self, system, messages):
        self.calls.append((system, [dict(m) for m in messages]))
        text = self.responses[min(len(self.calls) - 1, len(self.responses) - 1)]
        return {"text": text, "in": 10, "out": 10, "finish_reason": "stop"}


# ⭐ ONE definition of the contract, in `fixtures.py`, shared with
# `test_schema.py`, `test_checks.py` and `../../test_link.py`. This file is the
# one that needs the module as WIRE TEXT — `fixtures.module_json` is a thin
# serialiser over `fixtures.module`, never a second definition of the shape.
module_json = fixtures.module_json

BROKEN = module_json(asserts=[fixtures.assertion(
    read_back="producing this is forbidden",   # 0 slots...
    read_back_slots=["M"])])                   # ...1 entry. A real breach.

ABSTAINED = fixtures.abstention_json()


# --------------------------------------------------------------------------
#  The denial: what a repair attempt may and may not see
# --------------------------------------------------------------------------

def test_the_transcript_alternates_user_and_assistant():
    """A real conversation, not a flattened summary of one.

    The model's own module comes back as an ASSISTANT turn, and the findings go
    in as the next USER turn. That is the structure it was trained to repair in,
    and its own turns carry the reasoning a findings list cannot reconstruct.
    """
    model = ScriptedModel(BROKEN, BROKEN, module_json())
    T.repair_loop(BROKEN, clause={"id": "m0001", "quote": "Clause text."},
                  model=model, max_attempts=3)
    roles = [m["role"] for m in model.calls[-1][1]]
    assert roles == ["user", "assistant", "user", "assistant", "user"], roles


def test_the_transcript_PREFIX_is_byte_identical_as_it_grows():
    """Every turn after the first is then a cache hit.

    A loop that rebuilds the whole block each attempt re-sends the same tokens
    at full price. The only visible symptom is the bill.
    """
    model = ScriptedModel(BROKEN, BROKEN, module_json())
    T.repair_loop(BROKEN, clause={"id": "m0001", "quote": "Clause text."},
                  model=model, max_attempts=3)
    first, second = model.calls[0][1], model.calls[1][1]
    assert second[:len(first)] == first, "the prefix changed; caching is lost"
    assert model.calls[0][0] == model.calls[-1][0], \
        "the system block must be byte-identical too"


def test_the_clause_is_in_the_transcript_exactly_once():
    """It is carried by the conversation, so re-stating it wastes tokens and
    invites the model to treat the repeat as a second, different clause."""
    model = ScriptedModel(BROKEN, module_json())
    clause = {"id": "m0001",
              "quote": "The assistant must not produce disallowed material."}
    T.repair_loop(BROKEN, clause=clause, model=model, max_attempts=2)
    whole = " ".join(m["content"] for m in model.calls[-1][1])
    assert whole.count(clause["quote"]) == 1, whole.count(clause["quote"])


def test_the_error_log_ACCUMULATES_across_attempts():
    """Attempt 3 must see attempt 1's failure, not only attempt 2's.

    Without this the loop is amnesia rather than freshness, and a model repeats
    a mistake it already made — which would make the loop look like it cannot
    converge when the real cause is that it was never told.
    """
    model = ScriptedModel(BROKEN, BROKEN, module_json())
    T.repair_loop(BROKEN, clause={"id": "m0001"}, model=model, max_attempts=3)
    whole = " ".join(m["content"] for m in model.calls[-1][1])
    assert whole.count("attempt 1") == 1
    assert "attempt 2" in whole


def test_a_finding_that_was_FIXED_stays_in_the_log():
    """The reason the log accumulates: so old problems are not reintroduced.

    Without it the loop can oscillate — fix A and break B, fix B and reintroduce
    A — forever, inside the attempt budget, and the symptom is indistinguishable
    from a model that simply cannot do the task. The log has to show what has
    already been gone through, not only what is wrong right now.
    """
    # attempt 1 breaks the read-back; attempt 2 fixes THAT and breaks something
    # else; attempt 3 must still be able to see the read-back failure.
    # ⚠️ The script supplies attempts 2 ONWARD — attempt 1 is the argument.
    other = module_json(requires=[])          # undeclared `restricted/1`
    model = ScriptedModel(other, module_json())
    T.repair_loop(BROKEN, clause={"id": "m0001"}, model=model, max_attempts=3)
    final_log = " ".join(m["content"] for m in model.calls[-1][1])
    assert "slot" in final_log.lower(), \
        "attempt 1's read-back failure vanished once it was fixed"
    assert "declares" in final_log.lower(), \
        "attempt 2's failure is missing"


def test_the_log_carries_the_MODULE_as_well_as_the_finding():
    """"the prior attempts AND every check they failed" — both halves.

    A finding alone is unactionable: `read_back has 0 slots but 1 entry` does
    not say WHICH read-back, and the model cannot see what it wrote last time.
    """
    model = ScriptedModel(BROKEN, module_json())
    T.repair_loop(BROKEN, clause={"id": "m0001"}, model=model, max_attempts=2)
    repair_prompt = " ".join(m["content"] for m in model.calls[-1][1])
    assert "producing this is forbidden" in repair_prompt, \
        "the prior attempt's own text is missing, so the finding is unactionable"


def test_the_log_carries_the_REASON_not_just_the_verdict():
    """`this rule can never fire`, never `case C should have returned...`."""
    model = ScriptedModel(BROKEN, module_json())
    T.repair_loop(BROKEN, clause={"id": "m0001"}, model=model, max_attempts=2)
    repair_prompt = " ".join(m["content"] for m in model.calls[-1][1])
    assert "slot" in repair_prompt.lower(), \
        "the failing check's reason must reach the repair attempt"


def test_a_finding_from_a_LATER_stage_is_excluded_from_the_log():
    """Only stage-2 findings may be disclosed to a repair attempt.

    Later stages carry probe cases and their expected verdicts. Those route
    into the same node in the pipeline, and the log is persistent per clause —
    so one such finding appended once leaks the answer into every subsequent
    attempt, permanently.
    """
    leaky = T.RepairFinding(check_id="probe_mismatch", severity="error",
                            where="case C", message="should have returned no "
                            "violation", origin="stage3")
    rendered = T.render_error_log([("attempt 1", [leaky])])
    assert "should have returned" not in rendered
    assert "withheld" in rendered.lower(), \
        "an excluded finding must leave a visible hole, not vanish"


# --------------------------------------------------------------------------
#  Termination
# --------------------------------------------------------------------------

def test_an_abstention_TERMINATES_rather_than_being_repaired():
    """A model that says it cannot translate faithfully is not argued with.

    Re-prompting it produces exactly what abstention exists to prevent: a
    module that passes the checks and should not exist.
    """
    model = ScriptedModel(ABSTAINED)
    out = T.repair_loop(ABSTAINED, clause={"id": "m0001"}, model=model,
                        max_attempts=3)
    assert out.status == "abstained"
    assert len(model.calls) == 0, "an abstention must not be sent back at all"


def test_an_abstention_AFTER_a_failed_attempt_is_reported_separately():
    """Abstaining at attempt 2 is a repair-pressure artifact, not an answer.

    Counting it with first-attempt abstentions is how a model abstains its way
    out of the hard clauses while the abstention rate looks ordinary.
    """
    model = ScriptedModel(ABSTAINED)
    out = T.repair_loop(BROKEN, clause={"id": "m0001"}, model=model,
                        max_attempts=3)
    assert out.status == "abstained_under_repair", out.status
    assert out.attempts == 2


def test_exhausting_max_attempts_is_RECORDED_not_raised_and_not_passed():
    model = ScriptedModel(BROKEN, BROKEN, BROKEN)
    out = T.repair_loop(BROKEN, clause={"id": "m0001"}, model=model,
                        max_attempts=3)
    assert out.status == "unrepaired"
    assert out.attempts == 3
    assert out.findings, "the surviving findings must be kept"


def test_green_on_attempt_3_is_distinguishable_from_green_on_attempt_1():
    """Two different facts about the model. Averaging them hides the second."""
    # attempt 1 is the argument; the model supplies attempts 2 and 3.
    slow = T.repair_loop(BROKEN, clause={"id": "m0001"},
                         model=ScriptedModel(BROKEN, module_json()),
                         max_attempts=3)
    fast = T.repair_loop(module_json(), clause={"id": "m0001"},
                         model=ScriptedModel(module_json()), max_attempts=3)
    assert slow.status == fast.status == "translated"
    assert slow.attempts == 3 and fast.attempts == 1


def test_findings_per_attempt_is_recorded_so_NON_convergence_is_visIble():
    """Whether repair converges under this split is untested in the design.

    It has to be visible as data, not as a loop that quietly runs out.
    """
    out = T.repair_loop(BROKEN, clause={"id": "m0001"},
                        model=ScriptedModel(BROKEN, BROKEN, BROKEN),
                        max_attempts=3)
    assert len(out.per_attempt) == 3
    assert all(n > 0 for n in out.per_attempt)


# --------------------------------------------------------------------------
#  The gaming guard — a repair that goes green while making the module worse
# --------------------------------------------------------------------------

def test_a_repair_that_moves_a_predicate_from_requires_to_inputs_is_FLAGGED():
    """The cheapest way to clear an unresolved name, and it destroys the one
    distinction that makes linking possible: `requires` means another clause
    must define it, `inputs` means it arrives with the case. Collapse them and
    every translation looks fine."""
    dodge = module_json(requires=[], inputs=["restricted/1"])
    out = T.repair_loop(BROKEN, clause={"id": "m0001"},
                        model=ScriptedModel(dodge), max_attempts=2)
    assert out.status == "translated"
    assert "declaration-edit" in out.flags, out.flags


def test_a_repair_that_DELETES_the_offending_rule_is_FLAGGED():
    """Zero findings by removing the thing that was checked."""
    gutted = module_json(asserts=[], acts=[], closure=[])
    out = T.repair_loop(BROKEN, clause={"id": "m0001"},
                        model=ScriptedModel(gutted), max_attempts=2)
    assert "shrank" in out.flags, out.flags


def test_a_GENUINE_repair_is_NOT_flagged():
    """The negative control. Without it, `flags = ['declaration-edit']` on
    every repair passes both tests above and means nothing."""
    out = T.repair_loop(BROKEN, clause={"id": "m0001"},
                        model=ScriptedModel(module_json()), max_attempts=2)
    assert out.status == "translated"
    assert not out.flags, out.flags


def test_the_unclear_closure_RATE_is_reported():
    """Answering `unclear` everywhere is legal, grows the module, and restores
    the silent default the declaration exists to replace. No per-attempt diff
    shows that — only a rate does."""
    vague = module_json(closure=[dict(
        act_class="produce", closure="unclear",
        reason="the clause does not settle it")])
    out = T.repair_loop(BROKEN, clause={"id": "m0001"},
                        model=ScriptedModel(vague), max_attempts=2)
    assert out.unclear_closure_rate == pytest.approx(1.0)


# ==========================================================================
#  Wiring: the three things between a built loop and a live run
# ==========================================================================

def test_the_client_can_send_a_TRANSCRIPT_not_just_one_user_turn():
    """The loop is unreachable from the real client without this.

    `complete(system, user)` builds a two-message list internally, so there is
    no way to hand it turns 3, 4 and 5. Same request body otherwise — the
    response_format and the cost-relevant fields must not drift between the two
    entry points, or a repair attempt is quietly a different call.
    """
    prov = T.Provider("p", "openai-compatible", "m", "https://x/v1", "K",
                      0.2, 100, [1.0, 1.0])
    cfg = T.load_config(str(HERE / "config.json"))
    client = T.Client.__new__(T.Client)
    client.p, client.cfg, client.key = prov, cfg, "k"
    client.forcing = "json_schema"

    turns = [{"role": "user", "content": "clause"},
             {"role": "assistant", "content": "module"},
             {"role": "user", "content": "findings"}]
    body = client._body_messages("SYS", turns)
    assert [m["role"] for m in body["messages"]] == \
        ["system", "user", "assistant", "user"]
    assert body["messages"][1:] == turns, "the turns must go through verbatim"
    one = client._body("SYS", "clause")
    assert body["response_format"] == one["response_format"]
    assert body["max_tokens"] == one["max_tokens"]


def test_the_cost_gate_PRICES_the_repair_attempts():
    """With repair, one clause is up to `max_attempts` calls.

    A gate that prices one call per clause under-estimates by that factor —
    the one direction an estimate against a hard cap must never err in.

    ⚠️ THIS ASSERTION IS NEARLY BLIND and is kept only as a smoke test.
    `DEBUGGING_TIPS.md` §14: with `max_tokens=1000` and the strings `"sys"` /
    `"user"`, the OUTPUT term alone gives exactly 3×, so `three > one * 2.5`
    passes with the whole input term contributing nothing measurable. The real
    pins are in `test_cost_and_summary.py`, against a hand-priced worst case at
    realistic sizes.

    ⚠️ The strings are now realistic for a second reason:
    `translate._check_repair_log_budget` refuses to price a repair sequence
    whose `system + user` block is too small to absorb one repair-turn error
    log — which is exactly the case where the printed estimate would be low.
    """
    cfg = T.load_config(str(HERE / "config.json"))
    prov = T.Provider("p", "openai-compatible", "m", "u", "K", 0.2, 1000,
                      [1.0, 1.0])
    system, users = "s" * 33_506, ["u" * 5_341]
    one, _, _ = T.estimate_cost(system, users, prov, cfg, max_attempts=1)
    three, _, _ = T.estimate_cost(system, users, prov, cfg, max_attempts=3)
    assert three > one * 2.5, (one, three)


def test_a_live_run_WIRES_the_loop_and_records_what_it_did(tmp_path):
    """`run()` must actually invoke repair, and the record must show it.

    A loop nothing calls is the pass-looks-like-did-not-run failure in its
    largest form: every test green, and not one clause ever repaired.
    """
    import copy
    import json as _json
    cfg = copy.deepcopy(T.load_config(str(HERE / "config.json")))
    cfg["select"] = {"clause_ids": ["m0091"], "section_id": None,
                     "kinds": [], "limit": None}
    cfg["output"] = {"dir": str(tmp_path), "run_name": "t"}
    cfg["repair"] = {"max_attempts": 2}
    cfg["graveyard"] = {"dir": str(tmp_path / "gy"), "cap": 1000, "seed": 0,
                        "rates": {"repaired": 0.0, "first_try": 0.0}}

    class _Stub:
        calls = 0

        def __init__(self, *a, **k):
            pass

        def complete(self, system, user):
            _Stub.calls += 1
            return {"text": BROKEN, "in": 1, "out": 1, "finish_reason": "stop"}

        def complete_messages(self, system, messages):
            _Stub.calls += 1
            return {"text": module_json(clause_id="m0091"),
                    "in": 1, "out": 1, "finish_reason": "stop"}

    class A:
        clause = section = kinds = limit = provider = model = max_tokens = None
        live = True
        show_prompt = 0

    T.run(cfg, A(), client_factory=_Stub)
    rec = _json.load(open(tmp_path / "t" / "run.json"))["results"][0]
    assert rec["attempts"] == 2, rec
    assert rec["status"] == "translated"
    assert rec["per_attempt"] == [1, 0] or rec["per_attempt"][0] > 0, rec


def test_nothing_is_defined_below_the_main_guard():
    """Under `import` every definition exists; as a SCRIPT they do not.

    `run()` called `repair_loop`, which was defined after `if __name__ ==
    "__main__": raise SystemExit(main())`. Every test passed — tests import —
    and the first live invocation died with NameError, after paying for a call.
    A whole test suite cannot see this; only running the file can.
    """
    src = (HERE / "translate.py").read_text()
    guard = 'if __name__ == "__main__":'
    after = src[src.index(guard):]
    offenders = [ln for ln in after.splitlines()
                 if ln.startswith(("def ", "class "))]
    assert not offenders, offenders


# ==========================================================================
#  Observability: an unrepaired clause is the one you most need to read
# ==========================================================================

def test_the_transcript_keeps_the_FINAL_assistant_turn():
    """The last thing the model said is what you need to see when it failed.

    The loop appended the assistant turn only when preparing the NEXT prompt,
    so on exhaustion the final response was never added — and the stored
    transcript of a failed clause ended with our question rather than its
    answer. That is the exchange someone reads first.
    """
    out = T.repair_loop(BROKEN, clause={"id": "m0001"},
                        model=ScriptedModel(BROKEN), max_attempts=2)
    assert out.status == "unrepaired"
    assert out.transcript[-1]["role"] == "assistant", \
        [m["role"] for m in out.transcript]


def test_the_SURVIVING_findings_are_recorded_not_the_first_ones():
    """`per_attempt=[1,1]` cannot say whether it was the same finding twice.

    Without the final findings there is no way to tell a loop that is stuck
    from one that is trading one defect for another — which is exactly the
    question convergence turns on.
    """
    out = T.repair_loop(BROKEN, clause={"id": "m0001"},
                        model=ScriptedModel(module_json(requires=[])),
                        max_attempts=2)
    assert out.status == "unrepaired"
    assert out.findings, "no surviving findings recorded"
    assert "declares" in " ".join(f.message for f in out.findings), \
        "the recorded findings are attempt 1's, not the ones that survived"


# ==========================================================================
#  Four defects that made a run report better news than the truth.
#  Found independently by two clean reviews.
# ==========================================================================

def _run_one(tmp_path, cfg_over, stub, clause="m0091"):
    import copy, json as _json
    cfg = copy.deepcopy(T.load_config(str(HERE / "config.json")))
    cfg["select"] = {"clause_ids": [clause], "section_id": None, "kinds": [],
                     "limit": None}
    cfg["output"] = {"dir": str(tmp_path), "run_name": "t"}
    # ⚠️ ISOLATE THE GRAVEYARD. Without this every test that calls run() writes
    # into the repo's real `repair_graveyard/` — 16 entries appeared there on
    # the first suite run after wiring it in. Two consequences: a production
    # artifact filled with test garbage, and once it reached the cap, real runs
    # would refuse to start because of it.
    cfg["graveyard"] = {"dir": str(tmp_path / "gy"), "cap": 1000, "seed": 0,
                        "rates": {"repaired": 0.0, "first_try": 0.0}}
    cfg.update(cfg_over)

    class A:
        clause = section = kinds = limit = provider = model = max_tokens = None
        live = True
        show_prompt = 0
    code = T.run(cfg, A(), client_factory=stub)
    rec = _json.load(open(tmp_path / "t" / "run.json"))
    return code, rec


def test_an_UNREPAIRED_module_is_not_written_out_as_translated(tmp_path):
    """`if out.module is None` was the only failure branch.

    A module whose surviving breach is a corpus or link rule still CONSTRUCTS,
    so exhaustion was recorded as success — and the module's own `outcome`
    field then overwrote the loop's status. A fabricated citation, which the
    design calls the single worst failure available, survived repair and
    reported green.
    """
    forged = module_json(clause_id="m0091",
                         asserts=[fixtures.assertion(cites="m9999")])

    class Stub:
        def __init__(self, *a, **k): pass
        def complete(self, s, u):
            return {"text": forged, "in": 1, "out": 1, "finish_reason": "stop"}
        def complete_messages(self, s, m):
            return {"text": forged, "in": 1, "out": 1, "finish_reason": "stop"}

    code, rec = _run_one(tmp_path, {"repair": {"max_attempts": 2}}, Stub)
    r = rec["results"][0]
    assert r["status"] != "translated", r
    assert code == 1, "an unrepaired clause must not exit clean"


def test_stage_2_RUNS_on_a_module_that_passes_the_schema(tmp_path):
    """Half of stage 2 was reachable only via the repair path.

    `run()` gated the checks on whether `parse_module` RAISED, so a module that
    satisfied the schema was written without ever being compiled, link-checked,
    rule-shape checked or cycle checked. Two clauses were reported translated
    having never been near clingo.
    """
    clean = module_json(clause_id="m0091")

    class Stub:
        def __init__(self, *a, **k): pass
        def complete(self, s, u):
            return {"text": clean, "in": 1, "out": 1, "finish_reason": "stop"}
        def complete_messages(self, s, m):
            raise AssertionError("must not need repair")

    code, rec = _run_one(tmp_path, {"repair": {"max_attempts": 1}}, Stub)
    r = rec["results"][0]
    assert "n_findings" in r, "stage 2 did not run on a schema-valid module"


def test_the_transcripts_first_turn_is_the_prompt_that_was_ACTUALLY_SENT(tmp_path):
    """It was a synthesised stub: 491 chars against the 5,324 really sent.

    The eight cross-referenced clause texts were dropped, so repair ran without
    the definitions stage 1 calls load-bearing — and the stored transcript was
    a fiction of the exchange rather than a record of it.
    """
    class Stub:
        def __init__(self, *a, **k): pass
        def complete(self, s, u):
            Stub.sent = u
            return {"text": BROKEN, "in": 1, "out": 1, "finish_reason": "stop"}
        def complete_messages(self, s, m):
            return {"text": module_json(clause_id="m0091"),
                    "in": 1, "out": 1, "finish_reason": "stop"}

    import json as _json
    _run_one(tmp_path, {"repair": {"max_attempts": 2}}, Stub)
    tr = _json.load(open(tmp_path / "t" / "m0091.transcript.json"))
    assert tr[0]["content"] == Stub.sent, (
        f"turn 1 is {len(tr[0]['content'])} chars; "
        f"{len(Stub.sent)} were sent")


def test_a_provider_error_during_REPAIR_does_not_lose_the_whole_run(tmp_path):
    """`repair_loop` ran inside the `except ResponseParseError` handler, so it
    sat OUTSIDE the per-clause `except Phase1Error`. The same error on attempt 1
    was a per-clause failure; on attempt 2 it aborted everything and wrote a
    run.json with zero results — for clauses already billed."""
    class Stub:
        def __init__(self, *a, **k): pass
        def complete(self, s, u):
            return {"text": BROKEN, "in": 1, "out": 1, "finish_reason": "stop"}
        def complete_messages(self, s, m):
            raise T.ProviderError("the network went away")

    code, rec = _run_one(tmp_path, {"repair": {"max_attempts": 2}}, Stub)
    assert len(rec["results"]) == 1, "the billed clause vanished from the record"
    assert rec["results"][0]["status"] in ("error", "unrepaired"), rec


def test_abstained_UNDER_REPAIR_survives_into_the_record(tmp_path):
    """The loop distinguishes it; `run()` collapsed it back to `abstained`.

    `status=rec.get("status") or obj.outcome` — `rec` carries no status on the
    success path, so it always fell through to the module's own outcome. The
    comment above that line said the loop's status must never be overwritten.

    The distinction is the whole point: a first-attempt abstention is a real
    answer, and one produced after a failed attempt is repair pressure. Counted
    together, a model can abstain its way out of the hard clauses while the
    abstention rate looks ordinary.
    """
    class Stub:
        def __init__(self, *a, **k): pass
        def complete(self, s, u):
            return {"text": BROKEN, "in": 1, "out": 1, "finish_reason": "stop"}
        def complete_messages(self, s, m):
            return {"text": fixtures.abstention_json(
                clause_id="m0091",
                abstain_reason="it states a goal, not a condition"),
                "in": 1, "out": 1, "finish_reason": "stop"}

    _, rec = _run_one(tmp_path, {"repair": {"max_attempts": 2}}, Stub)
    assert rec["results"][0]["status"] == "abstained_under_repair", \
        rec["results"][0]["status"]


def test_the_repair_log_carries_ONLY_error_severity_findings():
    """A `note` is true of a CORRECT module and must never be shown as a fault.

    `requires-unprovided` fires on every well-formed single-clause module —
    `requires` means another clause defines it, and at single-module scope no
    other clause is linked. m0036 was handed eight of these under "Fix every one
    of them", twice, and never converged. The only way to clear one is to move
    the predicate into `inputs`, which destroys the distinction the design calls
    load-bearing.

    `checks.py` already rules that only errors drive repair. The log has to
    agree with that ruling or the loop asks for the impossible.
    """
    note = T.RepairFinding(check_id="requires-unprovided", severity="note",
                           where="m.lp", message="`x/1` is declared in "
                           "`%% requires:` and no module here defines it",
                           origin="link")
    err = T.RepairFinding(check_id="schema-breach", severity="error",
                          where="asserts[0]", message="read_back has 0 slots",
                          origin="schema")
    log = T.render_error_log([("attempt 1", [note, err])])
    assert "read_back has 0 slots" in log
    assert "requires-unprovided" not in log, log
    assert "no module here defines it" not in log, log


def test_a_log_of_only_notes_says_so_rather_than_looking_empty():
    """Otherwise the model is sent a prompt telling it to fix nothing."""
    note = T.RepairFinding(check_id="requires-unprovided", severity="note",
                           where="m.lp", message="declared and unprovided",
                           origin="link")
    log = T.render_error_log([("attempt 1", [note])])
    assert "no error-severity" in log.lower(), log
