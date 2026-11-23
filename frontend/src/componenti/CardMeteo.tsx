import type { KeyboardEvent, MouseEvent } from "react"
import { Link } from "react-router"

import { type Chiave, t } from "../i18n"
import { type Esito, Pillola } from "./Pillola"
import type { Formato } from "./Tema"

/** An hour's bar: its height in percent and its outcome; `null` outside the dark or unknown. The
 *  Weather's cards also dim it (`op`), point it (`on`) and fix the card to it (`click`). */
export interface CellaMeteo {
  h: number
  esito: 0 | 1 | 2 | null
  /** Unknown hour: hatched. */
  manca?: boolean
  op?: number
  title?: string
  on?: () => void
  click?: () => void
}

/** Where the measure is not there, and why (v79 `CardMeteo`, `stato`). */
export type StatoMeteo =
  | "normale"
  | "mancante"
  | "non si misura"
  | "chiave"
  | "chiave non valida"
  | "non disponibile"
  | "in arrivo"

const COLORE = {
  0: "var(--buono-testo)",
  1: "var(--incerto-testo)",
  2: "var(--non-adatto-testo)",
} as const
const TRATTEGGIO =
  "repeating-linear-gradient(135deg, var(--barretta-spenta) 0 3px, transparent 3px 8px)"

const AVVISI = {
  "non si misura": { segno: "?", testo: true, azione: false },
  chiave: { segno: "?", testo: false, azione: true },
  "chiave non valida": { segno: "!", testo: false, azione: true },
  "non disponibile": { segno: "?", testo: true, azione: false },
  "in arrivo": { segno: "?", testo: true, azione: false },
} as const

const chiaveDi = (stato: keyof typeof AVVISI): string => stato.replaceAll(" ", "-")

/** The words of a missing state the page writes itself (the Weather's jet estimate). */
export type ParoleDellAvviso = { titolo?: string; testo?: string; pillola?: string }

const ferma = (e: MouseEvent) => {
  e.preventDefault()
  e.stopPropagation()
}

/**
 * A weather measure over the night (v82 `CardMeteo`): name, number, an hour per bar in the
 * outcome's fixed colours, a note, the peak and the pill. Desktop, phone and the phone's compact
 * tile that opens; `mancante` is the dashed box of a forecast that did not come. The Weather adds
 * the ring and tag of a measure on the chart, the bars that fix the card to an hour and its \u00d7.
 */
export function CardMeteo({
  formato = "desktop",
  compatta = false,
  stato = "normale",
  nome,
  valore = "",
  unita = "",
  celle = [],
  nota = "",
  picco,
  esito = 0,
  giudizio,
  link,
  impostazioni = "/impostazioni/servizi",
  parole,
  anello,
  etichetta,
  aggiornamento,
  onAggiorna,
  onClick,
  onTorna,
  onTasto,
  onLeave,
  aperto = false,
}: {
  formato?: Formato
  /** Phone only: the small tile that opens its detail below. */
  compatta?: boolean
  stato?: StatoMeteo
  nome: string
  valore?: string
  unita?: string
  celle?: CellaMeteo[]
  nota?: string
  picco?: string | undefined
  esito?: Esito
  giudizio?: string
  /** Where the arrow opens the measure. */
  link?: string
  /** Where the key states send. */
  impostazioni?: string
  parole?: ParoleDellAvviso | undefined
  /** The colour of the measure on the chart. */
  anello?: string | undefined
  /** "sul grafico". */
  etichetta?: string | undefined
  /** The seeing kept from before, and why. */
  aggiornamento?: string | undefined
  onAggiorna?: () => void
  onClick?: () => void
  /** Back to the night: the card was fixed to an hour. */
  onTorna?: () => void
  onTasto?: (e: KeyboardEvent<HTMLDivElement>) => void
  onLeave?: () => void
  aperto?: boolean
}) {
  const tel = formato === "telefono"
  if (stato === "mancante") {
    return (
      <div
        className="al-c-card-meteo__colonna-8"
        style={{
          borderRadius: tel ? "20px" : "22px",
          padding: tel ? "12px 14px" : "16px 18px",
          gap: tel ? "4px" : "6px",
        }}
      >
        <span className="al-c-card-meteo__testo-3" style={{ fontSize: tel ? "13px" : "14px" }}>
          {nome}
        </span>
        <span style={{ fontSize: tel ? "12px" : "13px" }}>{t("ui.weather.missing")}</span>
      </div>
    )
  }
  const av = stato === "normale" ? null : { ...AVVISI[stato], k: chiaveDi(stato) }
  const pillola = av
    ? {
        esito: (av.segno === "!" ? 2 : "mancante") as Esito,
        testo: parole?.pillola ?? t(`ui.weather.${av.k}.pill` as Chiave),
      }
    : { esito, testo: giudizio ?? t("ui.outcome.good") }
  const barre = av
    ? Array.from({ length: 14 }, (_, i) => ({
        key: i,
        height: "100%",
        background: TRATTEGGIO,
        op: 1,
        c: undefined as CellaMeteo | undefined,
      }))
    : celle.map((c, i) => ({
        key: i,
        height: `${c.h}%`,
        background: c.manca
          ? TRATTEGGIO
          : c.esito === null
            ? "var(--barretta-spenta)"
            : COLORE[c.esito],
        op: c.op ?? 1,
        c,
      }))
  const bordo = anello ? { boxShadow: `inset 0 0 0 2px ${anello}` } : {}
  if (tel && compatta) {
    return (
      <a
        className="al-c-card-meteo__colonna-7"
        href="#"
        role="button"
        aria-expanded={aperto}
        onClick={(e) => {
          e.preventDefault()
          onClick?.()
        }}
        style={bordo}
      >
        <span className="al-c-card-meteo__riga-8">
          <span>{nome}</span>
          <span aria-hidden="true">{aperto ? "\u25b4" : "\u25be"}</span>
        </span>
        <span className="al-c-card-meteo__riga-9">
          <span className="al-c-card-meteo__testo-9">{av ? "?" : valore}</span>
          {!av && <span className="al-c-card-meteo__testo-10">{unita}</span>}
        </span>
        <span className="al-c-card-meteo__riga-10" aria-hidden="true">
          {barre.map((b) => (
            <span
              key={b.key}
              className="al-c-card-meteo__pillola-3"
              style={{ height: b.height, background: b.background, opacity: b.op }}
            />
          ))}
        </span>
        <Pillola
          esito={pillola.esito}
          testo={pillola.testo}
          fondo="carta"
          dimensione="micro"
          allinea="flex-start"
        />
      </a>
    )
  }
  if (tel) {
    return (
      <div className="al-c-card-meteo__colonna-6">
        <span className="al-c-card-meteo__testo-6">{nome}</span>
        <span className="al-c-card-meteo__riga-2">
          <span className="al-c-card-meteo__testo-7">{av ? "?" : valore}</span>
          {!av && <span className="al-c-card-meteo__testo-8">{unita}</span>}
        </span>
        <div className="al-c-card-meteo__riga-7" aria-hidden="true">
          {barre.map((b) => (
            <span
              key={b.key}
              className="al-c-card-meteo__pillola-3"
              style={{ height: b.height, background: b.background }}
            />
          ))}
        </div>
        <Pillola
          esito={pillola.esito}
          testo={pillola.testo}
          fondo="carta"
          dimensione="minima"
          allinea="flex-start"
        />
      </div>
    )
  }
  const segnaOre = celle.some((c) => c.on || c.click)
  return (
    <div
      className="al-c-card-meteo__colonna-1"
      onClick={onClick}
      style={{ ...bordo, cursor: onClick ? "pointer" : "default" }}
    >
      <div className="al-c-card-meteo__riga-1">
        <span className="al-c-card-meteo__testo-1">{nome}</span>
        {etichetta && <span className="al-c-card-meteo__pillola-1">{etichetta}</span>}
        {onTorna && (
          <a
            className="al-c-card-meteo__tondo-1"
            href="#"
            onClick={(e) => {
              ferma(e)
              onTorna()
            }}
            aria-label={t("ui.weather.back")}
            title={t("ui.weather.back")}
          >
            {"\u00d7"}
          </a>
        )}
        {link && (
          <Link
            className="al-c-card-meteo__tondo-2"
            to={link}
            aria-label={t("ui.weather.open", { nome })}
          >
            {"\u2197"}
          </Link>
        )}
      </div>
      {av ? (
        <div className="al-c-card-meteo__colonna-4">
          <span className="al-c-card-meteo__riga-6">
            <span
              className="al-c-card-meteo__tondo-4"
              aria-hidden="true"
              style={{
                background: av.segno === "!" ? "var(--avviso)" : "var(--carta)",
                color: av.segno === "!" ? "var(--avviso-testo)" : "var(--testo)",
              }}
            >
              {av.segno}
            </span>
            <span className="al-c-card-meteo__colonna-5">
              <b className="al-c-card-meteo__testo-4">
                {parole?.titolo ?? t(`ui.weather.${av.k}.title` as Chiave)}
              </b>
              {(parole?.testo ?? (av.testo ? t(`ui.weather.${av.k}.text` as Chiave) : "")) && (
                <span className="al-c-card-meteo__testo-5">
                  {parole?.testo ?? t(`ui.weather.${av.k}.text` as Chiave)}
                </span>
              )}
            </span>
          </span>
          {av.azione && (
            <Link
              className="al-bottone al-bottone--testo al-bottone--piccolo al-c-card-meteo__blocco-4"
              to={impostazioni}
            >
              {t("ui.weather.settings")}
            </Link>
          )}
        </div>
      ) : (
        <div className="al-c-card-meteo__colonna-2">
          <span className="al-c-card-meteo__riga-2">
            <span className="al-c-card-meteo__testo-2">{valore}</span>
            <span className="al-c-card-meteo__testo-3">{unita}</span>
          </span>
          <div
            className="al-c-card-meteo__riga-3"
            aria-hidden={segnaOre ? undefined : "true"}
            aria-label={segnaOre ? t("ui.weather.bars", { nome }) : undefined}
            role={segnaOre ? "group" : undefined}
            tabIndex={onTasto ? 0 : undefined}
            onKeyDown={onTasto}
            onMouseLeave={onLeave}
            style={{ cursor: segnaOre ? "crosshair" : undefined }}
          >
            {barre.map((b) => (
              <span
                key={b.key}
                className="al-c-card-meteo__riga-4"
                title={b.c?.title}
                onMouseEnter={b.c?.on}
                onClick={
                  b.c?.click
                    ? (e) => {
                        ferma(e)
                        b.c?.click?.()
                      }
                    : undefined
                }
              >
                <span
                  className="al-c-card-meteo__pillola-2"
                  style={{ height: b.height, background: b.background, opacity: b.op }}
                />
              </span>
            ))}
          </div>
          <span
            className="al-c-card-meteo__colonna-3"
            style={{ minHeight: picco !== undefined ? "34px" : "32px" }}
          >
            <span className="al-c-card-meteo__testo-3">{nota}</span>
            {picco !== undefined && picco !== "" && <span>{picco}</span>}
          </span>
          <Pillola
            esito={pillola.esito}
            testo={pillola.testo}
            fondo="carta"
            dimensione="media"
            allinea="flex-start"
          />
          {aggiornamento && (
            <span className="al-c-card-meteo__riga-5">
              <span className="al-c-card-meteo__tondo-3" aria-hidden="true">
                !
              </span>
              <span className="al-c-card-meteo__blocco-3">{aggiornamento}</span>
              {onAggiorna && (
                <a
                  href="#"
                  className="al-bottone al-bottone--testo"
                  onClick={(e) => {
                    ferma(e)
                    onAggiorna()
                  }}
                >
                  {t("weather.refresh")}
                </a>
              )}
            </span>
          )}
        </div>
      )}
    </div>
  )
}
