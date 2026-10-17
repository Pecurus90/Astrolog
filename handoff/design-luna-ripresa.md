# Per Claude Design -- la Luna decide la ripresa, non il punteggio

Da Claude Code, 17/10/2026. Marco ha visto una notte con la Luna al 63 % migliore di una al 43 %,
a parita' del resto. Il difetto era nella regola (ADR 0020 dell'app), non nel disegno: la Luna
pesava 15 punti su 100, e una Luna piena alta lasciava "buona" una notte perfetta. Marco ha
deciso una regola nuova. Estetica e comportamenti restano; cambiano la regola e cio' che si dice.

## 1. La regola

**Due risposte separate.**
- **Il meteo** dice se si esce: punteggio 0-100 e verdetto, come oggi (buona da 70, incerta da
  40; pioggia e nuvole dal 50 % bloccano). **La Luna non entra piu' nel punteggio.** Pesi nuovi:
  nuvole 35, seeing 30, trasparenza 12, condensa 9, vento 9, jet stream 5. "Cosa limita" non puo'
  piu' essere la Luna.
- **La Luna** dice cosa si riprende. Ogni ora di buio e' **banda larga** oppure **solo banda
  stretta**. Solo banda stretta quando la Luna e' illuminata **dal 25 %** e alta **da 10°**.
  Sotto l'una o l'altra soglia, l'ora e' banda larga. Le due soglie stanno nelle Impostazioni.

Esempio: Luna al 63 % che tramonta alle 23:10 = banda larga dopo le 23:10 (meglio per chi fa
LRGB); Luna al 43 % alta tutta la notte = tutta la notte solo banda stretta. Ora e' giusto.

## 2. Dove si vede

Ovunque c'e' oggi il verdetto della notte, sotto o accanto c'e' la ripresa. Il verdetto resta la
cosa piu' grande: la ripresa e' la seconda riga.

- **Dashboard, stanotte**: il verdetto, e sotto i tratti della ripresa ("Banda larga 21:10-00:40 ·
  poi solo banda stretta", oppure "Tutta la notte banda larga", "Tutta la notte solo banda
  stretta"). Il riquadro di lato dice le ore di ciascun tipo. Nel grafico della notte le ore
  "solo banda stretta" si riconoscono (la Luna c'e' gia' come curva: aggiungete il segno del
  tratto, per esempio una fascia sotto l'asse).
- **Meteo**: nella carta della notte la stessa riga; "Come va la notte" racconta anche dove cambia
  la ripresa ("23:10 · la Luna tramonta: banda larga"). La Luna esce da "inoltre" come fattore
  che pesa e resta come informazione.
- **Le sette notti** (Meteo) e **prossime 3 notti** (Dashboard): accanto al verdetto un segno
  piccolo del tipo di ripresa, con le ore di banda larga.
- **Calendario della Luna** (Dashboard): le "notti buone" usano le stesse soglie (25 %, 10°) e le
  ore di buio senza Luna dalla stessa definizione. La regola delle 4 ore resta.
- **Notti** (notti passate): nella carta della notte e nell'elenco "A confronto", accanto al
  cielo, la ripresa di quella notte (ore di banda larga). Il punteggio d'esempio delle notti
  passate non tiene conto della Luna.

## 3. Parole

Proposte, da approvare con Marco: **banda larga**, **solo banda stretta**, "Tutta la notte banda
larga", "ore di banda larga", "la Luna tramonta", "la Luna sale sopra 10°". Nei filtri delle
Notti, eventualmente, un gruppo "Ripresa". Dite se ne servono altre.

## 4. In `soglie.js` (simulato)

- `ora()` di notte: fuori la Luna dai `PUNTI`; pesi 35 / 30 / 12 / 9 / 9 / 5.
- nuova `ripresa(fase, altezza)`: `fase >= 25 && altezza >= 10 ? 'stretta' : 'larga'`.
- `puntoNotte`: senza Luna.
- Il giorno del Sole non cambia per ora: come si giudica senza "Sole basso" si decide con Marco
  quando si costruisce. Lasciatelo com'e' e ditelo nel CHANGELOG.

## 5. Consegna

CHANGELOG (prossima versione) con l'effetto sui dati d'esempio (quali notti cambiano verdetto o
ripresa), DECISIONI, Sistema se nasce un pezzo nuovo (la riga della ripresa).
