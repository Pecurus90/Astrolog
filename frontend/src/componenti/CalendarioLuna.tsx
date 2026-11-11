import type { ReactNode } from "react"

import { t } from "../i18n"
import { CorniceCalendario, type NavigaMese, cellaDi, giorniNelMese } from "./CalendarioNotti"
import { gesto } from "./gesto"

/** The Moon's step on a day: 0 broadband good, 1 broadband marginal, 2 narrowband only. */
export type GradinoLuna = 0 | 1 | 2

/** A day of the Moon calendar, as the page writes it from the API. */
export interface GiornoLuna {
  d: number
  g: GradinoLuna
  /** Dark hours without the Moon, already written ("4 h"). */
  ore: string
  /** New or full Moon. */
  evento?: "nuova" | "piena"
  /** A night was shot that day. */
  stella?: boolean
  sel?: boolean
  on?: () => void
  /** What a screen reader says of the day. */
  aria: string
}

const SEGNI_GRADINO = ["\u2713", "!", "\u25d0"] as const
const SEGNI_EVENTO = { nuova: "\u25cf", piena: "\u25cb" } as const
const TRATTEGGIO = "repeating-linear-gradient(135deg, var(--giorno-su) 0 3px, transparent 3px 8px)"
const FONDO: Record<GradinoLuna, string> = {
  0: "var(--giorno-su)",
  1: TRATTEGGIO,
  2: "var(--carta-2)",
}
const TESTO: Record<GradinoLuna, string> = {
  0: "var(--giorno-su-testo)",
  1: "var(--testo)",
  2: "var(--testo)",
}

/**
 * The month's Moon (v79 `CalendarioNotti`, `tipo="luna"`): each day its step on the Moon scale and
 * the dark hours without the Moon, a star where a night was shot, the two events. The whole
 * month: the Moon looks ahead too.
 */
export function CalendarioLuna({
  anno,
  mese,
  giorni,
  oggi,
  buona,
  limite,
  nuova,
  piena,
  onPrima,
  onDopo,
  primaNo = false,
  dopoNo = false,
  formato = "desktop",
}: {
  anno: number
  /** Month, 0-11. */
  mese: number
  giorni: GiornoLuna[]
  oggi?: number
  /** The Moon scale's two bounds, in percent, for the legend. */
  buona: string
  limite: string
  /** The legend's events, already written: new Moon and full Moon with their day. */
  nuova: string
  piena: string
} & NavigaMese) {
  const perGiorno = new Map(giorni.map((g) => [g.d, g]))
  const nelMese = giorniNelMese(anno, mese)
  const cella = cellaDi(formato)
  const celle: ReactNode[] = []
  for (let d = 1; d <= nelMese; d++) {
    const g = perGiorno.get(d)
    const stile = {
      ...cella,
      background: g?.sel ? "var(--testo)" : g ? FONDO[g.g] : "var(--carta-2)",
      color: g?.sel ? "var(--carta)" : g ? TESTO[g.g] : "var(--testo)",
      boxShadow: `inset 0 0 0 ${d === oggi ? "1.5px" : "0"} var(--testo)`,
      fontWeight: d === oggi ? 600 : 500,
      cursor: g?.on ? "pointer" : "default",
    }
    const dentro = (
      <>
        <span>{d}</span>
        {g && (
          <span className="al-c-calendario-notti__blocco-2">
            {`${g.evento ? SEGNI_EVENTO[g.evento] : SEGNI_GRADINO[g.g]} ${g.ore}`}
          </span>
        )}
        {g?.stella && (
          <span className="al-c-calendario-notti__strato-1" aria-hidden="true">
            {"\u2605"}
          </span>
        )}
      </>
    )
    celle.push(
      g?.on ? (
        <a
          key={d}
          className="al-c-calendario-notti__colonna-4"
          href="#"
          role="button"
          onClick={gesto(g.on)}
          aria-pressed={g.sel ? "true" : "false"}
          aria-label={g.aria}
          style={stile}
        >
          {dentro}
        </a>
      ) : (
        <span
          key={d}
          className="al-c-calendario-notti__colonna-4"
          aria-label={g?.aria}
          style={stile}
        >
          {dentro}
        </span>
      ),
    )
  }

  const legenda = [
    { s: "\u2713", l: t("ui.moonCalendar.good", { pct: buona }), bg: FONDO[0], fg: TESTO[0] },
    { s: "!", l: t("ui.moonCalendar.marginal", { pct: limite }), bg: FONDO[1], fg: TESTO[1] },
    { s: "\u25d0", l: t("ui.moonCalendar.narrow"), bg: FONDO[2], fg: TESTO[2] },
    { s: "h", l: t("ui.moonCalendar.hours"), bg: FONDO[2], fg: TESTO[2] },
    { s: "\u2605", l: t("ui.moonCalendar.shot"), bg: FONDO[2], fg: TESTO[2] },
    { s: SEGNI_EVENTO.nuova, l: nuova, bg: FONDO[2], fg: TESTO[2] },
    { s: SEGNI_EVENTO.piena, l: piena, bg: FONDO[2], fg: TESTO[2] },
  ].filter((v) => v.l)

  return (
    <CorniceCalendario
      anno={anno}
      mese={mese}
      celle={celle}
      legenda={legenda}
      onPrima={onPrima}
      onDopo={onDopo}
      primaNo={primaNo}
      dopoNo={dopoNo}
      formato={formato}
    />
  )
}
