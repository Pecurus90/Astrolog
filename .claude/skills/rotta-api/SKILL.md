---
name: rotta-api
description: Usa quando scrivi o modifichi una rotta dell'API (FastAPI) o la forma di una sua risposta. Dice come si scrive una risposta gia' pronta per lo schermo, come si dice "non so" con un campo e non con un null, come si sbaglia con un codice, e che la docstring e' il contratto.
---

# Una rotta e' un contratto

**La risposta e' gia' pronta per lo schermo.** Il frontend formatta e basta (un fatto, una casa):
quindi la rotta manda i valori **derivati** -- non le materie prime da combinare di la'. Se
una pagina ha bisogno di un numero che la rotta non manda, si allarga la rotta, non si
calcola nel componente.

**"Non so" e' un campo, non un `null` muto.** Dove un valore puo' mancare, la risposta porta
il valore **e** il perche' manca, con un **codice** da un vocabolario chiuso (`muto:
"filtro_senza_banda"`), mai una frase: la frase la scrive il frontend nelle sue lingue.
Un `null` da solo non dice se e' "non calcolabile", "non ancora arrivato" o "zero".

**Gli errori hanno un codice e un corpo fisso.** 404 per cio' che non esiste, 422 per una
richiesta malformata (con il campo colpevole nel `detail`), 409 per un conflitto che e'
una domanda all'utente -- e per ciascuno un `detail` che una macchina puo' leggere. Un
errore dell'utente non si confonde con uno stato dell'app: un sito predefinito cancellato
non e' colpa di chi chiama, e non e' un 404.

**La docstring e' il contratto, e il modello di risposta e' il tipo.** Cosa accetta, cosa
torna, quando tace e perche', quali codici di errore: nella docstring. La **forma** della
risposta e' un modello Pydantic dichiarato, non un dizionario libero: da li' l'OpenAPI, e
dall'OpenAPI i **tipi TypeScript del frontend**, generati. Un campo aggiunto senza
modello non arriva a nessuno; un campo tolto rompe la compilazione di chi lo usava --
che e' esattamente quello che deve succedere.

**Una rotta che tocca SQLite e' `def`, non `async def`.** `sqlite3` e' sincrono: dentro
un `async def` blocca l'event loop di tutti mentre il worker scrive. FastAPI manda i
`def` su un thread e il resto respira.

**Ogni elenco e' paginato**, e i nomi dei campi vengono dal glossario
(`docs/domini/glossario.md`): un archivio puo' avere cinquantamila frame in una cartella, e
un campo chiamato in due modi in due rotte e' due tipi TypeScript per la stessa cosa.

**Una rotta non calcola.** Legge, mette in fila, risponde. I conti stanno nel modulo del
disegno che li possiede; una formula dentro una rotta e' la seconda casa di quella formula.

**Ogni input e' validato** (Pydantic) e ogni percorso dell'utente e' confinato: vedi
`sicurezza-web`.

```python
# NO - il frontend dovra' capire da solo cosa vuol dire None
return {"exposure_s": None}

# SI - il numero, o il perche' non c'e', con un codice; e un modello che lo dichiara
class ExposureOut(BaseModel):
    exposure_s: float | None
    silent: Literal["read_noise_unknown", "filter_without_band", ...] | None
```
