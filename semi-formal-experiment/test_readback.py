"""Tests for the READ-BACK validity test.

The thing under test is not a scorer, so the usual "does the number go up"
tests do not apply. What has to be guarded here is different and, for this
experiment, load-bearing:

  1. the renderer is MECHANICAL — no model, no network, no file, no randomness,
     and a total function of the atom fields it declares it reads;
  2. the renderer does not SMUGGLE the document — it may not reproduce the
     source wording it is supposed to be a lossy projection of, or the whole
     measurement is a copy test;
  3. the discrimination harness cannot SEE its own answer — the prompt must be
     a function of (render, ordered candidate texts) and nothing else, and the
     order must be seeded and recorded;
  4. the stratification is REAL — equal cells per clause kind, deterministic;
  5. NOTHING in the pipeline touches the panel. This is a document-grounded
     validity test; its entire value is independence from the relevance task.
"""
from __future__ import annotations

import builtins
import io
import json
import os
import re

import pytest

import readback as rb

HERE = os.path.dirname(os.path.abspath(__file__))
ANN = os.path.join(HERE, "annotations_b8.json")
CLAUSES = os.path.join(HERE, "modelspec_clauses.json")

pytestmark = pytest.mark.skipif(
    not (os.path.exists(ANN) and os.path.exists(CLAUSES)),
    reason="real artifacts not present")


# --------------------------------------------------------------------------
# fixtures

@pytest.fixture(scope="module")
def rows():
    return rb.load_clauses(CLAUSES)


@pytest.fixture(scope="module")
def ann():
    return rb.load_annotations(ANN)


ATOMS = [
    {"name": "ambiguous_request", "kind": "situation",
     "gloss": "A request whose intent is unclear.", "span_id": "s1",
     "quote": "If the request is ambiguous", "clause_id": "m0100",
     "locator": "spec > A > 1"},
    {"name": "ask_clarifying_question", "kind": "act",
     "gloss": "Asking the user what they meant.", "span_id": "s1",
     "quote": "If the request is ambiguous", "clause_id": "m0100",
     "locator": "spec > A > 1"},
    {"name": "user_autonomy", "kind": "value",
     "gloss": "Leaving the choice with the user.", "span_id": "s4",
     "quote": "the assistant should ask", "clause_id": "m0100",
     "locator": "spec > A > 1"},
]


# --------------------------------------------------------------------------
# 1. the renderer is mechanical

def test_render_is_deterministic():
    a = rb.render(ATOMS, clause_kind="conditional")
    b = rb.render(ATOMS, clause_kind="conditional")
    assert a == b and isinstance(a, str) and a.strip()


def test_render_opens_no_file_and_calls_no_model(rows, ann, monkeypatch):
    """A model doing the read-back fills gaps from its own knowledge of what
    model specs say. That is the failure this whole design exists to avoid, so
    it is asserted mechanically rather than promised in a docstring."""
    import urllib.request

    import providers

    def boom(*a, **k):
        raise AssertionError("render() reached the network")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    monkeypatch.setattr(providers.LiveClient, "complete", boom)
    monkeypatch.setattr(providers.LiveClient, "complete_envelope", boom)

    opened = []
    saved = (builtins.open, io.open, os.open)

    def mk(real):
        def spy(path, *a, **k):
            opened.append(str(path))
            return real(path, *a, **k)
        return spy

    builtins.open, io.open, os.open = mk(saved[0]), mk(saved[1]), mk(saved[2])
    try:
        for cid in list(ann)[:120]:
            rb.render(ann[cid], clause_kind="conditional")
    finally:
        builtins.open, io.open, os.open = saved

    assert not opened, f"render() opened files: {sorted(set(opened))[:5]}"


@pytest.mark.parametrize("field", ["name", "kind", "gloss", "span_id"])
def test_render_is_total_over_every_field_it_reads(field):
    """A dropped or altered field MUST change the output. If it does not, the
    render is not expressing everything the ontology holds, and every
    downstream number is measuring a smaller object than the one under test."""
    assert field in rb.RENDERED_FIELDS

    dropped = [{k: v for k, v in a.items() if k != field} for a in ATOMS]
    altered = [dict(a) for a in ATOMS]
    altered[0][field] = "s9" if field == "span_id" else (
        "value" if field == "kind" else "ZZZ_changed")

    base = rb.render(ATOMS, clause_kind="conditional")
    assert rb.render(dropped, clause_kind="conditional") != base, (
        f"dropping {field!r} left the render unchanged")
    assert rb.render(altered, clause_kind="conditional") != base, (
        f"altering {field!r} left the render unchanged")


def test_clause_kind_is_part_of_the_render():
    assert (rb.render(ATOMS, clause_kind="conditional")
            != rb.render(ATOMS, clause_kind="example"))


@pytest.mark.parametrize("field", ["quote", "locator", "clause_id"])
def test_render_ignores_the_source_text_fields_by_design(field):
    """`quote` is verbatim document text and `locator` is its address. Putting
    either in the render would make the read-back a copy of the document rather
    than a projection of the ontology, and discrimination would be trivially
    perfect. Excluded ON PURPOSE — and asserted, so a later edit that "improves
    discriminability" by leaking the source has to delete a test to do it."""
    assert field in rb.IGNORED_FIELDS
    altered = [dict(a) for a in ATOMS]
    altered[0][field] = "COMPLETELY DIFFERENT TEXT 12345"
    assert (rb.render(altered, clause_kind="conditional")
            == rb.render(ATOMS, clause_kind="conditional"))


def test_render_never_reproduces_a_source_span(rows, ann):
    """No atom's verbatim `quote` may appear in its own render."""
    by_id = {r["id"]: r for r in rows}
    for cid, atoms in ann.items():
        text = rb.render(atoms, clause_kind=by_id.get(cid, {}).get("kind"))
        for a in atoms:
            q = (a.get("quote") or "").strip()
            if len(q) > 25:
                assert q not in text, f"{cid}: render reproduces a source span"


def test_render_adds_no_source_wording_of_its_own(rows, ann):
    """The renderer's TEMPLATE may not carry document wording.

    It is not true that a render shares no long shingle with its clause — a
    couple of clauses have a GLOSS that copies the source (see `gloss_echo`,
    measured at 0.3% of the corpus, so it is a caveat and not a leak). That is
    the annotator's doing and is genuine ontology content, so it is measured
    and reported, not asserted away. What must hold is narrower and is the
    thing actually under this module's control: every shingle a render shares
    with its clause comes from an atom's own name or gloss, never from the
    fixed template."""
    by_id = {r["id"]: r for r in rows}
    for cid, atoms in list(ann.items())[:250]:
        text = rb.render(atoms, clause_kind=by_id.get(cid, {}).get("kind"))
        atom_text = " ".join(f"{a.get('name','')} {a.get('gloss','')}"
                             for a in atoms).lower()
        words = re.findall(r"[A-Za-z']+", by_id.get(cid, {}).get("quote", ""))
        low = text.lower()
        for i in range(len(words) - 7):
            sh = " ".join(w.lower() for w in words[i:i + 8])
            if sh in low:
                assert sh in atom_text or sh.replace("_", " ") in atom_text, (
                    f"{cid}: the TEMPLATE carries document wording: {sh!r}")


def test_gloss_echo_is_measured(rows, ann):
    """The caveat has to be a number in the artifact, not a footnote."""
    e = rb.gloss_echo(rows, ann)
    assert 0 <= e["rate"] <= 1 and e["n"] == len(rows)
    assert e["clauses_with_echo"] == round(e["rate"] * e["n"])
    assert isinstance(e["examples"], list)


def test_render_states_every_atom(rows, ann):
    for cid, atoms in list(ann.items())[:150]:
        text = rb.render(atoms)
        for a in atoms:
            assert a["name"] in text
            assert a["gloss"].rstrip(".") in text


def test_render_is_total_on_empty_atoms():
    out = rb.render([], clause_kind="example")
    assert isinstance(out, str) and out.strip()
    assert out != rb.render([], clause_kind="meta")


# --------------------------------------------------------------------------
# 2. stratification is real

def test_stratified_sample_has_equal_real_cells(rows):
    ids = rb.stratified_sample(rows, per_kind=25, seed=7)
    by_id = {r["id"]: r for r in rows}
    kinds = {}
    for cid in ids:
        kinds[by_id[cid]["kind"]] = kinds.get(by_id[cid]["kind"], 0) + 1
    assert set(kinds) == set(rb.CLAUSE_KINDS)
    assert set(kinds.values()) == {25}
    assert len(set(ids)) == len(ids) == 125


def test_stratified_sample_is_seeded():
    r = rb.load_clauses(CLAUSES)
    assert rb.stratified_sample(r, 25, seed=7) == rb.stratified_sample(r, 25, seed=7)
    assert rb.stratified_sample(r, 25, seed=7) != rb.stratified_sample(r, 25, seed=8)


# --------------------------------------------------------------------------
# 3. the discrimination harness cannot see its answer

@pytest.fixture(scope="module")
def trials(rows, ann):
    ids = rb.stratified_sample(rows, per_kind=6, seed=11)
    return rb.build_trials(ids, rows, ann, n_candidates=4,
                           mode="section", seed=11)


def test_trial_answer_index_is_recorded_and_correct(trials):
    for t in trials:
        assert t["candidate_ids"][t["answer_index"]] == t["clause_id"]
        assert len(set(t["candidate_ids"])) == t["n_candidates"]


def test_prompt_is_a_function_of_render_and_ordered_candidates_only(trials):
    """THE LEAK TEST. If the prompt changes when only the recorded answer
    changes, the answer is reaching the model."""
    for t in trials[:8]:
        lied = dict(t)
        lied["answer_index"] = (t["answer_index"] + 1) % t["n_candidates"]
        lied["clause_id"] = t["candidate_ids"][lied["answer_index"]]
        assert rb.discrim_prompt([lied]) == rb.discrim_prompt([t])


def test_prompt_names_no_clause_id(trials):
    sys_, usr = rb.discrim_prompt(trials[:5])
    blob = sys_ + usr
    for t in trials[:5]:
        for cid in t["candidate_ids"]:
            assert cid not in blob, "a clause id reached the prompt"


def test_candidate_order_is_seeded_and_reproducible(rows, ann):
    ids = rb.stratified_sample(rows, per_kind=6, seed=11)
    a = rb.build_trials(ids, rows, ann, 4, "section", seed=11)
    b = rb.build_trials(ids, rows, ann, 4, "section", seed=11)
    c = rb.build_trials(ids, rows, ann, 4, "section", seed=12)
    assert [t["candidate_ids"] for t in a] == [t["candidate_ids"] for t in b]
    assert [t["candidate_ids"] for t in a] != [t["candidate_ids"] for t in c]
    assert all(t["seed"] == 11 for t in a)


def test_answer_positions_are_spread_not_pinned(rows, ann):
    ids = rb.stratified_sample(rows, per_kind=25, seed=3)
    ts = rb.build_trials(ids, rows, ann, 4, "random", seed=3)
    counts = [sum(1 for t in ts if t["answer_index"] == i) for i in range(4)]
    assert min(counts) > 0.5 * len(ts) / 4, f"answer position not spread: {counts}"


def test_distractors_are_drawn_from_the_declared_pool(rows, ann):
    by_id = {r["id"]: r for r in rows}
    ids = rb.stratified_sample(rows, per_kind=10, seed=5)
    for t in rb.build_trials(ids, rows, ann, 4, "section", seed=5):
        if t["pool"] != "section":
            continue
        sect = by_id[t["clause_id"]]["section_id"]
        for cid in t["candidate_ids"]:
            assert by_id[cid]["section_id"] == sect
    for t in rb.build_trials(ids, rows, ann, 4, "random", seed=5):
        assert t["pool"] == "random"
        assert t["clause_id"] in t["candidate_ids"]


def test_parse_discrim_rejects_out_of_range_and_missing(trials):
    batch = trials[:3]
    good = json.dumps([{"item": 1, "choice": 2}, {"item": 2, "choice": 1},
                       {"item": 3, "choice": 99}])
    got, errs = rb.parse_discrim(good, batch)
    assert got[0] == 1 and got[1] == 0        # 1-based in, 0-based out
    assert got[2] is None and errs             # out of range is not an answer


# --------------------------------------------------------------------------
# 4. offline pipeline touches nothing it did not declare

def test_offline_pipeline_opens_only_declared_artifacts():
    allowed = {"annotations_b8.json", "modelspec_clauses.json",
               "readback_prompt.md", "providers.json"}
    opened = []
    saved = (builtins.open, io.open, os.open)

    def mk(real):
        def spy(path, *a, **k):
            opened.append(os.path.abspath(str(path)))
            return real(path, *a, **k)
        return spy

    builtins.open, io.open, os.open = mk(saved[0]), mk(saved[1]), mk(saved[2])
    try:
        r = rb.load_clauses(CLAUSES)
        a = rb.load_annotations(ANN)
        ids = rb.stratified_sample(r, 5, seed=1)
        ts = rb.build_trials(ids, r, a, 4, "random", seed=1)
        rb.discrim_prompt(ts[:2])
        rb.fidelity_prompt(ts[:2])
        rb.equivalence_profile(r, a)
    finally:
        builtins.open, io.open, os.open = saved

    bad = [p for p in opened
           if os.path.basename(p) not in allowed
           and not p.endswith((".py", ".pyc", ".ini", ".cfg", ".txt"))
           and "/site-packages/" not in p and "/lib/python" not in p]
    assert not bad, f"undeclared artifact opened: {sorted(set(bad))}"


def test_source_never_names_the_panel():
    """Kept in sync with the repo's anti-cheat list by importing it, so this
    does not rot into a private copy that misses the next laundering path."""
    import test_no_reference_leak as leak
    src = open(os.path.join(HERE, "readback.py")).read()
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"#.*", "", src)
    hits = [tok for tok in leak.FORBIDDEN if tok in src]
    assert not hits, f"readback.py names the reference: {hits}"


def test_prompt_template_never_names_the_panel():
    src = open(os.path.join(HERE, "readback_prompt.md")).read()
    for tok in ("behaviour", "behavior", "panel", "relevan"):
        assert tok not in src.lower(), (
            f"readback_prompt.md mentions {tok!r} — this is a document-grounded "
            "test and must not know the relevance task exists")


# --------------------------------------------------------------------------
# 5. the ceiling and the statistics

def test_equivalence_profile_matches_a_recount(rows, ann):
    prof = rb.equivalence_profile(rows, ann)
    seen = {}
    for r in rows:
        seen.setdefault(frozenset(a["name"] for a in ann.get(r["id"], [])),
                        []).append(r["id"])
    assert prof["classes"] == len(seen)
    assert prof["n"] == len(rows)
    assert abs(prof["identity_ceiling"] - len(seen) / len(rows)) < 1e-12
    assert prof["collision_profile"]["1"] == sum(1 for v in seen.values() if len(v) == 1)


def test_trial_records_whether_a_twin_is_present(rows, ann):
    """The 534/589 ceiling is a WHOLE-CORPUS figure. Inside a 4-candidate
    trial it almost never binds, so the trial-conditional ceiling is what a
    measured accuracy must be read against."""
    ids = rb.stratified_sample(rows, 10, seed=2)
    ts = rb.build_trials(ids, rows, ann, 4, "section", seed=2)
    assert all("identity_collision" in t for t in ts)
    sigs = {r["id"]: frozenset(a["name"] for a in ann.get(r["id"], []))
            for r in rows}
    for t in ts:
        twin = any(sigs[c] == sigs[t["clause_id"]]
                   for c in t["candidate_ids"] if c != t["clause_id"])
        assert t["identity_collision"] is twin


def test_wilson_interval():
    lo, hi = rb.wilson(8, 10)
    assert 0.4 < lo < 0.55 and 0.93 < hi <= 1.0
    lo, hi = rb.wilson(0, 10)
    assert lo == 0.0 and 0.2 < hi < 0.4
    assert rb.wilson(0, 0) == (0.0, 1.0)


# --------------------------------------------------------------------------
# 6. guard compatibility: the module must be drivable by the anti-cheat spy

def test_index_exposes_a_drivable_query_surface(rows, ann):
    idx = rb.Index(rows, ann)
    out = idx.sweep(object())          # the guard passes an unrelated query
    assert len(list(out)) == len(rows)
    assert isinstance(idx.render_clause(rows[0]["id"]), str)


# ---------------------------------------------------------------- coverage
# THE DEFECT THIS SECTION EXISTS FOR. The 2026-08-02 run lost 52 of 125 calls
# to rate limits; one condition sat at 90/125 (28% missing, concentrated in
# whole clause-kind strata because batches are contiguous slices of a
# kind-sorted sample) and `summarize()` reported `"unanswered": 0`.
#
# Mechanism: a raised call yields `parsed is None` -> `continue` -> the whole
# batch never enters `results`. `unanswered` then counts `None` values AMONG
# CLAUSE IDS PRESENT, so a lost batch is invisible and every rate's
# denominator silently shrinks. That moves a reported number further than the
# effect the instrument is trying to measure.

def _artifact_missing_a_batch():
    """A 10-clause artifact where 2 clauses were never answered at all."""
    ids = [f"m{i:04d}" for i in range(10)]
    trial = lambda c: {"clause_id": c, "clause_kind": "meta",
                       "section_id": "s", "answer_index": 0,
                       "identity_collision": False, "kind_alone_solves": False,
                       "candidate_ids": [c]}
    return {
        "clause_ids": ids,
        "ceiling": {"identity_ceiling": 1.0},
        "trials": {"random_N4": [trial(c) for c in ids]},
        "fidelity_trials": [trial(c) for c in ids],
        "results": {
            # 8 of 10 present: m0008 and m0009 were lost with their batch
            "discrim": {"random_N4": {c: 0 for c in ids[:8]}},
            "fidelity": {c: {"faithful": True, "sufficient": True}
                         for c in ids[:8]},
        },
    }


def test_summarize_reports_unanswered_against_the_DECLARED_sample():
    """Counting `None`s among present keys cannot see a lost batch.

    The denominator must be `clause_ids` — what we set out to ask — not
    `results` — what came back. # MUTATION-VERIFIED
    """
    d = rb.summarize(_artifact_missing_a_batch())
    block = d["discrim"]["random_N4"]
    assert block["unanswered"] == 2, (
        "a whole lost batch is invisible: `unanswered` counted None values "
        "among the clause ids that came BACK, so 2 clauses that were never "
        "answered at all report as 0 unanswered")


def test_summarize_reports_coverage_so_a_short_pass_cannot_pass_silently():
    """Fidelity had NO coverage number at all — its denominator was
    `len(vals)` inside `_rate`, so a short fidelity pass shrank n with no
    trace in the artifact. # MUTATION-VERIFIED"""
    d = rb.summarize(_artifact_missing_a_batch())
    assert d["fidelity"]["coverage"] == (8, 10), \
        "fidelity must state answered/declared, not just a rate"
    assert d["discrim"]["random_N4"]["coverage"] == (8, 10)
