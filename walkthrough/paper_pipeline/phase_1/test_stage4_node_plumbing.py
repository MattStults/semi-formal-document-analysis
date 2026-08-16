"""Pins for the stage-4 plumbing the first node readback smoke mapped
(`resolve_runs/graph_v2/READBACK_SMOKE.md`).

⭐ THE LIVE SHAPE is the load-bearing pin here. Every pre-existing seat test
passes because its mock replies speak the internal denominator ids
(`concepts[0]`) — ids the live prompts never showed. The first live seat call
failed adjudication on exactly that gap, so the pin below drives `judge`
through a fake seat that replies with EXACTLY what the prompt displays,
per seat, and nothing else.

⛔ Nothing in this file spends. Every seat is driven through the
`client_factory` seam with a stub; everything else is deterministic
re-analysis of artifacts already on disk.
"""

import json
import os
import pathlib
import re
import sys
import types

import pytest

import readback
import readback_r3 as r3
import schema
import seats

HERE = pathlib.Path(__file__).resolve().parent
GRAPH_V2 = HERE / "resolve_runs" / "graph_v2"
if str(GRAPH_V2) not in sys.path:
    sys.path.insert(0, str(GRAPH_V2))


# ==========================================================================
#  fixtures — built through schema.validate(), never read off disk
# ==========================================================================

CLAUSE = (
    "Producing political content for a broad audience is permitted, provided "
    "it does not exploit the unique characteristics of a particular individual "
    "or demographic for manipulative purposes.")


def _lic(**kw):
    d = dict(licence="textual", cites="m0217", inference=None, toggleable=False)
    d.update(kw)
    return d


def _mod():
    return schema.validate(dict(
        outcome="translated", clause_id="m0217", abstain_reason=None,
        claims=["C1 political content for a broad audience is allowed",
                "C2 exploitative material is excluded"],
        acts=["produce(M)"],
        concepts=[
            _lic(name="political_content", arity=1,
                 gloss="content that concerns political topics or subjects "
                       "such as a politician, party or campaign"),
            _lic(name="broad_audience", arity=1,
                 gloss="content crafted for an unspecified or broad audience"),
            _lic(name="exploits_individual", arity=1,
                 gloss="it exploits the unique characteristics of a "
                       "particular individual or demographic for manipulative "
                       "purposes"),
        ],
        ontology=[], defines=[], beats=[], forbid_body=[], requires=[],
        inputs=["political_content/1", "broad_audience/1",
                "exploits_individual/1"],
        asserts=[_lic(
            read_back="producing % is permitted", read_back_slots=["M"],
            status="permit", act="produce(M)",
            body="political_content(M), broad_audience(M), "
                 "not exploits_individual(M)")],
        closure=[dict(act_class="produce", closure="cepa",
                      reason="the clause explicitly permits")],
    ))


def _plan():
    mod = _mod()
    rb = readback.render_module(mod, clause_quote=CLAUSE)
    return seats.plan_clause(mod, rb, clause_text=CLAUSE,
                             corpus_texts={"m0217": CLAUSE})


class Stub:
    def __init__(self, payload):
        self.payload = payload

    def complete_messages(self, system, messages):
        return json.dumps(self.payload)


# What each seat's prompt DISPLAYS as the item ids — parsed off the prompt
# text alone, because the prompt is the only thing a live seat ever sees.
_BRACKET = re.compile(r"^  \[(\w+\[\d+\]|\w+)\] ", re.M)
_4C_ITEM = re.compile(r"^  item (\S+)", re.M)


def displayed_items(seat, prompt):
    if seat in ("4a", "4b"):
        return _BRACKET.findall(prompt)
    if seat == "4c":
        return _4C_ITEM.findall(prompt)
    body = prompt.split("THE CLAIMS READ OUT OF IT", 1)[1]
    body = body.split("EVERY SENTENCE THE TRANSLATION RENDERS BACK", 1)[0]
    return [l[2:] for l in body.splitlines() if l.startswith("  ")]


# ==========================================================================
#  1 — the LIVE-SHAPED pin (READBACK_SMOKE gap 1)
# ==========================================================================

VERDICT = {"4a": "as-meant", "4b": "faithful", "4c": "licensed",
           "4d": "covered"}


@pytest.mark.parametrize("seat", seats.SEATS)
def test_LIVE_SHAPED_the_prompt_displays_the_denominator_ids(seat):
    """⭐ The prompt-visible ids ARE the validator-accepted ids, per seat."""
    plan = _plan()
    shown = displayed_items(seat, plan.prompts[seat])
    assert shown, f"{seat}: the prompt displays no item ids at all"
    assert sorted(shown) == sorted(plan.ids[seat])


@pytest.mark.parametrize("seat", seats.SEATS)
def test_LIVE_SHAPED_replying_exactly_what_the_prompt_displays_validates(seat):
    """⭐ A fake seat echoing EXACTLY what the prompt shows must adjudicate.
    This is the shape the first live call failed on: the mock-tested path
    spoke internal ids the live seat was never shown."""
    plan = _plan()
    shown = displayed_items(seat, plan.prompts[seat])
    stub = Stub({"judgements": [
        {"item": s, "verdict": VERDICT[seat], "reason": "as shown"}
        for s in shown]})
    js = seats.judge(seat, plan.prompts[seat], plan.ids[seat],
                     client_factory=lambda: stub)
    assert sorted(j.item for j in js) == sorted(plan.ids[seat])


def test_a_numeric_index_reply_maps_positionally_and_adjudicates():
    """The pre-fix prompts taught `0.`, `1.`; a stored reply in that shape
    replayed through `judge` still adjudicates, mapped to the denominator."""
    plan = _plan()
    ids = plan.ids["4b"]
    stub = Stub({"judgements": [
        {"item": str(i), "verdict": "faithful", "reason": "r"}
        for i in range(len(ids))]})
    js = seats.judge("4b", plan.prompts["4b"], ids,
                     client_factory=lambda: stub)
    assert tuple(j.item for j in js) == tuple(ids)


@pytest.mark.parametrize("seat", ["4c", "4d"])
def test_a_digit_reply_is_refused_for_seats_whose_prompts_never_taught_it(
        seat):
    """⛔ consolidated_fix_review.md F1 (2026-08-12): 4d numbers the
    SENTENCES, not the claims — mapping a digit reply positionally onto the
    claims denominator silently re-attributes every verdict to the wrong
    claim; 4c displays real item ids and numbers nothing. For both, a digit
    is NOT mapped: it fails coverage by name instead of adjudicating the
    wrong item."""
    plan = _plan()
    ids = plan.ids[seat]
    stub = Stub({"judgements": [
        {"item": str(i), "verdict": VERDICT[seat], "reason": "r"}
        for i in range(len(ids))]})
    with pytest.raises(seats.NotAdjudicated):
        seats.judge(seat, plan.prompts[seat], ids,
                    client_factory=lambda: stub)


def test_an_internal_id_reply_still_validates_mock_back_compat():
    plan = _plan()
    stub = Stub({"judgements": [
        {"item": i, "verdict": "faithful", "reason": "r"}
        for i in plan.ids["4b"]]})
    js = seats.judge("4b", plan.prompts["4b"], plan.ids["4b"],
                     client_factory=lambda: stub)
    assert sorted(j.item for j in js) == sorted(plan.ids["4b"])


def test_a_claim_with_edge_whitespace_still_adjudicates():
    """⛔ consolidated_fix_review.md F4 (2026-08-12): a `claims` sentence
    with a trailing space could never round-trip — `_reply_item` strips the
    reply, so the exact match missed FOREVER and 4d became permanently
    un-adjudicable for that clause. Stripped-to-stripped matching closes
    it; the mapped item keeps the denominator's own (unstripped) spelling."""
    ids = ("the first claim ", "the second claim")
    assert seats._reply_item("the first claim", ids) == "the first claim "
    # the guard: if stripping collides two ids, nothing is mapped
    dup = ("claim ", "claim")
    assert seats._reply_item("claim", dup) == "claim"    # exact match only
    assert seats._reply_item("claim x", dup) == "claim x"  # refused by name


#: ⭐ TWO REAL REFUSED 4d REPLIES, copied verbatim out of the first stage-4
#: baseline (`_debug_gen11/stage4_baseline/out/raw/<clause>.4d.json`). 57 of
#: 57 of that run's 4d refusals — its ENTIRE 70.4 % refusal rate — are this
#: one shape: the prompt displays the claim with its author-written label,
#: the seat replies with the claim sentence and drops the label, and
#: `_reply_item` matched neither, so every reply was NotAdjudicated. Both
#: label spellings in the corpus are represented (56 bare, 1 colon).
_REFUSED_4D = {
    # the colon spelling — and the clause of the independent dropped-content
    # finding, so this is the reply 4d must be able to give at all
    "l1_170_n056": (
        ("C1: honoring a user request is the default expectation",
         "C2: honoring a user request is forbidden when that request "
         "conflicts with a developer-level instruction"),
        ("honoring a user request is the default expectation",
         "honoring a user request is forbidden when that request conflicts "
         "with a developer-level instruction"),
    ),
    # the bare spelling, the other 56
    "l171_426_n001": (
        ("C1 the assistant must adhere to the Model Spec above all else",
         "C2 much of the Model Spec consists of default instructions at user "
         "or guideline level"),
        ("the assistant must adhere to the Model Spec above all else",
         "much of the Model Spec consists of default instructions at user or "
         "guideline level"),
    ),
}


@pytest.mark.parametrize("clause_id", sorted(_REFUSED_4D))
def test_a_stored_refused_4d_reply_now_adjudicates(clause_id):
    """RED WITHOUT THE FIX. A live 4d reply that names the claim the prompt
    displayed, minus its `C<n>` label, maps to the denominator item."""
    ids, replied = _REFUSED_4D[clause_id]
    for shown, said in zip(ids, replied):
        assert seats._reply_item(said, ids, "4d") == shown


def test_the_label_tolerance_does_not_reach_the_other_three_seats():
    """⛔ SCOPED BY SEAT, like the digit fallback. 4d is the only seat whose
    denominator is claim sentences; a de-labelled reply anywhere else is the
    seat inventing a shape it was never shown."""
    ids, replied = _REFUSED_4D["l171_426_n001"]
    for seat in ("4a", "4b", "4c", None):
        assert seats._reply_item(replied[0], ids, seat) == replied[0]


def test_an_ambiguous_de_labelled_claim_is_still_refused_by_name():
    """⚠️ PAIRED CONTROL. If two labelled claims de-label to the SAME text the
    reply names no unique item, and a tolerance that picked one would silently
    widen what counts as an answer. It is refused, exactly as the duplicate
    denominator above is."""
    dup = ("C1 the same claim", "C2 the same claim")
    assert seats._reply_item("the same claim", dup, "4d") == "the same claim"
    # and an unlabelled id is never reached by the tolerance
    mixed = ("C1 a claim", "a different claim")
    assert seats._reply_item("nothing like it", mixed, "4d") == "nothing like it"


def test_a_whole_de_labelled_4d_reply_passes_the_coverage_rule():
    """The end-to-end shape: every claim answered label-dropped adjudicates,
    through `judge`, against the real 4d denominator."""
    plan = _plan()
    ids = plan.ids["4d"]
    assert all(re.match(r"^C\d+", i) for i in ids), (
        "fixture claims must carry the author-written label this pins")
    stub = Stub({"judgements": [
        {"item": re.sub(r"^C\d+[.:)\]]?\s+", "", i), "verdict": "covered",
         "reason": "r"} for i in ids]})
    js = seats.judge("4d", plan.prompts["4d"], ids, client_factory=lambda: stub)
    assert sorted(j.item for j in js) == sorted(ids)


def test_a_hallucinated_item_is_still_refused_by_name():
    """⚠️ PAIRED CONTROL: the reply-shape tolerance must not have widened the
    coverage rule. An id matching nothing is still NOT ADJUDICATED."""
    plan = _plan()
    stub = Stub({"judgements": [
        {"item": "somewhere[9]", "verdict": "faithful", "reason": "r"}] + [
        {"item": i, "verdict": "faithful", "reason": "r"}
        for i in plan.ids["4b"]]})
    with pytest.raises(seats.NotAdjudicated):
        seats.judge("4b", plan.prompts["4b"], plan.ids["4b"],
                    client_factory=lambda: stub)


# ==========================================================================
#  2 — clause text for node-corpus rows (READBACK_SMOKE gap 3, synthesis 1)
# ==========================================================================

def _node_row(**span_over):
    import node_corpus
    span = dict(lines=[1, 2])
    span.update(span_over)
    node = {"id": "L1-10_n001", "establishes": "a claim", "provides": [],
            "needs": [], "spans": [span]}
    return node_corpus.row(node, ["alpha line one", "beta line two"])


def test_a_partially_narrowed_multi_span_node_keeps_every_span():
    """⛔ consolidated_fix_review.md F2 (2026-08-12): narrows used to win
    GLOBALLY, so a multi-span node with one narrowed span lost its
    un-narrowed spans' text entirely (5 such nodes in the live graph,
    fed to RB4/seats under full-corpus mode). Each span now contributes
    its own narrow, or its source text."""
    import node_corpus
    node = {"id": "L1-10_n001", "establishes": "a claim", "provides": [],
            "needs": [], "spans": [
                {"lines": [1, 1], "quote": "the narrowed claim"},
                {"lines": [2, 2]}]}
    row = node_corpus.row(node, ["alpha line one", "beta line two"])
    text = readback.clause_text(row)
    assert "the narrowed claim" in text
    assert "beta line two" in text          # the un-narrowed span survives
    assert "alpha line one" not in text     # the narrowed span's raw source
    assert "GRAPH NODE (" not in text       # never the packed prompt


def test_a_plain_corpus_row_returns_its_quote_verbatim():
    row = {"id": "m0217", "section_id": "s1", "quote": CLAUSE}
    assert readback.clause_text(row) == CLAUSE


def test_a_node_row_returns_the_narrowed_span_never_the_packed_prompt():
    row = _node_row(quote="the narrowed claim text")
    text = readback.clause_text(row)
    assert text == "the narrowed claim text"
    assert "GRAPH NODE" not in text and "PROVIDES" not in text


def test_a_node_row_without_a_narrow_returns_the_verbatim_span_text():
    row = _node_row()
    text = readback.clause_text(row)
    assert text == "alpha line one\nbeta line two"
    assert "SOURCE TEXT" not in text
    assert not re.search(r"L\d{4}-L\d{4}:", text)


def test_the_stored_node_corpus_never_yields_the_packed_prompt():
    """Subset check over the live artifact — no count pinned."""
    path = GRAPH_V2 / "node_corpus.json"
    if not path.is_file():
        pytest.skip("no node_corpus.json on disk")
    corpus = json.load(open(path, encoding="utf-8"))
    for row in corpus["clauses"]:
        text = readback.clause_text(row)
        assert "GRAPH NODE (" not in text, row["id"]
        assert "use EXACTLY these names" not in text, row["id"]


def test_load_corpus_quotes_goes_through_clause_text():
    """The seat driver's quote loader must use the accessor, so a node corpus
    swapped in via config can never hand a seat the packed prompt."""
    import inspect
    src = inspect.getsource(seats._load_corpus_quotes)
    assert "clause_text" in src


# ==========================================================================
#  3 — the merged concept table as the blessed gloss source (gaps 2 and 4)
# ==========================================================================

RUNS_DIR = GRAPH_V2 / "translation_sample" / "runs"
needs_sample = pytest.mark.skipif(not RUNS_DIR.is_dir(),
                                  reason="no translation_sample/runs on disk")


@needs_sample
def test_merged_gloss_is_a_bare_name_gloss_table():
    import link_nodes
    selected = link_nodes.gather()
    if not selected:
        pytest.skip("no translated node modules on disk")
    gl = link_nodes.merged_gloss(selected)
    assert gl, "the merged table glossed nothing"
    assert all("/" not in k for k in gl), "keys must be bare names, not sigs"
    assert all(isinstance(v, str) and v.strip() for v in gl.values())


@needs_sample
def test_merged_gloss_prefers_the_defining_nodes_gloss():
    """⛔ consolidated_fix_review.md F3 (2026-08-12): when several nodes
    gloss one bare name, the winner must be a node whose ASP DEFINES the
    predicate — before the fix the alphabetically-first node won, letting a
    borrower's gloss shadow the provider's (`stay_in_bounds_principles`
    live). Subset check over the live sample, no counts pinned."""
    import link_nodes
    sys_link = link_nodes.link
    selected = link_nodes.gather()
    if not selected:
        pytest.skip("no translated node modules on disk")
    definers = {}
    glosses = {}
    for r in link_nodes.merged_concepts(selected):
        name = str(r["concept"]).split("/")[0]
        nid = link_nodes.norm_id(str(r.get("clause_id") or ""))
        glosses.setdefault(name, {})[nid] = r["gloss"]
    for nid, (lp, _o, _r) in selected.items():
        for sig in sys_link.defined_predicates(
                open(lp, encoding="utf-8").read()):
            definers.setdefault(sig.split("/")[0], set()).add(nid)
    gl = link_nodes.merged_gloss(selected)
    checked = 0
    for name, by_node in glosses.items():
        defs = definers.get(name, set()) & set(by_node)
        if len(by_node) > 1 and defs:
            assert gl[name] in {by_node[n] for n in defs}, name
            checked += 1
    assert checked, "no multi-gloss defined name in the sample to check"


@needs_sample
def test_merged_gloss_feeds_render_module_as_extra_gloss():
    """The dict plugs straight into the render path — the smoke's exact call
    shape, now off the blessed accessor instead of a hand-rolled one."""
    import link_nodes
    selected = link_nodes.gather()
    if not selected:
        pytest.skip("no translated node modules on disk")
    gl = link_nodes.merged_gloss(selected)
    rb = readback.render_module(_mod(), extra_gloss=gl, clause_quote=CLAUSE)
    assert rb.outcome == "rendered"


@needs_sample
def test_provider_texts_returns_span_texts_never_packed_prompts():
    import link_nodes
    selected = link_nodes.gather()
    if not selected:
        pytest.skip("no translated node modules on disk")
    texts = link_nodes.node_clause_texts()
    resolution = link_nodes.requires_resolution(selected)
    for nid in selected:
        xrefs = link_nodes.provider_texts(nid, selected, texts, resolution)
        assert isinstance(xrefs, tuple)
        for t in xrefs:
            assert "GRAPH NODE (" not in t
        # a module whose requires all dangle in-corpus has no provider text
        per = resolution["per_module"].get(nid, {})
        if not per.get("resolved"):
            assert xrefs == ()


# ==========================================================================
#  4 — link-scope hygiene at readback scope (READBACK_SMOKE gap 5)
# ==========================================================================

LINK_TEXT = ("#const onto = on.\n"
             "o :- onto = on.\n"
             '%!trace_rule {"a helper rule"}.\n'
             "helper(x) :- o.\n"
             "%!show_trace {asserts(P,D,A)}.\n"
             "%!show_trace {beats(S,W,L)}.")


def test_shared_preamble_is_deduped_to_one_copy_across_the_link_scope():
    out = r3.hygienic_link_texts([("a.lp", LINK_TEXT), ("b.lp", LINK_TEXT)])
    blob = "\n".join(t for _n, t in out)
    assert blob.count("#const onto = on.") == 1
    assert blob.count("o :- onto = on.") == 1
    # both files' rules survive
    assert blob.count("helper(x) :- o.") == 2


def test_stored_show_trace_directives_are_stripped_and_trace_rules_kept():
    out = r3.hygienic_link_texts([("a.lp", LINK_TEXT)])
    blob = out[0][1]
    assert "%!show_trace" not in blob
    assert '%!trace_rule {"a helper rule"}.' in blob


def test_only_the_exact_shared_preamble_is_deduped():
    """⛔ Any OTHER `#const` collision must survive to error in clingo — a
    silently deduped constant is a rewrite of someone's program."""
    out = r3.hygienic_link_texts([("a.lp", "#const k = 1."),
                                  ("b.lp", "#const k = 1.")])
    blob = "\n".join(t for _n, t in out)
    assert blob.count("#const k = 1.") == 2


def test_render_r3_runs_exactly_one_show_trace_over_a_deduped_scope(
        monkeypatch):
    """⭐ INTEGRATION: the program xclingo actually receives carries ONE copy
    of the shared preamble and ONLY R3's own `%!show_trace` — with two stored
    link modules each contributing both shapes."""
    captured = {}

    def fake_run(text, xclingo=None, timeout=120):
        captured["text"] = text
        raise r3.R3Error("captured the program before any solver ran")

    monkeypatch.setattr(r3, "run_xclingo", fake_run)
    sit = types.SimpleNamespace(
        id="S0",
        true_atoms=("political_content(m1)", "broad_audience(m1)"),
        derived=("asserts(m0217,permit,produce(m1))",))
    with pytest.raises(r3.R3Error):
        r3.render_r3(_mod(), [sit],
                     link_texts=[("n.lp", LINK_TEXT), ("m.lp", LINK_TEXT)])
    text = captured["text"]
    assert text.count("#const onto = on.") == 1
    shows = [l.strip() for l in text.splitlines()
             if l.strip().startswith("%!show_trace")]
    assert shows == ["%!show_trace {asserts(m0217,permit,produce(m1))}."]
