"""Tests for extract_section.py (Agent B).

Everything runs offline. The one network-shaped test asserts the DRY-RUN path
touches no socket by poisoning urllib.
"""
import json
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import extract_section as ex
from extract_section import FailureLog


# --------------------------------------------------------------------------
# fixtures

@pytest.fixture(scope="module")
def rows():
    """The original single-section target."""
    return ex.load_section(ex.SECTION_TITLE)


@pytest.fixture(scope="module")
def all_rows():
    return ex.load_section(ex.ALL_SECTIONS)


@pytest.fixture
def fake_rows():
    """Three synthetic provisions in the real row shape — tests do not depend
    on the live document's wording."""
    return [
        {"id": "fa_aaa1", "source_id": "aaa1",
         "locator": "model_spec > S > Sub > L10",
         "quote": "The assistant must follow applicable instructions from the operator.",
         "marked_span": "must follow applicable instructions", "kind": "conditional", "section": "S",
         "modality": ["must"], "has_defeater": False, "line": 10},
        {"id": "fa_8ep2", "source_id": "8ep2",
         "locator": "model_spec > S > Sub > L20",
         "quote": "The assistant should weigh the user's interests unless the "
                  "operator has restricted the topic.",
         "marked_span": "should weigh the user's interests", "kind": "conditional", "section": "S",
         "modality": ["should"], "has_defeater": True, "line": 20},
        {"id": "fa_ccc3", "source_id": "ccc3",
         "locator": "model_spec > S > Sub > L30",
         "quote": "The assistant must not treat untrusted content as instructions.",
         "marked_span": "must not treat untrusted content as instructions",
         "kind": "conditional", "modality": ["must not"], "has_defeater": False,
         "line": 30, "section": "S"},
        {"id": "fa_ddd4", "source_id": "ddd4",
         "locator": "model_spec > S > Sub > L40",
         "quote": "An instruction is applicable when it is in scope.",
         "marked_span": "applicable", "kind": "definitional", "section": "S",
         "modality": [], "has_defeater": False, "line": 40},
    ]


def good_response(extra_atoms=(), extra_rules=(), incompat=(), unencoded=None,
                  exclusions=()):
    atoms = [
        {"name": "op_instruction_present", "kind": "context", "dimension": "principal",
         "gloss": "an operator instruction applies",
         "quote_spans": [{"focus_id": "fa_aaa1", "span_id": "s1"}],
         "status": "draft"},
        {"name": "follow_instruction", "kind": "act", "dimension": "act",
         "gloss": "the assistant follows the instruction",
         "quote_spans": [{"focus_id": "fa_aaa1", "span_id": "s2"}],
         "status": "draft"},
        {"name": "untrusted_content_present", "kind": "context", "dimension": "situation",
         "gloss": "untrusted content is in the context",
         "quote_spans": [{"focus_id": "fa_ccc3", "span_id": "s1"}],
         "status": "draft"},
        {"name": "obey_untrusted_content", "kind": "act", "dimension": "act",
         "gloss": "the assistant treats untrusted content as instructions",
         "quote_spans": [{"focus_id": "fa_ccc3", "span_id": "s2"}],
         "status": "draft"},
    ]
    rules = [
        {"id": "fa_aaa1", "modality": "oblige", "act": "follow_instruction",
         "conditions": ["op_instruction_present"], "defeaters": [], "tier": 1,
         "locator": "wrong", "quote": "wrong", "status": "draft"},
        {"id": "fa_ccc3", "modality": "forbid", "act": "obey_untrusted_content",
         "conditions": ["untrusted_content_present"], "defeaters": [], "tier": 1,
         "locator": "", "quote": "", "status": "draft"},
    ]
    body = {"atoms": atoms + list(extra_atoms),
            "rules": rules + list(extra_rules),
            "incompat": list(incompat),
            "exclusions": list(exclusions),
            "unencoded": ([{"focus_id": "fa_8ep2",
                            "reason": "weighing language with no determinate act"}]
                          if unencoded is None else unencoded)}
    return json.dumps(body)


class FakeClient:
    def __init__(self, text):
        self.text = text
        self.calls = 0

    def complete(self, system, user):
        self.calls += 1
        self.last = (system, user)
        return self.text


# --------------------------------------------------------------------------
# 1. the target section, as verified in the contract's §2

def test_section_counts_match_the_contract(rows):
    assert len(rows) == 62
    assert len(ex.encodable(rows)) == 42
    assert sum(len(r["quote"]) for r in rows) == 13924
    digit_initial = [r for r in rows if r["source_id"][0].isdigit()]
    assert len(digit_initial) == 13
    # ...and the prefix makes every one of them a legal identifier
    assert all(ex.IDENT_RE.match(r["id"]) for r in rows)


def test_inventory_and_the_direct_fallback_agree(rows):
    """load_section prefers Agent A's inventory (which owns the locator format
    the emitter reads) and falls back to the raw focus areas. The two must
    describe the same 62 provisions."""
    direct = ex._load_section_direct(ex.SECTION_TITLE, ex.FOCUS_AREAS_PATH)
    assert len(direct) == 62
    assert {r["id"] for r in direct} == {r["id"] for r in rows}
    assert {r["quote"] for r in direct} == {r["quote"] for r in rows}
    assert {r["kind"] for r in direct} == {r["kind"] for r in rows}


def test_fallback_is_used_when_inventory_is_unusable(monkeypatch):
    monkeypatch.setattr(ex, "_load_section_via_inventory", lambda *_: None)
    rows = ex.load_section(ex.SECTION_TITLE)
    assert len(rows) == 62 and len(ex.encodable(rows)) == 42


def test_rows_carry_the_agreed_keys(rows):
    for r in rows:
        assert all(k in r for k in ex.ROW_KEYS)
        assert isinstance(r["line"], int)


def test_every_row_id_is_a_legal_identifier_and_unique(rows):
    ids = [r["id"] for r in rows]
    assert len(set(ids)) == len(ids)
    assert all(re.match(r"^[a-z][a-z0-9_]*$", i) for i in ids)


# --------------------------------------------------------------------------
# 2. prompt

def test_provisions_sharing_a_clause_are_distinguishable_by_anchor(rows):
    """20 of the 42 conditional provisions share a sentence with another
    marker. Without the anchor span the model cannot tell them apart."""
    import collections
    prov = ex.encodable(rows)
    shared = {q for q, n in collections.Counter(r["quote"] for r in prov).items()
              if n > 1}
    assert shared, "fixture assumption: some clauses carry several markers"
    block = ex.build_provisions_block(prov)
    for r in prov:
        if r["quote"] in shared:
            assert f"[anchor]: {r['marked_span'].strip()}" in block
            assert r["marked_span"].strip() in r["quote"]
    # the whole clause is still shown, once, as s1
    for r in prov:
        assert f"s1 [whole clause]: {r['quote']}" in block


def test_section_text_prints_each_clause_once(rows):
    text = ex.build_section_text(rows)
    quotes = [r["quote"] for r in rows]
    assert len(set(quotes)) < len(quotes), "fixture assumption: duplicates exist"
    for q in set(quotes):
        assert text.count(q) >= 1
    # the multiply-marked clauses are not repeated verbatim
    dup = [q for q in set(quotes) if quotes.count(q) > 1]
    for q in dup:
        assert text.count(q) == 1


def test_prompt_contains_section_text_provisions_and_shapes(rows):
    system, user = ex.render_prompt(rows)
    assert "{{" not in system and "{{" not in user
    prov = ex.encodable(rows)
    assert f"({len(prov)})" in user
    for r in prov:
        assert r["id"] in user
        assert r["quote"] in user
    # the whole section, not only the encodable subset
    for r in rows:
        assert r["quote"] in user
    # the frozen shapes and the disciplines are stated
    for token in ("quote_spans", "^[a-z][a-z0-9_]*$", "oblige", "permit",
                  "unencoded", "logical", "textual", "assumed"):
        assert token in system
    assert "tier is always the integer 1" in system


def test_prompt_declares_no_schema_fields_beyond_the_dsl(rows):
    """The prompt must advertise exactly the dsl fields, and explicitly bar the
    one field a reader of the section would be tempted to add."""
    system, _ = ex.render_prompt(rows)
    declared = set(re.findall(r'"([a-z_]+)":', system))
    allowed = {"name", "kind", "dimension", "gloss", "quote_spans", "status",
               "locator", "focus_id", "quote", "id", "modality", "act",
               "conditions", "defeaters", "tier", "acts", "atoms", "license",
               "source", "rules", "incompat", "exclusions", "unencoded",
               "reason", "span_id"}
    assert declared <= allowed, f"prompt invents fields: {declared - allowed}"
    flat = re.sub(r"\s+", " ", system.lower())
    assert "do not add an authority field" in flat


# --------------------------------------------------------------------------
# 3. dry run makes no network call

def test_dry_run_makes_no_network_call(tmp_path, monkeypatch, rows):
    import urllib.request
    import providers

    def boom(*a, **k):
        raise AssertionError("network call attempted in dry run")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    cfg = providers.ProviderConfig(name="t", kind="openai-compatible",
                                   model="test-model", base_url="http://x")
    client = providers.make_client(cfg, live=False, log_dir=str(tmp_path / "plog"))
    assert isinstance(client, providers.DryRunClient)
    art, path, fail = ex.run_once(client, rows, model="test-model", seed=0,
                                  out_dir=str(tmp_path))
    assert art["dry_run"] is True
    assert client.calls == art["n_batches"] == 3      # 42 provisions / 14
    # every prompt was recorded to disk instead of sent
    assert len(os.listdir(tmp_path / "plog")) == 3
    # and the artifact is still contract-shaped
    assert art["section"] == ex.section_key(ex.ALL_SECTIONS)
    assert art["stats"]["unencoded_total"] == 42
    assert art["stats"]["coverage"] == 0.0
    assert json.load(open(path))["run_id"] == art["run_id"]


# --------------------------------------------------------------------------
# 4. schema conformance of a synthetic extraction

def test_synthetic_extraction_conforms_to_the_frozen_shape(fake_rows):
    fail = FailureLog(None)
    art = ex.build_extraction(good_response(), fake_rows, "m", "r1", fail)

    assert set(art) >= {"section", "model", "run_id", "atoms", "rules",
                        "incompat", "unencoded"}
    for a in art["atoms"]:
        assert set(a) == {"name", "kind", "dimension", "gloss",
                          "quote_spans", "status"}
        assert a["kind"] in ("context", "act")
        assert a["dimension"] in ("principal", "act", "epistemic",
                                 "situation", "deontic")
    for r in art["rules"]:
        assert set(r) == {"id", "modality", "act", "conditions", "defeaters",
                          "tier", "locator", "quote", "status"}
        assert r["modality"] in ("oblige", "forbid", "permit")
    assert art["stats"]["atoms_unverified"] == 0
    assert art["stats"]["rules_total"] == 2


def test_rule_provenance_is_taken_from_the_inventory_not_the_model(fake_rows):
    fail = FailureLog(None)
    art = ex.build_extraction(good_response(), fake_rows, "m", "r1", fail)
    r = {x["id"]: x for x in art["rules"]}
    assert r["fa_aaa1"]["locator"] == "model_spec > S > Sub > L10"
    assert r["fa_aaa1"]["quote"] == fake_rows[0]["quote"]      # model said "wrong"
    assert r["fa_ccc3"]["quote"] == fake_rows[2]["quote"]      # model left it blank


def test_tier_is_always_one(fake_rows):
    bad_tier = [{"id": "fa_8ep2", "modality": "permit", "act": "follow_instruction",
                 "conditions": [], "defeaters": [], "tier": 4,
                 "locator": "", "quote": "", "status": "draft"}]
    fail = FailureLog(None)
    art = ex.build_extraction(good_response(extra_rules=bad_tier, unencoded=[]),
                              fake_rows, "m", "r1", fail)
    assert art["rules"]
    assert all(r["tier"] == 1 for r in art["rules"])
    assert art["stats"]["rules_tier_corrected"] == 1
    assert all("authority" not in r for r in art["rules"])


# --------------------------------------------------------------------------
# 5. span verification

def test_unresolvable_span_ids_are_caught_and_the_atom_is_kept_and_counted(fake_rows):
    """The old failure mode was an authored quote that did not match. The new
    one is a lookup miss, and it has its own stage."""
    planted = [
        # span id that this provision does not offer
        {"name": "bad_span_id", "kind": "context", "dimension": "situation",
         "gloss": "", "quote_spans": [{"focus_id": "fa_aaa1", "span_id": "s99"}],
         "status": "draft"},
        # no span id at all, only text the model wrote
        {"name": "authored_quote", "kind": "context", "dimension": "situation",
         "gloss": "", "quote_spans": [
             {"focus_id": "fa_aaa1",
              "quote": "the assistant must always defer to the developer"}],
         "status": "draft"},
        # provision that does not exist
        {"name": "phantom_ctx", "kind": "context", "dimension": "situation",
         "gloss": "", "quote_spans": [{"focus_id": "fa_zzz9", "span_id": "s1"}],
         "status": "draft"},
    ]
    fail = FailureLog(None)
    art = ex.build_extraction(good_response(extra_atoms=planted), fake_rows,
                              "m", "r1", fail)
    by_name = {a["name"]: a for a in art["atoms"]}
    for n in ("bad_span_id", "authored_quote", "phantom_ctx"):
        assert n in by_name, "unresolved atoms must be kept, never dropped"
        assert by_name[n]["quote_spans"] == []
        assert by_name[n]["status"] == "draft"
    assert art["stats"]["atoms_unverified"] == 3      # the headline number
    assert art["stats"]["atoms_verified"] == 4
    assert art["stats"]["spans_rejected"] == 3
    assert fail.count("span_id") == 3, "lookup misses get their own stage"
    assert fail.count("span") == 0, "not the old authored-text failure"


def test_unknown_span_id_drops_only_that_span(fake_rows):
    atom = [{"name": "half_good", "kind": "context", "dimension": "situation",
             "gloss": "", "quote_spans": [
                 {"focus_id": "fa_aaa1", "span_id": "s99"},
                 {"focus_id": "fa_aaa1", "span_id": "s1"}],
             "status": "draft"}]
    fail = FailureLog(None)
    art = ex.build_extraction(json.dumps({"atoms": atom, "rules": [],
                                          "incompat": [], "unencoded": []}),
                              fake_rows, "m", "r1", fail)
    spans = art["atoms"][0]["quote_spans"]
    assert len(spans) == 1
    assert spans[0]["quote"] == fake_rows[0]["quote"]
    assert fail.count("span_id") == 1
    assert art["stats"]["atoms_verified"] == 1


def test_the_span_id_failure_names_what_was_offered(fake_rows):
    atom = [{"name": "x", "kind": "context", "dimension": "situation",
             "gloss": "", "quote_spans": [{"focus_id": "fa_aaa1",
                                           "span_id": "s99"}],
             "status": "draft"}]
    fail = FailureLog(None)
    ex.build_extraction(json.dumps({"atoms": atom, "rules": [], "incompat": [],
                                    "unencoded": []}), fake_rows, "m", "r1", fail)
    rec = [r for r in fail.records if r["stage"] == "span_id"][0]
    assert "s99" in rec["error"] and "offered" in rec["error"]
    assert rec["detail"]["focus_id"] == "fa_aaa1"


def test_model_authored_quote_text_never_reaches_the_artifact(fake_rows):
    """The point of the redesign: a fabricated quote is unrepresentable, not
    merely detectable. Even a span carrying BOTH a valid id and invented text
    resolves to the looked-up text."""
    invented = "the assistant must always defer to the developer"
    atom = [{"name": "sneaky", "kind": "context", "dimension": "situation",
             "gloss": "", "quote_spans": [{"focus_id": "fa_aaa1",
                                           "span_id": "s1",
                                           "quote": invented}],
             "status": "draft"}]
    fail = FailureLog(None)
    art = ex.build_extraction(json.dumps({"atoms": atom, "rules": [],
                                          "incompat": [], "unencoded": []}),
                              fake_rows, "m", "r1", fail)
    span = art["atoms"][0]["quote_spans"][0]
    assert span["quote"] == fake_rows[0]["quote"]
    assert invented not in json.dumps(art)
    assert art["stats"]["spans_authored_quote_ignored"] == 1


def test_no_resolved_quote_can_come_from_the_response(rows):
    """Over the whole real section: every quote written into the artifact is
    one of the enumerated candidate spans, so it is verbatim by construction
    whatever the model sends."""
    index = ex.span_index(rows)
    legal = {t for table in index.values() for t in table.values()}
    atoms = []
    for r in ex.encodable(rows):
        for sid in list(index[r["id"]]) + ["s99"]:
            atoms.append({"name": f"a_{r['id'][3:]}_{sid}", "kind": "context",
                          "dimension": "situation", "gloss": "",
                          "quote_spans": [{"focus_id": r["id"], "span_id": sid,
                                           "quote": "TOTALLY INVENTED TEXT"}],
                          "status": "draft"})
    fail = FailureLog(None)
    art = ex.build_extraction(json.dumps({"atoms": atoms, "rules": [],
                                          "incompat": [], "unencoded": []}),
                              rows, "m", "r1", fail)
    # NB: resolution keys on focus_id, which is unique; locator is NOT (see
    # test_locator_is_not_a_unique_key).
    by_fid = {r["id"]: r for r in rows}
    seen = 0
    for a in art["atoms"]:
        for sp in a["quote_spans"]:
            assert sp["quote"] in legal
            row = by_fid[sp["focus_id"]]
            assert sp["quote"] in row["quote"]        # verbatim, by construction
            assert sp["locator"] == row["locator"]
            seen += 1
    assert seen == sum(len(index[r["id"]]) for r in ex.encodable(rows))
    assert "TOTALLY INVENTED TEXT" not in json.dumps(art)
    assert fail.count("span_id") == 42        # one bogus id per provision


def test_locators_and_focus_ids_are_both_unique(all_rows):
    """Locators were ambiguous (34 distinct for 62 provisions, 7 covering
    different clause text); inventory now disambiguates them. Provenance still
    resolves on focus_id, but this guards the fix from regressing."""
    import collections
    assert len({r["id"] for r in all_rows}) == len(all_rows) == 259
    by_loc = collections.defaultdict(set)
    for r in all_rows:
        by_loc[r["locator"]].add(r["quote"])
    assert len(by_loc) == len(all_rows), "locator should identify one clause"
    assert not [loc for loc, qs in by_loc.items() if len(qs) > 1]


def test_every_surviving_span_is_a_verbatim_substring_of_a_real_provision(fake_rows):
    fail = FailureLog(None)
    art = ex.build_extraction(good_response(), fake_rows, "m", "r1", fail)
    by_loc = {r["locator"]: r for r in fake_rows}
    spans = 0
    for a in art["atoms"]:
        for s in a["quote_spans"]:
            assert s["locator"] in by_loc
            assert s["quote"] in by_loc[s["locator"]]["quote"]
            spans += 1
    assert spans == 4


def test_candidate_spans_are_rendered_under_each_provision(rows):
    """The model can only select an id it was shown, and the ids are local to
    each provision, so they must appear inside that provision's entry."""
    prov = ex.encodable(rows)
    block = ex.build_provisions_block(prov)
    entries = block.split("\n\n")
    assert len(entries) == len(prov)
    for entry, r in zip(entries, prov):
        spans = ex.candidate_spans(r)
        assert spans, f"{r['id']} offers no span to select"
        for sp in spans:
            tag = f" [{sp['role']}]" if sp["role"] in ("whole clause", "anchor") else ""
            assert f"\n  {sp['id']}{tag}: {sp['text']}" in entry
    # and they reach the real prompt
    _, user = ex.render_prompt(rows)
    assert "\n  s1 [whole clause]: " in user and "\n  s2 " in user


def test_a_marked_span_that_is_not_in_the_clause_is_not_offered():
    """The substring guard is what makes 'verbatim by construction' true for
    candidates that were not cut from the quote — marked_span comes from the
    inventory, not from slicing."""
    row = {"id": "fa_x", "quote": "The assistant must follow instructions.",
           "marked_span": "the assistant SHALL obey orders"}
    texts = [s["text"] for s in ex.candidate_spans(row)]
    assert texts == ["The assistant must follow instructions."]
    assert all(t in row["quote"] for t in texts)


def test_every_candidate_span_in_the_real_section_is_verbatim(rows):
    for r in rows:
        for sp in ex.candidate_spans(r):
            assert sp["text"] in r["quote"], f"{r['id']}/{sp['id']}"


def test_hardwrapped_clauses_still_yield_verbatim_candidate_spans():
    """The source joins hard-wrapped lines with newlines. Candidates are cut
    from the clause itself, so they stay exact substrings regardless."""
    row = {"id": "fa_aaa1", "quote": "The assistant must follow\napplicable "
                                     "instructions, unless they conflict.",
           "marked_span": "must follow\napplicable instructions"}
    spans = ex.candidate_spans(row)
    assert spans
    for s in spans:
        assert s["text"] in row["quote"]


# --------------------------------------------------------------------------
# 6. identifier regex

@pytest.mark.parametrize("bad", ["8ep1", "Follow_Instruction", "follow-instruction",
                                 "_leading", "has space", ""])
def test_illegal_atom_identifiers_are_rejected_and_logged(fake_rows, bad):
    atom = [{"name": bad, "kind": "context", "dimension": "situation",
             "gloss": "", "quote_spans": [], "status": "draft"}]
    fail = FailureLog(None)
    art = ex.build_extraction(json.dumps({"atoms": atom, "rules": [],
                                          "incompat": [], "unencoded": []}),
                              fake_rows, "m", "r1", fail)
    assert [a["name"] for a in art["atoms"]] == []
    assert fail.count("atom") == 1


@pytest.mark.parametrize("bad", ["8ep2", "FA_AAA1", "fa aaa1", "fa-aaa1"])
def test_illegal_rule_ids_are_rejected_and_logged(fake_rows, bad):
    rule = [{"id": bad, "modality": "oblige", "act": "x", "conditions": [],
             "defeaters": [], "tier": 1, "locator": "", "quote": "",
             "status": "draft"}]
    fail = FailureLog(None)
    art = ex.build_extraction(json.dumps({"atoms": [], "rules": rule,
                                          "incompat": [], "unencoded": []}),
                              fake_rows, "m", "r1", fail)
    assert art["rules"] == []
    assert art["stats"]["rules_bad_identifier"] == 1


def test_all_emitted_identifiers_match_the_regex(fake_rows):
    fail = FailureLog(None)
    art = ex.build_extraction(good_response(), fake_rows, "m", "r1", fail)
    for a in art["atoms"]:
        assert ex.IDENT_RE.match(a["name"])
    for r in art["rules"]:
        assert ex.IDENT_RE.match(r["id"])
    for u in art["unencoded"]:
        assert ex.IDENT_RE.match(u["focus_id"])


def test_fa_prefix_makes_digit_initial_ids_legal():
    assert ex.fa_id("8ep1") == "fa_8ep1"
    assert ex.IDENT_RE.match(ex.fa_id("8ep1"))


# --------------------------------------------------------------------------
# 7. unencoded is mandatory and complete

def test_unencoded_records_the_model_s_own_reason(fake_rows):
    fail = FailureLog(None)
    art = ex.build_extraction(good_response(), fake_rows, "m", "r1", fail)
    u = {x["focus_id"]: x["reason"] for x in art["unencoded"]}
    assert set(u) == {"fa_8ep2"}
    assert "weighing" in u["fa_8ep2"]
    assert art["stats"]["coverage"] == round(2 / 3, 4)


def test_unencoded_is_completed_when_the_model_forgets(fake_rows):
    fail = FailureLog(None)
    art = ex.build_extraction(good_response(unencoded=[]), fake_rows, "m", "r1", fail)
    u = {x["focus_id"]: x["reason"] for x in art["unencoded"]}
    assert set(u) == {"fa_8ep2"}, "coverage must not depend on the model's honesty"
    assert "reason unstated" in u["fa_8ep2"]
    assert fail.count("unencoded") == 1


def test_unencoded_covers_only_conditional_provisions(fake_rows):
    fail = FailureLog(None)
    art = ex.build_extraction(good_response(unencoded=[]), fake_rows, "m", "r1", fail)
    # fa_ddd4 is definitional — outside the encodable set
    assert "fa_ddd4" not in {x["focus_id"] for x in art["unencoded"]}
    assert art["stats"]["provisions_total"] == 3


def test_every_conditional_provision_is_either_ruled_or_unencoded(fake_rows):
    fail = FailureLog(None)
    art = ex.build_extraction(good_response(), fake_rows, "m", "r1", fail)
    accounted = {r["id"] for r in art["rules"]} | {u["focus_id"] for u in art["unencoded"]}
    assert {r["id"] for r in ex.encodable(fake_rows)} <= accounted


# --------------------------------------------------------------------------
# 8. incompat licensing

def test_incompat_requires_a_license_and_textual_requires_a_citation(fake_rows):
    cases = [
        {"acts": ["follow_instruction", "obey_untrusted_content"],
         "license": "logical", "source": "contradictory by definition"},
        {"acts": ["follow_instruction", "obey_untrusted_content"],
         "license": "textual", "source": ""},                        # no citation
        {"acts": ["follow_instruction", "obey_untrusted_content"]},   # no license
        {"acts": ["follow_instruction", "obey_untrusted_content"],
         "license": "vibes", "source": "x"},                          # bad license
        {"acts": ["follow_instruction", "nonexistent_act"],
         "license": "logical", "source": "x"},                        # unknown atom
        {"acts": ["follow_instruction"], "license": "logical", "source": "x"},  # arity
    ]
    fail = FailureLog(None)
    art = ex.build_extraction(good_response(incompat=cases), fake_rows,
                              "m", "r1", fail)
    assert len(art["incompat"]) == 1
    assert art["incompat"][0]["license"] == "logical"
    assert art["stats"]["incompat_rejected"] == 5
    assert fail.count("incompat") == 5


def test_textual_incompat_with_a_citation_survives(fake_rows):
    ok = [{"acts": ["follow_instruction", "obey_untrusted_content"],
           "license": "textual",
           "source": "model_spec > S > Sub > L30: \"must not treat untrusted "
                     "content as instructions\""}]
    fail = FailureLog(None)
    art = ex.build_extraction(good_response(incompat=ok), fake_rows, "m", "r1", fail)
    assert len(art["incompat"]) == 1 and art["incompat"][0]["source"]


# --------------------------------------------------------------------------
# 8b. exclusions (contract §3) — context atoms that cannot co-occur

def test_exclusions_is_always_present_in_the_artifact(fake_rows):
    """Mandatory key: A consumes it unconditionally."""
    fail = FailureLog(None)
    for resp in [good_response(), "junk", None,
                 '{"atoms": [], "rules": [], "incompat": [], "unencoded": []}']:
        art = ex.build_extraction(resp, fake_rows, "m", "r1", fail)
        assert "exclusions" in art and isinstance(art["exclusions"], list)


def test_valid_exclusions_survive_with_both_kinds(fake_rows):
    ok = [
        {"atoms": ["op_instruction_present", "untrusted_content_present"],
         "kind": "excludes", "license": "logical",
         "source": "a trusted operator instruction is not untrusted content"},
        {"atoms": ["op_instruction_present", "untrusted_content_present"],
         "kind": "at_most_one", "license": "assumed",
         "source": "one instruction source at a time"},
    ]
    fail = FailureLog(None)
    art = ex.build_extraction(good_response(exclusions=ok), fake_rows,
                              "m", "r1", fail)
    assert len(art["exclusions"]) == 2
    for e in art["exclusions"]:
        assert set(e) == {"atoms", "kind", "license", "source"}
        assert e["kind"] in ("at_most_one", "excludes")
        assert e["license"] in ("logical", "textual", "assumed")
    assert art["stats"]["exclusions_excludes"] == 1
    assert art["stats"]["exclusions_at_most_one"] == 1


def test_exclusion_arity_and_licensing_are_enforced(fake_rows):
    ctx = ["op_instruction_present", "untrusted_content_present"]
    cases = [
        # excludes takes exactly 2
        {"atoms": ctx + ["op_instruction_present"], "kind": "excludes",
         "license": "logical", "source": "x"},
        {"atoms": ["op_instruction_present"], "kind": "excludes",
         "license": "logical", "source": "x"},
        # at_most_one takes >= 2
        {"atoms": ["op_instruction_present"], "kind": "at_most_one",
         "license": "logical", "source": "x"},
        # licensing
        {"atoms": ctx, "kind": "excludes", "license": "textual", "source": ""},
        {"atoms": ctx, "kind": "excludes", "source": "x"},
        {"atoms": ctx, "kind": "excludes", "license": "hunch", "source": "x"},
        # bad kind
        {"atoms": ctx, "kind": "requires", "license": "logical", "source": "x"},
        # unknown atom
        {"atoms": ["op_instruction_present", "no_such_ctx"], "kind": "excludes",
         "license": "logical", "source": "x"},
        # illegal identifier
        {"atoms": ["op_instruction_present", "8bad"], "kind": "excludes",
         "license": "logical", "source": "x"},
    ]
    fail = FailureLog(None)
    art = ex.build_extraction(good_response(exclusions=cases), fake_rows,
                              "m", "r1", fail)
    assert art["exclusions"] == []
    assert art["stats"]["exclusions_rejected"] == len(cases)
    assert fail.count("exclusion") == len(cases)


def test_exclusions_may_not_name_act_atoms(fake_rows):
    """Acts belong in incompat; mixing them would compile to the wrong ASP."""
    bad = [{"atoms": ["follow_instruction", "obey_untrusted_content"],
            "kind": "excludes", "license": "logical", "source": "x"}]
    fail = FailureLog(None)
    art = ex.build_extraction(good_response(exclusions=bad), fake_rows,
                              "m", "r1", fail)
    assert art["exclusions"] == []
    assert "incompat" in fail.records[-1]["error"]


def test_exclusions_reach_the_checker_and_expose_dead_rules(fake_rows):
    """A rule whose trigger needs two mutually excluded context atoms is dead;
    the checker must say so rather than the solver inventing a conflict in an
    impossible world."""
    dead = [{"id": "fa_8ep2", "modality": "oblige", "act": "follow_instruction",
             "conditions": ["op_instruction_present", "untrusted_content_present"],
             "defeaters": [], "tier": 1, "locator": "", "quote": "",
             "status": "draft"}]
    excl = [{"atoms": ["op_instruction_present", "untrusted_content_present"],
             "kind": "excludes", "license": "logical", "source": "disjoint"}]
    fail = FailureLog(None)
    art = ex.build_extraction(
        good_response(extra_rules=dead, exclusions=excl, unencoded=[]),
        fake_rows, "m", "r1", fail)
    ch = art["check"]
    if ch["checker_available"]:
        bad = {e["id"]: e for e in ch["rules"] if not e["ok"]}
        assert "fa_8ep2" in bad and bad["fa_8ep2"]["stage"] == "coherence"
    # ...and without the exclusion the same rule looks fine
    fail2 = FailureLog(None)
    art2 = ex.build_extraction(good_response(extra_rules=dead, unencoded=[]),
                               fake_rows, "m", "r1", fail2)
    if art2["check"]["checker_available"]:
        assert art2["check"]["rules_failed"] == 0


def test_prompt_states_the_exclusion_discipline(rows):
    system, _ = ex.render_prompt(rows)
    for token in ("exclusions", "at_most_one", "excludes",
                  "exactly two atoms", "context atoms"):
        assert token in system


# --------------------------------------------------------------------------
# 9. per-item resilience — nothing raises

JUNK = [
    None,
    "",
    "I'm sorry, I can't help with that.",
    "{ not json at all ",
    "[1, 2, 3]",
    '{"atoms": [{"name": "x",}], "rules": []}',        # trailing comma
    '{"atoms": [1, 2}',                                # brace-balanced, invalid
    "Here is the extraction:\n{\"atoms\": [}\nHope that helps.",
    '{"atoms": [], "rules": [], "incompat": [], "unencoded": [], }',
    '{"atoms": "not a list", "rules": 7, "incompat": null}',
    '{"atoms": [null, 3, {"name": null}], "rules": [[], "x"]}',
    "```json\n{\"atoms\": [], \"rules\": []}\n```",
    123,
]


@pytest.mark.parametrize("junk", JUNK)
def test_junk_response_records_a_failure_and_yields_a_valid_artifact(fake_rows, junk):
    fail = FailureLog(None)
    art = ex.build_extraction(junk, fake_rows, "m", "r1", fail)   # must not raise
    assert art["section"] == ex.section_key(ex.ALL_SECTIONS)
    assert isinstance(art["atoms"], list) and isinstance(art["rules"], list)
    assert isinstance(art["incompat"], list)
    # every conditional provision is accounted for, with a reason
    assert len(art["unencoded"]) == 3
    assert all(u["reason"] for u in art["unencoded"])
    assert fail.count() >= 1


@pytest.mark.parametrize("value", [123, 4.5, ["a"], {"no": "text"}])
def test_non_string_content_never_reaches_the_parser(value):
    """A provider returning a number, a list, or an envelope without text must
    degrade to "no response", not crash the parser."""
    obj, err = ex.parse_response(value)
    assert obj is None and err
    env = ex.as_envelope(value)
    assert env["text"] is None or isinstance(env["text"], str)


def test_unparseable_response_is_flagged_not_silently_empty(fake_rows):
    fail = FailureLog(None)
    art = ex.build_extraction("total garbage", fake_rows, "m", "r1", fail)
    assert art["stats"]["response_parsed"] is False
    assert fail.count("response") == 1
    # ...whereas a well-formed but empty answer parses
    fail2 = FailureLog(None)
    art2 = ex.build_extraction('{"atoms": [], "rules": [], "incompat": [], '
                               '"unencoded": []}', fake_rows, "m", "r1", fail2)
    assert art2["stats"]["response_parsed"] is True


def test_provider_exception_is_recorded_and_the_run_completes(tmp_path, fake_rows):
    class Exploding:
        def complete(self, system, user):
            raise RuntimeError("connection reset")

    art, path, fail = ex.run_once(Exploding(), fake_rows, model="m", seed=0,
                                  out_dir=str(tmp_path))
    assert path and os.path.exists(path)
    assert fail.count("call") == 1
    assert art["dry_run"] is False
    assert len(art["unencoded"]) == 3


def test_failures_are_written_as_jsonl(tmp_path, fake_rows):
    log = tmp_path / "fails.jsonl"
    art, _, fail = ex.run_once(FakeClient("garbage"), fake_rows, model="m",
                               seed=0, out_dir=str(tmp_path), log_path=str(log))
    lines = [json.loads(x) for x in log.read_text().splitlines() if x.strip()]
    assert lines and all({"ts", "run_id", "model", "stage", "error"} <= set(l)
                         for l in lines)
    assert any(l["stage"] == "response" for l in lines)


# --------------------------------------------------------------------------
# 10. checker integration — report, don't discard

def test_checker_reports_bad_rules_without_dropping_them(fake_rows):
    broken = [{"id": "fa_8ep2", "modality": "oblige", "act": "no_such_act",
               "conditions": ["no_such_ctx"], "defeaters": [], "tier": 1,
               "locator": "", "quote": "", "status": "draft"}]
    fail = FailureLog(None)
    art = ex.build_extraction(good_response(extra_rules=broken, unencoded=[]),
                              fake_rows, "m", "r1", fail)
    assert "fa_8ep2" in {r["id"] for r in art["rules"]}, "reported, not discarded"
    ch = art["check"]
    if ch["checker_available"]:
        bad = {e["id"]: e for e in ch["rules"] if not e["ok"]}
        assert "fa_8ep2" in bad
        assert bad["fa_8ep2"]["errors"]
        assert ch["rules_ok"] == 2


def test_checker_passes_a_clean_extraction(fake_rows):
    fail = FailureLog(None)
    art = ex.build_extraction(good_response(), fake_rows, "m", "r1", fail)
    ch = art["check"]
    if ch["checker_available"]:
        assert ch["rules_failed"] == 0
        assert ch["vocabulary_errors"] == []


# --------------------------------------------------------------------------
# 11b. conflict capability — an extraction can be 100% complete and still
#      structurally incapable of producing any conflict (Agent A's finding on
#      the live together-cheap run: 24 rules, 17 acts, no act contested,
#      incompat [] -> |C_tool| = 0)

def unique_act_response(n=4):
    """Every rule gets its own bespoke act; no incompat. The failure shape."""
    atoms, rules = [], []
    for i, r in enumerate(("fa_aaa1", "fa_8ep2", "fa_ccc3")[:n]):
        act = f"bespoke_act_{i}"
        atoms.append({"name": act, "kind": "act", "dimension": "act",
                      "gloss": "", "quote_spans": [], "status": "draft"})
        rules.append({"id": r, "modality": "oblige", "act": act,
                      "conditions": [], "defeaters": [], "tier": 1,
                      "locator": "", "quote": "", "status": "draft"})
    return json.dumps({"atoms": atoms, "rules": rules, "incompat": [],
                       "exclusions": [], "unencoded": []})


def shared_act_response():
    """Two rules meet on one act with opposing modalities."""
    atoms = [{"name": "comply", "kind": "act", "dimension": "act",
              "gloss": "", "quote_spans": [], "status": "draft"}]
    rules = [{"id": "fa_aaa1", "modality": "oblige", "act": "comply",
              "conditions": [], "defeaters": [], "tier": 1, "locator": "",
              "quote": "", "status": "draft"},
             {"id": "fa_ccc3", "modality": "forbid", "act": "comply",
              "conditions": [], "defeaters": [], "tier": 1, "locator": "",
              "quote": "", "status": "draft"}]
    return json.dumps({"atoms": atoms, "rules": rules, "incompat": [],
                       "exclusions": [], "unencoded": []})


def test_one_act_per_rule_with_no_incompat_raises_the_warning(fake_rows):
    fail = FailureLog(None)
    art = ex.build_extraction(unique_act_response(), fake_rows, "m", "r1", fail)
    s = art["stats"]
    assert s["distinct_acts"] == 3 and s["rules_total"] == 3
    assert s["rules_per_act"] == 1.0
    assert s["acts_with_both_oblige_and_forbid"] == 0
    assert s["incompat_count"] == 0
    assert s["conflict_capable"] is False
    assert art["warnings"] and "CANNOT PRODUCE CONFLICTS" in art["warnings"][0]
    assert fail.count("conflict_capability") == 1


def test_a_contested_act_clears_the_warning(fake_rows):
    fail = FailureLog(None)
    art = ex.build_extraction(shared_act_response(), fake_rows, "m", "r1", fail)
    s = art["stats"]
    assert s["distinct_acts"] == 1 and s["rules_per_act"] == 2.0
    assert s["acts_with_both_oblige_and_forbid"] == 1
    assert s["contested_acts"] == ["comply"]
    assert s["conflict_capable"] is True
    assert art["warnings"] == []
    assert fail.count("conflict_capability") == 0


def test_an_incompat_alone_clears_the_warning(fake_rows):
    """Indirect conflicts: two obliges on acts that cannot co-occur."""
    fail = FailureLog(None)
    art = ex.build_extraction(good_response(incompat=[
        {"acts": ["follow_instruction", "obey_untrusted_content"],
         "license": "logical", "source": "opposites"}]),
        fake_rows, "m", "r1", fail)
    assert art["stats"]["acts_with_both_oblige_and_forbid"] == 0
    assert art["stats"]["incompat_count"] == 1
    assert art["stats"]["conflict_capable"] is True
    assert art["warnings"] == []


def test_capability_diagnostics_are_reported_on_every_artifact(fake_rows):
    fail = FailureLog(None)
    for resp in [good_response(), unique_act_response(), "junk", None]:
        art = ex.build_extraction(resp, fake_rows, "m", "r1", fail)
        for k in ("distinct_acts", "rules_per_act", "max_rules_on_one_act",
                  "acts_with_both_oblige_and_forbid", "incompat_count",
                  "conflict_capable", "declared_act_atoms"):
            assert k in art["stats"]


def test_the_live_run_shape_would_have_been_caught(fake_rows):
    """Reconstruct Agent A's numbers: 24 rules over 17 acts, none contested,
    no incompat. The warning must fire even though coverage is high."""
    atoms, rules = [], []
    for i in range(17):
        atoms.append({"name": f"act_{i}", "kind": "act", "dimension": "act",
                      "gloss": "", "quote_spans": [], "status": "draft"})
    prov = [r["id"] for r in ex.encodable(fake_rows)]
    for i in range(3):
        rules.append({"id": prov[i], "modality": "oblige" if i else "forbid",
                      "act": f"act_{i}", "conditions": [], "defeaters": [],
                      "tier": 1, "locator": "", "quote": "", "status": "draft"})
    fail = FailureLog(None)
    art = ex.build_extraction(json.dumps({"atoms": atoms, "rules": rules,
                                          "incompat": [], "exclusions": [],
                                          "unencoded": []}),
                              fake_rows, "m", "r1", fail)
    assert art["stats"]["coverage"] == 1.0, "coverage is fine..."
    assert art["stats"]["conflict_capable"] is False, "...and it is still vacuous"
    assert art["warnings"]


def test_declined_incompat_pairs_are_recorded_as_evidence(fake_rows):
    body = json.loads(good_response())
    body["incompat_declined"] = [
        {"acts": ["follow_instruction", "obey_untrusted_content"],
         "reason": "both can be done in one turn"}]
    fail = FailureLog(None)
    art = ex.build_extraction(json.dumps(body), fake_rows, "m", "r1", fail)
    assert art["stats"]["incompat_declined"] == 1
    rec = [r for r in fail.records if r["stage"] == "incompat_declined"][0]
    assert rec["detail"]["reason"] == "both can be done in one turn"


def test_prompt_pushes_act_reuse_and_deliberate_incompat(rows):
    system, _ = ex.render_prompt(rows)
    flat = re.sub(r"\s+", " ", system)
    assert "Two rules can only conflict if they are about the SAME act" in flat
    assert "Expect FAR FEWER acts than rules" in flat
    assert "incompat_declined" in system
    assert ex.AXIOM_ASK.split("\n")[0] in ex.AXIOM_ASK
    ask = ex.AXIOM_ASK
    assert "pairwise" in ask and "incompat_declined" in ask


def test_carried_act_list_is_prominent_and_urges_reuse(tmp_path, rows):
    client = ScriptedClient(rows)
    ex.run_once(client, rows, model="m", seed=0, out_dir=str(tmp_path),
                batch_size=14)
    u = client.prompts[1]
    assert "ACT atoms already declared" in u and "REUSE THESE" in u
    assert "guarantees zero conflicts" in u


# --------------------------------------------------------------------------
# 11c. document scope: --section <title> | all

def test_all_loads_the_whole_document_in_order(all_rows):
    assert len(all_rows) == 259
    assert len(ex.encodable(all_rows)) == 174
    assert ex.section_order(all_rows) == [
        "The chain of command", "Stay in bounds", "Seek the truth together",
        "Do the best work", "Use appropriate style"]
    lines = [r["line"] for r in all_rows]
    assert lines == sorted(lines)


def test_single_section_scope_is_a_subset_of_all(rows, all_rows):
    assert {r["id"] for r in rows} <= {r["id"] for r in all_rows}
    assert all(r["section"] == ex.SECTION_TITLE for r in rows)


@pytest.mark.parametrize("title,focus,cond", [
    ("The chain of command", 62, 42), ("Stay in bounds", 76, 61),
    ("Seek the truth together", 40, 27), ("Do the best work", 30, 22),
    ("Use appropriate style", 51, 22)])
def test_each_section_loads_its_own_provisions(title, focus, cond):
    got = ex.load_section(title)
    assert len(got) == focus
    assert len(ex.encodable(got)) == cond


def test_section_key_matches_the_contract():
    assert ex.section_key("The chain of command") == "chain_of_command"
    assert ex.section_key("all") == "all"
    assert ex.section_key("Stay in bounds") == "stay_in_bounds"
    assert ex.section_key("Seek the truth together") == "seek_the_truth_together"


def test_artifact_section_field_follows_the_scope(fake_rows):
    fail = FailureLog(None)
    for scope in ("all", "The chain of command"):
        art = ex.build_extraction(good_response(), fake_rows, "m", "r1", fail,
                                  section=scope)
        assert art["section"] == ex.section_key(scope)


def test_batch_plan_batches_within_sections(all_rows):
    plan = ex.batch_plan(all_rows, 14)
    assert len(plan) == 14
    # every request's context is exactly one section, and its batch belongs
    for title, srows, group in plan:
        assert {r["section"] for r in srows} == {title}
        assert all(r["section"] == title for r in group)
    # sections appear in document order and provisions are partitioned exactly
    assert [t for t, _, _ in plan][:3] == ["The chain of command"] * 3
    encoded = [r["id"] for _, _, g in plan for r in g]
    assert encoded == [r["id"] for r in ex.encodable(all_rows)]
    assert len(set(encoded)) == 174


def test_a_request_never_carries_another_sections_text(all_rows):
    plan = ex.batch_plan(all_rows, 14)
    title, srows, group = plan[5]           # somewhere in Stay in bounds
    _, user = ex.render_prompt(srows, group, (), 6, len(plan),
                               section_title=title)
    other = [r for r in all_rows if r["section"] != title]
    assert not any(r["quote"] in user for r in other if len(r["quote"]) > 60)
    assert title in user


def test_a_shared_clause_is_kept_when_only_one_of_its_provisions_is_batched():
    """6 clauses carry several markers. Eliding one because its neighbour is
    being encoded would delete the neighbour's text from the prompt."""
    rows = [{"id": "fa_a", "line": 10, "quote": "Shared sentence here.",
             "locator": "m > S > L10", "kind": "conditional", "section": "S",
             "marked_span": "Shared", "modality": [], "has_defeater": False},
            {"id": "fa_b", "line": 10, "quote": "Shared sentence here.",
             "locator": "m > S > L10", "kind": "conditional", "section": "S",
             "marked_span": "sentence here", "modality": [],
             "has_defeater": False}]
    partial = ex.build_section_text(rows, omit=[rows[0]])
    assert "Shared sentence here." in partial, "fa_b would have lost its text"
    both = ex.build_section_text(rows, omit=rows)
    assert "Shared sentence here." not in both
    assert "fa_a, fa_b — quoted in full below" in both


def test_batch_text_is_not_paid_for_twice(all_rows):
    """A clause encoded in this request appears in full in the provisions
    block, so the section text shows a marker in its place."""
    plan = ex.batch_plan(all_rows, 14)
    title, srows, group = plan[0]
    text = ex.build_section_text(srows, omit=group)
    solo = [r for r in group
            if sum(1 for x in srows if x["quote"] == r["quote"]) == 1]
    assert solo
    for r in solo:
        assert f"[{r['id']} — quoted in full below]" in text
        assert text.count(r["quote"]) == 0
    # non-batch clauses of the same section are still there in full
    rest = [r for r in ex.encodable(srows) if r not in group]
    assert any(r["quote"] in text for r in rest)


def test_run_once_sends_each_request_only_its_own_section(tmp_path, all_rows):
    """Covers the wiring, not just render_prompt: a full run must never put
    another section's clauses in a request."""
    client = ScriptedClient(all_rows)
    ex.run_once(client, all_rows, model="m", seed=0, out_dir=str(tmp_path),
                batch_size=14, section="all")
    plan = ex.batch_plan(all_rows, 14)
    assert len(client.prompts) == len(plan) == 14
    for user, (title, srows, group) in zip(client.prompts, plan):
        body = user.split("===== FULL SECTION TEXT", 1)[1] \
                   .split("===== PROVISIONS TO ENCODE", 1)[0]
        own = {r["quote"] for r in srows}
        for r in all_rows:
            if len(r["quote"]) > 60 and r["quote"] not in own:
                assert r["quote"] not in body, \
                    f"request for {title!r} carried {r['section']!r} text"
        # its own non-batched clauses ARE there
        rest = [r for r in srows if r not in group and len(r["quote"]) > 60]
        assert any(r["quote"] in body for r in rest)


def test_atoms_carry_across_sections_not_just_batches(tmp_path, all_rows):
    """Cross-section act sharing is the point: an act declared in section 1
    must be offered to section 5."""
    client = ScriptedClient(all_rows)
    ex.run_once(client, all_rows, model="m", seed=0, out_dir=str(tmp_path),
                batch_size=14, section="all")
    first_section = client.prompts[0]
    last_section = client.prompts[-1]
    assert "shared_ctx" not in first_section.split("===== PROVISIONS")[0]
    carried_last = last_section.split("===== PROVISIONS")[0]
    assert "shared_ctx" in carried_last
    # an act minted in the very first request survives to the very last
    first_act = re.search(r"act_(fa_[a-z0-9_]+)", client.prompts[1]).group(0)
    assert first_act in carried_last


def test_axioms_asked_once_at_the_end_of_the_whole_run(tmp_path, all_rows):
    client = ScriptedClient(all_rows)
    ex.run_once(client, all_rows, model="m", seed=0, out_dir=str(tmp_path),
                batch_size=14, section="all")
    asks = [p for p in client.prompts if ex.AXIOM_ASK in p]
    assert len(asks) == 1
    assert asks[0] is client.prompts[-1]
    assert all(ex.AXIOM_DEFER in p for p in client.prompts[:-1])


def test_stats_report_per_section_and_total(tmp_path, all_rows):
    art, _, _ = ex.run_once(ScriptedClient(all_rows), all_rows, model="m",
                            seed=0, out_dir=str(tmp_path), batch_size=14,
                            section="all")
    s = art["stats"]
    assert s["n_sections"] == 5
    assert set(s["sections"]) == set(ex.section_order(all_rows))
    assert s["sections"]["Stay in bounds"]["provisions"] == 61
    assert s["sections"]["The chain of command"]["provisions"] == 42
    assert sum(v["provisions"] for v in s["sections"].values()) == 174
    assert s["provisions_total"] == 174
    assert s["coverage"] == 1.0
    assert all(v["coverage"] == 1.0 for v in s["sections"].values())
    # capability is global, not per section
    assert "conflict_capable" in s and "sections" not in s["conflict_capable"] \
        if isinstance(s["conflict_capable"], dict) else True


def test_carried_atoms_are_capped_but_acts_are_never_dropped():
    from dsl import Atom
    atoms = ([Atom(name=f"c{i}", kind="context", dimension="situation")
              for i in range(200)]
             + [Atom(name=f"a{i}", kind="act", dimension="act")
                for i in range(150)])
    kept, dropped = ex.cap_carried_atoms(atoms)
    assert dropped == 200 - ex.MAX_CARRIED_CONTEXT
    assert sum(1 for a in kept if a.kind == "act") == 150, "acts never dropped"
    assert sum(1 for a in kept if a.kind == "context") == ex.MAX_CARRIED_CONTEXT
    # the ones kept are the most recent
    names = {a.name for a in kept}
    assert "c199" in names and "c0" not in names
    # declaration order preserved
    assert [a.name for a in kept] == [a.name for a in atoms if a.name in names]


def test_small_carried_lists_are_not_capped():
    from dsl import Atom
    atoms = [Atom(name=f"c{i}", kind="context", dimension="situation")
             for i in range(10)]
    kept, dropped = ex.cap_carried_atoms(atoms)
    assert dropped == 0 and len(kept) == 10


def test_long_context_lists_render_compactly_but_acts_keep_glosses():
    from dsl import Atom
    atoms = ([Atom(name=f"c{i}", kind="context", dimension="situation",
                   gloss="a long gloss that would bloat the prompt")
              for i in range(25)]
             + [Atom(name="do_x", kind="act", dimension="act",
                     gloss="the act gloss must survive")])
    block = ex.render_known_atoms(atoms)
    assert "a long gloss that would bloat the prompt" not in block
    assert "the act gloss must survive" in block, \
        "act reuse cannot be judged from a name alone"


# --------------------------------------------------------------------------
# 12. truncation is its own failure class (live smoke test on gpt-oss-20b:
#     8000 completion tokens, 31,767 chars of reasoning, 339 of content)

def truncated_envelope(text='{"atoms": [{"name": "op_inst', reasoning="x" * 31767):
    return {"text": text, "finish_reason": "length",
            "reasoning": reasoning,
            "usage": {"prompt_tokens": 8690, "completion_tokens": 8000}}


def test_truncated_response_is_not_reported_as_a_parse_error(fake_rows):
    fail = FailureLog(None)
    art = ex.build_extraction(truncated_envelope(), fake_rows, "m", "r1", fail)
    stages = [r["stage"] for r in fail.records]
    assert "truncated_output" in stages
    assert "response" not in stages, \
        "truncation and malformed JSON need different fixes; do not conflate"
    assert art["stats"]["truncated_batches"] == 1


def test_truncation_failure_carries_the_diagnostic_numbers(fake_rows):
    fail = FailureLog(None)
    ex.build_extraction(truncated_envelope(), fake_rows, "m", "r1", fail)
    rec = [r for r in fail.records if r["stage"] == "truncated_output"][0]
    d = rec["detail"]
    assert d["completion_tokens"] == 8000
    assert d["prompt_tokens"] == 8690
    assert d["reasoning_chars"] == 31767
    assert d["content_chars"] == len('{"atoms": [{"name": "op_inst')
    assert d["finish_reason"] == "length"


@pytest.mark.parametrize("reason", ["length", "max_tokens", "MAX_TOKENS",
                                    "max_output_tokens"])
def test_all_provider_truncation_reasons_are_recognized(fake_rows, reason):
    fail = FailureLog(None)
    ex.build_extraction({"text": "{", "finish_reason": reason, "usage": {}},
                        fake_rows, "m", "r1", fail)
    assert fail.count("truncated_output") == 1


def test_untruncated_junk_is_still_a_parse_error(fake_rows):
    fail = FailureLog(None)
    ex.build_extraction({"text": "garbage", "finish_reason": "stop"},
                        fake_rows, "m", "r1", fail)
    stages = [r["stage"] for r in fail.records]
    assert "response" in stages and "truncated_output" not in stages


def test_a_truncated_batch_does_not_lose_the_other_batches(tmp_path, fake_rows):
    class HalfTruncating:
        def __init__(self):
            self.n = 0

        def complete_envelope(self, system, user):
            self.n += 1
            if self.n == 1:
                return truncated_envelope()
            return {"text": good_response(unencoded=[]), "finish_reason": "stop"}

    art, _, fail = ex.run_once(HalfTruncating(), fake_rows, model="m", seed=0,
                               out_dir=str(tmp_path), batch_size=1)
    assert art["n_batches"] == 3
    assert fail.count("truncated_output") == 1
    assert art["stats"]["truncated_batches"] == 1
    assert art["rules"], "surviving batches must still contribute"


def test_reasoning_is_written_alongside_the_run(tmp_path, fake_rows):
    class Reasoner:
        def complete_envelope(self, system, user):
            return {"text": good_response(unencoded=[]), "finish_reason": "stop",
                    "reasoning": "long chain of thought here"}

    art, _, _ = ex.run_once(Reasoner(), fake_rows, model="m", seed=0,
                            out_dir=str(tmp_path), batch_size=1)
    files = sorted(os.listdir(tmp_path / "reasoning"))
    assert len(files) == art["n_batches"] == 3
    assert all(f.startswith(art["run_id"]) for f in files)
    body = (tmp_path / "reasoning" / files[0]).read_text()
    assert body == "long chain of thought here"
    assert art["stats"]["reasoning_chars"] == 3 * len(body)


def test_plain_string_clients_still_work(fake_rows):
    """providers.DryRunClient/LiveClient return bare strings; no finish_reason
    is available for them, and that must degrade rather than break."""
    fail = FailureLog(None)
    art = ex.build_extraction(good_response(), fake_rows, "m", "r1", fail)
    assert art["stats"]["rules_total"] == 2
    assert art["stats"]["truncated_batches"] == 0


def _client(kind):
    """An InstrumentedClient without the key check or any socket."""
    c = ex.InstrumentedClient.__new__(ex.InstrumentedClient)
    c.provider = type("P", (), {"kind": kind})()
    return c


def test_openai_style_envelope_captures_reasoning_and_finish_reason():
    """The exact shape the together-cheap smoke test returned."""
    env = _client("openai-compatible")._envelope({
        "choices": [{"finish_reason": "length",
                     "message": {"content": '{"atoms": [', "reasoning": "R" * 31767}}],
        "usage": {"prompt_tokens": 8690, "completion_tokens": 8000}})
    assert env["finish_reason"] == "length"
    assert len(env["reasoning"]) == 31767
    assert env["usage"] == {"prompt_tokens": 8690, "completion_tokens": 8000}
    assert ex.is_truncated(env)


@pytest.mark.parametrize("key", ["reasoning", "reasoning_content"])
def test_alternate_reasoning_field_names(key):
    env = _client("openai-compatible")._envelope(
        {"choices": [{"finish_reason": "stop",
                      "message": {"content": "{}", key: "thinking"}}]})
    assert env["reasoning"] == "thinking"
    assert not ex.is_truncated(env)


def test_anthropic_style_envelope_maps_stop_reason_and_thinking():
    env = _client("anthropic")._envelope({
        "content": [{"type": "thinking", "thinking": "deliberating"},
                    {"type": "text", "text": '{"atoms": []}'}],
        "stop_reason": "max_tokens",
        "usage": {"input_tokens": 100, "output_tokens": 200}})
    assert env["text"] == '{"atoms": []}'
    assert env["reasoning"] == "deliberating"
    assert ex.is_truncated(env)
    assert env["usage"]["completion_tokens"] == 200


def test_envelope_survives_a_malformed_provider_payload():
    for junk in [None, [], "text", {}, {"choices": []}]:
        env = _client("openai-compatible")._envelope(junk)
        assert set(env) == {"text", "finish_reason", "reasoning", "usage", "raw"}


def test_instrumented_client_refuses_to_construct_without_a_key():
    import providers
    cfg = providers.ProviderConfig(name="nope", kind="openai-compatible",
                                   model="m", base_url="http://x",
                                   api_key_env="DEFINITELY_NOT_SET_XYZ")
    with pytest.raises(RuntimeError):
        ex.InstrumentedClient(cfg)


def test_max_tokens_override_reaches_the_request_body(monkeypatch):
    import providers
    cfg = providers.ProviderConfig(name="t", kind="openai-compatible",
                                   model="m", base_url="http://x",
                                   max_tokens=8000)
    monkeypatch.setattr(providers.ProviderConfig, "key", lambda self: "k")
    c = ex.InstrumentedClient(cfg, max_tokens=16384)
    body = json.loads(c._request("sys", "usr").data)
    assert body["max_tokens"] == 16384


# --------------------------------------------------------------------------
# 13. output batching — input is never split, output is

class ScriptedClient:
    """Answers whatever batch it is shown, by reading the ids out of the
    prompt. Deterministic, so the same provisions produce the same atoms
    however they are grouped. `shared_ctx` appears in every batch's answer to
    exercise cross-batch merging."""

    def __init__(self, rows):
        self.by_id = {r["id"]: r for r in rows}
        self.prompts = []
        self.systems = []
        self.known_seen = []

    def complete(self, system, user):
        self.prompts.append(user)
        self.systems.append(system)
        block = user.split("PROVISIONS TO ENCODE", 1)[1]
        ids = [i for i in re.findall(r"^(fa_[a-z0-9_]+) \|", block, re.MULTILINE)]
        known = re.findall(r"^- ([a-z][a-z0-9_]*) \[", user, re.MULTILINE)
        self.known_seen.append(known)
        atoms = [{"name": "shared_ctx", "kind": "context", "dimension": "situation",
                  "gloss": "a condition every batch needs", "quote_spans": [],
                  "status": "draft"}]
        rules = []
        for i in ids:
            row = self.by_id[i]
            act = "act_" + i
            atoms.append({"name": act, "kind": "act", "dimension": "act",
                          "gloss": f"act for {i}",
                          "quote_spans": [{"focus_id": i, "span_id": "s1"}],
                          "status": "draft"})
            rules.append({"id": i, "modality": "oblige", "act": act,
                          "conditions": ["shared_ctx"], "defeaters": [],
                          "tier": 1, "locator": "", "quote": "",
                          "status": "draft"})
        return json.dumps({"atoms": atoms, "rules": rules, "incompat": [],
                           "exclusions": [], "unencoded": []})


def test_batching_yields_the_same_atoms_and_rules_as_one_pass(tmp_path, rows):
    """The headline invariant: batching changes how many requests are made,
    not what is extracted."""
    one, _, _ = ex.run_once(ScriptedClient(rows), rows, model="m", seed=0,
                            out_dir=str(tmp_path / "a"), batch_size=0)
    three, _, _ = ex.run_once(ScriptedClient(rows), rows, model="m", seed=0,
                              out_dir=str(tmp_path / "b"), batch_size=14)
    assert one["n_batches"] == 1 and three["n_batches"] == 3
    assert {a["name"] for a in one["atoms"]} == {a["name"] for a in three["atoms"]}
    assert {r["id"] for r in one["rules"]} == {r["id"] for r in three["rules"]}
    assert one["stats"]["coverage"] == three["stats"]["coverage"] == 1.0
    assert {u["focus_id"] for u in one["unencoded"]} == \
           {u["focus_id"] for u in three["unencoded"]}


def test_batching_merges_the_shared_atom_instead_of_forking_it(tmp_path, rows):
    art, _, _ = ex.run_once(ScriptedClient(rows), rows, model="m", seed=0,
                            out_dir=str(tmp_path), batch_size=14)
    names = [a["name"] for a in art["atoms"]]
    assert names.count("shared_ctx") == 1, "cross-batch duplicate not merged"
    assert art["stats"]["atoms_merged_across_batches"] == 2   # batches 2 and 3


def test_each_batch_is_shown_the_atoms_its_predecessors_defined(tmp_path, rows):
    client = ScriptedClient(rows)
    ex.run_once(client, rows, model="m", seed=0, out_dir=str(tmp_path),
                batch_size=14)
    assert client.known_seen[0] == [], "first batch has no predecessors"
    assert "shared_ctx" in client.known_seen[1]
    assert len(client.known_seen[2]) > len(client.known_seen[1])
    # and the reuse instruction travels with them
    assert "ATOMS ALREADY DEFINED" in client.prompts[1]
    assert "Reuse one whenever" in client.prompts[1]
    assert "REUSE an existing atom" in client.systems[1]


def test_every_batch_carries_the_whole_section_but_only_its_own_provisions(
        tmp_path, rows):
    client = ScriptedClient(rows)
    ex.run_once(client, rows, model="m", seed=0, out_dir=str(tmp_path),
                batch_size=14)
    prov = ex.encodable(rows)
    groups = ex.batches(prov, 14)
    for user, group in zip(client.prompts, groups):
        for r in rows:                        # input is never sliced
            assert r["quote"] in user
        block = user.split("PROVISIONS TO ENCODE", 1)[1]
        listed = set(re.findall(r"^(fa_[a-z0-9_]+) \|", block, re.MULTILINE))
        assert listed == {r["id"] for r in group}


def test_axioms_are_requested_only_on_the_final_batch(tmp_path, rows):
    client = ScriptedClient(rows)
    ex.run_once(client, rows, model="m", seed=0, out_dir=str(tmp_path),
                batch_size=14)
    assert ex.AXIOM_DEFER in client.prompts[0]
    assert ex.AXIOM_DEFER in client.prompts[1]
    assert ex.AXIOM_ASK in client.prompts[2]
    assert ex.AXIOM_ASK not in client.prompts[0]


def test_axioms_from_the_final_batch_see_the_whole_atom_set(tmp_path, fake_rows):
    """An incompat naming an act defined in batch 1 must survive when it is
    emitted in the last batch."""
    class LateAxiom:
        def __init__(self):
            self.n = 0

        def complete(self, system, user):
            self.n += 1
            if self.n < 3:
                return good_response(unencoded=[])
            return good_response(unencoded=[], incompat=[
                {"acts": ["follow_instruction", "obey_untrusted_content"],
                 "license": "logical", "source": "contradictory"}])

    art, _, _ = ex.run_once(LateAxiom(), fake_rows, model="m", seed=0,
                            out_dir=str(tmp_path), batch_size=1)
    assert len(art["incompat"]) == 1


def test_cross_batch_context_atom_used_as_an_act_is_rejected(tmp_path, fake_rows):
    """The fa_ag8e failure mode: batch 1 declares a context atom, a later batch
    names it as a rule's act. The rule is discarded and the provision lands in
    unencoded with the reason, so coverage stays honest."""
    class Confused:
        def __init__(self):
            self.n = 0

        def complete(self, system, user):
            self.n += 1
            if self.n == 1:
                return good_response(unencoded=[])
            # op_instruction_present is a CONTEXT atom from batch 1
            return json.dumps({"atoms": [], "unencoded": [], "incompat": [],
                               "exclusions": [],
                               "rules": [{"id": "fa_8ep2", "modality": "oblige",
                                          "act": "op_instruction_present",
                                          "conditions": [], "defeaters": [],
                                          "tier": 1, "locator": "", "quote": "",
                                          "status": "draft"}]})

    art, _, fail = ex.run_once(Confused(), fake_rows, model="m", seed=0,
                               out_dir=str(tmp_path), batch_size=1)
    assert "fa_8ep2" not in {r["id"] for r in art["rules"]}
    assert art["stats"]["rules_miskinded_act"] == 1
    rec = [r for r in fail.records
           if "not an act" in r["error"]][0]
    assert rec["detail"]["actual_kind"] == "context"      # the atom's real kind
    assert rec["detail"]["act"] == "op_instruction_present"
    u = {x["focus_id"]: x["reason"] for x in art["unencoded"]}
    assert "fa_8ep2" in u and "context atom" in u["fa_8ep2"]


def test_a_correct_act_atom_is_untouched(fake_rows):
    fail = FailureLog(None)
    art = ex.build_extraction(good_response(), fake_rows, "m", "r1", fail)
    assert art["stats"]["rules_miskinded_act"] == 0
    assert len(art["rules"]) == 2


def test_carried_atoms_are_listed_split_by_kind_with_the_act_rule(tmp_path, rows):
    client = ScriptedClient(rows)
    ex.run_once(client, rows, model="m", seed=0, out_dir=str(tmp_path),
                batch_size=14)
    u = client.prompts[1]
    assert "CONTEXT atoms" in u and "ACT atoms" in u
    assert 'A rule\'s "act" must name an ACT atom' in u
    ctx_block = u.split("CONTEXT atoms", 1)[1].split("ACT atoms", 1)[0]
    act_block = u.split("ACT atoms", 1)[1].split("A rule", 1)[0]
    assert "shared_ctx" in ctx_block and "shared_ctx" not in act_block
    assert "act_fa_" in act_block


def test_batches_partitions_provisions_exactly():
    items = list(range(42))
    for size in (1, 5, 14, 41, 42, 100, 0, None):
        gs = ex.batches(items, size)
        assert [x for g in gs for x in g] == items
        assert all(gs)
    assert len(ex.batches(items, 14)) == 3
    assert len(ex.batches(items, 42)) == 1
    assert ex.DEFAULT_BATCH_SIZE == 14


def test_default_batch_size_is_three_requests_for_this_section(rows):
    groups = ex.batches(ex.encodable(rows), ex.DEFAULT_BATCH_SIZE)
    assert [len(g) for g in groups] == [14, 14, 14]


def test_out_of_batch_rules_are_flagged_but_kept(fake_rows):
    fail = FailureLog(None)
    part = ex.extract_batch(good_response(), fake_rows, fail,
                            batch_rows=[fake_rows[2]], batch_no=1)
    assert {r.id for r in part["rules"]} == {"fa_aaa1", "fa_ccc3"}
    assert part["stats"]["rules_out_of_batch"] == 1
    assert any("outside this batch" in r["error"] for r in fail.records)


# --------------------------------------------------------------------------
# 11. run plumbing

def test_two_runs_get_distinct_run_ids_and_distinct_artifacts(tmp_path, fake_rows):
    arts = [ex.run_once(FakeClient(good_response()), fake_rows,
                        model=f"model-{i}", seed=i, out_dir=str(tmp_path))
            for i in range(2)]
    ids = {a[0]["run_id"] for a in arts}
    assert len(ids) == 2
    paths = {a[1] for a in arts}
    assert len(paths) == 2
    for a, p, _ in arts:
        assert os.path.basename(p) == f"extraction_{a['model']}_{a['run_id']}.json"


def test_run_id_is_deterministic_given_model_seed_and_prompt():
    a = ex.make_run_id("m", 0, "prompt")
    b = ex.make_run_id("m", 0, "prompt")
    assert a == b and a != ex.make_run_id("m", 1, "prompt")


def test_main_print_prompt_touches_no_provider(capsys, monkeypatch):
    import providers
    monkeypatch.setattr(providers, "make_client",
                        lambda *a, **k: pytest.fail("client constructed"))
    assert ex.main(["--print-prompt", "--section", ex.SECTION_TITLE]) == 0
    out = capsys.readouterr().out
    assert "### SYSTEM" in out and "### USER" in out
    assert "62 focus areas, 42 conditional, 13924 chars" in out
