# Per Claude Code — Statistiche, consegna (v31.8, 20/10/2026)

Pagina: `pagine/Statistiche.dc.html` (desktop e telefono; `?formato=`, `?stato=`). Dati di prova: `pagine/componenti/dati-statistiche.js` (`ALstat`). Decisioni: `docs/DECISIONI.md`, sezioni v31 – v31.8. La pagina non calcola niente nell'app: i numeri li manda la rotta.

## Cambiato rispetto alla brief v1.3 (scelte di Marco sulla tavola)

- **Per setup**: tolta la riga «soprattutto nebulose, 81 % delle ore». Il tipo di oggetto per notte non serve piu' a questa pagina.
- **Stagioni, Frame**: tolti «Stelle» e «Fondo cielo» (dipendono dall'oggetto). Restano FWHM, HFD, Eccentricita', SQM.
- **Stagioni**: interruttore «Griglia · Linee» (una linea per anno sui 12 mesi, l'anno scelto in accento, la media tratteggiata).
- **Celle dell'anno**: il delta col segno del trend (su, giu', piatto) in verde o rosso, piu' il segno «+» o «−».
- **Valori al passaggio o al tocco**: un riquadro unico in tutta la pagina, titolo e righe corte etichetta · valore.
- **Bortle**: sotto il numero solo «misurato su {n} notti»; la regola nel riquadro della «i».
- **Capacita'**: «Confronta: Anni · Setup», due setup in ″, i px nel riquadro.
- Animazioni d'ingresso (linee, barre, quadretti) quando la carta entra nello schermo; niente con «riduci movimento».

## Contratto dei dati della rotta (per notte, per sito)

qualita' 0-100 · seeing (dal {data} dell'app) · ore integrate · ore di buio · pose · setup (con la scala ″/px) · filtri con ore e pose · FWHM, HFD, eccentricita' allo zenit (mediana, primo e terzo quartile, numero di pose) · SQM con la Luna sotto −5° e con la Luna su (frame L, senza filtro o a colori) · SQM per ora dalle 21 alle 05 · pose senza massa d'aria escluse · Bortle del sito secondo l'ADR 0022 (notti e mesi). Esce dal contratto: stelle per posa, fondo cielo, tipo di oggetto.

## Controlli fatti (v31.8)

- Contrasto, chiaro e scuro × cinque accenti: testi 4.5:1, linee e punti 3:1. Corretto il gradino 4 della griglia delle stagioni in chiaro (era 4.3–4.4): ora il testo e' il migliore fra testo, nero e bianco (minimo 4.78).
- Carte dentro la colonna e nessun errore in tutti e sei gli stati, desktop e telefono.
- Telefono: le piste sono 38 px dentro 44 toccabili (regola v28). I quadretti del calendario (14 px) restano piccoli: ogni tocco apre il riquadro, e la carta scorre.

## Da approvare con Marco

- «Punto pieno {setup 1}, punto vuoto e linea tratteggiata {setup 2}; … In ″ si confronta fra setup diversi; i px al passaggio.» (nota sotto Confronta setup)
