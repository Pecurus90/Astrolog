"""Chiedere a SIMBAD cio' che al nostro catalogo manca: nomi propri, magnitudini, dimensioni.

E' uno strumento di COSTRUZIONE: gira quando si rifa' il catalogo, mai dentro l'app -- la
spina non tocca la rete in nessun punto. Il trasporto si passa come argomento (`posta=`),
cosi' i test non chiamano il servizio.

Vincoli non ovvi, tutti pagati in `old/`:

* **Si chiede a lotti.** Una richiesta per oggetto sarebbe ventimila richieste: il servizio
  e' pubblico e gratuito, e la sua politica non le gradisce.
* **La risposta si riaggancia alla sigla CHIESTA**, che la query si fa restituire (`i.id`).
  SIMBAD riscrive gli identificatori -- si chiede `Abell 1136` e torna `ACO  1136`, che cambia
  il nome del catalogo, non solo la spaziatura. Riagganciare sulla sua grafia vorrebbe dire
  attribuire il dato di un oggetto a un altro.
* **I nomi propri si prendono un catalogo per volta.** SIMBAD li tiene come identificatori
  `NAME ...`: una query per catalogo li prende tutti, e riempire ventimila nomi costa
  diciotto richieste invece di ventimila.
* **Un guasto di rete non e' "non lo conosco".** Confonderli vorrebbe dire non richiedere mai
  piu' una voce che il servizio conosceva benissimo, il giorno che la rete non andava.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request

TAP_URL = "https://simbad.cds.unistra.fr/simbad/sim-tap/sync"
USER_AGENT = "AstroLog/0.1 (https://github.com/Pecurus90/Astrolog)"
TIMEOUT_S = 30

# Quante SIGLE per richiesta. Ognuna diventa piu' stringhe (vedi `forme`), quindi il lotto e'
# piu' piccolo di quanto sembri: cinquanta sigle sono duecentocinquanta stringhe.
LOTTO = 50

# In SIMBAD il numero e' allineato a destra in un campo a larghezza fissa -- `M   1`, `M  11`,
# `M 110`, `NGC   224`, `NGC  2237` -- e la larghezza cambia col catalogo. Chiedere con la
# nostra grafia (`M 11`) non trova NIENTE, in silenzio. Invece di indovinare la larghezza si
# chiedono tutte le spaziature plausibili: costa una lista piu' lunga nella stessa richiesta,
# non piu' richieste.
SPAZI = range(1, 6)

# Come SIMBAD chiama i cataloghi che chiamiamo in un altro modo. **Misurato**, non supposto:
# chiedendo `Abell 1136` non risponde nessuno, chiedendo `ACO  1136` si'.
ALTRO_NOME = {"Abell": "ACO", "Arp": "APG", "B": "Barnard"}
# Il servizio e' pubblico: si va piano anche quando nessuno lo impone.
PAUSA_S = 0.25

# Il nome proprio in SIMBAD e' un identificatore che comincia cosi'.
PREFISSO_NOME = "NAME "

# Le misure che ci mancano, in una query sola: dimensioni e magnitudine in banda V.
# `i.id` e' cio' che rende possibile il riaggancio: e' la sigla come l'abbiamo chiesta.
_ADQL_MISURE = (
    "SELECT i.id, b.main_id, b.galdim_majaxis, b.galdim_minaxis, f.flux "
    "FROM ident AS i "
    "JOIN basic AS b ON b.oid = i.oidref "
    "LEFT JOIN flux AS f ON f.oidref = b.oid AND f.filter = 'V' "
    "WHERE i.id IN ({lista})"
)

# I nomi curati di un intero catalogo: chi ha un identificatore `NAME ...` e uno del catalogo.
_ADQL_NOMI = (
    "SELECT ic.id AS catcode, inm.id AS proper "
    "FROM ident AS inm "
    "JOIN ident AS ic ON ic.oidref = inm.oidref "
    "WHERE inm.id LIKE 'NAME %' AND ic.id LIKE '{like}'"
)


class SimbadNonRispondeError(Exception):
    """Il servizio non ha risposto, o ha risposto qualcosa che non si capisce. **Non** vuol
    dire "la voce non esiste": quella e' semplicemente assente dal risultato."""


def _cita(testo):
    """Una stringa dentro l'ADQL: gli apici si raddoppiano. Senza, un nome con l'apice
    romperebbe la query -- o la riscriverebbe."""
    return "'" + str(testo).replace("'", "''") + "'"


def _posta(url, query, timeout_s):
    """L'unico posto che tocca la rete. Chi lo sostituisce nei test passa `posta`."""
    dati = urllib.parse.urlencode(
        {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "json", "QUERY": query}
    ).encode()
    req = urllib.request.Request(  # noqa: S310 - solo https, host costante di questo file
        url, data=dati,
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"},
    )  # fmt: skip
    with urllib.request.urlopen(req, timeout=timeout_s) as r:  # noqa: S310 - idem
        return json.loads(r.read().decode("utf-8", "replace"))


def _chiedi(posta, query, timeout_s):
    """Chiede, e traduce ogni guasto in `SimbadNonRispondeError`. La traduzione sta QUI e non nel
    trasporto: chi inietta un trasporto suo (i test, o domani una cache) deve ottenere lo
    stesso patto, o il guasto passerebbe crudo e chi chiama lo scambierebbe per un errore
    di programmazione."""
    try:
        return _righe((posta or _posta)(TAP_URL, query, timeout_s))
    except SimbadNonRispondeError:
        raise
    except Exception as err:  # noqa: BLE001 - qualunque guasto del trasporto e' "non risponde"
        raise SimbadNonRispondeError(f"{type(err).__name__}: {err}") from err


def _righe(risposta):
    """`(nomi delle colonne, righe)` da una risposta TAP. Una risposta che non ha quella forma
    e' un guasto, non un risultato vuoto: HTML di errore, JSON storto, `None`."""
    try:
        colonne = [c["name"] for c in risposta["metadata"]]
        return colonne, list(risposta["data"])
    except (TypeError, KeyError, IndexError) as err:
        raise SimbadNonRispondeError(f"risposta che non si capisce: {type(err).__name__}") from err


def _numero(v):
    """Un numero, o `None`. Mai zero di ripiego: una dimensione a zero sarebbe un oggetto
    puntiforme e una magnitudine a zero un oggetto luminosissimo."""
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def forme(sigla):
    """Tutte le grafie con cui SIMBAD potrebbe conoscere questa sigla."""
    catalogo, _, resto = str(sigla).strip().partition(" ")
    nome = ALTRO_NOME.get(catalogo, catalogo)
    resto = resto.strip()
    return [f"{nome}{' ' * n}{resto}" for n in SPAZI] if resto else [nome]


def _lotti(elenco, quanti):
    for i in range(0, len(elenco), quanti):
        yield elenco[i : i + quanti]


def misure(sigle, *, posta=None, pausa=time.sleep, timeout_s=TIMEOUT_S):
    """`{sigla chiesta: {size_major_arcmin, size_minor_arcmin, magnitude}}`.

    Chi manca dal risultato e' una voce che SIMBAD non conosce: il chiamante la registra come
    tale e non la richiede piu'. Un guasto di rete solleva invece di tacere."""
    fuori = {}
    for i, lotto in enumerate(_lotti(list(sigle), LOTTO)):
        if i:
            pausa(PAUSA_S)
        # ogni sigla diventa piu' grafie, e ognuna sa da quale sigla nostra viene
        nostra = {f: sigla for sigla in lotto for f in forme(sigla)}
        query = _ADQL_MISURE.format(lista=", ".join(_cita(f) for f in nostra))
        colonne, righe = _chiedi(posta, query, timeout_s)
        dove = {nome: p for p, nome in enumerate(colonne)}
        for riga in righe:
            chiesta = nostra.get(str(riga[dove["id"]]))
            if chiesta is None:
                continue  # SIMBAD ha risposto con un identificatore che non abbiamo chiesto
            fuori[chiesta] = {
                "size_major_arcmin": _numero(riga[dove["galdim_majaxis"]]),
                "size_minor_arcmin": _numero(riga[dove["galdim_minaxis"]]),
                "magnitude": _numero(riga[dove["flux"]]),
            }
    return fuori


def nomi(catalogo, *, posta=None, timeout_s=TIMEOUT_S):
    """`{sigla NOSTRA: nome proprio}` per un intero catalogo, in una richiesta sola.

    Si chiede col nome che SIMBAD usa (`ACO`, non `Abell`) e si torna col nostro, o il
    chiamante non saprebbe a quale voce appartiene: e' la stessa regola delle misure, e
    valeva anche qui.

    I nomi restano **in inglese**: "Rosette Nebula" e' il nome dell'oggetto, non una frase da
    tradurre."""
    loro = ALTRO_NOME.get(catalogo, catalogo)
    query = _ADQL_NOMI.format(like=f"{loro} %")
    colonne, righe = _chiedi(posta, query, timeout_s)
    dove = {nome: p for p, nome in enumerate(colonne)}
    fuori = {}
    for riga in righe:
        proprio = str(riga[dove["proper"]]).strip()
        if proprio.startswith(PREFISSO_NOME):
            proprio = proprio[len(PREFISSO_NOME) :].strip()
        if proprio:
            # il codice torna nella grafia di SIMBAD (`ACO  1136`): si riporta alla nostra
            codice = " ".join(str(riga[dove["catcode"]]).split())
            if loro != catalogo and codice.startswith(loro + " "):
                codice = catalogo + codice[len(loro) :]
            fuori[codice] = proprio
    return fuori
