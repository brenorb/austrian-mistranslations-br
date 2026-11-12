# Mistranslations of Austrian-school books in Brazilian Portuguese: a sentence-level audit

*Prompted by J. P. Mayall's tweet of 16 Nov 2025 ([x.com/jpmayall/status/1990067165093855457](https://x.com/jpmayall/status/1990067165093855457)): "how many other examples like this exist?"*
*Run on 2026-11-12. Everything is reproducible from `scripts/` (see README.md).*

---

## 1. Short answer

1. **JP's example is real and checks out.** In *O que o governo fez com o nosso dinheiro?* (Rothbard, Mises Brasil 2013), one English sentence of 26 words becomes two Portuguese sentences of 62 words. The second sentence ("É de sua função como meio de troca que derivam todas as suas outras características, como ser unidade de conta e reserva de valor") has no counterpart in the English. One caveat: "store of value" does occur once in the English book, but in a different place, where Rothbard dismisses the textbook list of money's "functions" as aspects of the medium-of-exchange function.
2. **In that same book the example is not isolated.** After excluding the Brazilian preface, an automatic sentence alignment against the 2024 Mises Institute English text finds about **55 passages (≈1,400 words, ≈4% of the Portuguese text)** where the Portuguese is longer than the English by an added sentence or more. In **30 of them a whole Portuguese sentence has no counterpart anywhere in the English book**. I read about 25 in context. Twelve are described in section 4, including a "purely electronic money" gloss in a book written in 1963 and ~160 words of new macroeconomics.
3. **The same pattern, weaker, shows up in *A tragédia do euro*** (Hülsmann, Mises Brasil), where at least five explanatory sentences are absent from the English text. Caveat: the author may have supplied a newer text for the Brazilian edition, so I cannot say these come from the translator.
4. **A second pass over *every* aligned sentence (numbers, negations, quantifiers, semantic divergence) found a different kind of error in other books** (section 4b): units converted into nonsense ("1,6 bilhão de galões de trigo", "280 milhões de toneladas de algodão", a bolt that is 12,7 mm and then "12,7 centímetros" in the same sentence), changed years and figures in at least nine places, a constant ×1.43 on euro amounts in *A tragédia do euro* with the € sign kept, a false friend ("finally" → "finamente"), a dropped "sexual", a polarity reversal in Mises's calculation essay and two lost idioms. Most are in Rothbard's *A grande depressão americana* and the Mises Brasil in-house books.
5. **Books with no problem found at sentence level:** Hoppe's *Teoria do socialismo e do capitalismo* and *Ciência econômica e o método austríaco*, Mises's *Liberalismo* (checked against both EN and DE), *Crítica ao intervencionismo*, *A mentalidade anticapitalista*, Rothbard's *Anatomia do estado*, *Por uma nova liberdade* (apart from one dropped qualifier). The flags they raised were footnotes, tables, edition differences or sentence splitting.
6. **Tally of what I can stand behind (39 curated findings, `findings.json`):** one book with a systematic additions pattern (WHGDTOM), one probable (Tragedy of the Euro), one systematic terminology error and a unit/number cluster in AGD, and ~20 isolated numeric/unit/idiom/polarity errors elsewhere. This is a floor, not a ceiling (see section 7).

**Edition credit, for context only.** *O que o governo fez…* credits "Tradução: Leandro Augusto Gomes Roque; Revisão: Tatiana Villas Boas Gabbi; Revisão Final: Fernando Ulrich". The Portuguese front matter does not say the text was adapted or expanded. I draw no conclusion about intent or authorship of the added sentences, only that they are unmarked.

---

## 2. What was read and how

### Corpus
* **Portuguese**: all 52 free PDFs listed at [mises.org.br/livros](https://mises.org.br/livros/) (3.49 million words), converted to text.
* **Sources**: Mises Institute library EPUBs/PDFs (English; German *Liberalismus* and *Nationalökonomie*; Spanish Huerta de Soto), plus Hazlitt from a public PDF. Rothbard's *Ethics of Liberty* and *The Essential von Mises* were found as files on Mises's own CDN (the *Ethics* book page says no free copy is offered, yet the file is served publicly; I used it only for private comparison and do not redistribute it). *Interventionism: An Economic Analysis* was aligned from the FEE-distributed PDF (a copy hosted on maisliberdade.pt, used for private comparison); the Portuguese (Donald Stewart Jr.) is faithful, with only an added '100%' rate and one explanatory sentence. In the two Rothbard cases the Portuguese is a partial edition (about 20,000 of the English 141,000 words, and 13,000 of 35,000), so only the covered passages were compared; nothing grotesque was found in them (the Portuguese *Ética* adds disclosed translator glosses such as the *usucapião* note).
* Of the 52 Portuguese books, about 29 are translations whose source text I could obtain and align (30 alignments incl. DE/ES controls, ≈1.9 M Portuguese words aligned). The rest are Brazilian originals (Barbieri, Iorio, Constantino, Gianturco, Mazzilli, etc.), anthologies, or books whose source I could not get freely (list in section 8).

### Pipeline (the "ideas from the tweet" turned into code)
JP's example is a **length-inflation + concept-injection** pattern: a short source sentence becomes a longer paragraph with a new technical term. So the detector looks for exactly that.

1. Extract text (PyMuPDF with a font-size filter that drops footnotes and running heads; EPUB where available) and split into sentences.
2. Embed every sentence with **LaBSE** (multilingual), then align source and Portuguese sentences with anchors plus banded dynamic programming (1-1, 1-2, 2-1, 1-0, 0-1 … beads).
3. Flag beads: **ADDITION** (Portuguese sentence with no source counterpart), **EXPANSION** (Portuguese much longer than the aligned source), **OMISSION/CONTRACTION**, low similarity.
4. Filter artifacts: sentence moved elsewhere (global best-match search over the whole other book), neighbours misaligned (windowed length excess), citations, translator notes.
5. A separate **concept-injection lexicon** (store of value, unit of account, fiat, electronic/digital, central bank, GDP, Bitcoin…) lists Portuguese-only technical terms. It reproduces JP's case.
6. **I then read the flagged passages in both languages and grepped the full English text for the suspect concept.** That step removed several false positives of my own (for example, an "inserted" sentence about storage of gold turned out to be the translation of the previous English sentence, split in two).

---

## 3. Results by book

Numbers are *candidates* (upper bound after automatic filtering), not confirmed errors. "✔" = I read the flagged passages and confirmed a real pattern; "noise" = flagged text turned out to be footnotes, tables, edition differences or extraction artifacts.

| Book (PT, publisher/translator per front matter) | Insertion cand. | Inserted words (% PT) | Verdict |
|---|---:|---:|---|
| **O que o governo fez com o nosso dinheiro?** (Rothbard; Mises Brasil 2013) | 55 | 1,420 (4.0%) | ✔ **systematic unmarked additions** |
| **A tragédia do euro** (Hülsmann; Mises Brasil) | 46 | 1,394 (2.2%) | ✔ probable explanatory additions (≥5 confirmed absent from the English) |
| Governo e mercado (Rothbard) | 28 | 662 (0.6%) | mostly sentence merges; no clear case |
| Uma teoria do socialismo e do capitalismo (Hoppe) | 10 | 657 (0.8%) | noise (footnotes); faithful |
| Ação humana (Mises; Instituto Liberal) | 85 | 2,697 (0.7%) | edition differences (PT follows a later English edition than the Mises.org one); translator's note on *moeda* vs *dinheiro* is disclosed |
| A grande depressão americana (Rothbard) | 11 | 486 (0.4%) | faithful in length; ✔ **terminology error** ("Bills" → "Notas") |
| Liberalismo (Mises) vs EN **and** vs DE *Liberalismus* | 3 / 19 | <1% | faithful (apparent omissions are re-splits of long sentences) |
| Por uma nova liberdade (Rothbard) | 11 | 321 (0.2%) | noise (tables) |
| Crítica ao intervencionismo; Mentalidade anticapitalista; Anatomia do estado; Educação livre e obrigatória; Teoria e história; O que deve ser feito; Mises e a Escola Austríaca | 0 | 0 | faithful at this resolution |
| Contra a propriedade intelectual; Ciência econômica e o método austríaco; O cálculo econômico; Esquerda e direita; Liberdade e a lei; Discurso da servidão voluntária; Da produção de segurança | ≤6 | <0.6% | faithful / noise |
| A lei (Bastiat, via EN) | 20 | 507 (2.7%) | not comparable: French original, PT may follow another translation |
| Desestatização do dinheiro (Hayek) | 29 | 810 (1.8%) | noise (Hayek's long footnotes) |
| Dinheiro, crédito bancário e ciclos (Huerta de Soto; vs EN and ES) | 294 / 255 | 3–4% | not comparable: PT is a European-Portuguese text (Portugal), footnote-heavy source |
| Economia numa única lição (Hazlitt) | 59 | 11.7% | edition mismatch (PT follows Hazlitt's revised 1979 text; source is the 1946 text) |
| As seis lições; Defendendo o indefensável | 1 | "34%"/"8%" | alignment gap / Brazilian-edition introduction, not a finding |
| A teoria da exploração… (Böhm-Bawerk extract vs full *Capital and Interest*) | 35 | 1.5% | not comparable: different English translation |

Full table: `results/summary.csv`.

---

## 4. Verified examples (O que o governo fez com o nosso dinheiro?)

Severity is my own judgement, 1–5. English from the Mises Institute 2024 edition.

### 4.1 The tweet's passage (severity 5): concept injection
> **EN (26 words):** *It is important to realize that money cannot be an abstract unit of account or claim, except insofar as it serves as a medium of exchange.*
> **PT (62 words):** *É importante entender que o dinheiro só pode ser visto como uma unidade de conta ou como um título de reivindicação sobre bens a partir do momento em que ele passa a servir como um meio de troca.* **É de sua função como meio de troca que derivam todas as suas outras características, como ser unidade de conta e reserva de valor.**

* Sentence 1 drops "abstract". Rothbard's target, stated in the preceding chapter text, is "an abstract unit of account, divorceable from a concrete good".
* Sentence 2 (bold) is entirely new, and it is a substantive claim: that other properties of money, including store of value, *derive* from the exchange function.
* Nuance: the English book mentions "store of value" once, earlier, as an item in a textbook list Rothbard says is reducible to the exchange function. So the idea is not foreign to him; the problem is the added sentence presented as his.

### 4.2 "Dinheiro puramente eletrônico" (severity 5): anachronism
> **EN (34 words):** *If the banks keep a reserve/deposit ratio of 1:10, then "excess reserves" (above the required ratio) of ten million dollars will permit and encourage a nationwide bank inflation of one hundred million.*
> **PT (101 words, 3 sentences):** *Pode também reduzir a taxa do compulsório… Se os bancos são requeridos a manter um compulsório de 10% (o que significa que para cada $100.000.000 em depósitos bancários há apenas $10.000.000 em reservas bancárias; **todo o resto é dinheiro puramente eletrônico, sem nenhum lastro**)… Se houver, por exemplo, uma quantia excedente de $1.000.000 nas reservas bancárias, tal valor permitirá a criação de empréstimos (inflação monetária) no valor de $10.000.000.*

The English book contains "electronic" zero times. A parenthetical definition and a worked example were added in the same voice as the author.

### 4.3 Inserted macroeconomics (severity 4)
Two unmarked blocks in the chapter on stabilising the price level:
* *"Um aumento na quantidade de bens e serviços aumenta o poder de compra do dinheiro. Uma redução nessa quantidade diminui o poder de compra. Se um determinado setor da economia é mais produtivo do que outro setor, seus preços cairão mais…"* (~60 words)
* *"No que mais, um genuíno aumento no padrão de vida das pessoas decorre de investimentos em capital, o que aumenta a produtividade. E um aumento na produtividade tende a reduzir os preços (e os custos)… Aumentar forçadamente o nível dos preços impede essa disseminação de um padrão de vida mais elevado."* (~100 words)

No sentence in the English book matches either (best cosine anywhere: 0.54–0.55; grep for "more productive", "fixed measure", "rise in living standards", "prices (and costs)" returns nothing).

### 4.4 Other confirmed cases
| # | Passage (PT) | What changed | Sev. |
|---|---|---|:-:|
| 4.4a | *"Toda e qualquer demanda por dinheiro ocorre porque as pessoas podem utilizar aquele bem para calcular preços."* | New sentence generalising demand for money to price-calculation; shifts the emphasis of the regression-theorem passage | 4 |
| 4.4b | Chapter IV opening: *"Desde que o Ocidente abandonou o padrão-ouro clássico… em 1914, o sistema monetário internacional vem oscilando entre um sistema ruim e outro pior…"* | Three new sentences before Rothbard's text begins | 4 |
| 4.4c | *"A Europa já está prestes a adotar um papel-moeda único… área de livre comércio – que será chamada de Comunidade Econômica Europeia (CEE)"* | EN: "seems on the verge of success… a free-trade European Economic Community (EEC) necessarily requires an overarching bureaucracy". PT turns a hedge into an assertion, turns a claim about the EEC into a naming statement, adds a sentence | 3 |
| 4.4d | *"…são incapazes de perceber a importância deste explícito privilégio estatal que protegia os bancos…"* | EN: "fail to realize the importance of this clear dereliction of duty by the states". A different claim (legal privilege vs dereliction of duty) | 3 |
| 4.4e | *"A figura abaixo mostra a evolução do índice de preços ao consumidor… A partir de Bretton Woods, em 1944, já começa a haver uma aceleração…"* | Figure reference and interpretation not in the English | 2 |
| 4.4f | *"Mais recentemente, hiperinflações devastaram os principais países da América Latina."* | Post-publication fact appended to Rothbard's list of hyperinflations | 2 |
| 4.4g | *"pirâmide invertida de dólares sobre o ouro (a pirâmide é invertida porque na base está o ouro…)"* | Invented, self-contradictory metaphor added to "pyramiding of U.S. dollars on gold" | 2 |
| 4.4h | *"A lei de Gresham é válida apenas quando há um controle de preços imposto pelo governo sobre o dinheiro."* | Stand-alone thesis added between two English sentences | 2 |

Cases I examined and **rejected** as translation inflation (the Portuguese is faithful): "ludibriados" (the English says "swindled"), "esforço e prudência" (the English says "scorn sober effort"), "este banimento… em nome da proteção vigorosa" (present in English), and the two SDR sentences (all English content is present).

### 4.5 *A tragédia do euro*: explanatory additions
Examples with no English counterpart (best match 0.55–0.68 cosine, all different sentences): the sentence explaining that a trade deficit means the exporter reinvests in the importer's government bonds; "os dólares — cada vez mais sobrevalorizados, pois sua oferta havia aumentado… mas seu preço continuava fixo em relação ao ouro"; a 16-word English sentence on euro exchange rates that becomes ~146 Portuguese words; "(eletrônico ou físico)". These look like clarifications for readers, not changes of doctrine. Because the Portuguese may follow a newer text from the author, I rate them as *probable, unattributed*.

---

## 4b. Same-length distortions (second pass over every aligned sentence)

Length inflation misses errors that keep a sentence's size. For all 28 EN→PT alignments (≈2.3 M Portuguese words) `scripts/14_distort.py` compares every 1-1 / 1-2 / 2-1 aligned pair for: numbers present on one side only (with footnote marks and mil/milhões/bilhões normalised), negation present on one side only, dropped "only/always/never", and low cross-lingual similarity between similar-length sentences. Hits were then read in context (≈250 read, 39 kept after verification). Hedge/modal detectors were too noisy ("can" vs "pode") and are not reported.

| Book | Source → Portuguese | Type | Sev. |
|---|---|---|:-:|
| A grande depressão americana | "200 million more **bushels**" → "1,6 bilhão de **galões** de trigo" | unit | 4 |
| idem | "1.25 million **bales**" of cotton → "280 **milhões de toneladas** de algodão" (elsewhere "280 mil toneladas" for the same quantity; 850,000 bales → "185 mil toneladas") | unit / ×1000 | 5 |
| idem | "1921–1933 period" → "1921 a **1923**"; "$64.72 billion" → "US$ **64,27** bilhões" (contradicting its own "3,5 bilhões" fall); "56.1 percent" → "**51,6%**" | numeric | 2–3 |
| idem | "monetarism fell between two stools" → "perdeu uma oportunidade" | idiom | 2 |
| O que o governo fez… | "a 1/2 inch bolt must get a 1/2 inch bolt and not a mere 3/8 inch" → "um parafuso de 12,7 milímetros (1/2 polegada) deve obter um parafuso de exatamente **12,7 centímetros**, e não um de 9,5 milímetros" | unit | 5 |
| A tragédia do euro | "€144 billion exposure to Greece, but €507 billion to Spain" → "**€206** bilhões … **€727** bilhões"; five following sentences changed by the same ×1.43 (344→493, 324→465, 173→248, 141→202, 77→110) with the € kept | numeric | 5 |
| idem | "The €110 billion granted to Greece" → "Os **€240** bilhões dados à Grécia" (the same text says 110 bilhões elsewhere) | numeric | 4 |
| idem | "will be reformed and **finally** enforced" → "é **finamente** aplicado" | false friend | 3 |
| O cálculo econômico sob o socialismo | "This is **not** at all the case." → "Mas isso, em absoluto, irá ocorrer." | polarity | 3 |
| Por uma nova liberdade | "an impermissible **sexual** double standard" → "uma duplicidade de pesos e medidas inadmissível" | dropped qualifier | 3 |
| Teoria e história | "the group is the **subject** of history" → "o **assunto** que a história devia abordar" | mistranslation | 3 |
| Governo e mercado | "the argument … **proves far too much**" → "Isso já é bastante revelador" | idiom | 3 |
| Ação humana | "monetary cranks" → "pessoas que defendem zelosamente medidas monetárias não ortodoxas" | softened | 2 |
| Educação livre e obrigatória / Esquerda e direita / Liberalismo / Contra a PI | 1895→1885; mid-1933→1938; Bentham 1787→1781; patent 5,443,036→5.433.036 | numeric typos | 1–2 |

Nothing in this table is a "paragraph inflation" case. These are the errors a length check cannot see and that a reader of the Portuguese cannot detect without the original: the Portuguese is internally plausible ("galões de trigo", "€206 bilhões").

---

## 5. Other systematic problem: terminology

**A grande depressão americana** renders the Federal Reserve assets *Bills Discounted* and *Bills Bought* consistently as **"Notas Descontadas" (25×) and "Notas Compradas" (28×)**. In Fed accounting these are discounted paper and acceptances (usually *títulos/efeitos descontados*, *letras*); "notas" reads as banknotes. It recurs through the book's central statistical chapters (e.g. "Notas Descontadas (US$ 446 milhões) e … Notas Compradas (US$ 45 milhões)"). Severity 3: it is accurate enough for the numbers to follow, but it misleads a reader about what the Fed was doing.

---

## 6. What the aggregate says about JP's questions

* *How many other examples like this?* In WHGDTOM, dozens of the same type; in the other translations I could test, a handful of mild glosses, one terminology pattern, and about twenty isolated numeric/unit/idiom/polarity errors (section 4b). Not "pervasive" at sentence level across the 30 books I could audit, but the numeric and unit errors are exactly the kind a reader cannot spot without the English, and at least some (AGD, Tragedy of the Euro, WHGDTOM) change facts, not only style.
* *Do they come from specific editorial handling?* The two books with the clearest additions are both Mises Brasil in-house editions from 2013–2014. The faithful books credit other translators (e.g. Bruno Garschagen for Hoppe, Pedro Sette-Câmara for *A grande depressão*, Rafael de Sales Azevedo for *Por uma nova liberdade*, Rafael Hotz for Kinsella) and reviewers. With n=2 this is a hypothesis, not a finding.
* *Does it change the theory?* The additions in 4.1–4.3 can: they attach claims (store of value, price-calculation as the source of demand, "purely electronic" money) to Rothbard that his text does not contain.

---

## 7. Limits (read before quoting numbers)

* **"Read all books" was done by machine, not by eye.** All 52 downloadable Portuguese PDFs were extracted and classified (`results/corpus_coverage.csv`). 33 of them (2.45 M of 3.49 M words, 70%) were aligned against a source and every aligned sentence went through the detectors in sections 2 and 4b. I read in context roughly 850 flagged passages. Passing the detectors means "I did not see a problem", not "no problem".
* **The other 30% cannot be audited for mistranslation from the material available:** 11 Brazilian originals/anthologies (no source exists), 1 European-Portuguese translation of Huerta de Soto (*A escola austríaca*; Portugal, not Brazilian), 6 books whose source is not free (the Mises.org book page for Kirzner offers no file, and probes of its CDN for the others returned 403) and 1 where I could not locate a source. The premise that all are free in the Mises library does not hold for these six; the evidence per book is in the CSV.
* **Remaining blind spot:** a same-length, same-numbers sentence with a swapped technical term, a changed causal connective or a softened claim (examples found only when the sentence happened to be semantically divergent enough for LaBSE). Negation/modal/hedge detection is too noisy to rely on. A human or LLM reader per book is still needed for those.
* **Edition mismatches** (Human Action, Hazlitt, possibly Tragedy of the Euro) look like additions or number changes. I only counted a finding when the passage is absent from, or contradicted by, the *English text I had*.
* LaBSE gives modest cosine for long sentences, so the "unmatched" threshold is conservative.
* German (*Nationalökonomie*, OCR) and Spanish (Huerta) controls were too noisy to use; *Liberalismus* aligned well and confirms the Portuguese *Liberalismo* is faithful.
* Footnotes in PDFs were filtered by font size; small residual footnote text can still appear as "additions".

---

## 8. Books not auditable (11 BR originals + 6 source-not-free + 1 not located + 1 European PT + 3 without file)

Per-book evidence: `results/corpus_coverage.csv`. In short:
* **Brazilian originals (no source to compare):** Barbieri (2), Iorio (2), Constantino, *Economia e liberdade*, Mazzilli, Ulrich (*Bitcoin*), Gianturco, and the anthologies *O poder das ideias* and *Ebook de Natal*.
* **Source not free:** *A ética da redistribuição*, *Competição e atividade empresarial*, *Desemprego e política monetária*, *Definindo a liberdade*, *Além da democracia*, *Frédéric Bastiat*.
* **Source not located:** *Uma futura ordem monetária mundial*.
* **Quotation audit of the 11 Brazilian originals (`scripts/16_quotes.py`):** since these books have no source to align, I extracted every quotation of 14+ words (1,234 in total) and matched it against the 116,624 English sentences of the 33 books I hold. 99 quotes matched an English passage (cosine ≥ 0.72). The ones I read (the lowest-scoring 45) quote Mises, Rothbard, Hayek, Böhm-Bawerk and La Boétie faithfully in Portuguese; the rest are bibliographic lines. No distorted quotation was found. The other ~1,100 quotes belong to works I do not hold in English, so they remain unchecked.
* **Browser check (2026-11-12):** the Mises.org page for Kirzner's *Competition and Entrepreneurship* in a normal browser shows only "Buy Now from the Mises Store"; Liberty Fund's Online Library redirects *The Ethics of Redistribution* to a private host that returns 403; the Mises site search returned no results page for Hayek's title. So the six "source not free" books stay unaudited.
* **European Portuguese (Portugal):** *A escola austríaca* (Huerta de Soto); his other title, *Socialismo, cálculo econômico e função empresarial*, was aligned through the IEA's free English translation (one numeric slip found: 1960s → 1970).
* **Listed with no file:** three titles.

## 9. Suggested next steps
1. Ask the publisher or translator whether the 2013 WHGDTOM text was adapted; check the printed edition for an "adaptação" note (the PDF has none).
2. Run an LLM or human reader pass over the 1-1 sentences of the highest-risk titles (A grande depressão americana, A tragédia do euro, Governo e mercado, Ação humana) for the same-length distortions that no detector here catches.
3. Add the original French for Bastiat, La Boétie and Molinari, and the Spanish original for Huerta.
4. If JP's printed edition is not the same file as the free PDF, compare the printed page in his photo with the PDF: the passage matches word for word in the PDF (`data/tweet/` has the images).
