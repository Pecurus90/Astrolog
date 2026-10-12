# Per Claude Design -- Meteo: allineare la tavola all'app

Le tavole del Meteo (`pagine/meteo.html`, `meteo-telefono.html`, `meteo-stati.html`, generate da
`docs/proposte/meteo.js` e `telefono.js`) sono ferme al v27 del 3 ottobre. L'app e' andata avanti:
il 9 ottobre Marco ha rivisto tutto il linguaggio, e due regole sono diverse. Si chiede di
riportare le tavole a cio' che l'app dice e fa oggi. **Nessuna forma nuova**: stessi mattoni,
stessa disposizione.

## 1. Cosa correggere

1. **I testi.** Tutti quelli a schermo si prendono dal vocabolario qui sotto (sezione 2), parola
   per parola, maiuscole e punti compresi. Sono gia' approvati: non vanno riscritti. Se un testo
   non regge nella forma, dillo a parte. Le sostituzioni che pesano di piu':

   | sulla tavola | nell'app |
   |---|---|
   | niente | non adatta |
   | pesano, senza cambiare il semaforo | Altri fattori (non modificano il verdetto) |
   | Previsione arrivata oggi alle 13:00, 2 ore fa | Previsione del {giorno}, {ora} ({fa}) |
   | seeing arrivato alle 06:00, 9 ore fa | Seeing del {giorno}, {ora} ({fa}) |
   | ora del sito | ora locale del sito |
   | Scelto per il tuo posto · di fabbrica | Automatico · predefinito |
   | corrente a getto / Corrente a getto | jet stream / Jet stream |
   | passa sul cielo: le carte vanno a quell'ora | Passa sul grafico per vedere i valori di quell'ora. |
   | a destra, una alla volta | Scala di destra |
   | nessuna · solo le nubi | Nessuna · solo nubi |
   | senza giudizio | Senza valutazione |
   | la notte, sul buio | Riepilogo delle ore di buio |
   | in tutto nel buio | totale nel buio |
   | aria meno rugiada, il minimo | minimo di temperatura meno punto di rugiada |
   | 2 notti su 10 avevano meno vento | superiore a 2 notti su 10 in questo sito |
   | non fornito | non disponibile |

   «tocca le barrette di una carta per l'ora» nell'app non c'e': se serve, resta parola di tavola
   col filo tratteggiato, e la scrive Marco.

2. **Jet stream: nessun gradino «incerta».** Buona sotto 126 km/h, non adatta da 126 in su. Va
   tolta la linea di soglia a 108 e la parola «incerta dalle 03» di domenica.

3. **Le raffiche hanno un giudizio loro**: non adatta da 29 km/h (Beaufort 5). Quando pesano hanno
   una riga loro fra gli altri fattori («Raffiche dalle … alle … · N ore»), separata dal vento
   medio. Domenica, con raffiche fino a 44 km/h, la riga ci deve essere. La carta resta una sola,
   «Vento», con le raffiche disegnate sopra le barrette come oggi.

4. **Le parole della Luna sono sue**: «buona per la banda larga» fino al 25% illuminata, «al
   limite» fino al 50%, «solo banda stretta» oltre. Sulla tavola oggi ha «niente» e «incerta».

5. **L'ordine delle carte e degli altri fattori** lo decide il backend: Nuvole, Nuvole basse, poi
   le misure giudicate dalla parola peggiore (non adatta, incerta, senza parola, buona), a pari
   parola quella che comincia prima; poi le neutre. Un aerosol senza parola sta **prima** delle
   misure buone, non in fondo.

6. **Difetti di disegno**, desktop 1440:
   - nel cielo lo «0%» della scala di sinistra e l'ultimo numero di quella di destra sono tagliati
     dal bordo basso;
   - nella carta del seeing il segno dei secondi d'arco accanto alla cifra non si legge;
   - fra la riga del modello e la fila delle notti resta una fascia vuota;
   - le carte grandi vanno 5 + 3 e lasciano due posti vuoti.

7. **Dati di tavola che non tornano**: il vento medio di domenica e' 15 km/h, non 18 (media delle
   ore di buio della tavola stessa); la Luna nel pannello Stanotte (62%, sorge alle 23:40) e nella
   pagina (55%, dalle 23) deve essere la stessa.

Sul telefono (`meteo-telefono.html`, rifatta il 12 ottobre) valgono gli stessi sette punti: i
testi vecchi ci sono ancora.

## 2. Il vocabolario del Meteo

Copiato da `frontend/src/i18n/it-meteo.ts`. Fra graffe i valori che l'app riempie. Dove c'e' una
forma «una sola» e' il singolare della riga sopra.

### La pagina e i suoi stati

| testo | dove |
|---|---|
| Meteo | `weather.title` |
| Caricamento… | `weather.loading` |
| Previsione non disponibile | `weather.failed` |
| Sito predefinito mancante | `weather.noSite.title` |
| La previsione richiede un sito predefinito. | `weather.noSite.why` |
| Aggiungi sito | `weather.noSite.how` |
| Fuso orario del sito non riconosciuto: le notti non sono calcolabili. | `weather.noTimezone` |
| Modifica sito | `weather.noTimezone.how` |
| Nessuna previsione disponibile. | `weather.never` |
| La previsione si aggiorna ogni tre ore. | `weather.never.how` |
| Aggiorna | `weather.refresh` |
| Aggiornamento… | `weather.refreshing` |
| Aggiornamento non riuscito | `weather.refresh.failed` |
| Aggiornamento delle {ora} non riuscito. Previsione delle {prima}. | `weather.silent.unreachable` |
| Aggiornamento delle {ora} non riuscito. Nessuna previsione disponibile. | `weather.silent.unreachable.none` |
| Risposta non valida dal servizio alle {ora}. Nessuna previsione disponibile. | `weather.silent.bad_answer.none` |
| Risposta non valida dal servizio alle {ora}. Previsione delle {prima}. | `weather.silent.bad_answer` |
| Sito predefinito mancante: previsione non disponibile. | `weather.status.no_site` |
| Fuso orario del sito non riconosciuto: le notti non sono calcolabili. | `weather.status.no_timezone` |
| Nessuna notte disponibile per questo modello. | `weather.noNights` |

### La testa: dove, quando, il modello

| testo | dove |
|---|---|
| meteo a {sito} | `weather.head.where` |
| Previsione del {giorno}, {ora} ({fa}) | `weather.head.arrived` |
| Seeing del {giorno}, {ora} ({fa}) | `weather.head.seeing` |
| ora locale del sito | `weather.head.siteTime` |
| modello | `weather.model` |
| Cambio del modello non riuscito | `weather.model.failed` |
| Automatico | `weather.model.best_match` |
| ECMWF | `weather.model.ecmwf_ifs025` |
| ICON | `weather.model.icon_seamless` |
| GFS | `weather.model.gfs_seamless` |
| predefinito | `weather.model.best_match.what` |
| centro europeo | `weather.model.ecmwf_ifs025.what` |
| servizio meteo tedesco | `weather.model.icon_seamless.what` |
| servizio meteo americano | `weather.model.gfs_seamless.what` |

### La fila delle sette notti

| testo | dove |
|---|---|
| Le sette notti | `weather.nights` |
| ora per ora | `weather.nights.hourly` |
| tendenza, meno affidabile | `weather.nights.trend` |
| {n} ore · {da}–{a} | `weather.night.clear` |
| 1 ora · {da}–{a} | `weather.night.clear.one` (una sola) |
| nessuna serena | `weather.night.noneClear` |
| {n} ore di buio | `weather.night.dark` |
| 1 ora di buio | `weather.night.dark.one` (una sola) |
| Notte di {giorno} | `weather.night.name` |
| stanotte | `weather.night.tonight` |
| tendenza | `weather.night.trend` |

### La testa della notte

| testo | dove |
|---|---|
| {n} ore | `weather.clear.hours` |
| 1 ora | `weather.clear.hours.one` (una sola) |
| di buio sereno | `weather.clear.dark` |
| serene col Sole sotto l'orizzonte | `weather.clear.sun_down` |
| serena col Sole sotto l'orizzonte | `weather.clear.sun_down.one` (una sola) |
| Nessuna | `weather.clear.none` |
| ora di buio sereno | `weather.clear.none.dark` |
| ora serena col Sole sotto l'orizzonte | `weather.clear.none.sun_down` |
| dalle {da} alle {a}, {n} ore | `weather.clear.when` |
| dalle {da} alle {a}, 1 ora | `weather.clear.when.one` (una sola) |
| accordo dei modelli {n} su {su} | `weather.clear.agreement` |
| di buio | `weather.clear.trend` |
| nuvole al {pct}% nel buio | `weather.clear.trendWhen` |
| Non disponibile | `weather.verdict.unknown` |
| Nessuna notte astronomica | `weather.verdict.noNight` |
| Dalla quarta notte la previsione è una tendenza, meno affidabile e senza dettaglio orario. | `weather.trend.note` |
| Notte buona. | `weather.verdict.go` |
| Notte incerta. | `weather.verdict.marginal` |
| Notte non adatta. | `weather.verdict.nogo` |
| Non valutabile: copertura nuvolosa incompleta per le ore di buio. | `weather.verdict.none` |

### Le parole dei giudizi

| testo | dove |
|---|---|
| buona | `weather.word.go` |
| incerta | `weather.word.marginal` |
| non adatta | `weather.word.nogo` |
| limpido | `weather.word.aerosol.go` |
| molto fosco | `weather.word.aerosol.nogo` |
| buona per la banda larga | `weather.word.moon.go` |
| al limite | `weather.word.moon.marginal` |
| solo banda stretta | `weather.word.moon.nogo` |

### Altri fattori

| testo | dove |
|---|---|
| Altri fattori (non modificano il verdetto) | `weather.weighs` |
| dalle {da} alle {a} · {n} ore | `weather.weighs.span` |
| dalle {da} alle {a} · 1 ora | `weather.weighs.span.one` (una sola) |
| dalle {da}, al {pct}% · solo per la banda larga | `weather.weighs.moon` |
| Nessun altro fattore. | `weather.weighs.none` |

### Il cielo e la scala di destra

| testo | dove |
|---|---|
| il cielo, dal tramonto all'alba | `weather.sky.title` |
| Passa sul grafico per vedere i valori di quell'ora. | `weather.sky.hint` |
| Il cielo ora per ora: le frecce portano tutte le carte a quell'ora | `weather.sky.label` |
| Nubi basse, medie e alte e umidità, dal tramonto all'alba | `weather.sky.img` |
| la notte | `weather.sky.night` |
| alle {ora}: nubi basse {b}%, medie {m}%, alte {a}%, umidità {u}% | `weather.sky.at` |
| a sinistra, in % | `weather.sky.left` |
| Scala di destra | `weather.sky.right` |
| umidità | `weather.sky.humidity` |
| buio sereno, {n} ore | `weather.sky.clear` |
| buio sereno, 1 ora | `weather.sky.clear.one` (una sola) |
| nessuna ora di buio sereno | `weather.sky.noClear` |
| basse | `weather.sky.legend.low` |
| medie | `weather.sky.legend.mid` |
| alte | `weather.sky.legend.high` |
| nubi basse | `weather.sky.legend.lowFull` |
| nubi medie | `weather.sky.legend.midFull` |
| nubi alte | `weather.sky.legend.highFull` |
| a destra la scala della metrica scelta, col suo colore dove passa una soglia | `weather.sky.legend.right` |
| dal tramonto all'alba, {da}–{a} | `weather.sky.legend.span` |
| Misura sulla scala di destra | `weather.right.label` |
| Scala di destra | `weather.right.menu` |
| Nessuna | `weather.right.none` |
| solo nubi | `weather.right.noneWhat` |
| Senza valutazione | `weather.right.noWord` |
| pioggia | `weather.right.rain` |
| vento | `weather.right.wind` |
| condensa | `weather.right.condensation` |
| seeing | `weather.right.seeing` |
| jet stream | `weather.right.jet` |
| aerosol | `weather.right.aerosol` |
| Richiede una chiave Meteoblue | `weather.right.seeing.noKey` |
| Chiave non valida | `weather.right.seeing.refused` |

### Le carte delle misure

| testo | dove |
|---|---|
| alle {ora} | `weather.cards.at` |
| alle {ora} | `weather.card.at` |
| alle {ora} · rugiada {r} °C | `weather.card.atDew` |
| alle {ora} · raffiche {r} km/h | `weather.card.atGust` |
| × | `weather.card.back` |
| Torna al riepilogo della notte | `weather.card.backLabel` |
| la notte: {v}, {sotto} | `weather.card.valueNight` |
| alle {ora}: {v} | `weather.card.valueAt` |
| Riepilogo delle ore di buio | `weather.cards` |
| Nuvole | `weather.measure.cloud` |
| Nuvole basse | `weather.measure.cloud_low` |
| Pioggia | `weather.measure.rain` |
| Raffiche | `weather.measure.gust` |
| Vento | `weather.measure.wind` |
| Condensa | `weather.measure.condensation` |
| Jet stream | `weather.measure.jet` |
| Seeing | `weather.measure.seeing` |
| Aerosol | `weather.measure.aerosol` |
| Luna | `weather.measure.moon` |
| Temperatura e rugiada | `weather.measure.temperature` |
| Umidità | `weather.measure.humidity` |
| Polvere | `weather.measure.dust` |
| Vento a 700 hPa | `weather.measure.wind_700` |
| Vento a 200 hPa | `weather.measure.wind_200` |
| % | `weather.unit.pct` |
| mm | `weather.unit.mm` |
| km/h | `weather.unit.kmh` |
| ″ | `weather.unit.arcsec` |
| °C | `weather.unit.celsius` |
| µg/m³ | `weather.unit.dust` |
| media nel buio | `weather.card.mean` |
| totale nel buio | `weather.card.total` |
| media nel buio, a 10 m | `weather.card.wind` |
| minimo di temperatura meno punto di rugiada | `weather.card.condensation` |
| media nel buio, Meteoblue | `weather.card.seeing` |
| media fino alle {a}, Meteoblue | `weather.card.seeing.part` |
| media nel buio, 250 hPa | `weather.card.jet` |
| media nel buio, spessore ottico | `weather.card.aerosol` |
| minima nel buio · rugiada {r} °C | `weather.card.temperature` |
| massima nel buio | `weather.card.humidity` |
| Non disponibile | `weather.card.unknown` |
| superiore a {n} notti su 10 in questo sito | `weather.card.wind700` |
| fra i più deboli dell'anno in questo sito | `weather.card.wind700.zero` |
| superiore a 1 notte su 10 in questo sito | `weather.card.wind700.one` (una sola) |
| fra i più forti dell'anno in questo sito | `weather.card.wind700.ten` |
| confronto con lo storico non ancora disponibile | `weather.card.wind700.nobase` |
| {parola} tutta la notte | `weather.card.allNight` |
| {parola} dalle {da} | `weather.card.since` |
| picco {v} tra le {da} e le {a} | `weather.card.peak` |
| nessuna ora con pioggia | `weather.card.noRain` |
| raffiche fino a {v} km/h tra le {da} e le {a} | `weather.card.gusts` |
| sotto {s} °C dalle {da} | `weather.card.dewSince` |
| mai sotto {s} °C | `weather.card.dewNever` |
| dalle {da} non disponibile | `weather.card.missingSince` |
| {nome}, ora per ora | `weather.card.hours` |
| Il seeing richiede una chiave API Meteoblue (gratuita). | `weather.card.seeing.none` |
| Chiave Meteoblue non valida o scaduta. | `weather.card.seeing.refused` |
| Apri le Impostazioni | `weather.card.seeing.how` |

### Il seeing e la chiave Meteoblue

| testo | dove |
|---|---|
| Ultimo aggiornamento del seeing non riuscito: dati precedenti. | `weather.seeing.why.unreachable` |
| Risposta non valida da Meteoblue: dati precedenti. | `weather.seeing.why.bad_answer` |
| Chiave Meteoblue | `meteoblue.label` |
| Nessuna chiave: seeing non disponibile. | `meteoblue.none` |
| Chiave salvata (termina con {fine}). | `meteoblue.current` |
| Come ottenere una chiave gratuita | `meteoblue.where` |
| Verifica e salva | `meteoblue.save` |
| Rimuovi chiave | `meteoblue.remove` |
| Chiave valida: seeing attivo. | `meteoblue.saved` |
| Chiave rimossa: seeing non disponibile. | `meteoblue.removed` |
| Chiave non riconosciuta da Meteoblue: non salvata. | `meteoblue.refused` |
| Meteoblue non risponde: chiave non verificata e non salvata. | `meteoblue.unreachable` |
| Risposta non valida da Meteoblue: chiave non salvata. | `meteoblue.badAnswer` |
| Invio della chiave non riuscito | `meteoblue.failed` |

### Le fonti

| testo | dove |
|---|---|
| Previsione: | `weather.sources.forecast` |
| Weather data by Open-Meteo.com | `weather.attribution` |
| Seeing: meteoblue | `weather.attribution.meteoblue` |
| Aerosol e polveri: Generated using Copernicus Atmosphere Monitoring Service information {anno}. Ne' la Commissione europea ne' l'ECMWF rispondono dell'uso di questi dati. | `weather.attribution.cams` |

### In Stanotte e nelle Notti (lo stesso riassunto)

| testo | dove |
|---|---|
| Nuvole in media al {pct}%. | `weather.cloud` |
| {n} ore utili su {su} di buio. | `weather.usable.dark` |
| 1 ora utile su {su} di buio. | `weather.usable.dark.one` (una sola) |
| {n} ore utili su {su} col Sole sotto l'orizzonte: il buio astronomico non viene raggiunto. | `weather.usable.sun_down` |
| 1 ora utile su {su} col Sole sotto l'orizzonte: il buio astronomico non viene raggiunto. | `weather.usable.sun_down.one` (una sola) |
| {su} ore di buio. | `weather.window.dark` |
| {su} ore col Sole sotto l'orizzonte: il buio astronomico non viene raggiunto. | `weather.window.sun_down` |
| Il Sole non tramonta: nessuna ora di buio. | `weather.window.none` |
| {n} modelli su {su}: buona. | `weather.agreement.go` |
| {n} modelli su {su}: incerta. | `weather.agreement.marginal` |
| {n} modelli su {su}: non adatta. | `weather.agreement.nogo` |
| 1 modello su {su}: buona. | `weather.agreement.go.one` (una sola) |
| 1 modello su {su}: incerta. | `weather.agreement.marginal.one` (una sola) |
| 1 modello su {su}: non adatta. | `weather.agreement.nogo.one` (una sola) |
| Vento in quota {v} km/h: superiore a {n} notti su 10 dell'ultimo anno in questo sito. | `weather.wind700` |
| Vento in quota {v} km/h: fra i più deboli dell'ultimo anno in questo sito. | `weather.wind700.zero` |
| Vento in quota {v} km/h: superiore a 1 notte su 10 dell'ultimo anno in questo sito. | `weather.wind700.one` (una sola) |
| Vento in quota {v} km/h: fra i più forti dell'ultimo anno in questo sito. | `weather.wind700.ten` |
| Vento in quota {v} km/h. Confronto con lo storico del sito non ancora disponibile. | `weather.wind700.nobase` |
