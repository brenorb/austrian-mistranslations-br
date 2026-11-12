#!/usr/bin/env python3
"""Concept-injection detector (the tweet's 'store of value' pattern): PT bead contains a key technical term
that its aligned source bead does not (or the reverse).  usage: 11_lexicon.py work5/NAME [more...]"""
import sys, json, re
LEX = [  # (label, PT regex, EN regex)
 ("store of value", r"reserva(?:s)? de valor|armazenador(?:es)? de valor", r"store(?:s)? of value|value store"),
 ("unit of account", r"unidade(?:s)? de conta", r"unit(?:s)? of account"),
 ("medium of exchange", r"meio(?:s)? de troca|meio(?:s)? de pagamento", r"medi(?:um|a) of exchange"),
 ("public good", r"bens? públicos?", r"public goods?"),
 ("externalit", r"externalidades?", r"externalit"),
 ("liquidity", r"liquidez", r"liquid"),
 ("fiat", r"fiduciári|fiat", r"fiat"),
 ("electronic/digital money", r"eletrônic|digital|computador", r"electronic|digital|computer"),
 ("central bank", r"banco central|bancos centrais", r"central bank"),
 ("GDP", r"\bPIB\b|produto interno", r"\bGDP\b|gross domestic|gross national"),
 ("Keynes", r"keynes", r"keynes"),
 ("bitcoin/crypto", r"bitcoin|criptomoeda", r"bitcoin|cryptocurrenc"),
 ("monetarism", r"monetarismo|monetarista", r"monetari(?:sm|st)"),
 ("socialism", r"socialis", r"socialis"),
 ("inflation", r"inflação|inflacion", r"inflation"),
 ("interest rate", r"taxa(?:s)? de juros?", r"interest rate"),
]
for wd in sys.argv[1:]:
    beads = json.load(open(f"{wd}/beads.json")); res = []
    for k, b in enumerate(beads):
        if not b["pt"] or not b["en"] or (b["sim"] or 0) < 0.45: continue
        for lab, pr, er in LEX:
            p = bool(re.search(pr, b["pt"], re.I)); e = bool(re.search(er, b["en"], re.I))
            if p and not e and lab in ("store of value","unit of account","medium of exchange","fiat","electronic/digital money","GDP","bitcoin/crypto","monetarism","liquidity","externalit","central bank","Keynes"):
                res.append((lab, k, b))
    print(f"\n##### {wd}: {len(res)} PT-only concept hits")
    seen = 0
    for lab, k, b in res:
        print(f"[{lab}] #{k} sim={b['sim']:.2f}\n EN: {b['en'][:200]}\n PT: {b['pt'][:260]}"); seen += 1
        if seen >= 12: break
