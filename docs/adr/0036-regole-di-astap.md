# 0036 -- Le regole di ASTAP con le fonti verificate, e il catalogo stellare D50

**Stato:** accettata, 24/10/2026. Raccoglie le decisioni del piano di ASTAP (D2-D8) che stavano
solo nel materiale di lavoro; D1 e D7 sono in ADR 0033. Chiude la domanda aperta di ADR 0003
(quale catalogo). Soglie tecniche scelte dalla sessione sulle convenzioni (CLAUDE.md, principio 1).
Costruita in parte (`pipeline/solve.py`); punti 7, 8 e 10 fatti, 9 da fare. **Superata in parte da ADR 0039**: il
tempo per lancio diventa un limite di previsione, minimo 30 s; 60 s finche' non e' costruito.

## Contesto

Fase 2 del registro delle regole, gruppo ASTAP. Due ricerche: codice e documenti; sorgente di
ASTAP (mirror CanardConfit/ASTAP, CLI 2026.09.19) e di N.I.N.A. (isbeorn/nina) letti. Due difetti
trovati e riparati: `astap_cli` legge i `.fz` dal 2026.07.17, non dal 16 (la data della GUI);
"stessa focale" non era simmetrica.

## Decisione

| regola | valore | fonte |
|---|---|---|
| raggio con indizio | 30° | N.I.N.A. `PlateSolveSettings.cs` `searchRadius = 30` |
| raggio cieco | 180° | default di ASTAP (`radius_search1 '180'`); N.I.N.A. forza 180 senza coordinate |
| sottocampionamento | `-z 0` (ASTAP sceglie), poi `-z 1` | ASTAP `report_binning_astrometric`; N.I.N.A. 0; misura: `-z 1` 19/19 |
| campo | l'altezza calcolata; `-fov 0` solo a campo ignoto | N.I.N.A. passa l'altezza; ASTAP con `-fov 0` prova 0,3-11,9° |
| indizio ereditato | centro misurato di una sorella risolta con lo stesso OBJECT | `spine/solve.py` di prima; mai per sessione: due pose senza OBJECT non sono sorelle |
| campo ereditato | scala misurata di una posa risolta con camera, binning e ottica uguali (ottica non scritta in tutte e due: uguale, l'ASIAIR non la scrive mai) | misura: 9 frame veri (D80, indizio, `-z 0`) risolti tutti col campo da x0,7 a x1,25, quasi tutti da x0,6 a x1,5, nessuno da x2; un campo sbagliato fallisce in 13 s al piu', poi `-fov 0` |
| stelle, tolleranza, dimensione | default di ASTAP: 500, 0,007, 1,5" | help di `astap_cli` |
| tempo per lancio | 60 s | misura: oltre il doppio del cieco riuscito piu' lento (23 s); NAS da misurare |
| ritentativi | primo, piena risoluzione, campo libero, cieco col campo | N.I.N.A. fa solo il cieco (`ImageSolver.cs`); gli altri due gradini misurati |
| `.fz` | `astap_cli` dal 2026.07.17 | sorgente, RICE_1 nella CLI |
| scala attesa contro risolta (D8) | avviso oltre il 5% | manuale di ASTAP: "within preferably 5% accuracy" |
| catalogo | **D50** al primo avvio | manuale: sotto 40' "D20, D50 or even the D80"; D05 solo da 0,6°; D50 copre 0,2-10° |

Decisioni di Marco dal piano di ASTAP, qui con la loro casa:

- **D2 -> D5**: un frame oltre il tempo, che si blocca o che ASTAP non apre si riprova una volta
  alla scansione dopo, poi aspetta un ASTAP o un catalogo nuovo (`pipeline/solve.py` `PASSES`).
- **D4**: ASTAP 2026 col pacchetto, che legge i `.fz`.
- **D6**: un frame senza tipo ha un tentativo solo (spesso e' una calibrazione).
- **D8**: una scala risolta diversa dall'header oltre il 5% si segnala; la soluzione resta.

## Conseguenze

- Il pacchetto scarica il D50 (circa 900 MB) al primo avvio, accanto ad ASTAP. Per campi oltre
  ~10° (obiettivi fotografici) ASTAP chiede G05 o W08: un'idea, finche' un utente non la chiede.
- La scelta dell'oggetto principale e i mosaici non hanno una convenzione pubblicata (nessun
  software sceglie un soggetto): si decidono nel gruppo "oggetti", misurati sull'archivio.
- Punto 7 (indizio e campo ereditati) costruito: ogni soluzione dice da dove vengono
  (`pipeline_solutions.hint_from`, `field_from`: `card` o `sister`, ADR 0026), e le pose con indizio
  e campo propri si risolvono per prime. Punto 8 costruito: scala attesa dalla scheda contro la
  risolta, nei due versi (`solve.SCALE_TOLERANCE`), scritta con la soluzione
  (`expected_scale_arcsec_px`, `scale_disagrees`); `solve.forget` dimentica una soluzione a
  richiesta e la posa si rifa' alla passata dopo. Punto 10 costruito: focale misurata dal pixel
  della scheda e dalla scala risolta (ADR 0016, `measured_focal_mm`), e l'avviso di ASTAP
  (`WARNING=... FL=561mm`, con la virgola del sistema) tenuto com'e' in `astap_warning`. Punto 9
  (parallelo) resta da costruire.
