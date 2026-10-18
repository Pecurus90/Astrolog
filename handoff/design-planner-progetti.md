# Per Claude Design -- Planner e Progetti

Da Claude Code, 18/10/2026. Due pagine nuove e il cerchio dei progetti in Dashboard. Decisioni in
`docs/adr/0023-planner-e-progetti.md` (con 0005, 0006, 0013). Le parole fra «» sono proposte:
Marco le approva sulla tavola. Desktop prima; il telefono si disegna alla fine come le altre
pagine, ma la carta va provata presto su tablet.

## 1. Il percorso

**Trova → Scegli il corredo → Inquadra → Crea → Salva → Segui.** Il Planner fa le prime cinque,
la pagina Progetti l'ultima. Un progetto = oggetto + corredo + inquadratura + ore per filtro.

## 2. Planner

### 2.1 Trova

- Ricerca per nome su **tutto il catalogo** dell'app (non solo l'archivio). Se il nome non c'e',
  la ricerca online (Sesame, CDS) con la fonte accanto al risultato.
- **Criteri** (mai "filtri": la parola e' dei filtri ottici):
  - di catalogo: tipo, dimensione, costellazione, catalogo, magnitudine, AR, Dec;
  - del cielo: altezza minima per una durata minima, distanza dalla Luna.
  Valori di partenza dalle Impostazioni (30°, 1 h, 40°), cambiabili per la ricerca senza salvarli.
- Riga del risultato: nome, tipo, dimensione, **ore utili stanotte**, «sale fino a {alt}° alle
  {ora}», distanza dalla Luna, e il segno se c'e' gia' un progetto.

### 2.2 Il corredo

- Selettore: i corredi di Attrezzatura (nome come la produzione: ottica + camera).
- **«Corredo di prova»**: focale (mm), apertura (mm), riduttore o barlow (fattore), sensore da una
  lista con ricerca (nome del sensore, pixel, risoluzione, mono/colore; niente marche; solo
  sensori di camere astronomiche), oppure **«Sensore personalizzato»**: pixel (µm) e risoluzione
  (px).
  - Mostra campo, campionamento e rapporto focale come la scheda del corredo (ADR 0021).
  - Fascia fissa: «Corredo di prova: solo per guardare. Per salvare un progetto, aggiungilo in
    Attrezzatura.» Il pulsante Salva e' spento e dice perche'.
- Due corredi insieme = due rettangoli concentrici, uno per corredo (stesso centro e angolo).

### 2.3 La carta (Aladin Lite v3)

- La carta occupa **la maggior parte della pagina** (Marco); il resto le sta attorno.
- Fondo fotografico, con un selettore della mappa sulla carta: **DSS2 colore** (partenza),
  **PanSTARRS colore**, **Hα**, **OIII**, **SII**, **OIII · Hα · SII**, **Hα sud**. Hα, OIII e SII
  coprono solo il cielo del nord (65 %): fuori, la carta lo dice («Mappa non disponibile in questa
  zona del cielo») invece di restare nera. Elenco e crediti in ADR 0023.
- Sopra, disegnati da noi: **rettangolo del campo**, **mirino** dell'oggetto (non un'ellisse),
  griglia dei pannelli, orizzonte del sito.
- Trascinare la carta sposta l'inquadratura; il centro si legge in AR/Dec col punto («RA 10.68
  Dec 41.27» come in Da confermare).
- **Rotazione**: cursore **0-180°** e campo numerico, con la parola «dal Nord verso Est». Sui
  sensori quadrati 0-90°. Il rettangolo gira davvero (in senso antiorario per angoli che crescono,
  l'Est e' a sinistra).
- **Mosaico**: interruttore «Mosaico», poi **colonne** e **righe** (1-…), **sovrapposizione %**
  (partenza 20). Pannelli numerati riga per riga dall'alto a sinistra: «Pannello 1», «Pannello
  2»… Sotto: campo totale del mosaico.
- In basso: logo Aladin (obbligatorio) e credito «CDS Aladin Sky Atlas, Unistra/CNRS · {nome della
  mappa}»; con le mappe NSNS anche «Northern Sky Narrowband Survey, S. Ziegenbalg, CC BY-NC-SA».
- **Senza rete**: dove la cache non arriva, stelle disegnate e «Cielo fotografico non disponibile
  senza rete». Nessun pulsante per scaricare il cielo (Marco). Durante il caricamento le tessere
  arrivano a pezzi: nessuno spinner sulla carta intera.

### 2.4 Stanotte e l'anno

Accanto alla carta, per l'oggetto scelto e il sito attivo:
- **curva d'altezza** della notte: buio astronomico, linea dell'altezza minima, orizzonte del sito,
  altezza della Luna, linea «adesso»; ore utili;
- **periodo migliore**: 12 punti (il 15 di ogni mese) con le ore utili; i mesi buoni evidenziati.
Senza sito: «Sito mancante» e «Aggiungi sito», come nelle Notti.

### 2.5 Crea

- **Schema suggerito** dal tipo (emissione SHO, nebulose planetarie e resti HOO, il resto LRGB),
  cambiabile.
- **Filtri**: solo quelli adatti alla camera del corredo, dai filtri di Attrezzatura.
  - camera a colori: nessun filtro, UV/IR, multibanda, anti-inquinamento;
  - camera mono: L, R, G, B e banda singola (Hα, OIII, SII);
  - gli altri sotto «Tutti i filtri», chiuso.
- **Ore per filtro** in ore e minuti (es. Hα 20 h, OIII 30 h, R 20 min). Totale sotto. Col
  mosaico: «per pannello» e il totale del mosaico.
- **Esposizione del frame**, facoltativa, per filtro: serve solo a «mancano circa {n} frame».
- **Salva**. Se esiste gia' un progetto con lo stesso oggetto e corredo: niente doppione, si
  mostra quello («Questo oggetto ha gia' un progetto con questo corredo.» · «Apri il progetto»).

### 2.6 Pianeti, Luna e Sole: simulazione

Dal Trova, scegliendo Mercurio, Venere, Marte, Giove, Saturno, Urano, Nettuno, Luna o Sole, al
posto della carta del cielo compare la **simulazione**. Non si salva: nessun progetto.
- Il **rettangolo del sensore** del corredo (vero o di prova) con dentro il **disco** in scala: fase
  per Mercurio, Venere e Luna, anelli inclinati per Saturno. Disegnato, non fotografato.
- **Data**: partenza stanotte; accanto «prossima opposizione {data}», che porta al disco piu' grande.
- **Barlow / riduttore** (fattore) cambiano la scala subito.
- Numeri accanto: diametro apparente e in pixel, scala, rapporto focale del corredo e **rapporto
  focale critico** per il filtro scelto. Nessuna pillola buono/cattivo. Esempio coerente: C9.25
  (2350 mm, 235 mm) con barlow 1,5× e pixel da 2.9 µm, Giove a 44.8″ → «44.8″ · 264 px»,
  «0.17″/px», «f/15 · critico f/14.5 senza filtro (400 nm)»; con Hα «critico f/8.8 (656 nm)».
- Luna e Sole: anche la griglia del mosaico, come sulla carta.
- Sole: fascia fissa «Solo con un filtro solare a tutta apertura.»

## 3. Progetti

- **Gruppi**: in corso / in attesa / fermi / finiti.
- **Scheda di un progetto**:
  - nome: oggetto + ottica + camera; miniatura: la foto finale se c'e', altrimenti l'inquadratura
    sulla carta;
  - **cerchio di avanzamento** (ore fatte / ore dell'obiettivo), lo stesso della Dashboard;
  - barre per filtro (fatte / obiettivo); col mosaico, la griglia dei pannelli con l'avanzamento
    di ognuno;
  - ultima notte, prossima finestra utile, «fermo da {tempo}»;
  - mediane delle misure (FWHM, eccentricita', SQM…) coi giudizi gia' approvati (ADR 0022).
- **Azioni**: «Apri nel Planner», «Segna come finito» / «Riapri», «Elimina».
  - Elimina: «Il progetto sparisce. I frame restano nell'archivio.»
  - Finito: lo propone l'app quando le ore sono raggiunte («Obiettivo raggiunto. Segnarlo come
    finito?»), lo conferma l'utente.
- **Aperto nel Planner un progetto gia' iniziato**: ore, filtri ed esposizioni si cambiano liberi.
  Se cambiano inquadratura, griglia o corredo, prima di salvare: «{durata} gia' riprese non
  conterebbero piu'.» · «Salva lo stesso» / «Annulla». Il numero e' vero, contato dall'app.
- **Frame senza pannello** (non risolti sul cielo): «{n} frame senza pannello: non risolti.»
- **Vuoto**: «Nessun progetto ancora.» · «Apri il Planner».
- L'avanzamento si aggiorna da solo dopo ogni scansione: nessun pulsante «aggiorna».

## 4. Dashboard

Il cerchio dei progetti in corso usa lo stesso numero e lo stesso disegno della scheda in Progetti.

## 5. Fuori

- **Planetario e solare**: nessun progetto (Marco). C'e' solo la simulazione (2.6) e le
  effemeridi del Sistema solare in Dashboard.
- Nessun punteggio d'insieme e nessuna classifica «i migliori stanotte».
- La pagina delle sequenze e il piano della notte (ADR 0013) sono una brief a parte.

CHANGELOG e DECISIONI come al solito.
