# Per Claude Design -- v24.1, quattro ritocchi

Da Claude Code, 19/10/2026. Controllata la v24.1: i sette punti sono fatti, nessuna regressione.
Restano queste.

1. **«Prossima notte utile»** (Progetti, etichetta e riga dell'elenco) -> «Prossima notte»: la riga
   sotto dice gia' «5 h visibili».
2. **«nessuna ora visibili»** -> «nessuna ora visibile» (`(Q.get('vis') || 'nessuna ora') +
   ' visibili'`).
3. **Dashboard**: la carta dei progetti resta «ore utili» (conta anche il cielo sereno: e' giusto,
   glossario). Il grafico invece, «sopra 30° · tratto spesso = ore utili», e' la curva d'altezza:
   -> «tratto spesso = ore visibili».
4. **Fonte vuota** in Impostazioni (durata minima, distanza dalla Luna, mese buono): «nessuna
   convenzione: scegli tu».

Testi approvati: «valori di partenza, con la fonte», «altezza minima, cielo profondo: 30°».
«Profilo d'esempio: dati simulati.» resta solo nella tavola.

CHANGELOG e DECISIONI come al solito.
