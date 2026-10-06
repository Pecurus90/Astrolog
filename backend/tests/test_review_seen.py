"""Da confermare: fin dove la pagina ha guardato, e cosa l'Applica conferma per averlo visto.

Un mestiere solo, staccato da `test_review.py`: qui si prova il confine fra **visto** e **arrivato
dopo**, che si legge sui numeri di riga e non sugli orari -- due righe nate nello stesso istante
non si ordinano (`docs/domini/spina.md`). Si conferma vedendo solo un oggetto: l'attrezzatura non
e' una domanda (Marco, 25/9/2026).
"""

from astrolog.api import review_write
from astrolog.clock import now_iso
from conftest import all_objects, apply, by_name, db, review


def test_review_seen_does_not_count_the_poses(client):
    """Segnare gli oggetti come visti chiede chi sono e se sono ancora una domanda, non quante pose
    hanno: contarle rileggerebbe l'archivio a ogni Applica per numeri che nessuno guarda."""
    lette = []
    with db(client) as conn:
        conn.set_trace_callback(lette.append)
        assert review_write.confirm_seen(conn, None, now_iso()) > 0
    contate = [q for q in lette if "exposure_s" in q]
    assert not contate, contate


def _oggetto_nuovo(client, created_at):
    with db(client) as conn:
        conn.execute(
            "INSERT INTO objects(catalog_slug, created_at) VALUES('m-42', ?)", (created_at,)
        )


def _confermato(client):
    return next(o for o in all_objects(client) if o["key"] == "object:m-42")["confirmed"]


def test_review_does_not_confirm_what_arrived_after_the_page_was_read(client):
    """Se una scansione finisce fra la lettura della pagina e l'Applica, cio' che e' nato nel
    frattempo resta nuovo: nessuno lo ha ancora visto."""
    page = review(client)
    _oggetto_nuovo(client, now_iso())  # nato DOPO la lettura
    prima = review(client)["to_confirm"]  # col nuovo gia' dentro
    out = apply(client, seen=page["seen"])
    # il conto scende di quante voci l'Applica ha confermato, e quella nata dopo non e' fra loro
    assert review(client)["to_confirm"] == prima - out["confirmed"]
    assert _confermato(client) is False

    # Il contro-caso, ed e' cio' che rende questa prova capace di cadere se `seen` smettesse di
    # contare: senza dire cosa si e' visto, l'Applica conferma **anche quello**.
    # Si guarda l'oggetto, non un totale: un numero puo' tornare per mille ragioni, questo no.
    apply(client)
    assert _confermato(client) is True


def test_what_the_page_showed_is_confirmed_even_if_its_clock_ran_ahead(client):
    """Si conferma per NUMERO DI RIGA, non per orario: gli orari non ordinano due cose nate
    nello stesso istante, perche' l'orologio avanza a scatti (la misura sta in
    `docs/domini/spina.md`).

    Qui lo scatto e' portato all'estremo, con una riga il cui orario l'Applica non supera: col
    confronto sugli orari non si confermerebbe **mai**, per quante volte la si guardi. Col numero
    di riga la domanda non dipende dall'orologio di chi ha scritto quella riga."""
    _oggetto_nuovo(client, "2099-01-01T00:00:00.000Z")
    page = review(client)
    assert by_name(page["objects"], "M 42")["confirmed"] is False

    apply(client, seen=page["seen"])

    assert _confermato(client) is True


def test_an_answer_with_a_field_we_do_not_know_is_refused(client):
    """Una pagina aperta prima di un aggiornamento del server manda i nomi di ieri. Scartarli in
    silenzio sarebbe la cosa peggiore: l'Applica confermerebbe **tutto**, compreso cio' che quella
    pagina non ha mai mostrato, e nessuno lo verrebbe a sapere. Sul NAS e' lo scenario ordinario --
    una scheda lasciata aperta sul tablet -- quindi si risponde 422 e la pagina lo dice.

    I campi di ieri sono proprio `instruments` e `rigs`, che la pagina non manda piu'."""
    r = client.post("/api/v1/review/apply", json={"instruments": [], "rigs": []})
    assert r.status_code == 422, r.text

    with db(client) as conn:
        quante = conn.execute("SELECT COUNT(*) FROM declarations").fetchone()[0]
    assert quante == 0, "rifiutata la richiesta, ma l'archivio e' stato scritto lo stesso"
