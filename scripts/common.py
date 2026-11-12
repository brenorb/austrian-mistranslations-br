"""Text extraction, cleaning and sentence splitting shared by the pipeline."""
import re, subprocess, collections, pathlib, unicodedata

ABBR = r"(?:Mr|Mrs|Ms|Dr|Prof|Sr|Sra|Dra|St|vs|etc|cf|Cf|pp?|cap|caps|vol|vols|ed|eds|no|nº|n|fig|Fig|op|ibid|Ibid|cit|ca|e\.g|i\.e|U\.S|U\.K|Jr|Co|Inc|Ltd|Gen|Sen|Rep|Hon|Rev|Mt|Fr|Ex|Art|art|Exmo|Ilmo|p\.ex|trad|org|apud|Lt|Col|Capt|Cia|Dec|Jan|Feb|Mar|Apr|Aug|Sept|Oct|Nov|ibidem|Ph|D|Dep)"
SENT_RE = re.compile(r"(?<=[.!?…”\"’)\]])\s+(?=[“\"‘'(\[¿¡A-ZÁÀÂÃÉÈÊÍÓÔÕÚÜÇÄÖÑ0-9])")

def pdf_pages(path):
    """Per-page text via PyMuPDF; drops small-font lines (footnotes, footnote marks) and header/footer bands."""
    import fitz
    doc = fitz.open(str(path)); pages = []
    for page in doc:
        d = page.get_text("dict"); H = page.rect.height
        lines = []
        for b in d["blocks"]:
            if b.get("type") != 0: continue
            blk = []
            for l in b["lines"]:
                spans = [sp for sp in l["spans"] if sp["text"].strip()]
                if not spans: continue
                n = sum(len(sp["text"]) for sp in spans)
                size = sum(sp["size"] * len(sp["text"]) for sp in spans) / n
                blk.append((l["bbox"][1], size, "".join(sp["text"] for sp in l["spans"]), n))
            if blk: lines.append(blk)
        allc = [(sz, n) for blk in lines for (_, sz, _, n) in blk]
        if not allc: pages.append(""); continue
        # char-weighted median font size = body size
        allc.sort(); tot = sum(n for _, n in allc); acc = 0; med = allc[0][0]
        for sz, n in allc:
            acc += n
            if acc >= tot / 2: med = sz; break
        out = []
        for blk in lines:
            keep = [t for (y, sz, t, n) in blk if sz >= 0.9 * med and not ((y < 0.07 * H or y > 0.93 * H) and len(t.split()) <= 10)]
            if keep: out.append("\n".join(keep))
        pages.append("\n\n".join(out))
    return pages

def clean_pages(pages):
    """Remove running headers/footers (lines repeated on many pages) and bare page numbers."""
    cnt = collections.Counter()
    for p in pages:
        for l in set(x.strip() for x in p.splitlines() if x.strip()):
            if len(l) < 90: cnt[l] += 1
    n = max(len(pages), 1)
    junk = {l for l, c in cnt.items() if c >= max(6, 0.04 * n) and not re.search(r"[a-z]{4}.*[.!?]$", l)}
    out = []
    for p in pages:
        keep = []
        for l in p.splitlines():
            s = l.strip()
            if not s:
                keep.append(""); continue
            if s in junk: continue
            if re.fullmatch(r"[\divxlcdmIVXLCDM.\-–— ]{1,12}", s): continue   # page numbers / roman
            if re.fullmatch(r"(?:\d{1,4}\s+)?[A-ZÁÀÂÃÉÊÍÓÔÕÚÇÜÄÖ0-9 ,.'’:;&\-–—()]{6,90}(?:\s+\d{1,4})?", s) and len(s.split()) <= 12: continue  # ALL-CAPS running heads
            keep.append(s)
        out.append("\n".join(keep))
    return out

def to_paragraph_text(pages):
    text = "\n\f\n".join(pages)
    SH = chr(173)
    text = re.sub(SH + r"[ \t]*\n[ \t]*", "", text); text = text.replace(SH, "")
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)             # de-hyphenate
    text = re.sub(r"[ \t]+", " ", text)
    paras = re.split(r"\n\s*\n", text)
    paras = [re.sub(r"\s*\n\s*", " ", p).strip() for p in paras]
    # re-join paragraphs broken by page/column breaks (previous doesn't end a sentence)
    merged = []
    for p in paras:
        if not p or p == "\f": continue
        if merged and not re.search(r"[.!?:”\"’)\]…]$", merged[-1]) and re.match(r"[a-zàáâãéêíóôõúç(“\"‘]", p):
            merged[-1] += " " + p
        else:
            merged.append(p)
    return merged

def split_sentences(paras):
    """Return list of (sentence, paragraph_index)."""
    out = []
    prot = re.compile(r"\b" + ABBR + r"\.\s", re.I)
    for pi, p in enumerate(paras):
        marked = prot.sub(lambda m: m.group(0).replace(". ", ".\u0001"), p)
        marked = re.sub(r"(\b[A-Z])\.\s(?=[A-Z])", lambda m: m.group(1) + ".\u0001", marked)  # initials
        for s in SENT_RE.split(marked):
            s = s.replace("\u0001", " ").strip()
            if len(s.split()) >= 2: out.append((s, pi))
    return out

def words(s): return len(re.findall(r"\w+", s, re.UNICODE))

def epub_paragraphs(path):
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
    book = epub.read_epub(str(path), options={"ignore_ncx": True})
    paras = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "html.parser")
        for t in soup.find_all(["p", "li", "blockquote"]):
            if t.find_parent(["p", "li", "blockquote"]) is not None and t.name == "p" and t.find_parent("blockquote") is None and t.find_parent(["p","li"]): continue
            cls = " ".join(t.get("class", [])).lower()
            x = re.sub(r"\s+", " ", t.get_text(" ")).strip()
            x = re.sub(r"\s+([.,;:!?)”’])", r"\1", x)
            if x: paras.append(x)
    return paras

def load_book(pdf_or_txt):
    p = pathlib.Path(pdf_or_txt)
    if p.suffix.lower() == ".epub":
        paras = epub_paragraphs(p); return paras, split_sentences(paras)
    if p.suffix.lower() == ".pdf":
        pages = clean_pages(pdf_pages(p))
    else:
        pages = [p.read_text(errors="replace")]
    paras = to_paragraph_text(pages)
    sents = split_sentences(paras)
    return paras, sents
