"""R3 — the derivation layer of the read-back (`STEP_stage4.md` §2.1).

⭐ WHAT THESE TESTS ARE FOR. R3 is the only layer that puts a *derivation* in
front of a seat: R1 says what an item means, R2 says what a rule says, R3 says
**why a verdict followed in a particular situation**. Its single substantive
requirement is §2.1's last cell — *"xclingo explanation tree, every leaf
replaced by its R1 rendering"* — so the tests that matter most are the ones
about leaves.

⛔ THE FAILURE THIS FILE IS WRITTEN AGAINST is not a wrong tree. It is an
**empty** one that reads like a finding. A missing `xclingo`, an `_` anywhere in
the link scope, or a parse failure all produce zero trees, and zero trees
rendered without complaint says *"this clause has no derivations"* — which is a
substantive claim about the translation, made by a tool that did not run. Every
one of those paths is asserted to BLOCK.
"""

import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fixtures                                                # noqa: E402
import probe                                                   # noqa: E402
import readback                                                # noqa: E402
import readback_r3 as r3                                       # noqa: E402
import schema                                                  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WALKTHROUGH = os.path.dirname(os.path.dirname(HERE))


# ==========================================================================
#  helpers — situations are built by hand so these tests do not depend on
#  probe's enumerator. `render_r3` takes anything with the four fields.
# ==========================================================================

def situation(sid, true_atoms, derived):
    idx = int(sid[1:]) if sid[1:].isdigit() else 0
    return probe.Situation(sid, idx, frozenset(true_atoms), frozenset(derived))


def political():
    """The m0217 shape: one `permit` rule over two input predicates."""
    return schema.validate(fixtures.political_module())


POL_FIRES = situation("S3", ["political_content(x)", "broad_audience(x)"],
                      ["asserts(m0217,permit,produce(x))"])
POL_SILENT = situation("S1", ["broad_audience(x)"], [])


def fake_xclingo(tmp_path, name, stdout="", stderr="", code=0):
    """A scripted stand-in for `xclingo`.

    ⚠️ Deliberately NOT "a python that happens to lack xclingo"
    (`DEBUGGING_TIPS.md` §8): that makes the test a claim about the machine.
    This ignores its arguments and produces exactly the two observables the
    guard reads — a stream and an exit code.
    """
    path = tmp_path / name
    path.write_text(
        "import sys\n"
        f"sys.stdout.write({stdout!r})\n"
        f"sys.stderr.write({stderr!r})\n"
        f"sys.exit({code})\n", encoding="utf-8")
    return [sys.executable, str(path)]


# ==========================================================================
#  INVARIANT 1 — the leaves are the whole point
# ==========================================================================

def test_every_raw_leaf_is_replaced_by_its_R1_rendering():
    """§2.1's last cell, and `STEP_stage4.md` §0 finding (3)'s remedy.

    Today xclingo's leaves are raw ASP (`forbids(restricted_content,m3)`).
    After R3 they must be the written meaning, in gloss typography, with the
    predicate NAME gone (Invariant 1: render the definition, not the label).
    """
    out = r3.render_r3(political(), [POL_FIRES])
    assert out.outcome == "rendered", out.report()
    leaves = [n for d in out.situations[0].derivations
              for n in r3.walk(d) if n.is_leaf]
    assert leaves, out.report()
    for leaf in leaves:
        assert leaf.kind == "fact"
        assert readback.GLOSS_OPEN in leaf.text
        assert "political_content" not in leaf.text
        assert "broad_audience" not in leaf.text
    joined = " ".join(n.text for n in leaves)
    assert "content that is political in nature" in joined


def test_a_leaf_with_no_gloss_is_REPORTED_never_passed_through():
    """`readback-ungloss`'s rule, one level down.

    A leaf nobody wrote a meaning for must not reach a seat wearing the
    predicate name as though it were a meaning — that IS failure mode #4.
    """
    mod = political()
    out = r3.render_r3(mod, [POL_FIRES], gloss={"broad_audience": None})
    assert out.outcome == "readback-ungloss", out.report()
    ids = {f.check_id for f in out.findings + out.situations[0].findings}
    assert "readback-ungloss" in ids
    text = out.report()
    assert readback.UNGLOSS_MARK in text
    assert "broad_audience" in text


def test_the_ungloss_finding_is_ERROR_severity_so_the_clause_reaches_no_seat():
    out = r3.render_r3(political(), [POL_FIRES],
                       gloss={"broad_audience": None})
    bad = [f for f in out.situations[0].findings
           if f.check_id == "readback-ungloss"]
    assert bad and all(f.severity == "error" for f in bad)
    assert not r3.proceeds_to_a_seat(out)


def test_a_fully_glossed_run_DOES_proceed_to_a_seat():
    """The `if True:` guard on the test above — without it, a `proceeds_to_a_
    seat` that always returned False would pass every refusal test here."""
    assert r3.proceeds_to_a_seat(r3.render_r3(political(), [POL_FIRES]))


# ==========================================================================
#  §2.2 — the annotation is COMPOSED BY THE RENDERER, not asked of the model
# ==========================================================================

def test_the_trace_annotation_is_the_RENDERERS_sentence_not_the_authored_one():
    """`schema.render_lp` emits `%!trace_rule {"{read_back}"}` from the
    model's authored field. §2.2 demotes that to a second opinion, so R3 must
    annotate with the RENDERER's sentence instead."""
    mod = political()
    assert mod.asserts[0].read_back == "producing % is permitted"
    out = r3.render_r3(mod, [POL_FIRES])
    assert "producing % is permitted" not in out.program
    rb = readback.render_module(mod)
    sentence = {r.item: r.text for r in rb.renderings}["asserts[0]"]
    assert r3.trace_safe(sentence)[0] in out.program


def test_the_rule_node_carries_the_renderers_sentence_into_the_tree():
    out = r3.render_r3(political(), [POL_FIRES])
    roots = out.situations[0].derivations[0].roots
    assert roots
    assert all(n.kind == "rule" for n in roots)
    assert readback.GLOSS_OPEN in roots[0].text
    assert "permits" in roots[0].text


def test_a_gloss_carrying_a_character_clingo_cannot_parse_is_neutralised():
    """`schema._BAD_IN_TEXT` fences `read_back` and NOTHING ELSE. A gloss may
    hold `"`, `{`, `}` or a backslash, and every one of them breaks the
    `%!trace_rule {"..."}` literal the sentence is interpolated into. It is
    rewritten and the rewrite is RECORDED — never silent."""
    mod = political()
    out = r3.render_r3(mod, [POL_FIRES],
                       gloss={"political_content": 'a "political" {topic}'})
    assert '"political"' not in out.program
    assert out.outcome == "rendered", out.report()
    assert any(f.check_id == "readback-r3-trace-unsafe" for f in out.findings)


# ==========================================================================
#  two defects found on LIVE material, and pinned here
# ==========================================================================

def test_a_node_carrying_TWO_labels_does_not_leak_the_raw_atom():
    """⛔ FOUND ON `m0079`. A body-less `asserts` fact carries R3's own
    `%!trace_rule` label AND the one `--auto-tracing=facts` adds, and xclingo
    prints both, joined by `;`. Reading the payload as one quoted sentence put
    `asserts(m0079,oblige,produce_response)` in front of a seat — Invariant 1's
    exact failure, emitted by the layer written to fix it."""
    payload = '"clause m0079 obliges it";asserts(m0079,oblige,produce_response)'
    said, bare = r3.node_labels(payload)
    assert said == ("clause m0079 obliges it",)
    assert bare == ("asserts(m0079,oblige,produce_response)",)
    text = ('##Explanation: 1.1\n  *\n  |__' + payload + '\n\n')
    (_label, (root,)), = r3.parse_ascii_trees(text)
    assert root.kind == "rule"
    assert root.text == "clause m0079 obliges it"
    assert "asserts(" not in root.text


def test_the_label_order_xclingo_chooses_does_not_change_the_node():
    """The pair above happens to print sentence-first. Nothing documents that
    order, and a node classified by `raw.startswith('\"')` would read the other
    order as a FACT and gloss the verdict atom as though it were an input."""
    text = ('##Explanation: 1.1\n  *\n'
            '  |__asserts(m0079,oblige,produce_response);"clause m0079 obliges"'
            '\n\n')
    (_label, (root,)), = r3.parse_ascii_trees(text)
    assert root.kind == "rule"
    assert root.text == "clause m0079 obliges"
    assert root.atom == "asserts(m0079,oblige,produce_response)"


def test_a_LEAFS_CONSTANT_survives_into_its_rendering():
    """⛔ Silent under-rendering, which is RB2's failure one level down. A leaf
    `harm_category(terrorism)` rendered as «a category of critical harm» alone
    is TRUE of the wrong thing: it drops which harm the derivation rested on,
    and a seat cannot see that anything is missing. The placeholder individual
    is the one constant suppressed — it names nobody."""
    gloss = {"harm_category": "a category of critical and high severity harm"}
    text, ok = r3.gloss_leaf("harm_category(terrorism)", gloss)
    assert ok and "terrorism" in text and "concerning" in text
    plain, ok = r3.gloss_leaf(
        f"harm_category({probe.PROBE_DEFAULTS['placeholder']})", gloss)
    assert ok and "concerning" not in plain


def test_a_semicolon_INSIDE_a_rendered_sentence_is_not_a_label_boundary():
    """The `if True:` guard on the splitter. `readback.render_body` joins with
    ` and `, but a gloss the model wrote may hold a `;` and splitting on it
    would silently truncate the sentence a seat reads."""
    said, bare = r3.node_labels('"first; second"')
    assert said == ("first; second",) and bare == ()


def test_the_ONTOLOGY_ABLATION_GUARD_never_becomes_a_leaf():
    """⛔ FOUND ON `m0079`. `schema.render_lp` hangs every ontology rule off
    `o`, and `o :- onto = on.` has no positive body atom — so clingo makes `o`
    a FACT, `--auto-tracing=facts` labels it, and it surfaces as a leaf of
    every ontology-backed derivation. R3 reported it as a missing gloss and
    stopped the clause, for a symbol that is renderer scaffolding."""
    mod = schema.validate(fixtures.module())
    s = situation("S1", ["restricted(x)"],
                  ["disallowed(x)", "asserts(m0001,forbid,produce(x))"])
    out = r3.render_r3(mod, [s],
                       extra_gloss={"restricted": "the material is restricted"})
    assert "onto" not in out.program and "o :- " not in out.program
    assert out.outcome == "rendered", out.report()
    raws = [n.raw for d in out.situations[0].derivations for n in r3.walk(d)]
    assert "o" not in raws, raws


def test_an_ontology_step_becomes_an_INTERIOR_node_with_its_own_sentence():
    """The derivation is two deep — the rule, then the ontology step that
    supplies its body — and `STEP_stage4.md` §2.1 wants the whole tree, not
    just its root."""
    mod = schema.validate(fixtures.module())
    s = situation("S1", ["restricted(x)"],
                  ["disallowed(x)", "asserts(m0001,forbid,produce(x))"])
    out = r3.render_r3(mod, [s],
                       extra_gloss={"restricted": "the material is restricted"})
    nodes = [n for d in out.situations[0].derivations for n in r3.walk(d)]
    assert max(n.depth for n in nodes) >= 3
    assert any(n.kind == "rule" and "the material is disallowed" in n.text
               for n in nodes)
    leaves = [n for n in nodes if n.is_leaf]
    assert leaves and all("the material is restricted" in n.text
                          for n in leaves)


# ==========================================================================
#  ⛔ EVERY EMPTY RESULT BLOCKS. This is the repo's signature failure.
# ==========================================================================

def test_a_missing_xclingo_BLOCKS(tmp_path):
    exe = fake_xclingo(tmp_path, "gone.py", stderr="No module named xclingo\n",
                       code=1)
    with pytest.raises(r3.R3Error) as exc:
        r3.render_r3(political(), [POL_FIRES], xclingo=exe)
    assert "xclingo" in str(exc.value)


def test_xclingo_that_FAILED_but_exited_ZERO_still_BLOCKS(tmp_path):
    """⛔ THE ARM THAT COSTS THE MOST, and `[RAN]` it is the one that fires on
    the real defect. xclingo 2.0b24 on `p(X) :- q(X,_).` prints
    *"error: unsafe variables in: _xclingo_sup(...#Anon0)"*, produces NO
    explanation at all — and **exits 0**. A guard on the return code alone
    reports a clause with derivations as a clause with none.

    The premise is asserted inside the test (`DEBUGGING_TIPS.md` §8): the day
    xclingo starts exiting non-zero on this, the test says so rather than
    quietly passing on the other arm.
    """
    stdout = "xclingo version 2.0b24\nAnswer: 1\n"
    stderr = ("<block>:8:1-56: error: unsafe variables in:\n"
              "*** ERROR: (xclingo, explainer program) grounding stopped\n")
    exe = fake_xclingo(tmp_path, "zero.py", stdout=stdout, stderr=stderr,
                       code=0)
    with pytest.raises(r3.R3Error) as exc:
        r3.render_r3(political(), [POL_FIRES], xclingo=exe)
    assert "error" in str(exc.value).lower()
    # the premise, asserted rather than assumed
    proc = subprocess.run(exe, capture_output=True, text=True)
    assert proc.returncode == 0


def test_an_INFO_line_on_stderr_is_not_an_error(tmp_path):
    """The `if True:` guard on the arm above. xclingo prints
    `info: atom does not occur in any rule head` on almost every real program;
    a stderr scan that treats any output as failure would block everything and
    the redundancy would become decoration in the other direction."""
    stdout = ("xclingo version 2.0b24\nAnswer: 1\n##Explanation: 1.1\n"
              '  *\n  |__"a sentence"\n  |  |__political_content(x)\n\n'
              "##Total Explanations:\t1\nModels:\t1\n")
    stderr = ("<block>:13:23-61: info: atom does not occur in any rule head:\n"
              "  _xclingo_violated_constraint(ID,Vars)\n")
    exe = fake_xclingo(tmp_path, "info.py", stdout=stdout, stderr=stderr)
    trees = r3.run_xclingo("p.", xclingo=exe)
    assert "##Explanation" in trees


def test_a_NONZERO_EXIT_blocks_even_when_the_output_looks_perfect(tmp_path):
    """⛔ THE ARM THE OTHER TESTS COVER FOR FREE, and therefore the one that
    silently stops being tested. `DEBUGGING_TIPS.md` §8: a deliberately
    redundant guard needs a RED test PER ARM — mutating `if proc.returncode
    != 0:` to `if False:` survived the whole file until this existed, because
    every other failing-xclingo test also tripped the stderr or sentinel arm.
    """
    stdout = ('Answer: 1\n##Explanation: 1.1\n  *\n  |__"a sentence"\n\n'
              "##Total Explanations:\t1\nModels:\t1\n")
    exe = fake_xclingo(tmp_path, "rc.py", stdout=stdout, code=3)
    # the premise: neither other arm can see this one
    proc = subprocess.run(exe, capture_output=True, text=True)
    assert proc.stderr == "" and r3.DONE_MARK in proc.stdout
    with pytest.raises(r3.R3Error) as exc:
        r3.run_xclingo("p.", xclingo=exe)
    assert "exited 3" in str(exc.value)


def test_a_TRUNCATED_stream_blocks_even_though_what_arrived_parses(tmp_path):
    """The completion-sentinel arm, isolated. A stream cut short still parses
    — into a SHORTER tree — and a derivation missing a branch is a simpler
    explanation of the same verdict that nothing downstream could detect."""
    stdout = 'Answer: 1\n##Explanation: 1.1\n  *\n  |__"a sentence"\n'
    exe = fake_xclingo(tmp_path, "cut.py", stdout=stdout)
    # the premise: this is not caught by either other arm, and it PARSES
    assert r3.parse_ascii_trees(stdout)
    with pytest.raises(r3.R3Error) as exc:
        r3.run_xclingo("p.", xclingo=exe)
    assert r3.DONE_MARK in str(exc.value)


def test_a_line_R3_cannot_place_inside_a_tree_BLOCKS():
    """Skipping it would drop a branch and leave the tree looking complete."""
    text = ('##Explanation: 1.1\n  *\n  |__"top"\n'
            '  ~~ something xclingo has never printed ~~\n\n'
            '##Total Explanations:\t1\n')
    with pytest.raises(r3.R3Error) as exc:
        r3.parse_ascii_trees(text)
    assert "will not skip" in str(exc.value)


def test_an_empty_situation_list_BLOCKS():
    """⛔ Zero situations in must never be zero derivations out. `R3 over
    nothing` and `no derivation exists` are the same bytes downstream."""
    with pytest.raises(r3.R3Error):
        r3.render_r3(political(), [])


def test_unparseable_xclingo_output_BLOCKS(tmp_path):
    exe = fake_xclingo(tmp_path, "junk.py", stdout="Segmentation fault\n")
    with pytest.raises(r3.R3Error):
        r3.render_r3(political(), [POL_FIRES], xclingo=exe)


def test_a_derived_verdict_with_no_tree_BLOCKS(tmp_path):
    """The equivalence guard. The situation is known — from stage 3 — to derive
    `asserts(m0217,permit,produce(x))`. If the explanation run does not root a
    tree at it, the two programs disagree and the tree is about something else.
    Rendering it anyway would show a seat a derivation for a verdict that is
    not the one under review."""
    stdout = ("Answer: 1\n##Explanation: 1.1\n\n"
              "##Total Explanations:\t1\nModels:\t1\n")
    exe = fake_xclingo(tmp_path, "nada.py", stdout=stdout)
    with pytest.raises(r3.R3Error) as exc:
        r3.render_r3(political(), [POL_FIRES], xclingo=exe)
    assert "asserts(m0217,permit,produce(x))" in str(exc.value)


def test_two_answer_sets_BLOCK(tmp_path):
    """A situation is a single answer set by construction (`probe.enumerate_
    situations` refuses a module with two). A second one here means the
    explanation program is not the program stage 3 enumerated."""
    stdout = ("Answer: 1\n##Explanation: 1.1\n  *\n  |__\"s\"\n\n"
              "Answer: 2\n##Explanation: 2.1\n  *\n  |__\"s\"\n\n"
              "##Total Explanations:\t2\nModels:\t2\n")
    exe = fake_xclingo(tmp_path, "two.py", stdout=stdout)
    with pytest.raises(r3.R3Error):
        r3.render_r3(political(), [POL_FIRES], xclingo=exe)


# ==========================================================================
#  ⛔ `_` — it takes the WHOLE link set's explanation down, not one rule
# ==========================================================================

def test_an_anonymous_variable_in_the_link_scope_is_REFUSED_BY_NAME():
    with pytest.raises(r3.R3Error) as exc:
        r3.render_r3(political(), [POL_FIRES],
                     link_texts=[("neighbour.lp", "p(X) :- q(X,_).\nq(a,b).")])
    msg = str(exc.value)
    assert "neighbour.lp" in msg
    assert "p(X) :- q(X,_)." in msg


def test_an_underscore_inside_a_COMMENT_is_not_an_anonymous_variable():
    """`m0255.lp` line 30 is literally `% named, not `_`: xclingo cannot
    ground an anonymous variable`. A scan that reads comments refuses the one
    file in the repo that took the trouble to avoid the construct."""
    text = "% named, not `_`: xclingo cannot ground one\np(X) :- q(X).\nq(a)."
    assert r3.anonymous_variables(text) == ()


def test_an_underscore_inside_a_STRING_CONSTANT_is_not_one_either():
    assert r3.anonymous_variables('p("a _ b").') == ()


def test_a_LEADING_UNDERSCORE_NAME_is_not_an_anonymous_variable():
    """`_foo` is an ordinary (hidden) identifier, not `#Anon`."""
    assert r3.anonymous_variables("p(X) :- _q(X).") == ()


# ==========================================================================
#  a situation with no derivation is an OUTCOME, never an omission
# ==========================================================================

def test_a_silent_situation_is_recorded_as_no_derivation_and_COUNTED():
    out = r3.render_r3(political(), [POL_FIRES, POL_SILENT])
    by_id = {s.situation_id: s for s in out.situations}
    assert by_id["S1"].outcome == "no-derivation"
    assert by_id["S1"].derivations == ()
    assert by_id["S3"].outcome == "rendered"
    assert out.covering == 2
    assert out.with_derivation == 1
    assert "1 of 2" in out.report()


def test_a_run_where_NO_situation_derives_anything_says_so_in_the_outcome():
    out = r3.render_r3(political(), [POL_SILENT])
    assert out.outcome == "no-derivation"
    assert out.with_derivation == 0
    assert "no-derivation" in out.report()


# ==========================================================================
#  the tree is STRUCTURED, not a blob
# ==========================================================================

def test_the_tree_keeps_its_shape():
    text = ('##Explanation: 1.1\n'
            '  *\n'
            '  |__"top"\n'
            '  |  |__"middle"\n'
            '  |  |  |__leaf(a)\n'
            '  |  |__other(b)\n'
            '\n##Total Explanations:\t1\n')
    (label, roots), = r3.parse_ascii_trees(text)
    assert label == "1.1"
    assert len(roots) == 1
    top = roots[0]
    assert top.raw == '"top"' and len(top.children) == 2
    mid, other = top.children
    assert mid.raw == '"middle"' and len(mid.children) == 1
    assert mid.children[0].raw == "leaf(a)" and mid.children[0].is_leaf
    assert other.raw == "other(b)" and other.is_leaf
    assert [n.raw for n in r3.walk_nodes(top)] == \
        ['"top"', '"middle"', "leaf(a)", "other(b)"]


def test_a_tree_line_at_an_impossible_depth_BLOCKS():
    """A child two levels below its parent has no parent. Guessing one builds
    a tree that is not the one xclingo printed."""
    text = ('##Explanation: 1.1\n  *\n  |__"top"\n  |  |  |__leaf(a)\n\n')
    with pytest.raises(r3.R3Error):
        r3.parse_ascii_trees(text)


# ==========================================================================
#  regression fixture — `STEP_stage4.md` §0 finding (3), on real material
# ==========================================================================

@pytest.mark.skipif(not os.path.exists(os.path.join(WALKTHROUGH, "m0255.lp")),
                    reason="the hand translation is not on disk")
def test_C3_reproduces_at_EXPLANATION_granularity_on_m0255_case_c():
    """§0 finding (3): the C4 derivation over case C is four tree lines.

    ⚠️ Pinned as a SHAPE, not a count of a live artifact: the leaves are raw
    ASP today, which is exactly what R3 exists to replace, and this test is
    here so the day `m0255.lp` grows a gloss layer somebody notices.
    """
    paths = [os.path.join(WALKTHROUGH, p) for p in
             ("m0255.lp", "clauses/m0200.lp", "clauses/m0201.lp",
              "clauses/m0203.lp", "m0255_case_c.lp")]
    program = "\n".join(open(p, encoding="utf-8").read() for p in paths)
    out = r3.run_xclingo(program)
    trees = r3.parse_ascii_trees(out)
    assert trees
    lines = [n for _label, roots in trees for r in roots
             for n in r3.walk_nodes(r)]
    assert len(lines) >= 4
    assert any("is an action" in n.raw for n in lines)
    assert any(n.raw.startswith("forbids(") for n in lines)


# ==========================================================================
#  the real corpus — how many covering-set situations have a derivation
# ==========================================================================

def _live_modules():
    import glob
    import json
    out = []
    for path in sorted(glob.glob(os.path.join(HERE, "runs", "*", "m*.json"))):
        try:
            obj = json.load(open(path, encoding="utf-8"))
            mod = schema.validate(obj)
        except Exception:                                      # noqa: BLE001
            continue
        lp = path[:-5] + ".lp"
        if os.path.exists(lp):
            out.append((mod, lp))
    return out


def test_at_least_one_stored_module_yields_a_NON_EMPTY_derivation():
    """⛔ NOT an exact count — a cycle that adds a module must not fail this.
    What it pins is that the path is EXERCISED on real material: an R3 that
    exists only on fixtures is R3 existing on paper, which is the thing §2.1
    already suffers from.
    """
    import link
    total, with_deriv, seen = 0, 0, 0
    for mod, lp in _live_modules():
        rows, _l, _m = link.discover_concept_table([lp])
        rep = probe.probe_clause(lp, [], rows or [])
        if not rep.covering:
            continue
        out = r3.render_r3(mod, rep.covering,
                           extra_gloss=readback.gloss_from_rows(rows or []))
        seen += 1
        total += out.covering
        with_deriv += out.with_derivation
    assert seen >= 1, "no stored module reached R3 at all"
    assert with_deriv >= 1, f"{with_deriv} of {total} situations derived anything"
