# Per Claude Design -- Da confermare: le risposte dall'app

Da Claude Code, 17/10/2026. Controllato sull'app vera (API `GET /api/v1/review`, la pagina e il
dizionario italiano). I testi fra virgolette sono quelli dell'app: si usano parola per parola.
Dove la vecchia tavola diceva altro, vince questo.

## 1. L'unita' del conto: le domande

- L'API manda **un numero solo, `to_confirm`: le domande senza risposta**. Non notti, non frame.
  Una domanda risposta e salvata non conta piu'.
- **Il pannello in barra si allinea, come proponete.** "N notti da confermare" non esiste
  nell'app, e le domande non sono raggruppate per notte (sono per cartella, coordinate, filtro,
  intestazioni). Nella pillola il numero e' "{n} da confermare". Nel pannello: le sezioni con
  domande aperte, ognuna col suo conto ("{n} domande", "1 domanda"), e Rispondi che apre la
  pagina su quella sezione. Niente notte d'esempio, niente IC 1396.
- **"N frame fuori dai conti" e' un altro numero** e resta dove sta: Dashboard ("Da riprendere") e
  Notti (frame che non stanno in nessuna notte: senza sito o senza data). Fuori dal pannello.
- In testa alla pagina: "{n} da confermare".

## 2. Le sette sezioni, nell'ordine della pagina

L'API non ha un elenco di tipi: manda sette liste, e l'ordine lo fissa la pagina ("prima i
pezzi, poi come si montano insieme, poi il dove e il quando, poi il cielo"):
**Strumenti duplicati, Filtri, Attrezzatura da completare, Oggetti, Frame senza tipo, Frame
senza sito, Mosaici proposti.** Ogni sezione dice "{n} domande".

**Strumenti duplicati** -- "Strumenti con nome simile e stesse caratteristiche: possono essere lo
stesso strumento rilevato da due programmi. L'unione non è reversibile." Domanda: "{nome} e
{altra} sono lo stesso strumento?" Scelte: "Sì, unisci a {nome}", "No, sono distinti".

**Filtri** -- "Filtri non riconosciuti. L'associazione vale anche per i frame futuri." Domanda:
"Come rispondere per {nome}". Tre strade: **"Filtro esistente"**, **"Modello da catalogo"**
(predefinita), **"Nuovo filtro"** (non "Uno dei miei", "Un modello del catalogo"). Testi:
"Filtro esistente: {nome}"; "Cerca fra i modelli per {nome}", segnaposto "Marca o nome",
"Modelli trovati" (l'elenco compare solo scrivendo), "Nessun modello per «{cerca}». Se non è in
elenco, seleziona Nuovo filtro."; per il nuovo "Nome" e "Banda" (L, R, G, B, HA, HB, OIII, SII).
Chiusa e senza risposta, la riga elenca le tre strade separate da " · ".

**Attrezzatura da completare** -- "Camera, ottica o filtro non indicati nei file. La risposta
vale per tutti i frame con le stesse intestazioni, anche futuri." Parti: "Camera per {nome}",
"Ottica per {nome}", "Filtro per {nome}"; parte non data "da indicare". Camera: i corredi
dell'utente (nome, sotto "ottica · camera") o "Altra camera" (Camera, "Focale (mm)", Ottica
"Facoltativa."). Ottica: le proprie o "Altra ottica" ("Nome dell'ottica"). Filtro: "A colori,
senza filtro", "Nessun filtro", "Filtro esistente"; "Selezionabile dopo aver indicato la
camera.". Prove: "Camera nel file", "Telescopio nel file", "Sensore", "Ottica nei frame";
"Non indicato / Non indicata / Non indicati".

**Oggetti** -- "Oggetto non certo, oppure non indicato nei file né identificato dal plate
solving. La risposta vale per tutti i frame del gruppo." Domanda: "Oggetto per {nome}". Scelte:
i candidati ("nell'inquadratura", "fuori dall'inquadratura", "posizione non nota"), "Altro
nome" ("Nome dell'oggetto"), "Non è un oggetto" con "frame di prova o di messa a fuoco: esclusi
dalle ore"; nessun candidato: "Nessuno". **Oggetti gia' a posto** non sono domande: "{n}
oggetti riconosciuti" / "1 oggetto riconosciuto", gesto "Correggi". Il testo c'e' gia': niente
"lo scrive Marco".

**Frame senza tipo** -- "Tipo di frame non indicato nei file. Finché non viene indicato, i frame
sono esclusi dal conteggio delle ore." Domanda: "Tipo dei frame in {cartella}". Scelte: "Light",
"Calibrazione" (nessun "non so").

**Frame senza sito** -- "Frame ripresi a coordinate che non corrispondono a nessun sito.
L'associazione vale anche per le notti future." Domanda: "Sito per le coordinate {posto}".
Scelte: un sito per riga, "{luogo}, a {km} km", dal piu' vicino, nessuno scelto in partenza.
Prove: "Distanza" ("{km} km dal sito predefinito", solo se c'e' un sito predefinito), "Notti"
per mese, o "Notti non calcolabili senza sito".

**Mosaici proposti** -- "Pannelli adiacenti ripresi con lo stesso corredo. Vengono uniti solo
dopo conferma." Domanda: "{soggetti}, {dove}: mosaico?" con "{n} pannelli". Scelte: "Mosaico"
(campo "Oggetto del mosaico ({dove})"), "Non è un mosaico".

Comuni: "{n} frame" / "1 frame"; prove "Notte", "Camera e telescopio", "Puntamento", "Primo e
ultimo frame", "Oggetti nel campo", "Simile a", "Altri frame", "Durata", "Posizione".

## 3. Gli stati della risposta: quattro, tutti distinti

"senza risposta", "da applicare", "salvata", "cambiata, da applicare" (con "era {era}"). Gesti:
"Rispondi", "Cambia", "Correggi" (oggetto a posto), "Riapri". Sezione tutta risposta, chiusa in
una riga: "{n} risposte da applicare" o "{n} risposte salvate" con Riapri. Indice: "Sezioni",
"{n} senza risposta", "tutte con risposta". Telefono, un caso alla volta: "Tipi di domanda",
"← Tutti i tipi", "caso {k} di {n}", "Caso prima" / "Caso dopo"; conti per tipo "{n} senza
risposta", "{n} da applicare", "{n} salvate", "{n} cambiate, da applicare".
Strumenti duplicati e Filtri non restano "salvata": applicati, escono dalla coda.

## 4. Applica

- Regola in testa: **"Le risposte vengono salvate tutte insieme con Applica. Rispondere è
  facoltativo: senza risposta i frame restano invariati."**
- Piede: "{n} modifiche da applicare" / "1 modifica da applicare", bottone "Applica" (spento a
  zero). Avviso dell'unione: **"Include un'unione di strumenti:"** (grassetto) **"non è
  reversibile."**
- In corso: **"Applicazione in corso…"** (non "Applico…").
- Esito, chiudibile con "Chiudi": "{n} modifiche applicate, {pose} frame da rielaborare" / "1
  modifica applicata, {pose} frame da rielaborare".
- Rifiuti: titolo "Modifiche non applicate" e una di queste frasi (Applica e' una sola
  operazione, quindi finiscono tutte con "Nessuna modifica salvata."):
  - "Oggetto non presente nel catalogo. Nessuna modifica salvata."
  - "Dati non aggiornati: ricarica la pagina. Nessuna modifica salvata."
  - "Scansione in corso: riprova al termine. Nessuna modifica salvata."
  - "Unione non possibile. Nessuna modifica salvata."
  - "Nome già usato da un altro strumento. Nessuna modifica salvata."
  - ogni altro errore: solo "Modifiche non applicate".
  "Nessuna modifica salvata." non e' una riga a se'. "Ricarica la pagina" come bottone non c'e'.

## 5. Gli stati della pagina

- Caricamento: scheletro, "Caricamento…".
- Non si legge: "Da confermare non disponibile" · "Riprova".
- Niente da confermare: **"Niente da confermare"** / **"Nessuna domanda aperta."** Con risposte
  salvate restano le sezioni chiuse in una riga ("N risposte salvate" · Riapri), senza frase in
  piu'. ("L'app ha deciso da sola..." non c'e'.)
- Zero frame: **"Nessun frame in archivio. Le domande compaiono dopo la lettura delle
  cartelle."** · "Aggiungi cartelle" (verso Impostazioni, Cartelle).
- Elenco dei modelli non arrivato: "Elenco dei modelli non disponibile" (avviso d'allarme).
- Nuovo filtro senza banda: nessun messaggio; la banda parte su "--". Non disegnatelo.
- Attrezzatura senza nome: titolo dalla camera, poi telescopio, poi sensore ("W × H px · X µm"),
  infine "Attrezzatura senza nome". Gruppo senza oggetto: "Frame senza nome".
- Filtro scelto che non c'e' piu': nessun testo suo; torna come "Dati non aggiornati: ricarica
  la pagina. Nessuna modifica salvata.".
- **Nessun sito dichiarato**: oggi "Frame senza sito" mostra una domanda senza scelte, e nessuno
  dice perche'. E' un buco dell'app. Disegnate lo stato con la frase approvata da Marco: **"Per
  rispondere serve almeno un sito: si aggiunge nelle Impostazioni."** e il bottone **"Apri le
  Impostazioni"**.

## 6. Dati d'esempio

Vanno bene quelli della tavola vecchia, spostati sul 30 settembre 2026. Usate i nomi dei filtri
e degli strumenti come li scrive l'utente (O3, EQ6-R): sono dati, non parole dell'app.
