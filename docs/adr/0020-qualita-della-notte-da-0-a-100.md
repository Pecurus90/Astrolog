# 0020 -- La qualita' della notte e' un punteggio da 0 a 100, coi pesi decisi con Marco

**Stato:** accettata, 17/10/2026 (Marco). I pesi della tabella sono la proposta v2: si toccano
solo con Marco. Sostituisce, quando si costruisce, "il semaforo lo decidono solo le nuvole" di
`docs/domini/meteo.md`.

## Contesto

Il disegno nuovo (Design, 17/10/2026) mostra ora per ora una qualita' da 0 a 100 e cosa la
limita, con formule senza fonte in `soglie.js`. Per sommare i fattori **non esiste una
convenzione pubblica** (ricerca del 17/10/2026): AstroWeather pesa nuvole 3, seeing 2,
trasparenza 1 (https://github.com/mawinkler/astroweather); DarkHours meteo 40, Luna 25, buio 25,
Bortle 10, con le nuvole come tetto (https://github.com/mbeher2200/DarkHours); ClearSkys nuvole
55, vento 20, umidita' 15, pioggia 10 (https://clearskys.app/guides/how-stargazing-score-works).
In tutte le nuvole pesano di piu' e bloccano; il seeing viene subito dopo. Quindi i pesi li
decide Marco (CLAUDE.md, principio 1); le soglie dentro ogni fattore restano quelle con fonte.

## Decisione

- **Ogni ora vale da 0 a 100**: somma dei punti dei fattori. Un fattore prende i punti pieni fino
  alla sua soglia "buona", zero dalla "non adatta", in proporzione in mezzo. Le soglie sono
  quelle con fonte gia' nel backend (`weather/judge.py`).
- **Bloccano**: pioggia, e nuvole "non adatta". L'ora vale 0.
- **Una convenzione sola** per deep sky, Sole e pianeti: il seeing pesa per tutti (Marco). Il
  giorno del Sole: il "Sole basso" usciva coi 15 punti della Luna; come si giudica si decide con
  Marco quando si costruisce il Sole.
- **Pesi** (Marco, 17/10/2026; la Luna esce dal punteggio, vedi sotto, e i suoi 15 punti si
  ridistribuiscono in proporzione):

| Fattore | Punti | Pieni | Zero |
|---|---|---|---|
| Nuvole (blocca) | 35 | okta <= 2 (fino al 25%) | dal 50% ("non adatta": l'ora vale 0) |
| Seeing | 30 | <= 2″ | >= 4″ |
| Trasparenza (aerosol) | 12 | AOD < 0,1 | AOD >= 1 |
| Condensa | 9 | scarto > 3 °C | scarto <= 0 |
| Vento | 9 | <= Beaufort 3 | >= Beaufort 5 |
| Jet stream | 5 | < 25 m/s | >= 35 m/s |
| Pioggia (blocca) | -- | -- | qualunque |

  Il jet stream pesa poco perche' il seeing di Meteoblue lo contiene gia'.
- **La Luna non pesa nel punteggio: decide la ripresa** (Marco, 17/10/2026). Prima pesava 15
  punti su 100: una Luna piena alta lasciava "buona" una notte perfetta, e chi fa banda larga
  non puo' uscire. Ora due risposte separate: il **meteo** (punteggio e verdetto) dice se si
  esce, la **Luna** dice cosa si riprende.
  - Ogni ora di buio e' **banda larga** o **solo banda stretta**. Solo banda stretta quando la
    Luna e' illuminata dal **25 %** (schema ING: buio sotto 0,25, grigio fino a 0,65, chiaro
    oltre; ING Technical Note 127,
    https://www.ing.iac.es/Astronomy/observing/manuals/ps/tech_notes/tn127.pdf; gli stessi tagli in
    astroplan, `MoonIlluminationConstraint`) **e** alta **da 10°** (Marco, a
    gusto: nessuna convenzione sull'altezza; ESO e i pianificatori contano dall'orizzonte; una
    Luna bassa spesso sta dietro monti o alberi).
  - Le due soglie sono **una sola casa**, nelle Impostazioni (oggi la fase e' quella del
    calendario della Luna, 25 %): calendario, Meteo, Dashboard e Notti usano la stessa
    definizione di "ora senza Luna".
  - A schermo: il verdetto del meteo, e sotto la ripresa coi suoi tratti ("Banda larga
    21:10-00:40 · poi solo banda stretta"); il riquadro di lato dice le ore di ciascun tipo.
  - Superato: la Luna giudicata col modello di Krisciunas e Schaefer sul cielo del sito (resta
    un'idea per un giudizio per bersaglio, con la distanza dalla Luna).
- **La notte**: media delle ore di buio; la curva ora per ora e' il suo andamento.
- **Il verdetto viene dal punteggio della notte** (Marco, 17/10/2026): buona da 70, incerta da
  40, sotto non adatta. Non dalle ore utili: d'estate il buio dura 4 ore e nessuna notte sarebbe
  buona. Vale per le notti passate e per il giorno del Sole.
- **Ora utile**: qualita' da 60 (Marco, 17/10/2026). Le ore utili sono un numero da mostrare, non
  decidono il verdetto.
- **Calcola il backend** e scrive il risultato (una lettura non calcola); il frontend formatta.

## Conseguenze

- `docs/domini/meteo.md` si riscrive quando si costruisce: oggi dice "nessun voto unico della
  notte" e "la Luna resta fuori dal verdetto".
- Profili per tipo di ripresa (banda stretta: la Luna pesa meno) restano un'idea; il giudizio per
  bersaglio (BAIT) arriva coi progetti.
- `soglie.js` del disegno non decide piu' niente: punteggio, cosa limita e tratti arrivano
  dall'API.
