# Per Claude Code — le impostazioni e chi le legge

Da Claude Design, 19/10/2026 (v26.4). Ogni valore che una pagina prende dalle Impostazioni passa da un registro solo: `pagine/componenti/soglie.js`, `ALsoglie.imp`.

- `imp.schema`: per ogni chiave la partenza (`v`), l'unita' (`u`), la sezione delle Impostazioni (`sez`), la fonte (`fonte`) e chi la legge (`legge`).
- `imp.get(k)`: il valore salvato, o la partenza. `imp.set(k, v)`: salva. `imp.partenza(k)`, `imp.cambiata(k)`.
- Nella tavola si salva nel browser (localStorage «astrolog-impostazioni»); nell'app sono le impostazioni salvate dell'utente.
- I Tweaks delle pagine («luna», «tempi», «orizzonte») scavalcano il registro solo per provare: non salvano.

## Le chiavi

| chiave | partenza | sezione | la legge |
|---|---|---|---|
| generale.nome | — | Generale | Statistiche (intestazione) |
| siti.predefinito | Cima Ekar | Siti | conti delle notti senza sito, Da confermare |
| meteo.obiettivo | Deep sky | Meteo | Meteo, vista di partenza (Deep sky · Sole) |
| luna.buona | 25 % | Luna | `soglie.ripresa`: Meteo, Dashboard, Notti, Planner, Piano della notte |
| luna.limite | 50 % | Luna | idem |
| luna.alt | 0° | Luna | idem |
| planner.alt | 30° | Planner | Planner (Trova, Stanotte, periodo migliore), Progetti, Dashboard (vista Progetti), Piano della notte (deep sky e ricerca) |
| planner.dur | 1 h | Planner | Planner, Trova |
| planner.lun | 40° | Planner | Planner (Trova), Piano della notte (giudizio della Luna sulle proposte) |
| planner.mese | 3 h | Planner | Planner (periodo migliore), Progetti (mesi buoni) |
| planner.altS | 30° | Planner | Planner Sistema solare, Piano della notte Sistema solare |
| planner.adc | 35° | Planner | Planner Sistema solare, Piano della notte Sistema solare |
| planner.grs, grsD, grsV | 91°, 1/6/2026, 1.75° al mese | Planner | Planner Sistema solare, Giove |
| planner.tempi | quindici tempi vuoti (v27): raff, unpark, apri, park, chiudi, risc (min) · punt, af (min) · filtro, dither (s), ditherOgni (pose), scarico (s), afOgni (ore), flip (min), pannello (s) | Planner | Piano della notte: avvio, cambi, conto del blocco, flip, chiusura, margine |
| automazione.a, automazione.b | tetto, sensore, flat: No | Automazione | Piano della notte: passi di Avvio e Chiusura, tempi del tetto, export |

## Dove e' collegato nella tavola

- **Planner**: altezza, durata e distanza dalla Luna di Trova partono dal registro («cambiati» e «Ripristina» confrontano col registro); mese buono.
- **PlannerSolare**: altezza minima, ADC, riga della Macchia Rossa.
- **Piano della notte**: soglia per categoria (deep sky e ricerca `planner.alt`, Sistema solare `planner.altS`), conflitto «Sotto {n}°», ADC, giudizio della Luna, testi vuoti; tempi con il Tweak «dalle Impostazioni».
- **Dashboard**: linea e tratto spesso della vista Progetti, «sopra {n}°».
- **Progetti**: «mese buono: almeno {n} ore visibili».
- **Meteo**: vista di partenza; la ripresa da `luna.*`.
- **Impostazioni**: legge e scrive tutte le chiavi.

## Ancora fissi nella tavola (da collegare nel porting)

- Planner: alcune frasi e legende con «30°» scritte nei dati d'esempio (curva della Dashboard, numeri gia' calcolati).
- Progetti, Dashboard: le ore visibili d'esempio sono numeri scritti, non ricalcolati con la soglia.
- Siti: coordinate, Bortle, orizzonte stanno in `dati.js`, non nel registro (sono dati del sito, uno per sito).
- Tema e accento: li tiene il Telaio; nell'app vanno salvati con le impostazioni (chiavi da aggiungere: generale.modo, generale.accento).
- Cartelle, chiave Meteoblue, percorso di ASTAP: sono dati dell'app (servizi), non soglie: restano nei loro servizi.
