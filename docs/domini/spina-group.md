# La spina: `group` -- contratto

Lo stadio `group` mette insieme notti e sessioni, e chiede da dove hai ripreso.
Cio' che vale per tutta la catena sta in [`spina.md`](spina.md).

## Cosa chiede l'utente

| richiesta | prova |
|---|---|
| Le notti vanno da mezzogiorno a mezzogiorno nel fuso del mio sito; una sessione e' oggetto x notte x setup | `test_group_night_in_site_tz`, `test_group_session_key` |
| Se l'app non e' sicura da dove ho ripreso non inventa la notte: i frame restano in attesa col loro perche' | `test_group_asks_when_the_coordinates_say_elsewhere`, `test_group_invents_no_night_without_an_answer` |
| E me lo chiede una volta per **posto**, non per notte e nemmeno per frame, proponendomi i miei siti col piu' vicino in cima | `test_the_nights_section_asks_about_the_places_that_do_not_add_up`, `test_the_places_are_proposed_with_my_sites_the_nearest_first` |
| Rispondo una volta e quei frame vanno nella loro notte -- e le notti che riprendero' li' non me lo richiedono | `test_answering_where_i_was_puts_those_poses_in_their_night`, `test_the_answer_holds_for_the_nights_that_will_come` |
| L'ora di un frame e' quella di `DATE-OBS`, in UTC come dice lo standard FITS: l'app non me la chiede e non la corregge | `test_the_date_of_the_pose_is_utc_even_when_the_local_one_disagrees` |

## Le decisioni

**`group` mette insieme le notti e le sessioni.** La notte va **da mezzogiorno a mezzogiorno
nel fuso del sito**, mai in UTC: sull'archivio di collaudo le due strade danno lo stesso
risultato (zero frame cambiano notte), quindi la regola non e' per Marco -- e' per chi riprende
dove il fuso conta, ed e' la decisione che il vecchio aveva gia' rovesciato una volta. Una
**sessione** e' oggetto x notte x setup, coi filtri dentro: cambiare telescopio o camera a
meta' notte apre un'altra sessione. La chiave della sessione e' un indice **su un'espressione**
perche' un setup che non si e' potuto sapere e' vuoto, e in SQLite due vuoti non contendono.

**Da dove hai ripreso si chiede, non si indovina.** Le coordinate dell'header sono un indizio:
entro **1 km** da un sito dichiarato si tace -- casa, o il piu' vicino fra gli altri -- perche'
una coordinata scritta con due decimali si sposta gia' di 1,1 km e sotto quella soglia la
differenza e' in come e' scritta, non in dove eri
(`test_a_frame_shot_at_another_declared_site_goes_there_without_asking`,
`test_between_two_declared_sites_the_nearest_wins`). Lontano da tutti, la notte **non nasce**: i suoi frame restano in attesa col codice `site_unclear`. Il motivo per cui
non si indovina e' che un GPS o una rete possono sbagliare, e una notte attribuita male e' un
dato falso che nessuno rilegge (scelta di Marco, 2026-09-09).

**La domanda si fa per COORDINATE, non per notte.** La sezione *Frame senza sito* di Da
confermare chiede *"questi frame da quale sito?"* proponendo i siti dichiarati **in ordine di
distanza da quelle coordinate**, il piu' vicino in cima. Un gruppo per posto e non per notte perche' la risposta e'
un fatto sul posto: vale per tutte le notti riprese li', **anche quelle che verranno** -- come la
regola imparata sui nomi degli oggetti. Sull'archivio di collaudo questo trasforma cinque notti
sparse in **due domande**: 391 frame a 16 km da casa e 41 a 64 km.

La risposta vive in `declarations` sulle coordinate arrotondate al chilometro, quindi sopravvive
a un azzeramento del rilevato, e porta il **nome** del sito e non il suo numero di riga: gli id
si riusano, e una risposta scritta su un id finirebbe addosso a un altro sito in silenzio. Se
quel sito cambia nome la risposta lo segue (`domini/sito.md`); se sparisce, la risposta non
aggancia piu' e l'app torna a chiedere -- che e' la direzione sicura. La notte che ne nasce e' **`declared`** -- anche quando la risposta e'
"ero a casa", perche' cio' che conta e' che l'abbia detto l'utente -- e da li' in poi non la
sposta piu' nessuno: ne' il trasloco di casa, ne' la spazzata.

**Un gruppo a cui si e' gia' risposto resta in pagina**, con la risposta accanto: un clic
sbagliato attribuisce centinaia di frame, e rispondere di nuovo li sposta tutti. E' la stessa
lezione della seconda risposta sugli oggetti, che il primo giro di quella casella aveva
ignorato in silenzio. La proposta invece si **ricalcola alla lettura** e non si salva: uno stato salvato
invecchierebbe al primo sito nuovo. E le domande aperte **contano** in "da confermare", ma non
si chiudono con l'Applica: "ho visto la pagina" non e' una risposta a "da dove hai ripreso".

**L'ora del frame e' `DATE-OBS`, in UTC** (Marco, 23/9/2026): e' cio' che dice lo standard
(accordo IAU-FWG sulle date FITS, <https://fits.gsfc.nasa.gov/year2000.html>, 4.4: *"The
default interpretation shall use UTC"*), e l'app non la corregge con `DATE-LOC` ne' la chiede.

**Senza un sito dichiarato non nascono notti**, e l'app lo dice col codice `no_active_site`
(contratto del sito): a mani vuote non si inventa un fuso. Ogni altro motivo per cui un frame
resta fuori da una sessione ha il suo codice e si conta nella ricevuta: `site_no_timezone` (del
sito non si riconosce un fuso; in mare aperto vale quello nautico), `site_unclear`, `no_date` (un
software che non scrive `DATE-OBS` esiste; sull'archivio di collaudo non capita mai) e
`no_object`, per un frame che `identify` ha lasciato senza oggetto. Quest'ultimo arriva fin qui
**apposta**: se lo stadio non lo vedesse resterebbe `pending` per sempre, il residuo non
arriverebbe mai a zero e il pulsante Avvia partirebbe a vuoto a ogni clic.

**Si tocca solo cio' che e' in coda per questo stadio** -- a un frame rimesso in coda la
sessione vecchia si stacca all'inizio della corsa -- e rifarla non ri-chiave niente:
una notte il cui sito hai dichiarato tu non si sposta **mai** da sola, e cambiare il sito di
casa adotta le notti attribuite in automatico e nessun'altra. Unire due grafie di un pezzo in Da
confermare rimette in coda anche `group`, o le sessioni resterebbero appese al setup sparito.

**Cosa `group` NON fa**: non salva ore ne' medie -- si contano leggendo, e un numero derivabile
non si congela in una colonna; i mosaici li scrive, ma la loro casa e' `mosaico.md`; non tocca i FITS.
