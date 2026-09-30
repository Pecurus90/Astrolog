"""Dove cominciano i pixel e quanto e' lungo il blocco dati: la scansione lo ricava dai blocchi
dell'header, senza far leggere ad astropy tutte le pagine del file (`fits/header_read.py`). Da quei
due numeri dipende l'impronta, cioe' se un file gia' in archivio si riconosce: devono essere
identici a quelli di astropy su ogni forma di file, e dove la strada veloce non e' sicura si
ritira."""

import hashlib

import numpy as np
import pytest
from astropy.io import fits

from astrolog.fits import header_read
from astrolog.fits.header_read import _data_block, frame_fingerprint, read_header

# il banco ha file rotti apposta (troncati, senza END): astropy lo dice, ed e' atteso
pytestmark = pytest.mark.filterwarnings("ignore::astropy.utils.exceptions.AstropyUserWarning")


def _astropy(path):
    """L'oracolo: cio' che dice astropy leggendo tutto il file."""
    with fits.open(
        path, output_verify="silently", ignore_missing_end=True, memmap=False, lazy_load_hdus=False
    ) as hdul:
        for i, hdu in enumerate(hdul):
            info = hdul.fileinfo(i)
            if info and (isinstance(hdu, fits.CompImageHDU) or hdu.header.get("NAXIS", 0)):
                return info["datLoc"], info["datSpan"]
    return 0, 0


def _outcome(read, path):
    """Il risultato, o il tipo di errore: due strade che falliscono uguale sono uguali."""
    try:
        return read(path)
    except Exception as err:  # noqa: BLE001 - si confronta il tipo, non si ingoia
        return type(err)


def _image(path, shape, dtype, cards=0, extension=False, **keys):
    header = fits.Header()
    for key, value in keys.items():
        header[key] = value
    header["SEGNAPO"] = "posto per una card riscritta a mano"
    for i in range(cards):  # un header lungo, oltre il primo blocco da 2880 byte
        header[f"NOTA{i:04d}"] = "x" * 40
    data = np.arange(int(np.prod(shape)), dtype=dtype).reshape(shape)
    pages: list = [fits.PrimaryHDU(data=data, header=header)]
    if extension:
        pages.append(fits.ImageHDU(np.ones((4, 4), np.int16)))
    fits.HDUList(pages).writeto(path)
    return path


def _card(text):
    return text.encode("ascii").ljust(80)


def _rewrite(path, old, new):
    """Riscrive una card su disco, byte per byte: un header che astropy non scriverebbe mai."""
    raw = path.read_bytes()
    assert raw.count(old) >= 1, old
    path.write_bytes(raw.replace(old, new, 1))
    return path


def _bench(tmp_path):
    """Una forma per riga: quello che la scansione puo' incontrare. `simple` sono quelle che la
    strada veloce legge da se'; le altre le decide astropy."""
    simple = {
        "int16": _image(tmp_path / "a.fits", (3, 4), np.int16),
        "float32": _image(tmp_path / "b.fits", (8, 8), np.float32),
        "uint8_odd": _image(tmp_path / "c.fits", (7, 13), np.uint8),
        "int32": _image(tmp_path / "d.fits", (5, 5), np.int32),
        "float64": _image(tmp_path / "e.fits", (4, 6), np.float64),
        "cube": _image(tmp_path / "f.fits", (3, 4, 5), np.int16),
        "large": _image(tmp_path / "g.fits", (300, 300), np.int16),
        "long_header": _image(tmp_path / "h.fits", (3, 4), np.int16, cards=80),
        "with_extension": _image(tmp_path / "i.fits", (10, 10), np.int16, extension=True),
        # chiavi corte e una che comincia con END: sono chiavi, e la lettura prosegue
        "short_keys": _image(
            tmp_path / "j.fits", (3, 4), np.int16, RA=10.5, DEC=41.2, ENDTIME="21:00:00"
        ),
        # l'header e' intero, mancano pixel: la lunghezza la dice l'header, come per astropy
        "truncated": _image(tmp_path / "t.fits", (300, 300), np.int16),
    }
    simple["truncated"].write_bytes(simple["truncated"].read_bytes()[:10000])
    mef = tmp_path / "mef.fits"
    fits.HDUList([fits.PrimaryHDU(), fits.ImageHDU(np.ones((4, 4), np.int16))]).writeto(mef)
    rice = tmp_path / "rice.fits"
    fits.HDUList([fits.PrimaryHDU(), fits.CompImageHDU(np.ones((16, 16), np.float32))]).writeto(
        rice
    )
    # una pagina senza pixel prima di quella che li ha, e altre dopo: la pagina giusta e' la terza
    pages_after = tmp_path / "pages_after.fits"
    fits.HDUList(
        [fits.PrimaryHDU(), fits.ImageHDU(), fits.ImageHDU(np.ones((4, 4), np.int16))]
        + [fits.ImageHDU(np.zeros((2, 2), np.int16)) for _ in range(4)]
    ).writeto(pages_after)
    empty = tmp_path / "empty.fits"
    fits.PrimaryHDU().writeto(empty)
    groups = tmp_path / "groups.fits"
    fits.GroupsHDU(
        fits.GroupData(np.zeros((50, 1, 4, 4), np.float32), parnames=["P"], pardata=[np.zeros(50)])
    ).writeto(groups)
    placeholder = _card("SEGNAPO = 'posto per una card riscritta a mano'")
    others = {
        "mef": mef,
        "pages_after": pages_after,
        "compressed": rice,
        "no_data": empty,
        "groups": groups,
        "no_end": _rewrite(_image(tmp_path / "s.fits", (3, 4), np.int16), _card("END"), _card("")),
        "end_with_nulls": _rewrite(
            _image(tmp_path / "n.fits", (10, 10), np.int16, extension=True),
            _card("END"),
            b"END" + b"\0" * 77,
        ),
        "end_with_text": _rewrite(
            _image(tmp_path / "x.fits", (10, 10), np.int16, extension=True),
            _card("END"),
            _card("END  x"),
        ),
        "pcount": _rewrite(
            _image(tmp_path / "p.fits", (100, 10), np.int16), placeholder, _card("PCOUNT  = 2000")
        ),
        "groups_card": _rewrite(
            _image(tmp_path / "k.fits", (3, 4), np.int16),
            placeholder,
            _card("GROUPS  =                    T"),
        ),
        "gcount": _rewrite(
            _image(tmp_path / "q.fits", (100, 10), np.int16), placeholder, _card("GCOUNT  = 2")
        ),
        "odd_bitpix": _rewrite(
            _image(tmp_path / "o.fits", (3, 4), np.int16),
            _card("BITPIX  =                   16 / array data type"),
            _card("BITPIX  =                   12 / array data type"),
        ),
        "float_naxis": _rewrite(
            _image(tmp_path / "r.fits", (3, 4), np.int16),
            _card("NAXIS1  =                    4"),
            _card("NAXIS1  =                  4.0"),
        ),
        "naxis_without_equals": _rewrite(
            _image(tmp_path / "w.fits", (3, 4), np.int16),
            _card("NAXIS1  =                    4"),
            _card("NAXIS1                       4"),
        ),
        "not_simple": _rewrite(
            _image(tmp_path / "u.fits", (3, 4), np.int16),
            _card("SIMPLE  =                    T / conforms to FITS standard"),
            _card("SIMPLE  =                    F / conforms to FITS standard"),
        ),
    }
    return {**simple, **others}, set(simple), set(others)


def test_the_data_block_is_the_one_astropy_finds_on_every_kind_of_file(tmp_path):
    bench, _, _ = _bench(tmp_path)
    for name, path in bench.items():
        assert _outcome(_data_block, str(path)) == _outcome(_astropy, str(path)), name


def test_the_header_reader_finds_the_block_astropy_finds_where_it_opens_the_file(tmp_path):
    """Quando la lettura dell'header trova una pagina con pixel dopo una primaria che non ne ha,
    dice anche dove cominciano, e dice lo stesso di astropy che legge tutto. Quando non la trova
    non dice niente, e decide chi calcola l'impronta."""
    bench, _, _ = _bench(tmp_path)
    for name, path in bench.items():
        read = _outcome(header_read.read_frame, str(path))
        if isinstance(read, tuple) and read[1] is not None:
            assert read[1] == _astropy(str(path)), name
    for name in ("mef", "pages_after", "compressed"):
        assert header_read.read_frame(str(bench[name]))[1] is not None, name


def test_a_header_without_end_is_still_read(tmp_path):
    """Un header a cui manca l'END si legge lo stesso, come lo legge astropy quando glielo si
    concede: e' un file scritto male, non un file illeggibile, e buttarlo toglierebbe una posa."""
    bench, _, _ = _bench(tmp_path)
    read = _outcome(header_read.read_frame, str(bench["no_end"]))
    assert isinstance(read, tuple), read
    assert read[0]["NAXIS"] == 2


def test_the_header_of_the_pixel_page_joins_without_its_notes(tmp_path):
    """L'header di una pagina con pixel si unisce a quello della primaria senza le sue note
    (`HISTORY`, `COMMENT`): e' il comportamento di oggi, e ha un costo che la coda tiene aperto
    ("La spia dei file sommati non si vede su un FITS compresso"). Chi chiude quella voce ribalta
    questo test."""
    path = tmp_path / "notes.fits"
    page = fits.ImageHDU(np.ones((4, 4), np.int16))
    page.header["OBJECT"] = "M 42"
    page.header["HISTORY"] = "nota della pagina"
    page.header["COMMENT"] = "commento della pagina"
    fits.HDUList([fits.PrimaryHDU(), page]).writeto(path)
    header, _ = header_read.read_frame(str(path))
    assert header["OBJECT"] == "M 42"
    notes = [str(v) for k, v in header.items() if k in ("HISTORY", "COMMENT")]
    assert not any("della pagina" in n for n in notes), notes


def test_the_header_reader_stops_at_the_first_page_with_pixels(tmp_path, monkeypatch):
    """Le pagine si leggono fino alla prima con pixel, non oltre: un file con molte estensioni le
    farebbe leggere tutte a ogni file. E la pagina scelta e' quella giusta, non la prima dopo la
    primaria: l'header e l'impronta vengono tutti e due da li'."""
    bench, _, _ = _bench(tmp_path)
    with fits.open(str(bench["pages_after"])) as all_pages:
        pages = len(all_pages)
    loaded = []
    real = fits.HDUList._read_next_hdu

    def counted(self):
        loaded.append(1)
        return real(self)

    # un contesto suo: `monkeypatch.undo()` toglierebbe anche il recinto di tutta la suite
    with monkeypatch.context() as counting:
        counting.setattr(fits.HDUList, "_read_next_hdu", counted)
        header, block = header_read.read_frame(str(bench["pages_after"]))
    assert len(loaded) < pages, (len(loaded), pages)
    assert (header["NAXIS1"], block) == (4, _astropy(str(bench["pages_after"])))


def test_a_header_read_file_with_pages_is_opened_once(tmp_path, monkeypatch):
    """Un file a piu' pagine o compresso lo apre astropy **una** volta per header e impronta: ogni
    apertura fa rileggere ad astropy le pagine."""
    bench, _, _ = _bench(tmp_path)
    opened = []
    real_open, real_getheader = header_read.fits.open, header_read.fits.getheader

    def opening(*args, **kwargs):
        opened.append("open")
        return real_open(*args, **kwargs)

    def reading(*args, **kwargs):
        opened.append("getheader")
        return real_getheader(*args, **kwargs)

    monkeypatch.setattr(header_read.fits, "open", opening)
    monkeypatch.setattr(header_read.fits, "getheader", reading)
    for name in ("mef", "compressed"):
        opened.clear()
        header, block = header_read.read_frame(str(bench[name]))
        frame_fingerprint(str(bench[name]), header, block)
        assert len(opened) == 1, (name, opened)


def test_the_fingerprint_is_the_same_with_the_block_read_with_the_header(tmp_path):
    """L'impronta calcolata con cio' che dice la lettura dell'header e' quella di prima, su ogni
    forma di file: se cambiasse, una posa gia' in archivio diventerebbe un'altra. Comprese le
    primarie su cui astropy e la strada veloce non concordano -- l'END perso, `NAXIS` ripetuto --
    dove decide la strada veloce, come ha sempre deciso."""
    bench, _, _ = _bench(tmp_path)

    def two_pages(name):
        path = tmp_path / name
        fits.HDUList([fits.PrimaryHDU(), fits.ImageHDU(np.ones((40, 40), np.int16))]).writeto(path)
        return path

    bench["mef_primary_no_end"] = _rewrite(two_pages("m0.fits"), _card("END"), _card(""))
    # una primaria che ripete NAXIS: astropy prende il primo (niente pixel), la strada veloce
    # l'ultimo; decide la strada veloce, come ha sempre deciso l'impronta
    repeated = tmp_path / "m9.fits"
    primary = fits.PrimaryHDU()
    primary.header["SEGNAPO1"] = "x"
    primary.header["SEGNAPO2"] = "y"
    fits.HDUList([primary, fits.ImageHDU(np.ones((40, 40), np.int16))]).writeto(repeated)
    _rewrite(repeated, _card("SEGNAPO1= 'x       '"), _card("NAXIS   =                    1"))
    bench["primary_repeats_naxis"] = _rewrite(
        repeated, _card("SEGNAPO2= 'y       '"), _card("NAXIS1  =                    0")
    )
    # un'estensione con una card strutturale rovinata: astropy la legge lo stesso, a modo suo
    broken = {
        "ext_naxis_negative": ("NAXIS1  =                   40", "NAXIS1  =                   -5"),
        "ext_odd_bitpix": ("BITPIX  =                   16", "BITPIX  =                   17"),
        "ext_pcount_text": ("PCOUNT  =                    0", "PCOUNT  =                'abc'"),
        "ext_gcount_zero": ("GCOUNT  =                    1", "GCOUNT  =                    0"),
    }
    for i, (name, (old, new)) in enumerate(broken.items(), start=1):
        path = two_pages(f"m{i}.fits")
        raw = path.read_bytes()
        # nell'estensione, non nella primaria
        at = raw.index(old.encode("ascii"), header_read.BLOCK)
        path.write_bytes(raw[:at] + new.encode("ascii") + raw[at + len(old) :])
        bench[name] = path
    for name, path in bench.items():
        read = _outcome(header_read.read_frame, str(path))
        if not isinstance(read, tuple):
            continue  # un file che non si legge non ha impronta
        header, block = read
        before = _outcome(lambda p, h=header: frame_fingerprint(p, h), str(path))
        now = _outcome(lambda p, h=header, b=block: frame_fingerprint(p, h, b), str(path))
        assert now == before, name


def test_the_fingerprint_does_not_change(tmp_path):
    """Un file gia' in archivio si riconosce dall'impronta: la strada nuova non ne cambia
    nessuna."""
    bench, simple, _ = _bench(tmp_path)
    for name in simple:
        path = str(bench[name])
        start, span = _astropy(path)
        chunk = b""
        if span:
            with open(path, "rb") as f:
                f.seek(start + max(0, (span - header_read.FINGERPRINT_BYTES) // 2))
                chunk = f.read(header_read.FINGERPRINT_BYTES)
        header = read_header(path)
        dims = f"{header.get('NAXIS1')}x{header.get('NAXIS2')}:{header.get('BITPIX')}".encode()
        # senza pixel da leggere l'impronta ripiega sull'header, come dice `frame_fingerprint`
        body = chunk or header.tostring().encode("ascii", "replace")
        assert frame_fingerprint(path, header) == hashlib.sha256(dims + body).hexdigest(), name


def test_a_simple_file_does_not_need_astropy(tmp_path, monkeypatch):
    """Il caso comune -- una pagina con pixel, non compressa, con END -- si legge dai blocchi: e'
    la strada veloce, e senza di lei la scansione paga astropy su ogni file nuovo."""
    bench, simple, _ = _bench(tmp_path)
    expected = {n: _astropy(str(bench[n])) for n in simple}

    def forbidden(*_args, **_kwargs):
        raise AssertionError("fits.open chiamato su un file semplice")

    monkeypatch.setattr(header_read.fits, "open", forbidden)
    for name in simple:
        assert _data_block(str(bench[name])) == expected[name], name


def test_every_other_file_goes_through_astropy(tmp_path, monkeypatch):
    """Tutto il resto lo decide astropy: la strada veloce si ritira, non stima -- un END scritto
    storto, `PCOUNT`/`GCOUNT`, i gruppi, un `BITPIX` o una `NAXISn` fuori regola."""
    bench, _, others = _bench(tmp_path)
    calls = []
    real = header_read.fits.open

    def counted(*args, **kwargs):
        calls.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(header_read.fits, "open", counted)
    for name in sorted(others):
        calls.clear()
        _outcome(_data_block, str(bench[name]))
        assert calls, name
