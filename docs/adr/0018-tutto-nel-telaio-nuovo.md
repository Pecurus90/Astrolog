# 0018 -- Si passa tutto al telaio e al foglio v26, senza convivenza

**Stato:** accettata, 7/10/2026

## Contesto

Claude Design consegna il foglio v26 (`astrolog.css`), il telaio (binario, barra in alto,
pastiglia di Stanotte, barra del telefono), la Dashboard e il Meteo. L'app gira sul foglio v10.
Delle 260 classi che l'app usa, 205 non sono nel v26 (misurato il 7/10/2026): cambiare foglio
toglie l'aspetto a quasi tutte le pagine che il disegno non ha ancora rifatto.

## Decisione

- **Un foglio solo, il v26, e un telaio solo, quello nuovo, per tutta l'app** (Marco, 7/10/2026:
  *"delle vecchie non mi interessa nulla quindi tutto nuovo"*). Niente due gusci, niente foglio
  vecchio tenuto accanto: due fogli con le stesse classi sono due verita'.
- Le pagine che il disegno non ha rifatto restano **funzionanti ma spoglie** finche' non tocca a
  loro; non si rivestono a mano nel frattempo (ADR 0012: il disegno viene da Claude Design).
- **Il Meteo e' la prima pagina rifatta**: il suo disegno e' chiuso, coi suoi stati. La Dashboard
  aspetta i progetti e le domande aperte di `docs/per-claude-code.md` del progetto di disegno.
- **Il carattere Atkinson Hyperlegible (Next e Mono) si include nell'app**, file woff2 con
  licenza SIL OFL, mai scaricato da una rete esterna.

## Conseguenze

- Le prove del frontend che guardano classi del v10 cambiano insieme alla pagina che passa.
- La guida utente descrive le pagine come sono: quelle spoglie si dicono tali solo se cambia cosa
  si puo' fare, non l'aspetto.
