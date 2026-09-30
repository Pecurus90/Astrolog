"""Come si compone la pagina di Da confermare, sezione per sezione.

Le rotte stanno in `review.py`, cosa scrive una risposta in `review_write.py`. Qui c'e' solo
la lettura: ogni sezione arriva **gia' pronta per lo schermo** -- ordinata, coi conteggi
fatti e i candidati da cliccare gia' scelti -- perche' il frontend formatta e basta.

Vincolo non ovvio: i candidati del cielo li scrive chi identifica (`spine/object_candidates.py`),
perche' il cono sul catalogo costa; i filtri e i corredi fra cui scegliere e i luoghi vicini si
compongono qui da cio' che e' scritto, con una query o tre moltiplicazioni.
"""

from ..place import by_distance, distance_km
from ..spine import coordinates as places
from ..spine import declarations as decl
from ..spine import gear
from ..spine import objects as obj
from ..spine import rigs as corredi
from ..spine.group import SITE_UNCLEAR
from ..spine.identify_decide import DOUBT
from .models_review import FilterCandidate, ObjectCandidate, ObjectOut, RigChoice
from .models_review_groups import SiteCandidate, UnclearCoordinates


def filter_choices(conn):
    """I filtri fra cui si sceglie "uno dei tuoi" -- per i frame senza filtro, e per dire che un
    filtro che l'app non riconosce e' uno di questi: quelli con la banda nota, tranne la riga
    "nessun filtro", che e' un'altra risposta. Una casa sola per le tendine e per chi scrive la
    risposta: l'Applica non accetta come risposta un filtro che la tendina non offre."""
    righe = conn.execute("SELECT id, name, passband, is_none FROM filters ORDER BY name")
    return [
        FilterCandidate(id=r["id"], name=r["name"], passband=r["passband"])
        for r in righe
        if gear.filter_target(r)
    ]


def optics_choices(conn):
    """Le ottiche che hai, per nome: fra loro si risponde "quale ottica era". Si puo' scrivere anche
    un nome che non c'e', e il pezzo nasce."""
    righe = conn.execute(
        "SELECT name FROM instruments WHERE kind = 'optics' ORDER BY name COLLATE NOCASE"
    )
    return [r["name"] for r in righe]


# Le pose di ogni corredo, copie comprese: la tendina non chiede le ore, chiede chi e' usato.
USED_RIGS = "SELECT rig_id, COUNT(*) AS n FROM frames WHERE rig_id IS NOT NULL GROUP BY rig_id"


def rig_choices(conn):
    """I corredi fra cui si sceglie con che camera sono state riprese delle pose: quelli **con una
    camera** -- uno senza non risponde a quella domanda -- e con almeno una posa, anche solo una
    copia: uno rimasto senza nessuna e' un residuo di una risposta che ha spostato le sue pose. I
    piu' usati in cima. Una casa sola per la tendina e per chi scrive la risposta, come i filtri."""
    usati = {r["rig_id"]: r["n"] for r in conn.execute(USED_RIGS)}
    nomi = corredi.rig_names(conn)
    righe = [
        (key, r) for key, r in corredi.rigs_with_keys(conn) if r["camera"] and r["id"] in usati
    ]
    righe.sort(key=lambda kr: (-usati[kr[1]["id"]], kr[1]["id"]))
    return [
        RigChoice(
            id=r["id"],
            name=nomi.get(key),
            optics=r["optics"],
            camera=r["camera"],
            focal_mm=r["focal_mm"],
        )
        for key, r in righe
    ]


def object_still_open(conn, row):
    """Se quell'oggetto e' ancora una **domanda**: c'e' un dubbio **e** il cielo ha trovato
    qualcosa da cliccare.

    Si chiede **esattamente cio' che la pagina chiede** -- gli stessi candidati, dalla stessa
    funzione -- e non "ha una posa col cielo", che sembra la stessa domanda e non lo e': col
    cielo misurato ma **senza catalogo** (uno stato dichiarato supportato: l'app senza catalogo
    cataloga, cerca e conta le ore lo stesso) il cono non torna niente, e un oggetto resterebbe
    da confermare per sempre **senza niente da cliccare**. Il conto non tornerebbe piu' a zero,
    che e' la promessa che questa regola esiste per proteggere.

    Il dubbio da solo non basta per la ragione opposta: finche' ASTAP non e' installato le pose
    non hanno cielo e **ogni** oggetto nasce dubbio, e il contatore resterebbe acceso su un
    archivio dove nessuna domanda e' mai comparsa a schermo."""
    return row["identity_confidence"] == DOUBT and bool(_sky_candidates(conn, row["id"]))


def unclear_coordinates(conn):
    """I posti su cui l'app ha fermato delle pose, coi luoghi dichiarati da cliccare -- il piu'
    vicino a QUELLE coordinate in cima, che e' quasi sempre la risposta giusta.

    Le distanze si ricalcolano alla lettura: sono tre moltiplicazioni, e uno stato salvato
    invecchierebbe al primo luogo nuovo."""
    posti = places.unclear_coordinates(conn, SITE_UNCLEAR)
    if not posti:
        return []
    luoghi = conn.execute("SELECT id, name, latitude, longitude, is_default FROM sites").fetchall()
    casa = next((s for s in luoghi if s["is_default"]), None)
    out = []
    for posto in posti:
        # Un luogo senza coordinate non e' un candidato: non si saprebbe dove metterlo
        # nell'ordine, e proporlo per primo o per ultimo sarebbe inventare.
        # Si ordina sulla distanza VERA, e i modelli si costruiscono dopo: `SiteCandidate` la
        # arrotonda a cio' che lo schermo mostra, e ordinare gli arrotondati fa pareggiare due
        # luoghi a meno di cento metri l'uno dall'altro -- in cima finirebbe il piu' lontano,
        # a seconda di come il database restituisce le righe.
        vicini = [
            SiteCandidate(id=s["id"], name=s["name"], distance_km=quanto)
            for quanto, s in by_distance(posto["latitude"], posto["longitude"], luoghi)
        ]
        out.append(
            UnclearCoordinates(
                **posto,
                # Senza un luogo di casa non c'e' nessuna distanza da dire: il campo resta
                # vuoto. Uno zero sarebbe "sei a casa", che e' falso.
                distance_km=distance_km(
                    posto["latitude"], posto["longitude"], casa["latitude"], casa["longitude"]
                )
                if casa
                else None,
                candidates=vicini,
            )
        )
    out.sort(key=lambda n: -n.frames)
    return out


def objects(conn):
    """Gli oggetti dell'archivio divisi in due: `(aperti, gia' visti)`. Aperti sono quelli nuovi,
    che contano fra le cose da confermare, e quelli su cui c'e' qualcosa da cliccare, **i dubbi in
    cima**: chi apre la pagina deve vedere il lavoro, non scorrere per trovarlo. Gli altri sono gia'
    visti e senza niente da scegliere, e la pagina li legge a pagine (Marco, 27/9/2026).

    I candidati si leggono solo per quelli da decidere: gli altri non ne hanno di scritti."""
    confermati = decl.confirmed_keys(conn, "object")
    out = []
    for row in obj.listing(conn):
        nome = obj.display_name(row)
        chiave = obj.stable_key(row)
        dubbio = row["identity_confidence"] == DOUBT
        out.append(
            ObjectOut(
                id=row["id"],
                key=chiave,
                name=nome,
                slug=row["catalog_slug"],
                method=row["identity_method"],
                confidence=row["identity_confidence"],
                frames=row["frames"],
                integration_s=row["integration_s"],
                untimed=row["untimed"],
                confirmed=chiave in confermati,
                candidates=_sky_candidates(conn, row["id"]) if dubbio else [],
            )
        )
    out.sort(key=lambda o: (o.confidence != DOUBT, -o.frames, o.name or ""))
    # aperto: nuovo, o con qualcosa da cliccare -- i candidati ci sono solo dove `object_still_open`
    aperti, certi = [], []
    for o in out:
        (aperti if not o.confirmed or o.candidates else certi).append(o)
    return aperti, certi


def _sky_candidates(conn, object_id):
    """Cosa il cielo ha trovato nel campo di questo oggetto: e' cio' che si clicca per
    rispondere, e per il ramo "il cielo dice un'altra cosa" e' proprio la risposta al perche'.
    Li ha scritti chi identifica (`spine/object_candidates.py`): qui si leggono."""
    return [
        ObjectCandidate(
            slug=r["slug"],
            name=r["name"],
            common_name=r["common_name"],
            in_frame=None if r["in_frame"] is None else bool(r["in_frame"]),
        )
        for r in conn.execute(
            "SELECT slug, name, common_name, in_frame FROM object_candidates"
            " WHERE object_id = ? ORDER BY rank",
            (object_id,),
        )
    ]
