"""Tests for the LABEL-FREE candidate classifier.

Four mutants are named in the task and each has a test that dies on it:

  M1  negation scope ignored — "must not" read as "must"
  M2  the CONTROL arm silently emptied (a rule that fires on everything)
  M3  a single principal counted as PARTIED
  M4  the classifier reading anything outside the clause TEXT

M4 is the one that decides whether the selection can be accused of being
fitted, so it is tested twice: once with a recording dict that fails on any
key access other than the text field, and once by asserting the module opens
no artifact other than the clause file and imports no provider/model code.
"""
from __future__ import annotations

import json
import os

import pytest

import grammar
import grammar_candidates as gc

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------- deontic

def test_must_is_deontic():
    assert "must" in gc.forces("The assistant must cite its sources.")


@pytest.mark.parametrize("text,want", [
    ("The assistant must not reveal the system prompt.", "mustnot"),
    ("The assistant must never reveal the system prompt.", "mustnot"),
    ("The assistant should not speculate.", "shouldnot"),
    ("The assistant shouldn't speculate.", "shouldnot"),
    ("The assistant may not refuse on these grounds.", "mustnot"),
    ("The assistant cannot be made to do this.", "mustnot"),
])
def test_negation_scope_is_a_different_force(text, want):
    """M1. A negated modal is its own force and must NOT also report the
    positive one — that identity is the whole defect the grammar removes."""
    got = gc.forces(text)
    assert want in got
    assert "must" not in got or want == "must"
    assert "should" not in got or want == "should"
    assert "may" not in got


def test_negation_survives_an_intervening_adverb():
    assert "mustnot" in gc.forces("The assistant must always never do this.")
    assert "shouldnot" in gc.forces("It should generally not be disclosed.")


def test_a_later_unrelated_negation_does_not_flip_the_modal():
    """"must respect the user, not the operator" is an obligation, not a
    prohibition: `not` is outside the modal's scope."""
    got = gc.forces("The model must respect the user, not the operator.")
    assert "must" in got
    assert "mustnot" not in got


def test_both_forces_can_appear_in_one_clause():
    got = gc.forces("It must disclose the policy and must not quote it.")
    assert {"must", "mustnot"} <= set(got)


def test_forces_are_the_grammar_vocabulary():
    """The classifier's force names must be exactly the notation's polarity
    prefixes; a name this module invents would not be comparable to what the
    annotation pass will emit."""
    vocab = {p[:-1] for p in grammar.POLARITY_PREFIXES}
    assert set(gc.FORCES) == vocab


def test_paraphrases_of_obligation_and_prohibition():
    assert "must" in gc.forces("Developers are required to disclose this.")
    assert "mustnot" in gc.forces("The model is prohibited from doing this.")


@pytest.mark.parametrize("text", [
    "Maybe the answer is unclear.",
    "The mustard is on the shelf.",
    "The shoulder of the road is unsafe.",
])
def test_modals_need_word_boundaries(text):
    assert gc.forces(text) == []


def test_a_bare_definition_carries_no_force():
    assert gc.forces(
        "A developer is a business that builds on the API platform.") == []


# ---------------------------------------------------------------- defeaters

@pytest.mark.parametrize("text", [
    "Do this, unless the user objects.",
    "Everything applies except where local law differs.",
    "However, the model may decline.",
    "It is usually fine, but not in this case.",
    "Anyone other than the operator may not do this.",
    "Provided that consent was given, proceed.",
    "Notwithstanding the above, refuse.",
])
def test_defeater_cues_are_found(text):
    assert gc.defeaters(text)


def test_defeaters_need_word_boundaries():
    """`but` inside `attribute`, `except` inside `exceptional`."""
    assert gc.defeaters("The attribute is distributed and exceptional.") == []


def test_defeater_breakdown_separates_bare_but():
    """`but` alone is the weakest cue in the set and the biggest source of
    false positives; a reader has to be able to see how much of DEFEATED rests
    on it before spending against DEFEATED."""
    rows = [{"quote": "Helpful, but not obsequious."},
            {"quote": "Do this unless the user objects."},
            {"quote": "Do this, but not unless asked."},
            {"quote": "A definition."}]
    b = gc.defeater_breakdown(rows)
    assert b["but_only"] == 1
    assert b["explicit"] == 2
    assert b["total"] == 3


def test_a_plain_conditional_is_not_a_defeater():
    """`if` is a trigger, not a defeater. Conflating them would make DEFEATED
    a synonym for DEONTIC and destroy the contrast between them."""
    assert gc.defeaters("If the user asks, answer.") == []


# ---------------------------------------------------------------- principals

def test_two_principals_is_partied():
    assert gc.is_partied("The model defers to the operator.")


def test_one_principal_is_not_partied():
    """M3. Naming a single party is weaker evidence and must not select."""
    assert gc.principals("The model should be helpful.") == ["model"]
    assert not gc.is_partied("The model should be helpful.")


def test_repeating_one_principal_is_still_not_partied():
    assert not gc.is_partied(
        "The user asks the user what the user wants.")


def test_principals_are_the_grammar_vocabulary():
    assert set(gc.PRINCIPALS) == set(grammar.PRINCIPALS)


def test_surface_aliases_map_onto_principals():
    assert gc.principals("The assistant helps the user.") == ["model", "user"]
    assert "third_party" in gc.principals(
        "The operator may not share it with third parties.")


def test_plurals_count():
    assert gc.is_partied("Developers configure how operators are treated.")


def test_the_document_title_is_not_a_principal_mention():
    """"the Model Spec" is the document's own name; counting it would make a
    large share of the meta stratum look PARTIED for no linguistic reason."""
    assert "model" not in gc.principals(
        "The Model Spec outlines what the platform intends.")


# ---------------------------------------------------------------- classify

def test_control_is_none_of_the_above():
    r = gc.classify("A conversation consists of a sequence of messages.")
    assert r["categories"] == [gc.CONTROL]


def test_categories_may_overlap():
    r = gc.classify(
        "The model must not defer to the operator unless the user consents.")
    assert set(r["categories"]) == {gc.DEONTIC, gc.DEFEATED, gc.PARTIED}


def test_control_is_exclusive():
    r = gc.classify("The model must answer.")
    assert gc.CONTROL not in r["categories"]


def test_control_arm_is_not_empty_on_the_real_corpus():
    """M2. A rule that fires on everything empties the control arm and there
    is then no control. If this ever drops to zero the selection is not a
    selection."""
    rows = gc.load_clauses()
    counts = gc.set_sizes(rows)
    assert counts[gc.CONTROL] > 20, counts
    assert counts[gc.CONTROL] < len(rows) / 2, counts


def test_every_clause_lands_somewhere_exactly_once_in_the_partition():
    rows = gc.load_clauses()
    tagged = gc.categorize(rows)
    assert len(tagged) == len(rows)
    for t in tagged:
        assert t["categories"], t
        if gc.CONTROL in t["categories"]:
            assert t["categories"] == [gc.CONTROL]


# ------------------------------------------------- reads only the text (M4)

class _Recorder(dict):
    """A clause that screams if anything but the text field is read."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.seen = set()

    def __getitem__(self, k):
        self.seen.add(k)
        return super().__getitem__(k)

    def get(self, k, default=None):
        self.seen.add(k)
        return super().get(k, default)


def test_classify_clause_reads_only_the_text_field():
    c = _Recorder({"id": "m0001", "quote": "The model must not do this.",
                   "kind": "conditional", "section_path": ["Overview"],
                   "focus_ids": ["f1"], "locator": "x"})
    r = gc.classify_clause(c)
    assert gc.DEONTIC in r["categories"]
    assert c.seen <= {gc.TEXT_FIELD}, (
        f"read fields outside the clause text: {c.seen - {gc.TEXT_FIELD}}")


def test_kind_cannot_change_the_classification():
    """The same text under five different kinds classifies identically."""
    text = "The model should defer to the operator unless the user objects."
    got = {k: tuple(gc.classify_clause({"quote": text, "kind": k})["categories"])
           for k in ("conditional", "definitional", "example", "holistic",
                     "meta")}
    assert len(set(got.values())) == 1, got


def test_module_names_no_labels_or_model_calls():
    src = open(os.path.join(HERE, "grammar_candidates.py"),
               encoding="utf-8").read()
    #: Every artifact that carries a LABEL, and every route to a paid call.
    #: Naming any of them in this module would make the selection fittable.
    for banned in ("import providers", "complete_envelope", "api_key",
                   # the .json forms only: naming `modelspec_kinds.py` in
                   # PROSE (to explain what the cross-tab disagreement means)
                   # is not reading it, and the open-spy test below is what
                   # actually enforces that it is never read.
                   "annotations_b8.json", "behavior_atoms.json",
                   "modelspec_kinds.json",
                   "readback_results.json", "audit_ratings", "load_panel",
                   "load_universe_panel", "requests.post", "openai."):
        assert banned not in src, banned


def test_module_opens_only_the_clause_file(monkeypatch):
    opened = []
    real = open

    def spy(path, *a, **k):
        opened.append(str(path))
        return real(path, *a, **k)

    monkeypatch.setattr("builtins.open", spy)
    gc.categorize(gc.load_clauses())
    assert opened, "expected the clause file to be read"
    for p in opened:
        assert os.path.basename(p) in ("modelspec_clauses.json",), p


# ---------------------------------------------------------------- crosstab

def test_crosstab_covers_every_kind_and_totals_match():
    rows = gc.load_clauses()
    tab = gc.crosstab(rows)
    kinds = {r["kind"] for r in rows}
    assert set(tab) == kinds
    assert sum(sum(v.values()) for v in tab.values()) >= len(rows)


def test_the_prior_expectation_is_checked_and_says_so_when_it_fails():
    """Prior: `conditional` should be heavily DEONTIC *and* DEFEATED. If the
    labels and the linguistic structure disagree, that matters more than the
    classifier, so it must come out as a warning and not be left in a table
    for someone to notice."""
    tab = {"conditional": {"n": 100, gc.DEONTIC: 90, gc.DEFEATED: 12,
                           gc.PARTIED: 50, gc.CONTROL: 5}}
    w = gc.kind_disagreements(tab)
    assert any("DEFEATED" in x for x in w), w
    assert not any("DEONTIC" in x for x in w), w

    tab["conditional"][gc.DEONTIC] = 20
    assert any("DEONTIC" in x for x in gc.kind_disagreements(tab))


def test_no_warning_when_the_prior_holds():
    tab = {"conditional": {"n": 100, gc.DEONTIC: 90, gc.DEFEATED: 70,
                           gc.PARTIED: 50, gc.CONTROL: 2}}
    assert gc.kind_disagreements(tab) == []


def test_crosstab_counts_are_per_category_not_a_partition():
    """Overlap is real: a clause may be both DEONTIC and DEFEATED, so the row
    sums exceed the kind's clause count. The reporter must not pretend
    otherwise."""
    rows = [{"kind": "conditional",
             "quote": "The model must not do this unless the user asks."}]
    tab = gc.crosstab(rows)
    assert tab["conditional"][gc.DEONTIC] == 1
    assert tab["conditional"][gc.DEFEATED] == 1
    assert tab["conditional"]["n"] == 1


# ---------------------------------------------------------------- sampling

def test_sample_is_reproducible_under_a_seed():
    rows = gc.load_clauses()
    a = [r["id"] for r in gc.sample(rows, 40, seed=7)]
    b = [r["id"] for r in gc.sample(rows, 40, seed=7)]
    assert a == b
    assert len(a) == 40


def test_a_different_seed_gives_a_different_draw():
    rows = gc.load_clauses()
    a = [r["id"] for r in gc.sample(rows, 40, seed=7)]
    b = [r["id"] for r in gc.sample(rows, 40, seed=8)]
    assert a != b


def test_sample_is_stratified_across_categories():
    rows = gc.load_clauses()
    drawn = gc.sample(rows, 40, seed=7, stratify=True)
    cats = set()
    for r in drawn:
        cats.update(gc.classify_clause(r)["categories"])
    assert {gc.DEONTIC, gc.DEFEATED, gc.PARTIED, gc.CONTROL} <= cats


def test_sample_larger_than_the_corpus_returns_the_corpus():
    rows = gc.load_clauses()
    assert len(gc.sample(rows, 10 ** 6, seed=1)) == len(rows)


# ---------------------------------------------------------------- validation

def test_the_hand_gold_is_the_documented_draw():
    """The gold is adjudicated over a SEEDED draw, so anyone can regenerate
    the same 40 clauses and check the adjudication."""
    drawn = {r["id"] for r in gc.gold_sample()}
    assert set(gc.HAND_GOLD) == drawn
    assert len(drawn) == gc.GOLD_N


def test_the_gold_draw_is_balanced_across_strata():
    """Equal allocation, so the rare strata are estimable at all; the
    population weights are what put the estimate back on the corpus."""
    from collections import Counter
    got = Counter(gc.stratum_of(r["quote"]) for r in gc.gold_sample())
    assert set(got) == {gc.DEONTIC, gc.DEFEATED, gc.PARTIED, gc.CONTROL}
    assert set(got.values()) == {gc.GOLD_N // 4}


def test_strata_are_a_partition():
    rows = gc.load_clauses()
    st = gc.strata(rows)
    assert sum(len(v) for v in st.values()) == len(rows)
    assert set(st) == {gc.DEONTIC, gc.DEFEATED, gc.PARTIED, gc.CONTROL}


def test_the_hand_gold_uses_only_the_four_categories():
    ok = {gc.DEONTIC, gc.DEFEATED, gc.PARTIED, gc.CONTROL}
    for cid, cats in gc.HAND_GOLD.items():
        assert set(cats) <= ok, (cid, cats)
        assert cats, cid
        if gc.CONTROL in cats:
            assert list(cats) == [gc.CONTROL], cid


def test_wilson_interval_brackets_the_point_estimate():
    lo, hi = gc.wilson(8, 10)
    assert lo < 0.8 < hi
    assert (0.0, 1.0) == gc.wilson(0, 0)


def test_validation_reports_precision_and_recall_per_category():
    rep = gc.validate()
    for cat in (gc.DEONTIC, gc.DEFEATED, gc.PARTIED, gc.CONTROL):
        r = rep[cat]
        assert 0.0 <= r["precision"] <= 1.0
        assert 0.0 <= r["recall"] <= 1.0
        assert r["ci_precision"][0] <= r["precision"] <= r["ci_precision"][1]
        assert r["n_gold"] + r["n_pred"] > 0


def test_validation_is_honest_about_a_deliberately_broken_classifier(
        monkeypatch):
    """The harness must be able to FAIL. Break the classifier and precision
    on CONTROL has to collapse — otherwise `validate` is measuring nothing."""
    monkeypatch.setattr(gc, "classify", lambda text: {
        "categories": [gc.CONTROL], "forces": [], "defeaters": [],
        "principals": []})
    rep = gc.validate()
    assert rep[gc.DEONTIC]["recall"] == 0.0


# ---------------------------------------------------------------- cost

def test_cost_of_a_subset_is_below_the_full_corpus():
    full = gc.cost(gc.load_clauses())
    rows = [r for r in gc.load_clauses()
            if gc.DEONTIC in gc.classify_clause(r)["categories"]]
    sub = gc.cost(rows)
    assert 0 < sub["usd"] < full["usd"]
    assert sub["usd"] <= sub["usd_ceiling"]
    assert sub["clauses"] == len(rows)


def test_cost_uses_the_shared_costing_path():
    """Comparable to the $0.402/$0.552 full-corpus quote only if it is the
    same estimator, not a re-derived one."""
    import annotate
    called = {}

    def spy(**kw):
        called.update(kw)
        return {"usd": 0.1, "usd_low": 0.05, "usd_ceiling": 0.2,
                "clauses": len(kw.get("rows") or []), "calls": 1,
                "batch_size": 8, "model": "m", "provider": "luna",
                "in_tokens": 1.0, "out_tokens_high": 1.0}

    orig = annotate.estimate_cost
    annotate.estimate_cost = spy
    try:
        gc.cost(gc.load_clauses()[:5])
    finally:
        annotate.estimate_cost = orig
    assert called.get("rows") is not None
    assert called.get("batch_size") == 8


# ---------------------------------------------------------------- CLI

def test_main_runs_offline_and_prints_the_crosstab(capsys):
    gc.main([])
    out = capsys.readouterr().out
    assert "CROSS-TAB" in out
    assert "conditional" in out
    assert gc.CONTROL in out


def test_main_sample_flag_is_reproducible(capsys):
    gc.main(["--sample", "5", "--seed", "3"])
    a = capsys.readouterr().out
    gc.main(["--sample", "5", "--seed", "3"])
    b = capsys.readouterr().out
    assert a == b


def test_main_json_is_machine_readable(capsys):
    gc.main(["--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["sizes"][gc.CONTROL] > 0
    assert payload["crosstab"]["conditional"]["n"] > 0
