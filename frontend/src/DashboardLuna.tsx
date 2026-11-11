import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { Link } from "react-router"

import { api } from "./api/client"
import type { components } from "./api/schema"
import { Avviso } from "./componenti/Avviso"
import { CalendarioLuna, type GiornoLuna } from "./componenti/CalendarioLuna"
import { Carta } from "./componenti/Carta"
import { gesto } from "./componenti/gesto"
import { Luna } from "./componenti/Luna"
import { PillolaScelta } from "./componenti/PillolaScelta"
import { Ripresa } from "./componenti/Ripresa"
import type { Formato } from "./componenti/Tema"
import { ESITO, type Meteo, type Stanotte, latiDellaRipresa } from "./DashboardDati"
import { quandoDellEvento, quandoDellaLuna } from "./DashboardNotte"
import {
  type Chiave,
  giornoDelMese,
  giornoEMese,
  giornoENumero,
  maiuscola,
  numero,
  oraDelSito,
  oreEMinuti,
  t,
} from "./i18n"

type Calendario = components["schemas"]["MoonCalendarOut"]
type GiornoDetto = Calendario["nights"][number]

/** This month and the next as the background round wrote them; empty until it has run. */
function useCalendario() {
  return useQuery({
    queryKey: ["moon-calendar"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/moon/calendar")
      if (error) throw new Error(t("dashboard.moon.calendar.failed"))
      return data
    },
    staleTime: 60 * 60 * 1000,
    // the round passes every minute: reread until it writes
    refetchInterval: (q) => (q.state.data?.nights.length === 0 ? 15_000 : false),
  })
}

/** The Moon scale's two bounds from the forecast's scales (Meteo, ING 25/65). */
function soglieDellaLuna(meteo: Meteo | undefined): { buona: string; limite: string } | null {
  const passi = meteo?.scales.find((s) => s.code === "moon")?.steps ?? []
  const buona = passi.find((p) => p.level === "marginal")?.bound
  const limite = passi.find((p) => p.level === "nogo")?.bound
  return buona == null || limite == null ? null : { buona: numero(buona), limite: numero(limite) }
}

/** "Casa: M 31, M 33, 180 frame", for each night shot that day. */
function cosaRipreso(g: GiornoDetto): string {
  return g.shots
    .map(
      (s) =>
        `${s.site}: ${[...s.objects, t("dashboard.moon.shot.frames", { n: numero(s.frames) })].join(" \u00b7 ")}`,
    )
    .join(" \u00b7 ")
}

export function DashboardLuna({
  stanotte: s,
  meteo,
  formato,
}: {
  stanotte: Stanotte
  meteo: Meteo | undefined
  formato: Formato
}) {
  const tel = formato === "telefono"
  const calendario = useCalendario()
  const [dettaglio, setDettaglio] = useState(false)
  const [mese, setMese] = useState<string | null>(null)
  const [scelto, setScelto] = useState<string | null>(null)
  const luna = s.moon
  const soglie = soglieDellaLuna(meteo)
  const notti = calendario.data?.nights ?? []
  const mesi = [...new Set(notti.map((n) => n.date.slice(0, 7)))]
  const visto = mese && mesi.includes(mese) ? mese : (mesi[0] ?? null)
  const iMese = visto ? mesi.indexOf(visto) : -1
  const delMese = notti.filter((n) => visto && n.date.startsWith(visto))
  const oggi = calendario.data?.today ?? null
  const evento = (k: "new" | "full") => delMese.find((n) => n.event === k)
  const giorni: GiornoLuna[] = delMese.map((n) => {
    const ore = t("dashboard.moon.hours", { n: numero(Math.round(n.moonless_dark_s / 3600)) })
    return {
      d: Number(n.date.slice(8, 10)),
      g: ESITO[n.level],
      ore,
      ...(n.event ? { evento: n.event === "new" ? ("nuova" as const) : ("piena" as const) } : {}),
      stella: n.shots.length > 0,
      sel: scelto === n.date,
      ...(n.shots.length ? { on: () => setScelto(scelto === n.date ? null : n.date) } : {}),
      aria:
        t("dashboard.moon.day.aria", {
          giorno: giornoEMese(n.date),
          gradino: t(`dashboard.moon.step.${n.level}` as Chiave),
          ore,
        }) + (n.shots.length ? t("dashboard.moon.day.shot") : ""),
    }
  })
  const sel = delMese.find((n) => n.date === scelto && n.shots.length)
  // as the board: the day's first night gives the hours, the others go in words
  const selOre = sel?.shots[0]?.integration_s ?? 0
  const nuova = evento("new")
  const piena = evento("full")
  const lati = latiDellaRipresa(s)
  const pillole = luna
    ? [
        t("dashboard.moon.pill.highest", {
          gradi: numero(Math.round((luna.highest_in_chart ?? luna.highest).altitude_deg)),
          ora: oraDelSito((luna.highest_in_chart ?? luna.highest).at),
        }),
        t("dashboard.moon.pill.distance", { km: numero(luna.distance_km) }),
        t(luna.age_days === 1 ? "dashboard.moon.pill.age.one" : "dashboard.moon.pill.age", {
          n: numero(luna.age_days),
        }),
        ...(luna.rise_compass
          ? [t("dashboard.moon.pill.rises", { dove: t(`moon.compass.${luna.rise_compass}`) })]
          : []),
      ]
    : []
  const apri = (
    <a
      className="al-dash__tondo-3"
      href="#"
      onClick={gesto(() => setDettaglio(!dettaglio))}
      aria-expanded={dettaglio}
      aria-label={t("dashboard.moon.detail.open")}
    >
      {"\u2197"}
    </a>
  )
  const det = dettaglio && luna && (
    <div className="al-dash__colonna-8" role="region" aria-label={t("dashboard.moon.detail")}>
      <span className="al-dash__riga-13">
        <b className="al-dash__testo-14">{t("dashboard.moon.detail")}</b>
        <a
          className="al-dash__tondo-4"
          href="#"
          onClick={gesto(() => setDettaglio(false))}
          aria-label={t("dashboard.moon.detail.close")}
          style={{ width: tel ? "44px" : "28px", height: tel ? "44px" : "28px" }}
        >
          {"\u00d7"}
        </a>
      </span>
      <div className="al-dash__griglia-4">
        {[
          {
            l: t("dashboard.moon.age"),
            v: t(
              luna.age_days === 1 ? "dashboard.moon.age.value.one" : "dashboard.moon.age.value",
              { n: numero(luna.age_days) },
            ),
            s: luna.next_full
              ? t("dashboard.moon.fullDate", { giorno: giornoDelMese(luna.next_full) })
              : "",
          },
          {
            l: t("dashboard.moon.distance"),
            v: t("dashboard.moon.distance.value", { km: numero(luna.distance_km) }),
            s: "",
          },
          {
            l: t("dashboard.moon.rises"),
            v: luna.rise_compass
              ? t(`moon.compass.${luna.rise_compass}`)
              : t("dashboard.moon.noRise"),
            s: luna.rise ? quandoDellEvento(s, "at", luna.rise) : "",
          },
        ].map((v) => (
          <span key={v.l} className="al-dash__colonna-1">
            <span className="al-dash__testo-13">{v.l}</span>
            <b className="al-dash__testo-15">{v.v}</b>
            <span className="al-dash__testo-13">{v.s}</span>
          </span>
        ))}
      </div>
      {soglie && (
        <span className="al-dash__testo-16">{t("dashboard.moon.detail.legend", soglie)}</span>
      )}
    </div>
  )
  const cal = calendario.isError ? (
    <Avviso tipo="riga" formato={formato} segno="!" titolo={t("dashboard.moon.calendar.failed")} />
  ) : calendario.data && !notti.length ? (
    <Avviso tipo="riga" formato={formato} segno="?" titolo={t("dashboard.moon.calendar.none")} />
  ) : (
    visto && (
      <CalendarioLuna
        anno={Number(visto.slice(0, 4))}
        mese={Number(visto.slice(5, 7)) - 1}
        giorni={giorni}
        {...(oggi?.startsWith(visto) ? { oggi: Number(oggi.slice(8, 10)) } : {})}
        buona={soglie?.buona ?? ""}
        limite={soglie?.limite ?? ""}
        nuova={nuova ? t("dashboard.moon.newOn", { giorno: giornoENumero(nuova.date) }) : ""}
        piena={piena ? t("dashboard.moon.fullOn", { giorno: giornoENumero(piena.date) }) : ""}
        onPrima={() => {
          setMese(mesi[iMese - 1] ?? null)
          setScelto(null)
        }}
        onDopo={() => {
          setMese(mesi[iMese + 1] ?? null)
          setScelto(null)
        }}
        primaNo={iMese <= 0}
        dopoNo={iMese >= mesi.length - 1}
        formato={formato}
      />
    )
  )
  const notte = sel && (
    <div
      className={tel ? "al-dash__colonna-23" : "al-dash__griglia-5"}
      style={{
        display: "grid",
        gridTemplateColumns: "minmax(0,1fr) auto auto",
        alignItems: "center",
        gap: "4px 8px",
      }}
    >
      <b className="al-dash__testo-7">
        {t("dashboard.moon.shot.title", {
          giorno: maiuscola(giornoEMese(sel.date)),
          ore: selOre > 0 ? oreEMinuti(selOre) : t("dashboard.moon.shot.untimed"),
        })}
      </b>
      <Link
        className="al-dash__tondo-3"
        to={`/notti?notte=${sel.shots[0]?.night_id ?? ""}`}
        aria-label={t("dashboard.moon.shot.open")}
        title={t("nav.nights")}
      >
        {"\u2197"}
      </Link>
      <a
        className="al-dash__tondo-5"
        href="#"
        onClick={gesto(() => setScelto(null))}
        aria-label={t("ui.close")}
      >
        {"\u00d7"}
      </a>
      <span className="al-dash__testo-2" style={{ gridColumn: "1 / -1" }}>
        {cosaRipreso(sel)}
      </span>
    </div>
  )
  const scelta = (
    <PillolaScelta
      forma="segmentato"
      classe="al-scelta--sottili"
      misura="piccola"
      opzioni={[{ l: t("dashboard.moon.choice.moon"), sel: true }]}
      etichetta={t("dashboard.moon.choice")}
      formato={formato}
    />
  )
  const disco = luna && (
    <Luna
      percento={luna.illumination_pct}
      lato={luna.lit_side === "right" ? "destra" : "sinistra"}
      misura={tel ? 60 : 76}
      piena
    />
  )
  const pct = luna ? t("dashboard.moon.pct", { pct: numero(luna.illumination_pct) }) : ""
  const tessere = (
    <div className={tel ? "al-dash__griglia-17" : "al-dash__griglia-3"}>
      {lati.map((r) => (
        <span key={r.tipo} className={tel ? "al-dash__colonna-21" : "al-dash__colonna-7"}>
          <Ripresa tipo={r.tipo} testo={r.nome} formato={formato} />
          <b className={tel ? "al-dash__testo-34" : "al-dash__testo-12"}>{r.v}</b>
          <span className={tel ? "al-dash__testo-17" : "al-dash__testo-13"}>{r.sotto}</span>
        </span>
      ))}
    </div>
  )
  const senzaLuna = !luna && (
    <Avviso tipo="riga" formato={formato} segno="?" titolo={t("dashboard.moon.noZone")} />
  )
  // between the head and the calendar, the same on both forms
  const mezzo = (
    <>
      {senzaLuna}
      <div className="al-dash__riga-12">
        {pillole.map((p) => (
          <span key={p} className="al-dash__pillola-3">
            {p}
          </span>
        ))}
      </div>
      {s.shooting?.length ? tessere : null}
      {det}
    </>
  )
  if (tel) {
    return (
      <Carta
        formato="telefono"
        etichetta={t("dashboard.moon.card")}
        ritardo={60}
        padding="20px"
        gap="14"
      >
        <span className="al-dash__riga-34">{scelta}</span>
        <div className="al-dash__centro-2">
          <div className="al-dash__colonna-19">
            {luna && (
              <div className="al-dash__riga-35">
                <span className="al-dash__blocco-12">{disco}</span>
                <div className="al-dash__colonna-20">
                  <span className="al-dash__testo-29">{t(`moon.${luna.phase_key}`)}</span>
                  <span className="al-dash__testo-19">{quandoDellaLuna(s)}</span>
                </div>
                <span
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "flex-end",
                    gap: 4,
                  }}
                >
                  {apri}
                  <span className="al-dash__testo-33">{pct}</span>
                </span>
              </div>
            )}
            {mezzo}
            <div className="al-dash__colonna-22">
              {cal}
              {notte}
            </div>
          </div>
        </div>
      </Carta>
    )
  }
  return (
    <Carta colonne={5} ritardo={60}>
      <div className="al-dash__riga-10">{scelta}</div>
      <div className="al-dash__centro-1">
        <div className="al-dash__colonna-4">
          {luna && (
            <div className="al-dash__riga-11">
              <span className="al-dash__blocco-4">{disco}</span>
              <div className="al-dash__colonna-5">
                <span className="al-dash__testo-9">{t("dashboard.moon.tonight")}</span>
                <span className="al-dash__testo-10">{t(`moon.${luna.phase_key}`)}</span>
                <span className="al-dash__testo-9">{quandoDellaLuna(s)}</span>
              </div>
              <div className="al-dash__colonna-6">
                {apri}
                <span className="al-dash__testo-11">{pct}</span>
              </div>
            </div>
          )}
          {mezzo}
          {cal}
          {notte}
        </div>
      </div>
    </Carta>
  )
}
