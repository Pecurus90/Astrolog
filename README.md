# AstroLog

App **open source** per catalogare, analizzare e pianificare sessioni di astrofotografia.
Si punta alle cartelle dei FITS; l'app legge gli header, **risolve ogni frame sul cielo**
(ASTAP: per ora va installato a parte; sara' impacchettato), normalizza strumenti e filtri, e
ricostruisce una cronologia osservativa interrogabile. Backend Python, frontend React, SQLite,
nessun login.

**Stato: ricostruzione dalla radice (settembre 2026).** La spina dell'app --
scansiona, normalizza, risolvi, identifica, raggruppa, misura -- si rifa' partendo da un
disegno. Il progetto precedente e' intero in [`old/`](old/): e' la **cava** da cui si
portano i pezzi che valgono (vocabolari, catalogo, qualita', effemeridi, pagine), mai una
dipendenza.

- Il metodo di lavoro: [`CLAUDE.md`](CLAUDE.md)
- Cosa viene dopo: [`docs/coda.md`](docs/coda.md)
- Per contribuire: [`CONTRIBUTING.md`](CONTRIBUTING.md)

Licenza: [GPL-3.0](LICENSE). Il solver astrometrico e' [ASTAP](https://www.hnsky.org/astap.htm)
(MPL 2.0); i database stellari sono estratti di Gaia DR3 -- *ESA/Gaia/DPAC*.
