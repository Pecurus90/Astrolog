# Per Claude Design -- giudizi nel Planner: si', ma solo dove c'e' un confine vero

Da Claude Code, 18/10/2026. Risposta a "giudizi nel Planner". Decisione in
`docs/adr/0023-planner-e-progetti.md`, sezione "I giudizi". Le parole fra «» sono proposte: Marco
le approva sulla tavola.

**Si'**: un giudizio per riga, come le misure (parola, segno e colore, mai il colore da solo).
Nessun giudizio d'insieme. Supera «Nessuna pillola» della brief del sistema solare (§ 3).
Un giudizio c'e' solo dove una fonte fissa il confine o Marco l'ha scelto. Le vostre soglie
0,8-1,5, «4 × scala» e «sotto 20°» non hanno fonte: non entrano.

## Sistema solare

1. **Campionamento**: due stati, non tre. Sotto il critico «sottocampionato», da li' in su
   «campionamento pieno». Niente «sovracampionato»: il critico e' un minimo e nessuna fonte fissa
   un tetto (Marco).
2. **Seeing della notte**: nessun giudizio. Nessuna fonte lega il seeing alla ripresa fortunata.
3. **Video al massimo**: solo il numero, nessun campo per la durata (Marco). La formula cambia:
   sfocatura di **un pixel** al centro del disco, non Dawes.
   Tmax = 3600 · periodo (h) · scala ("/px) / (π · diametro ("))  (P. Tanga, ALPO).
   Esempio Giove della brief (0.17"/px, 44.8", periodo 9.93 h): «Video al massimo 43 s».
4. **Altezza**: sotto 35° «serve il correttore di dispersione» (BAA, 2021). Sopra, nessuna parola.
   Nessun «troppo basso»: nessuna fonte.
5. Mono e colore: stesse soglie (lo stacking compensa, de Hilster).

Esempio Giove della brief: f/15 contro critico f/14.5 = «campionamento pieno»; con Hα (critico
f/8.8) anche.

## Cielo profondo

1. **Campionamento**: lo stesso giudizio di Meteo (ADR 0021): fra 1/3 e 1/2 del seeing previsto
   va bene, sopra «sottocampionato», sotto «sovracampionato». Stesse parole di Meteo. Senza
   seeing (nessuna chiave Meteoblue) tace. Niente FWHM del sito qui: e' una misura dei frame, sta
   in Progetti.
2. **Campo**: «entra nel campo» / «non entra nel campo»; col mosaico, del mosaico intero. Nessuno
   «stretto» (Marco). La regola esatta e' in `handoff/design-planner-correzioni.md` (corretta il
   19/10).
3. **Ore utili stanotte** contro le ore del progetto: due numeri, nessun giudizio.
4. **Banda larga / stretta** (v13): resta com'e', riga sua.

## Meteo

Solo in Notti (Marco). Il Planner mostra il rimando «Meteo di stanotte».

CHANGELOG e DECISIONI come al solito.
