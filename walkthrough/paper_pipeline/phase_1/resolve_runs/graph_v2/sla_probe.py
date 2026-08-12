#!/usr/bin/env python3
"""Batch-API SLA probe (Matt-approved 2026-08-11): submit a TINY real batch
job to together.ai, measure turnaround, and verify our model is
batch-eligible -- the measurement that gates whether the batch executor
gets built at all (docs claim "small batches typically finish in minutes";
this checks it for OUR model, today).

3 requests x ~50 output tokens: ~$0.001. Stdlib urllib only (repo
convention). Writes probes/sla_probe_report.json.
"""
import json
import os
import sys
import time
import urllib.request
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(
    HERE, "..", "..", "..", "..", "..", "semi-formal-experiment")))
import providers as P  # noqa: E402

# derive from the config that live traffic verifiably works on
BASE = json.load(open(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "driver_config.json")))["model"]["base_url"].rstrip("/")


def key():
    for rc in ("~/.zshrc", "~/.bashrc", "~/.bash_profile"):
        k = P._parse_shell_export(rc, "TOGETHER_API_KEY")
        if k:
            return k
    return os.environ.get("TOGETHER_API_KEY") or sys.exit("no key")


def req(url, data=None, headers=None, method=None):
    r = urllib.request.Request(url, data=data, headers=headers or {},
                               method=method)
    with urllib.request.urlopen(r, timeout=120) as resp:
        return resp.read()


def main():
    k = key()
    cfg = json.load(open(os.path.join(HERE, "driver_config.json")))
    model = cfg["model"]["model"]
    stamp = uuid.uuid4().hex[:8]

    # 1. build + upload the JSONL (multipart by hand, stdlib only)
    lines = []
    for i in range(3):
        lines.append(json.dumps({
            "custom_id": f"sla-{stamp}-{i}",
            "body": {"model": model, "max_tokens": 50,
                     "messages": [{"role": "user",
                                   "content": f"Reply with the number "
                                              f"{i} and nothing else."}]}}))
    import subprocess, tempfile
    tf = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
    tf.write("\n".join(lines)); tf.close()
    t0 = time.time()
    # multipart via curl: the hand-rolled form was rejected with
    # "Missing required fields"; curl's canonical encoding is accepted
    up = json.loads(subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/files/upload",
         "-H", f"Authorization: Bearer {k}",
         "-F", "purpose=batch-api",
         "-F", f"file_name=sla_{stamp}.jsonl",
         "-F", f"file=@{tf.name}"],
        capture_output=True, text=True, check=True).stdout)
    file_id = up.get("id") or up.get("file_id") or (up.get("data") or {}).get("id")
    print(f"uploaded: {file_id} ({time.time() - t0:.1f}s)")

    # 2. create the batch
    t1 = time.time()
    b = json.loads(req(
        f"{BASE}/batches",
        data=json.dumps({"input_file_id": file_id,
                         "endpoint": "/v1/chat/completions"}).encode(),
        headers={"Authorization": f"Bearer {k}",
                 "Content-Type": "application/json"}))
    job = b.get("job") or b
    bid = job.get("id")
    print(f"batch created: {bid} status={job.get('status')}")

    # 3. poll to terminal
    status, out_id, err_id = job.get("status"), None, None
    while status not in ("COMPLETED", "FAILED", "EXPIRED", "CANCELLED"):
        time.sleep(20)
        j = json.loads(req(f"{BASE}/batches/{bid}",
                           headers={"Authorization": f"Bearer {k}"}))
        j = j.get("job") or j
        status = j.get("status")
        out_id = j.get("output_file_id")
        err_id = j.get("error_file_id")
        print(f"  {time.time() - t1:6.0f}s  {status}")
    turnaround = time.time() - t1

    # 4. results
    results = []
    if out_id:
        blob = req(f"{BASE}/files/{out_id}/content",
                   headers={"Authorization": f"Bearer {k}"}).decode()
        for ln in blob.strip().splitlines():
            r = json.loads(ln)
            results.append({
                "custom_id": r.get("custom_id"),
                "content": ((r.get("response") or {}).get("body") or r)
                .get("choices", [{}])[0].get("message", {})
                .get("content", "")[:40],
                "usage": ((r.get("response") or {}).get("body") or {})
                .get("usage")})
    report = {"model": model, "status": status,
              "turnaround_s": round(turnaround, 1),
              "n_ok": len(results), "results": results,
              "error_file": err_id, "batch_id": bid}
    with open(os.path.join(HERE, "probes", "sla_probe_report.json"),
              "w") as f:
        json.dump(report, f, indent=1)
    print(json.dumps(report, indent=1)[:800])


if __name__ == "__main__":
    main()
