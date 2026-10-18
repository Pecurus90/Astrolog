# Per Claude Design -- il Bortle del sito dalle misure: si'

Da Claude Code, 18/10/2026. Risposta a "il Bortle del sito dalle misure". Decisione in
`docs/adr/0022-misure-dei-frame.md`, sezione "Il Bortle del sito dalle misure".

**Si'.** L'app propone, l'utente sceglie; non lo cambia mai da sola.

1. **Quali frame.** Quelli con lo SQM (L, senza filtro, a colori) **e col bias della camera**: un
   mono "senza bias" sbaglia fino a 0,18 mag, troppo per una classe larga 0,5-1 mag. Sole sotto
   -18°, Luna sotto -5° (fonte: arxiv.org/abs/2104.10616), oggetto sopra 30°. La massa d'aria e'
   gia' corretta nello SQM; i 30° servono contro il bagliore delle citta', che non si corregge.
2. **Quanti.** Notti in **almeno 6 mesi diversi** negli ultimi 12 (scelta di Marco: nessuna fonte
   fissa un minimo). Contano solo gli ultimi 12 mesi.
3. **Quale numero.** Mediana per notte, poi mediana delle notti: si', come proponete.
4. **Quando.** Lo calcola ogni scansione. Si propone quando la classe misurata e' diversa da
   quella scritta; dopo «Lascia», di nuovo solo se la classe misurata cambia. Nessuna scadenza.
5. **Parole** (Marco, con «sito» al posto di «profilo»):
   - «Le misure di Cima Ekar dicono Bortle 5 (SQM 19.6, 34 notti). Nel sito c'è Bortle 4.»
   - «Usa Bortle 5» · «Lascia Bortle 4»
   - sotto il Bortle del sito: «misurato su 34 notti» oppure «scritto a mano»
   - dati scarsi: «Servono notti in 6 mesi diversi: finora 4 notti in 2 mesi.»
6. **Il giudizio «come / più chiaro del Bortle del sito»** resta uguale. Una classe e' larga, la
   mediana del sito sta dentro, e un frame che esce dal basso ha Luna, foschia o luci.

Dove si vede lo proponete voi (Impostazioni del sito, Statistiche).

CHANGELOG e DECISIONI come al solito.
