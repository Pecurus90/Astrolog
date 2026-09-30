"""La forma delle risposte e delle richieste della **spina**: cartelle, scansione, worker.

Vincolo non ovvio: "non so" e' un campo con codice, mai un null muto; ogni elenco e'
paginato (`items`, `total`, `limit`, `offset`). I nomi vengono dal glossario. La convenzione
vale per tutti; i modelli stanno in un file per dominio (`models_review`, `models_site`).
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

from .models_page import Page


class Health(BaseModel):
    status: Literal["ok"]
    api_version: str
    schema_tables: int
    data_root: str | None
    catalog_entries: int
    catalog_version: str | None


class PathInfo(BaseModel):
    family: Literal["windows", "posix"]
    data_root: str | None


class FolderCreate(BaseModel):
    root_path: str = Field(min_length=1)
    name: str | None = None


class PathProbe(BaseModel):
    root_path: str = Field(min_length=1)


class ProbeOut(BaseModel):
    root_path: str
    reachable: bool
    fits_count: int | None  # None = non ho guardato (cartella non raggiungibile), mai 0
    complete: bool | None  # False = conta fermata al tetto di tempo: sono "piu' di" fits_count


class FolderEntry(BaseModel):
    name: str
    path: str  # quello da registrare, cosi' com'e'


class BrowseOut(BaseModel):
    path: str
    parent: str | None  # None alla radice dei dati: piu' su non si sale
    folders: list[FolderEntry]  # le sottocartelle visibili, ordinate


class FolderOut(BaseModel):
    id: int
    name: str | None
    root_path: str
    created_at: str
    reachable: bool
    frames: int  # posizioni presenti: viene dal DB, vale anche a disco staccato
    reactivated: bool = False


class FolderList(Page[FolderOut]):
    pass


class RetireOut(BaseModel):
    folder_id: int
    retired: bool
    kept_frames: int


class ScanStarted(BaseModel):
    run_id: int
    folder_id: int


class FolderSkipped(BaseModel):
    """Una cartella che il gesto in barra non ha letto, col suo perche': oggi solo
    `root_unreachable` (il disco staccato, il NAS spento) e `scan_running` (la sta gia'
    leggendo un'altra corsa).

    Porta il **percorso** e non solo il numero di riga: e' cio' che l'utente riconosce, e chi
    avvia la scansione lo ha gia' in mano (`api/scan.py` lo legge per il pre-controllo). Senza,
    la pagina dovrebbe chiedere l'elenco delle cartelle e ricucire due risposte proprio nel
    momento del guasto -- e a un utente con piu' di cento cartelle non tornerebbe nemmeno."""

    folder_id: int
    root_path: str
    reason: Literal["root_unreachable", "scan_running"]


class ScanAllStarted(BaseModel):
    """Cosa ha fatto il gesto "leggile tutte": le cartelle avviate con la loro ricevuta, e
    quelle saltate col motivo. Le saltate si dicono invece di sparire: un disco staccato e'
    esattamente la cosa che l'utente deve sapere, e tacerla farebbe sembrare completa una
    scansione che non lo e'."""

    started: list[ScanStarted]
    skipped: list[FolderSkipped]


# Perche' un file non e' entrato, e perche' si e' saltato: le parole di `spine/scan_store`.
FileError = Literal["file_unreadable", "header_unreadable", "name_not_utf8", "internal_error"]
SkipReason = Literal["calibration", "stack", "still_writing"]


class FileNotRead(BaseModel):
    file: str  # relativo alla radice; un nome che non e' UTF-8 porta `?` al posto dei byte storti
    reason: FileError


class SkippedCount(BaseModel):
    reason: SkipReason
    count: int


class ScanRunOut(BaseModel):
    id: int
    folder_id: int
    # Il percorso della cartella, che e' quello che l'utente riconosce: col solo `folder_id` la
    # pagina dovrebbe leggersi le cartelle e appaiarle da se'. Non e' mai vuoto: togliere una
    # cartella la **ritira**, e la sua riga la trattiene la chiave esterna di `scan_runs`.
    folder_path: str
    started_at: str
    ended_at: str | None
    duration_s: float | None  # None = non lo so: la corsa e' aperta, o i due istanti non tornano
    status: Literal["ok", "stopped", "aborted", "error"] | None  # None = corsa aperta
    reason: Literal["root_unreachable", "stop_requested", "internal_error", "database_error"] | None
    found: int
    new: int
    unchanged: int
    duplicates: int
    missing: int
    skipped: int
    errors: int
    online_only: int  # FITS solo online: non aperti, per non scaricarli; si rivedono dopo
    unreadable_dirs: list[str]
    hidden_dirs: list[str]  # sottocartelle nascoste lasciate fuori (il cestino, per esempio)
    linked_dirs: list[str]  # raggiunte da un collegamento o una giunzione: non seguite
    skipped_by_reason: list[SkippedCount]  # quanti saltati per motivo, calibrazioni comprese


class ScanRunList(Page[ScanRunOut]):
    pass


class ScanErrorList(Page[FileNotRead]):
    """I file che una scansione non ha letto, a pagine: possono essere migliaia."""


# gli stati di uno stadio nel worker: un vocabolario, scritto una volta
StageState = Literal["not_run", "running", "stopped", "completed", "completed_with_errors", "error"]


class StageRecord(BaseModel):
    name: str
    state: StageState
    current: int | None
    total: int | None
    tally: dict[str, Any]
    # Perche' lo stadio si e' fermato, quando si e' fermato da solo: un codice, mai una frase.
    reason: str | None = None


class WorkerSnapshot(BaseModel):
    state: Literal["idle", "running", "stopped", "completed", "completed_with_errors", "error"]
    stage: str | None
    started_at: str | None  # None finche' non e' mai partito: mai un istante inventato
    ended_at: str | None
    stages: list[StageRecord]
    error: str | None = None


class ScanEvent(BaseModel):
    """Un evento di avanzamento della scansione: il file in corso e i conteggi finora."""

    current: int
    total: int
    file: str
    run_id: int
    folder_id: int
    found: int
    new: int
    unchanged: int
    duplicates: int
    missing: int
    skipped: int
    errors: int
    online_only: int


class ScanProgress(BaseModel):
    """La scansione della corsa corrente: cosa la pagina mostra mentre gira e a fine corsa."""

    state: StageState
    folder_id: int
    run_id: int
    last_event: ScanEvent | None
    receipt: ScanRunOut | None  # dal DB, quando la corsa e' finita comunque sia finita


class PipelineStatus(BaseModel):
    worker: WorkerSnapshot
    scan: ScanProgress | None  # None finche' non e' partita nessuna scansione
    pending: dict[str, int]  # per stadio: quanti frame mancano ancora
    # il verbo del pulsante, deciso qui e non nella pagina: Avvia / Ferma / Riprendi
    action: Literal["start", "stop", "resume"]


class WorkerOut(BaseModel):
    worker: WorkerSnapshot
