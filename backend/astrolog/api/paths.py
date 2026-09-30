"""Il percorso di una cartella FITS come lo accetta l'app: assoluto, fuori dalle zone di sistema
o dentro la radice confinata, e salvato nella forma che l'utente ritrova.

Vincolo non ovvio: i controlli guardano il percorso RISOLTO (`realpath` risolve i symlink PRIMA
del confinamento, cosi' un link che punta fuori dalla radice non la aggira), e le forme che li
scavalcherebbero -- percorsi di dispositivo, nomi che Windows non ammette, condivisioni
amministrative, cio' che risolto non e' assoluto -- non entrano. Le zone di sistema, in piu', si
guardano **anche com'e' scritto**: su Mac `/etc` e `/var` portano a `/private/...`, e dal solo
risolto sembravano cartelle qualunque.
"""

import os
import re

from fastapi import HTTPException

BLOCKLIST_POSIX = ("/", "/etc", "/sys", "/proc", "/dev", "/var", "/boot", "/root")

# Le forme di Windows che arrivano a un disco scavalcando i controlli. I percorsi di dispositivo
# `\\?\` e `\\.\` (Microsoft, *File path formats on Windows systems*): il primo salta anche la
# normalizzazione, e `realpath` non lo toglie. I caratteri che un nome di file o cartella non puo'
# contenere (Microsoft, *Naming Files, Paths, and Namespaces*): un percorso con `?` non e' una
# cartella, e' un nome dello spazio del sistema (`\??\C:\Windows`, `\GLOBAL??\...`). Le
# condivisioni nascoste che Windows crea da solo (Microsoft, *Remove administrative shares*): una
# per disco (`C$`, `D$`), `ADMIN$`, `IPC$`, `PRINT$` per le stampanti, `FAX$`.
# `\\localhost\C$\Windows` e' `C:\Windows`, e da fuori non si sa se `\\nome` e' questa macchina:
# si rifiutano su ogni PC (Marco, 2026-09-11). Le grafie con punto o spazio finale (`C$.`, `C$ `)
# non arrivano al disco: Windows 11 risponde "nome di rete non valido" (errore 67, misurato).
DEVICE_PATH_RE = re.compile(r"^[\\/]{2}[?.][\\/]")
RESERVED_NT_RE = re.compile(r'[<>"|?*]')
ADMIN_SHARE_RE = re.compile(
    r"^[\\/]{2}[^\\/]+[\\/](?:[a-z]|admin|ipc|print|fax)\$(?:[\\/]|$)", re.IGNORECASE | re.ASCII
)


def blocklist_nt():
    env = os.environ
    drive = env.get("SystemDrive", "C:") + "\\"
    return tuple(
        p
        for p in (
            drive,
            env.get("SystemRoot", drive + "Windows"),
            env.get("ProgramFiles", drive + "Program Files"),
            env.get("ProgramFiles(x86)", drive + "Program Files (x86)"),
            env.get("ProgramData", drive + "ProgramData"),
        )
        if p
    )


def same_folder(a, b):
    """Due percorsi sono la stessa cartella, per come il sistema confronta i nomi."""
    return os.path.normcase(a) == os.path.normcase(b)


def is_under(child, parent):
    """`child` sta sotto `parent` (entrambi risolti)? Case-insensitive dove serve."""
    # La radice di un disco (`C:\`) blocca solo se stessa, non tutto cio' che contiene.
    return same_folder(child, parent) or os.path.normcase(child).startswith(
        os.path.normcase(parent) + os.sep
    )


def is_blocked_system_path(path):
    blocklist = blocklist_nt() if os.name == "nt" else BLOCKLIST_POSIX
    return any(is_under(path, bad) for bad in blocklist)


def stored_form(written, resolved, rules=os.path):
    """La forma da salvare: quella risolta -- due grafie della stessa cartella sono una riga
    sola --, salvo quando la risoluzione cambia disco o condivisione. E' il disco di rete
    collegato a una lettera, che Python dalla 3.8 risolve nella sua condivisione (bpo-37993):
    l'utente ha scelto `Z:` e deve ritrovare `Z:`. Allora si tiene la lettera, maiuscola, e dei
    nomi di cartella la grafia che dice il sistema dove coincidono: `Z:\\foto` e `z:\\FOTO\\`
    restano una riga. Un collegamento verso un altro disco, invece, resta com'e' scritto."""
    drive, tail = rules.splitdrive(written)
    resolved_drive, resolved_tail = rules.splitdrive(resolved)
    if rules.normcase(drive) == rules.normcase(resolved_drive):
        return resolved
    names = [n for n in re.split(r"[\\/]", tail) if n]
    known = [n for n in re.split(r"[\\/]", resolved_tail) if n]
    for i in range(1, min(len(names), len(known)) + 1):
        if names[-i].casefold() == known[-i].casefold():
            names[-i] = known[-i]
    return rules.join(drive[:1].upper() + drive[1:] + rules.sep, *names)


def _refuse(code, path, **more):
    raise HTTPException(status_code=422, detail={"code": code, "path": path, **more})


def validate_root(raw, data_root):  # noqa: C901
    """Il percorso da salvare, o HTTPException 422 col motivo (in codice). Le cartelle di rete
    (`\\\\server\\cartella`) si accettano: perche', e il loro rischio, li dice il contratto."""
    if not raw or not os.path.isabs(raw):
        _refuse("path_not_absolute", raw)
    if "\x00" in raw:  # il carattere nullo non sta in nessun nome, su nessun sistema
        _refuse("path_invalid", raw)
    written = os.path.abspath(raw)
    if DEVICE_PATH_RE.match(raw) or DEVICE_PATH_RE.match(written):
        _refuse("path_device", raw)  # anche `C:\cartella\NUL`, che abspath fa diventare `\\.\NUL`
    if os.name == "nt" and RESERVED_NT_RE.search(raw):
        _refuse("path_invalid", raw)
    try:
        canonical = os.path.realpath(written)
    except OSError:
        # la cartella non risponde (NAS spento, credenziali rifiutate): si controlla com'e'
        # scritta, e la registrazione l'accetta come accetta un disco staccato
        canonical = written
    if not os.path.isabs(canonical):
        _refuse("path_not_absolute", canonical)
    if ADMIN_SHARE_RE.match(canonical):
        _refuse("path_admin_share", canonical)
    if data_root is not None:
        if not is_under(canonical, data_root):
            _refuse("path_outside_data_root", canonical, data_root=data_root)
    elif is_blocked_system_path(canonical):
        _refuse("path_is_system", canonical)
    elif is_blocked_system_path(written):
        # Anche com'e' scritto, non solo dove porta: su Mac `/etc` e `/var` sono collegamenti a
        # `/private/etc` e `/private/var`, e risolti uscivano dalle zone di sistema.
        _refuse("path_is_system", written)
    return stored_form(written, canonical)
