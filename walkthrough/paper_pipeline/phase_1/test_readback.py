"""Tests for the stage-4 read-back renderer.

⭐ The load-bearing property is TOTALITY (`STEP_stage4.md` §2, Matt's ruling):
**no ASP construct may be inadmissible.** Every test that hands the renderer an
exotic construct is asserting that it gets a rendering back, never an error and
never a refusal. A construct with no fluent template falls back to layer 1 —
its own source form with every predicate name replaced by its gloss.

⚠️ Fixtures here are built inline, not read from `runs/`. `DEBUGGING_TIPS.md` §9:
never pin the content of a live artifact. The real-corpus tests below are written
as PROPERTIES over whatever modules happen to validate today, and skip cleanly
when none do — they never assert a count.
"""

import json
import pathlib

import pytest

import readback
import schema

HERE = pathlib.Path(__file__).resolve().parent
RUNS = HERE / "runs"
WALKTHROUGH = HERE.parent.parent
CORPUS = HERE / ".." / ".." / ".." / "semi-formal-experiment" / "modelspec_clauses.json"


# ==========================================================================
#  fixtures
# ==========================================================================

def _mod(**over):
    """A minimal valid module dict, overridable field by field."""
    base = dict(
        outcome="translated", clause_id="m0217", abstain_reason=None,
        claims=["C1 a claim"], acts=[], concepts=[], ontology=[],
        asserts=[], beats=[], defines=[], closure=[],
        requires=[], inputs=[], forbid_body=[],
    )
    base.update(over)
    return schema.validate(base)


def _concept(name, gloss, arity=1):
    return dict(name=name, arity=arity, gloss=gloss, licence="textual",
                cites="m0217", inference=None, toggleable=False)


def _lic(**kw):
    d = dict(licence="textual", cites="m0217", inference=None, toggleable=False)
    d.update(kw)
    return d


def m0217_patched():
    """§3a's example, patched to the current schema.

    The file on disk carries the old `read_back_args` field and declares no
    provider for its body predicates, so it does not validate. Rebuilt here so
    the test does not depend on a run directory.
    """
    return _mod(
        clause_id="m0217",
        claims=["C1 political content for a broad audience is allowed"],
        acts=["produce(M)"],
        concepts=[
            _concept("political_content",
                     "content that concerns political topics or subjects such "
                     "as a politician, party or campaign"),
            _concept("broad_audience",
                     "content crafted for an unspecified or broad audience"),
            _concept("exploits_individual",
                     "it exploits the unique characteristics of a particular "
                     "individual or demographic for manipulative purposes"),
        ],
        inputs=["political_content/1", "broad_audience/1",
                "exploits_individual/1"],
        asserts=[_lic(
            read_back="producing % is permitted", read_back_slots=["M"],
            status="permit", act="produce(M)",
            body="political_content(M), broad_audience(M), "
                 "not exploits_individual(M)")],
        closure=[dict(act_class="produce", closure="cepa",
                      reason="the clause explicitly permits")],
    )


EXOTIC = [
    "#count{ X : harmed(X), person(X) } >= 3, risky(M)",
    "#sum{ C,X : cost(X,C) } < 10",
    "#min{ V : v(V) } = A, #max{ V : v(V) } = B",
    "ok(X) : member(X,G); big(G)",
    "p(X), 1 <= X, X <= 5",
    "q(X;Y), r(_)",
    "not not p(X)",
    "a(X), X != Y, b(Y)",
    "2 { p(X) : q(X) } 4",
    "p(1..5)",
    "p(X), X = #sum{ 1,Y : q(Y) }",
    "p(f(g(X),h(Y)))",
    "p(X), #false",
    "p(-1), q(X+1*2)",
    "p(X) : q(X), r(X)",
]


# ==========================================================================
#  substitute — the primitive layer 1 rests on
# ==========================================================================

def test_substitute_replaces_predicate_names_with_glosses():
    out = readback.substitute("political_content(M)",
                              {"political_content": "content about politics"})
    assert "«content about politics»" in out
    assert "political_content" not in out


def test_substitute_leaves_keywords_alone():
    """⚠️ REWRITTEN 2026-08-07. This used to pass a gloss for `count` and
    assert it was NOT used, which pinned the defect rather than the property:
    `count` is a legal predicate name, `_gloss_slot` glosses it, and layer 1
    refusing to made the two layers disagree and RB1 fire with a false message.
    See `KEYWORDS` and `test_a_predicate_legitimately_named_count_...`.

    What is actually true: the aggregate DIRECTIVES carry a `#`, which `_NAME`
    excludes, and bare `not` is a keyword.
    """
    out = readback.substitute("not #count #sum #min #max #true #false",
                              {"not": "WRONG", "count": "WRONG"})
    assert "«" not in out, out


def test_substitute_leaves_variables_and_directives_alone():
    out = readback.substitute("#count{ X : p(X) }", {"p": "a thing"})
    assert "#count" in out and "X" in out
    assert "«a thing»" in out


def test_substitute_marks_an_unglossed_name_rather_than_inventing_one():
    out = readback.substitute("p(X)", {})
    assert "p" in out and "«" not in out


# ==========================================================================
#  LAYER 1 — totality. ⛔ NO ASP CONSTRUCT MAY EVER BE INADMISSIBLE.
# ==========================================================================

@pytest.mark.parametrize("body", EXOTIC)
def test_layer1_renders_every_construct_without_error(body):
    spans = readback.render_body(body, {"p": "a thing", "harmed": "is harmed"})
    assert spans, f"no rendering at all for {body!r}"
    assert all(s.text.strip() for s in spans)


#: EXOTIC minus the constructs `schema.py` refuses at the CONTRACT layer.
#: ⭐ The split is the point, not an inconvenience: the renderer must handle
#: `_` — hand-written `.lp` files in this repo contain it, and `render_body` is
#: called on them — while the stage-1 contract refuses to EMIT it, because
#: xclingo dies on `_` in a body and takes the whole link set's explanation
#: down. "The renderer can render it" and "the contract should admit it" are
#: different claims, and conflating them is what caused that guard to be
#: withdrawn on a false ground and restored hours later.
SCHEMA_ADMISSIBLE = [b for b in EXOTIC if "_)" not in b and "_," not in b]


@pytest.mark.parametrize("body", SCHEMA_ADMISSIBLE)
def test_no_construct_is_refused_at_module_level(body):
    """The same constructs, reached through the public entry point."""
    mod = _mod(
        clause_id="m0217",
        concepts=[_concept("p", "a thing")],
        inputs=["p/1"],
        ontology=[_lic(atom="derived(X)", gloss="a derived thing", body=body)],
        requires=["harmed/1", "person/1", "risky/1", "cost/2", "v/1",
                  "member/2", "big/1", "ok/1", "q/1", "r/1", "a/1", "b/1",
                  "derived/1", "f/2", "g/1", "h/1"],
    )
    rb = readback.render_module(mod)
    assert rb.renderings, f"module carrying {body!r} rendered nothing"
    assert all(r.text.strip() for r in rb.renderings)


def test_a_construct_with_no_template_falls_back_and_says_so():
    """A choice aggregate has no fluent template today. It must still render."""
    spans = readback.render_body("2 { p(X) : q(X) } 4",
                                 {"p": "a thing", "q": "a condition"})
    assert any(s.layer == 1 for s in spans)
    assert any(readback.ASP_MARK in s.text for s in spans)
    assert "«a thing»" in " ".join(s.text for s in spans)


def test_unparseable_body_still_renders_and_is_recorded():
    """Even a body clingo cannot parse gets a rendering, plus a finding."""
    spans = readback.render_body("p(X) )( q(", {"p": "a thing"})
    assert spans and any(s.layer == 1 for s in spans)


def test_layer_is_recorded_on_every_rendering_and_visible_in_the_report():
    rb = readback.render_module(m0217_patched())
    assert all(r.layer in (1, 2) for r in rb.renderings)
    text = rb.report()
    for r in rb.renderings:
        assert r.stamp in text
    assert "layer" in text


# ==========================================================================
#  LAYER 2 — the fluency templates
# ==========================================================================

def test_symbolic_atom_renders_as_its_gloss_not_its_name():
    spans = readback.render_body("political_content(M)",
                                 {"political_content": "content about politics"})
    assert len(spans) == 1
    assert spans[0].layer == 2
    assert spans[0].text == "«content about politics»"


def test_polarity_comes_from_the_ast_not_from_prose():
    """§2.2's load-bearing reason. `not p(M)` must render negated whatever any
    authored sentence says."""
    spans = readback.render_body("not exploits_individual(M)",
                                 {"exploits_individual": "it exploits someone"})
    assert spans[0].layer == 2
    assert readback.NEG_MARK in spans[0].text
    assert "«it exploits someone»" in spans[0].text


def test_double_negation_emits_two_markers():
    spans = readback.render_body("not not p(X)", {"p": "a thing"})
    assert spans[0].text.count(readback.NEG_MARK) == 2


def test_comparison_renders_fluently():
    spans = readback.render_body("X != Y", {})
    assert spans[0].layer == 2
    assert "different from" in spans[0].text


def test_count_aggregate_renders_as_a_number_phrase():
    spans = readback.render_body("#count{ X : harmed(X) } >= 3",
                                 {"harmed": "someone is harmed"})
    assert spans[0].layer == 2
    t = spans[0].text
    assert "number" in t and "at least" in t and "3" in t
    assert "«someone is harmed»" in t


def test_sum_min_max_aggregates_render_fluently():
    for body, word in (("#sum{ C : cost(C) } < 10", "total"),
                       ("#min{ V : v(V) } = A", "smallest"),
                       ("#max{ V : v(V) } = A", "largest")):
        spans = readback.render_body(body, {"cost": "a cost", "v": "a value"})
        assert spans[0].layer == 2, body
        assert word in spans[0].text, body


def test_conditional_literal_renders_fluently():
    spans = readback.render_body("ok(X) : member(X,G)",
                                 {"ok": "it is acceptable",
                                  "member": "it belongs to the group"})
    assert spans[0].layer == 2
    assert "«it is acceptable»" in spans[0].text
    assert "«it belongs to the group»" in spans[0].text


def test_body_conjuncts_are_joined_with_and():
    rb = readback.render_module(m0217_patched())
    rule = [r for r in rb.renderings if r.kind == "asserts"][0]
    assert " and " in rule.text


# ==========================================================================
#  item templates (§2.3)
# ==========================================================================

def test_concept_item_renders_as_the_definition_itself():
    mod = _mod(concepts=[_concept("political_content", "content about politics")])
    rb = readback.render_module(mod)
    c = [r for r in rb.renderings if r.kind == "concept"][0]
    assert c.text == "«content about politics»"


def test_ontology_ground_fact_renders_x_is_g():
    mod = _mod(ontology=[_lic(atom="restricted(new_step)",
                              gloss="it falls under the restricted policy",
                              body=None)])
    rb = readback.render_module(mod)
    o = [r for r in rb.renderings if r.kind == "ontology"][0]
    # ⚠️ `«new_step»` UNTIL 2026-08-07, which was the F9 defect: an argument is
    # not a written definition and must not wear the typography of one.
    assert "new_step is " in o.text and "«new_step»" not in o.text, o.text
    assert "«it falls under the restricted policy»" in o.text


def test_ontology_with_a_body_renders_a_when_clause():
    mod = _mod(
        concepts=[_concept("risky", "it is risky")],
        inputs=["risky/1"],
        ontology=[_lic(atom="restricted(X)", gloss="it is restricted",
                       body="risky(X)")])
    rb = readback.render_module(mod)
    o = [r for r in rb.renderings if r.kind == "ontology"][0]
    assert " when " in o.text and "«it is risky»" in o.text


def test_asserts_renders_clause_status_act_when_body():
    rb = readback.render_module(m0217_patched())
    a = [r for r in rb.renderings if r.kind == "asserts"][0]
    assert a.text.startswith("clause m0217 permits ")
    assert " when " in a.text
    assert readback.NEG_MARK in a.text


def test_every_status_word_has_a_rendering():
    assert set(readback.STATUS) == {"forbid", "permit", "oblige", "prefer"}
    assert readback.STATUS["forbid"] == "forbids"


def test_beats_renders_who_says_so():
    mod = _mod(clause_id="m0217",
               beats=[_lic(read_back="m0217 says so", read_back_slots=[],
                           sayer="m0217", winner="m0100", loser="m0200",
                           body=None)])
    rb = readback.render_module(mod)
    b = [r for r in rb.renderings if r.kind == "beats"][0]
    assert "clause m0217 says" in b.text
    assert "clause m0100 outranks clause m0200" in b.text


def test_defines_without_a_gloss_for_its_term_is_an_ungloss_error():
    """§2.3's named live failure — it fires on m0053 today.

    ⛔ A MISSING GLOSS, not a missing template. The fallback makes templates
    optional; it cannot manufacture a definition that was never written.
    """
    mod = _mod(clause_id="m0053",
               concepts=[_concept("assistant", "the entity the user interacts with")],
               defines=[_lic(cites="m0053", kind="assistant",
                             term="interactable_entity")])
    rb = readback.render_module(mod)
    assert rb.outcome == "readback-ungloss"
    ungloss = [f for f in rb.findings if f.check_id == "readback-ungloss"]
    assert ungloss and any("interactable_entity" in f.message for f in ungloss)
    assert all(f.severity == "error" for f in ungloss)


def test_ungloss_is_not_reported_as_a_missing_template():
    mod = _mod(clause_id="m0053",
               concepts=[_concept("assistant", "the entity the user interacts with")],
               defines=[_lic(cites="m0053", kind="assistant",
                             term="interactable_entity")])
    rb = readback.render_module(mod)
    assert not any(f.check_id == "readback-no-template" for f in rb.findings)


def test_defines_with_both_glosses_renders():
    mod = _mod(clause_id="m0053",
               concepts=[_concept("assistant", "the entity the user interacts with"),
                         _concept("interactable_entity", "a thing one can interact with")],
               defines=[_lic(cites="m0053", kind="assistant",
                             term="interactable_entity")])
    rb = readback.render_module(mod)
    assert rb.outcome == "rendered"
    d = [r for r in rb.renderings if r.kind == "defines"][0]
    assert "«a thing one can interact with»" in d.text
    assert "«the entity the user interacts with»" in d.text


def test_an_act_with_no_gloss_is_rendered_literally_and_recorded():
    """Nothing in the schema glosses an act functor. Rendering its label is a
    deliberate, recorded exception to RB1 — never a silent one."""
    rb = readback.render_module(m0217_patched())
    assert any(f.check_id == "readback-act-literal" for f in rb.findings)
    assert all(f.severity == "note" for f in rb.findings
               if f.check_id == "readback-act-literal")


def test_an_abstained_module_renders_nothing_and_is_not_a_pass():
    mod = _mod(outcome="abstained", abstain_reason="a heading", claims=[])
    rb = readback.render_module(mod)
    assert rb.outcome == "no-readable-content"


# ==========================================================================
#  RB1 – RB5 (§2.4)
# ==========================================================================

def test_rb1_passes_when_no_label_survives():
    rb = readback.render_module(m0217_patched())
    assert rb.checks["RB1"] is True, [f.message for f in rb.findings]


def test_rb1_fires_when_a_predicate_name_survives_into_the_english():
    """A gloss that names its own predicate is Invariant 1's live failure."""
    mod = _mod(concepts=[_concept("restricted_content",
                                  "restricted_content still binds")])
    rb = readback.render_module(mod)
    assert rb.checks["RB1"] is False
    assert any(f.check_id == "RB1-label-survives" for f in rb.findings)


def test_rb1_fires_on_an_arity_signature():
    mod = _mod(concepts=[_concept("restricted", "whatever restricted/1 means")])
    rb = readback.render_module(mod)
    assert rb.checks["RB1"] is False


def test_rb1_allows_the_explicit_clause_reference():
    rb = readback.render_module(m0217_patched())
    a = [r for r in rb.renderings if r.kind == "asserts"][0]
    assert "m0217" in a.text
    assert rb.checks["RB1"] is True


def test_rb1_fires_on_a_bare_clause_id_that_is_not_a_reference():
    mod = _mod(concepts=[_concept("thing", "as m0217 elsewhere provides")])
    rb = readback.render_module(mod)
    assert rb.checks["RB1"] is False


def test_rb1_exempts_only_the_marked_act_term():
    """The act term is the one label the renderer emits ON PURPOSE.

    It is exempt because it is marked and carries a `readback-act-literal`
    note — never because it is quiet. Here `produce` is also a declared input,
    so it is in the label set and RB1 would fire without the exemption.
    """
    mod = _mod(
        clause_id="m0217", acts=["produce(M)"],
        concepts=[_concept("political_content", "content about politics")],
        inputs=["political_content/1", "produce/1"],
        asserts=[_lic(read_back="producing % is permitted",
                      read_back_slots=["M"], status="permit", act="produce(M)",
                      body="political_content(M)")],
        closure=[dict(act_class="produce", closure="cepa", reason="a reason")])
    rb = readback.render_module(mod)
    a = [r for r in rb.renderings if r.kind == "asserts"][0]
    assert readback.ACT_MARK in a.text and "produce" in a.text
    assert rb.checks["RB1"] is True
    assert any(f.check_id == "readback-act-literal" for f in rb.findings)


def test_rb2_passes_when_every_body_gloss_is_present():
    rb = readback.render_module(m0217_patched())
    assert rb.checks["RB2"] is True


def test_rb2_fires_when_the_renderer_drops_a_condition(monkeypatch):
    """Silent under-rendering: 4b would pass the weaker sentence."""
    real = readback.render_body

    def lossy(body, gloss, **kw):
        return real(body, gloss, **kw)[:1]

    monkeypatch.setattr(readback, "render_body", lossy)
    rb = readback.render_module(m0217_patched())
    assert rb.checks["RB2"] is False
    assert any(f.check_id == "RB2-missing-gloss" for f in rb.findings)


def test_rb3_counts_negation_markers_against_the_bodys_nots():
    rb = readback.render_module(m0217_patched())
    assert rb.checks["RB3"] is True


def test_rb3_is_not_fooled_by_the_word_not_inside_a_gloss():
    """A gloss saying 'has not read carefully' is prose, not polarity."""
    mod = _mod(
        concepts=[_concept("unread", "text the user has not read carefully")],
        inputs=["unread/1"],
        ontology=[_lic(atom="risky(X)", gloss="it is risky", body="unread(X)")])
    rb = readback.render_module(mod)
    assert rb.checks["RB3"] is True


def test_rb3_fires_when_polarity_is_dropped(monkeypatch):
    real = readback.render_body

    def unsigned(body, gloss, **kw):
        spans = real(body, gloss, **kw)
        return tuple(readback.Span(s.text.replace(readback.NEG_MARK, ""),
                                   s.layer, s.source) for s in spans)

    monkeypatch.setattr(readback, "render_body", unsigned)
    rb = readback.render_module(m0217_patched())
    assert rb.checks["RB3"] is False
    assert any(f.check_id == "RB3-polarity" for f in rb.findings)


def test_rb4_is_reported_and_never_fails_a_clause():
    """⭐ A threshold on an echo score is a scoring instrument (open question 3).
    It stamps; it must not gate."""
    quote = ("Content crafted for an unspecified or broad audience is "
             "permitted.")
    mod = _mod(concepts=[_concept(
        "broad_audience", "content crafted for an unspecified or broad audience")])
    rb = readback.render_module(mod, clause_quote=quote)
    item = [r for r in rb.renderings if r.kind == "concept"][0]
    assert rb.echo[item.item] == pytest.approx(1.0)
    assert rb.outcome == "rendered"
    assert rb.checks["RB4"] is None            # reported, never a pass/fail
    assert rb.non_evidential is True
    assert rb.echo_level_declared == pytest.approx(readback.ECHO_LEVEL)


def test_rb4_stamp_is_visible_in_the_report():
    quote = "content crafted for an unspecified or broad audience"
    mod = _mod(concepts=[_concept("broad_audience", quote)])
    rb = readback.render_module(mod, clause_quote=quote)
    assert "non-evidential" in rb.report()


def test_rb4_without_a_quote_reports_nothing_rather_than_zero():
    rb = readback.render_module(m0217_patched())
    assert rb.clause_echo is None
    assert rb.non_evidential is False


def test_rb5_empty_rendered_set_is_an_outcome_not_a_pass():
    """§3b. `m0037` renders zero rules; a vacuous pass is the failure."""
    mod = _mod(outcome="abstained", abstain_reason="a heading", claims=[])
    rb = readback.render_module(mod)
    assert rb.outcome == "no-readable-content"
    assert rb.checks["RB5"] is False
    assert any(f.check_id == "RB5-no-readable-content" for f in rb.findings)


def test_checks_report_all_five():
    rb = readback.render_module(m0217_patched())
    assert set(rb.checks) == {"RB1", "RB2", "RB3", "RB4", "RB5"}


# ==========================================================================
#  determinism
# ==========================================================================

def test_rendering_is_deterministic():
    a = readback.render_module(m0217_patched()).report()
    b = readback.render_module(m0217_patched()).report()
    assert a == b


# ==========================================================================
#  the real corpus — properties, never counts (DEBUGGING_TIPS §9)
# ==========================================================================

def _real_modules():
    out = []
    for path in sorted(RUNS.glob("*/m*.json")):
        try:
            obj = json.loads(path.read_text())
        except Exception:
            continue
        if not isinstance(obj, dict):
            continue
        try:
            out.append((path, schema.validate(obj)))
        except Exception:
            continue
    return out


def test_every_real_module_renders_without_raising():
    mods = _real_modules()
    if not mods:
        pytest.skip("no module in runs/ validates against the current schema")
    for path, mod in mods:
        rb = readback.render_module(mod)
        assert rb.outcome in ("rendered", "no-readable-content",
                              "readback-ungloss"), path
        assert all(r.layer in (1, 2) for r in rb.renderings), path


def test_ungloss_fires_exactly_when_a_required_symbol_has_no_gloss():
    mods = _real_modules()
    if not mods:
        pytest.skip("no module in runs/ validates against the current schema")
    for path, mod in mods:
        rb = readback.render_module(mod)
        want = bool(readback.unglossed_symbols(mod))
        assert (rb.outcome == "readback-ungloss") is want, path


def test_layer1_is_total_over_every_real_lp_rule_body():
    """The strongest totality evidence available: real ASP off disk."""
    files = sorted(WALKTHROUGH.glob("*.lp")) + \
        sorted((WALKTHROUGH / "clauses").glob("*.lp"))
    bodies = []
    for f in files:
        for body in readback.rule_bodies(f.read_text()):
            bodies.append((f, body))
    assert bodies, "no rule bodies found — this test would pass vacuously"
    for f, body in bodies:
        spans = readback.render_body(body, {})
        assert spans and all(s.text.strip() for s in spans), (f, body)


def test_a_missing_gloss_is_not_reported_as_a_missing_template():
    """⛔ The two must not be conflated. `p(X)` has a template and it fits;
    what is missing is the written meaning, and layer 1 must not be blamed."""
    spans = readback.render_body("p(X)", {})
    assert spans[0].layer == 2
    assert readback.UNGLOSS_MARK in spans[0].text
    assert readback.ASP_MARK not in spans[0].text


def test_a_missing_template_is_layer_1_even_when_every_gloss_is_present():
    """The converse: nothing is unglossed, and it still falls back."""
    spans = readback.render_body("2 { p(X) : q(X) } 4",
                                 {"p": "a thing", "q": "a condition"})
    assert spans[0].layer == 1
    assert readback.UNGLOSS_MARK not in spans[0].text


def test_defines_marks_the_ungloss_in_the_sentence_a_seat_would_read():
    mod = _mod(clause_id="m0053",
               concepts=[_concept("assistant", "the entity the user interacts with")],
               defines=[_lic(cites="m0053", kind="assistant",
                             term="interactable_entity")])
    rb = readback.render_module(mod)
    d = [r for r in rb.renderings if r.kind == "defines"][0]
    assert f"{readback.UNGLOSS_MARK}interactable_entity" in d.text


def test_rb1_says_whether_the_label_is_in_the_gloss_or_in_the_renderers_text():
    """Both fire, and the report must let them be told apart — on the real
    corpus the gloss-internal kind is the majority, and reading it as the
    renderer emitting labels would misdirect every repair."""
    inside = _mod(concepts=[_concept("task", "a task that cannot be completed")])
    rb = readback.render_module(inside)
    msg = [f.message for f in rb.findings if f.check_id == "RB1-label-survives"]
    assert msg and "inside a gloss" in msg[0]

    outside = _mod(
        concepts=[_concept("known", "a thing with a meaning")],
        inputs=["known/1", "nameless/1"],
        ontology=[_lic(atom="derived(X)", gloss="a derived thing",
                       body="known(X), nameless(X)")])
    rb = readback.render_module(outside)
    msg = [f.message for f in rb.findings
           if f.check_id == "RB1-label-survives" and "nameless" in f.message]
    assert msg and "renderer's own text" in msg[0]


def test_the_schema_admissible_split_is_real_and_not_vacuous():
    """Guards the list comprehension above. If it silently became "everything"
    or "nothing", the module-level test would either fail confusingly or cover
    nothing at all — the vacuous-pass shape this repo keeps re-learning."""
    assert SCHEMA_ADMISSIBLE, "the schema-admissible split is empty"
    assert len(SCHEMA_ADMISSIBLE) < len(EXOTIC), (
        "nothing was excluded, so the split is not doing its job — an "
        "anonymous variable is expected to be excluded")
    assert any("_" in b for b in EXOTIC), (
        "EXOTIC no longer exercises an anonymous variable at all, so layer 1 "
        "is untested on the one construct the contract refuses")


def test_a_body_carrying_TWO_statements_loses_nothing():
    """⛔ `_parse_body` returned the first Rule's literals and discarded the
    rest — a SILENT DROP, with every read-back check passing on the remnant.

    `schema._check_body` now rejects an internal full stop, so this is defence
    in depth. It is kept because a renderer that drops content silently is the
    exact failure the read-back exists to prevent, and trusting the layer above
    is how the first one got through.
    """
    body = "adult(P). N > 5, N != 9"
    spans = readback.render_body(body, {"adult": "the person is an adult"})
    joined = " ".join(s.text for s in spans)
    assert "N > 5" in joined and "N != 9" in joined, (
        f"content after the full stop was dropped: {joined!r}")
    assert all(s.layer == 1 for s in spans), (
        "an unparseable-as-one-rule body must fall back to layer 1, so the "
        "report shows it is ASP-with-glosses and not fluent English")


# ==========================================================================
#  ENGINEERING_REVIEW_2026-08-07b — F4 F5 F6 F7 F8 F9 F10
#  Every test below reproduced as RED against the reviewed tree first.
# ==========================================================================

# ---- F4: a quoted string constant is DATA, not a place to substitute ----

def test_a_gloss_is_not_substituted_INSIDE_a_quoted_string_constant():
    """⛔ `p("political_content is bad")` rendered as
    `«a thing» (of "«content about politics» is bad")`.

    Two costs, and the second is the serious one. A data constant is rewritten
    into prose; and a declared label sitting inside a string is glossed AWAY,
    so RB1 — the check whose entire job is to notice a surviving label — can no
    longer see it. `schema._strip_strings` is the only string-aware helper in
    the pipeline and the renderer had no counterpart.
    """
    gloss = {"p": "a thing", "political_content": "content about politics"}
    out = readback.substitute('p("political_content is bad")', gloss)
    assert '"political_content is bad"' in out, (
        f"the string constant was rewritten: {out!r}")
    assert "«a thing»" in out, f"the predicate name was not glossed: {out!r}"

    joined = " ".join(s.text for s in
                      readback.render_body('p("political_content is bad")',
                                           gloss))
    assert '"political_content is bad"' in joined, joined


def test_a_label_hiding_in_a_string_constant_is_still_visible_to_RB1():
    """The consequence, at the check. Glossing inside the string made the label
    disappear from RB1's scan, which is the inverse of what RB1 is for."""
    mod = _mod(
        concepts=[_concept("restricted", "the material is restricted")],
        inputs=["restricted/1", "tagged/1"],
        ontology=[_lic(atom="flagged(X)", gloss="the item is flagged",
                       body='tagged("restricted")')],
        requires=["flagged/1"])
    rb = readback.render_module(mod)
    text = " ".join(r.text for r in rb.renderings)
    assert '"restricted"' in text, (
        f"the label inside the string constant was glossed away: {text!r}")
    assert rb.checks["RB1"] is False, (
        "a declared label survives verbatim into the English and RB1 must say "
        "so")


# ---- F5: the substitution markers must stay unambiguous ----

def test_a_gloss_carrying_a_gloss_MARKER_does_not_break_the_stripper():
    """⛔ `_strip` is a flat scanner and `schema._BAD_IN_TEXT` does not forbid
    `«»` in a gloss, so a model can emit one:

        _strip('«a «flag» that has not been set»') -> ' that has not been set»'

    The residue leaks into every consumer — RB1's inside/outside gloss
    classification, `echo_score`, and `_markers`, which then counts the `not`
    of ordinary prose and fires RB3 on a CORRECT rendering.
    """
    raw = "a «flag» that has not been set"
    assert readback._strip(f"«{raw}»", readback.GLOSS_OPEN,
                           readback.GLOSS_CLOSE) != "", (
        "the premise of this test: `_strip` is a flat, non-nesting scanner, so "
        "a nested marker leaves prose behind. If that ever stops being true, "
        "this test is testing nothing and the fix below can be withdrawn")

    # ⭐ The fix is at INSERTION, not in the stripper: the markers have to keep
    # meaning exactly one thing for RB1 to mean anything, so a gloss carrying
    # one is neutralised on the way in — and said out loud, never silently.
    mod = _mod(concepts=[_concept("unread", raw)])
    rb = readback.render_module(mod)
    c = [r for r in rb.renderings if r.kind == "concept"][0]
    assert readback._strip(c.text, readback.GLOSS_OPEN,
                           readback.GLOSS_CLOSE) == "", (
        f"marker residue escaped the gloss: {c.text!r}")
    assert "flag" in c.text, f"the gloss's content was lost, not marked: {c.text!r}"
    assert any(f.check_id == "readback-marker-in-gloss" for f in rb.findings), (
        "rewriting a model's own text without saying so is the silent-edit "
        "shape this module exists to prevent")


def test_a_marker_inside_a_gloss_does_not_make_RB3_fire_on_a_correct_rendering():
    mod = _mod(
        concepts=[_concept("unread",
                           "text with a «flag» the user has not seen")],
        inputs=["unread/1"],
        ontology=[_lic(atom="stale(X)", gloss="the item is stale",
                       body="unread(X)")],
        requires=["stale/1"])
    rb = readback.render_module(mod)
    assert rb.checks["RB3"] is True, (
        "the body has zero `not`; the negation counted came out of the gloss's "
        "own prose, reachable only because the marker broke the stripper: "
        + str([f.message for f in rb.findings]))


# ---- F6: the converse table, all six operators, both guard positions ----

_CMP_CASES = [
    ("#count{ X : harmed(X) } = 3", "equal to 3"),
    ("#count{ X : harmed(X) } != 3", "different from 3"),
    ("#count{ X : harmed(X) } < 3", "less than 3"),
    ("#count{ X : harmed(X) } <= 3", "at most 3"),
    ("#count{ X : harmed(X) } > 3", "greater than 3"),
    ("#count{ X : harmed(X) } >= 3", "at least 3"),
    # ⭐ THE GUARD ON THE LEFT — the position `_CONVERSE` exists for. Read from
    # the aggregate's side the relation is the CONVERSE, and getting it
    # backwards inverts the bound silently. Only `<=` was covered before, and
    # only incidentally: clingo normalises `#count{…} >= 3` into `3 <= #count`.
    ("3 = #count{ X : harmed(X) }", "equal to 3"),
    ("3 != #count{ X : harmed(X) }", "different from 3"),
    ("3 < #count{ X : harmed(X) }", "greater than 3"),
    ("3 <= #count{ X : harmed(X) }", "at least 3"),
    ("3 > #count{ X : harmed(X) }", "less than 3"),
    ("3 >= #count{ X : harmed(X) }", "at most 3"),
]


@pytest.mark.parametrize("body,phrase", _CMP_CASES)
def test_every_aggregate_bound_reads_from_the_aggregates_side(body, phrase):
    spans = readback.render_body(body, {"harmed": "a person is harmed"})
    text = " ".join(s.text for s in spans)
    assert phrase in text, (
        f"{body!r} rendered as {text!r}; the bound must read {phrase!r} from "
        f"the aggregate's side. An inverted `_CONVERSE` entry flips a threshold "
        f"with every check still green")


def test_the_comparison_table_and_its_converse_are_a_bijection():
    """The guard that must kill the table above.

    Six asserts on rendered text cannot see a table that maps two operators
    onto one phrase, and `_CMP[Equal] = "different from"` survived the whole
    suite. Each operator needs its own phrase, and converting twice must be the
    identity.
    """
    assert len(set(readback._CMP.values())) == len(readback._CMP), (
        f"two comparison operators share a phrase: {readback._CMP}")
    for op in readback._CMP:
        assert readback._CONVERSE[readback._CONVERSE[op]] == op, (
            f"converting {readback._CMP[op]!r} twice is not the identity")


# ---- F7: the layer stamp of a MIXED item ----

def test_an_item_mixing_the_two_layers_is_stamped_with_the_WEAKER_one():
    """⛔ `_layer`'s `min` -> `max` survived the whole suite.

    Nothing built an item whose body mixes layers, so the module's own ⭐
    property — every rendering records WHICH layer produced it, because the two
    carry different amounts of trust — was unpinned exactly where it matters.
    Under `max` an item containing glossed raw ASP is handed to a seat stamped
    `fluent`.
    """
    body = "adult(P), 2 { q(P) } 4"
    spans = readback.render_body(body, {"adult": "the person is an adult",
                                        "q": "a condition"})
    assert sorted(s.layer for s in spans) == [1, 2], (
        f"this fixture no longer mixes the layers: "
        f"{[(s.text, s.layer) for s in spans]}")
    assert readback._layer(spans) == 1

    mod = _mod(
        concepts=[_concept("adult", "the person is an adult"),
                  _concept("q", "a condition")],
        inputs=["adult/1", "q/1"],
        ontology=[_lic(atom="eligible(P)", gloss="the person is eligible",
                       body=body)],
        requires=["eligible/1"])
    r = [x for x in readback.render_module(mod).renderings
         if x.kind == "ontology"][0]
    assert r.layer == 1, (
        "half this sentence is raw ASP; stamping it `fluent` tells a seat to "
        "trust it as English")
    assert readback.ASP_MARK in r.text


# ---- F8: layer 1 and layer 2 must agree about what a predicate name is ----

def test_a_predicate_legitimately_named_count_is_glossed_by_BOTH_layers():
    """⛔ `substitute` consulted `KEYWORDS`; `_gloss_slot` did not.

        substitute('count(X)', {'count': 'the tally'})  -> 'count(X)'
        render_body('count(X)', {'count': 'the tally'}) -> '«the tally»'

    So a module declaring `count/1` had RB1 fire on every layer-1 span with the
    message *"no definition was available to put there"* — which is FALSE: a
    definition existed and `substitute` refused to use it.

    The entries were also unnecessary. `_NAME`'s lookbehind is
    `(?<![A-Za-z0-9_#])`, so `#count`/`#sum`/`#min`/`#max`/`#true`/`#false` are
    already excluded by the `#`. Only bare `not` is load-bearing.
    """
    for word in ("count", "sum", "min", "max", "true", "false"):
        out = readback.substitute(f"{word}(X)", {word: "the tally"})
        assert "«the tally»" in out, (
            f"{word!r} is a legal predicate name and it has a written meaning, "
            f"but layer 1 emitted the label: {out!r}")


def test_the_aggregate_directives_are_still_left_alone():
    """The guard that must kill the test above: dropping the whole KEYWORDS
    check would gloss `#count` itself, and `not` is genuinely a keyword."""
    out = readback.substitute("#count{ X : p(X) }, not q(X)",
                              {"count": "WRONG", "not": "WRONG", "p": "a thing",
                               "q": "a condition"})
    assert "#count" in out and "WRONG" not in out, out
    assert "not «a condition»" in out, out


def test_layer_1_and_layer_2_agree_on_a_predicate_named_count():
    mod = _mod(
        concepts=[_concept("count", "the number of prior warnings")],
        inputs=["count/1"],
        ontology=[_lic(atom="warned(X)", gloss="the user has had a caution",
                       body="count(X), 2 { count(X) } 4")],
        requires=["warned/1"])
    rb = readback.render_module(mod)
    text = " ".join(r.text for r in rb.renderings)
    assert "«the number of prior warnings»" in text, text
    assert rb.checks["RB1"] is True, [f.message for f in rb.findings]


# ---- F9: an ontology ARGUMENT is not a written definition ----

def test_ontology_arguments_are_not_dressed_as_glosses():
    """⛔ `render_items` wrapped raw arguments in `«»` — the typography
    reserved for a written definition:

        restricted(new_step) -> '«new_step» is «it falls under…»'
        ok(P,N)              -> '«…» holds of «P», «N»'

    Because RB1 builds its `outside` scan by stripping `«…»`, a declared label
    appearing as an ontology argument was reported as *"inside a gloss — the
    written definition reuses its own predicate's name"* when the renderer had
    in fact emitted the bare label itself. That is the WEAKER of RB1's two
    diagnoses and the one a reader is told to discount: the classification was
    inverted for this case.
    """
    mod = _mod(
        inputs=["new_step/1"],
        ontology=[_lic(atom="restricted(new_step)",
                       gloss="it falls under the restriction", body=None)],
        requires=["restricted/1"])
    r = readback.render_module(mod).renderings[0]
    assert "new_step" in r.text
    assert "«new_step»" not in r.text, (
        f"a bare constant is not a written meaning: {r.text!r}")


def test_a_label_in_an_ontology_argument_is_blamed_on_the_RENDERER():
    """`new_step` is a declared input with no written meaning anywhere, so the
    renderer emits the bare label. RB1 must blame the renderer for it — before
    the fix the `«»` wrapper made the `outside` scan miss it and RB1 reported
    the module's gloss prose instead, sending the repair to the wrong place."""
    mod = _mod(
        inputs=["new_step/1"],
        ontology=[_lic(atom="restricted(new_step)",
                       gloss="it falls under the restriction", body=None)],
        requires=["restricted/1"])
    rb = readback.render_module(mod)
    hits = [f for f in rb.findings if f.check_id == "RB1-label-survives"
            and "new_step" in f.message]
    assert hits, [f.message for f in rb.findings]
    assert "renderer's own text" in hits[0].message, (
        "the renderer emitted the bare label itself; blaming the module's "
        "gloss prose sends the repair to the wrong place:\n" + hits[0].message)


def test_an_ontology_argument_that_HAS_a_meaning_still_gets_it():
    """The guard that must kill the two above: stripping the markers must not
    become "never gloss an argument"."""
    mod = _mod(
        concepts=[_concept("new_step", "a step that has just been added")],
        inputs=["new_step/1", "covers/2"],
        ontology=[_lic(atom="restricted(f(new_step))",
                       gloss="it falls under the restriction", body=None)],
        requires=["restricted/1", "f/1"])
    r = [x for x in readback.render_module(mod).renderings
         if x.kind == "ontology"][0]
    assert "«a step that has just been added»" in r.text, r.text


# ---- F10: RB1's clause-reference scrub is order-dependent ----

def test_the_clause_reference_scrub_is_not_prefix_blind():
    """⛔ `for cid in ids` iterates a SET, and the replacement is
    prefix-blind: with `m001` and `m0012` both in scope, replacing the shorter
    first corrupts the longer, and which happens depends on `PYTHONHASHSEED`.

    `REPRODUCIBILITY.md` requires determinism and
    `test_rendering_is_deterministic` runs both renders in ONE process, where
    the hash seed is constant — so it cannot see this class of defect at all.
    Latent on today's fixed-width ids; pinned so it cannot become live.
    """
    text = "clause m001 says clause m0012 outranks clause m0013"
    ids = {"m001", "m0012", "m0013"}
    got = readback._scrub_clause_refs(text, ids)
    assert got == "clause says clause outranks clause", (
        f"a clause reference was left half-erased: {got!r}. Replacing `m001` "
        f"first turns `clause m0012` into `clause2`")

    # ⭐ And it must not depend on the order the ids arrive in. This is the
    # part `test_rendering_is_deterministic` cannot see: it renders twice in
    # ONE process, where `PYTHONHASHSEED` is constant, so a set-iteration
    # dependency is invisible to it.
    import itertools
    outs = {readback._scrub_clause_refs(text, list(p))
            for p in itertools.permutations(sorted(ids))}
    assert len(outs) == 1, outs
