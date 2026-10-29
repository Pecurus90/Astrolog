# 0041 -- Il tetto di saturazione e' il fondo scala dichiarato

**Stato:** accettata, 29/10/2026 (Marco); supera ADR 0022 punto 7 nella parte "il tetto dall'istogramma". Passo 26.45.
**Supera** in `docs/domini/misure.md`: "Il tetto e' il valore piu' basso"; "Il tetto e' per frame"

## Contesto

Il passo 25.2 cercava il tetto come pila di pixel uguali in cima all'istogramma, per vedere le
camere che tagliano sotto il fondo scala (Canon 700D a 61208). La pila si riconosceva con 5
soglie tarate sulle 24 copie dell'archivio di Marco. Il passo 26.45 chiede una convenzione
pubblica per ogni misura. Il criterio di Chauvenet su conteggi di Poisson e' stato provato e non
regge: i picchi delle stelle fanno grumi piu' dispersi di una Poisson (60 stelle uguali: pila
falsa, tutte sature). PixInsight documenta la sua convenzione (ImageWeighting par. 3.1.1): una <!-- software-ok -->
stella con un pixel o piu' sopra la soglia di saturazione e' satura, soglia di default 1,0 del
fondo scala.

## Decisione

- Il tetto e' il fondo scala dichiarato: `DATAMAX`, altrimenti il massimo del tipo di dato dopo
  `BZERO` e `BSCALE`. Nessuna ricerca nell'istogramma; `pipeline/ceiling.py` sparisce.
- Satura e' una stella del conteggio con almeno un pixel del sensore al tetto.

## Conseguenze

- Niente soglie tarate per il tetto. Una camera che taglia sotto il fondo scala non ha stelle
  sature e le sue stelle tagliate entrano nell'HFD se stanno sotto il 90% del fondo scala: lo
  stesso fa PixInsight. Costo scelto da Marco (29/10/2026). <!-- software-ok -->
- A schermo: il tetto di un frame Canon passa da 61208 a 65535 e le sue sature a zero; sugli
  altri frame le sature possono salire un poco (un pixel basta, prima due).
