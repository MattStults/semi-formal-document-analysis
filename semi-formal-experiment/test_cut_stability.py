"""Tests for cut_stability.py — the cut-stability diagnostic.

Pins, per the diagnostic's contract:
  1. DETERMINISM — same fixture snapshots in, byte-identical results file out,
     twice, with a fixed literal seed and no wall clock.
  2. BYSTANDER CENSUS — the ±epsilon census on a constructed score vector
     returns exactly the known ids and counts, and never a zero-score clause.
  3. FENCE — the module's source (comments/docstrings stripped) names no
     FORBIDDEN token from test_no_reference_leak, and no wall-clock source.
  4. OPEN SPY — a full run() opens only the declared snapshot files and the
     declared output path (mirrors the dynamic guard's posture, scoped to
     this read-only diagnostic).
"""
from __future__ import annotations

import builtins
import inspect
import json
import os
import re

import pytest

import cut_stability
import threshold as threshold_rules
from test_no_reference_leak import FORBIDDEN

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------- fixtures

def _bimodal_scores(n_low=24, n_high=8):
    """A clean two-mode score vector with a known near-cut population."""
    scores = {}
    for i in range(n_low):
        scores[f"lo{i:02d}"] = round(0.05 + 0.006 * i, 10)   # 0.05 .. 0.188
    for i in range(n_high):
        scores[f"hi{i:02d}"] = round(0.70 + 0.03 * i, 10)    # 0.70 .. 0.91
    scores["zz_zero"] = 0.0                                   # never predicted
    return scores


def _fixture_snapshot(tag):
    scores = _bimodal_scores()
    positives = [s for s in scores.values() if s > 0]
    cut = threshold_rules.otsu(positives)
    return {
        "tag": tag,
        "config": {"inputs": {}, "weights": {}, "threshold_rule": "otsu"},
        "behaviours": {
            "beh-a": {
                "threshold": round(cut, 10),
                "predicted": sorted(k for k, s in scores.items()
                                    if s > 0 and s >= cut),
                "scores": scores,
            },
        },
    }


def _write_fixture_dir(tmp_path, tags=("tag-a", "tag-b")):
    d = tmp_path / "snapshots"
    d.mkdir()
    for tag in tags:
        with open(d / f"{tag}.json", "w") as f:
            json.dump(_fixture_snapshot(tag), f, sort_keys=True)
    return str(d), tags


# ------------------------------------------------------------- determinism

def test_run_is_byte_deterministic(tmp_path):
    snap_dir, tags = _write_fixture_dir(tmp_path)
    out1 = str(tmp_path / "r1.json")
    out2 = str(tmp_path / "r2.json")
    cut_stability.run(snapshot_dir=snap_dir, tags=tags, out_path=out1)
    cut_stability.run(snapshot_dir=snap_dir, tags=tags, out_path=out2)
    with open(out1, "rb") as f:
        b1 = f.read()
    with open(out2, "rb") as f:
        b2 = f.read()
    assert b1 == b2, "two runs over identical inputs differ — RNG or clock leak"
    assert json.loads(b1)["seed"] == cut_stability.SEED


def test_seed_is_a_fixed_literal():
    src = inspect.getsource(cut_stability)
    assert re.search(r"^SEED\s*=\s*\d+$", src, re.M), (
        "SEED must be a literal integer assignment, not derived at runtime")


# -------------------------------------------------------- bystander census

def test_bystander_census_on_constructed_vector():
    scores = {"a": 0.30, "b": 0.315, "c": 0.29, "d": 0.50, "e": 0.0}
    census = cut_stability.bystander_census(scores, cut=0.30,
                                            epsilons=(0.005, 0.02, 0.25))
    assert census["0.005"] == {"count": 1, "ids": ["a"]}
    assert census["0.02"] == {"count": 3, "ids": ["a", "b", "c"]}
    # eps=0.25 reaches d (0.50 is 0.20 away) but must NEVER admit the
    # zero-score clause e, whatever the epsilon: predict() requires s > 0.
    assert census["0.25"] == {"count": 4, "ids": ["a", "b", "c", "d"]}


def test_band_bystanders_are_inclusive_and_positive_only():
    scores = {"a": 0.30, "b": 0.315, "c": 0.29, "d": 0.50, "e": 0.0}
    got = cut_stability.band_bystanders(scores, lo=0.29, hi=0.315)
    assert got == ["a", "b", "c"]


# ------------------------------------------------------------------- fence

def test_source_is_fence_clean():
    src = inspect.getsource(cut_stability)
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    hits = [tok for tok in FORBIDDEN if tok in src]
    assert not hits, f"cut_stability.py names the reference: {hits}"
    clock = [tok for tok in ("time.time", "datetime", "utcnow", "perf_counter")
             if tok in src]
    assert not clock, f"cut_stability.py reads a clock: {clock} — determinism"


def test_run_opens_only_declared_files(tmp_path):
    snap_dir, tags = _write_fixture_dir(tmp_path)
    out = str(tmp_path / "results.json")

    import io as _io
    opened = []
    saved = {"builtins": builtins.open, "io": _io.open, "os": os.open}

    def mk(real):
        def spy(path, *a, **kw):
            try:
                opened.append(os.path.abspath(str(path)))
            except Exception:
                pass
            return real(path, *a, **kw)
        return spy

    builtins.open = mk(saved["builtins"])
    _io.open = mk(saved["io"])
    os.open = mk(saved["os"])
    try:
        cut_stability.run(snapshot_dir=snap_dir, tags=tags, out_path=out)
    finally:
        builtins.open = saved["builtins"]
        _io.open = saved["io"]
        os.open = saved["os"]

    declared = {os.path.abspath(os.path.join(snap_dir, f"{t}.json"))
                for t in tags} | {os.path.abspath(out)}
    unexpected = [p for p in opened
                  if p not in declared
                  and not p.endswith((".py", ".pyc", ".md", ".txt",
                                      ".ini", ".cfg"))
                  and "/site-packages/" not in p and "/lib/python" not in p]
    assert not unexpected, (
        f"cut_stability.run opened UNDECLARED files: {sorted(set(unexpected))}")


# ------------------------------------------------------------- band stats

def test_band_stats_filters_degenerate_cuts():
    cuts = [0.30, 0.31, 0.30, threshold_rules.DEGENERATE_CUT]
    stats = cut_stability.band_stats(cuts)
    assert stats["n_degenerate"] == 1
    assert stats["n"] == 3
    assert stats["min"] == 0.30 and stats["max"] == 0.31
    assert 0.30 <= stats["q05"] <= stats["q50"] <= stats["q95"] <= 0.31
