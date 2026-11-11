import { Link } from "react-router"

import { type Chiave, t } from "../i18n"
import { type Esito, Pillola } from "./Pillola"
import type { Formato } from "./Tema"

/** An hour's bar: its height in percent and its outcome; `null` outside the dark or unknown. */
export interface CellaMeteo {
  h: number
  esito: 0 | 1 | 2 | null
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

/**
 * A weather measure over the night (v79 `CardMeteo`): name, number, an hour per bar in the
 * outcome's fixed colours, a note and the pill. Desktop and phone forms; `mancante` is the dashed
 * box of a forecast that did not come.
 */
export function CardMeteo({
  formato = "desktop",
  stato = "normale",
  nome,
  valore = "",
  unita = "",
  celle = [],
  nota = "",
  esito = 0,
  giudizio,
  link,
  impostazioni = "/impostazioni/servizi",
}: {
  formato?: Formato
  stato?: StatoMeteo
  nome: string
  valore?: string
  unita?: string
  celle?: CellaMeteo[]
  nota?: string
  esito?: Esito
  giudizio?: string
  /** Where the arrow opens the measure. */
  link?: string
  /** Where the key states send. */
  impostazioni?: string
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
        testo: t(`ui.weather.${av.k}.pill` as Chiave),
      }
    : { esito, testo: giudizio ?? t("ui.outcome.good") }
  const barre = av
    ? Array.from({ length: 14 }, (_, i) => ({ key: i, height: "100%", background: TRATTEGGIO }))
    : celle.map((c, i) => ({
        key: i,
        height: `${c.h}%`,
        background: c.esito === null ? "var(--barretta-spenta)" : COLORE[c.esito],
      }))
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
  return (
    <div className="al-c-card-meteo__colonna-1">
      <div className="al-c-card-meteo__riga-1">
        <span className="al-c-card-meteo__testo-1">{nome}</span>
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
              <b className="al-c-card-meteo__testo-4">{t(`ui.weather.${av.k}.title` as Chiave)}</b>
              {av.testo && (
                <span className="al-c-card-meteo__testo-5">
                  {t(`ui.weather.${av.k}.text` as Chiave)}
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
          <div className="al-c-card-meteo__riga-3" aria-hidden="true">
            {barre.map((b) => (
              <span key={b.key} className="al-c-card-meteo__riga-4">
                <span
                  className="al-c-card-meteo__pillola-2"
                  style={{ height: b.height, background: b.background }}
                />
              </span>
            ))}
          </div>
          <span className="al-c-card-meteo__colonna-3" style={{ minHeight: "32px" }}>
            <span className="al-c-card-meteo__testo-3">{nota}</span>
          </span>
          <Pillola
            esito={pillola.esito}
            testo={pillola.testo}
            fondo="carta"
            dimensione="media"
            allinea="flex-start"
          />
        </div>
      )}
    </div>
  )
}
