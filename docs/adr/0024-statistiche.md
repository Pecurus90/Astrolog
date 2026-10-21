# 0024 -- Statistiche: i confronti nel tempo

**Stato:** accettata, 20/10/2026 (Marco). Riprende il contratto vecchio
(`old/docs/domini/statistiche.md`, regole misurate sull'archivio di Marco) e lo allarga a
stagioni, filtri, cielo del sito e calendario.

## Contesto

Glossario: `/statistiche` = "i confronti nel tempo: stagioni, setup, filtri, qualita'". Ricerca
del 20/10/2026 su app e forum:
- ricorrono l'esposizione per mese e anno (N.I.N.A. Session Analysis,
  ideviceapps.de/NINAImageAnalysisHandbook/history; Observatory 2.2,
  codeobsession.com/news/2026/07/15/observatory-2.2), per filtro, bersaglio e attrezzatura
  (Observatory, TheAstroImagingPlanner su github.com/gshau), e le notti serene per mese e anno
  (Stargazers Lounge topic 348989, forum BAA "2024 how was it for you");
- nessuna convenzione su cosa sia una "notte riuscita", nessun nome per il tasso di frame
  tenuti, nessun amatore che corregga la FWHM per la massa d'aria (pratica professionale: ESO,
  VATT astro-ph/0406495, modello di seeing di Rubin).

## Decisione

- **Base del contratto vecchio** (Marco): unita' = **notte x setup**; qualita' come punto per
  notte con la **banda dei quartili** (sotto 4 misure niente banda); volumi come barra per notte e
  **cumulato**; due anni si sovrappongono sul **giorno dell'anno**, mai sulla data; il progresso
  si legge come banda che si stringe. Buchi come buchi, col perche'; nessuna interpolazione.
  Cambi di setup marcati sulla serie.
- **In testa all'anno: notti buone sfruttate** (Marco): delle notti con qualita' da 70 (ADR
  0020) al sito, in quante sei uscito: «18 su 31». Accanto notti, ore integrate, frame, coi delta
  sull'anno di confronto (di partenza il precedente), e la **resa del buio** (ore integrate / ore
  di buio delle notti in cui sei uscito, contratto vecchio).
  - Serve il meteo storico di **ogni** notte al sito, non solo di quelle con frame: oggi
    `weather/history.py` chiede solo le notti in `nights`. Open-Meteo Archive (ERA5) e' gratuito
    dal 1940; una chiamata copre un anno. Si chiede dal primo frame del sito in poi.
  - Un sito per volta, di partenza quello di casa: le notti buone sono di un posto.
- **Qualita' senza un fattore** (Marco, vale anche per il Meteo; scritto nell'ADR 0020): i
  suoi punti vanno agli altri in proporzione, e accanto si dice quale manca («senza seeing»).
  Lo storico ERA5 non ha seeing: le notti prima dell'app si giudicano cosi'.
- **Stagioni meteorologiche** (Marco): mesi interi, inverno = dicembre, gennaio, febbraio, e cosi'
  via. NOAA le usa per confrontare statistiche fra anni
  (ncei.noaa.gov/news/meteorological-versus-astronomical-seasons). L'inverno porta il dicembre
  dell'anno prima.
- **Griglia mesi x anni** (Marco): righe gli anni, colonne i 12 mesi, sotto la media dei mesi e
  le quattro stagioni. Una misura alla volta, da un selettore:
  - notti buone e notti uscite (meteo storico e tue notti);
  - ore integrate;
  - FWHM mediana allo zenit, in arcsec (ADR 0022), coi quartili;
  - cielo: SQM dai frame L, senza filtro e a colori (ADR 0022; Luna sotto -5° separata da Luna
    su) e seeing storico (solo da quando l'app archivia la previsione);
  - le altre misure dei frame (Marco, 20/10/2026): HFD allo zenit, eccentricita'; e la qualita'
    della notte dal meteo (ADR 0020). Mediana del mese. Stelle e fondo cielo, prima in elenco,
    escono (Marco sulla tavola, v31.3): dipendono da posa, filtro e oggetto. Scelta a vista:
    griglia o una linea per anno.
    Il setup lo sceglie l'utente: uno, oppure «Tutti» = tutti insieme (Marco, 20/10/2026), e la
    pagina avverte che in px FWHM e HFD cambiano da un setup all'altro.
- **Capacita'**: FWHM e HFD allo zenit (ADR 0022, le due unita'), eccentricita' (senza
  correzione). **SNR fuori**: "SNR fra oggetti diversi: mai" (ADR 0022), e notti diverse sono
  oggetti diversi. Scelta di metodo.
- **Confronta setup** (Marco, 20/10/2026): due setup scelti, sovrapposti sul giorno dell'anno,
  FWHM in ″ (in px dipende dalla scala; `frame_wcs.scale_arcsec_px`).
- **Seeing e qualita' su tutte le notti** col meteo (il cielo del sito); misure dei frame solo
  sulle notti uscite. Scelta di metodo.
- **Per filtro**: ore per filtro nell'anno, barre impilate, il filtro con piu' ore in basso e il
  totale scritto (le barre impilate si confrontano solo sulla base: Cleveland & McGill 1984,
  service-manual.ons.gov.uk/data-visualisation/chart-types/stacked-bar-charts).
- **Per setup**: ore, frame, oggetti e FWHM mediana allo zenit di ogni setup, a parita' di
  altezza (contratto vecchio). Il tipo di oggetti prevalente esce (Marco sulla tavola, v31.3).
- **Cielo del sito**: SQM per sito, mese e anno; Luna sotto -5° separata da Luna su; curva media
  per ora della notte (Marco, 18/10/2026). Niente stima per i filtri stretti: la luce del cielo ha righe (sodio,
  mercurio, LED, ossigeno a 557 e 630 nm) che un filtro da pochi nm prende o manca.
- **Calendario delle notti** (Marco): un quadretto per notte, pieno piu' scuro con piu' ore
  integrate, gradini a 2, 4 e 6 ore (Marco, 20/10/2026: nessuna convenzione); un contorno sulle **notti buone in cui non sei uscito**. Il colore non e' l'unico
  segno (WCAG 1.4.1): numero e parola al passaggio o al tocco.
- **Non si fa** (contratto vecchio): nessuno scarto di frame, nessuna classifica fra oggetti,
  nessun grafico senza una domanda, nessun voto d'insieme, nessuna correlazione fra qualita' dei
  frame e meteo.

## Conseguenze

- `docs/domini/statistiche.md` nasce quando si costruisce, da questo ADR e dal contratto vecchio.
- Il backend scrive un aggregato per notte x setup e le celle della griglia; la pagina legge.
- Lo storico meteo si allarga a tutte le notti del sito (Open-Meteo Archive).
- Dipende da `measure` (ADR 0022) per FWHM, HFD, eccentricita' e SQM: prima di `measure` la
  pagina mostra volumi, notti buone e calendario, e le qualita' dicono perche' mancano.
