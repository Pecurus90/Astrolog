"""Le risposte di Da confermare che si danno **per gruppo di frame**: con che corredo e quale
oggetto (per notte e valori dell'header), e che file sono (per cartella, `spine/frame_folder.py`).

Stanno insieme perche' hanno la stessa forma: il gruppo si controlla **prima** di scrivere, poi si
dichiara e si rimettono in coda i frame. Una risposta verso un gruppo che non chiede piu' niente e'
una pagina vecchia, e resterebbe li' per sempre senza che nessuno la veda: per questo LookupError,
che la rotta traduce in 404.
"""

from ..spine import declarations as decl
from ..spine import rig_optics, rigless, typeless, typeless_answer, unnamed


def answer_rigless(conn, edit, now, scelte):
    """ "Le pose di questo gruppo sono state riprese con questo corredo": si scrive la risposta
    sul gruppo e si rimettono in coda le sue pose. Torna quelle pose.

    Il gruppo si controlla **prima** di scrivere: uno su cui non c'e' nessuna posa da chiedere e'
    una pagina vecchia, e una risposta verso il nulla resterebbe li' per sempre senza che nessuno la
    veda. I pezzi nascono dai nomi al giro dopo (`normalize_rig.instrument_named`)."""
    riga = rigless.row_of(conn, edit.key)
    if riga is None:
        raise LookupError(f"gruppo {edit.key}")
    optics, camera, focal = rig_parts(edit, scelte)
    rigless.declare(conn, edit.key, optics, camera, focal, now)
    return rigless.requeue(conn, riga)


def answer_opticsless(conn, edit, now):
    """ "Con quella camera, a quella focale, l'ottica era questa": come per la camera, la domanda si
    controlla prima di scrivere, e le sue pose tornano in coda."""
    riga = rig_optics.row_of(conn, edit.key)
    if riga is None:
        raise LookupError(f"camera e focale {edit.key}")
    rig_optics.declare(conn, edit.key, edit.optics.strip(), now)
    return rig_optics.requeue(conn, riga)


def answer_unnamed(conn, edit, now):
    """ "Le pose senza nome di questo gruppo sono questo oggetto", o "non sono un oggetto": come per
    la camera, il gruppo si controlla prima di scrivere, e le sue pose tornano in coda."""
    riga = unnamed.row_of(conn, edit.key)
    if riga is None:
        raise LookupError(f"gruppo {edit.key}")
    unnamed.declare(
        conn, edit.key, slug=edit.slug, name=edit.name, not_an_object=edit.not_an_object, now=now
    )
    return unnamed.requeue(conn, riga)


def rig_parts(edit, scelte):
    """(ottica, camera, focale) della risposta: i pezzi del corredo scelto dall'elenco, o quelli
    scritti a mano. Si scrivono sempre i **nomi**: un'unione cancella la riga rilevata, e la
    dichiarazione deve sopravvivere a un azzeramento del rilevato.

    Un corredo che l'elenco non offre (`scelte`, da `review_page.rig_choices`) -- uno **senza
    camera** non risponde a questa domanda, ed e' proprio quello che queste pose hanno creato dal
    solo `TELESCOP` -- e' un bersaglio che non esiste, e si dice."""
    if edit.rig_id is None:
        return edit.optics, edit.camera, edit.focal_mm
    scelto = scelte.get(edit.rig_id)
    if scelto is None:
        raise decl.UnknownTargetError(f"corredo {edit.rig_id}")
    return scelto.optics, scelto.camera, scelto.focal_mm


def answer_typeless(conn, edit, now):
    """ "I frame di questa cartella sono foto del cielo", oppure "sono file di calibrazione": si
    scrive la risposta sulla cartella e, solo se sono foto del cielo, i frame tornano in coda --
    un file di calibrazione non ha un cielo da cercare. Torna i frame rimessi in coda."""
    riga = typeless.row_of(conn, edit.key)
    if riga is None:
        raise LookupError(f"cartella {edit.key}")
    typeless.declare(conn, edit.key, edit.kind, now)
    return typeless_answer.apply_answer(conn, {**riga, "answer": edit.kind}, now)
