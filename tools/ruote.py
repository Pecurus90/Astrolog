"""Ogni dipendenza ha una ruota pronta per tutte e cinque le architetture, o e' Python puro.

Le cinque sono Windows x64, Mac Intel, Mac Apple Silicon, Linux amd64 e Linux arm64: e' cio'
che il progetto promette di far girare. Una dipendenza senza ruota per una di esse costringe
chi installa a compilarla, e su un NAS senza compilatore semplicemente non si installa.

Vincolo non ovvio: interroga PyPI, quindi **non sta nel cancello** (che deve girare offline e
in pochi secondi): sta in CI. Guarda la chiusura transitiva, non le sole dipendenze
dichiarate: una libreria Python pura che ne tira dentro una compilata avrebbe lo stesso
problema, spostato di un anello.

    python tools/ruote.py [--json]
"""

import json
import sys
import tomllib
import urllib.request
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parents[1] / "backend" / "pyproject.toml"
PYPI = "https://pypi.org/pypi/{}/{}/json"
TIMEOUT_S = 30

# Bersaglio -> i frammenti che una ruota deve avere nel nome per valere per lui. Una ruota
# `py3-none-any` (Python puro) vale per tutti e non compare qui.
TARGETS = {
    "Windows x64": ("win_amd64",),
    "Mac Intel": ("macosx", "x86_64"),
    "Mac Apple Silicon": ("macosx", "arm64"),
    "Linux amd64": ("manylinux", "x86_64"),
    "Linux arm64": ("manylinux", "aarch64"),
}
# Le musllinux valgono quanto le manylinux per l'immagine Docker Alpine, e una ruota
# `universal2` copre tutti e due i Mac in un file solo: senza questa riga una dipendenza
# sana risulterebbe scoperta su entrambi, e la CI andrebbe rossa a torto.
ALSO = {
    "Mac Intel": ("macosx", "universal2"),
    "Mac Apple Silicon": ("macosx", "universal2"),
    "Linux amd64": ("musllinux", "x86_64"),
    "Linux arm64": ("musllinux", "aarch64"),
}


def declared():
    """I nomi delle dipendenze dichiarate, senza vincolo di versione ne' commenti."""
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    out = []
    for spec in data["project"]["dependencies"]:
        name = spec.split(";")[0].strip()
        for stop in ("[", ">", "<", "=", "!", "~", " "):
            name = name.split(stop)[0]
        if name:
            out.append(name.strip())
    return out


def closure(names):
    """`{nome: versione}` delle dipendenze e di cio' che loro tirano dentro. Cio' che non e'
    installato si salta: e' un extra che nessuno ha chiesto."""
    found, frontier = {}, list(names)
    while frontier:
        name = frontier.pop()
        key = name.lower().replace("_", "-")
        if key in found:
            continue
        try:
            dist = distribution(name)
        except PackageNotFoundError:
            continue  # non installato: e' un extra che nessuno ha chiesto, non una dipendenza
        found[key] = dist.version
        for req in dist.requires or []:
            if "extra ==" in req:
                continue  # un extra non e' una dipendenza: lo installa chi lo chiede
            child = req.split(";")[0].strip()
            for stop in ("[", "(", ">", "<", "=", "!", "~", " "):
                child = child.split(stop)[0]
            if child.strip():
                frontier.append(child.strip())
    return found


def wheels(name, version):
    """I nomi dei file pubblicati su PyPI per quella versione."""
    with urllib.request.urlopen(PYPI.format(name, version), timeout=TIMEOUT_S) as r:  # noqa: S310 - solo https, host costante
        data = json.loads(r.read())
    return [f["filename"] for f in data.get("urls", []) if f.get("packagetype") == "bdist_wheel"]


def covers(files, target):
    """Il bersaglio e' coperto? Una ruota Python puro copre tutto."""
    if any(f.endswith("-none-any.whl") for f in files):
        return True
    for pieces in (TARGETS[target], ALSO.get(target)):
        if pieces and any(all(p in f for p in pieces) for f in files):
            return True
    return False


def check():
    """`{nome: {bersaglio: coperto}}` piu' l'elenco di chi manca."""
    esito, mancano = {}, []
    for name, version in sorted(closure(declared()).items()):
        try:
            files = wheels(name, version)
        except OSError as err:
            mancano.append(f"{name} {version}: PyPI non risponde ({err})")
            continue
        if not files:
            mancano.append(f"{name} {version}: nessuna ruota pubblicata, solo sorgente")
            continue
        coperti = {t: covers(files, t) for t in TARGETS}
        esito[f"{name} {version}"] = coperti
        scoperti = [t for t, ok in coperti.items() if not ok]
        if scoperti:
            mancano.append(f"{name} {version}: senza ruota per {', '.join(scoperti)}")
    return esito, mancano


def main():
    esito, mancano = check()
    if "--json" in sys.argv:
        print(json.dumps({"pacchetti": esito, "mancano": mancano}, indent=2))
    else:
        for nome, coperti in esito.items():
            segni = " ".join(("+" if ok else "-") + t for t, ok in coperti.items())
            print(f"  {'OK ' if all(coperti.values()) else 'NO '} {nome:28} {segni}")
        for riga in mancano:
            print(f"  MANCA {riga}")
    print(f"\n{len(esito)} pacchetti, {len(mancano)} senza ruota per tutte e cinque")
    return 1 if mancano else 0


if __name__ == "__main__":
    sys.exit(main())
