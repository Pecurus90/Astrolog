# 0046 -- Sole, Luna e pianeti con Skyfield sulla DE421

**Stato:** accettata, 20/11/2026 (Marco, scelta del 20/11 sul passo 6.9, Issue #87). I FITS restano
su astropy.

## Contesto

Le effemeridi passavano da astropy (`get_body`, `get_sun`, `AltAz`, modello incorporato del
sistema solare). Erano il costo piu' grosso della suite e della Nightly: il calendario della Luna
e le notti chiedono migliaia di posizioni, e i mutanti dello shard `rest-0` costavano 113
ore-processo (87 dopo 561a8753), contro le ~8 di una notte.

Misure del 20/11/2026 (due mesi a 5 minuti, quattro siti, riferimento DE421):

| strada | Luna | Sole | errore Luna |
|---|---|---|---|
| astropy, modello incorporato | 3,9 s | 1,4 s | 9,6" |
| Skyfield + DE421 | 0,29 s | 0,27 s | riferimento |
| PyEphem | 0,15 s | 0,08 s | 4,6", superata per il suo autore |
| erfa diretto | 0,38 s | 0,36 s | 22" |

Scartate anche una spline su griglia rada (fino a 1,6 gradi vicino allo zenit) e
`ErfaAstromInterpolator` di astropy (nessun guadagno).

## Decisione

- **Skyfield (MIT) sulla DE421 del JPL da `skyfield-data` (MIT, ruota da 17 MB).** Il file si
  apre una volta per processo, in sola lettura, dal percorso della ruota (`importlib.resources`),
  mai con `get_skyfield_data_path`, che avvisa per un altro file della ruota scaduto. La scala dei
  tempi e' quella incorporata in Skyfield: niente file, niente rete.
- **Una casa sola: `ephemeris/bodies.py`.** Ogni altezza, fase e frame passa da `observed`
  (apparente: tempo luce, aberrazione, deflessione) o da `astrometric` (senza aberrazione, per la
  separazione Luna-centro del frame). Altezze geometriche, senza rifrazione: la rifrazione sta
  nella soglia `RISESET_DEG`. Giove e Saturno sono baricentri: la DE421 non ha altro.
- **Copertura 1899-2053.** Fuori, Skyfield solleva. Le date che vengono da un header passano da
  `bodies.covers` prima del conto: un frame fuori resta senza Luna e Sole, una notte fuori senza
  fase, e le altre si calcolano. Prima, astropy rispondeva per qualunque anno.
- **Tolleranze scritte** contro astropy, che resta come oracolo indipendente nei test
  (`test_ephemeris_against_astropy.py`): orari di Sole e Luna entro 5 s (misurati 0,23 e 2,4),
  lune nuove e piene entro 20 s (misurati 11,7), altezze entro 30" (misurati 3,1 e 9,7),
  distanza della Luna entro 15 km (misurati 10,0), illuminazione entro 0,1 punti.
- **astropy resta per i FITS.** Il disarmo del suo download passa da `ephemeris/__init__.py` a
  `fits/header_coords.py`, l'unico modulo di produzione che ne usa le coordinate.

## Conseguenze

- Una dipendenza in piu' (`skyfield`, con `jplephem` e `sgp4`, tutte MIT e con ruota per i quattro
  bersagli) e 17 MB nella ruota. La pipeline nuova non porta piu' astropy nemmeno attraverso le
  effemeridi: cade l'eccezione `pipeline.sky_measure -> ephemeris.frames` di import-linter.
- A schermo: un orario di sorgere, tramonto o fase puo' cambiare di un minuto quando cade a
  cavallo dell'arrotondamento.
- Nel 2053 la DE421 finisce: servira' un'altra effemeride (DE440 da `skyfield-data` o simile).
- Il contratto di import-linter non vede dentro Skyfield, che sa scaricare: contro la rete regge
  la prova a interprete nuovo e socket rotto.
