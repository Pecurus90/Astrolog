"""I `Literal` dei modelli dell'API dicono le stesse parole delle costanti del codice: quando
uno stato o un contatore cambia, l'OpenAPI non deve mentire in silenzio. E la ricevuta
chiusa in DB rifiuta esiti fuori vocabolario."""

import ast
import dataclasses
import inspect
import re
import textwrap
from pathlib import Path
from typing import get_args

import pytest

from astrolog import astap, net, place
from astrolog.api import archive as api_archive
from astrolog.api import (
    models,
    models_nights,
    models_review,
    models_review_groups,
    models_site,
    models_tonight,
    models_weather,
    weather_key,
)
from astrolog.db.connect import SCHEMA_PATH
from astrolog.ephemeris import moon, sun
from astrolog.fits.frame_type import FrameType
from astrolog.spine import (
    archive,
    declarations,
    gear_usage,
    group,
    identify_decide,
    mosaic_proposals,
    nights,
    object_answer,
    objects,
    rewrite,
    scan_store,
    signature,
    solve,
    stages,
    typeless,
)
from astrolog.spine.scan_store import COUNTS
from astrolog.units import SQM_MAX, SQM_MIN
from astrolog.vocab.filters import BANDS, PASSBANDS
from astrolog.weather import fetches, forecast, verdict
from astrolog.worker.worker import STRUCTURAL_KEYS, State
from conftest import add_folder


def test_scan_run_status_and_counts_match_the_store():
    status_literal = models.ScanRunOut.model_fields["status"].annotation
    statuses = {a for arg in get_args(status_literal) for a in (get_args(arg) or (arg,))}
    assert statuses == {*scan_store.ScanStatus, type(None)}  # None = corsa aperta
    assert set(COUNTS) <= set(models.ScanRunOut.model_fields)
    # cio' che la scansione lascia fuori: una lista di nomi, e le altre case la seguono
    assert set(scan_store.RECEIPT_LISTS) <= set(models.ScanRunOut.model_fields)
    assert set(scan_store.RECEIPT_LISTS) <= STRUCTURAL_KEYS
    schema = Path(SCHEMA_PATH).read_text(encoding="utf-8")
    assert all(f"{name}_json" in schema for name in scan_store.RECEIPT_LISTS)
    assert set(get_args(models.FileError)) == set(scan_store.FileError)
    assert set(get_args(models.SkipReason)) == set(scan_store.SkipReason)
    reason_literal = models.ScanRunOut.model_fields["reason"].annotation
    reasons = {a for arg in get_args(reason_literal) for a in (get_args(arg) or (arg,))}
    assert reasons == {*scan_store.ScanReason, type(None)}


def test_worker_states_match_the_constants():
    worker_states = set(State) - {State.NOT_RUN}
    assert set(get_args(models.WorkerSnapshot.model_fields["state"].annotation)) == worker_states
    stage_states = (worker_states - {State.IDLE}) | {State.NOT_RUN}
    assert set(get_args(models.StageRecord.model_fields["state"].annotation)) == stage_states


def test_finish_run_refuses_an_outcome_outside_the_vocabulary(conn):
    run_id = scan_store.start_run(conn, add_folder(conn, "x"), "now")
    counts = dict.fromkeys(COUNTS, 0)
    with pytest.raises(ValueError):
        scan_store.finish_run(conn, run_id, "boh", None, counts, {}, [], "now")
    with pytest.raises(ValueError):
        scan_store.finish_run(conn, run_id, "error", "FileNotFoundError", counts, {}, [], "now")
    # e i motivi dei file lasciati fuori: un codice, mai la frase di un'eccezione
    frase = [{"file": "a.fits", "reason": "PermissionError: accesso negato"}]
    with pytest.raises(ValueError):
        scan_store.finish_run(conn, run_id, "ok", None, counts, {}, frase, "now")
    tipo = [{"reason": "dark", "count": 1}]
    with pytest.raises(ValueError):
        scan_store.finish_run(
            conn, run_id, "ok", None, counts, {"skipped_by_reason": tipo}, [], "now"
        )
    scan_store.finish_run(conn, run_id, "aborted", "root_unreachable", counts, {}, [], "now")


def test_the_stage_words_and_the_rewrite_marks_are_the_ones_the_schema_allows():
    """Stadi, stati e marchi hanno una casa sola in Python e il `CHECK` dello schema li ripete:
    una parola nuova da una parte sola la rifiuterebbe il database, a corsa avviata."""
    schema = Path(SCHEMA_PATH).read_text(encoding="utf-8")

    def check(riga):
        return set(re.findall(r"'([a-z_]+)'", next(r for r in schema.splitlines() if riga in r)))

    assert check("stage      TEXT NOT NULL CHECK") == set(stages.STAGES)
    assert set(stages.StageName) - set(stages.STAGES) == {stages.StageName.SCAN}
    assert check("status     TEXT NOT NULL CHECK (status IN ('pending'") == set(stages.StageStatus)
    assert check("rewrite_mark   TEXT CHECK") == set(rewrite.RewriteMark)
    assert set(rewrite.MARK_WEIGHT) == {None, *rewrite.RewriteMark}


def test_the_answers_about_a_camera_are_the_words_the_spine_reads():
    """Le risposte sulle pose che non dicono il filtro: l'API accetta le stesse parole che
    `normalize` legge -- piu' "a colori", che va sulla scheda della camera --, o una risposta
    arriverebbe e non sposterebbe niente."""
    parole = set(get_args(models_review_groups.GearFilterAnswer))
    assert parole == {*signature.FilterAnswer, declarations.CameraType.COLOR}


def test_the_answers_about_a_mosaic_are_the_words_the_spine_reads():
    """Le due risposte su un mosaico: l'API accetta le stesse parole che il lettore riconosce. Una
    che divergesse verrebbe scritta e poi **scartata come illeggibile** -- il lettore tratta un
    valore che non conosce come nessuna risposta -- e la domanda tornerebbe senza dire perche'."""
    assert set(get_args(models_review_groups.MosaicAnswer)) == set(declarations.MosaicAnswer)


def test_an_object_answer_has_the_kinds_the_spine_writes():
    """The routes repeat them as `Literal` on purpose (`models_tonight`): never drifted."""
    kind = models_review.ObjectAnswer.model_fields["kind"].annotation
    assert set(get_args(kind)) == set(object_answer.TargetKind)
    assert {f.name for f in dataclasses.fields(object_answer.Answer)} == set(
        models_review.ObjectAnswer.model_fields
    )


def test_the_two_sky_blanks_are_fields_of_the_subjects():
    """A blank the spine counts and the page does not carry would be frames lost from the sum."""
    found = {"found"}
    assert set(objects.SkyVoid) | found == set(models_review_groups.Subjects.model_fields)


def test_every_group_the_page_asks_carries_its_key_and_its_answer():
    """The promise of `models_review_groups`: a group is answered by its key and keeps the answer
    on the page. Coordinates answer with `site`, their own word for it."""
    for model in (
        models_review_groups.TypelessFolder,
        models_review_groups.GearSignature,
        models_review_groups.MosaicCandidate,
    ):
        assert {"key", "answer"} <= set(model.model_fields), model.__name__
    assert {"key", "site"} <= set(models_review_groups.UnclearCoordinates.model_fields)
    proposal = {f.name for f in dataclasses.fields(mosaic_proposals.Proposal)}
    assert proposal == set(models_review_groups.MosaicCandidate.model_fields)


def test_the_answers_about_a_file_type_are_the_words_the_spine_reads():
    """Le due risposte su una cartella di frame che non dicono che file sono: l'API accetta le
    stesse parole che la spina rilegge. Una che divergesse verrebbe scritta e poi scartata come
    illeggibile, e quei frame resterebbero fermi prima dell'oggetto senza che niente lo dica."""
    assert set(get_args(models_review_groups.TypelessAnswer)) == set(typeless.ANSWERS)


def test_the_type_a_file_does_not_say_is_the_word_the_schema_allows():
    """Il tipo che l'header non ha detto e' la parola che lo schema ammette: se lo schema e la
    spina divergessero, la domanda non troverebbe nessun frame e sparirebbe dalla pagina."""
    schema = Path(SCHEMA_PATH).read_text(encoding="utf-8")
    assert f"image_type IN ('light', '{FrameType.UNKNOWN}')" in schema


def test_the_camera_colours_say_what_the_schema_allows():
    """Il colore di una camera e' una parola del CHECK dello schema, del modello e della spina; e
    la risposta "a colori" e' la stessa parola. Una che divergesse si perderebbe in silenzio: si
    scriverebbe un colore e se ne rileggerebbe un altro."""
    schema = Path(SCHEMA_PATH).read_text(encoding="utf-8")
    riga = next(r for r in schema.splitlines() if "camera_type     TEXT CHECK" in r)
    dallo_schema = set(re.findall(r"'([a-z]+)'", riga))
    assert set(get_args(models_review.CameraType)) == dallo_schema
    assert set(declarations.CameraType) == dallo_schema


def test_the_declaration_types_the_spine_names_are_the_ones_the_schema_allows():
    """I tipi di dichiarazione che la spina nomina sono parole del `CHECK` dello schema. Una che
    divergesse non si scriverebbe affatto -- il database la rifiuterebbe -- e siccome a scrivere e'
    una risposta dell'utente, l'unico a vederlo sarebbe lo stadio, molto dopo, in un log."""
    schema = Path(SCHEMA_PATH).read_text(encoding="utf-8")
    riga = next(r for r in schema.splitlines() if "entity_type TEXT NOT NULL CHECK" in r)
    dallo_schema = set(re.findall(r"'([a-z_]+)'", riga))
    assert set(declarations.EntityType) == dallo_schema


def test_the_gear_usage_subjects_are_the_ones_the_schema_allows():
    """The `gear_usage.subject` CHECK and `UsageSubject` are one vocabulary: a word on one side only
    would make the end-of-stage rewrite fail, all or nothing."""
    schema = Path(SCHEMA_PATH).read_text(encoding="utf-8")
    riga = next(r for r in schema.splitlines() if "subject         TEXT NOT NULL CHECK" in r)
    assert set(re.findall(r"'([a-z_]+)'", riga)) == set(gear_usage.UsageSubject)


def test_declarable_bands_are_the_physical_ones_of_the_vocabulary():
    """Le bande che l'API accetta sono quelle che il vocabolario chiama fisiche: se domani
    ne nasce una, i due elenchi non devono poter divergere in silenzio."""
    assert set(get_args(models_review.Band)) == set(BANDS)
    assert set(BANDS) <= PASSBANDS  # e ognuna e' anche una banda canonica valida


@pytest.mark.sorgente
def test_the_channels_the_solver_can_come_from_are_one_list():
    """I quattro canali da cui l'eseguibile puo' arrivare sono **lo stesso elenco** nel codice e
    nell'API: un quinto aggiunto alla ricerca e non al tipo farebbe esplodere `SolverOut` alla
    costruzione -- 500 su `GET /solver` -- con la suite verde.

    E si confronta col tipo, non con quattro parole ricopiate qui: un elenco scritto a mano
    contro un altro scritto a mano e' una macchina che si fa dire di si'."""
    assert set(astap.Source) == set(get_args(models_site.SolverSource))

    # E i canali che la ricerca **scrive davvero**: la costante potrebbe essere d'accordo col tipo
    # e tutti e due in disaccordo col codice che gira.
    #
    # Si leggono dall'**albero sintattico**, non con un regexp: due dei quattro canali escono da
    # un'assegnazione e non da un `return` (un regexp sui `return` ne prendeva meta' dicendo di
    # prenderli tutti), e un regexp sulle virgolette raccoglie anche le parole dei **commenti**.
    # L'albero i commenti non ce l'ha.
    #
    # **Uguaglianza, non inclusione**: `<=` passa anche con la lettura sganciata, ed e' la forma
    # che rassicura senza guardare. Si contano i membri di `Source` che `_search` nomina: un
    # canale dell'enum che la ricerca non scrive fa cadere questa prova.
    detti = {
        n.attr
        for n in ast.walk(ast.parse(textwrap.dedent(inspect.getsource(astap._search))))
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "Source"
    }
    canali = set(astap.Source.__members__)
    assert detti == canali, detti ^ canali


def test_the_sources_of_a_site_are_the_same_in_the_models_and_in_place():
    """The routes repeat them as `Literal` on purpose (`models_tonight`): never drifted."""
    assert set(get_args(models_site.SkySource)) == set(place.SkySource)
    assert set(get_args(models_site.ElevationSource)) == set(place.ElevationSource)


def test_the_word_for_the_missing_solver_is_one_word():
    """Il codice con cui la spina dice "il solver non si trova" e quello che l'API dichiara
    sono **la stessa parola**: cambiarne una sola farebbe mandare a schermo un valore fuori dal
    tipo dichiarato, e il primo avvio smetterebbe di aggiungere il suo passo in silenzio."""
    assert solve.NO_SOLVER in get_args(models_site.Missing)
    # E la parola per "ASTAP c'e' ma il suo catalogo no", che vive in tre punti: il motivo di una
    # posa fallita, cio' che ferma la corsa, e la riga di `missing`. Una sola casa per tutte e tre.
    assert solve.NO_STAR_DATABASE in get_args(models_site.Missing)
    assert solve.NO_STAR_DATABASE in set(astap.Reason)
    assert solve.ABORTS_THE_RUN == (solve.NO_STAR_DATABASE,)


def test_the_words_group_uses_are_the_words_the_api_shows():
    """Perche' una notte non nasce l'app lo dice in due punti: nelle impostazioni ("cosa
    manca") e nel motivo scritto sulla posa che e' rimasta fuori. Devono essere **la stessa
    parola**: erano due stringhe a mano in due file, e chi ne cambiava una avrebbe lasciato
    l'altra a dire il falso senza che niente diventasse rosso."""
    assert group.GroupReason.NO_ACTIVE_SITE in get_args(models_site.Missing)
    assert group.GroupReason.SITE_NO_TIMEZONE in get_args(models_site.Unknown)


def test_instrument_kinds_say_what_the_schema_allows():
    """Il `Literal` dei tipi di pezzo e il CHECK dello schema sono lo stesso vocabolario: se
    lo schema cambia e il modello no, l'OpenAPI mentirebbe senza che niente diventi rosso."""
    schema = Path(SCHEMA_PATH).read_text(encoding="utf-8")
    blocco = schema[schema.index("kind            TEXT NOT NULL CHECK") :]
    blocco = blocco[: blocco.index("))") + 1]
    dallo_schema = set(re.findall(r"'([a-z_]+)'", blocco))
    assert set(get_args(models_review.InstrumentKind)) == dallo_schema


def test_the_sky_bounds_are_the_same_in_the_model_the_units_and_the_schema():
    """I confini di cio' che e' un cielo hanno una casa sola (`units`). Il modello li legge di
    li' e lo schema li ripete come guardia del database: se domani si spostassero, l'API non
    deve poter restare indietro in silenzio."""
    for campo in (models_site.SiteCreate, models_site.SiteEdit):
        limiti = {
            m.__class__.__name__: getattr(m, "ge", None) or getattr(m, "le", None)
            for m in campo.model_fields["sky_sqm"].metadata
        }
        assert limiti == {"Ge": SQM_MIN, "Le": SQM_MAX}

    schema = Path(SCHEMA_PATH).read_text(encoding="utf-8")
    riga = next(r for r in schema.splitlines() if "sky_sqm      REAL CHECK" in r)
    dallo_schema = re.findall(r"BETWEEN (\d+(?:\.\d+)?) AND (\d+(?:\.\d+)?)", riga)
    # confrontati da numeri, non da stringhe: un confine frazionario non deve poter passare
    assert [(float(a), float(b)) for a, b in dallo_schema] == [(SQM_MIN, SQM_MAX)]


def test_the_identity_vocabularies_say_what_the_schema_allows():
    """I due vocabolari chiusi di `objects` hanno una casa sola. Sono nati nel CHECK dello
    schema e per una fetta intera nessuno in Python li nominava: chi scriveva avrebbe messo
    stringhe a mano, e uno scarto si sarebbe visto solo su una posa vera, a valle."""
    schema = Path(SCHEMA_PATH).read_text(encoding="utf-8")
    for colonna, costanti in (
        ("identity_method", identify_decide.IdentityMethod),
        ("identity_confidence", identify_decide.IdentityConfidence),
    ):
        blocco = re.search(rf"{colonna} +TEXT CHECK \(.*?\)\)", schema, re.DOTALL)
        assert blocco, colonna
        assert set(re.findall(r"'([a-z_]+)'", blocco.group())) == set(costanti), colonna


def test_the_identity_literals_of_the_api_match_the_spine():
    """L'OpenAPI dice le stesse parole della spina: un metodo che il frontend non conosce
    sarebbe un campo che non compila, e uno che l'API non dichiara sarebbe un valore che arriva
    e non e' documentato. La catena e' schema -> `identify_decide` -> modelli, e ogni anello ha
    la sua guardia."""
    assert set(get_args(models_review.IdentityMethod)) == set(identify_decide.IdentityMethod)
    assert set(get_args(models_review.IdentityConfidence)) == set(
        identify_decide.IdentityConfidence
    )


def test_the_moon_phases_and_sky_bands_are_the_same_in_the_models_and_the_ephemeris():
    """The routes repeat them as `Literal` on purpose (`models_tonight`): never drifted."""
    assert set(get_args(models_tonight.PhaseKey)) == set(moon.MoonPhase)
    for literal in (
        models_tonight.SkyBandOut.model_fields["kind"].annotation,
        models_weather.WeatherHourOut.model_fields["sky"].annotation,
    ):
        assert set(get_args(literal)) == set(sun.Sky)


def _words(annotation):
    """The strings of a `Literal`, or of a `Literal | None`."""
    return {a for arg in get_args(annotation) for a in (get_args(arg) or (arg,))} - {type(None)}


def test_the_weather_words_are_the_same_in_the_models_and_the_weather_package():
    """The routes repeat them as `Literal` on purpose (`models_tonight`): never drifted."""
    fields = {
        name: model.model_fields[field].annotation
        for name, model, field in (
            ("verdict", models_weather.WeatherSkyOut, "verdict"),
            ("window", models_weather.WeatherSkyOut, "window"),
            ("code", models_weather.WeatherFactorOut, "code"),
            ("missing", models_weather.WeatherOut, "missing"),
            ("seeing", models_weather.WeatherSeeingOut, "source"),
            ("meteoblue", models_weather.WeatherSeeingOut, "meteoblue"),
        )
    }
    assert _words(fields["verdict"]) == set(verdict.Verdict)
    assert _words(fields["window"]) == set(verdict.Window)
    assert _words(fields["code"]) == set(verdict.FactorCode)
    assert _words(fields["missing"]) == {forecast.Outcome.NO_TIMEZONE}
    assert _words(fields["seeing"]) <= set(fetches.Source)
    key_outcomes = {forecast.Outcome.OK, forecast.Outcome.BAD_ANSWER, *net.Failure}
    assert _words(fields["meteoblue"]) == key_outcomes
    assert set(get_args(weather_key.KeyStatus)) == key_outcomes | {weather_key.REMOVED}
    assert set(get_args(models_weather.RefreshStatus)) == set(forecast.Outcome) | {
        net.Failure.UNREACHABLE
    }


def test_the_nights_and_archive_words_are_the_same_in_the_routes_and_the_spine():
    """Where a waiting frame is answered, and the Archive orders: `Literal` on purpose."""
    assert _words(models_nights.WaitingPoses.model_fields["answer_at"].annotation) == set(
        nights.AnswerAt
    )
    assert set(get_args(api_archive.Sort)) == set(archive.Order)
