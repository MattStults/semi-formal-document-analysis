"""node_worked_example.md must survive stage 2 against the NODE corpus.

Mirror of phase_1/test_prompt_examples.py for the graph-node pipeline: every
good example is validated by the same checks the model's real replies face
(an example that would fail our own checks teaches the failure as acceptable,
in the most credible form available). The good/bad split is the
'## The N bad ones' heading, same shape-matched regex as phase_1's -- the
count in the heading is deliberately NOT pinned, only its shape.
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


def _contract_block(quote, label):
    """The `- name: gloss` names inside one block of a node's contract.

    `label` is "PROVIDES" or "NEEDS". A block with no entries renders as
    `  (none)` and yields the empty set.
    """
    if label == "PROVIDES":
        m = re.search(r"^PROVIDES \(.*?\):\n(.*?)\n\nNEEDS", quote, re.S | re.M)
    else:
        m = re.search(r"^NEEDS --.*?:\n(.*?)\n\nCITATION", quote, re.S | re.M)
    assert m, f"no {label} block in the node contract; the corpus format moved"
    return {ln.strip()[2:].split(":")[0].strip()
            for ln in m.group(1).splitlines() if ln.strip().startswith("- ")}


def test_needs_names_are_required_verbatim(corpus):
    """The adapter's core contract: the flagship example's requires carries
    the node's NEEDS names exactly (with a chosen arity)."""
    flagship = next(m for m in _good_modules()
                    if m["clause_id"] == "l527_796_n012")
    req_names = {r.split("/")[0] for r in flagship["requires"]}
    assert req_names == {"authority_levels_hierarchy", "best_intentions_bias"}


def test_every_translated_example_requires_exactly_its_needs(corpus):
    """Contract 2 of the file, checked on EVERY translated example, not only
    the flagship.

    Both directions, and each has cost us a demonstration that taught the
    opposite of the prose:

    * NEEDS -> `requires`. `l4251_4571_n029` shipped `"requires": []` while
      its contract carried `NEEDS: voice_turn_taking_rule` -- failure mode #2
      (missing cross-reference), demonstrated in the file that forbids it.
    * `requires` -> NEEDS. `l3995_4164_n001` shipped
      `"requires": ["rule_under_heading/2"]` for a node whose NEEDS is
      *(none)*, so the rule's body waited on a definition no node supplies and
      the head derived nothing -- failure mode #3 (a rule that can never fire).
      A name the NEEDS block does not list is either this module's own or a
      fact about the case; it is not something to borrow.

    Abstentions are excluded by contract: an abstention carries every list
    empty, and that rule wins over this one.
    """
    for obj in _good_modules():
        if obj["outcome"] != "translated":
            continue
        cid = obj["clause_id"]
        needs = _contract_block(corpus[cid]["quote"], "NEEDS")
        req = {r.split("/")[0] for r in obj["requires"]}
        assert req == needs, (
            f"{cid}: `requires` names {sorted(req)} but the node's NEEDS block "
            f"is {sorted(needs)}. Missing names are failure mode #2; extra "
            f"names are failure mode #3 -- a body waiting on a provider that "
            f"does not exist.")


def test_a_provides_name_is_actually_made_derivable(corpus):
    """A node's PROVIDES is a promise other nodes are waiting on.

    `l3995_4164_n001` PROVIDES `guideline_authority` and many nodes NEED it.
    A translated module for a providing node must put that predicate at the
    HEAD of an ontology entry -- naming it in `concepts` only declares what it
    would mean, and derives nothing.
    """
    checked = 0
    for obj in _good_modules():
        if obj["outcome"] != "translated":
            continue
        cid = obj["clause_id"]
        provides = _contract_block(corpus[cid]["quote"], "PROVIDES")
        if not provides:
            continue
        heads = {e["atom"].split("(")[0].strip()
                 for e in (obj.get("ontology") or [])}
        heads |= {d.get("name") for d in (obj.get("defines") or [])}
        missing = provides - heads
        assert not missing, (
            f"{cid} promises {sorted(missing)} in PROVIDES and no ontology "
            f"entry derives it; every node NEEDing the name gets nothing")
        checked += 1
    assert checked, "no providing node is demonstrated at all"


def test_the_structural_fact_route_is_demonstrated():
    """Finding 2's resolution, pinned.

    The file offers three routes, not two: a norm goes to `asserts`, a
    structural fact goes to `ontology` with `asserts` empty, and only a node
    establishing neither abstains. If the middle route stops being
    demonstrated, "establishes no obligation" collapses back into "abstain"
    and heading nodes stop providing the authority 100+ nodes borrow.
    """
    mods = _good_modules()
    structural = [m for m in mods
                  if m["outcome"] == "translated"
                  and not m.get("asserts")
                  and (m.get("ontology") or [])]
    assert structural, (
        "no translated example with an empty `asserts` and a non-empty "
        "`ontology`; the structural-fact route is undemonstrated")


def test_exemplar_ids_exist_in_the_corpus_the_config_runs():
    """Finding 4, pinned as a RELATION and never as a count.

    `node_worked_example.md:5` makes a claim about its exemplars, and the
    claim went false once without anything noticing: the review found all four
    ids absent from `node_corpus_all.json` (they had been re-segmented), while
    this test file read the frozen fixture and passed blind.

    So the pin is: for the config that actually SHIPS this file as system
    prompt (`config_graph_nodes.json`), every exemplar `clause_id` resolves in
    the corpus that config points at -- whichever corpus that is, and however
    many rows it has. Repoint the config at a corpus the exemplars are not in
    and this fails, which is the failure the file's line 5 describes.

    It does NOT pin which corpus, a row count, or the ids themselves; the
    sample is free to move as long as the file moves with it.
    """
    cfg_path = os.path.join(HERE, "config_graph_nodes.json")
    cfg = json.load(open(cfg_path))
    corpus_path = os.path.join(os.path.dirname(cfg_path),
                               cfg["corpus"]["path"])
    ids = {c["id"] for c in json.load(open(corpus_path))["clauses"]}
    missing = sorted(m["clause_id"] for m in _good_modules()
                     if m["clause_id"] not in ids)
    assert not missing, (
        f"{missing} are shown as worked examples but are not in "
        f"{cfg['corpus']['path']}, the corpus config_graph_nodes.json runs. "
        f"Either the exemplars or the file's line-5 claim about them is "
        f"stale -- the segmentation moved and the file did not.")


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
