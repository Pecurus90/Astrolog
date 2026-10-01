# 0007 -- Le metriche dei frame con `sep` e numpy/scipy, non `photutils`

**Stato:** accettata

## Contesto

`measure` misurera' eccentricita', fondo cielo e tilt leggendo i pixel. Deve girare anche su un
NAS Linux arm64, e `photutils` non pubblica la ruota per quell'architettura.

## Decisione

- Le metriche si fanno con **`sep` + numpy/scipy**.
- Prima HFD, stelle e SNR da ASTAP, che li da' gia' (`frame_metrics`, `source = 'astap'`); poi
  `sep`.

## Conseguenze

- Si riapre quando photutils pubblica la ruota arm64, se la misura dice che vale.
- Lo stack si sceglie con la misura su arm64 in mano, quando nasce `measure`.
