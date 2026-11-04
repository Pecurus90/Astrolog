# 0043 -- I cicli caldi delle misure compilati con numba; i Mac Intel escono dai bersagli

**Stato:** accettata, 4/11/2026 (Marco). Passo 26.57.

## Contesto

Il passo 26.57 chiede che una misura per frame non sia piu' lenta di Image Analysis: 3,3 s su <!-- software-ok -->
un frame mono da 26 MP, 4,2 s a colori col debayer. Con solo numpy, sul banco del 26.47
servivano 5,3 s a mono e 11,7 s a colori. Il limite era la banda di memoria: ogni passata di
numpy scrive un array grande quanto il frame. Le prove su M51 sono arrivate allo stesso numero
entro 2e-13: biweight 0,38 s con numpy e 0,004 s compilato, starlet 0,42 s e 0,12 s.

numba (BSD-2, con llvmlite BSD-2) compila quei cicli. Dalla versione 0.63 numba e llvmlite non
pubblicano piu' la ruota per i Mac Intel. L'ultima che la pubblica, la 0.62, non regge numpy 2.5.

## Decisione

- I cicli caldi di measure_frame sono kernel numba: seriali e senza GIL, divisi sui core dai
  thread di `pipeline/cores.py` (`compiled`, `inlined`, `in_parts`). Il threading layer di numba
  non si usa, perche' sul Mac non c'e' OpenMP.
- Un kernel rifa' le operazioni di numpy nello stesso tipo e nello stesso ordine, NaN compresi.
  Fa eccezione la somma che numpy fa in float32 (`np.std` di un float32): il kernel la fa in
  float64. Sul banco lo scarto e' al massimo 6e-7 relativo e nessun conteggio cambia.
- I bersagli diventano quattro: Windows x64, Mac Apple Silicon, Linux amd64 e Linux arm64.
  `tools/ruote.py` li controlla.

## Conseguenze

- Chi ha un Mac Intel non installa AstroLog. Costo scelto da Marco, 4/11/2026: Apple non vende
  Mac Intel dal 2020.
- Il pacchetto cresce di circa 150 MB, soprattutto per llvmlite. Ogni kernel si compila alla
  prima chiamata e poi resta nella cache su disco.
- numpy si aggiorna solo quando lo regge numba (oggi numpy < 2.6).
- Da verificare quando nascera' il sidecar dell'ADR 0004: `cache=True` cerca il sorgente `.py`
  del kernel. Un pacchetto congelato senza i `.py` fallisce all'import ("no locator
  available"), quindi va incluso il sorgente o va puntato `NUMBA_CACHE_DIR`.
