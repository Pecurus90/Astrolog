# 0007 -- Le metriche dei frame con `sep` e numpy/scipy, non `photutils`

**Stato:** accettata; superata in parte da ADR 0033 (D1: HFD e stelle da `measure`, non da ASTAP). Codice dal passo 25 (`pipeline/stars.py`).
Resta: lo stack `sep` + numpy/scipy. arm64: `sep` 1.4.1 pubblica la ruota manylinux aarch64 per
cp312 e cp313 (PyPI, 26/10/2026); la misura dei tempi su arm64 arriva col pacchetto Docker.

## Contesto

`measure` misurera' eccentricita', fondo cielo e tilt leggendo i pixel. Deve girare anche su un
NAS Linux arm64, e `photutils` non pubblica la ruota per quell'architettura.

## Decisione

- Le metriche si fanno con **`sep` + numpy/scipy**.
- HFD, stelle e SNR li misura `measure`, non ASTAP (ADR 0033, D1; SNR: la PSF SNR, ADR 0037).

## Conseguenze

- Si riapre quando photutils pubblica la ruota arm64, se la misura dice che vale.
- Su arm64 la ruota c'e'; i tempi si misurano col pacchetto Docker multi-arch (passo 47), e se
  non reggono si riapre qui.
