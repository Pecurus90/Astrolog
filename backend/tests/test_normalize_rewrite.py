"""Il marchio di riscrittura: questo file dice di non essere uscito cosi' dalla camera.

Il marchio guarda le CHIAVI dell'header e il vocabolario dei quattro, mai un nome nuovo: non
aggiunge nessun software supportato. Le due chiavi di stato vengono da una convenzione pubblica
-- `CALSTAT` = stato di calibrazione (B/D/F: bias, dark, flat applicati) e `SWMODIFY` =
"software that modified the file" -- documentata da Diffraction Limited in *FITS File Header
Definitions*, l'aiuto di MaxIm DL.  <!-- software-ok: e' la fonte, non un software supportato -->

La regola sta nella spina (`spine/rewrite`) e non in `fits` per una ragione sola: dire se due
grafie sono lo stesso programma lo sa il vocabolario, e `fits` non puo' consultarlo.
"""

import pytest

from astrolog.spine.rewrite import rewrite_mark

# Lo stato di calibrazione: ogni valore che l'header puo' portare, e cosa deve rispondere
# **ognuna** delle due chiavi. Le due convenzioni sono diverse -- `CALSTAT` e' un codice di
# lettere (B bias, D dark, F flat), `CALIBRAT` un si'/no -- e la stessa parola dice il
# contrario nelle due: `F` e' il flat per una e il falso del FITS per l'altra.
# Si prova ogni valore su TUTTE E DUE, e la tabella e' il punto: le due inversioni trovate in
# revisione (`'F'` letto come flat su `CALIBRAT`, il logico non quotato perso su `CALSTAT`)
# erano celle provate su una chiave sola, e la suite restava verde.
STATO = [
    ("numero acceso", 1, True, True),
    ("numero a zero", 0, False, False),
    ("numero acceso fra apici", "'1'", True, True),
    ("numero a zero fra apici", "'0'", False, False),
    ("logico si'", True, True, True),
    ("logico no", False, False, False),
    ("logico si' fra apici", "'T'", True, True),
    ("logico no fra apici", "'F'", True, False),  # per CALSTAT la F e' il flat
    ("parola di si'", "YES", True, True),
    ("le tre lettere", "BDF", True, False),
    ("una lettera", "D", True, False),
    ("la lettera del flat", "F", True, False),
    ("lettere con gli spazi", "B D F", True, False),
    ("lettere fra apici", "'BDF'", True, False),
    ("lettere coi trattini", "B-D-F", True, False),
    ("lettere con gli underscore", "B_D_F", True, False),
    ("lettera fuori convenzione", "BDX", False, False),
    ("lettere con le virgole", "B,D,F", False, False),
    ("parola di rifiuto", "FALSE", False, False),
    ("frase di rifiuto", "NOT CALIBRATED", False, False),
    ("rifiuto in una parola", "uncalibrated", False, False),
    ("niente", "None", False, False),
    ("vuoto", "", False, False),
    ("solo spazi", "   ", False, False),
    ("parola muta", "OK", False, False),
]


@pytest.mark.parametrize(
    "valore, calstat, calibrat", [r[1:] for r in STATO], ids=[r[0] for r in STATO]
)
def test_the_two_state_keys_read_every_kind_of_value(valore, calstat, calibrat):
    """Un marchio dove non ci vuole e' peggio di nessun marchio: `calibrated` e' il grado piu'
    pesante, quindi un grezzo che dichiara di NON essere calibrato perderebbe contro qualunque
    gemello, e le sue ore andrebbero alla copia."""
    assert (rewrite_mark({"CALSTAT": valore}) == "calibrated") is calstat
    assert (rewrite_mark({"CALIBRAT": valore}) == "calibrated") is calibrat


def test_a_state_key_that_is_absent_says_nothing():
    """La chiave che non c'e' non e' un no travestito da si': e' il caso normale."""
    assert rewrite_mark({"CALSTAT": None}) is None
    assert rewrite_mark({"CALIBRAT": None}) is None


def test_two_programs_named_together_are_a_mark():
    """Uno ha scattato, l'altro ha riscritto: due nomi che il vocabolario chiama in due modi
    sono il marchio, e il nome di chi elabora non serve conoscerlo."""
    assert rewrite_mark({"SWCREATE": "N.I.N.A. 3.1", "PROGRAM": "Elab 1.9"}) == "rewritten"
    assert rewrite_mark({"CREATOR": "ZWO ASIAIR Plus", "PROGRAM": "Elab 2"}) == "rewritten"


def test_the_key_of_who_wrote_the_file_is_read_wherever_it_is():
    """Si guardano tutte le chiavi, non la prima di ogni famiglia: chi riprende occupa quella
    che vuole -- Voyager scrive `PROGRAM`, SGP `SWMODIFY` -- e chi elabora ci mette la propria
    accanto. Fermandosi alla prima, la copia di quel grezzo tornava a somigliargli."""
    assert rewrite_mark({"PROGRAM": "Voyager 2.3", "SWMODIFY": "Elab 1.9"}) == "rewritten"
    assert rewrite_mark({"SWMODIFY": "SGPro 4.4", "PROGRAM": "Elab 1.9"}) == "rewritten"


def test_two_spellings_of_the_same_program_are_not_a_mark():
    """E' il vocabolario a dire se sono lo stesso programma, mai la somiglianza fra le
    stringhe: `SGPro 4.4` e `Sequence Generator Pro` non si somigliano affatto e sono lo
    stesso, come `NINA` e `N.I.N.A.`. Chi lo decideva a occhio marchiava il grezzo di chi
    riprende con quei due, e in un caso lo faceva passare per copia del file elaborato."""
    assert (
        rewrite_mark({"SWCREATE": "Sequence Generator Pro v4.4", "SWMODIFY": "SGPro 4.4"}) is None
    )
    assert rewrite_mark({"SWCREATE": "N.I.N.A. 3.1.2.9001 (x64)", "PROGRAM": "NINA"}) is None
    assert rewrite_mark({"SWCREATE": "Voyager", "PROGRAM": "voyager"}) is None


def test_one_program_alone_is_not_a_mark():
    """Un nome solo non dice niente, in qualunque chiave stia: `PROGRAM` e `SWMODIFY` sono le
    grafie con cui due dei quattro si presentano, e prenderle per un marchio vorrebbe dire
    marchiare il loro grezzo. Chi riscrive l'header da capo e perde per strada chi ha
    acquisito resta riconoscibile dall'altro criterio: il suo nome non e' fra i quattro."""
    assert rewrite_mark({"PROGRAM": "Voyager 2.3"}) is None
    assert rewrite_mark({"SWMODIFY": "SGPro 4.4"}) is None
    assert rewrite_mark({"PROGRAM": "Elab 1.9"}) is None


def test_two_names_that_nobody_recognizes_are_not_a_mark():
    """Due nomi fuori dai quattro possono essere due programmi o due grafie dello stesso: non
    lo sa nessuno, e non si indovina. E' il caso dichiarato aperto in coda."""
    assert rewrite_mark({"SWCREATE": "Elab 1.9", "PROGRAM": "Altro 2"}) is None


def test_two_keys_of_who_took_the_shot_are_not_a_mark():
    """Che siano due programmi non lo dice nessuno, e in casa non c'e' un header vero che le
    porti tutte e due (misurato: zero file su 14.148 dell'archivio di collaudo)."""
    assert rewrite_mark({"SWCREATE": "N.I.N.A. 3.1", "CREATOR": "ZWO"}) is None


def test_a_header_that_says_nothing_has_no_mark():
    """Il caso normale: una posa appena scattata non porta nessuna delle due chiavi."""
    assert rewrite_mark({"SWCREATE": "N.I.N.A. 3.1.2.9001 (x64)", "IMAGETYP": "LIGHT"}) is None
    assert rewrite_mark({}) is None
