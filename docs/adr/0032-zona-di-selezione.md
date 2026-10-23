# 0032 -- La zona di selezione dei frame

**Stato:** accettata, 23/10/2026 (Marco). Si costruisce dopo measure (ADR 0022) e la parte 2 della
pipeline nuova (notti, setup, oggetti); la tavola la disegna Claude Design prima del codice.

## Contesto

Chi fotografa sceglie i frame buoni prima dello stacking con strumenti separati (blink, grafici
delle misure). L'app ha misure, notti, oggetti e setup insieme: puo' mostrare le statistiche dove
servono. Fin qui l'app non votava i frame e non toccava mai un FITS (`domini/spina.md`).

## Decisione

- **Un'area dedicata** per scegliere i frame, con le statistiche notte per notte, oggetto per
  oggetto, setup per setup.
- **Soglie ed espressioni automatiche** in una sezione delle impostazioni; proposte di partenza
  relative (stesso oggetto, setup, filtro: ADR 0022), perche' una soglia assoluta pubblica non
  esiste. **La scelta a mano vince sempre** sull'automatica.
- **Un frame escluso resta nell'app**, reversibile, e sopravvive alle scansioni.
- **Su comando, con conferma**, i frame esclusi si spostano in una sottocartella "scartati" accanto
  ai loro; **da li' si cancellano solo con avviso**. Mai una cancellazione da sola o diretta.

## Conseguenze

- E' la sola parte dell'app che sposta o cancella un FITS; tutto il resto li legge e basta.
- Uno spostamento in "scartati" la scansione lo vede come spostamento (stessa posa).
- Su una cartella in sola lettura (NAS) spostare e cancellare falliscono, e l'app lo dice.
