# Brief · Planner, porting (prossima conversazione)

Leggere prima: `CLAUDE.md`, `docs/DECISIONI.md` (v45–v48 e «Da fare dopo v48»), `docs/CHANGELOG.md`.

## Il brief, cinque righe

1. **A cosa serve.** Fare di un oggetto un progetto da riprendere quando è stagione: stanotte o fra sei mesi. Si inquadra (setup, rotazione, mosaico), si decidono le pose, si salva. La Dashboard lo ricorda quando è stagione.
2. **Che dati mostra.**
   - Il cielo di Aladin attorno all'oggetto, col campo del setup.
   - Stagione: mesi migliori, 12 barre, altezza massima, una notte del mese migliore, notti senza Luna, quanto manca o quanto resta.
   - Stanotte: dov'è adesso, la curva, la finestra utile.
   - Pose: lo schema, i filtri con la posa e le ore, il totale e le notti che servono, la priorità.
   - Centro RA/Dec e rotazione, da copiare per NINA o ASIAIR.
3. **Gli stati difficili.**
   - Progetto già in corso: «Aggiorna», con le ore fatte.
   - Fuori stagione: «in attesa · da …».
   - Non sale da questo sito: «Salva lo stesso».
   - Senza rete: c'è il campo, manca l'immagine.
   - Setup virtuale: Salva spento.
   - Più quelli che c'erano già: sito mancante, Aladin che non risponde.
4. **La cosa più importante.** La stagione, non stanotte. E l'inquadratura con le mani: maniglia, righello, mosaico che si adatta.
5. **Cosa NON c'è.**
   - Le note. La priorità invece resta.
   - Le pose preimpostate: la posa si scrive a mano per ogni filtro.
   - Setup e Campo dentro il piano: stanno sul cielo.
   - La barra del telefono sul desktop: lì resta il telaio di sempre.

## Riferimenti approvati

- Telefono: `pagine/Planner telefono.dc.html`, componente `componenti/PianoTelefono.dc.html`.
- Desktop: `pagine/Planner desktop.dc.html`, componente `componenti/PianoDesktop.dc.html`.

Sono tavole coi dati scritti a mano. Il porting li sostituisce con quelli veri del Planner.

## Dove si lavora

- `pagine/Planner.dc.html`, solo la fase di Aladin del cielo profondo (`qOn`, oggetti `A`, `Q`, `piano`). Oggi usa `componenti/PianoColonna.dc.html`, che il porting sostituisce.
- Restano come sono la ricerca (Cupola, Sfera, Dentro), il volo da Trova e il motore `cupola.js`.

## Dal Planner vero si tengono

- L'immagine di Aladin vera: `alaChiedi`, `_alaWant`, `A.imgEl`, il trascinamento che sposta `pDx`/`pDy`, lo zoom `aS`.
- I calcoli:
  - `corDi` e `campoDi`;
  - `anno(id)` per i 12 mesi;
  - `notte`, cioè curva, finestra, meridiano e Luna;
  - `candDi` e `oreDi` per le ore utili;
  - `PROG` per i progetti in corso;
  - le soglie da `ALsoglie`.
- Il salvataggio simulato e la finestra «Prima di salvare» quando un progetto già iniziato cambia rotazione o setup.

## Da fare, in ordine

1. **Desktop.**
   - Nel telaio di sempre: il cielo largo a sinistra, la carta Stanotte di vetro sul cielo, la colonna di 424 px con Stagione, poi Pose, poi Salva in fondo.
   - Sul cielo:
     - «← Cielo»;
     - il nome con l'altezza;
     - «Setup ▾», con il Setup virtuale e «Confronta col campo di»;
     - la scelta dell'immagine e «Adatta»;
     - il righello «da nord verso est» e «Mosaico» (colonne e righe −/+, il cielo si adatta);
     - la maniglia sul campo;
     - la riga del centro con «Copia» e «Rimetti al centro»;
     - la tastiera: frecce, [ e ], + e −, A.
2. **Telefono.**
   - Il cielo a tutto schermo.
   - In basso il righello, che si riduce a pillola; la bolla del Planner e la barra di vetro col riassunto e Salva.
   - Il foglio a tre altezze, con le linguette Stanotte · Stagione · Pose.
   - L'aiuto sui gesti al primo avvio.
3. **Stagione dai dati.**
   - Regola: i mesi con almeno due terzi delle ore del mese migliore, e almeno 3 h.
   - Le due soglie vanno in Impostazioni › Planner.
   - Lo stato «è stagione», «in attesa · da …» o «non sale da qui» si calcola dalla data simulata.
4. **I sette stati**, controllati uno per uno, su desktop e telefono:
   - progetto in corso, fuori stagione, non sale da qui, senza rete, setup virtuale;
   - sito mancante, Aladin che non risponde.

## Controlli prima di mostrare

- Catture a 1440 × 900, 1280 × 800 e su un telefono di 390 × 844.
- Niente da scorrere, salvo la colonna o il foglio quando lo schermo è basso.
- Bersagli di almeno 44 px sul telefono.
- Contrasto nei due modi, coi cinque accenti.
- Ogni stato con la parola e un segno, non solo il colore.

## Dopo il porting

- Sistema solare ed Eventi nella stessa forma; il modo si sceglie nella pagina «Cielo».
- La carta «È stagione» nella Dashboard, ordinata per priorità.
- Da cancellare:
  - le tavole di prova `Planner proposte`, `Telefono comandi`, `Telaio vivo`;
  - i componenti che non servono più: `ProposteNotte`, `PianoColonna`.
