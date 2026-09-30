"""Un comando per tutto, in Python e non in shell (uno per tre sistemi).

Uso: python tools/dev.py              avvia tutto e apre l'app nel browser
     python tools/dev.py --reset      prima ricrea il DB da schema.sql, se e' vuoto
     python tools/dev.py --no-open    non aprire il browser
Variabili: ASTROLOG_DATA_DIR (dove stanno DB, cache e log), ASTROLOG_PORT.

L'app si apre e basta: la chiave di avvio la consegna il backend alla pagina che serve, e
nessuno la incolla da nessuna parte.
"""

import os
import secrets
import subprocess
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"


def main(argv):
    port = os.environ.get("ASTROLOG_PORT", "8765")
    # un DB pieno si rifiuta, e il perche' l'ha gia' detto `reset_db`: qui ci si ferma e basta
    reset = [sys.executable, str(ROOT / "tools" / "reset_db.py")]
    if "--reset" in argv and subprocess.run(reset).returncode:
        return 1
    # La chiave la decide QUESTO comando e la da' a tutti e due: il backend la usa invece di
    # inventarsene una, e il server di sviluppo la mette nella pagina come farebbe il backend.
    # Senza, la pagina servita da Vite non ne porta nessuna e ogni chiamata all'API prende 401.
    ambiente = {**os.environ, "ASTROLOG_TOKEN": secrets.token_urlsafe(32)}
    procs = [subprocess.Popen([sys.executable, "-m", "astrolog"], cwd=str(BACKEND), env=ambiente)]
    if (FRONTEND / "package.json").exists():
        procs.append(
            subprocess.Popen(
                ["npm", "run", "dev"], cwd=str(FRONTEND), shell=os.name == "nt", env=ambiente
            )
        )
    if "--no-open" not in argv:
        # Finche' la pagina non e' costruita, aprirla vorrebbe dire atterrare su un errore in
        # JSON: si apre la documentazione, che intanto e' la cosa utile da guardare. Dove stia
        # la pagina lo dice **il codice che la serve**, non una copia di quel percorso: scritto
        # due volte, il giorno che si sposta questo comando aprirebbe `/docs` per sempre, in
        # silenzio. L'import sta qui dentro perche' serve solo a questa riga.
        sys.path.insert(0, str(BACKEND))
        from astrolog.api.page import WEB_DIR

        costruita = (WEB_DIR / "index.html").is_file()
        webbrowser.open(f"http://127.0.0.1:{port}/" + ("" if costruita else "docs"))
    sys.stdout.write(
        f"AstroLog su http://127.0.0.1:{port} (OpenAPI: /docs). Ctrl+C per fermare.\n"
        "La pagina riceve la chiave da sola; per chiamare l'API da fuori, l'header"
        " X-AstroLog-Token vale quanto il file 'token' della cartella dei dati.\n"
    )
    try:
        procs[0].wait()
    except KeyboardInterrupt:
        pass  # Ctrl+C e' il modo normale di fermare: non e' un errore
    finally:
        for p in procs:
            p.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
