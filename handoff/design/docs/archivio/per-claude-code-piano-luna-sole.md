# Per Claude Code — Luna e Sole a pannelli nel piano, e i pianeti di notte

Da Claude Design, 19/10/2026. Domanda di Marco, prima di disegnare. Niente e' deciso.

## Il caso

Una postazione remota che si apre da sola. Di giorno non c'e' nessuno, ma si vuole riprendere il Sole; di notte la Luna. Con una focale lunga il disco non entra in un campo: serve un mosaico a pannelli, come quello che il Planner gia' disegna nel modo Sistema solare (intera o una zona, pannelli numerati, ordine dal terminatore, Luce bianca · Hα per il Sole).

Oggi nel Piano della notte (v26) un blocco Luna o pianeta e' solo «video» con una durata: non porta un mosaico e l'export non sa cosa fare dentro il blocco.

## Le domande

1. **Un piano lunare o solare salvato.** Il Planner puo' salvare Luna e Sole come il deep sky salva un progetto: corpo, setup, mosaico (intero o zona), pannelli, sovrapposizione, ordine, filtro o Hα, video per pannello (durata o frame, fps)? Finisce in Progetti come gli altri, o e' un'altra cosa?

2. **Il blocco che lo richiama.** Nel Piano della notte un blocco «Luna · mosaico 12 pannelli» che prende quel piano, e nell'export per N.I.N.A. una sequenza per pannello. E' fattibile col sequencer avanzato?

3. **Puntare senza stelle.** Sul disco il plate solving non funziona. Come si arriva al pannello giusto?
   - offset in RA/Dec dal centro del disco, calcolati dall'app per l'ora del blocco (effemeridi, librazione, angolo di posizione, rotazione del campo)?
   - una centratura sul disco intero prima di partire, poi solo offset?
   - velocita' di inseguimento lunare / solare durante il blocco?
   - quanto errore di puntamento ci si aspetta con una focale lunga, e quindi quanta sovrapposizione fra pannelli serve? Chi la decide (un'impostazione con la fonte)?
   N.I.N.A. ha gia' qualcosa per questo, o serve un plugin?

4. **Il Sole di giorno.** Il Piano della notte va da tramonto ad alba. Per il Sole serve:
   - un «Piano del giorno» (finestra del Sole, il Meteo di giorno c'e' gia'),
   - oppure un modo «Sole» nella stessa pagina, con la linea del tempo da alba a tramonto?
   Filtro solare, apertura del tetto e sicurezza restano a N.I.N.A., come ora: confermi?

5. **I pianeti di notte: hanno senso nel piano?** Le riprese planetarie si fanno di solito a video, a mano, con programmi diversi da N.I.N.A. Possibili strade:
   - (a) restano blocchi che tengono il tempo nella notte, senza export («da fare a mano»);
   - (b) escono dal Piano della notte e restano solo nel Planner;
   - (c) nel piano solo Luna e Sole a mosaico, perche' quelli si possono eseguire da soli.
   Cosa fa l'app oggi, e cosa conviene?

## Cosa serve per disegnare

- I campi di un piano lunare o solare (cosa si salva, cosa si vede nel blocco).
- Cosa scrive l'export per un mosaico, e cosa non puo' fare (per i testi d'avviso).
- Se c'e' un piano di giorno: una pagina nuova o un modo della stessa.
- La scelta su (a) / (b) / (c) per i pianeti.

Fino alla risposta, nel disegno resta com'e' (v26.1).
