#!/usr/bin/env python3
"""Fixup-round applier (Matt's directive 2026-08-14, item 15): consume
<run>/frontier_verdicts.json (frontier_review.py's output) and apply the
MECHANICAL dispositions deterministically. Code never makes content
decisions:

  * seat_accepted_rename REJECTED by the frontier -> REVERT the rename:
    the need entries the resolution pass renamed to the provided name are
    restored to the original dangling name (both names ride in the
    verdict's `detail` -- the risk queue records the whole proposal).
  * dropped_merge UPHELD (dropping was correct / the merge was harmful)
    -> no-op: the merge is already dropped; the confirmation is recorded.
  * any verdict of `uphold` -> recorded as confirmed, nothing changes.

NON-mechanical dispositions are NOT applied -- they land on
<run>/fixup_queue.json with a reason each: a rejected modal drift or
broken promise needs regeneration (a later model stage); a rejected
low_sim_edge or dropped_merge needs a content decision about what
replaces it; a REJECTED dangling_near_miss (the frontier judged the pair
the same concept, i.e. the recorded non-rename is wrong -- review item 2)
proposes a NEW rename, which must go through the resolution pass's gate,
not a blind write. An UPHELD near-miss confirms the honest dangling.

Writes <run>/root_graph.fixed.json + a fixup report line appended to
<run>/health.jsonl. NEVER mutates root_graph.json in place. Offline, $0.

    python fixup.py runs/ds7
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import recurse_driver as R     # noqa: E402  (write_json)


def _revert_rename(g, detail):
    """Restore the original dangling name on the needer's renamed need
    entries. Returns (n_reverted, reason_or_None)."""
    needer = detail.get("needer")
    orig = detail.get("name")
    renamed = detail.get("rename_to") or detail.get("name")
    if not needer or not orig or renamed == orig:
        return 0, ("proposal carries no needer/original name -- cannot "
                   "revert mechanically")
    node = next((n for n in g.get("nodes", [])
                 if n.get("id") == needer), None)
    if node is None:
        return 0, f"needer node {needer!r} not in root graph"
    matches = [d for d in node.get("needs", [])
               if isinstance(d, dict) and d.get("name") == renamed]
    if not matches:
        return 0, (f"no needs entry named {renamed!r} on {needer!r} "
                   f"(already reverted, or renamed again since)")
    if len(matches) > 1:
        # adversarial review (INFO, latent): after the rename, a genuine
        # pre-existing need of `rename_to` is byte-indistinguishable from
        # the renamed entry -- blindly reverting all of them would rename
        # a REAL edge. Ambiguity goes to the queue, never to code.
        return 0, (f"{len(matches)} needs entries named {renamed!r} on "
                   f"{needer!r}: a genuine need may share the rename "
                   f"target; ambiguous, needs human review")
    matches[0]["name"] = orig
    return 1, None


def apply_fixups(run_dir):
    verdicts_path = os.path.join(run_dir, "frontier_verdicts.json")
    fv = json.load(open(verdicts_path))
    g = json.load(open(os.path.join(run_dir, "root_graph.json")))
    confirmed, reverted, queue = [], [], []
    for v in fv.get("verdicts", []):
        kind, verdict = v.get("kind"), v.get("verdict")
        row = {"idx": v.get("idx"), "kind": kind, "verdict": verdict,
               "grounds": v.get("grounds", ""), "detail": v.get("detail")}
        if verdict == "uphold":
            # confirmations are recorded, never applied -- including the
            # dropped_merge case (already dropped: confirming is a no-op)
            confirmed.append(row)
            continue
        if verdict == "no_verdict":
            queue.append(dict(row, reason="frontier reached no verdict; "
                                          "needs human review"))
            continue
        # verdict == reject
        if kind == "seat_accepted_rename":
            n_rev, why = _revert_rename(g, v.get("detail") or {})
            if why:
                queue.append(dict(row, reason=f"revert failed: {why}"))
            else:
                reverted.append(dict(row, reverted_needs=n_rev))
                g.setdefault("driver_autofixes", []).append(
                    f"fixup: frontier rejected rename "
                    f"{(v.get('detail') or {}).get('name')!r} -> "
                    f"{(v.get('detail') or {}).get('rename_to')!r} on "
                    f"{(v.get('detail') or {}).get('needer')!r}; "
                    f"reverted {n_rev} need(s) to the honest dangling")
        elif kind == "modal_drift":
            queue.append(dict(row, reason="modal drift needs node "
                              "regeneration -- a later model stage, "
                              "never a code edit"))
        elif kind == "broken_promise":
            queue.append(dict(row, reason="a vanished concept needs "
                              "regeneration of the promising span -- a "
                              "later model stage"))
        elif kind == "dropped_merge":
            queue.append(dict(row, reason="applying a merge is a content "
                              "decision (which node survives, what prose "
                              "merges); not mechanical"))
        elif kind == "dangling_near_miss":
            # review item 2: `reject` on a near-miss means the frontier
            # judged the pair the SAME concept -- the recorded NON-rename
            # is wrong, so this is a PROPOSED NEW RENAME. It must go
            # through the resolution pass's gate + seat, never a blind
            # code write. (`uphold` = honest dangling confirmed, above.)
            queue.append(dict(row, reason="frontier judged the near-miss "
                              "the same concept: a proposed NEW rename -- "
                              "route it through the resolution pass's "
                              "gate/seat, never auto-apply"))
        elif kind == "low_sim_edge":
            queue.append(dict(row, reason="unlinking an edge leaves an "
                              "unnamed dangling -- what the need becomes "
                              "is a content decision"))
        else:
            queue.append(dict(row, reason=f"unknown kind {kind!r}: "
                              f"no mechanical disposition defined"))
    fixed_path = os.path.join(run_dir, "root_graph.fixed.json")
    R.write_json(fixed_path, g)
    queue_path = os.path.join(run_dir, "fixup_queue.json")
    R.write_json(queue_path, {"run": run_dir, "items": queue,
                              "total": len(queue)})
    # review item 2: the dispositions persist as ROWS on the verdicts
    # artifact -- a count alone made "which items were confirmed" a
    # transcript-only fact
    fv["dispositions"] = {"confirmed": confirmed, "reverted": reverted,
                          "queued_nonmechanical": len(queue),
                          "queue_file": os.path.basename(queue_path)}
    R.write_json(verdicts_path, fv)
    report = {"artifact": "fixup", "kind": "fixup",
              "verdicts": len(fv.get("verdicts", [])),
              "confirmed": len(confirmed),
              "renames_reverted": len(reverted),
              "queued_nonmechanical": len(queue)}
    with open(os.path.join(run_dir, "health.jsonl"), "a") as f:
        f.write(json.dumps(report) + "\n")
    print(f"fixup: {len(confirmed)} confirmed, {len(reverted)} rename(s) "
          f"reverted -> {fixed_path}; {len(queue)} non-mechanical item(s) "
          f"-> {queue_path}")
    return {"confirmed": confirmed, "reverted": reverted, "queue": queue,
            "graph": g, "report": report}


def main(argv=None):
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("usage: fixup.py <run_dir>   (e.g. fixup.py runs/ds7)")
        return 2
    apply_fixups(args[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
