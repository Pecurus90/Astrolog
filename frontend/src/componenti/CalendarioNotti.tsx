import type { ReactNode } from "react"

import { type Chiave, giornoDelMese, meseEAnno, t } from "../i18n"
import { gesto } from "./gesto"
import { type Formato, useTema } from "./Tema"

/** A night's outcome in the calendar: 0 good, 1 uncertain, 2 not suitable, -1 no weather. */
export type EsitoNotte = 0 | 1 | 2 | -1

/** A day with nights, as the app sends it. */
export interface GiornoNotti {
  /** Day of the month. */
  d: number
  /** The outcome of each night that day, one sign each. */
  esiti: EsitoNotte[]
  /** The outcome that colours the day, chosen by the app. */
  esito: EsitoNotte
  sel?: boolean
  on?: () => void
  aria?: string
}

// signs of the delivery's tema.js (SEGNI), "?" for no weather
const SEGNI: Record<EsitoNotte, string> = { 0: "\u2713", 1: "!", 2: "\u2715", [-1]: "?" }
const TINTE: Record<EsitoNotte, { fondo: string; testo: string }> = {
  0: { fondo: "var(--buono-fondo)", testo: "var(--buono-testo)" },
  1: { fondo: "var(--incerto-fondo)", testo: "var(--incerto-testo)" },
  2: { fondo: "var(--non-adatto-fondo)", testo: "var(--non-adatto-testo)" },
  [-1]: { fondo: "var(--carta-2)", testo: "var(--testo)" },
}
const LEGENDA: [EsitoNotte, Chiave][] = [
  [0, "ui.outcome.good"],
  [1, "ui.outcome.uncertain"],
  [2, "ui.outcome.unsuitable"],
  [-1, "ui.calendar.noWeather"],
]
const SETTIMANA: Chiave[] = [
  "ui.calendar.mon",
  "ui.calendar.tue",
  "ui.calendar.wed",
  "ui.calendar.thu",
  "ui.calendar.fri",
  "ui.calendar.sat",
  "ui.calendar.sun",
]

const MISURE = {
  telefono: {
    gap: "12px",
    nav: "44px",
    navFs: "18px",
    tfs: "17px",
    gg: "3px",
    dpb: "0",
    ch: "46px",
    cg: "2px",
    cfs: "14px",
    lmt: "0",
    lpad: "0 4px",
  },
  desktop: {
    gap: "14px",
    nav: "36px",
    navFs: "17px",
    tfs: "18px",
    gg: "6px",
    dpb: "2px",
    ch: "42px",
    cg: "1px",
    cfs: "13px",
    lmt: "auto",
    lpad: "0",
  },
} as const

const due = (n: number): string => String(n).padStart(2, "0")

/** Monday-first column of a date: grid geometry, not a judgement. */
const colonna = (anno: number, mese: number, giorno: number): number =>
  (new Date(Date.UTC(anno, mese, giorno)).getUTCDay() + 6) % 7

/** Days in a month (0-11): calendar geometry. */
export const giorniNelMese = (anno: number, mese: number): number =>
  new Date(Date.UTC(anno, mese + 1, 0)).getUTCDate()

/** A day cell's size on each form. */
export function cellaDi(formato: Formato): { height: string; gap: string; fontSize: string } {
  const L = MISURE[formato]
  return { height: L.ch, gap: L.cg, fontSize: L.cfs }
}

/**
 * The month's nights (v76 `CalendarioNotti`, `tipo="notti"`): a day per cell, its nights' signs,
 * coloured by the outcome the app chose. In the current month the grid stops at today's week.
 */
export function CalendarioNotti({
  anno,
  mese,
  giorni = [],
  oggi,
  titolo,
  sub,
  numero,
  numeroL,
  conta,
  onPrima,
  onDopo,
  primaNo = false,
  dopoNo = false,
  formato = "desktop",
}: {
  anno: number
  /** Month, 0-11. */
  mese: number
  giorni?: GiornoNotti[]
  /** Today's day of the month in the site's time zone, only when the month shown is the current one. */
  oggi?: number
  /** Without it, month and year. */
  titolo?: string
  sub?: string
  /** The big number above the grid, its word, and the line below. */
  numero?: string
  numeroL?: string
  conta?: string
} & NavigaMese) {
  const perGiorno = new Map(giorni.map((g) => [g.d, g]))
  const nelMese = giorniNelMese(anno, mese)
  const chiusa = oggi === undefined ? nelMese : oggi + 6 - colonna(anno, mese, oggi)
  const fine = chiusa < nelMese ? chiusa : nelMese
  const mese2 = `${anno}-${due(mese + 1)}`
  const cella = cellaDi(formato)
  const celle: ReactNode[] = []

  for (let d = 1; d <= fine; d++) {
    const g = perGiorno.get(d)
    const adesso = d === oggi
    const anello = `inset 0 0 0 ${adesso ? "1.5px" : "0"} var(--testo)`
    if (!g) {
      const dopo = oggi !== undefined && d > oggi
      celle.push(
        <span
          key={d}
          className="al-c-calendario-notti__colonna-4"
          aria-hidden={dopo ? "true" : undefined}
          style={{
            ...cella,
            background: "transparent",
            color: "var(--tenue)",
            boxShadow: anello,
            fontWeight: adesso ? 600 : 400,
            visibility: dopo ? "hidden" : "inherit",
          }}
        >
          <span aria-hidden={adesso ? "true" : undefined}>{dopo ? "" : d}</span>
          <span className="al-c-calendario-notti__blocco-2" />
          {adesso && (
            <span className="al-solo-voce">
              {t("ui.calendar.today", { giorno: giornoDelMese(`${mese2}-${due(d)}`) })}
            </span>
          )}
        </span>,
      )
      continue
    }
    const tinta = TINTE[g.esito]
    celle.push(
      <a
        key={d}
        className="al-c-calendario-notti__colonna-4"
        href="#"
        onClick={gesto(g.on)}
        role="button"
        aria-pressed={g.sel ? "true" : "false"}
        aria-label={g.aria}
        style={{
          ...cella,
          background: g.sel ? "var(--scelta)" : tinta.fondo,
          color: g.sel ? "var(--scelta-testo)" : tinta.testo,
          boxShadow: anello,
          fontWeight: 600,
          cursor: "pointer",
        }}
      >
        <span>{d}</span>
        <span className="al-c-calendario-notti__blocco-2">
          {g.esiti.map((e) => SEGNI[e]).join("")}
        </span>
      </a>,
    )
  }

  return (
    <CorniceCalendario
      anno={anno}
      mese={mese}
      titolo={titolo}
      sub={sub}
      celle={celle}
      legenda={LEGENDA.map(([e, k]) => ({
        s: SEGNI[e],
        l: t(k),
        bg: TINTE[e].fondo,
        fg: TINTE[e].testo,
      }))}
      onPrima={onPrima}
      onDopo={onDopo}
      primaNo={primaNo}
      dopoNo={dopoNo}
      formato={formato}
      sopra={
        numero && (
          <span className="al-c-calendario-notti__colonna-3">
            <span className="al-c-calendario-notti__riga-2">
              <span className="al-c-calendario-notti__testo-3">{numero}</span>
              <span className="al-c-calendario-notti__testo-4">{numeroL}</span>
            </span>
            <span className="al-c-calendario-notti__testo-5">{conta}</span>
          </span>
        )
      }
    />
  )
}

/** The month arrows and the form, the same for both calendars. */
export interface NavigaMese {
  onPrima?: () => void
  onDopo?: () => void
  primaNo?: boolean
  dopoNo?: boolean
  formato?: Formato
}

/** A legend entry: sign on its ground, then the words. */
export interface VoceLegenda {
  s: string
  l: string
  bg: string
  fg: string
}

/**
 * The month frame both calendars share (v79 `CalendarioNotti`): arrows and title, what goes above
 * the grid, the weekdays with the blanks before day one, the day cells, the legend.
 */
export function CorniceCalendario({
  anno,
  mese,
  titolo,
  sub,
  sopra,
  celle,
  legenda,
  onPrima,
  onDopo,
  primaNo = false,
  dopoNo = false,
  formato = "desktop",
}: {
  anno: number
  mese: number
  titolo?: string | undefined
  sub?: string | undefined
  sopra?: ReactNode
  /** The day cells, from day one. */
  celle: ReactNode[]
  legenda: VoceLegenda[]
  onPrima?: (() => void) | undefined
  onDopo?: (() => void) | undefined
  primaNo?: boolean
  dopoNo?: boolean
  formato?: Formato
}) {
  const { modo, accento } = useTema()
  const L = MISURE[formato]
  const scritto = meseEAnno(`${anno}-${due(mese + 1)}`)
  const vuote = Array.from({ length: colonna(anno, mese, 1) }, (_, i) => (
    <span
      key={`v${i}`}
      className="al-c-calendario-notti__colonna-4"
      aria-hidden="true"
      style={{ ...cellaDi(formato), visibility: "hidden" }}
    />
  ))
  const freccia = (no: boolean, f: (() => void) | undefined, chiave: Chiave, segno: string) => (
    <a
      className="al-c-calendario-notti__tondo-1"
      href="#"
      onClick={gesto(no ? undefined : f)}
      aria-label={t(chiave)}
      aria-disabled={no ? "true" : undefined}
      style={{ width: L.nav, height: L.nav, fontSize: L.navFs, opacity: no ? 0.35 : 1 }}
    >
      {segno}
    </a>
  )
  return (
    <div className="al-c-calendario-notti__blocco-1" data-modo={modo} data-accento={accento}>
      <div className="al-c-calendario-notti__colonna-1" style={{ gap: L.gap }}>
        <div className="al-c-calendario-notti__riga-1">
          {freccia(primaNo, onPrima, "ui.calendar.prev", "\u2039")}
          <span className="al-c-calendario-notti__colonna-2">
            <b className="al-c-calendario-notti__testo-1" style={{ fontSize: L.tfs }}>
              {titolo || scritto.charAt(0).toUpperCase() + scritto.slice(1)}
            </b>
            {sub && <span className="al-c-calendario-notti__testo-2">{sub}</span>}
          </span>
          {freccia(dopoNo, onDopo, "ui.calendar.next", "\u203a")}
        </div>
        {sopra}
        <div className="al-c-calendario-notti__griglia-1" style={{ gap: L.gg }}>
          {SETTIMANA.map((k) => (
            <span
              key={k}
              className="al-c-calendario-notti__testo-6"
              style={{ paddingBottom: L.dpb }}
            >
              {t(k)}
            </span>
          ))}
          {vuote}
          {celle}
        </div>
        <div
          className="al-c-calendario-notti__riga-3"
          style={{ marginTop: L.lmt, padding: L.lpad }}
        >
          {legenda.map((v) => (
            <span key={v.s} className="al-c-calendario-notti__riga-4">
              <i
                className="al-c-calendario-notti__centro-1"
                style={{ background: v.bg, color: v.fg }}
              >
                {v.s}
              </i>
              {v.l}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
