# Per Claude Design -- Piano della notte completo, e la Luna in tutta l'app (v26)

Da Claude Code, 19/10/2026. Questa brief **sostituisce** `design-piano-della-notte.md` e
`design-piano-della-notte-categorie.md`: e' la pagina intera, piu' una regola nuova che tocca
tutta l'app. Decisioni in `docs/adr/0013-progetti-e-piano-della-notte.md` ("Il disegno", "Le
categorie") e `docs/domini/meteo.md`. Le parole fra «» sono proposte: Marco le approva sulla
tavola. I numeri li manda l'app.

Il Planner crea i progetti; il Piano della notte decide **cosa si fa una notte**, in che ordine,
e lo esporta in un file per N.I.N.A.

## Cosa cambia rispetto alla v25

- Due **modi** per notte, «Fotografia» e «Ricerca», che non si mischiano (sez. 2).
- **Proposte automatiche** e due pulsanti, «Completa la notte» e «Rifai la notte» (sez. 3).
- Il tempo di cambio unico diventa **sette tempi** della notte (sez. 4 e 8).
- La **regola della Luna** diventa un'impostazione e vale in tutta l'app (sez. 9). Sostituisce la
  regola fissa usata in v25 (`soglie.ripresa`, 25% e 10°).
- «Dietro l'orizzonte» usa l'orizzonte del sito importato in Impostazioni (ADR 0023), non 0°;
  senza orizzonte importato, 0°.
- I testi scritti da voi in v25 restano proposte («Nessun buio stanotte: nessuna ora utile.»,
  «Togli dal piano», «Ora fissa, {ora}: non si sposta.», «Nessun evento stanotte.», i totali
  vuoti, il testo della tastiera): Marco li guarda sulla tavola. La riga degli eventi mischia
  singolare e plurale: «Dal modo Eventi del Planner: l'ora e' fissa.».

Tutto il resto della v25 resta: griglia, blocchi trascinabili, bordi, tastiera, linea «adesso»,
conferma dell'export, telefono verticale.

## 1. In testa

- Nome in barra: **«Piano della notte»** (`/piano-della-notte`), voce nel menu Altro.
- La notte: «Stanotte» di partenza, pillole per le notti dopo.
- La postazione: linguette, una per montatura (montatura · ottica · camera). Un piano per
  postazione.
- Il **modo** della postazione per quella notte: **«Fotografia» · «Ricerca»**. Due postazioni
  possono fare modi diversi la stessa notte. Cambiare modo con blocchi nel piano chiede: «Il piano
  di stanotte si svuota: cambio modo?» · «Cambia» / «Annulla».
- Sito attivo e verdetto della notte in una riga, col rimando «Meteo ↗».

## 2. I due modi

### Fotografia

Linguette **«Deep sky» · «Sistema solare»** nella colonna di sinistra. I blocchi delle due stanno
nella stessa traccia, ognuno col segno piccolo della sua categoria.

- **Deep sky**: i progetti del Planner alti stanotte. Ogni proposta: nome (oggetto · ottica ·
  camera), «5 h visibili · 4 h utili», distanza dalla Luna col giudizio della soglia delle
  Impostazioni (40°), ore mancanti per filtro («Hα 1 h 50 · OIII 4 h»). Nelle ore in cui la Luna
  vieta la banda larga (sez. 9) i filtri a banda larga sono spenti e la riga lo dice («dalle
  23:10 solo banda stretta»).
- **Sistema solare**: pianeti e Luna come nel modo Sistema solare del Planner (altezza minima,
  ADC, Macchia Rossa). **Comete**: «Aggiungi una cometa» per sigla («C/2026 A1», «12P»); riga con
  sigla, magnitudine, altezza, distanza dalla Luna; sul blocco «posizione ricalcolata per ogni
  blocco». Senza rete: «Serve la rete per la posizione della cometa.».

### Ricerca

Un **elenco solo**; sopra, i Criteri a chip **«Esopianeti · NEO · Variabili»** (si accendono e si
spengono, tutti accesi di partenza). Esopianeti, NEO e variabili si mischiano nella stessa notte.
In piu' **«Aggiungi oggetto»** per nome. Tre tipi, ognuno col suo segno:

- **Esopianeta** («WASP-12 b»): evento a ora fissa col lucchetto. Il blocco ha tre parti: base
  prima, transito, base dopo. Riga: «transito 22:41-01:12 · base 1 h prima e dopo» (convenzione
  BAA: almeno 30 min, meglio 60).
- **Variabile** («Algol»): una binaria a eclisse ha il minimo a ora fissa, segno sul blocco
  («minimo 23:58»); le altre sono blocchi brevi e flessibili.
- **NEO** («2026 TX»): blocco flessibile, «posizione dal Minor Planet Center, serve la rete».

Stato vuoto coi Criteri scelti: «Nessun oggetto di ricerca stanotte. Aggiungine uno per nome.».

### In tutti e due i modi

Sotto le proposte, **«Eventi di stanotte»**: transiti della ISS, eclissi, occultazioni del modo
Eventi del Planner, con l'ora fissa e il lucchetto. Un oggetto o un evento si trascina sulla
linea del tempo, o «Aggiungi».

## 3. Proposte automatiche e i due pulsanti

Le proposte sono **gia' calcolate** dal sito e dall'orizzonte importato: in Fotografia i progetti
alti stanotte, i pianeti, le comete aggiunte; in Ricerca i transiti visibili stanotte coi
margini, i minimi delle variabili, i NEO osservabili. Ordine delle proposte in Fotografia: prima
chi si chiude (ultime settimane nei mesi buoni), poi le ore utili, poi le ore mancanti. Nessun
punteggio.

Sopra la linea del tempo due pulsanti:
- **«Completa la notte»**: tiene i blocchi messi a mano e riempie il resto;
- **«Rifai la notte»**: ricomincia da capo.
Dopo ognuno, «Annulla» torna al piano di prima.

Come mette in fila, in una riga d'aiuto sotto i pulsanti: «Prima le ore fisse, poi chi scende
prima.». Cioe': prima gli eventi a ora fissa; poi nei buchi gli oggetti liberi, prima chi chiude
prima la sua finestra (l'oggetto da 45° a 30° a cui manca un'ora va prima di quello da 30° a 70°
tutta la notte); a pari merito l'ordine delle proposte.

Due eventi di ricerca sovrapposti: entra quello che ci sta tutto coi margini, a pari merito il piu'
alto; l'altro resta fra le proposte con «Si sovrappone a {oggetto}: escluso.».

## 4. La linea del tempo

Da tramonto ad alba, orizzontale sul desktop.

- **Fasce del cielo**: giorno, crepuscoli civile, nautico, astronomico, buio (come Meteo).
- **Luna**: curva d'altezza sottile, fase in testa; tratteggiata la parte in cui conta per la
  regola della sez. 9.
- **Meteo**: striscia sottile del verdetto ora per ora, coi colori di Meteo; senza previsione:
  «Previsione non disponibile».
- **Blocchi**, uno per bersaglio: nome, filtri e durate («Hα 2 h»), curva d'altezza dell'oggetto,
  segno del transito al meridiano («transita 01:15»).
- **I tempi della notte** come pezzi tratteggiati, nome al passaggio del mouse:
  - a inizio notte il blocco **«Avvio»**: raffreddamento + unpark;
  - fra due bersagli la fascia **«Cambio»**: puntamento e centratura + autofocus;
  - sul blocco che passa il meridiano una tacca **«Flip»** della sua durata;
  - a fine notte il blocco **«Chiusura»**: park + riscaldamento.
  Un pezzo senza valore non si disegna; riga sotto: «Scrivi i tempi in Impostazioni: {elenco dei
  mancanti}.».
- **Eventi fissi** col lucchetto: non si spostano.
- Si trascinano i bordi per allungare, il blocco per spostare.

## 5. Conflitti in rosso

Con la frase sul blocco e l'elenco sotto («{n} conflitti»):
- due blocchi sovrapposti: «Si sovrappone a {bersaglio}.»;
- sotto la soglia o dietro l'orizzonte del sito: «Sotto 30° dalle 03:10.» / «Dietro l'orizzonte
  dalle 03:10.»;
- banda larga con la Luna che la vieta (sez. 9): «Banda larga con la Luna al 62% sopra
  l'orizzonte.» (con un'altezza scelta: «sopra 10°»);
- un blocco sopra un evento fisso: «Copre il transito della ISS delle 21:14.»;
- base di un transito sotto 30 min: «Base prima del transito sotto 30 min.».
Le ore «non adatte» del meteo non sono un conflitto: la striscia le mostra e basta.

## 6. Totali ed export

Totali: «Buio 7 h 40 · pianificato 6 h 10 · avvio, cambi e chiusura 50 min · libero 40 min».

**«Esporta per N.I.N.A.»**: un file per la notte intera, per il sequencer avanzato. Riga sotto:
«Un file per la notte intera, nel sequencer avanzato di N.I.N.A.». Spento col piano vuoto. Con un
conflitto aperto chiede: «{n} conflitti: esporto lo stesso?» · «Esporta» / «Annulla»; poi
«Esportato alle 18:42».

## 7. Stati (Tweaks)

- senza sito: «Serve un sito: il piano dipende da dove sei.»;
- nessun progetto (Fotografia): «Nessun progetto ancora.» · «Apri il Planner»;
- nessun progetto alto stanotte: «Nessun progetto sopra 30° stanotte.»;
- Ricerca senza oggetti coi Criteri scelti (testo in sez. 2);
- notte senza buio: «Nessun buio» e le fasce che ci sono;
- piano vuoto: la linea del tempo con le fasce e «Trascina qui un progetto.»;
- tempi della notte non scritti (riga della sez. 4);
- piano con conflitti; piano esportato;
- un piano Fotografia con due progetti (uno che scende, uno alto tutta la notte) dopo «Completa
  la notte»;
- un piano Ricerca con un esopianeta a inizio sera, un NEO a mezzanotte e mezza, una variabile
  dopo.

## 8. Impostazioni, sezione «Planner»

Via la riga «Tempo di cambio fra due bersagli». Al suo posto un gruppo **«Tempi della notte»**,
sette righe in minuti, vuote, fonte «nessuna convenzione: scegli tu»:

«Raffreddamento della camera» · «Unpark» · «Puntamento e centratura» · «Autofocus» · «Meridian
flip» · «Park» · «Riscaldamento della camera».

Riga sotto il gruppo: «Scrivi tempi larghi: il margine sta dentro il numero.». Valori d'esempio
solo nei Tweaks, mai di partenza: 15, 1, 3, 3, 4, 1, 10.

## 9. La Luna, in tutta l'app

Oggi la regola della Luna per la banda larga e' fissa: buona fino al 25% illuminata, «al limite»
fino al 50%, oltre «consigliata banda stretta», e conta solo quando la Luna e' sopra l'orizzonte.
Marco: **diventa un'impostazione**, perche' sotto un cielo buio anche una Luna sottile disturba,
in citta' molto meno.

**Impostazioni**, un gruppo nuovo **«Luna»** (sezione propria, prima di «Planner»), tre righe:

| riga | partenza | fonte |
|---|---|---|
| «Banda larga buona fino a» | 25% | «regola diffusa fra chi riprende» |
| «Banda larga al limite fino a» | 50% | «nessuna convenzione: scegli tu» |
| «La Luna conta sopra» | «l'orizzonte» (0°) | «Nautical Almanac: Luna sorta» |

Riga d'aiuto: «Sotto un cielo buio la Luna disturba prima: abbassa le percentuali.». La seconda
percentuale non puo' stare sotto la prima: il campo lo dice («Deve essere almeno {prima}%.»). La
riga «Distanza dalla Luna» (40°) resta nella sezione Planner.

**Ovunque la regola compare, legge queste tre righe**, e le frasi portano i numeri scelti:
- **Meteo**: la riga della Luna nel verdetto («Luna al 55% dalle 23 · banda larga fino alle
  23»), «banda larga al limite», «consigliata banda stretta»;
- **Dashboard**: la carta della Luna e le ore utili dei progetti;
- **Planner**: proposte e filtri spenti;
- **Piano della notte**: proposte, curva della Luna (sez. 4), conflitto (sez. 5).

Nei Tweaks un'impostazione diversa (10%, 25%, sopra 10°) e le stesse pagine che cambiano.

## 10. Telefono

Linea del tempo verticale (le ore scendono). In testa il selettore dei modi; le linguette o i
Criteri in cima al foglio delle proposte (dal basso); i due pulsanti sotto la linea. Avvio,
cambi e chiusura come fasce nella linea, stesso tratteggio. Blocchi da toccare per modificarli;
bersagli da 44 px. Impostazioni «Luna» e «Tempi della notte» come le altre sezioni.

## Fuori

- Occultazioni asteroidali, supernove, campagne AAVSO: dopo, non si disegnano.
- Nessun comando all'hardware: cupola, tetto e sicurezza restano a N.I.N.A.
- Nessuna scelta durante la notte: il piano e' fisso, N.I.N.A. lo esegue.
- La *Lorentzian moon avoidance*: nessuna fonte primaria.

## Foglio di stile

Nei commenti di `astrolog.css` i numeri col punto, come a schermo: «46,4843 N» -> «46.4843 N»
(`--campo-coordinata`), «Bortle 4 (20,8)» -> «Bortle 4 (20.8)» (blocco BORTLE).

CHANGELOG e DECISIONI come al solito.
