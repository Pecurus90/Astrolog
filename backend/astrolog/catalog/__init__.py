"""Il catalogo degli oggetti celesti: 22.080 voci, e cio' che serve per riconoscerle.

Qui dentro vive il **dato**, in `data/`, impacchettato col programma e versionato con lui:
un file solo, con la sua versione e il NOTICE delle licenze accanto. Non si scarica e non si
aggiorna da solo -- cambia quando cambia l'app.

Vincolo non ovvio: il catalogo **non si rifa' a mano**. Si costruisce dalle sorgenti con gli
strumenti in `tools/` (che stanno li' perche' sono costruzione, non prodotto: la spina non
tocca la rete in nessun punto). L'identita' di una voce e' lo **slug**, non un numero di riga:
gli id si rinumerano a ogni ricostruzione, lo slug no.

Dal file alle tabelle ci sono quattro moduli: `bundle` lo legge, `load` lo porta nel database,
`designation` legge le sigle come sono scritte, `lookup` risponde alle due domande -- che
oggetto e' questa sigla, e cosa c'e' in questo pezzo di cielo.
"""
