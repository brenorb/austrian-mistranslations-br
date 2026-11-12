#!/usr/bin/env python3
"""Run alignment for every pair in pairs.json whose source file exists and which has not been aligned yet."""
import json, pathlib, subprocess, sys
root = pathlib.Path(__file__).resolve().parent.parent
pairs = json.loads((root / "pairs.json").read_text())
only = set(sys.argv[1:])
for p in pairs:
    if only and p["name"] not in only: continue
    src = root / p["src"]; pt = root / p["pt"]; wd = root / "work5" / p["name"]
    if (wd / "beads.json").exists() or not src.exists() or not pt.exists(): continue
    print("==", p["name"], flush=True)
    r = subprocess.run([str(root / ".venv/bin/python"), str(root / "scripts/04_align.py"), str(src), str(pt), str(wd), "--lang", p.get("lang", "en")])
    if r.returncode == 0:
        subprocess.run([str(root / ".venv/bin/python"), str(root / "scripts/05_flag.py"), str(wd), "0"])
