#!/usr/bin/env python3
"""Is every critic artifact WRITE-ONCE, and does every "the critic found X"
claim cite a real file with a matching hash?

Written after a sibling slice found a `critic_1.md` REWRITTEN IN PLACE between
two readers: two agents read materially different documents under one filename
and neither could tell. That failure is invisible to `validate.py`, which does
not read prose.

    ../../../../../../semi-formal-experiment/.venv/bin/python check_immutable.py
"""
import hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
MANIFEST = os.path.join(HERE, "MANIFEST.sha256")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def artifacts():
    return sorted(f for f in os.listdir(OUT)
                  if f.endswith((".md", ".json")))


def c_versioned_names():
    """C1. Is every critic artifact turn-versioned? An unversioned `criticN.md`
    is a filename a second pass can overwrite without leaving a trace."""
    bad = []
    for f in artifacts():
        if "critic" in f and not re.search(r"\.critic_t\d+\.md$", f):
            bad.append(f"critic artifact is not turn-versioned: {f}")
    return bad


def c_manifest_matches():
    """C2. Does every artifact still hash to what the manifest recorded? A
    changed hash on a critic file is a rewrite-in-place, full stop."""
    if not os.path.exists(MANIFEST):
        return ["no manifest yet — run with --freeze to write one"]
    rec = dict(l.split()[::-1] for l in open(MANIFEST)
               if l.strip() and not l.startswith("#"))
    bad = []
    for f in artifacts():
        h = sha(os.path.join(OUT, f))
        if f in rec and rec[f] != h:
            kind = "CRITIC REWRITTEN IN PLACE" if "critic" in f else "changed"
            bad.append(f"{kind}: {f}\n      manifest {rec[f][:16]}  now {h[:16]}")
        elif f not in rec:
            bad.append(f"not in manifest (written after freeze): {f}")
    for f in rec:
        if not os.path.exists(os.path.join(OUT, f)):
            bad.append(f"MANIFEST ENTRY DELETED FROM DISK: {f}")
    return bad


def c_claims_cite_sources():
    """C3. Does every 'the critic found X' claim in the write-ups name a file?
    Scans SWEEP.md / LESSONS.md / PROMPT_FINDINGS.md for critic-attribution
    phrasing and reports paragraphs that name no artifact and carry no
    MINE ALONE marker. Crude — it directs attention, it does not adjudicate."""
    pat = re.compile(r"\b(the\s+)?[`\w]*\s*critic\b[^.]{0,120}?"
                     r"\b(found|said|raised|noted|refused|flagged|declined|"
                     r"adjudicated|confirmed|considered)\b", re.I)
    out = []
    for doc in ("SWEEP.md", "LESSONS.md", "PROMPT_FINDINGS.md"):
        p = os.path.join(HERE, doc)
        if not os.path.exists(p):
            continue
        for i, para in enumerate(open(p, encoding="utf-8").read().split("\n\n")):
            if not pat.search(para):
                continue
            cites = re.search(r"critic_t\d+\.md|MINE ALONE|NOT CORROBORATED",
                              para)
            if not cites:
                first = " ".join(para.split())[:110]
                out.append(f"{doc} ¶{i}: attribution with no artifact cite "
                           f"and no MINE ALONE marker — {first}")
    return out


def freeze():
    with open(MANIFEST, "w") as fh:
        fh.write("# slice3 artifact manifest — sha256  filename\n")
        fh.write("# Critic artifacts are WRITE-ONCE. A changed hash on a\n"
                 "# .critic_t*.md file is a rewrite-in-place and a finding\n"
                 "# about the run, not a mess to tidy away.\n")
        for f in artifacts():
            fh.write(f"{sha(os.path.join(OUT, f))}  {f}\n")
    print(f"froze {len(artifacts())} artifacts -> {MANIFEST}")


def main():
    if "--freeze" in sys.argv:
        return freeze()
    rc = 0
    for fn in (c_versioned_names, c_manifest_matches, c_claims_cite_sources):
        print("=" * 72)
        print(fn.__name__[2:].upper(), "—", (fn.__doc__ or "").strip().split("\n")[0])
        hits = fn()
        if hits:
            rc = 1
            for h in hits:
                print("  *", h)
        else:
            print("  clean")
    return rc


if __name__ == "__main__":
    sys.exit(main() or 0)
