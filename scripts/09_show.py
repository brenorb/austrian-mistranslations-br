#!/usr/bin/env python3
"""Show full beads around index. usage: 09_show.py WORKDIR K [radius]"""
import sys, json
wd, k = sys.argv[1], int(sys.argv[2]); r = int(sys.argv[3]) if len(sys.argv) > 3 else 1
b = json.load(open(f"{wd}/beads.json"))
for i in range(max(0, k - r), min(len(b), k + r + 1)):
    x = b[i]; s = x["sim"]
    print(f"[{i}{' <<<' if i==k else ''}] sim={s and round(s,2)} EN{x['en_w']}w PT{x['pt_w']}w\n EN: {x['en']}\n PT: {x['pt']}\n")
