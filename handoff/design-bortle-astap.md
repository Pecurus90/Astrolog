# Per Design: la scala di Bortle cambia tabella (23/10/2026)

Una correzione piccola al foglio, nel commento di `foglio/48-bortle.css` (`.as-bortle-letta`).

**Cosa cambia.** L'app usera' **una sola** conversione (la cambia insieme al vostro foglio, Issue #28) da luminosita' del cielo (SQM, mag/arcsec²)
a classe di Bortle: quella di ASTAP (`bortle()` in `unit_sqm.pas`, da ClearDarkSky), perche' lo
SQM lo misuriamo col metodo di ASTAP. Decisione di Marco, 23/10/2026. La tabella che vi avevamo
mandato (Wikipedia, siti di astrofotografia) esce.

**Il commento oggi dice:**

    1 = 21,76 · 2 = 21,60 · 3 = 21,30 · 4 = 20,80 · 5 = 19,25 · 6 = 18,50 ·
    7 = 18,00 · 8 = 17,00 · 9 = sotto.

**Deve dire** (una classe vale da sopra il suo pavimento; la 4,5 di ASTAP si legge 5):

    1 = 21,99 · 2 = 21,89 · 3 = 21,69 · 4 = 21,25 · 5 = 19,50 · 6 = 18,94 ·
    7 = 18,38 · 8 = 17,80 · 9 = sotto.

**L'esempio della riga** «Bortle 4 (20,8)» non e' piu' vero: 20,8 ora e' Bortle 5. Un esempio
giusto: «Bortle 4 (21,4)».

Nient'altro cambia: colori, classi, struttura restano. Una guardia del nostro lato
(`tools/controlli_foglio.py`) confronta questi pavimenti con quelli dell'app e resta rossa finche'
il foglio non li porta.
