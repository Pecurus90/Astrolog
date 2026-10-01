# 0002 -- Nessun login: la rete di casa e' fidata, e ogni avvio ha la sua chiave

**Stato:** accettata, 13/9/2026

## Contesto

L'app gira sul desktop di chi la usa o su un NAS di casa, da aprire anche da tablet e telefono.
Un login chiede account, password da ricordare e un posto dove tenerle, per un'app che ha un
utente solo. Sul desktop pero' la porta del backend e' raggiungibile da ogni programma della
macchina.

## Decisione

- **Nessun login in v1.** Sul NAS l'app ascolta solo in rete locale, mai su Internet, e la guida
  lo dice chiaro; risponde solo agli host ammessi (`ASTROLOG_HOSTS`). Un login vero, se servira',
  arriva dopo senza rifare nulla.
- **Sul desktop il backend ascolta solo su `127.0.0.1`, con una chiave per avvio** che la finestra
  dell'app conosce e le altre applicazioni della macchina no. La chiave e' obbligatoria su ogni
  rotta dell'API (`X-AstroLog-Token`); la pagina, i suoi file e la documentazione si servono senza.
  Sul NAS non c'e' chiave.
- **L'app si apre e basta**: e' il backend a servire la pagina, e le consegna la chiave mentre
  gliela manda. La chiave non finisce in un link, in una cronologia o in un messaggio. In sviluppo
  la pagina la serve Vite: la chiave la decide `tools/dev.py` e la passa ai due processi con
  `ASTROLOG_TOKEN`.

## Conseguenze

- Nessun endpoint puo' fare danni fuori dall'archivio dell'app: la skill `sicurezza-web` ne trae
  le regole (dove si ascolta, cosa si confina).
- Il contratto della spina dice la guardia che resta senza login (`docs/domini/spina.md`, *Il NAS
  senza login non e' senza guardia*).
