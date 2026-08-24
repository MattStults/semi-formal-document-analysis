#!/usr/bin/env python3
"""Semi-formal model checker for ERROR_CALCULUS.md (v0, 2026-08-24).

Abstracts a reported failure to its router-relevant state and EXHAUSTIVELY
explores every reachable state under the R1-R5 transition rules, checking:
  P1 COVERAGE/CONSISTENCY: every OPEN state has exactly one applicable rule
     (zero = a gap in the calculus; two+ = an ambiguity).
  P2 TERMINATION: every path reaches a terminal outcome within a finite
     bound (budgets on one-pass moves make this provable-by-search).
  P3 NO SILENT LOOPS: no cycle among open states.
Nondeterminism (audit outcomes, panel outcomes, whether a move improves the
census) is modeled by branching over ALL possibilities — so a property
holds only if it holds on every branch.

State: (census, v, panel_done, audited, retranslated,
        consumer_built, mint_attempts, defens_used, delta_attempts)
  census ∈ {SEP, REACH, UNSAT}
  v ∈ {UNAUDITED, FAITHFUL, UNFAITHFUL_KNOWN}
Terminals: RESOLVED_T, RESOLVED_V, RESOLVED_D, RESOLVED_I, DEFENSIBLE,
           TERMINAL_DOC, REVERTED (delta failed realization).
"""
import itertools, collections

SEP, REACH, UNSAT = "SEP", "REACH", "UNSAT"
MINT_BUDGET = 2

def rules(s):
    """Return list of (rule_name, [successor states or terminal strings])."""
    census, v, panel_done, audited, retrans, built, mints, defens, deltas = s
    out = []
    # R1: escalate truth to panel (once). Branch: overturn -> resolved; stand -> continue.
    if not panel_done:
        out.append(("R1", ["RESOLVED_T",
                           (census, v, True, audited, retrans, built, mints, defens, deltas)]))
        return out  # ordered router: R1 fires first when applicable
    # R2: faithfulness audit (once). Branch: faithful | unfaithful.
    if not audited:
        out.append(("R2", [(census, "FAITHFUL", True, True, retrans, built, mints, defens, deltas),
                           (census, "UNFAITHFUL_KNOWN", True, True, retrans, built, mints, defens, deltas)]))
        return out
    # R2b: known-unfaithful -> retranslate (once); census may become anything.
    if v == "UNFAITHFUL_KNOWN":
        if not retrans:
            out.append(("R2b", [ (c, "FAITHFUL", True, True, True, built, mints, defens, deltas)
                                 for c in (SEP, REACH, UNSAT) ] + ["RESOLVED_V"]))
            return out
        # unfaithful AND already retranslated once: calculus says? (checking for gaps)
        return out
    # v == FAITHFUL from here.
    # R3: current-separable -> mechanical delta. Branches: validates (resolved),
    # fails realization (reverted... then what? state unchanged = potential gap),
    # or NO candidate passes V1-V5 (potential gap).
    if census == SEP:
        if deltas < 2:   # A1 delta budget; A2: revert re-enters consuming budget
            nxt = (census, v, panel_done, audited, retrans, built, mints, defens, deltas+1)
            out.append(("R3", ["RESOLVED_D", nxt]))
        else:            # A1 R3x: missing intension -> mint track
            if mints < MINT_BUDGET:
                out.append(("R3x", [(SEP, v, panel_done, audited, retrans, built, mints+1, defens, 0),
                                    (REACH, v, panel_done, audited, retrans, built, mints+1, defens, 0),
                                    (UNSAT, v, panel_done, audited, retrans, built, mints+1, defens, 0)]))
            else:
                term = ["TERMINAL_DOC"] + (["DEFENSIBLE"] if not defens else [])
                out.append(("R3x", term))
        return out
    # R4: reachable-separable -> build consumer / annotate (once) -> census SEP.
    if census == REACH:
        # A4: per-FEATURE consumer builds — R4 always applicable at REACH
        # (the REACHABLE certificate names the unconsumed feature); model
        # bounds repeated builds via the mint budget that produced them.
        out.append(("R4", [(SEP, v, panel_done, audited, retrans, True, mints, defens, deltas)]))
        return out
    # R5: UNSAT -> mint (budgeted). Branch: separates (census->SEP or REACH) | doesn't.
    if census == UNSAT:
        if mints < MINT_BUDGET:
            out.append(("R5", [(SEP, v, panel_done, audited, retrans, built, mints+1, defens, 0),
                               (REACH, v, panel_done, audited, retrans, built, mints+1, defens, 0),
                               (UNSAT, v, panel_done, audited, retrans, built, mints+1, defens, 0)]))
            return out
        # exhausted: I4 ruling OR defensibility (one pass)
        term = ["TERMINAL_DOC"] + (["DEFENSIBLE"] if not defens else [])
        out.append(("R5x", term))
        return out
    return out

def check():
    init = [(c, "UNAUDITED", False, False, False, False, 0, False, 0)
            for c in (SEP, REACH, UNSAT)]
    seen = set(); gaps = []; ambigs = []; edges = collections.defaultdict(set)
    frontier = list(init)
    while frontier:
        s = frontier.pop()
        if s in seen: continue
        seen.add(s)
        rs = rules(s)
        if len(rs) == 0:
            gaps.append(s); continue
        if len(rs) > 1:
            ambigs.append((s, [r for r,_ in rs]))
        for rname, succs in rs:
            for t in succs:
                if isinstance(t, str):
                    edges[s].add(t)
                else:
                    edges[s].add(t); frontier.append(t)
    # termination: since every rule consumes a budget or reaches terminal,
    # cycles among open states would show as s reachable from itself
    def reaches_cycle():
        color = {}
        def dfs(u):
            color[u] = 1
            for w in edges.get(u, ()):
                if isinstance(w, str): continue
                if color.get(w) == 1: return True
                if color.get(w) is None and dfs(w): return True
            color[u] = 2; return False
        return any(dfs(s) for s in list(seen) if color.get(s) is None)
    # dead ends within successors that are open-but-gap
    print(f"reachable open states: {len(seen)}")
    print(f"P1 gaps (open state, NO applicable rule): {len(gaps)}")
    for g in gaps: print("   GAP:", g)
    print(f"P1 ambiguities (2+ rules applicable): {len(ambigs)}")
    for a in ambigs: print("   AMBIG:", a)
    print(f"P3 cycles among open states: {'FOUND' if reaches_cycle() else 'none'}")
    # pseudo-terminals introduced by branching that the calculus does not define:
    pseudo = set()
    for s, ts in edges.items():
        for t in ts:
            if isinstance(t, str) and t in ("R3_NO_VALID_DELTA", "REVERTED_THEN"):
                pseudo.add(t)
    print("P1 UNDEFINED OUTCOMES the calculus reaches but does not specify:", sorted(pseudo) or "none")

if __name__ == "__main__":
    check()
