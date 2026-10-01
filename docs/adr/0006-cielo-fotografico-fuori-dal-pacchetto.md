# 0006 -- Il cielo fotografico (DSS2) non sta mai nel pacchetto

**Stato:** accettata

## Contesto

Il fondo fotografico della carta del cielo e' DSS2, sotto ODbL e copyright STScI: non si puo'
ridistribuire dentro un'app.

## Decisione

- Le tessere arrivano dal proxy (0005) e restano in cache.
- Un bottone **"scarica il cielo per usarlo senza rete"** prende, a scelta dell'utente, gli ordini
  fino al 5 (circa 1,1 GB, 13"/px).

## Conseguenze

- Senza rete e senza lo scaricamento il fondo e' lo strato di stelle vettoriali nostro (0005).
