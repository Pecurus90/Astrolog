# Per Claude Design -- Brief completo prima del porting (v59)

Da Claude Code, 6/11/2026. Tutte le tavole v58.6 controllate contro cio' che l'app fa davvero
(rotte, contratti, ADR, decisioni di Marco), con la lista di `/porta-tavola`. Questo brief
**raccoglie e sostituisce** i brief aperti: `design-dopo-inventario.md` (27/10),
`design-meteo-dashboard-aggiunte.md` (punti 1 e 5), `design-statistiche.md` (0quater, 0ter.5),
`design-selezione.md` (punti aperti), `design-archivio-porting.md`, `design-misure.md` (6/11).

Regola (Marco, 27/10): la tavola e' la specifica, aspetto e funzioni. Si cambia solo dove una
decisione di Marco e' piu' recente della tavola, dove l'app non lo puo' fare, o dove la tavola non
dice qualcosa che l'app ha. Qui si aggiunge e si corregge; **nulla si toglie**. Cio' che l'app non
ha ancora resta disegnato, con uno stato provvisorio finche' arriva.

Le parole sono proposte: Marco le approva sulla tavola. Le scelte di Marco del 6/11 sono gia'
dentro.

---

## 0. Per tutte le pagine

1. **Luna: partenza 25 % / 65 % / 0 gradi** (dall'orizzonte), al posto di 25 / 50 / -5 (ADR 0034,
   Marco 24/10). Dove: `soglie.js` (`LUNA0`), Impostazioni (righe 392-401), Planner, Dashboard,
   Meteo, Notti. Fonte accanto al 65: la regola di ING (grigio fino a 0,65), non «regola diffusa».
   Cambia a schermo: le notti con Luna fra 50 e 65 % passano da «solo banda stretta» a «al limite».
2. **Ore di posa al posto delle ore utili** (ADR 0034): somma di (Trasparenza / 100) x ore di buio,
   divisa per banda della Luna: «4,6 ore di posa: 3,1 in banda larga, 1,5 solo banda stretta».
   Dove «ore utili» vuol dire solo alto e al buio senza meteo: «ore visibili». Occorrenze: Dashboard
   (15), Meteo e Meteo stati (8), Notti (2), Piano della notte (3), Planner (circa 20), Riepilogo,
   Impostazioni («Stagione: ore utili almeno» -> «ore visibili almeno»), Sistema (5).
3. **Trasparenza al posto della Qualita'** (ADR 0034): il numero 0-100 e' la Trasparenza oraria,
   media pesata sul buio; verdetto 70 / 40. Escono i pesi 35/30/12/9/9/5 e «limita X». Il seeing e'
   **fuori dal voto**: niente «senza seeing» (Notti, Statistiche); dove manca l'aerosol, «senza
   aerosol». Dove: Dashboard, Meteo, Notti, Statistiche, Sistema («Qualita' della notte»).
4. **Cielo in classi okta** (Marco 24/10, glossario): quattro parole del cielo dall'app: Sereno /
   Nuvole sparse / Nuvoloso / Coperto (non «poco, parzialmente, molto nuvoloso», classi superate),
   non frasi scritte a mano. Dove: Notti (riga 202), Dashboard prossime notti,
   Meteo («nuvole al 38 %» -> la classe, il numero accanto).
5. **Condensa e raffiche**: la condensa non dice mai «non adatto» (ADR 0034; in arrivo il modello
   di Beysens); raffiche a 25 km/h, non 29. Dashboard e Meteo.
6. **Giudizi relativi a 2,5 Qn**, non 2,5 MAD (ADR 0039, Marco 24/10): cambia solo la scritta.
   Selezione dei frame (testi 673-674, pillola «MAD del gruppo»), soglie partenza. Senza sigle a
   schermo (v56.31): «rispetto al gruppo».
7. **Numeri**: la virgola decimale ovunque (Marco, 6/11; glossario aggiornato): oggi «4.6»,
   «1.4», «0.07» in Dashboard e Meteo, `toFixed` nel Meteo.
8. **Stati che mancano quasi ovunque**: caricamento (`Scheletro`) ed errore dell'app
   (`Avviso` con «!»: «AstroLog non risponde, riprova»). Mancano in: Archivio (errore), Progetti,
   Statistiche, Impostazioni (anche errore di salvataggio), Cerca («cerco...» ed errore),
   Riepilogo (errore, notte o oggetto non trovati), Selezione dei frame, Meteo, Dashboard,
   Primo avvio (lettura delle impostazioni).
9. **Colore mai da solo**, dove oggi manca parola o segno: vista Carte / Elenco scelta (Archivio),
   riga selezionata (Notti), giorni «buona» del calendario della Luna e legenda senza segno,
   barre Kp (Dashboard), mesi della carta del Planner.
10. **Zone da toccare da 44 px**: CardMeteo ↗ e × (28 px), ↻ del Meteo (34 px), barrette del Meteo.
11. **Calcoli**: cio' che la tavola calcola (verdetti, soglie, zenit, tilt, quartili, Luna, ore,
    conti dell'Attrezzatura, Bortle misurato, orizzonte) nell'app arriva gia' fatto. Nella tavola
    puo' restare simulato; serve solo che il componente non decida nulla da solo.
12. **Dati di prova generici**: niente «Marco» come nome (Impostazioni 335), «Il disco E:», «sul
    NAS» (Selezione 469-470), percorsi con `\` (l'app gira su Windows, Mac e NAS).

## 1. Misure dei frame (MisureFrame, Riepilogo, Selezione)

L'app calcola 63 misure per frame, la tavola ne mostra 12. Le 12 tessere restano.
1. **«Altre misure ▾»** (Marco): elenco a discesa accanto alle tessere, voci a gruppi; la misura
   scelta fa come una tessera (grafici, fino a due; tabella per filtro) e la pagina la ricorda.
   - Stelle e forma: PSFResidual, FWHM Sigma, Eccentricita' Sigma, direzione e coerenza
     dell'allungamento (stesso verso: inseguimento o vento; versi diversi: ottica), stelle sature.
   - Segnale: PSF Signal Weight (il peso con cui si integra), PSF Flux, PSF Mean Flux, PSF Count.
   - Fondo e pixel: SkyRate (fondo al secondo: si confronta fra tempi di posa diversi), Mediana,
     Sigma, Entropia, NoiseRatio, SNR, M*, N*, banding di righe e colonne, lato chiaro del
     gradiente (anche come angolo sul cielo).
   - Cielo: azimut, angolo orario, lato del pilastro, zero point dello SQM.
   - Luna e Sole: altezza della Luna, distanza dall'oggetto, parte illuminata; altezza del Sole.
   - Trasparenza e nuvole: solo su una serie di almeno 5 frame dello stesso campo e filtro;
     arrivano dopo: serve ora lo stato «serve una serie».
   Senza soglia pubblica: senza pillola.
2. **Tilt e curvatura** (Marco): in tessera la % alla ASTAP dagli angoli col giudizio 10 / 20 %;
   nel dettaglio FWHMTilt e FWHMCurvature in px, senza giudizio.
3. **Gradiente** (Marco): in tessera in unita' di rumore (si confronta fra camere), accanto la %
   del fondo.
4. **Fondo cielo e Rumore** si confrontano solo fra frame con stessa camera, guadagno e tempo di
   posa: quando un grafico li mescola, una riga lo dice.
5. **Eccentricita'**: oltre al giudizio sul frame, l'app avvisa sul setup quando la sua mediana
   supera 0,6 (ADR 0039): un posto per l'avviso (Attrezzatura o Riepilogo).
6. Riepilogo stati, riga 19: «le misurera' sep» e' vecchio, la misura c'e'.

## 2. Selezione dei frame

1. **Criteri in piu'** (Marco): PSF Signal Weight, Scie (0-16 per frame), Luna (altezza, distanza,
   illuminata), SkyRate. La **formula libera** legge tutte le misure del punto 1.1, come le
   espressioni del SubframeSelector; l'aiuto le elenca. <!-- software-ok -->
2. **Eccentricita' di partenza** relativa al setup (una coda, Qn), non 0,6 fissa: cambia solo il
   numero iniziale.
3. **Gruppo** = oggetto, setup, filtro, tempo di posa e **guadagno** (ADR 0032): due guadagni con
   lo stesso tempo di posa non si fondono nel grafico.
4. **FWHM e HFD in px** quando la scala non e' nota (oggi solo in ″).
5. Stati: caricamento, errore, gruppo sotto 10 frame («la soglia tace e lo dice»), spostamento in
   corso con avanzamento (NAS lento).
6. **Anteprima del frame**: arriva dopo (l'app non ha ancora l'immagine): stato provvisorio con le
   sole misure.
7. **Nota per frame** («Perche'? scia di satellite»): l'app la scrive se c'e' una scia; per le
   altre ragioni serve la regola che l'ha segnato.
8. **«Un progetto in corso»**: i progetti arrivano dopo; finche' non ci sono, si parte dalle notti
   (come lo stato «nessun progetto»).
9. Impostazioni non ha la sezione «Selezione dei frame», ma le linguette puntano a
   `?sezione=selezione`: la sezione vive solo nella vista regole della Selezione. Decidere una casa.
10. Parole: «gain» -> «guadagno»; «Scarta / Tieni / da scartare / scartate» da fissare nel
    glossario, che usa «scartati» per i file saltati dalla scansione.

## 3. Da confermare

Le sette sezioni coincidono con le domande dell'app.
1. **Filtro nuovo con piu' bande** (l'app accetta bande con larghezza in nm): oggi una banda sola.
   Serve per i filtri doppi.
2. **Proposte gia' pronte** che la tavola lascia vuote: nome del mosaico proposto, focale proposta
   dall'ottica.
3. **Perche' l'app dubita** di un oggetto (metodo e fiducia), e i due vuoti diversi: «nessun
   oggetto trovato» e «non ancora cercato».
4. **Oggetti riconosciuti**: «Mostra altri» (l'app ne da' 50 per volta) e la scheda di «Correggi».
5. **Esiti di Applica**: «in coda» (il lavoro parte dopo), filtro che contraddice le bande, «nessun
   filtro» gia' presente.
6. **Campi che la tavola mostra e l'app non ha ancora**: «Oggetti nel campo» e «Ottica e camera»
   nei Filtri, «Sensore» negli Strumenti duplicati, «Notte» e «Durata» nei Frame senza tipo,
   «Notte» nei Mosaici. Restano: l'app li aggiunge.
7. **Unisci**: dire quale nome resta (quello con piu' frame).
8. **Domande nuove da prevedere**: «quali progetti sono finiti» dopo la prima scansione (Marco
   27/10: «Decido dopo» la lascia qui); montatura, chiesta una volta.
9. **Frame senza data** (le Notti li mandano qui): una sezione nuova con risposta (Marco, 6/11):
   per una cartella l'utente scrive la data o la notte, e i frame entrano nelle notti.
10. Sigle: Hα, Hβ, OIII, SII al posto di HA / HB.

## 4. Archivio e Riepilogo

1. Archivio: stato di errore; stili fissi scritti nella pagina in classi del foglio (selettore
   Carte / Elenco e tendina dell'ordine, righe 29 e 35; tondo dell'anteprima e griglia, 63; colonna
   della carta, 53); avviso «Togli tutti» -> «Togli i criteri», come il bottone di `Filtri`.
2. Riepilogo: «ore utili» -> «ore di posa» (riga 173); il ↗ Progetti solo se l'oggetto ha un
   progetto; stati errore e «non trovato».

## 5. Notti

1. Barra «N ore di posa su M di buio»: e' una proporzione, non un orario: dichiararlo.
2. «Fuori da ogni notte»: l'app distingue senza sito (si risponde in Da confermare) e senza data
   (vedi 3.9).
3. Luna: il componente vuole «crescente», l'app manda il lato illuminato (vale anche a sud).
4. Posto per la fonte del sito della notte e per il totale degli oggetti in «Tutto l'archivio».
5. Stato «Carica altre» in corso ed errore.

## 6. Dashboard

1. **Tre carte per riga** sul computer (brief del 12/10, punto 1): oggi scorrono di lato.
2. **FWHM media** nella Dashboard (brief del 12/10, punto 5): chiuso, no (Marco, 6/11): la
   Dashboard resta senza misure dei frame.
3. **Calendario della Luna a tre gradini** 25 / 65 con le ore senza Luna, al posto di due stati
   con la regola delle 4 ore.
4. **Luna**: giorni interi e punto della bussola (come li da' l'app), non «18,4 giorni» e «68°»;
   «tramonta domani» c'e' anche fuori dalla notte. Numeri coerenti fra carta e pillole.
5. **Buio e buio senza Luna** sotto «Buio 20:48-05:48».
6. Carta **Sole** e orari del Sole: arrivano dopo; stato «Sole non disponibile», segmentato con la
   sola Luna fino ad allora.
7. Progetti: carta e vista solo con progetti; «Crea un progetto» punta al Planner.
8. Stati: sito senza fuso, Luna che non sorge o non tramonta, calendario non ancora scritto,
   prima previsione non arrivata (diversa da «non raggiungibile»), seeing con chiave non valida,
   giorni polari.
9. Parole: «buona / incerta / non adatta» al femminile come il glossario.

## 7. Meteo

1. **Eventi della notte**: ai pianeti servono sorge, tramonta, culmina; «diventa buona» e
   «condensa» dipendono da Trasparenza e Beysens. Disegnati: restano.
2. **Obiettivo Sole**: arriva dopo; «Sole alto» non con 08-17 fisse ma da una regola con fonte.
3. **Campionamento**: arriva dopo (servono le scale dei setup).
4. «Cambio del modello non riuscito: ICON non risponde»: il cambio di modello legge e basta; lo
   stato resta col testo «AstroLog non risponde».
5. **Seeing senza chiave** (Marco, 6/11; ADR 0034): la parola stimata dalla corrente a getto
   (buono / medio / scarso), detta «stima dal vento in quota»; con la chiave Meteoblue il numero.
   L'invito a inserire la chiave resta accanto.
6. Fonte che tace: un testo generico per aerosol e jet, non solo la visibilita'; anno dei dati
   CAMS dai dati, non «2026».
7. Testo morto «Al massimo quattro misure».

## 8. Planner, Piano della notte, Progetti

1. **Cielo**: catalogo vero (OpenNGC, 22.080 voci, Sh2 compreso) e stelle fino a mag 6,5; la cupola
   e le librerie nel pacchetto dell'app, non da internet.
2. **Immagini** (inquadratura, Sole, pianeti): passano dal proxy dell'app con cache; senza rete le
   stelle disegnate. Sole da Helioviewer come il contratto. Arrivano col passo del Sistema solare.
   <!-- software-ok -->
3. **Eventi** (ISS, Tiangong, Hubble, eclissi, occultazioni, congiunzioni, ombra di Io): arrivano
   dopo, con l'orbita del giorno; stato «orbita in caricamento».
4. **Mappa del transito**: i servizi (mappe, strade) sono da scegliere (rischio di Marco); fino ad
   allora striscia, sito e «Apri in Google Maps». Leaflet nel pacchetto. <!-- software-ok -->
5. **Progetti per setup** (ADR 0033): un oggetto puo' avere un progetto per setup; manca «ha gia'
   un progetto con questo setup». «Prima di salvare»: «{durata} gia' riprese non conterebbero piu'»
   (la conta l'app).
6. **Sovrapposizione dei mosaici 20 %** (N.I.N.A.), non 15 %; il Sistema solare ha gia' 20.
7. **Crea**: ore e tempi di partenza da Impostazioni con la fonte (Marco 27/10), non 300 s fissi.
8. **Luna per filtro** anche nel Planner (oggi 40° fissi; il Piano della notte la usa gia').
9. **Prima scansione** (Marco 27/10): i progetti trovati finiti vanno in Archivio, gli altri in
   Progetti in corso con l'obiettivo vuoto («Scrivi l'obiettivo»). Domanda «quali sono finiti»:
   «Tutti finiti / Scelgo io / Decido dopo».
10. **Orizzonte del sito**: «con l'orizzonte di {sito}» e il suo import (Impostazioni › Siti).
11. **Campionamento col seeing** e consigli (bin 2x2, dithering) nella carta Setup.
12. Esportazioni N.I.N.A. e SharpCap, ricerche online (JPL, MPC, VizieR, AAVSO, TNS): restano <!-- software-ok -->
    disegnate; arrivano dopo.
13. Piano della notte, proposte del Deep sky: «4 h di posa» e basta (Marco, 24/10 e 6/11); le ore
    visibili restano nel Planner. L'ordine «chiude / utili / mancano» -> «chiude / di posa /
    mancano».
14. Parole: «NINA» -> «N.I.N.A.»; «Per bersaglio» -> «Per oggetto»; «Durante le pose» -> «Durante <!-- glossario-ok -->
    i frame»; «Cupola / Sfera / Dentro» restano (ora nel glossario); «Reframing» -> «Reinquadra»;
    «stagione» -> «mesi buoni» (Marco, 6/11), Planner e Impostazioni. <!-- glossario-ok -->
15. Stati: errore di salvataggio, doppione con altro setup, caricamento ed errore in Progetti,
    «Elimina» non riuscito.

## 9. Impostazioni e Primo avvio

1. **Siti completi**: oggi due siti fissi. L'app ha aggiungi per nome o coordinate, altitudine e
   fuso con la loro provenienza, rinomina, elimina (non se ha notti), le quattro vie per il cielo.
   Il **Bortle misurato** (Usa / Lascia / Lascia vuoto, tacche dei mesi, «misurato su n notti»,
   approvato il 18/10) va qui, non solo nelle Misure dei frame. Primo avvio promette «altri siti
   dalle Impostazioni».
2. **ASTAP**: da dove viene (canale), «Cercalo tu» (propone, non scrive), cataloghi dai nomi
   trovati (D80, D50, D05...; vuoto = «nessun catalogo»). Catalogo consigliato: **D50** (Marco,
   6/11; ADR 0036), D80 proposto per i campi molto stretti. Primo avvio (riga 88) e Impostazioni
   (riga 386).
3. **Servizi**: carta per la chiave del servizio del cielo; chiavi AAVSO e TNS e Meteoblue solo
   qui (oggi doppie in Planner › Ricerca e in Meteo).
4. **Lingua** in Generale (italiano, inglese).
5. **Cartelle**: «non raggiungibile», «Sposta», sfoglia il NAS anche qui, «Togli» con «i frame
   restano».
6. **Backup**: stato «file illeggibile»; il file porta anche le impostazioni (dirlo); ripristino
   non riuscito.
7. **Orizzonte**: la linea segue la soglia d'altezza del Planner, non 30° fissi.
8. «Meteo apre su: Sole» spenta con «arriva col Sole»; Diagnostica e «Ultimo tentativo» dei
   servizi arrivano dopo.
9. Automazione «per postazione»: la postazione e' la montatura; il setup non la contiene. Dire
   cosa sceglie l'utente.

## 10. Attrezzatura

1. **Elimina pezzo** coi suoi quattro stati (brief del 27/10, punto 3).
2. Il pixel e' «ricavato dal cielo», non calcolato da apertura e focale.
3. L'avviso «misure da rifare» vale per ogni modifica che cambia il cielo, non solo il Sensore.
4. I campi del Modulo (schema ottico, tolleranza, ADC, OAG, distanziale...) restano: l'app li
   aggiunge.

## 11. Statistiche

1. Bortle misurato: almeno 4 mesi senza buchi oltre 3, sugli ultimi 12 fino all'ultima notte
   misurata (non «6 mesi, ultimi 12»); proposto anche al sito senza cielo (Marco 5/11).
2. Trasparenza al posto della Qualita'; «senza aerosol» al posto di «senza seeing».
3. Frase dei setup a confronto: «in px dipende dalla scala» (brief statistiche 0ter.5).
4. «Notti buone perse»: lo stato «Meteo storico in arrivo» resta finche' l'app non scarica il
   meteo delle notti senza frame.
5. Celle e punti raggiungibili anche da tastiera.

## 12. Telaio e Sistema

1. **Stanotte**: la pastiglia apre sito, Luna e meteo della notte (oggi link vuoto).
2. **Carta del cielo**: nel menu del telefono senza link e assente sul computer; va nel Planner
   (cupola). Una casa.
3. Sistema: «ore utili» e «Qualita' della notte» come al punto 0.
