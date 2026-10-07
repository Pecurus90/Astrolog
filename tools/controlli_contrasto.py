"""Il contrasto dei token, **misurato** sui valori veri del foglio.

Perche' sta qui e non nella suite del frontend: axe, dentro jsdom, non ha layout e non carica CSS.
Un contrasto li' dentro non lo puo' misurare nessuno, e la guardia di accessibilita' resterebbe
verde per sempre senza aver guardato un colore.

Vincoli non ovvi:

* **La soglia non viene da noi**: WCAG 2.2, 1.4.3 chiede 4,5:1 al testo normale e 1.4.11 chiede
  3:1 a cio' che porta significato con la forma (una linea che distingue uno stato, il tratteggio
  del "non si sa").
* **`--inchiostro-spento` e' fuori dall'elenco**: nel v27 porta solo testo disabilitato
  (`.as-calendario__vai:disabled`), che 1.4.3 esenta, e non arriva a 4,5:1 (fra 2,08 e 2,77:1,
  misurato). **Il giorno che porta testo vivo la coppia entra qui** e il colore si corregge alla
  fonte, perche' il foglio si porta alla lettera.
* **Un colore con trasparenza non ha un contrasto suo**: si compone sul fondo. Misurare un
  `rgb(var(--tinta-velo) / .34)` come tinta piena darebbe un contrasto alto su qualunque cosa,
  cioe' un banco che si fa dire di si'.
* **Ogni inchiostro si prova su TUTTI i fondi di superficie**, non su quello dove lo si e' visto la
  prima volta: la riga sotto il mouse, la riga premuta e il campo sono fondi diversi, e un
  inchiostro che passa solo sul piu' scuro si rompe la prima volta che qualcuno lo mette altrove.
"""

import os
import re

STILI = ("frontend", "src", "stili")

# Il foglio della consegna, dove stanno i token **e** le classi. Il nome sta qui e non in
# `controlli_veste.py` perche' e' quello a importare da questo modulo, non il contrario: scritto
# di la' servirebbe un import all'incontrario, e i due moduli si terrebbero per mano.
FOGLIO = "astrolog.css"

FONDI = (
    "--fondo-app",
    "--fondo-app-basso",
    "--fondo-carta",
    "--fondo-carta-alta",
    "--fondo-rilievo",
    "--fondo-incavo",
)

# I fondi che **non sono opachi**: un velo non ha un colore suo, prende quello di sotto. Vanno
# dichiarati con la superficie su cui poggiano, o misurarli vorrebbe dire comporli sul nero e
# leggere un contrasto che nessuno vede. `--velo-vetro` e' il fondo della barra in alto
# (`.as-telaio__alto`): senza questa tabella non sarebbe misurato.
FONDI_VELATI = (
    ("--velo-vetro", "--fondo-app"),
    ("--velo-vetro", "--fondo-carta"),
)

# Le pastiglie: un velo di colore con **il suo** inchiostro, mai un altro. Misurare ogni
# inchiostro su ogni velo darebbe rossi per accostamenti che nessuno scrive -- un grigio dentro
# una pastiglia verde -- e un banco che grida al lupo si smette di ascoltarlo come uno che tace.
# Chi sta dentro cosa lo dice il foglio (`.as-stato--allarme`, le voci scelte su `--accento-velo`).
SOPRA_VELO = (
    ("--esito-allarme-inchiostro", "--esito-allarme-velo", "--fondo-carta"),
    ("--ignoto-inchiostro", "--ignoto-fondo", "--fondo-carta"),
    ("--inchiostro-accento", "--accento-velo", "--fondo-carta"),
    ("--inchiostro-accento", "--accento-velo", "--fondo-app-basso"),
    # la voce corrente del telaio e la voce scelta di menu e strati: inchiostro pieno sul velo
    ("--inchiostro", "--accento-velo", "--fondo-app-basso"),
    ("--inchiostro", "--accento-velo", "--fondo-carta"),
    # il bottone premuto, il piu' carico dei tre vetri; il nudo premuto porta l'inchiostro d'accento
    ("--inchiostro", "--vetro-premuto", "--fondo-carta"),
    ("--inchiostro-accento", "--vetro-premuto", "--fondo-carta"),
    ("--inchiostro-tenue", "--vetro-sopra", "--fondo-carta"),  # il segno dell'avviso
)

# Gli inchiostri che portano parole: 1.4.3, 4,5:1.
INCHIOSTRI = (
    "--inchiostro",
    "--inchiostro-tenue",
    "--inchiostro-debole",
    "--inchiostro-accento",
    "--freddo",
    "--ignoto-inchiostro",
    "--esito-buono-inchiostro",
    "--esito-attesa-inchiostro",
    "--esito-allarme-inchiostro",
)

# Cio' che dice qualcosa con la FORMA: 1.4.11, 3:1.
#
# Le nove fasce della scala di Bortle stanno qui e non fra gli inchiostri: non portano parole -- la
# classe e' sempre scritta col suo numero accanto -- ma sono **segni che portano significato**, e
# una scala di colori che si confonde col fondo non dice piu' quale fascia e' quale. Ci stanno
# tutte e nove perche' una rampa la si legge **insieme**: misurare solo i due estremi lascerebbe
# scoperto il centro, che e' dove due tinte vicine si somigliano di piu'.
FORME = (
    "--linea-significato",
    "--ignoto-tratteggio",
    "--linea-fuoco",
    *(f"--bortle-{n}" for n in range(1, 10)),
)

# Il bianco sopra un fondo pieno: bottoni, il conteggio del telaio, il segno dell'avviso d'allarme.
SOPRA_PIENO = (
    ("--inchiostro-su-accento", "--accento"),
    ("--inchiostro-su-accento", "--accento-sopra"),
    ("--inchiostro-su-accento", "--accento-premuto"),
    ("--inchiostro-su-accento", "--esito-allarme"),
)

TESTO, FORMA = 4.5, 3.0
TEMI = ("scuro", "chiaro")


def _valori(testo: str, tema: str) -> dict[str, str]:
    """I token del tema: prima quelli di `:root`, poi cio' che il tema chiaro riscrive.

    Il chiaro si accende sulla radice, `:root[data-tema="atlante"]` (sezione 15 del foglio).

    **Afferma di aver trovato il blocco chiaro.** Il modo in cui il foglio scrive quel selettore
    e' una cosa del foglio, e il foglio arriva da fuori: se la prossima consegna lo scrivesse
    altrimenti, senza questa riga la funzione tornerebbe i valori dello scuro e la meta' chiara
    del lavoro smetterebbe di essere misurata **in silenzio**. Un banco che si fa dire di si' e'
    peggio di nessun banco."""
    blocchi = re.findall(r":root(\[data-tema=\"atlante\"\])?\s*\{(.*?)\n\}", testo, re.S)
    if tema == "chiaro" and not any(chiaro for chiaro, _ in blocchi):
        raise ValueError("il blocco del tema chiaro non si trova: il foglio ha cambiato selettore")
    fuori = {}
    for chiaro, corpo in blocchi:
        if chiaro and tema != "chiaro":
            continue
        corpo = re.sub(r"/\*.*?\*/", "", corpo, flags=re.S)
        for nome, valore in re.findall(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", corpo):
            fuori[nome] = valore.strip()
    return fuori


def _risolvi(nome: str, valori: dict[str, str], visti: tuple[str, ...] = ()) -> str:
    """Il valore vero di un token, sostituendo ogni `var()` col token a cui rimanda.

    Anche dentro un colore: il v27 scrive `rgb(var(--tinta-velo) / .34)`, con la tinta in canali
    "R G B", e leggere solo il `var()` intero lascerebbe quei colori illeggibili."""

    def sostituisci(rimando: re.Match[str]) -> str:
        if rimando.group(1) in visti:
            raise ValueError(f"{nome}: rimando circolare su {rimando.group(1)}")
        return _risolvi(rimando.group(1), valori, (*visti, nome))

    return re.sub(r"var\((--[a-z0-9-]+)\)", sostituisci, valori[nome])


def colore(scritto: str, su: str = "#000000") -> tuple[int, int, int]:
    """(r, g, b) di un colore del foglio, composto su `su` se ha trasparenza.

    Legge le due grafie di `rgb()`: a virgole (`rgba(1,2,3,.5)`) e a spazi (`rgb(1 2 3 / .5)`)."""
    scritto = scritto.strip()
    if scritto.startswith("#"):
        grezzo = scritto.lstrip("#")
        if len(grezzo) == 3:
            grezzo = "".join(c * 2 for c in grezzo)
        r, g, b = (int(grezzo[i : i + 2], 16) for i in (0, 2, 4))
        return r, g, b
    pezzi = re.fullmatch(r"rgba?\(([^)]+)\)", scritto)
    if not pezzi:
        raise ValueError(f"colore che non so leggere: {scritto!r}")
    canali, _, alfa_scritta = pezzi.group(1).partition("/")
    numeri = [n for n in re.split(r"[\s,]+", canali.strip()) if n]
    if alfa_scritta:
        numeri.append(alfa_scritta.strip())
    if len(numeri) not in (3, 4):
        raise ValueError(f"colore che non so leggere: {scritto!r}")
    r, g, b = (int(n) for n in numeri[:3])
    alfa = float(numeri[3]) if len(numeri) > 3 else 1.0
    fondo = colore(su)
    composto = (round(c * alfa + f * (1 - alfa)) for c, f in zip((r, g, b), fondo, strict=True))
    r, g, b = composto
    return r, g, b


def _luce(rgb):
    def canale(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (canale(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrasto(sopra, sotto):
    """Il rapporto fra due colori, come lo definisce WCAG 2.2: da 1 (uguali) a 21 (nero e bianco).

    `sopra` puo' avere trasparenza, e allora si compone su `sotto`. Il fondo no: un fondo
    trasparente vuol dire che sotto c'e' dell'altro, e chi chiama deve dire cosa."""
    sopra = colore(sopra, su=sotto) if isinstance(sopra, str) else sopra
    sotto = colore(sotto) if isinstance(sotto, str) else sotto
    chiaro, scuro = sorted((_luce(sopra), _luce(sotto)), reverse=True)
    return (chiaro + 0.05) / (scuro + 0.05)


def _coppie():
    """Ogni coppia da misurare: (cosa sta sopra, su cosa, sotto cos'altro, la soglia che la tocca).

    Il terzo posto e' la superficie su cui poggia un fondo velato, e resta `None` quando il fondo
    e' opaco."""
    fondi = [(f, None) for f in FONDI] + list(FONDI_VELATI)
    for fondo, sotto_al_velo in fondi:
        for inchiostro in INCHIOSTRI:
            yield inchiostro, fondo, sotto_al_velo, TESTO
        for forma in FORME:
            yield forma, fondo, sotto_al_velo, FORMA
    for sopra, sotto in SOPRA_PIENO:
        yield sopra, sotto, None, TESTO
    for sopra, velo, sotto_al_velo in SOPRA_VELO:
        yield sopra, velo, sotto_al_velo, TESTO


def leggi_foglio(root):
    """Il foglio della consegna, o **l'elenco di colpe** da restituire se non c'e'.

    Un foglio che manca non e' un elenco vuoto: un controllo che tace quando la cosa da
    controllare sparisce e' verde per il motivo sbagliato. Sta qui, in una casa sola, perche' ogni
    guardia che legge il foglio ha lo stesso caso-limite -- ed era gia' scritto due volte."""
    foglio = os.path.join(root, *STILI, FOGLIO)
    if not os.path.isfile(foglio):
        return [f"{'/'.join((*STILI, FOGLIO))}: non c'e', e allora non si e' misurato niente"]
    with open(foglio, encoding="utf-8") as h:
        return h.read()


def sotto_soglia(root):
    """Le coppie che non arrivano alla loro soglia, nei due temi. Vuoto se va tutto bene."""
    testo = leggi_foglio(root)
    if isinstance(testo, list):
        return testo
    colpe = []
    for tema in TEMI:
        try:
            valori = _valori(testo, tema)
        except ValueError as perche:
            # una riga di FAIL, non un traceback: chi legge il cancello deve capire cosa fare
            colpe.append(f"{tema}: {perche}")
            continue
        for sopra, sotto, sotto_al_velo, soglia in _coppie():
            fondo = _risolvi(sotto, valori)
            if sotto_al_velo:  # un velo non ha colore suo: prende quello della superficie sotto
                fondo = "#{:02x}{:02x}{:02x}".format(
                    *colore(fondo, su=_risolvi(sotto_al_velo, valori))
                )
            misurato = contrasto(_risolvi(sopra, valori), fondo)
            if misurato < soglia:
                dove = f"{sotto} su {sotto_al_velo}" if sotto_al_velo else sotto
                colpe.append(f"{tema}: {sopra} su {dove} = {misurato:.2f}:1, serve {soglia}:1")
    return colpe
