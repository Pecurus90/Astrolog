# 0019 -- Sole e Sistema solare entrano in Archivio a mano, il deep sky resta automatico

**Stato:** accettata, 17/10/2026 (Marco). Nessun codice ancora. Ordine dei pezzi: disegno della linguetta e di "Aggiungi oggetto"; comete,
asteroidi e NEO dai FITS di oggi (orbite MPC); effemeridi di Sole e pianeti e le metriche; lettore
SER per percorso; log di FireCapture e SharpCap, con log veri; foto finale e campi a mano; meteo <!-- software-ok: ADR 0019 -->
storico e attivita' solare per data. Prima: quali altri programmi planetari scrivono un log.

## Contesto

Il disegno nuovo porta il Sole in Dashboard (meteo di giorno, calendario con attivita' solare).
Chi riprende Sole, Luna e pianeti non produce FITS: video (SER, AVI), uno stack, una foto finale.
Tiene poche riprese scelte a mano, non cartelle da scandire: una scansione passerebbe su decine
di GB di video scartati. Le Notti non c'entrano: il Sole si riprende di giorno.

## Decisione

- **Archivio a tre linguette: Deep sky, Sole, Sistema solare.** Un archivio solo: il genere e'
  un campo dell'oggetto, siti, attrezzatura e meteo restano comuni.
- **Deep sky non cambia**: cartelle, FITS, riconoscimento automatico come oggi.
- **Comete, asteroidi e NEO in FITS passano dalla catena di oggi**: ASTAP risolve il campo,
  l'identificazione li riconosce dalle orbite del Minor Planet Center, e l'oggetto compare nella
  linguetta Sistema solare. Il gesto a mano non li duplica.
- **Fuori dal deep sky si entra con "Aggiungi oggetto"**: si sceglie il tipo (Sole, pianeta,
  Luna, cometa, asteroide, altro), poi una o piu' fonti:
  - un **file SER indicato per percorso**, letto dove sta e mai copiato: header (camera,
    telescopio, osservatore, data e ora UTC, frame, bit) e, se ci sono, gli istanti dei frame;
  - il **log del programma di ripresa** (FireCapture e SharpCap lo scrivono; altri da <!-- software-ok -->
    verificare su file veri);
  - la **foto finale**, col nome alla convenzione WinJUPOS quando c'e' (data, ora, oggetto);
  - i **campi a mano**.
- **Precedenza delle fonti**: header del SER, poi log, poi nome della foto, poi la mano. Ogni
  campo dice da dove viene; la mano corregge sempre.
- **Obbligatori: tipo, oggetto, data, sito.** L'ora e' fortemente consigliata: senza, cio' che ne
  dipende (altezza, meridiano centrale, rotazione, dispersione) dice "non disponibile", e arriva
  solo cio' che vale per il giorno (macchie, Kp, fase della Luna). Per il Sole il filtro (H-alfa,
  luce bianca, CaK) e' facoltativo.
- **Piu' file dello stesso oggetto nella stessa data sono una sessione**, come nel deep sky.
- **Dopo l'inserimento calcola chi scrive**: effemeridi locali (altezza, massa d'aria,
  diametro, fase, meridiano centrale, coordinate di Carrington, colongitudine e librazione della
  Luna), meteo storico e attivita' solare scaricati per la data, scritti una volta.

## Conseguenze

- I software supportati oggi sono quattro (CLAUDE.md): un lettore di log planetari li allarga, e
  ognuno entra solo con log veri di quel programma.
- Servono le effemeridi di pianeti, Sole e comete (tappa 6), il catalogo delle orbite MPC e le
  fonti dell'attivita' solare; ogni soglia o formula nuova (es. il tempo massimo prima che la
  rotazione sfochi) si prende da una fonte pubblica o si decide con Marco.
- Parole nuove (la ripresa planetaria, la giornata del Sole) si decidono con Marco, nel glossario.
- Linguetta e modulo "Aggiungi oggetto" vengono dal disegno (ADR 0012) prima del codice.
