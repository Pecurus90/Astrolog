# 0007 -- Le metriche dei frame con `sep` e numpy/scipy, non `photutils`

**Stato:** accettata; superata in parte da ADR 0033 (D1: HFD e stelle da `measure`, non da ASTAP). Nessun codice: nasce con `measure`.
Resta: lo stack `sep` + numpy/scipy e la riapertura per arm64.

## Contesto

`measure` misurera' eccentricita', fondo cielo e tilt leggendo i pixel. Deve girare anche su un
NAS Linux arm64, e `photutils` non pubblica la ruota per quell'architettura.

## Decisione

- Le metriche si fanno con **`sep` + numpy/scipy**.
- HFD, stelle e SNR li misura `measure`, non ASTAP (ADR 0033, D1; SNR: la PSF SNR, ADR 0037).

## Conseguenze

- Si riapre quando photutils pubblica la ruota arm64, se la misura dice che vale.
- Lo stack si sceglie con la misura su arm64 in mano, quando nasce `measure`.
