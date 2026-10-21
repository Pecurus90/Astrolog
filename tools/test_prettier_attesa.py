"""The pre-porting frontend files waiting outside Prettier (frontend/.prettierignore).

The list only shrinks, and `tools/tetti.py` holds that; here every entry still names a file, or a
page removed by the porting would leave its line behind and nobody would notice the list is done.
"""

from pathlib import Path

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


def _waiting() -> list[str]:
    lines = (FRONTEND / ".prettierignore").read_text(encoding="utf-8").splitlines()
    return [row for row in lines if row and not row.startswith("#") and not row.endswith("/")]


def test_every_file_waiting_outside_prettier_still_exists():
    """Una pagina tolta o rifatta col porting esce anche dall'elenco."""
    gone = [f for f in _waiting() if f != "src/api/schema.d.ts" and not (FRONTEND / f).is_file()]
    assert not gone, f"non esistono piu', togli la riga da frontend/.prettierignore: {gone}"
