# Per Claude Code — Progetti v27.3–27.8

Da Claude Design, 19/10/2026. Pagina `pagine/Progetti.dc.html`, tavola `pagine/Progetti stati.dc.html` (Sistema solare, finito dalla prima scansione, Modifica, calendario su piu' mesi, oltre il 100%; telefono e desktop). Nella tavola tutto e' simulato: qui sotto cosa deve mandare l'app perche' il disegno regga, e i testi da far approvare a Marco.

## 1. Cosa deve mandare l'app

### Le notti di un progetto, col tipo di ripresa
Per ogni progetto deep sky (in corso, in attesa, fermi, finiti, anche dalla prima scansione), l'elenco delle notti in cui ha frame:
- data della notte (quella di Notti: la data della sera), sito;
- minuti integrati quella notte per il progetto;
- tipo di ripresa della notte: `larga` (banda larga), `mista` (banda larga, poi solo banda stretta), `stretta` (solo banda stretta), con la regola della Luna delle Impostazioni (v26). Senza Luna nei dati, senza fuso o senza buio: nessun tipo, la riga non lo dice.

Serve a: calendario di un mese (giorni accesi, frecce fra i mesi che hanno notti, parte dal mese dell'ultima notte), riga «{n} notti in {m} mesi», riga del giorno toccato (data, ore, ripresa) con «Apri in Notti ↗» (nella tavola apre Notti senza scegliere la notte: serve un indirizzo per la notte, da decidere).
- Domanda: la notte la decide il file (DATE-OBS spostata a mezzogiorno) come in Notti? Un progetto con frame di due siti la stessa notte: una riga o due?

### I finiti creati alla prima scansione
- Alla prima scansione, un progetto finito per ogni oggetto gia' ripreso: obiettivo = ore fatte (per filtro), setup = quello dei frame, rotazione 0 se non si sa.
- Campi: mese e anno dell'ultima notte («dalla prima scansione · agosto 2025»), segno che e' nato cosi' (`daScansione: true`).
- Domande: un oggetto ripreso con due setup diversi fa due progetti o uno? I mosaici gia' ripresi (pannelli riconosciuti dal nome o dalle coordinate) diventano un progetto a mosaico? Se l'utente poi ne fa un progetto nuovo dal Planner, il finito resta o si unisce?

### Le misure per progetto
- Tre mediane su tutti i filtri: FWHM (″ e px), eccentricita', luminosita' del cielo (SQM), piu' il numero di frame misurati («tutti i filtri · mediane di {n} frame»).
- I giudizi sono quelli di `soglie.js` (`ALsoglie.misure`): FWHM contro il campionamento del setup («non giudicabile su questo setup» quando il limite non si calcola), eccentricita', luminosita' contro il Bortle del sito.
- Per filtro e per notte restano nell'Archivio: il link «Tutte le misure, per filtro e per notte, nell'Archivio ↗» apre l'oggetto.
- Domanda: le mediane si calcolano su tutti i frame del progetto o solo su quelli tenuti (senza scarti)?

### «Ultima volta nel piano» (Sistema solare)
- I progetti del Sistema solare non hanno ore da raggiungere: niente barra ne' calendario.
- Per ognuno: nel piano di stanotte (ora d'inizio, «nel piano stanotte, 03:00») o la data dell'ultimo piano che lo conteneva («ultima volta nel piano: {data}»), «mai» se non c'e' mai stato.
- Domanda: «nel piano» vuol dire salvato o esportato per SharpCap? Proposta: esportato.

### Il piano di stanotte (deep sky)
- Per i progetti in corso: se stanotte sono nel piano, gli orari dei blocchi («nel piano stanotte · 22:45–03:15»; piu' blocchi separati da «·»). Altrimenti «prossima: {giorno} · {n} h visibili» dal Planner.

### I parametri di Rinquadra
«Rinquadra nel Planner ↗» apre il Planner sul progetto com'e', nello stato «progetto iniziato»:

`Planner.dc.html?da=progetto&p={id}&n={nome}&c={setup}&cn={nome del setup}&rot={gradi}&mos={colonne}x{righe}x{sovrapposizione %}&fatte={ore fatte}&ob={obiettivo}&fil={filtro}:{minuti},…`

- `mos` vuoto senza mosaico; `fil` per esempio `ha:480,oiii:420,sii:300` (obiettivo per filtro, in minuti).
- Il Salva del Planner aggiorna rotazione, mosaico e campo del progetto; le ore per filtro arrivano gia' scritte e non si riscrivono. Le ore fatte non cambiano.
- Domanda: cambiando rotazione o mosaico dopo frame gia' ripresi, il Planner avvisa «{ore} già riprese non conterebbero più.» (c'e' gia', stato «progetto iniziato»). L'app deve tenere le ore vecchie come «altro orientamento» o le toglie dal conto?

### Modifica
- Si scrivono: nome, setup (fra quelli di Attrezzatura), obiettivo per filtro (passi di 30 min, minimo 30). Le ore fatte non si toccano.
- Domanda: cambiare setup a un progetto con ore fatte e' permesso? Il campo cambia: va come Rinquadra (avviso) o si blocca?

### Oltre il 100%
- Ore fatte oltre l'obiettivo: anello pieno con ✓, a destra «+ {ore in piu'}», nella scheda «di {obiettivo} · + {ore in piu'}». Il progetto resta «in corso» finche' l'utente non lo segna finito (proposta «Obiettivo raggiunto. Segnarlo come finito?»).

### Cerca e ordine
- Cerca su nome e nome comune; con la ricerca i gruppi si aprono tutti. Ordine dentro i gruppi: Data (ultima notte), Ore che mancano, Nome (numeri in ordine naturale: M 8 prima di M 31).

## 2. Testi da far approvare a Marco

Gruppi e righe:
- «In corso» · «In attesa» · «Fermi» · «Finiti» · «Sistema solare»; sotto: «nei loro mesi buoni», «fuori dai mesi buoni», «mesi buoni passati senza frame», «segnati come finiti o dalla prima scansione», «Luna, pianeti e Sole, a video».
- «Mostra tutti · {n}» / «Mostra meno».
- «nel piano stanotte · 22:45–03:15», «prossima: ven 2 · 3 h visibili», «obiettivo raggiunto», «torna buono a {mese}», «fermo da {mese}», «finito il {data}», «dalla prima scansione · {mese anno}».
- «+ 10 min», «di 10 h · + 10 min».

Scheda:
- «Finito · dalla prima scansione, {mese anno}», «obiettivo = ore fatte».
- «Obiettivo raggiunto. Segnarlo come finito?» · «Segna come finito».
- Azioni: «Modifica», «Rinquadra nel Planner ↗», «Aggiungi al piano ↗», «Apri il piano ↗», «Segna come finito», «Elimina».
- Modifica: «le ore fatte restano; oggetto e inquadratura si cambiano con «Rinquadra»», «Nome», «Setup», «Obiettivo per filtro», «{ore} fatte», «niente ancora», «Salva», «Annulla».
- Le notti: «Stanotte», «nel piano · {orari}», «non nel piano», «Ultima notte», «Prossima notte», «{n} h visibili · con l'orizzonte di {sito}», «{n} notti in {m} mesi · tocca un giorno acceso», «notte ripresa per questo progetto», «Apri in Notti ↗»; ripresa: «banda larga», «banda larga, poi solo banda stretta», «solo banda stretta».
- Le misure: «tutti i filtri · mediane di {n} frame», «non giudicabile su questo setup», «Bortle 3 a Cima Ekar», «Tutte le misure, per filtro e per notte, nell'Archivio ↗», «Le misure arrivano con i primi frame.».
- Sistema solare: «Corpo», «Setup», «Mosaico», «Filtro», «Ripresa», «Durata nel piano» («pannelli × (ripresa + spostamento), dai tempi delle Impostazioni»), «Nel piano», «Ultima volta nel piano», «ultima volta nel piano: {data}», «mai», «da scrivere: frame e posa», «Apri nel Planner ↗».
- Cerca e ordine: «Cerca un progetto», «Ordine nei gruppi», «Data» · «Ore che mancano» · «Nome», «Nessun progetto col nome «…».».

Dal Planner (v27.8), carta «Salva come progetto»: «In Progetti, senza ore da raggiungere. Frame, posa e regione si scrivono nella scheda; il Piano della notte lo richiama nella linguetta Sistema solare.», «Apri in Progetti ↗», testa del modo «come il setup inquadra il corpo · si salva come progetto, in fondo».

## Dati simulati nella tavola
Progetti, ore, notti per progetto (ricavate dalle ore fatte), misure (oltre le tre mediane), 28 finiti dalla prima scansione (nomi e coordinate veri), piano di stanotte, «ultima volta nel piano».
