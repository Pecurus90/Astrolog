# Per Claude Design -- correzioni dopo il controllo della v18.1

Da Claude Code, 18/10/2026. Ho controllato pagine, componenti, `soglie.js`, `dati.js`, `tema.js`
e i documenti contro le decisioni (ADR 0020, 0021, 0022, risposte, glossario, testi dell'app).
**Le regole ci sono tutte**: soglie delle misure, campi dell'attrezzatura, Luna e ripresa, Da
confermare, primo avvio; nessuna traccia del V50. Restano un difetto che blocca, testi da
allineare e due avvertenze mancanti. Non ho visto le tavole "stati" di Meteo, Notti, Dashboard,
Primo avvio, Riepilogo e Da confermare, né `Telefono.dc.html`: le controllo alla prossima.

## 1. Blocca: la luminosità del cielo in `MisureFrame`

Il componente vero (quello che entra in Notti e Archivio) mostra "SQM 18.9" anche per le camere a
colori senza controllo del bias, e i mono non hanno mai "senza bias". La regola giusta c'è solo
nella tavola `Misure dei frame`. Portatela nel componente:
- **camera a colori senza bias**: niente SQM, «serve il bias della camera» e «Bias (ADU) in
  Attrezzatura ↗»;
- **mono senza bias**: il numero con «senza bias»; togliete «È una stima.» (non deciso);
- il giudizio contro il Bortle del sito vale anche per le **camere a colori** (oggi solo L e
  senza filtro).

## 2. Due avvertenze decise e mancanti (Notti, curva della notte)

- «**nessun frame L o a colori in questa notte**» quando la notte non ha frame adatti;
- «**il valore cambia anche con la direzione del cielo**» accanto alla curva.

## 3. Testi da allineare all'app

| dove | oggi | deve dire |
|---|---|---|
| `MisureFrame` | «la stessa camera, lo stesso guadagno e la stessa posa» | «… la stessa esposizione» («posa» non si usa) |
| `Misure dei frame`, SNR | «si confronta solo dentro la stessa notte» | «si confronta solo dentro la stessa notte e lo stesso oggetto, mai fra camere» |
| `Riepilogo`, `Archivio` | tipo, costellazione «non si sa» / «Non si sa» | «Tipo non disponibile», «Costellazione non disponibile» |
| `Riepilogo`, corredo | «Tutti i pezzi» / «Meno pezzi» | «**Tutti gli strumenti**» / «**Meno strumenti**» (Marco) |
| `tema.js` (e Sistema, pillole) | filtro `ignoto: 'non si sa'` | «Filtro non indicato» |
| `Cerca` | «senza tempo» | «senza durata» |
| `Archivio` | «seeing 1,6″», «diametro 46,2″» | «1.6″», «46.2″»: secondi d'arco col punto |
| `Da confermare` | «RA 305,2 Dec 40,6» | «RA 305.2 Dec 40.6» |
| `dati.js` | «1,61″ per pixel», «0,97″ per pixel» | «1.61″/px» |
| `Archivio`, vuoto | «L'archivio è vuoto» / «Gli oggetti arrivano dai frame delle cartelle delle riprese.» | «Archivio vuoto» / «Aggiungi le cartelle dei file e avvia la scansione.» |
| `Dashboard`, Luna | «culmina 07:30 · 68°» | «sale fino a 68° alle 07:30» («culmina» non si usa per la Luna) |
| `Dashboard` | «Qui vedrai quanto manca e quando riprenderlo.», «Il posto da cui riprendi: …» | senza «tu» discorsivo, tono neutro come «Nessun progetto ancora.» |
| `Dashboard`, legenda del calendario | «almeno 4 ore di banda larga, cioè con la Luna sotto il 25 % o sotto 10°» | «Notti buone per la banda larga: Luna sotto il {pct}%, o almeno {ore} ore di buio senza Luna» (testo dell'app) |
| `Notti` | «37 frame aspettano una tua risposta» · «Vai a Da confermare» | «{n} frame da confermare» · «Apri Da confermare» |
| `Notti` | «112 frame non sanno il sito» | «{n} frame senza sito» · «Apri le Impostazioni» |
| `Notti` | «Senza il sito non si sa a che notte appartengono.» · «Scegli il sito» | «Sito mancante» / «I frame sono stati letti, ma senza un sito non possono essere assegnati a una notte.» · «Aggiungi sito» |
| `Notti` | «Le notti arrivano man mano che i frame trovano la loro. Non serve fare niente.» | «Le notti compaiono man mano che i frame vengono letti.» |
| `Notti` | «Non si può sapere» / «Il sito non ha un fuso riconoscibile: senza, la notte non ha ore.» | «Non disponibile» / «Fuso orario del sito non riconosciuto.» |
| `Notti`, altri stati | «Le notti non si possono leggere»; «Questa notte non c'è più nell'archivio» / «I suoi frame sono stati tolti o spostati.»; «Mostra altre 20»; «Le notti nascono dai frame delle cartelle delle riprese.» | «Notti non disponibili»; «Notte non trovata» / «I frame sono stati rimossi o spostati.»; «Carica altre»; «Le notti vengono create dai frame delle cartelle aggiunte.» |
| `Menu`, scansione | «lettura delle intestazioni»; «La cartella D:\Astro non risponde: il disco è scollegato?» | «Lettura dei file»; «Lettura di una cartella non completata. Controlla il disco e riprova.» |
| `Primo avvio` | «Ricerca non riuscita: il servizio non ha risposto.» in una riga | titolo «Ricerca non riuscita», testo «Il servizio non ha risposto.» |

## 4. Attrezzatura

- «Riduttore (vuoto: dai file)» e «Guida (vuoto: dai file)»: solo «Riduttore» e «Guida». I file
  non li dicono mai (si scelgono a mano), come i distanziali.
- Backfocus **senza tolleranza**: solo la differenza («+0,0 mm»), nessuna parola. Oggi esce
  «esatto» anche senza tolleranza.
- Sotto la Luna del campo disegnato: «**Luna piena, per misura**» (Marco, 17/10).

## 5. Cose non decise da togliere

- Meteo, giorno del Sole: «Seeing migliore · col Sole sopra 15°». Il numero non ha fonte; il
  giudizio del giorno del Sole si decide più avanti con Marco.
- Testa del Riepilogo: «oggetto finito». Basta «oggetto».
- Nome delle produzioni con l'anno davanti («2026 · Askar FRA400 + …»): la produzione è oggetto +
  ottica + camera. L'anno, se serve, va accanto come dato.
- «la Luna scende sotto 10°»: le parole sono «la Luna tramonta» e «la Luna sale sopra 10°».
- Dati d'esempio coerenti: «Notte in quota» è Askar FRA400 + ZWO ASI2600MM Pro a 1.94″/px; oggi
  `dati.js` lo chiama «Rifrattore 80/480 · ASI2600MM» a 1.61″/px e «Casa leggero» è 3.82″/px
  contro 0.97″/px del Newton 200/800. Allineate i nomi e le scale fra `dati.js` e i componenti.

## 6. Approvati da Marco

- «fuoco: servono 10 frame della notte», «si giudica con 10 frame della notte», «stelle troppo
  piccole per una camera a colori», «senza Bortle del sito», «come il Bortle del sito / più chiaro
  del Bortle del sito».
- «Limite del corredo 4.1″: diffrazione dell'apertura da 28 mm.» quando a decidere è la
  diffrazione.
- «SQM 19.2» resta così (Marco).
- `soglie.js`: il commento della tabella Bortle dice «Wikipedia»; i numeri sono quelli di ASTAP
  (ClearDarkSky): correggete solo il commento.

CHANGELOG e DECISIONI come al solito.
