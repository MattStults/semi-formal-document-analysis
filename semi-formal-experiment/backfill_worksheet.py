"""PATIENT-BACKFILL worksheet + validator — chain_audit_worksheet.py's
sibling, the dual direction: not "are the written chains right?" but "which
unwritten chains does the clause text license?"

Deterministic (no wall clock, sorted output). Two modes:

  python3 backfill_worksheet.py build    --dir DIR   # write DIR/worksheet.json
  python3 backfill_worksheet.py validate --dir DIR   # check DIR/verdict_file.json

WORKSHEET. Every chain-free atom instance of kind `act` in the annotation
artifact (default annotations_ext_v1_merged.json), label-free: clause text
and annotation fields ONLY — no census field, no predicted set, nothing
score-side, and the licensing rules ride in the header verbatim from the
artifacts that own them. Primary stratum = the polarity-marked subset,
emitted first; deterministic (clause_id, name) order within each stratum.

VERDICTS. Closed schema per candidate:
  {clause_id, name, verdict: chain_licensed|no_chain_licensed|unclear,
   corrected_chain: [...]|null, license_quote: "<exact clause text>"|null,
   reason, flag?}
`chain_licensed` REQUIRES a license_quote that is a verbatim substring of
the clause text (checked mechanically), and a corrected_chain of length >= 2
drawn from grammar.PRINCIPALS whose formatted name parses and round-trips.
LENGTH-1 ADDITIONS ARE REFUSED OUTRIGHT: 11 of the chain audit's 12 findings
were agent-missing sole-member `__user` chains, and a lone member cannot
state who acts on whom. Stem and polarity are immutable under this seat —
the correction is always format_name(stem, polarity, corrected_chain)
(decoration only; anything else goes in `flag`, never an edit).
`no_chain_licensed` and `unclear` carry null corrected_chain AND null
license_quote; `unclear` is legal and lands nothing. The verdict file binds
to the worksheet via worksheet_sha256 (the verdict-binding discipline).

FENCES. The FORBIDDEN token tuple is read LIVE from
test_no_reference_leak.py (ast, no import) and scanned over the worksheet
and the verdict file. Tool-authored surfaces (licensing rules, field/CLI
names, summary keys) additionally pass a silence scan (no mention of what
any decoration is later worth); verbatim DOCUMENT text is exempt — the
clause corpus itself legitimately mentions shop prices. The seat brief
(briefs/backfill_author.md) passes the strictest scan via scan_brief().
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import sys

import grammar

HERE = os.path.dirname(os.path.abspath(__file__))
ANNOTATIONS = os.path.join(HERE, "annotations_ext_v1_merged.json")
CLAUSES = os.path.join(HERE, "modelspec_clauses.json")
GUARD = os.path.join(HERE, "test_no_reference_leak.py")

WORKSHEET_NAME = "worksheet.json"
VERDICT_FILE_NAME = "verdict_file.json"

#: Closed vocabularies (assert every one — the golden-author lesson).
KINDS = ("situation", "act", "entity", "value")
STRATA = ("polarity_marked", "unmarked")
VERDICT_VOCAB = ("chain_licensed", "no_chain_licensed", "unclear")
ROW_FIELDS = ("clause_id", "name", "kind", "gloss", "polarity", "stem",
              "atom_quote", "role", "agent_first_reading", "clause_text",
              "stratum")
VERDICT_FIELDS = ("clause_id", "name", "verdict", "corrected_chain",
                  "license_quote", "reason", "flag")
CLI_MODES = ("build", "validate")

#: The licensing rules, VERBATIM from the artifacts that own them
#: (golden_translations.json convention as quoted in briefs/golden_author.md;
#: annotate_prompt.md). The worksheet header carries these; the seat brief
#: quotes the same lines. Procedure may be added around them, never loosening.
LICENSING_RULES = (
    "THE CONVENTION (golden_translations.json, binding on every entry): 'A "
    "chain is written ONLY where the clause names both an actor and a party "
    "the act falls on (or an actor other than the assistant).'",
    "ORDER IS MEANING (annotate_prompt.md): the parties come after a double "
    "underscore, IN ORDER: 'who acts first, then who is acted upon, then any "
    "further party.' '__model_user' and '__user_model' are different atoms "
    "and must not be swapped.",
    "NEVER INFER (annotate_prompt.md, verbatim): 'Write a party ONLY where "
    "the clause names one. Do not infer an affected party from the subject "
    "matter: a clause forbidding an act does not thereby name whoever that "
    "act would harm.'",
    "NO BARE ASSISTANT CHAIN (annotate_prompt.md): 'Do NOT write a chain "
    "whose only party is the assistant itself.' 'A chain earns its place "
    "only when it names a PATIENT the act falls upon or an actor other than "
    "the assistant.'",
    "NO CAPACITY-PACKING (annotate_prompt.md): 'do not pack a chain with "
    "parties the clause mentions in other capacities (who selected a "
    "setting, who benefits): slot two is who the act is done TO.'",
    "DECORATION ONLY: this seat may not touch stems, polarity, kinds, "
    "glosses, spans, or atom membership. Anything believed wrong outside "
    "the chain is recorded in `flag`, never edited here.",
)

#: Silence fence for TOOL/SEAT-AUTHORED text (worksheet header, field/CLI
#: names, brief). What a decoration is later worth is not this seat's
#: business, so nothing authored here may hint at it. Verbatim document
#: quotes are exempt (the clause corpus mentions shop prices on its own).
_SILENCE_PATTERNS = (
    r"\bpric\w+", r"\bdiscount\w*", r"\bcycle\s*5\b", r"CYCLE5",
    r"_DESIGN\b", r"DESIGN\.md", r"PORTFOLIO_REVIEW",
)
#: The brief additionally may not gesture at the evaluation side at all.
_BRIEF_ONLY_PATTERNS = (
    r"\bbehaviou?rs?\b", r"\bpanel\w*\b", r"\bcensus\b", r"\bscores?\b",
    r"\bscoring\b", r"\bpredicted\b", r"\bthresholds?\b",
    r"avoiding-over-and-under-caution", r"harm-avoidance-to-third-parties",
    r"\bhelpfulness\b",
)


class WorksheetError(RuntimeError):
    """A refusal: invalid input artifact or invalid worksheet state."""


# ---------------------------------------------------------------- plumbing

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def forbidden_tokens() -> tuple:
    """The live FORBIDDEN tuple from test_no_reference_leak.py, extracted
    by ast so this module never imports the guard (or anything it fences)."""
    tree = ast.parse(open(GUARD).read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "FORBIDDEN"
                for t in node.targets):
            return tuple(el.value for el in node.value.elts
                         if isinstance(el, ast.Constant))
    raise WorksheetError(f"no FORBIDDEN tuple found in {GUARD}")


def _scan(text: str, extra_patterns=()) -> list:
    hits = [f"forbidden token {tok!r} present"
            for tok in forbidden_tokens() if tok in text]
    for pat in extra_patterns:
        for m in sorted(set(re.findall(pat, text, re.IGNORECASE))):
            hits.append(f"silence-fence pattern {pat!r} matched {m!r}")
    return sorted(hits)


def scan_file(path: str) -> list:
    """FORBIDDEN-token scan over a produced artifact (worksheet or verdict
    file), whole raw text."""
    return _scan(open(path).read())


def scan_brief(path: str) -> list:
    """The strictest scan, for the seat brief: FORBIDDEN tokens plus every
    silence pattern plus the evaluation-side vocabulary."""
    return _scan(open(path).read(),
                 _SILENCE_PATTERNS + _BRIEF_ONLY_PATTERNS)


# -------------------------------------------------------------- enumeration

def candidates(ann: dict) -> list:
    """Every chain-free act-kind atom instance, in artifact order. Asserts
    the closed kind vocabulary on EVERY atom (an invented kind is a refusal,
    not a skip — the calibration-author lesson) and clean parses on every
    candidate name."""
    out = []
    for atom in ann.get("atoms", []):
        kind = atom.get("kind")
        if kind not in KINDS:
            raise WorksheetError(
                f"atom {atom.get('name')!r} on {atom.get('clause_id')!r} "
                f"has kind {kind!r} outside the closed set {KINDS}")
        if kind != "act":
            continue
        p = grammar.parse_name(atom.get("name"))
        if p["error"] or p["principals"]:
            continue
        out.append(atom)
    return out


def build(annotations_path: str = ANNOTATIONS,
          clauses_path: str = CLAUSES,
          outdir: str | None = None) -> str:
    """Write DIR/worksheet.json deterministically; return its path."""
    if outdir is None:
        raise WorksheetError("build requires an output directory")
    with open(annotations_path) as f:
        ann = json.load(f)
    with open(clauses_path) as f:
        clause_text = {c["id"]: c["quote"]
                       for c in json.load(f)["clauses"]}
    rows = []
    for atom in candidates(ann):
        p = grammar.parse_name(atom["name"])
        cid = atom["clause_id"]
        if cid not in clause_text:
            raise WorksheetError(f"no clause text for {cid!r}")
        rows.append({
            "clause_id": cid,
            "name": atom["name"],
            "kind": atom["kind"],
            "gloss": atom.get("gloss", ""),
            "polarity": p["polarity"],
            "stem": p["stem"],
            "atom_quote": atom.get("quote", ""),
            "role": atom.get("role"),
            "agent_first_reading": grammar.describe(atom),
            "clause_text": clause_text[cid],
            "stratum": ("polarity_marked" if p["polarity"] else "unmarked"),
        })
    keys = [(r["clause_id"], r["name"]) for r in rows]
    if len(set(keys)) != len(keys):
        dupes = sorted({k for k in keys if keys.count(k) > 1})
        raise WorksheetError(f"duplicate candidate keys: {dupes}")
    rows.sort(key=lambda r: (STRATA.index(r["stratum"]),
                             r["clause_id"], r["name"]))

    by_stratum = {}
    by_polarity = {}
    for r in rows:
        s = by_stratum.setdefault(r["stratum"],
                                  {"instances": 0, "clauses": set()})
        s["instances"] += 1
        s["clauses"].add(r["clause_id"])
        pol = r["polarity"] or "(none)"
        by_polarity[pol] = by_polarity.get(pol, 0) + 1
    summary = {
        "total_instances": len(rows),
        "distinct_clauses": len({r["clause_id"] for r in rows}),
        "by_stratum": {k: {"instances": v["instances"],
                           "distinct_clauses": len(v["clauses"])}
                       for k, v in sorted(by_stratum.items())},
        "by_polarity": {k: by_polarity[k] for k in sorted(by_polarity)},
    }
    # silence fence on the TOOL-AUTHORED surfaces (document text exempt)
    authored = json.dumps({"licensing_rules": LICENSING_RULES,
                           "row_fields": ROW_FIELDS,
                           "verdict_fields": VERDICT_FIELDS,
                           "summary": summary}, sort_keys=True)
    hits = _scan(authored, _SILENCE_PATTERNS)
    if hits:
        raise WorksheetError("tool-authored worksheet text failed the "
                             "silence scan: " + "; ".join(hits))
    os.makedirs(outdir, exist_ok=True)
    ws_path = os.path.join(outdir, WORKSHEET_NAME)
    with open(ws_path, "w") as f:
        json.dump({"summary": summary,
                   "licensing_rules": LICENSING_RULES,
                   "instances": rows}, f, indent=1, sort_keys=True)
        f.write("\n")
    return ws_path


# ---------------------------------------------------------------- verdicts

def corrected_name(row: dict, chain) -> str:
    """THE only derivation of a decorated name: original stem + original
    polarity + the seat's chain. Stem and polarity cannot move."""
    return grammar.format_name(row["stem"], row["polarity"], list(chain))


def validate(worksheet_path: str, verdict_path: str) -> list:
    """Return the sorted error list (empty == clean)."""
    with open(worksheet_path) as f:
        ws = json.load(f)["instances"]
    with open(verdict_path) as f:
        payload = json.load(f)
    errors = []
    if not isinstance(payload, dict) or "worksheet_sha256" not in payload:
        return [f"{os.path.basename(verdict_path)} must be an object with "
                f"a worksheet_sha256 key binding it to the worksheet"]
    want = sha256_file(worksheet_path)
    if payload["worksheet_sha256"] != want:
        errors.append(
            f"worksheet_sha256 mismatch: verdict file is bound to "
            f"{payload['worksheet_sha256']} but the worksheet is {want}")
    records = payload.get("records") or []
    ws_by_key = {(r["clause_id"], r["name"]): r for r in ws}
    seen = {}
    for i, v in enumerate(records):
        key = (v.get("clause_id"), v.get("name"))
        tag = f"records[{i}] {key}"
        unknown = sorted(set(v) - set(VERDICT_FIELDS))
        if unknown:
            errors.append(f"{tag}: unknown fields {unknown}")
        if key not in ws_by_key:
            errors.append(f"{tag}: not a worksheet instance")
            continue
        seen[key] = seen.get(key, 0) + 1
        row = ws_by_key[key]
        vd = v.get("verdict")
        if vd not in VERDICT_VOCAB:
            errors.append(f"{tag}: verdict {vd!r} outside closed "
                          f"vocabulary {VERDICT_VOCAB}")
            continue
        corr = v.get("corrected_chain")
        quote = v.get("license_quote")
        if vd == "chain_licensed":
            if not isinstance(corr, list) or not corr:
                errors.append(f"{tag}: chain_licensed requires a non-empty "
                              "corrected_chain list")
            else:
                bad = [c for c in corr if c not in grammar.PRINCIPALS]
                if bad:
                    errors.append(f"{tag}: non-principal members {bad}")
                elif len(corr) < 2:
                    errors.append(
                        f"{tag}: length-1 chain addition refused outright "
                        "(length >= 2 required: a lone member cannot state "
                        "who acts on whom — the sole-member-chain lesson)")
                else:
                    new = corrected_name(row, corr)
                    p = grammar.parse_name(new)
                    if p["error"]:
                        errors.append(f"{tag}: corrected name {new!r} does "
                                      f"not parse: {p['error']}")
                    elif (p["principals"] != list(corr)
                          or p["stem"] != row["stem"]
                          or p["polarity"] != row["polarity"]):
                        errors.append(f"{tag}: corrected name round-trip "
                                      "mismatch (stem/polarity/chain)")
            if not (isinstance(quote, str) and quote.strip()):
                errors.append(f"{tag}: chain_licensed requires a non-empty "
                              "license_quote")
            elif quote not in row["clause_text"]:
                errors.append(f"{tag}: license_quote is not a verbatim "
                              "substring of the clause text")
        else:  # no_chain_licensed / unclear land nothing
            if corr is not None:
                errors.append(f"{tag}: {vd} requires corrected_chain null")
            if quote is not None:
                errors.append(f"{tag}: {vd} requires license_quote null "
                              "(the reason field carries any rationale)")
        if not v.get("reason") or len(str(v["reason"]).split()) > 25:
            errors.append(f"{tag}: reason missing or over 25 words")
        flag = v.get("flag")
        if flag is not None and not (isinstance(flag, str) and flag.strip()):
            errors.append(f"{tag}: flag must be a non-empty string when "
                          "present")
    for key in ws_by_key:
        n = seen.get(key, 0)
        if n == 0:
            errors.append(f"worksheet instance {key} has no verdict")
        elif n > 1:
            errors.append(f"worksheet instance {key} has {n} verdicts")
    errors.extend(scan_file(worksheet_path))
    errors.extend(scan_file(verdict_path))
    return sorted(set(errors))


# --------------------------------------------------------------------- CLI

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="backfill_worksheet.py")
    sub = parser.add_subparsers(dest="mode", required=True)
    pb = sub.add_parser("build")
    pb.add_argument("--dir", required=True)
    pb.add_argument("--annotations", default=ANNOTATIONS)
    pb.add_argument("--clauses", default=CLAUSES)
    pv = sub.add_parser("validate")
    pv.add_argument("--dir", required=True)
    args = parser.parse_args(argv)
    if args.mode == "build":
        ws_path = build(args.annotations, args.clauses, args.dir)
        with open(ws_path) as f:
            summary = json.load(f)["summary"]
        print(json.dumps(summary, indent=1, sort_keys=True))
        print(f"wrote {summary['total_instances']} instances -> {ws_path}")
        return 0
    ws_path = os.path.join(args.dir, WORKSHEET_NAME)
    vpath = os.path.join(args.dir, VERDICT_FILE_NAME)
    errors = validate(ws_path, vpath)
    if errors:
        for e in errors:
            print("FAIL:", e)
        print(f"validate: {len(errors)} error(s)")
        return 1
    with open(vpath) as f:
        records = json.load(f)["records"]
    dist = {}
    for r in records:
        dist[r["verdict"]] = dist.get(r["verdict"], 0) + 1
    print("validate: CLEAN —", len(records), "records cover the worksheet "
          "exactly once;", json.dumps(dict(sorted(dist.items()))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
