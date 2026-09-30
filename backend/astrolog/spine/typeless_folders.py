"""Le cartelle della domanda sul tipo di file, scritte: Da confermare le legge
(`typeless.by_folder`) invece di comporre la cartella di ogni posa senza tipo a ogni apertura.

Le riscrive chi cambia cio' che contano: la fine della scansione, il ritiro e la riattivazione di
una cartella (lo stacco, `typeless_answer.detach_waiting`), la fine del cielo, che decide chi il
cielo non sa dire, e la fine della normalizzazione, che trova le copie. Una risposta no: non cambia
quante pose conta la sua cartella, e la risposta si legge dalla sua casa.
A meta' giro la pagina puo' essere indietro di uno stadio, come l'Attrezzatura.
"""

from ..astap import NO_STARS
from ..db.replace_table import replace_rows
from ..fits.frame_type import UNKNOWN
from . import frame_folder as folder
from . import typeless

# Per cartella: quanti frame senza tipo, e quanti il cielo non sa dire -- ha rinunciato, ma non
# perche' mancano le stelle (quelli sono calibrazioni, e non si chiedono). Il `+` davanti a
# `sv.stage` tiene la query sull'indice del tipo di file: senza, parte dagli stadi e scorre tutti i
# frame anche in un archivio dove nessuno e' senza tipo.
_BY_FOLDER = f"""
SELECT {folder.COLUMNS}, SUM(f.copy_of IS NULL) AS n,
       SUM(sv.status = 'failed' AND IFNULL(sv.reason, '') <> '{NO_STARS}') AS undecided
FROM frames f {folder.JOIN}
JOIN frame_stages sv ON sv.frame_id = f.id AND +sv.stage = 'solve'
WHERE f.image_type = '{UNKNOWN}'
GROUP BY root, sub
"""  # noqa: S608 - un frammento costante di questo file, non un valore dell'utente

_COLUMNS = ("key", "root", "sub", "frames", "position")


def write(conn):
    """Riscrive tutte le cartelle della domanda. Una cartella dove il cielo sa dire di ogni posa e
    nessuno ha risposto non chiede niente, e non si scrive."""

    def silent(r):
        key = folder.folder_key(r["root"], r["sub"])
        return not r["undecided"] and typeless.answer(conn, key) is None

    groups = folder.counted(conn, _BY_FOLDER, skip=silent)
    rows = [(g["key"], g["root"], g["sub"], g["frames"], i) for i, g in enumerate(groups)]
    replace_rows(conn, "typeless_folders", _COLUMNS, rows)
