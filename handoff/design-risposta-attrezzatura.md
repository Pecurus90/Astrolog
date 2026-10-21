# Per Claude Design -- Attrezzatura: le risposte dall'app

Da Claude Code, 17/10/2026. Controllato sull'app vera (API `GET /api/v1/gear` e le scritture,
la pagina, il dizionario italiano). I testi fra virgolette sono dell'app o approvati da Marco
oggi: si usano parola per parola.

**La forma resta quella scelta da Marco l'11/10** ("schede grafiche"), e l'app oggi e' piu'
indietro del disegno: e' una pagina a righe, coi componenti sopra e i corredi sotto. Nel porting
l'app prende la forma del disegno. Quindi: dove l'app ha gia' la parola si usa quella; dove il
disegno ha un pezzo che l'app non ha ancora, il pezzo resta e la parola e' qui sotto.

## 1. Cosa manda l'API

- **Corredo**: nome (o niente), ottica, camera, focale effettiva, montatura e le altre parti,
  scala e campo, ore. Ordinati dal piu' usato.
  - Senza nome il titolo e' **"{ottica} + {camera}"** (col "+"); se manca un pezzo, "ottica non
    indicata" / "camera non indicata". Con un nome, "{ottica} + {camera}" scende sotto il titolo.
  - Focale: "{mm} mm". Montatura: "su {nome}".
  - **Rapporto focale**: l'app oggi non lo calcola. Lo calcolera' (focale effettiva / apertura
    dell'ottica, solo se ci sono tutte e due): tenetelo, segnato "(calcolato)".
  - Scala e campo sono **misurati sul cielo** (mediana dei frame risolti): "{n} arcosecondi per
    pixel" / "1 arcosecondo per pixel", "campo {larghezza}° × {altezza}°". Finche' nessun frame
    e' risolto: "campo non ancora disponibile".
  - **Uso: solo le ore** (Marco, 11/10: via frame, notti, oggetti ripresi, "senza durata"). I
    frame restano accanto alle parti del corredo; i filtri del corredo in proporzione, senza cifre.
- **Parti del corredo**: montatura, ruota portafiltri, focheggiatore, riduttore, ottica di guida,
  camera di guida, **programma di ripresa**, filtri. Il programma e' una parte come le altre, coi
  suoi frame, senza ore proprie. Una parte dai file: "{parte}: {nome}" coi frame; una parte
  scelta dall'utente: **"{parte}: {nome} (scelta a mano)"** (Marco, 17/10); una parte che i
  file non dicono: **"da indicare"** (Marco, 17/10: la stessa parola di Da confermare; non "da
  scegliere", non "scelto").
- **Gruppi dei componenti**, in quest'ordine: "Telescopi e obiettivi", "Camere", "Montature",
  "Riduttori e spianatori", "Ruote portafiltri", "Guide", "Camere di guida", "Focheggiatori";
  poi "Filtri". Il titolo dei corredi: "Corredi". Un gruppo vuoto non compare.
- **Le parole che chiedete esistono tutte**: "conteggio in corso"; "non indicato nei file"
  (le ore che i file non dicono); "inserito manualmente" (strumento scritto a mano);
  "non associata a un corredo" (montatura, ottica di guida) e "non associato a un corredo"
  (riduttore).
- **Scheda di un componente**, righe solo se c'e' il valore: "apertura {mm} mm", "focale {mm}
  mm", "monocromatica" / "a colori", "pixel {um} µm", "pixel {um} µm (calcolato)" (dal cielo,
  quando file e utente tacciono), "carico {kg} kg", "peso {kg} kg", "{n} posizioni" / "1
  posizione", "riduzione {fattore}×", "backfocus {mm} mm". Filtro: ogni banda "{banda} {nm} nm"
  o solo "{banda}".

## 2. La scheda del corredo

- Esistono: **"Rinomina"**, **"Nome di {nome}"**, **"Seleziona montatura"**, **"Montatura di
  {nome}"**, la tendina **"Montatura (vuoto: dai file)"** con la voce vuota "--" che torna al
  valore dei file, **"Salva"**, **"Annulla"**, "arcosecondi per pixel", "campo non ancora
  disponibile".
- "(calcolato)" nell'app sta sul pixel del componente; nel corredo lo usate per il rapporto
  focale (sopra).
- "filtri" come soprattitolo: va bene, e' l'intestazione del vostro disegno.
- "aggiungine uno": va bene come gesto quando non si possiede nessun pezzo di quel tipo (apre
  "Aggiungi strumento" col tipo gia' scelto).
- **Sotto la Luna nel campo disegnato: "Luna piena, per misura"** (Marco, 17/10).
- Il gesto di scelta vale per tutte le parti, non solo la montatura (oggi l'app lo offre solo
  per la montatura; il disegno lo estende, ed e' deciso).

## 3. I moduli

- Esistono: **"Aggiungi strumento"** (sempre in vista, anche a mani vuote), **"Nuovo
  strumento"**, il campo **"Tipo"**, **"Modifica"**, **"Unisci a"** (tendina con "--"; scelto,
  nome e campi spariscono).
- Tipi, al singolare: "ottica", "camera", "montatura", "riduttore", "ruota portafiltri",
  "ottica di guida", "camera di guida", "focheggiatore", "Filtro", "Corredo".
- Campi per tipo (l'unita' nell'etichetta): comuni a tutti Marca, Modello, Peso (kg), Note;
  ottica Apertura (mm), Focale nativa (mm); camera Tipo di sensore (mono, a colori), Pixel (µm);
  montatura Carico utile (kg); riduttore Fattore; ruota Numero di posizioni. Filtro: Nome,
  Banda (L, R, G, B, HA, HB, OIII, SII), Marca, Modello. Corredo: "Ottica", "Camera", "Focale
  effettiva (mm)", scelte fra i propri pezzi di quel tipo. Le misure sono maggiori di zero.
- **Obbligatori, confermati**: strumento il nome (il tipo ha sempre un valore); filtro nome e
  almeno una banda; corredo ottica, camera e focale effettiva. Il nome del corredo si da' dopo,
  con Rinomina.
- Pezzi del vostro modulo che l'app non ha ancora e che restano (forma approvata): "Tipo: …
  Cambia", i blocchi "chi è" e "dati tecnici" con "{n} di {m} scritti", "altra…" / "Nuova marca"
  (le marche gia' usate dall'utente), "calcolato" / "dai file" / "inserito" accanto al campo,
  "Quante bande", "Per salvare serve il nome.".
- **Unione**: avviso **"L'unione non è reversibile."** (la frase di Da confermare).
- **Mono / a colori** cambiato su una camera usata: **"{n} frame da rielaborare"** (l'app lo sa
  gia', oggi non lo dice).
- **Scansione in corso**: Salva spento con **"Scansione in corso: si salva al termine."**
  (Marco, 17/10; non "potrai").

## 4. Gli stati

- Caricamento: "Caricamento…".
- Non si legge: **"Attrezzatura non disponibile"** e **"Riprova"** (oggi manca; si aggiunge,
  come in Da confermare).
- Vuota: **"Nessuna attrezzatura"**, **"L'attrezzatura viene rilevata dagli header dei file FITS
  dopo la scansione."**, **"Aggiungi cartella"**; "Aggiungi strumento" resta sopra.
- Dopo il salvataggio: il modulo si chiude e la pagina si aggiorna, nessun messaggio; se ci sono
  frame da rielaborare, la riga "{n} frame da rielaborare".
- Errori di salvataggio, dentro il modulo, sopra Salva / Annulla:
  - "Nome già usato da uno strumento dello stesso tipo."
  - "Nome già usato da un altro filtro."
  - "Scansione in corso: riprova al termine."
  - "Unione non possibile. Nessuna modifica salvata."
  - "Dati non aggiornati: ricarica la pagina. Nessuna modifica salvata."
  - "Corredo già presente (stessa ottica, stessa camera, focale entro il 5%)."
  - "Ottica e camera vanno selezionate fra gli strumenti del tipo corrispondente."
  - ogni altro: "Salvataggio non riuscito".

## 5. Dati d'esempio

Quelli della tavola vecchia vanno bene. "Notte in quota" e' **Askar FRA400 + ZWO ASI2600MM
Pro**, come in Da confermare: allineate la tavola di Attrezzatura. Un corredo senza nome si
scrive col "+" in tutte e due le pagine.
