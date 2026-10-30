# 0042 -- Le misure del frame sono quelle di Image Analysis

**Stato:** accettata, 30/10/2026 (Marco). Supera ADR 0022 punto 4 (FWHM ed eccentricita' dalla
Moffat integrata sul pixel) e punto 7 (gradiente in % della mediana), ADR 0037 per tilt e
curvatura dall'HFD nelle zone di ASTAP, e il SubframeSelector come riferimento del confronto <!-- software-ok -->
(passo 24.05, `docs/domini/misure.md`). <!-- software-ok -->

## Contesto

Il 30/10/2026 PixInsight ha pubblicato Image Analysis, che sostituisce il SubframeSelector <!-- software-ok -->
(deprecato), con la sua documentazione (`doc/tools/ImageAnalysis`, 28/10) e il documento <!-- software-ok -->
ImageWeighting aggiornato. Sui 205 frame del banco, sui mono, da' gli stessi numeri del <!-- software-ok -->
SubframeSelector (stelle, fondo, rumore, PSF SNR 1,00; FWHM ed eccentricita' entro l'1%) e misura <!-- software-ok -->
57 grandezze, molte con la formula scritta. AstroLog oggi coincide su rumore, fondo, altezza,
massa d'aria, numero di stelle e direzione; si scosta su FWHM (0,81-0,99), eccentricita',
PSF SNR, tilt, curvatura e gradiente; ne manca 24. Analisi completa nel report del 30/10. <!-- software-ok -->

## Decisione

- **Riferimento unico:** ogni misura del frame che Image Analysis da' si calcola con la sua <!-- software-ok -->
  formula, citata accanto al numero (principio 1); dove la documentazione non basta, prove a
  scatola chiusa su sintetici, mai il sorgente PCL (licenza). I numeri devono tornare coi suoi
  sul banco, gruppi A e B, senza tarature. (Marco, 30/10/2026)
- **FWHM ed eccentricita'** come le sue: Moffat ellittica beta 4 valutata al centro del pixel,
  regione di campionamento adattiva, media biweight e dispersione Qn. (Marco, 30/10/2026)
- **Tilt, curvatura e gradiente** come i suoi: fit delle FWHM di tutte le stelle sul campo;
  gradiente picco-picco in unita' di rumore. (Marco, 30/10/2026)
- **Restano come misure nostre in piu'**, dette tali a schermo: HFD (regola del fuoco di
  N.I.N.A.), SQM, lato chiaro del gradiente. (Marco, 30/10/2026) <!-- software-ok -->
- **Tempo:** un frame non costa piu' di quanto costa a lui con le misure estese (3,3 s su 26 MP
  mono sul banco del 30/10). (Marco, 30/10/2026)
- Le misure che lui calcola sulla serie (estinzione relativa e da nuvole) si calcolano sulla
  serie dello stesso campo e filtro; PSFScale e PSFScaleSNR no: servono i file di
  LocalNormalization e AstroLog non integra. <!-- software-ok -->

## Conseguenze

- `tools/confronto_misure.py` confronta con Image Analysis; il SubframeSelector esce. <!-- software-ok -->
- A schermo cambiano FWHM (le stelle piccole crescono fino al 20-30%), tilt, curvatura e
  gradiente (unita' diverse); le soglie che li usano (ADR 0037, 0039) si rileggono passo per passo.
- Passi del piano 26.47-26.57 in fase 4; a valle 26.5, 32.1, 40, 40.1, 46, 46.1.
- Pesi e approvazione dei frame (sue espressioni con z-score, o le nostre soglie relative con
  Qn): da decidere, in `docs/idee.md`.
