#!/usr/bin/env python3
"""Build the curated, manually-verified findings list (findings.json + results/findings.md).
Every entry is located by a phrase in the PT bead; EN context comes from the aligned neighbours. Commentary is mine
(verified by reading both texts and grepping the full English source)."""
import json, pathlib, re
root = pathlib.Path(__file__).resolve().parent.parent
CUR = [
 # (book, PT phrase, category, severity 1-5, note)   -- every entry re-read in context and grepped against the full English text
 ("whgd", "É de sua função como meio de troca que derivam", "CONCEPT_INJECTION", 5,
  "The case in JP Mayall's tweet. The English has ONE sentence here (26 words: 'It is important to realize that money cannot be an abstract unit of account or claim, except insofar as it serves as a medium of exchange'). The Portuguese has two (62 words). Sentence 1 drops the word 'abstract', which carries Rothbard's point (the preceding chapter text says 'Money is not an abstract unit of account, divorceable from a concrete good'). Sentence 2 is invented: that unit of account and 'reserva de valor' (store of value) 'derive' from the exchange function. 'Store of value' occurs once in the whole English book, in a different passage where Rothbard dismisses the textbook list of 'functions' as mere aspects of the medium-of-exchange function."),
 ("whgd", "puramente eletrônico", "ANACHRONISM", 5,
  "English: 'If the banks keep a reserve/deposit ratio of 1:10, then excess reserves of ten million dollars will permit and encourage a nationwide bank inflation of one hundred million' (34 words). Portuguese: 101 words in three sentences; adds a parenthetical gloss ('...all the rest is purely electronic money, with no backing') and a new worked example with $1,000,000 / $10,000,000. The English book contains the word 'electronic' zero times; the book was written in 1963."),
 ("whgd", "Toda e qualquer demanda por dinheiro ocorre porque", "CONCEPT_INJECTION", 4,
  "Inserted generalisation: 'All demand for money exists because people can use that good to calculate prices.' Not in the English. It also shifts the emphasis of Rothbard's regression-theorem argument (demand for money arises from the exchange function added to previous non-monetary demand) towards price-calculation."),
 ("whgd", "Um aumento na quantidade de bens e serviços aumenta o poder de compra do dinheiro", "CONCEPT_INJECTION", 4,
  "~60-word block of new didactic macroeconomics with no English counterpart (best semantic match anywhere in the English book: cosine 0.55): 'an increase in the quantity of goods and services increases the purchasing power of money ... if one sector is more productive than another its prices will fall more ...'."),
 ("whgd", "No que mais, um genuíno aumento no padrão de vida", "CONCEPT_INJECTION", 4,
  "~100-word block on productivity, falling prices and living standards inserted in the section on stabilising the price level. Grepping the English book for 'more productive', 'fixed measure', 'rise in living standards', 'prices (and costs)' returns nothing."),
 ("whgd", "vem oscilando entre um sistema ruim e outro pior", "POLEMIC_INSERTION", 4,
  "Chapter IV is headed by three new sentences not in Rothbard: 'since the West abandoned the classical gold standard in 1914 the international monetary system has oscillated between a bad system and a worse one. Countries adopt fixed exchange rates and soon regret it ... Others prefer an amorphous system.' Editorial voice, unmarked."),
 ("whgd", "que será chamada de Comunidade Econômica Europeia", "MEANING_SHIFT", 3,
  "English: the drive for a European paper currency 'seems on the verge of success. This goal is being sold to the gullible public by the fallacious claim that a free-trade European Economic Community (EEC) necessarily requires an overarching bureaucracy...'. Portuguese: 'Europe is already about to adopt a single paper money' (a flat assertion instead of 'seems on the verge'), and the EEC becomes 'a free-trade area which will be called the EEC' (the claim about the EEC becomes a naming statement), plus an added sentence ('The bureaucrats' idea is to make the public believe...')."),
 ("whgd", "são incapazes de perceber a importância deste explícito privilégio", "MEANING_SHIFT", 3,
  "English: writers who cite 19th-century America as a horrid example of free banking 'fail to realize the importance of this clear dereliction of duty by the states'. Portuguese: they fail to see 'this explicit state privilege that protected the banks and exempted them from redeeming their notes in specie' (a different claim: a legal privilege rather than the states' dereliction), and glosses 'free banking' in parentheses."),
 ("whgd", "Mais recentemente, hiperinflações devastaram", "UPDATE_INSERTION", 2,
  "Appends 'More recently, hyperinflations devastated the main Latin American countries' to the list of historical hyperinflations; the English list ends with the Chinese and other currencies after WWII."),
 ("whgd", "A figura abaixo mostra a evolução do índice de preços ao consumidor", "UPDATE_INSERTION", 2,
  "Two inserted sentences ('The figure below shows the evolution of the CPI in the US. From Bretton Woods in 1944 an acceleration begins, strongly intensified after abandonment of the gold standard in 1971') are not in the English edition."),
 ("whgd", "A lei de Gresham é válida apenas quando", "DIDACTIC_PADDING", 2,
  "Adds the stand-alone thesis 'Gresham's law is valid only when there is government price control on money' between two English sentences that do not state it in this form."),
 ("whgd", "pirâmide invertida", "DIDACTIC_PADDING", 2,
  "English: 'a pyramiding of U.S. [dollars] on gold, of British pounds on dollars...'. Portuguese adds an invented metaphor ('inverted pyramid ... inverted because gold is at the base and dollars on the body'), which is self-contradictory as a metaphor."),
 ("tragedy_euro", "As reservas de ouro do Federal Reserve foram diminuindo", "DIDACTIC_PADDING", 2,
  "Added explanatory clause ('overvalued because their supply had increased greatly while their gold price stayed fixed')."),
 ("tragedy_euro", "Isso ocorre porque, quando há um déficit comercial", "DIDACTIC_PADDING", 3,
  "Added 39-word explanation of how trade deficits end in government bonds; absent from the English text."),
 ("tragedy_euro", "Como a adoção do euro significou um valor comum para todas as moedas", "DIDACTIC_PADDING", 3,
  "A 16-word English sentence becomes ~146 Portuguese words in three sentences (adds the purchasing-power / Deutschmark explanation and a sentence on Italians, Spaniards and Greeks)."),
 ("tragedy_euro", "eletrônico ou físico", "ANACHRONISM", 1, "Adds a '(electronic or physical)' gloss on how the ECB creates money."),
]
out = []
for book, phrase, cat, sev, note in CUR:
    wd = root / "work5" / book
    beads = json.loads((wd / "beads.json").read_text())
    k = next((i for i, b in enumerate(beads) if phrase in b["pt"]), None)
    if k is None: print("NOT FOUND", book, phrase); continue
    b = beads[k]
    ctx = [beads[i] for i in range(max(0, k - 1), min(len(beads), k + 2))]
    out.append(dict(book=book, bead=k, category=cat, severity=sev, note=note,
                    en=" ".join(x["en"] for x in ctx if x["en"]), pt=" ".join(x["pt"] for x in ctx if x["pt"]),
                    en_words=sum(x["en_w"] for x in ctx), pt_words=sum(x["pt_w"] for x in ctx)))
# ---- second pass: same-length distortions found by scripts/14_distort.py (located by bead index) ----
BYK = [
 ("agd", 3481, "UNIT_ERROR", 4, "'200 million more bushels [of wheat]' becomes '1,6 bilhão de galões de trigo' ('billion gallons of wheat'): the unit is silently converted to a liquid measure that makes no sense for wheat."),
 ("agd", 3492, "UNIT_ERROR", 5, "'1.25 million bales' of cotton becomes '280 milhões de toneladas de algodão' (280 million tonnes, roughly three times annual world production). Elsewhere the same translation gives '280 mil toneladas' for the same quantity (three orders of magnitude apart) and for the other bale counts (850,000 bales -> 185 mil toneladas)."),
 ("agd", 3500, "UNIT_ERROR", 3, "'1.3 million bales' -> '280 mil toneladas': bales converted to tonnes without a note, so the numbers no longer match the English table values."),
 ("agd", 1603, "NUMERIC_ERROR", 3, "'the 1921-1933 period' becomes 'o período que vai de 1921 a 1923'."),
 ("agd", 4341, "NUMERIC_ERROR", 3, "'from $68.25 to $64.72 billion' (a fall of $3.5 billion) becomes 'de US$ 68,25 bilhões para US$ 64,27 bilhões': digits transposed, and the Portuguese sentence now contradicts its own '3,5 bilhões'."),
 ("agd", 4769, "NUMERIC_ERROR", 2, "'56.1 percent' becomes '51,6%' (digits transposed)."),
 ("whgd", 352, "UNIT_ERROR", 5, "'The buyer of a 1/2 inch bolt must get a 1/2 inch bolt and not a mere 3/8 inch.' becomes 'O comprador de um parafuso de 12,7 milímetros (1/2 polegada) deve obter um parafuso de exatamente 12,7 centímetros, e não um de 9,5 milímetros': the same bolt is 12.7 mm and then 12.7 cm (ten times larger), inside one sentence."),
 ("whgd", 349, "UNMARKED_LOCALISATION", 2, "'an eight ounce bottle of medicine' becomes 'um frasco de 250 mililitros' (8 fl oz is ~237 ml, and the measure was changed without a note); same passage converts pounds to kilos."),
 ("tragedy_euro", 2526, "NUMERIC_ERROR", 5, "'Banks headquartered in the Eurozone had €144 billion exposure to Greece, but €507 billion to Spain' becomes '€206 bilhões ... €727 bilhões'. The next five sentences are changed the same way (344→493, 324->465, 173->248, 141->202, 77->110), a constant factor of ~1.43 (a USD/EUR rate) while the euro sign is kept. Either a silent currency conversion mislabelled as euros or different data; in both cases not what the English says."),
 ("tragedy_euro", 3086, "NUMERIC_ERROR", 4, "'The €110 billion granted to Greece' becomes 'Os €240 bilhões dados à Grécia'; the Portuguese text itself says '110 bilhões de euros' for the same package a few pages earlier."),
 ("tragedy_euro", 3215, "FALSE_FRIEND", 3, "'The SGP will be reformed and finally enforced' becomes 'O Pacto de Estabilidade e Crescimento é finamente aplicado' ('finally' -> 'finamente' = 'finely'); the future and 'reformed' are also lost."),
 ("education_free", 773, "NUMERIC_ERROR", 2, "'Pennsylvania Compulsory Education Law of 1895' becomes 'de 1885'."),
 ("left_right", 212, "NUMERIC_ERROR", 2, "'the editor had written in mid-1933' becomes 'meados de 1938' (the quote is about the New Deal period)."),
 ("liberalism", 3302, "NUMERIC_ERROR", 1, "Bentham's 'Defence of Usury (1787)' becomes '(1781)'."),
 ("against_ip", 789, "NUMERIC_ERROR", 1, "US patent No. 5,443,036 becomes 'N. 5.433.036' (and 6,007,340 becomes 6.007.349 two beads later): citation numbers transposed."),
 ("mises_calc", 510, "POLARITY", 3, "'This is not at all the case.' becomes 'Mas isso, em absoluto, irá ocorrer.' Without a negation word the sentence reads as an affirmation ('this will absolutely happen') of the thing Mises is denying (that socialist institutions evolve naturally out of capitalist ones)."),
 ("for_new_liberty", 1802, "DROPPED_QUALIFIER", 3, "'an impermissible SEXUAL double standard has been at work' (about rape victims treated as the guilty party) becomes 'uma duplicidade de pesos e medidas inadmissível': 'sexual' is dropped, which removes the point of the sentence."),
 ("theory_history", 2502, "MISTRANSLATION", 3, "'not individuals but the group is the subject of history' (subject = agent) becomes 'o assunto que a historia devia abordar era o grupo' (subject = topic)."),
 ("power_market", 1410, "IDIOM", 3, "'the argument ... proves far too much' (a standard objection: it would prove absurd conclusions too) becomes 'Isso já é bastante revelador' ('that is quite revealing'), losing the logical point."),
 ("human_action", 4451, "MEANING_SHIFT", 2, "'There are men who are commonly stigmatized as monetary cranks. The monetary crank suggests a method for making everybody prosperous by monetary measures.' becomes 'Há pessoas que defendem zelosamente medidas monetárias não ortodoxas': Mises's pejorative 'monetary crank' is neutralised."),
 ("huerta_socialism", 230, "NUMERIC_ERROR", 2, "'particularly in the 1960s' becomes 'especialmente nos anos de 1970' (European-Portuguese edition hosted by Mises Brasil, translated from the Spanish; compared here through the IEA's English translation)."),
 ("agd", 256, "IDIOM", 2, "'monetarism fell between two stools' becomes 'o monetarismo perdeu uma oportunidade' ('missed an opportunity')."),
]
for book, k, cat, sev, note in BYK:
    beads = json.loads((root / "work5" / book / "beads.json").read_text()); b = beads[k]
    out.append(dict(book=book, bead=k, category=cat, severity=sev, note=note, en=b["en"], pt=b["pt"], en_words=b["en_w"], pt_words=b["pt_w"]))
# AGD terminology finding (global, not bead-bound)
out.append(dict(book="agd", bead=None, category="TERMINOLOGY", severity=3,
    note="'Bills Discounted' / 'Bills Bought' (Federal Reserve assets: discounted commercial paper and acceptances) are rendered consistently as 'Notas Descontadas' (25x) and 'Notas Compradas' (28x). 'Notas' reads as banknotes; the standard rendering is 'títulos/efeitos descontados' or 'letras'. Systematic across the book's central statistical chapters.",
    en="Bills Discounted ($446 million) and Bills Bought ($45 million)", pt="Notas Descontadas (US$ 446 milhões) e as Notas Compradas (US$ 45 milhões)", en_words=None, pt_words=None))
(root / "findings.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
md = []
for i, f in enumerate(out, 1):
    md.append(f"### {i}. [{f['book']}] {f['category']} (severity {f['severity']}/5)\n\n{f['note']}\n\n> **EN:** {f['en'][:900]}\n>\n> **PT:** {f['pt'][:1100]}\n")
(root / "results/findings.md").write_text("\n".join(md))
print(len(out), "findings")
