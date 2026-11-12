#!/usr/bin/env python3
"""Slowly fetch mises.org book pages for a candidate slug list (site rate-limits with 429)."""
import sys, json, re, time, subprocess, pathlib
slugs = sys.argv[2:]
outp = pathlib.Path(sys.argv[1])
res = json.loads(outp.read_text()) if outp.exists() else {}
for s in slugs:
    if s in res and res[s].get("files") is not None: continue
    for attempt in range(6):
        r = subprocess.run(["curl","-sL","-m","60","-w","\n%{http_code}",f"https://mises.org/library/book/{s}"],capture_output=True)
        body, code = r.stdout.rsplit(b"\n",1)
        code = code.decode()
        if code == "200": break
        time.sleep(20*(attempt+1))
    if code != "200":
        res[s] = {"error": code}; print(s, "ERR", code, flush=True); continue
    h = body.decode("utf-8","replace")
    t = re.search(r"<title>([^<|]*)", h)
    files = sorted(set(re.findall(r'href="(https://cdn\.mises\.org/[^"]+\.(?:pdf|epub))"', h, re.I)))
    res[s] = {"title": t.group(1).strip() if t else s, "files": files}
    print(s, len(files), flush=True)
    cur = json.loads(outp.read_text()) if outp.exists() else {}
    cur[s] = res[s]; res = cur
    outp.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    time.sleep(12)
