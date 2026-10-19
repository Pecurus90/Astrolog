# Per Claude Design -- l'orizzonte del sito, la pagina Progetti, i progetti nella Dashboard

Da Claude Code, 19/10/2026. Decisioni in `docs/adr/0023-planner-e-progetti.md`, sezioni
"L'orizzonte del sito", "La pagina Progetti", "L'avanzamento". Le parole fra «» sono proposte:
Marco le approva sulla tavola. I numeri li manda l'app.

## 1. L'orizzonte del sito (Impostazioni)

Case e alberi coprono pezzi di cielo: l'utente importa il suo orizzonte, e da li' tutta l'app
conta le altezze col suo cielo vero.

- **Dove**: in Impostazioni, nel sito (uno per sito). Riga «Orizzonte»: «Importa file» e, se c'e',
  «Sostituisci» · «Togli».
- **Il file**: quello di N.I.N.A., testo con coppie azimut altezza (es. «90 35»), una per riga.
  Riga piccola: «File dell'orizzonte di N.I.N.A.: azimut e altezza in gradi, una coppia per
  riga.»
- **Il disegno a 360°**, dopo l'import: un cerchio visto dall'alto (N in alto, E a destra come una
  bussola), la sagoma degli ostacoli piena, e la linea tratteggiata dell'altezza minima delle
  Impostazioni (30°). Dove la sagoma supera la linea, conta la sagoma. Al passaggio: «Est 90°:
  ostacolo fino a 35°».
- **Stati** nei Tweaks: nessun orizzonte («Nessun orizzonte: conta solo l'altezza minima.»), file
  importato, file non leggibile («Il file non si legge: servono almeno due righe azimut altezza.»).

**Dove si vede, caricato**:
- **Planner, carta del cielo**: la sagoma dell'orizzonte al posto della linea piatta, e la parte di
  cielo coperta velata.
- **Curva d'altezza** (Stanotte, Sistema solare, Trova): la soglia non e' piu' una retta a 30°, ma
  segue l'orizzonte nella direzione dove sta l'oggetto a quell'ora. Le ore dietro l'ostacolo sono
  tratteggiate, come le ore sotto il minimo.
- Ore utili, momento migliore, mese buono ed Eventi usano lo stesso minimo: nessun disegno nuovo,
  cambiano i numeri. Una riga piccola dove serve: «con l'orizzonte di {sito}».
- **Meteo non cambia**: il cielo e la Luna non dipendono dagli ostacoli.

## 2. La pagina Progetti

Era nella prima brief (`handoff/design-planner-progetti.md`, punto 3): resta valida. Qui tutto, in
un posto.

- **Gruppi**:
  - «In corso»: l'oggetto e' nella sua stagione (mese buono adesso);
  - «In attesa»: fuori stagione, torna a {mese}. Un circumpolare non e' mai in attesa;
  - «Fermi»: una stagione intera passata senza frame;
  - «Finiti»: confermati dall'utente.
- **Scheda di un progetto**:
  - nome: oggetto + ottica + camera;
  - miniatura: l'inquadratura sulla carta;
  - **anello di avanzamento** (ore fatte / ore dell'obiettivo);
  - barre per filtro (fatte / obiettivo); col mosaico la griglia dei pannelli, ognuno col suo
    avanzamento;
  - ultima notte, prossima notte utile, «fermo da {tempo}»;
  - mediane delle misure (FWHM, eccentricita', SQM…) coi giudizi gia' approvati (ADR 0022).
- **Azioni**: «Apri nel Planner», «Segna come finito» / «Riapri», «Elimina».
  - Elimina: «Il progetto sparisce. I frame restano nell'archivio.»
  - Ore raggiunte: «Obiettivo raggiunto. Segnarlo come finito?» (lo propone l'app, lo conferma
    l'utente).
- **Progetto gia' iniziato, riaperto nel Planner**: ore, filtri ed esposizioni liberi. Se cambiano
  inquadratura, griglia o corredo, prima di salvare: «{durata} gia' riprese non conterebbero
  piu'.» · «Salva lo stesso» / «Annulla».
- **Frame senza pannello** (non risolti sul cielo): «{n} frame senza pannello: non risolti.»
- **Vuoto**: «Nessun progetto ancora.» · «Apri il Planner».
- L'avanzamento si aggiorna da solo dopo ogni scansione: nessun pulsante «aggiorna».
- Il Salva di Crea porta qui, sulla scheda appena nata.

## 3. Dashboard

La carta «Progetti in corso» c'e' gia' e resta com'e' (Marco): niente di nuovo da disegnare.
Solo i collegamenti: il ↗ della carta apre Progetti; toccando la riga di un progetto si apre
Progetti sulla sua scheda. L'anello legge lo stesso numero della scheda.

## Telefono

Progetti in una colonna, gruppi come pillole in testa; la scheda aperta a pagina intera. Il
disegno dell'orizzonte a tutta larghezza, bersagli da 44 px.

## Fuori

- Planetario e solare: nessun progetto (Marco).
- Nessun punteggio d'insieme, nessuna classifica.
- Il piano della notte e l'export (ADR 0013) hanno una brief a parte.

CHANGELOG e DECISIONI come al solito.
