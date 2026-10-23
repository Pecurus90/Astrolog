# Per Claude Design -- La zona di selezione dei frame

Da Claude Code, 23/10/2026. Pagina nuova. Decisione in `docs/adr/0032-zona-di-selezione.md`; le
misure e i giudizi in `docs/adr/0022-misure-dei-frame.md` e nella brief
`design-attrezzatura-v2-e-misure.md` (parte 2). Le etichette qui sotto sono proposte: Marco le
approva sulla tavola.

**Cosa cambia rispetto alla brief delle misure**: la' l'app "misura e basta, nessuno scarto". Ora
c'e' una zona dove l'utente sceglie quali frame tenere per lo stacking. Le misure e i giudizi
restano quelli; si aggiungono la scelta e le regole.

## 1. A cosa serve

Prima dello stacking chi fotografa scarta i frame mossi, sfocati, velati. Oggi lo fa con strumenti
separati (blink, SubframeSelector, grafici di Siril). Qui ha le misure gia' fatte, raggruppate <!-- software-ok -->
come pensa lui: **notte per notte, oggetto per oggetto, setup per setup**.

## 2. Come si entra e come si raggruppa

- Si sceglie un **gruppo**: oggetto + setup + filtro e' l'unita' tipica dello stacking. Dentro, i
  frame di tutte le notti, divisi per notte.
- Si puo' partire anche da una notte (tutti gli oggetti di quella notte) o da un setup.
- In testa al gruppo, il **riepilogo**: frame tenuti / totali, **integrazione tenuta / totale**
  (es. "4 h 10 min di 5 h 20 min"), quanti esclusi a mano, quanti proposti dalle regole.

## 3. Cosa si vede di ogni frame

Una riga per frame, ordinabile per ogni colonna: ora, notte, posa, filtro, FWHM (″ e px), HFD
(″ e px), stelle, eccentricita' (con direzione da 0,4 in su), SNR, fondo cielo (ADU), gradiente,
massa d'aria, luminosita' del cielo. Accanto, i giudizi gia' decisi (ADR 0022): "fuoco peggiore",
"SNR basso per la notte", "SNR basso per l'oggetto", "HFD alta per l'oggetto", "oggetto basso",
"allungate". I giudizi informano; la scelta e' una cosa a parte.

**Grafici**, una misura alla volta scelta dall'utente:
- lungo il tempo, notte per notte, con la soglia attiva tratteggiata e i frame esclusi segnati;
- la distribuzione del gruppo (mediana, quartili), con la soglia.
Selezionare punti nel grafico seleziona le righe, e viceversa.

## 4. Gli stati di un frame

| stato | come nasce | si vede |
|---|---|---|
| tenuto | predefinito | normale |
| proposto da escludere | una regola attiva lo prende | segnato, col nome della regola |
| escluso a mano | l'utente | segnato, "a mano" |
| tenuto a mano | l'utente, contro una regola | segnato, "a mano"; la regola non lo tocca piu' |
| in "scartati" | spostato su comando | in grigio, col percorso nuovo |
| non misurato | measure non l'ha ancora misurato o non puo' | le misure tacciono; le regole non lo toccano |

**La scelta a mano vince sempre** sulla regola, anche quando la regola cambia dopo. Tutto si
annulla: un frame escluso si riammette con un gesto.

## 5. Le azioni

- **Escludi / Tieni**: su un frame, su una selezione, su un'area del grafico.
- **Applica le proposte**: le esclusioni proposte diventano esclusioni (resta il nome della regola).
- **Sposta in "scartati"**: i frame esclusi vanno nella sottocartella `scartati` accanto ai loro
  file. Conferma con numero di frame, dimensione e cartelle toccate. Poi lo stacking non li vede.
- **Riporta indietro**: da "scartati" alla cartella di prima.
- **Cancella da "scartati"**: solo da li', con **avviso**: e' per sempre, il numero di frame e i
  GB. Mai una cancellazione diretta da una cartella normale.
- Errori da disegnare: cartella in sola lettura (NAS), disco staccato, file aperto da un altro
  programma: l'azione dice quanti frame ha fatto e quanti no, e perche'.

## 6. Le regole, nelle Impostazioni

Sezione nuova **"Selezione dei frame"**:
- **Soglie per misura**: assolute ("FWHM sopra 4.0″") o relative al gruppo ("HFD oltre mediana +
  2 MAD"). Le proposte di partenza sono le relative gia' decise (SNR sotto mediana − 2 MAD, HFD
  oltre mediana + 2 MAD, per oggetto e filtro): una soglia assoluta pubblica non esiste.
- **Espressioni**: combinazioni scritte dall'utente, es. `FWHM < 3.5 e Eccentricita' < 0.6 e
  Stelle > 300`, con i nomi delle misure da un elenco. Mentre si scrive, l'anteprima: "escluderebbe
  23 frame su 412 nel gruppo M 31 · FRA400 + 2600MM · L".
- Ogni regola si accende o spegne, vale per tutti i gruppi o per un setup.
- Una regola **propone**, non sposta e non cancella niente da sola.

## 7. Esempio

M 31 · Askar FRA400 + ZWO ASI2600MM Pro · L, 3 notti, 120 frame da 300 s = 10 h.
Regola attiva "HFD oltre mediana + 2 MAD": propone 9 frame (8 della notte del 12/10, nuvole
sottili). L'utente ne tiene 2 a mano, ne esclude altri 3 (scia di satellite). Riepilogo:
"110 di 120 frame, 9 h 10 min di 10 h". Poi "Sposta in scartati": 10 frame, 520 MB, 3 cartelle.

## 8. Cosa vi chiedo

1. La pagina: scelta del gruppo, riepilogo, tabella, grafici collegati.
2. Gli stati del §4 e le azioni del §5, con le conferme e l'avviso di cancellazione.
3. La sezione "Selezione dei frame" nelle Impostazioni, con l'anteprima dell'espressione.
4. Gli errori del §5.
5. Desktop prima; il mobile alla fine (la tabella dovra' diventare una lista).

CHANGELOG e DECISIONI come al solito.
