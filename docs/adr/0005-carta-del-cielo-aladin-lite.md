# 0005 -- Il motore della carta del cielo e' Aladin Lite v3

**Stato:** accettata

## Contesto

Planner e Carta del cielo devono disegnare il cielo con sopra il campo di un corredo, la griglia
di un mosaico e l'orizzonte del sito, anche offline e a mani vuote.

## Decisione

- **Aladin Lite v3, uno solo per Planner e Carta del cielo**: LGPL, zero dipendenze, mantenuto
  dal CDS, N impronte e rotazioni native. Le tessere arrivano dal **proxy nostro, con cache su
  disco**.
- Rettangolo del campo, griglia del mosaico e orizzonte del sito li disegniamo noi.
- Sopra il fondo, uno **strato di stelle vettoriali nostro** (HYG, circa 9.000 stelle fino a
  magnitudine 6,5, CC BY-SA) e la Via Lattea: offline e a mani vuote il cielo non e' mai nero.
  `celestia_atlas` e' il ripiego.

## Conseguenze

- Il cielo fotografico ha una regola sua: [0006](0006-cielo-fotografico-fuori-dal-pacchetto.md).
- HYG entra fra i crediti di `THIRD_PARTY.md`.
