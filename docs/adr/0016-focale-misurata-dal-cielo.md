# 0016 -- La focale di un frame si misura dal cielo, l'header e' il ripiego

**Stato:** accettata, 6/10/2026 (Marco).

## Contesto

La focale veniva solo da `FOCALLEN`, cio' che l'utente ha scritto nel programma di ripresa: con
un riduttore spesso resta la focale nativa, e il corredo nasce sbagliato. Le focali entro il 5 %
si raggruppano sui soli frame di un giro (`units.focal_buckets` in `normalize`), quindi lo stesso
archivio letto in un altro ordine puo' dare corredi diversi (*Il corredo di un frame dipende da
quando e' stato letto*, `docs/coda.md`).

Misura sull'archivio di Marco, dalla cache di ASTAP (10.898 frame risolti su 10.909): la focale
misurata oscilla al massimo dello 0,23 % (5-95 percentile) dentro un treno ottico; l'header, dove
Marco scrive la focale effettiva, ne dista al massimo lo 0,4 %; le tre grafie 559/560/561 della
stessa Canon misurano tutte 560.

## Decisione

- **Focale misurata**: dopo una soluzione, `206,265 x pixel / scala` (pixel in micron con il
  binning dentro, come `XPIXSZ`; scala in secondi d'arco per pixel binnato), arrotondata al
  millimetro, scritta accanto alla soluzione (`frame_wcs.focal_mm`). Il pixel e' `XPIXSZ`, o il
  pixel della scheda della camera (dichiarato o votato dai file) per il binning; **mai** il pixel
  ricavato dal cielo, che usa la focale del corredo. Senza pixel, niente focale misurata.
- **Focale del frame** = misurata se c'e', altrimenti `FOCALLEN`. La usa `normalize` per il
  corredo; firme dell'header e notte restano sull'header, perche' chiedono cio' che i file dicono
  e girano prima del cielo.
- **Il corredo nasce provvisorio e il cielo lo corregge**: `normalize` gira prima di `solve` e
  decide il corredo con la focale che ha. A fine soluzione, se la focale misurata non e' quella del
  corredo del frame (stessa regola di tolleranza dei corredi), il frame torna a `normalize`, che
  ora la legge nello stesso giro: lo stadio `solve` della coda (`run.queue`) rifa' `normalize`
  prima del suo `done`, perche' nella coda `normalize` e' gia' passato e `identify` lo aspetta.
  Nessun ciclo: rifatto, il corredo e' quello della misura, e il solver non rientra
  (`downstream(NORMALIZE)` non contiene `solve`).
- **La tolleranza resta il 5 %**: separa riduttori e moltiplicatori (passi del 15 % e oltre) e
  assorbe l'header scritto a mano dei frame senza cielo. Nessuna convenzione pubblica dice quando
  due focali sono lo stesso treno ottico: il numero si regge sulla misura sopra, 20 volte piu'
  stretta.

## Conseguenze

- Un frame risolto non dipende piu' da quando e' stato letto per il suo corredo: le focali
  misurate dello stesso treno stanno nello 0,3 %, e il raggruppamento non le separa mai. Restano
  dipendenti dall'ordine solo i frame senza cielo con focali scritte a mano a cavallo del 5 %.
- Chi monta un riduttore e scrive la focale nativa vede, dopo il solver, i frame passare al
  corredo della focale vera; il corredo dell'header, rimasto vuoto, sparisce come ogni corredo
  vuoto.
- Il solver costa un giro di `normalize` in piu' solo ai frame il cui corredo cambia.
