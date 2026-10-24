# 0023 -- Planner e Progetti: inquadratura, mosaico, setup di prova, filtri, modifiche

**Stato:** accettata, 18/10/2026 (Marco). ADR 0033: nel piano della notte il meteo e' una striscia (ADR 0013). Superata la riga "Planetario e solare: nessun progetto" (Marco, 19/10/2026: si salvano in Progetti senza ore). I progetti nascono solo nel Planner (Marco, 24/10/2026). La spec sta in `docs/domini/planner.md` (24/10/2026).

## Contesto

L'ADR 0013 dice cos'e' un progetto; le decisioni portate dal vecchio progetto stanno in
`docs/domini/ereditato.md` (A, F). Marco ha descritto il flusso del Planner il 18/10/2026; restavano
aperti rotazione, mosaico, sensori di prova, filtri per camera e modifica di un progetto iniziato.
Ricerca del 18/10/2026 sul codice di N.I.N.A. (MPL-2.0, branch develop), ASCOM, ASTAP, Calabretta
& Greisen 2002, CDS e pagine dei produttori di camere.

## Decisione

- **Percorso**: Trova, Scegli il setup, Inquadra, Crea, Salva, Segui. Pagina **Progetti**.
- **Carta**: Aladin Lite v3 stabile 3.8.1 (LGPL), logo e credito CDS visibili; sette mappe HiPS,
  DSS2 colore di partenza, NSNS non commerciale solo in cache; solo cache, nessuno scaricamento.
- **Rotazione** dal Nord verso Est, 0-180° (quadrati 0-90°), confronto modulo 180 con tolleranza
  1°, come N.I.N.A. e Calabretta & Greisen.
- **Mosaico** come il Framing Assistant di N.I.N.A.: colonne × righe, sovrapposizione 20% di
  partenza, centri per gnomonica, obiettivo per pannello.
- **Setup di prova solo per guardare**; lista dei sensori nostra, solo camere astronomiche
  dedicate, con l'uso dichiarato dal produttore; sensore personalizzato.
- **Filtri per camera** dal numero di bande, gli altri in «Tutti i filtri»; ore per filtro, posa
  facoltativa, Crea parte vuota.
- **Progetti**: nome «oggetto · ottica · camera»; gruppi dai mesi buoni; finito proposto
  dall'app; modifiche libere salvo inquadratura, griglia e setup, che chiedono un avviso
  numerico; «Apri nel Planner» riapre tutto.
- **Avanzamento** scritto dalla scansione: stesso oggetto, setup e centro nel campo.
- **Sistema solare**: simulazione dei nove corpi con immagini a credito e calcoli Meeus senza
  librerie nuove; Luna, Sole e pianeti si salvano in Progetti (ADR 0013).
- **Giudizi solo dove una fonte fissa il confine** (Nyquist, ADR 0021, Lewis/BAA, massa d'aria 2);
  consigli sotto i giudizi solo con una fonte; il resto resta un numero.
- **Soglie dell'utente in Impostazioni** con partenza e fonte, cambiabili per una ricerca.
- **Eventi** (ISS, eclissi Espenak, occultazioni lunari) e Macchia Rossa: si disegnano ora.
- **Orizzonte del sito** in formato N.I.N.A., uno per sito, vale dove conta l'altezza; Meteo no.

## Conseguenze

- Nuove tabelle: progetti, pannelli con inquadratura, obiettivi per filtro, oggetti aggiunti
  (ADR 0013). Lo schema si ricrea.
- Dipendenza frontend nuova: `aladin-lite` 3.8.1.
- ADR 0006 perde il pulsante "scarica il cielo": solo cache.
- File nuovo dei sensori, con test che lo confronta coi frame veri.
- `docs/domini/mosaico.md`: la frase "nessuno documenta un valore predefinito" era falsa per
  N.I.N.A.; il riconoscimento dei mosaici dai frame resta senza soglia minima.
