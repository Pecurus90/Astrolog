# Per Claude Design -- Piano della notte: categorie, tempi, correzioni (v25)

Da Claude Code, 19/10/2026. Controllata la v25: pagina quasi tutta fatta. Qui tre correzioni e
il ridisegno a categorie deciso con Marco (`docs/adr/0013-progetti-e-piano-della-notte.md`,
"Le categorie"). Le parole fra «» sono proposte: Marco le approva sulla tavola.

## Correzioni della v25

1. **Regola della Luna.** Riga 307 usa `soglie.ripresa` (25% e 10°). La regola del Piano e'
   quella di Meteo: banda larga spenta solo **oltre il 50%** illuminata e **sopra l'orizzonte**
   (-0.833°). Fra 25 e 50% la banda larga resta accesa («al limite»). Frase: «Banda larga con la
   Luna al 62% sopra l'orizzonte.».
2. **«Dietro l'orizzonte»** (riga 305): vale l'orizzonte del sito importato in Impostazioni
   (ADR 0023), non 0°. Senza orizzonte importato, 0°.
3. **Testi nuovi**: «Nessun buio stanotte: nessuna ora utile.», «Togli dal piano», «Ora fissa,
   {ora}: non si sposta.», «Nessun evento stanotte.», i totali vuoti, il testo della tastiera.
   Restano come proposte; Marco li guarda sulla tavola. La riga degli eventi mischia singolare e
   plurale: «Dal modo Eventi del Planner: l'ora e' fissa.».

## 1. Due modi, che non si mischiano

In testa, accanto alla postazione, un selettore **«Fotografia» · «Ricerca»**: ogni postazione,
ogni notte, fa l'uno o l'altro (Marco). Due postazioni possono fare modi diversi la stessa notte.

- **Fotografia**: linguette **«Deep sky» · «Sistema solare»** nella colonna di sinistra; i blocchi
  delle due stanno nella stessa traccia, ognuno col segno piccolo della sua categoria.
- **Ricerca**: un **elenco solo**, coi Criteri a chip sopra («Esopianeti · NEO · Variabili»):
  esopianeti, NEO e variabili si mischiano nella stessa notte.

«Eventi di stanotte» (ISS, eclissi, occultazioni) resta sotto in tutti e due i modi.

Cambiare modo con blocchi nel piano chiede: «Il piano di stanotte si svuota: cambio modo?» ·
«Cambia» / «Annulla».

## 1b. Proposte automatiche e i due pulsanti

In tutti e due i modi le proposte sono **gia' calcolate** dal sito e dall'orizzonte importato: in
Fotografia i progetti del Planner alti stanotte (piu' pianeti e comete); in Ricerca i transiti
visibili stanotte coi margini, i minimi delle variabili, i NEO osservabili.

Sopra la linea del tempo due pulsanti:
- **«Completa la notte»**: tiene i blocchi messi a mano e riempie il resto;
- **«Rifai la notte»**: ricomincia da capo.
Dopo ognuno, «Annulla» per tornare al piano di prima.

Come mette in fila (scrivetelo in una riga d'aiuto sotto i pulsanti): prima gli eventi a ora
fissa; poi nei buchi gli oggetti liberi, **prima chi scende prima** (l'oggetto da 45° a 30° a
cui manca un'ora va prima di quello da 30° a 70° tutta la notte); a pari merito l'ordine delle
proposte. Proposta di riga: «Prima le ore fisse, poi chi scende prima.».

Due eventi di ricerca sovrapposti: entra quello che ci sta tutto coi margini, a pari merito il
piu' alto; l'altro resta fra le proposte con «Si sovrappone a {oggetto}: escluso.».

Nei Tweaks: un piano Fotografia con due progetti (uno che scende, uno alto tutta la notte) e un
piano Ricerca con esopianeta a inizio sera, NEO a mezzanotte e mezza, variabile dopo.

### Deep sky

Le proposte di oggi (progetti dal Planner).

### Sistema solare

- Pianeti e Luna come nel modo Sistema solare del Planner (altezza minima, ADC, Macchia Rossa).
- **Comete**: «Aggiungi una cometa» per sigla («C/2026 A1», «12P»). Riga: sigla, magnitudine,
  altezza, distanza dalla Luna. Sul blocco: «posizione ricalcolata per ogni blocco». Senza rete:
  «Serve la rete per la posizione della cometa.».

### Ricerca

Elenco unico delle proposte, piu' **«Aggiungi oggetto»** (per nome) e trascinamento sulla linea
del tempo. Tre tipi, ognuno col suo segno:

- **Esopianeta** (es. «WASP-12 b»): evento a ora fissa col lucchetto. Il blocco ha tre parti:
  base prima, transito, base dopo. Riga: «transito 22:41-01:12 · base 1 h prima e dopo».
  Conflitto se una base scende sotto 30 min: «Base prima del transito sotto 30 min.» (convenzione
  BAA: almeno 30, meglio 60).
- **Variabile** (es. «Algol»): una binaria a eclisse ha il minimo a ora fissa, segno sul blocco
  («minimo 23:58»); le altre sono blocchi brevi e flessibili.
- **NEO** (es. «2026 TX»): blocco flessibile, «posizione dal Minor Planet Center, serve la rete».

Stato vuoto (nessuna proposta coi Criteri scelti): «Nessun oggetto di ricerca stanotte.
Aggiungine uno per nome.».

## 2. I tempi sulla linea del tempo

Il tempo di cambio unico diventa **una fascia fatta di pezzi**, ognuno col suo tratteggio e il
nome al passaggio del mouse:

- inizio notte, blocco **«Avvio»**: raffreddamento + unpark;
- fra due bersagli, fascia **«Cambio»**: puntamento e centratura + autofocus;
- sul blocco che passa il meridiano, una tacca **«Flip»** della sua durata;
- fine notte, blocco **«Chiusura»**: park + riscaldamento.

Un pezzo senza valore non si disegna; riga sotto: «Scrivi i tempi in Impostazioni: {elenco dei
mancanti}.». I totali: «Buio 7 h 40 · pianificato 6 h 10 · avvio, cambi e chiusura 50 min ·
libero 40 min».

## 3. Impostazioni, sezione «Planner»

Al posto di «Tempo di cambio fra due bersagli», un gruppo **«Tempi della notte»**, sette righe in
minuti, vuote, fonte «nessuna convenzione: scegli tu»:

«Raffreddamento della camera» · «Unpark» · «Puntamento e centratura» · «Autofocus» · «Meridian
flip» · «Park» · «Riscaldamento della camera».

Riga sotto il gruppo: «Scrivi tempi larghi: il margine sta dentro il numero.». Valori d'esempio
nei Tweaks (non di partenza): 15, 1, 3, 3, 4, 1, 10.

## 4. Telefono

Il selettore dei modi in testa; linguette o Criteri in cima al foglio delle proposte; i due
pulsanti sotto la linea verticale. Avvio, cambi e chiusura come fasce nella linea
verticale, stesso tratteggio.

## Fuori

- Occultazioni asteroidali, supernove, campagne AAVSO: dopo, non si disegnano.
- Nessun comando all'hardware; nessuna scelta automatica durante la notte (il piano e' fisso,
  N.I.N.A. lo esegue).

CHANGELOG e DECISIONI come al solito.
