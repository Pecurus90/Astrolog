# AstroLog

App **open source** per catalogare, analizzare e pianificare sessioni di astrofotografia.
Si punta alle cartelle dei FITS; l'app legge gli header, **risolve ogni frame sul cielo**
(ASTAP: per ora va installato a parte; sara' impacchettato), normalizza strumenti e filtri, e
ricostruisce una cronologia osservativa interrogabile. Backend Python, frontend React, SQLite,
nessun login.

**Stato: ricostruzione dalla radice (settembre 2026).** La spina dell'app --
scansiona, normalizza, risolvi, identifica, raggruppa, misura -- si rifa' partendo da un
disegno. Il progetto precedente, `old/`, e' tenuto solo in locale (non e' in questo
repository): e' la **cava** da cui si portano i pezzi che valgono (vocabolari, catalogo, qualita', effemeridi, pagine), mai una
dipendenza.

- Il metodo di lavoro: [`CLAUDE.md`](CLAUDE.md)
- Cosa viene dopo: [`docs/piano.json`](docs/piano.json) (`python tools/piano.py`); le idee in [`docs/idee.md`](docs/idee.md)
- Per contribuire: [`CONTRIBUTING.md`](CONTRIBUTING.md)

Licenza: [GPL-3.0](LICENSE). Il solver astrometrico e' [ASTAP](https://www.hnsky.org/astap.htm)
(MPL 2.0); i database stellari sono estratti di Gaia DR3 -- *ESA/Gaia/DPAC*. Il metodo dello SQM
e il lettore dei cataloghi sono portati dal sorgente di ASTAP (Han Kleijn, MPL 2.0: i due file,
`backend/astrolog/pipeline/sqm.py` e `star_catalogue.py`, restano sotto quella licenza).
