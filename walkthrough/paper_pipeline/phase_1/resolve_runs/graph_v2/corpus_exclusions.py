#!/usr/bin/env python3
"""Translated modules that must NOT enter the corpus, and why.

⭐ WHY THIS FILE EXISTS. Until now there was **no way to keep an adjudicated-bad
module out of the corpus.** Membership is computed fresh on every read by
`link_nodes.gather()` from what is physically present under
`translation_sample/runs/`, and its only predicates are "is a module file",
`outcome == "translated"`, and "the `.lp` exists". Nothing consulted a verdict.
The near neighbours all fall short, each for a stated reason:

  * **waivers** (`version.py:385-465`) are the right SHAPE -- signed, dated,
    precondition-checked, wildcards refused by name -- but they act on the
    *re-translation work list* under `--only-stale`, and their effect is to
    KEEP a stored module, never to drop one.
  * **the graveyard** (`graveyard.py:8`) says of itself "THIS MODULE IS
    PERSISTENCE ONLY". No corpus reader opens it.
  * **`graph_corrections.py`** edits `provides`/`needs` on GRAPH nodes; it never
    filters `g["nodes"]`, and it runs long before translation.
  * **refreeze / abstention** is the only thing that actually keeps a module
    out (`EXPERIMENTS.md:3948`), and it works by preventing the artifact from
    ever existing. It cannot be applied after the fact.

So the only way to remove a known-bad module with the code that existed was to
delete or move files under `runs/` -- destroying immutable evidence. That is
the design gap this file closes: **the evidence stays, the verdict is recorded
beside it, and the corpus reader honours the verdict.**

⭐ EVERY entry here was ADJUDICATED against the document by an independent pass
and is applied MECHANICALLY: this file makes no content judgment, it executes a
recorded verdict and REFUSES if a precondition fails. Same contract as
`graph_corrections.py`, and for the same reason (REPRODUCIBILITY.md requires the
procedure, not just the artifact).

⛔ AN EXCLUSION IS KEYED TO ONE ARTIFACT IN ONE RUN, by content digest. It is
NOT a ban on the clause id. If a later run produces a module for the same node,
that module is new evidence, it enters the corpus normally, and it needs its own
adjudication. A blanket id-level ban would silently suppress a future CORRECT
translation, and nothing would report the suppression.

⛔ NOT A HAND-EDIT OF THE RUN DIRECTORY. Nothing here writes, moves or deletes
anything under `runs/`.

⚠️ SECOND GATHER PATH, NOT COVERED. `_debug_gen11/stage4_baseline/stage4_driver.py`
carries a deliberately fenced COPY of the gather logic (`selected_in`), which
does not consult this table. Wiring it is a separate change on that file's owner.

Usage:
  python3 corpus_exclusions.py        # verify every precondition, print the table
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

#: One tuple per excluded artifact:
#:
#:   (clause_id, run_dir, sha256 of the module .json, marker, grounds)
#:
#: `marker` is (status, act, body) of an `asserts` entry that MUST still be
#: present in the module -- the specific defect the verdict was about. It is
#: what makes the exclusion refuse rather than guess: if the file on disk is
#: not the artifact that was judged, we stop instead of quietly dropping
#: whatever now sits at that path.
EXCLUSIONS = [
    (
        "l1108_1367_n014",
        "20260815-124836-together-deepseek-v4-flash",
        "09d67d065f093803903dad3e7cfc671e21640b39300c65b510e603d015454532",
        ("permit", "generate_content(C)", "exploring_generation(C)"),
        "FABRICATED PERMISSION FROM NON-NORMATIVE COMMENTARY (EXPERIMENTS.md "
        "D1, 'AN INVENTED PERMISSION FOR EROTICA AND GORE, FROM A COMMENTARY "
        "BLOCK'). The node's span is model_spec.md:1117, inside a "
        "`!!! meta \"Commentary\"` block, and says only \"We're exploring how "
        "to let developers and users generate erotica and gore in "
        "age-appropriate contexts\". Three lines above it, at "
        "model_spec.md:1114, sits the rule under the heading "
        "`{#no_erotica_or_gore authority=system}`: \"The assistant should not "
        "generate erotica ... or extreme gore\". The module's read-back hedges "
        "(\"is being explored as permitted\"); the machine-readable `status` "
        "does not -- it is `permit`. So the corpus carried a permission "
        "contradicting a SYSTEM-authority prohibition, sourced from prose that "
        "states no norm at all. This is the patient-pricing failure mode with "
        "the sign flipped: not deleted guidance, fabricated permission.",
    ),
    (
        "l1108_1367_n014",
        "20260816-094505-together-deepseek-v4-flash",
        "8a7161690f14ec1353552bcf148993ca878e110fd39a78922e44d408b06766f8",
        ("permit", "generate_content(C)",
         "erotica_or_gore(C), age_appropriate_context(K), "
         "generation_context(C, K), usage_policies_met(C)"),
        "THE SAME FABRICATED PERMISSION, RE-TRANSLATED. This is the SECOND "
        "artifact for the node, from a later run, and it commits the D1 defect "
        "again in a stronger form: `permit generate_content(C) :- "
        "erotica_or_gore(C), age_appropriate_context(K), generation_context(C, "
        "K), usage_policies_met(C)`, with the read-back 'generating % is "
        "permitted when it is erotica or gore in an age-appropriate context and "
        "usage policies are met' -- the earlier module at least hedged in its "
        "read-back, this one does not hedge anywhere. The source is unchanged "
        "and was re-checked against the document, not inherited from the first "
        "entry: node_corpus_all.json gives the node's locator as "
        "'graph_v2@2026-08-10 > L1108-1367_n014 > L1117-1117' and its ESTABLISHES "
        "text is the commentary sentence 'OpenAI is exploring how to let "
        "developers and users generate erotica and gore in age-appropriate "
        "contexts'. model_spec.md:1117 is inside a `!!! meta \"Commentary\"` "
        "block and states no norm; model_spec.md:1114, three lines above, "
        "carries `{#no_erotica_or_gore authority=system}` -- 'The assistant "
        "should not generate erotica ... or extreme gore'. So the permission "
        "contradicts a SYSTEM-authority prohibition and is sourced from prose "
        "that grants nothing. Excluded on the same grounds as the 20260815 "
        "artifact, keyed to THIS artifact's own digest per the one-artifact "
        "rule above. The recurrence is the finding: excluding one artifact does "
        "not stop the translator reproducing the defect on the next run of the "
        "same node, so a later run of this node needs adjudication before it "
        "enters the corpus. Ruling: same defect -- confirmed by the project "
        "owner, 2026-08-31.",
    ),
]


class PreconditionFailed(SystemExit):
    """Raised, never caught here: a failed precondition must stop the read."""


def _path(entry):
    cid, run, _sha, _marker, _why = entry
    return os.path.join(HERE, "translation_sample", "runs", run, cid + ".json")


def verified():
    """Check EVERY precondition, then return {(run_dir, filename): entry}.

    Refuses -- loudly, by raising -- rather than guessing, on any of:
      * the run directory or the module file is missing;
      * the module's content digest is not the one that was adjudicated;
      * the module no longer carries the assert the verdict was about;
      * the module is not `translated` (so it was never in the corpus, and the
        entry is stale rather than effective).

    An exclusion that cannot be justified against the bytes is worse than no
    exclusion: it removes something from the corpus on the strength of a
    verdict about a different artifact.
    """
    out = {}
    for entry in EXCLUSIONS:
        cid, run, sha, marker, _why = entry
        p = _path(entry)
        if not os.path.isfile(p):
            raise PreconditionFailed(
                f"precondition failed: {cid} has no module at {p}. An "
                f"exclusion names an artifact that is not there -- either the "
                f"run dir moved (evidence must not move) or this entry is "
                f"stale. Resolve it; do not ignore it.")
        raw = open(p, "rb").read()
        got = hashlib.sha256(raw).hexdigest()
        if got != sha:
            raise PreconditionFailed(
                f"precondition failed: {cid} in {run} digests {got}, the "
                f"verdict was recorded against {sha}. The file on disk is not "
                f"the artifact that was adjudicated; re-adjudicate before "
                f"excluding it.")
        obj = json.loads(raw.decode("utf-8"))
        if obj.get("outcome") != "translated":
            raise PreconditionFailed(
                f"precondition failed: {cid} in {run} is "
                f"{obj.get('outcome')!r}, not 'translated'. A module that "
                f"never entered the corpus needs no exclusion -- this entry "
                f"claims an effect it does not have.")
        status, act, body = marker
        if not any(a.get("status") == status and a.get("act") == act
                   and a.get("body") == body
                   for a in (obj.get("asserts") or [])):
            raise PreconditionFailed(
                f"precondition failed: {cid} in {run} no longer carries the "
                f"assert the verdict was about "
                f"({status} {act} :- {body}). Re-adjudicate.")
        out[(run, cid + ".json")] = entry
    return out


def assert_all_applied(excluded, hit):
    """Every verified exclusion must actually have skipped something.

    Modelled on `version.py`'s loud report of unused waivers: an exclusion that
    silently matches nothing is a rule the operator believes is in force and
    is not.
    """
    missed = sorted(k for k in excluded if k not in hit)
    if missed:
        raise PreconditionFailed(
            f"exclusion(s) verified but never applied: {missed}. The corpus "
            f"reader did not reach these files, so the verdict is not in "
            f"force. Check that the run dir name still matches the reader's "
            f"pattern.")


def main():
    excluded = verified()
    print(f"CORPUS EXCLUSIONS -- {len(excluded)} verified against the bytes")
    for (run, fname), (cid, _run, sha, marker, why) in sorted(excluded.items()):
        print(f"\n  {cid}  ({run}/{fname})")
        print(f"    sha256 {sha}")
        print(f"    assert {marker[0]} {marker[1]} :- {marker[2]}")
        print(f"    grounds: {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
