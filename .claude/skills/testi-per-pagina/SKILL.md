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

**Il tono** (Marco, 8/10/2026: "nomi professionali ... che corrispondono a quello che sono e un
tono neutro come ogni app al mondo"). Due regole, e valgono per ogni testo nuovo o toccato:

- **Nomi veri.** Ogni cosa si chiama col suo nome: ASTAP, sito di osservazione, cartella, chiave
  API. Mai un nome inventato dall'app ("il riconoscitore"), mai una metafora. Il nome tecnico
  vero si usa (seeing, plate solving); il gergo di chi programma no (container si', "spina" no).
- **Tono neutro.** L'app non parla in prima persona ("non trovo", "la leggo"), non spiega
  perche' fa le cose, non rassicura ("non e' un guasto"), non da' del tu discorsivo. Dice cosa
  c'e' e cosa fare: "Cartella non raggiungibile", "Salva sito", "Facoltativo." Un bottone e' un
  verbo o un verbo e un nome; un titolo e' un nome; un errore dice cosa non e' riuscito e, se
  c'e', il rimedio.
- **Le lettere accentate sono vere a schermo** (`è`, non `e'`): il file resta ASCII con gli
  escape. I testi vecchi scritti con l'apostrofo si correggono quando si tocca la loro pagina.

La casa delle parole e' `docs/domini/glossario.md`; le pagine si rivedono una alla volta, con
Marco, testo di oggi accanto alla proposta.

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
