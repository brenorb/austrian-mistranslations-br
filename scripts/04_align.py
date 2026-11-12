#!/usr/bin/env python3
"""Align a source-language book with its Brazilian-Portuguese translation at sentence level (LaBSE embeddings,
anchor + banded DP, Vecalign-style) and flag suspicious beads: additions, omissions, expansion, low similarity.

usage: 04_align.py SRC_FILE PT_FILE OUT_DIR [--lang en|de|es]
"""
import sys, json, pathlib, bisect, re, numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import load_book, words

def embed(model, sents, cache):
    if cache.exists(): return np.load(cache)
    E = model.encode(sents, batch_size=64, normalize_embeddings=True, show_progress_bar=False, convert_to_numpy=True).astype("float32")
    np.save(cache, E); return E

def anchors(E1, E2, thr=0.72):
    n, m = len(E1), len(E2)
    best_j = np.zeros(n, int); best_s = np.zeros(n, "float32")
    colbest = np.full(m, -1.0, "float32"); colarg = np.zeros(m, int)
    B = 2000
    for a in range(0, n, B):
        S = E1[a:a+B] @ E2.T
        best_j[a:a+B] = S.argmax(1); best_s[a:a+B] = S.max(1)
        cm = S.max(0); ca = S.argmax(0) + a
        upd = cm > colbest; colbest[upd] = cm[upd]; colarg[upd] = ca[upd]
    pairs = [(i, int(best_j[i]), float(best_s[i])) for i in range(n) if best_s[i] >= thr and colarg[best_j[i]] == i]
    # longest increasing subsequence on j (weighted by sim via tie-break) - standard patience LIS
    tails, tails_idx, prev = [], [], [-1] * len(pairs)
    for k, (i, j, s) in enumerate(pairs):
        pos = bisect.bisect_left(tails, j)
        if pos == len(tails): tails.append(j); tails_idx.append(k)
        else: tails[pos] = j; tails_idx[pos] = k
        prev[k] = tails_idx[pos - 1] if pos > 0 else -1
    k = tails_idx[-1] if tails_idx else -1; chain = []
    while k >= 0: chain.append(pairs[k]); k = prev[k]
    return chain[::-1]

BEADS = [(1,1),(1,0),(0,1),(1,2),(2,1),(2,2),(1,3),(3,1),(0,2),(2,0),(3,3),(2,3),(3,2)]
SKIP_COST = 0.62

def align_gap(P1, P2, L1, L2, i0, i1, j0, j1):
    """Align EN sents [i0,i1) with PT sents [j0,j1). Returns list of (i_a,i_b,j_a,j_b)."""
    ni, nj = i1 - i0, j1 - j0
    if ni == 0 and nj == 0: return []
    if ni == 0: return [(i0, i0, j, j + 1) for j in range(j0, j1)]
    if nj == 0: return [(i, i + 1, j0, j0) for i in range(i0, i1)]
    band = max(30, int(0.2 * max(ni, nj)))
    INF = 1e9
    cost = {}; back = {}
    cost[(0, 0)] = 0.0
    def cosd(a, b, c, d):
        v1 = P1[b] - P1[a]; v2 = P2[d] - P2[c]
        n1 = np.linalg.norm(v1); n2 = np.linalg.norm(v2)
        if n1 == 0 or n2 == 0: return 1.0
        return 1.0 - float(v1 @ v2) / (n1 * n2)
    for i in range(ni + 1):
        centre = i * nj / max(ni, 1)
        lo = max(0, int(centre - band)); hi = min(nj, int(centre + band))
        for j in range(lo, hi + 1):
            c0 = cost.get((i, j))
            if c0 is None: continue
            for di, dj in BEADS:
                a, b = i + di, j + dj
                if a > ni or b > nj: continue
                if di == 0 or dj == 0:
                    w = L1[i0 + i:i0 + a].sum() + L2[j0 + j:j0 + b].sum()
                    c = c0 + SKIP_COST * (di + dj)
                else:
                    lr = (L2[j0 + j:j0 + b].sum() + 1) / (L1[i0 + i:i0 + a].sum() + 1)
                    c = c0 + cosd(i0 + i, i0 + a, j0 + j, j0 + b) * (di + dj) / 2 * 2 + 0.1 * abs(np.log(lr / 1.12)) * 0.5 + 0.03 * (di + dj - 2)
                if c < cost.get((a, b), INF):
                    cost[(a, b)] = c; back[(a, b)] = (i, j, di, dj)
    if (ni, nj) not in cost:   # band failure: fall back to unaligned
        return [(i0, i1, j0, j1)]
    out = []; cur = (ni, nj)
    while cur != (0, 0):
        i, j, di, dj = back[cur]; out.append((i0 + i, i0 + i + di, j0 + j, j0 + j + dj)); cur = (i, j)
    return out[::-1]

def main():
    src, pt, outdir = sys.argv[1:4]
    lang = "en"
    if "--lang" in sys.argv: lang = sys.argv[sys.argv.index("--lang") + 1]
    outdir = pathlib.Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    from sentence_transformers import SentenceTransformer
    import torch
    model = SentenceTransformer("sentence-transformers/LaBSE", device="mps" if torch.backends.mps.is_available() else "cpu")
    _, S1 = load_book(src); _, S2 = load_book(pt)
    s1 = [x for x, _ in S1]; s2 = [x for x, _ in S2]
    print(f"{src}: {len(s1)} sents; {pt}: {len(s2)} sents", flush=True)
    E1 = embed(model, s1, outdir / "src.npy"); E2 = embed(model, s2, outdir / "pt.npy")
    P1 = np.vstack([np.zeros((1, E1.shape[1]), "float32"), np.cumsum(E1, 0)])
    P2 = np.vstack([np.zeros((1, E2.shape[1]), "float32"), np.cumsum(E2, 0)])
    L1 = np.array([words(s) for s in s1]); L2 = np.array([words(s) for s in s2])
    chain = anchors(E1, E2)
    print("anchors", len(chain), flush=True)
    beads = []; pi = pj = 0
    for (i, j, s) in chain + [(len(s1), len(s2), 1.0)]:
        beads += align_gap(P1, P2, L1, L2, pi, i, pj, j)
        if i < len(s1): beads.append((i, i + 1, j, j + 1))
        pi, pj = i + 1, j + 1
    # score beads
    rows = []
    for (a, b, c, d) in beads:
        en = " ".join(s1[a:b]); pts = " ".join(s2[c:d])
        v1 = E1[a:b].mean(0) if b > a else None; v2 = E2[c:d].mean(0) if d > c else None
        sim = float(v1 @ v2 / (np.linalg.norm(v1) * np.linalg.norm(v2))) if v1 is not None and v2 is not None else None
        rows.append(dict(a=a, b=b, c=c, d=d, en_w=int(L1[a:b].sum()), pt_w=int(L2[c:d].sum()), sim=sim,
                         en_n=b - a, pt_n=d - c, en=en, pt=pts))
    (outdir / "beads.json").write_text(json.dumps(rows, ensure_ascii=False))
    print("beads", len(rows), "total EN words", int(L1.sum()), "PT words", int(L2.sum()), flush=True)

if __name__ == "__main__": main()
