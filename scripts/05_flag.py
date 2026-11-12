#!/usr/bin/env python3
"""Flag suspicious beads from beads.json (additions / omissions / expansion / low similarity / negation flips).
usage: 05_flag.py WORKDIR [N_PRINT]
Each flag carries `ctx` = fraction of well-aligned neighbours (±12 beads); flags in badly aligned stretches
(front/back matter, differing editions) have low ctx and are down-weighted."""
import sys, json, pathlib, re
from collections import Counter
wd = pathlib.Path(sys.argv[1]); beads = json.loads((wd / "beads.json").read_text())
tot_en = sum(b['en_w'] for b in beads); tot_pt = sum(b['pt_w'] for b in beads)
RATIO = min(1.3, max(0.8, tot_pt / max(1, tot_en)))   # per-book baseline PT/EN length ratio
NEG_EN = re.compile(r"\b(not|no|never|neither|nor|cannot|can't|without|none|nothing|nobody|n't|impossible|unable|fail(?:s|ed)?\s+to)\b", re.I)
NEG_PT = re.compile(r"\b(não|nem|nunca|jamais|sem|nenhum[a]?s?|nada|ninguém|impossível|incapaz|deixa(?:m|r|ria|ram)?\s+de|tampouco)\b", re.I)
NEG_DE = re.compile(r"\b(nicht|kein\w*|nie|niemals|ohne|weder|nichts|niemand|unmöglich)\b", re.I)
NOTE = re.compile(r"\[N\.? ?(?:do )?[TE]\.?\]|\(N\.? ?(?:do )?[TE]\.?\)|Nota (?:do|da) (?:tradutor|editor|revisor)|N\.T\.|N\.E\.", re.I)
CITE = re.compile(r"^\s*(?:Ver (?:também|ainda)?|Cf\.|Veja|Op\. cit|Ibid|Id\.|See |Cf |\d{1,3}\s)|\b(?:p\.|pp\.|págs?\.|ed\.|Press|Editora|Nova York|São Paulo|Rio de Janeiro|Cambridge|Chicago|London|Oxford|Princeton|vol\.)\b", re.I)

good = [1 if (b["en_n"] == 1 and b["pt_n"] == 1 and b["sim"] is not None and b["sim"] > 0.7) else 0 for b in beads]
pref = [0]
for g in good: pref.append(pref[-1] + g)
def ctx(k, r=12):
    a, z = max(0, k - r), min(len(beads), k + r + 1)
    return (pref[z] - pref[a]) / max(1, z - a)

import numpy as np
E1 = np.load(wd / "src.npy"); E2 = np.load(wd / "pt.npy")
def global_best(b):
    """Best cosine of this bead's unmatched side against the WHOLE other book (detects moved / mis-split text)."""
    if b["en_w"] == 0 and b["pt_w"] > 0:
        v = E2[b["c"]:b["d"]]; return float((v @ E1.T).max()) if len(v) else 0.0
    if b["pt_w"] == 0 and b["en_w"] > 0:
        v = E1[b["a"]:b["b"]]; return float((v @ E2.T).max()) if len(v) else 0.0
    return 0.0
cen = [0]; cpt = [0]
for b in beads: cen.append(cen[-1] + b["en_w"]); cpt.append(cpt[-1] + b["pt_w"])
def win_extra(k, r=4):
    a, z = max(0, k - r), min(len(beads), k + r + 1)
    return (cpt[z] - cpt[a]) - RATIO * (cen[z] - cen[a])
flags = []
for k, b in enumerate(beads):
    en_w, pt_w, sim = b["en_w"], b["pt_w"], b["sim"]
    kind = None; score = 0
    if en_w == 0 and pt_w >= 10:
        kind, score = "ADDITION", pt_w
    elif pt_w == 0 and en_w >= 15:
        kind, score = "OMISSION", en_w
    elif en_w and pt_w:
        extra = pt_w - RATIO * en_w
        if extra >= 18 and pt_w >= 1.6 * en_w: kind, score = "EXPANSION", extra
        elif b["pt_n"] > b["en_n"] and extra >= 14: kind, score = "EXPANSION", extra
        elif -extra >= 25 and en_w >= 1.6 * pt_w: kind, score = "CONTRACTION", -extra
        elif sim is not None and sim < 0.5 and max(en_w, pt_w) >= 10: kind, score = "LOWSIM", (0.5 - sim) * 100
        elif sim is not None and sim > 0.6 and en_w >= 8 and pt_w >= 8 and bool(NEG_EN.search(b["en"])) != bool(NEG_PT.search(b["pt"])):
            kind, score = "NEGATION", 10 + (sim - 0.6) * 20
    if not kind: continue
    we = win_extra(k)
    if kind in ('ADDITION', 'EXPANSION') and we < 0.6 * score: kind += '_ARTIFACT'
    if kind in ('OMISSION', 'CONTRACTION') and -we < 0.6 * score: kind += '_ARTIFACT'
    c = ctx(k)
    gb = global_best(b) if kind in ("ADDITION", "OMISSION") else None
    if gb is not None and gb >= 0.80: kind += "_MOVED"
    text = b["pt"] or b["en"]
    if NOTE.search(text): kind += "_NOTE"
    elif CITE.search(text) and len(text.split()) < 40: kind += "_CITE"
    flags.append(dict(k=k, kind=kind, score=round(score, 1), ctx=round(c, 2), gbest=None if gb is None else round(gb, 2), wextra=round(we, 1), **b))
flags.sort(key=lambda f: -(f["score"] * (0.3 + f["ctx"])))
(wd / "flags.json").write_text(json.dumps(flags, ensure_ascii=False, indent=1))
print(wd.name, dict(Counter(f["kind"] for f in flags)), "good-ctx flags:", sum(1 for f in flags if f["ctx"] >= 0.5 and "_" not in f["kind"]))
N = int(sys.argv[2]) if len(sys.argv) > 2 else 15
shown = 0
for f in flags:
    if shown >= N: break
    if "_" in f["kind"] or f["ctx"] < 0.4: continue
    shown += 1
    print(f"\n#{f['k']} [{f['kind']} score={f['score']} ctx={f['ctx']} sim={f['sim'] and round(f['sim'],2)} EN{f['en_w']}w/{f['en_n']}s PT{f['pt_w']}w/{f['pt_n']}s]\n EN: {f['en'][:500]}\n PT: {f['pt'][:600]}")
