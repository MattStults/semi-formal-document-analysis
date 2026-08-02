"""Tests for the shared core: dsl + checker + sweep classification.

Run: .venv/bin/python -m pytest test_core.py -q
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dsl import Vocabulary, DerivedPredicate, Rule
from checker import check_definition, check_rule
from sweep import classify

HERE = os.path.dirname(os.path.abspath(__file__))


def vocab():
    return Vocabulary.load(os.path.join(HERE, "vocabulary_pilot.json"))


def test_vocabulary_loads_and_validates():
    v = vocab()
    assert v.validate() == []
    assert len(v.atoms) == 25
    licenses = [ax.license for ax in v.axioms]
    assert "assumed" in licenses  # the flagged one must not be laundered


def test_expressible_definition_passes_with_witness():
    v = vocab()
    d = DerivedPredicate(
        name="sycophancy-situation",
        expr={"all": ["user_prefers_p", "bel_false"]},
        concept_map={"user stated a preferred answer": "user_prefers_p",
                     "model believes it false": "bel_false"})
    verdict = check_definition(d, v)
    assert verdict.ok
    assert verdict.witness  # a satisfying world exists and is reported


def test_unmapped_concept_fires_existence_signal():
    v = vocab()
    d = DerivedPredicate(
        name="harm-to-third-parties",
        expr={"all": []},
        concept_map={"third party outside conversation": None})
    verdict = check_definition(d, v)
    assert not verdict.ok
    assert verdict.stage == "existence"
    assert any("unmapped concept" in e for e in verdict.errors)


def test_unknown_atom_fires_existence_signal():
    v = vocab()
    d = DerivedPredicate(name="x", expr="nonexistent_atom",
                         concept_map={"c": "nonexistent_atom"})
    verdict = check_definition(d, v)
    assert not verdict.ok and verdict.stage == "existence"


def test_axiom_contradiction_is_vacuous():
    v = vocab()
    d = DerivedPredicate(
        name="impossible",
        expr={"all": ["bel_true", "bel_false"]},   # at_most_one violated
        concept_map={"a": "bel_true", "b": "bel_false"})
    verdict = check_definition(d, v)
    assert not verdict.ok
    assert verdict.stage == "coherence"


def test_requires_axiom_constrains_witness():
    v = vocab()
    d = DerivedPredicate(name="endorsed-reliance", expr="reliance_endorsed",
                         concept_map={"c": "reliance_endorsed"})
    verdict = check_definition(d, v)
    assert verdict.ok
    # requires(reliance_endorsed, user_wants_reliance): witness must include both
    assert "ctx(user_wants_reliance)" in verdict.witness


def test_rule_check_catches_dead_defeater():
    v = vocab()
    r = Rule(id="dead", modality="forbid", act="tell_limits",
             conditions=["op_restricts_limit_info"],
             defeaters=[{"conditions": ["op_restricts_limit_info"]}],
             locator="test", quote="test quote")
    verdict = check_rule(r, v)
    assert verdict.ok  # structurally valid...
    assert verdict.warnings  # ...but flagged as the finding-9 pattern


def test_rule_check_catches_type_error():
    v = vocab()
    r = Rule(id="typo", modality="oblige", act="user_prefers_p",  # context as act
             conditions=["assert_p"],                              # act as context
             locator="test", quote="q")
    verdict = check_rule(r, v)
    assert not verdict.ok
    assert len(verdict.errors) >= 2


def test_classify_matches_pilot_triage():
    v = vocab()
    full = DerivedPredicate(name="f", expr="user_prefers_p",
                            concept_map={"a": "user_prefers_p"})
    partial = DerivedPredicate(name="p", expr="hedge_p",
                               concept_map={"a": "hedge_p", "b": None})
    none = DerivedPredicate(name="n", expr={"all": []},
                            concept_map={"a": None, "b": None})
    assert classify(full, check_definition(full, v)) == "EXPRESSIBLE"
    assert classify(partial, check_definition(partial, v)) == "PARTIAL"
    assert classify(none, check_definition(none, v)) == "INEXPRESSIBLE"


def test_dry_run_client_never_calls_network():
    from providers import ProviderConfig, make_client
    p = ProviderConfig(name="test", kind="openai-compatible", model="m",
                       api_key_env="NO_SUCH_KEY_SET", base_url="https://x")
    c = make_client(p, live=False, log_dir=os.path.join(HERE, "prompt_log"))
    assert c.complete("sys", "usr") is None  # records, returns None


def test_live_client_refuses_without_key():
    from providers import ProviderConfig, LiveClient
    p = ProviderConfig(name="test", kind="openai-compatible", model="m",
                       api_key_env="NO_SUCH_KEY_SET", base_url="https://x")
    try:
        LiveClient(p)
        assert False, "should have raised"
    except RuntimeError as e:
        assert "refusing" in str(e)


def test_negation_only_definition_warns_empty_world():
    """Regression: a definition satisfied by the empty world passes the
    satisfiability check but selects no scenario — observed live when a small
    model defined a behavior as NOT(bad things)."""
    v = vocab()
    d = DerivedPredicate(
        name="negation-only",
        expr={"not": {"any": ["hedge_p", "comply_restrict"]}},
        concept_map={"a": "hedge_p", "b": "comply_restrict"})
    verdict = check_definition(d, v)
    assert verdict.ok
    assert verdict.warnings and "empty world" in verdict.warnings[0]
