# Per Claude Design -- Archivio prima del porting

Da Claude Code, 6/11/2026. Tavola `Archivio.dc.html` v58.6 controllata con la lista di
`/porta-tavola` (passo 30). Il resto della tavola si porta com'e'; restano tre punti da disegnare.

## 1. Lo stato di errore

La tavola ha pieno, caricamento, archivio vuoto, nessun risultato, nessun oggetto identificato,
ASTAP assente. Manca l'errore: l'archivio non risponde (`docs/domini/archivio.md:45`, «l'archivio
non risponde, riprova»). `Avviso` col segno «!» esiste, la pagina non lo usa. Serve lo stato nei
Tweaks, desktop e telefono.

## 2. Stili scritti nella pagina

Il foglio dice che restano inline solo posizioni e misure che vengono dai dati o dal gesto
(`per-claude-code-porting.md:20`). In Archivio sono inline anche regole fisse, da portare in
classi del foglio:
- il selettore Carte / Elenco e la tendina dell'ordine (`Archivio.dc.html:29` e `:35`, uguali);
- il tondo per caricare l'anteprima e la griglia sopra la foto (`:63`);
- la colonna della carta (`:53`).

Le misure per formato in `L` (griglie, corpi del testo, `aspect-ratio`) possono restare valori
del componente solo se il foglio non le puo' dire con una classe per formato.

## 3. Carte / Elenco: la scelta solo col colore

La vista scelta si riconosce da anello e colore (`:29`, `v.fg`, `v.sh`); a schermo non c'e'
parola ne' segno («il colore non e' mai da solo»). Basta un segno o il nome della vista scelta.

## Una parola

L'avviso di nessun risultato dice «Togline uno, o tutti con «Togli tutti»» (`:50`), ma il
bottone in `Filtri` si chiama «Togli i criteri» (`Filtri.dc.html:20`). Proposta: «Togline uno, o
tutti con «Togli i criteri»»; Marco la approva sulla tavola.
