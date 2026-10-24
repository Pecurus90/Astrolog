# 0039 -- Le soglie deboli ricavate da fisica e statistica, o tarate su ogni utente

**Stato:** accettata, 24/10/2026; supera in parte ADR 0022, 0034, 0036, 0037. Nessun codice: tutto nella fase 4 (le raffiche a 25 km/h di ADR 0034 sono gia' costruite).
Fase 2b del registro (Marco: "portare dentro la nostra esperienza matematica, fisica, statistica";
"i miei dati sono solo miei").

## Contesto

Dopo la fase 2 restavano numeri appoggiati a un forum, a un solo operatore o al solo archivio di
Marco. Regola (CLAUDE.md): un numero vale se si tara da se' sui dati di ogni utente, se lo regge un
argomento indipendente, o se diventa Impostazione. Due ricerche con conti e simulazioni (script
nella scratchpad della sessione, cartella fase2b). Il criterio unico per altezza, seeing e vento
e' il **tempo doppio**: lo stesso del punteggio della notte (ADR 0034), la luce persa costa tempo
di posa.

## Decisione

| regola | oggi | ora | fonte |
|---|---|---|---|
| rischio rugiada | T - Td sotto 3 °C | modello di Beysens con nuvole, vento e quota: sereno e calmo fino a ~5 °C, coperto o vento oltre 4,4 m/s quasi mai | Beysens 2016, Atmos. Res. 167:146 (codice NREL pvdeg); bilancio radiativo verificato (Clark-Allen, Walton, Duffie-Beckman, Chadwick 2013) |
| oggetto basso | sotto 30° | esteso sotto 30°, stella sotto 45°: dove il tempo di posa raddoppia | Kasten-Young (massa d'aria), Patat 2003 (fondo cielo), seeing X^0,6, equazione CCD |
| seeing | 2" / 4" fissi | rispetto al pavimento del setup F (diffrazione, pixel 0,68 p): incerto da seeing = F (tempo x2 per le stelle), niente da seeing = 1,73 F (FWHM doppia); senza setup 2"/4" | Airy 1,029 lambda/D; pixel p^2/12; equazione CCD |
| raffiche | 25 km/h (costruito) | resta finche' i frame non bastano, poi tarata per setup: FWHM^2 = calma^2 + c v^4, soglia dove la FWHM cresce come per il seeing | pressione 1/2 rho v^2; nessuna rigidezza universale (LX200 30-60"/kg, LOLAS-2) |
| scarto dei frame | mediana +- 2,5 MAD | mediana +- 2,5 **Qn**, minimo 10 frame | Rousseeuw & Croux 1993; simulazione: con la MAD a 10 frame falsi allarmi 3x il nominale, con Qn 1,7x |
| eccentricita' | 0,45 / 0,71 / 0,6 fissi | scarto relativo al setup (una coda, Qn); avviso "stelle allungate" se la mediana del setup supera b/a 0,8 (e 0,6) | carte di controllo (Montgomery: limiti di controllo e di specifica sono due cose); 0,8 usanza di forum |
| solito del sito | 120 notti | 250 notti | quantili distribution-free (Conover); notti autocorrelate rho 0,46-0,67 misurato su 4 siti |
| tempo di ASTAP | 60 s | limite di previsione 99,9% sui log dei tempi riusciti, per macchina e per modo, dopo 20 riusciti; tetto il cieco fallito misurato li'; minimo 30 s; prima 60 s | intervallo di previsione lognormale; RFC 6298 respinto (ritrasmissioni a costo zero) |
| Bortle del sito | 6 mesi qualunque su 12 | almeno 4 mesi, nessun buco oltre 3, livello annuo da fit armonico (regola e parole in `domini/sito.md`) | Posch et al. 2018 (stagionalita' del cielo); "6 mesi" distorce fino a 0,13 mag |

- La rugiada si giudica per vetro esposto (lente, lastra): e' il caso peggiore; uno specchio
  alluminato resta piu' caldo (Chadwick 2013).
- Restano da verificare sulle fonti primarie: fattori di piccolo campione di Qn, Beysens
  originale (un termine in H^2 di pvdeg), Hahn & Meeker.

## Conseguenze

- Nel registro questi numeri prendono il tipo D (metodo) al posto di U.
- Il venv del backend non ha scipy: Qn e il limite di previsione si scrivono in numpy o stdlib.
- Quota del sito, apertura e scala del setup diventano ingressi del meteo: arrivano dal setup
  di casa (ADR 0021).
