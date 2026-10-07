"""I numeri che il foglio della consegna porta dentro di se', contro chi li contraddice.

Un mestiere suo, e diverso da quello di `controlli_veste.py`: li' si guarda **chi scrive le
classi**, qui si leggono i **numeri scritti nel foglio** e si confrontano con quelli che vivono nel
backend.

La guardia sulla soglia della riga (la riga a 420px contro `--avvio-largo`) e' uscita col v27: la
riga del v27 non si incolonna piu' e la carta del primo avvio non e' piu' un token, quindi la
contraddizione che sorvegliava non si puo' piu' scrivere.

Vincolo non ovvio: il foglio si porta **alla lettera** e non si emenda mai. Queste guardie non lo
correggono: dicono che una consegna ha portato dentro una contraddizione, e la correzione va
chiesta alla fonte. E' l'unica forma di controllo possibile su un file che non e' nostro -- e per
la stessa ragione un **falso rosso qui non ha rimedio locale**: bloccherebbe il cancello su un
file che nessuno puo' correggere.
"""

import ast
import os
import re

from controlli_contrasto import FOGLIO, leggi_foglio


def pavimenti_del_cielo(root: str) -> list[str]:
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
