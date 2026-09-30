---
name: sicurezza-web
description: Usa quando aggiungi un endpoint, chiami un processo esterno (il solver), carichi una risorsa da fuori, tocchi la configurazione del frontend, o lavori con chiavi di servizi esterni.
---

# Sicurezza in ottica web

L'app e' **distribuita** e il repo e' **pubblico**: ogni scorciatoia diventa un problema su
una macchina che non e' la nostra, con un archivio che non e' il nostro.

**Processi esterni.** ASTAP si chiama con `subprocess.run` a **lista di argomenti**, mai
`shell=True`, sempre con `timeout`, e i percorsi dell'utente non passano mai da una
stringa di shell. Le uscite del solver vanno in una cartella nostra (`-o`), **mai accanto
al file dell'utente**: i suoi FITS non si toccano, e' una promessa dell'app. Il contratto
del solver -- quali indizi passare, cosa leggere dopo, il vocabolario del "perche' non
risolto", dove sta il binario sui tre bersagli -- e' di dominio e sta in
`docs/domini/spina.md`.

**Superficie web.** CSP esplicita, niente `innerHTML` per dato dinamico, validazione lato
server su **ogni** endpoint (Pydantic sugli input). Nessuna risorsa da CDN: il frontend si
serve da se'.

**Rete.** In v1 non c'e' login: la rete di casa e' fidata (`docs/coda.md`). Ne segue che il
servizio **ascolta solo dove deve** -- `127.0.0.1` in locale, l'interfaccia del container
sul NAS, mai `0.0.0.0` su una macchina esposta -- e che nessun endpoint puo' fare danni
irreversibili senza conferma: i FITS non si toccano, e cancellare e' sempre un gesto
esplicito.

**Percorsi.** Tutto cio' che l'utente indica (cartelle, file) si risolve e si confina
dentro le radici che ha dichiarato: un `..` in una richiesta non esce mai dall'archivio.

**L'app non parla con nessuno, per costruzione.** Nessuna telemetria, nessun invio di
errori, nessuna chiamata in rete che l'utente non abbia chiesto (l'arricchimento online e
il meteo sono richieste sue). L'unica eccezione e' **il database stellare al primo
avvio**: si scarica da un indirizzo fisso, con checksum verificato prima dell'uso, e lo si
dice a schermo -- mai in silenzio, mai da un indirizzo letto da un dato. Una segnalazione la fa lui, a mano, con la pagina
Diagnostica -- il cui testo **non porta percorsi dell'utente ne' coordinate di sito**: si
copia e si incolla in pubblico.

**Una dipendenza nuova entra con tre cose scritte accanto**: il difetto che risolve (se
non lo sai nominare, non serve), la sua licenza (deve stare con la GPL-3 del progetto), e
**una ruota pronta per le cinque architetture** -- Windows x64, Mac Intel, Mac Apple
Silicon, Linux amd64, Linux arm64 -- oppure e' Python puro. Una libreria che su arm64 si
compila dal sorgente (e' successo con `photutils` in `old/`) non entra finche' la CI non
l'ha vista installarsi su tutte e cinque. Le versioni sono fissate; le vulnerabilita' le
cerca la CI.

**Segreti.** Chiavi e credenziali vivono in `.env`, si leggono con `os.environ`; gitleaks,
in pre-commit, blocca le righe che ci assomigliano. **Una chiave gia' committata non basta
spostarla: va revocata.** Git la conserva, e il repo e' pubblico.
