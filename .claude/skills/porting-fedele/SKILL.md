---
name: porting-fedele
description: Usa quando porti un modulo, un vocabolario o una pagina da old/ nella radice, o quando rifai qualcosa partendo da un esistente. Impone di riprodurre il comportamento coi suoi test prima, e di correggere dopo in un passo separato.
---

# Porting fedele: prima la fedelta', poi il miglioramento

**Cosa.** Portare un modulo da `old/` preserva il comportamento **coperto dai test** --
quirk inclusi -- e porta i test insieme al codice. Le correzioni arrivano **dopo**, ognuna
in un passo separato col proprio test.

**Perche'.** Un porting che migliora mentre traduce produce due cambiamenti sovrapposti: se
qualcosa si rompe, non si sa quale dei due e' stato. E i test di `old/` sono i **casi
limite imparati** -- gli header strani visti davvero -- che una riscrittura a memoria
perderebbe.

**Le tre regole della cava**

1. **Si porta, non si importa.** Nessun file della radice importa da `old/`. Il modulo si
   copia, si adatta al disegno (identificatori e commenti in **inglese**, commenti di
   al massimo due righe, il suo posto nei contratti di import-linter), e da quel momento vive qui. Il vecchio aveva nomi
   misti: si rinominano nel porting, coi test che seguono.
2. **Coi suoi test.** Il banco del modulo portato e' una replica di quello originale: gli
   stessi casi, gli stessi attesi. Se in `old/` i test non c'erano, si scrivono prima del
   porting, sul codice vecchio, e devono passare li' prima che qui.
3. **Solo cio' che il disegno chiede.** Non si porta un modulo intero se serve una funzione:
   si porta la funzione, col suo test, e il resto resta nella cava.

**Tre trappole del porting, viste davvero**

- **Uguaglianza esatta, non somiglianza.** Quando si confronta l'uscita del vecchio con
  quella del nuovo, l'asticella e' l'uguaglianza dell'artefatto (lo stesso JSON, la stessa
  riga), non "assomiglia". Un porting che somiglia non e' un porting.
- **Due difetti che si annullano.** Un quirk del vecchio puo' compensare un altro quirk:
  corretto uno solo, il risultato **peggiora**. Prima di correggere, si cerca chi dipende
  dal comportamento storto.
- **Regex su corpus non letto.** Una rinomina di massa o una regola nuova sui nomi si
  prova sul corpus intero (la regola del corpus sta in `per-altri-utenti`), non su tre
  esempi in testa: si guarda cosa prende, e cosa prende **che non doveva**.

**Cosa NON si porta mai**: le migrazioni, i backfill, le precedenze fra derivato e misurato
sui frame reali, le code di revisione dell'incertezza. I contratti dei moduli non hanno un
posto per loro, e non e' una svista.

**Quando la fonte e' una pagina di `old/src`**, il criterio e' *"ogni scostamento e'
voluto"*: il CSS **non si porta** (Marco, 13/9/2026 -- le pagine nascono semplici e la veste
arriva alla fine), il comportamento si riscrive in **TypeScript**
sui dati che ora arrivano gia' fatti e tipati dall'API. Un conto che la pagina vecchia
faceva in JavaScript **non si porta**: si sposta in Python, e la pagina riceve il
risultato.
