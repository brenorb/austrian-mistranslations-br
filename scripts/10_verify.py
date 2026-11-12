#!/usr/bin/env python3
"""For unmatched sentences in given beads, show best matches anywhere in the other book (global search).
usage: 10_verify.py NAME K [K...]   (uses pairs.json + stored embeddings)"""
import sys, json, pathlib, numpy as np
root = pathlib.Path(__file__).resolve().parent.parent; sys.path.insert(0, str(root / "scripts"))
from common import load_book
name = sys.argv[1]; ks = [int(x) for x in sys.argv[2:]]
pair = next(p for p in json.load(open(root / "pairs.json")) if p["name"] == name)
wd = root / "work5" / name
E1 = np.load(wd / "src.npy"); E2 = np.load(wd / "pt.npy")
_, S1 = load_book(root / pair["src"]); _, S2 = load_book(root / pair["pt"])
s1 = [x for x, _ in S1]; s2 = [x for x, _ in S2]
beads = json.load(open(wd / "beads.json"))
for k in ks:
    b = beads[k]; print(f"=== #{k}  EN{b['en_w']}w PT{b['pt_w']}w")
    if b["pt_w"] and not b["en_w"]:
        for j in range(b["c"], b["d"]):
            sims = E1 @ E2[j]; top = np.argsort(-sims)[:2]
            print(" PT:", s2[j][:260])
            for t in top: print(f"   best EN (sim {sims[t]:.2f}, pos {t/len(s1):.2f} vs {j/len(s2):.2f}):", s1[t][:230])
    elif b["en_w"] and not b["pt_w"]:
        for i in range(b["a"], b["b"]):
            sims = E2 @ E1[i]; top = np.argsort(-sims)[:2]
            print(" EN:", s1[i][:260])
            for t in top: print(f"   best PT (sim {sims[t]:.2f}, pos {t/len(s2):.2f} vs {i/len(s1):.2f}):", s2[t][:230])
