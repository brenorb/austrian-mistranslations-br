#!/usr/bin/env python3
"""Download the best English (or German/Spanish original) source file for each slug in en_pages.json.
usage: 07_download_en.py slug=outname[:hint] ...   (hint = substring that must be in file name, e.g. Liberalismus)"""
import json, sys, urllib.parse, subprocess, pathlib, re
root = pathlib.Path(__file__).resolve().parent.parent
pages = json.loads((root / "data/en_pages.json").read_text())
BAD = re.compile(r"discussion|study guide|greek|chinese|hebrew|danish|swedish|hungarian|polish|persian|mandarin|spanish|espa|\bla ley|contra la|politica econ|por una|anatomia|qu[eé] ha|dinero|ciencia econ|vol_?[12]\b", re.I)
for arg in sys.argv[1:]:
    slug, rest = arg.split("=", 1); name, _, hint = rest.partition(":")
    files = pages.get(slug, {}).get("files", [])
    cands = []
    for f in files:
        n = urllib.parse.unquote(f).split("/")[-1]
        if hint and hint.lower() not in n.lower(): continue
        if not hint and BAD.search(n): continue
        cands.append((f, n))
    if not cands: print("NO CANDIDATE", slug, [urllib.parse.unquote(f).split('/')[-1] for f in files]); continue
    cands.sort(key=lambda x: (not x[1].lower().endswith(".epub"), x[1]))    # epub first
    f, n = cands[0]; ext = n.rsplit(".", 1)[-1].lower()
    dst = root / "data/en_raw" / f"{name}.{ext}"
    if not dst.exists():
        subprocess.run(["curl", "-sfL", "-m", "600", "-o", str(dst), f])
    print(slug, "->", dst.name, dst.stat().st_size if dst.exists() else "FAIL", "|", n)
