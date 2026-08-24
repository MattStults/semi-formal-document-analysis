"""Docs-tests for CALCULUS_RUNBOOK.md: every tool, artifact, and doc the
runbook names must exist and expose what the runbook claims."""
import os, re, json
HERE = os.path.dirname(os.path.abspath(__file__))
RB = open(os.path.join(HERE, "CALCULUS_RUNBOOK.md")).read()

def test_referenced_files_exist():
    for f in ("ERROR_CALCULUS.md", "route.py", "probe.py",
              "HYPOTHESIS_LEDGER.jsonl", "LINEAGE_SEAT_INSTRUCTION.md",
              "trace_check.py"):
        assert f in RB, f"runbook stopped referencing {f}"
        assert os.path.exists(os.path.join(HERE, f)), f"{f} missing on disk"

def test_tools_expose_claimed_entry_points():
    import importlib, sys
    sys.path.insert(0, HERE)
    tc = importlib.import_module("trace_check")
    assert callable(getattr(tc, "check_trace", None))
    vt = importlib.import_module("verify_terminal")
    assert getattr(vt, "ENUMERATED", None) and getattr(vt, "KNOWN_UNENUMERATED", None)
    rba = importlib.import_module("relevance_by_act")
    assert getattr(rba, "DECLARABLE_MOVES", None)

def test_lineage_instruction_is_verbatim_pinned():
    t = " ".join(open(os.path.join(HERE, "LINEAGE_SEAT_INSTRUCTION.md")).read().split())
    # verbatim = token sequence, not byte layout (the file wraps lines)
    assert "BLIND relevance adjudicator" in t
    assert "governs, permits, forbids, scopes, or directly conditions" in t

def test_runbook_carries_stop_conditions_and_registration_order():
    assert "STOP CONDITIONS" in RB
    assert RB.index("REGISTER the predicted") < RB.index("STEP 4")
