"""Lo schema OpenAPI del backend, senza far partire il server.

Uso: python tools/openapi.py [percorso.json]   senza argomento scrive su stdout

Da qui il frontend **genera** i tipi e il client: un campo che l'API non manda non deve
compilare. Serve uno strumento e non una `curl` perche' i tipi si rigenerano nel cancello e in
CI, dove nessun server e' acceso -- e un generatore che pretende un servizio vivo e' un
generatore che non gira quando serve.

Vincolo non ovvio: l'app si costruisce su un database **temporaneo**. `create_app` crea il DB se
manca e carica il catalogo, e farlo sul database vero dell'utente per stampare uno schema
vorrebbe dire toccare i suoi dati per una cosa che non li guarda nemmeno.
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from astrolog.api.app import create_app  # noqa: E402


def schema():
    """Lo schema OpenAPI come lo pubblica l'app, su un database usa e getta."""
    with tempfile.TemporaryDirectory() as tmp:
        app = create_app(Path(tmp) / "schema.db", data_root=tmp)
        return app.openapi()


def main(argv):
    testo = json.dumps(schema(), indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if argv:
        Path(argv[0]).write_text(testo, encoding="utf-8")
        print(f"schema scritto in {argv[0]}")
    else:
        sys.stdout.write(testo)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
