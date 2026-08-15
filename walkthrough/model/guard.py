"""Staleness guard: when the design moves, the files transcribed from it are stale.

    python3 guard.py                    # check — non-zero if anything is stale
    python3 guard.py --accept PATH...   # record THOSE files as re-reviewed
                                        # (per file; there is deliberately no
                                        # accept-all — DESIGN NOTE below)
    python3 guard.py --watches PATH...  # hooks: exit 0 any path watched,
                                        # 3 nothing watched (the RESERVED skip
                                        # code — see __main__), else "broken"
    python3 guard.py --self-test        # prove the guard still does work

WHAT IT DETECTS. One thing, and it is the failure that cost the most: a file was
written by transcribing part of the design, the design then moved, and nothing
connects the two. The transcription keeps working. It keeps passing its own
tests. It is confidently instructing the previous design.

  ⭐ On 2026-08-07 this guard was RIGHT and RED for two hours while work
  proceeded from a stale reading of the design, and nobody looked, because
  hooks/pre-commit had never been installed. Being right is not the job;
  being SEEN is the job. Hence the hook, and hence the loud output.

WHAT IT CANNOT DO. It cannot tell you whether the transcription is still
correct. It tells you that nobody has asserted it is, since the change. The
assertion is a human act — that is what `--accept` records, with a name and a
date.

⚠️ THE ONE INVARIANT. A guard whose "pass" state is indistinguishable from its
"did not run" state is worse than no guard, because it manufactures confidence.
So: an empty watch list is an ERROR, an unreadable watch list is an ERROR, and a
watch pattern matching zero files is an ERROR. None of them is a pass.

DESIGN NOTE — why per-file, and why an exact sha.

  Per-file. The review point is recorded per file, with who accepted it and
  when. Accepting the prompt after a typo fix must not silently accept an
  unreviewed change to schema.py that happened to be sitting in the same
  working tree. `--accept` with no arguments is refused for that reason.

  RULING 2026-08-15 (G6) — there is deliberately no accept-all. The code
  and REVIEW_QUEUE §1 contradicted each other ("Accepting is per file …
  There is deliberately no accept-all" vs an `--accept --all` the docstring
  even advertised). The doctrine wins and the code was wrong. Provenance:
  the original guard (commit e29a55a) had no `--all`; the flag rode in on
  5c020cf — the 2026-08-07 save point committed WITH --no-verify while this
  very guard was RED — and no workflow need for it is recorded anywhere.
  Sibling ruling, same grounds: the repair graveyard deliberately has no
  clear-all — "a graveyard that gets bulk-emptied is worse than none: the
  mechanism that worked … blocked and had to be answered case by case"
  (paper_pipeline/phase_1/graveyard.py, pinned by test_graveyard.py).
  Rejected alternative, by name: keep `--all` as an escape hatch for a
  genuine whole-list re-read — the graveyard's answer is the answer here:
  the bulk path exists exactly once, spelled one `--accept <file>` per file
  actually re-read.

  Exact sha, deliberately, over the whole file. A whitespace-insensitive or
  section-scoped digest would cry wolf less — but the two error costs are not
  symmetric. A false STALE costs one `--accept <file>` and thirty seconds of
  reading. A false GREEN cost two hours on 2026-08-07. The cry-wolf problem is
  real and is answered a different way: every watched entry carries a `why` in
  watch.json, printed verbatim on STALE, so the report says what to re-read
  rather than merely that bytes moved. An unactionable warning is what gets
  ignored (see the invisible `no %% provides:` warning in link.py) — not a
  frequent one.

See RETIRED.md for the assertion layer that used to live beside this and does
not any more.
"""

import datetime
import fnmatch
import glob
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WALK = os.path.dirname(HERE)
WATCH_FILE = os.path.join(HERE, "watch.json")
STAMP = os.path.join(HERE, "reviewed.json")


class WatchListError(Exception):
    """The watch list is unusable. This is an ERROR, never a pass."""


def load_watch(path=None):
    """Return the watch entries. Raises rather than returning empty."""
    path = path or WATCH_FILE
    if not os.path.exists(path):
        raise WatchListError(f"watch list not found: {path}")
    try:
        raw = json.load(open(path))
    except Exception as e:
        raise WatchListError(f"watch list {path} is unreadable: {e}")
    entries = raw.get("watch")
    if not isinstance(entries, list) or not entries:
        raise WatchListError(
            f"watch list {path} is empty — nothing is being guarded. "
            f"An empty watch list is an error, not a clean run.")
    for e in entries:
        if not isinstance(e, dict) or not e.get("path"):
            raise WatchListError(f"watch entry without a path: {e!r}")
        if not str(e.get("why", "")).strip():
            raise WatchListError(
                f"watch entry {e['path']} has no `why` — a STALE report on it "
                f"would tell the reader nothing to do")
    return entries


def resolve(entries):
    """Expand the globs. Returns [(relpath, abspath, why)], sorted.

    ⚠️ A pattern matching nothing is an ERROR. That is how a renamed file stops
    being watched without anyone noticing — the same 'pass == did not run'
    shape, one entry down."""
    out = []
    for e in entries:
        hits = sorted(glob.glob(os.path.join(WALK, e["path"])))
        hits = [h for h in hits if os.path.isfile(h)]
        if not hits:
            raise WatchListError(
                f"watch entry `{e['path']}` matched no file — it was renamed, "
                f"moved or deleted, and is now silently unguarded. Fix "
                f"watch.json or restore the file.")
        for h in hits:
            out.append((os.path.relpath(h, WALK), h, e["why"]))
    return sorted(out)


def digest(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def current():
    """{relpath: digest} for every watched file."""
    return {rel: digest(p) for rel, p, _ in resolve(load_watch())}


def why_map():
    return {rel: why for rel, _, why in resolve(load_watch())}


def recorded():
    """{relpath: {digest, at, by}}. Tolerates the old flat {path: digest} form."""
    if not os.path.exists(STAMP):
        return {}
    raw = json.load(open(STAMP)).get("digests", {})
    return {k: (v if isinstance(v, dict) else {"digest": v, "at": "", "by": ""})
            for k, v in raw.items()}


def stale(now, then):
    """Watched files whose content moved since their review point."""
    return sorted(k for k in now if k in then and then[k].get("digest") != now[k])


def unreviewed(now, then):
    """Watched files with no review point at all — never asserted, not changed."""
    return sorted(k for k in now if k not in then)


def orphans(now, then):
    """Review points for files nobody watches: dead weight, and hides a rename."""
    return sorted(k for k in then if k not in now)


def _wrap(text, indent="        ", width=84):
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(indent + line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(indent + line)
    return "\n".join(out)


def check():
    try:
        now, whys = current(), why_map()
    except WatchListError as e:
        print("⛔ ERROR — the guard could not run, so nothing was checked.")
        print(f"   {e}")
        print("\n   This is NOT a pass. A guard that cannot read its watch list")
        print("   has exactly the shape of a guard that is not installed.")
        return 2

    then = recorded()
    changed, new = stale(now, then), unreviewed(now, then)
    gone = orphans(now, then)

    print(f"GUARD — {len(now)} watched file(s), review points in "
          f"{os.path.relpath(STAMP, WALK)}\n")

    if gone:
        print(f"⚠️  {len(gone)} recorded review point(s) for files no longer "
              f"watched — remove them, or restore the file:")
        for k in gone:
            print(f"      {k}")
        print()

    if changed or new:
        if changed:
            print(f"⛔ STALE — {len(changed)} watched file(s) moved since they were "
                  f"last reviewed:")
            for k in changed:
                print(f"\n   {k}")
                print(f"      {then[k].get('digest','?')} -> {now[k]}"
                      f"   (accepted {then[k].get('at') or '?'} "
                      f"by {then[k].get('by') or '?'})")
                print(_wrap(whys.get(k, "")))
            print()
        if new:
            print(f"⛔ NEVER REVIEWED — {len(new)} watched file(s) have no review "
                  f"point at all:")
            # Files added by one watch entry share one `why`; print it once.
            # A wall of repeated text is itself a way to get ignored.
            last = None
            for k in new:
                print(f"\n   {k}   {now[k]}")
                w = whys.get(k, "")
                if w != last:
                    print(_wrap(w))
                    last = w
            print()

        print("   ⭐ PROCESS: do not patch the file to match your memory of the design.")
        print("      Re-read the design section named above against the file. If a")
        print("      whole review is warranted, dispatch a CLEAN reviewer with")
        print("      model/REVIEW_BRIEF.md — it is explicitly allowed to answer")
        print("      'I cannot confidently review this', which is a wanted outcome.")
        print()
        print("   Then accept the files you actually re-read, ONE AT A TIME:")
        for k in changed + new:
            print(f"      python3 guard.py --accept {k}")
        print()
        print("   ⚠️ Accepting a file you did not read is the failure this guard")
        print("      exists to prevent, performed by hand.")
        return 1

    print(f"✅ every watched file is at its recorded review point ({len(now)} file(s))")
    return 0


def accept(paths, who=None):
    """Record the named files as re-reviewed. Per file, on purpose."""
    try:
        now, whys = current(), why_map()
    except WatchListError as e:
        print(f"⛔ ERROR — {e}")
        return 2

    if paths == ["--all"]:
        print("⛔ There is deliberately no accept-all (ruling 2026-08-15, G6).")
        print("   A single command attesting every file is how an unreviewed")
        print("   change rides in beside a typo fix — the exact failure the")
        print("   per-file review point exists to prevent, performed by hand.")
        print("   Sibling ruling, same grounds: the repair graveyard has no")
        print("   clear-all — 'a graveyard that gets bulk-emptied is worse than")
        print("   none' (graveyard.py). Accept the files you actually re-read,")
        print("   ONE AT A TIME:")
        for k in sorted(now):
            print(f"      python3 guard.py --accept {k}")
        return 2

    if not paths:
        print("⛔ --accept needs the paths you actually re-read.")
        print("   Accepting the whole list at once is how an unreviewed change")
        print("   rides in beside a typo fix. Accept the files you re-read,")
        print("   one at a time:")
        for k in sorted(now):
            print(f"      python3 guard.py --accept {k}")
        return 2

    resolved, bad = [], []
    for p in paths:
        key = os.path.relpath(os.path.abspath(p), WALK) if os.path.exists(p) else p
        hits = [k for k in now if k == key or k.endswith("/" + key.lstrip("./"))
                or os.path.basename(k) == key]
        if len(hits) == 1:
            resolved.append(hits[0])
        else:
            bad.append(p)
    if bad:
        print(f"⛔ not watched (or ambiguous), nothing recorded: {', '.join(bad)}")
        print("   Watched files are:")
        for k in sorted(now):
            print(f"      {k}")
        return 2

    who = who or os.environ.get("USER") or "unknown"
    stampdata = recorded()
    at = datetime.datetime.now().isoformat(timespec="seconds")
    for k in resolved:
        stampdata[k] = {"digest": now[k], "at": at, "by": who}

    json.dump({"_": "Per-file review points. An entry asserts: this person read "
                    "this file against the design on this date and confirmed it "
                    "still says what the design says. It is a claim about a "
                    "human act, not about bytes.",
               "digests": stampdata},
              open(STAMP, "w"), indent=1)
    print(f"recorded as reviewed by {who}:")
    for k in resolved:
        print(f"   {k}  {now[k]}")
    left = [k for k in sorted(now) if k not in stampdata
            or stampdata[k]["digest"] != now[k]]
    if left:
        print(f"\n⚠️ still stale or never reviewed ({len(left)}): {', '.join(left)}")
    return 0


def _glob_match(rel, pattern):
    """glob semantics for one relative path: `*` and `?` stop at `/`.

    resolve() watches with glob.glob; this matcher must agree with it, or
    'what is watched' has two answers (G10, 2026-08-15 — fnmatch's `*`
    crossed `/`, so a staged prompt/sub/x.md fired the hook for a file
    resolve() does not watch). Same segment count, then fnmatch per
    segment, which is glob's per-segment behaviour for `*`, `?` and [...]
    (no `**` recursion — resolve() does not use recursive=True either)."""
    rel_parts, pat_parts = rel.split("/"), pattern.split("/")
    return len(rel_parts) == len(pat_parts) and all(
        fnmatch.fnmatch(r, p) for r, p in zip(rel_parts, pat_parts))


def watches(paths):
    """Return 0 if any given path is one this guard watches, else a non-zero
    the caller maps to its skip code (the CLI maps it to exit 3, reserved
    for exactly this — see __main__). The hooks ask here rather than keeping
    their own copy — the list lived in three places once, which is how they
    drift apart.

    ⚠️ Matches on the whole relative path, not the basename. `00_task.md`
    somewhere else in the tree is a different file."""
    try:
        entries = load_watch()
    except WatchListError:
        return 0  # a broken watch list must make the hook RUN, not skip
    for p in paths:
        rel = p.replace("\\", "/")
        for prefix in ("walkthrough/", "./walkthrough/", ""):
            if prefix and rel.startswith(prefix):
                rel = rel[len(prefix):]
                break
        for e in entries:
            if _glob_match(rel, e["path"]):
                return 0
    return 1


def self_test():
    """Prove the guard still does work — each case is a way it once died quietly."""
    ok = True

    def case(name, passed, detail=""):
        nonlocal ok
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
        if detail:
            print(f"          {detail}")
        ok &= bool(passed)

    try:
        now = current()
    except WatchListError as e:
        case("the watch list resolves", False, str(e))
        return 1
    case("the guard watches something at all", len(now) > 0,
         f"{len(now)} file(s): {', '.join(sorted(now))}")

    # an empty / unreadable watch list must be an ERROR, not a quiet pass
    for label, obj in (("empty", {"watch": []}), ("unreadable", None)):
        p = os.path.join(HERE, "_selftest_watch.json")
        open(p, "w").write("{ not json" if obj is None else json.dumps(obj))
        real = globals()["WATCH_FILE"]
        globals()["WATCH_FILE"] = p
        try:
            import io, contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = check()
            case(f"an {label} watch list is a loud ERROR, not a pass",
                 rc == 2 and "⛔ ERROR" in buf.getvalue(), f"exit {rc}")
        finally:
            globals()["WATCH_FILE"] = real
            os.remove(p)

    # a pattern matching nothing must raise
    try:
        resolve([{"path": "no/such/*.md", "why": "x"}])
        case("a pattern matching no file is an error", False, "it returned quietly")
    except WatchListError:
        case("a pattern matching no file is an error", True)

    # staleness must actually fire
    fake_then = {k: {"digest": "0" * 16} for k in now}
    case("staleness fires when a digest differs",
         sorted(stale(now, fake_then)) == sorted(now))
    case("staleness does NOT fire when digests match",
         stale(now, {k: {"digest": v} for k, v in now.items()}) == [])

    # every watched file carries an actionable reason
    whys = why_map()
    case("every watched file states why it is watched",
         all(len(whys.get(k, "")) > 30 for k in now))

    return 0 if ok else 1


if __name__ == "__main__":
    argv = sys.argv[1:]
    if "--watches" in argv:
        # Exit codes the hook's scoping gate reads (G2, 2026-08-15):
        #   0 a staged path is watched     -> run the gates
        #   3 no staged path is watched    -> the RESERVED skip code
        #   anything else is the hook's business to BLOCK on, because 1 is
        # also Python's unhandled-exception exit: while "not watched" shared
        # it, a crashed guard was indistinguishable from a clean skip, and
        # the hook failed open. 3 cannot be produced by an interpreter that
        # never ran guard.py at all.
        # (watches() keeps the shell convention: 0 = watched, non-zero = not.)
        watched = watches(argv[argv.index("--watches") + 1:])
        raise SystemExit(0 if watched == 0 else 3)
    if "--self-test" in argv:
        raise SystemExit(self_test())
    if "--accept" in argv:
        raise SystemExit(accept(argv[argv.index("--accept") + 1:]))
    raise SystemExit(check())
