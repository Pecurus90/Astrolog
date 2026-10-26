# Per Claude Design -- Meteo e Dashboard: le aggiunte

Decise da Marco il 12 ottobre 2026, dopo il confronto con gli strumenti che gli astrofotografi
usano (Astrospheric, Clear Outside, Target Scheduler di N.I.N.A., Voyager, Telescopius).
**La disposizione delle due pagine non cambia.** Nel Meteo entra una carta e ne escono due; nella
Dashboard la tabella dei progetti prende colonne. Valgono per desktop, telefono, stati e Atlante.

Un testo segnato *(provvisorio)* resta col filo tratteggiato: Marco lo conferma dopo averlo visto.

## 1. Meteo

1. **Carta nuova: Visibilita'.** Stesso mattone delle altre (`as-parametro`), fra le carte grandi,
   dopo *Pioggia*. Dice se nel buio c'e' nebbia.

   | parte | testo |
   |---|---|
   | nome | Visibilità |
   | valore e unita' | 12 km (sotto 10 km con un decimale: 0,8 km) |
   | sotto il valore | minima nel buio |
   | parole | buona · non adatta (nessuna parola in mezzo) |
   | riga del giudizio | buona tutta la notte · non adatta dalle 03:00 |
   | sotto le barrette | nebbia dalle 03:00 · nessuna ora di nebbia |
   | soglia | 1 km: sotto e' nebbia (definizione WMO) |

   Le barrette crescono con la visibilita': alta e' buona. La soglia tratteggiata sta a 1 km.
   Quando pesa entra fra gli *Altri fattori*, come la Condensa:
   **Visibilità** nebbia dalle 03:00 alle 06:00 · 3 ore. Non modifica il verdetto.
   Nel cielo, sulla *Scala di destra*, entra come le altre misure, col nome «visibilità».
   Non tutti i modelli la danno: la carta ha lo stato *Non disponibile* come le altre.

2. **Escono due carte piccole:** *Vento a 200 hPa* (ripete il Jet stream a 250) e *Umidità* (la
   Condensa dice gia' cio' che serve). L'umidita' resta nel cielo, dove si accende a parte.
   Restano *Temperatura e rugiada*, *Polvere*, *Vento a 700 hPa*.

3. **Il conto.** Carte grandi nove: Nuvole, Nuvole basse, Condensa, Pioggia, Visibilita', Vento,
   Seeing, Jet stream, Aerosol. Carte piccole tre. Dodici in tutto: sul telefono, a quattro per
   riga, tre file piene, senza la carta rimasta sola di oggi. Sul desktop la fila delle grandi va
   ridisposta (oggi 4+4): come regge meglio, lo decidi tu e lo dici.

4. **La barra in alto del Meteo** dice ancora «Letto oggi alle 07:12»: diventa
   «Ultima scansione: oggi, 07:12», come nella Dashboard.

## 2. Dashboard

1. **Telefono, le sei carte del meteo.** A quattro per riga lasciano due posti vuoti: vanno a tre
   per riga, due file piene.

2. **La tabella dei progetti prende colonne.** Oggi: oggetto, ore, verso l'obiettivo, sopra 30°
   stanotte. Diventa:

   | colonna | esempio | cosa dice |
   |---|---|---|
   | oggetto | IC 1396 · Banda stretta | come oggi |
   | ore | 14 h 20 di 20 h | come oggi, con la barra |
   | per filtro | Hα 6 h 10 · OIII 5 h · SII 3 h 10 | le ore di ogni filtro, una barretta per filtro *(provvisorio)* |
   | utili stanotte | 5 ore | le ore di buio sereno in cui l'oggetto sta sopra 30°; prende il posto di «sopra 30° stanotte» *(provvisorio)* |
   | transito | 01:20 | l'ora in cui passa al meridiano *(provvisorio)* |
   | dalla Luna | 74° | la distanza dalla Luna stanotte, solo il numero: nessun semaforo *(provvisorio)* |
   | finestra | ancora 6 settimane | per quanto resta riprendibile *(provvisorio)* |

   Per un mosaico, sotto «per filtro» una riga in piu': *pannello 1: 6 h · pannello 2: 5 h 45*
   *(provvisorio)*.
   Un progetto che stanotte non ha ore utili dice «nessuna» in quella colonna, senza colore
   d'allarme: non e' un guasto.

3. **L'ordine della tabella.** Accanto al titolo un segmentato a due voci: *per ore* (oggi) e
   *meglio stanotte* *(provvisorio)*, che mette in cima chi ha piu' ore utili stanotte. Il titolo
   «progetti in corso · per ore» diventa «progetti in corso».

4. **Telefono.** La riga di riepilogo «Progetti in corso» dice il migliore di stanotte invece del
   piu' avanti: *IC 1396 · 5 ore utili stanotte* *(provvisorio)*. La tabella intera sta nella
   pagina Progetti, come oggi.

5. **L'ultima notte, in «da riprendere».** Sotto «4 h 12 su IC 1396, 126 frame» una riga:
   *FWHM media 2,8″* *(provvisorio)*. L'app la mostrera' quando misurera' i frame.

6. **La Luna.** La frase «Notti buone per la banda larga: Luna sotto il 25%, o almeno 4 ore di
   buio senza Luna» resta tratteggiata: la Luna si giudichera' per bersaglio, con la colonna
   «dalla Luna», e la frase si riscrive quando la regola e' decisa.

## 3. Cio' che non cambia

La volta, il dettaglio della Luna, le sei carte del meteo con i loro grafici, le prossime tre
notti, l'anno. Tutti i testi gia' consegnati con `design-meteo-testi.md` e `design-dashboard.md`.

## 4. Cosa dire a parte

- come hai ridisposto le nove carte grandi del Meteo sul desktop;
- se le sette colonne della tabella dei progetti reggono a 1440 e a 1024, e cosa hai fatto dove
  non reggono;
- ogni testo che non regge nella forma: non riscriverlo, segnalalo.
