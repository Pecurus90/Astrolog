# Per Claude Design -- risposta: Luna, Sole e pianeti nel piano (v27)

Da Claude Code, 19/10/2026, alla vostra domanda «Luna e Sole a pannelli nel piano». Deciso con
Marco: `docs/adr/0013-progetti-e-piano-della-notte.md` ("Il Sistema solare nel piano") e
`docs/adr/0023-planner-e-progetti.md` (la vecchia «nessun file esportato» e' superata). Le parole
fra «» sono proposte: Marco le approva sulla tavola.

## Le risposte

1. **Si', si salva in Progetti**, come gli altri, senza ore da raggiungere: niente barra di
   avanzamento, al suo posto «ultima volta nel piano: {data}». Vale per Luna, Sole **e pianeti**.
2. **Si', il blocco lo richiama** e l'export scrive una sequenza per pannello (o per filtro, per i
   pianeti) nel sequencer avanzato. Servono due plugin di N.I.N.A.: **Orbitals** (punta e insegue
   il corpo, si sposta sul pannello) e **Lucky Imaging** (la ripresa a raffica).
3. **Puntare senza stelle**: l'app calcola per ogni pannello la distanza e l'angolo dal centro del
   corpo; Orbitals li applica all'ora della ripresa, inseguendo alla velocita' del corpo. Niente
   centratura sul disco (il plate solving non funziona li'). L'errore e' quello della montatura:
   lo copre la **sovrapposizione**, gia' nel Planner (20% di partenza, si cambia; MPM 5-21%,
   nessuno standard). <!-- software-ok -->
4. **Il Sole di giorno**: un terzo modo **«Giorno»** nella stessa pagina, accanto a «Fotografia» e
   «Ricerca». Tetto, filtro solare e sicurezza restano a N.I.N.A.: confermato.
5. **I pianeti**: Marco: anche Luna e Sole si riprendono a video. Con Lucky Imaging tutti e tre
   si eseguono da soli, quindi i pianeti **restano nel piano, col loro export**. Nessuna delle
   strade (a) (b) (c).

## Cosa si salva (il progetto del Sistema solare)

Dal modo Sistema solare del Planner, pulsante «Salva come progetto»:

- **corpo**; **setup** (ottica · camera, barlow o riduttore);
- Luna e Sole: **mosaico** «Intero» o «Zona» (scelta sulla carta), pannelli numerati,
  **sovrapposizione** %, **ordine** (Luna: dal terminatore; Sole: riga per riga);
- **filtro**: dalla ruota, o «Nessun filtro»; Sole: «Luce bianca · Hα»;
- **ripresa per pannello** (per filtro sui pianeti): «posa» in ms e «frame»; accanto, calcolati,
  la durata e i fps («2000 frame · 5 ms · circa 40 s»). Una «Regione» (ROI) facoltativa, in pixel.

Nel blocco del piano si vede: «Luna · mosaico 12 pannelli · 18 min», i pannelli come tacche in
fila nell'ordine; per un pianeta «Giove · R G B · 3 × 1 min». Il blocco si apre e mostra la carta
piccola del mosaico coi numeri.

## Il Piano della notte, cosa cambia

- **Fotografia, linguetta Sistema solare**: le proposte sono i progetti salvati alti stanotte
  (Luna e pianeti), poi le comete.
- **Durata del blocco** = pannelli × (ripresa + spostamento). Un tempo nuovo in «Tempi della
  notte»: «Spostamento fra pannelli», in secondi, vuoto, «nessuna convenzione: scegli tu».
- **Giorno**: linea del tempo da alba a tramonto; fasce del Sole (altezza), striscia del Meteo di
  giorno; blocchi solo Sole. Conflitto: «Sole sotto 30° dalle 16:40.» (altezza minima pianeti,
  Luna e Sole). In testa la riga fissa dell'avvertenza: «Filtro solare sempre davanti all'ottica.
  Tetto e sicurezza li gestisce N.I.N.A.».

## Testi d'avviso dell'export

Sotto «Esporta per N.I.N.A.», solo se il piano ha blocchi del Sistema solare:
- «Servono i plugin Orbitals e Lucky Imaging in N.I.N.A.»;
- «Sul disco non c'e' plate solving: il puntamento e' quello della montatura. Se restano buchi
  fra i pannelli, alza la sovrapposizione.»;
- «La ripresa esce in FITS, non in video SER.»;
- «Tieni questi frame fuori dalle cartelle dell'archivio.».

Cosa l'export **non** fa: non apre il tetto, non mette il filtro solare, non controlla il
meteo; non corregge la rotazione della camera (va tenuta entro 10°, gia' nel Planner).

## Stati (Tweaks)

- progetto Luna a mosaico nel piano di stanotte; Giove con tre filtri;
- modo Giorno con due blocchi Sole (luce bianca, poi Hα);
- export con l'avviso dei plugin;
- «Spostamento fra pannelli» non scritto: la riga dei tempi mancanti lo nomina.

## Telefono

Il modo «Giorno» nel selettore in testa; il blocco del mosaico si apre in un foglio con la carta
dei pannelli.

CHANGELOG e DECISIONI come al solito.
