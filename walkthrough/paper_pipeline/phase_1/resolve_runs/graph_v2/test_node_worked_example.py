"""node_worked_example.md must survive stage 2 against the NODE corpus.

Mirror of phase_1/test_prompt_examples.py for the graph-node pipeline: every
good example is validated by the same checks the model's real replies face
(an example that would fail our own checks teaches the failure as acceptable,
in the most credible form available). The good/bad split is the
'## The five bad ones' heading, same shape-matched regex as phase_1's.
"""
import json
import os
import re
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (HERE, PHASE1):
    if p not in sys.path:
        sys.path.insert(0, p)

import checks  # noqa: E402
import schema as S  # noqa: E402

WORKED = os.path.join(HERE, "node_worked_example.md")
BAD_HEADING_RE = re.compile(r"^##\s+The\s+\w+\s+bad\s+ones\s*$", re.M | re.I)


def _good_region():
    text = open(WORKED, encoding="utf-8").read()
    m = BAD_HEADING_RE.search(text)
    return text[:m.start()] if m else text


def _modules(text):
    out = []
    for m in re.finditer(r"```json\n(.*?)```", text, re.S):
        try:
            obj = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "clause_id" in obj and "outcome" in obj:
            out.append(obj)
    return out


@pytest.fixture(scope="module")
def corpus():
    rows = json.load(open(os.path.join(HERE, "node_corpus.json")))["clauses"]
    return {c["id"]: c for c in rows}


def _good_modules():
    return _modules(_good_region())


def test_the_bad_examples_heading_still_exists():
    assert BAD_HEADING_RE.search(open(WORKED, encoding="utf-8").read())


def test_there_are_good_modules_to_check():
    assert len(_good_modules()) >= 4


@pytest.mark.parametrize("obj", _good_modules(),
                         ids=[m["clause_id"] for m in _good_modules()])
def test_a_good_worked_example_passes_stage_2(obj, corpus):
    cid = obj["clause_id"]
    assert cid in corpus, (
        f"the worked example cites {cid}, which is not in node_corpus.json; "
        f"regenerate the corpus or fix the example")
    res = checks.run_checks(obj, corpus[cid], set(corpus), attempt=1)
    errors = [f for f in res.findings if f.severity == "error"]
    assert not errors, "\n".join(
        f"[{f.check_id}] {f.where}: {f.message}" for f in errors)
    assert res.outcome == obj["outcome"], (
        f"{cid} is shown as {obj['outcome']} but stage 2 calls it "
        f"{res.outcome}")


def test_translated_examples_render_to_loadable_asp(corpus):
    for obj in _good_modules():
        if obj["outcome"] != "translated":
            continue
        cid = obj["clause_id"]
        mod, breaches = S.validate_all(obj, cid, set(corpus))
        assert mod is not None, f"{cid}: " + "; ".join(
            b.message for b in breaches)
        assert S.render_lp(mod, corpus[cid]).strip(), f"{cid} rendered empty"


def test_conditional_ontology_and_repeated_atom_are_demonstrated():
    entries = [e for m in _good_modules() for e in (m.get("ontology") or [])]
    conditional = [e for e in entries if (e.get("body") or "").strip()]
    assert len(conditional) >= 3
    heads = [e["atom"].split("(")[0].strip() for e in conditional]
    assert len(heads) != len(set(heads)), (
        "no repeated atom with different bodies; alternatives undemonstrated")


def test_requires_and_inputs_are_shown_together_and_abstention_is_shown():
    mods = _good_modules()
    assert any(m.get("requires") and m.get("inputs") for m in mods)
    assert any(m["outcome"] == "abstained" for m in mods)


def test_needs_names_are_required_verbatim(corpus):
    """The adapter's core contract: the flagship example's requires carries
    the node's NEEDS names exactly (with a chosen arity)."""
    flagship = next(m for m in _good_modules()
                    if m["clause_id"] == "l527_796_n012")
    req_names = {r.split("/")[0] for r in flagship["requires"]}
    assert req_names == {"authority_levels_hierarchy", "best_intentions_bias"}


def test_full_corpus_mode_covers_every_node_and_sample_is_unchanged():
    """`node_corpus.py --all` must emit one row per graph node; the DEFAULT
    selection must stay exactly the 15-sample already on disk (no count pin
    on the live graph -- the graph may grow; the pin is row count == node
    count, plus the frozen sample ids)."""
    import node_corpus as NC

    g = json.load(open(NC.GRAPH))
    all_ids = NC.select_ids(g, all_nodes=True)
    assert len(all_ids) == len(g["nodes"])
    assert len(set(all_ids)) == len(all_ids), "duplicate node ids in --all"

    default_ids = NC.select_ids(g)
    assert len(default_ids) == 15
    on_disk = [c["id"] for c in
               json.load(open(os.path.join(HERE, "node_corpus.json")))["clauses"]]
    assert [NC.asp_id(i) for i in default_ids] == on_disk, (
        "the default sample no longer matches the checked-in node_corpus.json")
