"""machine/scan.py — the MECHANICAL fact extractor.

`facts.lp` is hand-transcribed governance. This file is the opposite: it reads
the repo and emits facts that no human chose, so the integrity constraints in
`rules.lp` can fire on evidence nobody pointed them at. Two extractions:

1. RETRACTION SCAN. A file that says a claim is RETRACTED/WITHDRAWN, and then
   still asserts the same claim elsewhere, is self-contradictory. The scan is
   generic: it finds retraction markers anywhere in the repo's top-level .py
   and .md files, pulls the numeric literals off the marker's line, and then
   looks for those same literals asserted on non-marker lines. It is NOT told
   which file to look at.

2. VERDICT SCAN. Any JSON verdict artifact whose records carry `side` and
   `cause` is emitted as verdict/4, together with the cause taxonomy's own
   `kind` field read live from `audit_disagreements.CAUSE_TAXONOMY`. The
   taxonomy says which causes assert a tool fault (kind FP/FN) and which are
   genuinely two-sided (kind `either`); `rules.lp` does the rest.

Output: machine/scanned.lp, with a source/needle companion for every fact,
verified by machine/check_model.py exactly like the hand-authored ones.

    python3 machine/scan.py [--out machine/scanned.lp]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

#: Files never scanned, with the reason. Empty is the correct steady state:
#: a file excluded here is a file the model makes no claim about, so a hook
#: that guards it would be guarding nothing. HARNESS_REDESIGN.md sat here
#: while it was being concurrently edited (unstable line numbers); that
#: finished 2026-08-06 and it is now scanned like everything else.
EXCLUDED = {}  # HARNESS_REDESIGN.md un-excluded 2026-08-06: editing finished

#: A retraction marker. Deliberately narrow and case-SENSITIVE: these are the
#: repo's own shout-markers, not ordinary prose.
RETRACT_RE = re.compile(r"\bRETRACTED\b|\bRETRACTION\b|\bWITHDRAWN\b")

#: A numeric claim worth tracking: a signed decimal with >= 2 fractional
#: digits. Integers and one-decimal numbers are too common to be evidence.
NUM_RE = re.compile(r"[+\-−]?\d+\.\d{2,}")


def _norm_num(tok: str) -> str:
    return tok.replace("−", "-").lstrip("+")


def _scan_files():
    """Top-level .py and .md files, excluding this package and EXCLUDED."""
    for name in sorted(os.listdir(REPO)):
        if name in EXCLUDED:
            continue
        if not (name.endswith(".py") or name.endswith(".md")):
            continue
        path = os.path.join(REPO, name)
        if os.path.isfile(path):
            yield name, path


def retraction_facts():
    """[(fact_str, file, line, needle)] for claim_retracted / claim_asserted."""
    out = []
    for name, path in _scan_files():
        try:
            lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
        except OSError:
            continue
        retracted = {}       # token -> first marker line (1-based)
        for i, line in enumerate(lines, 1):
            if RETRACT_RE.search(line):
                for tok in NUM_RE.findall(line):
                    retracted.setdefault(_norm_num(tok), i)
        if not retracted:
            continue
        for tok, mline in sorted(retracted.items()):
            out.append((f'claim_retracted("{tok}","{name}",{mline}).',
                        name, mline, tok))
        for i, line in enumerate(lines, 1):
            if RETRACT_RE.search(line):
                continue
            for raw in NUM_RE.findall(line):
                tok = _norm_num(raw)
                if tok in retracted:
                    out.append((f'claim_asserted("{tok}","{name}",{i}).',
                                name, i, raw))
    return out


def _json_candidates():
    """Verdict-shaped JSON artifacts, found by walking — not by name."""
    roots = ("audit_dossiers", "cycles", "dossiers", "drift_standing")
    for root in roots:
        base = os.path.join(REPO, root)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirs, files in os.walk(base):
            for f in sorted(files):
                if f.endswith(".json"):
                    yield os.path.relpath(os.path.join(dirpath, f), REPO)


def _records(obj):
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict) and isinstance(obj.get("records"), list):
        return obj["records"]
    return []


def verdict_facts():
    out = []
    for rel in _json_candidates():
        path = os.path.join(REPO, rel)
        try:
            text = open(path, encoding="utf-8").read()
            obj = json.loads(text)
        except (OSError, ValueError):
            continue
        recs = _records(obj)
        if not recs or not isinstance(recs[0], dict):
            continue
        if not ("side" in recs[0] and "cause" in recs[0]):
            continue
        lines = text.splitlines()
        for r in recs:
            if not isinstance(r, dict):
                continue
            rid = r.get("dossier_id") or r.get("flip_id") or r.get("id")
            side, cause = r.get("side"), r.get("cause")
            if not (rid and side and cause):
                continue
            needle = f'"{rid}"'
            lineno = next((i for i, l in enumerate(lines, 1) if needle in l), None)
            if lineno is None:
                continue
            out.append((f'verdict("{rel}","{rid}","{side}","{cause}").',
                        rel, lineno, rid))
    return out


def cause_kind_facts():
    """The taxonomy's own kind field, read live from the module that owns it."""
    sys.path.insert(0, REPO)
    import audit_disagreements                              # noqa: E402
    src = open(os.path.join(REPO, "audit_disagreements.py"),
               encoding="utf-8").read().splitlines()
    out = []
    for cause, spec in sorted(audit_disagreements.CAUSE_TAXONOMY.items()):
        kind = spec.get("kind")
        lineno = next((i for i, l in enumerate(src, 1)
                       if f'"{cause}"' in l and l.strip().endswith("{")), None)
        if lineno is None or not kind:
            continue
        out.append((f'cause_kind("{cause}","{kind}").',
                    "audit_disagreements.py", lineno, cause))
    return out


def build(out_path: str) -> int:
    blocks = [("retraction scan (generic: every top-level .py/.md)",
               retraction_facts()),
              ("verdict scan (generic: every verdict-shaped JSON artifact)",
               verdict_facts()),
              ("cause taxonomy kinds (live from audit_disagreements)",
               cause_kind_facts())]
    lines = ["%% machine/scanned.lp — GENERATED by machine/scan.py. Do not edit.",
             "%% Every fact here was found by walking the repo, not by being",
             "%% pointed at a file. Regenerate with: python3 machine/scan.py",
             ""]
    for name, reason in sorted(EXCLUDED.items()):
        lines.append(f'scan_excluded("{name}","{reason}").')
    lines.append("")
    n = 0
    for title, facts in blocks:
        lines.append(f"% ---- {title}")
        for fact, f, line, needle in facts:
            key = fact[:-1]                      # strip trailing '.'
            esc = needle.replace('\\', '\\\\').replace('"', '\\"')
            lines.append(fact)
            lines.append(f'source({key},"{f}",{line}). '
                         f'needle({key},"{esc}").')
            n += 1
        lines.append("")
    open(out_path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"wrote {out_path}: {n} scanned facts")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "scanned.lp"))
    a = ap.parse_args(argv)
    return build(a.out)


if __name__ == "__main__":
    raise SystemExit(main())
