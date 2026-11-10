"""Una pagina portata misura come la sua tavola: la stessa riga, in Chrome, sotto il solo foglio
della consegna (la tavola) e sotto i tre fogli dell'app nell'ordine di `main.tsx`."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cattura

ROOT = Path(__file__).resolve().parent.parent
STILI = ROOT / "frontend" / "src" / "stili"
NUOVO, VECCHIO, APP = STILI / "consegna" / "astrolog.css", STILI / "astrolog.css", STILI / "app.css"

# La riga dell'elenco dell'Archivio (min-height 56, padding 10 12), un testo da 12 px e il bottone
# della vista (44 px, border-box del browser come ogni button), sotto il
# data-modo e col carattere che il Tema dell'app e la radice di ogni tavola portano.
CORPO = """<div data-modo="scuro" style="font-family: var(--carattere)">
<div class="app-cornice app-pagina" data-formato="desktop">
<div class="al-arch__centro-3 al-arch__elenco-righe al-arch__riga" id="riga">
<span class="al-arch__testo-7" id="testo">1 frame</span></div>
<button type="button" class="al-arch__vista" id="vista"><svg width="18" height="18"></svg></button>
</div></div>"""
# La testa delle tavole (Archivio.dc.html 13): margini a zero, link senza sottolineatura.
TAVOLA = "<style>html,body{margin:0}a{color:inherit;text-decoration:none}</style>"
MISURA = (
    "[riga.getBoundingClientRect().height, testo.getBoundingClientRect().height,"
    " vista.getBoundingClientRect().width]"
)

needs_chrome = pytest.mark.skipif(cattura.find_chrome() is None, reason="Chrome is not installed")


def _pagina(tmp_path: Path, nome: str, fogli: list[Path], testa: str, corpo_classe: str) -> str:
    link = "".join(f'<link rel="stylesheet" href="{f.as_uri()}">' for f in fogli)
    corpo = f'<body class="{corpo_classe}">{CORPO}</body>'
    html = f"<!doctype html><html><head>{link}{testa}</head>{corpo}</html>"
    pagina = tmp_path / f"{nome}.html"
    pagina.write_text(html, encoding="utf-8")
    return pagina.as_uri()


def _misura(url: str) -> list[float]:
    piano = {"url": url, "carica": 1.0, "passi": [{"js": MISURA, "attesa": 0}]}
    return cattura.run(piano)["values"][0]


@needs_chrome
def test_a_ported_row_measures_as_on_its_board(tmp_path):
    tavola = _misura(_pagina(tmp_path, "tavola", [NUOVO], TAVOLA, ""))
    app = _misura(_pagina(tmp_path, "app", [NUOVO, VECCHIO, APP], "", "as-app"))

    assert tavola[0] == 77, tavola  # content-box: 56 di altezza minima, 20 di padding, 1 di bordo
    assert app == tavola, (app, tavola)
