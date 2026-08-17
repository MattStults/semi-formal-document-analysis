#!/usr/bin/env python3
"""JOB 3 — the SPAN-FIRST stage: prototype + cost model. NOT a pipeline stage.

Two halves, and the split is the whole point:

  ENUMERATE  one model call per node. Reads ONLY the span. Emits a structured
             inventory of what the span states. NEVER sees the module. NEVER
             judges coverage.
  COMPARE    pure Python. Joins the inventory to the module. NO model call.

⛔ WHY THE COMPARISON MUST BE MECHANICAL. If one model both enumerates and
judges coverage it can silently agree with itself — the measured failure is
DeepSeek judging its own translations at kappa 0.294, lenient one-way. A judge
that sees the module is a seat, and every seat this project has built starts
from the module and therefore cannot see an omission.

⛔ ANTI-INVENTION GUARD, mechanical. Every enumerated item must carry `quote`,
a VERBATIM substring of the span. `verify_quotes` drops any item whose quote is
not literally present. An enumerator that invents an obligation cannot get it
past this without also inventing text that happens to be in the span.

Usage
    # free: cost model only
    python _debug_gen11/dropped_content/spanfirst.py --cost
    # free: compare an inventory already on disk against the modules
    python _debug_gen11/dropped_content/spanfirst.py --compare inv.json
    # SPENDS: enumerate N clauses (prints the estimate and refuses over --cap)
    TOGETHER_API_KEY=... python _debug_gen11/dropped_content/spanfirst.py \
        --enumerate --ids-file ids.txt --out inv.json --cap 0.05
"""
import argparse
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
GEN11 = os.path.dirname(HERE)
PHASE1 = os.path.dirname(GEN11)
for _p in (HERE, PHASE1):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import selfreport as S  # noqa: E402  (shares the lemma/tokenising helpers)

RUN = S.RUN
CORPUS = os.path.join(PHASE1, "resolve_runs", "graph_v2",
                      "node_corpus_all.json")

#: MEASURED from run.json's own `_price_per_mtok`, together.ai, fetched
#: 2026-08-07: $0.14 in / $0.28 out / $0.03 cached input per Mtok.
PRICE_IN, PRICE_OUT, PRICE_CACHED = 0.14, 0.28, 0.03
MODEL = "deepseek-ai/DeepSeek-V4-Flash-0731"
BASE_URL = "https://api.together.xyz/v1"

# ══════════════════════════════════════════════════════════════════════════
#  THE ENUMERATOR PROMPT.  Note what is ABSENT: the schema, the module, the
#  predicate vocabulary, any worked module. It cannot anchor on the encoding
#  because it is never shown one.
# ══════════════════════════════════════════════════════════════════════════
SYSTEM = """\
You make an INVENTORY of what a passage states. You do not formalise it, you do
not judge anything, and you do not summarise it. You list its separable claims.

For EVERY separable thing the passage states, emit one item:

  force            obligation | prohibition | permission | preference |
                   fact | definition
                   - obligation  the passage directs someone to do it
                   - prohibition the passage directs someone not to do it
                   - permission  the passage says it is allowed / may happen
                   - preference  a comparative: more/less, better, minimise,
                                 favour, "rather than". NOT a plain directive.
                   - fact        a state of the world the passage asserts
                   - definition  the passage says what a term means
  bearer           who it falls on: assistant, developer, user, model, or none
  act              the thing itself, a short verb phrase, no modal verb
  condition        the triggering condition, or null
  defeater         the stated exception or override, or null
  scope_qualifier  EXACTLY one of: only | always | regardless | by_default |
                   none  -- use it whenever the passage uses such a word, and
                   `none` otherwise
  quote            a VERBATIM substring of the passage, copied character for
                   character, that this item comes from

RULES YOU WILL BE CHECKED ON
1. `quote` must appear verbatim in the passage. Any item whose quote does not
   is DISCARDED without being read.
2. A sentence with a stated exception yields TWO items: the base and the
   exception. "X should do A unless B" -> an obligation A with defeater B, AND
   a prohibition of A with condition B.
3. A worked example with a GOOD and a BAD response yields an item for EACH
   pole. Both poles are content.
4. "only relevant to X" also states that it is NOT relevant to non-X: emit the
   exclusion as its own item with scope_qualifier `only`.
5. "By default P" is not the same as P: emit it with scope_qualifier
   `by_default`.
6. Say only what the passage says. Do not add anything you know from elsewhere.

Return JSON: {"items": [ ... ]}  and nothing else."""

USER_TMPL = """PASSAGE (clause {cid})

{span}

Inventory it."""


def span_text(cid):
    """ESTABLISHES + SOURCE TEXT out of the translator's own prompt, so the
    enumerator reads EXACTLY what the translator read and no more."""
    p = os.path.join(RUN, cid + ".prompt_user.txt")
    if not os.path.exists(p):
        return ""
    t = open(p, encoding="utf-8").read()
    est = re.search(r"ESTABLISHES[^\n]*\n(.*?)\n\nPROVIDES", t, re.S)
    src = re.search(r"SOURCE TEXT[^\n]*\n(.*)$", t, re.S)
    parts = []
    if est:
        parts.append(est.group(1).strip())
    if src:
        parts.append(src.group(1).strip())
    return "\n\n".join(parts)


# ── the mechanical comparator — NO MODEL ──────────────────────────────────
FORCE_TO_STATUS = {"obligation": "oblige", "prohibition": "forbid",
                   "permission": "permit", "preference": "prefer"}
NON_DEONTIC = {"fact", "definition"}


def verify_quotes(items, span):
    """Anti-invention guard. Returns (kept, dropped)."""
    norm = " ".join(span.split()).lower()
    kept, dropped = [], []
    for it in items:
        q = " ".join((it.get("quote") or "").split()).lower()
        (kept if q and q in norm else dropped).append(it)
    return kept, dropped


def _lemmas(text):
    return S.content_lemmas(text or "")


def _deontic_surface(m):
    """status -> lemmas of that status's acts and bodies."""
    out = {}
    for a in m.get("asserts") or []:
        toks = set()
        for t in S._preds(a.get("act")) + S._preds(a.get("body")):
            for p in t.split("_"):
                if len(p) >= 3:
                    toks.add(S.lemma(p))
        out.setdefault(a.get("status"), set()).update(toks)
    return out


def _fact_surface(m):
    toks = set()
    for o in m.get("ontology") or []:
        for t in S._preds(o.get("atom")) + S._preds(o.get("body")):
            for p in t.split("_"):
                if len(p) >= 3:
                    toks.add(S.lemma(p))
    for c in m.get("concepts") or []:
        for p in (c.get("name") or "").split("_"):
            if len(p) >= 3:
                toks.add(S.lemma(p))
    return toks


def compare(item, m):
    """Is this inventory item carried by the module? Deterministic.

    Returns (covered: bool, reason: str). THREE tests, in order:
      T1 KIND     a deontic item needs an assert of the MAPPED status; a fact/
                  definition needs an ontology rule or concept.
      T2 SUBJECT  at least one content lemma of `act` must appear among that
                  element's symbols. Symbols only, never the module's prose --
                  prose is where a translator restates a claim it did not
                  encode, and counting it would let a gloss discharge a missing
                  rule.
      T3 QUALIFIER  scope_qualifier imposes a structural requirement:
                  only        -> the module must carry a NEGATIVE-POLE element
                                 (an assert/ontology atom whose name is negated
                                 or a forbid_body entry). Absence = uncovered.
                  by_default  -> the mapped assert's body must contain a
                                 `not ` defeater. Absence = uncovered.
                  regardless  -> the mapped assert must have a body that does
                                 NOT introduce an extra binder beyond the act's
                                 own trigger. (Weak; reported, not scored.)
    """
    force = (item.get("force") or "").lower()
    acts = _lemmas(item.get("act"))
    if force in FORCE_TO_STATUS:
        st = FORCE_TO_STATUS[force]
        surf = _deontic_surface(m)
        if st not in surf:
            return False, f"no `{st}` assert in the module at all"
        if acts and not (acts & surf[st]):
            return False, (f"`{st}` asserts exist but none names "
                           f"{sorted(acts)}")
    elif force in NON_DEONTIC:
        surf = _fact_surface(m)
        if acts and not (acts & surf):
            return False, f"no ontology/concept names {sorted(acts)}"
    else:
        return True, "unknown force -- abstained, not scored"

    q = (item.get("scope_qualifier") or "none").lower()
    if q == "only":
        neg = bool(m.get("forbid_body")) or any(
            re.search(r"\b(not_|non_|no_)", (o.get("atom") or ""))
            for o in (m.get("ontology") or []))
        if not neg:
            return False, "scope `only` but the module has no negative pole"
    if q == "by_default":
        bodies = [a.get("body") or "" for a in (m.get("asserts") or [])
                  if a.get("status") == FORCE_TO_STATUS.get(force)]
        if not any(" not " in (" " + b + " ") for b in bodies):
            return False, "scope `by_default` but no defeater in any body"
    return True, "covered"


def run_compare(inv_path):
    inv = json.load(open(inv_path, encoding="utf-8"))
    diffs = json.load(open(S.DIFFS, encoding="utf-8"))
    truth = {}
    for e in diffs["edits"]:
        truth.setdefault(e["clause"], set()).add(e["class"])
    n_items = n_kept = n_unc = 0
    fired = {}
    for cid, payload in sorted(inv.items()):
        variant = payload.get("variant", "original")
        src = (os.path.join(RUN, cid + ".json") if variant == "original"
               else os.path.join(S.REF_DIR, cid + ".json"))
        m = json.load(open(src, encoding="utf-8"))
        span = span_text(cid)
        kept, dropped = verify_quotes(payload["items"], span)
        n_items += len(payload["items"])
        n_kept += len(kept)
        unc = []
        for it in kept:
            ok, why = compare(it, m)
            if not ok:
                unc.append((it, why))
        n_unc += len(unc)
        lbl = ",".join(sorted(truth.get(cid, set()))) or "UNTOUCHED-FAITHFUL"
        key = f"{cid}/{variant}"
        fired[key] = bool(unc)
        print(f"\n== {key:34s} [{lbl}]")
        print(f"   {len(payload['items'])} enumerated, "
              f"{len(payload['items'])-len(kept)} dropped by the quote guard, "
              f"{len(unc)} UNCOVERED")
        for it, why in unc:
            print(f"   !! [{it.get('force')}/{it.get('scope_qualifier')}] "
                  f"{str(it.get('act'))[:60]}")
            print(f"      -> {why}")
            print(f"      quote: {str(it.get('quote'))[:90]}")
    print(f"\nTOTAL {n_items} items, {n_items-n_kept} failed the quote guard, "
          f"{n_unc} uncovered")
    return fired


# ── cost model ────────────────────────────────────────────────────────────
def cost_model(n_nodes=773):
    """MEASURED inputs, stated one by one, so every figure is auditable."""
    chars_per_tok = 4.12          # MEASURED: (37874+2219)/9725 on this run
    sys_tok = round(len(SYSTEM) / chars_per_tok)
    # span size: MEASURED mean over the 48 spans in the run dir
    spans = []
    for f in sorted(os.listdir(RUN)):
        if f.endswith(".prompt_user.txt"):
            spans.append(len(span_text(f[:-len(".prompt_user.txt")])))
    mean_span = sum(spans) / len(spans)
    p95 = sorted(spans)[int(0.95 * len(spans))]
    span_tok = round(mean_span / chars_per_tok)
    # output: an inventory item is ~45 tokens (6 short fields + a quote);
    # MEASURED item counts come from a live run, INFERRED here at 6 items/node
    per_item, items = 45, 6
    out_tok = per_item * items + 20
    retry = 1.59                  # MEASURED: 0.124439/0.0782 on this run
    rows = []
    for label, in_price, sysc in (("no cache", PRICE_IN, sys_tok),
                                  ("cached system block", PRICE_CACHED, sys_tok)):
        c = (sysc * in_price + span_tok * PRICE_IN) / 1e6 \
            + out_tok * PRICE_OUT / 1e6
        rows.append((label, c, c * n_nodes, c * n_nodes * retry))
    print("SPAN-FIRST COST MODEL")
    print(f"  chars/token          4.12   MEASURED (system+user chars vs "
          f"tokens_in, run 20260815-124836)")
    print(f"  system block       {sys_tok:6d} tok  MEASURED (this file's SYSTEM)")
    print(f"  span, mean         {span_tok:6d} tok  MEASURED over "
          f"{len(spans)} spans (p95 {round(p95/chars_per_tok)})")
    print(f"  output             {out_tok:6d} tok  INFERRED "
          f"({items} items x {per_item} tok)")
    print(f"  retry factor         {retry:.2f}     MEASURED (72 calls / "
          f"48 results)")
    print(f"  prices             ${PRICE_IN}/${PRICE_OUT}/${PRICE_CACHED} per "
          f"Mtok in/out/cached  MEASURED (run.json)")
    print()
    for label, per, tot, tot_r in rows:
        print(f"  {label:22s} ${per:.6f}/node   {n_nodes} nodes = ${tot:.2f}"
              f"   with retries ${tot_r:.2f}")
    # translation baseline for comparison
    base = 0.124439 / 48
    print(f"\n  for scale, the MEASURED translate stage costs ${base:.6f}/node "
          f"(incl. retries) = ${base*n_nodes:.2f} for {n_nodes} nodes")
    return rows


# ── the live pass ─────────────────────────────────────────────────────────
def call(span, cid, max_tokens=1400):
    key = os.environ.get("TOGETHER_API_KEY")
    if not key:
        raise SystemExit("TOGETHER_API_KEY not set — refusing to guess")
    body = {"model": MODEL, "temperature": 0.0, "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user",
                          "content": USER_TMPL.format(cid=cid, span=span)}]}
    # ⚠️ curl, not urllib. together.ai's WAF 403s stdlib urllib — a recorded
    # operational quirk of this provider, reproduced here on first call. This
    # is a throwaway debug harness; a real stage would go through the repo's
    # `providers` module, which already handles it.
    import subprocess
    p = subprocess.run(
        ["curl", "-sS", "-X", "POST", BASE_URL + "/chat/completions",
         "-H", "Authorization: Bearer " + key,
         "-H", "Content-Type: application/json",
         "--data-binary", "@-"],
        input=json.dumps(body).encode(), capture_output=True, timeout=300)
    if p.returncode:
        raise SystemExit("curl failed: " + p.stderr.decode()[:400])
    return json.loads(p.stdout.decode())


def run_enumerate(ids, out_path, cap, variant="original"):
    est_rows = cost_model(len(ids))
    est = est_rows[0][2] * 1.59
    print(f"\nESTIMATE for {len(ids)} clauses: ${est:.4f}  (cap ${cap:.4f})")
    if est > cap:
        raise SystemExit("estimate over cap — refusing")
    inv, spent = {}, 0.0
    for cid in ids:
        span = span_text(cid)
        r = call(span, cid)
        u = r.get("usage") or {}
        spent += (u.get("prompt_tokens", 0) * PRICE_IN
                  + u.get("completion_tokens", 0) * PRICE_OUT) / 1e6
        txt = r["choices"][0]["message"]["content"]
        try:
            items = json.loads(txt).get("items", [])
        except Exception:
            items = []
            print(f"  !! {cid}: unparseable response")
        inv[cid] = {"variant": variant, "items": items,
                    "usage": {k: u.get(k) for k in
                              ("prompt_tokens", "completion_tokens")}}
        print(f"  {cid:22s} {len(items):2d} items  "
              f"in={u.get('prompt_tokens')} out={u.get('completion_tokens')}  "
              f"running ${spent:.4f}")
        if spent > cap:
            print("  !! cap reached — stopping")
            break
    json.dump(inv, open(out_path, "w", encoding="utf-8"), indent=1)
    print(f"\nMEASURED spend this run: ${spent:.4f} over {len(inv)} clauses "
          f"(${spent/max(1,len(inv)):.6f}/node)")
    return inv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cost", action="store_true")
    ap.add_argument("--nodes", type=int, default=773)
    ap.add_argument("--compare")
    ap.add_argument("--enumerate", action="store_true")
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--out", default=os.path.join(HERE, "inventory.json"))
    ap.add_argument("--cap", type=float, default=0.05)
    ap.add_argument("--variant", default="original")
    a = ap.parse_args()
    if a.cost:
        cost_model(a.nodes)
    if a.compare:
        run_compare(a.compare)
    if a.enumerate:
        run_enumerate(a.ids, a.out, a.cap, a.variant)


if __name__ == "__main__":
    main()
