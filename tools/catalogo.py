"""Il catalogo degli oggetti celesti: quali campi lo compongono, e come si legge e si scrive.

E' uno strumento di COSTRUZIONE, non un pezzo dell'app: la spina non tocca la rete e non
rigenera cataloghi. L'app legge il file finito; qui lo si snellisce e lo si completa.

Vincolo non ovvio: un campo resta se **l'app ci decide qualcosa** (coordinate, sigle, tipo,
dimensione, magnitudine) o se **chi legge la scheda lo cercherebbe** (nome comune, distanza,
luminosita' superficiale, opacita'). Tutto il resto e' peso e rumore, e quattro campi sono
usciti per questo (decisione di Marco, 2026-09-08). La magnitudine e' **un campo solo con la
sua banda**: due colonne separate costringevano ogni lettore a rifare la cascata "prima V poi
B", e coprivano il 28% invece del 69%.
"""

import json
from pathlib import Path

# I campi di una voce, elenco CHIUSO. Cio' che una fonte porta in piu' non entra di nascosto.
CAMPI = (
    # identita': lo slug e' l'ancora fra due ricostruzioni, gli id si rinumerano
    "slug", "name", "n",
    # il cielo, senza il quale una voce non e' una voce
    "ra", "dec", "constellation",
    # cosa e': il nostro codice e le famiglie per i filtri
    "type_code", "kind", "k",
    # la forma: identify ci sceglie il soggetto, il Planner ci dice "ci sta nel campo"
    "size_major_arcmin", "size_minor_arcmin", "position_angle_deg",
    # quanto e' luminoso, e in quale banda lo si e' misurato
    "magnitude", "magnitude_band",
    # cio' che si legge nella scheda
    "surface_brightness", "distance_ly", "opacity", "common_name",
    # da dove viene ogni valore
    "src",
)  # fmt: skip

# La cascata della magnitudine: la V e' la banda con cui si giudica un oggetto a occhio e in
# fotografia; la B e' piu' blu e su una nebulosa rossa la fa sembrare piu' debole di quanto sia.
BANDE = (("magnitude_v", "V"), ("magnitude_b", "B"))


def _magnitudine(voce):
    """`(valore, banda)` dalla cascata, o `(None, None)`. Una gia' fusa resta com'e'."""
    if voce.get("magnitude") is not None:
        return voce["magnitude"], voce.get("magnitude_band")
    for campo, banda in BANDE:
        if voce.get(campo) is not None:
            return voce[campo], banda
    return None, None


def _provenienza(voce, tenuti):
    """`src` ridotta ai campi rimasti. Una riga che parlasse di un campo uscito resterebbe a
    raccontare un dato che non c'e' piu'."""
    src = voce.get("src") or {}
    fuori = dict(src)
    prevalente = fuori.pop("_", None)
    out = {k: v for k, v in fuori.items() if k in tenuti}
    # la magnitudine ha cambiato nome fondendosi: la provenienza segue il valore
    for campo, _banda in BANDE:
        if campo in fuori and tenuti.get("magnitude") == voce.get(campo):
            out["magnitude"] = fuori[campo]
            out.pop(campo, None)
    if prevalente:
        out["_"] = prevalente
    return out


def snellisci_con_scarti(voci):
    """`(voci snellite, slug scartati)`. Si scarta chi non ha un cielo: senza coordinate non
    si puo' ne' riconoscere ne' disegnare, e tenerlo vorrebbe dire una riga che non risponde
    a nessuna domanda."""
    tenute, scarti = [], []
    for voce in voci:
        if voce.get("ra") is None or voce.get("dec") is None:
            scarti.append(voce.get("slug"))
            continue
        valore, banda = _magnitudine(voce)
        nuova = {k: v for k, v in voce.items() if k in CAMPI and k != "src" and v is not None}
        nuova.pop("magnitude", None)
        nuova.pop("magnitude_band", None)
        if valore is not None:
            nuova["magnitude"], nuova["magnitude_band"] = valore, banda
        src = _provenienza(voce, nuova)
        if src:
            nuova["src"] = src
        tenute.append(nuova)
    return tenute, scarti


def snellisci(voci):
    return snellisci_con_scarti(voci)[0]


def leggi(percorso):
    """Il catalogo dal disco: `(intestazione, voci)`. L'intestazione porta versione, data e
    le versioni delle sorgenti -- serve a sapere cosa si sta guardando."""
    dati = json.loads(Path(percorso).read_text(encoding="utf-8"))
    voci = dati.pop("objects", [])
    return dati, voci


def scrivi(percorso, intestazione, voci):
    """Il catalogo sul disco, compatto: e' un dato che viaggia col programma, non un file da
    leggere a mano."""
    dati = {**intestazione, "objects": voci}
    Path(percorso).write_text(
        json.dumps(dati, separators=(",", ":"), ensure_ascii=False), encoding="utf-8"
    )
    return Path(percorso).stat().st_size


# I due campi che l'arricchimento riempie, e nient'altro: sono quelli con cui l'app decide
# (la dimensione sceglie il soggetto e inquadra, la magnitudine ordina i candidati) piu' il
# nome, che l'app non usa ma senza il quale mostra "NGC 1976" dove serve "Orion Nebula".
ARRICCHIBILI = ("magnitude", "size_major_arcmin", "size_minor_arcmin")


def normalizza_sigla(testo):
    """Una sigla confrontabile. SIMBAD scrive `NGC  4490` con due spazi e `M  31` idem: senza
    questa, l'aggancio fallisce **in silenzio** -- nessun errore, solo nomi che non arrivano."""
    return " ".join(str(testo).split()).upper()


def e_un_nome(testo):
    """Un nome comune, o una sigla travestita?

    SIMBAD tiene sotto `NAME ...` anche designazioni di altri cataloghi -- `VV 543E`,
    `Her 36`, `IRAS F13373+0105 SE`. Scritte nella scheda sarebbero peggio della sigla che
    sostituiscono, perche' sembrerebbero un nome vero. La regola e' grossolana di proposito:
    **un nome comune non contiene cifre**. Si perde qualche nome vero che le ha (`30 Doradus`),
    e si e' scelto cosi': un nome mancante si vede, un nome falso no."""
    testo = str(testo or "").strip()
    return bool(testo) and not any(c.isdigit() for c in testo)


def sigle(voce):
    """Le sigle di una voce come stringhe (`M 31`), la principale per prima."""
    return [f"{c} {d}" for c, d in (voce.get("n") or ())]


def da_chiedere(voci, assenti=()):
    """Le sigle da portare a SIMBAD: solo le voci a cui manca almeno uno dei campi che
    l'arricchimento riempie, e che non si sia gia' interrogate a vuoto.

    Si chiede la principale: e' quella con cui il servizio ha piu' probabilita' di rispondere,
    e una richiesta per sigla moltiplicherebbe per tre il traffico."""
    assenti = set(assenti)
    fuori = []
    for voce in voci:
        if all(voce.get(c) is not None for c in ARRICCHIBILI):
            continue
        principale = next(iter(sigle(voce)), None)
        if principale and principale not in assenti:
            fuori.append(principale)
    return fuori


def arricchisci(voci, *, nomi, misure):
    """`(voci, {campo: quante riempite})`.

    **Non sovrascrive mai.** E' la regola pagata in `old/`: le sorgenti si sommano, non si
    sostituiscono. Un valore che c'e' gia' e' stato scelto da una cascata di precedenze fra
    fonti curate -- e una delle correzioni a mano e' proprio un nome che le fonti sbagliano.
    Lasciarlo riscrivere da un servizio esterno butterebbe via quella scelta in silenzio."""
    # Le chiavi si normalizzano QUI, una volta: chi passa i dizionari non deve ricordarsene,
    # e dimenticarsene faceva fallire l'aggancio in silenzio.
    nomi = {normalizza_sigla(k): v for k, v in nomi.items()}
    misure = {normalizza_sigla(k): v for k, v in misure.items()}
    conto = dict.fromkeys((*ARRICCHIBILI, "common_name"), 0)
    fuori = []
    for voce in voci:
        nuova = dict(voce)
        src = dict(nuova.get("src") or {})
        mie = sigle(nuova)

        if not nuova.get("common_name"):
            for sigla in mie:
                proposto = nomi.get(normalizza_sigla(sigla))
                if proposto and e_un_nome(proposto):
                    nuova["common_name"] = proposto
                    src["common_name"] = "simbad"
                    conto["common_name"] += 1
                    break

        trovata = misure.get(normalizza_sigla(mie[0])) if mie else None
        for campo in ARRICCHIBILI:
            if trovata and nuova.get(campo) is None and trovata.get(campo) is not None:
                nuova[campo] = trovata[campo]
                src[campo] = "simbad"
                conto[campo] += 1
        if nuova.get("magnitude") is not None and not nuova.get("magnitude_band"):
            # una magnitudine da SIMBAD e' in banda V (la query chiede `filter = 'V'`):
            # senza dirlo sarebbe un numero muto, e nessuno saprebbe quanto vale
            nuova["magnitude_band"] = "V"
        if src:
            nuova["src"] = src
        fuori.append(nuova)
    return fuori, conto


class CorrezioneScadutaError(Exception):
    """Una correzione che non trova piu' il valore sbagliato che doveva togliere: la fonte si
    e' corretta, e la pezza va tolta invece di sovrascrivere un dato ormai giusto."""


def correggi(voci, correzioni, *, severa=False):
    """Applica le correzioni curate: `(voci, quante applicate)`.

    Sono valori che una fonte **afferma** e che sappiamo falsi -- SIMBAD dice che `IC 434` e'
    la Flame Nebula, e non lo e': quella e' NGC 2024. Hanno **l'ultima parola**, dopo ogni
    arricchimento: senza, ogni giro reintroduce un errore che qualcuno aveva gia' chiuso.

    Il campo `da` dice quale valore sbagliato ci si aspetta di trovare, ed e' la scadenza:
    quando la fonte si corregge da sola, la correzione non serve piu' e `severa=True` lo
    grida invece di lasciarla li' a sovrascrivere per sempre."""
    per_sigla = {}
    for c in correzioni:
        per_sigla.setdefault(normalizza_sigla(f"{c['catalogo']} {c['designazione']}"), []).append(c)
    fatte = 0
    fuori = []
    for voce in voci:
        nuova = dict(voce)
        for sigla in sigle(nuova):
            for c in per_sigla.get(normalizza_sigla(sigla), ()):
                attuale = nuova.get(c["campo"])
                if attuale == c["a"]:
                    continue  # gia' applicata: e' il suo effetto, non una scadenza
                if attuale != c["da"]:
                    if severa and attuale is not None:
                        raise CorrezioneScadutaError(
                            f"{sigla} {c['campo']}: mi aspettavo {c['da']!r}, trovo {attuale!r}"
                        )
                    continue
                if c["a"] is None:
                    nuova.pop(c["campo"], None)
                else:
                    nuova[c["campo"]] = c["a"]
                src = dict(nuova.get("src") or {})
                src[c["campo"]] = "correzione"
                if c["a"] is None:
                    src.pop(c["campo"], None)
                nuova["src"] = src
                fatte += 1
        fuori.append(nuova)
    return fuori, fatte


def sconosciute(chieste, trovate, gia_note=()):
    """Le sigle che il servizio non conosce: si chiedono una volta e ci si ricorda.

    Il confronto passa dalla normalizzazione, come l'aggancio: senza, le voci **trovate**
    finivano in lista nera e non venivano piu' chieste, in silenzio e per sempre."""
    viste = {normalizza_sigla(s) for s in trovate}
    return sorted({*gia_note} | {s for s in chieste if normalizza_sigla(s) not in viste})


def copertura(voci):
    """`{campo: quante voci ce l'hanno}`: e' la misura con cui si dice se un arricchimento e'
    servito a qualcosa."""
    return {c: sum(1 for v in voci if v.get(c) is not None) for c in CAMPI}
