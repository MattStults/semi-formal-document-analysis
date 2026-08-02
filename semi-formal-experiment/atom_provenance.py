"""Atom -> source-document provenance lookup.

The vocabulary's governing rule is that an atom is admitted iff some clause's
applicability turns on it. ``quote_spans`` records the passages that do that
work. This module is the read side of that record: given atom names, return the
document passages that justify them.

Usage:
    .venv/bin/python atom_provenance.py user_prefers_p bel_false
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VOCAB_PATH = os.path.join(HERE, "vocabulary_pilot.json")
CLAUSES_PATH = os.path.join(HERE, "constitution_clauses.json")


class UnknownAtom(KeyError):
    """Raised when a requested atom is not in the vocabulary."""


def load_vocab(vocab_path: str = VOCAB_PATH) -> dict:
    with open(vocab_path, encoding="utf-8") as f:
        return json.load(f)


def load_clauses(clauses_path: str = CLAUSES_PATH) -> dict:
    """Return {clause_id: clause} for the source document."""
    with open(clauses_path, encoding="utf-8") as f:
        return {c["id"]: c for c in json.load(f)["clauses"]}


def atom_names(vocab_path: str = VOCAB_PATH) -> list[str]:
    return [a["name"] for a in load_vocab(vocab_path)["atoms"]]


def unjustified_atoms(vocab_path: str = VOCAB_PATH) -> list[str]:
    """Atoms with no recorded justifying passage (coined, not extracted)."""
    return [a["name"] for a in load_vocab(vocab_path)["atoms"]
            if not a.get("quote_spans")]


def lookup(atoms: list[str], vocab_path: str = VOCAB_PATH) -> list[dict]:
    """Return the justifying passages for ``atoms``.

    Each result is {"locator", "clause_id", "quote", "kind", "atoms"} where
    ``atoms`` lists the requested atoms that span justifies. Results are
    deduplicated on (clause_id, quote) and sorted by clause id then quote.

    Raises UnknownAtom if any requested name is not in the vocabulary.
    An atom that exists but has no spans simply contributes nothing.
    """
    if isinstance(atoms, str):  # tolerate a bare name
        atoms = [atoms]
    vocab = load_vocab(vocab_path)
    by_name = {a["name"]: a for a in vocab["atoms"]}
    unknown = [a for a in atoms if a not in by_name]
    if unknown:
        raise UnknownAtom(
            "not in vocabulary: " + ", ".join(sorted(set(unknown))))

    merged: dict[tuple[str, str], dict] = {}
    for name in atoms:
        for span in by_name[name]["quote_spans"]:
            key = (span["clause_id"], span["quote"])
            row = merged.setdefault(key, {
                "locator": span["locator"],
                "clause_id": span["clause_id"],
                "quote": span["quote"],
                "kind": span.get("kind"),
                "atoms": [],
            })
            if name not in row["atoms"]:
                row["atoms"].append(name)
    for row in merged.values():
        row["atoms"].sort()
    return [merged[k] for k in sorted(merged)]


def verify_spans(vocab_path: str = VOCAB_PATH,
                 clauses_path: str = CLAUSES_PATH) -> list[str]:
    """Return a list of source-groundedness errors (empty == all verified).

    Every recorded quote must be an exact substring of the cited clause's
    verbatim quote, and the locator must match the clause's locator.
    """
    clauses = load_clauses(clauses_path)
    errors: list[str] = []
    for atom in load_vocab(vocab_path)["atoms"]:
        for span in atom.get("quote_spans", []):
            cid = span.get("clause_id")
            clause = clauses.get(cid)
            if clause is None:
                errors.append(f"{atom['name']}: no such clause {cid!r}")
                continue
            if span["quote"] not in clause["quote"]:
                errors.append(
                    f"{atom['name']}/{cid}: quote is not a substring of the "
                    f"clause: {span['quote']!r}")
            if span.get("locator") != clause["locator"]:
                errors.append(
                    f"{atom['name']}/{cid}: locator mismatch")
    return errors


def _main(argv: list[str]) -> int:
    if not argv:
        print(__doc__.strip())
        print("\nknown atoms:")
        for n in atom_names():
            print("  " + n)
        return 2
    try:
        rows = lookup(argv)
    except UnknownAtom as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if not rows:
        print("(no recorded justifying passages for: %s)" % ", ".join(argv))
        return 0
    for row in rows:
        print(f"{row['clause_id']} [{row['kind']}]  <- {', '.join(row['atoms'])}")
        print(f"  {row['locator']}")
        print(f"  “{row['quote']}”")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
