# Il catalogo -- contratto

Il catalogo e' **cio' che si puo' fotografare, con un nome**: le voci portate da `old/`,
impacchettate col programma e versionate con lui. Non si scarica e non si aggiorna da solo.
Il dato vive in `backend/astrolog/catalog/data/`, gli strumenti che lo costruiscono in
`tools/` -- perche' sono **costruzione, non prodotto**: la spina non tocca la rete in nessun
punto. Le parole stanno in [`glossario.md`](glossario.md).

## Cosa chiede l'utente

| richiesta | prova |
|---|---|
| Quando l'app mi dice cos'ho fotografato, voglio leggere "Rosette Nebula", non "NGC 2237" | `test_il_nome_arriva_da_una_qualunque_delle_sigle` |
| Le mie ore su un oggetto non si sparpagliano perche' il mio software lo chiama in un altro modo | `test_le_sigle_restano_intere_e_in_ordine` |
| L'app non mi mostra numeri che nessuno ha controllato | `test_i_quattro_campi_tolti_non_passano` |
| Se un dato non c'e', resta vuoto: non me lo invento e non mi mette zero | `test_i_campi_vuoti_non_si_scrivono`, `test_i_valori_assenti_restano_vuoti_mai_zero` |
| Il catalogo si puo' ricompletare quando voglio, e dopo funziona anche senza rete | `test_le_sigle_da_chiedere_sono_solo_quelle_che_servono` |
| Un errore trovato una volta non torna al giro dopo | `test_una_correzione_curata_ha_l_ultima_parola` |
| Scrivo il nome come mi viene -- `M31`, `messier 31`, `Sh2-155` -- e l'app capisce lo stesso | `test_every_designation_in_the_catalogue_reads_back` |
| Chiedo cosa c'e' in un pezzo di cielo e mi dice anche quanto e' lontano ognuno | `test_the_cone_says_how_far_each_one_is` |
| Se il catalogo non c'e', l'app parte lo stesso e me lo dice | `test_health_says_whether_the_catalogue_is_there` |

## Le decisioni

**Diciannove campi, e ognuno ha un motivo.** Un campo resta se **l'app ci decide qualcosa**
(coordinate, sigle, tipo, costellazione, dimensione, magnitudine) o se **chi legge la scheda
lo cercherebbe** (nome comune, distanza, luminosita' superficiale, opacita'). Sono usciti
`redshift` (nessuna schermata lo usa, e porta rumore: 245 ammassi aperti ne hanno uno che
dovrebbe essere zero, perche' sono dentro la nostra galassia), `hubble_type` (da specialista),
`object_type` (il codice grezzo della fonte, che ripete il nostro tipo) e l'`id` numerico.

**L'identita' di una voce e' lo `slug`, mai un numero di riga.** Gli id si rinumerano a ogni
ricostruzione: un confronto prima/dopo che li mostrasse fermi sarebbe una coincidenza.

**La magnitudine e' un campo solo, con la sua banda.** Due colonne (`V` e `B`) costringevano
ogni lettore a rifare la cascata "prima V poi B" e a sbagliarla; un campo con scritto in quale
banda e' misurato copre il **69%** delle voci invece del 28%, e non si puo' fraintendere. Dove
ci sono tutte e due vince la V: e' la banda con cui si giudica un oggetto, mentre la B e' piu'
blu e fa sembrare piu' debole una nebulosa rossa.

**Le sigle di uno stesso oggetto sono gia' unite, e questo regge le ore.** La Rosetta e' **una
voce** con sette sigle (`NGC 2237`, `NGC 2238`, `NGC 2246`, `C 49`, `LBN 948`, `LBN 949`,
`Sh2 275`): qualunque cosa scriva il software di ripresa, le ore si sommano sullo stesso
oggetto. `NGC 2244`, l'ammasso **dentro** la Rosetta, resta una voce a se': sono due oggetti
veri, e uno sta dentro l'altro.

**L'arricchimento riempie i buchi e non sovrascrive mai.** Le sorgenti si **sommano**: un
valore che c'e' gia' e' stato scelto da una cascata di precedenze fra fonti curate, e
lasciarlo riscrivere da un servizio esterno butterebbe via quella scelta in silenzio.

**Le correzioni curate hanno l'ultima parola**, dopo ogni arricchimento. Sono valori che una
fonte **afferma** e che sappiamo falsi: SIMBAD dice che `IC 434` e' la Flame Nebula, e non lo
e' -- quella e' `NGC 2024`. Senza di loro ogni giro reintroduce un errore gia' chiuso, ed e'
successo. Il campo `da` dice quale valore sbagliato ci si aspetta di trovare: e' la scadenza
della correzione, e quando la fonte si corregge da sola la pezza va tolta.

**Le sigle di SIMBAD non sono le nostre, e sbagliarle non da' nessun errore.** Tre cose,
tutte misurate:

- il **numero e' allineato a destra in un campo a larghezza fissa** che cambia col catalogo
  (`M   1`, `M  11`, `M 110`, `NGC   224`, `NGC  2237`) e non e' documentato. Chiedere con la
  nostra grafia non trova **niente**. Invece di indovinare la larghezza si chiedono tutte le
  spaziature plausibili: costa una lista piu' lunga nella stessa richiesta, non piu' richieste;
- alcuni cataloghi **hanno un altro nome**: `Abell` e' `ACO`, `Arp` e' `APG`, `B` e' `Barnard`.
  Senza la mappa, Abell dava zero risultati su 3.745 voci chieste;
- in risposta si riaggancia **alla sigla che abbiamo chiesto noi**, non a quella che SIMBAD
  scrive, e lo stesso vale per l'elenco delle voci che non conosce: agganciare la prima e
  dimenticare il secondo faceva finire **le voci trovate** nella lista nera, che poi non si
  richiedono mai piu'.

**Le voci "sconosciute" lo sono con le regole di quel giorno.** L'elenco porta l'impronta della
mappa dei cataloghi e delle spaziature con cui si e' chiesto, e **scade** quando quelle
cambiano: il giorno che si scopre che anche `Sh2` ha un altro nome, quelle voci tornano in
gioco da sole invece di restare fuori per sempre. Non erano sconosciute: erano chieste male.

**Un nome comune non contiene cifre.** SIMBAD tiene sotto `NAME ...` anche designazioni di
altri cataloghi (`VV 543E`, `Her 36`, `IRAS F13373+0105 SE`): scritte nella scheda sarebbero
peggio della sigla che sostituiscono, perche' sembrerebbero un nome vero. La regola e'
grossolana di proposito e si perde qualche nome legittimo che porta un numero (`30 Doradus`):
**un nome mancante si vede, un nome falso no.**

**Una voce interrogata e non trovata si ricorda**; un guasto di rete no. Confonderli
vorrebbe dire non richiedere mai piu' una voce che il servizio conosceva benissimo, il giorno
che la rete non andava.

**I nomi comuni restano in inglese.** "Rosette Nebula" e' il nome dell'oggetto, non una frase
da tradurre; tipo e costellazione sono invece codici che l'interfaccia traduce.

**Le licenze viaggiano col dato** (`data/NOTICE`). OpenNGC e' CC-BY-SA-4.0, quindi il catalogo
derivato si distribuisce **sotto la stessa licenza**; VizieR vuole una citazione per catalogo;
Stellarium e' GPL-2.0-or-later; SIMBAD CC-BY-4.0 con la citazione di Wenger 2000. Fondere non
estingue gli obblighi, li concentra -- e la provenienza per campo (`src`) dice quale valore
viene da chi.

## Quanto e' pieno, e perche' il resto non si riempie

Misurato dopo l'arricchimento: coordinate, sigle, tipo e costellazione **100%**; magnitudine
**70%**; dimensione **72%**; angolo di posizione **48%**; nome comune **3%**.

Il resto **non e' un buco**, ed e' stato verificato invece che supposto:

- una **nebulosa oscura non ha magnitudine** (1.942 voci): e' polvere che nasconde, non luce.
  Una **stella non ha dimensione** (792): e' un punto;
- gli **ammassi di galassie** (1.350 senza magnitudine, 3.647 senza dimensione) sono oggetti
  che praticamente nessuno fotografa;
- il **nome comune e' quasi esaurito**: su 22.080 voci, un giro completo di SIMBAD ne ha
  aggiunte **nove** -- e cinque sono arrivate solo dopo aver scoperto che il catalogo `Arp`
  li' si chiama `APG` (*Tadpole Galaxy*, *Mayall's Object*, *Zwicky's Triplet*). Wikidata sui
  Messier ne aggiunge **zero**: le sue etichette sono "Messier 92", cioe' la sigla. Il 3% non
  e' un difetto del catalogo, e' com'e' il cielo: `M 3` non ha un nome perche' nessuno gliene
  ha dato uno, e i 43 Messier senza nome sono ammassi e galassie che un nome non l'hanno mai
  avuto;
- le **planetarie che si fotografano davvero** (Dumbbell, Anello, Elica, Occhio di Gatto)
  hanno gia' tutto: delle 526 senza magnitudine, **tre** hanno un nome.

Per questo l'arricchimento chiede **tre campi e basta**, e nessun'altra fonte e' stata aggiunta.

## Nel database: le due domande

Il catalogo sta **anche** in tre tabelle, e non solo nel file, perche' `identify` deve poter
chiedere "cosa c'e' in questo pezzo di cielo" con una query -- non leggendo l'intero catalogo per
ogni frame. Le tabelle sono **derivate al 100%**: si rifanno da capo quando la versione del
file cambia, e non si toccano se e' la stessa: il caricamento sta sotto il secondo, ma non ha
senso rifarlo a ogni avvio. La misura vive in `backend/tests/perf_baseline.json`, che e' la sua
casa: un numero che una macchina conta non si congela in un doc.

**Le domande sono due, e non ne servono altre**: *che oggetto e' questa sigla* e *cosa c'e' in
questo pezzo di cielo*. La prima non guarda la grafia -- `M31`, `M 31`, `m  31`, `M 031` e
`Messier 31` sono lo stesso oggetto, perche' negli header un nome e' scritto in mille modi e
nessuno di quei modi e' piu' giusto degli altri. La seconda torna gli oggetti **col loro scarto
in gradi**: chi scegliera' il soggetto ha bisogno di quello, non solo dell'elenco.

**Il prefisso di un catalogo si scrive, non si deduce.** `Sh2` porta una cifra dentro, e una
regola "lettere, poi numero" lo spezza in `SH` + `2155`: sono le 313 voci Sharpless, cioe'
proprio quelle che si scrivono negli header a banda stretta. Per questo i cataloghi stanno in
tabella, con la loro forma estesa accanto (`Barnard 33` e `B 33` sono lo stesso oggetto) --
**tranne `Lynds`, che manca apposta**: e' l'autore sia di LBN sia di LDN, e indovinare
manderebbe sull'oggetto sbagliato. La prova e' il giro completo: **tutte le 24.266
designazioni del catalogo, in quattro grafie ciascuna, devono tornare quelle di partenza** (per
le sigle `PK` tre: una coordinata galattica e' gia' impaginata, e uno zero in piu' la cambia).
La grafia normalizzata si scrive **in colonna** al caricamento (`NGC 224` -> `NGC|224`), non
si ricalcola nella query: e' cio' che fa usare l'indice invece di leggere tutte le righe.

**Ogni voce porta anche il suo versore** (`x, y, z`: le stesse coordinate sulla sfera
unitaria). E' cosi' che un cerchio di cielo diventa un **riquadro su tre assi**, che un indice
sa fare, e il salto dell'ascensione retta a 0/360 sparisce invece di restare un caso da
ricordarsi -- due oggetti a mezzo grado l'uno dall'altro possono avere coordinate 0,5 e 359,5.
Il riquadro sgrossa, il coseno decide. Sul catalogo vero la ricerca resta **nell'ordine del
decimo di millesimo di secondo**, ed e' un'operazione che `identify` fara' una volta per frame.

Le due ricerche sono tenute veloci da una guardia sul **piano della query**, non da un
cronometro: un tetto sui tempi ha troppo margine per accorgersi di un indice sparito (senza,
il cono costa 1,8 ms invece di 0,07: venticinque volte tanto, e comunque trentacinque volte
sotto il tetto). Il caricamento invece ha la sua misura in `backend/tests/perf_baseline.json`.

**Un catalogo che non si carica non impedisce all'app di partire.** Senza, l'archivio cataloga,
cerca e conta le ore lo stesso: non sa dire cosa hai fotografato, e lo dichiara in
`/api/health` (`catalog_entries`, `catalog_version`).

## Cosa NON fa

Non si aggiorna da solo e non scarica niente all'avvio. Non inventa un valore mancante. Non
sovrascrive un dato curato. Non tiene numeri che nessuna schermata legge. E **non sa ancora
che `NGC 2244` sta dentro la Rosetta**: la relazione pezzo/adiacenza e' misurata in `old/`
(87 ancore, 314 relazioni: 61 pezzi, 96 adiacenze, 157 da scartare) e mai costruita -- serve al Planner e alla Carta del cielo, non a
contare le ore, ed e' in coda.
