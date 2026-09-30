"""La forma di cio' che l'**Archivio** mostra: cio' che hai ripreso, gia' pronto per lo schermo.

Vincolo non ovvio: qui non c'e' niente che il frontend debba ricalcolare. Il nome e' gia' scelto
fra i due passi del contratto, le ore sono gia' sommate escludendo le copie riscritte e i filtri
arrivano gia' in ordine. Le ore **possono essere zero anche quando il tempo non si sa** -- la
somma di nessun frame con una durata -- per questo viaggiano con `untimed`, e chi le mostra
(`TempoDellePose`, nel frontend) non scrive "0 h". Le parole vengono dal glossario.
"""

from pydantic import BaseModel

from .models_nights import FilterUsed
from .models_page import Page


class ArchivePanel(BaseModel):
    """Un pannello di un mosaico: l'inquadratura, cio' che ci hai ripreso e quanto."""

    object: str | None  # l'oggetto (o gli oggetti) delle sue pose; nullo se il cielo non ne sa
    ra_deg: float  # il centro: dice QUALE pannello, se due hanno lo stesso oggetto
    dec_deg: float
    frames: int
    integration_s: float
    untimed: int


class ArchiveObject(BaseModel):
    """Una riga dell'Archivio: un gruppo di frame -- un oggetto, o un mosaico confermato -- e cosa
    ci hai messo dentro. La riga di un oggetto porta solo i frame che nessun mosaico ha preso."""

    key: str  # stabile: lo slug o il nome primario di un oggetto, la chiave di un mosaico
    name: str | None  # gia' risolto dal backend; nullo solo su una riga che non dovrebbe esistere
    slug: str | None  # lo slug di catalogo dell'oggetto, o del bersaglio del mosaico
    frames: int  # quanti frame, copie riscritte escluse
    integration_s: float  # la somma del tempo dei frame, in secondi; a schermo si legge in ore
    untimed: int  # quanti di quei frame non dicono quanto sono durati: non valgono zero
    constellation: str | None  # codice IAU a tre lettere, dal catalogo
    type_code: str | None  # che cosa e' (GALAXY, DARK_NEBULA...), dal catalogo
    filters: list[FilterUsed]  # con che filtri l'hai ripreso, dal piu' usato; vuoto se non si sa
    panels: int | None  # quanti pannelli, per un mosaico; nullo per un oggetto
    panel_list: list[ArchivePanel]  # i pannelli, dal piu' ripreso; vuoto per un oggetto


class ArchiveChoices(BaseModel):
    """Cosa offrono le tendine della barra: **cio' che c'e' in archivio**, non cio' che il
    catalogo conosce: chi ne usa due non deve scorrere tutti quelli che il catalogo porta."""

    catalogs: list[str]  # le sigle dei cataloghi che i tuoi oggetti hanno (`M`, `NGC`...)
    constellations: list[str]  # i codici IAU a tre lettere, in ordine
    filters: list[str]  # i nomi dei filtri con cui hai ripreso almeno un oggetto
    mosaics: bool  # se hai almeno un mosaico confermato: senza, "solo i mosaici" non si offre


class ArchiveFound(BaseModel):
    """Quante delle righe trovate sono oggetti e quanti mosaici: la conta a schermo non chiama
    "oggetto" un mosaico."""

    objects: int
    mosaics: int


class ArchiveList(Page[ArchiveObject]):
    # `total` sono le righe che **passano il filtro**, non quante ne hai in tutto
    found: ArchiveFound  # le stesse righe, divise fra oggetti e mosaici
    choices: ArchiveChoices
