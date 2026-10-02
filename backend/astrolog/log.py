"""Structured log, one JSON line per event in a rotated file beside the database: the source of
Diagnostics. The keys passed with `extra={...}` land in the JSON as they are."""

import json
import logging
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

_STANDARD = set(logging.LogRecord("x", 0, "", 0, "", (), None).__dict__) | {"message", "asctime"}


class JsonLines(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
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


def setup_logging(log_dir: Path, *, level: int = logging.INFO) -> RotatingFileHandler:
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
