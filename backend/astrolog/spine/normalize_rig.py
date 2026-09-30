"""I pezzi e il corredo di una posa: chi nasce da un valore d'header, e come si mette insieme.

E' la meta' di `normalize` che guarda l'attrezzatura -- l'altra guarda i filtri -- e si cambia
per una ragione sola: come un grezzo diventa un pezzo. Lo store e' quello di `normalize`,
perche' questo modulo **e'** quello stadio (la stessa ragione di `camera_specs`, dichiarata nei
contratti di `backend/pyproject.toml`).
"""

from ..units import known_focal, same_focal
from ..vocab.software import telescope_is_mount
from . import counts, declarations, gear, gear_create, rig_optics
from . import rigs as corredi


def instrument_named(conn, kind, name, counts, now):
    """Il pezzo con quel nome, creato se non c'e': un nome che l'utente ha scritto fa nascere un
    pezzo come lo fa nascere un header (`spine/rigless.py`)."""
    if not name:
        return None
    instrument_id = gear.instrument_id(conn, kind, name)
    if instrument_id is None:
        instrument_id = gear_create.instrument(conn, kind, name, now, detected=True)
        counts["instruments"] += 1
    return instrument_id


def instrument_for(conn, kind, raw, counts, now):
    """Il pezzo dietro un valore d'header, creato se non c'e'. Il GENERE lo decide chi chiama.

    Nessuna lista di nomi di montatura, mai: il nome cambia da utente a utente (`EQMod Mount`
    e `ZWO AM3` sono tutti e due veri) e una lista invecchia. A dire che quel valore e' una
    montatura e' il **software** che ha scritto il file."""
    return instrument_named(conn, kind, declarations.instrument_name(conn, kind, raw), counts, now)


def instruments_on_frame(conn, frame, conti, now):
    """Gli strumenti che **la posa nomina addosso a se'**, per genere: `{genere: id}`, e `None`
    dove l'header tace. Il grezzo si chiama come il genere piu' `_raw`; i generi li elenca
    `counts.ON_THE_FRAME`, che e' la casa sola.

    **Stanno sulla posa e non sul corredo**: i file li legano al singolo scatto -- e' per questo
    che le loro ore si sanno, a differenza della montatura -- e infilarli nell'impronta di un
    corredo farebbe nascere un secondo corredo a chi cambia una ruota."""
    return {
        kind: instrument_for(conn, kind, frame[f"{kind}_raw"], conti, now)
        for kind in counts.ON_THE_FRAME
    }


def mount_for_frame(conn, frame, rig_id, software, counts, now):  # noqa: PLR0913
    """La montatura della posa. **Cio' che dici tu sul corredo vince**, per tutte le sue pose;
    dove taci, quella che il file nomina, se il software dice che `TELESCOP` e' la montatura.
    Quella del file **nasce comunque**: la tua parola sceglie cosa va sulla posa, non cancella un
    pezzo che i tuoi file nominano."""
    dal_file = (
        instrument_for(conn, "mount", frame["telescope_raw"], counts, now)
        if telescope_is_mount(software)
        else None
    )
    detta = corredi.declared_mount(conn, rig_id) if rig_id is not None else None
    return detta if detta is not None else dal_file


def rig_for_frame(conn, frame, buckets, counts, now, camera, detto, software, notte=None):  # noqa: PLR0913
    """Il corredo: ottica + camera a una focale. Senza ne' l'una ne' l'altra non c'e' corredo.

    **Con l'ASIAIR `TELESCOP` non e' l'ottica**: quel programma ci scrive la montatura, sempre, e
    l'ottica non la scrive da nessuna parte (misurato su 171 header di quattro utenti, 14/9/2026).
    Il pezzo nasce quindi `mount` e il corredo resta **senza ottica**: un corredo a cui manca un
    pezzo e' vero, uno con la montatura al posto dell'ottica e' falso. Il criterio e' il software,
    non il nome della montatura. Quale ottica fosse lo dici tu, una volta per camera e focale
    (`spine/rig_optics.py`), e la risposta vale per ogni posa che l'ottica non la nomina.

    `camera` e `detto` li porta chi ha gia' letto la risposta sul gruppo: l'ottica dichiarata
    **vince** comunque, e la focale dichiarata riempie quella che le pose non dicono, o il corredo
    che nasce qui resterebbe un gemello separato da quello rilevato. `notte` e' il corredo della
    notte (`night_rig.night_rigs`): riempie solo cio' che il file tace, e l'ottica solo se la focale
    della posa, quando c'e', e' la sua."""
    if telescope_is_mount(software):
        optics_id = None  # e' la montatura, e la scrive `mount_for_frame`
    else:
        optics_id = instrument_for(conn, "optics", frame["telescope_raw"], counts, now)
    camera_id = instrument_named(conn, "camera", camera, counts, now)
    focal = known_focal(buckets.get(frame["focal_mm_raw"], frame["focal_mm_raw"]))
    if detto is not None:
        optics_id = instrument_named(conn, "optics", detto["optics"], counts, now) or optics_id
        focal = focal if focal is not None else detto["focal_mm"]
    if (
        notte is not None
        and optics_id is None
        and (focal is None or same_focal(notte["focal_mm"], focal))
    ):
        optics_id = instrument_named(conn, "optics", notte["optics"], counts, now)
        focal = notte["focal_mm"] if focal is None else focal
    detta = rig_optics.declared(conn, camera, focal) if optics_id is None and camera else None
    if detta is not None:
        optics_id = instrument_named(conn, "optics", detta[1], counts, now)
    if optics_id is None and camera_id is None:
        return None
    rig_id, created = corredi.rig_for(conn, optics_id, camera_id, focal, now)
    counts["rigs"] += 1 if created else 0
    # Il corredo che nasce da una risposta prende il nome e la montatura dati a quello senza
    # ottica; uno che c'era gia' tiene la sua parola, e cio' che gli togli non torna.
    if detta is not None and created:
        corredi.carry_declarations(conn, detta[0], rig_id, now)
    return rig_id
