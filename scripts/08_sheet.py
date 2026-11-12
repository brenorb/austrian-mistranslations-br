#!/usr/bin/env python3
"""Print a compact review sheet. usage: 08_sheet.py WORK/NAME KINDS(comma) [min_score] [min_ctx] [skip] [limit] [width]"""
import sys, json
wd = sys.argv[1]; kinds = sys.argv[2].split(",")
ms = float(sys.argv[3]) if len(sys.argv) > 3 else 20; mc = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
skip = int(sys.argv[5]) if len(sys.argv) > 5 else 0; lim = int(sys.argv[6]) if len(sys.argv) > 6 else 40
W = int(sys.argv[7]) if len(sys.argv) > 7 else 420
beads = json.load(open(f"{wd}/beads.json")); fl = json.load(open(f"{wd}/flags.json"))
sel = [f for f in fl if f["kind"] in kinds and f["score"] >= ms and f["ctx"] >= mc]
import os
sel.sort(key=(lambda f: -f["score"]) if os.environ.get("BYSCORE") else (lambda f: f["k"]))
for f in sel[skip:skip + lim]:
    k = f["k"]; prev = beads[k - 1] if k else None
    print(f"--- #{k} {f['kind']} s={f['score']} sim={f['sim'] and round(f['sim'],2)} EN{f['en_w']}w PT{f['pt_w']}w")
    if prev and f["en_w"] == 0: print("  prevPT:", prev["pt"][-150:])
    if f["en"]: print("  EN:", f["en"][:W])
    if f["pt"]: print("  PT:", f["pt"][:W+80])
print(f"[{len(sel)} total matching]")
