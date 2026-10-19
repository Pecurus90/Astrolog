# Per Claude Design -- Piano della notte v27: linguette, Sistema solare, automazione

Da Claude Code, 19/10/2026. Risponde alla vostra «Luna e Sole a pannelli nel piano» e cambia la
v26 in tre punti. Decisioni in `docs/adr/0013-progetti-e-piano-della-notte.md` ("Il Sistema
solare nel piano", "Le linguette e la postazione") e `docs/adr/0023-planner-e-progetti.md`. Le
parole fra «» sono proposte: Marco le approva sulla tavola. Tutto il resto della v26 resta.

## 1. Tre linguette per tecnica (al posto dei modi)

Via il selettore «Fotografia» · «Ricerca» e il modo «Giorno». In testa, per postazione e per
notte, tre linguette: **«Deep sky» · «Sistema solare» · «Ricerca»**. Una postazione fa una
linguetta per notte; due postazioni possono farne due diverse. Cambiare linguetta con blocchi
nel piano chiede: «Il piano di stanotte si svuota: cambio?» · «Cambia» / «Annulla».

- **Deep sky**: progetti DSO dal Planner e **comete** (pose lunghe, come il deep sky). Le comete
  per sigla, posizione ricalcolata per ogni blocco (dalla v26).
- **Sistema solare**: **Luna, pianeti, Sole**, tutto a video. Un interruttore **«Notte ·
  Giorno»**: Notte va da tramonto ad alba (Luna, pianeti); Giorno da alba a tramonto (Sole), con
  la striscia del Meteo di giorno e in testa la riga fissa «Filtro solare sempre davanti
  all'ottica. Tetto e sicurezza li gestisce N.I.N.A.».
- **Ricerca**: invariata dalla v26 (elenco unico, Criteri «Esopianeti · NEO · Variabili»).

«Completa la notte» / «Rifai la notte», conflitti, totali: uguali in tutte e tre.

## 2. Il Sistema solare si salva e va nel piano

**Progetti**: Luna, Sole e pianeti si salvano dal modo Sistema solare del Planner («Salva come
progetto»), senza ore da raggiungere: al posto della barra «ultima volta nel piano: {data}».

Campi:
- **corpo**; **setup** (ottica · camera, barlow o riduttore);
- Luna e Sole: **mosaico** «Intero» o «Zona» (sulla carta), pannelli numerati, **sovrapposizione**
  % (20% di partenza, gia' nel Planner), **ordine** (Luna: dal terminatore; Sole: riga per riga);
- **filtro**: dalla ruota o «Nessun filtro»; Sole «Luce bianca · Hα»;
- **ripresa** per pannello (per filtro sui pianeti): «posa» in ms e «frame»; accanto, calcolati,
  durata e fps («2000 frame · 5 ms · circa 40 s»); «Regione» (ROI) facoltativa, in pixel.

**Blocco nel piano**: «Luna · mosaico 12 pannelli · 18 min», pannelli come tacche in fila
nell'ordine; «Giove · R G B · 3 × 1 min». Si apre e mostra la carta piccola del mosaico coi
numeri. Durata = pannelli × (ripresa + spostamento).

**Puntare senza stelle**: l'app calcola per ogni pannello distanza e angolo dal centro del corpo;
il programma li applica all'ora della ripresa, inseguendo alla velocita' del corpo. Niente
centratura sul disco: il plate solving li' non funziona; l'errore della montatura lo copre la
sovrapposizione.

**Il programma che esegue il video e' ancora da scegliere** (Marco): N.I.N.A. coi plugin Orbitals
e Lucky Imaging, oppure SharpCap Pro. Disegnate il pulsante dell'export di questa linguetta con <!-- software-ok -->
un nome segnaposto «Esporta per {programma}» e la riga d'avviso vuota: i testi arrivano con la
scelta.

## 3. Automazione della postazione (Impostazioni)

Marco: chi ha un pannello per i flat o un coperchio motorizzato lo dice, e la sequenza esportata
li usa; chi non li ha non vede quei passi. Nella sezione «Planner», un gruppo per postazione
**«Automazione»**:

| riga | valori | effetto nel piano |
|---|---|---|
| «Coperchio motorizzato» | Si' / No | Si': «Avvio» lo apre, «Chiusura» lo chiude |
| «Pannello per i flat» | Si' / No | Si': a fine notte un blocco «Flat» |
| «Flat per filtro» | numero, vuoto | quanti flat per ogni filtro usato stanotte |
| «Dark-flat» | Si' / No, e numero | dopo i flat, stesso numero di partenza |
| «Riscaldatore anticondensa» | Si' / No | Si': acceso in «Avvio», spento in «Chiusura» |

Riga sotto: «I flat si fanno solo per i filtri usati stanotte.». Numeri vuoti, fonte «nessuna
convenzione: scegli tu»; nei Tweaks 20 e 20 d'esempio.

Un tempo nuovo in «Tempi della notte»: «Flat e dark-flat», in minuti, vuoto. E «Spostamento fra
pannelli», in secondi, vuoto.

**Sulla linea del tempo**: dopo «Chiusura» un blocco **«Flat»** con l'elenco dei filtri («Flat ·
Hα OIII · 20 + 20»); i pezzi di «Avvio» e «Chiusura» elencano coperchio e riscaldatore se
accesi. Con «Pannello per i flat» su No: niente blocco Flat. Sul telefono uguale, in verticale.

## 4. Tweaks

- le tre linguette, Sistema solare in Notte (Luna a mosaico, Giove con tre filtri) e in Giorno (due
  blocchi Sole, luce bianca poi Hα);
- una postazione con coperchio e pannello (Avvio e Chiusura completi, blocco Flat) e una senza;
- tempi mancanti: la riga nomina anche «Spostamento fra pannelli» e «Flat e dark-flat».

## Fuori

- Flat al crepuscolo (sky flat): non ora.
- Nessun comando diretto all'hardware dall'app: tutto passa dal file esportato.

CHANGELOG e DECISIONI come al solito.
