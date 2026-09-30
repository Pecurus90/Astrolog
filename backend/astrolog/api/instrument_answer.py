"""La risposta su **uno strumento**: la sua scheda, o l'unione con un altro.

Sta in un modulo suo perche' la stessa unione arriva da **due pagine** -- l'Attrezzatura e la
domanda "sono lo stesso pezzo?" di *Da confermare* -- e due strade vorrebbero dire due verita'
sullo stesso pezzo: le pose rimesse in coda solo per chi passa dal posto giusto.

Vincolo non ovvio: **i campi di una scheda li decide il genere, e lo decide qui** -- non la
pagina. Il browser non e' l'unico che chiama queste rotte, e lo schema ferma solo quattro campi su
tredici: gli altri li scriverebbe in silenzio, e una montatura nascerebbe con l'apertura di un
telescopio.
"""

from fastapi import HTTPException

from ..spine import declarations as decl
from ..spine import gear
from ..spine import unfiltered as unfiltered_reader

# La scheda di ogni tipo di pezzo: **si chiede solo cio' con cui l'app fa un conto**
# (`docs/coda.md`, 7/9/2026). Rapporto focale, lato del sensore e scala non ci sono mai: si
# derivano. Il colore e il pixel della camera sono `decl.CAMERA_SPECS` e non una copia, perche' sono
# gli stessi due campi che la scheda scrive fra le dichiarazioni.
_COMMON = ("brand", "model")
_ON_EVERY_PIECE = ("weight_kg", "notes")
CARD = {
    kind: (*_COMMON, *own, *_ON_EVERY_PIECE)
    for kind, own in {
        "optics": ("aperture_mm", "focal_mm"),
        "camera": decl.CAMERA_SPECS,
        "mount": ("payload_kg",),
        "reducer": ("reducer_factor",),
        "filter_wheel": ("slots",),
        "guide_scope": (),
        "guide_camera": (),
        "focuser": (),
    }.items()
}


class FieldNotOfKindError(ValueError):
    """Un campo che la scheda di quel genere non chiede. Chi espone la rotta lo traduce in 422."""

    def __init__(self, kind, fields):
        super().__init__(f"{kind} non ha {', '.join(fields)}")
        self.fields = fields


def of_the_kind(kind, fields):
    """Solo i campi che la scheda di **quel genere** chiede.

    **Si rifiuta, non si scarta**: un campo che quel genere non ha e' uno sbaglio di chi chiama, e
    ingoiarlo vorrebbe dire una risposta accettata che non ha fatto quello che diceva."""
    # `kind`, `name` e `merge_into` non sono campi di scheda: dicono **quale** pezzo e come
    # si chiama, e valgono per tutti i generi.
    fuori = sorted(set(fields) - {"kind", "name", "merge_into", *CARD[kind]})
    if fuori:
        raise FieldNotOfKindError(kind, fuori)
    return fields


def refused(err):
    """Il rifiuto come lo legge una pagina: un codice, non una frase. Sta qui perche' lo traducono
    tre rotte, e tre traduzioni della stessa eccezione divergono al primo campo aggiunto."""
    return HTTPException(
        status_code=422, detail={"code": "field_not_of_kind", "fields": err.fields}
    )


def answer(conn, instrument_id, edit, now):
    """La scheda corretta, o l'unione con un altro pezzo. Torna le pose da rimettere in coda."""
    if edit.merge_into is not None:
        return merge(conn, instrument_id, edit.merge_into, now)
    colour_before = _colour(conn, instrument_id)
    kind = _kind(conn, instrument_id)  # None: e' `declare_instrument` ad alzare il LookupError
    scheda = edit.model_dump(exclude_none=True)
    if kind is not None:
        of_the_kind(kind, scheda)
    if not gear.declare_instrument(conn, instrument_id, scheda, now):
        return set()
    # Il colore della scheda e' anche la risposta sulle pose che non dicono il filtro, ma tornano
    # in coda **solo se cambia**: "mono" su una camera gia' trattata da mono non sposta niente, e
    # sull'archivio vero erano 6.558 pose rifatte per 0 cambiate.
    if edit.camera_type is not None and _colour(conn, instrument_id) != colour_before:
        return set(unfiltered_reader.requeue(conn, instrument_id))
    return set()


def merge(conn, instrument_id, into_id, now):
    """L'unione di due grafie. Torna le pose da rimettere in coda."""
    requeued = set(gear.merge_instrument(conn, instrument_id, into_id, now))
    # la risposta della camera assorbita passa alla tenuta: le sue pose la devono sentire
    requeued.update(unfiltered_reader.requeue(conn, into_id))
    return requeued


def _kind(conn, instrument_id):
    row = conn.execute("SELECT kind FROM instruments WHERE id = ?", (instrument_id,)).fetchone()
    return None if row is None else row["kind"]


def _colour(conn, instrument_id):
    """Se quel pezzo e' una camera che l'app tratta a colori: lo stesso fatto che legge `normalize`
    (`unfiltered.is_colour`), letto per id -- la risposta puo' anche rinominarla."""
    row = conn.execute(
        "SELECT kind, name FROM instruments WHERE id = ?", (instrument_id,)
    ).fetchone()
    return (
        row is not None
        and row["kind"] == "camera"
        and unfiltered_reader.is_colour(conn, row["name"])
    )
