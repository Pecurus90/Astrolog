# Per Claude Design -- v24, correzioni e parole

Da Claude Code, 19/10/2026. Controllata la v24 nel codice: orizzonte (lettura, interpolazione
oltre 360/0, minimo = il piu' alto fra orizzonte e altezza minima), Progetti, collegamenti della
Dashboard con gli stessi numeri: tutto come da brief, nessuna regressione. Restano queste.

## Tre difetti

1. **Il Salva di Crea non porta alla scheda.** «Apri in Progetti» (Planner, riga 244) e «✓ In
   Progetti» (riga 756) hanno `href="#"`: vanno a `Progetti.dc.html?p={id}`, sullo stato «appena
   creato» che gia' c'e'.
2. **Nome del progetto nell'elenco**: oggi solo l'ottica («IC 1396 · Askar FRA400»). Il nome e'
   oggetto + ottica + camera, come la scheda (lo stesso ritocco gia' fatto in Trova).
3. **Impostazioni, altezza minima**: oggi una riga sola «per tutti i corpi». Sono due, e con loro
   le altre soglie: in Impostazioni una sezione «Planner» con le sette righe di ADR 0023 (partenza
   e fonte accanto):
   - Altezza minima, cielo profondo: 30° (massa d'aria 2)
   - Durata minima sopra l'altezza: 1 h
   - Distanza dalla Luna: 40°
   - Mese buono: 3 ore visibili il 15 del mese
   - Altezza minima di pianeti, Luna e Sole: 30° (massa d'aria 2)
   - Correttore di dispersione sotto: 35° (BAA)
   - Macchia Rossa: 91° (Sistema II) al 1/6/2026, deriva 1.75° al mese (Sky & Telescope, da JUPOS)

   Il disegno a 360° dell'orizzonte mostra la linea della prima (cielo profondo); nel Sistema solare
   conta la quinta.

## Due parole (Marco, glossario)

1. **«ore visibili», non «ore utili»**, in tutto Planner e Progetti: «ore utili» e' del Meteo (buio
   con cielo sereno). Nel Planner sono ore di buio con l'oggetto sopra l'altezza minima e
   l'orizzonte. Es.: «5 h visibili stanotte», «mese buono: almeno 3 ore visibili», «visibili
   stanotte · con l'orizzonte di Cima Ekar». Il Meteo e la Dashboard del meteo restano «ore utili».
2. **«mesi buoni», non «stagione»**: «stagioni» saranno delle Statistiche (primavera, estate...).
   - Gruppi: «nei loro mesi buoni» · «fuori dai mesi buoni» · «mesi buoni passati senza frame» ·
     «segnati come finiti».
   - «Torna in stagione» -> «Torna buono a {mese}».
   - «la stagione di primavera 2026 e' passata senza frame» -> «mesi buoni marzo–giugno 2026
     passati senza frame» (i mesi veri dell'oggetto).
   - «Nessun progetto nella sua stagione.» -> «Nessun progetto nei suoi mesi buoni.»; «Nessun
     progetto fuori stagione.» -> «Nessun progetto fuori dai mesi buoni.»

## Testi approvati da Marco

Tutti gli altri testi nuovi della v24 restano come sono (Impostazioni dell'orizzonte, legende delle
curve, scheda del progetto, «{n} progetti, {m} in corso · ultima scansione oggi, 07:12»), tranne
«per tutti i corpi · massa d'aria 2», che esce col punto 3.

## Per il porting (solo nota in DECISIONI)

- In Progetti «con l'orizzonte di {sito}» esce solo se il sito ha il file.
- «almeno 3 ore visibili»: il 3 viene dalle Impostazioni.

CHANGELOG e DECISIONI come al solito.
