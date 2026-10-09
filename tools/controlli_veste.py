"""Le classi della veste e il foglio della consegna: chi le scrive, e che sia quello.

Il contrasto lo misura `controlli_contrasto.py`: e' un altro mestiere, e teneva questo file sopra
il tetto di righe.

Vincoli non ovvi:

* **L'impronta e' un gesto, non una prova**: chi cambia il foglio puo' cambiare anche l'impronta.
  Serve a questo: renderlo un gesto **visibile nel diff**, perche' il CSS si porta alla lettera e
  una correzione fatta qui la cancellerebbe la consegna dopo (`handoff/design-brief.md`).
* **Una classe sbagliata non rompe niente**: non si applica, e la pagina resta nuda in quel punto
  senza che nessun test cada. Per questo la si cerca a mano di macchina.
* **Dove un mattone c'e', la sua classe si scrive li' dentro e basta.** Non e' teoria:
  `as-riga__conteggio` era finita in ventiquattro posti, e mentre la si riparava `as-campo` e
  `as-bottone` ci finivano da capo, in sette e dodici file.
"""

import hashlib
import os
import re

from controlli_contrasto import FOGLIO, STILI, leggi_foglio, sotto_soglia
from controlli_foglio import pavimenti_del_cielo

# L'impronta della consegna portata alla lettera. Si cambia SOLO riportando una consegna nuova
# dal progetto Claude Design, mai per far passare una modifica fatta qui. Resta una **mappa**
# anche con un foglio solo: quanti sono lo decide la consegna, non noi.
IMPRONTE = {
    FOGLIO: "219df05cb5da089f45bd757a17b9dec98b0ee7e53a3adf680d1a8b6a2917edc6",
}


# I fondi su cui l'app scrive: tutte le superfici, non solo quella dove un colore si e' visto la
# prima volta.
def _sorgenti(root):
    """I file dove una classe `as-*` puo' essere scritta: il codice della pagina **e la pagina**.

    `frontend/index.html` ci sta perche' e' li' che vive `.as-app`, da cui dipendono i reset e il
    contorno di fuoco di tutta l'app: un refuso li' spegne il fuoco da tastiera ovunque, e nessuna
    prova del frontend lo vedrebbe -- in jsdom il body e' un altro."""
    yield os.path.join(root, "frontend", "index.html")
    for cartella, _, files in os.walk(os.path.join(root, "frontend", "src")):
        if "stili" in cartella:
            continue
        for nome in sorted(files):
            if nome.endswith((".tsx", ".ts")):
                yield os.path.join(cartella, nome)


# I mattoni nostri e la classe che ognuno incapsula. Dove un mattone c'e', la sua classe si scrive
# **li' dentro e basta**: e' "un fatto, una casa" applicato alla veste. Non e' teoria --
# `as-riga__conteggio` era finita in ventiquattro posti, e mentre la si riparava `as-campo` e
# `as-bottone` ci finivano da
# capo, in sette e dodici file. Il giorno che il design rinomina una classe, chi non usa il mattone
# non viene segnalato da niente.
# Le varianti di colore di un filtro: **una per banda** del vocabolario, con le grafie che il
# foglio usa. Qui dicono **di chi e' quella classe**; che siano una per banda e che esistano nel
# foglio lo prova `frontend/tests/filtri-usati.test.ts`, e che questo elenco sia quello che il
# mattone scrive davvero lo prova `test_the_filter_variants_in_the_table...` accanto a questo
# file: senza, una banda dimenticata qui spegnerebbe la guardia proprio su quella classe.
_VARIANTI = (
    "l", "r", "g", "b", "ha", "hb", "oiii", "sii", "ha-oiii", "sii-oiii", "tri", "quad",
    "colori", "colori-lp", "colori-uvir", "ignoto", "senza",
)  # fmt: skip

MATTONI = {
    "frontend/src/Riga.tsx": ("as-riga__conteggio", "as-riga__prova"),
    # Dal v31 `as-campo` e' il campo di ricerca del foglio: il campo dei moduli, che aspetta
    # ancora il suo disegno, ha preso un nome suo per non vestirsi da ricerca.
    "frontend/src/Campo.tsx": ("as-campo-modulo", "as-campo-modulo__etichetta"),
    "frontend/src/CampoDiRicerca.tsx": ("as-campo-cerca",),
    "frontend/src/Ricerca.tsx": ("as-cerca", "as-trova"),
    "frontend/src/Tendina.tsx": (
        "as-tendina",
        "as-tendina-elenco",
        "as-tendina-coppia",
        "as-tendina__togli",
    ),
    "frontend/src/Bottone.tsx": ("as-bottone",),
    "frontend/src/Avviso.tsx": ("as-avviso",),
    "frontend/src/Semaforo.tsx": ("as-semaforo", "as-semaforo__lampade"),
    # La fila dei filtri con cui hai ripreso: la stessa nell'Archivio e nelle Notti, col colore che
    # viene dalla banda canonica e mai dal nome. Le varianti (`as-filtro--l`, `--ha`...) sono la
    # mappa che ci vive dentro: stanno qui con lei, o la mappa si ricopierebbe alla seconda pagina
    # -- ed e' **una per banda**, perche' accorparne due da' a un filtro il colore di un altro.
    "frontend/src/FiltriUsati.tsx": (
        "as-filtro",
        "as-filtri",
        "as-filtri__barra",
        "as-filtri__legenda",
        "as-filtri__voce",
        "as-filtri__pallino",
        *(f"as-filtro--{v}" for v in _VARIANTI),
    ),  # fmt: skip
    # La scala del cielo ha **tre forme**, e il foglio da' a ognuna un nome suo: `as-bortle-scegli*`
    # estesa (dove si sceglie), `as-bortle-letta*` compatta (dove si legge accanto a un luogo),
    # `as-bortle-scala*` la rampa intera, che il foglio assegna **al piede della barra e a
    # nient'altro**. Le prime due stanno nel mattone; la terza sta dove il foglio la manda.
    "frontend/src/ScalaDelCielo.tsx": (
        "as-bortle-scegli",
        "as-bortle-scegli__scala",
        "as-bortle-scegli__voce",
        "as-bortle-scegli__cifra",
        "as-bortle-scegli__estremi",
        "as-bortle-scegli__letta",
        "as-bortle-letta",
        "as-bortle-letta__fascia",
        "as-bortle-letta__classe",
        "as-bortle-letta__misura",
    ),
    "frontend/src/Stanotte.tsx": (
        "as-bortle-scala",
        "as-bortle-scala__dice",
        "as-bortle-scala__scala",
        "as-bortle-scala__voce",
        "as-bortle-scala__ignota",
        "as-bortle-scala__estremi",
    ),
}


def _senza_prosa(testo):
    """Il file senza i suoi commenti: i blocchi `/* ... */` e le righe che cominciano per `//`.

    Si toglie la **riga intera** solo quando comincia col segno, non da qualunque `//` in mezzo:
    un indirizzo dentro una stringa ne porta uno, e tagliare li' mangerebbe codice vero.

    **Dove non arriva**: un `/*` dentro una stringa mangia fino al primo `*/`, e li' il codice
    sparisce in silenzio. Oggi non succede -- in `frontend/src` non ce n'e' nessuno fuori da un
    commento -- ma un lessico vero al posto di questa regex e' l'unico modo di chiuderlo."""
    testo = re.sub(r"/\*.*?\*/", "", testo, flags=re.S)
    return "\n".join(r for r in testo.splitlines() if not r.lstrip().startswith("//"))


def classi_fuori_casa(root):
    """Le classi che hanno un mattone e sono scritte da un'altra parte.

    Si guardano **tutte** le classi scritte nel file, non solo quelle dentro `className="..."`: una
    copia nasce quasi sempre nella forma in cui il mattone stesso la scrive -- un ternario, una
    mappa di varianti -- e una guardia che vede solo la forma piu' semplice lascia passare proprio
    quella che conta.

    La classe **del controllo** (`as-campo__input`, `as-scelta`) resta dove sta il controllo: il
    mattone gli fa da involucro, non lo sostituisce. Per questo l'elenco nomina solo cio' che il
    mattone rende **di suo** -- e `as-campo` non aggancia `as-campo__input`, che e' un altro nome.

    L'esenzione e' per **percorso**, non per nome di file: un domani `pagine/Riga.tsx` non deve
    esentarsi perche' si chiama come il mattone. Ed e' per **la sua classe**, non per il file:
    saltare il file intero appena e' una casa lo esentava da tutti gli altri mattoni, e il primo
    file a pagarlo sarebbe stato quello dove `as-bottone` scritta a mano era gia' stata trovata.

    E **i commenti non si leggono**: in una docstring una classe e' prosa, e accusare un mattone di
    ospitare la classe di cui sta spiegando la differenza e' un falso allarme -- che costa quanto un
    silenzio, perche' si smette di dare retta alla macchina. Si toglie la prosa, non i backtick: una
    copia nasce quasi sempre **dentro una template**, e smettere di guardarle sarebbe barattare un
    falso allarme con un buco."""
    fuori = []
    for percorso in _sorgenti(root):
        detto = os.path.relpath(percorso, root).replace("\\", "/")
        if not os.path.isfile(percorso):
            continue
        with open(percorso, encoding="utf-8") as h:
            testo = _senza_prosa(h.read())
        scritte = set()
        for stringa in re.findall(r"""["'`]([^"'`\n]*\bas-[a-z0-9_-]+[^"'`\n]*)["'`]""", testo):
            scritte |= {c for c in stringa.split() if c.startswith("as-")}
        for casa, classi in MATTONI.items():
            if casa == detto:
                continue
            for classe in classi:
                if classe in scritte:
                    fuori.append(f"{detto}: {classe} (sta in {os.path.basename(casa)})")
    return sorted(fuori)


# I mattoni che un ruolo lo scrivono **di mestiere**, e che portano gia' il segno non cromatico
# che il foglio da' loro: `Avviso` (spunta e triangolo) e `Campo`, il cui errore vive dentro
# `as-campo--errore`. Non e' una allowlist di comodo -- ci entra un mattone, cioe' la casa unica
# di una classe, e per la stessa ragione per cui la regola esiste: il segno c'e'. `CartaSola`
# porta "l'app si apre", col segno dell'attesa del foglio (`.as-entra__attesa`).
MATTONI_CHE_PARLANO = {
    "frontend/src/Avviso.tsx",
    "frontend/src/Campo.tsx",
    "frontend/src/CartaSola.tsx",
}


def avvisi_a_mano(root):
    """Gli avvisi scritti senza passare da `Avviso`.

    E' la stessa regola delle classi, su un'altra cosa: il mattone c'e', e chi non lo usa perde
    cio' che il mattone porta -- qui il **segno non cromatico** (spunta o triangolo), senza il
    quale l'esito e' detto dal colore soltanto e chi non distingue verde e rosso non lo legge
    (WCAG 2.2, 1.4.1). Dodici volte in nove file, mentre la regola era scritta in prosa.

    Si cercano i **due ruoli che `Avviso` sa fare**, `alert` e `status`, e non ogni `role`: la
    barra ne ha uno, una sezione un altro, e una guardia che gridasse su quelli verrebbe spenta.

    Ma un ruolo **scritto in un modo che non so leggere** si dice, invece di tacere: `Avviso`
    stesso scrive `role={ruolo}`, quindi chi lo ricopia parte da li' -- e' la stessa ragione per
    cui `classi_fuori_casa` guarda i ternari e le mappe, non solo le stringhe. Un `role={...}` da
    cui non esce nessun ruolo scritto e' una colpa col suo nome.

    **Dove non arriva**: un ruolo passato per attributi sparsi (`{...{role: "alert"}}`) o composto
    a pezzi da una variabile. Dichiararlo e' meglio che lasciar credere che sia stato guardato."""
    fuori = []
    for percorso in _sorgenti(root):
        detto = os.path.relpath(percorso, root).replace("\\", "/")
        if detto in MATTONI_CHE_PARLANO or not os.path.isfile(percorso):
            continue
        with open(percorso, encoding="utf-8") as h:
            testo = h.read()
        detti = re.findall(r"""role\s*=\s*["'](\w+)["']""", testo)
        graffe = re.findall(r"role\s*=\s*\{([^}]*)\}", testo)
        detti += [r for pezzo in graffe for r in re.findall(r"""["'](\w+)["']""", pezzo)]
        if {"alert", "status"} & set(detti):
            fuori.append(f"{detto}: un avviso a mano (usa Avviso)")
            continue
        for pezzo in graffe:
            if not re.search(r"""["']\w+["']""", pezzo):
                fuori.append(f"{detto}: un ruolo che non so leggere (role={{{pezzo.strip()}}})")
    return sorted(fuori)


def tutti(root: str) -> list[tuple[str, list[str]]]:
    """I controlli della veste, gia' col loro titolo: `[(cosa si guarda, cio' che non va)]`.

    L'elenco sta qui e non nel cancello perche' e' un fatto di questo modulo -- chi aggiunge un
    controllo lo aggiunge dove lo scrive, e il cancello resta un ciclo di due righe."""
    return [
        ("contrasto dei token (WCAG 1.4.3 e 1.4.11)", sotto_soglia(root)),
        ("classi as-* che il foglio non ha", classi_inventate(root)),
        ("classi scritte fuori dal loro mattone", classi_fuori_casa(root)),
        ("avvisi scritti senza il mattone Avviso", avvisi_a_mano(root)),
        ("fogli della consegna toccati a mano", fogli_cambiati(root)),
        ("pavimenti della scala citati nel foglio", pavimenti_del_cielo(root)),
    ]


# Le classi del v10 che le pagine non ancora ridisegnate scrivono e il foglio v27 non ha (ADR 0018).
ATTESA = ("tools", "classi_in_attesa.txt")


def classi_in_attesa(root: str) -> set[str]:
    """L'elenco dichiarato delle classi in attesa; vuoto se il file non c'e'."""
    percorso = os.path.join(root, *ATTESA)
    if not os.path.isfile(percorso):
        return set()
    with open(percorso, encoding="utf-8") as h:
        righe = (r.strip() for r in h)
        return {r for r in righe if r and not r.startswith("#")}


def classi_usate(root: str) -> tuple[set[str], list[str]]:
    """Le classi `as-*` scritte nel codice, e i posti dove non si riesce a leggerle.

    Si leggono le classi **scritte per esteso**, anche dentro le graffe (`className={... "as-x"}`),
    che e' come nascono gli stati di una riga. Dove da un `className={...}` non esce **nessuna**
    classe scritta -- una variabile, una funzione che la compone, un pezzo attaccato a un altro --
    si **dice**, e si dice anche se li' dentro la parola `as-` non compare affatto: e' proprio la
    forma in cui una classe sfugge (`className={classeRiga(stato)}`). Una guardia che tace dove non
    arriva e' peggio di una che non c'e', perche' sembra che abbia guardato."""
    usate: set[str] = set()
    illeggibili: list[str] = []
    for percorso in _sorgenti(root):
        if not os.path.isfile(percorso):
            continue
        with open(percorso, encoding="utf-8") as h:
            testo = h.read()
        detto = os.path.relpath(percorso, root).replace("\\", "/")
        # ogni stringa del file che contiene una classe: un mattone le tiene in una mappa, non
        # dentro l'attributo, e guardare solo `className` lascerebbe fuori proprio i mattoni.
        # Apici soltanto, mai i backtick: in una docstring `as-campo*` e' prosa, non una classe.
        for stringa in re.findall(r"""["']([^"'\n]*\bas-[a-z0-9_-]+[^"'\n]*)["']""", testo):
            usate |= {c for c in stringa.split() if c.startswith("as-")}
        for scritto in re.findall(r'class(?:Name)?="([^"]*)"', testo):
            usate |= {c for c in scritto.split() if c.startswith("as-")}
        for dentro_graffe in _fra_graffe(testo):
            parole = []
            for stringa in re.findall(r'["\'`]([^"\'`]*)["\'`]', dentro_graffe):
                parole += stringa.split()
            if not parole:
                illeggibili.append(
                    f"{detto}: una classe che non so leggere ({dentro_graffe.strip()[:40]})"
                )
            usate |= {c for c in parole if c.startswith("as-")}
    return usate, illeggibili


def classi_inventate(root: str) -> list[str]:
    """Le classi `as-*` scritte nel codice che nel foglio non esistono, e i posti dove non si
    riesce a leggerle.

    Una classe sbagliata non rompe niente: non si applica, e la pagina resta nuda in quel punto
    senza che nessun test cada. Successo scrivendo questa stessa fetta -- `as-elenco-nudo`, che
    non e' mai esistito -- e lo ha trovato una rilettura, non una macchina.

    **Le classi in attesa** (`tools/classi_in_attesa.txt`, ADR 0018) passano: sono le pagine non
    ancora ridisegnate, che restano funzionanti ma spoglie. L'elenco **solo si accorcia**: una voce
    che il codice non scrive piu', o che il foglio ora ha, e' un rosso, cosi' non resta li' a
    coprire una classe nuova con lo stesso nome."""
    testo = leggi_foglio(root)
    if isinstance(testo, list):
        return testo
    nel_foglio = set(re.findall(r"\.(as-[a-z0-9_-]+)", testo))
    usate, illeggibili = classi_usate(root)
    attesa = classi_in_attesa(root)
    elenco = "/".join(ATTESA)
    fuori = set(illeggibili) | (usate - nel_foglio - attesa)
    fuori |= {f"{elenco}: {c} il codice non la scrive piu', togli la voce" for c in attesa - usate}
    fuori |= {f"{elenco}: {c} il foglio ora la ha, togli la voce" for c in attesa & nel_foglio}
    return sorted(fuori)


def _fra_graffe(testo):
    """Il contenuto di ogni `className={...}`, **con le graffe bilanciate**.

    Una regex si ferma alla prima graffa chiusa, e su una classe composta -- `` `${VERSI[verso]}` ``
    -- taglia a meta' e fa dire alla guardia che non sa leggere cio' che invece e' li'. Un falso
    allarme costa quanto un silenzio: si smette di dare retta alla macchina."""
    for apre in re.finditer(r"class(?:Name)?=\{", testo):
        i, aperte = apre.end(), 1
        while i < len(testo) and aperte:
            aperte += {"{": 1, "}": -1}.get(testo[i], 0)
            i += 1
        yield testo[apre.end() : i - 1]


def fogli_cambiati(root):
    """I fogli della consegna che non sono piu' quelli consegnati -- o che non ci sono."""
    fuori = []
    for nome, impronta in IMPRONTE.items():
        percorso = os.path.join(root, *STILI, nome)
        detto = "/".join((*STILI, nome))
        if not os.path.isfile(percorso):
            fuori.append(detto)
            continue
        with open(percorso, "rb") as h:
            byte = h.read()
        if hashlib.sha256(byte).hexdigest() == impronta:
            continue
        # Il caso che altrimenti si presenta come "qualcuno ha toccato il foglio" senza che
        # nessuno l'abbia toccato: i fine riga riscritti al checkout. Sta chiuso in
        # `.gitattributes`, ma se quella riga sparisse il rosso direbbe la cosa sbagliata.
        raddrizzato = hashlib.sha256(byte.replace(b"\r\n", b"\n")).hexdigest()
        perche = " (sono i fine riga: guarda .gitattributes)" if raddrizzato == impronta else ""
        fuori.append(detto + perche)
    return fuori
