"""Tests for `semantic_arm.py` — the embedding diagnostic.

Same two jobs as `test_weight_diag.py`. Pin the CONTRACT (this thing may never
ship, and nothing may import it), and pin the handful of properties that make
its numbers readable at all.

The arms themselves need numpy/sklearn and, for arm B, a cached embedding
table, so the measurement is not re-run here — `semantic_arm_results.json` and
`SEMANTIC_ARM_RESULTS.md` carry it. What is pinned here is everything that
would let a WRONG number look like a right one.
"""
import glob
import json
import os
import re

import pytest

import semantic_arm as SA

REPO = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------- the contract

def test_module_declares_itself_a_one_shot_diagnostic():
    doc = SA.__doc__
    assert "DIAGNOSTIC" in doc
    assert "MAY EVER SHIP" in doc
    assert "SEMANTIC_ARM_PREREGISTRATION.md" in doc


def test_no_repo_module_imports_semantic_arm():
    """A dense per-passage embedding table with a consumer is a dense channel,
    which contract §5 invariant 10 forbids outright. `semantic_arm_ci` is the
    one legitimate consumer: it is the CI companion, and is itself covered by
    the `semantic_arm` prefix entry in `test_no_reference_leak.FORBIDDEN`."""
    offenders = []
    for path in glob.glob(os.path.join(REPO, "*.py")):
        name = os.path.basename(path)
        if name in ("semantic_arm.py", "semantic_arm_ci.py",
                    "test_semantic_arm.py"):
            continue
        with open(path) as fh:
            src = fh.read()
        if re.search(r"^\s*(import|from)\s+semantic_arm\b", src, re.M):
            offenders.append(name)
    assert offenders == [], f"semantic_arm has consumers: {offenders}"


def test_it_is_fenced_from_every_query_module():
    import test_no_reference_leak as NRL
    assert "semantic_arm" in NRL.FORBIDDEN


# ------------------------------------------------- the pre-registration bond

def test_preregistration_exists_and_still_carries_its_frozen_predictions():
    """The predictions are the whole evidential value of this arm. If the file
    is edited down to match the outcome, the arm becomes a story about numbers
    that were always going to come out that way."""
    path = os.path.join(REPO, "SEMANTIC_ARM_PREREGISTRATION.md")
    text = open(path).read()
    for marker in ("**P1.**", "**P2.**", "**P3.**", "**P4.**", "**P5.**",
                   "**P6 (Arm B).**"):
        assert marker in text, f"{marker} vanished from the pre-registration"
    assert "PREDICTIONS — frozen" in text
    assert "+0.40" in text          # the falsification bar
    assert "0.045" in text          # the declared noise floor
    assert "power caveat" in text.lower()


def test_the_falsification_bar_is_stated_in_both_directions():
    text = open(os.path.join(REPO, "SEMANTIC_ARM_PREREGISTRATION.md")).read()
    assert "What would falsify" in text
    assert "What would confirm" in text
    assert "settles nothing" in text


# ------------------------------------------------------------ the mechanics

def test_the_api_key_is_never_written_into_any_artifact():
    """`_openai_key` parses ~/.zshrc. A key that reaches the results JSON or a
    print statement is a leaked credential in a git repo."""
    src = open(os.path.join(REPO, "semantic_arm.py")).read()
    body = src.split("def _openai_key")[1].split("\ndef ")[0]
    assert "print(" not in body
    assert "json.dump" not in body
    # the key is only ever an Authorization header value
    assert src.count("OPENAI_API_KEY") <= 3


def test_arm_a_never_reaches_an_external_corpus():
    """Arm A's whole meaning is 'the document and nothing else'. If it ever
    learns from outside text it stops answering the question it was built for."""
    src = open(os.path.join(REPO, "semantic_arm.py")).read()
    body = src.split("def arm_a_vectors")[1].split("\n# ---")[0]
    for tok in ("urllib", "openai", "_embed_batch", "_openai_key", "requests"):
        assert tok not in body, f"arm A reaches outside the document via {tok}"


def test_both_arms_score_the_same_universe_and_the_same_cells():
    """A ranking comparison across arms is meaningless if the arms disagree
    about which passages exist."""
    src = open(os.path.join(REPO, "semantic_arm.py")).read()
    assert "D.locs" in src
    assert "D.cells()" in src
    # neither arm may filter the universe
    assert "D.locs[:" not in src


@pytest.mark.parametrize("k", SA.DIMS)
def test_the_dimension_sweep_is_declared_not_chosen(k):
    """No k may be selected on the panel — every one is reported. This is the
    exact shape of the withdrawn `rho` lead, one level out."""
    assert isinstance(k, int) and k > 0
    text = open(os.path.join(REPO, "SEMANTIC_ARM_PREREGISTRATION.md")).read()
    assert str(k) in text


def test_results_json_if_present_reports_every_variant_including_losers():
    """`LABEL_FREE_VARIANTS` keeps its losers on purpose — 'a variant removed
    after it lost is a variant the next reader will propose again'. Same rule
    here: a results file pruned to the winners is a fitted result."""
    path = os.path.join(REPO, "semantic_arm_results.json")
    if not os.path.exists(path):
        pytest.skip("arms not yet run in this checkout")
    r = json.load(open(path))
    assert any(k.startswith("ANCHOR/") for k in r), "no anchor to read against"
    assert any("passage-text cosine" in k for k in r), \
        "the losing scorer was pruned from the results"
    for key, row in r.items():
        assert set(row) >= {"mcc", "auc", "cells"}
        assert len(row["cells"]) == len(r[key]["cells"])
        assert -1.0 <= row["mcc"] <= 1.0
        assert 0.0 <= row["auc"] <= 1.0
