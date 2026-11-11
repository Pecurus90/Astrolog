# Differenze fra le tavole e l'app

Cosa l'app fa diverso dalla tavola congelata, e perche' (Marco, 8/11/2026: a ogni lavoro chiuso
su una superficie, nello stesso commit; ricetta `/porta-tavola`, punto 8). Una voce per
differenza: **tavola** (file e riga in `handoff/design/pagine/`), **app**, **perche'**: una
convenzione pubblica, una decisione di Marco piu' recente, un dato che l'app non ha, o un passo
dopo. Quando la tavola si allinea o l'app la raggiunge, la voce esce.

Tavola: v79 (10/11). Le differenze delle pagine portate prima dell'8/11 sono nelle voci di
`per-design.md`; da qui in poi stanno qui.

## Telaio (passo 33, commit B, 10/11)

Fuori per ora (esiti della lista fissa):
- **Il tondo del modo e "Modo automatico".** Tavola: tondo chiaro/scuro nella testa (Telaio 33),
  "Modo automatico" nell'ingranaggio e "Passa al modo chiaro" in Altro del telefono (Menu 42, 45).
  App: niente. Perche': Marco 10/11, arrivano col passo Tema.
- **"dati simulati" in Stanotte.** Tavola: Telaio 26, 51. App: niente. Perche': i dati sono veri.
- **Il vetro accanto alla bolla.** Tavola: `vb.acc` (Telaio 60-63), spento (`CON=[]`). App: niente.
  Perche': Marco v50.
- **L'anteprima del telefono.** Tavola: telefono 390 x 844 in una finestra larga (Telaio 145).
  App: il telefono riempie la finestra. Perche': serve alla tavola, non a chi usa l'app.
- **Le strisce che scorrono non sfumano il bordo.** Tavola: `componenti/tema.js` 75-85 mette una
  sfumatura di 40 px sul bordo che continua a ogni elemento con `overflow-x: auto` (striscia delle
  notti a ogni larghezza dalla v79, e sul telefono). App: taglio netto. Perche': e' di tutte le
  strisce, non della v78 ne' della v79; va col passo che porta la prima striscia del telefono che ancora manca (piano, passo 33).
- **Gli stati dell'app (caricamento, errore).** Tavola: prop `app` del Telaio (Telaio 13, 38, 55).
  App: li disegna ogni pagina, come prima. Perche': la lista fissa li tiene nelle pagine.
- **Pieno (il Planner a tutto schermo).** Tavola: `pn` (Telaio 147). App: niente. Perche': il
  Planner non c'e' ancora.

Scelte diverse dalla tavola:
- **La scelta del sito in Stanotte.** Tavola v67: i siti coi bottoni; v70: *Cambia ↗*. App: *Cambia ↗*
  verso Impostazioni › Sito. Perche': v70 vince. Il ricordo aperto/chiuso di Stanotte esce con lei.
- **Il giorno dell'ultima scansione e dell'interruzione.** Tavola: «oggi, 07:12» (Menu 36-41).
  App: «30 set 2026, 07:12». Perche': il giorno relativo non arriva dall'API.
- **La riga della scansione in corso senza la lettura dei file.** Tavola: sempre «file letti X su Y».
  App: in una fase dopo la lettura «{fatti} su {su}» della fase. Perche': i file letti esistono
  solo nella lettura.
- **Il perche' della scansione bloccata.** Tavola: sempre «Lettura di una cartella non completata».
  App: quella frase solo se la lettura e' caduta (`scan.state` error), altrimenti «Scansione
  interrotta da un errore.». Perche': il worker va in errore anche in solve, identify, db.
- **La barra della scansione non e' un `progressbar`.** Tavola: `role=progressbar` (Menu 13). App:
  disegno nascosto ai lettori; i numeri li dice la riga sotto. Perche': ARIA non ammette un
  progressbar dentro un menu (axe, `aria-required-children`).
- **Le schede nascoste della bolla.** Tavola: chiusa, le altre schede restano nel giro del
  tabulatore. App: `aria-hidden` e fuori dal giro; la scheda Altro dice `aria-haspopup` e
  `aria-expanded`, e porta il segno della scansione (la tavola lo calcola, `navTel`, e non lo
  disegna). Perche': un bottone invisibile non si raggiunge.
- **Il logo del telefono.** Tavola: `span aria-label` (Telaio 44). App: `role="img"`. Perche': axe
  rifiuta `aria-label` su un elemento senza ruolo.
- **Il titolo della pagina sul desktop.** Tavola: nessuno. App: un titolo nascosto in testa al
  corpo, e il link «Vai al contenuto». Perche': chi usa un lettore di schermo sa dove si trova.
- **Il verdetto di Stanotte senza «buona».** Tavola: solo «✓ notte buona». App: «! notte incerta»,
  «✕ notte non adatta», coi segni delle pillole; senza previsione «Previsione non disponibile.
  Dettagli nella pagina Meteo.». Perche': la tavola mostra un caso solo.
- **La pastiglia Stanotte larga al massimo 340 px, padding compreso.** Tavola v78: 340 piu' i 28 px
  di padding (368, `box-sizing: content-box`). App: 340 (`* { box-sizing: border-box }` del foglio
  dell'app). Perche': il brief v78 dice «al massimo 340»; 28 px di nome in meno.
- **Il menu Altro del telefono, l'ordine.** Tavola: Planner prima di Piano della notte (Menu 44), al
  contrario del desktop (46). App: come la tavola, ognuno il suo (`ALTRO_TELEFONO`).

## Cerca (passo 33, telaio commit D, 10/11)

Tavola `componenti/Cerca` v77: finestra al centro col velo sul desktop, pagina intera sul
telefono. Fuori:
- **Il gruppo Progetti, "Progetti" nell'aiuto e «Planner ↗» accanto agli oggetti.** Tavola:
  Cerca 109, 115, 138. App: niente. Perche': le pagine Progetti e Planner non ci sono ancora (i
  rimandi restano spenti finche' la pagina non esiste, `navigazione.md`).
- **Voci delle Impostazioni senza sezione nell'app.** Tavola: Nome utente, Tema, Orizzonte, Meteo
  apre su, Soglie del Planner, Tempi della notte, Tetto e sicurezza (Cerca 87). App: niente.
  Perche': quelle impostazioni non esistono ancora.
- **«dati simulati» nel piede.** Tavola: Cerca 34-35. App: niente. Perche': i dati sono veri.

Scelte diverse dalla tavola:
- **Gli esempi di attrezzatura e sito nell'aiuto.** Tavola: «zwo, FRA400», «Casa». App: il pezzo
  con piu' ore e il sito predefinito di chi cerca, dalla rotta; senza, solo la parola. Perche':
  principio 1, sono l'attrezzatura e il sito di Marco.
- **Le voci delle Impostazioni portano alle sezioni dell'app.** Tavola: «Chiave Meteoblue» in
  Meteo, «Scansione» in Cartelle e scansione. App: Servizi (le chiavi stanno solo li', v68) e
  Scansioni; in piu' Servizi e Backup, che la tavola non elenca. «Percorso di ASTAP» si trova
  anche con D50 (Marco 6/11), non solo D80.
- **Un sito apre la sua sezione.** Tavola: un sito non apre niente (`href: null`, Cerca 116). App:
  Impostazioni › Siti su quel sito, come prima. Perche': la voce c'e', meglio che porti dove si legge.
- **Il telefono copre lo schermo con `position: fixed`.** Tavola: `absolute` e lo scorrimento in
  cima. App: fissa, la lista scorre dentro. Perche': stesso aspetto, senza spostare la pagina sotto.
- **La finestra chiusa col velo, Esc o Annulla riporta il fuoco al bottone Cerca; Tab gira dentro
  la finestra.** Tavola: non lo dice. Perche': finestra modale (`aria-modal`).
- **L'esempio delle notti senza anno.** Tavola: «25/9, settembre 2026». App: «25/9, settembre».
  Perche': Marco 10/11, un anno fisso invecchia; la ricerca capisce il mese senza anno.
- **Quale riga in testa quando ne valgono due.** Tavola: archivio vuoto, scansione, «Cerco…»,
  errore (un solo stato nei Tweaks). App: errore, «Cerco…», archivio vuoto, scansione. Perche'
  l'errore e l'attesa riguardano cio' che hai appena scritto; a scansione in corso, mentre scrivi,
  si legge «Cerco…».
- **Pezzi e siti col testo in qualunque punto del nome.** Tavola: il nome o una sua parola
  comincia col testo (`prende`, Cerca 94). App: come prima di questo commit, il frammento ovunque
  nel nome (con «m» anche «ASI2600MM Pro»); pagine e voci delle Impostazioni invece come la
  tavola. Perche': la regola dei pezzi e' quella dell'Archivio; cambiarla e' un altro passo.
- **Le righe sono `div role=option`.** Tavola: `a href="#"`. Perche': un'opzione di un `combobox`
  non entra nel giro del tabulatore; il fuoco resta nel campo.

## Notti -- la pagina fra 700 e 1000 px e il sito lungo (v78, 10/11)


## Notti -- Tutto della notte (passo 33, commit B, 8/11)

- **Tilt, soglie del giudizio.** Tavola: incerto fino a 20% compreso (`soglie.js` 106). App:
  incerto da 10 a sotto 20, non adatto da 20. Perche': manuale di ASTAP, "equal or more than 20%
  ... tilt problem" (`pipeline/inspection.py`).
- **Il tilt giudicato sulla mediana.** Tavola: la soglia del frame sulla mediana calcolata dalla
  pagina. App: lo stesso giudizio, scritto dal backend (`night_measures.verdict`). A schermo uguale.
- **Eccentricita', l'asse.** Tavola: «in AR» o «in Dec» solo da 0,40 in su (MisureFrame 242,
  355). App: l'asse quando il frame ne ha uno (stelle non tonde e risolte). Perche': ADR 0039 ha
  tolto le soglie fisse dell'eccentricita'.
- **Gradiente, il lato chiaro.** Tavola: «piu' chiaro verso est» fisso nel frame (357). App:
  niente riga sotto. Perche': testo simulato; il lato vero e' fra le Altre misure, in gradi (passo
  32.1).
- **Luminosita' del cielo senza valore.** Tavola: «nessun frame L o a colori in questa notte» o
  «serve il bias della camera» (235). App: «non c'e' per questi frame». Perche': l'API non manda
  ancora il motivo per l'insieme, solo per frame.
- **SQM col Bortle.** Tavola: il giudizio dello SQM col Bortle. App: solo il numero. Perche':
  nessuna convenzione pubblica (principio 1, ADR 0039).
- **Nomi delle misure.** Tavola: in italiano («Fondo cielo», «Massa d'aria», «Gradiente del
  fondo», «Peso del segnale · PSF Signal Weight»). App: il nome tecnico inglese dei programmi,
  uguale in ogni lingua («Background», «Airmass», «Gradient», «PSF Signal Weight»). Perche':
  Marco 9/11, nessun riferimento italiano (la documentazione italiana di Siril le lascia in <!-- software-ok -->
  inglese); contratto `misure.md`.
- **Altre misure.** Tavola: tutte le colonne (passo 32.1, Marco 6/11). App: anche stelle usate,
  scie, tetto, angoli della forma, PSF SNR, altezza, calibrazione dello SQM. Restano fuori il bias
  (della camera, non del frame), la scala di luminosita' (serve la trasparenza di serie, passo
  40) e zenit, angoli, centro, tilt e curvatura dalla FWHM, curvatura in ″ (gia' in Frame per frame,
  Il frame e Tilt e curvatura).
- **Lato del pilastro, Trasparenza, Nuvole, SNR dei pixel.** Tavola: fra le Altre misure. App:
  assenti. Perche': la pipeline non le misura per frame.
- **Setup, titolo.** Tavola: «Setup» o «Due setup». App: anche «Tre setup»... «Nove setup», poi
  «10 setup». Perche': la tavola non dice il caso; in lettere fino a nove, Marco 9/11.
- **Setup, link a Progetti e «simulato».** Tavola: ↗ Progetti accanto all'oggetto, «simulato»
  accanto al titolo. App: assenti. Perche': Progetti non e' ancora portata; niente e' simulato.
- **Frame scelto all'apertura.** Tavola: il sesto misurato (368). App: il primo misurato.
  Perche': il sesto e' una scelta della dimostrazione.

## Notti -- Tutto della notte, Frame per frame e Tilt e curvatura (passo 33, commit C, 8/11)

- **Ordine «per ora».** Tavola: gli oggetti uno dopo l'altro (MisureFrame 275, `u.g - w.g`). App:
  l'ordine di ripresa, un separatore a ogni cambio di oggetto. Perche': la didascalia della tavola
  dice «nell'ordine di ripresa»; con oggetti alternati nella notte i due ordini divergono.
- **Seleziona i frame ↗.** Tavola: il tondo accanto a «Frame per frame» (36). App: assente.
  Perche': Selezione dei frame non e' ancora portata.
- **Nota della luminosita' del cielo nel grafico.** Tavola: «c'e' solo con L, nessun filtro e a
  colori» o «serve il bias della camera» (310). App: «non c'e' per questi frame». Perche': l'API
  non manda il motivo per l'insieme, solo per frame.
- **Fondo e rumore non confrontabili nel grafico.** Tavola: cita i valori («tempo di posa (300 s e
  180 s)», 311). App: «frame con tempo di posa diversi». Perche': l'API dice cosa cambia, non i
  valori.
- **Tilt e curvatura del sensore.** Tavola: ricalcolati dalle mediane di angoli e centro (339).
  App: la mediana del tilt dei frame (ASTAP, col giudizio) e quella dell'aberrazione fuori asse,
  in px e in ″. Perche': una lettura non calcola; sono le stesse misure delle tessere (ADR 0044).
- **Verso del sensore.** Tavola: non lo dice. App: la riga 1 del file in basso, come lo standard
  FITS; gli angoli sono ai pixel (1,1) (W,1) (W,H) (1,H).
- **«Stelle troppo piccole per una camera a colori».** Tavola: tilt e curvatura tacciono sotto 1,2
  superpixel (233, 358). App: assente; senza tilt la tessera dice «non c'e' per questi frame».
  Perche': la pipeline non ha questa regola (ADR 0044 dice solo le nove aree).
- **Nome dell'oggetto sotto il grafico, telefono.** Tavola: toglie la prima parola («1396» per IC
  1396, 282). App: il nome intero. Perche': tagliare un nome che non conosciamo puo' lasciarne
  solo un numero ambiguo (principio 1); quello che non ci sta salta, come sul desktop.
- **Bottoni degli oggetti sotto la finestra dei frame.** Tavola: uno per gruppo anche se il gruppo
  e' uno (302). App: solo con piu' di un oggetto. Perche': un bottone solo porta dove si e' gia'.

## Archivio -- La pagina (passo 33, tavola v78, 10/11)

- **Deep sky, Sole, Sistema solare e «+ Aggiungi oggetto».** Tavola: linguette in testa e la
  finestra Aggiungi oggetto (Archivio.dc.html 32, 86-94). App: assenti, la pagina e' il deep sky.
  Perche': nessuna sorgente scrive oggetti a mano, SER o log (ADR 0019, passo 46.12); linguette
  che portano a niente non si mostrano.
- **Anteprime da caricare.** Tavola: un tasto per produzione che aggiunge o cambia la foto (63).
  App: il posto c'e', col nome; il tasto arriva con l'anteprima salvata (passo 33.2).
- **Tipo.** Tavola: la prima parola del tipo (139), quindi «ammasso di galassie» sta con gli
  ammassi. App: le famiglie galassia, nebulosa, ammasso, stella, altro, non si sa (archivio.md).
- **Catalogo.** Tavola: Messier, NGC, IC, Sharpless, altro (128). App: le sigle che il catalogo
  scrive (M, NGC, Sh2, LBN...). Perche': «altro» nasconderebbe quale catalogo; il nome e' un dato.
- **Campo di ricerca.** Tavola: «Cerca: M 31, Velo, Andromeda…» (39). App: «Cerca: M 31, NGC
  7000…». Perche': la ricerca guarda sigle e nomi dell'oggetto, non i nomi comuni (in inglese nel
  catalogo): «Velo» non troverebbe niente. A Design.
- **Nome comune.** Tavola: in italiano (catalogo.js). App: come lo scrive il catalogo, in inglese
  («Andromeda Galaxy»), come gia' la finestra dell'oggetto.
- **Carta dei frame senza oggetto.** Tavola: sotto il nome «un gruppo e 2 pannelli senza oggetti
  identificati» (172, simulato). App: su quella riga «restano qui finché ASTAP non c'è» o «frame
  senza oggetti identificati», le parole che la tavola mette accanto al nome (l'API non conta
  gruppi e pannelli); ore, frame e filtri sono quelli veri. La carta non si apre: quei frame si
  guardano in Da confermare.
- **Costellazioni.** Tavola: in italiano (Cefeo, Cigno, catalogo.js). App: il nome latino IAU
  (Cepheus, Cygnus), uguale in ogni lingua. Perche': decisione di Marco del 27/9, confermata il
  10/11. A Design.
- **Frame senza durata in una riga con ore.** Tavola: «senza durata» solo senza ore (167). App:
  «120 frame · 12 senza durata» (archivio.md, «non lo so» non e' zero).
- **Accanto alla ricerca e a «Mostra altri».** Tavola: «15 di 240» fisso (156, 229). App: le righe
  a schermo su quelle trovate; «Mostra altri N» dice le righe che restano, fino a 20.
- **Aperto dalla Ricerca (`?key=`).** Tavola: non c'e'. App: al posto della riga di ricerca
  «← Archivio completo» e «Risultato della ricerca: M 31» (contratto, ricerca.test.tsx).
- **La rete cade dopo una scelta.** Tavola: non c'e'. App: testa e criteri restano, sotto un avviso
  «Archivio non disponibile · Riprova» (archivio.md).
- **Elenco, la carta dei frame senza oggetto.** Riga senza comando e senza ↗: non apre niente.
- **Testa, frame che non sanno la notte.** Tavola: sempre «· 212 notti» (simulato). App: senza
  nessuna notte nota (frame letti senza un sito) le notti non si scrivono, come le ore a zero
  (archivio.md, «non lo so» non e' zero).
- **Carta dei frame senza oggetto, aperto dalla Ricerca (`?key=`).** Tavola: lo stato non c'e'.
  App: la carta manca, la pagina e' l'oggetto cercato; coi criteri resta in testa come in tavola.

## Archivio -- La finestra dell'oggetto (passo 33, commit B, 9/11)

- **Misure dei frame (commit C, 9/11).** Portate: MisureFrame tipo oggetto, gruppi le notti
  (*Mercoledì 16 settembre*, Riepilogo 121), «Le notti a confronto» con l'esito della notte accanto, tessere FWHM e SNR, le
  mediane in testa (Riepilogo 58, 165; MisureFrame 211, 326, 333). Differenze:
  - **Riga del seeing** «seeing previsto … · FWHM allo zenit …» (MisureFrame 332). App: assente.
    Perche': serve la previsione Meteoblue tenuta per le notti passate; arriva in un passo suo.
  - **Tessera della luminosita' del cielo** senza frame L o a colori (229): come nelle Notti, resta.
  - **FWHM in testa con piu' produzioni insieme** (un mosaico). Tavola: la FWHM sempre, l'SNR no
    (165). App: anche la FWHM solo in secondi d'arco; senza scala «—». Perche': i pixel di due
    camere non si confrontano (ADR 0022), come l'SNR.
  - **«misura in corso»** e lo stato «misure in calcolo»: gli stessi della notte, dall'API
    (`pending`), non simulati.
- **Mosaico, l'ordine dei pannelli.** Tavola: Pannello 1..N nell'ordine dei dati (116). App:
  l'ordine della carta, dal pannello con piu' ore; un pannello con piu' oggetti li dice tutti
  («LBN 796, Sh2 230»). Perche': lo stesso pannello porta lo stesso numero nella carta e nella
  finestra.
- **Mosaico con piu' produzioni.** Tavola: non lo mostra. App: solo le linguette dei pannelli, ogni
  pannello di tutte le produzioni (`?panel` con `?production` e' un 422). Perche': le misure di un
  pannello sono scritte solo cosi'; due righe di linguette non stanno nella testa.
- **In cielo, le righe sotto tipo e costellazione.** Tavola: «idrogeno ionizzato da stelle
  giovani», «alta d'estate e d'autunno» (156). App: vuote. Perche': testi simulati, il catalogo
  non li ha.
- **Setup, «simulato».** Tavola: 35. App: assente, come nelle Notti (sopra).
- **Le notti, riga senza Luna.** Tavola: sempre la Luna (121, simulata). App: la cella vuota quando
  la notte non sa la sua Luna; il cielo e' la frase corta delle Notti.
- **Pagina intera con «← Archivio».** Tavola: `contenitore="pagina"` (Riepilogo.dc.html). App:
  solo la finestra; sul telefono la finestra e' gia' a pagina intera.
- **Dalla notte.** Tavola: gli oggetti della notte non aprono niente (Riepilogo.dc.html 53). App:
  il nome apre la finestra dell'oggetto al posto di quella della notte. Perche': lista fissa di
  Marco, 9/11 (si apre da Archivio, Gli oggetti delle Notti, Ricerca).
- **↗ Progetti.** Assente: Progetti non e' ancora portata.
- **Una Luna piena e mezza.** Tavola: «più di 1 Lune piene» da 1,5 a 2 Lune (132). App: «più di
  una Luna piena». Lo stesso giorno da due siti: tavola non lo dice; app «il 18 maggio 2024 · 2
  notti».

## Dashboard -- La pagina (passo 33, commit C, 11/11)

Fuori per ora (esiti della lista fissa):
- **Progetti in corso, vista Progetti, «Prima scansione finita».** Tavola: carta dei progetti, la
  vista del grafico e la domanda dei progetti finiti (Dashboard.dc.html 21-24, 85-98). App:
  assenti; le prossime 3 notti prendono la riga intera, come la tavola senza progetti (297).
  Perche': i progetti non esistono ancora (passi 44, 44.1).
- **Il Sole.** Tavola: la scelta Luna/Sole e la carta del Sole con Kp (55-72). App: la scelta ha
  solo «Luna», come lo stato «Sole non disponibile» della tavola (570). Perche': passi 46.10-46.12.
- **«Il 2026» a barre e «Filtri del 2026».** Arrivano col commit D; fino ad allora in fondo resta
  la sezione dell'anno di prima.

Diverse dalla tavola:
- **Le sei carte del meteo restano le stesse anche a notte coperta.** Tavola: con la notte
  coperta Pioggia e Visibilità prendono il posto di Seeing e Aerosol (360-365). App: sempre
  Nuvole, Seeing, Jet stream, Vento, Condensa, Aerosol; Seeing e Aerosol senza ore dicono «non si
  misura» (stato della CardMeteo). Perche': nessun dato dice quando una notte e' «coperta» per
  cambiare le carte; sei carte al loro posto (Marco, 12/10). A Design.
- **«La prossima notte buona».** Tavola: a notte coperta la testa dice «la prossima notte buona e'
  venerdi' 2, con 8,4 ore di posa» (418). App: non lo dice ancora. Perche': il backend non la
  scrive; arriva col passo 33.4.
- **Le curvette delle prossime notti senza la Luna.** Tavola: la linea tratteggiata della Luna e
  «Luna 00:10» (517, 523). App: la Trasparenza ora per ora e le ore di buio senza Luna. Perche':
  la previsione non porta l'altezza della Luna ora per ora.
- **La Ripresa delle prossime notti.** Tavola: dalla Luna ora per ora (509). App: dalle ore di
  posa divise per banda («3,1 in banda larga, 1,5 stretta»), che il backend scrive per notte.
- **Prossime notti senza previsione.** Tavola: le tre notti restano, con le ore di buio (526). App:
  la carta non c'e'. Perche': senza previsione la risposta non ha le notti dopo stanotte.
- **Da riprendere.** Tavola: le domande una per una («Due siti lo stesso giorno», «Filtro
  sconosciuto», 588). App: «Da confermare, N» con Rispondi e i frame fuori dai conti. Perche':
  l'elenco tipizzato delle domande arriva col passo 33.4.
- **Prima scansione.** Tavola: «Cartella Dati/Astro» e «in lettura: il 2024» (583). App: file
  letti su quanti e quanto manca. Perche': lo stato della scansione non dice cartella e anno in
  lettura.
- **Il dettaglio della Luna.** Tavola: «(le soglie stanno nelle Impostazioni, gruppo Luna)» (596).
  App: la frase senza la parentesi. Perche': la regola della Luna non e' ancora nelle Impostazioni
  (passo 10); 25 e 65 vengono dalla scala della Luna del Meteo.
- **Giorni polari.** Tavola: «fino al 12 agosto» (427). App: senza la data. Perche': il backend
  non scrive quando il buio torna.
