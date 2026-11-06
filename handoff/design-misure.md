# Per Claude Design -- Le misure dei frame: tutte quelle che l'app calcola

Da Claude Code, 6/11/2026, con le scelte di Marco dello stesso giorno. Confronto fra la tavola v58.6
(`MisureFrame`, Selezione dei frame) e cio' che l'app misura davvero: 63 misure per frame contro
le 12 della tavola. Le 12 tessere restano come sono; qui si aggiunge, non si toglie nulla.

## 1. Le misure in piu': un elenco a discesa (Marco)

Accanto alle 12 tessere, un elenco a discesa «Altre misure ▾» che sceglie una misura e la mostra
come le tessere (mediana, quartili, grafico, per filtro), nel frame scelto e nel Riepilogo. Le voci,
a gruppi:

- **Stelle e forma**: PSFResidual (qualita' del fit); FWHM Sigma ed Eccentricita' Sigma (quanto
  cambiano nel campo); direzione dell'allungamento e coerenza (stelle allungate tutte nello stesso
  verso: inseguimento o vento; in versi diversi: ottica); stelle sature.
- **Segnale**: PSF Signal Weight (il peso con cui PixInsight integra), PSF Flux, PSF Mean Flux, <!-- software-ok -->
  PSF Count.
- **Fondo e pixel**: SkyRate (fondo al secondo: si confronta fra tempi di posa diversi), Mediana, Sigma,
  Entropia, NoiseRatio, SNR (alla Image Analysis), M*, N*, banding di righe e di colonne, lato
  chiaro del gradiente (anche come angolo sul cielo).
- **Cielo**: azimut, angolo orario, lato del pilastro, zero point dello SQM.
- **Luna e Sole**: altezza della Luna, distanza dall'oggetto, parte illuminata; altezza del Sole.
- **Trasparenza e nuvole**: si calcolano solo su una serie di frame dello stesso campo e filtro.
  Arrivano dopo; serve ora lo stato «serve una serie di almeno 5 frame».

Nell'elenco le voci stanno a gruppi. La misura scelta fa come una tessera: entra nei grafici
(fino a due, come oggi) e nella tabella per filtro, e la pagina la ricorda alla visita dopo.
Nessuna di queste ha una soglia pubblica: senza pillola di giudizio.

## 2. Tilt e curvatura: due misure (Marco)

- In tessera, come oggi: **% alla ASTAP** dalle HFD dei quattro angoli e del centro, col giudizio
  10 / 20 % di ASTAP.
- Nel dettaglio, accanto: **FWHMTilt e FWHMCurvature di Image Analysis**, in px, senza giudizio
  (nessuna soglia pubblica).

## 3. Gradiente: due unita' (Marco)

- In tessera: **unita' di rumore** (picco-picco della superficie diviso il rumore, come Image
  Analysis): si confronta fra camere.
- Accanto: la **% del fondo**, dalla stessa superficie.

## 4. Selezione dei frame: criteri in piu' (Marco)

Oltre ai sei di oggi (FWHM, eccentricita', stelle, SNR, fondo, altezza):
- **PSF Signal Weight** (piu' alto e' meglio) e **Scie** (numero per frame, da 0 a 16);
- **Luna**: altezza, distanza dall'oggetto, parte illuminata;
- **SkyRate**.

La **formula libera** legge tutte le misure dell'elenco del punto 1, come le espressioni del
SubframeSelector di PixInsight; l'aiuto della formula le elenca coi loro nomi. <!-- software-ok -->

## 5. Da correggere nella tavola

- **2,5 MAD -> 2,5 Qn**: i giudizi relativi (SNR basso, HFD alta, soglie partenza della Selezione)
  usano lo stimatore Qn di Rousseeuw e Croux (ADR 0039, Marco 24/10), non il MAD del 23/10. Cambia
  solo la scritta.
- **Fondo cielo e Rumore del fondo** si confrontano solo fra frame con stessa camera, guadagno e
  posa: quando un grafico li mescola, una riga lo dice.
- **Eccentricita'**: oltre al giudizio sul frame (0,45 / 0,71), l'app avvisa sul setup quando la
  sua mediana supera 0,6 (ADR 0039): serve il posto per l'avviso nell'Attrezzatura o nel Riepilogo.
- I valori che la tavola calcola (allo zenit, tilt, curvatura, quartili, mediane) arrivano gia'
  fatti dall'app: nella tavola possono restare simulati.
