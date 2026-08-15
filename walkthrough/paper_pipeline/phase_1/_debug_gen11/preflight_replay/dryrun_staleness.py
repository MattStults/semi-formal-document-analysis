"""CHECK 3a — exactly what is stale in dryrun.txt, and what regenerating it
would change. ZERO API SPEND, and it does NOT write dryrun.txt.

It rebuilds, in memory, the three sections `write_dry_run_artifact` produces,
and diffs them against the stored artifact. The stored file's provenance
matters, so the regenerated text goes to a scratch path passed on the command
line (default: this directory) and NEVER to phase_1/dryrun.txt.
"""
import contextlib
import difflib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, PHASE1)
os.chdir(PHASE1)

import translate  # noqa: E402


def build():
    cfg = translate.load_config(translate.rel("config.json"))
    fp = translate.inputs_fingerprint(cfg)
    out = ["# phase_1/translate.py — DRY RUN artifact",
           f"# inputs-sha: {fp}   (config.json + every prompt file)",
           "# Regenerate with: translate.py --write-artifact",
           "# Nothing was sent. This is the complete prompt that WOULD be sent.",
           ""]

    class _A:
        clause = section = kinds = limit = provider = model = max_tokens = None
        live = False
        show_prompt = 0
    for title, over in (
            ("default config", {}),
            ("--section definitions --kinds definitional --limit 4",
             {"section": "definitions", "kinds": ["definitional"], "limit": 4}),
            ("--clause m0255 --show-prompt 1",
             {"clause": ["m0255"], "show_prompt": 1})):
        a = type("A", (_A,), dict(over))()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            translate.run(cfg, a)
        out += [f"{'#' * 12} {title} {'#' * 12}", buf.getvalue()]
    return fp, "\n".join(out)


def main():
    dest = sys.argv[1] if len(sys.argv) > 1 else \
        os.path.join(HERE, "dryrun.REGENERATED.txt")
    assert os.path.abspath(dest) != translate.rel("dryrun.txt"), \
        "refusing to overwrite the stored artifact"
    fp, new = build()
    old = open(translate.rel("dryrun.txt"), encoding="utf-8").read()
    open(dest, "w", encoding="utf-8").write(new)

    stored_fp = old.splitlines()[1].split("inputs-sha:")[1].split()[0]
    print(f"stored  inputs-sha: {stored_fp}")
    print(f"current inputs-sha: {fp}")
    print(f"MATCH: {stored_fp == fp}")
    print()
    d = list(difflib.unified_diff(old.splitlines(), new.splitlines(),
                                  "dryrun.txt (stored)", "regenerated",
                                  lineterm="", n=1))
    print(f"diff lines: {len(d)}")
    for line in d:
        print(line)
    print(f"\nregenerated text -> {dest} (stored artifact untouched)")


if __name__ == "__main__":
    main()
