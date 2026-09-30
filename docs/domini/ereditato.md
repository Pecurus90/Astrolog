# Ereditato da old/ -- le decisioni di prodotto che il nuovo riprende, e quelle che non deve

Il progetto precedente aveva preso, in due anni, circa duecento decisioni di prodotto. Sono
state rilette tutte (settembre 2026) e stanno qui **una volta sola**, in tre gruppi: quelle
che valgono ancora sul principio (il nuovo le riprende), i bivi che il vecchio non aveva
chiuso (chiusi da Marco, sotto), e i ragionamenti che il vecchio stesso aveva gia'
superato (il nuovo non li deve riesumare). Ogni riga cita il posto in `old/` da cui viene.
Quando un dominio riceve il suo contratto in `docs/domini/`, le righe che lo riguardano
**si spostano li'** e spariscono da qui: questo file si svuota man mano che la spina cresce.

Le parole sono quelle del glossario (`glossario.md`): dove il vecchio diceva "produzione"
o "posa", qui si legge progetto e frame.

---

## A. Rilevato e dichiarato -- chi vince, e come si tiene

- **Tre fonti per ogni dato modificabile** (FITS / cataloghi e servizi / utente) e la traccia
  dell'origine e' un requisito strutturale, non un lusso -- `old/docs/database.md:11-19`.
- **L'utente vince sempre; fra FITS e cataloghi decide il tipo di dato**: l'oggetto celeste lo
  sanno i cataloghi, la ripresa la sanno i FITS -- `database.md:21-31`.
- **Il dichiarato e' uno strato separato**, non una colonna-origine per campo: l'import scrive
  solo sullo strato rilevato; in lettura "presenza della riga dichiarata vince", mai un
  `COALESCE` a mano in ogni query -- `database.md:1287-1319`. *Chiuso da Marco*: **vince sempre
  il dichiarato e l'header si conserva**, cosi' si vede sempre cosa diceva e si torna indietro.
- **Origine a cinque valori**: `header / computed / catalog / external / user` -- `architettura.md:45`.
- **Niente badge di provenienza nelle card**: il dato si mostra, il trattino se manca; la
  provenienza si legge nella scheda -- `prodotto.md:103,236`.
- **Nomi di default mai inventati**: niente "Sito sconosciuto" o "Corredo sconosciuto" nel DB;
  l'assenza si dice nella lingua dell'utente, a schermo -- `database.md:1618-1645`.

### Attrezzatura e filtri -- cio' che non ha ancora una casa

Il resto e' stato assorbito in [`spina.md`](spina.md) col contratto di `normalize`. Qui
restano tre decisioni i cui domini non sono ancora nati.

- **Il corredo di una notte** ha una cascata a quattro gradini: dichiarato per (notte, corredo)
  -> rilevato dai frame -> quello solito del corredo -> assente. Le correzioni si **propongono**
  dove il valore vecchio coincide, non si eseguono a tappeto -- `architettura.md:152-170`.
  (casa: `group`)
- **Colore del corredo**: dichiarato vince; con un corredo solo -> neutro; altrimenti dall'ordine
  di creazione, otto tinte non spettrali (i colori spettrali sono dei filtri) -- `database.md:394-399`.
  (casa: la pagina Attrezzatura)
- **Tri-banda e quad-banda sono due bande diverse**; nella ricetta un quad vale da solo solo se
  manca la coppia di duo; su LRGB nessuno dei due -- `roadmap.md:646-660`. (casa: la ricetta)

### Oggetti e identita'

- **Un oggetto per soggetto reale; il nome vive negli alias** (mai una colonna `name`); il nome
  grezzo d'import e' immutabile, quello di catalogo viene dall'aggancio, quello dell'utente
  dalla rinomina -- `database.md:105-135`.
- **Il nome da mostrare ha quattro rami in una funzione sola** (utente -> canonico se e' gia'
  la sigla della voce -> sigla primaria della voce -> grezzo), e tutte le superfici la usano --
  `architettura.md:210-218`.
- **Le proprieta' scientifiche dell'oggetto sono un riferimento alla voce di catalogo**, non una
  copia; si copia solo cio' che arriva dai servizi di rete -- `database.md:1327-1337`.
- **Aggancio al catalogo con provenienza e certezza** (coordinate confermate / da rivedere /
  nome esatto / nome storico / utente x certo / alto / basso / utente); "certo" solo se nome e
  coordinate concordano; oggetti mobili (pianeti, comete) mai agganciati per nome -- `database.md:77-89`,
  `architettura.md:694-721`. *Nota del nuovo*: con ASTAP le coordinate ci sono quasi sempre, i
  rami "senza coordinate" restano per i frame non risolti.
- **Rivedi identita' e' una superficie con due code** (conferma per coordinate; "stesso
  soggetto?"); confermare o correggere porta il metodo a *utente* ed esce dalla coda --
  `schermate.md:469-475`. Nel nuovo e' la sezione Oggetti di *Da confermare*.
- **Mosaico o doppione non si decide da soli**: coordinate contigue sono un suggerimento, decide
  l'utente; i pannelli si raccolgono, i doppioni si fondono -- `prodotto.md:382-386`.
- **`OBJECT` non ASCII in latin-1 resta storpiato** e riapribile: degrado onesto -- `backlog.md:1578-1580`.

### Siti -- cio' che non ha ancora una casa

Il resto e' stato assorbito in [`sito.md`](sito.md). Qui resta una decisione il cui dominio
non e' ancora nato.

- **L'orizzonte e' del sito**. *Chiuso da Marco*: il formato interno e' **uno solo**, una lista
  di punti (azimut, altezza); ci si arriva importando un `.hrz`, **disegnandolo a schermo** su
  una rosa dei venti, o lasciandolo libero. Fuori dall'arco misurato l'orizzonte e' libero,
  non zero -- `database.md:1647-1693`. (casa: il Planner, l'unico che lo legge)

### Notti, sessioni, progetti

- **Notte = data-notte + sito**; porta i dati irripetibili (meteo, Luna, ore di buio); due siti
  nella stessa data sono due notti -- `database.md:264-303`.
- **Sessione = notte x oggetto x corredo**, persistita; le metriche aggregate **non si
  memorizzano**; correggere uno dei tre attributi su un frame lo fa migrare di sessione --
  `database.md:869-895`.
- **Il progetto non e' derivabile**: l'automatismo **propone** una coppia (oggetto, corredo)
  scoperta all'import -- una per coppia, incrementale, mai spezzata nel tempo -- e l'utente
  decide. Ogni oggetto ha almeno un progetto -- `architettura.md:660-668,727-733`.
- **Un frame sta in al piu' un progetto**; l'attribuzione e' derivata (oggetto, corredo, periodo),
  l'eccezione dichiarata per frame vince; i non assegnati restano sempre interrogabili --
  `architettura.md:670`.
- **Chi cambia camera a meta' campagna trova due progetti; "Fondi" e' l'inverso** -- `architettura.md:732`.
- **Il nome del progetto e' derivato** ("filtri . corredo . anno"), mai persistito, non ripete
  l'oggetto; arriva in due pezzi e la frase la compone il frontend nella sua lingua --
  `architettura.md:674-680`.
- **L'obiettivo si esprime in ore** (secondi nello schema); totale obbligatorio, per filtro
  facoltativo, sbilanciamento libero; la ricetta non fa mai il totale; i frame mancanti si
  contano con l'esposizione dichiarata, non con la media -- `architettura.md:765-814`, `target.md:471-475`.
- **Nessun obiettivo nasce da solo**; nasce **solo nel Planner**, anche per un progetto gia'
  cominciato ("Apri nel Planner") -- `target.md:44-98`. Con la clausola del vecchio: *se gli
  obiettivi non nascono, e' la prima decisione da riaprire*.
- **Lo stato (completo / in corso / nessuno) e' derivato, mai una colonna**; `None` non e' zero --
  `target.md:13-33`.
- *Chiuso da Marco*: **fondere tiene l'obiettivo piu' alto; eliminare toglie l'intenzione, mai i
  frame; "sospeso" non e' una colonna, e' "fermo" da una stagione** -- `backlog.md:1868-1879`.
- **Un progetto finito resta**; alzare l'obiettivo lo riapre; la chiusura la propone l'app e la
  conferma l'utente -- `target.md:402-405`.
- **Mosaico**: un progetto con N pannelli; griglia (righe, colonne, sovrapposizione) sul
  progetto, pannelli derivati dal centro; **congelata a progetto iniziato**; obiettivo per
  pannello, il totale e' la somma solo se dichiarati tutti. *Debito del vecchio da non
  ripetere*: la chiave (progetto, oggetto) non regge due pannelli sullo stesso oggetto --
  `planner.md:80-97,652-656`.
- *Chiuso da Marco*: **il progetto e' legato a soggetto e corredo, non al sito**: il sito e' della notte.

### Foto finali

- **La foto finale si associa a mano**: mai cercata su disco, mai indovinata dal nome; una per
  oggetto **e** una per progetto (mosaico); vive in una cartella dell'app, mai sotto le cartelle
  FITS -- `prodotto.md:183`, `database.md:520-560`.
- **Non esiste "oggetto finito"**: se c'e' la foto finale si mostra, altrimenti il segnaposto --
  `prodotto.md:183`.
- *Chiuso da Marco*: **niente foto di terzi** (Commons, Wikidata), da nessuna parte. L'arricchimento
  resta di testo.

---

## B. I frame -- cosa entra, cosa si conta

- **Tipo del frame normalizzato** in {light, dark, flat, bias, dark_flat, unknown} da
  `IMAGETYP`/`FRAME`/`FRAMETYPE` con i sinonimi (`offset`, `zero` -> bias; `science`, `object`
  -> light); **assente -> unknown, mai "assumiamo light"** -- `fits/header_read.py:88-104`.
- **I file di calibrazione e gli unknown si riconoscono e si contano, non si catalogano**; la
  libreria di calibrazione e' fuori scope -- `backlog.md:1315-1317`, `importer.py:396-401`.
- **Anti-stack**: un file con `STACKCNT`/`NCOMBINE`/`NIMAGES`, o con *master / integration / stack*
  nel tipo o nell'oggetto, e' unknown -- mai per confronto di esposizione con la mediana --
  `header_read.py:106-118`.
- **Un frame senza oggetto o senza data entra lo stesso**, con stato "non assegnato" e segnalato --
  `database.md:1395-1401`.
- **`solved` = vera presenza di un WCS** (`WCSAXES`, matrice `CD`, `PLTSOLVD`), non un `CRVAL1` nudo --
  `architettura.md:1333-1335`. Nel nuovo il WCS lo misura ASTAP: quello dell'header e' un indizio.
- **Rotazione in convenzione `CROTA2`** da `atan2(-CD1_2, CD2_2)`; NULL dove manca, mai derivata
  da `OBJCTROT` -- `database.md:227-253` e la calibrazione del 2026-09 (segno opposto, 55 % a zero).
- **Scala a tre livelli**: `SCALE`/`PIXSCALE` dell'header -> matrice `CD` -> pixel/focale x 206,265;
  mai ricalcolata a valle -- `database.md:235-239`. Nel nuovo, il solver ha la precedenza.
- **Altezza, azimut e massa d'aria: header prima (94 % dei casi), effemeride come ripiego**;
  valori implausibili si scartano, non si correggono -- `database.md:202-225`.
- **Il rumore float32 si taglia a sette cifre dove il dato entra** -- `database.md:191-200`.

---

## C. L'anteprima

- **Il frame per la miniatura si sceglie con un punteggio composito relativo dentro l'oggetto**
  (z robusto su MAD, clip a +-3, segno invertito su FWHM/eccentricita'/fondo), pesi in una
  fonte sola (SNR 35 / FWHM 25 / eccentricita' 15 / stelle 15 / fondo 10), peso mancante
  ridistribuito; la FWHM entra in arcosecondi. **Non e' un voto** e non introduce scarti --
  `db/preview_select.py:12-42`.
- **Serve solo alla miniatura** (Dashboard, mosaico, card notte), mai a giudicare -- `prodotto.md:172-183`.
- **Resa**: mono -> autostretch deterministico; colore -> debayer col `BAYERPAT` **letto**, mai
  assunto -- `prodotto.md:193`.
- **First light del corredo = la notte piu' vecchia**; "ultima notte" di un progetto mai ripreso
  e' `null`, non una data antica -- `target.md:481-482`.

---

## D. Le assenze -- il vocabolario dei perche'

- **`null` = non so, mai uno zero di ripiego; il trattino e' lecito solo per un valore
  calcolato pari a zero** -- `architettura.md:1747`.
- **Un motivo sconosciuto degrada a una frase generica, mai a una chiave grezza a schermo** --
  `schermate.md:212`.
- **Vocabolari chiusi da riprendere**: meteo mancante (`ok / no_forecast / not_provided / partial`);
  sito (`no_active_site / site_no_coords / site_no_timezone`, in cascata); oggetto
  (`object_no_coords`); non-fattibilita' di un progetto stanotte (`object_no_coords -> never_up
  -> never_above_min -> below_min_hours -> moon_too_close -> weather_nogo`, **uno solo per riga,
  dal permanente al passeggero**); celle dell'archivio (`no_nights / outside_archive /
  future_month`); storico (`not_enough_history`); pipeline (`already_running / nothing_to_do`) --
  `planning/tonight.py:15-22`, `db/site_resolve.py:27-32`, `schermate.md:290-295`.
- **Tre assenze diverse nel meteo di una notte non si scrivono uguali**: non registrato, in
  attesa, dal modello -- `schermate.md:615`.
- **Altitudine assente = "non fornita", mai 0 m** -- `schermate.md:176-181`.
- **`UNKNOWN` come tipo e' un fatto sul catalogo, non sull'oggetto** -- `architettura.md:1124`.

---

## E. Le metriche di qualita'

- **L'app misura, non marca e non scarta**: niente keep/reject, niente percentuale di tenuta --
  `prodotto.md:166`. *Confermato da Marco*: nessun voto ai frame, nessuna soglia impostabile.
- **Metriche a doppia fonte, sdoppiate per origine** (header e calcolata); si mostra la calcolata
  se c'e' -- `database.md:838-851`.
- **FWHM e HFR nascono in pixel; la FWHM esce in arcosecondi (x scala), l'HFR resta in pixel**;
  senza scala -> `None`, e il frame non entra nelle medie -- `architettura.md:1689-1693`.
- **SNR = mediana robusta di picco / rumore del cielo** (non di flusso: guadagno e rumore di
  lettura non stanno in tutti gli header) -- `architettura.md:1706-1716`.
- **Media FWHM pesata sui frame misurati**, mai sui frame totali -- `architettura.md:1695-1704`.
- **Il fondo cielo si chiama `sky_background`** -- `architettura.md:1745`.
- **Statistiche: unita' = notte x corredo**; qualita' come punto + banda dei quartili, volumi
  come barre e cumulato; asse = giorno dell'anno; **FWHM e HFR riportate allo zenit** con
  `valore / airmass^0.6` (Kolmogorov), eccentricita' e SNR no -- `domini/statistiche.md:13-114`.
- **Resa del buio = ore integrate / ore di buio delle notti in cui si e' usciti** -- `statistiche.md:68-80`.
- **Non si correla qualita' e meteo** (si misurerebbe il filtro) -- `lezioni.md:206`.
- **L'analisi parte da sola a fine import, un thread, l'import ha precedenza, non riparte al
  boot** (riprendere e' una scelta dell'utente) -- `architettura.md:1441-1458`.
- **Una soglia dell'aria ferma, non tre**: quella derivata dal campionamento (Nyquist, 2 x
  scala fra 1,5" e 3"); le altre due del vecchio (2,5/4,5 e 4,0) non si portano -- `backlog.md:1524-1537`.

---

## F. Planner e progetti stanotte

- **Sei mosse**: Trova -> Seleziona -> Inquadra -> Crea -> Salva -> Traccia -- `planner.md:17-28`.
- **I modi di restringere si chiamano criteri, mai filtri** -- `planner.md:206-211`.
- **Criteri divisi per costo**: sette di catalogo (tipo, dimensione, costellazione, catalogo,
  magnitudine, AR, Dec -- AR circolare, estremi vuoti non stringono, "senza dato" nato acceso)
  e due del cielo (altezza minima per una durata minima; distanza dalla Luna), applicati **alla
  pagina che si guarda** -- `planner.md:213-249,371-424`.
- **La ricerca non toglie nulla per via del sito** (la declinazione non e' un AND) -- `planner.md:358-369`.
- **Comanda il buio**: ore, culmine, massa d'aria, distanza dalla Luna si misurano dentro il
  buio; **il buio lo decide il sito, non una manopola** (alle alte latitudini si scende al bordo
  piu' buio disponibile e lo si dichiara) -- `planner.md:427-436`, `architettura.md:392`.
- **Il numero che decide e' `usable_hours`** (ore di buio sereno sopra l'orizzonte) --
  `planning/tonight.py:6-11`.
- *Chiuso da Marco*: **altezza minima 30 gradi, distanza dalla Luna 40 gradi, ore minime 1 h
  sono valori di fabbrica in Impostazioni**, con la fonte accanto, modificabili una volta e
  usati ovunque; nel Planner si cambiano per una singola ricerca senza salvarli.
- **Periodo migliore = 12 notti (il 15 di ogni mese), ore utili, Luna esclusa, run ciclico
  all'80 % del massimo**; distinto dalla **stagione lavorabile** -- `architettura.md:398-423`.
- **La carta disegna, la geometria e' nostra**: rettangolo, rotazione, pannelli, mirino, scala
  sopravvivono senza rete; l'oggetto e' un mirino, non un'ellisse; trascinare la carta sposta
  l'inquadratura -- `planner.md:471-561`. Nel nuovo la carta e' Aladin Lite v3.
- **L'inquadratura si salva come centro e angolo, mai larghezza e altezza** (derivate dal
  corredo); N corredi = N rettangoli concentrici; angolo in `CROTA2` -- `planner.md:658-712`.
- **Un progetto porta cinque cose alla nascita**: inquadratura, ricetta, corredo atteso
  (obbligatorio), esposizione per filtro (**dichiarata, mai calcolata**), griglia + sito +
  apertura della carta -- `planner.md:120-144`.
- **Corredo di prova solo per simulare; un progetto non nasce su un corredo di prova** -- `planner.md:716-725`.
- **Stessa coppia (soggetto, corredo) -> 409 e si mostra il progetto che c'e'** -- `planner.md:71-75`.
- **Schema suggerito dal tipo dell'oggetto** (emissione -> SHO; planetarie e resti -> HOO; il
  resto LRGB) e filtri per famiglia d'uso (ammassi mai con filtro anti-inquinamento) --
  `catalogs/kinds.py:110-122`, `prodotto.md:218-231`.
- **Fattibile stanotte = tre condizioni** (ore di buio >= ore minime, Luna non troppo vicina,
  meteo non "no"); **ordine a tre chiavi** (si chiude stanotte -> ore utili -> ore mancanti);
  nessun punteggio composito; **l'assenza di previsione non e' un no** -- `target.md:127-163`.
- **La postazione = la montatura, si rileva, non si configura**; nessuno scheduler -- `target.md:165-194`.
- **Quattro bande**: in corso / in attesa / fermi / finiti; confine = stagione di ripresa;
  circumpolare mai "in attesa" -- `target.md:317-372`.
- **Nessuna classifica assoluta del catalogo ("i migliori stanotte")** -- `target.md:512-513`.
- **Il suggerimento "stanotte conviene X" e' passivo, all'apertura; mai una notifica push** --
  `prodotto.md:336-340`.
- **Esposizioni previste (SNR, formula Lorenzi/Cinzano)**: decisa, mai costruita, con copertura
  onesta per tipo -- `planner.md:155-200`. *Parcheggio*.

---

## G. Meteo

- **Un fattore da portare con la sua fetta**: seeing (soglia dal campionamento). Il vento in quota
  (60esimo percentile della climatologia a 700 hPa del sito) e' arrivato come **confronto**, non
  come fattore: la soglia veniva dall'archivio di Marco (casa: `docs/domini/meteo.md`). Esclusi: jet stream come fattore, umidita' da sola, igrometrico, visibilita' --
  `verdict.py:52-133`, `climatology.py:43-51`.
- *Confermato da Marco*: **il seeing non cambia la parola del verdetto**; e' un fattore mostrato.
- **Visibilita' a cinque tacche** -- `architettura.md:584`.
- **La griglia del modello non si inventa**: "previsione di zona", senza numero -- `architettura.md:602`.

---

## H. Vocabolari e cataloghi

- **Sensori (35 geometrie) e corpi camera**: solo geometria, i millimetri si derivano; chip fuori
  catalogo -> `None`, mai preso in prestito -- `equipment/sensori.py`, `camere.py`.
- **Ottiche: nessuna tassonomia curata**; testo libero + tendina auto-popolata -- `prodotto.md:209`.
- **Tipo dell'oggetto (21 codici) derivato in Python; il frontend traduce**; famiglie d'uso (9)
  separate dal tipo; `Dup` e `NonEx` esclusi -- `catalogs/kinds.py:35-128`.
- **Costellazione come codice IAU, derivata offline dalle coordinate se manca** -- `architettura.md:1124`.
- **Fasi lunari come enum**, campionate al centro del buio, dal sito della notte -- `architettura.md:372`.
- **Nomi comuni solo in inglese; tipo e costellazione codice + traduzione** -- `architettura.md:1118`.
- **Valori scientifici mai localizzati; durate in ore e minuti, mai decimali** -- `architettura.md:1128-1142`.
- **Stack dei cataloghi**: OpenNGC > VizieR > Stellarium, le correzioni nostre hanno l'ultima
  parola; Abell del bundle = ammassi di galassie -- `prodotto.md:237-243`. *Chiuso da Marco*: il
  catalogo si aggiorna **con la versione dell'app**.
- **Magnitudine mostrata: V poi B, con la banda sempre accanto** -- `src/lib/magnitudine.js:23-25`.

---

## I. Import, impostazioni, superfici

- **Normalizzazione all'import, mai script di riparazione** -- `domini/importazione.md:13-28`.
- **Il rifacimento e' esplicito** ("Rifai tutto", con le sue pastiglie di cio' che non tocca) --
  `importazione.md:51-62`, `schermate.md:644,650`.
- **Il totale puo' non esistere**: nessuna percentuale senza denominatore; "N trovati" -- `schermate.md:632-633`.
- **Le correzioni dell'utente diventano regole riusabili** (alias header -> strumento, filtro,
  oggetto), applicate per gruppo e proposte dove il valore coincide -- `prodotto.md:324-328`,
  `aliases.py`. Nel nuovo e' il cuore di *Da confermare*.
- *Chiuso da Marco*: **export = un file solo del dichiarato, reimportabile**; CSV di sessioni e
  frame in coda; pacchetto per oggetto in parcheggio -- `confronto-astro-pm.md:183-196`.
- **Aggiornamenti dell'app: avvisa e decidi, mai forzato** -- `intervista-requisiti.md:99-101`.
- **Nessun controllo finto in Impostazioni**: ogni controllo fa effetto -- `schermate.md:774-786`.
- **Il primo avvio e' un timbro, non un'euristica**; wizard corto, senza rosso, saltabile. Il
  vecchio diceva "tre domande e mai una quarta": la quarta, facoltativa, e' la chiave Meteoblue
  (Marco, 25/9/2026) -- `database.md:1593-1615`, `prodotto.md:113-138`.
- **Lingua e tema nella barra in alto, non in Impostazioni** -- `schermate.md:682`.
- **Reset: ricrea il file, conserva cartelle, siti e impostazioni; FITS mai toccati** -- `architettura.md:1643-1672`.
- **"Stanotte" la decide il server sul fuso del sito** -- `architettura.md:378`.
- **Le modali di oggetto e notte sono l'una la trasposta dell'altra** -- `schermate.md:425,601`.
- **Sei superfici con anteprima, nessuna mostra due immagini** -- `prodotto.md:170-180`.
- **Nessun voto per notte, nessuna nota manuale sulle sessioni** -- `schermate.md:591-595`.
- **Affordance a tre livelli** (naviga / apre / niente); il rosso solo per chi perde dati; ambra
  = invito -- `schermate.md:256,645`.
- **Niente registro di manutenzione in Attrezzatura** -- `schermate.md:890`.
- **Parita' di funzioni fra desktop e mobile, solo layout diverso; soglie sulla colonna, non
  sulla finestra** -- `architettura.md:63-67`.

---

## J. Superato dentro old/ -- non riesumare

Il vecchio le aveva decise e poi rovesciate; compaiono ancora nei suoi doc e possono sembrare
vive. Non lo sono.

- progetto = oggetto + un solo corredo (`database.md:961,1181`) -> M:N
- serve la finestra temporale del progetto (`database.md:414`) -> facoltativa
- catalogo a due livelli con voce canonica (`database.md:581-600`) -> una voce
- seeing stimato dal vento in quota (`prodotto.md:49-58`) -> fonti di seeing
- Stellarium scartato per la licenza (`architettura.md:1122`) -> portato, GPL compatibile
- il framing e' "roba nostra, non Aladin" (`planner.md:473-477`) -> Aladin disegna, la geometria e' nostra
- obiettivo auto-posto all'import (`architettura.md:816`) -> mai
- crepuscolo, altezza minima, distanza Luna come preferenze libere -> valori di fabbrica dichiarati
- card dell'archivio con l'anteprima (`backlog.md:792`) -> solo foto finale o segnaposto
- faccetta "Stato" e badge Completato in Library (`backlog.md:1883`) -> l'archivio e' del finito
- "produzione" ritirata e poi reintrodotta (`backlog.md:1884`, `prodotto.md:354`) -> progetto
- pagina "Sessioni" -> Notti; trasparenza -> visibilita'; `median` -> `sky_background`
- survey di Aladin tolto e poi rinato nel Planner (`prodotto.md:258`)
- chiave della sessione notte + oggetto senza corredo (`database.md:874-883`)
- data della notte = `DATE-OBS` - 12 h senza fuso (`database.md:1150`) -> fuso del sito
- plate solving fuori dalla v1 (`prodotto.md:388-390`) -> ASTAP per tutti
- guscio Electron, cinque lingue, "niente riscrittura da zero"
- "Sito sconosciuto", `defaultRigId`, le manopole senza lettori (`api/config.py:28-34`)

---

## K. Due nature -> una casa

Cio' che il vecchio calcolava in due posti. Nel nuovo ognuno ha **una** casa in Python e il
frontend formatta; il rilevatore di duplicati e il revisore lo fanno rispettare.

| cosa | dove stava due volte |
|---|---|
| ore utili vs ore di buio | `weather/verdict.py` e `src/lib/nightHours.js` (due pagine davano 3,0 h e 4,7 h) |
| soglie meteo (okta, rugiada, raffica, seeing) | `verdict.py:92-126` e `src/lib/soglie.js` |
| magnitudine V-poi-B | `catalogs/lookup.py` e `src/lib/magnitudine.js` |
| scala e campo | `header_read._wcs_scale`, `equipment/inquadratura.py` e `src/lib/astro/fov.js` (ricalcolava e prendeva la peggiore) |
| data della notte | `db/assemble.py:115-134` e `src/lib/astro/night.js` |
| Luna crescente/calante | `ephemeris/moon._phase_key` e `src/lib/astro/library.js:13-16` |
| le 14 bande | `api/filters.py:56-59` e `src/lib/filters.js:42-60` |
| colore dei filtri | colonna `filters.color` e token CSS `--f-*` (due "fonti uniche") |
| sentinella "nessun filtro" | stringa italiana nel DB, `filters.js:36`, due chiavi i18n |
| sigla di catalogo | `/objects` e regex `catOf` in `library.js:29-40` |
| registro delle metriche per frame | `queries._FRAME_METRICS_SQL` e `modals/metrics.js:56-60` |
| motivi di non-fattibilita' | sei codici Python, cinque chiavi i18n (due collassati) |
| motivi del sito | copiati in otto rotte prima di `site_resolve.py` |
| bordi della finestra | `api/visibility.py` e `ephemeris/visibility._BORDI_FINESTRA` |
| soglia dell'aria ferma | tre risposte: `verdict`, `quality.js`, `statsModel.js` |
| nome da mostrare | copiato in due query prima di `resolve_display_name` |
| media FWHM | pesata sui frame totali in tre punti del frontend |
| schema (suggerito vs osservato) | `kinds.KIND_TO_SCHEME` e `schemeOf` nel frontend: due grandezze, una parola |
| corredo di una notte | `_gear_from_frames` (prevalente + misto) e `setup_instruments` (unione storica) |
| giorni fra due date, disco lunare, colore Bortle, trend anno su anno | quattro conti nel frontend che appartengono all'API |
| motivo dell'identita' | `identify.py` e una coda che lo ricavava **dalla prosa** |
| ore di buio | colonna, calcolo al volo e funzione del Sole: una fonte, tre trasporti |
