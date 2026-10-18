# 0006 -- Il cielo fotografico (DSS2) non sta mai nel pacchetto

**Stato:** accettata

## Contesto

Il fondo fotografico della carta del cielo e' DSS2, sotto ODbL e copyright STScI: non si puo'
ridistribuire dentro un'app.

## Decisione

- Le tessere arrivano dal proxy (0005) e restano in cache, solo dove l'utente ha gia' guardato.
- Nessuno scaricamento del cielo per l'uso senza rete (Marco, 18/10/2026: sono giga e tera di
  dati; vale anche per le altre mappe di 0023).

## Conseguenze

- Senza rete, dove la cache non arriva, il fondo e' lo strato di stelle vettoriali nostro (0005).
