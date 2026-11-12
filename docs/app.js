/* Austrian Mistranslations BR — site estático, sem dependências. */
const $ = (s, r = document) => r.querySelector(s);
const el = (tag, attrs = {}, ...kids) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") n.className = v; else if (k === "html") n.innerHTML = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v); else if (v !== false && v != null) n.setAttribute(k, v === true ? "" : v);
  }
  for (const k of kids.flat()) { if (k == null || k === false) continue; n.append(k instanceof Node ? k : document.createTextNode(k)); }
  return n;
};
const esc = s => s.replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const dot = s => s + (/[.?!]$/.test(s) ? "" : ".");
const fmt = n => n.toLocaleString("pt-BR");
const norm = s => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const SEV_COLOR = g => `var(--s${g})`;
const REPO = "https://github.com/brenorb/austrian-mistranslations-br";

let DATA = [], BOOKS = [], META = {};
const state = { q: "", grav: new Set(), fam: new Set(), tipo: new Set(), livro: new Set(), sort: "grav" };

/* ---------- carga ---------- */
Promise.all(["data/achados.json", "data/livros.json", "data/meta.json"].map(u => fetch(u).then(r => r.json())))
  .then(([a, l, m]) => { DATA = a; BOOKS = l; META = m; init(); })
  .catch(e => { $("#list").replaceChildren(el("li", { class: "empty" }, "Não foi possível carregar os dados. Se abriu o arquivo direto do disco, sirva a pasta docs/ por HTTP (python3 -m http.server).")); console.error(e); });

function init() {
  $("#repo").href = REPO;
  $("#gerado").textContent = `Dados gerados em ${META.gerado.split("-").reverse().join("/")}.`;
  renderStats(); renderCase(); readHash(); renderFilters(); renderCoverage(); bind(); update();
  if (location.hash.startsWith("#a")) { const t = document.getElementById(location.hash.slice(1)); if (t) setTimeout(() => t.scrollIntoView({ block: "center" }), 50); }
}

/* ---------- topo ---------- */
function renderStats() {
  const grav45 = DATA.filter(a => a.gravidade >= 4).length;
  const pct = Math.round(100 * META.palavras_comparadas / META.palavras_total);
  const items = [[DATA.length, "achados verificados"], [grav45, "graves ou grotescos"], [`${META.livros_comparados}/${META.livros}`, "livros comparados"], [`${pct}%`, "das palavras cobertas"]];
  $("#stats").replaceChildren(...items.map(([n, l]) => el("div", { class: "stat" }, el("dd", {}, String(n)), el("dt", {}, l))));
}
function renderCase() {
  const a = DATA.find(x => x.id === "a01"); if (!a) return;
  $("#case").replaceChildren(
    el("figcaption", {}, "O caso que originou este projeto: ", el("a", { href: "https://x.com/jpmayall/status/1990067165093855457", rel: "noopener" }, "tweet de J. P. Mayall"), " · Rothbard, ", a.livro),
    el("div", { class: "cols" },
      el("div", {}, el("h5", {}, "Original · 26 palavras"), el("blockquote", { html: markup("It is important to realize that money cannot be an abstract unit of account or claim, except insofar as it serves as a medium of exchange.", ["cannot be an abstract unit of account or claim"], "orig") })),
      el("div", {}, el("h5", {}, "Tradução · 62 palavras"), el("blockquote", { html: markup("É importante entender que o dinheiro só pode ser visto como uma unidade de conta ou como um título de reivindicação sobre bens a partir do momento em que ele passa a servir como um meio de troca. É de sua função como meio de troca que derivam todas as suas outras características, como ser unidade de conta e reserva de valor.", a.pt_mark, "tr") }))),
    el("a", { class: "btn primary", href: "#a01", onclick: () => focusCard("a01") }, "Ver achado completo e fontes"));
}

/* ---------- destaque ---------- */
function markup(text, marks, cls) {
  const ranges = [];
  for (const m of marks || []) { const i = text.indexOf(m); if (i >= 0) ranges.push([i, i + m.length]); }
  ranges.sort((a, b) => a[0] - b[0]);
  const merged = [];
  for (const r of ranges) { const l = merged[merged.length - 1]; if (l && r[0] <= l[1]) l[1] = Math.max(l[1], r[1]); else merged.push(r.slice()); }
  let out = "", p = 0;
  for (const [s, e] of merged) { out += esc(text.slice(p, s)) + `<mark class="${cls}">${esc(text.slice(s, e))}</mark>`; p = e; }
  return out + esc(text.slice(p));
}
function windowed(text, marks, max = 520) {
  if (text.length <= max) return { text, cut: false };
  let c = 0; for (const m of marks || []) { const i = text.indexOf(m); if (i >= 0) { c = i + m.length / 2; break; } }
  let s = Math.max(0, Math.round(c - max / 2)), e = Math.min(text.length, s + max); s = Math.max(0, e - max);
  const sp = text.indexOf(" ", s); if (s > 0 && sp > 0 && sp < s + 40) s = sp + 1;
  const ep = text.lastIndexOf(" ", e); if (e < text.length && ep > e - 40) e = ep;
  return { text: (s > 0 ? "… " : "") + text.slice(s, e) + (e < text.length ? " …" : ""), cut: true };
}

/* ---------- filtros ---------- */
function counts(filterFn) { const c = {}; for (const a of DATA) if (filterFn(a)) { for (const k of ["gravidade", "familia", "tipo", "livro_chave"]) { const key = k + ":" + a[k]; c[key] = (c[key] || 0) + 1; } } return c; }
function renderFilters() {
  const g = $("#f-grav"); g.replaceChildren();
  for (let n = 5; n >= 1; n--) g.append(chip(`${n} · ${META.gravidade[n]}`, "g" + n, () => toggle(state.grav, n), { dot: SEV_COLOR(n), count: DATA.filter(a => a.gravidade === n).length, pressed: () => state.grav.has(n) }));
  const t = $("#f-tipo"); t.replaceChildren();
  for (const [fk, fv] of Object.entries(META.familias)) {
    const types = Object.entries(META.tipos).filter(([, v]) => v.familia === fk).filter(([k]) => DATA.some(a => a.tipo === k));
    const box = el("div", { class: "fam" }, el("p", { class: "fam-title" }, fv.rotulo), el("div", { class: "chips" },
      chip("Toda a família", "f" + fk, () => toggle(state.fam, fk), { count: DATA.filter(a => a.familia === fk).length, pressed: () => state.fam.has(fk), strong: true }),
      ...types.map(([k, v]) => chip(v.rotulo, "t" + k, () => toggle(state.tipo, k), { count: DATA.filter(a => a.tipo === k).length, pressed: () => state.tipo.has(k), title: v.desc }))));
    t.append(box);
  }
  const l = $("#f-livro"); l.replaceChildren();
  const byBook = {}; for (const a of DATA) byBook[a.livro_chave] = a;
  Object.entries(byBook).sort((x, y) => DATA.filter(a => a.livro_chave === y[0]).length - DATA.filter(a => a.livro_chave === x[0]).length)
    .forEach(([k, a]) => l.append(chip(a.livro, "l" + k, () => toggle(state.livro, k), { count: DATA.filter(x => x.livro_chave === k).length, pressed: () => state.livro.has(k) })));
  renderMatrix();
}
function chip(label, id, onclick, o = {}) {
  const b = el("button", { type: "button", class: "chip", "data-id": id, "aria-pressed": "false", title: o.title || false, onclick },
    o.dot ? el("span", { class: "dot", style: `background:${o.dot}` }) : null, el("span", {}, label), el("span", { class: "n" }, String(o.count ?? "")));
  b._pressed = o.pressed; return b;
}
function renderMatrix() {
  const m = $("#matrix"); m.replaceChildren(el("span", {}));
  for (let g = 1; g <= 5; g++) m.append(el("span", { class: "h", title: META.gravidade[g] }, String(g)));
  for (const [fk, fv] of Object.entries(META.familias)) {
    m.append(el("span", { class: "rl" }, fv.rotulo));
    for (let g = 1; g <= 5; g++) {
      const n = DATA.filter(a => a.familia === fk && a.gravidade === g).length;
      const c = el("button", { type: "button", class: "cell", "data-n": n, "data-fam": fk, "data-g": g, "aria-pressed": "false", "aria-label": `${fv.rotulo}, gravidade ${g}: ${n} achados`, disabled: n === 0, onclick: () => { const same = state.fam.size === 1 && state.fam.has(fk) && state.grav.size === 1 && state.grav.has(g); state.fam = new Set(same ? [] : [fk]); state.grav = new Set(same ? [] : [g]); state.tipo.clear(); update(); } }, n ? String(n) : "·");
      if (n) c.style.background = `color-mix(in srgb, var(--s${g}) ${Math.min(14 + n * 11, 80)}%, var(--bg))`;
      m.append(c);
    }
  }
}
const toggle = (set, v) => { set.has(v) ? set.delete(v) : set.add(v); update(); };

function matches(a) {
  if (state.grav.size && !state.grav.has(a.gravidade)) return false;
  if (state.fam.size && !state.fam.has(a.familia)) return false;
  if (state.tipo.size && !state.tipo.has(a.tipo)) return false;
  if (state.livro.size && !state.livro.has(a.livro_chave)) return false;
  if (state.q) {
    const hay = norm([a.titulo, a.nota, a.livro, a.autor, a.livro_en, a.en, a.pt, a.tipo_rotulo, a.fonte.pt.tradutor || "", a.fonte.en.capitulo || ""].join(" "));
    if (!state.q.split(/\s+/).every(w => hay.includes(w))) return false;
  }
  return true;
}
function update() {
  const rows = DATA.filter(matches);
  const S = { grav: (a, b) => b.gravidade - a.gravidade || a.id.localeCompare(b.id), livro: (a, b) => a.livro.localeCompare(b.livro) || b.gravidade - a.gravidade, tipo: (a, b) => a.tipo_rotulo.localeCompare(b.tipo_rotulo) || b.gravidade - a.gravidade };
  rows.sort(S[state.sort]);
  $("#list").replaceChildren(...rows.map(card));
  $("#empty").hidden = rows.length > 0;
  $("#count").textContent = rows.length === DATA.length ? `${DATA.length} achados` : `${rows.length} de ${DATA.length} achados`;
  for (const b of document.querySelectorAll(".chip[data-id]")) b.setAttribute("aria-pressed", b._pressed ? String(!!b._pressed()) : "false");
  for (const c of document.querySelectorAll(".cell")) c.setAttribute("aria-pressed", String(state.fam.size === 1 && state.fam.has(c.dataset.fam) && state.grav.size === 1 && state.grav.has(+c.dataset.g)));
  const fc = document.getElementById("fclose"); if (fc) fc.textContent = `Ver ${rows.length} resultado${rows.length === 1 ? "" : "s"}`;
  renderActive(); writeHash();
}
function renderActive() {
  const out = [];
  const add = (label, rm) => out.push(el("button", { type: "button", class: "chip", onclick: rm, title: "Remover filtro" }, label, el("span", { class: "n" }, "✕")));
  if (state.q) add(`“${state.q}”`, () => { state.q = ""; $("#q").value = ""; update(); });
  state.grav.forEach(g => add(`Gravidade ${g}`, () => toggle(state.grav, g)));
  state.fam.forEach(f => add(META.familias[f].rotulo, () => toggle(state.fam, f)));
  state.tipo.forEach(t => add(META.tipos[t].rotulo, () => toggle(state.tipo, t)));
  state.livro.forEach(l => add(DATA.find(a => a.livro_chave === l).livro, () => toggle(state.livro, l)));
  $("#active").replaceChildren(...out);
}

/* ---------- card ---------- */
function paneEl(label, sub, text, marks, cls, emptyMsg) {
  const w = windowed(text || "", marks);
  const p = el("p", { html: text ? markup(w.text, marks, cls) : `<span class="none">${esc(emptyMsg)}</span>` });
  const box = el("div", { class: "pane" }, el("h4", {}, el("span", {}, label), el("span", {}, sub || "")), p);
  if (w.cut) {
    let open = false;
    box.append(el("button", { type: "button", class: "link more", onclick: e => { open = !open; p.innerHTML = markup(open ? text : w.text, marks, cls); e.target.textContent = open ? "Mostrar menos" : "Mostrar contexto completo"; } }, "Mostrar contexto completo"));
  }
  return box;
}
function card(a) {
  const f = a.fonte, pt = f.pt, en = f.en;
  const ptLoc = [pt.pagina_pdf ? `p. ${pt.pagina_pdf} do PDF` : null].filter(Boolean).join(", ");
  const enLoc = en.capitulo ? `cap. “${en.capitulo}”` : en.pagina_pdf ? `p. ${en.pagina_pdf} do PDF` : "";
  const noEn = !a.en_mark.length;
  return el("li", { class: "card", id: a.id, style: `--sev:${SEV_COLOR(a.gravidade)}` },
    el("div", { class: "card-top" },
      el("span", { class: "badge", title: `Gravidade ${a.gravidade} de 5` }, el("b", {}, String(a.gravidade)), a.gravidade_rotulo),
      el("span", { class: "tag", title: a.tipo_desc }, a.tipo_rotulo),
      el("span", { class: "book" }, `${a.autor} · `, el("em", {}, a.livro))),
    el("h3", {}, a.titulo),
    el("div", { class: "cmp" },
      paneEl("Original (EN)", noEn ? "trecho vizinho" : "", a.en, a.en_mark, "orig", "Sem trecho correspondente no original"),
      paneEl("Tradução (PT-BR)", a.fonte.pt.pagina_pdf ? `p. ${a.fonte.pt.pagina_pdf}` : "", a.pt, a.pt_mark, "tr", "")),
    el("p", { class: "note" }, a.nota),
    a.ressalva ? el("p", { class: "warn" }, el("strong", {}, "Ressalva: "), a.ressalva) : null,
    el("div", { class: "src" },
      el("div", {}, el("span", { class: "lbl" }, "Fonte · tradução"), el("strong", {}, dot(pt.titulo)), ` ${dot(pt.edicao)} Tradução: ${dot(pt.tradutor)} `, ptLoc ? `${ptLoc}. ` : "",
        el("a", { href: pt.pagina_url, rel: "noopener" }, "Livro no Mises Brasil"), " · ", pt.pdf_url ? el("a", { href: pt.pdf_url, rel: "noopener" }, "PDF") : ""),
      el("div", {}, el("span", { class: "lbl" }, "Fonte · original"), el("strong", {}, dot(en.titulo)), ` ${dot(en.edicao)} `, enLoc ? `${enLoc}. ` : "",
        el("a", { href: en.url, rel: "noopener" }, en.url.includes("mises.org/library") ? "Livro no Mises.org" : "Texto original"))),
    el("div", { class: "card-actions" }, el("button", { type: "button", class: "link", onclick: e => copyLink(a.id, e.target) }, "Copiar link deste achado")));
}
function copyLink(id, btn) {
  const url = location.href.split("#")[0].split("?")[0] + "#" + id;
  (navigator.clipboard ? navigator.clipboard.writeText(url) : Promise.reject()).then(() => { btn.textContent = "Link copiado ✓"; setTimeout(() => btn.textContent = "Copiar link deste achado", 1800); }).catch(() => { prompt("Copie o link:", url); });
}
function focusCard(id) { state.grav.clear(); state.fam.clear(); state.tipo.clear(); state.livro.clear(); state.q = ""; $("#q").value = ""; update(); setTimeout(() => { const t = document.getElementById(id); t && t.scrollIntoView({ block: "center" }); }, 30); }

/* ---------- cobertura ---------- */
let covFilter = "ALL";
function renderCoverage() {
  const pct = Math.round(100 * META.palavras_comparadas / META.palavras_total);
  $("#cov-sum").textContent = `${META.livros_comparados} de ${META.livros} livros (${pct}% das ${fmt(META.palavras_total)} palavras) foram comparados com uma fonte. Para os demais não existe texto original comparável (originais brasileiros) ou não há versão gratuita.`;
  const groups = [["ALL", "Todos"], ...[...new Set(BOOKS.map(b => b.status))].map(s => [s, BOOKS.find(b => b.status === s).status_rotulo])];
  const cf = $("#cov-filter"); cf.replaceChildren(...groups.map(([k, l]) => { const b = chip(l, "c" + k, () => { covFilter = k; renderCovTable(); cf.querySelectorAll(".chip").forEach(x => x.setAttribute("aria-pressed", String(x.dataset.id === "c" + covFilter))); }, { count: k === "ALL" ? BOOKS.length : BOOKS.filter(b => b.status === k).length }); b.setAttribute("aria-pressed", String(k === covFilter)); return b; }));
  renderCovTable();
}
function renderCovTable() {
  const rows = BOOKS.filter(b => covFilter === "ALL" || b.status === covFilter);
  $("#cov tbody").replaceChildren(...rows.map(b => el("tr", {},
    el("td", {}, b.pagina_url ? el("a", { href: b.pagina_url, rel: "noopener" }, b.titulo) : b.titulo, b.evidencia ? el("small", {}, b.evidencia) : null),
    el("td", { class: "num" }, b.palavras ? fmt(b.palavras) : "—"),
    el("td", {}, el("span", { class: "st" + (b.status === "ALIGNED_AND_SCANNED" ? " ok" : "") }, b.status_rotulo)),
    el("td", { class: "num" }, b.achados ? el("a", { href: "#explorar", onclick: () => { const k = DATA.find(a => a.livro === b.titulo || b.titulo.startsWith(a.livro.slice(0, 18))); if (k) { state.livro = new Set([k.livro_chave]); update(); } } }, String(b.achados)) : "—"))));
}

/* ---------- estado na URL ---------- */
function writeHash() {
  const p = new URLSearchParams();
  if (state.q) p.set("q", state.q); if (state.grav.size) p.set("g", [...state.grav].join(",")); if (state.fam.size) p.set("f", [...state.fam].join(","));
  if (state.tipo.size) p.set("t", [...state.tipo].join(",")); if (state.livro.size) p.set("l", [...state.livro].join(",")); if (state.sort !== "grav") p.set("o", state.sort);
  const s = p.toString(); history.replaceState(null, "", s ? "?" + s : location.pathname + (location.hash.startsWith("#a") ? location.hash : ""));
}
function readHash() {
  const p = new URLSearchParams(location.search);
  state.q = p.get("q") || ""; $("#q").value = state.q;
  const list = k => (p.get(k) || "").split(",").filter(Boolean);
  state.grav = new Set(list("g").map(Number)); state.fam = new Set(list("f")); state.tipo = new Set(list("t")); state.livro = new Set(list("l")); state.sort = p.get("o") || "grav"; $("#sort").value = state.sort;
}

/* ---------- eventos ---------- */
function bind() {
  let t; $("#q").addEventListener("input", e => { clearTimeout(t); t = setTimeout(() => { state.q = norm(e.target.value.trim()); update(); }, 120); });
  $("#sort").addEventListener("change", e => { state.sort = e.target.value; update(); });
  const reset = () => { state.q = ""; $("#q").value = ""; ["grav", "fam", "tipo", "livro"].forEach(k => state[k].clear()); update(); };
  $("#reset").addEventListener("click", reset); $("#reset2").addEventListener("click", reset);
  const tg = $("#toggle"), fl = $("#filters");
  tg.addEventListener("click", () => { const o = fl.classList.toggle("open"); tg.setAttribute("aria-expanded", String(o)); if (o) { if (!$("#fclose")) fl.prepend(el("button", { id: "fclose", class: "btn primary", type: "button", onclick: () => { fl.classList.remove("open"); tg.setAttribute("aria-expanded", "false"); } }, "Ver resultados")); } });
  document.addEventListener("keydown", e => {
    if (e.key === "/" && !/input|textarea|select/i.test(document.activeElement.tagName)) { e.preventDefault(); $("#q").focus(); }
    if (e.key === "Escape") { if (fl.classList.contains("open")) { fl.classList.remove("open"); tg.setAttribute("aria-expanded", "false"); } else if (document.activeElement === $("#q")) { $("#q").value = ""; state.q = ""; update(); } }
  });
}
