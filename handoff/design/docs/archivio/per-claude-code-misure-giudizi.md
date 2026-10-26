# Per Claude Code — misure dei frame: backfocus e giudizi (18/10/2026)

Dal Riepilogo v2 (`pagine/Riepilogo v2.dc.html`, componente `componenti/MisureFrame`). L'utente chiede due cose nuove. La seconda va contro l'ADR 0022 ("l'app misura e basta: nessun voto"): serve una decisione di Marco prima di disegnarla.

## 1. Backfocus dai frame

Oggi dalle HFD dei quattro angoli e del centro ricaviamo tilt e curvatura di campo. L'utente vorrebbe anche capire dai frame se il backfocus e' giusto: stelle degli angoli allungate verso il centro o verso l'esterno (forma radiale o tangenziale), come fanno ASTAP (o altri strumenti) con l'analisi del campo.

Domande:
- Si puo' misurare per frame? Con che cosa (sep, ASTAP, altro) e con che affidabilita'?
- Che cosa arriva: un numero (per esempio un indice con segno: negativo = troppo corto, positivo = troppo lungo), una direzione per angolo, o tutti e due?
- Ha un senso fisico la conversione in millimetri, o resta un indice?
- Vale anche in banda stretta e con stelle sottocampionate?
- Si collega al backfocus del treno calcolato in Attrezzatura (ADR 0021)?

Nel disegno andrebbe accanto al rettangolo del sensore di tilt e curvatura, con una freccia per angolo verso il centro o verso l'esterno, e come misura nelle tessere e nei grafici.

## 2. Giudizi sulle misure

L'utente vorrebbe sapere se un oggetto o una notte e' venuto bene o male, misura per misura, come gia' facciamo con "rotonde" fino a 0,45. I giudizi terrebbero conto:
- del seeing della notte (previsto, dove c'e'; vedi la risposta sul seeing salvato in weather_nights);
- del corredo: focale, pixel, apertura, quindi campionamento e potere risolutore;
- per alcune misure, di soglie fisse.

Proposta di partenza, da correggere:
- **FWHM**: rispetto a cosa? Contro il seeing della notte (FWHM allo zenit / seeing previsto), contro il limite del corredo (potere risolutore, 2–3 × campionamento), o tutti e due? "Sottocampionata" resta un'informazione separata dal giudizio. L'utente: "ero a fuoco o no".
- **Eccentricita'**: c'e' gia' "rotonde" fino a 0,45. Serve un secondo gradino (per esempio "allungate" oltre 0,6)?
- **SNR**: si puo' giudicare? Dipende da oggetto, filtro e posa: esiste una soglia sensata, o solo il confronto con le altre notti dello stesso oggetto e filtro?
- **Tilt e curvatura**: soglie in %? (L'utente: "8 % e' buono o no?")
- **Gradiente del fondo**: soglia in %?
- **Luminosita' del cielo**: contro il Bortle del sito?
- **Stelle, fondo, rumore, massa d'aria**: niente giudizio (dipendono da campo, camera, guadagno, posa).

Per ogni giudizio servono: le parole (stesso schema degli esiti: buono / incerto / non adatto, o parole proprie come "rotonde"), le soglie con la loro fonte, e cosa succede quando un dato manca (seeing non disponibile, corredo senza apertura, frame senza scala del cielo).

Domande:
- Marco accetta i giudizi? Se si', l'ADR 0022 cambia.
- Il giudizio vale per frame, per notte (sulla mediana), per produzione, o a tutti e tre i livelli?
- Un giudizio d'insieme dell'oggetto o della notte ("ripreso bene") si vuole, o solo misura per misura? (Il disegno lo sconsiglia: si inventa un peso fra misure diverse.)

## Gia' nel disegno, da confermare
- Direzione dell'allungamento solo da 0,40, "sottocampionata" sotto 2 px (risposte del 18/10).
- Grafico "Frame per frame": due misure, la prima piena, la seconda tratteggiata; "per valore" ordina sulla prima.
