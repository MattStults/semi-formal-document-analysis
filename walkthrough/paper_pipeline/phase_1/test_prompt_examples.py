"""Every GOOD example in the prompt must survive stage 2.

An example is an instruction with a picture attached, and it outranks the prose:
a model shown a module that would fail our own checks has been told, in the most
credible form available, that the failure is acceptable. There is no way to
notice that by reading — the example looks like the surrounding text.

⛔ THE ONE THAT MOTIVATED THIS. Across all four prompt files the ontology block
was demonstrated by 5 ground facts and 1 conditional entry, and the worked
example itself contained no derived predicate at all. The dominant stage-2
failure on held-out clauses -- 59 in 36 first attempts -- was a whole rule
written into `atom`, on exactly the clauses that need conditional entries. The
prompt forbade the wrong shape in prose and never showed the right one.

⚠️ ONLY THE GOOD EXAMPLES. `20_worked_example.md` ends with five deliberately
broken modules, and a test that demanded those pass would be demanding the
prompt stop teaching. The split is the `## The five bad ones` heading: fragments
below it are excluded, and a separate test asserts that heading still exists, so
renaming it cannot silently switch this check off.
"""

import json
import os
import re
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import checks  # noqa: E402
import schema as S  # noqa: E402
import translate as T  # noqa: E402

WORKED = os.path.join(HERE, "prompt", "20_worked_example.md")
BAD_HEADING = "## The five bad ones"


def _good_region(path):
    """The part of a prompt file before the deliberately-broken examples."""
    text = open(path, encoding="utf-8").read()
    return text.split(BAD_HEADING)[0]


def _modules(text):
    """Every fenced json block that is a whole module (has `clause_id`)."""
    out = []
    for m in re.finditer(r"```json\n(.*?)```", text, re.S):
        body = m.group(1)
        try:
            obj = json.loads(body)
        except json.JSONDecodeError:
            continue                      # a field fragment, not a module
        if isinstance(obj, dict) and "clause_id" in obj and "outcome" in obj:
            out.append(obj)
    return out


@pytest.fixture(scope="module")
def corpus():
    cfg = T.load_config(os.path.join(HERE, "config.json"))
    rows = T.load_corpus(cfg)
    return {c["id"]: c for c in rows}


def _good_modules():
    return _modules(_good_region(WORKED))


def test_the_bad_examples_heading_still_exists():
    """If this fails, `_good_region` is silently returning the whole file and
    every check below is asserting that a deliberately broken module passes."""
    assert BAD_HEADING in open(WORKED, encoding="utf-8").read()


def test_there_are_good_modules_to_check():
    """A regex that matches nothing passes every loop below vacuously. This
    project has shipped that exact failure more than once."""
    mods = _good_modules()
    assert len(mods) >= 3, f"expected at least 3 good worked modules, found {len(mods)}"


@pytest.mark.parametrize("obj", _good_modules(),
                         ids=[m["clause_id"] for m in _good_modules()])
def test_a_good_worked_example_passes_stage_2(obj, corpus):
    cid = obj["clause_id"]
    assert cid in corpus, (
        f"the worked example cites {cid}, which is not a clause in the corpus; "
        f"a model told to imitate it would be imitating a fiction")
    res = checks.run_checks(obj, corpus[cid], set(corpus), attempt=1)
    errors = [f for f in res.findings if f.severity == "error"]
    assert not errors, "\n".join(
        f"[{f.check_id}] {f.where}: {f.message}" for f in errors)
    assert res.outcome == "translated", (
        f"{cid} is shown as a good example but stage 2 calls it {res.outcome}")


def test_the_ontology_block_is_demonstrated_with_a_BODY_somewhere():
    """The gap this file exists for, pinned so it cannot reopen.

    Counting conditional entries rather than pinning a number: a later example
    that adds more is a legitimate improvement and must not fail its own gate.
    """
    entries = [e for obj in _good_modules() for e in (obj.get("ontology") or [])]
    conditional = [e for e in entries if (e.get("body") or "").strip()]
    assert conditional, (
        "no worked example shows an ontology entry with a body. The model is "
        "then told, by demonstration, that `ontology` holds ground facts only "
        "-- and the commonest stage-2 failure is a rule written into `atom`")
    assert len(conditional) >= 3, (
        f"only {len(conditional)} conditional ontology entr(ies) demonstrated; "
        f"the shapes a definition needs are a conjunctive body and alternatives")


def test_alternatives_are_demonstrated_by_a_REPEATED_atom():
    """`p :- a.` / `p :- b.` has no other expression: there is no disjunction
    inside a body. Verified reachable through `schema.validate_all`, so this is
    a documented capability rather than an accident."""
    for obj in _good_modules():
        atoms = [e["atom"] for e in (obj.get("ontology") or []) if e.get("body")]
        heads = [a.split("(")[0].strip() for a in atoms]
        if len(heads) != len(set(heads)):
            return
    pytest.fail("no worked example repeats an atom with two different bodies; "
                "a clause with alternative sufficient conditions has no "
                "demonstrated route and the model invents one")


def test_every_good_example_renders_to_loadable_asp(corpus):
    """A module can satisfy the schema and still produce a file clingo refuses."""
    for obj in _good_modules():
        cid = obj["clause_id"]
        mod, breaches = S.validate_all(obj, cid, set(corpus))
        assert mod is not None, f"{cid}: " + "; ".join(b.message for b in breaches)
        text = S.render_lp(mod, corpus[cid])
        assert text.strip(), f"{cid} rendered to nothing"


# ==========================================================================
# link.header — the `%% acts:` list is not a flat comma list
# ==========================================================================

def test_an_act_with_arity_above_one_is_ONE_act_not_several(tmp_path):
    """⛔ `%% acts:` was split on every comma, so `respond(A, B)` became two
    act classes. Both fragments then looked like act classes with no closure
    declaration, and `closure-missing` is an ERROR: the model was sent back to
    fix acts it had never written, named in a message reading
    `governs act class(es) CoT), Input), Outputs), Seq)`.

    Found on a held-out run, not by a test — a spurious error that inflates the
    finding count and burns a repair attempt looks exactly like a real one.
    """
    import link
    p = tmp_path / "m.lp"
    p.write_text("%% acts: respond(CoT, Input, Outputs, Seq), refuse(M)\n",
                 encoding="utf-8")
    h = link.header(str(p))
    assert h["acts"] == {"respond(CoT, Input, Outputs, Seq)", "refuse(M)"}
    assert {a.split("(")[0].strip() for a in h["acts"]} == {"respond", "refuse"}


def test_nested_parentheses_in_an_act_survive(tmp_path):
    import link
    p = tmp_path / "m.lp"
    p.write_text("%% acts: emit(wrap(A, B), C), plain\n", encoding="utf-8")
    h = link.header(str(p))
    assert h["acts"] == {"emit(wrap(A, B), C)", "plain"}


def test_a_simple_act_list_is_unchanged(tmp_path):
    import link
    p = tmp_path / "m.lp"
    p.write_text("%% acts: respond(M), refuse(M), escalate\n", encoding="utf-8")
    h = link.header(str(p))
    assert h["acts"] == {"respond(M)", "refuse(M)", "escalate"}
