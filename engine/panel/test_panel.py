#!/usr/bin/env python3
"""Unit tests for the panel pipeline's pure logic. No network, no keys, sub-second.

Each test class names the shipped bug it guards against (all found in review or
the ~2-cent integration run of 2026-07-30). Run:  python3 engine/panel/test_panel.py
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


h = load("harness")
rr = load("run_rollout")
wd = load("whole_doc")
bs = load("build_site_data")


class TestParseVerdicts(unittest.TestCase):
    """Guards the K3/whole-doc parsing failures: truncation, renumbering, noise."""

    def test_ternary_keyed_lines(self):
        out = "\n".join(f"{i}: {v}" for i, v in enumerate([2, 1, 0, 2], 1))
        self.assertEqual(h.parse_verdicts(out, 4), {1: 2, 2: 1, 3: 0, 4: 2})

    def test_out_of_range_indices_dropped(self):
        out = "1: 2\n2: 1\n999: 2\n3: 0\n4: 1"
        v = h.parse_verdicts(out, 4)
        self.assertNotIn(999, v)
        self.assertEqual(len(v), 4)

    def test_truncated_output_reports_missing_not_zeros(self):
        # 374-passage response cut off at 300 lines: the missing 74 must be ABSENT
        # from the dict (unparsed), never silently graded 0.
        out = "\n".join(f"{i}: 1" for i in range(1, 301))
        v = h.parse_verdicts(out, 374)
        self.assertEqual(len(v), 300)
        self.assertNotIn(374, v)

    def test_tail_fallback_requires_exact_count(self):
        # bare digits without "n:" keys, one short of n -- must refuse to guess
        out = "\n".join("2" for _ in range(9))
        self.assertEqual(h.parse_verdicts(out, 10), {})

    def test_reasoning_prose_does_not_shift_alignment(self):
        # in-content reasoning with digits above the verdict block (the K3 style)
        out = "Passage 3 discusses 2 things about 1 topic.\n" + \
              "\n".join(f"{i}: 0" for i in range(1, 41))
        v = h.parse_verdicts(out, 40)
        self.assertEqual(v, {i: 0 for i in range(1, 41)})


class TestBuildPlan(unittest.TestCase):
    """Guards the resume blocker: banked cells must be skipped, rubric-scoped."""

    FIRST = {"constitution": "c@1 > A > ¶1", "model-spec": "m@1 > #a > ¶1"}

    def setUp(self):
        self._runlog = h.RUNLOG
        self.addCleanup(lambda: setattr(h, "RUNLOG", self._runlog))

    def synth_runlog(self, rows):
        f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
        for r in rows:
            f.write(json.dumps(r) + "\n")
        f.close()
        self.addCleanup(lambda p=Path(f.name): p.unlink(missing_ok=True))
        return Path(f.name)

    def test_banked_cell_is_resumed(self):
        log = self.synth_runlog([{"behaviour": "b1", "spec": "constitution", "model": "sol",
                                  "locator": self.FIRST["constitution"], "rubric": "v3w"}])
        h.RUNLOG = log
        done = h.done_keys("v3w")
        plan, skipped = rr.build_plan(["b1"], ["constitution"], ["sol", "fable"], done, self.FIRST)
        self.assertEqual(skipped, [("b1", "constitution", "sol")])
        self.assertEqual(plan, [("b1", "constitution", "fable")])

    def test_other_rubric_rows_do_not_satisfy_resume(self):
        # the original bug's cousin: v1/v2 rows must never mark a v3w cell done
        log = self.synth_runlog([{"behaviour": "b1", "spec": "constitution", "model": "sol",
                                  "locator": self.FIRST["constitution"], "rubric": "v2"}])
        h.RUNLOG = log
        plan, skipped = rr.build_plan(["b1"], ["constitution"], ["sol"],
                                      h.done_keys("v3w"), self.FIRST)
        self.assertEqual(skipped, [])
        self.assertEqual(len(plan), 1)

    def test_empty_log_plans_full_grid(self):
        h.RUNLOG = Path("/nonexistent/runlog.jsonl")
        plan, skipped = rr.build_plan(["b1", "b2"], ["constitution", "model-spec"],
                                      ["sol", "fable", "kimi"], h.done_keys("v3w"), self.FIRST)
        self.assertEqual(len(plan), 12)
        self.assertEqual(skipped, [])


class TestEstimate(unittest.TestCase):
    """Estimate must be config-derived so it stays meaningful for ANY configured
    model (a hardcoded table crashed on new tags and guessed 10 cents)."""

    MODELS = {"pricey": {"price_per_mtok": [10.0, 50.0], "max_output": 32768},
              "cheap": {"price_per_mtok": [0.1, 0.3], "max_output": 8192}}
    TOK = {"constitution": 45000}
    NP = {"constitution": 374}

    def test_any_configured_model_gets_a_real_estimate(self):
        low, high = rr.estimate([("b", "constitution", "pricey")], self.TOK, self.NP, self.MODELS)
        self.assertAlmostEqual(low, 45000/1e6*10 + 374*rr.OUT_TOKENS_PER_PASSAGE/1e6*50, places=4)
        self.assertAlmostEqual(high, 45000/1e6*10 + 32768/1e6*50, places=4)
        self.assertLess(low, high)

    def test_price_ordering_follows_config(self):
        lo_c, hi_c = rr.estimate([("b", "constitution", "cheap")], self.TOK, self.NP, self.MODELS)
        lo_p, hi_p = rr.estimate([("b", "constitution", "pricey")], self.TOK, self.NP, self.MODELS)
        self.assertLess(hi_c, lo_p)


class TestJudgeKwargs(unittest.TestCase):
    """Guards the hardcoded-65k-cap crash and the provider param quirks."""

    CONFIG = {"models": {
        "kimi": {"max_output": 65536}, "qwen-big": {"max_output": 16384},
        "sol": {}, "fable": {}, "opus": {}, "mystery": {}}}

    def test_cap_comes_from_config(self):
        self.assertEqual(wd.judge_kwargs("kimi", "moonshotai/Kimi-K3", self.CONFIG)["max_tokens"], 65536)
        self.assertEqual(wd.judge_kwargs("qwen-big", "Qwen/Qwen3-235B", self.CONFIG)["max_tokens"], 16384)

    def test_unconfigured_model_gets_sane_default_not_65k(self):
        self.assertEqual(wd.judge_kwargs("mystery", "some/other-model", self.CONFIG)["max_tokens"], 32768)

    def test_anthropic_models_never_send_temperature(self):
        for model in ("claude-fable-5", "claude-opus-4-8", "claude-haiku-4-5-20251001"):
            self.assertNotIn("temperature", wd.judge_kwargs("x", model, {"models": {"x": {}}}))

    def test_gpt5_uses_completion_tokens_and_effort(self):
        k = wd.judge_kwargs("sol", "gpt-5.6-sol", self.CONFIG)
        self.assertIn("max_completion_tokens", k)
        self.assertEqual(k["reasoning_effort"], "low")
        self.assertNotIn("temperature", k)


class TestBuilderGuards(unittest.TestCase):
    """Guards the 0-citations bug: the stray-vote guard must scale with panel size."""

    def test_single_judge_panel_keeps_its_votes(self):
        self.assertTrue(bs.keeps_citation(score=2, n_votes=1, panel_size=1))

    def test_lone_stray_vote_in_full_panel_dropped(self):
        self.assertFalse(bs.keeps_citation(score=2, n_votes=1, panel_size=3))

    def test_zero_score_dropped_regardless(self):
        self.assertFalse(bs.keeps_citation(score=0, n_votes=3, panel_size=3))

    def test_two_of_three_votes_kept(self):
        self.assertTrue(bs.keeps_citation(score=1, n_votes=2, panel_size=3))


class TestCleanQuote(unittest.TestCase):
    """Guards the constitution mid-word-bold anchor break (conten**t)."""

    def test_midword_bold_stripped(self):
        self.assertEqual(bs.clean_quote("**Information and educational conten**t: x"),
                         "Information and educational content: x")


class TestCitationQuote(unittest.TestCase):
    """Guards the 20-anchor demo failure: fenced examples render as code the
    matcher cannot see; quote must be the caption line + exampleBlock flag."""

    def test_example_block_quotes_caption_only(self):
        t = "**Example**: shoplifting deterrence tips ~~~xml <user> x </user> ~~~"
        q, ex = bs.citation_quote(t)
        self.assertEqual(q, "Example: shoplifting deterrence tips")
        self.assertTrue(ex)

    def test_fence_leading_passage_falls_back_to_full_text(self):
        q, ex = bs.citation_quote("~~~xml <user> no caption here </user> ~~~")
        self.assertTrue(q)          # never an empty quote (it would anchor wrongly)
        self.assertFalse(ex)

    def test_plain_passage_unchanged(self):
        q, ex = bs.citation_quote("An ordinary paragraph.")
        self.assertEqual(q, "An ordinary paragraph.")
        self.assertFalse(ex)


if __name__ == "__main__":
    unittest.main(verbosity=2)
