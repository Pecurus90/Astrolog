"""La chiave di avvio: chi la riceve, chi la impone, e chi puo' leggerla sul disco.

Sta qui e non in `__main__.py` perche' li' non la guardava nessuno: quel file e' escluso dalla
copertura, con la sua ragione ("l'avvio del processo: si collauda lanciandolo, non con un test").
La ragione vale per `uvicorn.run`, non per queste tre regole -- e una decisione di sicurezza
senza una macchina e' scritta in un commento, non nel codice.

La cartella dei dati arriva da chi chiama: cosi' una prova puo' darne una vuota invece di
scrivere in quella vera dell'utente.
"""

import os
import secrets

CASA = ("127.0.0.1", "localhost")
MODO_SOLO_UTENTE = 0o600


def token_for(host, data_dir):
    """La chiave per questo avvio, o `None` se non ne serve una.

    - **Nasce solo per chi ascolta in casa.** Sul NAS (`0.0.0.0`) la rete e' fidata per scelta, e
      una chiave scritta su un disco condiviso sarebbe un segreto in piu' senza un difetto in meno.
    - **Chi avvia il processo puo' imporla** con `ASTROLOG_TOKEN`: serve a `tools/dev.py`, che
      accende backend e server di sviluppo e deve dare **la stessa** chiave a tutti e due --
      altrimenti la pagina servita da Vite ne porta una che il backend non riconosce, e ogni
      richiesta prende 401. Senza la variabile nasce qui, diversa a ogni avvio.
    - **Il file lo legge solo l'utente**: il default (0644) lo darebbe a chiunque abbia un account
      sulla macchina, e su un Mac di famiglia o su un NAS e' la differenza fra una chiave e un
      file pubblico. Su Windows i permessi POSIX non significano, e infatti la prova si salta li'.
    """
    if host not in CASA:
        return None
    token = os.environ.get("ASTROLOG_TOKEN") or secrets.token_urlsafe(32)
    fd = os.open(data_dir / "token", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, MODO_SOLO_UTENTE)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(token)
    return token
