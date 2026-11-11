# Per Claude Design -- la coda

Ogni richiesta per Design entra qui nel momento in cui nasce, mai solo in chat (Marco, 6/11/2026).
All'avvio di ogni sessione `tools/stato.py` conta le voci e dice se in `handoff/design/` c'e' una
consegna nuova.

**Come si usa.** Marco incolla a Design le voci `[data]` e dice «dato»: diventano `[data]`.
Quando la consegna nuova arriva in `handoff/design/`, Claude Code controlla ogni voce `[data]`
sulle tavole: `[fatta vN]` se c'e', di nuovo `[data]` con cio' che manca se no. Le voci fatte
escono alla consegna dopo. Il testo lungo di un brief sta nel suo file accanto (`design-v59.md`).

Consegna controllata: dce48035 (v79, 10/11), in `handoff/design/` al posto della v78.

## Da dare

- [da dare] Errori delle tavole v79 (collaudo 11/11): il `sc-if` attorno ai `<path d="{{ … }}">`
  non basta, il browser legge il segnaposto prima del runtime. `componenti/Cerca.dc.html` da'
  `<path> attribute d` con `{{ a.d }}` e `{{ g.d }}`; `componenti/Telaio.dc.html` ancora i quattro
  `{{ m.altroChev }}`, `{{ m.modeIcon }}`, `{{ vb.az.d }}`, `{{ b.d }}`. Solo tavola: l'app non li ha.
- [da dare] Archivio, porting v78 (10/11): (a) il campo dice «Cerca: M 31, Velo, Andromeda…», ma
  la ricerca trova sigle e nomi dell'oggetto, non i nomi comuni: l'app scrive «Cerca: M 31, NGC
  7000…»; (b) le costellazioni nell'app sono latine IAU (Cepheus, Cygnus), decisione di Marco
  confermata il 10/11: catalogo.js le ha in italiano; (c) i nomi comuni arrivano dal catalogo in
  inglese («Andromeda Galaxy»); (d) Sole, Sistema solare e Aggiungi oggetto restano fuori finche'
  non c'e' una sorgente (ADR 0019). Allineare la tavola.
## Date, da controllare alla consegna

- [data 11/11] Dashboard, Il 2026 e Filtri del 2026 (porting 11/11): (a) «4.6» col punto e' un
  errore: «4,6»; (b) i frame senza filtro sono l'ultima riga «Filtro non indicato» col pallino a
  filo tratteggiato e un pezzo grigio dell'anello: disegnarli; (c) l'app elenca tutti i filtri
  dell'anno: dire se e dove tagliare; (d) senza notti nell'anno prima ne' tratteggio ne'
  confronto; (e) anno senza ore: zeri, media «—», «Nessuna posa nel 2026, per ora.» al posto
  dell'anello (Marco); (f) l'anno che non risponde: Avviso riga; (g) un filtro a colori
  nell'anello e' tre fette R, G, B (la strisciata del foglio nel conic-gradient lo cancella);
  (h) a 700 px le etichette dei mesi si accavallano («marapr»), anche in tavola; (i) a 860 e
  1280 lo scarto «−2 h 20» va a capo a meta'. Disegnare (d), (e), (f) negli stati. Dettaglio in
  `differenze-dalle-tavole.md`.

## Fatte

Le sette voci del 10/11 (brief archiviato in `handoff/design/docs/archivio/brief-porting-v78.md`)
sono fatte nella v79, portate nell'app l'11/11: fonte del sito fuori dalla pillola, striscia da
176 px, Impostazioni/Primo avvio/Sistema misurate (Sistema non e' una pagina dell'app), calendario
delle Notti sulla riga intera, sito lungo in Tutto della notte e Cerca, icona della scheda
(`frontend/src/icona.svg`, `icona-16.svg`, Issue #56). Gli errori delle tavole restano: in «Da dare».

Le tre voci date il 10/11 sono fatte nella v78, controllate nell'app e sulle tavole il 10/11 (a
700, 760, 860, 960, 1000, 1100, 1280, 1440 e 390 nessuno scorrimento di lato, nemmeno con la barra
vera): pagine fra 700 e 1000 px, sito dal nome lungo, errori della tavola v77 (lo schermo alto 0
di `Riepilogo stati` non ricontrollato: pagina non ancora portata). I resti sono in «Da dare».

Le 14 voci date il 10/11 sono fatte nella v77 (brief archiviato in
`handoff/design/docs/archivio/brief-porting-v76.md`).

- Resta per il porting, non per Design: le etichette degli assi di Statistiche 446 e 449 usano
  `toFixed(1)` col punto; nell'app i numeri li formatta il frontend con la virgola.
- Risposta a Design (v68): le quattro vie del cielo del sito sono quelle dell'app (Dalle misure =
  `frames`, Bortle a mano = `scale`, SQM a mano = `measured`, Dalla mappa = `service`; `sito.md`
  74-76); il servizio e' quello della mappa della luce artificiale.
