#!/usr/bin/env python3
"""ARM F — the cheap critic's REPLY CONTRACT is changed. Two cells, one design.

Arm F is arm E with ONE thing different: what the critic is allowed to write.
Everything else -- the 17 clauses, arm A's byte-identical stored turn-1 drafts,
the eleven-entry review list, the three anti-rules, the unforced critic call,
the mechanical FIX extraction, the imperative edit-list form -- is held.

  CELL F1  BAN.  A FIX line must commit to exactly ONE edit.  No "either X or
           delete Y".  Arm E MEASURED 11 of 39 DeepSeek FIX lines offering the
           drafter a branch, against 1 across all 17 Opus feedback files, and
           every harm case was a cheap branch taken.  F1 isolates that.
  CELL F2  BAN + PRESERVE.  Same ban, plus every FIX line must name what the
           edit must NOT destroy.  The Opus critic's edit supplies the field,
           the new value, the branch not to take AND the constraint; F2 adds
           back the constraint.

⛔ THE TRAP, INSTRUMENTED NOT ASSUMED AWAY.  Banning the disjunction may simply
move the coin flip inside the critic.  Branch count is therefore a MANIPULATION
CHECK, never the headline.  The headline is `asserts` delta, conclusion-changing
defects acquired, and identified-vs-repaired reported separately.

⚠️ This is a SUPERSET of arm E's harness: `run_arme.py` is the parent and every
piece of measurement machinery below is unchanged from it except the cell
plumbing.  `ds_opus_loop/loop.py` is imported, not reimplemented.

Design, grounds and pre-registered branches: `PREREG.md`. Read it first.

⚠️ WHAT IS REUSED, AND WHAT IS NOT.  `ds_opus_loop/loop.py` owns the turn
boundary and the pricing arithmetic and both are IMPORTED, not reimplemented:
`loop.adjudicate_floor`, `loop.worst_case`, `loop.clause_row`, `loop._Args`.
What this file adds is the one thing no prior arm has: the review call happens
in a FRESH CONTEXT that has never seen the drafting transcript, and its findings
are then piped back into the drafting transcript in the Opus loop's own
imperative edit-list form.

⛔ `ds_opus_loop/out/` and `selfreview_arm/` are READ ONLY here.  Turn 1 is arm
A's stored draft, resumed byte-identically; every byte this arm writes lands
under `_debug_gen11/ds_critic_arm/`.

⚠️ THE LEDGER HOLE, CLOSED 2026-08-16.  `translate.Client._log_usage` runs
BEFORE `_check_envelope`, so a truncated completion is BILLED and then RAISES.
The record written for that raise used to carry `cost_usd: 0.0`, so the arm's
own totals under-counted by exactly the truncated calls -- $0.01612 of arm E's
$0.08335, and $0.09066 of arm F's $0.15999, i.e. 57% of arm F's spend across 21
billed-then-raised truncations.  The under-report was CORRELATED with the
outcome: the calls that raise are the long reasoners, the hard clauses.  `_send`
now hands the billed envelope out on the exception and `record()` writes the
real cost, token counts and the count at cut BEFORE the raise propagates.
Nothing is retried and no cap is raised: the cap is a pre-registered variable.
The spend gate still takes the MAX of the on-disk records and `usage.jsonl`
attribution, and `reconcile.py` produces the spend of record.

USAGE
    run_armf.py --cell f1 --dry                 price every planned call
    run_armf.py --cell f1 --live --phase critic
    run_armf.py --cell f1 --live --phase repair
"""
import argparse
import concurrent.futures as cf
import copy
import hashlib
import json
import os
import re
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, PHASE1)
sys.path.insert(0, os.path.join(PHASE1, "_debug_gen11", "ds_opus_loop"))

import translate                                              # noqa: E402
import loop                                                   # noqa: E402

CONFIG = os.path.join(HERE, "config_armf.json")
MSG = os.path.join(HERE, "messages")
CELLS = ("f1", "f2")

#: set by main() before anything else runs.  Every path below is per-cell so the
#: two cells cannot overwrite each other.
CELL = None


def OUTDIR():
    return os.path.join(HERE, f"out_{CELL}")
ARM_A_OUT = os.path.join(PHASE1, "_debug_gen11", "ds_opus_loop", "out")
LEDGER = os.path.abspath(os.path.join(
    PHASE1, "..", "..", "..", "semi-formal-experiment", "usage.jsonl"))

#: HARD CAP in measured dollars, owner-set for this experiment.  ⚠️ It is the
#: cap ACROSS BOTH CELLS: `ledger_spent` counts every arm-F row since the single
#: recorded ledger start line, so cell f2 is gated against f1's spend too.  Not a config
#: knob.  A PHASE is priced at its worst case IN FULL, against the ledger,
#: before any of its calls is sent -- the calls run in parallel and a per-call
#: gate cannot serialise against itself.
CAP_USD = 0.25

#: arm A's recorded system-block sha256.  The run REFUSES to send if it moved.
ARM_A_SHA256 = ("3a66c5f54277fbea1c6a8f030435f0c3083d480954b2f6ee3aee"
                "f5f1f4e4c34c")

#: PREREG §3.6.  UNIFORM ACROSS BOTH CELLS, fixed in advance, no per-clause
#: retry at another cap.  ⚠️ 8192, not arm E's 7168: arm E lost 4 of 17 to
#: truncation at 7168 and the loss was CORRELATED with the outcome (the longest
#: reasoners).  Raising it is a DEPARTURE FROM ARM E and is disclosed as one --
#: F-vs-E comparisons on truncation rate are therefore not like-for-like.
CRITIC_MAX_TOKENS = 8192

MAX_WORKERS = 5
MODEL_ID = "deepseek-ai/DeepSeek-V4-Flash-0731"
#: arm E's prompts are >=39,959c of system block alone -> >=10,000 prompt
#: tokens.  Used only to attribute ledger rows, never to price a send.
MIN_PROMPT_TOKENS = 9000


def setup():
    #: LEDGER ATTRIBUTION (2026-08-16): every row this cell prices carries
    #: `#run=armF/<cell>` in `priced_by`, so `reconcile.py` joins on a stamped
    #: fact instead of a timestamp window. `priced_by` was identical on all
    #: 5,012 rows and attribution only worked because the arms happened to run
    #: nearly disjointly.
    translate.set_run_tag(f"armF/{CELL}" if CELL else "armF")
    cfg = translate.load_config(CONFIG)
    rows = translate.load_corpus(cfg)
    prov = translate.resolve_provider(cfg, loop._Args())
    system = translate.build_system(cfg)
    sha = hashlib.sha256(system.encode()).hexdigest()
    if sha != ARM_A_SHA256:
        raise SystemExit(
            f"REFUSED: system block sha256 {sha} != arm A's {ARM_A_SHA256}. "
            f"The prompt is not the one that produced the turn-1 drafts this "
            f"arm resumes. Nothing sent.")
    return cfg, rows, prov, system


def critic_provider(cfg):
    """The critic call only: format forcing OFF and a raised output cap.

    PREREG §3.2 -- forcing the shape is MEASURED to zero out reasoning chars,
    and diagnosis quality tracks reasoning length, so forcing would destroy the
    faculty under test.  PREREG §3.6 -- 4,096 lost 47% of arm D's sample, and
    the loss was correlated with the outcome.  The REPAIR call is built from the
    UNMODIFIED cfg and keeps production's response_format and max_tokens.
    """
    c = copy.deepcopy(cfg)
    c["model"]["format_forcing"] = "none"
    c["model"]["max_tokens"] = CRITIC_MAX_TOKENS
    return translate.resolve_provider(c, loop._Args()), c


def msg(name):
    return open(os.path.join(MSG, name), encoding="utf-8").read()


def critic_msg_name():
    """f1 -> critic_f1.md, f2 -> critic_f2.md.  The ELEVEN ENTRIES AND THE THREE
    ANTI-RULES in both files are byte-identical to arm E's `critic_e.md` (a gate
    in `verify_prompts` refuses to run otherwise).  Only the reply contract at
    the head of the file differs, and F2 differs from F1 only by the PRESERVE
    field."""
    return f"critic_{CELL}.md"


def verify_prompts():
    """⛔ GATE: the review list must be byte-identical to arm E's, in both cells.
    Entry E6 is a MEASURED defect generator (two different critics produced the
    identical weakening on l171_426_n022 by obeying it) and pulling it is
    tempting.  It stays.  Changing the list would add a second variable and
    destroy the comparison; E6 firings are COUNTED instead."""
    tail_marker = "---\n\n**E1. Does a `gloss`"
    ref = open(os.path.join(HERE, "..", "ds_critic_arm", "messages",
                            "critic_e.md"), encoding="utf-8").read()
    ref_tail = ref[ref.index(tail_marker):]
    for cell in CELLS:
        t = open(os.path.join(MSG, f"critic_{cell}.md"), encoding="utf-8").read()
        if t[t.index(tail_marker):] != ref_tail:
            raise SystemExit(f"REFUSED: critic_{cell}.md's review list is not "
                             f"byte-identical to arm E's. Nothing sent.")
        if cell == "f1" and "PRESERVE:" in t:
            raise SystemExit("REFUSED: f1 must not carry the PRESERVE field.")
        if cell == "f2" and "PRESERVE:" not in t:
            raise SystemExit("REFUSED: f2 must carry the PRESERVE field.")
        if "No alternatives" not in t:
            raise SystemExit(f"REFUSED: critic_{cell}.md carries no "
                             f"disjunction ban. Nothing sent.")
    return hashlib.sha256(ref_tail.encode()).hexdigest()


def arm_a_turn1(cid):
    """Arm A's stored turn-1 user block and draft, READ ONLY."""
    p = os.path.join(ARM_A_OUT, f"{cid}.transcript.json")
    st = json.load(open(p, encoding="utf-8"))
    return st["transcript"][0]["content"], st["turns"][0]["raw"]


def state_path(cid):
    return os.path.join(OUTDIR(), f"{cid}.armf.json")


def load_state(cid):
    p = state_path(cid)
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    return {"clause_id": cid, "calls": []}


def phases_done(cid):
    return {c["phase"] for c in load_state(cid)["calls"]}


def all_records(clauses=None):
    """Every call record on disk, ACROSS BOTH CELLS, cell-tagged."""
    out = []
    for cell in CELLS:
        d = os.path.join(HERE, f"out_{cell}")
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.endswith(".armf.json"):
                st = json.load(open(os.path.join(d, f), encoding="utf-8"))
                out += [dict(c, cell=cell, clause_id=st.get("clause_id"))
                        for c in st["calls"]]
    return out


def records_spent(clauses):
    """⚠️ ACROSS BOTH CELLS -- the cap is a total, not a per-cell allowance.

    ⚠️ No longer an under-count. A billed-then-raised call now carries its real
    `cost_usd` (see `record`); this used to differ from `ledger_spent` by
    exactly the 21 truncated calls, i.e. by 57% of the arm's spend.
    """
    return sum(float(c.get("cost_usd") or 0.0) for c in all_records())


def _mine(row):
    """⚠️ ATTRIBUTION. A row TAGGED with another arm's run tag is not this
    arm's spend; an UNTAGGED row still counts, because every row written
    before 2026-08-16 is untagged and over-counting is the safe direction
    under a hard cap. Once a run is tagged (`translate.set_run_tag`), the
    prompt-size heuristic below stops having to carry the attribution alone.
    """
    tag = translate.run_tag_of(row)
    return tag is None or tag.split("/")[0] == RUN_TAG.split("/")[0]


#: this arm's run tag family (see `setup`)
RUN_TAG = "armF"


def ledger_spent(clauses):
    """MAX of the on-disk records and this arm's share of `usage.jsonl` after
    the recorded start line.  The records under-count by construction whenever
    a call raised after being billed (the measured hole); the ledger over-counts
    if a sibling arm is running with a comparably large prompt.  The gate takes
    the larger, which is the safe direction for a hard cap."""
    rec = records_spent(clauses)
    start = start_line()
    if start is None:
        return rec
    tot = 0.0
    try:
        with open(LEDGER, encoding="utf-8") as fh:
            for i, ln in enumerate(fh, 1):
                if i < start or not ln.strip():
                    continue
                try:
                    r = json.loads(ln)
                except json.JSONDecodeError:
                    continue
                if (r.get("model") == MODEL_ID
                        and (r.get("prompt_tokens") or 0) >= MIN_PROMPT_TOKENS
                        and _mine(r)):
                    tot += float(r.get("cost_usd") or 0.0)
    except FileNotFoundError:
        return rec
    return max(rec, tot)


def start_line():
    p = os.path.join(HERE, "_ledger_start.json")
    if os.path.exists(p):
        return json.load(open(p))["first_new_line"]
    return None


def stamp_start_line():
    p = os.path.join(HERE, "_ledger_start.json")
    if os.path.exists(p):
        return
    n = sum(1 for _ in open(LEDGER, encoding="utf-8"))
    json.dump({"first_new_line": n + 1}, open(p, "w"), indent=1)


# ---------------------------------------------------------------- messages

def critic_message(cid, cfg, rows):
    """One user message, in a context that has never seen a drafting turn:
    arm A's turn-1 user block byte-identical, then the module, then the list."""
    user1, draft1 = arm_a_turn1(cid)
    row = loop.clause_row(rows, cfg, cid)
    rebuilt, _, _ = translate.build_user(row, rows, cfg)
    if rebuilt != user1:
        raise SystemExit(f"REFUSED: rebuilt turn-1 user block for {cid} is not "
                         f"byte-identical to arm A's. Nothing sent.")
    body = msg(critic_msg_name()).replace("{module}", draft1.strip())
    return user1 + "\n\n---\n\n" + body


FIX_RE = re.compile(r"^\s*E(\d+)\s*:\s*FIX\b[\s—\-:]*(.*)$")
VERDICT_RE = re.compile(r"^\s*E(\d+)\s*:\s*(PASS|FIX)\b", re.I)


def parse_verdicts(raw):
    """Eleven `E<n>: PASS|FIX -- <sentence>` lines.  Mechanical; no rewriting."""
    verdicts, fixes = {}, []
    for ln in raw.splitlines():
        m = VERDICT_RE.match(ln)
        if not m:
            continue
        n, v = int(m.group(1)), m.group(2).upper()
        verdicts[n] = v
        f = FIX_RE.match(ln)
        if f:
            s = f.group(2).strip()
            if s:
                fixes.append((n, s))
    return verdicts, fixes


def edit_list(fixes):
    """The Opus loop's own feedback shape.  PREREG §3.4 -- the sentences are the
    critic's, extracted, never rewritten."""
    lines = "\n".join(f"{i}. {s}" for i, (_, s) in enumerate(fixes, 1))
    return msg("repair_f.md").format(n=len(fixes), edits=lines)


def repair_transcript(cid, cfg, rows):
    user1, draft1 = arm_a_turn1(cid)
    st = load_state(cid)
    crit = next((c for c in st["calls"] if c["phase"] == "critic"), None)
    if crit is None or not crit.get("raw"):
        return None, []
    _, fixes = parse_verdicts(crit["raw"])
    if not fixes:
        return None, []
    return ([{"role": "user", "content": user1},
             {"role": "assistant", "content": draft1},
             {"role": "user", "content": edit_list(fixes)}], fixes)


# ---------------------------------------------------------------- pricing

def price_phase(cfg, rows, prov, cprov, system, clauses, phase):
    total = 0.0
    for cid in clauses:
        if phase == "critic":
            total += loop.worst_case(system, critic_message(cid, cfg, rows),
                                     cprov, cfg, 0)
        else:
            t, _ = repair_transcript(cid, cfg, rows)
            if t is None:
                continue
            total += loop.worst_case(
                system, "".join(m["content"] for m in t), prov, cfg, 0)
    return total


# ---------------------------------------------------------------- sending

def record(cid, phase, env, floor, sent_chars, error=None, exc=None):
    """⚠️ A RAISING CALL HAS ALREADY SPENT (ledger hole, closed 2026-08-16).

    This used to write `cost_usd: 0.0` for a raise, which hid $0.09066 of this
    arm's $0.15999 — 57% of its spend — across 21 billed-then-raised
    truncations. `translate.billed_record` reads the billed envelope off the
    exception, so the record carries the real cost, the token counts and the
    count at cut. `error` is kept alongside so every reader still works.
    """
    st = load_state(cid)
    st["calls"] = [c for c in st["calls"] if c["phase"] != phase]
    raw = (env or {}).get("text") or ""
    rec = {
        "phase": phase, "raw": raw,
        "sha1": hashlib.sha1(raw.encode()).hexdigest(),
        "cost_usd": float((env or {}).get("cost_usd") or 0.0),
        "usage": (env or {}).get("usage"), "sent_chars": sent_chars,
        "error": error, "floor": floor,
    }
    if exc is not None:
        b = translate.billed_record(exc)
        b.pop("text", None)
        rec.update(b)
        rec["error"] = error or b["raised"]
    st["calls"].append(rec)
    with open(state_path(cid), "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=1)
    return rec


def one_clause(cid, cfg, ccfg, rows, prov, cprov, system, phase, lock):
    row = loop.clause_row(rows, cfg, cid)
    if phase == "critic":
        content = critic_message(cid, cfg, rows)
        try:
            env = translate.Client(cprov, ccfg).complete_messages(
                system, [{"role": "user", "content": content}])
        except Exception as exc:                              # noqa: BLE001
            # ⚠️ THE MEASURED HOLE, CLOSED: this call was BILLED before it
            # raised, and the record now carries what it cost and where it was
            # cut. Nothing is retried and the cap is NOT raised — the cap is a
            # pre-registered variable of this arm (RULING_01_no_retry.md).
            with lock:
                r = record(cid, phase, None, None, len(content), repr(exc),
                           exc=exc)
            return (cid, phase, float(r.get("cost_usd") or 0.0), None,
                    repr(exc))
        with lock:
            record(cid, phase, env, None, len(content))
            open(os.path.join(OUTDIR(), f"{cid}.critic.txt"), "w",
                 encoding="utf-8").write(env["text"])
        return cid, phase, float(env.get("cost_usd") or 0.0), None, None

    t, fixes = repair_transcript(cid, cfg, rows)
    if t is None:
        return cid, phase, 0.0, None, "no-fix-lines"
    sent = "".join(m["content"] for m in t)
    try:
        env = translate.Client(prov, cfg).complete_messages(system, t)
    except Exception as exc:                                  # noqa: BLE001
        with lock:
            r = record(cid, phase, None, None, len(sent), repr(exc), exc=exc)
        return cid, phase, float(r.get("cost_usd") or 0.0), None, repr(exc)
    floor, _ = loop.adjudicate_floor(env["text"], row, cfg, rows)
    with lock:
        record(cid, phase, env, floor, len(sent))
        open(os.path.join(OUTDIR(), f"{cid}.edits.md"), "w",
             encoding="utf-8").write(edit_list(fixes))
        if floor["parsed"]:
            json.dump(json.loads(env["text"]),
                      open(os.path.join(OUTDIR(), f"{cid}.repair.module.json"), "w",
                           encoding="utf-8"), indent=1)
    return cid, phase, float(env.get("cost_usd") or 0.0), floor, None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cell", choices=CELLS, required=True)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--phase", choices=("critic", "repair"), default="critic")
    a = ap.parse_args(argv)
    global CELL
    CELL = a.cell

    list_sha = verify_prompts()
    cfg, rows, prov, system = setup()
    cprov, ccfg = critic_provider(cfg)
    clauses = list(cfg["select"]["clause_ids"])
    os.makedirs(OUTDIR(), exist_ok=True)
    stamp_start_line()

    spent = ledger_spent(clauses)
    grand = price_phase(cfg, rows, prov, cprov, system, clauses, a.phase)

    print(f"CELL {CELL}   critic message {critic_msg_name()}")
    print(f"review list sha256 VERIFIED == arm E ({list_sha[:8]}...)")
    print(f"provider {prov.name}  model {prov.model}")
    print(f"  repair max_tokens {prov.max_tokens} forcing "
          f"{cfg['model']['format_forcing']}")
    print(f"  critic max_tokens {cprov.max_tokens} forcing "
          f"{ccfg['model']['format_forcing']}")
    print(f"system block {len(system)}c  sha256 VERIFIED == arm A "
          f"({ARM_A_SHA256[:8]}...)")
    print(f"phase {a.phase}: {len(clauses)} clauses, worst case ${grand:.4f}; "
          f"measured so far ${spent:.4f}; cap ${CAP_USD:.2f}")
    if spent + grand > CAP_USD:
        raise SystemExit(f"REFUSED: ${spent:.4f} + ${grand:.4f} worst case "
                         f"would cross the ${CAP_USD:.2f} cap. Nothing sent.")
    if not a.live:
        # the truncation tally rides on EVERY summary, the dry one included:
        # a cell that delivered 5 modules of 17 must not read as 17 anywhere.
        print(loop.summarize_truncation(all_records(), f"armF/{CELL}"))
        print("WITHIN cap. nothing sent (--dry).")
        return 0

    todo = [c for c in clauses if a.phase not in phases_done(c)]
    print(f"sending {len(todo)} of {len(clauses)} clauses "
          f"({len(clauses) - len(todo)} already on disk)")

    lock = threading.Lock()
    with cf.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(one_clause, c, cfg, ccfg, rows, prov, cprov, system,
                          a.phase, lock): c for c in todo}
        for f in cf.as_completed(futs):
            try:
                cid, phase, cost, floor, err = f.result()
            except Exception as exc:                          # noqa: BLE001
                print(f"  !! {futs[f]}: {exc!r}")
                continue
            tag = f"  {cid} {phase}: ${cost:.5f}"
            if err:
                print(f"{tag} ERROR {err[:120]}")
            elif floor is None:
                print(tag)
            else:
                print(f"{tag} parsed={floor['parsed']} "
                      f"outcome={floor['outcome']} "
                      f"repair_needed={floor.get('repair_needed')} "
                      f"breaches={len(floor['breaches'])} "
                      f"findings={len(floor['checks'])}")
    print(f"TOTAL (records) ${records_spent(clauses):.5f}  "
          f"(ledger-attributed) ${ledger_spent(clauses):.5f}  "
          f"cap ${CAP_USD:.2f}")
    print(loop.summarize_truncation(all_records(), f"armF/{CELL}"))
    for cell in CELLS:
        rc = [r for r in all_records() if r["cell"] == cell]
        cut = [r for r in rc if r.get("truncated")]
        crit = [r for r in rc if r.get("phase") == "critic"]
        print(f"  cell {cell}: {len(cut)} of {len(rc)} calls cut; "
              f"critic delivered {len(crit) - len([r for r in crit if r.get('error')])}"
              f" of {len(crit)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
