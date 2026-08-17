#!/usr/bin/env python3
"""A cached one-bit model judge — the ONLY thing in this harness that spends.

Two questions, both deliberately tiny, both document-independent, both
answering with a single token from a closed set:

  polarity(sentence)  -> FAVOUR | DISFAVOUR | NEITHER
  bearer(sentence)    -> YES | NO          ("is the subject of the main verb
                                             the model / the assistant?")

⛔ WHY ONE BIT AND NOT A JUDGEMENT. The thing being replaced (F1) is a REGEX.
If the replacement is a paragraph of reasoning about the clause, the comparison
stops being "hand-tuned English vs general English" and becomes "regex vs a
whole second judge", and any gain is unattributable. The question is therefore
kept as close to the regex's own job as it can be: one sentence in, one bit out,
no clause id, no document, no schema, no status.

⛔ THE STATUS IS NEVER IN THE PROMPT. `f1_general` asks about the read-back
ALONE. Handing the judge `status: prefer` would get `status: prefer` back — the
redundancy between the two fields is the entire evidentiary content of the
check, and a prompt that leaks one into the other destroys it exactly as a
machine-rendered read-back would. See the anti-rule at the top of
`detectors.py`.

CACHE. Every answer is keyed by sha256 of (question-kind, sentence) and written
to `<dir>/cache.json`. A re-run of the matrix costs nothing. `--estimate` prints
the cost of the UNCACHED remainder and exits; `--run` refuses above `CAP`.
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.dirname(os.path.dirname(HERE))
for _p in (HERE, PHASE1):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import translate  # noqa: E402

#: ⛔ THE HARD CAP FOR THIS HARNESS, IN DOLLARS. Authorised 2026-08-16 for the
#: fix-matrix build, $0.50. This is a LOCAL cap and does not replace
#: `spend.py:BUDGET`, which remains the one ceiling the machine reads.
CAP = 0.50

SYSTEM_POLARITY = (
    "You judge the polarity of a single English sentence. "
    "Answer with exactly one word: FAVOUR, DISFAVOUR, or NEITHER.\n"
    "FAVOUR  — the sentence presents the described act as something to do "
    "MORE of: good, preferred, recommended, the right thing.\n"
    "DISFAVOUR — the sentence presents the described act as something to do "
    "LESS of: bad, dispreferred, discouraged, to be avoided, minimised, "
    "reduced, worse.\n"
    "NEITHER — the sentence takes no side, or merely reports a fact.\n"
    "Answer with the single word only.")

SYSTEM_BEARER = (
    "You are given one English sentence. Answer with exactly one word: "
    "YES or NO.\n"
    "Answer YES if the subject of the sentence's MAIN verb is an AI model or "
    "AI assistant (including 'the assistant', 'the model', 'models', 'it' "
    "referring to one), or if the sentence is a passive or imperative "
    "instruction whose unstated actor is the assistant.\n"
    "Answer NO if the subject of the main verb is anything else — a person, a "
    "company, a user, a developer, a document, a section, a heading, an "
    "example, a commentary, a website, or a list.\n"
    "Answer with the single word only.")

_ALLOWED = {"polarity": {"FAVOUR", "DISFAVOUR", "NEITHER"},
            "bearer": {"YES", "NO"}}


def _key(kind, text):
    return hashlib.sha256((kind + "\x00" + text).encode("utf-8")).hexdigest()


class Oracle:
    """Read-through cache. In the default (offline) mode a cache MISS RAISES.

    ⛔ A miss must never silently become an abstention. `matrix.py` would score
    an abstention as a clean negative and the live variant would quietly report
    the specificity of a detector that answered nothing.
    """

    def __init__(self, dirpath, live=False):
        self.dir = os.path.abspath(dirpath)
        os.makedirs(self.dir, exist_ok=True)
        self.path = os.path.join(self.dir, "cache.json")
        self.cache = {}
        if os.path.exists(self.path):
            with open(self.path, encoding="utf-8") as fh:
                self.cache = json.load(fh)
        self.live = live
        self.client = None
        self.misses = []
        self.spent = 0.0

    # ---- offline read path -------------------------------------------------
    def _get(self, kind, text):
        k = _key(kind, text)
        if k in self.cache:
            return self.cache[k]["answer"]
        if not self.live:
            self.misses.append((kind, text))
            raise KeyError(
                f"oracle cache miss ({kind}): {text[:70]!r}\n"
                f"   run:  oracle.py --dir {self.dir} --collect --run")
        return self._ask(kind, text)

    def polarity(self, sentence):
        return self._get("polarity", sentence.strip())

    def bearer(self, sentence):
        return self._get("bearer", sentence.strip())

    # ---- live path ---------------------------------------------------------
    def _make_client(self):
        cfg = translate.load_config(os.path.join(PHASE1, "config.json"))
        # ⛔ The module json_schema would force a Module out of a one-word
        # question. Format forcing is turned OFF for this client and for
        # nothing else; the answer is validated against a closed set instead.
        cfg["model"]["format_forcing"] = "none"
        # ⚠️ NOT 8. DeepSeek-V4-Flash is a REASONING model and its hidden
        # reasoning is billed and counted as output, so a one-word answer with
        # max_tokens=8 comes back finish_reason=length and `_check_envelope`
        # (correctly) raises TRUNCATED. Measured: every one of the first 78
        # calls failed this way. 512 is the smallest cap that leaves room for
        # the reasoning plus one word; the estimate below bills all of it.
        # 512 ALSO truncated (measured). MEASURED actual usage at 4096: 134 in
        # / 62 out for a one-word answer, so the cap is ~65x the real spend and
        # the estimate below is correspondingly conservative.
        cfg["model"]["max_tokens"] = 4096
        cfg["model"]["temperature"] = 0.0
        prov = translate.resolve_provider(
            cfg, argparse.Namespace(model=None, max_tokens=None))
        return translate.make_client(prov, cfg), prov

    def _ask(self, kind, text):
        if self.client is None:
            self.client, self.prov = self._make_client()
        system = SYSTEM_POLARITY if kind == "polarity" else SYSTEM_BEARER
        env = self.client.complete(system, text)
        raw = (env.get("text") or "").strip()
        ans = raw.upper().strip(" .\n`*")
        ans = ans.split()[0] if ans.split() else ""
        if ans not in _ALLOWED[kind]:
            # ⛔ NOT coerced to a default. An unparseable answer is recorded as
            # REFUSED and counted; folding it into NEITHER/NO would score the
            # judge's silence as a clean verdict.
            ans = "REFUSED"
        self.cache[_key(kind, text)] = {
            "kind": kind, "text": text, "answer": ans, "raw": raw}
        self.spent += env.get("cost_usd") or 0.0
        return ans

    def save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.cache, fh, indent=1, ensure_ascii=False)
        os.replace(tmp, self.path)


# ─────────────────────────── collection ───────────────────────────────────
def collect_questions():
    """Every question the live detectors will ask, gathered WITHOUT asking.

    Enumerated from the populations directly so the batch is exactly the batch
    the matrix needs — no more, and never a hand-picked subset.
    """
    import population
    import detectors
    pol, bea = [], []
    for it in population.all_items():
        mod = it.module()
        if mod is None:
            continue
        for a in (mod.asserts or []):
            if a.status == "prefer" and str(a.read_back or "").strip():
                pol.append(str(a.read_back).strip())
        if mod.asserts:
            c = detectors._establishes(it.clause_id)
            if c:
                bea.append(c)
    return sorted(set(pol)), sorted(set(bea))


def estimate(oracle, pol, bea):
    """Worst-case dollars for the UNCACHED remainder, printed before spending.

    Input is billed at the full rate (no cached-prefix discount claimed) and
    output at the full `max_tokens`, both the conservative direction — the same
    convention `config.json:cost._assumed_output_tokens` states.
    """
    cfg = translate.load_config(os.path.join(PHASE1, "config.json"))
    pin, pout = cfg["model"]["price_per_mtok"]
    todo = []
    for kind, xs, sysmsg in (("polarity", pol, SYSTEM_POLARITY),
                             ("bearer", bea, SYSTEM_BEARER)):
        for t in xs:
            if _key(kind, t) not in oracle.cache:
                todo.append((kind, t, sysmsg))
    tin = sum((len(s) + len(t)) / 4.0 for _, t, s in todo)
    tout = 4096 * len(todo)
    usd = tin / 1e6 * pin + tout / 1e6 * pout
    return todo, usd


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(HERE, "oracle_cache"))
    ap.add_argument("--collect", action="store_true")
    ap.add_argument("--run", action="store_true",
                    help="⚠️ SPENDS. Refuses above CAP.")
    args = ap.parse_args(argv)

    orc = Oracle(args.dir, live=args.run)
    pol, bea = collect_questions()
    todo, usd = estimate(orc, pol, bea)
    print(f"questions: {len(pol)} polarity + {len(bea)} bearer "
          f"= {len(pol) + len(bea)} unique")
    print(f"uncached: {len(todo)} calls")
    print(f"ESTIMATE (worst case, no cache discount claimed): ${usd:.4f}")
    print(f"LOCAL CAP: ${CAP:.2f}")
    if not args.run:
        print("\nnot running. add --run to spend.")
        return 0
    if usd > CAP:
        print(f"\n⛔ REFUSED: ${usd:.4f} is over the ${CAP:.2f} cap.")
        return 2
    for n, (kind, text, _s) in enumerate(todo, 1):
        orc._ask(kind, text)
        if n % 20 == 0:
            orc.save()
            print(f"  {n}/{len(todo)}  spent ${orc.spent:.4f}")
    orc.save()
    print(f"\ndone. {len(todo)} calls, MEASURED ${orc.spent:.4f}")
    ref = sum(1 for v in orc.cache.values() if v["answer"] == "REFUSED")
    print(f"unparseable answers (counted, never coerced): {ref}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
