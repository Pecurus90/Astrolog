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
- **Fuori fino al commit C.** Frame per frame (grafici, Luna, zenit, finestra dei frame) e Tilt e
  curvatura. Il frame si sceglie con ‹ ›, non dal grafico.
