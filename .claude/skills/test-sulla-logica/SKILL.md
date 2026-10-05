---
name: test-sulla-logica
description: Usa quando aggiungi o modifichi logica in backend/astrolog, scrivi un test, o scrivi una guardia (un hook di pre-commit, un test di fonte unica). Dice cosa si prova, dove, come si tiene la suite veloce, e come si dimostra che un controllo controlla.
---

# Test sulla logica

**Cosa.** La logica nuova -- parsing, normalizzazione, identificazione, raggruppamento,
schema -- nasce **dal suo test**: prima il caso che deve passare, visto **rosso**, poi il
codice che lo fa passare. Non e' "una funzione, un test": e' **una regola, un test che
diventa rosso se la regola si rompe**. Un test scritto dopo, guardando il codice, prova
che il codice fa quello che fa, non quello che deve. Un test prova una regola su un caso
che la distingue, non ricopia il codice: **cambia la costante e guarda se il test diventa
rosso** -- se resta verde, il test prende l'attesa dal codice e non prova niente.

**La copertura ha un pavimento, ed e' bloccante** (il numero sta in `.pre-commit-config.yaml`): non
misura la qualita' dei test, misura il codice che **nessun** test attraversa -- ed e'
quello che va guardato riga per riga prima di dichiarare una fetta fatta.

**Dove.** `backend/tests/` e' la suite **veloce**, ed e' cio' che pre-commit gira a ogni
push. I test numerici pesanti (l'analizzatore sui
fixture, un solve vero) portano `@pytest.mark.lento` e girano a richiesta e in CI.

**Il DB nei test si crea da `schema.sql`**, in un file temporaneo per test, via una fixture
sola. Non esistono migrazioni da provare.

**Casi di altri utenti, non solo di Marco.** Un test di normalizzazione vale se prova un
header che Marco non ha mai avuto: i test di lettura attraversano tutto il corpus (la sua
regola sta in `per-altri-utenti`), e i casi limite gia' imparati stanno nei test di
`old/` -- quando porti un modulo, porti anche quelli.

**Un pattern letto non e' un pattern verificato.** Una regola sui nomi (un filtro, una
sigla di catalogo, un marcatore di pannello) si prova con **due liste**: cio' che deve
prendere e cio' che **non** deve prendere. La seconda e' quella che manca sempre.

**Quando due chiavi rispondono alla stessa domanda, il banco e' una TABELLA, non un elenco
di asserzioni**: una riga per valore, una colonna per chiave, e ogni valore provato su
tutte. Un valore provato su una colonna sola e' dove nascono le inversioni -- una modifica
da tre righe sposta la risposta sulla chiave scoperta e la suite resta verde (es. `CALSTAT`
a lettere e `CALIBRAT` a si'/no, dove la stessa parola dice il contrario).

**Una guardia si vede rossa prima che verde.** Un hook, un controllo di pre-commit, un test
di fonte unica: si scrive, si fa fallire sul caso che deve bloccare, e solo dopo si
sistema. Un controllo che non ha mai visto il difetto puo' essere sempre-verde per un
errore di regex, e nessuno lo saprebbe.

**Il frontend si verifica in tre modi**, e nessuno copre gli altri due: `vitest` (la
logica), `vite build` (la sintassi nei file che nessun test importa), `eslint` (gli
identificatori usati senza import). Pre-commit e la CI li girano tutti e tre. **Il linter e' minimo
per costruzione**: poche regole, ognuna con il difetto che prende scritto accanto; un
controllo che litiga con lo stile viene spento, e un controllo spento e' peggio di uno
assente perche' la sua riga continua a promettere.

**I test non dipendono dalla lingua della macchina.** La suite frontend parte da una lingua
fissata in un solo posto; chi asserisce testo-utente passa dalla traduzione, mai dalla
stringa scritta a mano.

**Quando ripari una duplicazione, lasci un test** che si rompe se il pezzo torna in due case.

**Un refactor si prova con le snapshot** (`backend/tests/test_snapshot_comportamento.py`, syrupy):
restano identiche o il comportamento e' cambiato. Aggiornarle e' una decisione di Marco (hook).
