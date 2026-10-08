# Glossario -- una parola per cosa, in due lingue

Le parole a schermo le ha scelte Marco, una per una (settembre 2026). Il nome nel **codice**
e' inglese, il nome che **l'utente legge** e' italiano, e ogni cosa ne ha **uno solo** di
ciascuno. Un identificatore nuovo che non sta qui, o che chiama con un altro nome una cosa
che qui c'e', e' un rosso per il revisore. Nei documenti si usano le stesse parole -- **tranne
dove una parola e' di dominio e non di schermo**, e allora la colonna *non si dice* non la
nomina: `scan_run` a schermo e' **una lettura**, ma nel codice e nei contratti si chiama
**ricevuta**, cioe' cio' che resta di una corsa. Le
traduzioni nelle altre lingue attive le tiene il file comune di traduzione del frontend,
che il `traduttore` legge per primo.

## Cio' che c'e' nell'archivio

| cosa e' | nel codice | a schermo (it) | non si dice |
|---|---|---|---|
| un file di ripresa letto dalle cartelle: un light, o un file che non dice che tipo e' finche' non lo dici tu | `frame` | frame | posa, scatto, sub, immagine, esposizione |
| cio' che identifica un frame per sempre: sha256 di dimensioni e 64 KB di pixel dal centro. Sopravvive a uno spostamento, a una rinomina e a un header riscritto | `frame_hash` | impronta | hash, checksum, firma |
| il tempo di un frame, in secondi | `exposure_s` | esposizione | posa, durata |
| la somma del tempo dei frame -- di un oggetto, di un mosaico -- in secondi. Le copie riscritte non contano, e un frame che non dice il tempo **non vale zero**: resta fuori dalla somma e si conta in `untimed`. Se **nessun** frame lo dice, a schermo le ore non compaiono affatto: restano i frame senza durata | `integration_s` | ore | integrazione, tempo totale, somma, esposizione, 0 h (per un tempo che non si sa) |
| quanti frame, fra quelli contati, non dicono il loro tempo: viaggia accanto alle ore perche' "non lo sappiamo" e "zero ore" non sono la stessa cosa. Zero secondi invece e' una misura, e non si conta qui | `untimed` | senza durata | senza tempo, a zero, mancante, nullo, vuoto |
| un dark, flat, bias o dark-flat: riconosciuto e contato, non catalogato | `calibration_frame` | file di calibrazione | calibrazioni, master |
| una volta che l'app ha letto una cartella, con cosa e' entrato, cosa e' rimasto fuori e quanto e' durata: resta, e si rilegge dopo | `scan_run` | lettura | corsa, scansione (il gesto), passata, sessione |
| un file che la scansione non ha letto, col suo motivo: il sistema non lo apre (`file_unreadable`), non e' un FITS (`header_unreadable`), il nome non si puo' scrivere (`name_not_utf8`), un guasto che nessuno aspettava (`internal_error`) | `errors_detail` | file non letto | errore, fallito, scartato |
| quanti file la scansione ha saltato, per motivo: calibrazione (`calibration`), somma di frame (`stack`), ancora in scrittura (`still_writing`) | `skipped_by_reason` | saltati | scartati, ignorati, esclusi |
| il frame riscritto da un programma accanto al suo originale: resta in archivio con le sue posizioni, ma le sue ore le conta l'originale | `copy_of` | copia | doppione, duplicato, gemello |
| cio' che un file dichiara di se': che e' stato calibrato, o che nomina due programmi diversi (uno lo ha scritto, l'altro lo ha ripreso). Non dice **chi**, e da solo non toglie niente: sceglie l'originale fra due copie, e il calibrato pesa piu' del riscritto | `rewrite_mark` | (non a schermo) | flag, elaborato, processato |
| cio' che l'header di un frame lascia da chiedere in Da confermare: la camera non c'e' (`night_rig.asks_camera`), il filtro non dice niente (`unfiltered.says_no_filter`), e se nomina l'ottica (`header_asks.names_the_optics`: allora sull'ottica non si chiede). Dipende solo dal grezzo e dal vocabolario: lo scrive `scan`, una volta | `asks_camera`, `asks_filter`, `names_optics` (`spine/header_asks.py`) | (non a schermo) | verdetto, flag |
| l'immagine elaborata che l'utente carica a mano | `final_photo` | foto finale | immagine finale, elaborata, master |
| il frame scelto dall'app per farne la miniatura di un oggetto | `preview` | anteprima | miglior frame, miniatura |
| l'insieme di tutto cio' che l'app sa; anche la pagina degli oggetti | `archive` | archivio / Archivio | libreria, catalogo, raccolta |
| una cartella di FITS indicata dall'utente (puo' averne piu' d'una) | `folder` | cartella | libreria, sorgente, radice |
| da mezzogiorno a mezzogiorno nel fuso del sito, con un sito | `night` | notte | serata, sessione, uscita |
| oggetto x notte x corredo | `session` | sessione | notte, serata, ripresa |
| il posto da cui si osserva | `site` | sito | postazione, luogo, localita' |
| le coordinate che l'header porta, arrotondate al chilometro: sono cio' su cui l'app chiede quando non tornano con nessuno dei siti dichiarati. Un **sito** lo dichiara l'utente, le **coordinate** le dice il file | `coordinates` | coordinate | sito, posto, postazione |
| una montatura in campo in una notte (chi ne ha due riprende due cose) | `station` | postazione | sito |
| il fuso orario del sito, ricavato dalle sue coordinate | `timezone` | fuso | zona, orario |
| l'ora che il file dice, UTC come vuole lo standard FITS: e' l'istante su cui la posa conta | `date_obs` | ora della posa | ora vera, ora corretta |
| quanto e' scuro il cielo di un sito, in magnitudini per arcosecondo quadrato: e' la misura | `sky_sqm` | luminosita' del cielo | SQM, brillanza |
| la classe di cielo da 1 a 9, ricavata dalla luminosita': si mostra col numero misurato accanto, **tranne in due posti** -- il primo avvio, dove si sceglie e non c'e' ancora niente da dichiarare, e il piede della barra, dove sono 227px e la classe e' un promemoria di dov'e' puntata l'app | `bortle` | Bortle | classe, qualita' del cielo |
| come si sa la luminosita' di un sito: misurata, chiesta al servizio, scelta sulla scala | `sky_source` | (una frase tradotta) | fonte, origine |
| l'altezza del sito sul livello del mare; assente vuol dire "non fornita", mai zero | `elevation_m` | altitudine | quota, altezza |
| come si sa l'altitudine di un sito: scritta da chi c'e' stato, o chiesta al servizio | `elevation_source` | (una frase tradotta) | fonte, origine |
| il sito da cui si osserva di solito: e' lui a dare il fuso alle notti. Uno solo | `is_default` | sito di casa | sito predefinito, principale, attivo |
| le domande del primo avvio (come mi chiamo, da dove osservo, dove stanno i file, la chiave Meteoblue facoltativa) | `wizard` | primo avvio | onboarding, configurazione iniziale, procedura guidata |
| la data in cui il primo avvio e' stato fatto o saltato: e' un fatto scritto, e non si riscrive | `onboarding_done_at` | timbro del primo avvio | flag, completato |

## Cio' che si fotografa

| cosa e' | nel codice | a schermo (it) | non si dice |
|---|---|---|---|
| cio' che e' stato fotografato, come entita' dell'archivio | `object` | oggetto | target, bersaglio, soggetto |
| in un campo con piu' oggetti, quello scelto come principale | `subject` | soggetto | oggetto principale, target |
| gli oggetti che il cielo ha trovato nei frame di un gruppo di Da confermare, il piu' ripreso in cima, coi frame dove non ha trovato niente (`not_found`) e quelli che non ha ancora guardato (`not_yet`): si leggono accanto alla domanda e non la cambiano. La domanda *che file sono* non li porta: li' il cielo non ha guardato niente | `subjects` | ripreso | soggetti, contenuto, target |
| una voce del catalogo astronomico | `catalog_entry` | voce di catalogo | oggetto |
| lo stesso soggetto seguito nel tempo con un corredo, fino alla foto finale; puo' avere un obiettivo | `project` | progetto | piano, lavoro, campagna |
| una riga dell'Archivio ripresa con la stessa ottica e la stessa camera, finche' non esistono i progetti (Marco, 8/10/2026; `docs/domini/archivio.md`) | `production` | produzione | corredo, sessione, progetto |
| le ore che si vogliono raggiungere su un progetto | `goal_hours` (`goal_seconds` in schema) | obiettivo | traguardo, target, meta |
| le ore per filtro dentro l'obiettivo | `recipe` | ricetta | piano filtri |
| progetto con pannelli affiancati sullo stesso soggetto | `mosaic` | mosaico | -- |
| una delle inquadrature affiancate di un mosaico | `panel` | pannello | tessera, riquadro |
| la chiave di un mosaico: l'impronta di uno dei suoi frame, scelta quando nasce e poi ferma, che non cambia con la camera. Sui frame di un mosaico confermato | `mosaic_key` | -- | ancora, id del mosaico |
| i pannelli e i mosaici scritti da `group`, una volta per frame | `panels`, `mosaics` | -- | -- |
| il pannello di un frame, scritto una volta | `panel_id` | -- | numero del pannello, tessera |
| se un pannello regge una parte del lavoro del suo mosaico: almeno il 25% del tempo del piu' lungo | `counts_in_mosaic` | pannello che conta | pannello minore, pannello scarto |
| centro, rotazione e rettangolo scelti nel Planner | `framing` | inquadratura | framing, campo |
| centro, scala, rotazione e rettangolo misurati dal solver | `wcs` / `footprint` | il cielo del frame / il campo | astrometria |
| il gruppo di un frame senza nome e senza cielo: la notte, la camera, il telescopio e il puntamento di chi ha aperto il gruppo. Lo scrive `identify` quando il frame arriva, e si risceglie solo se casa cambia fuso e la notte del frame con lei | `unnamed_key` | -- | cella, id del gruppo |
| un frame risolto nel cui campo il catalogo non ha nessun candidato: il cielo c'e', ma non dice cosa hai ripreso. Lo scrive `identify`, e resta quando il frame torna in coda | `empty_cone` | il cielo non ha trovato niente | vuoto, senza oggetto, non identificato |
| un frame che il solver non ha risolto | `unsolved` | non risolto | senza cielo, da risolvere, fallito |
| quanto sono larghe le stelle in un frame, in pixel: e' la misura del fuoco. La da' il solver nella sua passata di analisi | `hfd_px` | HFD | fuoco, nitidezza, FWHM |
| l'identita' di una voce di catalogo, stabile fra due ricostruzioni (gli id invece si rinumerano) | `slug` | sigla-chiave | id, codice, chiave |
| il numero che un oggetto porta dentro un catalogo (`224`); il catalogo sta accanto, in `catalog` | `designation` | designazione | numero, sigla |
| catalogo e designazione insieme, come si scrivono (`NGC 224`) | `catalog` + `designation` | sigla | nome, designazione |
| la designazione ridotta alla forma con cui si cerca, uguale per ogni grafia (`M31`, `m  31`, `Messier 31` -> `M|31`) | `key` | chiave della sigla | normalizzazione, slug |
| le stesse coordinate in cartesiane sulla sfera unitaria: rende un cerchio di cielo un riquadro su tre assi | `x, y, z` | versore | vettore, direzione |
| quanto dista un oggetto dal **centro di un frame**, in gradi | `sep_deg` | scarto | distanza, separazione |
| quanto distano **due direzioni del cielo** fra loro, in gradi: non e' lo scarto, e non ha un centro | `separation_deg` | distanza angolare | scarto, separazione |
| la voce di catalogo agganciata a un oggetto dell'archivio, con **come** si e' deciso e **quanto** ci si fida | `catalog_slug` + `identity_method` + `identity_confidence` | l'aggancio | ancora, match, identificazione |
| un oggetto che cade dentro il rettangolo vero dell'inquadratura, non solo nel cerchio che la contiene | `in_frame` | nell'inquadratura | dentro il campo, contenuto |
| quanto e' probabile che una voce sia il soggetto del frame: contenimento, luminosita', estensione, catalogo, centratura | `score` | punteggio | rank, peso, affinita' |
| quanto e' luminoso un oggetto, **con la banda in cui e' misurato**: la V si preferisce alla B | `magnitude` + `magnitude_band` | magnitudine | luminosita', mag |

## L'attrezzatura

| cosa e' | nel codice | a schermo (it) | non si dice |
|---|---|---|---|
| un pezzo: ottica, camera, filtro, montatura, riduttore, ruota, guida, focheggiatore | `instrument` | strumento | componente, dispositivo, device |
| la montatura di una posa: quella che hai scelto sul corredo, o dove taci quella che il file nomina | `mount_id` (su `frames`), `mount` (dichiarazione del corredo) | sulla {montatura}, Scegli la montatura | setup, postazione (la postazione e' un'altra cosa) |
| i generi che una posa porta in una colonna sua: ruota, focheggiatore, camera di guida, montatura | `CARRIED` (`spine/counts.py`) | -- | -- |
| perche' un pezzo contato non ha ore: i file non nominano quel genere, o nessun corredo porta quella montatura | `no_hours` (`files_silent`, `no_rig`) | i tuoi file non dicono..., nessun corredo la porta ancora | -- |
| la pagina che li elenca | -- | Attrezzatura | equipaggiamento |
| ottica + camera (+ riduttore) visti insieme, a una focale | `rig` | corredo | setup, configurazione, attrezzatura, impronta |
| un corredo simulato nel Planner, mai salvato | `trial_rig` | corredo di prova | -- |
| la dimensione di un pixel del sensore, senza binning: e' quella della scheda della camera | `instruments.pixel_size_um` | dimensione del pixel | pitch |
| la stessa grandezza come l'header la scrive (`XPIXSZ`), col binning gia' dentro: sta sul frame | `frames.pixel_size_um` | -- | pixel fisico |
| quanto e' servito ogni pezzo, corredo e filtro -- frame, ore, notti, oggetti, e per i corredi il cielo misurato -- scritto a fine giro di ogni stadio e letto dall'Attrezzatura | `gear_usage` | quanto ti e' servito | statistiche, contatori |
| i candidati del cielo di una scheda dell'oggetto in dubbio, o di frame detti "non e' un oggetto", dal piu' probabile: li scrive `spine/object_candidates.py` e li legge Da confermare | `object_candidates` | candidati | proposte, suggerimenti |
| se chi conta ha gia' contato un pezzo: falso per uno nato a meta' giro, che la pagina dice "si sta contando" e non "non si sa" | `counted` | si sta contando | in attesa, pending |
| il pixel di una camera ricavato dalla scala misurata sulle sue pose, la focale del corredo e il binning, quando i file non lo dicono | `instruments.pixel_from_sky_um` | pixel ricavato dal cielo | pixel stimato, pixel calcolato |
| il filtro davanti al sensore, come strumento | `filter` | filtro | vetro |
| la categoria di un filtro (L, R, G, B, Ha, OIII, SII, duo, OSC...) | `passband` | banda | tipo, canale, categoria |
| il filtro esplicito di chi non ha un vetro davanti: una riga sola, non un vuoto | `is_none` | nessun filtro | vuoto, senza filtro |
| cio' che l'header dice dell'attrezzatura, e la chiave della domanda su di essa: grafia di camera e telescopio (non quella che il programma dice montatura), focale entro il 5 %, sensore e pixel; mai la notte o la cartella | `signature` (`spine/signature.py`) | firma | impronta, gruppo |
| la scheda di Da confermare su una firma: chiede solo cio' che i frame lasciano fuori -- la camera, l'ottica, il filtro (su una camera non a colori, senza i frame con la matrice) -- e conta finche' ogni parte chiesta non ha risposta | `gear`, `GearSignature` | attrezzatura da completare | frame senza camera, frame senza ottica, frame senza filtro |
| la risposta su una firma: i NOMI di camera e ottica con la focale, e cosa c'era davanti -- nessun filtro (`no_filter`) o uno dei tuoi (`filter`, col nome del filtro in un campo suo). "A colori" (`color`) si scrive sulla scheda della camera | `GearEdit`, `signature.Answer` | risposta sull'attrezzatura | correzione, filtro dichiarato |
| i filtri fra cui si sceglie una risposta: quelli con la banda nota, tranne la riga "nessun filtro" | `filter_choices` | i tuoi filtri | candidati, proposte |
| i corredi fra cui si sceglie con che camera sono stati ripresi dei frame: quelli con una camera e almeno un frame | `rig_choices` | i tuoi corredi | candidati, proposte |
| i frame che non dicono **che file sono** -- l'header non porta `IMAGETYP` e nessuno l'ha ancora detto -- raggruppati per la cartella che li contiene; ci sono solo quelli su cui il cielo non sa dire (risolto e' una foto, senza stelle una calibrazione). Restano fermi prima dell'oggetto, quindi non diventano ore e non compaiono fra i frame senza nome | `typeless` | frame senza tipo | tipo mancante, tipo sconosciuto, non classificati |
| la risposta su una cartella di frame senza tipo: una foto del cielo (`light`) o un file di calibrazione (`calibration`) | `TypelessAnswer` | tipo della cartella | classe, categoria |
| il frame aspetta una risposta sul tipo: la regola sta in `spine/stages.py`, e l'esito lo scrive sulla posa chi cambia un suo ingresso -- il cielo, la posizione del file, la risposta della cartella; chi legge legge questo | `asks_type` | aspetta una risposta | bloccato, sospeso |
| le cartelle della domanda sul tipo coi frame che contano, scritte a fine scansione, a fine cielo e a fine normalizzazione e quando togli o rimetti una cartella, e lette da Da confermare; la risposta si legge dalla sua casa | `typeless_folders` | frame senza tipo | cache, conteggi |
| la notte di un frame, da mezzogiorno a mezzogiorno nel fuso delle coordinate dell'header o di casa (UTC se non si sa), o del giorno in cui il file e' stato scritto se manca `DATE-OBS`: la scrive `scan` quando il frame entra, e si riscrive se il fuso non viene dalle coordinate dell'header e casa cambia fuso | `local_night`, `local_tz`, `night_instant` (l'istante da cui viene) | notte della posa | notte UTC, data della posa |
| la camera che gli header di una notte (la notte della posa) dicono, quando e' una sola, con l'ottica e la focale se anche quelle sono una sola: il frame che non le dice prende cio' che il suo file tace | `night_rigs` | corredo della notte | camera della notte, camera dedotta, camera indovinata |
| la cartella che contiene il file di un frame, non la radice registrata: una sola per frame, ed e' quella con cui si chiede che file sono i frame senza tipo | `frame_folder` | cartella dei frame | sottocartella, radice, sorgente |
| i frame che non dicono l'oggetto e di cui il cielo non dice niente, raggruppati per notte, camera, telescopio e dove puntava la montatura (entro un campo inquadrato da chi ha aperto il gruppo, scelto quando il frame arriva e riscelto solo se casa cambia fuso e con lei la notte del frame), non per cartella | `unnamed` | frame senza nome | orfane, sconosciute, non identificate |
| la scheda di Da confermare che chiede l'oggetto di un gruppo di frame: quelli che l'app ha messo su un oggetto, o un gruppo di frame senza nome; coi candidati del cielo, anche zero | `ObjectCard` | scheda dell'oggetto | sezione Oggetti, sezione Senza nome |
| la risposta su una scheda dell'oggetto: un oggetto di catalogo, un nome scritto, oppure "non e' un oggetto" | `ObjectAnswer` | oggetto del gruppo | oggetto dichiarato, etichetta, risposta sulla cartella |
| cio' che `identify` aveva trovato per un frame detto "non e' un oggetto": la chiave della sua scheda, che resta per cambiare idea | `found_key` | -- | oggetto originale, vecchio oggetto |
| la risposta su quel gruppo: i nomi di ottica e camera con la focale, e da quei nomi i pezzi nascono | `GroupRig` | risposta sul gruppo | corredo dichiarato, assegnazione |
| la combinazione di bande di un progetto (LRGB, SHO, HOO) | `scheme` | schema | palette |

## Da dove viene un valore

| cosa e' | nel codice | a schermo (it) | non si dice |
|---|---|---|---|
| ricavato dall'app: header, solver, misura, catalogo | `detected` | rilevato | dedotto, calcolato, automatico, letto |
| impostato dall'utente; vince sul rilevato, sopravvive ai reset, si esporta | `declared` | dichiarato | impostato, manuale, override |
| il perche' un valore manca, come codice chiuso | `reason` | (una frase tradotta) | muto, null, n/d |
| la pagina delle domande dell'app su cio' che la scansione ha trovato -- filtri, grafie che sembrano un pezzo solo, gruppi di frame, siti, mosaici, oggetti -- perche' l'utente risponda a cio' che l'app non puo' sapere | `review` | Da confermare | dati mancanti, revisione, Da completare |
| la regola imparata li': "quando l'header dice X, e' Y" | `header_alias` | regola imparata | alias, mappatura, sinonimo |
| due grafie dello stesso pezzo o dello stesso filtro diventano una riga sola: la grafia assorbita diventa una regola verso quella tenuta, e la regola vale anche sul nome che il vocabolario da'. `mergeable_into` sono i pezzi in cui uno si puo' unire | `merge_into` | unione, "e' lo stesso di" | fusione, accorpamento |
| due grafie che hanno l'aria di essere la stessa camera -- stesso nome tolte le annotazioni, stesso pixel, stesso colore -- e la domanda se lo sono: si' e' l'unione, no (`not_same_as`, sulla camera chiesta col nome dell'altra, che la segue se cambia nome) la spegne per quella coppia | `lookalike` | stesso pezzo? | doppione, duplicato |
| la parola dell'utente su un oggetto che l'app ha trovato: "quello, per me e' quest'altro" -- si rilegge a ogni giro, e sposta i frame | `correction` | correzione | mappatura, override, rinomina |
| la chiave con cui si parla di un oggetto da fuori (lo slug di catalogo, o il suo nome), mai il numero di riga | `stable_key` | chiave dell'oggetto | id, identificativo |

## Il cielo e il tempo

| cosa e' | nel codice | a schermo (it) | non si dice |
|---|---|---|---|
| la notte **in corso**, nel fuso del sito: da mezzogiorno a mezzogiorno, quindi alle dieci del mattino e' ancora quella di ieri sera | `tonight` | stanotte | oggi, stasera |
| che luna fa: il nome della fase e quanto e' illuminata | `moon` | la Luna | fase lunare |
| quale delle otto fasi, come parola chiusa (`new`, `full`, `waxing_gibbous`...) | `phase_key` | nuova, piena, gibbosa crescente... | fase, numero della fase |
| quanta della faccia visibile e' illuminata, in percento | `illumination_pct` | illuminata al {n}% | luminosita', luce |
| quando la Luna passa sopra l'orizzonte **stanotte**, o niente se non succede stanotte | `rise` | sorge | alba della Luna |
| quando ci passa sotto **stanotte**, o niente se non succede stanotte | `set` | tramonta | tramonto lunare |
| il punto **piu' alto della notte**: quando, e a quanti gradi. E' il massimo dentro la finestra, che ogni tanto non contiene una culminazione vera | `highest` | sale fino a | culmina, culminazione, transito (vietate **per la Luna**: un oggetto del Planner invece culmina davvero) |
| quanto e' alto un corpo sull'orizzonte, in gradi: **negativo** quando sta sotto | `altitude_deg` | alto {n} gradi | altitudine (e' l'altezza del sito sul mare), elevazione, quota |
| l'altezza della Luna campionata lungo la notte, per chi la disegna | `track` | l'andamento della notte | traiettoria, percorso, serie |
| quanto in alto la Luna puo' arrivare **da questo sito**, mai di piu': il bordo alto del grafico, e dipende solo dalla latitudine | `ceiling_deg` | il tetto del sito | massimo, culmine, zenit |
| ore fra i due crepuscoli astronomici | `dark_hours` | ore di buio | notte |
| la notte divisa nei pezzi in cui il cielo e' sempre la stessa cosa, ognuno con **da quando a quando**: escono gia' divisi, perche' quali crepuscoli ci siano dipende da dove sei | `sky_bands` | le fasce del cielo | strisce, crepuscoli (che sono **tre** delle cinque), bande |
| il Sole sopra l'orizzonte | `day` (una fascia) | giorno | luce |
| il Sole fra l'orizzonte e sei gradi sotto: fuori serve gia' la luce artificiale | `civil` | crepuscolo civile | imbrunire, tramonto (che e' l'istante) |
| fra sei e dodici gradi sotto: in mare l'orizzonte si distingue ancora | `nautical` | crepuscolo nautico | -- |
| fra dodici e diciotto: l'ultima luce del Sole se ne va | `astronomical` | crepuscolo astronomico | -- |
| sotto i diciotto gradi: la luce del Sole e' meno di quella delle stelle, ed e' il buio di chi fotografa il cielo | `dark` (una fascia) | buio | notte (che e' la finestra da mezzogiorno a mezzogiorno), nero, **buio pieno** (che e' la classe 1 di Bortle, e si legge nello stesso piede) |
| ore di buio con cielo sereno (sotto la soglia) | `usable_hours` | ore utili | ore buone |
| la parola del meteo sulla notte: si fa / incerta / no | `verdict` (`go`, `marginal`, `nogo`) | verdetto | voto, punteggio |
| una grandezza della notte, col suo valore, il picco e (se ha soglia) la sua parola | `measure`, `measures` | misura | parametro, indicatore |
| una misura che nella notte diventa incerta o niente: sta accanto al verdetto e non lo cambia | `weighs` | pesa, cosa pesa | fattore, allarme |
| la parola di una misura in un'ora o nella notte: buona, incerta, niente (aerosol: limpido, molto fosco; Luna: al limite, solo banda stretta) | `level`, `levels` (`go`, `marginal`, `nogo`) | giudizio | voto, punteggio, semaforo (che e' il verdetto) |
| le misure con soglia | `cloud`, `cloud_low`, `rain`, `gust`, `wind`, `condensation`, `jet`, `seeing`, `aerosol`, `moon` | nuvole, nuvole basse, pioggia, raffiche, vento, condensa, jet stream, seeing, aerosol, Luna | umidita' (che e' neutra) |
| le soglie di ogni misura, dalla peggiore, come le usa il giudizio | `scales`, `steps` | soglie | limiti |
| su quali ore si giudica una notte: il buio, o dove il buio non arriva l'arco col Sole sotto l'orizzonte | `window` (`dark`, `sun_down`) | le ore di buio / col Sole sotto l'orizzonte | finestra osservativa |
| il modello numerico da cui viene la previsione, che l'utente sceglie | `weather_model`, `model` (`best_match`, `ecmwf_ifs025`, `icon_seamless`, `gfs_seamless`) | modello della previsione | fonte, servizio (il servizio e' Open-Meteo) |
| quando e' arrivata la previsione che si legge | `fetched_at` | arrivata il... alle... | aggiornata, scaricata |
| una notte oltre la terza: il verdetto, le nuvole, le ore di buio e l'accordo, detti meno affidabili | `trend` | tendenza | previsione lunga |
| quanti modelli dicono si fa, incerta, no | `agreement` | modelli d'accordo | consenso, affidabilita' |
| cio' che conta per la planetaria, ora per ora: vento in quota, seeing, aerosol (campi dell'ora) | `wind_*hpa_kmh`, `seeing_arcsec`, `aerosol_optical_depth`, `dust_ugm3` | il cielo in quota | alta quota, atmosfera |
| il vento a 250 e 200 hPa | `wind_250hpa_kmh`, `wind_200hpa_kmh` | jet stream | corrente a getto |
| il vento a 700 hPa, circa 3.000 metri, medio nelle ore su cui si giudica una notte | `wind_700hpa_kmh` | vento in quota | turbolenza |
| il vento in quota solito di un sito: un anno di notti, scritto una volta l'anno | `weather_climate`, `climate.py` | il solito del sito | climatologia, media |
| quante notti su dieci dell'ultimo anno del sito avevano meno vento in quota | `wind_700hpa_tenths`, `position.py` | piu' forte di N notti su 10 | percentile, soglia |
| il riassunto della notte in corso che legge Stanotte | `WeatherBriefOut`, `tonight.weather` | il meteo di stanotte | -- |
| il meteo vero di una notte passata, dall'archivio, definitivo dopo cinque giorni | `observed` (tipo di `weather_nights`), `open-meteo/archive` | lo storico, il cielo di quella notte | consuntivo |
| il cielo di una notte passata detto con le classi del verdetto (FEW, SCT, BKN/OVC) | `verdict` di una riga `observed` | poco, parzialmente, molto nuvoloso | sereno, velato, coperto (velato dice nuvole alte, il verdetto guarda la copertura) |
| se il cielo di una notte c'e', arriva, o non si puo' sapere | `weather.state` (`ok`, `waiting`, `unknown`) | -- | -- |
| la chiave personale di Meteoblue, per il seeing ora per ora; fuori esce solo come finisce | `meteoblue_key`, `hint` | chiave Meteoblue | password, token |
| l'ultimo tentativo di una fonte che non deve ripetersi troppo spesso (Meteoblue, lo storico), e com'e' andato | `weather_fetches`, `status` (`ok`, `refused`, `unreachable`, `bad_answer`) | ultimo tentativo | log, cronologia |
| se il seeing c'e': viene solo da Meteoblue, con la chiave dell'utente | `seeing.source` (`meteoblue` o vuoto) | il seeing viene da Meteoblue | fonte del seeing |
| la sezione delle Impostazioni con le chiavi dei servizi | `/impostazioni/servizi` | Servizi | account, integrazioni |
| lo spessore ottico degli aerosol e le polveri, da CAMS | `aerosol_optical_depth`, `dust_ugm3` | aerosol, polveri | trasparenza, smog |
| il seeing di Meteoblue in secondi d'arco, un valore per ora | `seeing_arcsec` | seeing | qualita' del cielo, fascia |
| i modi di restringere una ricerca nel Planner | `criteria` | criteri | filtri |
| la linea di alberi e case attorno a un sito | `horizon` | orizzonte | maschera, profilo |
| altezza minima, distanza dalla Luna, ore minime: i tre numeri di fabbrica | `thresholds` | soglie | preferenze |

## Le pagine, e come si arriva

Lo scheletro -- i gruppi, l'ordine, cosa vive in alto -- sta in
[`navigazione.md`](navigazione.md). Qui ci sono solo i **nomi**: uno per cosa, e l'indirizzo con
cui ci si arriva (in italiano, come `/da-confermare`, perche' un indirizzo l'utente lo legge e lo
manda a qualcuno).

| cosa e' | indirizzo | a schermo (it) | non si dice |
|---|---|---|---|
| la pagina di apertura: cosa e' successo e cosa c'e' da fare | `/` | Casa | dashboard, home, cruscotto |
| la pagina degli oggetti: cosa hai ripreso, con le sue ore | `/archivio` | Archivio | libreria, catalogo, raccolta |
| le notti, una per una, con cosa e' stato ripreso | `/notti` | Notti | sessioni, serate, uscite |
| gli strumenti, i corredi e i filtri che possiedi | `/attrezzatura` | Attrezzatura | equipaggiamento, setup |
| i confronti nel tempo: stagioni, corredi, filtri, qualita' | `/statistiche` | Statistiche | analitica, report, grafici |
| le cartelle di FITS che hai indicato, e cosa e' successo l'ultima volta che l'app le ha lette: **una sezione di Impostazioni**, non una pagina in barra | `/impostazioni/cartelle` | Cartelle | importa, sorgenti, libreria, scansione |
| le domande dell'app (la voce e' in *Da dove viene un valore*) | `/da-confermare` | Da confermare | revisione, dati mancanti |
| le letture passate: cosa e' entrato, cosa e' rimasto fuori e perche', **coi file non letti** | `/impostazioni/letture` | Le letture | corse, passate, storico |
| perche' l'app non parte o non funziona: il diario, il solver che non si avvia, lo stato del sistema | `/diagnostica` | Diagnostica | log, errori, problemi |
| dove si decide una ripresa che non esiste ancora: si cerca, si inquadra, nasce un progetto | `/planner` | Planner | pianificatore, programma |
| i progetti e a che punto sono, con quanto manca all'obiettivo | `/progetti` | Progetti | piani, campagne |
| la carta su cui si naviga il cielo | `/carta-del-cielo` | Carta del cielo | mappa, sky map, atlante, cielo |
| la notte ora per ora intorno al buio, col verdetto | `/meteo` | Meteo | previsioni, tempo |
| cio' che l'app non deduce dai file, a sezioni: le cartelle, i siti, il nome, le chiavi dei servizi, le soglie | `/impostazioni` | Impostazioni | preferenze, configurazione, opzioni |
| il pulsante che fa leggere le cartelle, col verbo che decide il backend | `action` (`start`/`stop`/`resume`) | Scansiona / Ferma / Riprendi | importa, indicizza, aggiorna, sincronizza |
| il programma che riconosce cosa hai ripreso confrontando i frame col cielo: si chiama **ASTAP**, col suo nome ovunque: anche il passo del primo avvio e la sezione delle Impostazioni | `astap` / `solver` | ASTAP (cio' che fa si chiama *plate solving*, e si scrive una volta, dove ASTAP si presenta) | riconoscitore, plate solver, risolutore, astrometria |
| quello che manca all'app per fare il suo mestiere, come codice e non come frase | `missing` (`no_active_site`, `no_solver`) | (una frase tradotta) | errore, allarme |
