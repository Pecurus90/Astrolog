# 0029 -- Due programmi verificati e una convenzione: N.I.N.A., ASIAIR, SBIG

**Stato:** accettata, 22/10/2026 (Marco). Supera "Software supportati: quattro" di CLAUDE.md.

## Contesto

L'app diceva di supportare N.I.N.A., ASIAIR, Voyager e SGP, ma file veri esistono solo per i primi
due (l'archivio di Marco, il corpus in `backend/tests/header/`). Per Voyager e SGP le regole venivano
da header postati sui forum, senza una lista ufficiale delle chiavi: segno della longitudine, chiavi
del programma e binning restavano ipotesi (Issue #23). La revisione del 21/10 ha chiesto regole da
fonti vere, non da memoria.

## Decisione

- **Verificati: N.I.N.A. e ASIAIR.** Per loro valgono gli alias, le stranezze dichiarate (la
  montatura che l'ASIAIR scrive in `TELESCOP`) e le prove sugli header veri.
- **Lettura comune: la convenzione SBIG** (SBFITSEXT 1.0), che quasi tutti i programmi seguono:
  `DATE-OBS`, `EXPTIME`, `IMAGETYP`, `FILTER`, `XPIXSZ` col binning, `CALSTAT`. Un file di un altro
  programma passa da qui: cio' che la convenzione dice si legge, cio' che non si sa si chiede.
- **Nessun alias, nessuna regola propria per altri programmi** (Voyager, SGP, MaxIm e gli altri): <!-- software-ok -->
  se i loro file funzionano con la lettura comune, meglio; non si scrive niente per loro finche'
  Marco non decide di aggiungerli, e un programma si aggiunge solo con un suo file vero.
- Resta SharpCap Pro solo per l'export del Sistema solare (ADR 0013). <!-- software-ok -->

## Conseguenze

- Il codice che riconosce Voyager e SGP (`vocab/software.py`, `fits/frame_type.py`, i profili di
  `tests/synthetic.py`, circa 60 righe fra codice e prove) esce nella fase "interpretare un file da
  solo" del progetto della pipeline; nella stessa fase il controllo `foreign-software` li blocca.
- La Issue #23 resta come porta per il giorno in cui arriva un file vero, non come lavoro.
- **Pipeline nuova: niente lettura comune** (Marco, 22/10/2026, terzo audit). Un file che non e'
  di N.I.N.A. ne' ASIAIR si salta come "non supportato". Misura: nell'archivio di prova gli unici
  file di altri programmi (398) sono elaborati da PixInsight con `IMAGETYP LIGHT` e le chiavi <!-- software-ok -->
  SBIG: la lettura comune li avrebbe contati come pose. La lettura SBIG resta solo nella vecchia,
  finche' c'e'.
