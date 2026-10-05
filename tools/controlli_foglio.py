"""I numeri che il foglio della consegna porta dentro di se', contro chi li contraddice.

Un mestiere suo, e diverso da quello di `controlli_veste.py`: li' si guarda **chi scrive le
classi**, qui si leggono i **numeri scritti nel foglio** e si confrontano con altri numeri -- uno
dentro il foglio stesso, uno che vive nel backend.

Vincolo non ovvio: il foglio si porta **alla lettera** e non si emenda mai. Queste guardie non lo
correggono: dicono che una consegna ha portato dentro una contraddizione, e la correzione va
chiesta alla fonte. E' l'unica forma di controllo possibile su un file che non e' nostro -- e per
la stessa ragione un **falso rosso qui non ha rimedio locale**: bloccherebbe il cancello su un
file che nessuno puo' correggere. Per questo si legge il foglio **senza i suoi commenti**, dove i
selettori si nominano in prosa.
"""

import ast
import os
import re

from controlli_contrasto import FOGLIO, leggi_foglio

# La colonna del primo avvio: **l'unica larghezza di carta che il foglio dichiara come token e
# dentro cui montiamo righe**. Non si prende il minimo di tutti i `--*-largo`: fra quelli ci sono
# un segno di legenda da 14px, la colonna di una navigazione e la larghezza di un dialogo, che
# righe non ne contengono -- misurato, e il confronto col minimo grida su sei numeri su sette.
CARTA_DEL_PRIMO_AVVIO = "--avvio-largo"


def _senza_commenti(testo):
    """Il foglio senza i suoi commenti. Un commento che nomina un selettore -- e il foglio ne e'
    pieno, li spiega tutti -- farebbe dire a una regex che quella regola sta dove non sta."""
    return re.sub(r"/\*.*?\*/", "", testo, flags=re.S)


def soglia_della_riga(root):
    """La riga si affianca dentro la carta piu' stretta che l'app monta, o e' una promessa rotta.

    E' la contraddizione che e' costata una consegna: il foglio dichiarava la colonna del primo
    avvio a 680px **e** faceva incolonnare ogni `.as-riga` sotto i 720, quindi la forma affiancata
    che il montaggio del fornitore mostra non era raggiungibile in quella carta -- per costruzione,
    non per un caso di bordo. Nessuna prova poteva vederlo: in jsdom i fogli non si applicano, e
    l'impronta va rossa per qualunque consegna, quindi dice "e' cambiato", mai "e' sbagliato".

    Si confrontano **due numeri indipendenti del foglio**, che e' l'unico modo di prendere una
    contraddizione interna: la soglia sotto la quale una riga si incolonna, e `--avvio-largo`.

    **Dove non arriva, dichiarato**: legge quel token e nessun altro. E' la colonna piu' stretta
    in cui l'app monta righe *oggi*, ed e' l'unica scritta come token -- le altre larghezze di
    carta nascono dalla pagina, non dal foglio, e una guardia non puo' leggerle. Se domani si
    montasse una colonna piu' stretta senza un token, questa resterebbe verde misurando il numero
    sbagliato: e' un limite, non una svista, e sta scritto qui perche' chi la legge lo sappia."""
    intero = leggi_foglio(root)
    if isinstance(intero, list):
        return intero
    testo = _senza_commenti(intero)
    largo = re.search(rf"{CARTA_DEL_PRIMO_AVVIO}:\s*(\d+)px", testo)
    if largo is None:
        return [f"{FOGLIO}: non trovo {CARTA_DEL_PRIMO_AVVIO}, la carta del primo avvio"]
    colonna = int(largo.group(1))
    # La at-rule che porta `.as-riga`: si cerca il blocco, non la prima soglia che capita -- il
    # foglio ne ha piu' d'una con la stessa forma, e le altre riguardano altri mattoni.
    soglie = [
        int(s)
        for s, corpo in re.findall(
            r"@container colonna \(max-width:\s*(\d+)px\)\s*\{(.*?)^\}",
            testo,
            re.S | re.M,
        )
        if re.search(r"(^|[\s,}])\.as-riga\s*[,{.]", corpo)
    ]
    if not soglie:
        return [f"{FOGLIO}: nessuna soglia di colonna porta .as-riga"]
    return [
        f"{FOGLIO}: una riga si incolonna sotto {s}px, ma la carta del primo avvio"
        f" e' larga {colonna}px: li' non si affianca mai"
        for s in soglie
        if s >= colonna
    ]


def pavimenti_del_cielo(root):
    """I pavimenti della scala di Bortle che il foglio cita, contro quelli che l'app usa.

    Il fornitore se li e' scritti nel commento di `.as-bortle` -- glieli avevamo mandati noi --
    per disegnare mockup con la coppia classe/misura giusta. Sono **un nostro fatto in casa loro**,
    e il foglio non si emenda: il giorno che la nostra tabella cambia quel commento dice il falso
    e la correzione va chiesta alla fonte. Senza questa guardia se ne accorgerebbe solo chi
    rilegge il CSS, cioe' nessuno.

    Si guardano tutte e due le direzioni: un pavimento **diverso** e un pavimento **sparito**. La
    seconda e' quella che conta -- confrontare solo cio' che il foglio cita ancora vuol dire
    tacere proprio sul cambio parziale, che e' quello probabile."""
    intero = leggi_foglio(root)
    if isinstance(intero, list):
        return intero
    detti = {int(c): float(v.replace(",", ".")) for c, v in re.findall(r"(\d) = (\d+,\d+)", intero)}
    if not detti:
        return [f"{FOGLIO}: il commento della scala non cita piu' nessun pavimento"]
    veri = dict(_nostri_pavimenti(root))
    colpe = [
        f"{FOGLIO}: la scala dice {classe} = {detto}, l'app usa {veri.get(classe)}"
        for classe, detto in detti.items()
        if veri.get(classe) != detto
    ]
    colpe += [
        f"{FOGLIO}: la scala non cita piu' il pavimento della classe {classe} ({veri[classe]})"
        for classe in sorted(set(veri) - set(detti))
    ]
    return sorted(colpe)


def _nostri_pavimenti(root):
    """`BORTLE_FLOORS` letto dalla sua casa, `backend/astrolog/units.py`.

    Si **legge il letterale** invece di importare il modulo: importarlo tirerebbe dentro la catena
    di astropy per confrontare otto numeri, e farebbe dipendere una guardia della veste dal fatto
    che il backend sia installato. Ricopiarli qui sarebbe peggio ancora -- sarebbe una terza casa
    dello stesso fatto, ed e' proprio quella che questa guardia esiste per impedire."""
    percorso = os.path.join(root, "backend", "astrolog", "units.py")
    with open(percorso, encoding="utf-8") as h:
        albero = ast.parse(h.read())
    for nodo in albero.body:
        if isinstance(nodo, ast.Assign) and any(
            isinstance(b, ast.Name) and b.id == "BORTLE_FLOORS" for b in nodo.targets
        ):
            try:
                return ast.literal_eval(nodo.value)
            except ValueError as perche:
                # Un letterale diventato calcolato: la guardia non puo' piu' leggerlo senza
                # eseguire il modulo. Si dice cosa e' successo e dove, invece di lasciare una
                # traccia che nomina un numero di riga e nient'altro.
                raise LookupError(
                    "BORTLE_FLOORS in backend/astrolog/units.py non e' piu' un letterale:"
                    " questa guardia lo legge senza eseguire il modulo, quindi o torna letterale"
                    " o la guardia va rifatta"
                ) from perche
    raise LookupError("BORTLE_FLOORS non e' piu' in backend/astrolog/units.py")
