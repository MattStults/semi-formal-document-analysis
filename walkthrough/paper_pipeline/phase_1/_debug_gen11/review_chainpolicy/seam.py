import sys, json
HERE="/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
sys.path.insert(0, HERE)
import translate as T
prov = T.Provider("p","openai-compatible","m","http://x","K",0.2,1000,[1.0,1.0])
cfg = {"model":{"format_forcing":"none"}}
c = T.Client.__new__(T.Client)
c.p, c.cfg, c.forcing = prov, cfg, "none"
c.key="K"; c.spent_usd=0.0; c.calls=0; c._failed_body_hashes=set(); c.retry_variations=0
sys_, user = "SYS", "CLAUSE m0001\ntext"
b1 = json.dumps(c._body(sys_, user)).encode()                 # attempt 1 (run())
b2 = json.dumps(c._body_messages(sys_, [{"role":"user","content":user}])).encode()  # the redraw
print("attempt-1 body == redraw body :", b1 == b2)
import hashlib
c._failed_body_hashes.add(hashlib.sha256(b1).hexdigest())     # attempt 1 failed once
body, payload = c._vary_identical_retry(json.loads(b2.decode()))
print("redraw varied by the seam guard:", payload != b2)
print("redraw final user turn:", repr(body["messages"][-1]["content"][-70:]))
