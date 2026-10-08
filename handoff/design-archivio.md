# Brief per Claude Design -- l'Archivio e la ricerca nella barra

Dopo le Notti (v29-v30). Vale tutto il primo brief ([`design-brief.md`](design-brief.md)) e il
foglio attuale (v30). Si chiedono **due cose**: la pagina **Archivio**, e il **campo di ricerca
nella barra in alto**, che oggi nel telaio c'e' solo come posto vuoto.

Il metodo e' quello delle Notti: la pagina **esiste gia'** e funziona, coi dati veri; le manca la
forma. Sotto c'e' **esattamente** cio' che l'API manda oggi. Un dato che non sta qui non va
disegnato: per portarlo dovremmo prima costruirlo, e il disegno resterebbe fermo (e' successo al
primo brief dell'Archivio, settembre 2026).

Consegna come per le Notti: prima le proposte (`pagine/archivio.html`, `archivio-stati.html`, e
la barra con la ricerca aperta), classi `pr-`; scelta la forma, i mattoni nel foglio (v31,
`73-pagina-archivio`) e le pagine senza `pr-`.

---

## 1. Cosa racconta la pagina

L'Archivio risponde a *"cosa ho ripreso, e quanto"*. Le Notti dicono *quando*; qui si guarda per
**oggetto**. Una riga e' un **gruppo di frame**: un oggetto, oppure un **mosaico** confermato.
Un oggetto ripreso anche dentro un mosaico ha due righe: il mosaico porta i suoi frame, l'oggetto
solo quelli fuori. La conta lo dice: "12 oggetti e 1 mosaico".

Domani la riga sara' un **progetto concluso** (i progetti non esistono ancora): cambiera' quali
righe arrivano, non come si mostrano. Il disegno non va rifatto quel giorno.

**Vanno disegnate tutte e due le viste**, gia' montate: **carte** (di apertura: "guardo cosa ho")
ed **elenco** ("confronto", una tabella con oggetto, tipo, costellazione, frame, ore, filtri,
mosaico). Si passa dall'una all'altra con un clic, e la vista sta nell'indirizzo
(`?vista=elenco`). Ogni proposta le mostra entrambe, coi loro stati, sul desktop e sul telefono.

## 2. I dati di una riga

| campo | cos'e' | quando manca |
|---|---|---|
| `name` | il nome di catalogo (`M 31`) o quello dato dall'utente | mai, in pratica |
| `constellation` | sigla IAU (`And`): si scrive col nome latino ufficiale (*Andromeda*) | oggetto fuori catalogo |
| `type_code` | che cos'e' (galassia, nebulosa planetaria, ammasso globulare... 19 tipi) | fuori catalogo |
| `frames` | quanti frame | -- |
| `integration_s` | le ore (in secondi; a schermo ore) | puo' essere 0 con frame: vedi `untimed` |
| `untimed` | frame che non dicono la durata | mai "0 h": si dice "N senza tempo" |
| `filters` | i filtri: nome, banda, frame e ore di ognuno, nell'**ordine dell'app** (L, R, G, B, Ha, OIII, SII, a colori, altre bande, non si sa, senza filtro) | vuoto: i file non dicono il filtro |
| `panels` | quanti pannelli, se e' un mosaico | `null` per un oggetto |
| `panel_list` | per ogni pannello: l'oggetto (o nessuno), il centro (RA, Dec in gradi), frame, ore | vuoto per un oggetto |

I colori dei filtri sono quelli del v30, uno per banda. **Novita' rispetto a oggi**: l'API manda
per ogni filtro anche i **frame**, non solo le ore; la riga puo' dirli come la legenda delle Notti.

**Non esistono, e non vanno disegnati:** anteprima o miniatura (il pozzo della carta resta vuoto);
la data dell'ultima notte (decisione di Marco: "quando" sta nelle Notti); progetti, obiettivi,
stato; scheda dell'oggetto; numero di notti per oggetto; magnitudine, dimensioni, coordinate
dell'oggetto; il nome comune sulla riga ("Galassia di Andromeda": c'e' solo nella ricerca).

## 3. La barra della pagina (gia' montata, mai disegnata)

Nell'ordine di oggi: la vista (carte/elenco), **cerca** (nome, sigla o catalogo, qualunque grafia:
`m31`, `NGC 224`), **catalogo**, **costellazione**, **filtro usato**, **solo i mosaici**,
**periodo** (gli anni, oppure "scegli le date" dal/al), **sito**, **ottica**, **camera**; in coda
l'**ordine** (nome, ore, frame; di partenza nome, M 13 prima di M 103) e la **conta** dei trovati.

- Le tendine offrono **cio' che l'archivio ha**, non tutto il catalogo. Sito, ottica e camera
  compaiono solo se sono almeno due; una tendina senza voci non compare.
- Periodo, sito, ottica e camera **restringono i frame**: la riga dice le ore di quel periodo, non
  della sua vita. Il numero dei pannelli di un mosaico invece resta.
- Tutto sta nell'indirizzo: un archivio filtrato si manda a qualcuno.
- Mentre arriva la risposta resta a schermo cio' che c'era, e il segno dell'attesa sta sul campo e
  sulle tendine, non sulle righe.
- 100 righe per volta, "Mostra altri" (come le Notti: "100 oggetti di 240").

Una barra con nove controlli e' tanta: va disegnata anche come si piega sul telefono.

## 4. Gli stati

- **In lettura** (la prima risposta non c'e'): oggi un testo, serve uno scheletro.
- **Errore**: una frase e "Riprova".
- **A mani vuote** (primo avvio, nessun frame): una frase e "Scegli le cartelle". Senza barra.
- **Niente trovato** (i filtri non trovano niente): la barra resta, e c'e' "Togli i filtri". E'
  un'altra cosa dal vuoto: confonderli manda l'utente a sistemare la cosa sbagliata.
- **Una cella che non sa** (tipo, costellazione, filtri): un segno e la parola "non si sa", mai un
  trattino muto.
- **Un oggetto aperto dalla ricerca** (`?key=`): l'Archivio ristretto a quella riga sola. Deve
  dire che e' ristretto, e come tornare a tutto (come "Tutte le notti").

## 5. La ricerca nella barra in alto

Trova **oggetti, notti, attrezzatura e siti** dell'archivio, da ogni pagina. Non le pagine
dell'app: c'e' il binario. Si apre un menu sotto il campo, **diviso per gruppo**, poche voci per
gruppo (5) e quante ce ne sono in tutto; frecce e Invio. Campo vuoto: nessun menu.

| gruppo | una voce dice | si apre |
|---|---|---|
| oggetti | nome di catalogo e, se c'e', il nome comune ("M 31 · Andromeda Galaxy"); frame e ore; se e' un mosaico, i pannelli | l'Archivio ristretto a lui |
| notti | data, sito, frame e ore della notte | le Notti su quella notte |
| attrezzatura | nome e genere (camera, ottica, filtro...); frame e ore, oppure "non ancora contato" / "i file non lo dicono" | la sua scheda in Attrezzatura |
| siti | nome, quante notti | il sito nelle Impostazioni |

Le notti si trovano **per data**, come la si scrive ("25/9", "2026-09-25", "25 settembre",
"settembre 2026"; "5/6" vale in tutti e due i versi), **o per oggetto ripreso**: "M31" mette nel
gruppo notti anche le notti di M 31. Ore mai "0 h": "senza tempo". Nessun risultato: va detto.

Sul telefono il campo sta nella prima riga della barra (telaio v20): il menu prende la larghezza.

## 6. Cose aperte dal primo brief

- `as-segmentato--caricamento` spegne il mouse ma non la tastiera: la barra non lo usa.
- `as-cerca` e `as-barra__cerca` hanno due larghezze massime in conflitto.
- Le classi che la pagina usa e il foglio non ha ancora (`tools/classi_in_attesa.txt`): la barra
  (`as-barra*`), i campi (`as-campo*`, `as-scelta`), le misure della carta (`as-misure*`), la fila
  dei filtri (`as-ore-filtro*`, `as-filtro__pastiglia`), il dato che non sa (`as-dato*`), il segno
  del mosaico (`as-badge*`), le parti della carta (`as-carta__corpo--colonna`, `__segni`,
  `__titolo--riga`, `__piede--prosa`), `as-num`, `as-tabella-guscio`, `as-elenco`, e il vuoto
  (`as-vuoto__titolo`, `__nota`, `__disegno`: il vuoto nuovo e' una frase e un'azione, come nelle
  Notti). Ognuna o entra nel foglio, o la sostituisce un mattone che c'e' gia'.
