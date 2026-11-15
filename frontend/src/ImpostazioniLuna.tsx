import { useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

import { Carta } from "./componenti/Carta"
import { useFormato } from "./componenti/formato"
import { gesto } from "./componenti/gesto"
import { Tema, type Formato } from "./componenti/Tema"
import { useScriviImpostazioni } from "./ImpostazioniGenerale"
import { anello } from "./ImpostazioniSiti"
import { type Chiave, numero, t } from "./i18n"
import { usePreferenze } from "./preferenze"

type Valori = { buona: number; limite: number; sopra: number }

/** The altitude as the board writes it: the horizon in words, the others in degrees. */
function altezza(a: number): string {
  return a === 0
    ? t("settings.moon.horizon")
    : t("settings.moon.deg", { n: numero(a).replace("-", "\u2212") })
}

// Where each altitude comes from (tavola `lunaR`); the registry holds the same sources.
const FONTI: Record<number, Chiave> = {
  [-5]: "settings.moon.above.tess",
  0: "settings.moon.above.horizon",
}

/**
 * **Luna** (tavola Impostazioni v82, 183-189 and 392-398): the Moon's rule for broadband, read by
 * every page (ADR 0034). The backend rewrites calendar, forecast and nights on a change; the
 * second percentage cannot sit under the first, so a wrong number is not sent.
 */
export function Luna() {
  const formato = useFormato()
  const preferenze = usePreferenze().data
  if (!preferenze) return null
  const v = preferenze.values
  const salvati: Valori = {
    buona: Number(v.moon_good_pct),
    limite: Number(v.moon_limit_pct),
    sopra: Number(v.moon_above_deg),
  }
  // the ranges come from the backend (`config.RANGES`), the altitudes too (`CHOICES`)
  const misure = {
    buona: preferenze.ranges.moon_good_pct ?? { min: 0, max: 100 },
    limite: preferenze.ranges.moon_limit_pct ?? { min: 0, max: 100 },
  }
  const scelte = (preferenze.choices.moon_above_deg ?? []).map(Number)
  return (
    <Tema>
      <div className={formato === "telefono" ? "al-imp__colonna-18" : "al-imp__griglia-2"}>
        <CartaLuna formato={formato} salvati={salvati} misure={misure} scelte={scelte} />
      </div>
    </Tema>
  )
}

type Misura = { min: number; max: number }

function CartaLuna({
  formato,
  salvati,
  misure,
  scelte,
}: {
  formato: Formato
  salvati: Valori
  misure: { buona: Misura; limite: Misura }
  scelte: readonly number[]
}) {
  const tel = formato === "telefono"
  const cache = useQueryClient()
  const scrivi = useScriviImpostazioni(() => {
    for (const k of ["moon-calendar", "weather", "tonight", "nights", "year"]) {
      void cache.invalidateQueries({ queryKey: [k] })
    }
  })
  const [buona, setBuona] = useState(String(salvati.buona))
  const [limite, setLimite] = useState(String(salvati.limite))
  const intero = (s: string) => (/^\d+$/.test(s) ? Number(s) : NaN)
  const nb = intero(buona)
  const nl = intero(limite)
  const dentro = (n: number, m: Misura) => n >= m.min && n <= m.max
  const fuori = (m: Misura) => t("settings.moon.range", { min: numero(m.min), max: numero(m.max) })
  const okB = dentro(nb, misure.buona)
  const inL = dentro(nl, misure.limite)
  const okL = inL && (!okB || nl >= nb)
  const errB = okB ? "" : fuori(misure.buona)
  const errL = !inL ? fuori(misure.limite) : okL ? "" : t("settings.moon.atLeast", { n: numero(nb) })
  const salva = () => {
    if (okB && okL && (nb !== salvati.buona || nl !== salvati.limite)) {
      scrivi.mutate({ moon_good_pct: nb, moon_limit_pct: nl })
    }
  }
  const righe = [
    {
      k: "buona",
      l: t("settings.moon.good"),
      v: buona,
      set: setBuona,
      ph: String(salvati.buona),
      err: errB,
      s: t("settings.moon.good.source"),
    },
    {
      k: "limite",
      l: t("settings.moon.limit"),
      v: limite,
      set: setLimite,
      ph: String(salvati.limite),
      err: errL,
      s: t("settings.moon.limit.source"),
    },
  ]
  const pillole = (
    <span className="al-imp__riga-17" role="radiogroup" aria-label={t("settings.moon.above")}>
      {scelte.map((a) => (
        <a
          key={a}
          className={tel ? "al-imp__riga-40" : "al-imp__riga-18"}
          href="#"
          role="radio"
          aria-checked={salvati.sopra === a ? "true" : "false"}
          onClick={gesto(() => {
            if (a !== salvati.sopra) scrivi.mutate({ moon_above_deg: a })
          })}
          style={anello(salvati.sopra === a, 1.5)}
        >
          {altezza(a)}
        </a>
      ))}
    </span>
  )
  const fonteSopra = t(FONTI[salvati.sopra] ?? "settings.moon.above.none")
  return (
    <Carta
      formato={formato}
      colonne={12}
      ritardo={0}
      padding={tel ? "20px" : "24px 28px"}
      gap={0}
      etichetta={t("settings.moon")}
    >
      {tel ? (
        <span className="al-imp__testo-28">{t("settings.moon")}</span>
      ) : (
        <span className="al-imp__riga-9">
          <span className="al-imp__testo-3">{t("settings.moon")}</span>
          <span className="al-imp__testo-5">{t("settings.moon.sub")}</span>
        </span>
      )}
      {righe.map((r) => {
        const campo = (
          <span className="al-imp__riga-12">
            <input
              type="text"
              inputMode="numeric"
              value={r.v}
              onChange={(e) => r.set(e.target.value.replace(/[^0-9]/g, "").slice(0, 3))}
              onBlur={salva}
              onKeyDown={(e) => {
                if (e.key === "Enter") salva()
              }}
              placeholder={r.ph}
              aria-label={t("settings.moon.aria", { riga: r.l })}
              aria-invalid={r.err ? "true" : "false"}
              className={
                tel
                  ? "al-campo al-campo--numero al-imp__blocco-19"
                  : "al-campo al-campo--numero al-campo--piccolo al-imp__blocco-19"
              }
            />
            <span className="al-imp__testo-2">{"%"}</span>
          </span>
        )
        const errore = r.err && (
          <span className="al-imp__testo-20" aria-live="polite">
            {`✕ ${r.err}` /* glifo-ok: segno della tavola */}
          </span>
        )
        return tel ? (
          <div key={r.k} className="al-imp__colonna-26">
            <span className="al-imp__testo-5">{r.l}</span>
            {campo}
            {errore}
            <span className="al-imp__testo-8">{r.s}</span>
          </div>
        ) : (
          <div key={r.k} className="al-imp__griglia-8">
            <span className="al-imp__testo-2">{r.l}</span>
            <span className="al-imp__colonna-13">
              {campo}
              {errore}
            </span>
            <span className="al-imp__testo-5">{r.s}</span>
          </div>
        )
      })}
      {tel ? (
        <div className="al-imp__colonna-26">
          <span className="al-imp__testo-5">{t("settings.moon.above")}</span>
          {pillole}
          <span className="al-imp__testo-8">{fonteSopra}</span>
        </div>
      ) : (
        <div className="al-imp__griglia-8">
          <span className="al-imp__testo-2">{t("settings.moon.above")}</span>
          <span className="al-imp__colonna-13">{pillole}</span>
          <span className="al-imp__testo-5">{fonteSopra}</span>
        </div>
      )}
      {tel ? (
        <span className="al-imp__blocco-31">{t("settings.moon.dark")}</span>
      ) : (
        <span className="al-imp__riga-20">
          <span>{t("settings.moon.dark")}</span>
          <span className="al-imp__testo-21">
            {t("settings.moon.now", {
              buona: numero(salvati.buona),
              limite: numero(salvati.limite),
              sopra: altezza(salvati.sopra),
            })}
          </span>
        </span>
      )}
    </Carta>
  )
}
