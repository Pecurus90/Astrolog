# Per Claude Design -- Piano della notte v27: linguette, Sistema solare, postazione, tempi

Da Claude Code, 19/10/2026. **Brief unica** dopo la v26.1: risponde alla vostra «Luna e Sole a
pannelli nel piano» e raccoglie tutto cio' che Marco ha deciso dopo. Decisioni in
`docs/adr/0013-progetti-e-piano-della-notte.md` ("Il Sistema solare nel piano", "Le linguette
e la postazione") e `docs/adr/0023-planner-e-progetti.md`. Le parole fra «» sono proposte: Marco
le approva sulla tavola. Della v26 resta tutto cio' che qui non cambia (Luna in Impostazioni,
proposte automatiche, «Completa la notte» / «Rifai la notte», conflitti, export, telefono).

## Le risposte alle vostre domande

1. **Luna e Sole si salvano in Progetti**, come gli altri, senza ore da raggiungere. Anche i
   pianeti.
2. **Il blocco li richiama** e l'export scrive la sequenza: per il Sistema solare con **SharpCap <!-- software-ok -->
   Pro**, non con N.I.N.A. (sez. 3).
3. **Puntare senza stelle**: l'app calcola per ogni pannello distanza e angolo dal centro del
   corpo; il programma li applica all'ora della ripresa, inseguendo alla velocita' del corpo.
   Niente centratura sul disco (il plate solving li' non funziona). L'errore della montatura lo
   copre la sovrapposizione, gia' nel Planner (20% di partenza, si cambia; nessuno standard).
4. **Il Sole di giorno**: nella stessa pagina, interruttore «Notte · Giorno» della linguetta
   Sistema solare (sez. 1). Tetto, filtro solare e sicurezza restano a N.I.N.A.: confermato.
5. **I pianeti restano nel piano**, col loro export: si riprendono a video come Luna e Sole.

## 1. Tre linguette per tecnica (al posto di «Fotografia» · «Ricerca»)

In testa, per postazione e per notte: **«Deep sky» · «Sistema solare» · «Ricerca»**. Una
postazione fa una linguetta per notte; due postazioni possono farne due diverse. Cambiare
linguetta con blocchi nel piano chiede: «Il piano di stanotte si svuota: cambio?» · «Cambia» /
«Annulla».

- **Deep sky**: progetti DSO dal Planner e **comete** (pose lunghe, come il deep sky). Le comete
  per sigla, posizione ricalcolata per ogni blocco. Export per N.I.N.A.
- **Sistema solare**: **Luna, pianeti, Sole**, tutto a video. Interruttore **«Notte ·
  Giorno»**: Notte da tramonto ad alba (Luna, pianeti); Giorno da alba a tramonto (Sole), con la
  striscia del Meteo di giorno e in testa la riga fissa «Filtro solare sempre davanti
  all'ottica. Tetto e sicurezza li gestisce N.I.N.A.». Conflitto: «Sole sotto 30° dalle 16:40.».
  Export per SharpCap. <!-- software-ok -->
- **Ricerca**: come nella v26 (elenco unico, Criteri «Esopianeti · NEO · Variabili»). Export per
  N.I.N.A.

## 2. Il progetto del Sistema solare

Dal modo Sistema solare del Planner, «Salva come progetto». In Progetti, al posto della barra:
«ultima volta nel piano: {data}».

Campi:
- **corpo**; **setup** (ottica · camera, barlow o riduttore);
- Luna e Sole: **mosaico** «Intero» o «Zona» (sulla carta), pannelli numerati,
  **sovrapposizione** %, **ordine** (Luna: dal terminatore; Sole: riga per riga);
- **filtro**: dalla ruota o «Nessun filtro»; Sole «Luce bianca · Hα»;
- **ripresa** per pannello (per filtro sui pianeti): «posa» in ms e «frame»; accanto, calcolati,
  durata e fps («2000 frame · 5 ms · circa 40 s»); «Regione» (ROI) facoltativa, in pixel.

**Blocco nel piano**: «Luna · mosaico 12 pannelli · 18 min», pannelli come tacche in fila
nell'ordine; «Giove · R G B · 3 × 1 min». Si apre e mostra la carta piccola del mosaico coi
numeri. Durata = pannelli × (ripresa + spostamento fra pannelli).

## 3. Export del Sistema solare: SharpCap Pro <!-- software-ok -->

Pulsante **«Esporta per SharpCap»**, riga sotto: «Un file di sequenza per SharpCap Pro: parte da <!-- software-ok -->
solo all'avvio.». Avvisi sotto, solo in questa linguetta:
- «Sul disco non c'e' plate solving: il puntamento e' quello della montatura. Se restano buchi
  fra i pannelli, alza la sovrapposizione.»;
- «Il video esce in SER: tienilo fuori dalle cartelle dell'archivio.».
Cosa non fa: non apre il tetto, non mette il filtro solare, non corregge la rotazione della
camera (entro 10°, gia' nel Planner).

## 4. Automazione della postazione: solo Si' / No

In Impostazioni, gruppo **«Automazione»** per postazione, tre righe Si' / No, niente numeri:

| riga | Si' nel piano e nell'export |
|---|---|
| «Tetto o cupola motorizzati» | «Avvio»: apre il tetto prima dell'unpark; «Chiusura»: park, poi chiude il tetto |
| «Sensore di sicurezza» | «Avvio»: «aspetta che sia sicuro» prima di aprire |
| «Pannello per i flat» | «Avvio» apre il coperchio, «Chiusura» lo chiude |

Riga sotto: «La chiusura d'emergenza col maltempo si imposta in N.I.N.A.». Come e quando fare i
flat si decide dopo: niente blocco Flat.

**La ruota portafiltri viene dal setup**: nessuna opzione. Se il setup in Attrezzatura ha una
ruota, il piano conta i cambi filtro; senza, no. Sotto la postazione, in piccolo: «mono · ruota 7
filtri» o «a colori · senza ruota».

## 5. Tempi della notte (al posto delle sette righe della v26)

Nella sezione «Planner», **uguali per tutta l'app**, tutti vuoti, fonte «nessuna convenzione:
scegli tu». Tre gruppi:

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

## 6. Sulla linea del tempo

- **Avvio** e **Chiusura** elencano i passi accesi («aspetta che sia sicuro · apre il tetto ·
  unpark»).
- Il **blocco** aperto mostra il conto: «Hα 12 × 300 s = 1 h · dither 4 × 34 s · filtro 8 s ·
  autofocus 1 × 3 min → 1 h 05». Senza un tempo scritto quella parte manca, e la riga dei tempi
  mancanti la nomina.
- **Conflitto nuovo**: prima di un evento fisso, se il tempo libero e' meno di puntamento +
  autofocus + cambio filtro: «Arrivi al transito con 5 min di margine.».

## 7. Tweaks

- le tre linguette; Sistema solare in Notte (Luna a mosaico, Giove con tre filtri) e in Giorno
  (due blocchi Sole, luce bianca poi Hα);
- export SharpCap con gli avvisi; <!-- software-ok -->
- una postazione col tetto e il sensore, una senza;
- un setup mono con ruota e uno a colori senza (niente cambi filtro nel conto);
- il conflitto del margine prima di un transito;
- tempi mancanti: la riga nomina quelli vuoti.

## Telefono

Le linguette in testa, l'interruttore Notte · Giorno sotto; il blocco del mosaico si apre in un
foglio con la carta dei pannelli; Avvio e Chiusura come fasce nella linea verticale.

## Fuori

- Flat (quanti, dark-flat, quando): dopo, con le sequenze complete.
- Occultazioni asteroidali, supernove, campagne AAVSO: dopo.
- Nessun comando diretto all'hardware dall'app: tutto passa dal file esportato.

CHANGELOG e DECISIONI come al solito.
