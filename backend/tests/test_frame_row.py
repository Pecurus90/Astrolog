"""La riga di `frames` la scrive la pipeline senza importare la spina (passo 40.4): due fatti
che la spina ha gia' vivono qui in copia, e queste prove le tengono legate alla loro casa."""

import pytest

from astrolog.pipeline import frame_row
from astrolog.spine import stages
from astrolog.spine.frame_folder import key_of_path


def test_a_frame_is_born_with_the_stages_of_the_spine():
    assert tuple(str(s) for s in stages.STAGES) == frame_row.STAGES


@pytest.mark.parametrize(
    ("root", "rel"),
    [
        ("D:\\Astro", "M31/a.fits"),
        ("D:\\Astro\\", "a.fits"),
        ("/volume1/astro", "2026/10/12/dark/d.fits"),
        ("/volume1/astro/", "/notte/a.fits"),
        ("Z:/", "x/y.fits"),
    ],
)
def test_the_folder_of_a_file_has_the_key_the_answers_use(root, rel):
    """La risposta "calibrazione" su una cartella si cerca con questa chiave: se diverge da quella
    della spina, il file entra in una cartella che l'utente ha fermato."""
    assert frame_row.folder_key(root, rel) == key_of_path(root, rel)
