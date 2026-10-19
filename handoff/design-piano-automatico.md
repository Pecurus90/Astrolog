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

## Tweaks

- un piano Deep sky dopo «Completa il piano»: un oggetto che scende (subito), uno che sale
  (aspetta il transito), un blocco che divide banda stretta con la Luna e larga dopo;
- un piano Sistema solare: Giove centrato sulla Macchia Rossa, Saturno sul seeing migliore,
  Luna a mosaico al punto piu' alto;
- senza chiave Meteoblue: tutti al transito, riga «al transito».

CHANGELOG e DECISIONI come al solito.
