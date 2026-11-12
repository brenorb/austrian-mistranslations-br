#!/usr/bin/env python3
"""Per-book summary table (candidates, upper bound) -> results/summary.csv + results/summary.md"""
import json, pathlib, csv
root = pathlib.Path(__file__).resolve().parent.parent
pairs = json.loads((root / "pairs.json").read_text())
rows = []
for p in pairs:
    wd = root / "work5" / p["name"]
    if not (wd / "flags.json").exists() or p["name"] in ("human_action_de",): continue   # DE OCR too noisy to score
    beads = json.loads((wd / "beads.json").read_text()); fl = json.loads((wd / "flags.json").read_text())
    start = 128 if p["name"] == "whgd" else 0     # skip Brazilian preface/TOC (no source counterpart)
    en = sum(b["en_w"] for b in beads[start:]); pt = sum(b["pt_w"] for b in beads[start:])
    ins = [f for f in fl if f["kind"] in ("ADDITION", "EXPANSION") and f["ctx"] >= 0.5 and f["k"] >= start and f["score"] >= 15]
    om = [f for f in fl if f["kind"] in ("OMISSION", "CONTRACTION") and f["ctx"] >= 0.5 and f["k"] >= start and f["score"] >= 15]
    rows.append(dict(book=p["name"], title=p["title"], author=p["author"], lang=p["lang"], src_words=en, pt_words=pt,
                     insertion_candidates=len(ins), inserted_words=int(sum(f["score"] for f in ins)),
                     inserted_pct=round(100 * sum(f["score"] for f in ins) / max(pt, 1), 2),
                     omission_candidates=len(om), omitted_words=int(sum(f["score"] for f in om))))
rows.sort(key=lambda r: -r["inserted_pct"])
with open(root / "results/summary.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
md = ["| Book (source → PT) | Author | Lang | PT words | Insertion cand. | Inserted words | % of PT | Omission cand. |", "|---|---|---|---:|---:|---:|---:|---:|"]
for r in rows:
    md.append(f"| {r['title']} | {r['author']} | {r['lang']} | {r['pt_words']:,} | {r['insertion_candidates']} | {r['inserted_words']:,} | {r['inserted_pct']} | {r['omission_candidates']} |")
(root / "results/summary.md").write_text("\n".join(md) + "\n")
print("\n".join(md))
