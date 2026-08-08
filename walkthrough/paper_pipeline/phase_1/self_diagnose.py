#!/usr/bin/env python3
"""Ask each failed attempt why it did what it did, and what would have helped.

The model that produced a failing translation is still holding the whole
context — the clause, its own attempts, and the checks against them. Continuing
that conversation with one question is the cheapest diagnosis available.

⚠️ IT IS A PROPOSER, NEVER A DIAGNOSIS. Two recorded cases here of a model's
account of its own output being false: one annotated "the anonymous variable is
avoided by using a named variable" while writing one, and another stated a rule
that could not have produced its own examples. Everything this returns is a
HYPOTHESIS, to be tested against clauses the model did not see.

    python3 self_diagnose.py <run-dir>            # dry run: prompt + cost
    python3 self_diagnose.py <run-dir> --live
"""

import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import translate as T  # noqa: E402

#: Deliberately neutral. Asking "what would have helped?" alone invites the
#: model to invent a prompt defect whether or not one exists, so the last
#: paragraph gives it an explicit way to answer "nothing — the fault was mine".
QUESTION = """Stop translating. This is a post-mortem on the exchange above, and
your answer will be read by someone deciding whether to change the instructions
you were given.

For each check that failed on your attempts:

1. What were you actually trying to express? State the intent, not the syntax.
2. Was there something in the instructions that led you to that shape — or that
   failed to rule it out? Quote the exact sentence if there is one.
3. What specific change would have made you produce the right shape first time?
   Give the text you would remove and the text you would put in its place.

⚠️ If you think the instructions were already clear and the mistake was simply
yours, say that plainly. "The instructions were clear, I misapplied them" is a
useful and acceptable answer, and is more useful than a change that would not
have helped. Do not invent a defect to be helpful.

Answer in prose. Do not return a module."""


def diagnose(run_dir, live=False):
    cfg = T.load_config(os.path.join(HERE, "config.json"))
    # ⭐ Format forcing OFF, everything else kept. It is a request-body flag,
    # not a property of the transcript — with `response_format` set the model
    # is contractually unable to emit prose, and the first run of this script
    # got eight JSON modules back instead of eight diagnoses.
    #
    # The stage-1 system block STAYS. The question asks which instruction led
    # to the wrong shape; swapping in a diagnostic system prompt would remove
    # the very thing being diagnosed.
    cfg = {**cfg, "model": {**cfg["model"], "format_forcing": "none"}}
    prov = T.resolve_provider(cfg, type("A", (), {
        "provider": None, "model": None, "max_tokens": None})())
    system = T.build_system(cfg)

    jobs = []
    for path in sorted(glob.glob(os.path.join(run_dir, "*.transcript.json"))):
        cid = os.path.basename(path).split(".")[0]
        transcript = json.load(open(path, encoding="utf-8"))
        if len(transcript) < 3:          # never repaired: nothing to diagnose
            continue
        jobs.append((cid, transcript + [{"role": "user", "content": QUESTION}]))

    chars = sum(len(system) + sum(len(m["content"]) for m in t) for _, t in jobs)
    est = (chars / 4 / 1e6) * prov.price_per_mtok[0] + \
          (len(jobs) * 1500 / 1e6) * prov.price_per_mtok[1]
    print(f"transcripts with at least one repair : {len(jobs)}  "
          f"[{', '.join(c for c, _ in jobs)}]")
    print(f"cost (rough)                         : ${est:.4f}")
    if not live:
        print("\nDRY RUN — nothing sent. Add --live.")
        return 0

    client = T.make_client(prov, cfg)
    out = os.path.join(run_dir, "diagnoses")
    os.makedirs(out, exist_ok=True)
    for cid, messages in jobs:
        try:
            env = client.complete_messages(system, messages)
        except T.Phase1Error as exc:
            print(f"  ⛔ {cid}: {exc}")
            continue
        with open(os.path.join(out, f"{cid}.md"), "w", encoding="utf-8") as fh:
            fh.write(f"# {cid} — self-diagnosis\n\n"
                     f"⚠️ A HYPOTHESIS from the model that produced the failure. "
                     f"Not a diagnosis. Test before acting.\n\n" + env["text"])
        print(f"  ✓ {cid}: {env['out']:,} out-tokens")
    print(f"\nwritten to {out}")
    print("⚠️ These are hypotheses. Aggregate them, then test any prompt change "
          "against clauses the model did not see.")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(diagnose(args[0], live="--live" in sys.argv))
