"""Two defects that both hide in ARITHMETIC OVER A RECORD, not in the record.

    ../../../semi-formal-experiment/.venv/bin/python -m pytest \
        walkthrough/paper_pipeline/phase_1/test_cost_and_summary.py -q

⭐ Both were found by an audit, both were already "fixed" once, and both
survived the fix because the test asserted on the STORED VALUE and the defect
was in a number DERIVED from it:

* `estimate_cost` was made triangular in `max_attempts` — and priced only
  `system + user`, never the prior completions the transcript actually resends.
  The test that pinned the triangularity (`three > one * 2.5`) cannot see the
  input term at all: with `max_tokens=1000` and the strings `"sys"`/`"user"`,
  the OUTPUT term alone gives exactly 3×.
* `abstained_under_repair` was made to survive into `run.json` — and the run
  summary, one line below, still partitioned on `status == "abstained"`, so it
  counted the refusal as a translation. The test that closed it reads
  `run.json` and never the printed line.

⇒ Every assertion here is on the DERIVED number: the estimate returned, and the
summary line as printed.
"""

import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import fixtures                    # noqa: E402  ⭐ the shared stage-1 fixtures
import translate as T              # noqa: E402  the module under test


# ==========================================================================
#  1.  The cost estimate must be a WORST case, in the direction it claims
# ==========================================================================
#
# `config.json`: "Overstating an estimate is survivable; understating is how a
# hard cap gets passed." `README.md`: cost is triangular "because each repair
# turn resends the transcript". The transcript contains the prior COMPLETIONS,
# and that term was missing — so both documents asserted conservatism while the
# number was anti-conservative, on a project with a hard $8.50 ledger.


def _hand_priced_worst_case(system, users, prov, cfg, max_attempts):
    """The check `DEBUGGING_TIPS.md` §12 tells you to run, as code.

    Attempt 1 sends `system + user`. Attempt k additionally re-sends every
    earlier completion, each of which may be the full `max_tokens` — that is
    what `finish_reason=length` is raised on, so it is reachable, not
    hypothetical. Output is `max_tokens` per attempt.

    ⚠️ Deliberately written out attempt by attempt rather than as a closed
    form. The closed form is what the code under test uses; re-deriving it here
    would let one algebra slip pass both.
    """
    cpt = float(cfg["cost"]["chars_per_token"])
    pin, pout = prov.price_per_mtok
    in_tok = out_tok = 0.0
    for u in users:
        for k in range(1, max(1, int(max_attempts)) + 1):
            in_tok += (len(system) + len(u)) / cpt + (k - 1) * prov.max_tokens
            out_tok += prov.max_tokens
    return (in_tok / 1e6) * pin + (out_tok / 1e6) * pout


def _shipped_provider(cfg):
    """The prices and `max_tokens` this repo actually ships."""
    return T.Provider("together", "openai-compatible", "m", "u", "K", 0.2,
                      int(cfg["model"]["max_tokens"]),
                      list(cfg["cost"].get("price_per_mtok")
                           or cfg["model"]["price_per_mtok"]))


def test_the_estimate_is_NOT_BELOW_a_hand_priced_worst_case():
    """The defect, at the shipped `max_attempts: 3`: 12.7 % low.

    ⭐ The strings must be REALISTIC or this test is blind. The completion term
    is `max_tokens` (16,384 tokens ≈ 12× the user block); against the 3-char
    fixtures the older test uses it would be swamped and an assertion on the
    total would pass with the term absent.
    """
    cfg = T.load_config(str(HERE / "config.json"))
    prov = _shipped_provider(cfg)
    system = "s" * 33614                      # the real stage-1 system block
    users = ["u" * 5341]                      # m0091's user block

    for attempts in (1, 2, 3, 4, 5):
        est, _, _ = T.estimate_cost(system, users, prov, cfg,
                                    max_attempts=attempts)
        floor = _hand_priced_worst_case(system, users, prov, cfg, attempts)
        assert est >= floor, (
            f"max_attempts={attempts}: the printed worst case is ${est:.6f} "
            f"and the true worst case is ${floor:.6f} — the estimate is "
            f"{(floor - est) / est * 100:.1f} % LOW. Over-estimating is "
            f"survivable; this is the other direction, and two documents "
            f"assert it cannot happen")


def test_the_completion_carried_forward_is_priced_as_INPUT():
    """The specific missing term, isolated from everything else.

    Holding `system`, `users` and the attempt count fixed, raising ONLY
    `max_tokens` must raise the INPUT token count — because the thing the
    transcript carries forward is a completion, and a completion is bounded by
    `max_tokens`. Before the fix the input term did not depend on `max_tokens`
    at all, so this reads 0.
    """
    cfg = T.load_config(str(HERE / "config.json"))
    small = T.Provider("p", "openai-compatible", "m", "u", "K", 0.2,
                       1_000, [1.0, 1.0])
    large = T.Provider("p", "openai-compatible", "m", "u", "K", 0.2,
                       100_000, [1.0, 1.0])
    _, in_small, _ = T.estimate_cost("s" * 4000, ["u" * 400], small, cfg,
                                     max_attempts=3)
    _, in_large, _ = T.estimate_cost("s" * 4000, ["u" * 400], large, cfg,
                                     max_attempts=3)
    assert in_large > in_small, (
        f"input tokens are {in_small} either way, so the prior completion is "
        f"not being billed as input on the next attempt")
    # Two attempts carry a completion forward at max_attempts=3 (attempt 2
    # carries one, attempt 3 carries two): 3 completions' worth of difference.
    assert in_large - in_small >= 3 * (100_000 - 1_000), (in_small, in_large)


def test_one_attempt_bills_no_carried_completion():
    """The guard that must kill the two tests above.

    With repair disabled there is no prior completion, so `max_tokens` must
    move the OUTPUT term and leave the input term alone. Without this, simply
    inflating the estimate passes everything.
    """
    cfg = T.load_config(str(HERE / "config.json"))
    a = T.Provider("p", "openai-compatible", "m", "u", "K", 0.2, 1_000,
                   [1.0, 1.0])
    b = T.Provider("p", "openai-compatible", "m", "u", "K", 0.2, 100_000,
                   [1.0, 1.0])
    _, in_a, out_a = T.estimate_cost("s" * 4000, ["u" * 400], a, cfg,
                                     max_attempts=1)
    _, in_b, out_b = T.estimate_cost("s" * 4000, ["u" * 400], b, cfg,
                                     max_attempts=1)
    assert in_a == in_b, (in_a, in_b)
    assert out_b > out_a, (out_a, out_b)


# ==========================================================================
#  2.  The run summary must partition on the WHOLE status set
# ==========================================================================

def _run_one(tmp_path, cfg_over, stub, clause="m0091"):
    """A single-clause live-shaped run against a stub client.

    ⚠️ ISOLATE THE GRAVEYARD (`conftest.py` fails the session otherwise): a
    test calling `run()` without this writes into the repo's production
    graveyard, and a full graveyard REFUSES to start a real run.
    """
    cfg = copy.deepcopy(T.load_config(str(HERE / "config.json")))
    cfg["select"] = {"clause_ids": [clause], "section_id": None, "kinds": [],
                     "limit": None}
    cfg["output"] = {"dir": str(tmp_path), "run_name": "t"}
    cfg["graveyard"] = {"dir": str(tmp_path / "gy"), "cap": 1000, "seed": 0,
                        "rates": {"repaired": 0.0, "first_try": 0.0}}
    cfg.update(cfg_over)

    class A:
        clause = section = kinds = limit = provider = model = max_tokens = None
        live = True
        show_prompt = 0

    code = T.run(cfg, A(), client_factory=stub)
    rec = json.loads((tmp_path / "t" / "run.json").read_text())
    return code, rec


BROKEN = fixtures.module_json(
    clause_id="m0091",
    asserts=[fixtures.assertion(read_back="producing this is forbidden",
                                read_back_slots=["M"])])   # 0 slots, 1 entry


class _AbstainsUnderRepair:
    """Attempt 1 breaches the schema; attempt 2 declines to translate.

    That is the exact sequence the `abstained_under_repair` status exists to
    name: not a first-attempt refusal (a real answer) but one produced under
    repair pressure, after the model was told it was wrong.
    """

    def __init__(self, *a, **k):
        pass

    def complete(self, s, u):
        return {"text": BROKEN, "in": 1, "out": 1, "finish_reason": "stop"}

    def complete_messages(self, s, m):
        return {"text": fixtures.abstention_json(
            clause_id="m0091",
            abstain_reason="it states a goal, not a condition"),
            "in": 1, "out": 1, "finish_reason": "stop"}


def test_the_PRINTED_SUMMARY_does_not_count_an_abstention_as_a_translation(
        tmp_path, capsys):
    """⛔ The one line a human reads, not the field a test reads.

    `run()` computed `n_ab` as `status == "abstained"` exactly and printed
    `len(results) - failures - n_ab` as the translated count.
    `abstained_under_repair` matches neither that nor the failure branch — it
    is admitted on the success branch — so it landed in "translated". A clause
    the model refused after two failed attempts was reported as a success.

    The record was fixed and pinned (`test_repair.py`
    ::test_abstained_UNDER_REPAIR_survives_into_the_record). The ARITHMETIC
    OVER the record was not, and that test cannot see it: it reads `run.json`.
    """
    _, rec = _run_one(tmp_path, {"repair": {"max_attempts": 2}},
                      _AbstainsUnderRepair)
    # The premise. If this ever changes, the test below is measuring nothing.
    assert rec["results"][0]["status"] == "abstained_under_repair", rec

    line = [ln for ln in capsys.readouterr().out.splitlines()
            if "translated" in ln and "failed" in ln]
    assert len(line) == 1, f"expected exactly one summary line, got {line}"
    line = line[0]
    assert line.startswith("0 translated"), (
        f"one clause ran and it ABSTAINED under repair; the summary says "
        f"{line!r}")
    assert "1 abstained under repair" in line, line


def test_the_PRINTED_SUMMARY_still_counts_a_real_translation(tmp_path, capsys):
    """The guard that must kill the test above — `0 translated` always passes
    a run that translated nothing."""
    clean = fixtures.module_json(clause_id="m0091")

    class Stub:
        def __init__(self, *a, **k):
            pass

        def complete(self, s, u):
            return {"text": clean, "in": 1, "out": 1, "finish_reason": "stop"}

        def complete_messages(self, s, m):
            raise AssertionError("a clean module must not enter repair")

    _, rec = _run_one(tmp_path, {"repair": {"max_attempts": 2}}, Stub)
    assert rec["results"][0]["status"] == "translated", rec
    line = [ln for ln in capsys.readouterr().out.splitlines()
            if "translated" in ln and "failed" in ln][0]
    assert line.startswith("1 translated"), line
    assert "0 abstained under repair" in line, line
