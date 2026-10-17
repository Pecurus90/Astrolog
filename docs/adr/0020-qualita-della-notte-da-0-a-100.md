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
- **Una convenzione sola** per deep sky, Sole e pianeti: il seeing pesa per tutti (Marco).
- **Pesi**:

| Fattore | Punti | Pieni | Zero |
|---|---|---|---|
| Nuvole (blocca) | 30 | okta <= 2 (fino al 25%) | coperto |
| Seeing | 25 | <= 2″ | >= 4″ |
| Luna di notte / Sole basso di giorno | 15 | nessuno schiarimento | 2 mag di schiarimento |
| Trasparenza (aerosol) | 10 | AOD < 0,1 | AOD >= 1 |
| Condensa | 8 | scarto > 3 °C | scarto <= 0 |
| Vento | 8 | <= Beaufort 3 | >= Beaufort 5 |
| Jet stream | 4 | < 25 m/s | >= 35 m/s |
| Pioggia (blocca) | -- | -- | qualunque |

  Il jet stream pesa poco perche' il seeing di Meteoblue lo contiene gia'.
- **La Luna si giudica sul cielo del sito**: schiarimento in magnitudini fra il cielo del sito
  (`sky_sqm`, dal Bortle dichiarato o misurato) e lo stesso cielo con la luce della Luna, dal
  modello di Krisciunas e Schaefer (PASP 103:1033, 1991; incertezza ~0,25 mag): fase, altezza
  della Luna, estinzione. Sotto l'orizzonte non schiarisce. Un cielo buio perde di piu' di un
  cielo di citta'. Zero punti a 2 mag (un sito di campagna che diventa periferia; Marco). Sito
  senza Bortle: si giudica come cielo buio, e la pagina lo dice.
- **La notte**: media delle ore di buio; la curva ora per ora e' il suo andamento, e le notti
  dopo cambiano da sole con la Luna che sorge piu' tardi.
- **Calcola il backend** e scrive il risultato (una lettura non calcola); il frontend formatta.

## Conseguenze

- `docs/domini/meteo.md` si riscrive quando si costruisce: oggi dice "nessun voto unico della
  notte" e "la Luna resta fuori dal verdetto".
- La parola della notte (buona / incerta / non adatta) dal punteggio si decide con Marco: soglia
  senza convenzione.
- Profili per tipo di ripresa (banda stretta: la Luna pesa meno) restano un'idea; il giudizio per
  bersaglio (BAIT) arriva coi progetti.
- `soglie.js` del disegno non decide piu' niente: punteggio, cosa limita e tratti arrivano
  dall'API.
