# Planner e Progetti -- resoconto e proposta

Da Claude Code a Marco, 18/10/2026. Da leggere e decidere insieme; poi diventa ADR e brief per
Design. Fonti: ricerca online del 18/10 (codice di N.I.N.A., pagine ASCOM, ASTAP, CDS, produttori
di camere) e le decisioni gia' nel repo (ADR 0005, 0006, 0013; `docs/domini/ereditato.md` A e F;
`docs/domini/mosaico.md`; glossario).

## 0. In breve

- La tua idea combacia quasi tutta con cio' che avevamo gia' deciso (ADR 0013 e il Planner del
  vecchio progetto). Cambiano quattro cose, che ti chiedo a video (sezione 10).
- La carta resta **Aladin Lite v3**: e' ancora la scelta migliore, e la usa anche Telescopius. <!-- software-ok -->
- La rotazione va da **0 a 180 gradi**, non 0-90.
- Il mosaico si fa come N.I.N.A.: colonne × righe e sovrapposizione, **partenza al 20 %**.
- La lista dei sensori la scriviamo noi: nessun elenco aperto e' riusabile.
- Planetario e solare: **niente piano e niente inquadratura**. Basta cio' che la Dashboard avra'
  per il Sistema solare (ADR 0019).
- La pagina si chiama **Progetti**, non "Piani": e' la parola del glossario.

## 1. Il percorso dell'utente

Le sei mosse gia' decise: **Trova → Scegli → Inquadra → Crea → Salva → Segui**.

1. **Trova**: cerca un oggetto per nome nel catalogo dell'app (22.080 oggetti, con le coordinate).
   Se non c'e', lo chiede a Sesame (CDS) e lo tiene con la fonte (ADR 0013). Oppure lo cerca con
   i criteri: tipo, dimensione, costellazione, magnitudine, quanto sale stanotte, distanza dalla
   Luna.
2. **Scegli il corredo**: uno dei corredi veri di Attrezzatura, oppure un **corredo di prova**
   (focale, apertura, sensore dalla lista) per simulare un acquisto.
3. **Inquadra** sulla carta: trascini il rettangolo, giri la rotazione, accendi il mosaico.
4. **Crea**: scegli i filtri (solo quelli adatti alla camera, sezione 6) e le ore per filtro.
5. **Salva**: il progetto va nella pagina Progetti.
6. **Segui**: a ogni scansione, anche quella automatica sul NAS, il progetto si aggiorna da solo:
   ore fatte per filtro e per pannello, cerchio di avanzamento, misure delle notti.

## 2. La carta del cielo: Aladin Lite v3

**Confronto** (licenze lette sui repository):

| | licenza | stato | giudizio |
|---|---|---|---|
| **Aladin Lite v3** (CDS, Strasburgo) | LGPL-3.0 | stabile 3.8.1 (5/3/2026), mantenuta | **scelta** |
| Stellarium Web Engine | AGPL-3.0 | nessuna release, codice fermo dal 2021 | no: AGPL e abbandonato | <!-- software-ok -->
| d3-celestial | BSD | fermo dal 2022 | no: solo disegno, niente fotografie |
| VirtualSky | non open source | fermo dal 2023 | no |

- **Perche' Aladin.** Mostra il cielo fotografato vero e permette di disegnarci sopra
  rettangoli ruotati e griglie. Gira nel browser, anche sul NAS. E' compatibile con la nostra
  licenza GPL-3.0, purche' non lo modifichiamo. Telescopius lo usa per il suo simulatore; <!-- software-ok -->
  N.I.N.A. usa le stesse fotografie (DSS2 a colori del CDS).
- **Le fotografie del cielo** (DSS2 a colori) pesano circa 281 GB: non entrano nell'app.
  Restano le decisioni ADR 0005 e 0006:
  - le immagini passano dal nostro server, che le tiene in cache;
  - nessuno scaricamento per l'uso senza rete (Marco, dopo questa proposta: solo cache);
  - senza rete, un fondo di stelle disegnate da noi.
- **Obblighi**: il logo di Aladin resta visibile; la riga di credito del CDS sta sotto la carta.
- **Un rischio da provare subito**: il supporto ai telefoni di Aladin non e' finito (lo dice il
  suo README). Lo verifico su tablet e telefono prima di disegnarci attorno.
- **Dipendenza nuova**: `aladin-lite` 3.8.1, l'ultima stabile e non la beta. La scelta e' gia'
  nell'ADR 0005; la segnalo perche' e' la prima libreria grande del frontend.

## 3. La rotazione

**Convenzione**: l'angolo si misura dal Nord verso Est, in senso antiorario. E' la convenzione di
ASCOM per i rotatori, di ASTAP (`CROTA2`) e dei frame risolti nell'app. Cosi' il numero del
piano e quello misurato sui frame si confrontano senza conversioni.

**Intervallo 0-180°, non 0-90°.**
- Un rettangolo girato di 30° e uno girato di 120° inquadrano cieli diversi: lato lungo e lato
  corto si scambiano.
- Girato di 180° copre invece lo stesso cielo (l'immagine e' solo capovolta). La norma FITS lo
  dice: le soluzioni vengono "in coppie separate da 180°".
- N.I.N.A. lavora su 0-360. Con un rotatore pieno sceglie da solo il piu' vicino fra l'angolo e
  l'angolo + 180, quindi un piano a 0-180 si esporta senza perdere nulla.
- Solo per i **sensori quadrati** (IMX533, IMX676) basta 0-90: N.I.N.A. lo dice per il rotatore
  a "90 gradi".

**Confronto con i frame**:
- l'avanzamento **non dipende dall'angolo**: un frame conta se e' dell'oggetto, del corredo e
  del puntamento giusti;
- l'angolo misurato sui frame si mostra accanto a quello del piano, confrontato a meno di 180°;
- tolleranza di 1°, il valore di partenza di N.I.N.A. ("Rotation Tolerance").

## 4. Il mosaico

Come il Framing Assistant di N.I.N.A., dal suo codice:
- **colonne × righe**, da 1 × 1 in su (1 × 2, 2 × 1, 2 × 2, 3 × 3...);
- **sovrapposizione in %**, partenza **20 %**: e' il valore di N.I.N.A. Nei forum si va dal 10 al
  40 %; con rotazione imprecisa si sale verso il 25 %;
- pannelli numerati **riga per riga, dall'angolo in alto a sinistra**: «Pannello 1», «Pannello 2»;
- il centro di ogni pannello si calcola sulla sfera (proiezione gnomonica, formula di N.I.N.A.).
  Una griglia piatta sbaglierebbe sui mosaici grandi e vicino al polo;
- **obiettivo per pannello**: le ore per filtro valgono per ogni pannello. Il totale del
  progetto e' la somma.

Da correggere nel repo: `mosaico.md` dice che nessuno dei quattro programmi ha una sovrapposizione
di partenza. N.I.N.A. ce l'ha (20 %, nel codice). Quella frase parlava di come si riconosce un
mosaico dai frame, dove la soglia resta assente; la sistemo.

## 5. La lista dei sensori

- **Nessun elenco aperto si puo' riusare.** Quelli di AstroBin, Telescopius e Astronomy Tools <!-- software-ok -->
  sono proprietari. Quello di Stellarium e' GPL ma ha solo 17 reflex. N.I.N.A. e ASTAP non ne <!-- software-ok -->
  hanno uno.
- **La scriviamo noi**, una riga per sensore, senza marca della camera: nome (IMX571),
  pixel (µm), risoluzione (px), mono/colore disponibili. I millimetri si calcolano, non si
  scrivono. Ogni riga porta l'URL della pagina del produttore da cui viene.
- **Base pronta**: il vecchio progetto aveva 36 sensori (`old/.../sensori.json`), comprese le
  reflex e mirrorless piu' diffuse. Si porta e si ricontrolla riga per riga contro le pagine dei
  produttori trovate oggi (circa 35 sensori: IMX571, 455, 533, 585, 294, 492, 183, 410, 678,
  662, 462, 174, 432, 464, 482, 715, 676, 461, 411, KAF-8300, KAF-16200...).
- **Una trappola trovata**: per lo stesso sensore i produttori danno risoluzioni diverse (IMX585:
  3840 × 2160 per ZWO, 3856 × 2180 per Player One). ZWO da' i pixel utili, gli altri i totali.
  Sotto l'1 % il rettangolo e' lo stesso (regola del vecchio progetto); si tiene il dato utile.
- **Si aggiorna senza rifare l'app** (un file); un sensore che manca si scrive a mano.

## 6. Filtri del corredo

- Il corredo **non ha oggi un elenco di filtri**. I filtri disponibili sono quelli in
  Attrezzatura (scritti a mano o visti nei frame di quel corredo).
- **Regola proposta**, dal numero di bande del filtro (dato gia' in Attrezzatura):
  - **camera a colori**: nessun filtro, UV/IR, multibanda (duo, tri, quad), anti-inquinamento;
  - **camera mono**: L, R, G, B e i filtri a banda singola (Hα, OIII, SII).
- Non e' una convenzione pubblicata: viene da come funziona la matrice di Bayer. Alcuni usano
  l'Hα anche sulle camere a colori. Ti chiedo se gli altri filtri si nascondono o spariscono.
- **Schema suggerito** dal tipo di oggetto, gia' deciso: emissione → SHO, planetarie e resti →
  HOO, il resto LRGB. L'utente lo cambia.
- **Ore per filtro**: in ore e minuti (es. Hα 20 h, OIII 30 h, R/G/B 20 min per le stelle).
  L'esposizione del singolo frame si puo' scrivere, ma non serve: serve solo per dire «mancano
  circa N frame».

## 7. La pagina Progetti

- **Nome del progetto**: oggetto + ottica + camera, come la produzione («M 31 · Askar FRA400 +
  ASI2600MM Pro»). Un oggetto con due corredi fa due progetti: e' gia' deciso.
- **Gruppi**: in corso / in attesa / fermi / finiti (deciso). Ogni scheda mostra il cerchio di
  avanzamento, le ore per filtro (e per pannello), l'ultima notte e la prossima finestra utile.
- **Finito**: lo propone l'app quando le ore sono raggiunte; lo conferma l'utente.
  Alzare l'obiettivo lo riapre.
- **Eliminare** toglie il progetto, mai i frame.
- **Modificare**, la parte nuova della tua idea:
  - **ore, filtri, esposizioni**: sempre liberi. I progressi non si perdono, perche' vengono dai
    frame dell'archivio e non sono scritti a mano;
  - **inquadratura, griglia del mosaico o corredo** su un progetto iniziato: qui l'avviso ha
    senso. Se il centro si sposta, i frame gia' ripresi possono smettere di contare. L'avviso
    dice il numero vero: «12 h 40 min gia' riprese non conterebbero piu'»;
  - **«Rifai l'inquadratura»** riapre il progetto nel Planner con tutto com'era.

## 8. L'avanzamento automatico

- Lo calcola **chi scrive**: la scansione, anche quella automatica sul NAS. La pagina legge
  soltanto (regola "una lettura non calcola mai").
- **Un frame conta per un progetto** se ha stesso oggetto, stesso corredo e centro risolto
  dentro il campo del progetto (o del pannello). Il centro arriva dalla risoluzione di ASTAP. Un
  frame non risolto conta per il nome dell'oggetto, ma non si sa in che pannello.
- La Dashboard mostra lo stesso cerchio: un solo calcolo per le due pagine.
- Le misure delle notti (FWHM, eccentricita', SQM...) arrivano da `measure`, gia' deciso; nel
  progetto si vedono come mediane, con i giudizi gia' approvati.

## 9. Planetario e solare

- **Proposta: nessun piano.** Non c'e' nulla da inquadrare (il pianeta sta al centro), niente
  mosaico (salvo Luna e Sole) e niente ore da accumulare. Si esce se il meteo va.
- Cio' che serve davvero c'e' gia' come idea nell'ADR 0019 (Sistema solare in Dashboard): quando
  culmina, quanto sale, il diametro.
- Per dopo, se lo vorrai: transiti della Grande Macchia Rossa e meridiano centrale di Giove (dati
  JUPOS, il calcolatore di Sky & Telescope). Non lo metto nel brief.

## 10. Cosa decidi tu

1. **Corredo di prova**: si salva un progetto su un corredo che non hai?
2. **Rotazione**: 0-180°, o 0-360° come N.I.N.A.?
3. **Filtri non adatti alla camera**: nascosti dietro «Tutti i filtri», o tolti del tutto?
4. **Progetto iniziato**: si modifica con l'avviso delle ore che non conterebbero piu', o si
   congela?

Tutto il resto e' gia' deciso o ha una convenzione. Dopo le risposte: ADR 0023 «Planner e
Progetti», correzione di `mosaico.md`, brief per Design.
