# Differenze fra le tavole e l'app

Cosa l'app fa diverso dalla tavola congelata, e perche' (Marco, 8/11/2026: a ogni lavoro chiuso
su una superficie, nello stesso commit; ricetta `/porta-tavola`, punto 8). Una voce per
differenza: **tavola** (file e riga in `handoff/design/pagine/`), **app**, **perche'**: una
convenzione pubblica, una decisione di Marco piu' recente, un dato che l'app non ha, o un passo
dopo. Quando la tavola si allinea o l'app la raggiunge, la voce esce.

Tavola: v76 (7/11). Le differenze delle pagine portate prima dell'8/11 sono nelle voci di
`per-design.md`; da qui in poi stanno qui.

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
- **Altre misure.** Tavola: tutte le colonne (passo 32.1, Marco 6/11). App: solo quelle che la
  tavola nomina. Perche': per le altre (stelle usate, scie, tetto, scala di luminosita',
  calibrazione dello SQM, angoli della forma) i nomi vanno concordati con Marco.
- **Lato del pilastro, Trasparenza, Nuvole, SNR dei pixel.** Tavola: fra le Altre misure. App:
  assenti. Perche': la pipeline non le misura per frame.
- **Setup, titolo.** Tavola: «Setup» o «Due setup». App: anche «3 setup» e oltre. Perche': la
  tavola non dice il caso; testo provvisorio da confermare.
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
