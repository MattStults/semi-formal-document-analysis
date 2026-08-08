"""Where a clause goes when repair does not converge, and why some that do.

A clause whose repair runs out of attempts carries a signal about the PROMPT,
not only about that clause — and the signal is only visible by comparing
failures against one another. Reading two transcripts by hand found one shared
cause behind both. That does not scale to 593 clauses.

⚠️ THIS MODULE IS PERSISTENCE ONLY. It writes entries and refuses to lose them.
It does not diagnose, aggregate, cluster or change a prompt: those steps carry
design decisions that are not settled, and one of them — editing the prompt
automatically — would route around the review guard that watches these files.

WHY SUCCESSES ARE SAMPLED TOO

Waiting for outright failures throws most of the signal away. One clause
converged, was flagged `shrank`, and was garbage: it cleared its finding by
deleting the offending entry and the run recorded it as a success. A
failures-only graveyard would never have contained it.

And a graveyard holding only trouble makes every diagnosis read as "the prompt
is broken". Someone comparing entries needs cases where it WORKED to tell a real
defect from an unlucky clause, which is why clean first-try successes are kept
at a low rate rather than never.

TWO HASHES, ANSWERING DIFFERENT QUESTIONS

    contract_hash    clause text + the schema source.
                     Changes => the artifact may no longer VALIDATE.
    provenance_hash  prompt + model + params.
                     Changes => it is not REPRODUCIBLE, but is still valid.

Keeping them apart is what stops a prompt fix invalidating a corpus. A module
translated under an older prompt still satisfies the contract, still compiles,
still links — it simply cannot be cited as evidence about the current prompt.
Collapsing them into one hash marks the whole corpus stale on every prompt edit.

⭐ RULED 2026-08-08 (Matt): BOTH now trigger a re-run — a provenance change does
not merely relabel. That does NOT merge them. They answer different questions,
a report has to distinguish them, and only the provenance one may ever be
waived. `version.py` is where the comparison, the classification and the
partial-re-run flag live; these two functions stay here, where the entry that
first needed them is written.
"""

import hashlib
import json
import os
import time


class GraveyardError(RuntimeError):
    """Refusing to lose an entry, or to proceed past the cap."""


#: What is always kept, regardless of sampling rate, and why.
ALWAYS = {
    "unrepaired": "repair ran out of attempts — the case this exists for",
    "abstained_under_repair": "abstained only after a failed attempt; that is "
                              "repair pressure, not a first-class answer",
    "flagged": "converged, but a guard fired — a repair that goes green while "
               "making the module worse is the case a failures-only "
               "population misses",
    "last_attempt": "converged on the last available attempt; one more defect "
                    "and it would have failed, so the budget is hiding it",
}


def contract_hash(clause_text, schema_source):
    """Changes => the artifact may no longer validate. Drives re-translation."""
    h = hashlib.sha256()
    h.update(("clause:" + (clause_text or "")).encode())
    h.update(("schema:" + (schema_source or "")).encode())
    return h.hexdigest()[:16]


def provenance_hash(prompt, model, temperature, params=None):
    """Changes => not reproducible from current inputs, but still valid.

    ⚠️ `params` is APPENDED ONLY WHEN NON-EMPTY, and canonicalised with
    `sort_keys`. Both matter. Hashing `{}` differently from "no params" would
    have marked every artifact ever written provenance-stale the day this
    argument was added — the whole-corpus invalidation the two-hash split
    exists to prevent, arriving from the side. And serialising a dict without
    sorting makes an artifact's version depend on the order somebody happened
    to write a config file in, which is not a fact about the artifact.

    ⛔ Nothing here may reach Python's `hash()`: it is salted per process, so
    two runs over identical inputs would disagree and every staleness verdict
    downstream would be noise. See `version.py`.
    """
    h = hashlib.sha256()
    h.update(("prompt:" + (prompt or "")).encode())
    h.update(f"model:{model}|temp:{temperature}".encode())
    if params:
        h.update(("params:" + json.dumps(params, sort_keys=True,
                                         default=str)).encode())
    return h.hexdigest()[:16]


def should_keep(out, max_attempts, rates, clause_id="", seed=0):
    """(keep, reason). Deterministic — same clause and seed, same decision.

    Two runs over one corpus must produce the same population, or the graveyard
    is not a reproducible artifact and no comparison across it means anything.
    So sampling is a hash of the clause id, never a random draw.
    """
    status = getattr(out, "status", "")
    flags = list(getattr(out, "flags", []) or [])
    attempts = int(getattr(out, "attempts", 1) or 1)

    if status in ("unrepaired", "abstained_under_repair"):
        return True, ALWAYS[status]
    if flags:
        return True, ALWAYS["flagged"] + f" ({', '.join(flags)})"
    if attempts >= max_attempts:
        return True, ALWAYS["last_attempt"]

    bucket = "repaired" if attempts > 1 else "first_try"
    rate = float(rates.get(bucket, 0.0))
    if rate <= 0:
        return False, ""
    if rate >= 1:
        return True, f"sampled: every {bucket} case"
    draw = int(hashlib.sha256(f"{seed}:{bucket}:{clause_id}".encode())
               .hexdigest()[:8], 16) / 0xFFFFFFFF
    if draw < rate:
        return True, f"sampled at {rate:.0%} of {bucket} cases"
    return False, ""


def write_entry(root, clause, out, reason, contract_hash, provenance_hash,
                extra=None):
    """One directory per entry. Never overwrites; never partially writes."""
    os.makedirs(root, exist_ok=True)
    name = f"{clause.get('id', 'unknown')}-{time.strftime('%Y%m%d-%H%M%S')}"
    path = os.path.join(root, name)
    if os.path.exists(path):                       # same clause, same second
        path += "-b"
    os.makedirs(path)

    meta = {
        "clause_id": clause.get("id"),
        "reason": reason,
        "status": getattr(out, "status", None),
        "attempts": getattr(out, "attempts", None),
        "per_attempt": list(getattr(out, "per_attempt", []) or []),
        "flags": list(getattr(out, "flags", []) or []),
        "contract_hash": contract_hash,
        "provenance_hash": provenance_hash,
        "section_id": clause.get("section_id"),
        "kind": clause.get("kind"),
        **(extra or {}),
    }
    _dump(path, "entry.json", meta)
    _dump(path, "transcript.json", getattr(out, "transcript", []))
    _dump(path, "findings.json",
          [{"check_id": f.check_id, "severity": f.severity, "where": f.where,
            "message": f.message, "origin": f.origin}
           for f in (getattr(out, "findings", []) or [])])
    mod = getattr(out, "module", None)
    if mod is not None and hasattr(mod, "model_dump"):
        _dump(path, "module.json", mod.model_dump())
    return path


def _dump(path, name, obj):
    with open(os.path.join(path, name), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, default=str)


def open_entries(root):
    """Entries with no VERDICT.md. These are what block."""
    if not os.path.isdir(root):
        return []
    return sorted(d for d in os.listdir(root)
                  if os.path.isdir(os.path.join(root, d))
                  and not os.path.exists(os.path.join(root, d, "VERDICT.md")))


def clear(root, name):
    """Per entry, and only with a written diagnosis.

    ⛔ There is deliberately no clear-all. A graveyard that gets bulk-emptied is
    worse than none: this project has already watched a warning that fired on
    every run become invisible, and the mechanism that worked instead was one
    that blocked and had to be answered case by case.
    """
    path = os.path.join(root, name)
    if not os.path.isdir(path):
        raise GraveyardError(f"no such entry: {name}")
    if not os.path.exists(os.path.join(path, "VERDICT.md")):
        raise GraveyardError(
            f"{name} has no VERDICT.md. An entry is cleared by diagnosing it, "
            f"not by deleting it — the diagnosis is the artifact the graveyard "
            f"exists to produce")
    os.rename(path, os.path.join(root, "_cleared_" + name))


def at_cap(root, cap):
    return len(open_entries(root)) >= int(cap)


def check_cap(root, cap):
    """Raise rather than overflow.

    A hundred uninspected non-convergences is not a corpus; it is one prompt
    defect repeated a hundred times, and the remaining clauses cost money to
    reproduce it.
    """
    n = len(open_entries(root))
    if n >= int(cap):
        raise GraveyardError(
            f"graveyard cap reached: {n} open entries at {root}. Diagnose and "
            f"clear them before translating more — continuing spends the budget "
            f"reproducing a defect that is already recorded {n} times")
