"""Tests for atom provenance: source-groundedness of quote_spans + lookup().

Run: .venv/bin/python -m pytest test_provenance.py -q
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import atom_provenance as ap

HERE = os.path.dirname(os.path.abspath(__file__))


def _vocab():
    return ap.load_vocab()


# --- source-groundedness -------------------------------------------------

def test_every_span_is_an_exact_substring_of_its_clause():
    """The non-negotiable check: a span not literally in the document is a
    hallucinated justification."""
    assert ap.verify_spans() == []


def test_span_shape_is_well_formed():
    clauses = ap.load_clauses()
    for atom in _vocab()["atoms"]:
        for span in atom["quote_spans"]:
            assert set(span) == {"locator", "clause_id", "quote", "kind"}
            assert span["clause_id"] in clauses
            assert span["quote"].strip() == span["quote"]
            assert span["kind"] == clauses[span["clause_id"]]["kind"]


def test_vocabulary_still_has_exactly_25_atoms():
    """quote_spans population must not add or remove atoms."""
    assert len(_vocab()["atoms"]) == 25


def test_unjustified_atoms_are_reported_not_hidden():
    """Whatever the current set is, it must be derivable from the file --
    an atom with no spans is a finding, not an error."""
    unjustified = ap.unjustified_atoms()
    assert isinstance(unjustified, list)
    assert set(unjustified) <= set(ap.atom_names())
    # current state of the pilot: every atom is grounded
    assert unjustified == []


# --- lookup() ------------------------------------------------------------

def test_lookup_returns_passages_for_an_atom():
    rows = ap.lookup(["business_reason"])
    assert rows
    assert any("legitimate business reason" in r["quote"] for r in rows)
    for r in rows:
        assert set(r) == {"locator", "clause_id", "quote", "kind", "atoms"}
        assert "business_reason" in r["atoms"]


def test_lookup_dedupes_shared_spans():
    """foster_reliance and reliance_endorsed both cite c063's same sentence."""
    a = ap.lookup(["foster_reliance"])
    b = ap.lookup(["reliance_endorsed"])
    both = ap.lookup(["foster_reliance", "reliance_endorsed"])
    keys = lambda rows: {(r["clause_id"], r["quote"]) for r in rows}
    assert keys(a) & keys(b), "expected a shared span for this test to bite"
    assert keys(both) == keys(a) | keys(b)
    assert len(both) == len(keys(both)) < len(a) + len(b)
    shared = (keys(a) & keys(b)).pop()
    row = [r for r in both if (r["clause_id"], r["quote"]) == shared][0]
    assert row["atoms"] == ["foster_reliance", "reliance_endorsed"]


def test_lookup_dedupes_repeated_atom():
    once = ap.lookup(["bel_true"])
    twice = ap.lookup(["bel_true", "bel_true"])
    assert once == twice


def test_lookup_results_are_sorted_by_clause_id():
    rows = ap.lookup(ap.atom_names())
    ids = [r["clause_id"] for r in rows]
    assert ids == sorted(ids)


def test_lookup_empty_input_returns_empty():
    assert ap.lookup([]) == []


def test_lookup_unknown_atom_raises_cleanly():
    with pytest.raises(ap.UnknownAtom) as exc:
        ap.lookup(["no_such_atom"])
    assert "no_such_atom" in str(exc.value)
    # and it does not poison a request that also contains known atoms
    with pytest.raises(ap.UnknownAtom):
        ap.lookup(["bel_true", "no_such_atom"])


def test_lookup_accepts_a_bare_string():
    assert ap.lookup("bel_true") == ap.lookup(["bel_true"])


def test_cli_prints_passages(capsys):
    rc = ap._main(["user_prefers_p", "bel_false"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "c227" in out
    assert "Being honest" in out


def test_cli_unknown_atom_exits_nonzero(capsys):
    rc = ap._main(["definitely_not_an_atom"])
    assert rc == 1
    assert "definitely_not_an_atom" in capsys.readouterr().err
