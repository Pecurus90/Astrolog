---
name: componente-che-formatta
description: Usa quando scrivi o modifichi un componente React, un file TSX o un foglio CSS di pagina. Dice che il componente formatta e basta (niente conti, niente stato derivato), che i tipi delle risposte si generano dall'OpenAPI, come il CSS resta a fonte unica, perche' il layout non porta logica (il mobile arriva alla fine), e la trappola del commento chiuso da una glob.
---

# Un componente formatta, e basta

**I dati arrivano fatti, e tipati.** Il componente riceve dall'API cio' che deve mostrare
e lo formatta: numeri con l'helper a fonte unica, testi con `t()`, date nel fuso del sito.
Il frontend e' **TypeScript** e i tipi delle risposte si **generano** dall'OpenAPI del
backend, mai scritti a mano: un campo che l'API non manda non compila, e una rotta che non
esiste nemmeno. Se un tipo scritto a mano sta per nascere, e' il generatore che va
rilanciato. Se
si trova a fare `Math.`, `.reduce(`, `.toFixed(`, un `.sort(` per decidere un ordine di
merito, o una soglia (`if x > 2`), quel conto va in Python e la rotta lo manda fatto
(vedi `rotta-api`). Il revisore cerca esattamente queste forme.

**Niente stato derivato.** Uno `useState` che tiene una copia trasformata dei dati e' una
seconda verita': si deriva al render da cio' che l'API ha mandato, o lo manda l'API. I
dati dell'API stanno in una cache di query (TanStack Query o equivalente): cosi' "nessuna
copia" e' una proprieta' della struttura, non una regola da ricordare.

**Presentazione si', derivazione no** -- e la differenza va detta, altrimenti la regola si
aggira alla prima tabella. **Ammesso**: ordinare una tabella per la colonna cliccata,
filtrare una lista mentre l'utente scrive, aprire/chiudere, paginare -- riordini di cio'
che l'API ha gia' mandato, senza produrre un numero nuovo. **Vietato**: una media, una
somma, un giudizio, una soglia, un "migliore" -- qualunque valore che non esisteva nella
risposta. Il revisore cerca `.sort(`/`.filter(`: se riordinano, passano; se decidono,
no.

**Il layout non porta logica.** Il mobile arriva alla fine come **veste**: se un componente
decide *cosa* mostrare in base alla larghezza, quella decisione andra' rifatta. La
larghezza decide *come* si dispone, mai *cosa* c'e'. Un controllo si sceglie per la
natura delle voci, non per lo schermo: elenco a comparsa se vengono dall'archivio,
segmentato solo per voci poche e fisse.

**La pagina nasce semplice**: struttura, testi e dati veri, senza grafica
-- nessun mock da trascrivere, nessun pack di `old/design/`.
La veste **non la mette chi costruisce la pagina**: gliela mette la fetta della veste, coi
mattoni del design system, cosi' due pagine sorelle si somigliano perche' condividono i
mattoni e non perche' sono state copiate dallo stesso mock.

**Il design system e' arrivato, e si usa cosi'.** Il foglio sta in
`frontend/src/stili/astrolog.css` -- prima i valori, poi i componenti (classi `as-*`) -- ed e'
la consegna di Claude Design **portata alla lettera**: non si toccano, e
una correzione torna alla fonte, perche' la versione dopo cancellerebbe la nostra. Si
vestono le pagine **una fetta per volta**, e una pagina nuova entra vestita solo quando la
sua fetta la veste. Le guardie che lo fanno rispettare le elenca
`controlli_veste.tutti()`, che e' anche l'unico posto dove contarle: il contrasto si **misura** sui
valori veri (axe, in jsdom, i colori non li vede), una classe `as-*` che il foglio non ha e' un
rosso, cosi' come una classe scritta fuori dal suo mattone e un avviso che non passa da
`Avviso`; e l'impronta del foglio dice se qualcuno ci ha messo le mani.

**Il CSS ha una casa sola.** I token e i mattoni sono quelli della consegna; `app.css`
porta **solo** ciò che e' nostro e che il design system non puo' conoscere (il nodo in cui
l'app vive), e non ridichiara nessun mattone. Quando si porta una pagina da `old/`, si
porta **il comportamento**, non il CSS.

**La trappola del commento.** In CSS `/* .x-* */` chiude il commento **a meta'** (`*/`
nasce dalla glob), e la regola dopo viene scartata in silenzio. Pre-commit lo prende
(`css-glob-comment`); se un selettore "non funziona" senza motivo, e' il primo posto
dove guardare -- misurando il valore calcolato, non leggendo il sorgente.

**Ogni testo passa da `t()`** e ogni pagina finita si traduce (`testi-per-pagina`). Ogni
elemento azionabile e' raggiungibile da tastiera e ha un nome: la guardia di
accessibilita' lo pretende.

```tsx
// NO - un conto e una soglia nel componente
const mean = frames.reduce((a, f) => a + f.fwhm, 0) / frames.length
{mean > 3 ? 'scarso' : 'buono'}

// SI - la rotta ha gia' deciso, il componente scrive; il tipo viene dall'OpenAPI
{t('quality.' + night.verdict)}   // verdict: "good" | "poor" | "unknown"
```
