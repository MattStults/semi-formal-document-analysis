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


def broken(tag):
    """A DIFFERENT broken module: the same breach, distinct bytes.

    ⚠️ Needed by every test about transcript growth, and the need is itself a
    contract. Since the freeze detector landed, a script that hands back the
    same text twice no longer exercises the accumulating chain at all — it
    exercises the RESTART. A test of turn structure that fed `BROKEN, BROKEN`
    would be silently testing the other branch, so the scripts below hand back
    a fresh breach each round and the repeat is written down only where it is
    the subject.
    """
    return module_json(asserts=[fixtures.assertion(
        read_back=f"producing this is forbidden ({tag})",
        read_back_slots=["M"])])


BROKEN2, BROKEN3, BROKEN4 = broken(2), broken(3), broken(4)

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
    model = ScriptedModel(BROKEN2, BROKEN3, module_json())
    T.repair_loop(BROKEN, clause={"id": "m0001", "quote": "Clause text."},
                  model=model, max_attempts=3)
    roles = [m["role"] for m in model.calls[-1][1]]
    assert roles == ["user", "assistant", "user", "assistant", "user"], roles


def test_the_transcript_PREFIX_is_byte_identical_as_it_grows():
    """Every turn after the first is then a cache hit.

    A loop that rebuilds the whole block each attempt re-sends the same tokens
    at full price. The only visible symptom is the bill.
    """
    model = ScriptedModel(BROKEN2, BROKEN3, module_json())
    T.repair_loop(BROKEN, clause={"id": "m0001", "quote": "Clause text."},
                  model=model, max_attempts=3)
    first, second = model.calls[0][1], model.calls[1][1]
    assert second[:len(first)] == first, "the prefix changed; caching is lost"
    assert model.calls[0][0] == model.calls[-1][0], \
        "the system block must be byte-identical too"


def test_the_clause_is_in_the_transcript_exactly_once():
    """It is carried by the conversation, so re-stating it wastes tokens and
    invites the model to treat the repeat as a second, different clause."""
    model = ScriptedModel(BROKEN2, module_json())
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
    model = ScriptedModel(BROKEN2, BROKEN3, module_json())
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
    model = ScriptedModel(BROKEN2, module_json())
    T.repair_loop(BROKEN, clause={"id": "m0001"}, model=model, max_attempts=2)
    repair_prompt = " ".join(m["content"] for m in model.calls[-1][1])
    assert "producing this is forbidden" in repair_prompt, \
        "the prior attempt's own text is missing, so the finding is unactionable"


def test_the_log_carries_the_REASON_not_just_the_verdict():
    """`this rule can never fire`, never `case C should have returned...`."""
    model = ScriptedModel(BROKEN2, module_json())
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
    model = ScriptedModel(BROKEN2, BROKEN3, BROKEN4)
    out = T.repair_loop(BROKEN, clause={"id": "m0001"}, model=model,
                        max_attempts=3)
    assert out.status == "unrepaired"
    assert out.attempts == 3
    assert out.findings, "the surviving findings must be kept"


def test_green_on_attempt_3_is_distinguishable_from_green_on_attempt_1():
    """Two different facts about the model. Averaging them hides the second."""
    # attempt 1 is the argument; the model supplies attempts 2 and 3.
    slow = T.repair_loop(BROKEN, clause={"id": "m0001"},
                         model=ScriptedModel(BROKEN2, module_json()),
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
                        model=ScriptedModel(BROKEN2, BROKEN3, BROKEN4),
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
                        model=ScriptedModel(BROKEN2), max_attempts=2)
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


# ==========================================================================
#  The freeze detector and the one restart
#  (`_debug_gen11/CHAIN_ANALYSIS.md`, 2026-08-15)
# ==========================================================================
#
# 96 stored repair chains. A chain whose every reply differs from every earlier
# reply ended `translated` 63 of 64 times (98%); a chain in which ANY reply
# repeats an earlier one ended translated 3 of 32 times (9%). Nothing about the
# defect predicts the outcome — not the number of round-1 findings, not the
# check_id, not the finding class, not the output length. The separator is
# whether the model is still producing answers it has not already produced.
#
# ⚠️ THE FIXTURES BELOW ARE FROZEN AND LOCAL, and no count of any live artifact
# appears in this section (`AGENTS.md`: never pin a count of a live artifact).
# `FROZEN_CHAIN` is a synthetic 5-turn chain whose reply 3 equals reply 1 —
# the oscillating shape (A, B, A) that adjacent-identity misses and
# repeat-of-any catches. It is not read from any run.

#: reply 1 is `BROKEN` (passed in as attempt 1), then B, then A again.
FROZEN_CHAIN = (BROKEN2, BROKEN, BROKEN3, BROKEN4)

#: the same length, never repeating: the negative control.
MOVING_CHAIN = (BROKEN2, BROKEN3, BROKEN4, broken(5))


class SpendingModel(ScriptedModel):
    """A ScriptedModel that also carries a per-clause spend counter.

    `dispatch_core.ClauseState.feed` sets `self.spent = 0.0` on its restart.
    Translation must NOT copy that: its gate is a run-level budget against a
    per-clause estimate, and re-basing spend at the restart makes the printed
    worst case a lie.
    """

    def __init__(self, *responses):
        super().__init__(*responses)
        self.spent_usd = 0.0

    def complete_messages(self, system, messages):
        env = super().complete_messages(system, messages)
        self.spent_usd += 0.001
        env["cost_usd"] = 0.001
        return env


def test_a_reply_that_REPEATS_AN_EARLIER_ONE_stops_the_chain():
    """PRE-FIX BEHAVIOUR THIS CATCHES: the loop ran the accumulating chain to
    `max_attempts` regardless, spending the whole budget on a model that had
    stopped answering. Reply 3 = reply 1, and the loop must not simply carry on
    to attempt 5 asking a frozen model a fourth time."""
    model = ScriptedModel(*FROZEN_CHAIN)
    out = T.repair_loop(BROKEN, clause={"id": "m0001"}, model=model,
                        max_attempts=5)
    assert out.restarted, "the repeat was not detected"
    # the repeat is at the 2nd scripted reply (reply 3 of the chain), so the
    # accumulating chain stopped there instead of running to attempt 5
    assert out.pre_restart_per_attempt == [1, 1, 1], out.pre_restart_per_attempt


def test_a_repeat_of_ANY_earlier_reply_counts_not_only_the_previous_one():
    """PRE-FIX / MIS-PORT BEHAVIOUR THIS CATCHES: `recurse_driver` and
    `dispatch_core` compare against `transcript[-2]` only. The attractor here
    is a small CYCLE, not a fixed point — one lost chain replies A,B,C,A,D —
    so adjacent identity caught 27 of the 29 lost gen-11 chains and
    repeat-of-any caught 29 of 29. `FROZEN_CHAIN` never repeats ADJACENTLY."""
    replies = (BROKEN,) + FROZEN_CHAIN
    assert not any(a == b for a, b in zip(replies, replies[1:])), \
        "the fixture must not repeat adjacently, or it tests nothing"
    out = T.repair_loop(BROKEN, clause={"id": "m0001"},
                        model=ScriptedModel(*FROZEN_CHAIN), max_attempts=5)
    assert out.restarted


def test_a_chain_that_KEEPS_MOVING_is_never_restarted():
    """The negative control, and the expensive half of the trade. 98% of
    chains whose replies keep changing converge; restarting one throws away a
    transcript that was working. Without this test a detector that fires on
    everything passes every other test in this section."""
    model = ScriptedModel(*MOVING_CHAIN)
    out = T.repair_loop(BROKEN, clause={"id": "m0001"}, model=model,
                        max_attempts=5)
    assert not out.restarted, "a moving chain was discarded"
    assert out.status == "unrepaired" and out.attempts == 5
    assert len(model.calls) == 4, "one call per repair round, no redraw"


def test_the_restarted_chain_starts_from_a_ONE_TURN_TRANSCRIPT():
    """The whole mechanism. The repair message was refuted as the cause (four
    frozen transcripts were repaired in ONE turn by a stand-in model from the
    exact accumulated bytes); what is left is the model anchoring on its own
    prior answer. Carrying any of those answers into the redraw carries the
    anchor with it, and the restart would be theatre."""
    model = ScriptedModel(*FROZEN_CHAIN)
    T.repair_loop(BROKEN, clause={"id": "m0001", "quote": "Clause text."},
                  model=model, first_user="THE REAL FIRST PROMPT",
                  max_attempts=5)
    # calls[0..1] are the accumulating chain; calls[2] is the redraw
    assert len(model.calls[1][1]) > 1, "the pre-restart chain did accumulate"
    redraw = model.calls[2][1]
    assert redraw == [{"role": "user", "content": "THE REAL FIRST PROMPT"}], \
        redraw
    sent = " ".join(m["content"] for c in model.calls[2:] for m in c[1])
    for stale in FROZEN_CHAIN[:2]:
        assert stale not in sent, "a discarded reply came back into context"


def test_the_restart_happens_EXACTLY_ONCE_and_a_refreeze_is_ABANDONED():
    """PRE-FIX BEHAVIOUR THIS CATCHES (the one the design most feared):
    restart-on-every-repeat is an unbounded loop and a runaway bill. The cap is
    one restart per clause, so the worst case stays 2 x max_attempts calls.
    4 of the 19 measured clauses refroze on a fresh draw; that tail is a
    translation defect, not a loop defect, and it is recorded rather than
    re-attempted."""
    # every reply the same after the redraw: it refreezes immediately
    model = ScriptedModel(BROKEN2, BROKEN, BROKEN3, BROKEN3)
    out = T.repair_loop(BROKEN, clause={"id": "m0001"}, model=model,
                        max_attempts=5)
    assert out.restarted
    assert out.status == "unrepaired", out.status
    assert "frozen" in out.flags, out.flags
    assert len(model.calls) == 4, \
        f"a second restart happened: {len(model.calls)} calls"


def test_frozen_is_a_FLAG_and_the_status_is_still_unrepaired():
    """`unrepaired` drives every downstream branch in `run()` and nothing about
    this clause's disposition changed — but "froze twice" has to be separable
    from "ran out of attempts" in later census work, and `graveyard.should_keep`
    keeps every `unrepaired` clause already, so the flag needs no sampling
    change to survive."""
    import graveyard
    out = T.repair_loop(BROKEN, clause={"id": "m0001"},
                        model=ScriptedModel(BROKEN2, BROKEN, BROKEN3, BROKEN3),
                        max_attempts=5)
    assert out.status == "unrepaired" and "frozen" in out.flags
    keep, why = graveyard.should_keep(out, 5, {}, clause_id="m0001")
    assert keep, why
    # and a chain that merely exhausted its attempts is NOT flagged frozen
    plain = T.repair_loop(BROKEN, clause={"id": "m0001"},
                          model=ScriptedModel(*MOVING_CHAIN), max_attempts=5)
    assert plain.status == "unrepaired" and "frozen" not in plain.flags


def test_a_restart_that_RECOVERS_is_reported_translated():
    """~9-12% of repeating chains do recover on their own, which is why the
    policy is stop-and-redraw and not stop-and-abandon: abandoning them saves
    20% of the calls and loses real modules. On the 19 clauses the 08-14 loop
    lost, continuing produced 0 modules in 95 calls and stop-and-restart
    produced 14 in 99."""
    out = T.repair_loop(BROKEN, clause={"id": "m0001"},
                        model=ScriptedModel(BROKEN2, BROKEN, module_json()),
                        max_attempts=5)
    assert out.status == "translated", out.status
    assert out.restarted
    # RE-BASED, as the design requires: the redraw's own attempt number, so
    # `should_keep`'s `attempts >= max_attempts` still means "this transcript
    # had one attempt left"
    assert out.attempts == 1, out.attempts


def test_the_per_clause_SPEND_IS_NOT_ZEROED_by_a_restart():
    """⛔ EXPLICITLY NOT COPIED from `dispatch_core.ClauseState.feed`, which
    sets `self.spent = 0.0` on its restart. Translation's cost gate is a
    run-level budget against a per-clause estimate; re-basing spend at the
    restart would make the printed worst case a lie, and a gate the loop can
    spend past is not a gate."""
    model = SpendingModel(*FROZEN_CHAIN)
    out = T.repair_loop(BROKEN, clause={"id": "m0001"}, model=model,
                        max_attempts=5)
    assert out.restarted
    assert model.spent_usd == pytest.approx(0.001 * len(model.calls)), \
        "spend was re-based across the restart"


def test_the_run_level_estimate_PRICES_the_restart():
    """The other half of the same contract. The restart makes the worst case
    two chains of `max_attempts` calls, and `estimate_cost`'s OUTPUT term is
    exactly linear in the turn count — so pricing one chain leaves the printed
    worst case 50% low, against a hard ledger cap."""
    cfg = T.load_config(str(HERE / "config.json"))
    prov = T.Provider("p", "openai-compatible", "m", "u", "K", 0.2, 1000,
                      [1.0, 1.0])
    system, users = "s" * 33_506, ["u" * 5_341]
    T_ = 3
    one, in_one, out_one = T.estimate_cost(system, users, prov, cfg,
                                           max_attempts=T_)
    twice, in_2t, out_2t = T.estimate_cost(system, users, prov, cfg,
                                           max_attempts=2 * T_)
    # ⛔ THE SHIM THAT LOOKS CONSERVATIVE AND IS NOT. `estimate_cost`'s dominant
    # term is `max_tokens · n · T(T-1)/2` — QUADRATIC in turns — so one chain of
    # 2T is far more than two chains of T. Shipped once, it refused config.json
    # against its own $0.25 ceiling. The multiplier is pinned so nobody
    # "simplifies" the doubling back into the argument.
    assert twice > 2.5 * one, (one, twice)
    assert out_2t == 2 * out_one, "the OUTPUT term is linear; the input is not"
    assert in_2t > 2 * in_one

    # what run() must actually print: EXACTLY twice the single-chain estimate
    printed, single = _dry_run_cost(HERE / "config.json")
    # `printed` is the %.4f the operator actually sees, so compare at that
    # resolution — the claim is "exactly twice", not "twice to 12 digits"
    assert printed == pytest.approx(2 * single, abs=1e-4), (printed, single)


class _NoArgs:
    clause = section = kinds = limit = provider = model = max_tokens = None
    live = False
    show_prompt = 0
    only_stale = False


def _dry_run_cost(path, monkey=None, limit=None):
    """(what run() PRINTS, what `estimate_cost` returned for ONE chain).

    The single-chain number is recorded by wrapping `estimate_cost` for the
    duration of the dry run rather than re-deriving the user blocks here — a
    second copy of run()'s selection/xref logic in a test is a second thing to
    keep equivalent, and it would drift.

    ⚠️ `monkey` is required for any config OUTSIDE `phase_1/`: a config's
    `corpus.path` and `prompt.system_files` are relative to the config, so the
    dry run has to happen with that directory as cwd — and it has to be undone,
    which is `monkeypatch.chdir`'s job and not this function's.
    """
    import contextlib
    import io
    import re as _re
    path = Path(path)
    real, seen = T.estimate_cost, []

    def spy(*a, **k):
        out = real(*a, **k)
        seen.append(out[0])
        return out

    args = _NoArgs()
    args.limit = limit
    buf = io.StringIO()
    T.estimate_cost = spy
    try:
        if monkey is not None:
            monkey.chdir(path.parent)
        with contextlib.redirect_stdout(buf):
            T.run(T.load_config(path.name if monkey is not None else str(path)),
                  args)
    finally:
        T.estimate_cost = real
    m = _re.search(r"cost \(worst\) : \$([0-9.]+)", buf.getvalue())
    assert m and seen, buf.getvalue()
    return float(m.group(1)), seen[-1]


def test_the_TWO_cost_call_sites_do_not_DRIFT():
    """Serial and concurrent must price identically, or a run is refused in one
    mode and sent in the other — the failure the shared gate exists to prevent.
    `translate_exec` re-expresses run()'s body call-for-call, so a textual pin
    is the honest one here: the two blocks must be the same arithmetic."""
    ser = (HERE / "translate.py").read_text()
    con = (HERE / "resolve_runs" / "graph_v2" / "translate_exec.py").read_text()
    double = "est, in_tok, out_tok = est * 2, in_tok * 2, out_tok * 2"
    assert ser.count(double) == 1 and con.count(double) == 1
    # ⛔ and NEITHER may feed a doubled TURN COUNT into the estimate: the
    # resent-completion term is quadratic, so `max_attempts * 2` over-charges
    # 4.5x and refused every shipped config at its own ceiling
    for name, src in (("translate.py", ser), ("translate_exec.py", con)):
        # CODE only — the prose above each call site quotes the wrong shim by
        # name so nobody reintroduces it, and must not trip its own pin
        code = "\n".join(ln for ln in src.splitlines()
                         if not ln.lstrip().startswith("#"))
        assert "max_attempts * 2" not in code, name
    # ⚠️ AND ONE PROSE SPELLING, because stripping `#` lines is exactly what
    # let the shim survive as PROSE: `repair_loop`'s docstring asserted "`run()`
    # prices the restart instead (`estimate_cost` is called with twice
    # `max_attempts`)" as current behaviour — the removed shim, stated as fact
    # in the docstring of the function whose restart it prices, which is how it
    # gets reintroduced. A docstring-wide pin is NOT attempted: prose has
    # unbounded paraphrases and any general matcher would either miss them or
    # fire on the rejection notices themselves. This pins the ONE spelling that
    # was wrong and that never has a correct use — the true statement is
    # "twice the RESULT", never twice the attempt count.
    for name, src in (("translate.py", ser), ("translate_exec.py", con)):
        assert "twice `max_attempts`" not in src, name
        assert "twice max_attempts" not in src, name


#: ⛔ SLICED BY DESIGN, and the config says so itself: `config_corpus_all`'s
#: `cost._ceiling_note` prices 773 nodes at "~$40" worst case against an $8.00
#: ceiling and explains that the ceiling is deliberately NOT the unbounded
#: worst case — the full corpus is never dispatched in one run, it is run in
#: `--limit` slices. Pinning the full-corpus price against the ceiling would
#: therefore pin a claim the config never made. What IS pinned for it is that a
#: real slice still fits, sized from the config's own `execution.batch_min_pending`
#: — a config-derived number rather than one invented here, and a slice that
#: size is unambiguously real.
#: ⛔ CORRECTED (review finding F-C, 2026-08-15): this used to justify that
#: size by claiming "below that, batch mode will not dispatch at all, so a
#: config whose smallest DISPATCHABLE slice is unaffordable is dead".
#: `dispatch_core.py:930-937` says the opposite in its own docstring — a flush
#: fires when the ready queue holds >= `batch_min_pending`, and "when nothing
#: is in flight and the queue is smaller, the queued items run LIVE
#: (starvation fallback — the tail and top of a tree never wait on a
#: threshold they cannot reach)". So a sub-threshold slice IS dispatchable.
#: The assertion was never wrong — 8 nodes is a real slice and it passes — but
#: the stated grounds were, and this round's own F3 was precisely "a docstring
#: asserting behaviour the code contradicts is how the wrong thing gets
#: reintroduced". Do not restore the "will not dispatch" claim.
#: The largest gate-passing slice at the time of the
#: 2026-08-15 review was 125 nodes (down from ~250 — the restart doubling
#: legitimately halves it); that figure is recorded in
#: `resolve_runs/graph_v2/EXPERIMENTS.md` and deliberately NOT pinned here,
#: because it is a live-artifact number and this repo forbids pinning those.
#:
#: ⭐ RULED 2026-08-15 (human): this ceiling STAYS AT $8.00. The remedy for the
#: halved slice is to run more, smaller slices — not to raise the ceiling — so
#: that the gate keeps its stopping power on the one run that commits the whole
#: corpus. Nothing here should be read as a claim that the full 773-node
#: selection is meant to pass in a single run; it is not, and it never was.
_SLICED_BY_DESIGN = {"config_corpus_all.json"}

#: Output snapshots, not shipped configurations. A config copied into a run
#: directory records what a past run was sent and must not be re-gated against
#: today's corpus.
#: ⛔ `_debug_gen11` ADDED 2026-08-15, and only after it actually bit. The
#: fix-round review asked whether this glob could CATCH files that are not
#: shipped configs, and cleared it because nothing then matched. Then an A/B
#: experiment wrote `_debug_gen11/prompt_ab/config_arm_b_d{1,2}.json` — arm-B
#: copies carrying a DELIBERATELY enlarged prompt — and both failed this pin,
#: which was measuring a scratch artifact against a ceiling it was never
#: shipped under. An experiment must be able to build an over-ceiling arm
#: without reddening the suite; that is what an arm is for.
#: ⚠️ SCOPED TO THE SCRATCH DIRECTORY, NOT TO A NAME PATTERN. Skipping
#: `*_arm_*` or `*_b_*` would hide a genuinely shipped config that happened to
#: be named that way — `config_arm_head.json` and friends ARE shipped and ARE
#: pinned here. The rule is WHERE it lives, not what it is called.
_NOT_A_SHIPPED_CONFIG = ("runs", "repair_graveyard", "translation_sample",
                         "__pycache__", "_debug_gen11")


def _shipped_configs():
    """Every `config*.json` reachable from `phase_1/` — discovered, not listed.

    ⚠️ A GLOB AND NOT A LITERAL LIST, deliberately. The pin this replaces read
    exactly one path (`HERE / "config.json"`) and so missed the one shipped
    configuration that was actually dead at its own ceiling
    (`resolve_runs/graph_v2/config_graph_nodes.json`). A hand-maintained list
    would have the same hole the day the next config lands.
    """
    out = []
    for p in sorted(HERE.rglob("config*.json")):
        rel = p.relative_to(HERE).parts
        if any(part in _NOT_A_SHIPPED_CONFIG or _re_run_dir(part)
               for part in rel[:-1]):
            continue
        out.append(p)
    assert out, "no shipped configs found — the glob is broken, not the repo"
    return out


def _re_run_dir(name):
    """`run1/`, `run2/`, … — numbered output directories.

    ⚠️ NOT `.*_runs`: `resolve_runs/` is where the graph configs SHIP, and a
    pattern that swallowed it would restore precisely the blind spot this
    parametrisation exists to remove.
    """
    import re as _re
    return bool(_re.fullmatch(r"run\d+", name))


#: ⚠️ THIS PIN WAS RED WHEN IT WAS WRITTEN, and how it went green is the part
#: worth keeping. `config_graph_nodes.json` priced $1.9940 against a $1.00
#: ceiling — `cost_gate` refused it before a single call — and it was carried
#: as an explicit `xfail(strict=True)` naming the pending decision rather than
#: quietly narrowed away. THE HUMAN THEN RULED (2026-08-15): raise that one
#: ceiling to exactly $2.00, because the restart's doubling is real cost and
#: not an estimation artefact. The mark came off in the same change. Nothing
#: about the pin was weakened to achieve it — ⛔ REJECTED BY NAME, then and
#: still: lowering the estimate, dropping a config from the parametrisation,
#: and a bare or silent xfail. `config_corpus_all.json`'s $8.00 ceiling was
#: deliberately NOT raised in the same ruling (see `_SLICED_BY_DESIGN`): the
#: run that commits the whole corpus is the one the gate must keep stopping,
#: so the answer there is more, smaller slices.
@pytest.mark.parametrize(
    "cfg_path", [pytest.param(p, id=str(p.relative_to(HERE)))
                 for p in _shipped_configs()])
def test_EVERY_shipped_config_passes_its_OWN_cost_gate(cfg_path, monkeypatch):
    """⛔ THE PIN THE BLOCKER NEEDED, WIDENED TO EVERY SHIPPED CONFIG. The
    suite priced the restart against a synthetic provider and never against a
    shipped config, so an over-charge that refused `config.json` at its own
    ceiling was green in every test. Then the pin that caught THAT read one
    path, and so was itself green while
    `resolve_runs/graph_v2/config_graph_nodes.json` was dead at its own
    ceiling. "Green in its own suite, dead in the real configuration" is the
    failure mode this project keeps hitting, and it survives a pin with a
    narrow field of view.

    ⚠️ NO LIVE COUNT AND NO PINNED DOLLAR FIGURE anywhere below: the assertion
    is the RELATION between the printed worst case and that config's own
    ceiling, so a config that legitimately grows a corpus still passes.
    """
    cfg = T.load_config(str(cfg_path))
    ceiling = float(cfg["cost"]["max_cost_usd"])
    limit = None
    if cfg_path.name in _SLICED_BY_DESIGN:
        limit = int((cfg.get("execution") or {}).get("batch_min_pending") or 1)
    printed, _ = _dry_run_cost(cfg_path, monkeypatch, limit=limit)
    what = ("the smallest dispatchable slice of this config"
            if limit else "this shipped config")
    assert printed <= ceiling, (
        f"{what} prices at ${printed:.4f} against its own ${ceiling:.2f} "
        f"ceiling — `cost_gate` would REFUSE it at --live, before a single "
        f"call is made")
    T.cost_gate(printed, cfg)          # the gate itself, on the same number


def test_the_STORED_transcript_keeps_BOTH_segments_and_says_where_it_broke():
    """A restart adds a second sampled draw to the clause's history. If the
    stored transcript kept only the surviving segment it would stop being a
    record of the exchange and become a fiction of it — the same failure the
    synthesised first prompt caused, and the one an unrepaired clause's reader
    hits first. What is SENT is clean; what is STORED is complete."""
    out = T.repair_loop(BROKEN, clause={"id": "m0001"},
                        model=ScriptedModel(*FROZEN_CHAIN), max_attempts=5)
    texts = [t["content"] for t in out.transcript]
    assert T.RESTART_MARKER_TEXT in texts, texts
    cut = texts.index(T.RESTART_MARKER_TEXT)
    assert BROKEN in texts[:cut], "the discarded segment was not kept"
    assert out.transcript[cut + 1]["role"] == "user", "the redraw begins clean"
    assert out.transcript[-1]["role"] == "assistant"
    # ⚠️ every stored turn must stay WIRE-LEGAL: `self_diagnose.py` appends a
    # question to a stored transcript and SENDS it, and `_body_messages` copies
    # each turn verbatim, so an invented role or an extra key is a rejected
    # request the day somebody diagnoses a restarted clause
    for t in out.transcript:
        assert set(t) == {"role", "content"}, t
        assert t["role"] in ("user", "assistant"), t
    # ⚠️ AND THE ASSUMPTION THAT MAKES THAT ENOUGH, PINNED RATHER THAN LEFT
    # IMPLICIT (group review P3): the marker turn creates the only two adjacent
    # same-role turns any stored transcript contains, and re-sending it is legal
    # ONLY because the provider is OpenAI-compatible and tolerates them.
    # Endpoints that enforce strict alternation exist. If this project ever
    # points at one, fold the marker into the redraw's first user turn — do NOT
    # give it an invented role or an extra key, which is the failure above.
    roles = [t["role"] for t in out.transcript]
    same = [i for i, (a, b) in enumerate(zip(roles, roles[1:])) if a == b]
    assert same == [cut], (same, roles)


def test_an_abstention_AFTER_A_RESTART_is_not_counted_as_a_first_answer():
    """`attempts` is re-based by the restart, so `n == 1` no longer means "the
    model's first word on this clause". Without this the loop would report a
    post-restart abstention as a first-class `abstained` — exactly the
    accounting the abstained_under_repair split exists to prevent."""
    out = T.repair_loop(BROKEN, clause={"id": "m0001"},
                        model=ScriptedModel(BROKEN2, BROKEN, ABSTAINED),
                        max_attempts=5)
    assert out.restarted
    assert out.status == "abstained_under_repair", out.status


def test_the_loop_does_not_PARAPHRASE_or_RE_RENDER_to_break_a_freeze():
    """⛔ REJECTED BY NAME, and the rejection is the finding: paraphrasing the
    repair message, raising the temperature on repair rounds, and re-rendering
    the full finding history. Four frozen transcripts were repaired in ONE turn
    by a stand-in model from the exact accumulated bytes DeepSeek froze on, so
    the message is sufficient and the defect is the CONTEXT IT ARRIVES IN. All
    three vary the prompt — changing a measured artifact to fix an unmeasured
    one. The redraw's first turn is therefore byte-identical to the original.

    ⚠️ THAT LAST SENTENCE IS TRUE OF THE LOOP AND NOT ALWAYS OF THE WIRE
    (adversarial review 2026-08-15, F4; ACCEPTED). `repair_loop` never varies
    it, but `Client._vary_identical_retry` can append a contentless
    `[transport retry N: …]` line to it if attempt 1's identical body is
    already recorded failed — reachable via a truncated attempt 1 under
    `resample_truncation`. Grounds, the reachable path and the two claims that
    go false are in `_vary_identical_retry`'s docstring. This test asserts the
    loop-level claim, which is the one the rejection doctrine is about."""
    model = ScriptedModel(*FROZEN_CHAIN)
    out = T.repair_loop(BROKEN, clause={"id": "m0001"}, model=model,
                        first_user="THE REAL FIRST PROMPT", system="SYS",
                        max_attempts=5)
    # ⚠️ WITHOUT THIS LINE THIS TEST MEASURED NOTHING (group review P1): with
    # the detector disabled no redraw happens, `calls[2]` is an ordinary repair
    # round, and "its first turn equals call 1's first turn" is trivially true
    # because the transcript PREFIX never changes. The claim is about the
    # REDRAW, so the redraw has to have happened.
    assert out.restarted, "no restart: the assertions below are vacuous"
    redraw = model.calls[2][1]
    assert len(redraw) == 1, redraw
    assert redraw[0] == model.calls[0][1][0], \
        "the redraw's first turn was rewritten"
    assert len({c[0] for c in model.calls}) == 1, \
        "the system block changed between rounds"
    # attempt 1's error log and the redraw's carry the same rendering
    logs = [m["content"] for c in model.calls for m in c[1]
            if m["role"] == "user" and "failed these checks" in m["content"]]
    bodies = {"\n".join(log.split("\n")[1:]) for log in logs}
    assert len(bodies) == 1, bodies   # same findings, same rendering, verbatim


# ==========================================================================
#  The repair log repeats itself
#  (`_debug_gen11/CHAIN_ANALYSIS.md` §4.6 — separate from the loop change,
#   and deliberately so: bundled together neither could be attributed)
# ==========================================================================

def test_an_IDENTICAL_finding_is_shown_ONCE_with_a_count():
    """PRE-FIX BEHAVIOUR THIS CATCHES: one name used at four body sites
    produced four byte-identical lines. `where` is `<root>` for the declaration
    checks, so these are not similar lines, they are the same line — a measured
    log carried 6 lines for 4 distinct problems, another 9 for 3. The repeat
    says nothing the first line did not, spends the repair-turn budget, and
    makes a small defect look like a large one.

    ⛔ NOT a rewording. Paraphrasing the repair message is rejected by name;
    every finding's own text goes through verbatim.
    """
    def dup(name):
        return T.RepairFinding(
            check_id="schema-breach", severity="error", where="<root>",
            message=f"body references `{name}` but nothing declares it",
            origin="schema")

    log = T.render_error_log([("attempt 1", [dup("a"), dup("b"), dup("a"),
                                             dup("c"), dup("a")])])
    lines = [ln for ln in log.split("\n") if ln.startswith("  - [")]
    assert len(lines) == 3, lines
    assert sum("`a`" in ln for ln in lines) == 1
    assert "× 3" in " ".join(lines), lines
    # the finding's own text is untouched, and the ORDER is the checks' order
    assert lines[0].startswith(
        "  - [schema-breach] <root>: body references `a` but nothing "
        "declares it")
    assert "`b`" in lines[1] and "`c`" in lines[2]


def test_findings_that_DIFFER_ANYWHERE_are_never_collapsed():
    """The negative control. `where` is what separates two real occurrences of
    one check, and a dedupe on `message` alone would hide half the module."""
    a = T.RepairFinding("schema-breach", "error", "asserts[0]", "same text",
                        "schema")
    b = T.RepairFinding("schema-breach", "error", "asserts[1]", "same text",
                        "schema")
    c = T.RepairFinding("link-missing", "error", "asserts[0]", "same text",
                        "link")
    log = T.render_error_log([("attempt 1", [a, b, c])])
    assert len([ln for ln in log.split("\n") if ln.startswith("  - [")]) == 3
    assert "×" not in log, log


# --------------------------------------------------------------------------
#  The graveyard seams (group adversarial review D2, D3)
# --------------------------------------------------------------------------

def test_a_restarted_and_recovered_clause_is_sampled_as_REPAIRED():
    """PRE-FIX BEHAVIOUR THIS CATCHES: `attempts` is re-based by the restart, so
    a clause that burned four calls, froze, was redrawn and then recovered
    arrived at `graveyard.should_keep` with `attempts == 1` and was bucketed
    `first_try` — 5% under the shipped rates against 25% for an ordinary
    repair. The single most diagnostically valuable outcome this loop produces
    would have been kept at a fifth of the rate of the ordinary one.

    ⚠️ The `attempts >= max_attempts` branch is a DIFFERENT question and is
    correctly left reading the re-based number: it asks about the transcript
    that produced the result. This one asks how much work the clause took.
    """
    import graveyard
    out = T.repair_loop(BROKEN, clause={"id": "m0001"},
                        model=ScriptedModel(BROKEN2, BROKEN, module_json()),
                        max_attempts=5)
    assert out.status == "translated" and out.restarted and out.attempts == 1
    keep, why = graveyard.should_keep(
        out, 5, {"repaired": 1.0, "first_try": 0.0}, clause_id="m0001")
    assert keep, "a restarted chain was bucketed as a first-try"
    assert "repaired" in why, why
    keep, _ = graveyard.should_keep(
        out, 5, {"repaired": 0.0, "first_try": 1.0}, clause_id="m0001")
    assert not keep, "a restarted chain is still being sampled as a first-try"


def test_the_graveyard_ENTRY_does_not_contradict_its_own_transcript(tmp_path):
    """PRE-FIX BEHAVIOUR THIS CATCHES: `entry.json` recorded `attempts: 1`
    beside a `transcript.json` holding twelve turns and a restart marker. A
    graveyard entry is read BY HAND — that is the whole reason the directory
    exists — and a self-contradictory one costs more than it tells."""
    import graveyard
    out = T.repair_loop(BROKEN, clause={"id": "m0001"},
                        model=ScriptedModel(BROKEN2, BROKEN, BROKEN3, BROKEN3),
                        max_attempts=5)
    path = graveyard.write_entry(str(tmp_path), {"id": "m0001"}, out,
                                 reason="test", contract_hash="c",
                                 provenance_hash="p")
    import json as _json
    entry = _json.load(open(f"{path}/entry.json"))
    stored = _json.load(open(f"{path}/transcript.json"))
    assert entry["restarted"] is True, entry
    assert entry["pre_restart_per_attempt"], entry
    assert T.RESTART_MARKER_TEXT in [t["content"] for t in stored]
    assert len(stored) > 2 * entry["attempts"], (len(stored), entry["attempts"])


def test_a_flag_earned_BEFORE_the_restart_does_not_ride_onto_the_new_module():
    """⭐ RULED, and the alternative is rejected by name in
    `RepairOutcome.pre_restart_flags`: a flag is a SHAPE DIFF between two
    drafts, and a restart throws its drafts away.

    PRE-FIX BEHAVIOUR THIS CATCHES: a `shrank` earned by a discarded draft rode
    through onto a clean redrawn module — `run()` printed `⚠️ shrank` against a
    module that never shrank, `run.json` recorded a claim about bytes nobody
    kept, and `should_keep`'s force-keep on `if flags:` routed the clause into
    the graveyard on the strength of a draft. That is precisely the population
    distortion `restarted` was made a field rather than a flag to avoid,
    arriving through the other door.
    """
    import graveyard
    # shrank AND still broken: the ontology that derived `disallowed/1` is
    # gone, so the assertion body references an undeclared name
    shrunk_broken = module_json(ontology=[])
    out = T.repair_loop(BROKEN, clause={"id": "m0001"},
                        model=ScriptedModel(shrunk_broken, BROKEN,
                                            module_json()),
                        max_attempts=5)
    assert out.status == "translated" and out.restarted
    assert out.flags == [], out.flags
    # NOT LOST — moved, and written into the graveyard entry
    assert "shrank" in out.pre_restart_flags, out.pre_restart_flags
    # and the discarded draft no longer force-keeps the clause
    keep, why = graveyard.should_keep(
        out, 5, {"repaired": 0.0, "first_try": 0.0}, clause_id="m0001")
    assert not keep, why


def test_a_NON_PARSING_redraw_does_not_inherit_the_discarded_shape():
    """⭐ THE OTHER DOOR INTO THE SAME DISTORTION, and the reason the test
    above does not cover it: its redraw PARSES, so the shape baseline is
    overwritten no matter what the fallback does.

    PRE-FIX BEHAVIOUR THIS CATCHES: the restart cleared `flags` but left
    `prev_shape = _shape(raw) or prev_shape`. When the redraw does not parse,
    `_shape` returns `{}` and the `or` RETAINED the discarded draft's counts —
    so the next post-restart module was diffed against bytes nobody kept, wore
    a `shrank` it never earned, and `should_keep`'s force-keep on `if flags:`
    routed a clean converged clause into the graveyard. Same population
    distortion as `pre_restart_flags`, arriving through the shape baseline
    instead of the flag list.

    The chain: a BIG draft, repeated verbatim (the freeze) → restart → a
    redraw that is not JSON at all → a small but VALID module. Nothing after
    the restart ever shrank, because the only parsed post-restart shape is the
    last one.
    """
    import graveyard
    bad = fixtures.assertion(read_back="producing this is forbidden",
                             read_back_slots=["M"])       # a real breach
    big = module_json(claims=["C1 a", "C2 b", "C3 c", "C4 d"],
                      asserts=[bad, bad, bad])
    not_json = "sorry, I cannot produce JSON for this clause"
    out = T.repair_loop(big, clause={"id": "m0001"},
                        model=ScriptedModel(big, not_json, module_json()),
                        max_attempts=5)
    assert out.restarted and out.status == "translated", out.status
    assert out.flags == [], (
        f"{out.flags} — earned against the DISCARDED draft's shape; the "
        f"redraw did not parse and its `{{}}` shape was overwritten by the "
        f"pre-restart one")
    keep, why = graveyard.should_keep(
        out, 5, {"repaired": 0.0, "first_try": 0.0}, clause_id="m0001")
    assert not keep, why


def test_a_flag_earned_AFTER_the_restart_is_still_reported():
    """The negative control for the rule above. Clearing flags at the restart
    must not disarm the guards for the rest of the clause's life — the guards
    are the reason a repair that goes green while making the module worse is
    visible at all."""
    gutted = module_json(asserts=[], acts=[], closure=[])
    out = T.repair_loop(BROKEN, clause={"id": "m0001"},
                        model=ScriptedModel(BROKEN2, BROKEN, BROKEN3, gutted),
                        max_attempts=5)
    assert out.restarted and out.status == "translated"
    assert "shrank" in out.flags, out.flags
