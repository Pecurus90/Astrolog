Per Claude Design -- Riordino prima del porting (brief v1)
Da Claude Code, 20/10/2026. Il disegno di AstroLog e' finito: Marco ha approvato tutte le pagine, fino alle Statistiche v31.8. Da qui il progetto di Design diventa la fonte da cui Claude Code porta tutto nel codice vero (React + TypeScript, un foglio di stile copiato com'e'). Questa brief chiede un giro solo di riordino, fatto bene, prima dell'import. Non si ridisegna niente: l'aspetto e i comportamenti approvati restano identici, pixel per pixel.

Ho fatto un giro profondo su tutto il progetto (lessico, decisioni, convenzioni, codice). Quello che serve e' qui sotto, in ordine d'importanza.

Come lavorare
Prima le catture. Prima di toccare qualcosa, catturate ogni pagina e ogni stato dei Tweaks nei due modi (chiaro, scuro), desktop e telefono, in screenshots/prima-riordino/. Alla fine rifate le stesse catture in screenshots/dopo-riordino/: devono essere uguali, salvo le correzioni elencate nella sez. 6. Ogni differenza non voluta e' un difetto.
Una pagina alla volta, nell'ordine della sez. 7. Finita una pagina: catture, console pulita, contrasto, poi la successiva.
Riusare prima di creare. Prima di scrivere una pillola, una carta, una finestra, un campo, si cerca se esiste gia' in componenti/ o nel foglio. Un componente nuovo solo se manca, e solo alla seconda volta che serve.
Nessun testo nuovo. Le parole restano quelle approvate, salvo le correzioni della sez. 6. Se una parola sembra sbagliata, si scrive in DECISIONI come domanda, non si cambia.
Nessuna soglia nuova. I numeri stanno in soglie.js con la loro fonte; se ne serve uno che non c'e', domanda.
CHANGELOG: una versione v32 -- Riordino, con l'elenco di cosa e' uscito e cosa e' stato unificato. DECISIONI: una sezione v32.
1. Un foglio di stile unico, usato da tutte le pagine (il punto piu' importante)
Oggi le pagine non usano nessun foglio: zero class="al-…" nelle 13 pagine vive, tutto in style= inline coi colori di AL.tema(). pagine/astrolog.css (prefisso al-) e' fermo alla v17 e lo carica solo il Foglio. Per il porting questo non va: il codice vero usa classi da un foglio solo, e un nostro controllo confronta il foglio del codice con quello che consegnate.

pagine/astrolog.css diventa il foglio completo di tutte le pagine: token (colori dei due modi e dei cinque accenti, caratteri, misure, raggi, ombre, durate), poi i componenti, poi le pagine. Prefisso al-, nomi in italiano come oggi, BEM come oggi (al-carta__titolo, al-pillola--buona).
Ogni pagina e ogni componente usa le classi; style= inline solo per valori che vengono dai dati (una larghezza in %, la posizione di un punto su un grafico, il colore di un filtro).
Nessun colore esadecimale nelle pagine: oggi Planner 63, PlannerSolare 30, Statistiche 13, Dashboard 9, Meteo 7. Servono token nuovi almeno per: il fondo del cielo (#05060a in Planner, Progetti, PlannerSolare), i colori dei setup a confronto (Statistiche r.373 ricopia t.pal), Sole e Luna disegnati (Dashboard r.514-515), la linea della Luna (#8a8474 in Attrezzatura r.80 = AL.LUNA.line).
Le classi mancanti da aggiungere: Planner, Progetti, Piano della notte, Impostazioni, Statistiche, Cerca, le carte dell'Archivio.
Le classi mai usate escono, dopo aver controllato: al-finestra*, al-filtri*, al-ripresa*, al-chiusura*, al-sfoglia*, quelle di Da confermare e Attrezzatura, al-tendina, al-tabella-filtri, al-riquadro, al-sensore*, al-navtel -- oppure diventano usate, che e' meglio, quando la sez. 2 le riporta in vita.
Nessun nome di classe con «corredo» (al-corredo-carta -> al-setup-carta): la parola e' «setup».
Il foglio porta in testa la sua versione (v32) e, accanto a ogni token, il contrasto misurato come fate gia'.
Numeri nei commenti col punto (46.4843 N, 20.8), come nel resto.
2. Componenti: riusare, unificare, aggiungere solo i mancanti
Oggi i 23 componenti sono tutti vivi, ma molte pagine rifanno a mano le stesse cose. Da unificare (righe delle copie che ho letto, contate):

Segmentato e linguette: rifatti a mano con role=tablist/radiogroup in Piano della notte (8: r.29, 30, 36, 40, 48, 49, 63), Impostazioni (7: r.19, 69, 94, 111, 203, 232, 253), Progetti (4), Planner (4), Notti (r.109), Archivio (pista del telefono e foglio «Vista e ordine»). Tutti con PillolaScelta forma="segmentato", o un componente Linguette se le linguette di pagina sono una cosa diversa (decidetelo voi, una volta, e scrivetelo).
Finestre: role=dialog a mano in Piano (r.32), Progetti (r.31), Planner (r.19, r.283), Archivio «Aggiungi oggetto». Ricalcano 1:1 .al-finestra e .al-campo. Serve un componente Finestra (titolo, corpo, gesti in fondo, Esc, fuoco intrappolato, foglio dal basso sul telefono) e tutte lo usano.
Campi e tendine: <input> a mano in Planner (33), Impostazioni (19), Primo avvio (8); <select> a mano in Statistiche (r.18, 29, 102), Planner (r.174-175), PlannerSolare (6). Tutti con Modulo (campo, tendina, errore sotto, unita' a destra) o le sue classi.
Bottoni: border-radius:999px inline 61 volte nel Piano, 55 nel Planner, 41 in Impostazioni; in Archivio «+ Aggiungi oggetto», «Mostra altri 20», «Annulla/Aggiungi». Un componente o una classe al-bottone con le sue varianti (pieno, contorno, testo, piccolo, pericolo).
Quartili: la scatola dei quartili ridisegnata in Misure dei frame (Archivio · produzione), MisureFrame e Statistiche. Un componente Quartili (mediana, banda, baffi, valore al passaggio).
Pillole dei giudizi: fatte a mano in PlannerEventi (GJ) e Misure dei frame (segno «?»). Tutte con Pillola.
Il riquadro al passaggio (titolo e righe etichetta · valore, v31.4): un componente Riquadro usato da tutti i grafici, non solo dalle Statistiche.
Il caricatore alPronto() (6 righe) incollato in 13 pagine e almeno 5 componenti, e la tabella L = tel ? {…} : {…} col calcolo del formato in ogni pagina: in un file solo (componenti/pagina.js o dentro tema.js), importato.
Piano della notte e Progetti usano solo Telaio, Carta e Luna/CalendarioNotti: dopo i punti 1-7 devono usare Pillola, PillolaScelta, Avviso, Finestra, Modulo come le altre pagine.
Consegna in piu': docs/COMPONENTI.md, l'elenco che mi serve per portarli senza doppioni. Per ogni componente: nome, a cosa serve, parametri (nome, tipo, valori, partenza), stati, le classi del foglio che usa, le pagine che lo usano, e cosa non deve fare (logica: la pagina non calcola, i numeri arrivano dall'app). In fondo l'elenco dei token.

3. Codice morto e file superati
Da togliere (controllato che nessuno li apra; se uno li usa, ditelo in DECISIONI):

File: Meteo v4.dc.html (nessuno lo apre); docs/proposte/ (11 file: il CHANGELOG v8, v14, v15 dice gia' che sono usciti); le due copie in piu' di support.js (radice, pagine/, componenti/: una sola); screenshots/ di lavoro vecchie (tenete solo prima/dopo del riordino); i docs/per-claude-code-*.md gia' risposti (11) in docs/archivio/.
old/ (sistema vecchio, astrolog.css v38 col prefisso as-, foglio/, mattoni/): esce dopo che il foglio al- copre tutto. Il nostro codice oggi copia old/astrolog.css: passiamo al foglio nuovo al porting, quindi non serve piu'.
soglie.js: verdetto, oreSerene, okta, intervallo, lunaPartenza (v29, superati dal punteggio; un loro commento lo dice); le opzioni dei Tweaks della Luna di prima («25% · 50% · orizzonte», «10% · 25% · sopra 10°»).
dati.js: archivio (non lo usa nessuno). dati-statistiche.js: stelle, fondo, tipo per notte (usciti dalla pagina, v31.3); in Statistiche r.550 il calcolo di tipo e tb.
Meteo: pesaT («Pesa accanto: …»), calcolato e mai mostrato.
Tweaks e commenti con «corredo»: «corredo piu' usato», «Corredi», «limite del corredo».
Restano, perche' in sospeso: PUNTI_GIORNO con «Sole basso» (il giudizio del giorno del Sole si decide quando si costruisce il Sole), puntoNotte, larghePassate.
4. Quattro sezioni nuove in Impostazioni (le prevedono i contratti; Marco le vuole ora)
Stessa forma delle altre sezioni (linguetta, carte, Modulo), desktop e telefono, coi loro stati nei Tweaks. Parole fra «» proposte: Marco le approva sulla tavola.

Servizi (/impostazioni/servizi): le chiavi in un posto solo -- Meteoblue (seeing), AAVSO (campagne), TNS (supernove), oggi sparse fra Meteo e Piano della notte. Per ognuna: il campo (mostra solo come finisce: «…a3f9»), a cosa serve in una riga, dove si prende (link), l'ultimo tentativo con l'esito (riuscito, chiave rifiutata, non raggiungibile, risposta non valida) e quando. Stati: senza chiave, attiva, rifiutata, non raggiungibile.
Scansioni (/impostazioni/letture): le scansioni passate, la piu' recente in alto. Per ognuna: quando, quanto e' durata, quali cartelle, frame entrati, rimasti fuori e perche', file non leggibili con il percorso e il motivo, interrotta a mano o bloccata. Stati: nessuna scansione, in corso, una bloccata, molti file non leggibili.
Diagnostica (/diagnostica, ADR 0008): versione, sistema, percorsi (dati, database, ASTAP), stato di ASTAP e del catalogo, i frame che uno stadio non ha potuto lavorare e perche', gli ultimi errori del diario. Un bottone «Copia» che copia tutto come testo per una segnalazione. Riga fissa: «L'app non manda niente da sola: copi tu e incolli dove vuoi.» Nessun dato personale (niente chiavi, niente nome).
Backup (ADR 0017): il file delle risposte accanto al database e quando e' stato scritto l'ultima volta; Esporta (senza le chiavi segrete e senza il percorso di ASTAP: una riga lo dice) e Importa (lo stesso ripristino); il ripristino proposto al primo avvio («Ho trovato le tue risposte del {data}: le rimetto?»).
Il menu dell'ingranaggio («siti, tema, cartelle, servizi») porta davvero a queste sezioni.

5. Una tabella sola per SQM e Bortle
Oggi due tabelle diverse: in soglie.js quella di ASTAP / Clear Dark Sky (3 da 21.69, 4 da 20.49), nel codice dell'app quella della voce Bortle scale di Wikipedia, la stessa dei nomi delle classi nel primo avvio. Un SQM di 21.4 sarebbe classe 3 per il sito e 4 per le misure. Vale quella dell'app: limiti inferiori 1 = 21.76, 2 = 21.60, 3 = 21.30, 4 = 20.80, 5 = 19.25, 6 = 18.50, 7 = 18.00, 8 = 17.00, 9 sotto. Una tabella sola in soglie.js, usata ovunque.

6. Correzioni dal giro (lessico, decisioni, convenzioni)
Decisioni di Marco del 20/10/2026:

Nebbia (visibilita' sotto 1 km) blocca come la pioggia: l'ora vale 0. Non entra nella trasparenza (oggi ALIAS 'la visibilità' la mette li'): la trasparenza e' solo l'aerosol.
«Trasparenza» e' la parola a schermo per il fattore («limita la trasparenza»); la carta del dato resta «Aerosol».
Un fattore che manca (seeing senza chiave, notti passate) cede i suoi punti agli altri in proporzione, e accanto si scrive «senza seeing». Oggi ora() in soglie.js lo conta pieno (m[k] ?? 100) e «senza seeing» non compare mai. Va negli stati «seeing senza chiave», «seeing parziale» e nelle notti passate (Notti, Statistiche).
Pianeti nel racconto della notte: «culmina» da 30° (planner.altS, massa d'aria 2), non da 10° (mx >= 10 nel Meteo).
Archivio: il gruppo di Criteri «Ripresa» diventa «Produzioni» («ripresa» e' della Luna: banda larga o stretta).
Flat restano solo nel Piano della notte (l'app non gestisce i file di calibrazione). Avviso: «Sotto 20 il master flat e' rumoroso.» -> «Sotto 20 flat la calibrazione aggiunge rumore.» («master» non si usa, e non e' una fonte: la fonte resta quella scritta accanto).
Dashboard si chiama Dashboard; barra, menu e Cerca restano come li avete fatti.
Errori da correggere:

Il nome di Marco a schermo, in soglie.js e Impostazioni: «scelta di Marco (7/10/2026)», «nessuna convenzione: scelta di Marco», «giorni scelti da Marco», «scelta di Marco: un cielo buio la sente prima». L'app e' per tutti: «nessuna convenzione: scegli tu», che usate gia'.
«bersaglio» -> «oggetto» ovunque a schermo: «Luna per bersaglio» -> «Luna per oggetto», «piu' il bersaglio deve stare lontano» -> «piu' l'oggetto deve stare lontano», il gruppo tempi «Per bersaglio» -> «Per oggetto». L'errore era nella nostra brief.
«pose» come conto di frame -> «frame» (la posa e' il tempo in secondi): Statistiche cella «pose» (r.311), «… pose · N oggetti» (r.548), «{n} pose senza massa d'aria escluse.» -> «{n} frame senza massa d'aria esclusi.» (r.414), riga «pose» nel riquadro (r.403). Anche questo era nella nostra brief. «ore, filtri e pose si cambiano» nel Planner resta (li' e' il tempo).
V50 esce del tutto: Impostazioni, ASTAP «Catalogo V50 · non trovato»; Cerca, parola chiave «cataloghi D80 V50» -> «catalogo D80».
«Solo se in N.I.N.A. la usi.» (Pausa prima del meridiano) -> «Solo se la usi nel programma di ripresa.»: chi usa ASIAIR, Voyager o SGP non resta fuori.
Crepuscolo in Impostazioni: la pillola «crepuscolo nautico» dice anche «Sole sotto −6°».
Scansione: «Fermata a mano: 3412 file letti…» -> «Interrotta a mano: …»; lo stato bloccata ha il motivo, «Dettagli» e il verbo per ripartire, non solo «Riprendi».
Archivio: «Senza oggetto», «frame senza oggetto identificato», «1204 frame restano senza oggetto» -> «senza oggetti identificati»; con ASTAP assente i frame sono «non risolti». «Aggiungi oggetto»: «sereno · seeing 2.1″» -> «buona · seeing 2.1″» (la parola del verdetto).
Da confermare: «Le domande compaiono dopo la lettura delle cartelle.» -> «… dopo la scansione.»; «oggetti riconosciuti» -> «oggetti identificati».
Notti: «ore serene» resta nello stato senza buio («ore serene col Sole sotto l'orizzonte», «ore serene, senza buio») e nella nota di Notti stati (Lofoten): «ore utili», come nel Meteo.
Dashboard stati.dc.html contiene il documento due volte, come era Meteo stati: uno solo.
Seeing di 2.0″ esatto: soglie.esito.seeing ha x < 2 ? 0; buona fino a 2″ compreso: x <= 2.
MisureFrame: «La FWHM di ASTAP: sulle stelle piccole circa 14% sotto altri programmi.» esce: FWHM e HFD le misura l'app (ADR 0022), ASTAP da' la soluzione e le stelle. Riepilogo stati: «le misurera' sep: FWHM, HFD, stelle…» -> togliere «stelle» (le conta ASTAP).
Riepilogo: «SNR mediano» dell'oggetto mescola due setup (IC 1396: Askar e Casa leggero): solo per produzione, mai sull'oggetto intero (ADR 0022: «SNR fra oggetti diversi: mai», e mai fra camere).
Piano della notte: «Nessun progetto sopra {n}° stanotte.» -> «Nessun progetto alto piu' di {n} gradi stanotte.», come per i pianeti.
Tavola Telefono: aggiungere Statistiche e Misure dei frame.
Statistiche: la nota sotto Confronta setup («Punto pieno {setup 1}, punto vuoto e linea tratteggiata {setup 2}; … In ″ si confronta fra setup diversi; i px al passaggio.») e' approvata.
7. Ordine e consegna
Ordine: foglio e token -> componenti nuovi e unificati (Finestra, Bottone, Quartili, Riquadro, segmentato, Modulo) -> Sistema e Foglio (la tavola dei componenti veri) -> pagine: Dashboard, Meteo, Notti, Riepilogo, Misure dei frame, Archivio, Attrezzatura, Da confermare, Primo avvio, Impostazioni (con le quattro sezioni nuove), Cerca, Planner, Progetti, Piano della notte, Statistiche -> tavole degli stati e Telefono -> pulizia dei file -> catture dopo.

Consegnate:

il progetto riordinato (v32), con le catture prima/dopo uguali salvo la sez. 6;
docs/COMPONENTI.md (sez. 2);
in DECISIONI: cosa avete unificato, cosa e' uscito, ogni dubbio come domanda;
un documento docs/per-claude-code-porting.md con: il foglio da copiare (percorso e versione), l'elenco delle pagine con i componenti che usano, e cio' che e' ancora simulato (dati, soglie, funzioni di soglie.js che nel codice vero calcola l'app).
Grazie: e' il passo che ci fa portare tutto senza rifare niente due volte.
