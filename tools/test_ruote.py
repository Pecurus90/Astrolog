"""La guardia delle ruote, vista rossa.

Non tocca la rete: si prova la REGOLA (quali nomi di ruota coprono quale bersaglio) sui nomi
di file, che e' l'unica parte che puo' sbagliare. Il giro su PyPI e' un lavoro di CI.
"""

import ruote


def test_a_pure_python_wheel_covers_every_target():
    """`py3-none-any` gira dappertutto: e' la ruota che non ha architettura."""
    files = ["x-1.0-py3-none-any.whl"]
    assert all(ruote.covers(files, t) for t in ruote.TARGETS)


def test_a_library_without_the_arm_wheel_is_caught():
    """E' il caso che questa guardia esiste per prendere: una libreria compilata che su un NAS
    arm64 andrebbe compilata a mano, e quindi non si installa."""
    solo_x86 = [
        "x-1.0-cp312-cp312-manylinux_2_17_x86_64.whl",
        "x-1.0-cp312-cp312-win_amd64.whl",
        "x-1.0-cp312-cp312-macosx_11_0_x86_64.whl",
    ]
    assert ruote.covers(solo_x86, "Linux amd64") is True
    assert ruote.covers(solo_x86, "Windows x64") is True
    assert ruote.covers(solo_x86, "Linux arm64") is False
    assert ruote.covers(solo_x86, "Mac Apple Silicon") is False


def test_a_universal2_wheel_covers_both_macs():
    """Un file solo per i due Mac: chi lo pubblica non deve risultare scoperto su entrambi."""
    universal = ["x-1.0-cp312-cp312-macosx_11_0_universal2.whl"]
    assert ruote.covers(universal, "Mac Intel") is True
    assert ruote.covers(universal, "Mac Apple Silicon") is True
    assert ruote.covers(universal, "Linux arm64") is False


def test_musllinux_counts_as_much_as_manylinux():
    """L'immagine Docker puo' essere Alpine: una ruota musl copre lo stesso bersaglio."""
    assert ruote.covers(["x-1.0-cp312-cp312-musllinux_1_2_aarch64.whl"], "Linux arm64") is True


def test_a_wheel_for_another_architecture_covers_nothing_by_mistake():
    """I frammenti si cercano tutti insieme: `macosx` piu' `arm64`. Senza, una ruota Linux
    aarch64 sembrerebbe coprire il Mac Apple Silicon."""
    linux_arm = ["x-1.0-cp312-cp312-manylinux_2_17_aarch64.whl"]
    assert ruote.covers(linux_arm, "Linux arm64") is True
    assert ruote.covers(linux_arm, "Mac Apple Silicon") is False


def test_the_declared_dependencies_are_read_from_the_one_place_they_live():
    """L'elenco viene da `backend/pyproject.toml`, non da una copia: se qualcuno aggiunge una
    dipendenza e non la controlla, la guardia deve accorgersene da sola."""
    nomi = ruote.declared()
    assert "astropy" in nomi and "tzfpy" in nomi and "tzdata" in nomi
    assert all(c not in n for n in nomi for c in "<>=!~ #")
