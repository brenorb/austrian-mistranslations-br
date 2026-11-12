#!/usr/bin/env python3
"""Quotation audit for Brazilian ORIGINAL books: find passages in “…” (>=14 words) that quote an Austrian author whose
English text we hold, and compare each quote with its best English match (LaBSE).  -> results/quotes.json"""
import sys, json, re, pathlib, numpy as np
root = pathlib.Path(__file__).resolve().parent.parent; sys.path.insert(0, str(root / "scripts"))
from common import load_book, words
from sentence_transformers import SentenceTransformer
import torch
BR = ["a-economia-do-intervencionismo","historia-do-debate-do-calculo-economico-socialista","dez-licoes-fundamentais-de-economia-austriaca",
      "acao-tempo-e-conhecimento-a-escola-austriaca","economia-do-individuo-o-legado-da-escola-austriaca","economia-e-liberdade-a-escola-austriaca-e-a-economia-brasileira",
      "estado-nao-obrigado","bitcoin-a-moeda-na-era-digital","o-empreendedorismo-de-israel-kirzner","o-poder-das-ideias","ebook-de-natal"]
pairs = json.loads((root / "pairs.json").read_text())
EN_E, EN_T = [], []
for p in pairs:
    if p["lang"] != "en": continue
    wd = root / "work5" / p["name"]
    if not (wd / "src.npy").exists(): continue
    E = np.load(wd / "src.npy"); _, S = load_book(root / p["src"]); s = [x for x, _ in S]
    if len(s) != len(E): continue
    EN_E.append(E); EN_T += [(p["name"], x) for x in s]
EN_E = np.vstack(EN_E); print("EN sentences:", len(EN_T), flush=True)
model = SentenceTransformer("sentence-transformers/LaBSE", device="mps" if torch.backends.mps.is_available() else "cpu")
out = []
for slug in BR:
    f = root / "data/pt_raw" / f"{slug}.pdf"
    paras, _ = load_book(f); text = " ".join(paras)
    qs = [q.strip() for q in re.findall(r"[“\"]([^”\"]{80,700})[”\"]", text) if words(q) >= 14]
    if not qs: print(slug, 0); continue
    Q = model.encode(qs, batch_size=64, normalize_embeddings=True, show_progress_bar=False, convert_to_numpy=True).astype("float32")
    S = Q @ EN_E.T; j = S.argmax(1); sc = S.max(1)
    n_hit = 0
    for qi, (q, k, s) in enumerate(zip(qs, j, sc)):
        if s >= 0.72:
            n_hit += 1; out.append(dict(book=slug, sim=float(s), quote=q, src_book=EN_T[k][0], src=EN_T[k][1]))
    print(f"{slug:60s} quotes={len(qs):4d} matched>=0.72: {n_hit}", flush=True)
(root / "results/quotes.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
