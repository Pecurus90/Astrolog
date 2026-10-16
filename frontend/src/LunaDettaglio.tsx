import { useQuery } from "@tanstack/react-query"
import { useState } from "react"

import { Bottone } from "./Bottone"
import { Disco } from "./Stanotte"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { type Chiave, durata, giornoDelMese, giornoEMese, meseEAnno, numero, oraDelSito, t } from "./i18n"

type Luna = components["schemas"]["MoonOut"]
type Calendario = components["schemas"]["MoonCalendarOut"]
type NotteDellaLuna = Calendario["nights"][number]

function useCalendario(aperto: boolean) {
  return useQuery({
    queryKey: ["moon-calendar"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/moon/calendar")
      if (error) throw new Error(t("dashboard.moon.calendar.failed"))
      return data
    },
    enabled: aperto,
    staleTime: 60 * 60 * 1000,
  })
}

/** La Luna in testa: un bottone che apre il suo dettaglio sotto (tavola v37). */
export function LunaInTesta({ luna, aperto, apri }: { luna: Luna; aperto: boolean; apri: () => void }) {
  const sorge = luna.rise === null ? t("tonight.rise.never") : t("dashboard.moon.rise", { ora: oraDelSito(luna.rise) })
  const tramonta = luna.set === null ? t("tonight.set.never") : t("dashboard.moon.set", { ora: oraDelSito(luna.set) })
  return (
    <div className="as-dashboard__luna">
      <button className="as-luna" type="button" id="dash-luna-apri" aria-expanded={aperto} aria-controls="dash-luna-dettaglio" onClick={apri}>
        <Disco luna={luna} className="as-luna__faccia--testa" />
        <span>
          <b>{`${t(`moon.${luna.phase_key}`)}, ${t("tonight.illuminated", { pct: luna.illumination_pct })}`}</b>
          {`${sorge} \u00b7 ${tramonta}`}
        </span>
        <svg className="as-luna__apri" viewBox="0 0 20 20" aria-hidden="true"><path d="m6 8 4 4 4-4" /></svg>
      </button>
    </div>
  )
}

/**
 * Il **dettaglio della Luna** (`as-pannello--luna`, tavola v37): fase, luce, eta', sorge con la
 * direzione, culmina con l'altezza, tramonta, distanza, prossime nuova e piena; accanto il
 * calendario di questo mese e del prossimo, scritto dal giro in background, con le notti buone
 * per la banda larga dalle due soglie delle Impostazioni.
 */
export function LunaDettaglio({ luna, notte, chiudi }: { luna: Luna; notte: string; chiudi: () => void }) {
  const calendario = useCalendario(true).data
  // "di domani" oltre la fine della notte, il mezzogiorno dopo: le 07:30 sono ancora stanotte
  const dopo = (iso: string) => iso.slice(0, 10) > notte && iso.slice(11, 13) >= "12"
  const quando = (iso: string) => (dopo(iso) ? t("dashboard.moon.tomorrow", { ora: oraDelSito(iso) }) : oraDelSito(iso))
  const righe: [Chiave, string][] = [
    ["dashboard.moon.lit", t("dashboard.moon.lit.value", { pct: numero(luna.illumination_pct) })],
    ["dashboard.moon.age", t("dashboard.moon.age.value", { n: numero(luna.age_days) })],
    ["tonight.rise", luna.rise === null ? t("tonight.rise.never") : luna.rise_compass
      ? `${quando(luna.rise)} \u00b7 ${t("dashboard.moon.from", { dove: t(`moon.compass.${luna.rise_compass}` as Chiave) })}`
      : quando(luna.rise)],
    ["dashboard.moon.culminates", `${quando(luna.highest.at)} \u00b7 ${numero(Math.round(luna.highest.altitude_deg))}\u00b0`],
    ["tonight.set", luna.set === null ? t("tonight.set.never") : quando(luna.set)],
    ["dashboard.moon.distance", t("dashboard.moon.distance.value", { km: numero(luna.distance_km) })],
    ["moon.new", luna.next_new ? giornoEMese(luna.next_new) : "\u2014"],
    ["moon.full", luna.next_full ? giornoEMese(luna.next_full) : "\u2014"],
  ]
  return (
    <div className="as-pannello as-pannello--luna" id="dash-luna-dettaglio" role="dialog" aria-label={t("dashboard.moon.panel")}
      onKeyDown={(ev) => { if (ev.key === "Escape") chiudi() }}>
      <div className="as-pannello__testa">
        <Disco luna={luna} className="as-luna__faccia--pannello" />
        <div>
          <p className="as-soprattitolo">{t("dashboard.moon.kicker")}</p>
          <p className="as-pannello__titolo">{t(`moon.${luna.phase_key}`)}</p>
        </div>
        <Bottone verso="nudo" piccolo onClick={chiudi}>{t("frame.close.word")}</Bottone>
      </div>
      <dl className="as-pannello__dettagli">
        {righe.map(([nome, valore]) => <div key={nome}><dt>{t(nome)}</dt><dd>{valore}</dd></div>)}
      </dl>
      {calendario && calendario.nights.length > 0 && <CalendarioDellaLuna calendario={calendario} />}
    </div>
  )
}

/** Due mesi, uno alla volta con le frecce; ogni giorno col disco, la luce e le ore senza Luna. */
function CalendarioDellaLuna({ calendario: c }: { calendario: Calendario }) {
  const mesi = [...new Set(c.nights.map((n) => n.date.slice(0, 7)))]
  const [quale, setQuale] = useState(0)
  const mese = mesi[quale] ?? mesi[0] ?? ""
  const notti = c.nights.filter((n) => n.date.startsWith(mese))
  const [anno, numeroDelMese] = mese.split("-").map(Number)
  // la griglia comincia di lunedi': i giorni vuoti prima del primo
  const prima = (new Date(Date.UTC(anno ?? 2000, (numeroDelMese ?? 1) - 1, 1)).getUTCDay() + 6) % 7
  const nome = meseEAnno(mese)
  return (
    <div className="as-calendario">
      <div className="as-calendario__mese">
        <div className="as-calendario__capo">
          <button className="as-calendario__vai" type="button" aria-label={t("dashboard.moon.prev")} disabled={quale === 0}
            onClick={() => setQuale(quale - 1)}>{"\u2039"}</button>
          <p>{nome}</p>
          <button className="as-calendario__vai" type="button" aria-label={t("dashboard.moon.next")} disabled={quale >= mesi.length - 1}
            onClick={() => setQuale(quale + 1)}>{"\u203a"}</button>
        </div>
        <div className="as-calendario__giorni">
          {t("dashboard.moon.weekdays").split(",").map((g) => <span key={g} className="as-calendario__settimana">{g}</span>)}
          {Array.from({ length: prima }, (_, i) => <span key={`v${i}`} />)}
          {notti.map((n) => <Giorno key={n.date} notte={n} oggi={n.date === c.today} />)}
        </div>
      </div>
      <p className="as-calendario__legenda">
        <span className="as-calendario__campione" />
        {t("dashboard.moon.legend", { pct: numero(c.max_pct), ore: numero(c.min_dark_h) })}
      </p>
    </div>
  )
}

function Giorno({ notte: n, oggi }: { notte: NotteDellaLuna; oggi: boolean }) {
  return (
    <span className={["as-calendario__giorno", n.good ? "as-calendario__giorno--buio" : "", oggi ? "as-calendario__giorno--oggi" : ""]
      .filter(Boolean).join(" ")}
      title={t("dashboard.moon.day", { giorno: giornoDelMese(n.date), pct: numero(n.illumination_pct), durata: durata(n.moonless_dark_s) ?? "" })}>
      <b>{numero(Number(n.date.slice(8, 10)))}</b>
      <Disco luna={n} className="as-luna__faccia--giorno" />
      {n.event && <i>{t(`dashboard.moon.event.${n.event}`)}</i>}
    </span>
  )
}
