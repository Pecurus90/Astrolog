# Contribuire

Il metodo di lavoro sta in [`CLAUDE.md`](CLAUDE.md): vale per chiunque, umano o no.

**Ambiente.** Python 3.12 e Node 20.19 o piu' recente. Una volta:
`python -m pip install -e "backend[dev]"` e `npm install` in `frontend/` (su Windows e Mac
`npm install`, non `npm ci`: il lock e' risolto per Linux, l'immagine Docker, e i binari nativi
differiscono).

**Avviare l'app**: `python tools/dev.py` avvia backend e pagina e apre il browser (`--reset`
ricrea il DB da `schema.sql`; se dentro c'e' qualcosa rifiuta, e `tools/reset_db.py
--anche-se-pieno` lo butta lasciandone una copia accanto). `python -m astrolog` funziona da qualunque cartella solo dopo
l'installazione, e serve la pagina solo dopo `npm run build`. Porta 8765, `ASTROLOG_PORT` per
cambiarla. I dati stanno fuori dal repo:
`%LOCALAPPDATA%\AstroLog` su Windows, `~/Library/Application Support/AstroLog` su Mac, `/data`
nel container (`ASTROLOG_DATA_DIR` lo sposta). Per un collaudo si usa **una copia** del
database, o uno ricreato da `schema.sql`: mai l'archivio vero.

**Controlli.** Una volta: `python -m pre_commit install`. Da li' i controlli veloci girano a ogni
commit, quelli completi (test, tipi, duplicati) a ogni push; tutti insieme, come in CI:
`python -m pre_commit run --all-files --hook-stage manual`. Il messaggio di commit e' una riga
[Conventional Commits](https://www.conventionalcommits.org/) (`fix: ...`, `feat: ...`).

**Con Claude Code** c'e' una ricetta per tipo di lavoro (`.claude/commands/`, ADR 0015); `/esegui`
sceglie quella giusta. `security-guidance` avvisa (e puo' fermare) una modifica che apre un buco di
sicurezza; `pr-review-toolkit` si usa a mano. Tutti e due li propone `.claude/settings.json`
all'apertura del progetto.

**Un modulo, un mestiere; un fatto, una casa.** Se un cambiamento tocca un file che fa gia'
due cose, il cambiamento giusto e' prima separarle.

**`old/`** e' il progetto precedente, tenuto come riferimento solo in locale: non e' in questo
repository. Da li' si porta -- coi test -- mai si importa.

**Come si chiede un lavoro** (vale per Marco e per chiunque). Si dice **cosa si vuole
vedere o ottenere**, non come farlo: il come e' il mestiere di chi esegue. **Una cosa alla
volta**: due richieste in un prompt diventano una fetta a meta'. Quando arriva una domanda
a scelta multipla, la consigliata e' in cima con il perche': si puo' scegliere altro, ma la
domanda e' li' perche' la risposta dipende da cio' che solo chi la riceve sa. E i nomi delle cose sono
quelli del [glossario](docs/domini/glossario.md).
