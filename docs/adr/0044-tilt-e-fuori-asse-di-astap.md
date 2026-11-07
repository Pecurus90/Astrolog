# 0044 -- Il tilt e l'aberrazione fuori asse di ASTAP tornano accanto a Image Analysis <!-- software-ok -->

**Stato:** accettata, 7/11/2026 (Marco: scelte del 6/11 al passo 32.1 e del 7/11 al passo 32.2).
Corregge ADR 0042, che aveva tolto il tilt dalle HFD per zone, e ADR 0037 per la stessa riga:
FWHMTilt e FWHMCurvature restano, il tilt di ASTAP torna accanto. <!-- software-ok -->

## Contesto

Le tavole di Design mostrano il tilt in % col giudizio 10 / 20 % e una curvatura in %. FWHMTilt
e FWHMCurvature di Image Analysis sono rapporti senza unita' e senza soglie pubbliche. Il tilt <!-- software-ok -->
in % ha una convenzione pubblica: l'ispettore di ASTAP (manuale, hnsky.org/astap.htm, "Image
inspection"; sorgente `unit_inspector_plot.pas`, CCDinspector). Una curvatura in % non ha
nessuna convenzione: ASTAP, e Siril allo stesso modo, misura su un frame l'aberrazione fuori asse, <!-- software-ok -->
in pixel di HFD. Il gradiente in % del fondo non ha nessuna convenzione pubblica.

## Decisione

- **Tilt alla ASTAP**: il frame in terzi, nove aree; mediana delle HFD in ognuno dei quattro
  angoli; tilt = 100 x (angolo peggiore - migliore) / mediana delle HFD di tutte le stelle.
  Giudizio del manuale: fino al 10% buono, dal 20% problema, in mezzo incerto. Serve almeno una
  stella in ognuna delle nove aree. (Marco, 6/11/2026)
- **Curvatura a schermo = aberrazione fuori asse di ASTAP**: mediana delle HFD delle stelle oltre
  il 75% della distanza dal centro all'angolo, meno la mediana dell'area centrale; in px e in ″
  con la scala; con segno; senza giudizio, perche' ASTAP non ne da'. (Marco, 7/11/2026)
- **Gradiente**: niente % del fondo; restano le unita' di rumore di Image Analysis e il lato
  chiaro. (Marco, 7/11/2026) <!-- software-ok -->
- **FWHMTilt e FWHMCurvature** restano nel dettaglio, come numeri puri. <!-- software-ok -->
- Le HFD dell'ispettore vengono dalle stelle usabili di ogni forma, sparse sulla griglia 3 x 3
  come quelle dell'HFD del frame (60 per area): una stella allungata dalla coma resta dentro.
  ASTAP le prende tutte; la mediana per area non cambia, solo il suo rumore.

## Conseguenze

- `pipeline_measures` porta `hfd_tilt_pct`, `tilt_level`, `off_axis_px`; `pipeline_sky` porta
  `off_axis_arcsec` (`pipeline/inspection.py`, `docs/domini/misure.md`).
- A schermo cambia la tavola: un tilt di 20,0% esatto e' "non adatto" (la tavola diceva incerto
  fino a 20 compreso), la Curvatura diventa px e la % del gradiente esce (`handoff/per-design.md`).
- Nessun confronto col programma: `astap_cli` non ha il tilt, e il menu che lo scrive riscrive il
  FITS (TILT, in px). La formula e' confrontata col sorgente, riga per riga.
