"""Il log strutturato: una riga JSON per evento, file ruotato accanto al DB; ogni passata
di scansione porta il suo `scan_run_id`, lo stesso della ricevuta. E' la fonte della
Diagnostica.

Vincolo non ovvio: ogni modulo logga col logger del suo nome (`logging.getLogger(__name__)`),
mai `print`. Le chiavi extra passate con `extra={...}` finiscono nel JSON tali e quali.
"""

import json
import logging
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler

_STANDARD = set(logging.LogRecord("x", 0, "", 0, "", (), None).__dict__) | {"message", "asctime"}


class JsonLines(logging.Formatter):
    """Un evento per riga: istante UTC, livello, logger, messaggio, e le chiavi extra."""

    def format(self, record):
        row = {
            "t": datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for k, v in record.__dict__.items():
            if k not in _STANDARD and not k.startswith("_"):
                row[k] = v
        if record.exc_info:
            row["exc"] = self.formatException(record.exc_info)
        return json.dumps(row, ensure_ascii=False, default=str)


def setup_logging(log_dir, *, level=logging.INFO):
    """Attacca al logger radice il file ruotato in `log_dir` (5 MB x 3) in formato JSON."""
    root = logging.getLogger()
    root.setLevel(level)
    for h in list(root.handlers):
        if getattr(h, "_astrolog", False):
            root.removeHandler(h)
    handler = RotatingFileHandler(
        str(log_dir / "astrolog.log"), maxBytes=5_000_000, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(JsonLines())
    handler._astrolog = True  # type: ignore[attr-defined]
    root.addHandler(handler)
    return handler
