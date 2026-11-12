#!/usr/bin/env python3
"""Download all free Portuguese PDFs listed at mises.org.br/livros (public ebooks)."""
import re, sys, json, urllib.request, urllib.parse, pathlib, time
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
def get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research script)"})
    d = urllib.request.urlopen(req, timeout=60).read()
    return d if binary else d.decode("utf-8", "replace")
idx = get("https://mises.org.br/livros/")
links = sorted(set(re.findall(r'href="(https://mises\.org\.br/livros/\d+/[^"]+/)"', idx)))
manifest = []
for l in links:
    slug = l.rstrip("/").split("/")[-1]
    try:
        html = get(l)
        pdfs = re.findall(r'href="([^"]+\.(?:pdf|epub))"', html, re.I)
        title = re.search(r"<title>([^<]*)</title>", html)
        rec = {"slug": slug, "page": l, "title": title.group(1) if title else slug, "files": pdfs}
        for u in pdfs:
            ext = u.rsplit(".",1)[-1].lower()
            dst = out / f"{slug}.{ext}"
            if not dst.exists():
                try:
                    dst.write_bytes(get(urllib.parse.quote(u, safe=":/%+"), True))
                except Exception as e:
                    rec.setdefault("errors", []).append(str(e))
            rec.setdefault("saved", []).append(dst.name)
        manifest.append(rec); print(slug, len(pdfs), rec.get("errors"), flush=True)
    except Exception as e:
        print("ERR", slug, e, flush=True)
(out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
