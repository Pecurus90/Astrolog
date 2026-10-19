# Per Claude Design -- Planner v21.3, correzioni

Da Claude Code, 19/10/2026. Revisione di `pagine/Planner.dc.html` e
`componenti/PlannerSolare.dc.html`, desktop e telefono. Decisioni in
`docs/adr/0023-planner-e-progetti.md`, sezione "I giudizi". Le parole fra «» sono proposte: Marco
le approva sulla tavola.

I conti tornano: campo, campionamento, mosaico (3.46° × 1.29°), luminosita' superficiale, rotazione
dal Nord verso Est con l'Est a sinistra, pannelli numerati, scala e critico di Giove, video al
massimo con un pixel (43 s). Fascia del Sole e crediti esatti. Restano queste.

## Le soglie stanno in Impostazioni (Marco)

Ogni soglia che dipende da dove e come si riprende si cambia in Impostazioni, col valore di
partenza e la fonte accanto. Nel Planner si cambia per una ricerca, senza salvarla.

- Altezza minima, cielo profondo: 30° (massa d'aria 2)
- Durata minima sopra l'altezza: 1 h
- Distanza dalla Luna: 40°
- Mese buono: 3 h utili il 15 del mese
- Altezza minima di pianeti, Luna e Sole: 30° (massa d'aria 2)
- Correttore di dispersione sotto: 35° (BAA)

Nelle Impostazioni una sezione «Planner» con queste sei righe. Dove il Planner usa una di queste
soglie, la riga piccola sotto dice «da Impostazioni». Fisse, perche' fisica: rapporto critico,
campionamento, video al massimo, campo che entra.

**Momento migliore**: la pillola in verde (✓, conferma: «✓ migliore»), non gialla. Il seeing
accanto col giudizio di Meteo (sotto 2″ buono, 2-4″ incerto, oltre non adatto): se anche l'ora
migliore ha seeing cattivo, lo dice il seeing, non la pillola.

## I consigli (Marco)

Sotto un giudizio, una riga piccola che dice come arrivarci: un input, non una guida. Testi
proposti; i numeri li manda l'app.

- Pianeti, «! sottocampionato»: «Per il critico: barlow {x}×. Il fattore cresce allontanando il
  sensore dalla barlow.»
- Video al massimo: «Con la derotazione il tempo in tutto arriva a 3-4 volte; il singolo video
  no.»
- Pianeti, sempre (riga fissa sotto i numeri): «Pose sotto 30 ms, almeno 30 fotogrammi al
  secondo; area di ripresa stretta attorno al disco.»
- Pianeti bassi (sotto la soglia del correttore) o seeing da 2″: «Un filtro IR-pass soffre meno
  il seeing.»
- Cielo profondo, «! sovracampionato»: «Bin 2 × 2 (anche in elaborazione) o un riduttore: con bin
  2 × 2, {s}″/px.»
- Cielo profondo, «! sottocampionato»: «Dithering e drizzle, con molti frame; oppure pixel fino a
  {p} µm con questa focale.»

Il consiglio non ha pillola e non ha colore: testo tenue sotto il giudizio. Senza giudizio (manca
il seeing) niente consiglio.

## Cielo profondo

1. **«Entra nel campo» boccia l'esempio di apertura.** M 31 (190′ × 60′) nel mosaico 2 × 1
   (3.46° × 1.29°) ci sta, e la pillola dice «non entra». L'errore era nostro: la regola nuova e'
   geometrica. Entra se l'ellisse dell'oggetto (asse maggiore, asse minore, angolo di posizione
   del catalogo) sta tutta dentro il rettangolo ruotato del campo o del mosaico. Senza angolo di
   posizione, asse maggiore contro il lato corto, come prima. Il giudizio cambia girando la
   rotazione.
2. **Crea parte vuota** (Marco): i filtri dello schema in lista, ore a 0, esposizione vuota. Via
   le ore suggerite (SHO 10 h, HOO 15 h, LRGB 6 + 2 + 2 + 2, colore 20 o 10 h, filtro aggiunto
   5 h) e le esposizioni 300 / 120 s: nessuna fonte. Riepilogo dei frame solo quando c'e'
   l'esposizione.
3. **Mese buono**: ✓ se il 15 del mese l'oggetto ha almeno **3 ore utili** (Marco). E'
   un'impostazione dell'utente: la legenda lo dice («mese buono: da 3 ore, cambia in
   Impostazioni»). Via il 60 % del mese migliore.
4. **Senza seeing**: uno stato nei Tweaks («nessuna chiave Meteoblue»). Il campionamento mostra
   solo il numero, senza pillola, e la riga «Giudizio col seeing previsto: serve la chiave
   Meteoblue.» (proposta). Il seeing del giudizio e' la mediana delle ore utili dell'oggetto.
5. **Camera a colori**: niente schemi SHO e HOO (servono filtri a banda singola). Schemi:
   «Senza filtro», «Multibanda».
6. **PanSTARRS**: l'ID e' `CDS/P/PanSTARRS/DR1/color-i-r-g` (ADR 0023), non `color-z-zg-g`.
7. **Finestra del progetto iniziato**: «i frame gia' ripresi non cadono piu' nei pannelli nuovi» non
   vale se cambia il corredo. Proposta: «{durata} gia' riprese non conterebbero piu'.» da sola,
   come concordato.
8. **Telefono, foglio chiuso**: il giudizio del campionamento e' sparito con la forma A. E' il
   piu' utile: nella casella Corredo, sotto il nome («✓ ottimo» / «! sottocampionato»).
9. **Una sigla sola**: «AR» in Altri filtri, «RA» sulla carta. Si usa **RA / Dec** ovunque, come la
   brief.
10. **Numeri col punto** (regola v16.1): campo, mosaico, rapporto focale e luminosita' superficiale
    oggi hanno la virgola.
11. Pulizia prima del porting: il codice delle forme A e C del telefono (`variante`, `chipsR`,
    `righeC`, `sheetC`, `varA`, `varC`) e' ancora nella pagina.
12. Nota per la tavola: la copertura NSNS disegnata come «Dec > −16» e' una semplificazione;
    nell'app la da' il MOC della mappa.

## Sistema solare

1. **Una domanda, un giudizio.** Sotto «Diametro apparente» «entra intero / non entra intero»
   confronta col lato lungo, sotto «Campo» col lato corto: possono dire il contrario insieme. Via
   la riga sotto il diametro; resta quella del Campo.
2. **Tessere stimate = tessere del mosaico.** «→ mosaico di n tessere» conta il disco intero, il
   mosaico solo la parte illuminata (Luna all'80 %: 12 contro 9). La stima usa lo stesso conto.
   Sovrapposizione vuota: 20 in tutti e due (oggi 0 nel mosaico, 20 nella stima).
3. **Esempio della Luna**: il 30/9 la Luna e' a 371 402 km, 32.2′: con C11 e 9.0 µm le tessere
   sono **12 (3 × 4)**, non 6. Il 6 della brief vale a distanza media (31.1′). DECISIONI e
   didascalie col numero della data mostrata.
4. **Video al massimo per difetto**: oggi 150 s diventano «3 min». E' un massimo: «2 min 30 s», o
   minuti per difetto. Commento e DECISIONI (righe 1062-1063) parlano ancora di Dawes e «circa
   2 min»: 1 pixel, 43 s.
5. **Altezza minima 30°** per pianeti, Luna e Sole (Marco): massa d'aria 2, come «oggetto basso»
   nelle misure dei frame. Via 20° e 15°. La riga del correttore resta sotto 35°.
6. **Mercurio e Venere anche di giorno** nel momento migliore (Marco), con una riga fissa quando il
   Sole e' sopra l'orizzonte: «A {n}° dal Sole: non cercarlo mai a occhio o col cercatore.»
   (proposta; fonte BAA, guida di Mercurio). Il giorno viene dall'altezza del Sole, non dalle ore
   fisse 6.9-19.2.
7. **Fuori, non decisi**: «attivita' moderata · 112 macchie», «Macchia Rossa al meridiano», «Faccia
   di Marte». L'ADR li tiene come idee per dopo.
8. **Barlow per il critico**: sotto «! sottocampionato» la riga «per il critico: barlow {x}×»
   (critico / rapporto del corredo, una cifra decimale).
9. **Hα**: col filtro Hα, riga fissa «Hα solo con un telescopio o un filtro Hα dedicato.»
   (proposta).
10. Periodi di rotazione dalla stessa fonte (NASA Planetary Fact Sheet): Saturno 10.656 h, non
    10.56.
11. Telefono: il pulsante del sensore nel corredo di prova e' alto 38 px: 44.

CHANGELOG e DECISIONI come al solito.
