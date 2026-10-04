"""Il percorso di una cartella come l'app lo accetta e lo salva. Le regole e il loro perche'
stanno in `api/paths.py` e nel contratto `docs/domini/spina.md`.

La tabella della forma salvata e i controlli sul percorso risolto girano su qualunque sistema.
Le forme che esistono solo su Windows si provano la', dove la CI le fa girare.
"""

import ntpath
import os
import posixpath

import pytest
from fastapi import HTTPException

from astrolog.api import paths
from astrolog.api.paths import stored_form, validate_root

# (nome, regole dei percorsi, scritto, risolto da realpath, salvato)
FORME = [
    ("disco di rete collegato a una lettera", ntpath, "Z:\\Foto", "\\\\nas\\foto\\Foto",
     "Z:\\Foto"),
    ("lo stesso, scritto in un altro modo", ntpath, "z:\\FOTO\\", "\\\\nas\\foto\\Foto",
     "Z:\\Foto"),
    ("una lettera collegata a una sottocartella", ntpath, "Z:\\M31",
     "\\\\nas\\foto\\Notti\\M31", "Z:\\M31"),
    ("nome corto su una lettera collegata: un'altra riga, dichiarata", ntpath, "Z:\\ARCHIV~1",
     "\\\\nas\\foto\\ArchivioNomiLunghi", "Z:\\ARCHIV~1"),
    ("cartella di rete scritta a mano", ntpath, "\\\\NAS\\Foto\\M31", "\\\\NAS\\Foto\\M31",
     "\\\\NAS\\Foto\\M31"),
    ("disco locale, maiuscole del sistema", ntpath, "D:\\astro", "D:\\Astro", "D:\\Astro"),
    ("collegamento verso un altro disco", ntpath, "C:\\archivio", "D:\\Astro\\Foto",
     "C:\\archivio"),
    ("collegamento su Linux o nel container", posixpath, "/library/foto", "/volume1/foto",
     "/volume1/foto"),
]  # fmt: skip


@pytest.mark.parametrize(
    "regole, scritto, risolto, salvato", [c[1:] for c in FORME], ids=[c[0] for c in FORME]
)
def test_the_folder_is_saved_in_the_form_the_user_finds_again(regole, scritto, risolto, salvato):
    assert stored_form(scritto, risolto, regole) == salvato


def _codice(scritto, data_root=None):
    with pytest.raises(HTTPException) as rifiuto:
        validate_root(scritto, data_root)
    return rifiuto.value.detail["code"]


ZONA_DI_SISTEMA = os.environ.get("SYSTEMROOT", "C:\\Windows") if os.name == "nt" else "/etc"


def _non_risponde(_percorso):
    raise OSError(1326, "credenziali rifiutate (mock)")


def test_a_system_zone_that_leads_elsewhere_is_refused_too(monkeypatch, tmp_path):
    """Una zona di sistema si rifiuta anche quando **porta altrove**. Su Mac `/etc` e `/var` sono
    collegamenti a `/private/etc` e `/private/var`: guardando solo dove portano, uscivano dalle zone
    di sistema e l'app li accettava come cartelle di foto. Vista in CI, su macOS: 201 invece di 422.
    Qui il collegamento si simula, cosi' la regola si prova su ogni sistema e non solo su un Mac."""
    altrove = str(tmp_path / "private" / "etc")
    monkeypatch.setattr(
        paths.os.path, "realpath", lambda p: altrove if paths.same_folder(p, ZONA_DI_SISTEMA) else p
    )
    assert _codice(ZONA_DI_SISTEMA) == "path_is_system"


def test_the_checks_look_at_where_the_path_leads(monkeypatch, tmp_path):
    """Un percorso innocuo che porta a una zona di sistema si rifiuta, e uno che porta fuori
    dalla radice dei dati anche: i controlli guardano dove porta, non come e' scritto."""
    innocuo = str(tmp_path / "archivio")
    monkeypatch.setattr(paths.os.path, "realpath", lambda p: ZONA_DI_SISTEMA)
    assert _codice(innocuo) == "path_is_system"
    assert _codice(innocuo, str(tmp_path)) == "path_outside_data_root"


def test_a_path_that_resolves_to_no_absolute_path_is_refused(monkeypatch, tmp_path):
    """Un percorso che risolto non e' assoluto (`C:Windows`, relativo al disco) sfuggirebbe al
    controllo delle zone di sistema: si rifiuta. E' una guardia di riserva: le forme note che ci
    arrivano si fermano prima, ai caratteri che Windows non ammette."""
    monkeypatch.setattr(paths.os.path, "realpath", lambda p: "Windows")
    assert _codice(str(tmp_path / "archivio")) == "path_not_absolute"


def test_a_folder_that_does_not_answer_is_checked_and_kept_as_written(monkeypatch, tmp_path):
    """Un NAS spento, o che rifiuta le credenziali, non si lascia risolvere: la registrazione non
    va in errore e controlla il percorso com'e' scritto -- un percorso innocuo entra, una zona
    di sistema resta fuori anche se non si risolve."""
    monkeypatch.setattr(paths.os.path, "realpath", _non_risponde)
    nas = str(tmp_path / "nas" / "foto")
    assert validate_root(nas, None) == os.path.abspath(nas)
    assert _codice(ZONA_DI_SISTEMA) == "path_is_system"


def test_a_null_character_is_refused(tmp_path):
    """Il carattere nullo non sta nel nome di nessun file, su nessun sistema: 422, non un 500."""
    assert _codice(str(tmp_path) + "\x00archivio") == "path_invalid"


windows = pytest.mark.skipif(
    os.name != "nt", reason="queste forme esistono solo su Windows: la CI le prova li'"
)


@windows
@pytest.mark.parametrize(
    "scritto, codice",
    [
        ("\\\\?\\C:\\Windows", "path_device"),
        ("\\\\.\\C:\\Windows", "path_device"),
        ("C:\\Astro\\NUL", "path_device"),
        ("\\??\\C:\\Windows", "path_invalid"),
        ("\\GLOBAL??\\C:\\Windows", "path_invalid"),
        ("\\??\\Volume{7f7c0000-0000-0000-0000-000000000000}\\Windows", "path_invalid"),
        ("\\\\localhost\\C$\\Windows", "path_admin_share"),
        ("\\\\127.0.0.1\\d$", "path_admin_share"),
        ("\\\\PC-STUDIO\\D$\\Astro", "path_admin_share"),
        ("\\\\nas\\ADMIN$\\System32", "path_admin_share"),
        ("\\\\localhost\\IPC$", "path_admin_share"),
        ("\\\\localhost\\print$", "path_admin_share"),
        ("\\\\localhost\\FAX$", "path_admin_share"),
    ],
    ids=["dispositivo, senza normalizzazione", "dispositivo", "nome di dispositivo",
         "spazio dei nomi del sistema", "spazio globale", "volume per identificativo",
         "condivisione di un disco", "condivisione di un altro disco", "disco di un altro PC",
         "condivisione di Windows", "condivisione dei processi", "condivisione delle stampanti",
         "condivisione dei fax"],
)  # fmt: skip
def test_the_forms_that_would_bypass_the_checks_are_refused(monkeypatch, scritto, codice):
    """Aprire le cartelle di rete non apre le zone di sistema: `\\\\?\\C:\\Windows`,
    `\\??\\C:\\Windows` e `\\\\localhost\\C$\\Windows` sono `C:\\Windows` scritto in altri modi."""
    monkeypatch.setattr(paths.os.path, "realpath", lambda p: p)  # niente rete vera
    assert _codice(scritto) == codice


@windows
def test_a_system_share_is_refused_where_the_path_leads(monkeypatch):
    """Il controllo delle condivisioni guarda dove il percorso porta: un disco collegato a
    `\\\\localhost\\C$` resta fuori, e anche una condivisione che non si lascia risolvere."""
    monkeypatch.setattr(
        paths.os.path,
        "realpath",
        lambda p: "\\\\localhost\\C$\\Windows" if p.casefold().startswith("z:") else p,
    )
    assert _codice("Z:\\Windows") == "path_admin_share"
    monkeypatch.setattr(paths.os.path, "realpath", _non_risponde)
    assert _codice("\\\\localhost.\\C$\\Windows") == "path_admin_share"


@windows
@pytest.mark.parametrize(
    "scritto",
    ["\\\\localhost\\C$.\\Windows", "\\\\localhost\\C$ \\Windows"],
    ids=["punto", "spazio"],
)
def test_a_share_name_with_a_trailing_dot_or_space_passes(monkeypatch, scritto):
    """`C$.` e `C$ ` non si rifiutano: Windows non porta al disco attraverso di loro
    ("nome di rete non valido"), quindi non scavalcano la guardia."""
    monkeypatch.setattr(paths.os.path, "realpath", lambda p: p)  # niente rete vera
    assert validate_root(scritto, None) == scritto


@windows
def test_a_mapped_drive_is_one_row_however_it_is_written(monkeypatch):
    """Le grafie della stessa cartella su un disco collegato danno la stessa forma, quindi la
    stessa riga; e un percorso senza lettera prende quella del disco corrente."""
    monkeypatch.setattr(
        paths.os.path,
        "realpath",
        lambda p: "\\\\nas\\foto\\Foto" if p.casefold().startswith("z:") else p,
    )
    assert validate_root("Z:\\Foto", None) == validate_root("z:\\FOTO\\", None) == "Z:\\Foto"
    assert ntpath.splitdrive(validate_root("\\Astro", None))[0] != ""
