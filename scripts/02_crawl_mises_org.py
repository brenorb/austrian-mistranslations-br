#!/usr/bin/env python3
"""Crawl mises.org/library/books, collect every book page and its pdf/epub links."""
import re, sys, json, urllib.request, pathlib, concurrent.futures as cf
import subprocess
def get(url):
    # urllib gets 403 from mises.org (bot filter); curl works
    r = subprocess.run(["curl","-sfL","-m","60",url],capture_output=True)
    if r.returncode: raise RuntimeError(f"curl {r.returncode} {url}")
    return r.stdout.decode("utf-8","replace")
slugs = []
p = 0
while True:
    try: h = get(f"https://mises.org/library/books?page={p}")
    except Exception as e: print("stop", p, e); break
    s = re.findall(r'href="/library/book/([^"#?]+)"', h)
    new = [x for x in dict.fromkeys(s) if x not in slugs]
    if not new: break
    slugs += new; p += 1; print("page", p, len(slugs), flush=True)
def one(s):
    try:
        h = get(f"https://mises.org/library/book/{s}")
        t = re.search(r"<title>([^<|]*)", h)
        files = sorted(set(re.findall(r'href="(https://cdn\.mises\.org/[^"]+\.(?:pdf|epub))"', h, re.I)))
        return {"slug": s, "title": t.group(1).strip() if t else s, "files": files}
    except Exception as e:
        return {"slug": s, "error": str(e)}
with cf.ThreadPoolExecutor(8) as ex: res = list(ex.map(one, slugs))
pathlib.Path(sys.argv[1]).write_text(json.dumps(res, ensure_ascii=False, indent=1))
print(len(res), "books")
