"""La chiave di avvio: chi la riceve, chi la impone, e chi puo' leggerla sul disco.

Sta fuori da `__main__.py` perche' li' non la guardava nessuno: quel file e' escluso dalla
copertura con la sua ragione scritta ("l'avvio del processo: si collauda lanciandolo, non con un
test"), e la ragione vale per `uvicorn.run`, non per **queste** decisioni -- quale host conta
come locale, che la chiave si genera solo per lui, e che il file si scrive in modo che lo legga
solo l'utente. Sono tre regole, e fino al 14/9/2026 erano scritte in un commento.
"""

import os
import sys

import pytest

import astrolog.__main__ as avvio
from astrolog.startup import token_for


def test_the_key_is_born_only_for_who_listens_at_home(tmp_path):
    """Sul NAS non nasce nessuna chiave: la rete di casa e' fidata, e una chiave scritta su un
    disco condiviso sarebbe un segreto in piu' senza un difetto in meno."""
    assert token_for("0.0.0.0", tmp_path) is None  # noqa: S104 - qui non si lega niente: si prova che su quell'host la chiave NON nasce
    assert not (tmp_path / "token").exists()

    for casa in ("127.0.0.1", "localhost"):
        assert token_for(casa, tmp_path)


def test_who_starts_the_process_can_impose_the_key(tmp_path, monkeypatch):
    """Serve a `tools/dev.py`, che accende backend e server di sviluppo e deve dare **la stessa**
    chiave a tutti e due: altrimenti la pagina servita da Vite ne porta una che il backend non
    riconosce, e ogni richiesta prende 401."""
    monkeypatch.setenv("ASTROLOG_TOKEN", "la-mia-chiave")
    assert token_for("127.0.0.1", tmp_path) == "la-mia-chiave"
    assert (tmp_path / "token").read_text(encoding="utf-8") == "la-mia-chiave"


def test_without_the_variable_the_key_is_born_here_and_is_not_guessable(tmp_path, monkeypatch):
    monkeypatch.delenv("ASTROLOG_TOKEN", raising=False)
    chiave = token_for("127.0.0.1", tmp_path)
    assert chiave and len(chiave) >= 32
    assert (tmp_path / "token").read_text(encoding="utf-8") == chiave
    # Due avvii, due chiavi: una chiave che si ripete non e' una chiave per avvio.
    assert token_for("127.0.0.1", tmp_path) != chiave


@pytest.mark.parametrize(("minuti", "secondi"), [("60", 3600.0), ("0.5", 30.0), (None, None)])
def test_the_nas_scan_cadence_reaches_the_app(monkeypatch, minuti, secondi):
    """`ASTROLOG_SCAN_EVERY_MIN` e' l'unico modo di accendere la scansione a cadenza sul NAS: se
    l'avvio la leggesse storta, la scansione si spegnerebbe in silenzio. Senza, nessuna cadenza."""
    chiesto = {}
    monkeypatch.setattr(avvio, "setup_logging", lambda *a: None)
    monkeypatch.setattr(avvio, "create_app", lambda *a, **k: chiesto.update(k))
    monkeypatch.setattr(avvio.uvicorn, "run", lambda *a, **k: None)
    monkeypatch.delenv("ASTROLOG_SCAN_EVERY_MIN", raising=False)
    if minuti is not None:
        monkeypatch.setenv("ASTROLOG_SCAN_EVERY_MIN", minuti)
    avvio.main()
    assert chiesto["scan_every_s"] == secondi


@pytest.mark.skipif(sys.platform == "win32", reason="i permessi POSIX su Windows non significano")
def test_only_the_user_can_read_the_key_file(tmp_path, monkeypatch):
    """Il default (0644) la darebbe a chiunque abbia un account sulla macchina. Su un NAS o su un
    Mac di famiglia e' la differenza fra una chiave e un file pubblico."""
    monkeypatch.delenv("ASTROLOG_TOKEN", raising=False)
    token_for("127.0.0.1", tmp_path)
    assert oct(os.stat(tmp_path / "token").st_mode & 0o777) == oct(0o600)
