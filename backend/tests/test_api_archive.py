"""L'Archivio: la rotta che racconta **cosa hai ripreso**, invece di chiedertene conto.

Le regole che questa rotta deve rispettare vengono tutte da decisioni gia' prese altrove -- le
copie non raddoppiano le ore, un frame senza tempo non vale zero, "non lo so" ha sempre accanto il
suo perche' -- e qui si prova che valgono anche da questa parte.
"""

from astrolog.db.connect import connect
from conftest import ORDINE_OSTILE


def archivio(client, **parametri):
    r = client.get("/api/v1/archive", params=parametri)
    assert r.status_code == 200, r.text
    return r.json()


def per_nome(risposta):
    return {o["name"]: o for o in risposta["items"]}


def test_repeating_a_criterion_is_either(client):
    """`?filter=a&filter=b`: passa chi ha l'uno o l'altro, e la conta e' quella della spina."""
    voci = {c["key"]: [o["value"] for o in c["options"]] for c in archivio(client)["criteria"]}
    assert len(voci["filter"]) >= 2, "l'archivio di prova ha un filtro solo: non guarda niente"
    primo, secondo = voci["filter"][:2]

    uno = archivio(client, filter=primo)["total"]
    tutti_e_due = archivio(client, filter=[primo, secondo])["total"]

    assert tutti_e_due >= uno > 0


def test_a_missing_solver_is_said_with_the_frames_it_leaves(client, db_path, monkeypatch):
    """Senza ASTAP i frame senza oggetto restano non risolti, e la rotta lo dice con loro."""
    with connect(db_path) as conn:
        conn.execute(
            "INSERT INTO frames(frame_hash, image_type, header_json, exposure_s, created_at)"
            " VALUES('senza-oggetto', 'light', '[]', 60.0, 'x')"
        )
        conn.commit()
    monkeypatch.setattr("astrolog.api.archive.solver_where", lambda _conn: (None, None))

    fuori = archivio(client)["unresolved"]

    assert fuori["frames"] >= 1
    assert fuori["solver_missing"] is True


def nome_di(conn, object_id):
    riga = conn.execute(
        "SELECT n.name FROM object_names n WHERE n.object_id = ? AND n.is_primary = 1",
        (object_id,),
    ).fetchone()
    return riga["name"] if riga else None


def un_oggetto_con_pose(conn):
    """Un oggetto dell'archivio di prova che abbia almeno una posa vera attaccata."""
    return conn.execute(
        "SELECT id, object_id, exposure_s FROM frames"
        " WHERE object_id IS NOT NULL AND copy_of IS NULL LIMIT 1"
    ).fetchone()


def test_the_archive_lists_what_you_shot(client):
    """La domanda della pagina e' una: cosa ho ripreso, e quanto. Ogni riga porta il nome gia'
    fatto dal backend, quante pose e quanto tempo -- il frontend formatta e basta."""
    risposta = archivio(client)

    assert risposta["total"] == len(risposta["items"]) > 0
    riga = risposta["items"][0]
    assert riga["name"]
    assert riga["frames"] > 0
    assert riga["integration_s"] >= 0


def test_each_row_carries_its_productions_and_they_add_up_to_the_row(client):
    """Una produzione e' la riga ripresa con un'ottica e una camera: insieme fanno la riga, senza
    contare un frame due volte e senza perderne."""
    risposta = archivio(client)

    for riga in risposta["items"]:
        sue = riga["productions"]
        assert sue, riga["name"]
        assert sum(p["frames"] for p in sue) == riga["frames"]
        assert sum(p["integration_s"] for p in sue) == riga["integration_s"]
        assert sum(p["untimed"] for p in sue) == riga["untimed"]
        assert all({"optics", "camera", "filters"} <= p.keys() for p in sue)


def test_a_rewritten_copy_is_not_another_hour_of_sky(client, db_path):
    """Una copia calibrata dello stesso scatto **non** e' un'altra ora di cielo: chi elabora
    tiene grezzo e calibrato nella stessa cartella, e contarli tutti e due raddoppierebbe la
    vita osservativa di chiunque."""
    conn = connect(db_path)
    try:
        originale = un_oggetto_con_pose(conn)
        nome = nome_di(conn, originale["object_id"])
        prima = per_nome(archivio(client))[nome]

        conn.execute(
            "INSERT INTO frames(frame_hash, image_type, header_json, object_id, exposure_s,"
            " copy_of, created_at)"
            " VALUES('copia-di-prova', 'light', '{}', ?, ?, ?, '2026-09-16T00:00:00Z')",
            (originale["object_id"], originale["exposure_s"] or 300.0, originale["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    dopo = per_nome(archivio(client))[nome]
    assert (dopo["frames"], dopo["integration_s"]) == (prima["frames"], prima["integration_s"])


def test_a_pose_without_a_time_is_not_zero_hours(client, db_path):
    """Una posa che non dice quanto e' durata **non vale zero**: non entra nella somma e si
    conta a parte, cosi' "non lo sappiamo" e "nessuna ora" restano due cose diverse. E' la
    terza forma del dato, quella che l'app non ha il diritto di inventare."""
    conn = connect(db_path)
    try:
        oggetto = un_oggetto_con_pose(conn)["object_id"]
        nome = nome_di(conn, oggetto)
        ore_prima = per_nome(archivio(client))[nome]["integration_s"]

        conn.execute(
            "INSERT INTO frames(frame_hash, image_type, header_json, object_id, exposure_s,"
            " created_at) VALUES('senza-tempo', 'light', '{}', ?, NULL, '2026-09-16T00:00:00Z')",
            (oggetto,),
        )
        conn.commit()
    finally:
        conn.close()

    riga = per_nome(archivio(client))[nome]
    assert riga["untimed"] >= 1
    assert riga["integration_s"] == ore_prima  # non ha aggiunto zero ore: non ha aggiunto niente
    assert riga["frames"] > riga["untimed"]  # le pose ci sono tutte, il tempo no


def test_the_bar_narrows_the_page_and_the_count_follows(client):
    """La barra arriva fino alla spina: si scrive qualcosa e la pagina si stringe, **e la conta
    con lei**. Una conta che resta quella di prima e' il numero su cui la pagina decide se c'e'
    un'altra pagina: sbagliarlo vuol dire offrire un "mostra altri" che non porta da nessuna
    parte, o nasconderne uno che servirebbe."""
    intero = archivio(client)
    uno = next(o for o in intero["items"] if o["name"])

    stretto = archivio(client, q=uno["name"])

    assert [o["name"] for o in stretto["items"]] == [uno["name"]]
    assert stretto["total"] == 1 < intero["total"]


def test_the_row_a_search_opens_is_there_whatever_the_bar_says(client):
    """`key` e' la riga che la ricerca apre: una parola rimasta nella barra non la nasconde, o la
    pagina direbbe "questo oggetto non c'e'" di un oggetto che c'e'."""
    uno = next(o for o in archivio(client)["items"] if o["name"])
    aperto = archivio(client, key=uno["key"], q="zzz")
    assert [o["key"] for o in aperto["items"]] == [uno["key"]]


def test_an_order_that_does_not_exist_is_refused_by_the_route(client):
    """I tre ordini sono un elenco chiuso e la rotta li rifiuta **prima** della spina: cio' che
    arriva da fuori non deve nemmeno avvicinarsi a un `ORDER BY`."""
    assert client.get("/api/v1/archive", params={"sort": ORDINE_OSTILE}).status_code == 422


def test_the_criteria_and_the_whole_archive_travel_with_the_page(client):
    """I criteri e la testa viaggiano **con la pagina**, gia' fatti: ricavarli a schermo dalle
    venti righe scaricate darebbe le scelte della prima pagina invece che dell'archivio.
    Cosa contengono lo prova la spina (`test_spine_archive_criteria.py`)."""
    intero = archivio(client)
    stretto = archivio(client, limit=1, q=intero["items"][0]["name"])

    assert intero["criteria"], "l'archivio di prova non offre criteri: la prova non guarda niente"
    assert stretto["whole"] == intero["whole"]
    assert intero["whole"]["rows"] == intero["total"]


def test_the_filters_of_an_object_come_with_it_from_the_same_house(client, db_path):
    """Con che filtri hai ripreso un oggetto arriva **gia' fatto**, dal filtro a cui e' andato piu'
    tempo, e dalla stessa casa che li conta per una notte (`spine/filters_used.py`). Se un giorno
    l'Archivio se li riscrivesse per conto suo, lo stesso scatto varrebbe due tempi diversi a
    seconda della pagina da cui lo guardi.

    test-tolto: test_an_object_never_grouped_says_nothing_instead_of_a_date -- guardava che
    `last_night` restasse nullo, e quel campo la rotta non lo manda piu' (Marco, 22/9/2026).
    test-tolto: test_the_newest_first_because_that_is_what_you_are_doing -- l'ordine di partenza
    adesso e' il nome (Marco, 22/9/2026: l'Archivio e' un inventario, le date stanno nelle Notti),
    e l'ordine per nome ha la sua prova in `test_spine_archive.py`.
    test-tolto: test_on_the_same_night_the_one_with_more_frames_comes_first -- stessa ragione: non
    esiste piu' un ordine "a pari notte".
    """
    conn = connect(db_path)
    try:
        oggetto = un_oggetto_con_pose(conn)["object_id"]
        nome = nome_di(conn, oggetto)
        nasce = "INSERT INTO filters(name, passband, created_at) VALUES(?, ?, '2026-09-16')"
        lum = conn.execute(nasce, ("Lum di prova", "L")).lastrowid
        ha = conn.execute(nasce, ("Ha di prova", "HA")).lastrowid
        # al Lum il doppio del tempo, cosi' l'ordine "dal piu' usato" ha qualcosa da ordinare; e una
        # copia riscritta del primo, che non deve contare
        conn.execute("UPDATE frames SET filter_id = NULL WHERE object_id = ?", (oggetto,))
        pose = []
        for filtro, quante, secondi in ((lum, 2, 600.0), (ha, 1, 300.0)):
            for _ in range(quante):
                pose.append(
                    conn.execute(
                        "INSERT INTO frames(frame_hash, image_type, header_json,"
                        " object_id, filter_id, exposure_s, created_at)"
                        " VALUES(?, 'light', '{}', ?, ?, ?, 'x')",
                        (f"filtri-{filtro}-{len(pose)}", oggetto, filtro, secondi),
                    ).lastrowid
                )
        conn.execute(
            "INSERT INTO frames(frame_hash, image_type, header_json, object_id, filter_id,"
            " exposure_s, copy_of, created_at) VALUES('filtri-copia', 'light', '{}', ?, ?, 600.0,"
            " ?, 'x')",
            (oggetto, ha, pose[0]),
        )
        conn.commit()
    finally:
        conn.close()

    riga = per_nome(archivio(client))[nome]

    # scritti a mano: un atteso che chiama la stessa casa della rotta proverebbe il cablaggio e
    # non il contenuto -- il banco si farebbe dire di si' anche con l'ordine rovesciato
    assert riga["filters"] == [
        {"name": "Lum di prova", "passband": "L", "frames": 2, "integration_s": 1200.0},
        {"name": "Ha di prova", "passband": "HA", "frames": 1, "integration_s": 300.0},
    ]


def test_the_list_is_paged_like_every_other(client):
    """Ogni elenco dell'API si legge allo stesso modo (`items`, `total`, `limit`, `offset`):
    una pagina che si impagina a modo suo obbliga chi la scrive a impararne due."""
    intero = archivio(client)
    prima = archivio(client, limit=1)
    seconda = archivio(client, limit=1, offset=1)

    assert prima["limit"] == 1 and prima["offset"] == 0
    assert prima["total"] == intero["total"] > 1
    assert len(prima["items"]) == 1
    assert seconda["items"][0]["key"] != prima["items"][0]["key"]


def test_the_criteria_come_with_the_first_page_only(client):
    """«Mostra altri» non cambia i criteri, e contarli legge i frame: arrivano con la prima
    pagina, la pagina li tiene da li'."""
    prima, seconda = archivio(client, limit=1), archivio(client, limit=1, offset=1)

    assert prima["criteria"]
    assert seconda["criteria"] == []


def test_an_empty_archive_is_an_answer_not_an_error(client_vuoto):
    """A mani vuote l'Archivio risponde **200 con zero righe**, non un errore: chi ha appena
    installato l'app non ha sbagliato niente, e la pagina glielo deve dire con parole sue."""
    risposta = archivio(client_vuoto)

    assert risposta["items"] == []
    assert risposta["total"] == 0


def test_the_catalog_says_what_kind_of_thing_it_is(client, db_path):
    """Dove l'oggetto e' di catalogo, la riga porta **costellazione e tipo**: sono le due cose
    che fanno di un elenco un archivio invece di una lista di nomi. Dove il catalogo non c'e'
    restano nulle, e la pagina non inventa."""
    conn = connect(db_path)
    try:
        conn.execute(
            "INSERT INTO catalog_entries(slug, name, common_name, ra_deg, dec_deg, x, y, z,"
            " constellation, type_code) VALUES('m-31', 'M 31', 'Andromeda', 10.68, 41.27,"
            " 0.65, 0.12, 0.66, 'And', 'GALAXY')"
        )
        oggetto = un_oggetto_con_pose(conn)["object_id"]
        conn.execute("UPDATE objects SET catalog_slug = 'm-31' WHERE id = ?", (oggetto,))
        conn.commit()
    finally:
        conn.close()

    righe = {o["key"]: o for o in archivio(client)["items"]}
    assert righe["m-31"]["constellation"] == "And"
    assert righe["m-31"]["type_code"] == "GALAXY"
    assert all(o["constellation"] is None for k, o in righe.items() if k != "m-31")
