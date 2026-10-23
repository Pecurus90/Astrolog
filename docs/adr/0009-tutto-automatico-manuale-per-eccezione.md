# 0009 -- Tutto automatico, manuale per eccezione; v1 e' un'app completa

**Stato:** accettata
Superato in parte da ADR 0033: lo scarto dei frame lo sceglie l'utente (ADR 0032); un'impostazione
nasce dove una soglia non ha una convenzione unica (ADR 0013, 0020, 0023, 0032).

## Contesto

Chi apre l'app ha gia' migliaia di frame. Un catalogo che chiede di classificarli a mano non lo
usa nessuno; uno che indovina senza dirlo mente.

## Decisione

- **L'app deduce e propone**; l'unico gesto manuale necessario e' dare un nome all'oggetto che non
  riconosce. Cio' che ne' l'header, ne' la misura, ne' l'arricchimento online sanno dare si chiede
  in *Da confermare*, per gruppo (`docs/domini/spina.md`).
- **Impostazioni minime.**
- **Nessun "accetta/scarta" dei frame in v1.**
- **v1 = app completa**: si rilascia una cosa finita, non un pezzo.

## Conseguenze

- Ogni domanda nuova all'utente deve dire cosa si guadagna rispondendo, e cadere su un gruppo di
  frame, mai su uno solo.
