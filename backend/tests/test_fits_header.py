"""Il lettore dell'header: i campi escono grezzi ma tipati, con le catene di alias, e un file
rotto e' un errore tipato che si conta. Portato da old/ (52 casi) e adattato: il lettore non
normalizza piu' filtri e nomi (e' mestiere di vocab), quindi qui si asseriscono i grezzi."""

import json

import astropy.units as u
import numpy as np
import pytest
from astropy.coordinates import FK4, FK5, SkyCoord
from astropy.io import fits
from astropy.time import Time

from astrolog.fits.frame_type import says_calibrated
from astrolog.fits.header_fields import extract_fields
from astrolog.fits.header_keys import text
from astrolog.fits.header_read import (
    HeaderReadError,
    frame_fingerprint,
    header_from_json,
    header_to_json,
    read_header,
)
from astrolog.fits.header_wcs import solved, wcs_rotation_deg, wcs_scale


def read(path):
    return extract_fields(read_header(path), path)


CLEAN = {
    "OBJECT": "M 31",
    "EXPTIME": 300.0,
    "FILTER": "Ha",
    "TELESCOP": "SkyWatcher",
    "INSTRUME": "ASI2600",
    "GAIN": 100,
    "CCD-TEMP": -10.0,
    "OFFSET": 50,
    "FOCALLEN": 530.0,
    "XBINNING": 1,
    "DATE-OBS": "2024-01-10T22:00:00",
    "CRVAL1": 10.5,
    "CRVAL2": 41.2,
    "WCSAXES": 2,
}


def test_clean_header_fields(make_fits):
    m = read(make_fits("clean.fits", CLEAN))
    expected = {
        "object_raw": "M 31",
        "date_obs": "2024-01-10T22:00:00.000",
        "exposure_s": 300.0,
        "filter_raw": "Ha",
        "gain": 100.0,
        "offset": 50.0,
        "telescope_raw": "SkyWatcher",
        "instrument_raw": "ASI2600",
        "focal_mm": 530.0,
        "ccd_temp_c": -10.0,
        "naxis1": 4,
        "naxis2": 3,
        "binning": 1,
        "ra_deg": 10.5,
        "dec_deg": 41.2,
        "image_type": "unknown",
    }
    for field, value in expected.items():
        assert m[field] == value, field


def test_object_with_slash_is_not_truncated(make_fits):
    assert (
        read(make_fits("s.fits", {"OBJECT": "NGC 7000 / North America"}))["object_raw"]
        == "NGC 7000 / North America"
    )


def test_hierarch_cards_are_read(make_fits):
    assert read_header(make_fits("h.fits", {"HIERARCH ESO DET FOO": 42})).get("ESO DET FOO") == 42


@pytest.mark.parametrize(
    "header, ra, dec",
    [
        ({"CRVAL1": 83.633, "CRVAL2": 22.0}, 83.633, 22.0),
        ({"OBJCTRA": "05 34 32.0", "OBJCTDEC": "+22 00 52"}, 83.6333, 22.0144),
        ({"RA": 81.3784301863022, "DEC": 35.2739361702128}, 81.3784301863022, 35.2739361702128),
    ],
)
def test_coordinates_decimal_and_sexagesimal(make_fits, header, ra, dec):
    m = read(make_fits("c.fits", header))
    assert m["ra_deg"] == pytest.approx(ra, abs=1e-3)
    assert m["dec_deg"] == pytest.approx(dec, abs=1e-3)


def test_coordinates_out_of_range_are_none(make_fits):
    m = read(make_fits("o.fits", {"CRVAL1": 400.0, "CRVAL2": 95.0}))
    assert m["ra_deg"] is None and m["dec_deg"] is None


def test_decimal_with_unit_is_none_never_times_15(make_fits):
    assert read(make_fits("d.fits", {"CRVAL1": "83.633 deg"}))["ra_deg"] is None


def test_zero_zero_without_wcs_is_none_with_wcs_is_kept(make_fits):
    m = read(make_fits("z.fits", {"CRVAL1": 0.0, "CRVAL2": 0.0}))
    assert m["ra_deg"] is None and m["dec_deg"] is None
    m = read(make_fits("zw.fits", {"CRVAL1": 0.0, "CRVAL2": 0.0, "PLTSOLVD": True}))
    assert m["ra_deg"] == 0.0 and m["dec_deg"] == 0.0
    m = read(make_fits("r0.fits", {"CRVAL1": 0.0, "CRVAL2": 41.0}))
    assert m["ra_deg"] == 0.0 and m["dec_deg"] == 41.0


def test_jnow_equinox_is_precessed_to_icrs(make_fits):
    m = read(make_fits("j.fits", {"CRVAL1": 10.0, "CRVAL2": 41.0, "EQUINOX": 2025.5}))
    exp = SkyCoord(10.0 * u.deg, 41.0 * u.deg, frame=FK5(equinox=Time(2025.5, format="jyear"))).icrs
    assert m["ra_deg"] == pytest.approx(exp.ra.deg, abs=1e-4)
    assert m["dec_deg"] == pytest.approx(exp.dec.deg, abs=1e-4)
    assert m["ra_deg"] != pytest.approx(10.0, abs=1e-2)


def test_fk4_is_converted_and_j2000_untouched(make_fits):
    m = read(make_fits("f.fits", {"CRVAL1": 10.0, "CRVAL2": 41.0, "RADESYS": "FK4"}))
    exp = SkyCoord(10.0 * u.deg, 41.0 * u.deg, frame=FK4(equinox=Time(1950.0, format="byear"))).icrs
    assert m["ra_deg"] == pytest.approx(exp.ra.deg, abs=1e-4)
    for hdr in ({"EQUINOX": 2000.0}, {"RADESYS": "ICRS"}, {"RADESYS": "FK5", "EQUINOX": 2000.0}):
        m = read(make_fits("k.fits", {"CRVAL1": 10.0, "CRVAL2": 41.0, **hdr}))
        assert (m["ra_deg"], m["dec_deg"]) == pytest.approx((10.0, 41.0), abs=1e-6)


def test_galactic_wcs_becomes_equatorial_but_objctra_does_not(make_fits):
    m = read(
        make_fits(
            "g.fits", {"CRVAL1": 120.0, "CRVAL2": -15.0, "CTYPE1": "GLON-TAN", "CTYPE2": "GLAT-TAN"}
        )
    )
    exp = SkyCoord(l=120.0 * u.deg, b=-15.0 * u.deg, frame="galactic").icrs
    assert m["ra_deg"] == pytest.approx(exp.ra.deg, abs=1e-4)
    m = read(
        make_fits(
            "og.fits",
            {
                "OBJCTRA": "05 34 32.0",
                "OBJCTDEC": "+22 00 52",
                "CTYPE1": "GLON-TAN",
                "CTYPE2": "GLAT-TAN",
            },
        )
    )
    assert m["ra_deg"] == pytest.approx(83.6333, abs=1e-2)


@pytest.mark.parametrize(
    "raw, expected",
    [
        # le grafie misurate sull'archivio vero (N.I.N.A. e ASIAIR)
        ("LIGHT", "light"),
        ("Light", "light"),
        ("Light Frame", "light"),
        ("Dark Frame", "dark"),
        ("Bias Frame", "bias"),
        ("Flat Frame", "flat"),
        ("Flat Field", "flat"),
        ("DARK", "dark"),
        ("BIAS", "bias"),
        ("DARKFLAT", "dark_flat"),
        ("zero", "bias"),
        ("qualcosa", "unknown"),
        # e le grafie della stessa parola: separatore, maiuscole, plurale
        ("dark-flat", "dark_flat"),
        ("Dark Flat", "dark_flat"),
        ("dark_flat", "dark_flat"),
        ("DARK  FLAT", "dark_flat"),
        ("darks", "dark"),
        ("Flats", "flat"),
        ("BIASES", "bias"),
        ("lightframe", "light"),
        ("Light Frames", "light"),
    ],
)
def test_image_type_variants(make_fits, raw, expected):
    """La stessa parola si scrive in molti modi. Dei quattro software supportati abbiamo
    l'header vero solo di N.I.N.A. e ASIAIR (scrivono `DARK`): di Voyager e SGP no. Se una
    grafia non si riconosce, quel file di calibrazione entra in archivio come una posa del
    cielo -- ed e' successo, con `darkflat`."""
    assert read(make_fits("t.fits", {"IMAGETYP": raw}))["image_type"] == expected


def test_image_type_absent_is_unknown_never_light(make_fits):
    assert read(make_fits("n.fits", {"OBJECT": "M 1"}))["image_type"] == "unknown"


@pytest.mark.parametrize(
    "header",
    [
        {"IMAGETYP": "LIGHT", "NCOMBINE": 40, "EXPTIME": 36000.0},
        {"IMAGETYP": "LIGHT", "STACKCNT": 25},
        {"IMAGETYP": "LIGHT", "NIMAGES": 25},
        {"IMAGETYP": "Master Light"},
        {"OBJECT": "M 31 stacked", "IMAGETYP": "LIGHT"},
        {"OBJECT": "NGC 7000 integration", "IMAGETYP": "LIGHT"},
    ],
)
def test_stacks_are_unknown(make_fits, header):
    assert read(make_fits("st.fits", header))["image_type"] == "stack"


@pytest.mark.parametrize(
    "header",
    [
        {"IMAGETYP": "LIGHT", "NCOMBINE": 1},
        {"IMAGETYP": "LIGHT", "STACKCNT": 1},
        {"IMAGETYP": "LIGHT", "NIMAGES": "1"},
    ],
    ids=["NCOMBINE", "STACKCNT", "NIMAGES scritto come testo"],
)
def test_a_count_of_one_is_a_single_frame(make_fits, header):
    """Una chiave che conta i frame sommati dice "stack" solo quando ne conta piu' di uno: un
    file che dichiara di essere la somma di se stesso e' una posa, e non deve sparire."""
    assert read(make_fits("uno.fits", header))["image_type"] == "light"


def test_a_combined_file_is_not_a_frame(make_fits):
    """Chi non conta i frame sommati li **elenca**: la storia dell'header nomina i sorgenti.

    Misurato sull'archivio di collaudo: cinque integrazioni (la serie M83) si dichiaravano
    `LIGHT` proprio cosi', e senza questa riga diventavano cinque pose e una sessione mai
    esistita -- una notte in cui l'utente non era sotto il cielo."""
    m = read(
        make_fits(
            "comb.fits",
            {"IMAGETYP": "LIGHT", "OBJECT": "M83", "HISTORY": "SOURCE1 = 'M83_B_0001.fit'"},
        )
    )
    assert m["image_type"] == "stack"


def test_a_calibration_word_in_the_object_field_is_calibration(make_fits):
    """La seconda spia. Misurato sull'archivio di collaudo: 56 file di una libreria di
    calibrazione (bias e dark-flat) dicono `IMAGETYP = LIGHT` e `OBJECT = darkflat`, ed
    entravano in archivio come un oggetto del cielo chiamato "darkflat".

    Il confronto e' sull'intero campo, non su un pezzo: *Dark Nebula* non deve sparire."""
    for parola, atteso in (
        ("darkflat", "dark_flat"),
        ("Bias", "bias"),
        ("FLAT ", "flat"),
        ("dark flat", "dark_flat"),
        ("Darks", "dark"),
    ):
        m = read(make_fits(f"c{parola.strip()}.fits", {"IMAGETYP": "LIGHT", "OBJECT": parola}))
        assert m["image_type"] == atteso, parola


def test_an_object_that_merely_contains_a_calibration_word_is_a_frame(make_fits):
    """La guardia dell'altra meta': un oggetto vero non si perde perche' nel nome c'e' una
    parola che altrove vuol dire calibrazione."""
    for nome in (
        "Dark Nebula",
        "Flaming Star",
        "Barnard 33 dark",
        "Bias Ridge",
        "Dark-Nebula",  # nemmeno togliendo i separatori: si confronta il campo INTERO
        "Flat Iron",
    ):
        m = read(make_fits("o.fits", {"IMAGETYP": "LIGHT", "OBJECT": nome}))
        assert m["image_type"] == "light", nome


def test_a_calibrated_frame_is_still_a_frame(make_fits):
    """`CALSTAT` dice **calibrato**, non **sommato**: se fosse una spia di stack, a chi tiene
    le pose calibrate accanto alle originali sparirebbe meta' archivio. Fa un altro mestiere:
    e' il marchio di riscrittura, che vale solo fra due gemelli e non fa sparire niente."""
    m = read(make_fits("cal.fits", {"IMAGETYP": "LIGHT", "OBJECT": "M83", "CALSTAT": "BDF"}))
    assert m["image_type"] == "light"
    assert says_calibrated({"CALSTAT": "BDF"})  # l'altro mestiere della stessa chiave


def test_a_long_real_light_is_not_a_stack(make_fits):
    m = read(make_fits("l.fits", {"OBJECT": "M 31", "IMAGETYP": "LIGHT", "EXPTIME": 1200.0}))
    assert m["image_type"] == "light"


def test_solved_means_a_real_wcs(make_fits):
    """Un `CRVAL1` nudo non e' un cielo misurato: senza questa distinzione una coordinata di
    puntamento passerebbe per una soluzione. Lo chiede la scansione su ogni posa -- e' cosi'
    che il placeholder 0/0 diventa None -- e il solver sull'esito di ASTAP."""
    for hdr in ({"WCSAXES": 2}, {"CD1_1": 0.0002}, {"PLTSOLVD": True}):
        assert solved(read_header(make_fits("s.fits", hdr))) is True
    assert solved(read_header(make_fits("c.fits", {"CRVAL1": 180.0, "CRVAL2": 0.0}))) is False


def test_the_scale_comes_from_the_cd_matrix_or_from_cdelt(make_fits):
    """La scala dalla matrice: la legge il solver sull'esito di ASTAP. Quella da pixel e focale
    e' un'altra cosa e vive in `units` (la prova `test_solve_field_from_the_header`): nella
    scansione non si calcola nessuna delle due, perche' nessuno le scriveva da nessuna parte."""
    cd11, cd21 = 0.000402, 0.0000115
    header = read_header(
        make_fits("cd.fits", {"CD1_1": cd11, "CD1_2": 0.0, "CD2_1": cd21, "CD2_2": cd11})
    )
    assert wcs_scale(header) == pytest.approx((cd11**2 + cd21**2) ** 0.5 * 3600.0, abs=1e-4)
    assert wcs_scale(read_header(make_fits("dl.fits", {"CDELT1": -0.000402}))) == pytest.approx(
        0.000402 * 3600.0, abs=1e-4
    )
    # PIXSIZE1 e' di un software non supportato: non si legge, e la dimensione resta None
    assert read(make_fits("p.fits", {"PIXSIZE1": 3.76}))["pixel_size_um"] is None


def test_rotation_is_crota2_from_cd_matrix(make_fits):
    """La rotazione la legge il solver sull'esito di ASTAP. `OBJCTROT` non si legge mai: sui
    frame veri ha il segno opposto e vale zero come sentinella su meta' di essi."""
    header = read_header(
        make_fits("r.fits", {"CD1_1": 0.0, "CD1_2": -0.0004, "CD2_1": 0.0004, "CD2_2": 0.0})
    )
    assert wcs_rotation_deg(header) == pytest.approx(90.0)
    assert wcs_rotation_deg(read_header(make_fits("c.fits", {"CROTA2": -10.0}))) == pytest.approx(
        350.0
    )
    assert wcs_rotation_deg(read_header(make_fits("n.fits", {"OBJCTROT": 45.0}))) is None
    # `CD1_2` assente si legge 0 (WCS Paper I): la matrice c'e' e l'angolo e' zero, non ignoto
    assert wcs_rotation_deg({"CD1_1": 0.0004, "CD2_2": 0.0004}) == 0.0
    # matrice degenere (CD1_2 e CD2_2 entrambe nulle): l'angolo resta ignoto, e si ripiega su
    # CROTA2 invece di dichiarare uno zero che non e' stato misurato
    assert wcs_rotation_deg({"CD1_1": 0.0004, "CD1_2": 0.0, "CD2_2": 0.0, "CROTA2": 33.0}) == 33.0
    assert wcs_rotation_deg({"CROTA1": -10.0}) == pytest.approx(350.0)  # la grafia secondaria


def test_float32_noise_stops_at_the_reader_but_coordinates_keep_precision(make_fits):
    m = read(
        make_fits(
            "n.fits",
            {
                "XPIXSZ": 4.28999996185303,
                "CCD-TEMP": -10.1000003814697,
                "RA": 81.3784301863022,
                "DEC": 35.2739361702128,
            },
        )
    )
    assert m["pixel_size_um"] == 4.29 and m["ccd_temp_c"] == -10.1
    assert m["ra_deg"] == pytest.approx(81.3784301863022, abs=1e-10)


def test_site_and_bayer(make_fits):
    """Il luogo e la matrice di Bayer, con la guardia di intervallo: una latitudine di 95 gradi
    non esiste, e una matrice che non e' una delle sei non si inventa."""
    m = read(
        make_fits(
            "s.fits", {"SITELAT": 45.5, "SITELONG": 9.2, "SITEELEV": 120.0, "BAYERPAT": "RGGB"}
        )
    )
    assert (m["site_lat"], m["site_lon"], m["site_elev_m"]) == (45.5, 9.2, 120.0)
    assert m["bayer_pattern"] == "RGGB"
    m = read(make_fits("bad.fits", {"BAYERPAT": "XRGGB", "SITELAT": 95.0}))
    assert (m["bayer_pattern"], m["site_lat"]) == (None, None)


def test_date_obs_chain_and_mjd_fallback(make_fits):
    d = read(make_fits("m.fits", {"MJD-OBS": 60202.95}))["date_obs"]
    assert d is not None and d.startswith("2023-09-15")
    assert (
        read(make_fits("b.fits", {"DATE-OBS": "2024-01-10T22:00:00", "MJD-OBS": 60202.95}))[
            "date_obs"
        ]
        == "2024-01-10T22:00:00.000"
    )
    assert (
        # l'ora locale senza fuso non e' una data del DB (tutto in UTC): resta None
        read(make_fits("l.fits", {"DATE-LOC": "2024-01-10T23:00:00"}))["date_obs"] is None
    )


def test_software_raw_chain(make_fits):
    assert read(make_fits("a.fits", {"SWCREATE": "N.I.N.A. 3.1"}))["software_raw"] == "N.I.N.A. 3.1"
    assert (
        read(make_fits("b.fits", {"CREATOR": "ZWO ASIAIR Plus"}))["software_raw"]
        == "ZWO ASIAIR Plus"
    )
    assert (
        read(make_fits("c.fits", {"PROGRAM": "Elaborazione 1.9"}))["software_raw"]
        == "Elaborazione 1.9"
    )


def test_data_page_header_for_multi_hdu(tmp_path):
    p = tmp_path / "mef.fits"
    fits.HDUList(
        [
            fits.PrimaryHDU(),
            fits.ImageHDU(
                data=np.zeros((4, 4), dtype=np.int16),
                header=fits.Header({"OBJECT": "M 31", "EXPTIME": 300.0, "IMAGETYP": "LIGHT"}),
            ),
        ]
    ).writeto(p)
    m = read(str(p))
    assert (m["object_raw"], m["exposure_s"], m["image_type"]) == ("M 31", 300.0, "light")
    assert (m["naxis1"], m["naxis2"]) == (4, 4)


def test_missing_keys_give_none_and_defaults(make_fits):
    m = read(make_fits("bare.fits", {"OBJECT": "M 1"}))
    for field in (
        "ccd_temp_c",
        "ra_deg",
        "dec_deg",
        "telescope_raw",
        "instrument_raw",
        "filter_raw",
        "date_obs",
        "software_raw",
        "pixel_size_um",
        "site_lat",
        "exposure_s",
        "gain",
        "focal_mm",
        "bayer_pattern",
        "binning",
    ):
        assert m[field] is None, field


@pytest.mark.parametrize(
    "valore, atteso",
    [(1, 1), (2, 2), (0, None), ("due", None)],
    ids=["bin 1", "bin 2", "zero", "illeggibile"],
)
def test_the_binning_is_what_the_header_says_or_unknown(valore, atteso):
    """Un binning che l'header non dice non vale 1: vale "non si sa". Da lui dipende il pixel
    fisico della camera, e un 1 inventato lo sbaglierebbe proprio su chi riprende binnato."""
    assert extract_fields({"XBINNING": valore}, "x")["binning"] == atteso


def test_broken_files_raise_a_typed_error(tmp_path):
    with pytest.raises(HeaderReadError):
        read_header(str(tmp_path / "missing.fits"))
    bad = tmp_path / "garbage.fits"
    bad.write_bytes(b"this is not a FITS file at all\x00\xff" * 10)
    with pytest.raises(HeaderReadError):
        read_header(str(bad))


def test_giant_header_is_read_whole(tmp_path):
    hdr = fits.Header()
    hdr["OBJECT"] = "M 51"
    for i in range(600):
        hdr["COMMENT"] = f"filler card numero {i} per superare i 23040 byte"
    p = tmp_path / "giant.fits"
    fits.PrimaryHDU(data=np.zeros((2, 2), dtype=np.int16), header=hdr).writeto(p)
    assert read(str(p))["object_raw"] == "M 51"


# --- le catene di alias -----------------------------------------------------------------

# Le grafie **secondarie** di ogni catena, scritte a mano una per una: questa tabella NON si
# deriva da `KEYS`, o guarderebbe se stessa. E' la lezione della guardia sull'anonimato del
# corpus, che costruita dagli alias era cieca proprio sulla grafia che non conosceva.
# Troncare una catena non rompeva niente: sette grafie tolte, sette suite verdi -- cioe' un
# ASIAIR che perde guadagno e binning senza che nessuno se ne accorga.
ALIAS_SECONDARI = [
    ("DATE-AVG", "2024-05-17T21:00:00", "date_obs", "2024-05-17T21:00:00.000"),
    ("EXPOSURE", 120.0, "exposure_s", 120.0),
    ("GAINRAW", 100, "gain", 100.0),  # ASIAIR
    ("SET-TEMP", -10.0, "ccd_temp_c", -10.0),  # il setpoint: ripiego, non misura
    ("CCDXBIN", 2, "binning", 2),  # ASIAIR, SGP
    ("RA", 10.5, "ra_deg", 10.5),
    ("DEC", 41.2, "dec_deg", 41.2),
    ("CREATOR", "ASIAIR", "software_raw", "ASIAIR"),
    ("PROGRAM", "Voyager 2.3", "software_raw", "Voyager 2.3"),
    ("SWMODIFY", "SGPro 4.4", "software_raw", "SGPro 4.4"),
    ("ORIGIN", "Osservatorio", "software_raw", "Osservatorio"),
]


@pytest.mark.parametrize(
    "key, raw, field, expected", ALIAS_SECONDARI, ids=[r[0] for r in ALIAS_SECONDARI]
)
def test_every_secondary_spelling_reaches_its_field(key, raw, field, expected):
    """Ogni grafia secondaria di una catena deve arrivare al suo campo: e' l'unica ragione per
    cui la catena esiste. L'header porta SOLO quella grafia, come l'header vero di chi la
    scrive."""
    assert extract_fields({key: raw, "NAXIS1": 4, "NAXIS2": 3}, "x")[field] == expected


def test_the_historic_spellings_of_the_reference_system_are_read():
    """`RADECSYS` e `EPOCH` sono le grafie storiche di `RADESYS` e `EQUINOX`: se non si
    leggessero, un frame in FK4 o in coordinate apparenti entrerebbe con le sue coordinate
    prese per ICRS -- cioe' spostate di mezzo grado, in silenzio."""
    fk4 = extract_fields({"CRVAL1": 10.0, "CRVAL2": 41.0, "RADECSYS": "FK4"}, "x")
    assert fk4["ra_deg"] != pytest.approx(10.0, abs=1e-2), "RADECSYS non letto"
    jnow = extract_fields({"CRVAL1": 10.0, "CRVAL2": 41.0, "EPOCH": 2025.5}, "x")
    assert jnow["ra_deg"] != pytest.approx(10.0, abs=1e-2), "EPOCH non letto"


def test_the_first_value_of_a_chain_must_not_be_empty():
    """ "Primo valore **presente e non vuoto**": una chiave che c'e' ma e' vuota non deve
    zittire la grafia dopo di lei. N.I.N.A. scrive `DATE-OBS` sempre, anche vuota."""
    m = extract_fields({"DATE-OBS": "   ", "DATE-AVG": "2024-05-17T21:00:00"}, "x")
    assert m["date_obs"] == "2024-05-17T21:00:00.000"


def test_a_not_a_number_never_reaches_the_archive():
    """`NaN` e infinito non sono misure: un `CCD-TEMP = NaN` entrerebbe in archivio come NaN,
    e da li' nell'intestazione salvata -- dove rompe il JSON che la pagina deve leggere."""
    m = extract_fields({"CCD-TEMP": float("nan"), "EXPTIME": float("inf")}, "x")
    assert m["ccd_temp_c"] is None and m["exposure_s"] is None


def test_the_saved_header_is_always_valid_json():
    """L'intestazione intera si salva su ogni posa, e la pagina la deve poter leggere: un
    valore non serializzabile diventa testo. `json.dumps(nan)` scriverebbe `NaN`, che il
    lettore JSON di un browser rifiuta -- e a quel punto la scheda della posa non si apre."""
    # astropy rifiuta di SCRIVERE un NaN in un header, ma un file che ce l'ha si legge: e'
    # da li' che arriva. La card anomala si costruisce come la costruirebbe la lettura.
    header = {"OBJECT": "M 31", "CCD-TEMP": float("nan"), "FOCUSPOS": float("inf")}
    testo = header_to_json(header)
    assert json.loads(testo) == [["OBJECT", "M 31"], ["CCD-TEMP", "nan"], ["FOCUSPOS", "inf"]]


def test_the_saved_header_can_be_read_back(make_fits):
    """Chi rilegge l'header dal database non deve conoscerne il formato: `header_from_json` e'
    l'inverso, e torna un dizionario come quello che il lettore FITS da'. Le chiavi ripetute
    (`HISTORY`, `COMMENT`) collassano sull'ultima -- chi ha bisogno di tutte legge la lista."""
    header = read_header(make_fits("r.fits", {"OBJECT": "M 31", "EXPTIME": 300.0}))
    assert header_from_json(header_to_json(header))["OBJECT"] == "M 31"
    assert header_from_json('[["HISTORY", "prima"], ["HISTORY", "poi"]]') == {"HISTORY": "poi"}
    assert header_from_json(None) == {}  # una posa senza header salvato non fa esplodere nessuno


def test_the_container_keys_stay_out_of_the_combined_header(tmp_path):
    """In un file a pagina primaria vuota le due pagine si combinano, ma le chiavi che
    descrivono il **contenitore** (`BITPIX`, `NAXIS`, `XTENSION`...) restano quelle del
    primario: sono del file, non del frame. Se entrassero cambierebbe perfino la stringa delle
    dimensioni dentro l'impronta, e due frame diversi potrebbero coincidere."""
    primary = fits.PrimaryHDU()
    image = fits.ImageHDU(data=np.zeros((8, 4), dtype=np.int16))
    image.header["OBJECT"] = "M 31"
    p = tmp_path / "mef.fits"
    fits.HDUList([primary, image]).writeto(p)
    combinato = read_header(str(p))
    assert combinato["OBJECT"] == "M 31"  # cio' che descrive il FRAME arriva
    assert combinato["NAXIS"] == 0  # cio' che descrive il CONTENITORE resta del primario
    assert "XTENSION" not in combinato


def test_the_fingerprint_carries_the_dimensions_not_only_the_pixels(tmp_path):
    """L'impronta e' `sha256` delle **dimensioni** piu' 64 KB di pixel dal centro.

    Il caso che lo dimostra e' l'unico che isola le dimensioni: due immagini con gli stessi
    byte esatti ma di forma diversa (40x60 e 60x40, tutte a zero). I pixel non li distinguono
    -- solo le dimensioni -- e sono due frame diversi."""
    impronte = set()
    for righe, colonne in ((40, 60), (60, 40)):
        p = tmp_path / f"c{righe}x{colonne}.fits"
        fits.PrimaryHDU(data=np.zeros((righe, colonne), dtype=np.int16)).writeto(p)
        letto = read_header(str(p))
        assert (letto["NAXIS1"], letto["NAXIS2"]) == (colonne, righe)
        impronte.add(frame_fingerprint(str(p), letto))
    assert len(impronte) == 2, "due immagini di forma diversa non sono un frame solo"


def test_an_apostrophe_is_part_of_the_name(make_fits):
    """Gli apici che delimitano una stringa FITS li toglie astropy; togliere **tutti** gli
    apici mangiava le lettere dei nomi veri, e in archivio finiva `Barnards Loop`. Ce ne sono
    diversi in cielo: *Barnard's Loop*, *Hind's Variable Nebula*, *Baade's Window*."""
    for nome in ("Barnard's Loop", "Hind's Variable Nebula", "Baade's Window"):
        assert read(make_fits("o.fits", {"OBJECT": nome}))["object_raw"] == nome
    # e la coppia che AVVOLGE il valore si toglie ancora: un header letto come testo la porta
    assert text("'M 31'") == "M 31"
    assert text("''") is None


def test_the_site_out_of_range_is_dropped_never_corrected():
    """Un valore implausibile si scarta, mai si corregge: una latitudine di 95 gradi non
    esiste, e una longitudine di 400 nemmeno. L'altezza resta: e' plausibile."""
    m = extract_fields({"SITELAT": 95.0, "SITELONG": 400.0, "SITEELEV": 120.0}, "x")
    assert (m["site_lat"], m["site_lon"], m["site_elev_m"]) == (None, None, 120.0)
