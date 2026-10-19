# Per Claude Design -- risposta: come sceglie il piano automatico (v27.1)

Da Claude Code, 19/10/2026, alla vostra «come sceglie il piano automatico». Deciso con Marco e
verificato sulle convenzioni (Target Scheduler di N.I.N.A., Telescope Live, Sky & Telescope,
Omegon, Sky at Night): `docs/adr/0013-progetti-e-piano-della-notte.md`, "Come sceglie il piano
automatico". Le parole fra «» sono proposte: Marco le approva sulla tavola.

## Nomi dei pulsanti

**«Completa il piano» / «Rifai il piano»**, uguali di notte e di giorno. Non «sequenza»: nel
glossario e' la parola di N.I.N.A. e per questa pagina e' vietata.

## Regole fisse, nessuna impostazione

Non si sceglie la regola: una per mondo, scritta in una riga d'aiuto sotto i pulsanti.

### Deep sky e Ricerca

Riga d'aiuto: **«Prima le ore fisse, poi chi scende prima, vicino al suo transito.»**

1. Prima gli eventi a ora fissa.
2. Poi, fra chi passa altezza minima, durata minima e Luna, **chi scende prima**; a pari merito
   l'ordine delle proposte.
3. Ogni blocco si sposta **il piu' vicino possibile al suo transito**, se c'e' spazio: un oggetto
   che sale aspetta, uno che scende va subito.
4. Un blocco non e' mai piu' corto della durata minima (Impostazioni, 1 h): meno cambi.
5. Dentro il blocco **la banda larga va nelle ore senza Luna, la stretta in quelle con la Luna**
   (oggi la larga si spegne soltanto: ora si sposta).
6. Le ore «non adatte» del meteo si evitano finche' c'e' altro posto; non diventano un conflitto.

### Sistema solare

Riga d'aiuto: **«Ogni corpo nell'ora col seeing migliore sopra la soglia, vicino al transito.»**

1. Fra le ore sopra l'altezza minima, quelle con la **classe di seeing migliore** (le classi di
   Meteo: buono, incerto); a pari merito la piu' vicina al transito.
2. Senza previsione del seeing (nessuna chiave Meteoblue, o oltre la previsione): **al transito**.
3. **Giove**: se la Macchia Rossa passa al meridiano centrale mentre Giove e' sopra la soglia, il
   blocco si centra su di lei; vince sul seeing.
4. **Luna a mosaico**: piu' alta possibile; i pannelli partono dal terminatore (gia' nel
   progetto).
5. **Sole** (Giorno): come i pianeti.
6. Meteo: come sopra.

## Cosa mostra la proposta (il perche' dell'ora)

Sul blocco messo dal piano automatico, una riga piccola col motivo:
- «al transito 01:15»;
- «seeing buono 02:00» (e «previsione del seeing, non una misura» al passaggio del mouse);
- «Macchia Rossa al meridiano 23:40»;
- «prima che scenda: sotto 30° alle 23:10»;
- «Hα con la Luna, RGB dopo le 01:30».
Un blocco spostato a mano perde la riga.

## Impostazioni › Planner: quattro righe da Target Scheduler

Marco ha voluto il confronto con la documentazione di Target Scheduler: queste quattro si
prendono (ADR 0013, "Dalla documentazione di Target Scheduler").

1. **Via «Distanza dalla Luna 40°»**. Al suo posto due righe, ognuna con due numeri:
   - «Luna, banda larga»: «120° a Luna piena · meta' a 14 giorni», fonte «ACP, via Target
     Scheduler»;
   - «Luna, banda stretta»: «60° a Luna piena · meta' a 7 giorni», fonte «Target Scheduler».
   Accanto, una curva piccola: la distanza richiesta lungo il mese lunare, col segno di stanotte
   («stanotte servono 45°»). Riga d'aiuto: «Piu' la Luna e' piena, piu' il bersaglio deve stare
   lontano.».
2. **«Crepuscolo ammesso»**: banda larga «buio astronomico» (fissa); banda stretta a scelta
   «buio astronomico» (partenza) o «crepuscolo nautico».
3. **«Altezza massima»**: vuota = spenta. Riga: «Per montature altazimutali o setup che allo zenit
   toccano.».
4. La regola della Luna per fase (25% · 50%, sezione «Luna») **resta** per il verdetto della notte
   in Meteo e Dashboard; nel Planner e nel Piano il giudizio sul bersaglio usa le due righe sopra.

**Dove si vede**:
- Planner e proposte: la pillola diventa «Luna a 74° · servono 45°» (giudizio per la banda del
  filtro); con un filtro largo e uno stretto, due giudizi.
- Piano: la banda larga sta solo nelle ore in cui la distanza basta; con «crepuscolo nautico»
  scelto, i blocchi a banda stretta possono cominciare nella fascia nautica (la fascia resta
  disegnata). Conflitto: «Luna a 38°: in banda larga servono 45°.».
- Fuori dal buio permesso: «Hα dal crepuscolo nautico, 20:05».

## Tweaks

- un piano Deep sky dopo «Completa il piano»: un oggetto che scende (subito), uno che sale
  (aspetta il transito), un blocco che divide banda stretta con la Luna e larga dopo;
- un piano Sistema solare: Giove centrato sulla Macchia Rossa, Saturno sul seeing migliore,
  Luna a mosaico al punto piu' alto;
- senza chiave Meteoblue: tutti al transito, riga «al transito»;
- Luna al primo quarto e Luna piena: la curva delle Impostazioni e i giudizi che cambiano;
- banda stretta col crepuscolo nautico acceso.

CHANGELOG e DECISIONI come al solito.
