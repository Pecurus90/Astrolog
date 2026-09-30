"""Le preferenze dell'utente, il timbro del primo avvio, e cio' che manca all'app per fare il
suo mestiere -- compreso **dove sta il riconoscitore**, che e' una preferenza e cio' che l'app
ne deduce.

Vincolo non ovvio: il primo avvio e' un TIMBRO, non un'euristica. "Sembra vuoto" tornerebbe
vero mesi dopo, dopo un azzeramento dell'archivio, e il wizard ricomparirebbe da solo davanti
a chi lo aveva gia' fatto. Le chiavi sono un elenco chiuso: il tipo e il valore di fabbrica
stanno in `db/config.py`, e qui si traduce solo un rifiuto in una risposta.
"""

from fastapi import APIRouter, Depends, HTTPException

from ..clock import now_iso
from ..db import config
from ..db.transaction import transaction
from ..spine.group import NO_ACTIVE_SITE
from ..spine.solve import (
    NO_SOLVER,
    NO_STAR_DATABASE,
    databases_next_to,
    solver_found,
    solver_path,
    solver_where,
)
from .deps import get_db
from .models_site import Missing, SettingsOut, SettingsPatch, SolverOut

router = APIRouter(prefix="/api/v1", tags=["impostazioni"])


def _missing(conn) -> list[Missing]:
    """Cosa manca, con un codice e non una frase.

    Senza un luogo di casa l'app cataloga e cerca, ma le notti non nascono: una notte e'
    data-notte + luogo, e il fuso e' del luogo. Non se ne elegge uno da sola -- un luogo che
    nessuno ha detto e' un dato inventato.

    Senza il **solver** l'archivio si costruisce lo stesso -- i file entrano, i nomi si mettono
    in ordine, le ore si contano -- ma non si sa **cosa** hai ripreso. Dirlo qui e' cio' che
    permette al primo avvio di chiederlo prima che qualcuno aspetti invano una scansione che non
    riconoscera' niente."""
    manca: list[Missing] = []
    if conn.execute("SELECT 1 FROM sites WHERE is_default = 1").fetchone() is None:
        manca.append(NO_ACTIVE_SITE)
    percorso = solver_path(conn)
    if percorso is None:
        manca.append(NO_SOLVER)
    elif not databases_next_to(percorso):
        # Il catalogo si nomina **solo a chi ha il programma**: e' il catalogo di ASTAP, e due
        # allarmi per un problema solo mandano a cercare due cose invece di una. Si chiede col
        # percorso gia' in mano, non cercandolo un'altra volta: due ricerche nella stessa
        # risposta potrebbero dire due cose.
        manca.append(NO_STAR_DATABASE)
    return manca


def _out(conn):
    values = config.read(conn)
    values = {k: config.hint(v) if k in config.SECRETS else v for k, v in values.items()}
    return SettingsOut(
        values=values,
        wizard_done=values["onboarding_done_at"] is not None,
        missing=_missing(conn),
    )


@router.get("/settings", response_model=SettingsOut)
def read_settings(conn=Depends(get_db)):
    return _out(conn)


@router.patch("/settings", response_model=SettingsOut)
def write_settings(body: SettingsPatch, conn=Depends(get_db)):
    """Scrive le chiavi date. O passano tutte o non passa niente: meta' preferenze scritte
    sarebbe peggio di nessuna, e chi ha sbagliato una chiave non deve indovinare quali sono
    entrate."""
    unknown = sorted(k for k in body.values if k not in config.KEYS)
    if unknown:
        raise HTTPException(status_code=422, detail={"code": "unknown_setting", "keys": unknown})
    provate = sorted(k for k in body.values if k in config.TRIED_ELSEWHERE)
    if provate:
        raise HTTPException(status_code=422, detail={"code": "tried_elsewhere", "keys": provate})
    try:
        with transaction(conn):
            for key, value in body.values.items():
                config.write(conn, key, value)
    except ValueError as err:
        raise HTTPException(status_code=422, detail={"code": "wrong_type"}) from err
    return _out(conn)


def _solver(conn, dove):
    return SolverOut(
        path=dove[0],
        source=dove[1],
        declared=config.read(conn).get("astap_path"),
        databases=list(databases_next_to(dove[0])),
    )


@router.get("/solver", response_model=SolverOut)
def read_solver(conn=Depends(get_db)):
    """Dove l'app prende il riconoscitore, e da quale canale.

    Il percorso **dichiarato** esce sempre, anche quando non porta a niente: e' l'unica cosa che
    si puo' correggere, e nasconderlo lascerebbe una sezione che dice "non trovato" senza dire
    perche'."""
    return _solver(conn, solver_where(conn))


@router.post("/solver/search", response_model=SolverOut)
def search_solver(conn=Depends(get_db)):
    """*Cercalo tu*: cosa troverebbe l'app **ignorando la preferenza**.

    E' un POST perche' guarda il disco e il PATH della macchina, non perche' scriva: **non
    scrive niente**. Adottare la proposta e' un gesto dell'utente -- sovrascrivere di nascosto un
    percorso scritto a mano toglierebbe l'unica via d'uscita quando questa ricerca prende il
    programma sbagliato."""
    return _solver(conn, solver_found())


@router.post("/settings/wizard-done", response_model=SettingsOut)
def stamp_wizard(conn=Depends(get_db)):
    """Il primo avvio e' passato: completandolo o saltandolo, e' lo stesso timbro. Riaprire il
    wizard dalle Impostazioni non lo riscrive: la prima volta e' stata una sola."""
    if config.read(conn)["onboarding_done_at"] is None:
        with transaction(conn):
            config.write(conn, "onboarding_done_at", now_iso())
    return _out(conn)
