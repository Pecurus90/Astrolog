---
name: per-altri-utenti
description: Usa quando scrivi o modifichi codice che legge un header FITS, normalizza un nome (filtro, strumento, oggetto), interpreta una cartella o un nome di file, o assume qualcosa sul software di acquisizione. Impone il principio 1 - si progetta per chi la usera', non per Marco - e dice qual e' la sua macchina.
---

# Per altri utenti

**Cosa.** Ogni regola che legge un header, un nome o una cartella vale per **un archivio
qualunque**, non per quello di Marco. Il suo archivio e' **un** caso di prova: scritto con
NINA, due camere, nove filtri, una convenzione di cartelle. Il rilascio ne avra' cento
diversi.

**Quando scatta.** Prima di scrivere `header.get("...")`, una regex su un nome, un
`if` su un valore letto da un file, o un percorso composto a mano.

**Come si pensa.** Per ogni chiave o nome che stai per leggere, chiediti:

- **chi altro la scrive, e come?** I software di acquisizione non sono uno (l'elenco di
  quelli nel corpus sta in `docs/coda.md`, ed e' l'unico): scrivono chiavi diverse per la
  stessa cosa, la stessa chiave con significati diversi, e alcune non le scrivono affatto;
- **da dove viene questa soglia?** Una soglia nuova cita la **convenzione pubblica** da
  cui viene (okta WMO, Nyquist, Beaufort, la scala di Bortle). Se viene "dall'archivio di
  Marco" non e' una soglia, e' una coincidenza: reggerebbe a un trasloco in Arizona?
- **cosa succede se manca?** Un header senza `RA`, senza `FILTER`, senza `OBJECT` e' un
  caso normale, non un errore: il frame entra lo stesso e la superficie dice cosa non sa;
- **e se e' scritto in un altro modo?** `Hα`, `Ha`, `H-alpha`, `HA 7nm`, `Halpha`: lo
  stesso filtro. Il vocabolario si allarga, non si assume;
- **e su un altro sistema?** Percorsi con spazi, accenti e caratteri non latini, percorsi
  **oltre i 260 caratteri** su Windows (una cartella di archivio profonda li supera: si
  usa la forma lunga), maiuscole indifferenti su Windows e no su Linux, un NAS montato in
  rete dove leggere un file intero costa secondi: **la scansione legge l'header, mai i
  pixel**. E **il fuso e' quello del sito**, mai
  `date.today()` del server: la notte va da mezzogiorno a mezzogiorno dove sta il
  telescopio, e l'archivio si consulta da fuori casa.

**La macchina.** `backend/tests/header/` e' il **corpus di header veri**: almeno un file per
software di acquisizione, presi da archivi reali (mai scritti a mano da memoria), e **piu'
d'uno quando lo stesso software si comporta diversamente da utente a utente** -- dell'ASIAIR
ce ne sono tre, perche' il nome che scrive in `TELESCOP` cambia da persona a persona, e con un
header solo la regola sbagliata sembrava quella giusta. Ogni test
di lettura e normalizzazione **attraversa tutto il corpus**, non un header solo. Una regola
nuova che regge sul corpus intero e' una regola; una che regge su NINA e' un'ipotesi. Il
corpus cresce ogni volta che arriva un header che rompe qualcosa: quell'header entra prima
della correzione, e la correzione lo fa passare.

**Il corpus non porta dati personali.** Un header vero contiene `SITELAT`/`SITELONG` -- la
casa di chi l'ha scritto -- e a volte nomi e percorsi. Entra **anonimizzato**: coordinate
spostate, nomi e percorsi sostituiti, tutto il resto intatto. Un test lo pretende: nel
corpus nessuna coordinata di sito reale.

**Cosa e' vietato per costruzione**

- un nome di filtro, camera o telescopio scritto in chiaro nel codice come "il" caso;
- una convenzione di cartelle (`Oggetto/Data/...`) data per scontata;
- un dato **stimato al posto di uno mancante** perche' "di solito e' cosi'".

```python
# NO - vale solo per chi ha questa camera e questo software
if header["INSTRUME"] == "ATR2600M":

# SI - la regola vive nel vocabolario, il codice chiede
corpo = vocabolario.camera(header.get("INSTRUME"))   # None se non lo conosce, e lo dice
```
