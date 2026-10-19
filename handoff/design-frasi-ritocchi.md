# Per Claude Design -- frasi, ultimi ritocchi (v24.4)

Da Claude Code, 19/10/2026. Controllata la v24.4: le tre scelte, l'elisione, le costellazioni e
quasi tutta la brief sono fatte; testi approvati invariati. Restano i numeri e poche righe.

## Numeri (Marco: regola SI)

- **Decimali col punto, sempre**: via `AL.virg` e i `replace('.', ',')` dai valori a schermo.
  Oggi con la virgola: MisureFrame 169, 186, 194, 248, 271, 318, 327, 329 (eccentricita', massa
  d'aria); Misure dei frame, box dell'eccentricita' (mediana e quartili); Attrezzatura 151-161,
  258-337, 402, 567 (f/5.6, 7.5 mm, ±0.5 mm, 1.25″, valori d'esempio); Dashboard 297, 301, 333, 334;
  Meteo 250 (`nf`: seeing, aerosol, pioggia, visibilita'); Da confermare 261 (3.76 µm) e 282 (44.1
  km); Riepilogo (distanze: 1.2 milioni di anni luce).
- **Coordinate col punto**: «45.8486 N · 11.5689 E» (Primo avvio 132 e 300, Da confermare 271),
  come Impostazioni.
- **Migliaia con lo spazio sottile** (U+202F) da 10 000 in su: «396 200 km», «18 430 frame»; sotto,
  niente separatore: «1366 m», «1240 oggetti». Mai il punto per le migliaia.

## Righe

1. Misure dei frame, array `PR`: «Askar 103 + ZWO ATR2600M» -> «Askar 103 · ZWO ATR2600M»;
   «Newton 200/800 + ZWO ASI533MC Pro» -> «Newton 200/800 · ZWO ASI533MC Pro».
2. Eventi, riga dell'elenco dell'eclisse di Luna (`subDi`): «grandezza 1.25 da Cima Ekar» ->
   «grandezza 1.25» (col Sole resta «da {sito}»).
3. Primo avvio 273: «Con una chiave API Meteoblue…» -> «Con una chiave Meteoblue…»; 72: «Come
   ottenere una chiave gratuita ↗» -> «Come ottenere una chiave ↗».
4. Intestazioni di colonna minuscole: «Integrazione» -> «integrazione» dove le altre sono minuscole
   (Archivio, elenco; Notti 73). Maiuscola solo dove il titolo e' maiuscolo.
5. «Seeing: Meteoblue» -> «Seeing: meteoblue»: il marchio si scrive minuscolo nei crediti, come
   chiede il servizio (scusate il giro). Altrove resta «Meteoblue».

CHANGELOG e DECISIONI come al solito.
