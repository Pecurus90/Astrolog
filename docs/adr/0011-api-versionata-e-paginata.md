# 0011 -- L'API e' versionata, e pagina ogni elenco che cresce con l'archivio

**Stato:** accettata

## Contesto

Il frontend, e in futuro altri client, parlano col backend solo dall'API. Un archivio puo' avere
cinquantamila frame in una cartella.

## Decisione

- **L'API e' versionata** (`/api/v1`): un cambiamento che rompe un client e' un `v2`.
- **Ogni rotta che restituisce un elenco che cresce con l'archivio pagina.**
- Non paginano, e lo dicono nella loro docstring, gli elenchi che non crescono con l'archivio:
  l'attrezzatura (`/gear`), il vocabolario dei filtri (`/vocab/filter-models`), le sottocartelle di
  una sola cartella (`/folders/browse`), i siti proposti da una ricerca (`/places`, col tetto di
  `place.search`) e Da confermare (`/review`), che manda cio' che e' da guardare: cresce con cio'
  che e' nuovo, mentre gli oggetti gia' visti si leggono a pagine (`/review/objects/settled`).

## Conseguenze

- La skill `rotta-api` porta la regola a chi scrive una rotta.
