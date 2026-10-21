# Il piano

Ora una cosa, Dopo in ordine, Piu' avanti cio' che arriva con una tappa (ADR 0027). Si riscrive,
non si appende: una cosa fatta sparisce, la storia e' git. Le decisioni stanno nei contratti
(`domini/`) e negli ADR (`adr/`), le idee di Marco in [`idee.md`](idee.md), i difetti bloccati da
fuori nelle Issue con l'etichetta `bloccato`.

## Ora

**La pipeline riprogettata da zero** (Marco, 22/10/2026): scansione, lettura, attribuzione e
normalizzazione si riscrivono in una casa nuova da una mappa concettuale decisa prima del codice,
uno strato alla volta, affiancate alla vecchia finche' non la sostituiscono. Verificati N.I.N.A. e
ASIAIR, piu' la convenzione SBIG (ADR 0029). Fatto il primo strato: `backend/astrolog/pipeline/scanner.py` trova i FITS e
estrae solo le chiavi che scrivono N.I.N.A. e ASIAIR (Marco: nient'altro). Il passo dopo lo
sceglie Marco, uno alla volta. Le Issue #14-#24 aspettano: molte le chiude la pipeline nuova.

## Dopo

1. **Le ricette** (ADR 0028): `rivedi` e `ripara` mandano ogni rilievo a `/ripara`, a una Issue
   `bloccato` o a un "no" col motivo; nascono `salute`, `audit`, `smista`, `porta-tavola`,
   `rilascia`; l'audit settimanale su GitHub (`/install-github-app`, Marco).
2. **I documenti**: le brief risposte di `handoff/` si cancellano; `domini/spina.md` si divide per
   stadio; gli ADR sopra 100 righe si riducono alla decisione, il dettaglio va nel contratto;
   CLAUDE.md, ricette e skill parlano delle case nuove.
3. **La squadra** (ADR 0025): agenti `collaudatore` e `verificatore-disegno`, modo `pagina` dello
   `sviluppatore`, `tools/glossario.py`, `tools/contratti.py`, **Supera** obbligatoria.
4. **Mutazione solo sui file cambiati** dall'ultimo verde: oggi le notti sono tutte rosse, shard
   tagliati a 280 minuti. Oggi guarda solo `backend/astrolog`: `tools` dopo; il frontend vuole
   uno strumento nuovo (una dipendenza, la decide Marco).
5. **Scansione di una copia parziale** dell'archivio di Marco (notti N.I.N.A. e ASIAIR, nello
   scratch): Da confermare per motivo, i numeri per ADR 0026.
6. **Pulizia prima del porting**: soglie di nuvole e Luna in una casa (`weather/verdict.py`,
   `weather/judge.py`); `Site` dataclass nel meteo al posto dei `Mapping[str, Any]`; un `StrEnum`
   per i tipi di strumento prima di ADR 0021; controlli del foglio sul prefisso `al-`
   (`tools/controlli_veste.py`); le domande all'API in `frontend/src/api/` (doppioni
   `Confermare.tsx` / `revisione.ts`, `["sites"]` in due case); `solve._in_order` senza `set` nel
   ciclo; test della Luna calcolati una volta; job `lento` che cade per rumore; CI Windows 30
   minuti contro 8; Node 22/24 in CI; chiavi i18n morte.
7. **Un `/salute` finale** (ADR 0028), poi il porting.
8. **Il porting del disegno nuovo**: il backend di ADR 0020 (dopo il riordino v32 di Design, Marco
   20/10/2026) e di ADR 0021, poi foglio e componenti, poi le pagine, una tavola alla volta (ADR
   0025). Delle pagine restano le misure dei frame nelle Notti, il modale dell'oggetto (lo stesso
   per notte, oggetto e libreria), l'etichetta dei progetti nell'Archivio, la Casa per ultima.
9. **Pipeline piu' intelligente** (ADR 0026): nome del file, sito dalla notte, posizione
   dell'header come partenza del solve, pianeti e Luna nel campo, comete e asteroidi da MPC,
   Sesame, montature.
10. **L'uso vero di Marco** sul suo archivio, coi difetti riparati.
11. **`measure`** (ADR 0007): contratto e posto nei contratti dei moduli, poi eccentricita', fondo
    cielo, tilt. Dopo una spina che dice il vero: su difetti muti misurerebbe dati che mentono.
    Con lui: la provenienza di `frame_metrics` (oggi `astap`, poi `sep`) e la qualita' chiesta e
    non arrivata, che oggi non si richiede.
12. **Le effemeridi che mancano** (orari del Sole come numeri, ore di buio, quanto sale un oggetto
    stanotte, dalla cava `old/backend/astrolog/ephemeris/`), poi **Planner e Progetti** (ADR 0013,
    0023): prima i DSO, poi esopianeti, variabili e AAVSO, poi supernove, per ultimi comete e NEO;
    poi la Carta del cielo (ADR 0005).
13. **Le statistiche** (ADR 0024), la pagina da decidere con Marco.
14. **Il pacchetto** (ADR 0003, 0004): prototipo desktop prima che costi; immagine Docker con
    ASTAP, multi-arch su runner arm64 nativi; installer e updater firmati su Windows e Mac.
15. **Il mobile**, per ultimo, a desktop funzionante: tablet e telefono, su ogni pagina.

**Dopo cinque o sei funzioni nuove si misura il metodo** (ADR 0025, *La misura del metodo*).

## Piu' avanti

Cose nominate dal metodo che non esistono ancora, con la tappa che le porta. Passata la tappa
senza di loro, la riga lo dice (scaduta).

| cosa | con |
|---|---|
| `THIRD_PARTY.md` generato (`pip-licenses`, `license-checker`): dipendenze, licenze, crediti (ESA/Gaia/DPAC, ASTAP, Aladin, HYG, OpenNGC, Stellarium, SIMBAD) | il pacchetto |
| in CI `npm audit` e controllo licenze (`--no-audit` in `ci.yml` lo spegne) | il pacchetto |
| `tools/gen_changelog.py` e `release.yml` su tag `v*` (versione in `astrolog/__init__.py`) | il pacchetto |
| la pagina Diagnostica col bottone "copia" (ADR 0008) | il pacchetto |
| build dell'immagine amd64 e arm64 in CI (runner `ubuntu-24.04-arm`) | il pacchetto |
| la misura del solver su un NAS arm64 vero (1-2 GB di RAM) | il pacchetto |
| lo stack delle metriche misurato su arm64 (ADR 0007), con `old/backend/astrolog/misura.py` e i suoi 8 test | `measure` |
| header veri di Voyager e SGP in `backend/tests/header/`, anonimizzati, prima della correzione che li fa passare | un file vero |
| pochi FITS veri con licenza e un database ASTAP piccolo (D05), per i test `lento` del solver in CI | un file vero |
| rifare cio' che si ricava dal vocabolario quando cambia (`spine/header_asks.py`, il software normalizzato), e dirlo all'avvio | il primo rilascio |
| la regola della Luna nelle Impostazioni (due gradini e altezza, `domini/meteo.md`) | il porting |
