# 0034 -- Le regole del meteo con le fonti verificate, e il punteggio della notte v4

**Stato:** accettata, 24/10/2026 (Marco); costruite le soglie (`weather/judge.py`, commit 07077958); non costruiti punteggio v4, Ore di posa, seeing dal jet, buio nautico, calendario a tre gradini.
Supera in parte ADR 0020 (pesi, ora utile da 60, seeing nel voto) e ADR 0013 (Luna da -5°).
Superata in parte da ADR 0039: condensa (Beysens), seeing (rispetto al setup), raffiche (per setup).

**Supera** in `docs/domini/meteo.md`: "nuvole 35, seeing 30, trasparenza 12, condensa 9, vento 9, jet stream 5"; "sono le ore di buio con qualita' da 60"; "cede i suoi punti agli altri in proporzione"; "regola FAA dei 5 gradi Fahrenheit"; "classi del Canadian Meteorological"; "la regola diffusa fra chi riprende"; "il 50 e' di Marco"; "con 25%, 50% e -5° di partenza"; "previsione, fino a 16 giorni"; "cloudatlas.wmo.int/en/fog-compared-with-mist.html"

## Contesto

Fase 2 del registro delle regole (ADR 0033): ogni soglia del meteo confrontata con le
convenzioni. Sei ricerche (codice e documenti; fonti citate; forum di astrofotografia; stazioni,
sensori e osservatori; seeing; app e fisica del punteggio), due verifiche indipendenti della
proposta del punteggio, una misura sull'archivio di Marco. Materiale: registro/ e calibrazione/
nella scratchpad della sessione. Due citazioni erano sbagliate: il manuale FAA-H-8083-28 non ha
la soglia dei 3 °C; la scala canadese del seeing ha un buco fra 2" e 3".

## Decisione: le soglie

| misura | regola | fonte |
|---|---|---|
| nuvole | buona fino al 25%, incerta fino al 50%, no oltre | WMO/ICAO code D-8: FEW 1-2 ottavi, SCT 3-4 |
| pioggia | qualunque goccia nel buio = no | ASCOM ObservingConditions.RainRate: >0 bagnato |
| vento medio | incerto da 20 km/h, no da 29 | RMetS, Beaufort 4 "20-28", 5 "29-38" km/h |
| raffiche | **no oltre 25 km/h** (era 29) | iTelescope: chiude "con raffiche oltre 25 km/h" |
| condensa | **sotto 3 °C incerta, "serve la fascia"; mai no** (era no) | AstroBin: "worry ... less than about 3C"; la nebbia la dice la visibilita' |
| jet stream | no da 126 km/h (35 m/s) | meteoblue astronomy-seeing |
| seeing | incerto oltre 2", no oltre 4" | Astronomy Tools: Good 1-2", OK 2-4", Poor 4-5"; 4" anche CMC classe I |
| aerosol | limpido sotto 0,1, molto fosco da 1 | NASA Earth Observatory; Open-Meteo a 550 nm |
| visibilita' | nebbia sotto 1 km = no | FAA-H-8083-28 18.1.1; METAR FG |
| Luna | **buona sotto 25%, incerta 25-65%, no da 65%** (era 25/50) | ING: buio < 0,25, grigio fino a 0,65 |
| Luna, altezza | **dall'orizzonte** (-0,833°), come il codice | ESO: FLI 0 sotto l'orizzonte; astroplan; Target Scheduler |

Non giudicate: umidita' relativa (la dice il punto di rugiada), nubi medie e alte (il totale le
contiene), jet debole sotto 5 m/s (una pagina meteoblue sola, un'altra dice altro). Il calendario
della Luna usa gli stessi tre gradini, con le ore di buio senza Luna accanto (24/10/2026, al
posto di "25% o 4 ore"); 25 e 65 sono di fabbrica e si cambiano nelle Impostazioni, una casa per
Meteo e calendario (Marco, 24/10/2026). Le soglie tecniche le sceglie la sessione
dalle convenzioni (CLAUDE.md, principio 1, 24/10/2026).

## Decisione: il punteggio della notte v4

Nessuna formula standard fra le app (pyastroweatherio somma pesata con tetto 1 - nuvole; Clear
Sky Chart, 7Timer, meteoblue nessun voto). Fisica: la luce persa si moltiplica, come il tempo
efficace della Dark Energy Survey (Neilsen et al. 2019, arXiv 1912.06254). Tre risposte, coi nomi
di Marco:

- **Trasparenza** (si esce?), per ora = 100 x (1 - nuvole) x min(1, e^(-2 (AOD - 0,1))); 0 con
  un "no": pioggia, nebbia, nuvole oltre 50%, vento da 29, raffica oltre 25. Allo zenit, 550 nm.
  Notte = media delle ore di buio astronomico, ogni ora pesata per i suoi minuti di buio; senza
  buio astronomico il buio nautico, detto. Aerosol assente: fuori, "senza aerosol" accanto.
- **Verdetto**: buona da 70, incerta da 40. Misurato sull'archivio di Marco (105 notti con pose,
  76 piene, 684 senza, 2024-2026, storico Open-Meteo): l'86% delle notti piene sopra 70, delle
  notti senza pose il 21% (due terzi con la Luna oltre il 50%); 60/35 e 80/50 peggio.
- **Ore di posa** = somma di (Trasparenza / 100) x ore di buio, divisa per banda della Luna: "4,6
  ore di posa: 3,1 in banda larga, 1,5 solo banda stretta". Sostituisce le ore utili da 60.
- **Seeing**: la sua parola (soglie sopra), fuori dal voto: a una nebulosa toglie dettaglio, non
  segnale (manuale ING sul S/N degli oggetti estesi). Senza chiave meteoblue la parola viene dal
  jet stream, detto. Nessun setup serve.
- Condensa e vento incerto: avvisi accanto, mai punti.

## Conseguenze

- Fase 4: `weather/judge.py` (raffica, condensa, Luna), calendario della Luna, punteggio nuovo
  nel backend, contratto e guida-utente nello stesso intervento; il disegno nuovo mostra le tre
  risposte.
- Lo storico non ha la visibilita' (misurato: 0 valori su 24.336 ore): la nebbia non blocca le
  notti passate, e la pagina lo dice.
- Le nuvole dell'archivio sono ECMWF IFS, non ERA5 (misurato): le notti riprese sotto nubi
  "viste" dal modello (5% delle piene) restano un limite del dato.
