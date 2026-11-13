# austrian-mistranslations-br

Site estático para explorar problemas de tradução em livros da Escola Austríaca publicados em português do Brasil
(edições gratuitas do Mises Brasil comparadas com os originais do Mises Institute). Cada achado tem **tipo**, **gravidade**
e **fonte** (edição, página/capítulo e link nos dois idiomas).

* **Site (GitHub Pages):** https://brenorb.github.io/austrian-mistranslations-br/  (publicado a partir de `docs/`)
* **Relatório completo:** [REPORT.md](REPORT.md) · **Dados:** `docs/data/*.json`, `findings.json`, `results/`
* **Rodar o site localmente:** `cd docs && python3 -m http.server 8000` e abrir http://localhost:8000
* **Regenerar os dados do site:** `.venv/bin/python scripts/17_build_site_data.py` (curadoria em `scripts/site_curation.py`)

> Os livros baixados (`data/`) e os artefatos de alinhamento (`work5/`) não estão no repositório. Excertos curtos são reproduzidos
> para análise e crítica; os livros completos estão nos links de cada achado.

---

# mistranslations-austrians

Sentence-level audit of Brazilian-Portuguese translations of Austrian-school books against their English
(and where possible German/Spanish) sources, prompted by
[J. P. Mayall's tweet](https://x.com/jpmayall/status/1990067165093855457) about a 26-word Rothbard sentence that
became 62 words in Portuguese.

**Start with [REPORT.md](REPORT.md).** Machine-readable results: `results/summary.csv`, `findings.json`,
`results/findings.md`.

## Layout
| Path | What |
|---|---|
| `REPORT.md` | findings, method, limits |
| `pairs.json` | the source ↔ PT book pairs analysed |
| `scripts/01_fetch_pt.py` | downloads all PDFs listed at mises.org.br/livros |
| `scripts/02,03,07_*` | Mises.org catalogue crawl (rate-limited: Cloudflare 429s if hit fast) and source downloads |
| `scripts/common.py` | text extraction (PyMuPDF font-size filter for footnotes; EPUB) and sentence splitting |
| `scripts/04_align.py` | LaBSE embeddings, anchor + banded DP sentence alignment |
| `scripts/05_flag.py` | additions / omissions / expansion flags with artifact filters |
| `scripts/06_run_pairs.py` | runs 04+05 for every pair → `work5/<pair>/` |
| `scripts/08_sheet.py`, `09_show.py`, `10_verify.py` | review helpers (compact sheets, full beads, global match search) |
| `scripts/11_lexicon.py` | concept-injection detector (store of value, fiat, electronic…) |
| `scripts/14_distort.py` | second pass: numbers / negation / quantifier / semantic-divergence detectors on every aligned sentence |
| `scripts/16_quotes.py` | quotation audit for Brazilian originals (quotes vs. English texts held) |
| `scripts/12_summary.py`, `13_findings.py`, `15_coverage.py` | summary table, curated findings (37), coverage of all 52 books (`results/corpus_coverage.csv`) |
| `data/` (git-ignored) | downloaded PDFs/EPUBs and text; `data/tweet/` has the tweet images |
| `work5/` (git-ignored) | embeddings, beads.json, flags.json per pair; `work_old/` = superseded runs |

## Reproduce
```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python sentence-transformers numpy rapidfuzz pymupdf ebooklib beautifulsoup4
python3 -I scripts/01_fetch_pt.py data/pt_raw
# source files: see scripts/07_download_en.py (needs data/en_pages.json from 03_fetch_en_pages.py)
.venv/bin/python scripts/06_run_pairs.py        # all pairs
.venv/bin/python scripts/12_summary.py && .venv/bin/python scripts/13_findings.py
BYSCORE=1 .venv/bin/python scripts/08_sheet.py work5/whgd ADDITION,EXPANSION 20 0.5 0 30
```
Note: mises.org returns 403/429 to default Python clients and to fast crawlers; use `curl` and ≥12 s spacing. File
downloads from `cdn.mises.org` are not rate-limited.
