# Per Claude Design -- Piano della notte v28: automazione e tempi

Da Claude Code, 19/10/2026. Cambia **la sezione 3 della v27** (Automazione) e **i tempi della
notte** della v26 (sez. 4 e 8). Il resto di v26 e v27 resta. Decisioni in
`docs/adr/0013-progetti-e-piano-della-notte.md`, "Le linguette e la postazione". Le parole fra
«» sono proposte: Marco le approva sulla tavola.

## 1. Automazione della postazione: solo Si' / No

In Impostazioni, gruppo **«Automazione»** per postazione, tre righe Si' / No, niente numeri:

| riga | Si' nel piano e nell'export |
|---|---|
| «Tetto o cupola motorizzati» | «Avvio»: apre il tetto prima dell'unpark; «Chiusura»: park, poi chiude il tetto |
| «Sensore di sicurezza» | «Avvio»: «aspetta che sia sicuro» prima di aprire |
| «Pannello per i flat» | «Avvio» apre il coperchio, «Chiusura» lo chiude |

Riga sotto: «La chiusura d'emergenza col maltempo si imposta in N.I.N.A.».

**Via dalla v27**: «Flat per filtro», «Dark-flat», «Riscaldatore anticondensa», il blocco «Flat»
sulla linea del tempo e il tempo «Flat e dark-flat». I flat si decidono dopo.

## 2. La ruota portafiltri viene dal setup

Nessuna opzione: se il setup in Attrezzatura ha una ruota, il piano conta i cambi filtro; senza
ruota, no. Sotto la postazione, in piccolo: «mono · ruota 7 filtri» o «a colori · senza ruota».

## 3. Tempi della notte (al posto delle sette righe della v26)

Nella sezione «Planner», uguali per tutta l'app, tutti vuoti, fonte «nessuna convenzione: scegli
tu». Tre gruppi:

- **Avvio e chiusura** (minuti): «Raffreddamento della camera» · «Unpark» · «Apertura del tetto»
  · «Park» · «Chiusura del tetto» · «Riscaldamento della camera». Le due del tetto si vedono solo
  se una postazione ha il tetto.
- **Per bersaglio** (minuti): «Puntamento e centratura» · «Autofocus».
- **Durante le pose**: «Cambio filtro» (s) · «Dither col settle» (s) · «Dither ogni» (pose) ·
  «Scaricamento della posa» (s) · «Un autofocus ogni» (ore, stima) · «Meridian flip» (min) ·
  «Spostamento fra pannelli» (s).

Riga sotto: «Scrivi tempi larghi: il margine sta dentro il numero.».

Nei Tweaks, d'esempio (misurati su un setup vero, mai di partenza): 10, 0.1, 1, 0.5, 1, 10 · 2,
3 · 8, 34, 3, 0.5, 2, 3, 5.

## 4. Sulla linea del tempo

- **Avvio** e **Chiusura** elencano i passi accesi (tetto, sensore, coperchio).
- Il **blocco** aperto mostra il conto: «Hα 12 × 300 s = 1 h · dither 4 × 34 s · filtro 8 s ·
  autofocus 1 × 3 min → 1 h 05». Senza un tempo scritto, quella parte manca e la riga dei tempi
  mancanti la nomina.
- **Conflitto nuovo**: prima di un evento fisso, se il tempo libero e' meno di puntamento +
  autofocus + cambio filtro: «Arrivi al transito con 5 min di margine.».

## 5. Tweaks

- una postazione col tetto e il sensore (Avvio: «aspetta che sia sicuro · apre il tetto ·
  unpark»), una senza;
- un setup mono con ruota e uno a colori senza (niente cambi filtro nel conto);
- il conflitto del margine prima di un transito.

CHANGELOG e DECISIONI come al solito.
