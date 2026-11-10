# Differenze fra le tavole e l'app

Cosa l'app fa diverso dalla tavola congelata, e perche' (Marco, 8/11/2026: a ogni lavoro chiuso
su una superficie, nello stesso commit; ricetta `/porta-tavola`, punto 8). Una voce per
differenza: **tavola** (file e riga in `handoff/design/pagine/`), **app**, **perche'**: una
convenzione pubblica, una decisione di Marco piu' recente, un dato che l'app non ha, o un passo
dopo. Quando la tavola si allinea o l'app la raggiunge, la voce esce.

Tavola: v77 (10/11). Le differenze delle pagine portate prima dell'8/11 sono nelle voci di
`per-design.md`; da qui in poi stanno qui.

## Telaio (passo 33, commit B, 10/11)

Fuori per ora (esiti della lista fissa):
- **Il tondo del modo e "Modo automatico".** Tavola: tondo chiaro/scuro nella testa (Telaio 33),
  "Modo automatico" nell'ingranaggio e "Passa al modo chiaro" in Altro del telefono (Menu 42, 45).
  App: niente. Perche': Marco 10/11, arrivano col passo Tema.
- **"dati simulati" in Stanotte.** Tavola: Telaio 26, 51. App: niente. Perche': i dati sono veri.
- **Cerca in dialogo, coi gruppi pagine e impostazioni.** Tavola: `Cerca` al centro (Telaio 40, 56).
  App: il campo di `Ricerca.tsx` sotto la testa, a destra, sopra la pagina (sul telefono sotto la
  testa). Perche': commit D.
- **Il vetro accanto alla bolla.** Tavola: `vb.acc` (Telaio 60-63), spento (`CON=[]`). App: niente.
  Perche': Marco v50.
- **L'anteprima del telefono.** Tavola: telefono 390 x 844 in una finestra larga (Telaio 145).
  App: il telefono riempie la finestra. Perche': serve alla tavola, non a chi usa l'app.
- **Il contenuto delle pagine fra 700 e 1000 px.** Tavola v77: la testa ci sta, alcune carte
  escono dalla colonna (la Luna nella Dashboard). App: come la tavola. Perche': chiesto a Design
  (`handoff/per-design.md`).
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
- **Il menu Altro del telefono, l'ordine.** Tavola: Planner prima di Piano della notte (Menu 44), al
  contrario del desktop (46). App: come la tavola, ognuno il suo (`ALTRO_TELEFONO`).

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
- **Elenco, cosa si tocca.** Tavola v77: il comando sul nome steso sulla riga (`al-arch__riga-apri`).
  App: il nome. Perche': la tabella di oggi sta nel foglio vecchio, che non si tocca a mano
  (`tools/controlli_veste.py`); arriva col porting della pagina dell'Archivio.
- **Dalla notte.** Tavola: gli oggetti della notte non aprono niente (Riepilogo.dc.html 53). App:
  il nome apre la finestra dell'oggetto al posto di quella della notte. Perche': lista fissa di
  Marco, 9/11 (si apre da Archivio, Gli oggetti delle Notti, Ricerca).
- **↗ Progetti.** Assente: Progetti non e' ancora portata.
- **Una Luna piena e mezza.** Tavola: «più di 1 Lune piene» da 1,5 a 2 Lune (132). App: «più di
  una Luna piena». Lo stesso giorno da due siti: tavola non lo dice; app «il 18 maggio 2024 · 2
  notti».
