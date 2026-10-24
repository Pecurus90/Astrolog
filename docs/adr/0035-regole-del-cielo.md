# 0035 -- Le regole del cielo con le fonti verificate

**Stato:** accettata, 24/10/2026; costruiti classe 1 a 22,00, Garstang, SQM 7-23, Luna a -0,833 topocentrica, nomi delle fasi (commit 26656192, 9046559a, 1f464d3d); non costruiti tabella Bortle di ASTAP (Issue #28, aspetta il foglio di Design) e buio nautico.
Soglie tecniche scelte dalla sessione sulle convenzioni (CLAUDE.md, principio 1); conferma la
tabella Bortle di ADR 0033 R2 e ne verifica la fonte.

**Supera** in `docs/domini/sito.md`: "quella dei **siti di astrofotografia** (Wikipedia"; "da 20,3 a 20,8"

## Contesto

Fase 2 del registro delle regole, gruppo cielo: Bortle, SQM, luminanza, effemeridi, Luna, luogo.
Due ricerche (codice e documenti; fonti pubbliche, col sorgente di ASTAP letto). Trovato: la
tabella Bortle del codice (Wikipedia) non e' quella decisa (ASTAP); il cielo naturale stimato dal
servizio esce 21,98 perche' mescola due costanti (174 ucd/m2 di Falchi con 1,08e5 di Unihedron),
e con la tabella di ASTAP non arriverebbe mai alla classe 1; la Luna sorge e tramonta con la
regola del Sole.

## Decisione

| regola | oggi | scelta | fonte |
|---|---|---|---|
| Bortle da SQM | Wikipedia, `>=` | >21,99 / 21,89 / 21,69 / 21,25 / (4,5: >20,49, letta 5) / 19,50 / 18,94 / 18,38 / 17,80, stretto | ASTAP `unit_sqm.pas` `bortle()`, letto; atlante di Lorenz su ClearDarkSky: 22,00 - 2,5 log10(1 + r) |
| classe 1 rappresentata | centro 21,88 | 22,00, il cielo naturale | Falchi 2016: "22.0 mag/arcsec2" |
| luminanza -> SQM | 1,08e5 (cielo naturale 21,98) | Garstang: V = 12,603 - 2,5 log10 L; 174 ucd/m2 = 22,00 | Falchi 2016 (174 = 22,0); Garstang 1986 via Cinzano |
| SQM credibile | 10-23 | 7-23 | Unihedron FAQ SQM-LU: "about 7 (brightest) to 23 (darkest)" |
| Sole sorge/tramonta | -0,833 | resta | USNO: distanza zenitale 90,8333 |
| crepuscoli | -6 / -12 / -18 | restano | USNO |
| Luna sorge/tramonta | -0,833 | resta (corretto 24/10: era +0,125) | Meeus cap. 15: +0,125 e' per l'altezza geocentrica; la nostra e' topocentrica, parallasse gia' dentro: -0,833 coincide entro 1-2 min |
| nomi delle fasi | finestre di 12 gradi | fase principale nella notte che contiene l'istante; fra le due, falce sotto il 50%, gibbosa sopra | USNO, Phases of the Moon |
| mese sinodico | 29,530588861 | resta | Meeus cap. 49 |
| declinazione massima Luna | 28,8 | resta, tetto per eccesso | lunistizio: 28,725 |
| km per grado | 111,2 | resta | IUGG, raggio medio 6371,0088 km |
| senza buio astronomico | Sole sotto l'orizzonte | buio nautico (-12), detto | ADR 0034; USNO |

- La Luna "dall'orizzonte" di ADR 0034 vuol dire -0,833 sull'altezza topocentrica. Misurato
  (24/10, Vicenza, 4 date): geocentrica a +0,125 e topocentrica a -0,833 sorgono entro 2 minuti;
  topocentrica a +0,125 sorgerebbe 6-8 minuti tardi.
- Il filtro dello SQM misurato e delle Statistiche (ADR 0022, 0024) tiene la Luna sotto -5°: e'
  una misura del cielo naturale, e la rete TESS lo vede costante solo da li' (arXiv 2105.01066).
- Tecnici, senza regola: passi di calcolo, cifre del float32, margini e legende delle tavole.

## Conseguenze

- Fase 4: `units.py` (tabella, Garstang, classe 1, 7-23), CHECK di `schema.sql`, nomi delle
  fasi, finestra senza buio, test e fixture del frontend (20,8 diventa 5, 21,3
  diventa 4), contratti `sito.md`, `effemeridi.md`, `glossario.md`, guida-utente.
- Il foglio di Design (`astrolog.css`) tiene i pavimenti vecchi in un commento: la guardia
  `pavimenti_del_cielo` diventa rossa finche' Design non consegna il foglio nuovo.
- Valori ripetuti senza guardia (latitudine e longitudine nel frontend, legenda dell'anno, "25% e
  4 ore" nelle Impostazioni, 90° del grafico della Luna): si riordinano con una guardia.
