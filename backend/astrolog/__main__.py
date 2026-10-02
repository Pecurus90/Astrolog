"""`python -m astrolog`. NAS: `ASTROLOG_HOST=0.0.0.0`, `ASTROLOG_HOSTS=nas.local,...`,
`ASTROLOG_SCAN_EVERY_MIN=60`; no token (docs/adr/0002-rete-di-casa-e-chiave-di-avvio.md)."""

import os

import uvicorn

from .api.app import create_app
from .db.paths import data_dir, db_path, log_dir
from .log import setup_logging
from .startup import token_for
from .weather.forecast import REFRESH_EVERY_S


def main() -> None:
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
