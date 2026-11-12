#!/usr/bin/env python3
"""Gera docs/data/*.json para o site: achados classificados (tipo, gravidade) com fonte em todos
(edição PT + página do PDF, edição EN + link + capítulo/página) e o painel de cobertura dos 52 livros."""
import sys, json, re, csv, pathlib, unicodedata, warnings
warnings.filterwarnings("ignore")
root = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "scripts"))
from site_curation import TYPES, FAMILIES, SEVERITY, CUR, BOOKS
import fitz

norm = lambda s: re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s).replace("­", "").replace("’", "'").replace("“", '"').replace("”", '"')).lower()
def clean_ctx(s):
    s = re.sub(r"(?:\b[A-Z] [A-Z]{2,}\b ?){2,}", " ", s)          # garble de versaletes: "T HE M ONETARY U NIT"
    s = re.sub(r"\s+", " ", s).strip()
    return s

# ---------- índices de página dos PDFs/EPUBs ----------
pairs = {p["name"]: p for p in json.loads((root / "pairs.json").read_text())}
_pdf_cache, _epub_cache = {}, {}
def pdf_pages(path):
    if path not in _pdf_cache:
        d = fitz.open(str(path)); out = []
        for pg in d:
            t = pg.get_text().replace("-\n", "").replace("\n", " ")
            out.append(norm(t))
        _pdf_cache[path] = out
    return _pdf_cache[path]
def find_pdf_page(path, text):
    words = norm(text).split()
    pages = pdf_pages(path)
    for n in (7, 5, 4):
        for i in range(0, max(1, len(words) - n + 1), max(1, n // 2)):
            w = " ".join(words[i:i + n])
            if len(w) < 18: continue
            hits = [pi for pi, t in enumerate(pages) if w in t]
            if hits: return hits[0] + 1
    return None
def fix_caps(t):
    t = re.sub(r"\b([A-Z]) ([A-Z]{2,})\b", r"\1\2", t)                      # "C HAPTER T WO" -> "CHAPTER TWO"
    t = re.sub(r"\b(CHAPTER|CHARTER)\s+([A-Z]+)\b", lambda m: "Chapter " + m.group(2).capitalize(), t)
    return re.sub(r"\s+", " ", t).strip()
def epub_docs(path):
    if path not in _epub_cache:
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup
        bk = epub.read_epub(str(path), options={"ignore_ncx": True}); toc = {}
        def walk(items):
            for it in items:
                if isinstance(it, tuple): walk([it[0]] + list(it[1]))
                elif hasattr(it, "href"): toc.setdefault(it.href.split("#")[0].split("/")[-1], it.title)
        walk(bk.toc)
        docs = []
        for it in bk.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(it.get_content(), "html.parser"); name = it.get_name().split("/")[-1]
            h = soup.find(["h1", "h2", "h3"]); title = toc.get(name) or (re.sub(r"\s+", " ", h.get_text(" ")).strip() if h else "")
            m = re.search(r"chapter\s*0*(\d+)", name, re.I)
            if not title and m: title = f"Capítulo {m.group(1)}"
            title = fix_caps(title or name)
            if title.isdigit(): title = f"Capítulo {title}"
            docs.append((title, norm(soup.get_text(" "))))
        _epub_cache[path] = docs
    return _epub_cache[path]
SKIP = re.compile(r"^(contents|table of contents|index|copyright|cover|title page)$|toc\.html|\.x?html$", re.I)
def find_epub_chapter(path, text):
    words = norm(text).split(); docs = epub_docs(path)
    for n in (8, 6, 4):
        for i in range(0, max(1, len(words) - n + 1), max(1, n // 2)):
            w = " ".join(words[i:i + n])
            if len(w) < 14: continue
            for title, t in docs:
                if SKIP.match(title): continue
                if w in t: return title
    return None

findings_in = json.loads((root / "findings.json").read_text())
out = []
for idx, f in enumerate(findings_in):
    cur = CUR[idx]; book = f["book"]; B = BOOKS[book]; pair = pairs[book]
    fam, tlabel, tdesc = TYPES[f["category"]]
    en, pt = clean_ctx(f["en"] or ""), clean_ctx(f["pt"] or "")
    def trim_tail(text, marks):
        """remove fragmento final sem pontuação (ex.: título de seção colado pelo PDF) depois do último destaque"""
        ends = [text.find(m) + len(m) for m in marks if text.find(m) >= 0]
        if not ends: return text
        e = max(ends); tail = text[e:]
        if tail.strip() and len(tail.split()) <= 4 and not re.search(r"[.!?]", tail): return text[:e]
        return text
    pt, en = trim_tail(pt, cur["pt_mark"]), trim_tail(en, cur["en_mark"])
    # fonte PT: página do PDF
    pt_key = cur["pt_mark"][0] if cur["pt_mark"] else pt
    pt_pdf = root / pair["pt"]
    page = find_pdf_page(pt_pdf, pt_key) or find_pdf_page(pt_pdf, pt)
    # fonte EN: capítulo (EPUB) ou página (PDF)
    en_key = cur["en_mark"][0] if cur["en_mark"] else en
    en_path = root / pair["src"]; en_loc = None; en_page = None
    if en_path.suffix == ".epub":
        en_loc = find_epub_chapter(en_path, en_key) or (find_epub_chapter(en_path, en) if en else None)
        if not en_loc and f.get("bead") is not None:      # acréscimos: usa as frases do original vizinhas
            bds = json.loads((root / "work5" / book / "beads.json").read_text())
            for j in range(f["bead"] - 1, max(0, f["bead"] - 25), -1):
                if bds[j]["en"] and len(bds[j]["en"].split()) > 8:
                    en_loc = find_epub_chapter(en_path, bds[j]["en"])
                    if en_loc: break
    else:
        en_page = find_pdf_page(en_path, en_key) or (find_pdf_page(en_path, en) if en else None)
    manifest = {r["slug"]: r for r in json.loads((root / "data/pt_raw/manifest.json").read_text())}
    mr = manifest[B["pt_slug"]]
    # excertos com destaque: avisar se algum destaque não está no texto
    for m in cur["pt_mark"]:
        if m not in pt: print(f"[aviso] #{idx} destaque PT ausente:", m[:60])
    for m in cur["en_mark"]:
        if m not in en: print(f"[aviso] #{idx} destaque EN ausente:", m[:60])
    out.append(dict(
        id=f"a{idx+1:02d}", titulo=cur["titulo"], nota=cur["nota"], ressalva=cur.get("ressalva"),
        familia=fam, familia_rotulo=FAMILIES[fam]["rotulo"], tipo=f["category"], tipo_rotulo=tlabel, tipo_desc=tdesc,
        gravidade=f["severity"], gravidade_rotulo=SEVERITY[f["severity"]],
        livro_chave=book, livro=B["pt_titulo"], autor=B["autor"], livro_en=B["en_titulo"],
        en=en, pt=pt, en_mark=cur["en_mark"], pt_mark=cur["pt_mark"],
        fonte=dict(
            pt=dict(titulo=B["pt_titulo"], edicao=B["pt_ed"], tradutor=B["pt_trad"], pagina_pdf=page,
                    pagina_url=mr["page"], pdf_url=mr["files"][0] if mr.get("files") else None),
            en=dict(titulo=B["en_titulo"], edicao=B["en_ed"], url=B["en_url"], capitulo=en_loc, pagina_pdf=en_page)),
    ))
    print(f"{out[-1]['id']} {book:16s} sev{f['severity']} {tlabel:26s} PT p.{page} | EN {en_loc or en_page}")

# ---------- cobertura ----------
cov = list(csv.DictReader(open(root / "results/corpus_coverage.csv")))
man = {r["slug"]: r for r in json.loads((root / "data/pt_raw/manifest.json").read_text())}
rev = {}
for p in pairs.values(): rev.setdefault(p["pt"].split("/")[-1][:-4], []).append(p["name"])
STATUS_PT = {"ALIGNED_AND_SCANNED": "Comparado com a fonte", "BR_ORIGINAL": "Original brasileiro (sem fonte)", "BR_ANTHOLOGY": "Coletânea brasileira",
             "SOURCE_NOT_FREE": "Fonte sem versão gratuita", "SOURCE_NOT_FOUND": "Fonte não localizada", "ES_ORIGINAL_EU_PT": "Português de Portugal (fora do escopo)", "NO_PDF": "Sem arquivo no Mises Brasil"}
def short_title(t): return re.sub(r"\s*[-–—|].*$", "", t or "").strip()
summ = {r["book"]: r for r in csv.DictReader(open(root / "results/summary.csv"))}
nfind = {}
for a in out: nfind[a["livro_chave"]] = nfind.get(a["livro_chave"], 0) + 1
PT_EVID = {
 "a-economia-do-intervencionismo": "Fabio Barbieri (Mises Brasil, 2013): original em português.",
 "historia-do-debate-do-calculo-economico-socialista": "Fabio Barbieri: original em português.",
 "dez-licoes-fundamentais-de-economia-austriaca": "Ubiratan Jorge Iorio: original em português.",
 "acao-tempo-e-conhecimento-a-escola-austriaca": "Ubiratan Jorge Iorio: original em português.",
 "economia-do-individuo-o-legado-da-escola-austriaca": "Rodrigo Constantino (2009): original em português.",
 "economia-e-liberdade-a-escola-austriaca-e-a-economia-brasileira": "Coletivo brasileiro: original em português.",
 "estado-nao-obrigado": "Marcello Mazzilli: original em português.",
 "bitcoin-a-moeda-na-era-digital": "Fernando Ulrich (2014): original em português.",
 "o-empreendedorismo-de-israel-kirzner": "Adriano Gianturco (2014): escrito para o Mises Brasil, sem original para comparar.",
 "o-poder-das-ideias": "Coletânea do Fórum da Liberdade, autores brasileiros.",
 "ebook-de-natal": "Compilação de artigos do Mises Brasil.",
 "o-centenario-de-uma-lenda": "Listado no site do Mises Brasil, sem arquivo.",
 "a-desconsideracao-da-personalidade-juridica-na-justica-do-trabalho": "Obra de direito do trabalho, sem arquivo no site.",
 "ciclos-fatais-socialismo-e-direitos-humanos": "Sem arquivo no site do Mises Brasil.",
 "a-etica-da-redistribuicao": "Jouvenel; a Liberty Fund vende o livro, sem arquivo gratuito encontrado.",
 "competicao-e-atividade-empresarial": "Kirzner; a página do Mises.org só oferece compra.",
 "desemprego-e-politica-monetaria": "Hayek (Cato, 1979); sem arquivo gratuito encontrado.",
 "definindo-a-liberdade": "Ron Paul, Liberty Defined; edição comercial, sem arquivo gratuito.",
 "alem-da-democracia": "Karsten e Beckman; só o primeiro capítulo é gratuito oficialmente.",
 "frederic-bastiat": "Dean Russell (FEE); sem arquivo gratuito encontrado.",
 "uma-futura-ordem-monetaria-mundial": "Volume do CME (2025); original em inglês não localizado.",
 "a-escola-austriaca": "Huerta de Soto, tradução em português de Portugal; fora do escopo do Brasil.",
}
books = []
for r in cov:
    m = man.get(r["slug"], {})
    names = rev.get(r["slug"], [])
    if names: ev = "Comparado com o original: " + "; ".join(sorted({pairs[n]["title"].split(" / ")[0] for n in names}))
    else: ev = PT_EVID.get(r["slug"], "")
    title = short_title(m.get("title")) or r["slug"].replace("-", " ").capitalize()
    title = re.sub(r"\b(De|Do|Da|Dos|Das|Com|O|A|Os|As|E|Em|Para|Por|Um|Uma|Sob|No|Na)\b", lambda x: x.group(1).lower(), title)
    title = title[0].upper() + title[1:]
    title = {"frederic-bastiat": "Frédéric Bastiat (Dean Russell)"}.get(r["slug"], title)
    books.append(dict(slug=r["slug"], titulo=title, palavras=int(r["pt_words"]),
                      status=r["status"], status_rotulo=STATUS_PT.get(r["status"], r["status"]), evidencia=ev,
                      pagina_url=m.get("page"), achados=sum(nfind.get(n, 0) for n in names)))
books.sort(key=lambda b: (b["status"] != "ALIGNED_AND_SCANNED", -b["achados"], b["titulo"]))
tot = sum(b["palavras"] for b in books); cmp_ = sum(b["palavras"] for b in books if b["status"] == "ALIGNED_AND_SCANNED")
meta = dict(gerado="2026-11-12", achados=len(out), livros=len(books), livros_comparados=sum(1 for b in books if b["status"] == "ALIGNED_AND_SCANNED"),
            palavras_total=tot, palavras_comparadas=cmp_,
            tipos={k: dict(familia=v[0], rotulo=v[1], desc=v[2]) for k, v in TYPES.items()}, familias=FAMILIES, gravidade={str(k): v for k, v in SEVERITY.items()})
d = root / "docs/data"; d.mkdir(parents=True, exist_ok=True)
(d / "achados.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
(d / "livros.json").write_text(json.dumps(books, ensure_ascii=False, indent=1))
(d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
print(len(out), "achados;", meta["livros_comparados"], "/", meta["livros"], "livros comparados")
