# Differenze fra le tavole e l'app

Cosa l'app fa diverso dalla tavola congelata, e perche' (Marco, 8/11/2026: a ogni lavoro chiuso
su una superficie, nello stesso commit; ricetta `/porta-tavola`, punto 8). Una voce per
differenza: **tavola** (file e riga in `handoff/design/pagine/`), **app**, **perche'**: una
convenzione pubblica, una decisione di Marco piu' recente, un dato che l'app non ha, o un passo
dopo. Quando la tavola si allinea o l'app la raggiunge, la voce esce.

Tavola: v76 (7/11). Le differenze delle pagine portate prima dell'8/11 sono nelle voci di
`per-design.md`; da qui in poi stanno qui.

## Notti -- la pagina (passo 33)

- **La parola del numero grande.** Tavola: «ore» (Notti 221), anche coi minuti («10 min ore»).
  App: «integrazione». Perche': Marco 10/11; e' la parola delle finestre della notte e dell'oggetto.

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
- **Giudizi tolti.** Tavola: pillole della FWHM (3/4/5″), eccentricita' 0,45/0,71, oggetto basso,
  fuoco, SNR e HFD relativi, «stelle allungate» del Setup, SQM col Bortle. App: solo i numeri.
  Perche': nessuna convenzione pubblica per la FWHM (principio 1, ADR 0039); i giudizi di gruppo e
  setup al passo 40. Brief in `per-design.md`.
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
- **Misure della finestra per formato.** Tavola: inline (Riepilogo 97-98, FinestraRiepilogo 36).
  App: inline uguali. Brief a Design per passarle al foglio.

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
  - **Pillole «HFD alta / SNR basso per l'oggetto»** nel frame scelto (354, 356). App: assenti.
    Perche': soglie senza convenzione pubblica, come i giudizi tolti nelle Notti (sopra).
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
- **Linguette delle produzioni.** Tavola: «2026 · Rifrattore 80/480 · Cima Ekar» (dati.js,
  simulate una per anno). App: l'ottica, sotto camera e ore. Perche': una produzione e' ottica e
  camera (`archivio.md`); anno e sito non la definiscono.
- **In cielo, le righe sotto tipo e costellazione.** Tavola: «idrogeno ionizzato da stelle
  giovani», «alta d'estate e d'autunno» (156). App: vuote. Perche': testi simulati, il catalogo
  non li ha.
- **Fuori catalogo, la costellazione.** Tavola: «si muove nel cielo» (157). App: niente sotto.
  Perche': un oggetto fuori catalogo non per forza si muove (principio 1).
- **Setup, «simulato» e l'avviso dell'eccentricita'.** Tavola: 35, 173. App: assenti, come nelle
  Notti (sopra).
- **Le notti, riga senza Luna.** Tavola: sempre la Luna (121, simulata). App: la cella vuota quando
  la notte non sa la sua Luna; il cielo e' la frase corta delle Notti.
- **Pagina intera con «← Archivio».** Tavola: `contenitore="pagina"` (Riepilogo.dc.html). App:
  solo la finestra; sul telefono la finestra e' gia' a pagina intera.
- **Elenco, cosa si tocca.** Tavola: la riga (DECISIONI 1634). App: il nome. Perche': la tabella
  non ha la classe che stende il comando sulla riga; brief a Design.
- **Dalla notte.** Tavola: gli oggetti della notte non aprono niente (Riepilogo.dc.html 53). App:
  il nome apre la finestra dell'oggetto al posto di quella della notte. Perche': lista fissa di
  Marco, 9/11 (si apre da Archivio, Gli oggetti delle Notti, Ricerca).
- **↗ Progetti.** Assente: Progetti non e' ancora portata.
- **Una Luna piena e mezza.** Tavola: «più di 1 Lune piene» da 1,5 a 2 Lune (132). App: «più di
  una Luna piena». Lo stesso giorno da due siti: tavola non lo dice; app «il 18 maggio 2024 · 2
  notti».
