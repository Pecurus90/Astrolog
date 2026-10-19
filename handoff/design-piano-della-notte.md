# Per Claude Design -- il Piano della notte

Da Claude Code, 19/10/2026. Pagina nuova, l'ultima del Planner. Decisioni in
`docs/adr/0013-progetti-e-piano-della-notte.md` (sezione "Il disegno") e
`docs/adr/0023-planner-e-progetti.md`. Le parole fra «» sono proposte: Marco le approva sulla
tavola. I numeri li manda l'app.

Il Planner crea i progetti; qui si decide **cosa si fa una notte**, in che ordine, e si esporta un
file per N.I.N.A.

## 1. In testa

- Nome in barra: **«Piano della notte»** (`/piano-della-notte`), accanto a Planner e Progetti.
- La notte: «Stanotte» di partenza, si sceglie un'altra data.
- La postazione: un piano per montatura e setup. Con due postazioni, due linguette della stessa
  notte.
- Il sito attivo e il verdetto della notte in una riga, col rimando «Meteo ↗».

## 2. Cosa si fa stanotte (le proposte)

Una colonna a sinistra con i progetti che stanotte sono alti, nell'ordine gia' deciso: **prima chi
si chiude** (ultime settimane nei mesi buoni), **poi le ore utili** stanotte, **poi le ore
mancanti**. Nessun punteggio.

Ogni proposta: nome del progetto (oggetto · ottica · camera), «5 h visibili · 4 h utili», distanza
dalla Luna col giudizio della soglia delle Impostazioni (40°), ore mancanti per filtro («Hα 3 h ·
OIII 4 h»). Con la Luna che vieta la banda larga (regola di Meteo: oltre il 50% e sopra
l'orizzonte), i filtri a banda larga sono spenti in quelle ore e la riga lo dice («dalle 23 solo
banda stretta»).

Sotto, **«Eventi di stanotte»**: transiti della ISS, eclissi, occultazioni del modo Eventi del
Planner, con l'ora fissa.

Un progetto o un evento si trascina sulla linea del tempo (o «Aggiungi»).

## 3. La linea del tempo

Da tramonto ad alba, orizzontale sul desktop.

- **Fasce del cielo**: giorno, crepuscoli civile, nautico, astronomico, buio (le stesse di Meteo).
- **Luna**: curva d'altezza sottile, fase in testa.
- **Meteo**: una striscia sottile del verdetto ora per ora (buona, incerta, non adatta), coi colori
  di Meteo; senza previsione: «Previsione non disponibile».
- **Blocchi**, uno per bersaglio: nome, filtro e durata («Hα 2 h»), piu' filtri in fila nello
  stesso blocco. Dentro il blocco la curva d'altezza dell'oggetto e il segno del transito
  («transita 01:15»: il cambio lato al meridiano lo fa N.I.N.A.).
- **Tempo di cambio** fra due blocchi (puntare, centrare, mettere a fuoco): una fascia tratteggiata
  della durata scritta in Impostazioni. Senza valore: niente fascia e una riga «Scrivi il tempo
  dei cambi in Impostazioni.».
- **Eventi fissi** con un lucchetto: non si spostano.
- Si trascinano i bordi per allungare, il blocco per spostare.

**Conflitti in rosso**, con la frase sul blocco:
- due blocchi sovrapposti: «Si sovrappone a {bersaglio}.»;
- bersaglio sotto la soglia o dietro l'orizzonte: «Sotto 30° dalle 03:10.» / «Dietro l'orizzonte
  dalle 03:10.»;
- banda larga con la Luna che la vieta: «Banda larga con la Luna al 72% sopra l'orizzonte.»;
- un blocco sopra un evento fisso: «Copre il transito della ISS delle 21:14.».
Le ore «non adatte» del meteo non sono un conflitto: la striscia le mostra e basta.

In fondo i totali: «Buio 7 h 40 · pianificato 6 h 50 · libero 50 min».

## 4. Export

Pulsante **«Esporta per N.I.N.A.»**: un file per tutta la notte, per il sequencer avanzato. Riga
sotto: «Un file per la notte intera, nel sequencer avanzato di N.I.N.A.». Con un conflitto aperto il
pulsante resta attivo, ma prima chiede: «{n} conflitti: esporto lo stesso?» · «Esporta» /
«Annulla».

## 5. Stati (Tweaks)

- senza sito: «Serve un sito: il piano dipende da dove sei.»;
- nessun progetto: «Nessun progetto ancora.» · «Apri il Planner»;
- nessun progetto alto stanotte: «Nessun progetto sopra 30° stanotte.»;
- notte senza buio (estate, latitudini alte): «Nessun buio» e le fasce che ci sono;
- piano vuoto (nessun blocco): la linea del tempo con le fasce e «Trascina qui un progetto.»;
- piano con conflitti; piano esportato («Esportato alle 18:42»).

## 6. Impostazioni

Nella sezione «Planner», una riga in piu': «Tempo di cambio fra due bersagli», vuota, fonte
«nessuna convenzione: scegli tu».

## Telefono

Linea del tempo verticale (le ore scendono), proposte in un foglio dal basso, blocchi da toccare
per modificarli; bersagli da 44 px.

## Fuori

- Variabili, esopianeti, NEO, comete, supernove: vengono dopo (ADR 0013, l'ordine). Non si
  disegnano.
- Nessun comando all'hardware: cupola, tetto e sicurezza restano a N.I.N.A.
- La *Lorentzian moon avoidance*: nessuna fonte primaria; vale la regola della Luna gia' decisa.

CHANGELOG e DECISIONI come al solito.
