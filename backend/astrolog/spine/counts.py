"""I tre numeri con cui l'app racconta un pezzo di archivio: **quante pose, quante ore, e quante
pose non dicono quanto sono durate**.

Sta in una casa sola perche' lo chiedono da piu' parti -- per oggetto (l'Archivio e *Da
confermare*), per notte e per l'archivio intero (le Notti), per pezzo (l'Attrezzatura e *Da
confermare*), per corredo e per filtro (l'Attrezzatura) -- e ogni copia di questi sotto-select
sarebbe un altro modo di contare le stesse ore, cioe' due pagine dello stesso archivio che prima o
poi dicono numeri diversi. La regola e' scritta in `docs/domini/archivio.md`.

Vincoli non ovvi:

* **Le copie riscritte non contano mai** (`copy_of`): chi elabora tiene grezzo e calibrato nella
  stessa cartella, e contarli tutti e due raddoppierebbe la vita osservativa di chiunque.
* **Il soggetto e' una chiave, non un pezzo di SQL.** Chi chiama sceglie da un elenco chiuso: una
  funzione che si fa passare un `WHERE` da fuori e' una porta aperta, anche quando chi la usa oggi
  passa una costante.
"""

import re

# I generi che una posa **nomina addosso a se'**, ognuno col suo grezzo (`<genere>_raw`): li fa
# nascere `normalize` e se ne impara la grafia vecchia quando li rinomini. Ricopiarlo vorrebbe dire
# che il genere numero quattro nasce ma non si rinomina, e rinasce doppio.
ON_THE_FRAME = ("filter_wheel", "focuser", "guide_camera")
# I pezzi che la posa **porta** in una colonna sua: quelli sopra piu' la montatura, che non ha un
# grezzo suo -- la scrive `normalize`, dalla tua parola sul corredo o da `TELESCOP` quando il
# software dice che li' c'e' la montatura. Su questo elenco si legano le ore, si scrive la posa, si
# decide quali generi hanno le ore e si stacca un pezzo che sparisce: dimenticarne uno in una di
# quelle case e' un'unione che schianta.
CARRIED = (*ON_THE_FRAME, "mount")


def _pezzo(dai_corredi):
    """Il legame fra una posa e un pezzo, composto da **un pezzo solo**: come ci arriva dai
    corredi (che cambia con cio' che chi chiama ha nel `FROM`) piu' le colonne che la posa
    porta addosso, che sono sempre quelle."""
    return (  # noqa: S608 - generi del nostro elenco, mai valori dell'utente
        "(" + dai_corredi + "".join(f" OR f.{k}_id = i.id" for k in CARRIED) + ")"
    )


# La stessa condizione per chi ha **gia' i corredi nel suo `FROM`**: li' la sotto-select
# correlata costa una ricerca per ogni coppia (posa, pezzo), mentre la giunzione e' gia' fatta.
# Non e' un secondo legame: e' lo stesso, composto dalla stessa funzione, e una prova li tiene
# uguali (`test_the_shapes_of_the_link_pick_the_same_frames`).
_WITH_RIGS = _pezzo("i.id IN (g.optics_id, g.camera_id)")

# E la terza forma, per chi conta **tutti i pezzi insieme** raggruppando: le coppie (pezzo, posa),
# una volta ciascuna -- `UNION` toglie la posa che arriva allo stesso pezzo per due strade. Senza,
# chi conta tutti i pezzi fa i sotto-select correlati pezzo per pezzo, che su un archivio grande
# sono la parte piu' cara. Gli stessi generi, dallo stesso elenco: la prova e' la stessa di sopra.
_DAI_CORREDI = ("optics", "camera")
PIECE_FRAMES = " UNION ".join(
    [
        f"SELECT g.{k}_id AS piece, f.id AS frame FROM frames f"  # noqa: S608 - generi nostri
        f" JOIN rigs g ON g.id = f.rig_id WHERE g.{k}_id IS NOT NULL"
        for k in _DAI_CORREDI
    ]
    + [
        f"SELECT f.{k}_id AS piece, f.id AS frame FROM frames f WHERE f.{k}_id IS NOT NULL"  # noqa: S608
        for k in CARRIED
    ]
)

# Le pose che nessun mosaico confermato ha preso. L'Archivio racconta per GRUPPI, e le pose di un
# mosaico stanno solo nella sua riga: contarle anche in quella del loro oggetto le conterebbe due
# volte. Gli altri lettori -- Notti, Da confermare -- guardano l'oggetto intero, e non lo chiedono.
ALONE = "f.mosaic_key IS NULL"
_DEL_MOSAICO = "f.mosaic_key = r.mosaic_key"

# Su cosa si conta. Una voce nuova entra qui, con la sua tabella gia' nel `FROM` di chi chiama --
# tranne `archive`, che non ne ha bisogno: e' tutto cio' che una notte ha raccolto, e si chiede
# senza una riga a cui agganciarsi.
_SOGGETTI = {
    "object": "f.object_id = o.id",
    "night": "f.night_id = n.id",
    "archive": "f.night_id IS NOT NULL",
    "rig": "f.rig_id = g.id",
    "filter": "f.filter_id = x.id",
    # Le pose di un mosaico confermato, e quelle di una riga dell'Archivio -- un mosaico, o un
    # oggetto con le sole pose fuori dai mosaici -- per chi ha la riga `r` (`spine/archive.py`).
    "mosaic": _DEL_MOSAICO,
    # Le pose dei pannelli di un mosaico `m`, risposto o no: e' cio' che Da confermare propone.
    "proposal": "f.panel_id IN (SELECT p.id FROM panels p WHERE p.mosaic_id = m.id"
    " AND p.counts_in_mosaic = 1)",
    "row": f"({_DEL_MOSAICO} OR (r.mosaic_key IS NULL AND f.object_id = r.id AND {ALONE}))",
    # Un pezzo arriva alle sue pose per **due strade**, e le ore sono la somma delle due.
    # Ottica e camera passano dal **corredo**, che e' quello che la posa conosce. Ruota,
    # focheggiatore, camera di guida e montatura no: quelli la posa li porta addosso (`CARRIED`).
    "instrument": _pezzo(
        "f.rig_id IN (SELECT id FROM rigs WHERE optics_id = i.id OR camera_id = i.id)"
    ),
}

# Lo stesso conto quando si **raggruppa** invece di chiedere riga per riga, e l'ordine con cui si
# racconta un pezzo di archivio: prima cio' a cui e' stato dato piu' tempo. Stanno qui con gli
# altri per la stessa ragione -- due copie direbbero due numeri e due ordini.
AGGREGATE = "COUNT(*) AS frames, COALESCE(SUM(f.exposure_s), 0) AS integration_s"
# E le pose che non dicono quanto sono durate, nella stessa forma raggruppata.
UNTIMED = "SUM(f.exposure_s IS NULL) AS untimed"
ORDER_BY_TIME = "ORDER BY integration_s DESC, frames DESC"

# La colonna dentro un legame semplice (`f.qualcosa = x.id`). Chi raggruppa un lotto di soggetti
# ha bisogno del **nome della colonna**, non del `WHERE`, ma e' lo stesso fatto visto dall'altro
# lato: tenerne un secondo elenco vorrebbe dire due case che prima o poi divergono -- e la prova
# che le confrontasse guarderebbe due stringhe, non due significati. Qui si **ricava**.
_UNA_COLONNA = re.compile(r"f\.(\w+) = \w+\.\w+$")


def column_of(soggetto):
    """La colonna di `frames` che porta quel soggetto, **letta dal suo legame**.

    Alza per i soggetti il cui legame non e' una colonna sola -- l'archivio intero, il pezzo che
    arriva per due strade -- e deve alzare: raggrupparli su una colonna conterebbe altre pose. Non
    e' un elenco chiuso in meno: la chiave resta quella di `_SOGGETTI`, e cio' che cambia e' che la
    colonna non si puo' piu' scrivere diversa dal `WHERE` che le sta accanto."""
    dove = _SOGGETTI[soggetto]  # da un elenco chiuso: una chiave che non c'e' e' un KeyError
    trovata = _UNA_COLONNA.fullmatch(dove)
    if trovata is None:
        raise KeyError(f"il legame di {soggetto} non e' una colonna sola: {dove}")
    return trovata.group(1)


def of(soggetto, *, rigs_joined=False):
    """Il frammento di `WHERE` che lega una posa a quel soggetto. Sta qui e si chiede, invece
    di riscriverlo: chi conta **altro** sulle stesse pose -- le notti di un pezzo, per esempio --
    deve legarle allo stesso modo, o due numeri della stessa riga verrebbero da due definizioni.

    `rigs_joined` lo chiede chi ha gia' `rigs g` nel suo `FROM`: stessa condizione, senza la
    sotto-select che costerebbe una ricerca per ogni coppia."""
    dove = _SOGGETTI[soggetto]  # da un elenco chiuso, sempre: una chiave che non c'e' e' un
    # KeyError anche qui, o chi chiedesse i corredi con la forma giunta si prenderebbe in
    # silenzio la condizione del pezzo, cioe' numeri sbagliati senza nessun errore.
    if not rigs_joined:
        return dove
    if soggetto != "instrument":
        raise KeyError(f"la forma coi corredi esiste solo per il pezzo, non per {soggetto}")
    return _WITH_RIGS


def counts_on(soggetto):
    """I tre sotto-select -- `frames`, `integration_s`, `untimed` -- gia' scritti per quel
    soggetto. Chi chiama li infila nella sua `SELECT` e ha la riga di cui la pagina ha bisogno."""
    dove = of(soggetto)  # da un elenco chiuso: una chiave che non c'e' e' un KeyError
    tre = f"""
       (SELECT COUNT(*) FROM frames f
         WHERE {dove} AND f.copy_of IS NULL) AS frames,
       (SELECT COALESCE(SUM(f.exposure_s), 0) FROM frames f
         WHERE {dove} AND f.copy_of IS NULL) AS integration_s,
       (SELECT COUNT(*) FROM frames f
         WHERE {dove} AND f.copy_of IS NULL AND f.exposure_s IS NULL) AS untimed"""  # noqa: S608
    return tre
