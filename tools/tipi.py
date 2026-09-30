"""I tipi TypeScript del frontend, generati dallo schema OpenAPI del backend.

Uso: python tools/tipi.py            riscrive `frontend/src/api/schema.d.ts`
     python tools/tipi.py --check    esce 1 se il file su disco non e' quello che uscirebbe

Perche' un controllo e non solo un generatore: generare una volta e committare il risultato
vuol dire che il giorno in cui una rotta cambia il file resta indietro, e la pagina compila
**contro una bugia** -- cioe' esattamente il difetto che generare i tipi doveva togliere. Un file
generato che diverge dal codice e' rosso al push e in CI.

Vincolo non ovvio: si genera passando dal file, non da un server acceso. Il generatore gira nel
cancello e in CI, dove nessun backend e' in piedi.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import openapi  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
OUT = FRONTEND / "src" / "api" / "schema.d.ts"
# Il generatore sta nelle dipendenze del frontend: si chiama quello installato, non uno preso
# dalla rete al volo -- la versione dei tipi non deve cambiare sotto i piedi fra due giri.
NPX = "npx.cmd" if sys.platform == "win32" else "npx"


def genera():
    """Il contenuto di `schema.d.ts` come uscirebbe adesso dallo schema del backend."""
    with tempfile.TemporaryDirectory() as tmp:
        schema = Path(tmp) / "openapi.json"
        schema.write_text(json.dumps(openapi.schema()), encoding="utf-8")
        esito = subprocess.run(
            [NPX, "--no-install", "openapi-typescript", str(schema)],
            cwd=FRONTEND,
            capture_output=True,
            text=True,
            check=False,
        )
    if esito.returncode != 0:
        sys.stderr.write(esito.stderr)
        raise SystemExit(f"il generatore dei tipi e' fallito ({esito.returncode})")
    return esito.stdout


def main(argv):
    atteso = genera()
    if "--check" in argv:
        adesso = OUT.read_text(encoding="utf-8") if OUT.is_file() else ""
        if adesso != atteso:
            print("  i tipi non corrispondono all'API: rigenera con `python tools/tipi.py`")
            return 1
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(atteso, encoding="utf-8")
    # Il percorso accorciato solo se sta davvero sotto la radice: `relative_to` esplode quando
    # non ci sta, e chi scrive altrove (un test) si trovava lo strumento rotto dal suo messaggio.
    print(f"tipi scritti in {OUT.relative_to(ROOT) if OUT.is_relative_to(ROOT) else OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
