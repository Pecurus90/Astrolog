# 0032 -- La zona di selezione dei frame

**Stato:** accettata, 23/10/2026 (Marco); soglie e file rivisti lo stesso giorno sulla tavola di
Claude Design, con le fonti sotto. Si costruisce dopo measure (ADR 0022) e la parte 2 della
pipeline nuova (notti, setup, oggetti).

## Contesto

Chi fotografa sceglie i frame buoni prima dello stacking con strumenti separati (blink, grafici
delle misure). L'app ha misure, notti, oggetti e setup insieme: puo' mostrare le statistiche dove
servono. Fin qui l'app non votava i frame e non toccava mai un FITS (`domini/spina.md`).

## Decisione

- **Un'area dedicata** per scegliere i frame, con le statistiche notte per notte, oggetto per
  oggetto, setup per setup.
- **Soglie e una formula** in una sezione delle impostazioni, per setup e filtro, modificabili
  anche dalla pagina. **La scelta a mano vince sempre** sull'automatica.
- **Un frame escluso resta nell'app**, reversibile, e sopravvive alle scansioni.
- **Su comando, con conferma**, i frame esclusi si spostano nella cartella "scartate"; **da li'
  si eliminano solo con avviso**. Mai una cancellazione da sola o diretta.

### Il gruppo

Oggetto + setup + filtro + posa + guadagno, tutte le notti, solo frame misurati. Il fondo in ADU
cambia con posa e guadagno, l'SNR con la posa; WBPP raggruppa da solo per filtro, posa e binning,
il guadagno solo con una keyword (guida WBPP di B. Landmann, tabella 1).

### Le soglie

- **Relative**: mediana ± 2,5 MAD scalato (1,4826 × mediana degli scarti), come i giudizi
  (ADR 0022): "By default, we suggest a threshold of 2.5" (Leys et al. 2013, J. Exp. Soc.
  Psychol. 49:764, doi 10.1016/j.jesp.2013.03.013). Non il 2 dei forum ("FWHMSigma < 2"): i
  `*Sigma` del SubframeSelector dividono per la deviazione media dalla mediana, non scalata
  (PCL, `SubframeSelectorMeasureData.h`). Una soglia assoluta pubblica non esiste per nessuna
  misura.
- **Dalla mediana o a valore**: ogni riga lo sceglie l'utente (Marco); le partenze sono dalla
  mediana dove una soglia a valore non ha fonte.
- **Partenze, uguali per ogni setup** (un numero dei setup di Marco a un altro utente non serve):

  | misura | partenza |
  |---|---|
  | FWHM | accesa, > mediana + 2,5 MAD |
  | Stelle | accesa, < mediana − 2,5 MAD |
  | SNR | accesa, < mediana − 2,5 MAD |
  | Fondo cielo | spenta, > mediana + 2,5 MAD |
  | Eccentricita' | spenta; accesa parte a valore > 0,6 (Marco: nessuna soglia ufficiale, forum 0,5-0,6; lo 0,71 ESO e' un giudizio) |
  | Altezza | spenta, < 30° ("oggetto basso", ADR 0022) |

- **Minimo 10 frame** nel gruppo (Marco: nessuna fonte fissa un minimo; e' il numero dei giudizi
  per la notte). Sotto, la soglia relativa tace e lo dice.
- **Una FWHM a valore sotto il limite del setup** (F di ADR 0022) scarterebbe tutto: lo si dice.
- **Al limite**: dalla parte buona, entro 1 MAD dalla soglia relativa. Stessa distanza fra avviso e
  azione delle carte di controllo, 2σ e 3σ (NIST/SEMATECH 6.3.2; ISO 7870-2). Nessun programma di
  astrofotografia ha una zona di avviso. Una soglia a valore non ha "al limite".

### I file

- **Sposta**: in `<radice dell'archivio>/scartate/<stesso percorso>`, sullo stesso disco, con
  l'elenco dei percorsi per "Riporta indietro" (Marco). Non una sottocartella accanto ai light:
  il "+ Directory" di WBPP scende in tutto il sottoalbero e non esclude cartelle
  (`BPP-Helper.js`, `File.searchDirectory(..., true /*recursive*/)`). Siril e DeepSkyStacker <!-- software-ok -->
  leggono una cartella sola.
- **Elimina**: nel cestino. Dove il cestino non c'e' (cartella di rete, NAS, Docker) si cancella
  per sempre, e la conferma lo dice prima (Marco).

## Conseguenze

- E' la sola parte dell'app che sposta o cancella un FITS; tutto il resto li legge e basta.
- Uno spostamento in "scartate" la scansione lo vede come spostamento (stessa posa).
- Su una cartella in sola lettura (NAS) spostare e cancellare falliscono, e l'app lo dice.
