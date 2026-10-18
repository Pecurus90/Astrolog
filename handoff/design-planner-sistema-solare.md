# Per Claude Design -- Planner, modo «Sistema solare»

Da Claude Code, 18/10/2026. Il secondo modo del Planner, accanto a «Cielo profondo»
(`handoff/design-planner-progetti.md` § 2.6). Decisioni in `docs/adr/0023-planner-e-progetti.md`,
sezione "Planetario e solare". Le parole fra «» sono proposte: Marco le approva sulla tavola.

## 1. Cos'e'

- **Simulazione, non progetto**: Mercurio, Venere, Marte, Giove, Saturno, Urano, Nettuno, Luna,
  Sole. Si vede come il corredo inquadra il corpo, e per Luna e Sole il mosaico. Non si salva.
- Nessun file esportato (Marco): la ripresa la guidano programmi come SharpCap o Moon Panorama <!-- software-ok -->
  Maker; AstroLog non comanda la montatura e i video (SER, AVI) non entrano nell'archivio.
- Il corredo scelto nel modo «Cielo profondo» resta; la lista dei sensori apre su **Planetario**
  (su **Solare** col Sole). Barlow e riduttore (fattore) cambiano la scala subito.

## 2. La pagina

- In alto: il corpo (nove pulsanti o un selettore), la **data e l'ora** (partenza: adesso, o
  stanotte se e' giorno) e il sito.
- Al centro, grande come la carta del cielo: **il corpo con sopra il rettangolo del sensore**,
  ruotabile 0-180° come nel cielo profondo.
- Accanto, i numeri (sotto, l'esempio).

### 2.1 Luna

- Fondo: la **mappa LRO della NASA** (100 m/px) dentro Aladin, **zoomabile** fino al singolo
  cratere. Al clic, il nome ufficiale («Copernicus»). Credito: «LROC/ASU, NASA».
- Sopra: la **fase** di quella data (parte in ombra scurita, terminatore come linea), la Luna
  girata come si vede quella notte (librazione e asse).
- **Mosaico**: interruttore «Mosaico», sovrapposizione % (partenza 20). Due modi di scegliere:
  «Luna intera» (tessere solo sulla parte illuminata) o «Una zona», trascinando un rettangolo.
  Tessere numerate; accanto il numero di tessere e l'**ordine consigliato**: prima quelle sul
  terminatore («Il terminatore cambia in circa 30 minuti: riprendilo per primo.»).
- Riga fissa: «Le tessere sono fissate sulla Luna: la Luna si sposta di mezzo grado l'ora.»
- Avvertenza sulla rotazione: «Rotazione della camera entro 10°, o restano buchi fra le tessere.»

### 2.2 Sole

- Fondo: **l'immagine di oggi**, a scelta «Luce bianca» (SDO, le macchie) o «Hα» (GONG, le
  protuberanze). Credito: «Courtesy of NASA/SDO and the AIA, EVE, and HMI science teams» oppure
  «GONG, NISP/NSO/AURA/NSF with NOAA». Senza rete: «Immagine del Sole non disponibile senza rete»
  e un disco grigio in scala.
- Mosaico come per la Luna (disco intero o una zona).
- **Fascia fissa, mai chiudibile**: «Solo con un filtro solare a tutta apertura, davanti
  all'ottica. Mai filtri da oculare. Copri il cercatore.»

### 2.3 Pianeti

- Una **foto in scala** per pianeta (Hubble OPAL per Giove, Saturno, Urano, Nettuno; NASA per gli
  altri), col credito sotto, con le parole che la fonte chiede (segnaposto «Credito: NASA, ESA»).
- Fase disegnata per Mercurio e Venere; anelli di Saturno con l'inclinazione della data.
- Riga: «Foto per la scala: l'aspetto della notte cambia.»
- Niente mosaico (un pianeta sta sempre nel campo).
- Accanto: «prossima opposizione {data} · {diametro}» (Mercurio e Venere: «massima elongazione»),
  che porta la data li'.

## 3. I numeri accanto

Diametro apparente e in pixel, scala, campo, rapporto focale del corredo e **rapporto focale
critico** del filtro scelto (2 × pixel / lunghezza d'onda; senza filtro 400 nm). I giudizi per
riga sono in `handoff/design-risposta-giudizi-planner.md`. Per Luna e Sole anche «km per pixel»
sulla Luna e il numero di tessere.

**Esempi coerenti** (calcolati):
- Giove, C9.25 (2350 mm, 235 mm) con barlow 1,5×, pixel 2.9 µm, Giove a 44.8″: «44.8″ · 264 px»,
  «0.17″/px», «f/15 · critico f/14.5 senza filtro (400 nm)»; con Hα «critico f/8.8 (656 nm)».
- Luna, C11 (2800 mm) con sensore da 9.0 µm, 1608 × 1104 px: «0.663″/px», campo «17.8′ × 12.2′»,
  «1.24 km per pixel», Luna piena intera (31′) con sovrapposizione 20 %: **2 × 3 = 6 tessere**.

## 4. Prossime opposizioni (per i dati d'esempio)

Da JPL Horizons, 18/10/2026: Urano 26/11/2026 3.8″ · Giove 11/2/2027 45.2″ · Marte 20/2/2027
13.8″ · Saturno 18/10/2027 20.0″, anelli aperti col lato sud verso di noi.

CHANGELOG e DECISIONI come al solito.
