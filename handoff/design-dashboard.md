# Per Claude Design -- Dashboard: la lingua dell'app e le carte del meteo

Le tavole della Dashboard (`pagine/dashboard.html`, `dashboard-telefono.html`, `dashboard-stati*.html`,
`dashboard-atlante.html`) sono il disegno definitivo: **la disposizione e le funzioni non cambiano**,
l'app si costruisce attorno. Parlano pero' la lingua di prima del 9 ottobre, e le carte del meteo
sono disegnate in un modo diverso da quelle della pagina Meteo. Si chiedono tre cose, decise da
Marco il 12 ottobre 2026.

## 1. Cosa cambiare

1. **Sei carte del meteo, sempre le stesse, nello stesso posto.** La fila da sei resta. Le misure
   sono quelle della pagina Meteo, in quest'ordine:

   | posto | oggi | diventa |
   |---|---|---|
   | 1 | seeing | **Nuvole** |
   | 2 | corrente a getto | **Seeing** |
   | 3 | trasparenza | **Jet stream** |
   | 4 | vento | **Vento** |
   | 5 | umidita' | **Condensa** |
   | 6 | temperatura | **Aerosol** |

   La trasparenza esce: l'app non ha piu' una fonte che la dia. Temperatura, umidita', pioggia e
   nuvole basse si leggono nella pagina Meteo. Lo scambio di carte della notte coperta (nuvolosita'
   e pioggia al posto di seeing e trasparenza) sparisce: ogni misura sta sempre al suo posto.

2. **La carta e' quella della pagina Meteo, in piccolo.** Stesso mattone (`as-parametro`): il
   valore della notte, cio' che vuol dire (*media nel buio*), la parola col semaforo e le barrette
   ora per ora col colore del giudizio. La carta delle Nuvole non ha la riga del giudizio: la sua
   parola e' il verdetto in testa. Sul telefono sono le carte piccole del Meteo, quattro per riga
   o come regge, con lo stesso gesto di oggi (tocchi, si apre sotto).

3. **Il grafico che si apre sotto una carta resta**, col suo titolo e «chiudi». Cambia il disegno
   dentro: non piu' la linea coi numeri sopra, ma il disegno che quella misura ha nel cielo del
   Meteo (foglio 64, la scala di destra): il tratto o le barre col colore del giudizio ora per
   ora, la soglia tratteggiata, la parola dove il giudizio cambia, l'ora non data a tratteggio.

4. **I testi** si prendono dal vocabolario qui sotto (sezione 2), parola per parola. Le
   sostituzioni che pesano di piu':

   | sulla tavola | nell'app |
   |---|---|
   | niente (il verdetto) | non adatta |
   | meteo della serata | meteo della notte (titolo nuovo: l'app dice sempre «notte», mai «serata») |
   | meteo delle prossime 3 serate | meteo delle prossime 3 notti (titolo nuovo, stessa ragione) |
   | 5 h 12 di buio sereno | 6 ore di buio sereno (ore intere: la previsione e' oraria) |
   | Coperto tutta la notte | Nessuna ora di buio sereno |
   | corrente a getto 28 m/s | Jet stream, in km/h |
   | nuvolosita' | Nuvole |
   | media della notte / massima della notte | media nel buio / massima nel buio |
   | migliore 2,0″ alle 22 | picco 3,1″ tra le 22:00 e le 23:00 |
   | previsione di mercoledi' 30 settembre, 18:05 | Previsione del 30 settembre, 18:05 (2 ore fa) |
   | Letto oggi alle 07:12 | Ultima scansione: oggi, 07:12 |
   | Leggo l'archivio 1.240 su 8.310 | In corso · 1.240 su 8.310 |
   | prima lettura dell'archivio, a lettura finita | prima scansione, a scansione finita |
   | 32 casi da confermare | 32 da confermare |
   | illuminata 62% | illuminata al 62% |
   | Stanotte, riga del meteo: «Il posto c'e': arriva con il meteo.» | Notte buona. Nuvole in media al 16%. 6 ore utili su 9 di buio. |

5. **Le prossime tre notti.** Ogni riquadro dice cio' che dice la fila delle notti del Meteo: il
   giorno, il semaforo con la parola, e le ore serene (*6 ore · 21–03*, oppure *nessuna serena*).
   Le parole «Sereno», «Nubi sparse», «Coperto» e «buio senza Luna» nell'app non ci sono: restano
   col filo tratteggiato finche' Marco non decide se entrano.

6. **Il dettaglio di una notte** (l'elenco che si apre): i nomi delle misure sono quelli del
   Meteo -- Nuvole, Pioggia, Seeing, Jet stream (km/h), Vento, Umidita', Temperatura -- e la
   trasparenza esce.

## 2. Cio' che resta com'e'

- La volta con le curve, i progetti in corso, «da riprendere», l'anno col calendario colorato, il
  dettaglio della Luna col calendario delle fasi: restano. I dati che mancano li costruisce l'app.
- **Una frase aspetta Marco**: «Notti buone per la banda larga: Luna sotto il 25%, o almeno 4 ore
  di buio senza Luna». Il 25% e' la regola dell'app; le «4 ore» non hanno ancora una fonte. Resta
  com'e', col filo tratteggiato.
- «214 frame fuori dai conti»: resta; l'app oggi non da' quel numero.

## 3. Il vocabolario

I testi dell'app che la Dashboard usa, alla lettera. `{…}` e' un dato.

### Il verdetto e le ore serene

| testo | dove |
|---|---|
| buona · incerta · non adatta | il verdetto, una parola sola in tutta l'app |
| Non disponibile | il verdetto quando le nuvole non si sanno |
| Nessuna notte astronomica | quando il Sole non scende |
| {n} ore di buio sereno · 1 ora di buio sereno | in testa |
| Nessuna ora di buio sereno | in testa, a zero ore |
| dalle {da} alle {a}, {n} ore | sotto il verdetto, coi minuti: *dalle 21:00 alle 03:00, 6 ore* |
| accordo dei modelli {n} su {su} | sotto il verdetto |
| {n} ore · {da}–{a} | nel riquadro di una notte: *6 ore · 21–03* |
| nessuna serena | nel riquadro di una notte, a zero ore |
| Notte buona. · Notte incerta. · Notte non adatta. | nel pannello Stanotte |
| Nuvole in media al {pct}%. | nel pannello Stanotte |
| {n} ore utili su {su} di buio. | nel pannello Stanotte |
| Previsione non disponibile. Dettagli nella pagina Meteo. | Stanotte, senza previsione |

### Le sei carte

| nome | valore e unita' | sotto il valore | parole |
|---|---|---|---|
| Nuvole | % | media nel buio | (nessuna riga: e' il verdetto) |
| Seeing | ″ | media nel buio, Meteoblue | buona · incerta · non adatta |
| Jet stream | km/h | media nel buio, 250 hPa | buona · non adatta |
| Vento | km/h | media nel buio, a 10 m | buona · incerta · non adatta |
| Condensa | °C | minimo di temperatura meno punto di rugiada | buona · non adatta |
| Aerosol | (senza unita') | media nel buio, spessore ottico | limpido · molto fosco · nessuna parola in mezzo |

| testo | dove |
|---|---|
| {parola} tutta la notte | la riga del giudizio: *buona tutta la notte* |
| {parola} dalle {da} | la riga del giudizio, coi minuti: *incerta dalle 21:00, non adatta dalle 22:00* |
| picco {v} tra le {da} e le {a} | sotto le barrette: *picco 145 km/h tra le 22:00 e le 23:00* |
| raffiche fino a {v} km/h tra le {da} e le {a} | sotto le barrette del Vento |
| sotto 3 °C dalle {da} · mai sotto 3 °C | sotto le barrette della Condensa |
| Non disponibile | un valore che il servizio non da' |
| dalle {da} non disponibile | una misura che copre solo parte della notte |
| Il seeing richiede una chiave API Meteoblue (gratuita). · Apri le Impostazioni | la carta del Seeing senza chiave |
| non adatta dalle 22 | la parola dentro il grafico, senza minuti |

### La testa del meteo

| testo | dove |
|---|---|
| Previsione del {giorno}, {ora} ({fa}) | l'eta' della previsione |
| Seeing del {giorno}, {ora} ({fa}) | l'eta' del seeing |
| ora locale del sito | accanto alle due |
| Aggiorna | il bottone |
| Meteo | il collegamento alla pagina |

### La Luna

| testo | dove |
|---|---|
| Luna nuova · Crescente · Primo quarto · Gibbosa crescente · Luna piena · Gibbosa calante · Ultimo quarto · Calante | le fasi |
| illuminata al {pct}% | accanto alla fase |
| sorge · tramonta · non sorge · non tramonta | gli orari |
| consigliata banda stretta · banda larga al limite | quando la Luna pesa (oltre il 50%, fra 25 e 50%) |

### La barra e Stanotte

| testo | dove |
|---|---|
| Ultima scansione: {giorno}, {ora} | la barra, a riposo |
| In corso · {fatti} su {su} | la barra, mentre scansiona |
| Inattiva · Interrotta · Bloccata | gli altri stati della scansione |
| Scansione interrotta da un errore · Dettagli | la scansione bloccata |
| {n} da confermare | il conto, nella barra e in «Altro» |
| Stanotte · Stanotte a {sito} | il titolo del pannello |
| sito · luna · meteo | le tre righe del pannello |
| Bortle {n} · Bortle non indicato | la classe del cielo |
| Gestisci i siti | il collegamento |
| Nessun sito selezionato. · Seleziona sito | senza sito |
| Apri il Meteo | dal pannello |
| chiudi | ogni riquadro che si chiude |

### Le pagine

Dashboard · Notti · Archivio · Progetti · Statistiche · Attrezzatura · Planner · Carta del cielo ·
Meteo · Da confermare · Impostazioni · Altro.
