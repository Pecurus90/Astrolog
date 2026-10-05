"""Che luna fa stanotte, chiesto dalla rotta: il giro intero, dal sito di casa alla risposta.

Le prove del calcolo stanno in `test_ephemeris_moon.py`. Qui si guarda cio' che il calcolo da
solo non puo' sbagliare: **da quale sito**, **in quale notte**, e cosa succede quando un sito di
casa non c'e'.
"""

import datetime as dt
import typing
import zoneinfo

import pytest

from astrolog.api.models_tonight import PhaseKey
from astrolog.clock import night_window
from astrolog.ephemeris import moon
from astrolog.units import bortle_of
from conftest import db

# i siti nascono al sito buio: creandoli l'app chiede l'altitudine, e qui nessun servizio risponde
pytestmark = [
    pytest.mark.filterwarnings("ignore:Tried to get polar motions:"),
    pytest.mark.usefixtures("offline"),
]


def crea_sito(client_vuoto, nome, lat, lon, sky_sqm=None):
    """Un sito di casa. Senza `sky_sqm` la classe del suo cielo resta **non dichiarata**, che e'
    lo stato di chi salta quella domanda al primo avvio."""
    corpo = {"name": nome, "latitude": lat, "longitude": lon, "is_default": True}
    if sky_sqm is not None:
        corpo["sky_sqm"] = sky_sqm
    r = client_vuoto.post("/api/v1/sites", json=corpo)
    assert r.status_code == 201, r.text
    return r.json()


def test_without_a_home_site_there_is_no_moon_and_it_is_said(client_vuoto):
    """Chi ha saltato il primo avvio non ha un sito: non c'e' nessuna luna da mostrare, e la
    rotta lo **dice** invece di calcolarla su un posto inventato. Un numero verosimile sarebbe
    peggio di un vuoto, perche' non si distingue da uno vero."""
    r = client_vuoto.get("/api/v1/tonight")

    assert r.status_code == 200, r.text
    detto = r.json()
    # il cielo segue la stessa regola: niente sito, niente notte da dividere in fasce
    assert detto == {"night": None, "site": None, "moon": None, "sky_bands": [], "weather": None}


def test_with_a_home_site_the_moon_is_told_with_its_night(client_vuoto):
    """Col sito di casa arrivano i due numeri che il piede della barra mostra, e la **notte** a
    cui si riferiscono: senza quella, chi li mostra non sa quando sono scaduti."""
    crea_sito(client_vuoto, "Vicenza", 45.5455, 11.5354)

    detto = client_vuoto.get("/api/v1/tonight").json()

    assert detto["site"]["name"] == "Vicenza"
    assert detto["night"] is not None and len(detto["night"]) == len("2026-09-19")
    assert detto["moon"]["phase_key"] in moon.PHASES
    assert 0 <= detto["moon"]["illumination_pct"] <= 100


def test_the_moon_comes_from_the_home_site_not_from_any_site(client_vuoto):
    """Due siti lontani danno due orari diversi, e quello che vale e' **quello di casa**: senza
    questa riga la rotta potrebbe prendere il primo che trova e nessuno se ne accorgerebbe --
    l'altro sito sarebbe pure un sito vero."""
    crea_sito(client_vuoto, "Vicenza", 45.5455, 11.5354)
    da_vicenza = client_vuoto.get("/api/v1/tonight").json()

    lontano = crea_sito(client_vuoto, "Auckland", -36.8485, 174.7633)
    assert lontano["is_default"] is True  # l'ultimo creato di casa prende il posto
    da_auckland = client_vuoto.get("/api/v1/tonight").json()

    assert da_vicenza["site"]["name"] == "Vicenza"
    assert da_auckland["site"]["name"] == "Auckland"
    assert da_vicenza["moon"]["rise"] != da_auckland["moon"]["rise"]


def test_the_night_is_the_one_of_the_site_not_of_the_server(client_vuoto, monkeypatch):
    """La notte va da mezzogiorno a mezzogiorno **nel fuso del sito**, non del server.

    Si ferma l'orologio alle **08:00 UTC** del 15 luglio. A Vicenza sono le 10 del mattino:
    prima di mezzogiorno, quindi si e' ancora nella notte cominciata il **14**. Ad Auckland sono
    le 20 di sera: dopo mezzogiorno, quindi la notte e' quella del **15**. Stesso istante, due
    notti diverse -- ed e' diverso **perche' si guarda il fuso del sito**. Chi leggesse l'ora del
    server ne direbbe una sola, e sarebbe sbagliata per uno dei due."""
    monkeypatch.setattr("astrolog.api.tonight.now_iso", lambda: "2026-07-15T08:00:00.000Z")

    crea_sito(client_vuoto, "Vicenza", 45.5455, 11.5354)
    qui = client_vuoto.get("/api/v1/tonight").json()
    crea_sito(client_vuoto, "Auckland", -36.8485, 174.7633)
    la = client_vuoto.get("/api/v1/tonight").json()

    assert qui["night"] == "2026-07-14", qui
    assert la["night"] == "2026-07-15", la


def test_the_window_lasts_the_real_night_not_a_fixed_day(client_vuoto, monkeypatch):
    """La notte del cambio d'ora **non dura ventiquattro ore**: a Roma ne dura 23 in primavera e
    25 in autunno. Contandone 24 fisse si guarderebbe un'ora della notte dopo, o si perderebbe
    l'ultima di questa -- e un attraversamento che cade proprio li' finirebbe nel posto
    sbagliato. La finestra si misura fra i due mezzogiorni veri."""
    import datetime as dt

    from astrolog.clock import night_window

    primavera, quante = night_window("2027-03-27", "Europe/Rome")
    assert quante == 23, quante
    autunno, quante_autunno = night_window("2027-10-30", "Europe/Rome")
    assert quante_autunno == 25, quante_autunno
    # e comincia sempre a mezzogiorno, che nessuna transizione toglie
    for quando in (primavera, autunno):
        assert quando.hour == 12, quando
    assert isinstance(primavera, dt.datetime)


def test_a_site_whose_timezone_no_longer_exists_does_not_break_the_page(client_vuoto, monkeypatch):
    """Un fuso salvato che il sistema non conosce piu' -- succede quando il database dei fusi
    cambia -- non deve diventare un 500: il sito si legge lo stesso, senza la sua luna. Senza
    l'uscita anticipata, il conto del mezzogiorno solleverebbe e la pagina cadrebbe intera."""
    crea_sito(client_vuoto, "Vicenza", 45.5455, 11.5354)
    monkeypatch.setattr("astrolog.api.tonight.night_date", lambda *a, **k: None)

    r = client_vuoto.get("/api/v1/tonight")

    assert r.status_code == 200, r.text
    detto = r.json()
    assert detto["site"]["name"] == "Vicenza"
    assert detto["night"] is None and detto["moon"] is None


def test_the_phase_is_asked_in_the_middle_of_the_night_not_at_noon(client_vuoto, monkeypatch):
    """La Luna cambia circa il sei per cento al giorno: chiesta a mezzogiorno, chi guarda la barra
    alle undici di sera legge il numero di dodici ore prima. Misurato: 48% contro 54% sulla stessa
    notte. Si chiede a **meta' finestra**, che e' l'ora in cui si osserva."""
    chiesto = []
    vera = moon.phase
    monkeypatch.setattr("astrolog.ephemeris.moon.phase", lambda q: chiesto.append(q) or vera(q))
    crea_sito(client_vuoto, "Vicenza", 45.5455, 11.5354)

    client_vuoto.get("/api/v1/tonight")

    assert len(chiesto) == 1, chiesto
    # **Dentro la finestra**, non solo a un'ora che somiglia a mezzanotte: andando all'indietro
    # invece che in avanti si arriva lo stesso alle 00:00, ma della notte prima -- e guardando
    # solo l'ora la prova resterebbe verde (visto: il sabotaggio sopravviveva).
    notte = client_vuoto.get("/api/v1/tonight").json()["night"]
    comincia, quante = night_window(notte, "Europe/Rome")
    finisce = comincia.astimezone(dt.UTC) + dt.timedelta(hours=quante)  # in UTC: vedi sotto
    assert comincia < chiesto[0] < finisce, (chiesto[0], comincia)
    assert chiesto[0].astimezone(zoneinfo.ZoneInfo("Europe/Rome")).hour == 0, chiesto[0]


def test_the_route_sends_the_curve_and_the_highest_point(client_vuoto):
    """Il piede della barra disegna l'andamento della notte, e il pannello ne scrivera' i numeri:
    tutti e due escono **dalla rotta**, gia' fatti.

    Si guarda che la curva **copra la notte**, non che esista: una curva che comincia a
    mezzanotte, o che finisce un'ora prima, a schermo e' un grafico plausibile e sbagliato."""
    crea_sito(client_vuoto, "Vicenza", 45.5455, 11.5354)

    detto = client_vuoto.get("/api/v1/tonight").json()
    luna = detto["moon"]

    comincia, quante = night_window(detto["night"], "Europe/Rome")
    assert dt.datetime.fromisoformat(luna["track"][0]["at"]) == comincia
    # **Le ore si sommano in UTC**, anche qui. Scritto `comincia + timedelta(hours=quante)`, con
    # `comincia` che porta un fuso vero, questa riga fa aritmetica da orologio da parete -- la
    # stessa trappola che `night_window` documenta, al contrario -- e sbaglia di un'ora le due notti
    # del cambio d'ora: il 25/10/2026 si aspetterebbe le 13:00 dove la rotta manda mezzogiorno,
    # che e' l'ora giusta. La prova diventerebbe rossa da sola, e chi la guarda riparerebbe la
    # rotta invece della prova.
    finisce = comincia.astimezone(dt.UTC) + dt.timedelta(hours=quante)
    assert dt.datetime.fromisoformat(luna["track"][-1]["at"]) == finisce
    # una notte intera a quindici minuti: abbastanza punti da disegnare, non 481
    assert 90 < len(luna["track"]) < 110, len(luna["track"])
    # e il punto piu' alto e' davvero il piu' alto di quelli mandati
    assert luna["highest"]["altitude_deg"] >= max(p["altitude_deg"] for p in luna["track"])


def test_the_route_sends_the_ceiling_of_the_home_site(client_vuoto):
    """Il bordo alto del grafico dipende **dalla latitudine del sito di casa**, non da stanotte, e
    lo manda il backend gia' fatto: derivarlo nel disegno vorrebbe dire un conto dentro il layout.

    Si guarda con due siti a latitudini diverse, perche' un tetto costante -- o preso dal sito
    sbagliato -- resterebbe verde con un sito solo."""
    crea_sito(client_vuoto, "Vicenza", 45.5455, 11.5354)
    da_vicenza = client_vuoto.get("/api/v1/tonight").json()["moon"]

    crea_sito(client_vuoto, "Singapore", 1.3521, 103.8198)
    da_singapore = client_vuoto.get("/api/v1/tonight").json()["moon"]

    assert da_vicenza["ceiling_deg"] == 75, da_vicenza["ceiling_deg"]
    # ai tropici la Luna passa allo zenit: il tetto e' novanta, non qualcosa oltre
    assert da_singapore["ceiling_deg"] == 90, da_singapore["ceiling_deg"]
    # e nessuna delle due notti sfonda il proprio tetto
    for luna in (da_vicenza, da_singapore):
        assert luna["highest"]["altitude_deg"] <= luna["ceiling_deg"], luna["highest"]


def test_the_route_sends_the_site_with_the_sky_it_has(client_vuoto):
    """Il piede della barra scrive *"Vicenza - Bortle 4"*: il nome e la classe del cielo stanno
    nella **stessa** risposta, perche' sono una frase sola. Chiederli a due rotte vorrebbe dire due
    giri di rete per una riga, e due momenti in cui la pagina e' a meta'.

    La classe **non e' una colonna**: nasce dalla luminosita' del cielo, e la conversione vive in
    un posto solo (`astrolog.units.bortle_of`). Qui si guarda che la rotta usi quella, non che
    sappia contare: un 20,8 che diventasse Bortle 5 sarebbe un cielo sbagliato di una classe."""
    crea_sito(client_vuoto, "Vicenza", 45.5455, 11.5354, sky_sqm=20.8)

    sito = client_vuoto.get("/api/v1/tonight").json()["site"]

    assert sito["name"] == "Vicenza"
    assert sito["sky_sqm"] == 20.8
    assert sito["bortle"] == bortle_of(20.8)


def test_a_site_whose_sky_was_never_declared_says_so_instead_of_guessing(client_vuoto):
    """Un sito c'e' ma la classe del suo cielo no: capita a chi salta la domanda al primo avvio, e
    **non e' un guasto**. I due campi tornano vuoti insieme -- la classe non compare mai senza la
    misura da cui nasce -- e il resto della notte arriva lo stesso, perche' la Luna non dipende da
    quanto e' buio.

    Senza questa riga il caso si sarebbe visto solo a schermo, e solo da chi ha saltato quel passo:
    chi sviluppa ha sempre un cielo dichiarato."""
    crea_sito(client_vuoto, "Passo Giau", 46.4849, 12.0533)

    detto = client_vuoto.get("/api/v1/tonight").json()

    assert detto["site"]["name"] == "Passo Giau"
    assert detto["site"]["sky_sqm"] is None, detto["site"]
    assert detto["site"]["bortle"] is None, detto["site"]
    assert detto["moon"]["phase_key"] in moon.PHASES


def test_starting_the_app_already_disarms_the_download():
    """**"Offline sempre" vale dall'avvio**, non dalla prima volta che qualcuno apre la Luna.

    L'import delle effemeridi era pigro, dentro la rotta, "per non far aspettare l'avvio": la
    ragione era falsa -- misurato, l'app ci mette 531 ms e le effemeridi ne aggiungono uno --
    e intanto il processo girava col download di astropy **armato** per tutto il tempo in cui
    nessuno apriva quella rotta. Ogni altro uso di astropy, come la lettura degli header, girava
    li' dentro."""
    from astropy.utils import iers

    assert iers.conf.auto_download is False
    assert iers.conf.auto_max_age is None


def test_the_phases_of_the_route_are_the_phases_of_the_sky():
    """Le otto fasi vivono in **due case**: il modulo che le calcola e il contratto della rotta,
    che le riscrive apposta -- un contratto che cambia forma perche' e' cambiato un modulo interno
    non si puo' leggere. Ma i due elenchi devono restare gli stessi, o la rotta prometterebbe una
    parola che il cielo non dice.

    Questa prova era stata scritta, ed e' sparita riscrivendo il file: la guardia sui test spariti
    non l'ha vista perche' il file era nuovo, quindi non c'era un "prima" da confrontare."""
    dette = set(typing.get_args(PhaseKey))

    assert dette == set(moon.PHASES), dette ^ set(moon.PHASES)


def test_a_moon_that_never_rises_comes_back_empty_not_invented(client_vuoto, monkeypatch):
    """Sopra il circolo polare la Luna puo' non attraversare l'orizzonte in tutta la notte, e il
    calcolo lo dice con `None`. Qui si guarda che **la rotta non lo riempia**: un orario scritto
    li' sarebbe inventato e indistinguibile da uno vero.

    Il cielo si finge invece di aspettare il giorno giusto: la prova deve cadere se la rotta
    inventa, non se oggi a Longyearbyen la Luna sorge."""
    vera = moon.night_track
    monkeypatch.setattr(
        "astrolog.ephemeris.moon.night_track",
        lambda *a, **k: {**vera(*a, **k), "rise": None, "set": None},
    )
    crea_sito(client_vuoto, "Longyearbyen", 78.2232, 15.6267)

    luna = client_vuoto.get("/api/v1/tonight").json()["moon"]

    assert luna["rise"] is None and luna["set"] is None, luna
    # e il resto arriva lo stesso: una luna senza orari ha comunque una fase, una luce, e il suo
    # punto piu' alto -- che e' proprio cio' che si vuole sapere quando non sorge
    assert luna["phase_key"] in moon.PHASES
    assert luna["highest"]["at"] is not None


def test_the_route_sends_the_bands_of_the_sky_already_made(client_vuoto):
    """Le fasce del crepuscolo escono **dalla rotta, gia' fatte**: una lista di segmenti attaccati
    che copre la notte intera, dal primo istante all'ultimo.

    Qui si guarda che **coprano** la notte: un buco a schermo sarebbe una striscia di fondo
    indistinguibile da un dato che manca."""
    crea_sito(client_vuoto, "Vicenza", 45.5455, 11.5354)

    detto = client_vuoto.get("/api/v1/tonight").json()
    fasce = detto["sky_bands"]

    comincia, quante = night_window(detto["night"], "Europe/Rome")
    assert dt.datetime.fromisoformat(fasce[0]["starts_at"]) == comincia
    finisce = (comincia.astimezone(dt.UTC) + dt.timedelta(hours=quante)).astimezone(comincia.tzinfo)
    assert dt.datetime.fromisoformat(fasce[-1]["ends_at"]) == finisce
    for prima, dopo in zip(fasce, fasce[1:], strict=False):
        assert prima["ends_at"] == dopo["starts_at"]
    # e a Vicenza a qualunque data il cielo passa per il buio e torna al giorno
    quali = [f["kind"] for f in fasce]
    assert quali[0] == "day" and quali[-1] == "day"
    assert "dark" in quali


def test_a_site_that_has_no_timezone_at_all_does_not_break_the_page(client_vuoto):
    """Un sito **senza fuso** -- un fuso che non si riconosce, o un database dei fusi vecchio sul
    NAS -- non e' un caso teorico: lo schema lo ammette, le Impostazioni lo mostrano col suo
    codice, e lo stadio che raggruppa lo salta apposta. Qui la pagina si legge lo stesso, senza
    la sua luna.

    Non si ripiega su Greenwich: la Luna di un posto che non sappiamo dov'e' sarebbe un numero
    giusto per un altro sito, e nessuno potrebbe accorgersene."""
    crea_sito(client_vuoto, "Senza fuso", 0.0, -30.0)
    with db(client_vuoto) as conn:
        conn.execute("UPDATE sites SET timezone = NULL")
        conn.commit()

    r = client_vuoto.get("/api/v1/tonight")

    assert r.status_code == 200, r.text
    detto = r.json()
    assert detto["site"]["name"] == "Senza fuso"
    assert detto["night"] is None and detto["moon"] is None
    assert detto["sky_bands"] == []


def test_a_site_without_a_timezone_has_no_bands_instead_of_invented_ones(client_vuoto, monkeypatch):
    """Senza fuso non c'e' notte, quindi non c'e' nemmeno un cielo da dividere in fasce: esce una
    lista vuota, come la Luna esce `None`. Inventare una finestra qui vorrebbe dire dipingere il
    buio di un posto che non sappiamo dov'e'."""
    monkeypatch.setattr("astrolog.api.tonight.night_date", lambda *a, **k: None)
    crea_sito(client_vuoto, "Vicenza", 45.5455, 11.5354)

    detto = client_vuoto.get("/api/v1/tonight").json()

    assert detto["sky_bands"] == []
    assert detto["moon"] is None and detto["site"] is not None
