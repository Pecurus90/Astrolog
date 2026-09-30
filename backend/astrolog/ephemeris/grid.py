"""La griglia del tempo e l'attraversamento di una soglia. **Niente astronomia qui.**

Si campiona una finestra a passo fisso e si cerca dove una curva di altezza passa sopra o sotto
un valore: e' il mestiere che serve a sorgere, tramontare e crepuscoli, ed e' lo stesso per il
Sole e per la Luna. Sta in un file suo perche' non sa cosa sta guardando, e questo lo rende
provabile senza cielo.

Vincoli non ovvi:

* **L'istante si interpola fra i due campioni**, non si prende quello piu' vicino: arrotondare al
  campione sbaglierebbe fino a meta' passo, che a schermo e' un altro orario. Cosi' il passo
  decide quanto e' fitta la ricerca, non quanto e' preciso il risultato.
* **Nessun attraversamento e' `None`, non il primo campione.** Sopra il circolo polare la Luna
  puo' non incontrare mai l'orizzonte: e' un fatto, e un orario inventato li' non si
  distinguerebbe da uno vero.
* **La griglia si costruisce in UTC**, e questo non e' un dettaglio. Sommare un `timedelta` a un
  istante con un fuso vero fa aritmetica **da orologio da parete**: la notte del cambio d'ora
  primaverile "24 ore" diventano 23, e in autunno 25. Misurato a Roma: in primavera la griglia
  **torna indietro di 57 minuti**, e quel salto all'indietro crea un attraversamento che non
  esiste. A Vicenza, sui vent'anni 2020-2039, i due cambi d'ora sbagliavano **quattro orari su
  ottanta**: fino a un'ora di scarto, e in un caso un tramonto **inventato** dove non ce n'era.
  Allargando la finestra si trova di peggio -- nel 2008 lo scarto arriva a **quasi nove ore**. E
  l'orario che usciva era comunque un'ora che sull'orologio quella notte non era mai esistita.
"""

import datetime as dt


def night_grid(inizio, hours, step_min):
    """Gli istanti da `inizio` per `hours` ore **vere**, ogni `step_min` minuti, estremi inclusi.

    L'ultimo campione c'e' davvero: una griglia che si ferma un passo prima perde
    l'attraversamento che cade in coda, e il tramonto sparisce senza che niente cada.

    Gli istanti tornano **in UTC**: e' li' che un'ora dura un'ora. Chi li mostra li riporta nel
    fuso del sito, dove l'ora legale e' un fatto della lettura e non del conto.

    Nessuno dei due numeri ha un valore di partenza: il passo vive in `GRID_STEP_MIN` e la durata
    la decide chi conosce la notte. Scritto qui un valore di riserva, il giorno che quello vero
    cambia questo mentirebbe in silenzio."""
    if inizio.tzinfo is None:
        raise ValueError("una griglia senza fuso non si sa dove comincia")
    base = inizio.astimezone(dt.UTC)
    quanti = round(hours * 60 / step_min)
    passo = dt.timedelta(minutes=step_min)
    return [base + passo * i for i in range(quanti + 1)]


def first_crossing(istanti, altezze, soglia, verso):
    """Il primo istante in cui `altezze` attraversa `soglia`, o `None`.

    `verso` e' `"up"` (da sotto a sopra: sorge) o `"down"` (da sopra a sotto: tramonta).
    L'istante si interpola linearmente fra i due campioni che lo racchiudono."""
    scarti = [a - soglia for a in altezze]
    for i in range(len(scarti) - 1):
        prima, dopo = scarti[i], scarti[i + 1]
        attraversa = prima > 0 >= dopo if verso == "down" else prima < 0 <= dopo
        if not attraversa:
            continue
        # `prima / (prima - dopo)` e' la frazione di intervallo a cui lo scarto si annulla: il
        # denominatore non puo' essere zero, perche' i due scarti hanno segno diverso.
        quota = prima / (prima - dopo)
        return istanti[i] + (istanti[i + 1] - istanti[i]) * quota
    return None
