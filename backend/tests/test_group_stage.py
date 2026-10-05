"""Lo stadio `group`: da una posa alla sua notte e alla sua sessione.

Le notti vanno da mezzogiorno a mezzogiorno **nel fuso del sito**, e una sessione e' oggetto x
notte x corredo. Qui si prova cosa finisce nel database e cosa resta fuori col suo perche':
un archivio in cui una posa sparisce senza motivo e' peggio di uno in cui manca una notte.
"""

import sqlite3

import pytest

from astrolog import place
from astrolog.place import coordinates_key
from astrolog.spine import declarations as decl
from astrolog.spine import group
from astrolog.spine.stages import invalidate
from group_bench import (
    ARIZONA,
    ROMA,
    VICINO,
    corri,
    luogo,
    notte_di,
    posa,
    prepara,
    sessione_di,
    stato,
)


@pytest.fixture
def archivio(conn):
    return prepara(conn)


# --- la notte -----------------------------------------------------------------------------


def test_the_night_runs_from_noon_to_noon(archivio):
    """Una notte tiene insieme la sera e il mattino dopo: a Roma le 01:30 del 18 maggio e le
    08:00 dello stesso 18 sono la **notte del 17**, perche' il taglio e' a mezzogiorno."""
    luogo(archivio, ROMA)
    sera = posa(archivio, quando="2024-05-17T23:30:00Z", hash_="a")  # 01:30 del 18, a Roma
    mattino = posa(archivio, quando="2024-05-18T06:00:00Z", hash_="b")  # 08:00 del 18, a Roma
    corri(archivio)
    assert notte_di(archivio, sera)["night_date"] == "2024-05-17"
    assert notte_di(archivio, mattino)["night_date"] == "2024-05-17"


def test_group_night_in_site_tz(conn):
    """**La regola che il vecchio aveva sbagliato**, ed e' questo il caso che la prova: il
    taglio e' a mezzogiorno **del fuso del sito**, non in UTC.

    Le 18:00 UTC del 18 maggio, in Arizona (UTC-7), sono le 11:00 del **mattino**: la notte e'
    quella del 17, che sta finendo. Calcolate in UTC come faceva il progetto di prima,
    18:00 meno dodici ore darebbe il **18**: una notte di distanza, e le ore di quella sera
    finirebbero spaccate in due."""
    conn.execute(
        "INSERT INTO objects(id, identity_method, identity_confidence, created_at)"
        " VALUES(1, 'exact_name', 'high', 'now')"
    )
    conn.execute("INSERT INTO rigs(id, focal_mm, detected, created_at) VALUES(1, 700, 1, 'now')")
    luogo(conn, ARIZONA)
    f = posa(conn, quando="2024-05-18T18:00:00Z")
    corri(conn)
    assert notte_di(conn, f)["night_date"] == "2024-05-17"


def test_two_places_the_same_date_are_two_nights(archivio):
    """Deciso nel contratto del sito: una notte e' data + luogo."""
    casa = luogo(archivio, ROMA)
    altro = luogo(archivio, ("Cima", 46.05, 11.316, "Europe/Rome"), casa=False)
    a = posa(archivio, quando="2024-05-17T22:00:00Z", hash_="a")
    corri(archivio)
    archivio.execute(
        "INSERT INTO nights(site_id, night_date, site_source, created_at)"
        " VALUES(?, '2024-05-17', 'declared', 'now')",
        (altro,),
    )
    notti = archivio.execute("SELECT COUNT(*) FROM nights WHERE night_date = ?", ("2024-05-17",))
    assert notti.fetchone()[0] == 2
    assert notte_di(archivio, a)["site_id"] == casa


# --- la sessione --------------------------------------------------------------------------


def test_group_session_key(archivio):
    """Oggetto x notte x corredo, e i filtri stanno dentro. Cambiare telescopio o camera a
    meta' notte apre un'altra sessione; la stessa terna non ne apre due."""
    luogo(archivio, ROMA)
    a = posa(archivio, quando="2024-05-17T22:00:00Z", oggetto=1, corredo=1, hash_="a")
    b = posa(archivio, quando="2024-05-17T23:00:00Z", oggetto=1, corredo=1, hash_="b")
    c = posa(archivio, quando="2024-05-17T23:30:00Z", oggetto=1, corredo=2, hash_="c")
    d = posa(archivio, quando="2024-05-17T23:40:00Z", oggetto=2, corredo=1, hash_="d")
    e = posa(archivio, quando="2024-05-18T22:00:00Z", oggetto=1, corredo=1, hash_="e")
    ricevuta = corri(archivio)

    assert sessione_di(archivio, a)["id"] == sessione_di(archivio, b)["id"]
    diverse = {sessione_di(archivio, x)["id"] for x in (a, c, d, e)}
    assert len(diverse) == 4, "corredo, oggetto o notte diversi devono aprire un'altra sessione"
    assert ricevuta["sessions"] == 4 and ricevuta["nights"] == 2
    assert ricevuta["linked"] == 5


def test_a_frame_whose_rig_is_unknown_does_not_open_two_sessions(archivio):
    """In SQLite due vuoti non contendono un indice unico: senza la chiave scritta come
    espressione, due pose senza corredo aprivano due sessioni identiche."""
    luogo(archivio, ROMA)
    a = posa(archivio, quando="2024-05-17T22:00:00Z", corredo=None, hash_="a")
    b = posa(archivio, quando="2024-05-17T23:00:00Z", corredo=None, hash_="b")
    corri(archivio)
    assert sessione_di(archivio, a)["id"] == sessione_di(archivio, b)["id"]
    assert archivio.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 1


# --- l'ora della posa: DATE-OBS e' UTC ---------------------------------------------------


def test_the_date_of_the_pose_is_utc_even_when_the_local_one_disagrees(archivio):
    """Lo standard FITS dice che `DATE-OBS` e' UTC (accordo IAU-FWG sulle date,
    <https://fits.gsfc.nasa.gov/year2000.html>, 4.4): un `DATE-LOC` che non torna col fuso non
    ferma la posa e non la sposta. 18:00 UTC in Arizona sono le 11:00 del 15, la notte del 14."""
    luogo(archivio, ARIZONA)
    f = posa(archivio, quando="2024-01-15T18:00:00.000", ora_locale="2024-01-15T18:00:00.000")
    corri(archivio)
    assert stato(archivio, f) == ("done", None)
    assert notte_di(archivio, f)["night_date"] == "2024-01-14"


# --- da dove hai ripreso: si chiede, non si indovina ----------------------------------------


def test_group_asks_when_the_coordinates_say_elsewhere(archivio):
    """Le coordinate dell'header dicono un altro posto: l'app non attribuisce, si ferma col
    suo codice. Sull'archivio di collaudo sono 432 pose, cinque notti -- e due di quelle
    hanno pose di due luoghi diversi nella stessa data, che e' proprio il caso in cui
    indovinare sarebbe sbagliato."""
    luogo(archivio, ROMA)
    f = posa(archivio, quando="2024-05-17T22:00:00Z", coord=(45.6, 11.667))  # 12 km
    ricevuta = corri(archivio)
    assert stato(archivio, f) == ("skipped", group.SITE_UNCLEAR)
    assert ricevuta["waiting"] == 1 and ricevuta["linked"] == 0


def test_a_pose_just_past_the_threshold_is_still_a_question(archivio):
    """La soglia dello stesso posto si gioca sui **decimali**, e per questo la distanza non si
    arrotonda dove si calcola.

    Queste coordinate distano 1,04 km da casa: oltre `SAME_PLACE_KM`, quindi la posa si ferma e
    si chiede. Arrotondando la distanza a un decimale -- come fa l'API per mostrarla a schermo --
    diventerebbe 1,0, non supererebbe piu' la soglia, e questa posa verrebbe attribuita a casa
    **in silenzio**. E' il motivo per cui si arrotonda al bordo e mai in `place.distance_km`."""
    luogo(archivio, ROMA)
    f = posa(archivio, quando="2024-05-17T22:00:00Z", coord=(45.554853, 11.5354))
    corri(archivio)
    assert stato(archivio, f) == ("skipped", group.SITE_UNCLEAR)


def test_group_invents_no_night_without_an_answer(archivio):
    """E non nasce nemmeno la notte: una notte attribuita al posto sbagliato e' un dato falso
    che nessuno rilegge piu'."""
    luogo(archivio, ROMA)
    posa(archivio, quando="2024-05-17T22:00:00Z", coord=(45.6, 11.667))
    corri(archivio)
    assert archivio.execute("SELECT COUNT(*) FROM nights").fetchone()[0] == 0
    assert archivio.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0


def test_a_frame_shot_at_another_declared_site_goes_there_without_asking(archivio):
    """Il sito dove hai ripreso l'hai gia' dichiarato, e non e' casa: le coordinate dell'header
    cadono li', e la notte nasce su quel sito senza chiedere. Solo un posto che non conosci e'
    una domanda."""
    luogo(archivio, ROMA)
    montagna = luogo(archivio, ("Montagna", *VICINO, "Europe/Rome"), casa=False)
    f = posa(archivio, quando="2024-05-17T22:00:00Z", coord=(VICINO[0] + 0.001, VICINO[1]))
    corri(archivio)
    assert stato(archivio, f) == ("done", None)
    notte = notte_di(archivio, f)
    # l'ha deciso l'app, non l'utente: la notte resta rifacibile, e vuota si spazza
    assert (notte["site_id"], notte["site_source"]) == (montagna, "detected")


def test_between_two_declared_sites_the_nearest_wins(archivio):
    """Due siti dichiarati a meno di un chilometro dalle coordinate: vale il piu' vicino, non
    il primo dell'elenco."""
    luogo(archivio, ("Lontano", 33.0, -111.0, "America/Phoenix"))
    luogo(archivio, ("Prato", VICINO[0] + 0.006, VICINO[1], "Europe/Rome"), casa=False)
    vicino = luogo(archivio, ("Rifugio", VICINO[0] + 0.001, VICINO[1], "Europe/Rome"), casa=False)
    f = posa(archivio, quando="2024-05-17T22:00:00Z", coord=VICINO)
    corri(archivio)
    assert notte_di(archivio, f)["site_id"] == vicino


def test_an_answer_wins_over_a_site_declared_later_nearer(archivio):
    """Per quelle coordinate l'utente ha risposto "Rifugio"; poi dichiara "Prato", piu' vicino.
    La sua risposta resta la sua parola: la vicinanza non la scavalca."""
    luogo(archivio, ROMA)
    rifugio = luogo(archivio, ("Rifugio", VICINO[0] + 0.04, VICINO[1], "Europe/Rome"), casa=False)
    decl.declare_coordinates(archivio, coordinates_key(*VICINO), "Rifugio")
    luogo(archivio, ("Prato", VICINO[0] + 0.004, VICINO[1], "Europe/Rome"), casa=False)
    f = posa(archivio, quando="2024-05-17T22:00:00Z", coord=VICINO)
    corri(archivio)
    notte = notte_di(archivio, f)
    assert (notte["site_id"], notte["site_source"]) == (rifugio, "declared")


def test_without_a_home_a_frame_near_a_declared_site_goes_there(archivio):
    """Casa non c'e' -- cancellata, e nessuna eletta al suo posto -- ma il frame e' a cento metri
    da un sito dichiarato: si sa dov'eri, e la notte nasce li'."""
    montagna = luogo(archivio, ("Montagna", *VICINO, "Europe/Rome"), casa=False)
    f = posa(archivio, quando="2024-05-17T22:00:00Z", coord=(VICINO[0] + 0.001, VICINO[1]))
    corri(archivio)
    assert notte_di(archivio, f)["site_id"] == montagna


def test_a_declared_site_without_a_timezone_says_so(archivio):
    """Il sito dichiarato piu' vicino non ha un fuso: si dice, non si ripiega su casa."""
    luogo(archivio, ROMA)
    luogo(archivio, ("Senza fuso", *VICINO, None), casa=False)
    f = posa(archivio, quando="2024-05-17T22:00:00Z", coord=VICINO)
    corri(archivio)
    assert stato(archivio, f) == ("skipped", group.SITE_NO_TIMEZONE)


def test_a_frame_within_the_tolerance_does_not_ask(archivio):
    """Sotto il chilometro la differenza e' in **come e' scritta** la coordinata, non in dove
    eri: due decimali si spostano gia' di 1,1 km."""
    luogo(archivio, ROMA)
    f = posa(archivio, quando="2024-05-17T22:00:00Z", coord=(45.5485, 11.5384))  # ~400 m
    corri(archivio)
    assert stato(archivio, f) == ("done", None)
    assert notte_di(archivio, f)["night_date"] == "2024-05-17"


def test_a_frame_without_coordinates_does_not_ask(archivio):
    """La maggior parte degli header non le porta: l'assenza non e' un dubbio."""
    luogo(archivio, ROMA)
    f = posa(archivio, quando="2024-05-17T22:00:00Z", coord=None)
    corri(archivio)
    assert stato(archivio, f) == ("done", None)


# --- cosa resta fuori, e lo dice ------------------------------------------------------------


def test_no_home_place_no_nights_and_it_says_so(archivio):
    """A mani vuote l'app cataloga e cerca, ma le notti non nascono: una notte e' data +
    luogo, e il fuso e' del luogo. Non se ne elegge uno da sola."""
    f = posa(archivio, quando="2024-05-17T22:00:00Z")
    ricevuta = corri(archivio)
    assert stato(archivio, f) == ("skipped", group.NO_ACTIVE_SITE)
    assert archivio.execute("SELECT COUNT(*) FROM nights").fetchone()[0] == 0
    assert ricevuta["waiting"] == 1


def test_on_the_open_sea_the_night_follows_the_nautical_zone(archivio):
    """In mare aperto la libreria dei confini da' il fuso nautico, e la notte va da mezzogiorno a
    mezzogiorno in quel fuso: le 20:00 UTC sono le 11:00 di bordo, ancora la notte prima."""
    fuso = place.timezone_of(0.0, -140.0)
    assert fuso == "Etc/GMT+9"
    luogo(archivio, ("Pacifico", 0.0, -140.0, fuso))
    f = posa(archivio, quando="2024-05-17T20:00:00Z")
    corri(archivio)
    assert stato(archivio, f) == ("done", None)
    assert notte_di(archivio, f)["night_date"] == "2024-05-16"


def test_a_site_without_a_timezone_does_not_guess_one(archivio):
    """Del sito non si riconosce un fuso. Si dice, non si ripiega su UTC."""
    archivio.execute(
        "INSERT INTO sites(name, latitude, longitude, timezone, is_default, created_at)"
        " VALUES('Senza fuso', 0.0, -30.0, NULL, 1, 'now')"
    )
    f = posa(archivio, quando="2024-05-17T22:00:00Z")
    corri(archivio)
    assert stato(archivio, f) == ("skipped", group.SITE_NO_TIMEZONE)


def test_a_frame_identify_left_without_an_object_stops_here(archivio):
    """Una posa senza nome e senza cielo arriva fin qui apposta: se lo stadio non la vedesse,
    il suo residuo non arriverebbe mai a zero e il pulsante Avvia partirebbe a vuoto per
    sempre. Si ferma col suo perche', e il residuo scende.

    E' anche **la rete sotto la rete della calibrazione**: un dark che sfuggisse alle due spie
    della scansione non ha un cielo, non si risolve e resta senza oggetto -- e qui si vede che
    non diventa una notte ne' una sessione, cioe' da solo non diventa un'ora di integrazione
    (se qualcuno gli da' un nome in Da confermare si': la domanda sul tipo e' in coda)."""
    luogo(archivio, ROMA)
    f = posa(archivio, quando="2024-05-17T22:00:00Z", oggetto=None, identify="skipped")
    ricevuta = corri(archivio)
    assert stato(archivio, f) == ("skipped", group.NO_OBJECT)
    assert ricevuta["waiting"] == 1
    assert (
        archivio.execute(
            "SELECT COUNT(*) FROM frame_stages WHERE stage = 'group' AND status = 'pending'"
        ).fetchone()[0]
        == 0
    )
    assert archivio.execute("SELECT COUNT(*) FROM nights").fetchone()[0] == 0
    assert archivio.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0


def test_a_frame_without_a_date_stops_here(archivio):
    """Senza `DATE-OBS` non c'e' notte. Sull'archivio di collaudo non capita mai -- nessuna
    delle 11.033 pose entrate -- ma un software che non la scrive esiste."""
    luogo(archivio, ROMA)
    f = posa(archivio, quando=None)
    corri(archivio)
    assert stato(archivio, f) == ("skipped", group.NO_DATE)


# --- rifare non rovina ----------------------------------------------------------------------


def test_running_the_stage_twice_changes_nothing(archivio):
    """Rifare uno stadio riscrive, non duplica."""
    luogo(archivio, ROMA)
    f = posa(archivio, quando="2024-05-17T22:00:00Z")
    corri(archivio)
    prima = (notte_di(archivio, f)["id"], sessione_di(archivio, f)["id"])
    invalidate(archivio, [f], "group")
    corri(archivio)
    assert (notte_di(archivio, f)["id"], sessione_di(archivio, f)["id"]) == prima
    assert archivio.execute("SELECT COUNT(*) FROM nights").fetchone()[0] == 1
    assert archivio.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 1


def test_a_session_left_without_frames_disappears(archivio):
    """Quando una posa cambia oggetto, la sessione vecchia resta senza nessuno: e' un residuo,
    e sulla pagina Notti sarebbe una riga che dice "0 pose". Sparisce, e con lei la notte che
    non ha piu' sessioni. E' la stessa lezione degli oggetti rimasti vuoti."""
    luogo(archivio, ROMA)
    f = posa(archivio, quando="2024-05-17T22:00:00Z", oggetto=1)
    corri(archivio)
    archivio.execute("UPDATE frames SET object_id = 2 WHERE id = ?", (f,))
    invalidate(archivio, [f], "group")
    ricevuta = corri(archivio)
    assert archivio.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 1
    assert sessione_di(archivio, f)["object_id"] == 2
    assert ricevuta["swept"] == 1


def test_when_a_rig_disappears_its_sessions_go_and_the_frames_stay(archivio):
    """Unire due grafie di un pezzo, in Da confermare, **cancella un corredo**. Le sessioni che
    lo usavano sono un derivato e se ne vanno con lui; le pose restano, senza sessione, e il
    giro dopo le rimette dove vanno -- l'unione rimette in coda anche `group`.

    Senza questa regola l'unione falliva col database in faccia: misurato,
    `FOREIGN KEY constraint failed`. Era una voce della coda, e si chiude qui."""
    luogo(archivio, ROMA)
    f = posa(archivio, quando="2024-05-17T22:00:00Z", corredo=1)
    corri(archivio)

    archivio.execute("UPDATE frames SET rig_id = 2 WHERE id = ?", (f,))
    archivio.execute("DELETE FROM rigs WHERE id = 1")  # e' cio' che fa l'unione
    assert archivio.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0
    resta = archivio.execute("SELECT session_id FROM frames WHERE id = ?", (f,)).fetchone()
    assert resta["session_id"] is None, "la posa deve restare, senza la sua sessione"

    invalidate(archivio, [f], "group")
    corri(archivio)
    assert sessione_di(archivio, f)["rig_id"] == 2


def test_the_database_refuses_two_sessions_with_the_same_key(archivio):
    """La chiave della sessione e' un indice **su un'espressione**, e questa e' la sua guardia.

    Lo stadio la rispetta da solo -- cerca prima di creare -- quindi senza un inserimento
    diretto l'indice non verrebbe mai interrogato, e toglierlo dallo schema non farebbe
    diventare rosso niente. Il caso che conta e' il corredo vuoto: li' un `UNIQUE` di colonne
    non avrebbe fermato nessuno."""
    luogo(archivio, ROMA)
    posa(archivio, quando="2024-05-17T22:00:00Z", corredo=None)
    corri(archivio)
    riga = archivio.execute("SELECT night_id, object_id FROM sessions").fetchone()
    with pytest.raises(sqlite3.IntegrityError):
        archivio.execute(
            "INSERT INTO sessions(night_id, object_id, rig_id) VALUES(?, ?, NULL)",
            (riga["night_id"], riga["object_id"]),
        )


def test_a_night_the_user_declared_survives_an_empty_pass(archivio):
    """Una notte **dichiarata** puo' restare vuota per un giro -- le sue pose stanno aspettando
    un altro stadio -- e non e' un residuo: e' una risposta dell'utente. La spazzata non la
    tocca, o cancellerebbe una risposta in silenzio."""
    casa = luogo(archivio, ROMA)
    archivio.execute(
        "INSERT INTO nights(site_id, night_date, site_source, created_at)"
        " VALUES(?, '2024-05-17', 'declared', 'now')",
        (casa,),
    )
    corri(archivio)
    rimaste = archivio.execute("SELECT site_source FROM nights").fetchall()
    assert [r["site_source"] for r in rimaste] == ["declared"]


def test_a_night_left_without_sessions_disappears(archivio):
    """Una notte senza sessioni non e' una notte: e' una riga che nessuno guardera'."""
    luogo(archivio, ROMA)
    f = posa(archivio, quando="2024-05-17T22:00:00Z")
    corri(archivio)
    archivio.execute("UPDATE frames SET date_obs = '2024-06-01T22:00:00Z' WHERE id = ?", (f,))
    invalidate(archivio, [f], "group")
    corri(archivio)
    date = [r[0] for r in archivio.execute("SELECT night_date FROM nights")]
    assert date == ["2024-06-01"]
