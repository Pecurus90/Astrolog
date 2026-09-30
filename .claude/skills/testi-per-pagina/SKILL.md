---
name: testi-per-pagina
description: Usa quando scrivi o modifichi un testo mostrato all'utente. Dice come si scrive (sempre attraverso la traduzione), quando si traduce nelle altre lingue (per pagina finita, non per stringa), quali lingue sono attive, e quali dati NON si traducono mai.
---

# Testi per pagina

**Cosa.** Ogni testo all'utente passa da `t('chiave')`, mai scritto a mano nel componente.
Si costruisce in **italiano**; quando una **pagina e' finita e collaudata** la si affida al
`traduttore`, che la porta in un colpo nelle **lingue attive** -- oggi l'inglese. Le altre
(de, fr, es) arrivano quando un utente le chiede: aggiungerne una e' un giro del traduttore
su ogni pagina, non un progetto. La regola vale per pagina, non per stringa: mentre la
struttura si muove, tradurre ogni riga piu' volte e' lavoro che si butta. Il mobile, che
arriva alla fine, riusa le stesse chiavi: si traducono solo quelle che nascono con lui.

**Le chiavi e i file sono in inglese** (`night.hours`, non `notte.ore`): sono nomi nel
codice. I **valori** italiani sono la sorgente.

**Prima di creare una chiave, cerca se esiste.** Il grep si fa sul **nome** della chiave e
sul **testo italiano**: la stessa frase con due chiavi e' una duplicazione, e il traduttore
la tradurra' due volte in due modi.

**Come si verifica.** Nessun letterale per l'utente fuori da `t()`. Una pagina dichiarata
finita ha tutte le sue chiavi in tutte le lingue attive: e' la guardia i18n a dirlo,
pagina per pagina. L'elenco delle lingue attive vive in un posto solo nel frontend, e la
guardia lo legge da li'.

## Le tre nature del dato

1. **Identita' universale** (designazioni: `M 31`, `NGC 7000`): una forma sola, non si
   traduce.
2. **Codice + traduzione** (tipo di oggetto, costellazione, categoria di filtro): si salva
   il **codice**, l'app traduce con `t('tipo.<CODICE>')`.
3. **Testo per-lingua** (nome descrittivo, descrizione): per lingua, con provenienza.

Mai una stringa-tipo presa da una fonte esterna usata come testo a schermo.

## I numeri scientifici NON si localizzano

RA/Dec, magnitudine, FWHM, dimensione apparente, scala in arcsec/px: identita' universale,
col **punto** decimale in ogni lingua, come in ogni catalogo e software di acquisizione.
Si localizzano **conteggi, migliaia, durate e date**, via l'helper a fonte unica del
frontend.

```tsx
// NO
<span>Nebulosa planetaria</span>
{entry.type}

// SI
{t('type.' + entry.type_code)}
```
