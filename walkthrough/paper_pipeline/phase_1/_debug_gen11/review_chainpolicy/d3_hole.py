import sys, json
HERE="/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
sys.path.insert(0, HERE)
import fixtures, translate as T

class Scripted:
    def __init__(self,*r): self.r=list(r); self.calls=[]
    def complete_messages(self, system, messages):
        self.calls.append((system,[dict(m) for m in messages]))
        return {"text": self.r[min(len(self.calls)-1, len(self.r)-1)],
                "in":10,"out":10,"finish_reason":"stop"}

bad = fixtures.assertion(read_back="producing this is forbidden",
                         read_back_slots=["M"])          # a real breach
BIG = fixtures.module_json(claims=["C1 a","C2 b","C3 c","C4 d"],
                           asserts=[bad, bad, bad])
GARBAGE = "sorry, I cannot produce JSON for this clause"
GOOD    = fixtures.module_json()                          # 1 claim, 1 assert

out = T.repair_loop(BIG, clause={"id":"m0001"},
                    model=Scripted(BIG, GARBAGE, GOOD), max_attempts=5)
print("status      :", out.status)
print("restarted   :", out.restarted)
print("attempts    :", out.attempts)
print("flags       :", out.flags)              # <-- earned against a DISCARDED draft?
print("pre_restart :", out.pre_restart_flags)

import graveyard
keep, why = graveyard.should_keep(out, 5, {"repaired":0.0,"first_try":0.0},
                                  clause_id="m0001")
print("should_keep :", keep, "|", why)
