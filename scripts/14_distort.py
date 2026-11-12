#!/usr/bin/env python3
"""Same-length distortion detectors over EVERY aligned 1-1 / 1-2 / 2-1 bead (not just flagged ones).
 NUM   numbers present on one side only (after normalising PT decimal comma / thousands dot)
 NEG   negation present in source but not in PT (or vice versa), with antonym/lexical-negation guards
 QUANT 'only / always / never / all' quantifiers dropped or added
 HEDGE 'may / probably / seems / perhaps' hedges dropped or added (strength shift)
 SEM   low cross-lingual similarity between similar-length sentences in a well-aligned stretch
usage: 14_distort.py NAME [NAME...]  -> work5/NAME/distort.json"""
import sys, json, re, pathlib, unicodedata
root = pathlib.Path(__file__).resolve().parent.parent

MULT = [(r"thousand|mil\b", 1e3), (r"million|milh(?:ão|ões)|milhao|milhoes", 1e6), (r"billion|bilh(?:ão|ões)|bilhao|bilhoes", 1e9), (r"trillion|trilh(?:ão|ões)", 1e12)]
def norm_nums(s):
    """significant numbers only: years, >=100, decimals/percentages; multipliers (mil/milhões/billion) applied."""
    out = []
    s = re.sub(r"^\s*\d{1,3}\s+(?=[A-Z“\"(])", "", s)                                  # leading footnote mark
    s = re.sub(r"(?<=[.,;:!?”\"’)])\s?\d{1,3}(?=\s+[A-Z“\"(])", " ", s)                 # footnote mark after punctuation
    s = re.sub(r"(?<=[a-zà-ú])\d{1,3}(?=[\s.,;:])", "", s)                              # superscript glued to a word
    for m in re.finditer(r"(?<![\w.])\$?(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)(\s?(?:%|percent|por cento|thousand|mil\b|million|milh\w+|billion|bilh\w+|trillion|trilh\w+))?", s, re.I):
        t, suf = m.group(1), (m.group(2) or "").strip()
        if re.fullmatch(r"(1[5-9]|20)\d\d[.,]\d", t): t = t[:4]          # year glued to a footnote mark
        if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", t): t = re.sub(r"[.,]", "", t)
        else: t = t.replace(",", ".")
        try: v = float(t)
        except ValueError: continue
        for pat, mult in MULT:
            if re.fullmatch(pat, suf, re.I): v *= mult
        if v >= 100 or v != int(v) or suf in ("%", "percent", "por cento"):
            out.append(round(v, 4))
    return out

NEG_EN = re.compile(r"\b(not|never|neither|nor|cannot|without|none|nothing|nobody|nowhere|hardly|scarcely|rarely|n't|no one|impossible|unable|fail(?:s|ed|ing)? to|lack(?:s|ed|ing)?|absence)\b|(?<![A-Za-z])\bno\b(?!\.\s?\d|\s\d)", re.I)
NEG_PT = re.compile(r"\b(não|nem|nunca|jamais|sem|nenhum[a]?s?|nada|ninguém|tampouco|impossível|incapaz|incapazes|impossibilidade|falta|ausência|deixa(?:m|r|ria|ram|rá)? de|raramente|dificilmente|pouco|nenhures)\b", re.I)
QUANT = [("only", r"\b(only|solely|merely|exclusively)\b", r"\b(apenas|somente|só|unicamente|exclusivamente|meramente|simplesmente|único|única|únicos|únicas|nada mais)\b"),
         ("always", r"\balways\b", r"\b(sempre|invariavelmente|constantemente|todo o tempo)\b"),
         ("never", r"\bnever\b", r"\b(nunca|jamais)\b"),
         ("all/every", r"\b(all|every|everyone|everybody|entire|whole)\b", r"\b(todo|toda|todos|todas|cada|inteiro|inteira|inteiros|inteiras|qualquer|totalmente|completamente)\b"),
         ("any", r"\bany\b", r"\b(qualquer|quaisquer|algum|alguma|alguns|algumas|nenhum|nenhuma)\b")]
HEDGE_EN = re.compile(r"\b(may|might|perhaps|probably|possibly|seems?|appears?|tends? to|likely|presumably|apparently)\b", re.I)
HEDGE_PT = re.compile(r"\b(pode|podem|poderia|poderiam|talvez|provavelmente|possivelmente|parece|parecem|tende|tendem|tendência|provável|presumivelmente|aparentemente|pode ser)\b", re.I)
MOD_EN = re.compile(r"\b(must|has to|have to|necessarily|certainly|undoubtedly|clearly|obviously|inevitably)\b", re.I)
MOD_PT = re.compile(r"\b(deve|devem|tem de|têm de|tem que|têm que|necessariamente|certamente|sem dúvida|claramente|obviamente|inevitavelmente|necessário|precisa|precisam)\b", re.I)

for name in sys.argv[1:]:
    wd = root / "work5" / name
    beads = json.loads((wd / "beads.json").read_text()); fl = {f["k"]: f for f in json.loads((wd / "flags.json").read_text())}
    good = [1 if (b["en_n"] == 1 and b["pt_n"] == 1 and b["sim"] and b["sim"] > .7) else 0 for b in beads]
    pref = [0]
    for g in good: pref.append(pref[-1] + g)
    def ctx(k, r=8): a, z = max(0, k - r), min(len(beads), k + r + 1); return (pref[z] - pref[a]) / (z - a)
    out = []
    for k, b in enumerate(beads):
        if not b["en"] or not b["pt"] or b["en_n"] > 2 or b["pt_n"] > 2: continue
        if not b["sim"] or b["sim"] < .5: 
            pass
        lr = (b["pt_w"] + 1) / (b["en_w"] + 1)
        if b["en_w"] < 6 or lr < .6 or lr > 1.7: continue
        c = ctx(k)
        if c < .5: continue
        en, pt = b["en"], b["pt"]; hits = []
        ne, npt = norm_nums(en), norm_nums(pt)
        se, sp = set(ne), set(npt)
        # ignore tiny footnote numbers: only values >= 10 or non-integers or percentages matter
        sig = lambda s: set(s)
        if sig(se) != sig(sp) and (sig(se) | sig(sp)):
            hits.append(("NUM", f"EN{sorted(sig(se) - sig(sp))} / PT{sorted(sig(sp) - sig(se))}"))
        ce = len(NEG_EN.findall(en)); cp = len(NEG_PT.findall(pt))
        if (ce >= 1 and cp == 0) or (cp >= 1 and ce == 0 and not re.search(r"\b(little|few|lack|absence|unable|impossible)", en, re.I)):
            hits.append(("NEG", f"EN neg={ce} PT neg={cp}"))
        for lab, pe, pp in QUANT:
            e1 = bool(re.search(pe, en, re.I)); p1 = bool(re.search(pp, pt, re.I))
            if e1 and not p1 and lab in ("only", "always", "never"): hits.append(("QUANT", f"EN has '{lab}', PT lacks it"))
            if p1 and not e1 and lab in ("only", "always", "never") and lab == "only" and re.search(r"\b(apenas|somente|unicamente|exclusivamente)\b", pt, re.I): hits.append(("QUANT", f"PT adds 'only' ({lab})"))
        he, hp = bool(HEDGE_EN.search(en)), bool(HEDGE_PT.search(pt))
        if he != hp: hits.append(("HEDGE", "EN hedge" if he else "PT adds hedge"))
        me, mp = bool(MOD_EN.search(en)), bool(MOD_PT.search(pt))
        if me != mp: hits.append(("MODAL", "EN intensifier/modal dropped" if me else "PT adds intensifier/modal"))
        if b["sim"] and b["sim"] < .55 and .75 <= lr <= 1.35 and b["en_w"] >= 8: hits.append(("SEM", f"sim={b['sim']:.2f}"))
        if hits: out.append(dict(k=k, hits=hits, sim=b["sim"], en=en, pt=pt, ctx=round(c, 2)))
    (wd / "distort.json").write_text(json.dumps(out, ensure_ascii=False))
    from collections import Counter
    cnt = Counter(h[0] for o in out for h in o["hits"])
    n11 = sum(1 for b in beads if b["en"] and b["pt"] and b["en_n"] <= 2 and b["pt_n"] <= 2)
    print(f"{name:24s} scanned beads={n11:5d} flagged={len(out):4d} {dict(cnt)}")
