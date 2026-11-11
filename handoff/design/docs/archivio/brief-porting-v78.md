# Brief del 10/11/2026 · collaudo della v78 (dalla coda per Design, «Da dare»)

Testo della coda di Claude Code, come arrivato.

1. Pillola del sito nella carta della notte, telefono (resto della v78): con un nome lungo la fonte («dalle coordinate nei frame») sparisce, resta solo nel title, che sul telefono non si vede. La fonte deve restare leggibile a ogni lunghezza del nome.
2. Striscia delle notti sul desktop stretto (resto della v78): nelle carte da 150 px «1 h 50 di banda larga» va a capo su due righe.
3. Impostazioni, Primo avvio e Sistema fra 700 e 1440 px (resto della v78: Design non le ha misurate). Claude Code le misura nell'app e porta qui cio' che sborda.
4. Notti fra 700 e 999 px (collaudo v78, 10/11): il calendario delle notti (.al-notti__colonna-4) resta largo 4/12 (244 px a 860) con due terzi vuoti a destra, mentre la carta della notte prende la riga intera. Anche il calendario sulla riga intera, o accanto a qualcosa.
5. Sito dal nome lungo, i posti che la v78 non ha toccato (collaudo v78 nell'app con «Osservatorio del Monte Generoso, terrazza nord sopra la funicolare»): nella testa di Tutto della notte, sotto il titolo, il nome va a capo su due righe a 390 e a 700; in Cerca sul telefono la riga «Siti · …» va a capo. Il ?sito= della tavola non arriva al Riepilogo ne' all'aiuto di Cerca.
6. Errori delle tavole v78 (collaudo 10/11): Notti.dc.html da' «TypeError: Cannot read properties of undefined (reading 'q')» in componentDidUpdate dopo Tutto della notte, Esc, Cerca; componenti/Telaio.dc.html da' quattro <path> attribute d coi segnaposto {{ m.altroChev }}, {{ m.modeIcon }}, {{ vb.az.d }}, {{ b.d }} (la v78 li ha tolti solo nell'Archivio); componenti/Telaio.dc.html?formato=telefono a 390 resta desktop e scorre di 153 px.
7. Icona di AstroLog per la scheda del browser (Issue #56, Marco 10/11): oggi l'app usa il marchio della testa del telaio (anello e punto, frontend/src/icona.svg, colore del testo chiaro o scuro). Un'icona disegnata per 16 e 32 px, SVG, che regga sulle schede chiare e scure.
