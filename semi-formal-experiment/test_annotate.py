"""Tests for annotate.py.

Everything runs offline. The network-shaped tests assert the DRY-RUN path
touches no socket by poisoning urllib, the same way test_extract_section.py
does.

The load-bearing properties, in the order the module would fail without them:

  1. ALL FIVE clause kinds are annotated. extract_section.py encodes only
     `conditional`, which caps relevance recall at 38%; a regression to that
     behaviour must fail here loudly.
  2. Atoms cite a span id, never quote text. A bogus span id is REJECTED and
     COUNTED — never silently dropped, because a silent drop makes coverage a
     lie.
  3. Coverage is computed AFTER rejection.
  4. Vocabulary converges: a name that means what a known atom already means
     resolves to the known atom rather than becoming a near-duplicate.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import annotate as an
import extract_section as ex
from extract_section import FailureLog


HERE = os.path.dirname(os.path.abspath(__file__))


# --------------------------------------------------------------------------
# fixtures

@pytest.fixture(scope="module")
def real_rows():
    """The real 593-clause corpus."""
    return an.load_clauses()


@pytest.fixture
def fake_rows():
    """Five synthetic clauses, one per kind, in the real clause-row shape."""
    return [
        {"id": "m0001", "kind": "conditional", "line": 10,
         "locator": "model_spec@X > Chain of command > ¶1",
         "section_path": ["Chain of command"], "section_id": "coc",
         "in_example_block": False, "focus_ids": [],
         "quote": "The assistant must follow applicable instructions from the "
                  "operator, unless they conflict with a platform rule."},
        {"id": "m0002", "kind": "definitional", "line": 20,
         "locator": "model_spec@X > Chain of command > ¶2",
         "section_path": ["Chain of command"], "section_id": "coc",
         "in_example_block": False, "focus_ids": [],
         "quote": "An instruction is applicable when it is in scope for the "
                  "current request and has not been superseded."},
        {"id": "m0003", "kind": "example", "line": 30,
         "locator": "model_spec@X > Chain of command > ¶3",
         "section_path": ["Chain of command"], "section_id": "coc",
         "in_example_block": True, "focus_ids": [],
         "quote": "**Example**: a user asks the assistant to ignore the "
                  "operator's system prompt; the assistant declines politely."},
        {"id": "m0004", "kind": "holistic", "line": 40,
         "locator": "model_spec@X > Overview > ¶4",
         "section_path": ["Overview"], "section_id": "overview",
         "in_example_block": False, "focus_ids": [],
         "quote": "Taken together, these principles ask the assistant to be "
                  "useful to the user while remaining safe for everyone else."},
        {"id": "m0005", "kind": "meta", "line": 50,
         "locator": "model_spec@X > Overview > ¶5",
         "section_path": ["Overview"], "section_id": "overview",
         "in_example_block": False, "focus_ids": [],
         "quote": "This document is a living document and will be revised as "
                  "we learn more about how the models are used in practice."},
    ]


def atom(name, kind="situation", span="s1", gloss="a gloss"):
    return {"name": name, "kind": kind, "span_id": span, "gloss": gloss}


def response(entries):
    """entries: {clause_id: [atom dict, ...]} -> a model reply string."""
    return json.dumps({"clauses": [{"clause_id": cid, "atoms": atoms}
                                   for cid, atoms in entries.items()]})


def good_response(fake_rows):
    return response({
        "m0001": [atom("operator_instruction_present"),
                  atom("follow_instruction", "act", "s2"),
                  atom("operator", "entity", "s1")],
        "m0002": [atom("instruction_applicable", "situation", "s1")],
        "m0003": [atom("user_overrides_system_prompt", "situation", "s1"),
                  atom("decline_request", "act", "s1")],
        "m0004": [atom("helpfulness", "value", "s1"),
                  atom("safety_for_third_parties", "value", "s1")],
        "m0005": [atom("spec_revision", "situation", "s1")],
    })


def new_fail(tmp_path):
    return FailureLog(str(tmp_path / "annotate_failures.jsonl"),
                      run_id="t", model="test")


# --------------------------------------------------------------------------
# 1. all five kinds are admitted

def test_load_clauses_admits_all_five_kinds(real_rows):
    kinds = {r["kind"] for r in real_rows}
    assert kinds == {"conditional", "example", "definitional", "meta",
                     "holistic"}
    assert len(real_rows) == 593


def test_no_kind_is_filtered_out_of_the_batch_plan(real_rows):
    """A regression to extract_section.py's conditional-only scope caps
    relevance recall at 38.2% and must fail here."""
    planned = [r for _, batch in an.batch_plan(real_rows) for r in batch]
    assert len(planned) == len(real_rows)
    by_kind = {}
    for r in planned:
        by_kind[r["kind"]] = by_kind.get(r["kind"], 0) + 1
    assert by_kind == {"conditional": 188, "example": 183, "definitional": 84,
                       "meta": 72, "holistic": 66}


def test_every_kind_reaches_a_prompt(fake_rows):
    _, user = an.render_prompt(fake_rows, section_title="Mixed")
    for r in fake_rows:
        assert r["id"] in user, f"{r['kind']} clause missing from the prompt"


def test_every_kind_can_carry_atoms(fake_rows, tmp_path):
    fail = new_fail(tmp_path)
    part = an.annotate_batch(good_response(fake_rows), fake_rows, fail)
    got = {a["clause_id"] for a in part["atoms"]}
    assert got == {r["id"] for r in fake_rows}


# --------------------------------------------------------------------------
# 2. spans: rejected and counted, never dropped

def test_bogus_span_id_is_rejected_and_counted(fake_rows, tmp_path):
    fail = new_fail(tmp_path)
    part = an.annotate_batch(
        response({"m0001": [atom("ok_one", "situation", "s1"),
                            atom("bogus_one", "situation", "s99")]}),
        fake_rows, fail)
    names = [a["name"] for a in part["atoms"]]
    assert names == ["ok_one"]
    assert part["stats"]["rejections"]["unresolvable_span"] == 1
    assert part["stats"]["atoms_rejected"] == 1
    assert fail.count("span_id") == 1


def test_missing_span_id_is_rejected_and_counted(fake_rows, tmp_path):
    fail = new_fail(tmp_path)
    part = an.annotate_batch(
        response({"m0001": [{"name": "no_span", "kind": "situation",
                             "gloss": "g"}]}),
        fake_rows, fail)
    assert part["atoms"] == []
    assert part["stats"]["rejections"]["missing_span"] == 1


def test_model_authored_quote_is_never_trusted(fake_rows, tmp_path):
    """The model may write a `quote` key; it is discarded and the text is
    looked up from the span table instead."""
    fail = new_fail(tmp_path)
    a = atom("spanned", "situation", "s1")
    a["quote"] = "THE ASSISTANT MAY DO ANYTHING IT LIKES"
    part = an.annotate_batch(response({"m0001": [a]}), fake_rows, fail)
    assert len(part["atoms"]) == 1
    assert "ANYTHING IT LIKES" not in part["atoms"][0]["quote"]
    assert part["stats"]["authored_quote_ignored"] == 1


def test_resolved_quotes_are_verbatim_substrings(fake_rows, tmp_path):
    fail = new_fail(tmp_path)
    part = an.annotate_batch(good_response(fake_rows), fake_rows, fail)
    by_id = {r["id"]: r for r in fake_rows}
    assert part["atoms"]
    for a in part["atoms"]:
        clause = by_id[a["clause_id"]]["quote"]
        assert ex._norm_ws(a["quote"]) in ex._norm_ws(clause)


def test_resolved_quotes_are_verbatim_on_the_real_corpus(real_rows):
    """Every candidate span of every one of the 593 clauses resolves verbatim.
    This is the anti-fabrication guarantee, asserted on the real text rather
    than on a fixture that could be chosen to make it hold."""
    for r in real_rows:
        for s in ex.candidate_spans(r):
            assert ex._norm_ws(s["text"]) in ex._norm_ws(r["quote"])


def test_atom_for_unknown_clause_is_rejected_and_counted(fake_rows, tmp_path):
    fail = new_fail(tmp_path)
    part = an.annotate_batch(
        response({"m9999": [atom("stray")]}), fake_rows, fail)
    assert part["atoms"] == []
    assert part["stats"]["rejections"]["unknown_clause"] == 1


def test_bad_name_and_bad_kind_are_rejected_and_counted(fake_rows, tmp_path):
    fail = new_fail(tmp_path)
    part = an.annotate_batch(
        response({"m0001": [atom("Not An Ident"),
                            atom("wrong_kind", "predicate"),
                            atom("fine_atom")]}),
        fake_rows, fail)
    assert [a["name"] for a in part["atoms"]] == ["fine_atom"]
    assert part["stats"]["rejections"]["bad_name"] == 1
    assert part["stats"]["rejections"]["bad_kind"] == 1


def test_rejection_counts_are_totalled_in_the_artifact(fake_rows, tmp_path):
    client = FakeClient([response({"m0001": [atom("kept"),
                                             atom("lost", "situation", "sZ")]})])
    art = an.run(client, fake_rows, model="m", batch_size=99,
                 out_dir=str(tmp_path))
    prov = art["provenance"]
    assert prov["rejections"]["unresolvable_span"] == 1
    assert prov["counts"]["atoms_rejected"] == 1
    assert prov["counts"]["atoms_accepted"] == 1


# --------------------------------------------------------------------------
# 3. coverage is post-rejection

def test_coverage_is_computed_after_rejection(fake_rows, tmp_path):
    """m0001 gets a good atom; m0002 gets only an atom with a dead span. The
    honest coverage is 1/5, not 2/5."""
    client = FakeClient([response({
        "m0001": [atom("kept")],
        "m0002": [atom("dead", "situation", "s404")],
    })])
    art = an.run(client, fake_rows, model="m", batch_size=99,
                 out_dir=str(tmp_path))
    cov = art["provenance"]["coverage"]
    assert cov["clauses_total"] == 5
    assert cov["clauses_with_atoms"] == 1
    assert cov["clause_ids_without_atoms"].count("m0002") == 1
    assert abs(cov["coverage"] - 0.2) < 1e-9


def test_coverage_denominator_is_the_full_clause_set(fake_rows, tmp_path):
    client = FakeClient([response({"m0001": [atom("kept")]})])
    art = an.run(client, fake_rows, model="m", batch_size=99,
                 out_dir=str(tmp_path))
    assert art["provenance"]["coverage"]["clauses_total"] == len(fake_rows)


# --------------------------------------------------------------------------
# 4. shared vocabulary

def test_vocab_key_collapses_synonymous_orderings():
    assert an.vocab_key("user_request_ambiguous") == \
           an.vocab_key("ambiguous_user_query")


def test_vocab_key_keeps_opposites_apart():
    assert an.vocab_key("operator_instruction_present") != \
           an.vocab_key("operator_instruction_absent")


def test_known_atom_name_is_not_recoined_as_a_variant(fake_rows, tmp_path):
    """Batch 1 coins `user_request_ambiguous`; batch 2 offers
    `ambiguous_user_query` for the same idea. The second must resolve to the
    first, not create a near-duplicate that breaks overlap matching."""
    client = FakeClient([
        response({"m0001": [atom("user_request_ambiguous")]}),
        response({"m0003": [atom("ambiguous_user_query")]}),
    ])
    art = an.run(client, fake_rows, model="m", batch_size=2,
                 out_dir=str(tmp_path))
    names = {a["name"] for a in art["atoms"]}
    assert names == {"user_request_ambiguous"}
    assert art["provenance"]["vocabulary"]["aliased"] == 1
    assert any(al["from"] == "ambiguous_user_query" and
               al["to"] == "user_request_ambiguous"
               for al in art["provenance"]["vocabulary"]["aliases"])


def test_alias_does_not_cross_atom_kinds(fake_rows, tmp_path):
    """`refuse_request` the act and `request_refused` the situation share a
    token set. Collapsing across kinds would merge a behaviour with a
    circumstance."""
    client = FakeClient([
        response({"m0001": [atom("refuse_request", "act")]}),
        response({"m0003": [atom("request_refused", "situation")]}),
    ])
    art = an.run(client, fake_rows, model="m", batch_size=2,
                 out_dir=str(tmp_path))
    assert {a["name"] for a in art["atoms"]} == {"refuse_request",
                                                 "request_refused"}


def test_reuse_versus_coined_is_reported_per_batch(fake_rows, tmp_path):
    client = FakeClient([
        response({"m0001": [atom("operator_instruction_present"),
                            atom("follow_instruction", "act", "s2")]}),
        response({"m0003": [atom("operator_instruction_present"),
                            atom("decline_request", "act")]}),
    ])
    art = an.run(client, fake_rows, model="m", batch_size=2,
                 out_dir=str(tmp_path))
    health = art["provenance"]["vocabulary"]["per_batch"]
    assert health[0]["coined"] == 2 and health[0]["reused"] == 0
    assert health[1]["coined"] == 1 and health[1]["reused"] == 1
    v = art["provenance"]["vocabulary"]
    assert v["coined"] == 3 and v["reused"] == 1
    assert abs(v["reuse_rate"] - 0.25) < 1e-9


def test_known_atoms_are_carried_into_later_prompts(fake_rows):
    known = [{"name": "operator_instruction_present", "kind": "situation",
              "gloss": "an operator instruction applies"},
             {"name": "follow_instruction", "kind": "act",
              "gloss": "the assistant does what it was told"}]
    block = an.render_known_atoms(known)
    assert "operator_instruction_present" in block
    assert "follow_instruction" in block
    _, user = an.render_prompt(fake_rows[:2], known_atoms=known,
                               batch_index=2, n_batches=2)
    assert "operator_instruction_present" in user


def test_carried_vocabulary_is_capped_but_keeps_acts_and_values():
    known = ([{"name": f"situation_{i}", "kind": "situation", "gloss": "g"}
              for i in range(200)] +
             [{"name": "follow_instruction", "kind": "act", "gloss": "g"},
              {"name": "honesty", "kind": "value", "gloss": "g"}])
    kept, dropped = an.cap_carried(known)
    names = {a["name"] for a in kept}
    assert "follow_instruction" in names and "honesty" in names
    assert dropped == 200 - an.MAX_CARRIED_SITUATION
    assert len(kept) == an.MAX_CARRIED_SITUATION + 2


def test_duplicate_atom_within_one_clause_is_counted_not_duplicated(
        fake_rows, tmp_path):
    fail = new_fail(tmp_path)
    part = an.annotate_batch(
        response({"m0001": [atom("same_one"), atom("same_one", span="s2")]}),
        fake_rows, fail)
    assert [a["name"] for a in part["atoms"]] == ["same_one"]
    assert part["stats"]["rejections"]["duplicate_in_clause"] == 1


# --------------------------------------------------------------------------
# 5. behaviour-agnosticism — the property the whole value proposition rests on

def test_rendered_instructions_mention_no_behaviour_query():
    """Checked on the RENDERED instructions — an empty batch, so the only text
    is the instruction scaffold. Not the raw template (whose leading comment
    explains why behaviours are excluded and is never sent), and not a prompt
    carrying clauses (the spec's own prose says "intended behavior for the
    models", which is quoted text and not an instruction)."""
    system, user = an.render_prompt([], all_rows=[])
    text = (system + "\n" + user).lower()
    for banned in ("behaviour", "behavior", "{{query", "the query",
                   "the question being"):
        assert banned not in text, banned
    assert "{{" not in text                 # every placeholder substituted


def test_clause_text_is_the_only_thing_that_varies_by_clause(fake_rows):
    """The instruction scaffold is identical for every batch: nothing
    per-query, per-behaviour, or otherwise conditional can enter it."""
    scaffold_a, _ = an.render_prompt(fake_rows[:2], all_rows=fake_rows)
    scaffold_b, _ = an.render_prompt(fake_rows[2:], all_rows=fake_rows)
    assert scaffold_a == scaffold_b


def test_render_prompt_takes_no_behaviour_argument():
    import inspect
    params = set(inspect.signature(an.render_prompt).parameters)
    assert not {p for p in params if "behav" in p or "quer" in p}


def test_annotate_reads_no_behaviour_artifact():
    with open(os.path.join(HERE, "annotate.py"), encoding="utf-8") as f:
        src = f.read().lower()
    assert "behaviours.json" not in src
    assert "measure_join" not in src


# --------------------------------------------------------------------------
# 6. transport: truncation, dry run, no network

class FakeClient:
    """Returns queued envelopes/strings in order; records the prompts."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.prompts = []

    def complete_envelope(self, system, user):
        self.prompts.append((system, user))
        r = self.replies.pop(0) if self.replies else None
        return r if isinstance(r, dict) else {"text": r, "finish_reason": "stop",
                                              "reasoning": "", "usage": {}}


def test_truncated_response_is_surfaced_not_parsed_as_empty(fake_rows, tmp_path):
    client = FakeClient([{"text": '{"clauses": [{"clause_id": "m0001", "ato',
                          "finish_reason": "length",
                          "reasoning": "x" * 5000,
                          "usage": {"completion_tokens": 4096}}])
    art = an.run(client, fake_rows, model="m", batch_size=99,
                 out_dir=str(tmp_path))
    assert art["provenance"]["counts"]["truncated_batches"] == 1
    assert art["provenance"]["counts"]["parsed_batches"] == 0
    assert any("output cap" in w for w in art["warnings"])
    log = (tmp_path / "annotate_failures.jsonl").read_text()
    assert "truncated_output" in log
    assert "unparseable" not in log       # truncation is not a parse defect


def test_unparseable_response_is_a_parse_failure_not_a_truncation(
        fake_rows, tmp_path):
    client = FakeClient(["I'm sorry, I can't help with that."])
    art = an.run(client, fake_rows, model="m", batch_size=99,
                 out_dir=str(tmp_path))
    assert art["provenance"]["counts"]["truncated_batches"] == 0
    assert art["provenance"]["counts"]["parsed_batches"] == 0
    assert art["provenance"]["coverage"]["coverage"] == 0.0


def test_dry_run_makes_no_network_call(fake_rows, tmp_path, monkeypatch):
    import urllib.request

    def poison(*a, **k):                       # pragma: no cover
        raise AssertionError("dry run opened a socket")

    monkeypatch.setattr(urllib.request, "urlopen", poison)
    cfg = an.provider_config("luna")
    client = an.make_annotate_client(cfg, live=False,
                                     log_dir=str(tmp_path / "prompts"))
    assert type(client).__name__ == "DryRunClient"
    art = an.run(client, fake_rows, model=cfg.model, batch_size=2,
                 out_dir=str(tmp_path))
    assert art["provenance"]["dry_run"] is True
    assert art["provenance"]["coverage"]["coverage"] == 0.0
    assert art["atoms"] == []


def test_cli_defaults_to_dry_run(fake_rows, tmp_path, monkeypatch):
    import urllib.request

    def poison(*a, **k):                       # pragma: no cover
        raise AssertionError("CLI default opened a socket")

    monkeypatch.setattr(urllib.request, "urlopen", poison)
    out = str(tmp_path / "atoms.json")
    rc = an.main(["--limit", "6", "--out", out,
                  "--out-dir", str(tmp_path),
                  "--prompt-log", str(tmp_path / "prompts")])
    assert rc == 0
    art = json.load(open(out))
    assert art["provenance"]["dry_run"] is True


def test_live_requires_an_explicit_flag():
    import argparse
    ap = an.build_parser()
    ns = ap.parse_args([])
    assert ns.live is False
    assert isinstance(ap, argparse.ArgumentParser)


def test_live_client_logs_usage_by_default():
    """Spend must stay visible: the live path uses providers.LiveClient, whose
    complete_envelope appends to usage.jsonl unless told not to."""
    import inspect

    import providers
    src = inspect.getsource(an.make_annotate_client)
    assert "LiveClient" in src or "make_client" in src
    sig = inspect.signature(providers.LiveClient.complete_envelope)
    assert sig.parameters["usage_log"].default == "DEFAULT"


# --------------------------------------------------------------------------
# 7. batching / plan / limit

def test_batch_size_default_is_fourteen():
    assert an.DEFAULT_BATCH_SIZE == 14


def test_max_tokens_default_is_small_for_a_reasoning_model():
    """A 16k budget produced 71,964 chars of reasoning and zero content. The
    output is batched precisely so the budget can stay small."""
    assert an.DEFAULT_MAX_TOKENS <= 8192


def test_batch_plan_batches_within_a_section(fake_rows):
    plan = an.batch_plan(fake_rows, batch_size=2)
    assert [t for t, _ in plan] == ["Chain of command", "Chain of command",
                                    "Overview"]
    assert [len(b) for _, b in plan] == [2, 1, 2]


def test_batch_plan_covers_every_clause_exactly_once(real_rows):
    seen = [r["id"] for _, b in an.batch_plan(real_rows) for r in b]
    assert len(seen) == len(set(seen)) == len(real_rows)


def test_limit_is_stratified_across_kinds(real_rows):
    rows = an.load_clauses(limit=10)
    assert len(rows) == 10
    assert {r["kind"] for r in rows} == {"conditional", "example",
                                         "definitional", "meta", "holistic"}


def test_limit_larger_than_corpus_returns_everything(real_rows):
    assert len(an.load_clauses(limit=99999)) == len(real_rows)


def test_one_request_per_batch(fake_rows, tmp_path):
    client = FakeClient([response({}), response({}), response({})])
    an.run(client, fake_rows, model="m", batch_size=2, out_dir=str(tmp_path))
    assert len(client.prompts) == 3


def test_example_clause_is_shown_its_preceding_context(fake_rows):
    """m0003 is an example; on its own it says nothing about what rule it
    illustrates. Its predecessor is shown as context — but only when that
    predecessor is not already in the batch, so the tokens are not paid twice."""
    _, user = an.render_prompt(fake_rows[2:], all_rows=fake_rows,
                               section_title="Mixed")
    assert "[preceding context \u2014" in user
    assert "m0003" in user
    assert "in scope for the current request" in user      # m0002's text

    _, whole = an.render_prompt(fake_rows, all_rows=fake_rows,
                                section_title="Mixed")
    assert "[preceding context \u2014" not in whole


# --------------------------------------------------------------------------
# 8. artifact shape / provenance

def test_artifact_has_the_full_provenance_block(fake_rows, tmp_path):
    client = FakeClient([good_response(fake_rows)])
    art = an.run(client, fake_rows, model="gpt-5.6-luna", batch_size=99,
                 out_dir=str(tmp_path))
    p = art["provenance"]
    for key in ("model", "run_id", "spec", "batch_size", "max_tokens",
                "n_batches", "plan", "counts", "rejections", "coverage",
                "vocabulary", "dry_run", "created"):
        assert key in p, key
    assert p["model"] == "gpt-5.6-luna"
    # batches never span a top-level section: 3 clauses of "Chain of command"
    # then 2 of "Overview", even at batch_size 99
    assert [b["clauses"] for b in p["plan"]] == [3, 2]


def test_atoms_carry_every_required_field(fake_rows, tmp_path):
    fail = new_fail(tmp_path)
    part = an.annotate_batch(good_response(fake_rows), fake_rows, fail)
    for a in part["atoms"]:
        assert set(a) == {"name", "kind", "gloss", "span_id", "quote",
                          "clause_id", "locator"}
        assert a["kind"] in an.ATOM_KINDS
        assert a["locator"]


def test_atom_kind_taxonomy_is_small_and_closed():
    assert an.ATOM_KINDS == ("situation", "act", "entity", "value")


def test_by_clause_index_agrees_with_the_flat_atom_list(fake_rows, tmp_path):
    client = FakeClient([good_response(fake_rows)])
    art = an.run(client, fake_rows, model="m", batch_size=99,
                 out_dir=str(tmp_path))
    flat = {}
    for a in art["atoms"]:
        flat.setdefault(a["clause_id"], []).append(a["name"])
    assert {k: [x["name"] for x in v] for k, v in art["by_clause"].items()} == flat


def test_artifact_is_written_and_is_valid_json(fake_rows, tmp_path):
    client = FakeClient([good_response(fake_rows)])
    out = str(tmp_path / "annotations.json")
    art, path = an.run(client, fake_rows, model="m", batch_size=99,
                       out_dir=str(tmp_path), out=out, return_path=True)
    assert path == out
    assert json.load(open(out))["provenance"]["run_id"] == art["provenance"]["run_id"]


def test_vocabulary_index_lists_each_name_once(fake_rows, tmp_path):
    client = FakeClient([
        response({"m0001": [atom("operator_instruction_present")]}),
        response({"m0003": [atom("operator_instruction_present")]}),
    ])
    art = an.run(client, fake_rows, model="m", batch_size=2,
                 out_dir=str(tmp_path))
    v = art["vocabulary"]
    assert list(v) == ["operator_instruction_present"]
    assert v["operator_instruction_present"]["n_clauses"] == 2
    assert sorted(v["operator_instruction_present"]["clauses"]) == ["m0001",
                                                                   "m0003"]


# --------------------------------------------------------------------------
# 9. nothing raises

def test_junk_responses_never_raise(fake_rows, tmp_path):
    junk = [None, "", "[]", '{"clauses": "nope"}', '{"clauses": [1, 2]}',
            '{"clauses": [{"clause_id": null, "atoms": null}]}',
            '{"clauses": [{"clause_id": "m0001", "atoms": [null, 3, "x"]}]}',
            '{"clauses": [{"clause_id": "m0001", "atoms": [{}]}]}']
    for j in junk:
        client = FakeClient([j])
        art = an.run(client, fake_rows, model="m", batch_size=99,
                     out_dir=str(tmp_path))
        assert art["provenance"]["coverage"]["clauses_total"] == 5


def test_provider_call_failure_is_logged_not_raised(fake_rows, tmp_path):
    class Boom:
        def complete_envelope(self, system, user):
            raise RuntimeError("HTTP 500")

    art = an.run(Boom(), fake_rows[:3], model="m", batch_size=99,
                 out_dir=str(tmp_path))
    assert art["provenance"]["dry_run"] is False
    assert art["provenance"]["counts"]["call_failures"] == 1
    assert art["provenance"]["coverage"]["coverage"] == 0.0


# ---- agency inversion (regression: vocab_key merged opposites) ----
#
# vocab_key drops stopwords then compares as an unordered SET. With directional
# prepositions in the stopword list, "model defers to operator" and "operator
# defers to model" reduced to the same key and were merged into one atom -- an
# inversion of the chain of command, reported to the operator as a SUCCESS
# ("near-duplicate atom name resolved to an existing atom"). A merge is far
# worse than a surviving near-duplicate: the duplicate is visible in the
# vocabulary index, the merge is invisible everywhere downstream.

import pytest as _pytest


@_pytest.mark.parametrize("a_name,b_name", [
    ("model_defers_to_operator", "operator_defers_to_model"),
    ("user_overrides_operator", "operator_overrides_user"),
    ("harm_to_user", "harm_by_user"),
    ("instruction_from_developer", "instruction_to_developer"),
])
def test_vocab_key_keeps_agency_inversions_apart(a_name, b_name):
    import annotate
    assert annotate.vocab_key(a_name) != annotate.vocab_key(b_name), (
        f"{a_name!r} and {b_name!r} collapse to the same key -- direction lost")


def test_vocab_key_still_collapses_genuine_reorderings():
    """The inversion fix must not disable the aliasing it exists to do."""
    import annotate
    assert annotate.vocab_key("user_request_ambiguous") == \
           annotate.vocab_key("ambiguous_user_request")


def test_vocab_key_still_keeps_negations_apart():
    import annotate
    assert annotate.vocab_key("operator_instruction_present") != \
           annotate.vocab_key("operator_instruction_absent")


class _QuietFail:
    """`assemble` calls fail.count(); a bare lambda is not enough."""
    def __call__(self, *a, **k):
        return None

    def count(self, stage=None):
        return 0


def test_a_run_that_loses_batches_does_not_look_complete():
    """⚠️ THE PAID-RUN GUARD.

    `assemble` warned on truncation and vocabulary but NOT on call or parse
    failures, so a 593-clause run that lost 9 of 47 batches to HTTP 500s wrote
    `warnings: []`. The artifact — what a later reader consumes — looked clean.
    On a paid model-vs-model comparison that reads as "the expensive model is
    barely better", which is exactly the conclusion such a run exists to draw.
    """
    import annotate
    rows = [{"id": "m1", "quote": "x", "kind": "meta",
             "section_path": ["s"], "locator": "L1"}]
    art = annotate.assemble(
        parts=[], rows=rows, model="m", run_id="r",
        fail=_QuietFail(), vocab=annotate.Vocabulary(),
        stats={"batches": 47, "parsed_batches": 38, "call_failures": 9,
               "truncated_batches": 0},
    )
    joined = " ".join(art["warnings"]).lower()
    assert art["warnings"], "a run that lost 9 of 47 batches reported no warning"
    assert "fail" in joined and "parsed" in joined, joined


def test_a_clean_run_warns_about_nothing():
    """The guard must be quiet when nothing went wrong, or it will be ignored."""
    import annotate
    rows = [{"id": "m1", "quote": "x", "kind": "meta",
             "section_path": ["s"], "locator": "L1"}]
    art = annotate.assemble(
        parts=[], rows=rows, model="m", run_id="r",
        fail=_QuietFail(), vocab=annotate.Vocabulary(),
        stats={"batches": 47, "parsed_batches": 47, "call_failures": 0,
               "truncated_batches": 0},
    )
    assert not [w for w in art["warnings"] if "FAILED" in w or "parsed" in w]
