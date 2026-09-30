"""Avvia il servizio: `python -m astrolog`.

Sul desktop ascolta su 127.0.0.1 con un token per avvio: la **pagina** se lo trova dentro (e'
l'app a consegnarglielo), e resta scritto in `<dati>/token` per chi chiama l'API da fuori --
uno script, una prova a mano. Sul NAS si imposta `ASTROLOG_HOST=0.0.0.0`,
`ASTROLOG_HOSTS=nas.local,192.168.1.10` (gli host con cui lo si chiama) e
`ASTROLOG_SCAN_EVERY_MIN=60`; senza token, perche' la rete di casa e' fidata.
"""

import os

import uvicorn

from .api.app import create_app
from .db.paths import data_dir, db_path, log_dir
from .log import setup_logging
from .startup import token_for
from .weather.forecast import REFRESH_EVERY_S


def main():
    setup_logging(log_dir())
    host = os.environ.get("ASTROLOG_HOST", "127.0.0.1")
    every_min = os.environ.get("ASTROLOG_SCAN_EVERY_MIN")
    hosts = [h.strip() for h in os.environ.get("ASTROLOG_HOSTS", "").split(",") if h.strip()]
    token = token_for(host, data_dir())
    app = create_app(
        db_path(),
        scan_every_s=float(every_min) * 60 if every_min else None,
        weather_every_s=REFRESH_EVERY_S,
        hosts=hosts,
        token=token,
    )
    uvicorn.run(app, host=host, port=int(os.environ.get("ASTROLOG_PORT", "8765")), log_config=None)


if __name__ == "__main__":
    main()
