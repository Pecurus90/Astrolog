"""Le specifiche della camera: il pixel fisico e il colore su cui concordano i file, e la parola
dell'utente che nessun ricalcolo tocca. La convenzione di `XPIXSZ` e le sue fonti stanno nel
contratto, `docs/domini/spina.md`.
"""

import sqlite3

import pytest

from astrolog.spine import camera_specs, gear, normalize, unfiltered
from astrolog.spine import declarations as decl
from astrolog.spine.normalize import normalize_frames
from astrolog.units import most_frequent, physical_pixel_um
from conftest import senza_soggetti, write_light
from test_normalize import one, run_normalize, scan

CAMERA = "ATR2600M"

# (nome, XPIXSZ, binning, pixel fisico atteso)
PIXEL_FISICO = [
    ("bin 1", 3.76, 1, 3.76),
    ("bin 2: XPIXSZ scritto col binning", 7.52, 2, 3.76),
    ("bin 3, senza la coda della divisione", 11.28, 3, 3.76),
    ("binning che non si sa", 3.76, None, None),
    ("pixel che non si sa", None, 2, None),
]  # fmt: skip


@pytest.mark.parametrize(
    "scritto, binning, fisico", [c[1:] for c in PIXEL_FISICO], ids=[c[0] for c in PIXEL_FISICO]
)
def test_the_physical_pixel_is_the_written_one_divided_by_the_binning(scritto, binning, fisico):
    assert physical_pixel_um(scritto, binning) == fisico


# (nome, {valore: file che lo dicono}, valore che vince)
PIU_FREQUENTE = [
    ("nessun file", {}, None),
    ("un valore solo", {3.76: 1}, 3.76),
    ("la maggioranza", {3.76: 3, 4.0: 1}, 3.76),
    ("pari in cima: nessuno", {3.76: 2, 4.0: 2}, None),
    ("pari in fondo non conta", {3.76: 3, 4.0: 1, 4.5: 1}, 3.76),
]  # fmt: skip


@pytest.mark.parametrize(
    "voti, vince", [c[1:] for c in PIU_FREQUENTE], ids=[c[0] for c in PIU_FREQUENTE]
)
def test_the_most_frequent_value_wins_and_a_tie_on_top_writes_nothing(voti, vince):
    assert most_frequent(voti) == vince


def scansiona(conn, cartella, *headers):
    """Una cartella nuova con una posa per header, scansionata. Ogni posa ha la sua data: con la
    stessa data, camera ed esposizione sarebbero copie l'una dell'altra."""
    for n, header in enumerate(headers):
        campi = {"INSTRUME": CAMERA, **header}
        write_light(cartella / f"posa{n}.fits", date=f"2024-05-17T21:{n:02d}:00", **campi)
    scan(conn, cartella)


def pose(conn, cartella, *headers):
    """Come `scansiona`, e poi normalizzate."""
    scansiona(conn, cartella, *headers)
    run_normalize(conn)


def colonna(conn, campo):
    return one(conn, f"SELECT {campo} FROM instruments WHERE name = ?", (CAMERA,))  # noqa: S608


def camera_id(conn, name=CAMERA):
    return one(conn, "SELECT id FROM instruments WHERE name = ?", (name,))


BIN1 = {"XPIXSZ": 3.76, "XBINNING": 1}


def _in_coda(conn):
    return one(conn, "SELECT COUNT(*) FROM frame_stages WHERE stage = 'normalize'"
                     " AND status = 'pending'")  # fmt: skip


def test_a_vote_that_does_not_change_the_colour_requeues_nothing(conn, tmp_path):
    """Il voto rimette in coda le pose senza matrice solo se il colore della camera cambia: rifarlo
    uguale a ogni giro rilavorerebbe per niente, e riaprirebbe anche gli stadi dopo."""
    pose(conn, tmp_path / "lib", {"BAYERPAT": "RGGB"}, {"BAYERPAT": "RGGB"}, {})
    assert colonna(conn, "camera_type") == "color"
    camera_specs.from_files(conn)
    assert _in_coda(conn) == 0


RGGB = {"BAYERPAT": "RGGB"}


def test_the_poses_already_done_follow_a_camera_that_turns_colour(conn, tmp_path):
    """La posa senza matrice entrata quando la camera non era ancora a colori rientra nel giro che
    la scopre a colori, e ne esce OSC con le altre: non resta un filtro da chiedere per sempre."""
    # (cartella, minuto, matrice): minuti diversi, o sarebbero copie l'una dell'altra
    for folder, poses in [("prima", [(0, {})]), ("poi", [(1, RGGB), (2, RGGB)])]:
        for minute, bayer in poses:
            write_light(tmp_path / folder / f"{minute}.fits", date=f"2024-05-17T21:0{minute}:00",
                        INSTRUME=CAMERA, FILTER="L", **bayer)  # fmt: skip
        scan(conn, tmp_path / folder)
        run_normalize(conn)
    filters = one(
        conn,
        "SELECT GROUP_CONCAT(DISTINCT COALESCE(fl.name, '-')) FROM frames f"
        " LEFT JOIN filters fl ON fl.id = f.filter_id",
    )
    assert filters == "OSC"
    assert _in_coda(conn) == 0


def test_a_final_vote_other_than_the_one_used_requeues(conn, tmp_path):
    """Se il voto di fine corsa non e' quello con cui le pose hanno scelto il filtro -- una corsa
    fermata prima delle pose che lo spostavano -- quelle senza matrice tornano in coda."""
    pose(conn, tmp_path / "lib", {"BAYERPAT": "RGGB"}, {"BAYERPAT": "RGGB"}, {})
    camera_specs.from_files(conn, {CAMERA: None})
    assert _in_coda(conn) == 1


def test_a_vote_under_a_colour_the_user_wrote_requeues_nothing(conn, tmp_path):
    """Se il colore l'ha scritto l'utente sulla scheda, il voto dei file non sposta nessun filtro:
    cambiare voto non rimette in coda niente."""
    pose(conn, tmp_path / "lib", {"BAYERPAT": "RGGB"}, {"BAYERPAT": "RGGB"}, {})
    gear.declare_instrument(conn, camera_id(conn), {"camera_type": "mono"})
    run_normalize(conn)
    conn.execute("UPDATE instruments SET camera_type = NULL WHERE name = ?", (CAMERA,))
    camera_specs.from_files(conn)
    assert colonna(conn, "camera_type") == "color"  # il voto e' cambiato
    assert _in_coda(conn) == 0


def test_the_pixel_follows_the_files_not_the_first_one(conn, tmp_path):
    """Il primo file che capita non decide per sempre: quando arrivano altri file che dicono
    un'altra cosa, vince il valore piu' frequente."""
    pose(conn, tmp_path / "uno", {"XPIXSZ": 4.0, "XBINNING": 1})
    assert colonna(conn, "pixel_size_um") == 4.0
    pose(conn, tmp_path / "due", BIN1, BIN1, BIN1)
    assert colonna(conn, "pixel_size_um") == 3.76


def test_files_at_bin_two_give_the_physical_pixel(conn, tmp_path):
    """Chi riprende a bin 2 ha `XPIXSZ` doppio nell'header: la camera ha il pixel fisico."""
    pose(conn, tmp_path / "lib", {"XPIXSZ": 7.52, "XBINNING": 2}, {"XPIXSZ": 7.52, "XBINNING": 2})
    assert colonna(conn, "pixel_size_um") == 3.76


def test_files_without_binning_do_not_vote(conn, tmp_path):
    """Senza binning non si sa quale pixel fisico dica `XPIXSZ`: quei file non contano."""
    pose(conn, tmp_path / "lib", {"XPIXSZ": 3.76}, {"XPIXSZ": 3.76})
    assert colonna(conn, "pixel_size_um") is None


def test_a_tie_writes_nothing(conn, tmp_path):
    """A pari file non c'e' un valore piu' frequente, e non si sceglie a caso."""
    pose(conn, tmp_path / "lib", BIN1, {"XPIXSZ": 4.0, "XBINNING": 1})
    assert colonna(conn, "pixel_size_um") is None


def test_a_calibrated_copy_does_not_vote(conn, tmp_path):
    """Una copia riscritta non e' un'altra posa, e non vota: tolta lei, vince il valore che le
    pose vere dicono piu' spesso, invece di un pari costruito da una copia."""
    quattro = {"XPIXSZ": 4.0, "XBINNING": 1}
    pose(conn, tmp_path / "uno", BIN1, quattro, quattro)
    assert colonna(conn, "pixel_size_um") == 4.0
    ids = [r[0] for r in conn.execute("SELECT id FROM frames WHERE pixel_size_um = 4.0")]
    conn.execute("UPDATE frames SET copy_of = ? WHERE id = ?", (ids[0], ids[1]))
    pose(conn, tmp_path / "due", BIN1)  # una posa nuova: il suo giro ricalcola la camera
    assert colonna(conn, "pixel_size_um") == 3.76


def test_a_stopped_run_still_writes_the_camera(conn, tmp_path):
    """Fermare la corsa a meta' non lascia la camera senza pixel fino alla prossima
    scansione: le pose gia' collegate votano anche cosi'."""
    scansiona(conn, tmp_path / "lib", BIN1, BIN1, BIN1)
    corsa = normalize_frames(conn)
    next(corsa)
    corsa.close()
    assert colonna(conn, "pixel_size_um") == 3.76


def test_a_run_that_breaks_still_writes_the_camera(conn, tmp_path, monkeypatch):
    """Una corsa che si schianta dopo aver lavorato delle pose le ha gia' scritte, e quelle non
    tornano in coda: la camera si ricalcola anche li', o resterebbe vuota fino alla prossima
    posa che arriva."""
    scansiona(conn, tmp_path / "lib", BIN1, BIN1)
    real, calls = normalize.frame_safely, []

    def breaks_after_one(*args):
        calls.append(1)
        if len(calls) > 1:  # la prima posa si lavora, poi la corsa si schianta
            raise sqlite3.OperationalError("database is locked")
        return real(*args)

    monkeypatch.setattr(normalize, "frame_safely", breaks_after_one)
    with pytest.raises(sqlite3.OperationalError):
        run_normalize(conn)
    assert colonna(conn, "pixel_size_um") == 3.76


def test_a_camera_left_without_files_forgets_what_they_said(conn, tmp_path):
    """Una camera che non ha piu' pose che votano non tiene il pixel di quando le aveva."""
    pose(conn, tmp_path / "uno", BIN1)
    conn.execute("UPDATE frames SET rig_id = NULL")
    pose(conn, tmp_path / "due", {**BIN1, "INSTRUME": "Un'altra camera"})
    assert colonna(conn, "pixel_size_um") is None


def test_the_colour_follows_the_files_too(conn, tmp_path):
    """La matrice di Bayer piu' frequente fa la camera a colori; la sua assenza non fa una
    camera mono, e un primo file senza matrice non decide per tutti."""
    pose(conn, tmp_path / "uno", BIN1)
    assert colonna(conn, "camera_type") is None
    pose(conn, tmp_path / "due", {**BIN1, "BAYERPAT": "RGGB"}, {**BIN1, "BAYERPAT": "RGGB"})
    assert colonna(conn, "camera_type") == "color"


def test_the_card_says_the_sensor_and_the_answer_stays_and_the_pixel_does_nothing(conn, tmp_path):
    """La risposta sulle pose che non dicono il filtro parla del FILTRO, la scheda del SENSORE
    (`spine/unfiltered.py`): scrivere "a colori" non la ritira -- la camera non si chiede piu',
    perche' un sensore nudo a colori E' OSC -- e tornando a mono la risposta e' ancora quella. Il
    pixel non c'entra con nessuna delle due."""
    pose(conn, tmp_path / "lib", {**BIN1, "FILTER": ""})
    cam = camera_id(conn)
    unfiltered.declare(conn, CAMERA, unfiltered.NO_FILTER_ANSWER)
    gear.declare_instrument(conn, cam, {"pixel_size_um": 3.8})
    assert risposte(conn) == [(CAMERA, unfiltered.NO_FILTER_ANSWER)]
    gear.declare_instrument(conn, cam, {"camera_type": "color"})
    assert risposte(conn) == []
    gear.declare_instrument(conn, cam, {"camera_type": "mono"})
    assert risposte(conn) == [(CAMERA, unfiltered.NO_FILTER_ANSWER)]


def risposte(conn):
    """Le risposte sulle pose che non dicono il filtro, come le vede la pagina: per camera."""
    return [(g["key"], g["answer"]) for g in unfiltered.by_camera(conn)]


def test_the_unfiltered_answer_follows_the_camera_when_renamed(conn, tmp_path):
    """La risposta sulle pose che non dicono il filtro e' agganciata al nome della camera, come la
    scheda: rinominarla la porta con se'."""
    pose(conn, tmp_path / "lib", {"FILTER": ""})
    unfiltered.declare(conn, CAMERA, unfiltered.NO_FILTER_ANSWER)
    gear.declare_instrument(conn, camera_id(conn), {"name": "La mia mono"})
    assert risposte(conn) == [("La mia mono", unfiltered.NO_FILTER_ANSWER)]


def test_merging_into_a_colour_camera_carries_the_answer_even_there(conn, tmp_path):
    """Nell'unione la risposta dell'assorbita passa alla tenuta anche quando la tenuta dice "a
    colori": la scheda dice il sensore, la risposta dice il filtro, e tornando a mono la risposta
    e' ancora li' invece di essere sparita."""
    pose(
        conn,
        tmp_path / "lib",
        {"INSTRUME": "CAMA", "FILTER": ""},
        {"INSTRUME": "CAMB", "FILTER": ""},
    )
    a, b = camera_id(conn, "CAMA"), camera_id(conn, "CAMB")
    unfiltered.declare(conn, "CAMA", unfiltered.NO_FILTER_ANSWER)
    gear.declare_instrument(conn, b, {"camera_type": "color"})
    gear.merge_instrument(conn, a, b)
    assert risposte(conn) == []
    gear.declare_instrument(conn, b, {"camera_type": "mono"})
    assert risposte(conn) == [("CAMB", unfiltered.NO_FILTER_ANSWER)]


def test_the_unfiltered_poses_are_asked_per_camera(conn, tmp_path):
    """Le pose che non dicono il filtro si raggruppano per camera, la piu' numerosa in cima
    (`spine/unfiltered.py`): `open` e' come un filtro che manca, una posa col suo filtro non si
    conta, e un file con la matrice contro uno senza non fa la camera a colori."""
    pose(
        conn,
        tmp_path / "lib",
        {"INSTRUME": "B mono", "FILTER": "open"},
        {"INSTRUME": "B mono", "FILTER": ""},
        {"INSTRUME": "B mono", "FILTER": "L"},
        {"INSTRUME": "A colori", "FILTER": ""},
        {"INSTRUME": "A colori", "BAYERPAT": "RGGB"},
    )
    assert [senza_soggetti(g) for g in unfiltered.by_camera(conn)] == [
        {"key": "B mono", "frames": 2, "answer": None, "filter_id": None},
        {"key": "A colori", "frames": 1, "answer": None, "filter_id": None},
    ]


def test_the_colour_normalize_reads_is_the_one_the_card_shows(conn, tmp_path):
    """Il colore con cui `normalize` decide il filtro (`unfiltered.is_colour`) e quello che la
    scheda mostra (`gear.camera_specs`) sono lo stesso fatto: cio' che l'utente ha scritto, poi il
    voto dei file. Se divergessero, la spina deciderebbe il filtro con un colore diverso da quello
    che l'utente sta guardando -- ed e' la meta' "scritto mono vince sul voto" a non avere prove."""
    pose(conn, tmp_path / "lib", {**BIN1, "BAYERPAT": "RGGB"}, {**BIN1, "BAYERPAT": "RGGB"})
    cam = camera_id(conn)

    def concordano():
        scheda = gear.camera_specs(conn)[cam]["camera_type"]
        assert unfiltered.is_colour(conn, CAMERA) == (scheda == "color")
        return scheda

    assert concordano() == "color"  # non c'e' niente di scritto: lo dicono i file
    gear.declare_instrument(conn, cam, {"camera_type": "mono"})
    assert concordano() == "mono"  # scritto mono: vince sul voto dei file
    gear.declare_instrument(conn, cam, {"camera_type": "color"})
    assert concordano() == "color"


def test_what_i_write_on_the_card_is_never_recomputed(conn, tmp_path):
    """Pixel e colore scritti dall'utente vincono su cio' che dicono i file, anche dopo che
    altri file sono arrivati; il rilevato resta nella sua colonna."""
    pose(conn, tmp_path / "uno", BIN1)
    gear.declare_instrument(conn, camera_id(conn), {"pixel_size_um": 3.8, "camera_type": "mono"})
    pose(conn, tmp_path / "due", BIN1, BIN1)
    assert gear.camera_specs(conn)[camera_id(conn)] == {"camera_type": "mono", "pixel_size_um": 3.8}
    assert colonna(conn, "pixel_size_um") == 3.76


def test_what_i_write_wins_field_by_field(conn, tmp_path):
    """Scrivere il pixel non spegne il colore letto dai file: si vince campo per campo."""
    pose(conn, tmp_path / "lib", {**BIN1, "BAYERPAT": "RGGB"})
    gear.declare_instrument(conn, camera_id(conn), {"pixel_size_um": 3.8})
    specs = gear.camera_specs(conn)[camera_id(conn)]
    assert specs == {"pixel_size_um": 3.8, "camera_type": "color"}


def test_merging_two_cameras_keeps_the_card_of_the_one_that_stays(conn, tmp_path):
    """Nell'unione vince la scheda della camera tenuta, e cio' che la camera assorbita diceva
    passa dove la tenuta non ha scritto niente. Non resta niente di orfano: rinominare poi la
    tenuta col nome dell'assorbita non riporta a galla la scheda sparita."""
    pose(conn, tmp_path / "lib", {**BIN1, "INSTRUME": "CAMA"}, {**BIN1, "INSTRUME": "CAMB"})
    a, b = camera_id(conn, "CAMA"), camera_id(conn, "CAMB")
    gear.declare_instrument(conn, a, {"pixel_size_um": 9.9, "camera_type": "mono"})
    gear.declare_instrument(conn, b, {"pixel_size_um": 5.5})
    gear.merge_instrument(conn, a, b)
    assert gear.camera_specs(conn)[b] == {"pixel_size_um": 5.5, "camera_type": "mono"}
    orfane = "SELECT COUNT(*) FROM declarations WHERE entity_key = 'camera|CAMA'"
    assert one(conn, orfane) == 0
    gear.declare_instrument(conn, b, {"name": "CAMA"})
    assert gear.camera_specs(conn)[b]["pixel_size_um"] == 5.5


def test_renaming_carries_the_confirmation_and_beats_leftovers(conn, tmp_path):
    """Rinominando, la conferma va col pezzo, e sotto il nome nuovo vince cio' che si sposta:
    li' non puo' esserci un pezzo vivo, solo resti."""
    pose(conn, tmp_path / "lib", BIN1)
    cam = camera_id(conn)
    decl.confirm(conn, "instrument", decl.instrument_key("camera", CAMERA))
    gear.declare_instrument(conn, cam, {"pixel_size_um": 3.8})
    decl.write_declaration(conn, "instrument", "camera|Nuova", "pixel_size_um", 1.0)
    gear.declare_instrument(conn, cam, {"name": "Nuova"})
    assert gear.camera_specs(conn)[cam]["pixel_size_um"] == 3.8
    assert "camera|Nuova" in decl.confirmed_keys(conn, "instrument")


def test_renaming_the_camera_keeps_what_i_wrote(conn, tmp_path):
    """La parola dell'utente e' agganciata al nome del pezzo: rinominarlo la porta con se'. E le
    pose che arrivano dopo, con la grafia vecchia nell'header, trovano la camera rinominata
    invece di ricrearne una senza la sua scheda."""
    pose(conn, tmp_path / "uno", BIN1)
    cam = camera_id(conn)
    gear.declare_instrument(conn, cam, {"pixel_size_um": 3.8})
    gear.declare_instrument(conn, cam, {"name": "La mia camera"})
    assert gear.camera_specs(conn)[cam]["pixel_size_um"] == 3.8
    pose(conn, tmp_path / "due", BIN1)
    assert one(conn, "SELECT COUNT(*) FROM instruments WHERE kind = 'camera'") == 1
    assert gear.camera_specs(conn)[cam]["pixel_size_um"] == 3.8
