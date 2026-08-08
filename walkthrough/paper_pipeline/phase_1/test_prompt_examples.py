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
#: The deliberately-broken examples start here. ⚠️ Matched by SHAPE, not by the
#: exact wording: pinning "## The five bad ones" meant that adding a sixth bad
#: example — an ordinary, desirable edit — failed this test and reported the
#: improvement as a defect. That is DEBUGGING_TIPS entry 9, and it has now bitten
#: four times in this repo.
BAD_HEADING_RE = re.compile(r"^##\s+The\s+\w+\s+bad\s+ones\s*$", re.M | re.I)


def _good_region(path):
    """The part of a prompt file before the deliberately-broken examples."""
    text = open(path, encoding="utf-8").read()
    m = BAD_HEADING_RE.search(text)
    return text[:m.start()] if m else text


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
    """If this fails, `_good_region` returns the WHOLE file and every check
    below is asserting that a deliberately broken module passes. That is the
    silent-vacuous-pass failure, so it gets its own test."""
    assert BAD_HEADING_RE.search(open(WORKED, encoding="utf-8").read()), (
        "no '## The <n> bad ones' heading found; the good/bad split is gone "
        "and every example check below is now vacuous")


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


# ==========================================================================
# translate.py --self-test must RUN. It was the only self-test not in pytest.
# ==========================================================================

def test_translate_self_test_runs_to_completion():
    """⛔ THE GAP THIS CLOSES. `link.py --self-test` and `guard.py --self-test`
    are both driven from pytest. `translate.py --self-test` was not — so when a
    bare-fenced ASP block was added to `20_worked_example.md`, its example
    extractor called `json.loads` on ASP and died with a traceback before a
    single check ran. **pytest stayed green at 294 while the self-test was
    crashing outright**, which is this project's signature failure: a check that
    cannot run must not be reachable from the same state as a check that passed.

    ⚠️ Asserts the run COMPLETES and REPORTS, not a pass count. Pinning "53
    passed" would fail the moment someone legitimately adds a check
    (DEBUGGING_TIPS entry 9). A crash is the thing being caught here; individual
    check failures are visible in the summary and are a separate question.
    """
    import subprocess
    r = subprocess.run(
        [sys.executable, os.path.join(HERE, "translate.py"), "--self-test"],
        cwd=HERE, capture_output=True, text=True)
    out = r.stdout + r.stderr
    assert "Traceback" not in out, (
        "translate.py --self-test crashed instead of reporting:\n" + out[-2000:])
    assert re.search(r"\d+ passed", out), (
        "no summary line — the self-test did not reach its own report:\n"
        + out[-2000:])


def test_every_json_block_in_the_prompt_is_valid_json():
    """The narrower defect underneath the crash: a worked example whose JSON is
    not parseable. A `gloss` string was written across two source lines, which
    is invalid JSON. It sat in the BAD-examples section, so the good-example
    checks above skipped it by design — and the model is still shown it.
    """
    import glob
    bad = []
    for path in sorted(glob.glob(os.path.join(HERE, "prompt", "*.md"))):
        text = open(path, encoding="utf-8").read()
        for i, block in enumerate(re.findall(r"```json\s*\n(.*?)```", text, re.S)):
            # `...` is a deliberate "and the rest of the fields" placeholder in
            # partial fragments, and is not a defect. Strip it (and a dangling
            # comma) and require what REMAINS to parse — a fragment must still
            # be well-formed, which is what catches a string broken across two
            # source lines.
            probe = re.sub(r",?\s*\.\.\.\s*", "", block)
            try:
                json.loads(probe)
            except json.JSONDecodeError as exc:
                bad.append(f"{os.path.basename(path)} block {i + 1}: {exc}")
    assert not bad, "\n".join(bad)
