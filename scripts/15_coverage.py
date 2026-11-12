#!/usr/bin/env python3
"""Coverage table for ALL 52 Portuguese books: how each was processed. -> results/corpus_coverage.csv/.md"""
import json, csv, pathlib, re
root = pathlib.Path(__file__).resolve().parent.parent
pairs = {p["pt"].split("/")[-1][:-4]: p["name"] for p in json.loads((root / "pairs.json").read_text())}
ALIGN = {}
for k, v in pairs.items(): ALIGN.setdefault(k, []).append(v)
STATUS = {
 "a-economia-do-intervencionismo": ("BR_ORIGINAL", "Fabio Barbieri, Mises Brasil 2013; no source text exists"),
 "historia-do-debate-do-calculo-economico-socialista": ("BR_ORIGINAL", "Fabio Barbieri; no source text exists"),
 "dez-licoes-fundamentais-de-economia-austriaca": ("BR_ORIGINAL", "Ubiratan Jorge Iorio; no source text exists"),
 "acao-tempo-e-conhecimento-a-escola-austriaca": ("BR_ORIGINAL", "Ubiratan Jorge Iorio; no source text exists"),
 "economia-do-individuo-o-legado-da-escola-austriaca": ("BR_ORIGINAL", "Rodrigo Constantino 2009; no source text exists"),
 "economia-e-liberdade-a-escola-austriaca-e-a-economia-brasileira": ("BR_ORIGINAL", "Brazilian collective; no source"),
 "estado-nao-obrigado": ("BR_ORIGINAL", "Marcello Mazzilli; no source"),
 "bitcoin-a-moeda-na-era-digital": ("BR_ORIGINAL", "Fernando Ulrich 2014; no source"),
 "o-empreendedorismo-de-israel-kirzner": ("BR_ORIGINAL", "Adriano Gianturco 2014 (written for Mises Brasil); no source found"),
 "o-poder-das-ideias": ("BR_ANTHOLOGY", "Forum da Liberdade collection of essays by Brazilian authors"),
 "ebook-de-natal": ("BR_ANTHOLOGY", "Mises Brasil articles compilation"),
 "o-centenario-de-uma-lenda": ("NO_PDF", "listed at mises.org.br but no file offered"),
 "a-desconsideracao-da-personalidade-juridica-na-justica-do-trabalho": ("NO_PDF", "Brazilian labour-law work; no file offered"),
 "ciclos-fatais-socialismo-e-direitos-humanos": ("NO_PDF", "no file offered at mises.org.br"),
 "a-etica-da-redistribuicao": ("SOURCE_NOT_FREE", "de Jouvenel; Liberty Fund sells it, no free file found"),
 "competicao-e-atividade-empresarial": ("SOURCE_NOT_FREE", "Kirzner; Mises.org book page offers no file"),
 "desemprego-e-politica-monetaria": ("SOURCE_NOT_FREE", "Hayek (Cato/IEA 1979); no free file found"),
 "definindo-a-liberdade": ("SOURCE_NOT_FREE", "Ron Paul, Liberty Defined (Grand Central); commercial, no free file"),
 "alem-da-democracia": ("SOURCE_NOT_FREE", "Karsten & Beckman; only first chapter free officially"),
 "frederic-bastiat": ("SOURCE_NOT_FREE", "Dean Russell (FEE); not on Mises.org as a file"),
 "uma-futura-ordem-monetaria-mundial": ("SOURCE_NOT_FOUND", "2025 CME debate volume; English file not located"),
 "a-escola-austriaca": ("ES_ORIGINAL_EU_PT", "Huerta de Soto, European-Portuguese translation (Portugal); out of scope for Brazilian PT; Spanish original not aligned"),
}
rows = []
for f in sorted((root / "data/pt_raw").glob("*.pdf")):
    slug = f.stem
    words = len(re.findall(r"\w+", (root / "data/pt_txt" / f"{slug}.txt").read_text(errors="replace"))) if (root / "data/pt_txt" / f"{slug}.txt").exists() else 0
    if slug in ALIGN: st, ev = "ALIGNED_AND_SCANNED", "aligned with source: " + ", ".join(ALIGN[slug])
    elif slug in STATUS: st, ev = STATUS[slug]
    else: st, ev = "UNCLASSIFIED", ""
    rows.append(dict(slug=slug, pt_words=words, status=st, evidence=ev))
for slug in ("a-desconsideracao-da-personalidade-juridica-na-justica-do-trabalho", "ciclos-fatais-socialismo-e-direitos-humanos", "o-centenario-de-uma-lenda"):
    if not any(r["slug"] == slug for r in rows): rows.append(dict(slug=slug, pt_words=0, status=STATUS[slug][0], evidence=STATUS[slug][1]))
with open(root / "results/corpus_coverage.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
from collections import Counter
c = Counter(r["status"] for r in rows); w = Counter()
for r in rows: w[r["status"]] += r["pt_words"]
print(len(rows), "books"); [print(f"{k:22s} {c[k]:3d} books {w[k]:>9,} words") for k in c]
print([r["slug"] for r in rows if r["status"] == "UNCLASSIFIED"])
