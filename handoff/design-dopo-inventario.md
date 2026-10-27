# Per Claude Design -- Ritocchi dopo l'inventario delle tavole

Da Claude Code, 27/10/2026. Inventario delle tavole v58.6 fatto (passo 24.1); Marco ha deciso le
funzioni nuove: tutte entrano, quasi tutte come sono nella tavola. Restano quattro ritocchi. Le
parole qui sotto sono proposte: Marco le approva sulla tavola.

**La regola del porting** (Marco, 27/10): la tavola e' la specifica, aspetto e funzioni; il codice
si adegua. Fanno eccezione solo cio' che non si puo' fare e le decisioni di Marco piu' recenti
della tavola. Per questo i punti 1 e 2 chiedono di cambiare la tavola, i punti 3 e 4 di disegnare
cio' che manca. Il resto della consegna v58.6 si porta com'e'.

## 1. Luna: partenza 25 / 65, dall'orizzonte

Decisione di Marco del 24/10 (ADR 0034), piu' recente della tavola, che ha 25 / 50 e -5 gradi
(`soglie.js`, `LUNA0`; `Impostazioni.dc.html:398-401`).

- I tre campi restano come sono: «Banda larga buona fino a», «al limite fino a», «conta sopra»
  (-5 / 0 / 5 / 10 gradi). L'utente li cambia; cambia solo la partenza.
- Partenza: **25 %**, **65 %**, **0 gradi** (la Luna conta da quando sorge).
- Fonte accanto al 65: «Marco, 24/10/2026» al posto di «nessuna convenzione: scegli tu» (resta
  vero: nessuna convenzione pubblica). Il -5 di TESS resta come scelta, non come partenza.
- Cosa cambia a schermo: le notti con Luna fra 50 e 65 % passano da «solo banda stretta» a «al
  limite»; nelle Notti passate cambiano le pillole della ripresa.

## 2. Ore di posa al posto delle ore utili

ADR 0034 (Marco, 24/10): le ore utili («qualita' da 60», `soglie.js`) escono; al loro posto le
**Ore di posa**, la somma di (Trasparenza / 100) x ore di buio, divisa per banda della Luna: «4,6
ore di posa: 3,1 in banda larga, 1,5 solo banda stretta».

- Dove compare «ore utili» oggi: Dashboard (7 volte), Meteo e Meteo stati (8), Notti e Notti
  stati (2), Piano della notte (3), Planner (10), Riepilogo (1), Impostazioni (1), Sistema (5).
- Il numero protagonista di Meteo e Dashboard diventa «Ore di posa», con sotto la divisione per
  banda quando la Luna divide la notte.
- Piano della notte, proposte del Deep sky (`Piano della notte.dc.html:607`): oggi «{h} visibili ·
  {h} utili». Proposta: «{h} visibili · {h} di posa»; l'ordine «chiude / utili / mancano» diventa
  «chiude / di posa / mancano».
- Planner: dove «ore utili» vuol dire le ore dell'oggetto alto e al buio con il meteo, diventa «di
  posa»; dove vuol dire solo alto e al buio, senza meteo, resta «visibili».
- Impostazioni, Planner: «Stagione: ore utili almeno, il 15 del mese» conta ore senza meteo,
  quindi diventa «ore visibili almeno» (come `planner.md`, «3 ore visibili il 15»). Il verdetto 70 / 40
  resta.

## 3. Attrezzatura: Elimina pezzo

Promesso dal contratto (`docs/domini/attrezzatura.md`, Marco 21/10), non disegnato.

- Si elimina **solo un pezzo senza frame**. Nella scheda del pezzo, «Elimina» testo rosso in fondo
  (come Elimina in Progetti), conferma nella stessa carta: «Eliminare {pezzo}? Non tiene frame.»
  Elimina · Annulla.
- Un pezzo che tiene frame: «Elimina» c'e' ma spento, con sotto «Lo usano {n} frame di {setup}:
  nessuna ora si perde. Uniscilo a un altro pezzo, se e' lo stesso.» e il rimando a «Unisci a».
- Stati: pezzo senza frame; pezzo usato da un setup; pezzo usato da piu' setup; eliminazione non
  riuscita (dati non aggiornati, come gli altri errori della pagina). Desktop e telefono.

## 4. Prima scansione: quali progetti sono finiti

Nuovo (Marco, 27/10). Dopo la prima scansione l'app chiede, una volta, quali oggetti ripresi sono
progetti finiti.

- Una riga per **oggetto e setup** (stessa regola dei progetti: oggetto e setup non si doppiano):
  nome, setup, ore per filtro, ultima notte. Scelta a pillole: **Finito** · **In corso**.
- **Finito**: resta in Archivio, come oggi. **In corso**: diventa un progetto in Progetti, con le ore
  fatte come avanzamento e l'**obiettivo vuoto** («Scrivi l'obiettivo»): l'app non inventa numeri.
- Scorciatoie: «Tutti finiti», e un ordine per ultima notte (i recenti in cima, i piu' probabili in
  corso). Si puo' saltare: «Decido dopo» lascia tutti in Archivio; la domanda resta in Da confermare.
- Dove vive (scelta di Design): fine della prima scansione in Dashboard, oppure una sezione di Da
  confermare. Stati: archivio piccolo (5 righe), archivio grande (200 righe), un oggetto con due
  setup, nessun oggetto riconosciuto (la domanda non c'e'), telefono.

## Cosa NON chiedo

- Il Piano della notte sul telefono e' gia' a elenco (v28.4, approvato il 19/10): non va ridisegnato.
- La scheda Progetti sul telefono resta «affiancata» (v28.3, 19/10).
- I numeri sotto i giudizi delle misure (eccentricita' rispetto al setup, Qn, 30 / 45 gradi, Bortle
  su 4 mesi) li prende l'app dagli ADR 0039 e da `sito.md`; l'aspetto resta quello della tavola.
- L'immagine del cielo passa dal proxy dell'app (ADR 0006): a schermo non cambia niente.
