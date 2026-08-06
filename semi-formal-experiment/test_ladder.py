"""Tests for the attribution ladder harness.

The ladder is a measurement, so the things that have to be guarded here are
the ways a measurement lies rather than the ways code crashes. Each group
below corresponds to a failure this project has already had:

  RATE CAP      a rung that reaches sufficiency by writing more, or longer,
                atoms has measured its own budget and not its grammar. The
                withdrawn refinement design priced atom NAMES and not glosses
                and died of it; rung 4 can invent fields, so the price has to
                cover invented text too.
  REUSE PROFILE a sufficiency gain with a rising hapax share is memorisation.
                It is only visible if the table prints it, so the table must.
  COVERAGE      `readback.summarize` reported `unanswered: 0` while a
                condition sat at 90/125, because a lost batch never reaches
                `results` and the denominator is taken from `results`. The
                ladder counts against the DECLARED sample or refuses to print.
  NULL ARM      `render([], kind)` still emits a kind label and boilerplate.
                Without an empty-render control a rung can bank a
                target-independent constant.
  DEMONSTRATIONS a demonstration lifted from either spec is a hand-curated
                annotation of an evaluation passage, chosen by someone who has
                seen the panel. That is a leak channel and a blocking defect.
  NO SPEND      nothing in this file may construct a live client.
"""
from __future__ import annotations

import json
import os

import pytest

import ladder as L
import readback as rb

HERE = os.path.dirname(os.path.abspath(__file__))
ANN = os.path.join(HERE, "annotations_b8.json")
CLAUSES = os.path.join(HERE, "modelspec_clauses.json")

pytestmark = pytest.mark.skipif(
    not (os.path.exists(ANN) and os.path.exists(CLAUSES)),
    reason="real artifacts not present")


# --------------------------------------------------------------------------
# helpers — every model response in this file is scripted, never fetched

class ScriptedClient:
    """Returns canned text per call. Records every prompt it was given.

    `script` is a list of (text | Exception). An Exception is RAISED, which is
    how a 429 is simulated; the harness is expected to retry it.
    """

    def __init__(self, script=None, default=None):
        self.script = list(script or [])
        self.default = default
        self.calls = []

    def complete(self, system, user):
        self.calls.append((system, user))
        item = self.script.pop(0) if self.script else self.default
        if isinstance(item, Exception):
            raise item
        return item


def _atom(name, kind="situation", gloss="g", span_id="s1", **extra):
    return dict(name=name, kind=kind, gloss=gloss, span_id=span_id, **extra)


def _by_clause(ids, per=2, gloss="g"):
    return {cid: [_atom(f"a{i}", gloss=gloss) for i in range(per)]
            for cid in ids}


def _artifact(ids, rungs):
    return {"provenance": {"seed": L.SEED, "model": "gpt-5.6-luna",
                           "cap_atoms": L.CAP_ATOMS_PER_CLAUSE,
                           "cap_text_chars": L.CAP_TEXT_CHARS_PER_CLAUSE},
            "clause_ids": list(ids), "rungs": rungs}


def _rung_block(ids, faithful=True, sufficient=False, by_clause=None,
                annotated=None):
    bc = by_clause if by_clause is not None else _by_clause(ids)
    return {
        "by_clause": bc,
        "annotated": list(annotated if annotated is not None else ids),
        "fidelity": {cid: {"faithful": faithful, "sufficient": sufficient,
                           "unsupported": [], "missing": []} for cid in ids},
        "errors": [],
    }


# --------------------------------------------------------------------------
# 1. THE RUNGS ARE THE ONES IN THE PLAN

def test_the_rungs_are_exactly_the_plan_of_records_rungs():
    assert L.RUNGS == ("0", "1", "1.5", "2", "3", "4")
    assert L.NULL_ARM not in L.RUNGS


def test_every_rung_isolates_something_and_says_what():
    for r in L.RUNGS:
        spec = L.rung_spec(r)
        assert spec["isolates"]
        assert spec["relaxes"] is not None


def test_rung_1_is_closed_vocabulary_and_rung_2_is_not():
    assert L.rung_spec("1")["vocabulary"] == "closed"
    assert L.rung_spec("1.5")["vocabulary"] == "closed"
    assert L.rung_spec("2")["vocabulary"] == "open"
    assert L.rung_spec("3")["vocabulary"] == "open"


def test_only_rung_4_may_invent_structure():
    assert [r for r in L.RUNGS if L.rung_spec(r)["free_shape"]] == ["4"]


def test_conventions_are_required_from_rung_1_5_up_and_free_at_3():
    assert not L.rung_spec("1")["require_conventions"]
    assert L.rung_spec("1.5")["require_conventions"]
    assert L.rung_spec("2")["require_conventions"]
    assert not L.rung_spec("3")["require_conventions"]


# --------------------------------------------------------------------------
# 2. THE SAMPLE IS THE READ-BACK'S SAMPLE

def test_the_ladder_scores_the_read_backs_own_125_clauses():
    rows = rb.load_clauses()
    assert L.sample(rows) == rb.stratified_sample(rows, 25, L.SEED)
    assert len(L.sample(rows)) == 125


def test_the_seed_is_the_read_backs_seed():
    assert L.SEED == 20260802


# --------------------------------------------------------------------------
# 3. THE NAMING CONVENTION IS PARSEABLE AND DOES NOT COLLIDE

def test_polarity_prefixes_are_reserved_against_the_shipped_vocabulary():
    """A prefix that an existing atom already starts with is not reserved: the
    parser would read polarity off a name that never encoded any."""
    vocab = L.load_vocabulary()
    assert len(vocab) == 361
    clashes = [n for n in vocab
               if any(n.startswith(p) for p in L.POLARITY_PREFIXES)]
    assert clashes == []


def test_the_principal_separator_does_not_collide_either():
    vocab = L.load_vocabulary()
    assert [n for n in vocab if L.PRINCIPAL_SEP in n] == []


def test_parse_name_reads_polarity_and_ORDERED_principals():
    got = L.parse_name("mustnot_reassign_plot__operator_user_third_party")
    assert got["polarity"] == "mustnot"
    assert got["stem"] == "reassign_plot"
    assert got["principals"] == ["operator", "user", "third_party"]


def test_principal_order_is_content_and_is_not_normalised():
    a = L.parse_name("must_defer__model_operator")
    b = L.parse_name("must_defer__operator_model")
    assert a["principals"] != b["principals"]
    assert a != b


def test_a_bare_name_parses_as_no_polarity_and_no_principals():
    got = L.parse_name("plot_left_untended")
    assert got["polarity"] is None
    assert got["principals"] == []
    assert got["stem"] == "plot_left_untended"


def test_an_unknown_principal_word_is_a_parse_failure():
    got = L.parse_name("must_tell__gardener")
    assert got["error"]


# --------------------------------------------------------------------------
# 4. RUNG CONSTRAINTS ARE ENFORCED, NOT MERELY REQUESTED

def _row(cid="m0006"):
    rows = rb.load_clauses()
    return {r["id"]: r for r in rows}[cid]


def _resp(cid, atoms):
    return json.dumps({"clauses": [{"clause_id": cid, "atoms": atoms}]})


def test_rung_1_rejects_a_name_outside_the_closed_vocabulary():
    row = _row()
    vocab = L.load_vocabulary()
    known = sorted(vocab)[0]
    obj = json.loads(_resp(row["id"], [
        _atom(known, kind=vocab[known]["kind"]),
        _atom("brand_new_invented_atom", kind="situation")]))
    atoms, stats = L.verify_rung_atoms(obj, row, "1", vocab)
    assert [a["name"] for a in atoms] == [known]
    assert stats["rejections"]["off_vocabulary"] == 1


def test_rung_2_accepts_a_coined_name():
    row = _row()
    vocab = L.load_vocabulary()
    obj = json.loads(_resp(row["id"], [
        _atom("brand_new_invented_atom__user", kind="act")]))
    atoms, stats = L.verify_rung_atoms(obj, row, "2", vocab)
    assert [a["name"] for a in atoms] == ["brand_new_invented_atom__user"]


def test_rung_1_5_rejects_an_act_atom_with_no_principals():
    row = _row()
    vocab = L.load_vocabulary()
    act = sorted(n for n, v in vocab.items() if v["kind"] == "act")[0]
    obj = json.loads(_resp(row["id"], [_atom(act, kind="act")]))
    atoms, stats = L.verify_rung_atoms(obj, row, "1.5", vocab)
    assert atoms == []
    assert stats["rejections"]["missing_principals"] == 1


def test_rung_1_5_accepts_the_same_act_once_it_names_its_principals():
    row = _row()
    vocab = L.load_vocabulary()
    act = sorted(n for n, v in vocab.items() if v["kind"] == "act")[0]
    obj = json.loads(_resp(row["id"], [
        _atom(f"must_{act}__model_user", kind="act")]))
    atoms, stats = L.verify_rung_atoms(obj, row, "1.5", vocab)
    assert len(atoms) == 1
    assert atoms[0]["polarity"] == "must"
    assert atoms[0]["principals"] == ["model", "user"]


def test_rung_1_5_still_holds_the_stem_to_the_closed_vocabulary():
    row = _row()
    vocab = L.load_vocabulary()
    obj = json.loads(_resp(row["id"], [
        _atom("must_a_stem_nobody_coined__model_user", kind="act")]))
    atoms, stats = L.verify_rung_atoms(obj, row, "1.5", vocab)
    assert atoms == []
    assert stats["rejections"]["off_vocabulary"] == 1


def test_rungs_1_and_1_5_use_the_vocabularys_gloss_not_the_models():
    """Per-occurrence glosses are a rung-2 relaxation. If rung 1 could write
    its own gloss it would be measuring vocabulary and assignment at once."""
    row = _row()
    vocab = L.load_vocabulary()
    known = sorted(vocab)[0]
    obj = json.loads(_resp(row["id"], [
        _atom(known, kind=vocab[known]["kind"], gloss="a bespoke gloss")]))
    atoms, _ = L.verify_rung_atoms(obj, row, "1", vocab)
    assert atoms[0]["gloss"] == vocab[known]["gloss"]


def test_rung_3_imposes_no_convention_and_no_vocabulary():
    row = _row()
    obj = json.loads(_resp(row["id"], [
        _atom("anything_at_all", kind="act", gloss="free")]))
    atoms, _ = L.verify_rung_atoms(obj, row, "3", L.load_vocabulary())
    assert len(atoms) == 1


def test_rung_3_still_refuses_a_field_outside_the_schema():
    row = _row()
    obj = json.loads(_resp(row["id"], [
        _atom("anything_at_all", kind="act", deontic="required")]))
    atoms, stats = L.verify_rung_atoms(obj, row, "3", L.load_vocabulary())
    assert atoms == []
    assert stats["rejections"]["extra_field"] == 1


def test_rung_4_preserves_the_fields_the_annotator_invented():
    row = _row()
    obj = json.loads(_resp(row["id"], [
        _atom("announce_absence", kind="act", deontic="required",
              addressee="garden_steward")]))
    atoms, _ = L.verify_rung_atoms(obj, row, "4", L.load_vocabulary())
    assert atoms[0]["deontic"] == "required"
    assert atoms[0]["addressee"] == "garden_steward"


# --------------------------------------------------------------------------
# 5. THE RATE CAP

def test_the_shipped_budget_is_regenerable_from_the_annotation_artifact():
    """No hand-transcribed constants. The cap is what the shipped run spent."""
    m = L.measured_shipped_budget()
    assert abs(m["atoms_per_clause"] - L.CAP_ATOMS_PER_CLAUSE) < 0.01
    assert abs(m["text_chars_per_clause"] - L.CAP_TEXT_CHARS_PER_CLAUSE) < 5


def test_rate_cap_holds_the_mean_atoms_per_clause_at_the_shipped_budget():
    ids = [f"c{i}" for i in range(125)]
    bc = _by_clause(ids, per=5)
    capped, stats = L.enforce_rate_cap(bc, ids)
    prof = L.rate_profile(capped, ids)
    assert prof["atoms_per_clause"] <= L.CAP_ATOMS_PER_CLAUSE
    assert stats["atoms_dropped"] > 0


def test_rate_cap_enforces_the_per_clause_ceiling_too():
    ids = ["c0"]
    bc = {"c0": [_atom(f"a{i}") for i in range(9)]}
    capped, _ = L.enforce_rate_cap(bc, ids)
    assert len(capped["c0"]) <= L.PER_CLAUSE_ATOM_CEILING


def test_rate_cap_holds_the_mean_gloss_characters():
    ids = [f"c{i}" for i in range(125)]
    bc = _by_clause(ids, per=2, gloss="x" * 400)
    capped, stats = L.enforce_rate_cap(bc, ids)
    prof = L.rate_profile(capped, ids)
    assert prof["text_chars_per_clause"] <= L.CAP_TEXT_CHARS_PER_CLAUSE
    assert stats["gloss_chars_dropped"] > 0


def test_rate_cap_prices_invented_field_text_as_well_as_gloss():
    """The hole the withdrawn refinement design died of, one level up: at rung
    4 a relation written as prose in an invented field is free text and must
    be paid for, or the cap is decorative."""
    ids = [f"c{i}" for i in range(125)]
    bc = {cid: [_atom("a", gloss="short", condition="y" * 400)] for cid in ids}
    assert L.text_chars(bc["c0"][0]) > 400
    capped, _ = L.enforce_rate_cap(bc, ids)
    prof = L.rate_profile(capped, ids)
    assert prof["text_chars_per_clause"] <= L.CAP_TEXT_CHARS_PER_CLAUSE


def test_rate_cap_is_deterministic():
    ids = [f"c{i}" for i in range(125)]
    bc = _by_clause(ids, per=5, gloss="y" * 300)
    a, _ = L.enforce_rate_cap(bc, ids)
    b, _ = L.enforce_rate_cap(bc, ids)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_rate_cap_does_not_touch_a_run_already_inside_the_budget():
    ids = [f"c{i}" for i in range(125)]
    bc = _by_clause(ids, per=2, gloss="g")
    capped, stats = L.enforce_rate_cap(bc, ids)
    assert capped == bc
    assert stats["atoms_dropped"] == 0 and stats["gloss_chars_dropped"] == 0


def test_rung_0_is_the_budget_and_is_never_trimmed():
    """Rung 0 IS the shipped encoding budget; trimming it would move the
    baseline the other rungs are compared against."""
    ids = rb.stratified_sample(rb.load_clauses(), 25, L.SEED)
    bc = rb.load_annotations()
    before = L.rate_profile({i: bc.get(i, []) for i in ids}, ids)
    art = L.build_rung_0(ids, rb.load_clauses(), bc)
    after = L.rate_profile(art["by_clause"], ids)
    assert after == before


# --------------------------------------------------------------------------
# 6. THE REUSE PROFILE — memorisation has to be visible

def test_reuse_profile_reports_hapax_share_and_df_distribution():
    ids = [f"c{i}" for i in range(4)]
    bc = {"c0": [_atom("shared")], "c1": [_atom("shared")],
          "c2": [_atom("once")], "c3": [_atom("twice")]}
    p = L.reuse_profile(bc, ids)
    assert p["distinct_names"] == 3
    assert p["hapax"] == 2
    assert p["hapax_share"] == pytest.approx(2 / 3)
    assert p["df_distribution"]["1"] == 2
    assert p["df_distribution"]["2"] == 1


def test_the_table_reports_hapax_share_on_every_rung_row():
    ids = [f"c{i}" for i in range(3)]
    art = _artifact(ids, {r: _rung_block(ids) for r in L.RUNGS})
    art["rungs"][L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    txt = L.table(art)
    header = [l for l in txt.splitlines() if l.lstrip().startswith("rung ")]
    assert header and "hapax" in header[0], "no hapax COLUMN in the table"
    for r in L.RUNGS:
        line = [l for l in txt.splitlines() if l.strip().startswith(r + " ")]
        assert line, f"no row for rung {r}"


def test_the_hapax_number_printed_is_the_rungs_ACTUAL_hapax_share():
    """A column that prints a constant is not a report. Two rungs with known,
    different reuse profiles must print their own numbers."""
    ids = [f"c{i}" for i in range(4)]
    shared = {i: [_atom("shared")] for i in ids}          # hapax share 0.00
    bespoke = {i: [_atom(f"bespoke_{i}")] for i in ids}   # hapax share 1.00
    rungs = {r: _rung_block(ids, by_clause=shared) for r in L.RUNGS}
    rungs["3"] = _rung_block(ids, by_clause=bespoke)
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    txt = L.table(_artifact(ids, rungs))
    lines = txt.splitlines()
    header = next(l for l in lines if l.lstrip().startswith("rung "))
    end = header.index("hapax") + len("hapax")

    def hapax_cell(prefix):
        row = next(l for l in lines if l.startswith(prefix + " "))
        return row[end - 8:end].strip()

    # read the COLUMN, not the row: a row contains several 0.00/1.00 cells and
    # a test that greps the whole line passes even when the column is a
    # hardcoded constant.
    assert hapax_cell("0") == "0.00"
    assert hapax_cell("3") == "1.00"


def test_the_table_warns_when_sufficiency_rises_with_hapax_share():
    """The plan's own failure signature: a sufficiency gain accompanied by a
    rise in hapax share is memorisation, not expressiveness."""
    ids = [f"c{i}" for i in range(4)]
    shared = {i: [_atom("shared")] for i in ids}
    bespoke = {i: [_atom(f"bespoke_{i}")] for i in ids}
    art = _artifact(ids, {
        "0": _rung_block(ids, sufficient=False, by_clause=shared),
        "1": _rung_block(ids, sufficient=False, by_clause=shared),
        "1.5": _rung_block(ids, sufficient=False, by_clause=shared),
        "2": _rung_block(ids, sufficient=False, by_clause=shared),
        "3": _rung_block(ids, sufficient=True, by_clause=bespoke),
        "4": _rung_block(ids, sufficient=False, by_clause=shared),
        L.NULL_ARM: _rung_block(ids, by_clause={i: [] for i in ids}),
    })
    txt = L.table(art)
    assert "MEMORISATION" in txt.upper()
    assert "3" in [w.strip() for w in txt.upper().split()]


# --------------------------------------------------------------------------
# 7. THE COVERAGE GATE

def test_the_table_refuses_to_print_below_full_coverage():
    ids = [f"c{i}" for i in range(10)]
    rungs = {r: _rung_block(ids) for r in L.RUNGS}
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    rungs["2"]["fidelity"].pop("c3")           # a lost batch
    with pytest.raises(L.CoverageError) as e:
        L.table(_artifact(ids, rungs))
    assert "c3" in str(e.value) or "9/10" in str(e.value)


def test_coverage_counts_against_the_declared_sample_not_the_results_dict():
    """The readback defect, in one assertion: a clause that never reached
    `results` must still appear in the denominator."""
    ids = [f"c{i}" for i in range(10)]
    rungs = {r: _rung_block(ids) for r in L.RUNGS}
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    del rungs["2"]["fidelity"]["c7"]
    cov = L.coverage(_artifact(ids, rungs))
    assert cov["2"]["judged"] == (9, 10)
    assert cov["2"]["missing_judged"] == ["c7"]


def test_a_none_verdict_is_unanswered_not_answered():
    ids = [f"c{i}" for i in range(10)]
    rungs = {r: _rung_block(ids) for r in L.RUNGS}
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    rungs["1"]["fidelity"]["c2"] = None
    cov = L.coverage(_artifact(ids, rungs))
    assert cov["1"]["judged"] == (9, 10)


def test_annotation_coverage_is_gated_separately_from_judging():
    ids = [f"c{i}" for i in range(10)]
    rungs = {r: _rung_block(ids) for r in L.RUNGS}
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    rungs["3"]["annotated"] = ids[:8]
    with pytest.raises(L.CoverageError):
        L.table(_artifact(ids, rungs))


def test_an_empty_annotation_is_answered_but_a_missing_one_is_not():
    """A clause the annotator answered with zero atoms is a legitimate answer;
    a clause whose call died is not. Conflating them shrinks the denominator
    silently, which is exactly the defect being guarded."""
    ids = [f"c{i}" for i in range(10)]
    rungs = {r: _rung_block(ids) for r in L.RUNGS}
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    rungs["3"]["by_clause"]["c4"] = []
    cov = L.coverage(_artifact(ids, rungs))
    assert cov["3"]["annotated"] == (10, 10)


def test_readback_summarize_undercounts_unanswered_and_ladder_says_so():
    """✅ THE DEFECT IS FIXED, and this test did its job by failing.

    It was written to pin a defect in `readback.summarize`: `unanswered` was
    computed from the results dict, which a lost batch never enters, so it
    reported 0 while a condition sat at 90/125 with the losses concentrated in
    whole clause-kind strata. The docstring said "the day readback.py is
    fixed, this test tells us". It did — it went red the same day.

    Now inverted: `summarize` counts against the DECLARED sample, so the two
    implementations must AGREE. Keeping the ladder's independent
    `readback_coverage` as a cross-check is deliberate — two ways of counting
    the same thing, from different code, is how the original defect would have
    been caught before it corrupted a live run."""
    rows = rb.load_clauses()
    ann = rb.load_annotations()
    ids = rb.stratified_sample(rows, 25, L.SEED)[:10]
    trials = rb.build_trials(ids, rows, ann, 4, "random", L.SEED)
    art = {
        "clause_ids": ids,
        "trials": {"random_N4": trials},
        "fidelity_trials": trials,
        "results": {"fidelity": {},
                    # two clauses' batch was lost: they never got a key
                    "discrim": {"random_N4": {c: 0 for c in ids[:8]}}},
        "ceiling": rb.equivalence_profile(rows, ann),
        "errors": [],
    }
    summ = rb.summarize(art)["discrim"]["random_N4"]
    assert summ["unanswered"] == 2, (
        "readback.summarize regressed to counting None values among the keys "
        "that came BACK — a lost batch is invisible that way")
    assert summ["coverage"] == (8, 10)
    #: the ladder's independent count must agree with it
    assert L.readback_coverage(art)["discrim"]["random_N4"] == (8, 10)
    assert L.readback_coverage(art)["fidelity"] == (0, 10)


# --------------------------------------------------------------------------
# 8. THE NULL-ONTOLOGY ARM

def test_the_null_arm_renders_the_boilerplate_and_nothing_else():
    txt = L.render_for_rung([], "conditional", L.NULL_ARM)
    assert "conditional" in txt
    assert "NO CONCEPTS" in txt.upper()


def test_the_null_arm_render_is_identical_to_readbacks_empty_render():
    for kind in rb.CLAUSE_KINDS:
        assert (L.render_for_rung([], kind, L.NULL_ARM)
                == rb.render([], kind))


def test_the_table_refuses_to_print_without_the_null_arm():
    ids = [f"c{i}" for i in range(5)]
    art = _artifact(ids, {r: _rung_block(ids) for r in L.RUNGS})
    with pytest.raises(L.LadderError):
        L.table(art)


def test_the_table_prints_the_null_arm_as_its_own_row():
    ids = [f"c{i}" for i in range(5)]
    rungs = {r: _rung_block(ids) for r in L.RUNGS}
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    txt = L.table(_artifact(ids, rungs))
    assert any(l.strip().startswith(L.NULL_ARM) for l in txt.splitlines())


# --------------------------------------------------------------------------
# 9. THE RENDERER — reused, not forked

def test_rungs_0_and_1_render_byte_identically_to_readback():
    """The instrument is `readback.render`. Rung 0's measured baseline is only
    applicable if the render it is scored through is the same render."""
    atoms = [_atom("x", kind="act", gloss="does a thing", span_id="s1")]
    for r in ("0", "1"):
        assert (L.render_for_rung(atoms, "meta", r)
                == rb.render(atoms, "meta"))


def test_a_rung_whose_names_carry_polarity_gets_a_render_that_says_so():
    """Rungs 1.5 and 2 encode polarity and principals IN THE NAME, so leaving
    readback's 'it records no polarity' disclaimer in place would make the
    render assert something false — scored, correctly, as unfaithful."""
    atoms = [_atom("must_x__model_user", kind="act")]
    for r in ("1.5", "2"):
        txt = L.render_for_rung(atoms, "meta", r)
        assert L.READBACK_CLOSING not in txt
        assert "polarity" in txt.lower()


def test_readbacks_closing_paragraph_is_still_what_ladder_splices():
    """render_for_rung replaces readback's closing disclaimer for the rungs
    where it has become FALSE. If readback.py rewords it, the splice silently
    stops happening — so pin the string."""
    assert L.READBACK_CLOSING in rb.render([], "meta")
    assert L.READBACK_CLOSING in rb.render([_atom("x")], "meta")


def test_rung_1_5_render_stops_claiming_the_index_records_no_polarity():
    atoms = [_atom("must_x__model_user", kind="act")]
    txt = L.render_for_rung(atoms, "meta", "1.5")
    assert L.READBACK_CLOSING not in txt
    assert "polarity" in txt.lower()


def test_rung_4_render_shows_the_invented_structure():
    atoms = [_atom("announce", kind="act", deontic="required",
                   addressee="steward")]
    txt = L.render_for_rung(atoms, "meta", "4")
    assert "deontic" in txt and "required" in txt
    assert "addressee" in txt and "steward" in txt


def test_rung_4_render_does_not_deny_holding_what_it_holds():
    atoms = [_atom("announce", kind="act", deontic="required")]
    txt = L.render_for_rung(atoms, "meta", "4")
    assert L.READBACK_CLOSING not in txt


def test_render_is_deterministic_and_reads_no_file_or_clock():
    atoms = [_atom("x", kind="act")]
    assert (L.render_for_rung(atoms, "meta", "4")
            == L.render_for_rung(atoms, "meta", "4"))


def test_render_never_carries_the_quote_or_the_locator():
    atoms = [dict(_atom("x"), quote="THE VERBATIM PASSAGE TEXT",
                  locator="model_spec@x > y", clause_id="m0006")]
    for r in list(L.RUNGS) + [L.NULL_ARM]:
        txt = L.render_for_rung(atoms, "meta", r)
        assert "VERBATIM" not in txt
        assert "model_spec@" not in txt


# --------------------------------------------------------------------------
# 10. DEMONSTRATIONS ARE SYNTHETIC

def test_rungs_that_must_show_the_grammar_actually_ship_demonstrations():
    blocks = L.load_rung_blocks()
    for r in ("1.5", "2", "4"):
        assert "DEMO>" in blocks[r], f"rung {r} tells but does not show"


def test_no_demonstration_is_a_passage_of_either_spec():
    passages = L.demonstration_passages()
    assert passages
    L.assert_demonstrations_synthetic(passages)


def test_the_leak_check_catches_a_demonstration_lifted_from_the_spec():
    spec_clause = json.load(open(CLAUSES, encoding="utf-8"))["clauses"]
    lifted = next(c["quote"] for c in spec_clause
                  if len(c.get("quote") or "") > 120)
    with pytest.raises(L.DemonstrationLeak):
        L.assert_demonstrations_synthetic(["a synthetic one", lifted.strip()])


def test_the_leak_check_catches_a_lifted_FRAGMENT_too():
    """Curation is the leak, so a lifted sentence inside a longer invented
    passage is the same defect as a lifted passage."""
    spec_clause = json.load(open(CLAUSES, encoding="utf-8"))["clauses"]
    lifted = next(c["quote"] for c in spec_clause
                  if len(c.get("quote") or "") > 200)
    frag = " ".join(lifted.split()[:14])
    with pytest.raises(L.DemonstrationLeak):
        L.assert_demonstrations_synthetic([f"In the garden, {frag}, we agree."])


def test_building_a_prompt_refuses_when_a_demonstration_is_spec_sourced(
        monkeypatch):
    spec_clause = json.load(open(CLAUSES, encoding="utf-8"))["clauses"]
    lifted = next(c["quote"] for c in spec_clause
                  if len(c.get("quote") or "") > 120).strip()
    blocks = dict(L.load_rung_blocks())
    blocks["1.5"] = blocks["1.5"] + "\n\nDEMO> " + lifted + "\n"
    monkeypatch.setattr(L, "load_rung_blocks", lambda *a, **k: blocks)
    with pytest.raises(L.DemonstrationLeak):
        L.annotate_prompt_for(_row(), "1.5", L.load_vocabulary())


# --------------------------------------------------------------------------
# 11. PROMPTS

def test_the_rung_block_is_appended_to_the_shipped_annotation_system_prompt():
    import annotate
    base_system, _ = annotate.load_template()
    system, _ = L.annotate_prompt_for(_row(), "1", L.load_vocabulary())
    assert system.startswith(base_system)
    assert L.load_rung_blocks()["1"] in system


def test_one_clause_at_a_time_means_one_clause_in_the_prompt():
    rows = rb.load_clauses()
    row = _row()
    _, user = L.annotate_prompt_for(row, "1", L.load_vocabulary(), rows)
    other = [r["id"] for r in rows if r["id"] != row["id"]][:50]
    assert row["id"] in user
    assert sum(user.count(o) for o in other) == 0


def test_the_whole_vocabulary_is_carried_with_no_eviction():
    vocab = L.load_vocabulary()
    _, user = L.annotate_prompt_for(_row(), "1", vocab)
    missing = [n for n in vocab if n not in user]
    assert missing == []


def test_the_prompt_never_names_a_behaviour_or_a_query():
    system, user = L.annotate_prompt_for(_row(), "3", L.load_vocabulary())
    low = (system + user).lower()
    for banned in ("behaviour", "behavior query", "relevance", "panel",
                   "which behaviour"):
        assert banned not in low


def test_the_prompt_is_a_pure_function_of_rung_and_clause():
    a = L.annotate_prompt_for(_row(), "2", L.load_vocabulary())
    b = L.annotate_prompt_for(_row(), "2", L.load_vocabulary())
    assert a == b


# --------------------------------------------------------------------------
# 12. THE MODEL IS A PARAMETER — ONE CODE PATH

def test_luna_and_sol_build_byte_identical_prompts():
    rows = rb.load_clauses()
    ids = L.sample(rows)[:2]
    cl_a, cl_b = ScriptedClient(default=None), ScriptedClient(default=None)
    L.annotate_rung(ids, rows, "1", L.load_vocabulary(), cl_a, attempts=1)
    L.annotate_rung(ids, rows, "1", L.load_vocabulary(), cl_b, attempts=1)
    assert cl_a.calls == cl_b.calls


def test_the_model_only_reaches_the_provider_config():
    """`--model sol` and `--model luna` differ in the provider row and nowhere
    else; anything else would make the delta uninterpretable."""
    assert L.provider_for("luna").model == "gpt-5.6-luna"
    assert L.provider_for("sol").model == "gpt-5.6-sol"


# --------------------------------------------------------------------------
# 13. NO SPEND

def test_nothing_here_constructs_a_live_client(monkeypatch, tmp_path):
    import providers

    def boom(*a, **k):
        raise AssertionError("a live client was constructed")

    monkeypatch.setattr(providers, "LiveClient", boom)
    rows = rb.load_clauses()
    # Writes to tmp_path, NOT to HERE/smoke_annotate/. That directory is
    # gitignored, so on a fresh clone it does not exist and this test failed
    # with FileNotFoundError — the suite could not pass from a clean checkout
    # (found by the 2026-08-05 quality read, RELEVANCE_QUALITY_READ.md §6).
    # The output path is incidental to what this test asserts: that a dry run
    # constructs no live client. Owning its own directory also stops the test
    # depending on repo state it does not create.
    L.main(["--dry-run", "--rungs", "0", "--out",
            str(tmp_path / "ladder_dryrun.json")])


def test_the_cli_requires_live_to_be_asked_for_explicitly():
    ap = L.build_parser()
    a = ap.parse_args([])
    assert a.live is False


# --------------------------------------------------------------------------
# 14. RETRY AND RESUME

def test_a_rate_limited_call_is_retried_and_then_succeeds():
    rows = rb.load_clauses()
    ids = L.sample(rows)[:1]
    vocab = L.load_vocabulary()
    known = sorted(vocab)[0]
    good = _resp(ids[0], [_atom(known, kind=vocab[known]["kind"])])
    client = ScriptedClient([RuntimeError("HTTP 429: rate limit"), good])
    bc, stats, errors = L.annotate_rung(ids, rows, "1", vocab, client,
                                        attempts=3, sleep=lambda s: None)
    assert bc[ids[0]]
    assert errors == []
    assert stats["retries"] == 1


def test_a_call_that_never_succeeds_is_recorded_and_not_silently_dropped():
    rows = rb.load_clauses()
    ids = L.sample(rows)[:1]
    client = ScriptedClient(default=RuntimeError("HTTP 429: rate limit"))
    bc, stats, errors = L.annotate_rung(ids, rows, "1", L.load_vocabulary(),
                                        client, attempts=2,
                                        sleep=lambda s: None)
    assert ids[0] not in bc
    assert errors


def test_resume_never_rebills_an_answered_clause():
    rows = rb.load_clauses()
    ids = L.sample(rows)[:3]
    vocab = L.load_vocabulary()
    known = sorted(vocab)[0]
    prior = {i: [_atom(known, kind=vocab[known]["kind"])] for i in ids[:2]}
    client = ScriptedClient(default=_resp(ids[2], [
        _atom(known, kind=vocab[known]["kind"])]))
    bc, _, _ = L.annotate_rung(ids, rows, "1", vocab, client, attempts=1,
                               prior=prior, sleep=lambda s: None)
    assert len(client.calls) == 1
    assert set(bc) == set(ids)


def test_resume_never_rebills_an_answered_fidelity_judgement():
    items = [{"clause_id": f"c{i}", "clause_kind": "meta", "render": "R",
              "source_text": "S"} for i in range(10)]
    prior = {f"c{i}": {"faithful": True, "sufficient": False,
                       "unsupported": [], "missing": []} for i in range(5)}
    client = ScriptedClient(default=json.dumps(
        [{"item": i + 1, "faithful": True, "sufficient": True,
          "unsupported": [], "missing": []} for i in range(5)]))
    res, errors = L.judge_fidelity(items, client, batch_size=5, prior=prior,
                                   sleep=lambda s: None)
    assert len(client.calls) == 1
    assert len(res) == 10


# --------------------------------------------------------------------------
# 15. THE JUDGE IS THE READ-BACK'S JUDGE

def test_the_fidelity_prompt_is_readbacks_own_prompt():
    items = [{"clause_id": "c0", "clause_kind": "meta", "render": "R",
              "source_text": "S"}]
    assert L.fidelity_prompt(items) == rb.fidelity_prompt(items)


def test_fidelity_items_carry_the_render_and_the_source_passage():
    rows = rb.load_clauses()
    ids = L.sample(rows)[:3]
    ann = rb.load_annotations()
    items = L.fidelity_items(ids, rows, {i: ann.get(i, []) for i in ids}, "0")
    assert [i["clause_id"] for i in items] == ids
    for it, cid in zip(items, ids):
        assert it["source_text"]
        assert it["render"] == rb.render(
            ann.get(cid, []), {r["id"]: r for r in rows}[cid]["kind"])


# --------------------------------------------------------------------------
# 16. COST, FROM MEASURED TOKENS

def test_chars_per_token_is_calibrated_from_this_repos_own_logged_calls():
    r = L.calibrate_chars_per_token()
    assert 3.5 < r["chars_per_token"] < 6.0
    assert r["n_calls"] > 50
    assert r["source"].endswith("usage.jsonl")


def test_cost_is_estimated_per_rung_for_both_models():
    est = L.estimate_cost(rungs=("1",), models=("luna", "sol"))
    assert est["luna"]["1"]["usd"] > 0
    assert est["sol"]["1"]["usd"] > est["luna"]["1"]["usd"]


def test_the_cost_estimate_counts_real_prompt_characters():
    """Not a guess: the estimate builds the prompts it would send and measures
    them. A rung whose prompt carries the whole vocabulary must cost more than
    the null arm, which sends no annotation prompt at all."""
    est = L.estimate_cost(rungs=("1", L.NULL_ARM), models=("luna",))
    assert est["luna"]["1"]["prompt_chars"] > 100_000
    assert (est["luna"][L.NULL_ARM]["prompt_chars"]
            < est["luna"]["1"]["prompt_chars"])


def test_the_estimate_reports_the_cached_input_case_separately():
    """Every annotation call in a rung shares a long constant prefix, so the
    provider's automatic prompt cache changes the input bill by an order of
    magnitude. Reporting one number would be a guess dressed as a measurement.
    """
    est = L.estimate_cost(rungs=("1",), models=("sol",))
    assert est["sol"]["1"]["usd_cached_input"] < est["sol"]["1"]["usd"]


# --------------------------------------------------------------------------
# 17. THE TABLE

def test_the_table_is_deterministic():
    ids = [f"c{i}" for i in range(5)]
    rungs = {r: _rung_block(ids) for r in L.RUNGS}
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    art = _artifact(ids, rungs)
    assert L.table(art) == L.table(art)


def test_the_table_reports_the_realised_rate_not_the_requested_one():
    ids = [f"c{i}" for i in range(125)]
    rungs = {r: _rung_block(ids, by_clause=_by_clause(ids, per=2))
             for r in L.RUNGS}
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    txt = L.table(_artifact(ids, rungs))
    assert "2.00" in txt


def test_the_table_shows_faithful_and_sufficient_with_intervals():
    ids = [f"c{i}" for i in range(5)]
    rungs = {r: _rung_block(ids) for r in L.RUNGS}
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    txt = L.table(_artifact(ids, rungs))
    assert "faithful" in txt.lower() and "sufficient" in txt.lower()
    assert "[" in txt and "]" in txt


# --------------------------------------------------------------------------
# 18. THE JUDGE'S OWN CONTROLS (drift review, finding 10)
#
# All six of the read-back's pre-registered predictions were wrong, several
# inverted, and nobody has checked that the judge's `sufficient` means what
# the word says. A null arm bounds the render; these bound the JUDGE.

def test_a_positive_control_shows_the_judge_the_clauses_own_text():
    rows = rb.load_clauses()
    ids = L.sample(rows)[:3]
    items = L.control_items(ids, rows, "positive")
    by_id = {r["id"]: r for r in rows}
    for it in items:
        assert it["render"].strip() == by_id[it["clause_id"]]["quote"].strip()
        assert it["source_text"].strip() == it["render"].strip()


def test_a_negative_control_shows_the_judge_a_DIFFERENT_clauses_render():
    rows = rb.load_clauses()
    ids = L.sample(rows)[:5]
    items = L.control_items(ids, rows, "negative")
    ann = rb.load_annotations()
    by_id = {r["id"]: r for r in rows}
    for it in items:
        own = rb.render(ann.get(it["clause_id"], []),
                        by_id[it["clause_id"]]["kind"])
        assert it["render"] != own
        assert it["source_text"].strip() == by_id[it["clause_id"]]["quote"].strip()


def test_the_controls_are_deterministic():
    rows = rb.load_clauses()
    ids = L.sample(rows)[:5]
    assert (L.control_items(ids, rows, "negative")
            == L.control_items(ids, rows, "negative"))


def test_the_gates_stop_when_the_judge_fails_its_own_controls():
    ids = [f"c{i}" for i in range(20)]
    rungs = {r: _rung_block(ids) for r in L.RUNGS}
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    art = _artifact(ids, rungs)
    art["controls"] = {
        # the judge calls a clause's own text insufficient: it is broken
        "positive": {c: {"faithful": True, "sufficient": False,
                         "unsupported": [], "missing": []} for c in ids},
        "negative": {c: {"faithful": True, "sufficient": False,
                         "unsupported": [], "missing": []} for c in ids},
    }
    g = L.gates(art)
    assert g["instrument"]["verdict"] == "STOP"
    assert "STOP" in L.table(art)


def test_an_artifact_with_no_judge_controls_at_all_is_a_STOP():
    """An unrun control is not a passed control. The read-back's six
    pre-registered predictions were all wrong; an unvalidated `sufficient` is
    the one thing that would make every rung above uninterpretable."""
    ids = [f"c{i}" for i in range(20)]
    rungs = {r: _rung_block(ids) for r in L.RUNGS}
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    g = L.gates(_artifact(ids, rungs))
    assert g["instrument"]["verdict"] == "STOP"
    assert "unvalidated" in g["instrument"]["why"].lower()


def test_the_gates_pass_a_judge_that_answers_its_controls_correctly():
    ids = [f"c{i}" for i in range(20)]
    rungs = {r: _rung_block(ids) for r in L.RUNGS}
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    art = _artifact(ids, rungs)
    art["controls"] = {
        "positive": {c: {"faithful": True, "sufficient": True,
                         "unsupported": [], "missing": []} for c in ids},
        "negative": {c: {"faithful": False, "sufficient": False,
                         "unsupported": [], "missing": []} for c in ids},
    }
    assert L.gates(art)["instrument"]["verdict"] == "PROCEED"


# --------------------------------------------------------------------------
# 19. PROSPECTIVE STOP CONDITIONS (drift review)

def test_rung_3_matching_rung_0_blocks_the_sol_run():
    """The plan's own words: rung 3 ~= rung 0 means the grammar was never the
    constraint. That has to be a machine-checked line, not a note a human is
    trusted to notice."""
    ids = [f"c{i}" for i in range(125)]
    rungs = {r: _rung_block(ids, sufficient=False) for r in L.RUNGS}
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    art = _artifact(ids, rungs)
    g = L.gates(art)
    assert g["grammar_is_the_constraint"]["verdict"] == "STOP"
    assert "sol" in g["grammar_is_the_constraint"]["why"].lower()


def test_a_real_rung_3_gain_clears_the_sol_gate():
    ids = [f"c{i}" for i in range(125)]
    rungs = {r: _rung_block(ids, sufficient=False) for r in L.RUNGS}
    rungs["3"] = _rung_block(ids, sufficient=True)
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    assert (L.gates(_artifact(ids, rungs))["grammar_is_the_constraint"]
            ["verdict"] == "PROCEED")


def test_the_table_prints_one_explicit_proceed_or_stop_line():
    ids = [f"c{i}" for i in range(125)]
    rungs = {r: _rung_block(ids) for r in L.RUNGS}
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    txt = L.table(_artifact(ids, rungs))
    verdicts = [l for l in txt.splitlines() if l.startswith("VERDICT")]
    assert len(verdicts) == 1


def test_a_rung_over_the_rate_cap_is_a_stop():
    ids = [f"c{i}" for i in range(125)]
    rungs = {r: _rung_block(ids) for r in L.RUNGS}
    rungs["4"] = _rung_block(ids, by_clause=_by_clause(ids, per=5))
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    assert L.gates(_artifact(ids, rungs))["rate_cap"]["verdict"] == "STOP"


# --------------------------------------------------------------------------
# 20. THE TABLE SAYS WHAT IT MEASURES (drift review, finding 11)

def test_the_table_says_annotation_and_renderer_are_measured_JOINTLY():
    """render() is held fixed across every rung, so a faithfulness failure
    caused by the template over-asserting is charged to the ontology. The
    table has to say so where the numbers are, not in a docstring."""
    ids = [f"c{i}" for i in range(5)]
    rungs = {r: _rung_block(ids) for r in L.RUNGS}
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    txt = L.table(_artifact(ids, rungs)).upper()
    assert "JOINTLY" in txt


def test_every_rung_declares_its_batch_size_and_eviction_policy():
    """Finding 2: the cost of `no eviction` is the whole 361-atom vocabulary
    on every one of 125 calls, and it has to be stated where it is priced."""
    for r in L.RUNGS:
        spec = L.rung_spec(r)
        assert spec["batch_size"] >= 1
        assert spec["eviction"]


# --------------------------------------------------------------------------
# 21. THE DEMONSTRATIONS ARE FROZEN (drift review, finding 9)

def test_the_prompt_file_declares_a_sha256_over_its_demonstrations():
    """The substring test is a backstop against a syntactic leak. The actual
    mitigation is that the demonstrations were written and FROZEN before any
    panel-conditioned analysis; the hash is what makes that checkable."""
    assert L.declared_demonstrations_sha256()
    assert (L.declared_demonstrations_sha256()
            == L.demonstrations_sha256())


def test_a_changed_demonstration_breaks_the_frozen_hash():
    passages = L.demonstration_passages()
    assert (L.demonstrations_sha256(passages + ["a new one"])
            != L.demonstrations_sha256(passages))


def test_prompt_building_refuses_when_the_demonstrations_are_not_frozen(
        monkeypatch):
    monkeypatch.setattr(L, "declared_demonstrations_sha256",
                        lambda *a, **k: "0" * 64)
    with pytest.raises(L.DemonstrationLeak):
        L.annotate_prompt_for(_row(), "1.5", L.load_vocabulary())


# --------------------------------------------------------------------------
# 22. THE RELEVANCE HOOK (drift review, finding 1)
#
# Fidelity and sufficiency are properties of the read-back. Nothing in rungs
# 0-4 shows that a rung's atoms RETRIEVE better, which is the actual goal.
# The hook is $0, runs after the live pass, is measured ONCE and never fed
# back — invariant 9 bars fitting, not measuring.

def test_the_relevance_hook_is_fenced_as_diagnostic_only():
    doc = (L.relevance_diagnostic.__doc__ or "").upper()
    assert "DIAGNOSTIC" in doc
    assert "NEVER" in doc


def test_no_annotation_path_can_reach_the_relevance_hook():
    """A diagnostic that reads the panel must not be able to inform the
    ontology. The mechanical guarantee is that nothing on the build path
    mentions it."""
    import inspect
    for fn in (L.annotate_rung, L.annotate_prompt_for, L.verify_rung_atoms,
               L.enforce_rate_cap, L.run_ladder, L.render_for_rung,
               L.judge_fidelity):
        src = inspect.getsource(fn)
        assert "relevance_diagnostic" not in src
        assert "benchmark" not in src


def test_the_relevance_hook_normalises_convention_decorated_names():
    """Rung 1.5 renames `disclose` to `must_disclose__model_user`, which
    matches no query atom. Scoring that raw would report a collapse caused by
    the ladder's own notation rather than by the annotation."""
    bc = {"m1": [_atom("must_disclose_reasoning__model_user", kind="act")]}
    flat = L.stem_normalised(bc)
    assert [a["name"] for a in flat["m1"]] == ["disclose_reasoning"]


def test_stem_normalisation_leaves_an_undecorated_name_alone():
    bc = {"m1": [_atom("user_request_ambiguous")]}
    assert L.stem_normalised(bc) == bc


def test_polarity_readiness_counts_what_a_structural_operator_could_use():
    """HANDOFF.md:449: 3-11 of every 19-28 query atoms earn a NEGATIVE weight
    'which our query cannot express'. A parseable prefix is a label-free way
    to make it expressible, so the count of clause atoms that now carry one is
    the number that says whether rung 1.5 bought anything usable."""
    bc = {"m1": [_atom("mustnot_disclose__model_user", kind="act"),
                 _atom("plain_situation")],
          "m2": [_atom("may_refuse__model_user", kind="act")]}
    r = L.polarity_readiness(bc)
    assert r["atoms"] == 3
    assert r["with_polarity"] == 2
    assert r["with_principals"] == 2
    assert r["by_polarity"]["mustnot"] == 1


def test_the_relevance_hook_returns_a_score_per_rung_or_says_why_not():
    ids = [f"c{i}" for i in range(3)]
    rungs = {r: _rung_block(ids) for r in L.RUNGS}
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    got = L.relevance_diagnostic(_artifact(ids, rungs))
    assert "DIAGNOSTIC" in got["fence"].upper()
    for r in L.RUNGS:
        assert r in got["rungs"]
        cell = got["rungs"][r]
        assert ("mcc" in cell) or ("unavailable" in cell)


def test_the_relevance_hook_actually_scores_the_shipped_annotations():
    """Rung 0 IS the shipped annotation set, so this is the retrieval number
    every other rung is read against. If it cannot be produced, the ladder
    cannot answer the question it was extended to answer, and saying so
    explicitly beats a silent `unavailable`."""
    rows = rb.load_clauses()
    ids = L.sample(rows)
    art = {"clause_ids": ids,
           "rungs": {"0": L.build_rung_0(ids, rows, rb.load_annotations())}}
    got = L.relevance_diagnostic(art)["rungs"]["0"]
    if "unavailable" in got:
        pytest.skip(f"query stack unavailable: {got['unavailable']}")
    assert -1.0 <= got["mcc"] <= 1.0
    assert got["n_clauses_replaced"] == 125
    assert set(got["by_behaviour"])


# --------------------------------------------------------------------------
# 23. STRUCTURALLY ORPHANED CLAUSES (segmentation attribution, step 2)
#
# 16 of the 125 cannot stand alone whatever atoms they are given: list items
# severed from their "...:" lead-in, lower-case fragments, bare antecedents.
# No rung can make them sufficient, so leaving them in the denominator makes
# rung 3 look like rung 0 on 13% of the sample — which is the exact pattern
# the PROCEED/STOP gate reads as "the grammar was never the constraint".

def test_the_orphaned_clauses_come_from_the_segmentation_attribution():
    got = L.structurally_orphaned()
    assert got["available"], got
    ids = L.sample(rb.load_clauses())
    flagged = set(got["ids"]) & set(ids)
    assert len(flagged) == 16
    assert "m0117" in flagged or "m0103" in flagged


def test_the_orphan_set_degrades_honestly_if_the_module_is_missing(
        monkeypatch):
    import builtins
    real = builtins.__import__

    def no_seg(name, *a, **k):
        if name == "segmentation_attr":
            raise ImportError("owned by another agent, mid-edit")
        return real(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", no_seg)
    L._ORPHAN_CACHE.clear()
    got = L.structurally_orphaned()
    assert got["available"] is False
    assert got["ids"] == []
    assert got["why"]
    L._ORPHAN_CACHE.clear()


def _real_artifact(sufficient_by_rung):
    rows = rb.load_clauses()
    ids = L.sample(rows)
    orphans = set(L.structurally_orphaned()["ids"])
    kinds = {r["id"]: r["kind"] for r in rows}
    rungs = {}
    for rung, suff in sufficient_by_rung.items():
        rungs[rung] = {
            "by_clause": _by_clause(ids), "annotated": list(ids),
            "fidelity": {c: {"faithful": True,
                             "sufficient": bool(suff) and c not in orphans,
                             "unsupported": [], "missing": []} for c in ids},
            "errors": []}
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    art = _artifact(ids, rungs)
    art["clause_kinds"] = kinds
    return art


def test_sufficiency_is_reported_on_all_125_AND_on_the_standalone_subset():
    art = _real_artifact({r: False for r in L.RUNGS})
    s = L.summarize(art)
    assert s["0"]["sufficient"]["n"] == 125
    assert s["0"]["sufficient_standalone"]["n"] == 125 - 16


def test_the_grammar_gate_is_computed_on_the_standalone_subset():
    """THE CONFOUND, exactly. 16 clauses cannot be fixed by any rung, so they
    dilute rung 3's gain. Here rung 3 fixes 12 clauses: 12/125 = 0.096 is
    below the gate, 12/109 = 0.110 is above it. Computed on all 125 this gate
    would fire — and it would be firing on segmentation, not on grammar."""
    rows = rb.load_clauses()
    ids = L.sample(rows)
    orphans = set(L.structurally_orphaned()["ids"])
    standalone = [c for c in ids if c not in orphans]
    assert len(standalone) == 109
    fixed = set(standalone[:12])
    rungs = {}
    for rung in L.RUNGS:
        rungs[rung] = {
            "by_clause": _by_clause(ids), "annotated": list(ids),
            "fidelity": {c: {"faithful": True,
                             "sufficient": rung == "3" and c in fixed,
                             "unsupported": [], "missing": []} for c in ids},
            "errors": []}
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    art = _artifact(ids, rungs)
    art["clause_kinds"] = {r["id"]: r["kind"] for r in rows}
    s = L.summarize(art)
    assert s["3"]["sufficient"]["rate"] < L.GRAMMAR_GATE_DELTA
    assert s["3"]["sufficient_standalone"]["rate"] >= L.GRAMMAR_GATE_DELTA
    g = L.gates(art)
    assert g["grammar_is_the_constraint"]["verdict"] == "PROCEED"
    why = g["grammar_is_the_constraint"]["why"]
    assert "standalone" in why.lower()
    assert "16" in why


def test_the_table_shows_both_denominators_so_the_exclusion_is_not_silent():
    art = _real_artifact({r: False for r in L.RUNGS})
    txt = L.table(art)
    assert "standalone" in txt.lower()
    assert "16" in txt


# --------------------------------------------------------------------------
# 24. OVER-ASSERTION (step 1: sufficiency vs retrieval error)
#
# The channel from the read-back to retrieval runs through UNSUPPORTED
# content, not missing content: >=1 unsupported phrase correlates +0.157
# [+0.062, +0.250] with per-clause retrieval error, missing-party and
# missing-deontic are indistinguishable from zero, and 86% of retrieval errors
# are false positives. Rungs 2-4 relax exactly the freedom that produces
# unsupported assertions, so a rung can "win" by asserting more.

def _fid(ids, sufficient=False, unsupported=()):
    return {c: {"faithful": not unsupported, "sufficient": sufficient,
                "unsupported": list(unsupported), "missing": []} for c in ids}


def test_the_unsupported_rate_is_a_first_class_column():
    ids = [f"c{i}" for i in range(4)]
    rungs = {r: _rung_block(ids) for r in L.RUNGS}
    rungs["3"]["fidelity"] = _fid(ids, unsupported=["a party the clause "
                                                    "never names"])
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    art = _artifact(ids, rungs)
    s = L.summarize(art)
    assert s["3"]["unsupported"]["rate"] == 1.0
    assert s["3"]["unsupported"]["mean_count"] == 1.0
    assert s["0"]["unsupported"]["rate"] == 0.0
    assert "unsup" in L.table(art).lower()


def test_a_sufficiency_gain_bought_with_more_unsupported_content_is_a_STOP():
    ids = [f"c{i}" for i in range(20)]
    rungs = {r: _rung_block(ids) for r in L.RUNGS}
    rungs["4"]["fidelity"] = _fid(ids, sufficient=True,
                                  unsupported=["invented duty"])
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    g = L.gates(_artifact(ids, rungs))
    assert g["over_assertion"]["verdict"] == "STOP"
    assert "4" in g["over_assertion"]["why"]


def test_a_sufficiency_gain_without_more_unsupported_content_passes():
    ids = [f"c{i}" for i in range(20)]
    rungs = {r: _rung_block(ids) for r in L.RUNGS}
    rungs["4"]["fidelity"] = _fid(ids, sufficient=True)
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    assert (L.gates(_artifact(ids, rungs))["over_assertion"]["verdict"]
            == "PROCEED")


def test_the_table_says_faithful_and_unsupported_are_ONE_measurement():
    ids = [f"c{i}" for i in range(4)]
    rungs = {r: _rung_block(ids) for r in L.RUNGS}
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    txt = L.table(_artifact(ids, rungs)).lower()
    assert "complement" in txt


def test_a_reduced_sample_prefers_meta():
    """meta is the worst retrieval stratum (+0.127 one-vs-rest) and sits at
    2/25 on sufficiency, so it has the most headroom if a rung ever has to run
    at reduced n."""
    rows = rb.load_clauses()
    got = L.reduced_sample(rows, 25)
    kinds = {r["id"]: r["kind"] for r in rows}
    assert len(got) == 25
    assert all(kinds[c] == "meta" for c in got)
    assert set(got) <= set(L.sample(rows))


def test_the_example_stratum_is_reported_apart_from_the_headline():
    """20 of the example stratum's 23 missing phrases point at content inside
    XML transcripts, so its sufficiency answers 'can atoms represent a
    rendered dialogue' — a different question from the other four kinds."""
    art = _real_artifact({r: False for r in L.RUNGS})
    s = L.summarize(art)
    assert s["0"]["by_kind"]["example"]["n"] == 25
    assert s["0"]["sufficient_headline"]["n"] <= 125 - 25
    txt = L.table(art)
    assert "example" in txt.lower()
    assert "transcript" in txt.lower()


# ==========================================================================
# 25. THE ENGINEERING REVIEW'S FOUR SEV-1s
#
# Each of these is a defect that a passing test suite did not catch, mostly
# because the tests hand-built the artifact the code was supposed to build.
# The rule they encode: assert on what the PRODUCING function produced.
# ==========================================================================

def _offline_artifact(rungs=("0", L.NULL_ARM), out=None):
    """A REAL run_ladder artifact — no client, no spend, nothing injected."""
    rows = rb.load_clauses()
    return L.run_ladder(list(rungs), "luna", live=False, rows=rows,
                        out_path=out, controls=False)


# ---- SEV-1 #1: the artifact must carry what the report reads --------------

def test_run_ladder_writes_clause_kinds_for_every_declared_clause():
    art = _offline_artifact()
    ids = art["clause_ids"]
    assert set(art["clause_kinds"]) >= set(ids)
    assert set(art["clause_kinds"][c] for c in ids) == set(rb.CLAUSE_KINDS)


def test_run_ladder_freezes_the_orphan_set_into_the_artifact():
    """Recomputing the exclusion at report time means a later --report, or a
    later edit to segmentation_attr, silently scores against a different
    denominator than the run did."""
    art = _offline_artifact()
    assert art["structurally_orphaned"]["available"] is True
    assert len(set(art["structurally_orphaned"]["ids"])
               & set(art["clause_ids"])) == 16


def test_summarize_uses_the_ARTIFACTS_orphan_set_not_a_recomputed_one():
    ids = [f"c{i}" for i in range(10)]
    rungs = {r: _rung_block(ids) for r in L.RUNGS}
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    art = _artifact(ids, rungs)
    art["structurally_orphaned"] = {"ids": ["c0", "c1"], "available": True,
                                    "why": "frozen at run time"}
    assert L.summarize(art)["0"]["n_orphans"] == 2
    assert L.summarize(art)["0"]["sufficient_standalone"]["n"] == 8


def test_the_per_kind_block_and_headline_survive_a_REAL_artifact():
    """The bug: `sufficient_headline` silently equalled `sufficient_standalone`
    on a real run because clause_kinds was never written, so the `example`
    filter never ran while the table's prose claimed it had."""
    art = _offline_artifact()
    fid = L.rung_0_fidelity_from_readback()
    for block in art["rungs"].values():
        block["fidelity"] = dict(fid)
    s = L.summarize(art)
    assert s["0"]["by_kind"]["example"]["n"] == 25
    assert s["0"]["sufficient_headline"]["n"] < s["0"]["sufficient_standalone"]["n"]
    txt = L.table(art)
    assert "conditional" in txt and "definitional" in txt


# ---- SEV-1 #2: the cap must bind on NESTED invented text -----------------

def test_nested_invented_text_is_priced_AND_capped():
    """`{"conditions": ["X"*500, "Y"*500]}` was priced by text_chars but
    invisible to the truncator, so rung 4 could buy sufficiency with prose the
    cap could not reach — and the binary search drove the ceiling to 0,
    emptying every legitimate gloss to protect it."""
    ids = [f"c{i}" for i in range(125)]
    bc = {c: [_atom("a", gloss="a real gloss",
                    conditions=["X" * 500, "Y" * 500])] for c in ids}
    capped, stats = L.enforce_rate_cap(bc, ids)
    assert L.rate_profile(capped, ids)["text_chars_per_clause"] <= 211
    assert stats["text_field_ceiling"] not in (0, None)
    assert capped["c0"][0]["gloss"], "a legitimate gloss was emptied"
    assert sum(len(s) for s in capped["c0"][0]["conditions"]) < 1000


def test_deeply_nested_invented_text_is_capped_too():
    ids = [f"c{i}" for i in range(125)]
    bc = {c: [_atom("a", gloss="g",
                    rel={"triggers": {"when": ["Z" * 400]}})] for c in ids}
    capped, _ = L.enforce_rate_cap(bc, ids)
    assert L.rate_profile(capped, ids)["text_chars_per_clause"] <= 211
    assert capped["c0"][0]["rel"]["triggers"]["when"][0]


def test_capping_preserves_the_shape_of_an_invented_field():
    ids = ["c0"]
    bc = {"c0": [_atom("a", conditions=["X" * 500, "Y" * 500])]}
    capped, _ = L.enforce_rate_cap(bc, ids)
    got = capped["c0"][0]["conditions"]
    assert isinstance(got, list) and len(got) == 2


def test_truncation_stops_at_a_word_boundary():
    """Cutting mid-word hands the judge a fragment that reads as a different
    claim than the one the annotator wrote — and that is scored as the
    ontology's failure. The fixture asserts its own precondition (that a naive
    cut WOULD land mid-word) so it cannot pass by an accident of alignment."""
    ids = [f"c{i}" for i in range(125)]
    words = ("abcdefghij " * 40).strip()   # 11-char period; 211 % 11 = 2
    bc = {c: [_atom("a", gloss=words)] for c in ids}
    capped, stats = L.enforce_rate_cap(bc, ids)
    ceiling = stats["text_field_ceiling"]
    assert ceiling and ceiling < len(words)
    assert words[ceiling] != " " and words[ceiling - 1] != " ", \
        "fixture is word-aligned at the ceiling; it cannot detect a mid-word cut"

    g = capped["c0"][0]["gloss"]
    assert words.startswith(g), "truncation must be a prefix"
    assert len(g) < ceiling, "a mid-word cut survived"
    assert words[len(g)] == " "
    assert not g.endswith(" ")


# ---- SEV-1 #5: the cap must bind on text the ANNOTATOR CHOSE -------------

def test_a_vocabulary_lookup_gloss_is_priced_but_never_truncated():
    """Rung 1 writes no text: its glosses are the vocabulary's own, substituted
    by the harness. 2.78 x the mean shipped gloss (76.2) is 211.3 > 211, so a
    global truncation chops rung 1's glosses while rung 0 is exempt by design —
    and rung 0 vs rung 1 IS the assignment-error contrast."""
    assert L.rung_spec("1")["text_is_chosen"] is False
    assert L.rung_spec("1.5")["text_is_chosen"] is False
    assert L.rung_spec("2")["text_is_chosen"] is True
    assert L.rung_spec("3")["text_is_chosen"] is True
    assert L.rung_spec("4")["text_is_chosen"] is True

    ids = [f"c{i}" for i in range(125)]
    bc = {c: [_atom("a", gloss="x" * 300)] for c in ids}
    capped, stats = L.enforce_rate_cap(bc, ids, cap_text=False)
    assert capped["c0"][0]["gloss"] == "x" * 300
    assert stats["gloss_chars_dropped"] == 0
    assert stats["text_capped"] is False
    assert stats["text_chars_per_clause"] > 211      # priced and REPORTED


def test_the_rate_cap_gate_does_not_fire_on_text_the_annotator_did_not_write():
    ids = [f"c{i}" for i in range(125)]
    over = {c: [_atom("a", gloss="x" * 300)] for c in ids}
    rungs = {r: _rung_block(ids) for r in L.RUNGS}
    rungs["1"] = _rung_block(ids, by_clause=over)
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    g = L.gates(_artifact(ids, rungs))
    assert g["rate_cap"]["verdict"] == "PROCEED"
    assert "not written" in g["rate_cap"]["why"].lower()


def test_the_rate_cap_gate_still_fires_on_text_the_annotator_DID_write():
    ids = [f"c{i}" for i in range(125)]
    over = {c: [_atom("a", gloss="x" * 300)] for c in ids}
    rungs = {r: _rung_block(ids) for r in L.RUNGS}
    rungs["3"] = _rung_block(ids, by_clause=over)
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    assert L.gates(_artifact(ids, rungs))["rate_cap"]["verdict"] == "STOP"


# ---- SEV-1 #3: the atom trim must not be strata-correlated ---------------

def _drops_by_kind(per=3):
    rows = rb.load_clauses()
    ids = L.sample(rows)
    kinds = {r["id"]: r["kind"] for r in rows}
    bc = {c: [_atom(f"a{i}") for i in range(per)] for c in ids}
    capped, stats = L.enforce_rate_cap(bc, ids)
    out = {}
    for c in ids:
        d = per - len(capped[c])
        if d:
            out[kinds[c]] = out.get(kinds[c], 0) + d
    return out, stats


def test_the_atom_trim_is_not_correlated_with_clause_kind():
    """The modal outcome: every clause returns the instructed 3 atoms, so 28
    must be dropped. A lexicographic tie-break took 9 from `example` and 1
    from `definitional` — clause ids are contiguous within kind — and
    `by_kind` and `sufficient_headline` are read off exactly that split."""
    drops, stats = _drops_by_kind(3)
    assert sum(drops.values()) == stats["atoms_dropped"] == 28
    assert set(drops) == set(rb.CLAUSE_KINDS), f"a whole kind was spared: {drops}"
    assert max(drops.values()) <= 12, drops
    assert min(drops.values()) >= 2, drops


def test_the_atom_trim_is_still_deterministic_and_seed_pinned():
    a, _ = _drops_by_kind(3)
    b, _ = _drops_by_kind(3)
    assert a == b


# ---- SEV-1 #4: the judge controls need a coverage gate -------------------

def _art_with_controls(n_pos, n_neg, n=125):
    ids = [f"c{i}" for i in range(n)]
    rungs = {r: _rung_block(ids) for r in L.RUNGS}
    rungs[L.NULL_ARM] = _rung_block(ids, by_clause={i: [] for i in ids})
    art = _artifact(ids, rungs)
    art["controls"] = {
        "positive": {c: {"faithful": True, "sufficient": True,
                         "unsupported": [], "missing": []}
                     for c in ids[:n_pos]},
        "negative": {c: {"faithful": False, "sufficient": False,
                         "unsupported": ["x"], "missing": []}
                     for c in ids[:n_neg]}}
    return art


def test_two_surviving_control_calls_do_not_certify_the_instrument():
    """The survivors-denominator defect, inside the gate that certifies every
    rung above it: 2 of 125 controls answered perfectly used to print
    PROCEED."""
    art = _art_with_controls(2, 2)
    cov = L.control_coverage(art)
    assert cov["positive"] == (2, 125)
    g = L.gates(art)
    assert g["instrument"]["verdict"] == "STOP"
    assert "2/125" in g["instrument"]["why"]
    assert g["coverage"]["verdict"] == "STOP"


def test_full_control_coverage_still_certifies():
    assert (L.gates(_art_with_controls(125, 125))["instrument"]["verdict"]
            == "PROCEED")


def test_control_errors_are_printed_not_merely_stored():
    art = _art_with_controls(125, 125)
    art["control_errors"] = ["fidelity/7: RuntimeError: HTTP 429"]
    txt = L.table(art)
    assert "control_errors" in txt or "429" in txt


# ---- #7: rung 3's prompt and render ---------------------------------------

def test_rung_3_does_not_reference_instructions_it_never_receives():
    """Each call carries exactly one rung block, so a cross-reference to an
    'earlier instruction' points at nothing. Rung 3 is the gate that
    authorises the Sol spend."""
    b = L.load_rung_blocks()["3"]
    for dangling in ("earlier instruction", "described in earlier",
                     "previous instruction", "as above"):
        assert dangling not in b.lower()


def test_a_render_decodes_the_convention_wherever_a_name_uses_it():
    """A rung with no convention REQUIREMENT may still use one. Judging
    `mustnot_x__model_user` against a closing that does not decode it scores
    an opaque string."""
    used = [_atom("mustnot_disclose__model_user", kind="act")]
    plain = [_atom("disclose", kind="act")]
    for rung in ("3", "4"):
        assert "double underscore" in L.render_for_rung(used, "meta",
                                                        rung).lower()
        assert "double underscore" not in L.render_for_rung(plain, "meta",
                                                            rung).lower()


# ---- #12 + operational ----------------------------------------------------

def test_the_cost_report_carries_a_TRUE_ceiling_from_max_tokens():
    """`$ worst` used the batch-8 mean reasoning. The b8 completion
    distribution is p90 3202 / max 4060 against a 4096 cap, so a batch-1 call
    running to the cap is not a tail event."""
    est = L.estimate_cost(rungs=("1",), models=("luna",), max_tokens=4096)
    d = est["luna"]["1"]
    assert d["out_tokens_ceiling"] > d["out_tokens_high"]
    assert d["usd_ceiling"] > d["usd"]
    assert "ceiling" in L.cost_report(est).lower()


def test_the_preflight_refuses_a_run_that_would_break_the_budget():
    ok = L.preflight(("0", L.NULL_ARM), "luna", budget=100.0)
    assert ok["ok"] is True
    bad = L.preflight(L.RUNGS, "sol", budget=1.0)
    assert bad["ok"] is False
    assert bad["projected_ceiling_usd"] > 1.0
    assert "sol" in bad["why"].lower() or "budget" in bad["why"].lower()


def test_a_live_run_is_refused_when_the_preflight_fails(monkeypatch, tmp_path):
    import providers

    def boom(*a, **k):
        raise AssertionError("a live client was constructed after a refusal")

    monkeypatch.setattr(providers, "LiveClient", boom)
    monkeypatch.setattr(L, "preflight", lambda *a, **k: {
        "ok": False, "why": "over budget", "projected_ceiling_usd": 99.0,
        "spent": 0.0, "budget": 1.0})
    with pytest.raises(SystemExit):
        L.main(["--live", "--rungs", "1", "--model", "luna",
                "--out", str(tmp_path / "x.json")])


def test_out_equal_to_resume_keeps_the_rungs_this_invocation_did_not_run(
        tmp_path):
    """Rungs must be runnable as separate invocations, which is the only way a
    $5-ceiling run stays interruptible."""
    p = str(tmp_path / "ladder.json")
    _offline_artifact(("0",), out=p)
    art = L.run_ladder([L.NULL_ARM], "luna", live=False, out_path=p, resume=p,
                       controls=False)
    assert set(art["rungs"]) == {"0", L.NULL_ARM}
    with open(p, encoding="utf-8") as f:
        assert set(json.load(f)["rungs"]) == {"0", L.NULL_ARM}


def test_a_checkpoint_is_written_DURING_a_rung_not_only_after_it():
    """A crash at call 120 of 125 must not lose 120 paid calls."""
    rows = rb.load_clauses()
    ids = L.sample(rows)[:3]
    vocab = L.load_vocabulary()
    known = sorted(vocab)[0]
    client = ScriptedClient(default=None)
    seen = []
    L.annotate_rung(ids, rows, "1", vocab, client, attempts=1,
                    sleep=lambda s: None,
                    checkpoint=lambda bc: seen.append(len(bc)))
    assert len(seen) == 3


def test_the_cap_budget_is_the_whole_sample_not_the_survivors():
    """Otherwise a resumed run gives resumed and fresh clauses different
    budgets — and failures cluster contiguously in a kind-sorted sample, so
    the difference is correlated with kind."""
    ids = [f"c{i}" for i in range(125)]
    answered = ids[:60]
    bc = {c: [_atom(f"a{i}") for i in range(4)] for c in answered}
    capped, stats = L.enforce_rate_cap(bc, ids)
    assert stats["atoms_dropped"] == 0, "a partial run was trimmed to a " \
                                        "partial budget"


def test_resume_recaps_from_raw_and_invalidates_the_verdicts_it_changed():
    """The stored by_clause is already capped, so re-capping a resumed run
    trims twice. Keeping the raw answer means the cap is applied once, over
    the union — and any clause whose atoms MOVED must lose its verdict,
    because the verdict was made on a render that no longer exists."""
    ids = [f"c{i}" for i in range(125)]
    raw = {c: [_atom(f"a{i}") for i in range(4)] for c in ids}
    fid = {c: {"faithful": True, "sufficient": False, "unsupported": [],
               "missing": []} for c in ids}
    block = {"by_clause_raw": raw, "annotated": list(ids), "fidelity": fid,
             "errors": []}
    out = L.recap_block(block, ids, cap_text=True)
    changed = [c for c in ids if len(out["by_clause"][c]) != 4]
    assert changed
    assert all(out["fidelity"].get(c) is None for c in changed)
    assert all(out["fidelity"].get(c) is not None
               for c in ids if c not in changed)
    assert L.rate_profile(out["by_clause"], ids)["atoms_per_clause"] <= 2.78


def test_recapping_twice_is_idempotent():
    ids = [f"c{i}" for i in range(125)]
    raw = {c: [_atom(f"a{i}") for i in range(4)] for c in ids}
    b1 = L.recap_block({"by_clause_raw": raw, "annotated": list(ids),
                        "fidelity": {}, "errors": []}, ids)
    b2 = L.recap_block(b1, ids)
    assert b1["by_clause"] == b2["by_clause"]


def test_run_ladder_keeps_the_raw_answer_alongside_the_capped_one():
    art = _offline_artifact(("0", L.NULL_ARM))
    assert "by_clause_raw" in art["rungs"]["0"]


def test_the_prompt_provenance_is_recorded_because_the_client_drops_it():
    """`providers.make_client(..., log_dir=...)` is accepted and IGNORED by
    LiveClient, so a live run writes no prompt log. Usage logging survives, so
    spend accounting is intact; provenance is not. Record a hash per call."""
    rows = rb.load_clauses()
    ids = L.sample(rows)[:2]
    vocab = L.load_vocabulary()
    client = ScriptedClient(default=None)
    _, stats, _ = L.annotate_rung(ids, rows, "1", vocab, client, attempts=1,
                                  sleep=lambda s: None)
    assert len(stats["prompt_sha256"]) == 2
    assert all(len(h) == 64 for h in stats["prompt_sha256"].values())


def test_the_raw_answer_makes_the_trim_ledger_verifiable():
    """With the budget taken over the whole sample, cap(cap(x)) == cap(x), so
    keeping the raw answer is not what stops a double trim — the full-sample
    budget is. What raw buys is auditability: `atoms_dropped` is a claim about
    the difference between what the model produced and what the judge saw, and
    without the former the claim cannot be checked."""
    ids = [f"c{i}" for i in range(125)]
    raw = {c: [_atom(f"a{i}") for i in range(4)] for c in ids}
    out = L.recap_block({"by_clause_raw": raw, "annotated": list(ids),
                         "fidelity": {}, "errors": []}, ids)
    n_raw = sum(len(v) for v in out["by_clause_raw"].values())
    n_capped = sum(len(v) for v in out["by_clause"].values())
    assert n_raw == 500
    assert n_raw - n_capped == out["cap"]["atoms_dropped"]


def test_the_role_field_is_structure_not_free_text_and_is_never_clipped():
    """`role` is a closed enum, so the rate cap must not price or trim it.

    Reported by the annotate agent, in a file it did not own: `_extras` treated
    any unknown key as free text, so `role` was PRICED against the gloss budget
    and could be clipped `"condition" -> "cond"` — silently destroying the
    condition/consequent structure the whole grammar extension exists to add,
    while the cap reported success. A four-character string is not prose and
    cannot be shortened without changing its meaning. # MUTATION-VERIFIED
    """
    assert "role" in L.BASE_FIELDS, (
        "role must be a declared base field; left out, it falls through to "
        "_extras and is charged to the free-text budget")
    atoms = {"c1": [{"name": "mustnot_x__model_user", "kind": "act",
                     "gloss": "g" * 400, "span_id": "s", "role": "condition"}]}
    capped, _ = L.enforce_rate_cap(atoms, ["c1"])
    assert capped["c1"][0]["role"] == "condition", \
        "the cap clipped a closed-enum value into a different (invalid) one"
