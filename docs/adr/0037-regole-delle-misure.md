# 0037 -- Le regole delle misure dei frame con le fonti verificate

**Stato:** accettata, 24/10/2026. Soglie tecniche scelte dalla sessione sulle convenzioni
(CLAUDE.md, principio 1). Supera in parte ADR 0022 (dieci contraddizioni interne) e conferma ADR
0032. Nessun codice: le misure nascono con `measure`.

## Contesto

Fase 2 del registro delle regole, gruppo misure. Due ricerche: documenti e codice (la misura
oggi e' solo `-analyse` di ASTAP); sorgenti di ASTAP, N.I.N.A. (master e develop), Hocus Focus,
Siril, DeepSkyStacker letti, e la documentazione di PHD2. Convenzioni vere poche: la definizione <!-- software-ok -->
di HFD, HFD = FWHM per una gaussiana, 1,4826 x MAD come sigma, l'eccentricita' dai momenti, la
massa d'aria di Pickering. Le soglie sono quasi tutte di un programma o di un forum; per scartare
un frame nessun programma usa la stessa statistica.

## Decisione

| regola | scelta | fonte |
|---|---|---|
| HFD | diametro che contiene meta' del flusso, esatto (non la formula rapida, +6,4%) | Weber & Brady via FocusMax; N.I.N.A. develop (curva di crescita) |
| rumore | 1,4826 x MAD del fondo | Rousseeuw & Croux 1993; ASTAP e N.I.N.A. lo usano |
| SNR del frame | la PSF SNR di ADR 0022 (rho 0,97 col riferimento); la formula CCD dello stesso ADR esce | nessuna convenzione: ogni programma la sua |
| valore del frame | stelle sparse su una griglia 3 x 3; le 5 zone (centro e angoli) solo per tilt e curvatura | ADR 0022, verifica |
| tilt | 100 x (HFD angolo peggiore - migliore) / HFD **mediana**; fino al 10% buono, dal 20% problema, in mezzo incerto | manuale di ASTAP: "equal or less than 10% ... good", "equal or more than 20% ... tilt problem"; codice `unit_inspector_plot.pas` |
| eccentricita' | e = sqrt(1 - b^2/a^2) dai momenti; giudizio rotonde fino a 0,45, allungate oltre 0,71; scarto (ADR 0032) a 0,6 | Bertin & Arnouts 1996 (definizione); soglie solo di forum, nessuna primaria (lo 0,42 attribuito alla documentazione di riferimento non c'e') |
| limite del setup | F = max(2 x scala, 1,029 lambda / D) | Nyquist; FWHM del disco di Airy 1,029 lambda / D |
| scarto dei frame | mediana +- 2,5 x MAD scalato, nel gruppo di ADR 0032 | Leys et al. 2013; robusta contro i frame cattivi, che spostano media e deviazione standard (Siril: mediana + k SD; ASTAP: media - k SD) | <!-- software-ok -->
| fuoco peggiorato | HFD oltre il 10° percentile della notte + 5% | N.I.N.A. `AutofocusAfterHFRIncreaseTrigger` default 5 |
| SQM dai pixel | metodo di ASTAP: massa d'aria di Pickering 2002, estinzione 0,2811 mag | `unit_sqm.pas`, manuale |
| oggetto basso | sotto 30° (massa d'aria 2) | IRAF 1,996 a 30°; uso AAVSO |

- Le misure scritte negli header (FWHM, HFR di N.I.N.A.) non si leggono: N.I.N.A. ha cambiato la
  definizione della HFR nel 2026 (media dei momenti contro curva di crescita).
- La guida non si giudica: l'app non legge i log; l'unica cifra con fonte e' "circa 1 secondo
  d'arco RMS come punto di partenza" (PHD2, Best Practices).
- Restano scelte di Marco senza convenzione: minimo 10 frame per un giudizio relativo; 6 mesi su
  12 per il Bortle del sito.

## Conseguenze

- ADR 0022 porta in testa "superata in parte da ADR 0037": formula CCD dell'SNR, "5 zone" come
  base del frame, denominatore del tilt al centro, "nessuna fonte" per il tilt.
- Il commento di `frame_metrics` in `schema.sql` (SNR dal solver) si corregge con `measure`.
