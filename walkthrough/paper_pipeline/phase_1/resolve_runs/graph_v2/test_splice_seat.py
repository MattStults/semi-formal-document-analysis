"""Pins for the three repaired_verification.md fixes to promise_repair
(2026-08-14), each RED against the ds7 defect it names:

  FIX 1  the SPLICE ADJUDICATION SEAT -- every mechanical guard answers
         WHERE to aim a splice; none asked whether the receiving node's
         content establishes the concept, and 4 of 26 ds7 splices were
         wrong claims (R1 spliced prose asserting the NEGATION of the
         document's principle onto a commentary line);
  FIX 2  NARRATION MISMATCH -- a redraw whose reason says "I will add a
         provides entry ..." and then adds none was booked as an honest
         decline;
  FIX 3  SELF-LOOPS -- the repair made 3 nodes need a name they provide.

⛔ The seat's TRANSPORT and PARSE behaviour is pinned against the real
`splice_seat.judge`. Its MEANING judgment is a model call, so these
stage-level pins drive it with a stand-in judge that reads the prompt
and applies one written rule (a passage containing a negation marker
does not establish the concept). That stand-in tests the WIRING -- that
a does_not_establish verdict blocks the splice and that the prompt the
seat would send is blind on the name -- and claims nothing about model
accuracy, which is the seat brief's business.

Offline throughout: no network, $0.
"""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (PHASE1, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import translate as T           # noqa: E402
import recurse_driver as R      # noqa: E402
import promise_repair as PR     # noqa: E402
import splice_seat as SS        # noqa: E402

NAME = "vault_logging_duty"
PROSE = "The duty to log every retrieval from the vault."
SEED = {"name": NAME, "prose": PROSE, "established_around": [3, 4]}

#: the fixture document in two versions, identical but for lines 3-4
_DOC = ["# Archive Rules", ""] + ["filler line"] * 18
ESTABLISHING = list(_DOC)
ESTABLISHING[2] = ("Staff must log every retrieval from the vault, "
                   "without exception.")
ESTABLISHING[3] = "The log is kept at the front desk."
NEGATING = list(_DOC)
NEGATING[2] = ("Commentary: staff need not log retrievals from the "
               "vault; no logging duty applies.")
NEGATING[3] = "This commentary may be controversial."

#: negation / mention markers the stand-in judge reads. NOT a model.
_NEG_MARKERS = ("need not", "no logging duty", "commentary", "does not")


class SeatClient(R.MockClient):
    """Redraws come off the scripted list; seat calls are answered by the
    stand-in judge (or by a fixed verdict / raw text when one is given).
    Seat calls are counted separately so `calls` keeps meaning redraws."""

    def __init__(self, replies, verdict=None, raw=None, boom=None):
        R.MockClient.__init__(self, replies)
        self.seat_calls, self.seat_prompts = 0, []
        self.verdict, self.raw, self.boom = verdict, raw, boom

    def complete(self, system, user):
        if system != SS.BRIEF:
            return R.MockClient.complete(self, system, user)
        self.seat_calls += 1
        self.seat_prompts.append(user)
        if self.boom is not None:
            raise self.boom
        if self.raw is not None:
            return {"text": self.raw, "usage": {}}
        v = self.verdict
        if v is None:
            passage = user.split("THE PASSAGE PROPOSED AS ITS "
                                 "ESTABLISHMENT:")[1].lower()
            v = ("does_not_establish"
                 if any(m in passage for m in _NEG_MARKERS)
                 else "establishes")
        return {"text": json.dumps({"verdict": v,
                                    "grounds": "(stand-in judge)"}),
                "usage": {}}


def _reply(lo, hi, provides=(), needs=(), jcs=None):
    g = {"nodes": [{"id": f"L{lo}-{hi}_n001", "establishes": "claim",
                    "needs": [dict(d) for d in needs],
                    "provides": [dict(p) for p in provides],
                    "spans": [{"lines": [lo, hi]}]}],
         "uncovered": []}
    if jcs is not None:
        g["judgment_calls"] = list(jcs)
    return g


def _run(tmp_path, target_needs=(), extra_nodes=()):
    """A one-plan promise repair: the needer at L13-20 wants NAME, the
    node covering the establishment lines is L1-12_n001."""
    run = tmp_path / "run"
    run.mkdir(parents=True)
    R.write_json(os.path.join(str(run), "division.json"),
                 {"decision": "divide", "seed_vocabulary": [dict(SEED)],
                  "children": [{"span": [1, 12]}, {"span": [13, 20]}]})
    nodes = [
        {"id": "L1-12_n001", "establishes": "the receiving passage",
         "needs": [dict(d) for d in target_needs], "provides": [],
         "spans": [{"lines": [1, 6]}]},
        {"id": "L13-20_n001", "establishes": "the needer",
         "needs": [{"name": NAME, "prose": "relies on the logging duty"}],
         "provides": [], "spans": [{"lines": [13, 14]}]}]
    nodes.extend(json.loads(json.dumps(list(extra_nodes))))
    R.write_json(os.path.join(str(run), "root_graph.json"),
                 {"nodes": nodes})
    R.write_json(os.path.join(str(run), "fixup_queue.json"),
                 {"items": [{"kind": "broken_promise", "verdict": "reject",
                             "detail": {"unwind": str(run), "name": NAME},
                             "reason": "needs regeneration"}]})
    return str(run)


def _cfg(**pr):
    return {"leaf_max_lines": 15, "price_per_mtok": [0.14, 0.28],
            "promise_repair": dict({"max_cost_usd": 0.25}, **pr)}


def _delivering_reply(needs=()):
    return _reply(1, 12, provides=[{"name": NAME, "prose": PROSE}],
                  needs=needs)


def _row(rep, name=NAME):
    return next(r for r in rep["items"] if r["name"] == name)


# ==========================================================================
#  FIX 1 -- the splice adjudication seat
# ==========================================================================

def test_negating_passage_is_rejected_and_nothing_is_spliced(tmp_path):
    """RED (THE ds7 DEFECT, R1): every mechanical guard passes -- the
    redraw delivers the entry at the establishment lines, a root node
    covers them, no duplicate name, not an authority-assignment node --
    and the receiving passage says the OPPOSITE of the concept. Without
    the seat this splices a false claim into the production graph."""
    run = _run(tmp_path)
    rep = PR.run_repair(run, _cfg(), SeatClient([_delivering_reply()]),
                        list(NEGATING))
    assert rep["repaired"] == 0
    assert rep["rejected_by_splice_seat"] == 1
    row = _row(rep)
    assert row["status"] == "rejected_by_splice_seat"
    assert "does not establish" in row["why"] and "stand-in" in row["why"]
    assert rep["by_class"]["promise"]["rejected_by_splice_seat"] == 1
    # the graph copy is CONTENT-IDENTICAL: no provides, no needs, no
    # provenance rows -- a rejected splice changes nothing
    fixed = json.load(open(os.path.join(run, "root_graph.repaired.json")))
    orig = json.load(open(os.path.join(run, "root_graph.json")))
    assert fixed["nodes"] == orig["nodes"]
    assert "promise_repairs" not in fixed
    assert rep["danglings_after"] == rep["danglings_before"] == 1
    assert rep["needers_resolved"] == 0, \
        "a rejected splice must not be counted as resolving anything"


def test_establishing_passage_is_spliced(tmp_path):
    """The same fixture, the same mechanical path, a passage that DOES
    establish the concept: the gate lets it through unchanged."""
    run = _run(tmp_path)
    client = SeatClient([_delivering_reply()])
    rep = PR.run_repair(run, _cfg(), client, list(ESTABLISHING))
    assert rep["repaired"] == 1 and rep["rejected_by_splice_seat"] == 0
    assert client.seat_calls == 1, "one seat call per delivered redraw"
    fixed = json.load(open(os.path.join(run, "root_graph.repaired.json")))
    assert any(R.nm(p) == NAME for p in fixed["nodes"][0]["provides"])
    assert rep["needers_resolved"] == 1
    # the verdict rides ON THE ARTIFACT, with its grounds
    pr0 = fixed["promise_repairs"][0]
    assert pr0["splice_seat"]["verdict"] == "establishes"
    assert pr0["splice_seat"]["grounds"]
    assert rep["splice_seat"] == "on" and rep["splice_seat_calls"] == 1


def test_the_seat_prompt_is_blind_on_the_name(tmp_path):
    """⛔ The failure mode is a plausible NAME papering over a passage
    that says something else. The prompt carries the concept's prose and
    the receiving node's own claim + span text -- and never the name."""
    run = _run(tmp_path)
    client = SeatClient([_delivering_reply()])
    PR.run_repair(run, _cfg(), client, list(ESTABLISHING))
    prompt = client.seat_prompts[0]
    assert NAME not in prompt, "the seat was shown the predicate name"
    assert PROSE in prompt
    assert "the receiving passage" in prompt, "the node's own claim"
    assert "Staff must log every retrieval" in prompt, "the span text"
    # and the receiving node is the one adjudicated, not the needer
    assert "relies on the logging duty" not in prompt


def test_seat_off_is_byte_parity_with_an_accepted_verdict(tmp_path):
    """`splice_seat: false` is the pre-fix behaviour exactly: no seat
    call, and a repaired graph byte-identical to the seat-ON run whose
    verdict was `establishes`. The gate decides WHETHER to merge; it
    never changes WHAT is merged."""
    on = _run(tmp_path / "a")
    PR.run_repair(on, _cfg(), SeatClient([_delivering_reply()]),
                  list(ESTABLISHING))
    off_client = SeatClient([_delivering_reply()])
    off = _run(tmp_path / "b")
    PR.run_repair(off, _cfg(splice_seat=False), off_client,
                  list(ESTABLISHING))
    assert off_client.seat_calls == 0, "seat off must not call the seat"

    def _canon(run_dir):
        g = json.load(open(os.path.join(run_dir,
                                        "root_graph.repaired.json")))
        for pr in g.get("promise_repairs", []):
            pr.pop("splice_seat", None)      # the only recorded delta
            pr["redraw_artifact"] = pr["unwind"] = ""   # tmp-path dependent
        return json.dumps(g, sort_keys=True)
    assert _canon(on) == _canon(off)


def test_seat_off_reproduces_the_defect_it_gates(tmp_path):
    """The RED half of the pin above: with the gate off, the negating
    passage is spliced -- the exact ds7 R1 outcome. Turning the gate off
    is therefore a deliberate, visible choice, recorded on the report."""
    run = _run(tmp_path)
    rep = PR.run_repair(run, _cfg(splice_seat=False),
                        SeatClient([_delivering_reply()]), list(NEGATING))
    assert rep["repaired"] == 1 and rep["splice_seat"] == "off"
    fixed = json.load(open(os.path.join(run, "root_graph.repaired.json")))
    assert any(R.nm(p) == NAME for p in fixed["nodes"][0]["provides"])


def test_unparseable_seat_reply_fails_closed_in_the_stage(tmp_path):
    """Fail-closed end to end: garbage from the seat blocks the splice
    (never accepts it), and the parse problem is the recorded grounds."""
    run = _run(tmp_path)
    rep = PR.run_repair(run, _cfg(),
                        SeatClient([_delivering_reply()],
                                   raw="I think it probably establishes it"),
                        list(ESTABLISHING))
    assert rep["repaired"] == 0 and rep["rejected_by_splice_seat"] == 1
    assert "unparseable" in _row(rep)["why"]
    fixed = json.load(open(os.path.join(run, "root_graph.repaired.json")))
    assert fixed["nodes"][0]["provides"] == []


# ---------------------------------------------------------- judge() unit
def test_judge_fails_closed_on_every_malformed_reply():
    for text in ("", "not json", "{}", '{"verdict": "maybe"}',
                 '{"verdict": "same_concept"}', "[]"):
        v = SS.judge(lambda s, u: {"text": text}, "p")
        assert v["verdict"] == "does_not_establish", text
        assert "fail-closed" in v["grounds"]
    ok = SS.judge(lambda s, u: {"text": json.dumps(
        {"verdict": "establishes", "grounds": "the text states it"})}, "p")
    assert ok == {"verdict": "establishes", "grounds": "the text states it"}


def test_judge_sets_the_schema_slot_and_uses_the_brief():
    seen = {}

    def complete(system, user):
        seen["system"] = system
        return {"text": json.dumps({"verdict": "establishes", "grounds": ""})}
    slots = []
    SS.judge(complete, "prompt", schema_slot=slots.append)
    assert slots == [SS.SCHEMA]
    assert seen["system"] == SS.BRIEF
    assert "does_not_establish" in SS.BRIEF and "NEGATION" in SS.BRIEF


def test_transient_transport_is_retried_then_fails_closed(monkeypatch):
    monkeypatch.setattr(SS.time, "sleep", lambda *_a: None)
    tries = []

    def flaky(system, user):
        tries.append(1)
        raise T.ProviderError("HTTP 429 rate limited")
    v = SS.judge(flaky, "p")
    assert len(tries) == 3
    assert v["verdict"] == "does_not_establish" and "3 attempts" in v["grounds"]


def test_cost_gate_and_terminal_transport_propagate(monkeypatch):
    """⛔ The rename_seat carve-outs, verbatim: a ceiling that has said
    stop must not be retried, and a 402/401/403 or key-resolution error
    fails EVERY later call identically -- fail-closing those would grind
    a paid stage into silent all-rejections instead of stopping."""
    monkeypatch.setattr(SS.time, "sleep", lambda *_a: None)

    def gate(system, user):
        raise T.CostGateError("ceiling reached")
    with pytest.raises(T.CostGateError):
        SS.judge(gate, "p")
    for msg in ("HTTP 402 payment required", "HTTP 401 unauthorized",
                "HTTP 403 forbidden", "no key for $TOGETHER_API_KEY",
                "Refusing to build a live client"):
        def terminal(system, user, _m=msg):
            raise T.ProviderError(_m)
        with pytest.raises(T.ProviderError):
            SS.judge(terminal, "p")


def test_seat_transport_errors_stop_the_stage_not_the_splice(tmp_path):
    """A CostGateError from the seat propagates out of run_repair: the
    stage stops loudly rather than booking a rejection it did not judge."""
    run = _run(tmp_path)
    with pytest.raises(T.CostGateError):
        PR.run_repair(run, _cfg(),
                      SeatClient([_delivering_reply()],
                                 boom=T.CostGateError("ceiling")),
                      list(ESTABLISHING))


def test_splice_without_a_seat_is_the_mechanical_unit_path():
    """`splice(seat=None)` keeps the pure-merge contract the mechanical
    pins use -- the MANDATORY gate lives in run_repair, which builds a
    seat whenever `promise_repair.splice_seat` is true (the default)."""
    g = {"nodes": [{"id": "L1-12_n001", "establishes": "x", "needs": [],
                    "provides": [], "spans": [{"lines": [1, 6]}]}]}
    status, target = PR.splice(g, dict(SEED), _delivering_reply(), "u", ".")
    assert (status, target) == ("repaired", "L1-12_n001")
    assert PR.splice.__defaults__[-1] is None      # seat defaults off
    import inspect
    assert (inspect.signature(PR.run_repair).parameters
            and "splice_seat" in PR.__doc__)


# ==========================================================================
#  FIX 2 -- narration mismatch is not an honest decline
# ==========================================================================

@pytest.mark.parametrize("text", [
    "I will add a provides entry to n007 for 'x' with the seed's prose.",
    "I'll add a provides entry here.",
    "We have added the provides entry to the node.",
    "I am adding a provides entry for it.",
    "A provides entry will be added to n007.",
    "The provides entry has been included.",
    "I include a provides entry for this concept.",
])
def test_delivery_narration_is_detected(text):
    assert PR.asserts_delivery(text, "x"), text


@pytest.mark.parametrize("text", [
    "the span does not establish this; I will not add a provides entry",
    "I cannot provide this entry: the establishment is in the appendix",
    "I decline to add a provides entry -- L712 is a bullet item",
    "I will explain the omission in judgment_calls",   # not about the entry
    "the provides entry would duplicate the heading-metadata role",
    "",
])
def test_a_genuine_decline_is_not_delivery_narration(text):
    assert not PR.asserts_delivery(text, "x"), text


def test_narration_mismatch_is_booked_as_a_failed_repair(tmp_path):
    """RED (repaired_verification.md §1e, `support_mental_health`): the
    reason argues both sides and ENDS BY ANNOUNCING COMPLIANCE, then
    emits nothing. ds7 booked it as one of "3 honestly undeliverable"."""
    run = _run(tmp_path)
    reply = _reply(1, 12, jcs=[
        f"{NAME}: the section heading establishes the existence of the "
        f"policy section. I will add a provides entry to n001 for "
        f"'{NAME}' with the seed's prose to satisfy the promise repair."])
    rep = PR.run_repair(run, _cfg(), SeatClient([reply]),
                        list(ESTABLISHING))
    assert rep["declined_honestly"] == 0, \
        "a reply that announced delivery is not an honest decline"
    assert rep["narration_mismatch"] == 1
    assert rep["failed"] == 1, "a non-delivery is a failed repair"
    assert rep["by_class"]["promise"]["narration_mismatch"] == 1
    row = _row(rep)
    assert row["status"] == "narration_mismatch"
    assert "asserts it delivers" in row["why"] and "NOT an honest" in row["why"]
    fixed = json.load(open(os.path.join(run, "root_graph.repaired.json")))
    assert fixed["nodes"][0]["provides"] == [], "nothing may be spliced"


def test_an_honest_decline_is_still_an_honest_decline(tmp_path):
    """The exemplary ds7 decline (`letter_and_spirit_principle`): names
    the seed, refuses, says why. It must NOT be reclassified."""
    run = _run(tmp_path)
    reply = _reply(1, 12, jcs=[
        f"{NAME}: L3 is a bullet item about a different duty, not a "
        f"statement of this principle; I will not add a provides entry."])
    rep = PR.run_repair(run, _cfg(), SeatClient([reply]),
                        list(ESTABLISHING))
    assert rep["declined_honestly"] == 1 and rep["narration_mismatch"] == 0
    assert rep["failed"] == 0
    assert _row(rep)["status"] == "declined"


# ==========================================================================
#  FIX 3 -- self-loops
# ==========================================================================

def test_the_receiving_nodes_self_need_is_dropped(tmp_path):
    """RED (ds7 made 3 of these): the node the concept is spliced onto
    was ITSELF one of the danglers, so after the splice it needs a name
    it provides. A node cannot depend on itself, and counting that as a
    resolved needer is a degenerate 'resolution'."""
    run = _run(tmp_path, target_needs=[{"name": NAME,
                                        "prose": "cites the duty"},
                                       {"name": "other", "prose": "keep"}])
    rep = PR.run_repair(run, _cfg(), SeatClient([_delivering_reply()]),
                        list(ESTABLISHING))
    assert rep["repaired"] == 1
    fixed = json.load(open(os.path.join(run, "root_graph.repaired.json")))
    tgt = fixed["nodes"][0]
    assert any(R.nm(p) == NAME for p in tgt["provides"])
    assert [R.nm(d) for d in tgt["needs"]] == ["other"], \
        "the self-need must be dropped, the unrelated need kept"
    assert rep["self_needs_dropped"] == 1
    assert rep["self_loops_after"] == 0
    assert fixed["promise_repairs"][0]["dropped_self_needs"] == [NAME]
    assert any("dropped the node's self-need" in a
               for a in fixed["driver_autofixes"])


def test_a_new_need_naming_the_spliced_concept_is_not_spliced(tmp_path):
    """The other direction: the redraw's own needs are merged onto the
    target, so a redraw need naming the concept would CREATE the loop."""
    run = _run(tmp_path)
    rep = PR.run_repair(
        run, _cfg(),
        SeatClient([_delivering_reply(
            needs=[{"name": NAME, "prose": "self"},
                   {"name": "real_dep", "prose": "a real dependency"}])]),
        list(ESTABLISHING))
    assert rep["repaired"] == 1 and rep["self_loops_after"] == 0
    fixed = json.load(open(os.path.join(run, "root_graph.repaired.json")))
    assert [R.nm(d) for d in fixed["nodes"][0]["needs"]] == ["real_dep"]
    assert fixed["promise_repairs"][0]["spliced_needs"] == ["real_dep"]


def test_the_report_carries_a_graph_level_self_loop_census(tmp_path):
    """Pre-existing self-loops are NOT the repair's to fix (ds7 had 16
    before it ran); the stage reports the count on both sides so a
    repair-created loop is visible against the baseline."""
    pre = [{"id": "L21-30_n001", "establishes": "pre-existing loop",
            "needs": [{"name": "loopy", "prose": "self"}],
            "provides": [{"name": "loopy", "prose": "self"}],
            "spans": [{"lines": [21, 22]}]}]
    run = _run(tmp_path, extra_nodes=pre)
    rep = PR.run_repair(run, _cfg(), SeatClient([_delivering_reply()]),
                        list(ESTABLISHING))
    assert rep["self_loops_before"] == 1 and rep["self_loops_after"] == 1
    assert PR.self_loops(json.load(open(os.path.join(
        run, "root_graph.repaired.json")))) == {("L21-30_n001", "loopy")}
