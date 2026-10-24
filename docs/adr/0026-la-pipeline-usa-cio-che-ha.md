# 0026 -- La pipeline usa cio' che ha gia': nome del file, posizione nell'header, effemeridi, notte

**Stato:** accettata, 20/10/2026 (Marco, dal check di salute). Costruito solo il centro WCS come
indizio (`pipeline/sky.py`, `pipeline/solve.py`); il resto in `docs/piano.json`.
Superato in parte da ADR 0033: XISF si ignorano (ADR 0031); Voyager e SGP fuori finche' Marco non li
aggiunge con un file vero (ADR 0029). Montature: regola rifatta da Marco il 24/10/2026 (sotto).

## Contesto

Check di salute del 20/10/2026. La pipeline decide bene quando l'header parla; e' cieca su fonti
che possiede. Misurato sul DB di `old/` (10.390 light; la pipeline nuova non ha ancora
scansionato l'archivio vero):
- ASIAIR, 542 frame: OBJECT 0, SITELAT 0, RA/DEC 0; WCS (CRVAL, CD) in 537; nome
  `Light_<oggetto>_<esposizione>_Bin1_...` in 542 su 542;
- N.I.N.A., 9.457 frame: OBJECT, RA/DEC, SITELAT/LONG nel 100 %;
- 579 frame senza coordinate del sito: oggi vanno al sito di casa senza domanda
  (`spine/group.py`); 579 frame con `TELESCOP = EQMod Mount`, una montatura;
- pianeti, Luna, comete: riconosciuti solo dal nome (`vocab/moving.py`); un frame lunare
  finirebbe nel cono come campo stellare.

Vincoli che restano: il nome e' un indizio, il cielo decide (`old/docs/architettura.md`:
"rileva + conferma"); la spina non tocca la rete, l'arricchimento online e' a richiesta, in
cache, `urllib`, niente `astroquery` (`docs/domini/catalogo.md`).

## Decisione

- **Nome del file**: il prefisso `Light/Dark/Flat/Bias` da' il tipo ai frame `unknown`; il
  nome dell'oggetto si **propone** al gruppo senza nome ("M 101?"). Il cielo vince sempre.
  Formati da verificare su nomi veri di ogni software.
- **Sito dalla notte**: un frame senza coordinate prende il sito degli altri frame della stessa
  notte, se ne hanno uno solo; altrimenti la casa, come oggi.
- **Posizione dell'header come partenza del solve** (Marco, 20/10/2026): il centro WCS
  (ASIAIR, riscritture PixInsight) fa da indizio come RA/DEC per N.I.N.A. Il cielo resta quello <!-- software-ok -->
  di ASTAP (`spine/solve.py`).
- **Pianeti e Luna nel campo**: con le effemeridi di astropy gia' in casa, se un corpo cade nel
  WCS all'ora del frame l'oggetto e' il corpo. Offline.
- **Comete e asteroidi dal cielo e dalla data**: elementi orbitali del Minor Planet Center
  (`CometEls.txt`, elenco dei numerati), scaricati a richiesta e poi offline, propagati da noi
  senza dipendenze nuove (ADR 0019).
- **Sesame (CDS)** per un OBJECT fuori catalogo e senza cielo: propone le coordinate in Da
  confermare. A richiesta, in cache, fuori dalla spina.
- **Montature** (Marco, 24/10/2026; supera "un vocabolario di montature per ogni software"):
  nessuna lista di nomi. Si legge l'header (ASIAIR: `TELESCOP` e' la montatura), il resto si chiede una volta.
- **Prima, i numeri veri**: una scansione con la pipeline nuova su una copia parziale
  dell'archivio di Marco (alcune notti N.I.N.A. e ASIAIR, nello scratch), per contare Da
  confermare per motivo.

**Scartati**: astrometry.net come secondo solver (GPL, indici da GB, contro ADR 0003); tipo di
frame dalle statistiche dell'immagine (le calibrazioni non entrano in archivio, nessuna
convenzione per le soglie). XISF: deciso, si ignora (ADR 0031). **Da decidere con Marco**: il testo
per i file di altri formati trovati e per i FITS compressi che ASTAP non apre.

## Conseguenze

- Ogni indizio dice da dove viene (nome, notte, header), come le altre provenienze.
- Servono header e nomi veri di Voyager e SGP prima di dare per buona una regola su di loro.
