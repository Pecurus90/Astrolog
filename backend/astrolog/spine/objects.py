"""Gli oggetti dell'archivio in lettura: **come si chiamano**, e chi ci sta attaccato.

Sta qui e non nello store di uno stadio perche' lo leggono in tanti -- la pagina Da confermare
oggi, l'Archivio, `group` e gli export domani -- e il contratto vieta a uno stadio di importare
da un altro. Un fatto, una casa: chi scrive gli oggetti e' `identify`, chi li legge e' questo.

Vincolo non ovvio: **il nome di un oggetto non e' una colonna, sono due passi.** Il primario di
`object_names` se c'e'; se non c'e', il nome che il catalogo da' al suo `catalog_slug`. Il
secondo caso non e' teorico: un oggetto di catalogo nasce senza nomi propri quando la sigla e
il nome comune erano gia' di altri (110 voci del catalogo si spartiscono 42 nomi comuni, e un
oggetto nato prima che il catalogo fosse caricato puo' essersi preso una sigla). Ricavare il
nome con un `JOIN` naturale mostrerebbe una scheda vuota proprio li' -- il caso piu' raro e
piu' difficile da vedere. I tre invarianti stanno in `docs/domini/spina.md`.

E i conteggi filtrano `copy_of IS NULL`: una copia riscritta non e' un'altra ora di cielo. Le
**ore** sono la somma del tempo delle pose, in secondi (`integration_s`), e una posa che il tempo
non lo dice non vale zero: non entra nella somma e si conta a parte (`untimed`), cosi' "non lo
sappiamo" e "zero ore" restano due cose diverse. Si somma in SQL, accanto al conteggio che c'e'
gia': tirar fuori le pose per sommarle in Python vorrebbe dire centomila righe per un numero.
"""

from . import counts

# Le due colonne che `display_name` legge, sull'oggetto `o`: chi vuole un nome le prende da qui.
NAME_COLUMNS = """
       (SELECT n.name FROM object_names n
         WHERE n.object_id = o.id AND n.is_primary = 1) AS primary_name,
       (SELECT e.name FROM catalog_entries e WHERE e.slug = o.catalog_slug) AS catalog_name"""

# Quante pose, quanto tempo, e quante non lo dicono: la casa e' `counts`. Ogni conto legge le pose
# dell'oggetto dall'indice `frames_object`, che le porta con cio' che serve a contarle.
_LIST = f"""
SELECT o.*, {NAME_COLUMNS},{counts.counts_on("object")}
FROM objects o
"""  # noqa: S608 - frammenti costanti della spina

# Cosa ha trovato il cielo in una posa `f`, per i gruppi di Da confermare: l'oggetto, oppure uno
# dei due vuoti -- che non si confondono, perche' una posa che `identify` non ha ancora lavorato,
# che una risposta ha rimesso in coda o su cui si e' guastato non e' una posa in cui il cielo non
# ha trovato niente. Si guarda lo STATO prima dell'oggetto: una posa rimessa in coda, fallita o
# saltata tiene il vecchio `object_id`, e mostrarlo direbbe un oggetto che il cielo non ha detto.
# Il JOIN e' LEFT perche' una posa non esca mai dal conto del suo gruppo.
NOT_YET, NOT_FOUND = "not_yet", "not_found"
SUBJECT_JOIN = "LEFT JOIN frame_stages si ON si.frame_id = f.id AND si.stage = 'identify'"
SUBJECT = (
    f"CASE WHEN si.status IN ('pending', 'failed') THEN '{NOT_YET}'"
    f" WHEN si.status = 'skipped' OR f.object_id IS NULL THEN '{NOT_FOUND}' ELSE f.object_id END"
)
_NAMES = f"SELECT o.id, o.catalog_slug, o.identity_confidence, {NAME_COLUMNS} FROM objects o"  # noqa: S608


def display_name(row):
    """Come si chiama un oggetto: il suo nome primario, o quello che il catalogo da' al suo
    slug. `None` solo se non ha ne' l'uno ne' l'altro, che vuol dire un oggetto senza catalogo
    e senza nomi -- una riga che nessuno dovrebbe poter creare."""
    return row["primary_name"] or row["catalog_name"]


def counted(row):
    """Un oggetto come lo mostra chi lo elenca dentro qualcos'altro -- una notte, un corredo --
    con quanto pesa li' dentro. Sta qui perche' il nome di un oggetto e' gia' due passi, e
    comporlo a mano in ogni pagina sarebbe lo stesso nome scritto in due modi."""
    return {
        "key": stable_key(row),
        "name": display_name(row),
        "frames": row["frames"],
        "integration_s": row["integration_s"],
    }


def stable_key(row):
    """La chiave con cui si parla di un oggetto da fuori: lo slug di catalogo, o il suo nome.

    **Mai l'id di riga.** Lo dice lo schema per le dichiarazioni (`entity_key` sopravvive ai
    reset del rilevato) e vale anche per la risposta che le crea: `identify` cancella gli oggetti
    rimasti senza pose e li rifa' da capo con numeri nuovi, quindi una risposta agganciata a un
    numero di riga punterebbe al nulla -- in silenzio."""
    return row["catalog_slug"] or display_name(row)


def label(row):
    """Il nome da scrivere a schermo: quello di `display_name`, o la chiave stabile per l'oggetto
    che un nome non ce l'ha -- a video una riga vuota non si legge."""
    return display_name(row) or stable_key(row)


# Gli oggetti delle pose di un gruppo -- un mosaico proposto, un pannello -- e come si scrivono
# insieme. Chi chiama sceglie il gruppo (`per`, sull'alias `f` delle pose) e da dove arrivano.
def subjects_sql(per, sorgente="frames f", where=""):
    """La domanda: una riga per (gruppo, oggetto), copie riscritte escluse; `where` e' un `AND ...`
    che stringe le pose. I doppi si tolgono **prima** di cercare il nome: dopo, lo si cercherebbe
    per ogni posa del gruppo. Le pose senza oggetto le scarta la giunzione: chiederlo anche dentro
    fa lasciare a SQLite l'indice di chi stringe, e l'Archivio scorrerebbe tutte le pose."""
    return f"""
SELECT s.gruppo, o.id, o.catalog_slug, {NAME_COLUMNS}
FROM (SELECT DISTINCT {per} AS gruppo, f.object_id FROM {sorgente}
      WHERE f.copy_of IS NULL {where}) s
JOIN objects o ON o.id = s.object_id
"""  # noqa: S608 - frammenti costanti di chi chiama


def subjects_of(righe):
    """`{gruppo: [nomi]}` dalle righe di `subjects_sql`, i nomi in ordine."""
    nomi = {}
    for r in righe:
        nomi.setdefault(r["gruppo"], set()).add(label(r))
    return {g: sorted(n) for g, n in nomi.items()}


def together(nomi):
    """I nomi di un gruppo come si leggono in una riga sola."""
    return ", ".join(nomi)


def count_subject(gruppo, subject, n):
    """Aggiunge `n` pose a cio' che il cielo ha trovato in quel gruppo (`SUBJECT` di una riga)."""
    conti = gruppo.setdefault("subjects", {})
    conti[subject] = conti.get(subject, 0) + n


def subjects(conn, gruppi):
    """I conti di `count_subject` diventano cio' che la pagina mostra: gli oggetti coi loro nomi,
    il piu' ripreso in cima, e le pose dei due vuoti. I nomi si leggono **una volta** per tutti i
    gruppi: gli oggetti di un archivio sono una manciata, i gruppi possono essere centinaia."""
    nomi = {r["id"]: label(r) for r in conn.execute(_NAMES)}
    for g in gruppi:
        conti = g.get("subjects", {})
        vuoti = (NOT_YET, NOT_FOUND)
        trovati = [{"name": nomi[s], "frames": n} for s, n in conti.items() if s not in vuoti]
        g["subjects"] = {
            "found": sorted(trovati, key=lambda t: (-t["frames"], t["name"])),
            "not_found": conti.get(NOT_FOUND, 0),
            "not_yet": conti.get(NOT_YET, 0),
        }
    return gruppi


def by_key(conn, key):
    """L'oggetto che porta quella chiave stabile, o `None`."""
    row = conn.execute(
        f"{_LIST} WHERE o.catalog_slug = ?"  # noqa: S608 - query costante di questo file
        " OR (o.catalog_slug IS NULL AND o.id IN"
        "     (SELECT object_id FROM object_names WHERE name = ? AND is_primary = 1))",
        (key, key),
    ).fetchone()
    return dict(row) if row else None


def listing(conn):
    """Tutti gli oggetti dell'archivio, ognuno col suo nome e quante pose ci stanno attaccate.

    Si legge intero, perche' gli oggetti sono molti meno delle pose: a pagine esce la risposta, non
    la lettura (`api/review.py`, gli oggetti gia' visti)."""
    return [dict(r) for r in conn.execute(_LIST)]


def identities(conn):
    """Tutti gli oggetti con cio' che li identifica -- la chiave, il nome, quanto e' sicuro -- senza
    contarne le pose: per chi li scorre e i numeri non li mostra."""
    return [dict(r) for r in conn.execute(_NAMES)]


def a_frame_of(conn, object_id):
    """Una posa dell'oggetto che abbia il cielo misurato, per ricalcolare i candidati.

    Una sola: le pose di uno stesso oggetto guardano lo stesso pezzo di cielo, e chiederne il
    cono per tutte sarebbe pagare N volte la stessa risposta."""
    row = conn.execute(
        "SELECT w.ra_deg, w.dec_deg, w.scale_arcsec_px, w.rotation_deg, w.width_deg, w.height_deg"
        " FROM frame_wcs w JOIN frames f ON f.id = w.frame_id"
        " WHERE f.object_id = ? ORDER BY f.id LIMIT 1",
        (object_id,),
    ).fetchone()
    return dict(row) if row else None


def frames_of(conn, object_id):
    """Gli id delle pose attaccate a un oggetto: sono quelle che una risposta rimette in coda."""
    return [r[0] for r in conn.execute("SELECT id FROM frames WHERE object_id = ?", (object_id,))]


def raw_names_of(conn, object_id):
    """Le grafie dell'header che sono finite su questo oggetto, come stanno nel file."""
    return [
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT object_raw FROM frames WHERE object_id = ? AND object_raw IS NOT NULL",
            (object_id,),
        )
    ]


def raw_names_with_objects(conn):
    """Ogni coppia (grafia dell'header, oggetto) dell'archivio, una volta sola.

    Serve a decidere se una risposta puo' diventare una **regola**: vale solo se quella grafia
    punta a un oggetto solo. Il confronto lo fa chi chiama, sulle grafie ripulite -- qui non si
    sa cosa sia una parola di tavolozza, e non deve saperlo. Le righe sono poche: una per grafia
    distinta, non una per posa."""
    return [
        (r["object_raw"], r["object_id"])
        for r in conn.execute(
            "SELECT DISTINCT object_raw, object_id FROM frames"
            " WHERE object_raw IS NOT NULL AND object_id IS NOT NULL"
        )
    ]
