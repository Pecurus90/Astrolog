import type { CSSProperties } from "react"

import { type Chiave, t } from "../i18n"
import { gesto } from "./gesto"
import { ACCENTI, type Accento, type Formato, type ModoScelto, useTema } from "./Tema"

// [T] SceltaTema.dc.html `L`: the layout per format
const MISURE: Record<
  Formato,
  {
    cols: string
    dir: CSSProperties["flexDirection"]
    al: string
    gap: string
    voceH: string
    campW: string
    campH: string
    nomePad: string
  }
> = {
  desktop: {
    cols: "repeat(auto-fill,minmax(124px,1fr))",
    dir: "column",
    al: "stretch",
    gap: "10px",
    voceH: "0",
    campW: "100%",
    campH: "64px",
    nomePad: "0 4px 4px",
  },
  telefono: {
    cols: "minmax(0,1fr)",
    dir: "row",
    al: "center",
    gap: "14px",
    voceH: "60px",
    campW: "112px",
    campH: "44px",
    nomePad: "0",
  },
}

export const NOMI_MODO: Record<ModoScelto, Chiave> = {
  chiaro: "theme.mode.light",
  scuro: "theme.mode.dark",
  automatico: "theme.mode.auto",
}

export const NOMI_ACCENTO: Record<Accento, Chiave> = {
  originale: "theme.accent.original",
  ambra: "theme.accent.amber",
  turchese: "theme.accent.teal",
  corallo: "theme.accent.coral",
  ghiaccio: "theme.accent.ice",
}

/**
 * **SceltaTema** (v82 component): the mode and the five accents, each accent with its swatch in
 * the mode worn now (`useTema`). The swatch wears the sheet's tokens under its own `data-accento`.
 *
 * - **Automatico** follows the home site's sunset and sunrise: without a site (`sito` null) it is
 *   off and the note says why; chosen, the note names the site.
 */
export function SceltaTema({
  modo,
  accento,
  sito,
  formato,
  onModo,
  onAccento,
}: {
  modo: ModoScelto
  accento: Accento
  sito: string | null
  formato: Formato
  onModo: (m: ModoScelto) => void
  onAccento: (a: Accento) => void
}) {
  const L = MISURE[formato]
  const visto = useTema().modo
  const nota =
    sito === null
      ? t("theme.auto.noSite")
      : modo === "automatico"
        ? t("theme.auto.site", { sito })
        : null
  const voceModo = (k: ModoScelto) => {
    const sel = k === modo
    // [T] v82: a chosen Automatico stays reachable even if the site went
    const no = k === "automatico" && sito === null && !sel
    return (
      <a
        key={k}
        className="al-scelta__voce"
        href="#"
        role="radio"
        aria-checked={sel ? "true" : "false"}
        aria-disabled={no ? "true" : undefined}
        onClick={gesto(() => {
          if (!no) onModo(k)
        })}
        style={{ opacity: no ? 0.45 : 1, cursor: no ? "not-allowed" : "pointer" }}
      >
        {t(NOMI_MODO[k])}
      </a>
    )
  }
  return (
    <div className="al-c-scelta-tema__colonna-1" role="group" aria-label={t("theme.label")}>
      <div className="al-c-scelta-tema__colonna-2">
        <span className="al-c-scelta-tema__testo-1" id="st-modo">
          {t("theme.mode")}
        </span>
        <span
          className="al-scelta al-scelta--segmentato al-scelta--sottili"
          role="radiogroup"
          aria-labelledby="st-modo"
          style={{ alignSelf: "flex-start" }}
        >
          {voceModo("chiaro")}
          {voceModo("scuro")}
          {voceModo("automatico")}
        </span>
        {nota && <span className="al-c-scelta-tema__testo-2">{nota}</span>}
      </div>
      <div className="al-c-scelta-tema__colonna-2">
        <span className="al-c-scelta-tema__testo-1" id="st-acc">
          {t("theme.accent")}
        </span>
        <span
          className="al-c-scelta-tema__centro-1"
          role="radiogroup"
          aria-labelledby="st-acc"
          style={{ gridTemplateColumns: L.cols }}
        >
          {ACCENTI.map((k) => {
            const sel = k === accento
            return (
              <a
                key={k}
                className="al-c-scelta-tema__riga-3"
                href="#"
                role="radio"
                aria-checked={sel ? "true" : "false"}
                onClick={gesto(() => onAccento(k))}
                style={{
                  flexDirection: L.dir,
                  alignItems: L.al,
                  gap: L.gap,
                  minHeight: L.voceH,
                  background: sel ? "var(--carta-2)" : "transparent",
                  boxShadow: `inset 0 0 0 ${sel ? "2px" : "1px"} ${sel ? "var(--testo)" : "var(--linea)"}`,
                }}
              >
                {/* the swatch wears the accent's own tokens, in the mode in use */}
                <span
                  className="al-c-scelta-tema__riga-4"
                  aria-hidden="true"
                  data-modo={visto}
                  data-accento={k}
                  style={{
                    width: L.campW,
                    height: L.campH,
                    background: "var(--telaio)",
                    boxShadow: "inset 0 0 0 1px var(--linea)",
                  }}
                >
                  <span className="al-c-scelta-tema__riga-5" style={{ background: "var(--carta)" }}>
                    <span
                      className="al-c-scelta-tema__tondo-1"
                      style={{ border: "3px solid var(--accento)" }}
                    />
                    <span
                      className="al-c-scelta-tema__pillola-1"
                      style={{ background: "var(--scelta)", color: "var(--scelta-testo)" }}
                    >
                      {t("theme.swatch")}
                    </span>
                  </span>
                </span>
                <span className="al-c-scelta-tema__riga-6" style={{ padding: L.nomePad }}>
                  <span
                    className="al-c-scelta-tema__tondo-2"
                    aria-hidden="true"
                    style={
                      sel
                        ? {
                            background: "var(--testo)",
                            color: "var(--carta)",
                            border: "1.5px solid var(--testo)",
                          }
                        : {
                            background: "transparent",
                            color: "var(--testo)",
                            border: "1.5px solid var(--tenue)",
                          }
                    }
                  >
                    {sel ? "✓" /* glifo-ok: segno della tavola */ : ""}
                  </span>
                  <span
                    className="al-c-scelta-tema__blocco-2"
                    style={{ fontWeight: sel ? 600 : 400 }}
                  >
                    {t(NOMI_ACCENTO[k])}
                  </span>
                </span>
              </a>
            )
          })}
        </span>
      </div>
    </div>
  )
}
