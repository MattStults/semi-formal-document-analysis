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
    # TOOLING item 4: the dry-run default writes to <name>.dryrun.json
    art = json.load(open(str(tmp_path / "atoms.dryrun.json")))
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
    for i, j in enumerate(junk):
        client = FakeClient([j])
        # one out path per run: the non-stub overwrite guard (TOOLING item
        # 4) correctly refuses a live rerun onto an existing artifact
        art = an.run(client, fake_rows, model="m", batch_size=99,
                     out=str(tmp_path / f"junk{i}.json"),
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


# ==========================================================================
# THE GRAMMAR EXTENSION — polarity, ordered principals, condition/consequent
#
# WHY. The read-back (n=125, pre-registered) measured `sufficient` = 0.16: 91
# of 125 clauses are identifiable from their atoms while a reader of those
# atoms would not know what the clause requires. The missing content sits in
# the three things the grammar had no slot for — the obligated party (23% of
# missing phrases), the deontic force (15%) and the trigger (10%) — and
# conditionals are 1/25 sufficient because "if X then Y", "Y unless X" and
# "never Y" all rendered as the same unordered set {X, Y}.
#
# This is a VALIDITY fix. The capacity bound (+0.972 against a +0.555 bar) says
# representation was never the relevance ceiling, so no MCC movement is
# expected or claimed here.

import grammar as gr


def _atom(name="a", kind="act", gloss="g", span_id="s1", **extra):
    d = {"name": name, "kind": kind, "gloss": gloss, "span_id": span_id}
    d.update(extra)
    return d


# ---- the prompt SHOWS the features ---------------------------------------

def test_the_prompt_declares_every_reserved_polarity_prefix():
    system, _ = an.load_template()
    for p in gr.POLARITY_PREFIXES:
        assert p in system, f"the extractor is never shown {p!r}"


def test_the_prompt_declares_the_principal_separator_and_the_principals():
    system, _ = an.load_template()
    assert gr.PRINCIPAL_SEP in system
    for p in gr.PRINCIPALS:
        assert p in system, p


def _principal_vocabulary_lines(system):
    """Lines that ARE the closed vocabulary list, not lines that mention it.

    Every principal word also occurs in the prompt's ordinary prose ("the
    user", "a system message"), so a substring scan for each word passes even
    when the enumerated line has been deleted outright. The line is identified
    structurally instead: a whitespace-separated run of tokens that is exactly
    the principal set.
    """
    want = set(gr.PRINCIPALS)
    out = []
    for line in system.splitlines():
        toks = line.split()
        if toks and set(toks) == want:
            out.append(line)
    return out


def test_the_prompt_ENUMERATES_the_principals_on_a_closed_line():
    """⚠️ REGRESSION GUARD. `test_..._declares_...` above is a substring scan
    and does NOT bind: an adversarial review deleted the entire enumerated
    principal line from both prompt files and all 1701 tests stayed green.
    Annotation is paid and non-reproducible, so the extractor silently losing
    its closed vocabulary would be discovered only after spending."""
    system, _ = an.load_template()
    lines = _principal_vocabulary_lines(system)
    assert len(lines) == 1, (
        "expected exactly one line enumerating the principal vocabulary and "
        f"found {len(lines)}; the extractor is shown {sorted(gr.PRINCIPALS)}")


def test_no_prompt_teaches_a_retired_principal():
    """`platform` was RETIRED, not renamed away in one place. It may appear
    only where the prompt says it does not exist. A worked example using it
    teaches the extractor a level the current Model Spec does not have, and
    contradicts the vocabulary line in the same prompt.

    Since the document-facts split, the teaching about `platform` lives in
    the docfacts files, so the guard scans what each of them SENDS (their
    spliced blocks — the commentary outside the blocks may cite the word)
    as well as the two prompt files."""
    import pathlib
    here = pathlib.Path(__file__).parent
    sent = {fn: (here / fn).read_text()
            for fn in ("annotate_prompt.md", "ladder_prompt.md")}
    for fn in ("docfacts_model_spec.md", "docfacts_constitution.md"):
        sent[fn] = "\n".join(an.load_docfacts(fn).values())
    for fn, text in sent.items():
        for i, line in enumerate(text.splitlines(), start=1):
            if "platform" not in line:
                continue
            assert "no `platform`" in line or "There is no" in line, (
                f"{fn}:{i} uses the retired principal `platform` outside the "
                f"disclaimer: {line.strip()!r}")


def test_the_prompt_declares_the_closed_role_vocabulary():
    system, _ = an.load_template()
    for r in gr.ROLES:
        assert r in system, r
    assert gr.ROLE_FIELD in system


def test_the_prompt_still_names_no_behaviour_and_no_panel():
    """Invariant 8. The extension must not become a channel for one.

    ("query" and "helpfulness" are NOT checked: both already occur as ordinary
    vocabulary illustrations — `ambiguous_user_query` in the reuse paragraph,
    `helpfulness` as an example of a `value` atom — and neither names a
    behaviour being scored.)
    """
    system, user = an.load_template()
    blob = (system + user).lower()
    for word in ("behaviour", "behavior", "panel", "judge", "relevant to",
                 "harm-avoidance", "over-caution", "gold"):
        assert word not in blob, word


# ---- the demonstrations are SYNTHETIC and FROZEN --------------------------

def test_the_prompt_carries_a_demonstration_block():
    demo = an.demonstrations()
    assert demo.strip(), "the extractor is told about the features, not shown"


def test_the_demonstrations_exercise_all_three_features():
    demo = an.demonstrations()
    assert any(p in demo for p in gr.POLARITY_PREFIXES)
    assert gr.PRINCIPAL_SEP in demo
    for r in ("condition", "exception", "consequent"):
        assert f'"{r}"' in demo, r


def test_the_demonstrations_are_frozen_by_a_sha256_in_the_prompt_file():
    assert an.declared_demonstration_sha() == an.demonstration_sha()
    an.verify_demonstrations()          # must not raise


def test_editing_a_demonstration_without_updating_the_sha_is_refused(tmp_path):
    """A6: the leak channel is SELECTION — which features get demonstrated, on
    what content, by an author who has read panel-conditioned analysis. The
    mitigation is that the block is frozen before any panel-facing output
    exists, so an edit has to be a visible diff of BOTH the text and the hash."""
    src = open(an._p(an.PROMPT_TEMPLATE_PATH), encoding="utf-8").read()
    tampered = src.replace(an.DEMO_BEGIN,
                           an.DEMO_BEGIN + "\nsmuggled line\n", 1)
    p = tmp_path / "prompt.md"
    p.write_text(tampered, encoding="utf-8")
    with pytest.raises(an.DemonstrationLeak):
        an.verify_demonstrations(str(p))


def test_no_demonstration_line_is_a_passage_of_either_spec():
    """BLOCKING DEFECT if it fires. A spec-sourced demonstration hands the
    extractor hand-curated annotations of evaluation-set clauses, and the care
    taken in choosing them is a channel from someone who has seen the panel."""
    corpora = []
    for path in ("modelspec_clauses.json", "constitution_clauses.json"):
        full = an._p(path)
        if os.path.exists(full):
            with open(full, encoding="utf-8") as f:
                data = json.load(f)
            rows = data["clauses"] if isinstance(data, dict) else data
            corpora.append(" ".join(ex._norm_ws(r.get("quote") or "")
                                    for r in rows))
    assert corpora, "no spec on disk to check against"
    for line in an.demonstration_prose():
        for blob in corpora:
            assert line not in blob, (
                f"DEMONSTRATION SOURCED FROM A SPEC: {line!r}")


def test_the_demonstration_clauses_are_declared_and_non_trivially_long():
    """A substring test never fires on a one-word line, so the prose actually
    checked has to be sentences."""
    lines = an.demonstration_prose()
    assert len(lines) >= 3
    for line in lines:
        assert len(line) >= 40, line


# ---- verification accepts the notation, and REJECTS a malformed one -------

def test_a_polarity_prefixed_name_with_principals_is_accepted(fake_rows):
    fail = FailureLog(os.devnull)
    obj = {"clauses": [{"clause_id": "m0001", "atoms": [
        _atom("mustnot_disclose_reasoning__model_user")]}]}
    atoms, stats = an.verify_atoms(obj, fake_rows[:1], fail)
    assert stats["atoms_accepted"] == 1
    assert atoms[0]["name"] == "mustnot_disclose_reasoning__model_user"


def test_a_name_whose_notation_does_not_parse_is_rejected_and_counted(fake_rows):
    """`a__b__c` matches the identifier regex, so without this it would be
    accepted and then decode as an opaque string in every render."""
    fail = FailureLog(os.devnull)
    obj = {"clauses": [{"clause_id": "m0001", "atoms": [
        _atom("a__b__c"), _atom("must_"), _atom("x__nobody")]}]}
    atoms, stats = an.verify_atoms(obj, fake_rows[:1], fail)
    assert atoms == []
    assert stats["rejections"]["bad_notation"] == 3


def test_a_role_outside_the_closed_set_is_rejected_and_counted(fake_rows):
    fail = FailureLog(os.devnull)
    obj = {"clauses": [{"clause_id": "m0001",
                        "atoms": [_atom("x", role="trigger")]}]}
    atoms, stats = an.verify_atoms(obj, fake_rows[:1], fail)
    assert atoms == []
    assert stats["rejections"]["bad_role"] == 1


def test_a_declared_role_survives_into_the_atom(fake_rows):
    fail = FailureLog(os.devnull)
    obj = {"clauses": [{"clause_id": "m0001",
                        "atoms": [_atom("x", role="Condition")]}]}
    atoms, _ = an.verify_atoms(obj, fake_rows[:1], fail)
    assert atoms[0]["role"] == "condition"


def test_an_atom_with_no_role_gets_no_role_key(fake_rows):
    """BACKWARD COMPATIBILITY. A default would make every legacy atom assert a
    conditional structure nobody wrote."""
    fail = FailureLog(os.devnull)
    obj = {"clauses": [{"clause_id": "m0001", "atoms": [_atom("x")]}]}
    atoms, _ = an.verify_atoms(obj, fake_rows[:1], fail)
    assert "role" not in atoms[0]


def test_must_and_mustnot_are_not_merged_by_the_near_duplicate_resolver():
    """Collapsing opposites is far worse than leaving a duplicate: a duplicate
    is visible in the vocabulary index, a merge is invisible everywhere."""
    assert an.vocab_key("must_disclose") != an.vocab_key("mustnot_disclose")
    assert an.vocab_key("must_defer__model_operator") != \
        an.vocab_key("must_defer__operator_model")


def test_the_notation_is_the_identity_on_the_real_shipped_artifact():
    """Point 3 of the task, tested on the artifact rather than a fixture."""
    with open(an._p("annotations_b8.json"), encoding="utf-8") as f:
        data = json.load(f)
    names = set(data.get("vocabulary") or {})
    names |= {a["name"] for a in data.get("atoms", []) if a.get("name")}
    assert len(names) >= 361
    for n in names:
        assert gr.stem_of(n) == n, n
    for a in data.get("atoms", [])[:2000]:
        assert gr.role_of(a) is None


# ---- THE RATE CAP: richer names are not a licence to emit more ------------

def test_the_rate_cap_constants_are_the_shipped_budget_and_ladders():
    import ladder as L
    assert an.CAP_ATOMS_PER_CLAUSE == L.CAP_ATOMS_PER_CLAUSE == 2.78
    assert an.CAP_TEXT_CHARS_PER_CLAUSE == L.CAP_TEXT_CHARS_PER_CLAUSE == 211


def test_the_rate_cap_reuses_ladders_implementation_rather_than_a_copy():
    import inspect
    import ladder as L
    src = inspect.getsource(an.apply_rate_cap)
    assert "enforce_rate_cap" in src
    assert L.enforce_rate_cap is not None


def test_the_rate_cap_trims_an_over_budget_run_and_says_by_how_much(fake_rows):
    atoms = []
    for r in fake_rows:
        for i in range(6):
            atoms.append(dict(_atom(f"n{i}", gloss="x" * 300),
                              clause_id=r["id"], quote="Q", locator="L"))
    kept, stats = an.apply_rate_cap(atoms, fake_rows)
    assert stats["atoms_dropped"] > 0
    assert len(kept) / len(fake_rows) <= an.CAP_ATOMS_PER_CLAUSE
    assert (sum(len(a["gloss"]) for a in kept) / len(fake_rows)
            <= an.CAP_TEXT_CHARS_PER_CLAUSE)


def test_the_rate_cap_never_touches_the_looked_up_quote_or_the_role(fake_rows):
    """`quote` is verbatim provenance and `role` is a closed enum — clipping
    either would corrupt, not shorten. Only free text is the budget."""
    atoms = [dict(_atom(f"n{i}", gloss="x" * 400, role="condition"),
                  clause_id=fake_rows[0]["id"],
                  quote="A VERBATIM SPAN OF THE DOCUMENT, LONG ENOUGH TO CLIP",
                  locator="L") for i in range(9)]
    kept, _ = an.apply_rate_cap(atoms, fake_rows)
    assert kept, "the cap deleted everything"
    for a in kept:
        assert a["quote"] == ("A VERBATIM SPAN OF THE DOCUMENT, LONG ENOUGH "
                              "TO CLIP")
        assert a["role"] == "condition"


def test_the_rate_cap_is_a_no_op_on_an_annotation_inside_budget(fake_rows):
    atoms = [dict(_atom("n0", gloss="short"), clause_id=fake_rows[0]["id"],
                  quote="Q", locator="L")]
    kept, stats = an.apply_rate_cap(atoms, fake_rows)
    assert kept == atoms and stats["atoms_dropped"] == 0


def test_the_prompt_states_the_budget_so_the_model_is_not_asked_to_overspend():
    system, _ = an.load_template()
    assert "2.78" in system or "three" in system.lower()
    low = system.lower()
    assert "more atoms" in low or "not a licence" in low or "fewer" in low


# ---- --dry-run: MEASURED tokens and a price ------------------------------

def test_dry_run_cost_is_built_from_the_prompts_it_would_actually_send():
    est = an.estimate_cost(limit=28, provider="luna")
    assert est["calls"] >= 1
    assert est["prompt_chars"] > 0
    assert est["in_tokens"] > 0
    assert est["chars_per_token"] > 3.0


def test_dry_run_cost_prices_through_spend_cost_of():
    import inspect
    src = inspect.getsource(an.estimate_cost)
    assert "cost_of" in src, "the price must go through spend.py, not arithmetic"
    est = an.estimate_cost(limit=28, provider="luna")
    assert est["usd"] > 0 and est["usd_ceiling"] >= est["usd"]


def test_dry_run_cost_scales_with_the_number_of_clauses():
    small = an.estimate_cost(limit=28, provider="luna")
    big = an.estimate_cost(limit=112, provider="luna")
    assert big["usd"] > small["usd"]


def test_dry_run_makes_no_network_call(monkeypatch):
    import urllib.request

    def boom(*a, **k):
        raise AssertionError("the dry run opened a socket")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    an.estimate_cost(limit=28, provider="luna")
    assert an.main(["--limit", "28", "--dry-run", "--out",
                    os.devnull, "--log", os.devnull]) == 0


def test_run_ACTUALLY_APPLIES_the_rate_cap_end_to_end(fake_rows, tmp_path):
    """MUTATION-VERIFIED, and it caught a real hole: every other cap test
    calls `apply_rate_cap` directly, so turning the call OFF inside `run()`
    left the whole suite green. That is the `section_path` defect shape — a
    unit tested in isolation while the pipeline forgot to call it — and it is
    exactly the failure mode the rate cap exists to prevent, since a rung could
    then win by asserting more."""
    over = {r["id"]: [atom(f"n{i}", "situation", "s1", gloss="x" * 300)
                      for i in range(6)] for r in fake_rows}
    client = FakeClient([response(over)])
    art = an.run(client, fake_rows, model="m", batch_size=99,
                 out_dir=str(tmp_path))
    cap = art["provenance"]["rate_cap"]
    assert cap["applied"] is True and cap["atoms_dropped"] > 0
    n = len(fake_rows)
    assert len(art["atoms"]) / n <= an.CAP_ATOMS_PER_CLAUSE
    assert (sum(len(a["gloss"]) for a in art["atoms"]) / n
            <= an.CAP_TEXT_CHARS_PER_CLAUSE)
    assert art["provenance"]["vocabulary"]["atoms_per_clause"] <= \
        an.CAP_ATOMS_PER_CLAUSE


def test_an_uncapped_run_says_so_in_its_own_artifact(fake_rows, tmp_path):
    client = FakeClient([response({r["id"]: [atom(f"n{i}") for i in range(6)]
                                   for r in fake_rows})])
    art = an.run(client, fake_rows, model="m", batch_size=99,
                 out_dir=str(tmp_path), rate_cap=False)
    assert art["provenance"]["rate_cap"] == {"applied": False}
    assert len(art["atoms"]) / len(fake_rows) > an.CAP_ATOMS_PER_CLAUSE


# ------------------------------------------------------- the budget must BIND
# Found by the pre-spend review. `print_cost` ended in a bare
# `print("!! THE CEILING WOULD EXCEED THE BUDGET.")` with no return and no
# raise, and the next statements spent the money. On luna the $0.552 ceiling is
# arithmetically bounded so it could not bite — but the SAME command with
# `--provider sol` prices at $10.05 expected / $13.79 ceiling against an $8.50
# hard cap, and would have run anyway after printing a warning.
#
# A guard that reports and proceeds is not a guard. `ladder.main` raises
# SystemExit on the same condition; this is the divergence.

def test_a_ceiling_over_budget_RAISES_rather_than_printing_and_proceeding():
    """# MUTATION-VERIFIED"""
    est = {"clauses": 593, "calls": 78, "batch_size": 8, "provider": "sol",
           "model": "gpt-5.6-sol", "prompt_chars": 3858255, "in_tokens": 840839,
           "chars_per_token": 4.59, "chars_per_token_method": "measured",
           "out_tokens_low": 1e5, "out_tokens_high": 2e5,
           "out_tokens_ceiling": 3e5, "output_profile": "b8",
           "usd_low": 8.0, "usd": 10.05, "usd_ceiling": 13.79,
           "spent_so_far": 1.52, "budget": 8.50}
    with pytest.raises(SystemExit) as e:
        an.print_cost(est, live=True)
    assert "BUDGET" in str(e.value).upper(), \
        "the refusal must say why, so it is not mistaken for a crash"


def test_the_same_ceiling_only_WARNS_on_a_dry_run():
    """A dry run spends nothing, so it must still print the number rather than
    refusing — otherwise you cannot cost a run you have not been approved for.
    """
    est = {"clauses": 593, "calls": 78, "batch_size": 8, "provider": "sol",
           "model": "gpt-5.6-sol", "prompt_chars": 1, "in_tokens": 1,
           "chars_per_token": 4.59, "chars_per_token_method": "m",
           "out_tokens_low": 1, "out_tokens_high": 1, "out_tokens_ceiling": 1,
           "output_profile": "b8", "usd_low": 8.0, "usd": 10.05,
           "usd_ceiling": 13.79, "spent_so_far": 1.52, "budget": 8.50}
    an.print_cost(est, live=False)   # must not raise


# --------------------------------------------------------------------------
# the document-facts split (REPRODUCIBILITY.md "Document-agnostic vs
# document-specific"; NEW_DOCUMENT_RUNBOOK.md step 3)
#
# annotate_prompt.md is the PROCEDURE — how to annotate any document. The
# facts of one document's ontology (its authority levels, its principal
# names, its terminology corrections) live in a per-document docfacts file
# that load_template splices in at {{DOCFACTS:...}} markers. Running the
# Model-Spec facts on the constitution would TEACH FALSE FACTS ("root vs
# system", "there is no platform"), which is the defect this split removes.

import hashlib as _hashlib

DOCFACTS_MODEL_SPEC = "docfacts_model_spec.md"
DOCFACTS_CONSTITUTION = "docfacts_constitution.md"

# sha256 of the COMPOSED (system, user) pair as produced by an.load_template().
# This pin makes every prompt change a VISIBLE, deliberate act: annotation is
# paid, and a silent prompt change would make artifacts incomparable.
#
# PIN HISTORY (update the sha AND this log together, never the sha alone):
# - 2026-08-03 "13152a8c99ac…5298caec": the pre-docfacts-split prompt; proved
#   the split was a pure refactor on the default path (b8-comparable).
# - 2026-08-03 "0f6462f0009c…d8d1efc": DELIBERATE CHANGE, pilot iteration 2 —
#   added the no-assistant-only-chains paragraph to the procedure after the
#   18-pair mismatch analysis showed 11/18 span_deco failures were `__model`
#   solo chains golden's convention omits. Measured effect on the pilot set:
#   span_deco 0.500 -> 0.612, model-only chains 40 -> 0. Artifacts produced
#   under the OLD prompt: annotations_b8.json, annotations_pilot_ext.json.
#   Under the NEW: annotations_pilot_ext2.json.
PRE_SPLIT_SYSTEM_SHA = (
    "0f6462f0009c007e602c92e48e23ea994de86d54ec645cd85eb97c861d8d1efc")
PRE_SPLIT_USER_SHA = (
    "cea9193b30694bf5c6c49126f3ee0224da19e4c5bcc01ed49ccf14af25ec1d3c")


def _sha256(text):
    return _hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_the_default_docfacts_is_the_model_spec_file():
    assert an.DOCFACTS_PATH == DOCFACTS_MODEL_SPEC


def test_default_composition_is_byte_identical_to_the_pre_split_prompt():
    """The split must be a pure refactor on the default path: procedure +
    Model-Spec docfacts == the exact prompt every shipped artifact was
    produced under."""
    system, user = an.load_template()
    assert _sha256(system) == PRE_SPLIT_SYSTEM_SHA, (
        "the composed DEFAULT system prompt is not the pre-split prompt — "
        "live-run behaviour changed silently")
    assert _sha256(user) == PRE_SPLIT_USER_SHA


def test_the_procedure_file_names_no_document_ontology():
    """The procedure file itself — not a composition — must never state a
    fact about one document's authority levels. These phrases are the
    Model-Spec facts the 2026-08-03 audit found inline."""
    with open(os.path.join(HERE, an.PROMPT_TEMPLATE_PATH),
              encoding="utf-8") as f:
        src = f.read()
    for phrase in ("root rule",
                   "`root` and `system` are DIFFERENT",
                   "platform",
                   "old name"):
        assert phrase not in src, (
            f"annotate_prompt.md still teaches a document fact: {phrase!r}")


def test_no_composition_carries_an_unspliced_marker():
    for df in (DOCFACTS_MODEL_SPEC, DOCFACTS_CONSTITUTION):
        system, user = an.load_template(docfacts_path=df)
        assert "{{DOCFACTS" not in system + user, df


def test_constitution_composition_teaches_no_model_spec_facts():
    """On the constitution, `root` may survive only as (a) the grammar's
    closed vocabulary line — grammar.PRINCIPALS is shared, not per-document —
    or (b) a line telling the extractor the level does NOT exist here. Same
    for the retired `platform`."""
    system, user = an.load_template(docfacts_path=DOCFACTS_CONSTITUTION)
    blob = system + "\n" + user
    assert "root rule" not in blob
    assert "old name" not in blob
    vocab_lines = _principal_vocabulary_lines(system)
    assert len(vocab_lines) == 1
    for line in blob.splitlines():
        if "root" in line and line not in vocab_lines:
            assert "There is no" in line, (
                f"Model-Spec `root` teaching reached the constitution "
                f"prompt: {line.strip()!r}")
        if "platform" in line:
            assert "There is no" in line, line.strip()


def test_constitution_composition_names_the_documents_principals():
    system, _ = an.load_template(docfacts_path=DOCFACTS_CONSTITUTION)
    for word in ("Anthropic", "operator", "user"):
        assert word in system, word


def test_both_compositions_enumerate_the_principals_exactly_once():
    """The ENUMERATES regression guard, held on EVERY composition: a docfacts
    block must never delete or duplicate the closed vocabulary line."""
    for df in (DOCFACTS_MODEL_SPEC, DOCFACTS_CONSTITUTION):
        system, _ = an.load_template(docfacts_path=df)
        assert len(_principal_vocabulary_lines(system)) == 1, df


def test_both_compositions_hold_invariant_8():
    """Invariant 8 (no behaviour, no panel) binds on the COMPOSITION — a
    docfacts file is part of the sent prompt and must clear the same bans."""
    for df in (DOCFACTS_MODEL_SPEC, DOCFACTS_CONSTITUTION):
        system, user = an.load_template(docfacts_path=df)
        blob = (system + user).lower()
        for word in ("behaviour", "behavior", "panel", "judge", "relevant to",
                     "harm-avoidance", "over-caution", "gold"):
            assert word not in blob, (df, word)


def test_a_docfacts_file_missing_a_needed_key_is_refused(tmp_path):
    """A docfacts file that lacks a block the procedure calls for must fail
    loudly, not send a prompt with a hole (or a literal marker) in it."""
    p = tmp_path / "docfacts_incomplete.md"
    p.write_text("<!-- DOCFACTS:principals BEGIN -->\nx\n"
                 "<!-- DOCFACTS:principals END -->\n", encoding="utf-8")
    with pytest.raises(an.DocfactsError):
        an.load_template(docfacts_path=str(p))


def test_the_cli_exposes_a_docfacts_flag():
    args = an.build_parser().parse_args([])
    assert args.docfacts == DOCFACTS_MODEL_SPEC


# --------------------------------------------------------------------------
# 10. dry-run write guards (TOOLING item 4 — the behavior_atoms.json
#     clobber incident, guarded on BOTH annotators)

LIVE_SHAPED_ANN = {
    "atoms": [{"clause_id": "m0001", "name": "operator", "kind": "entity",
               "gloss": "g", "quote": "q", "span_id": "s1"}],
    "provenance": {"dry_run": False, "model": "gpt-5.6-luna",
                   "run_id": "shipped"},
}


def test_dryrun_output_lands_at_dryrun_suffix(fake_rows, tmp_path,
                                              monkeypatch):
    """Guard 1: an artifact carrying provenance.dry_run true must default to
    <name>.dryrun.json — for the generated default name AND for an explicit
    out path."""
    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda *a, **k: (_ for _ in ()).throw(
                            AssertionError("dry run opened a socket")))
    cfg = an.provider_config("luna")
    client = an.make_annotate_client(cfg, live=False,
                                     log_dir=str(tmp_path / "prompts"))
    art, path = an.run(client, fake_rows, model=cfg.model, batch_size=2,
                       out_dir=str(tmp_path), return_path=True)
    assert art["provenance"]["dry_run"] is True
    assert path.endswith(".dryrun.json")
    # explicit --out gains the suffix
    art2, path2 = an.run(client, fake_rows, model=cfg.model, batch_size=2,
                         out_dir=str(tmp_path),
                         out=str(tmp_path / "explicit.json"),
                         return_path=True)
    assert path2 == str(tmp_path / "explicit.dryrun.json")
    assert not (tmp_path / "explicit.json").exists()


def test_live_write_refuses_nonstub_overwrite_without_force(fake_rows,
                                                            tmp_path):
    """Guard 2, independent of guard 1: any write refuses an existing
    artifact whose provenance.dry_run is not true, naming the path; force
    is the only override."""
    out = tmp_path / "annotations.json"
    with open(out, "w") as f:
        json.dump(LIVE_SHAPED_ANN, f)
    before = open(out, "rb").read()
    client = FakeClient([good_response(fake_rows)])
    with pytest.raises(SystemExit) as e:
        an.run(client, fake_rows, model="m", batch_size=99, out=str(out),
               out_dir=str(tmp_path))
    assert str(out) in str(e.value)
    assert open(out, "rb").read() == before
    client2 = FakeClient([good_response(fake_rows)])
    art = an.run(client2, fake_rows, model="m", batch_size=99, out=str(out),
                 out_dir=str(tmp_path), force=True)
    assert art["provenance"]["dry_run"] is False
    assert open(out, "rb").read() != before


def test_annotate_cli_has_a_force_flag():
    ns = an.build_parser().parse_args([])
    assert ns.force is False
