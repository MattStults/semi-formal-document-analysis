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
import re
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


def test_every_node_carries_the_LAYER_that_produced_it():
    """§2.3: *"Every rendering records the layer that produced it, and the
    layer is visible in the report"*, and the layer-1 fraction is printed even
    when zero. Without it the two layers are indistinguishable in the output,
    which is the defect RB5 exists to prevent one level up."""
    out = r3.render_r3(political(), [POL_FIRES])
    nodes = out.nodes
    assert nodes and all(n.layer in (1, 2) for n in nodes)
    assert all(readback.LAYER_STAMP[n.layer] in out.report() for n in nodes)
    assert out.layer1_fraction == 0.0
    assert "layer-1 nodes: 0.00" in out.report()


def test_a_MISSING_GLOSS_is_not_reported_as_a_missing_TEMPLATE():
    """⛔ §2.3 forbids blurring these and says why: a missing template is OUR
    gap and costs fluency; a missing gloss is a hole in the TRANSLATION and is
    the failure the read-back exists to catch. So an unglossed leaf stays
    layer 2 — the template fitted — and the signal is carried by an ERROR that
    stops the clause, not by a fluency statistic nobody acts on.

    ⚠️ This test was written the other way round first, and the assertion was
    wrong: `readback._gloss_slot` already stamps a marked hole layer 2 inside
    a rule rendering, so stamping the same hole layer 1 at a leaf would have
    made R3 and R1 disagree about the same missing definition.
    """
    out = r3.render_r3(political(), [POL_FIRES],
                       gloss={"broad_audience": None})
    holes = [n for n in out.nodes if readback.UNGLOSS_MARK in n.text]
    assert holes and all(n.layer == 2 for n in holes)
    assert out.layer1_fraction == 0.0
    assert out.outcome == "readback-ungloss"


def test_a_layer_1_rule_rendering_reaches_the_tree_stamped_as_such():
    """The other half: a construct with no layer-2 template still renders, in
    layer-1 form, and the stamp says so rather than the clause being refused."""
    mod = schema.validate(fixtures.political_module(
        asserts=[dict(**fixtures.textual("m0217"), status="permit",
                      act="produce(M)",
                      # ⚠️ POOLING. `readback` has layer-2 templates for
                      # aggregates, comparisons, intervals and conditional
                      # literals — `[RAN]` all four render at layer 2 — so a
                      # fixture reaching for "something exotic" does NOT
                      # exercise the fallback. `p(X;Y)` does.
                      body="political_content(M), broad_audience(M;M)",
                      read_back="producing % is permitted",
                      read_back_slots=["M"])]))
    s = situation("S3", ["political_content(x)", "broad_audience(x)"],
                  ["asserts(m0217,permit,produce(x))"])
    out = r3.render_r3(mod, [s])
    assert out.outcome == "rendered", out.report()
    assert out.layer1_fraction > 0
    assert any(n.layer == 1 and readback.ASP_MARK in n.text for n in out.nodes)


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

def test_an_anonymous_variable_in_a_HEAD_is_REFUSED_BY_NAME():
    """⛔ THE RESIDUAL, and its ground is the SOLVER, not xclingo.

    `deanonymise` rewrites a BODY `_` and the program renders. A HEAD `_` is
    left where the author wrote it, because no transform can rescue it —
    `[RAN]` plain clingo on `q(a). p(_) :- q(X).` gives
    *"error: unsafe variables in: p(#Anon0)"*. So this refusal is clingo's
    rule about the whole file, and R3 states it as one.
    """
    with pytest.raises(r3.R3Error) as exc:
        r3.render_r3(political(), [POL_FIRES],
                     link_texts=[("neighbour.lp", "p(_) :- q(X).\nq(a,b).")])
    msg = str(exc.value)
    assert "neighbour.lp" in msg
    assert "p(_)" in msg


def test_a_BODY_anonymous_variable_in_the_link_scope_now_RENDERS():
    """⭐ The other half, and the reason the guard above had to be narrowed.

    `schema._check_body` no longer rejects `_`, so a stored `.lp` may carry
    one — and every stored `.lp` is another clause's `link_texts`. A refusal
    here would block clause B because clause A used legal ASP.
    """
    out = r3.render_r3(political(), [POL_FIRES],
                       link_texts=[("neighbour.lp", "p(X) :- q(X,_).\nq(a,b).")])
    assert out.outcome == "rendered", out.findings
    assert out.with_derivation == 1


# ==========================================================================
#  ⭐ THE PRE-RENDER TRANSFORM — `_` in a body is legal ASP, and alpha-renaming
#  it to a fresh variable is meaning-preserving. The property that makes the
#  whole thing safe is THE ANSWER SETS, so it is pinned directly and not
#  inferred from the shape of the output text.
# ==========================================================================

VENV_PY = os.path.join(WALKTHROUGH, os.pardir, "semi-formal-experiment",
                       ".venv", "bin", "python")


def answer_sets(program, tmp_path, name="as.lp"):
    """Every answer set of `program`, as a set of frozensets of atom strings.

    ⛔ NOT "clingo's stdout matched" (`DEBUGGING_TIPS.md` §8/§8a). The JSON
    output carries an explicit `Result`, which is asserted SATISFIABLE before
    any comparison — a program that failed to ground produces zero witnesses,
    and two programs that both failed would otherwise compare EQUAL and the
    round-trip test would pass having proved nothing.
    """
    import json
    f = tmp_path / name
    f.write_text(program, encoding="utf-8")
    r = subprocess.run([VENV_PY, "-m", "clingo", str(f), "-n", "0",
                        "--outf=2"], capture_output=True, text=True)
    try:
        doc = json.loads(r.stdout)
    except ValueError:
        raise AssertionError(
            f"clingo produced no JSON for:\n{program}\n"
            f"rc={r.returncode}\nstdout={r.stdout[:400]}\nstderr={r.stderr[:400]}")
    assert doc.get("Result") == "SATISFIABLE", (
        f"clingo did not solve this program, so its answer sets cannot be "
        f"compared with anything:\n{program}\nResult={doc.get('Result')!r}\n"
        f"{r.stderr[:400]}")
    return {frozenset(w["Value"]) for w in doc["Call"][0]["Witnesses"]}


#: (name, program) — each carries at least one `_` in a body. The last three
#: are the cases a naive implementation gets wrong: two `_` in one rule, a `_`
#: inside a nested term, and a rule that already uses the names a lazy
#: generator would reach for.
ROUND_TRIP = [
    ("one anonymous variable",
     "q(a,b). q(b,c). p(X) :- q(X,_)."),
    ("two anonymous variables in one rule",
     "q(a,b). q(b,c). {r(z)}. s(X) :- q(X,_), r(_)."),
    ("an anonymous variable inside a NESTED term",
     "q(a, f(b,c)). q(b, f(d,e)). p(X) :- q(X, f(_, _))."),
    ("a positive literal beside an untouched negated one",
     "q(a,b). q(b,c). r(a,z). p(X) :- q(X,_), not r(X,_)."),
    ("an aggregate",
     "q(a,b). q(b,c). p(X) :- q(X,_), 2 = #count{ Y : q(Y,_) }."),
    ("a rule that already uses the obvious fresh names",
     "q(a,b). q(b,c). p(X,_V1,_V2) :- q(X,_V1), q(_V1,_V2), q(X,_)."),
    ("an interval and an arithmetic comparison in the same body",
     "q(a,b). n(1). n(5). p(X) :- q(X,_), n(N), N = 1..3."),
    ("an anonymous variable in a CONSTRAINT (no head at all)",
     "q(a,b). r(a). :- q(X,_), not r(X). p(a)."),
    ("a pooled body and a string constant holding a lone underscore",
     'q(a,b). q(b,c). t("a _ b"). p(X) :- q(X,_), t(_).'),
]


@pytest.mark.parametrize("name,program",
                         ROUND_TRIP, ids=[n for n, _p in ROUND_TRIP])
def test_the_transform_PRESERVES_THE_ANSWER_SETS(name, program, tmp_path):
    """⭐ THE TEST THAT MAKES THE TRANSFORM SAFE, and the only one that can.

    An anonymous variable IS a fresh variable used once, so replacing it with
    a distinct new name is alpha-renaming. That claim is checked by running
    both programs, not by reading either.
    """
    out, _n = r3.deanonymise(program)
    assert answer_sets(out, tmp_path, "after.lp") == \
        answer_sets(program, tmp_path, "before.lp"), (
            f"{name}: the transform changed the meaning of the program.\n"
            f"before: {program}\nafter:  {out}")


def test_the_transform_actually_REMOVED_the_anonymous_variables(tmp_path):
    """The guard on the test above: `return text` preserves every answer set.

    Without this, a transform that does nothing passes the whole round-trip
    table — the `if True:` shape `DEBUGGING_TIPS.md` §8 names.
    """
    for name, program in ROUND_TRIP:
        out, _n = r3.deanonymise(program)
        assert r3.renameable_anonymous(out) == (), (
            f"{name}: a renameable body `_` survived the transform: {out!r}")
        assert r3.renameable_anonymous(program) != (), (
            f"{name}: the INPUT has no anonymous variable, so this row proves "
            f"nothing about the transform")


def test_each_anonymous_variable_gets_a_DISTINCT_name():
    """⛔ CONDITION 1. One shared name JOINS the two positions and changes the
    meaning — `[RAN]` `s(X) :- q(X,_V1), r(_V1).` over `q(a,b). q(b,c). r(z).`
    derives NOTHING, where the anonymous form derives `s(a), s(b)`.
    """
    out, _n = r3.deanonymise("s(X) :- q(X,_), r(_).")
    fresh = [t for t in re.findall(r"_[A-Za-z0-9_]*", out)]
    assert len(fresh) == 2, out
    assert fresh[0] != fresh[1], (
        f"both anonymous variables were given the same name, which joins them: "
        f"{out!r}")


def test_a_fresh_name_never_COLLIDES_with_a_variable_already_present():
    """⛔ CONDITION 2, generated against the variables actually there."""
    out, _n = r3.deanonymise("p(_V1,_V2,V) :- q(_V1,_V2,V,_).")
    fresh = re.findall(r"_V\d+|_Anon\d+", out)
    assert "_V1" in out and "_V2" in out          # the author's names survive
    new = [t for t in fresh if t not in ("_V1", "_V2")]
    assert len(new) == 1 and new[0] not in ("_V1", "_V2"), out


def test_fresh_names_are_distinct_ACROSS_SOURCES_too():
    """Rule-scoped variables could not collide, but the counter is shared so
    the property does not rest on that reasoning."""
    got = r3.deanonymise_all([("a.lp", "p(X) :- q(X,_)."),
                              ("b.lp", "r(X) :- s(X,_).")])
    names = [re.search(r"_V\d+", t).group() for _w, t in got]
    assert names[0] != names[1], got


def test_the_transform_leaves_COMMENTS_and_STRING_CONSTANTS_alone():
    """A gloss lives inside a `%!trace_rule` comment and may hold a lone `_`.
    Rewriting it would change the sentence a seat reads."""
    text = ('%!trace_rule {"a gloss with a lone _ in it"}.\n'
            'p(X) :- q(X,_), t("also _ here").')
    out, _n = r3.deanonymise(text)
    assert 'a gloss with a lone _ in it' in out
    assert '"also _ here"' in out
    assert "q(X,_)" not in out


def test_the_transform_does_not_rewrite_a_COMMENT_INSIDE_A_RULE_BODY():
    """⛔ Found by the mutation sweep, not by me: my first comment test put the
    `_` inside a `%!trace_rule` STRING, so blanking strings alone already
    covered it and `if c == "%":` survived as a SURVIVOR.

    A comment only matters where it sits INSIDE a body span, and then it
    matters a lot — `m0255.lp` line 30 is a comment saying the author avoided
    `_` on purpose, and rewriting it would corrupt the one file that took the
    trouble. Every `%!trace_rule` R3 emits is a comment too.
    """
    text = ("p(X) :-\n"
            "    q(X,_),      % written in full here; never as _\n"
            "    r(X).")
    out, _n = r3.deanonymise(text)
    assert "% written in full here; never as _" in out, out
    assert "q(X,_)" not in out, out         # the real one was still renamed


def test_a_FULL_STOP_INSIDE_A_COMMENT_does_not_end_a_statement():
    """The other half: a comment's `.` read as a terminator truncates the body
    span, and every `_` after it is silently left for the refusal to trip on."""
    text = ("p(X) :- q(X,Y),   % see clause m0255. it avoids this\n"
            "        r(Y,_).")
    out, _n = r3.deanonymise(text)
    # ⚠️ Asserted on the OUTPUT TEXT and not via `renameable_anonymous`: that
    # helper reads the same body spans the transform does, so under a defect
    # in the span scan it agrees with the defect and the check passes
    # vacuously (`DEBUGGING_TIPS.md` §8). This is how the first version of
    # this test let a mutation survive.
    assert "r(Y,_)." not in out, (
        f"the `_` on the second line was not reached, so the body span ended "
        f"at the full stop inside the comment: {out!r}")
    assert "% see clause m0255. it avoids this" in out, out


def test_a_HEAD_anonymous_variable_is_LEFT_where_the_author_wrote_it():
    """⛔ No transform rescues it (`[RAN]` clingo: `p(#Anon0)` is unsafe), so
    it must reach the refusal rather than be quietly renamed into a program
    that still cannot ground."""
    out, _n = r3.deanonymise("p(_) :- q(X). q(a).")
    assert "p(_)" in out


def test_a_NOT_LITERAL_is_left_alone_because_RENAMING_IT_BREAKS_IT(tmp_path):
    """⛔ THE ONE PLACE THE BRIEF'S PREMISE FAILS, and it is `[RAN]`.

    *"An anonymous variable IS a fresh variable used once"* is true of gringo's
    positive literals and FALSE of its negative ones: gringo PROJECTS `_` under
    `not`, so the anonymous form solves and the renamed form is unsafe. A
    transform there would turn a working program into a refused one — the
    opposite of meaning-preserving — so `deanonymise` leaves it.

    ⭐ And it never needed transforming: xclingo renders this case unaided.
    That is asserted in `test_xclingo_renders_a_NOT_LITERAL_underscore_unaided`.
    """
    prog = "q(a,b). q(b,c). r(a,z). p(X) :- q(X,Y), not r(X,_)."
    out, _n = r3.deanonymise(prog)
    assert "not r(X,_)" in out, out
    assert answer_sets(prog, tmp_path, "neg.lp") == {
        frozenset({"q(a,b)", "q(b,c)", "r(a,z)", "p(b)"})}

    # the ground, executed: the rename is not available here
    renamed = prog.replace("not r(X,_)", "not r(X,_V9)")
    f = tmp_path / "renamed.lp"
    f.write_text(renamed, encoding="utf-8")
    res = subprocess.run([VENV_PY, "-m", "clingo", str(f), "-n", "0"],
                         capture_output=True, text=True)
    assert "unsafe" in (res.stdout + res.stderr).lower(), (
        "clingo accepted a named variable in a negative literal, so the reason "
        "`not` is excluded from the transform no longer holds and the "
        "EXCLUSION should be re-examined, not this test relaxed.\n"
        + (res.stdout + res.stderr)[:400])


def test_xclingo_renders_a_NOT_LITERAL_underscore_unaided():
    """⭐ The restriction was WIDER THAN ITS OWN GROUND. xclingo only lifts
    POSITIVE body literals into `_xclingo_sup`, so `not r(X,_)` was never the
    thing that broke it — and `schema._check_body` rejected it anyway."""
    mod = schema.validate(fixtures.political_module(
        asserts=[dict(status="permit", act="produce(M)",
                      body="political_content(M), broad_audience(M), "
                           "not forbidden(M,_)",
                      read_back="producing % is permitted",
                      read_back_slots=["M"], licence="textual", cites="m0217",
                      inference=None, toggleable=False)],
        inputs=["political_content/1", "broad_audience/1", "forbidden/2"]))
    out = r3.render_r3(mod, [POL_FIRES])
    assert out.outcome == "rendered", out.findings
    assert "not forbidden(M,_)" in out.program        # untouched, and it works


def test_an_underscore_the_SOLVER_already_refuses_is_refused_EITHER_WAY(
        tmp_path):
    """`X > _` is unsafe to plain clingo before any transform touches it, so
    the rename changes no outcome — a refusal stays a refusal. Recorded so the
    transform is not blamed for a program clingo was never going to load."""
    prog = "n(1). n(5). p(X) :- n(X), X > _."
    out, _n = r3.deanonymise(prog)
    for text in (prog, out):
        f = tmp_path / "u.lp"
        f.write_text(text, encoding="utf-8")
        res = subprocess.run([VENV_PY, "-m", "clingo", str(f), "-n", "0"],
                             capture_output=True, text=True)
        assert "unsafe" in (res.stdout + res.stderr).lower(), text


def test_a_module_whose_BODY_carries_an_underscore_RENDERS():
    """End to end: the schema now admits it, and R3 must produce a tree."""
    mod = schema.validate(fixtures.political_module(asserts=[dict(
        status="permit", act="produce(M)",
        body="political_content(M), broad_audience(_)",
        read_back="producing % is permitted", read_back_slots=["M"],
        licence="textual", cites="m0217", inference=None, toggleable=False)]))
    out = r3.render_r3(mod, [POL_FIRES])
    assert out.outcome == "rendered", out.findings
    assert out.with_derivation == 1


def test_the_STORED_program_keeps_the_AUTHORS_underscore():
    """⛔ Not persisted. `ModuleR3.program` is the module's own logic; the
    transform happens at the xclingo boundary and is re-derivable from it with
    `deanonymise(out.program)`."""
    mod = schema.validate(fixtures.political_module(asserts=[dict(
        status="permit", act="produce(M)",
        body="political_content(M), broad_audience(_)",
        read_back="producing % is permitted", read_back_slots=["M"],
        licence="textual", cites="m0217", inference=None, toggleable=False)]))
    out = r3.render_r3(mod, [POL_FIRES])
    assert "broad_audience(_)" in out.program


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


# ==========================================================================
#  ⭐ Findings of the stage-4 adversarial review, 2026-08-08.
# ==========================================================================

def test_a_PERCENT_in_a_gloss_is_neutralised_and_RECORDED():
    """⛔ THE THIRD INVARIANT-1 ESCAPE, and the same shape as the two the build
    already fixed: seat-facing text corrupted by the layer written to render it.

    `TRACE_SAFE` covered every character that would break the quoted literal
    and missed the one character xclingo's own annotation dialect is built on.
    xclingo's preprocessor rewrites `%!` to `&` INSIDE the string literal, so a
    gloss carrying `%!` produced a RULE node reading `«… &x here»` and a LEAF
    node reading `«… %!x here»` — two different sentences for one definition,
    in one tree, with no `readback-r3-trace-unsafe` note firing.

    ⚠️ Text corruption, NOT injection: the rewrite stays inside the literal and
    does not become a directive. The program's semantics are unaffected; what
    is affected is what a seat reads.
    """
    assert r3.trace_safe("content about politics %!x here")[1] == ("%",)
    mod = political()
    out = r3.render_r3(mod, [POL_FIRES],
                       gloss={"political_content":
                              "content about politics %!x here"})
    assert any(f.check_id == "readback-r3-trace-unsafe" for f in out.findings)
    rule_text = [n.text for n in out.nodes if n.kind == "rule"]
    assert rule_text and all("&" not in t for t in rule_text), rule_text
    # ⚠️ the program still contains `%!trace_rule` — those are OURS. What may
    # not survive is the model-authored `%` inside the quoted literal.
    assert "%!x here" not in out.program


def test_control_an_ordinary_gloss_raises_no_trace_unsafe_note():
    """The paired control. A neutraliser that fires on everything is pinned by
    nothing — and no gloss in the stored corpus contains a `%`."""
    mod = political()
    out = r3.render_r3(mod, [POL_FIRES])
    assert r3.trace_safe("content about politics")[1] == ()
    assert not [f for f in out.findings
                if f.check_id == "readback-r3-trace-unsafe"]


def test_a_run_with_NO_derivation_reports_the_layer1_fraction_as_not_measured():
    """R10. `report()` prints `not-measured (no derivation)` from `frac is
    None`. Returning `0.0` instead makes it print `0.00 of 0` — `DEBUGGING_TIPS`
    §2 verbatim, a rate reading 0.0000 when it measured nothing, in the field
    §2.3 requires *printed even when zero*."""
    mod = political()
    out = r3.render_r3(mod, [POL_SILENT])
    assert out.nodes == ()
    assert out.layer1_fraction is None, (
        "0.0 over no nodes is indistinguishable from 0.0 over a corpus")
    assert "not-measured (no derivation)" in out.report()


def test_control_a_run_WITH_derivations_reports_a_real_layer1_fraction():
    mod = political()
    out = r3.render_r3(mod, [POL_FIRES])
    assert out.nodes
    assert out.layer1_fraction is not None
    assert "not-measured" not in out.report()


def test_a_DEFINES_rule_is_annotated_exactly_as_an_ontology_rule_is():
    """R11. `module_program`'s own docstring: *"`defines` and `ontology` are
    annotated too… an unannotated rule is INVISIBLE to xclingo, so leaving them
    bare would silently flatten a derivation… a shorter tree that reads like a
    simpler explanation."* The ONTOLOGY half is pinned by
    `test_an_ontology_step_becomes_an_INTERIOR_node_with_its_own_sentence`.
    The `defines` half was pinned by nothing — no fixture puts a `defines`
    inside a derivation — so the annotation could be dropped outright."""
    mod = schema.validate(dict(
        outcome="translated", clause_id="m0053", abstain_reason=None,
        claims=["C1 terrorism is a harm category"], acts=[], concepts=[],
        ontology=[], asserts=[], beats=[],
        defines=[dict(kind="harm_category", term="terrorism",
                      licence="textual", cites="m0053", inference=None,
                      toggleable=False)],
        closure=[], requires=[], inputs=[], forbid_body=[]))
    notes = []
    renderings = readback.render_items(mod, readback.gloss_table(mod), notes)
    program = r3.module_program(mod, renderings, notes)
    lines = [l for l in program.splitlines() if l.strip()]
    body = "defines(m0053, harm_category, terrorism)."
    assert body in lines
    assert lines[lines.index(body) - 1].startswith('%!trace_rule {"'), (
        f"the `defines` rule is bare, so xclingo cannot see it and any "
        f"derivation through it is silently flattened: {lines}")
