import { useState } from "react"
import { Link } from "react-router"

import { Avviso, type SegnoAvviso } from "./componenti/Avviso"
import { CardMeteo, type CellaMeteo, type StatoMeteo } from "./componenti/CardMeteo"
import { Carta } from "./componenti/Carta"
import { gesto } from "./componenti/gesto"
import { Pillola } from "./componenti/Pillola"
import { Ripresa } from "./componenti/Ripresa"
import type { Formato } from "./componenti/Tema"
import { FORME, parola, picco, quota, sotto, tondo } from "./CartaDelParametro"
import {
  ESITO,
  type Meteo,
  type NotteMeteo,
  cieloDellaNotte,
  esitoDellaNotte,
  oreDellaNotte,
  ripresaDellaNotte,
} from "./DashboardDati"
import { useCalendario } from "./DashboardLuna"
import {
  type Chiave,
  fa,
  giornoBreve,
  giornoENumero,
  maiuscola,
  numero,
  oraDelSito,
  orario,
  t,
  alPiu,
} from "./i18n"
import { useAggiorna } from "./Meteo"

type Misura = NotteMeteo["measures"][number]
type Codice = Misura["code"]

/** The six cards of the night, always in their place (board v79, `defs`). */
const SEI: readonly Codice[] = ["cloud", "seeing", "jet", "wind", "condensation", "aerosol"]

/** What the weather card says when there is no forecast to show, and why. */
export type Mancanza = {
  segno: SegnoAvviso
  titolo: string
  testo: string
  riprova: boolean
} | null

export function mancanzaDelMeteo(m: Meteo): Mancanza {
  if (m.missing === "no_timezone")
    return {
      segno: "?",
      titolo: t("dashboard.weather.noZone.title"),
      testo: t("dashboard.weather.noZone.text"),
      riprova: false,
    }
  if (m.fetched_at === null && (m.last_request === null || m.last_request.status === "ok")) {
    return {
      segno: "?",
      titolo: t("dashboard.weather.first.title"),
      testo: t("dashboard.weather.first.text"),
      riprova: false,
    }
  }
  if (m.nights.length === 0 || m.fetched_at === null) {
    const da = m.last_request?.at
    return {
      segno: "!",
      titolo: t("dashboard.weather.down.title"),
      testo: da
        ? t("dashboard.weather.down.since", {
            ora: orario(da),
            minuti: numero(Math.round(m.retry_s / 60)),
          })
        : t("dashboard.weather.down.never", { minuti: numero(Math.round(m.retry_s / 60)) }),
      riprova: true,
    }
  }
  return null
}

/** "Previsione del 30 settembre, 18:05 (2 ore fa)" and the other heads of the card. */
function sottotitolo(m: Meteo, manca: Mancanza): string {
  if (m.missing === "no_timezone") return t("dashboard.weather.sub.noZone")
  if (m.fetched_at === null) return t("dashboard.weather.sub.none")
  const quando = {
    giorno: giornoBreve(m.fetched_at),
    ora: orario(m.fetched_at),
    fa: fa(m.fetched_at),
  }
  return t(manca ? "dashboard.weather.sub.last" : "dashboard.weather.sub", quando)
}

type Carta6 = {
  codice: Codice
  stato: StatoMeteo
  valore: string
  unita: string
  celle: CellaMeteo[]
  nota: string
  esito: 0 | 1 | 2 | "mancante" | "neutra"
  giudizio: string
}

/** A card's numbers from the measure the backend wrote; the bars are the shown hours. */
function cartaDi(codice: Codice, n: NotteMeteo, meteo: Meteo): Carta6 {
  const m = n.measures.find((x) => x.code === codice)
  const forma = FORME[codice]
  const ore = n.hours.filter((o) => o.shown)
  const spente = ore.map(() => ({ h: 100, esito: null }))
  const vuota = {
    codice,
    valore: "",
    unita: "",
    celle: spente,
    nota: "",
    esito: "mancante" as const,
    giudizio: "",
  }
  if (
    codice === "seeing" &&
    (!m || m.known_hours === 0) &&
    (!meteo.seeing.key || meteo.seeing.meteoblue === "refused")
  ) {
    // no key, no seeing: say so; a strong jet is Meteoblue's own estimate
    const jet = n.measures.find((x) => x.code === "jet")?.level === "nogo"
    const perche = t(meteo.seeing.key ? "dashboard.seeing.refused" : "dashboard.seeing.noKey")
    return {
      ...vuota,
      stato: "normale",
      valore: jet ? t("dashboard.seeing.poor") : "?",
      nota: jet ? `${t("dashboard.seeing.fromJet")} \u00b7 ${perche}` : perche,
      giudizio: t(jet ? "dashboard.seeing.estimate" : "ui.outcome.missing"),
    }
  }
  if (!m || !forma || m.known_hours === 0) {
    const nuvole = n.measures.find((x) => x.code === "cloud")?.level === "nogo"
    return {
      ...vuota,
      stato:
        nuvole && (codice === "seeing" || codice === "aerosol")
          ? "non si misura"
          : "non disponibile",
    }
  }
  const celle = ore.map((o) => {
    const v = o[forma.campo]
    const livello = codice in o.levels ? o.levels[codice as keyof typeof o.levels] : null
    return {
      h: v === null ? 25 : 25 + Math.max(0, Math.min(1, quota(m, v))) * 75,
      esito: o.sky !== "dark" || !livello ? null : ESITO[livello],
    }
  })
  const scala = meteo.scales.find((s) => s.code === codice)
  return {
    codice,
    stato: "normale",
    valore: m.value === null ? "?" : numero(tondo(codice, m.value)),
    unita: forma.unita ? t(forma.unita) : "",
    celle,
    nota: [sotto(m, n, forma), picco(m, n, forma, scala)].filter(Boolean).join(" \u00b7 "),
    ...giudizioDi(m, scala),
  }
}

/** The pill: the measure's word; a value between two bounds with no word says the bounds. */
function giudizioDi(
  m: Misura,
  scala: Meteo["scales"][number] | undefined,
): Pick<Carta6, "esito" | "giudizio"> {
  if (m.level) return { esito: ESITO[m.level], giudizio: parola(m.code, m.level) }
  const limiti = (scala?.steps ?? []).map((p) => p.bound).sort((a, b) => a - b)
  const [da, a] = [limiti[0], limiti[limiti.length - 1]]
  if (m.value === null || da === undefined || a === undefined || da === a) {
    return { esito: "mancante", giudizio: t("ui.outcome.missing") }
  }
  return {
    esito: "neutra",
    giudizio: t("dashboard.weather.between", { da: numero(da), a: numero(a) }),
  }
}

export function MeteoDellaNotte({ meteo, formato }: { meteo: Meteo; formato: Formato }) {
  const tel = formato === "telefono"
  const riprova = useAggiorna()
  const manca = mancanzaDelMeteo(meteo)
  const notte = manca ? undefined : meteo.nights[0]
  const titolo = t("dashboard.weather.title")
  const sub = sottotitolo(meteo, manca)
  const freccia = (
    <Link
      className="al-dash__tondo-3"
      to="/meteo"
      aria-label={t("dashboard.weather.open")}
      title={t("nav.weather")}
    >
      {"\u2197"}
    </Link>
  )
  const avviso = manca && (
    <Avviso
      tipo="blocco"
      formato={formato}
      segno={manca.segno}
      titolo={manca.titolo}
      testo={manca.testo}
      {...(tel ? { rientro: 20 } : {})}
      {...(manca.riprova
        ? { azione: t("dashboard.weather.down.how"), onAzione: () => riprova.mutate() }
        : {})}
    />
  )
  const carte = notte ? SEI.map((c) => cartaDi(c, notte, meteo)) : []
  const nome = (c: Codice) => t(`weather.measure.${c}` as Chiave)
  if (tel) {
    return (
      <Carta formato="telefono" etichetta={titolo} ritardo={120} padding="20px 0" gap="14">
        <div className="al-dash__riga-37">
          <span className="al-dash__testo-29">{titolo}</span>
          {freccia}
        </div>
        <span className="al-dash__blocco-13">{sub}</span>
        {notte ? (
          <div className="al-dash__riga-38">
            {carte.map((c) => (
              <CardMeteo
                key={c.codice}
                formato="telefono"
                stato={c.stato}
                nome={nome(c.codice)}
                valore={c.valore}
                unita={c.unita}
                celle={c.celle}
                esito={c.esito}
                giudizio={c.giudizio}
              />
            ))}
          </div>
        ) : (
          avviso
        )}
      </Carta>
    )
  }
  return (
    <Carta colonne={12} ritardo={120} padding="24px 28px 28px">
      <div className="al-dash__riga-15">
        <div className="al-dash__riga-17">
          <span className="al-dash__testo-1">{titolo}</span>
          <span className="al-dash__testo-19">{sub}</span>
        </div>
        <span className="al-dash__riga-16">{freccia}</span>
      </div>
      {notte ? (
        <div className="al-dash__griglia-6">
          {carte.map((c) => (
            <CardMeteo
              key={c.codice}
              stato={c.stato}
              nome={nome(c.codice)}
              valore={c.valore}
              unita={c.unita}
              celle={c.celle}
              nota={c.nota}
              esito={c.esito}
              giudizio={c.giudizio}
              link="/meteo"
            />
          ))}
        </div>
      ) : (
        <>
          {avviso}
          <div className="al-dash__griglia-6">
            {SEI.map((c) => (
              <CardMeteo key={c} stato="mancante" nome={nome(c)} />
            ))}
          </div>
        </>
      )}
    </Carta>
  )
}

/** A next night's line: its Transparency, dark without the Moon and the Moon's rise or set, then,
 *  where the forecast has hours, the small chart with the sky and the Moon by hour, the dark's
 *  edges and midnight. */
function Curva({ notte: n }: { notte: NotteMeteo }) {
  const ore = n.hours.filter((o) => o.shown)
  const passo = 1000 / (ore.length || 1)
  const y = (v: number) => 46 - (v / 100) * 42
  const noti = ore.flatMap((o, i) =>
    o.transparency == null ? [] : [{ x: (i + 0.5) * passo, v: o.transparency }],
  )
  const linea = noti
    .map((p, i) => `${i ? "L" : "M"}${p.x.toFixed(1)} ${y(p.v).toFixed(1)}`)
    .join(" ")
  // the Moon on the same scale as the board: 90 degrees at the top, below the horizon on the floor
  const t0 = Date.parse(ore[0]?.at ?? "")
  const luna = (n.moon_track ?? [])
    .map((p, i) => {
      const x = ((Date.parse(p.at) - t0) / 3_600_000 + 0.5) * passo
      const v = p.altitude_deg < 0 ? -1 : (p.altitude_deg / 90) * 100
      return `${i ? "L" : "M"}${x.toFixed(1)} ${y(v).toFixed(1)}`
    })
    .join(" ")
  const id = `dash-mq-${n.night}`
  const buio = ore.findIndex((o) => o.sky === "dark")
  const fine = ore.length - [...ore].reverse().findIndex((o) => o.sky === "dark")
  const mezzanotte = ore.findIndex((o) => oraDelSito(o.at) === "00:00")
  const etichette = [
    { l: oraDelSito(ore[0]?.at ?? "").slice(0, 2), p: 0, al: "l" },
    ...(mezzanotte > 0 ? [{ l: "00", p: (mezzanotte / ore.length) * 100, al: "c" }] : []),
    { l: oraDelSito(ore[ore.length - 1]?.at ?? "").slice(0, 2), p: 100, al: "r" },
  ]
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: 12,
          color: "var(--tenue)",
        }}
      >
        <span>
          {n.transparency != null && (
            <>
              {t("dashboard.next.transparency")}{" "}
              <b style={{ color: "var(--testo)", fontWeight: 600 }}>
                {t("dashboard.next.transparency.value", { v: numero(Math.round(n.transparency)) })}
              </b>
            </>
          )}
        </span>
        <span
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "flex-end",
            columnGap: 5,
            flexWrap: "wrap",
          }}
        >
          {n.moonless_dark_hours != null && (
            <span>
              {t("dashboard.next.moonless", { n: numero(n.moonless_dark_hours) })}
              {n.moon_event != null && " \u00b7"}
            </span>
          )}
          {n.moon_event != null && (
            <span
              style={{ display: "inline-flex", alignItems: "center", gap: 5, whiteSpace: "nowrap" }}
            >
              <i style={{ width: 12, borderTop: "2px dashed var(--luna-linea)" }} />
              {t(`dashboard.next.moon.${n.moon_event}`, {
                ora: oraDelSito(n.moon_event_at ?? ""),
              })}
            </span>
          )}
        </span>
      </div>
      {ore.length > 0 && (
        <>
          <div style={{ position: "relative", height: 48 }}>
            <svg
              viewBox="0 0 1000 48"
              preserveAspectRatio="none"
              aria-hidden="true"
              style={{
                position: "absolute",
                inset: 0,
                width: "100%",
                height: "100%",
                overflow: "visible",
              }}
            >
              <defs>
                <linearGradient id={id} x1={0} y1={0} x2={0} y2={1}>
                  <stop offset="0%" stopColor="var(--barretta)" stopOpacity={0.32} />
                  <stop offset="100%" stopColor="var(--barretta)" stopOpacity={0} />
                </linearGradient>
              </defs>
              {ore.map((o, i) => (
                <rect
                  key={o.at}
                  x={i * passo}
                  y={0}
                  width={passo + 0.5}
                  height={48}
                  style={{
                    fill: "var(--banda-colore)",
                    fillOpacity: `var(--banda-${LIVELLO[o.sky]})`,
                  }}
                />
              ))}
              {buio >= 0 &&
                [buio * passo, fine * passo].map((xx) => (
                  <line
                    key={xx}
                    x1={xx}
                    x2={xx}
                    y1={0}
                    y2={48}
                    stroke="var(--tenue)"
                    strokeOpacity={0.5}
                    strokeDasharray="1 3"
                    vectorEffect="non-scaling-stroke"
                  />
                ))}
              {noti.length > 1 && (
                <path
                  d={`M${noti[0]?.x ?? 0} 46 ${linea.replace(/^M/, "L")} L${noti[noti.length - 1]?.x ?? 0} 46 Z`}
                  fill={`url(#${id})`}
                />
              )}
              {luna.includes("L") && (
                <path
                  d={luna}
                  fill="none"
                  stroke="var(--luna-linea)"
                  strokeWidth={1.5}
                  strokeDasharray="5 4"
                  vectorEffect="non-scaling-stroke"
                />
              )}
              {noti.length > 1 && (
                <path
                  d={linea}
                  fill="none"
                  stroke="var(--barretta)"
                  strokeWidth={2.5}
                  vectorEffect="non-scaling-stroke"
                  strokeLinejoin="round"
                  strokeLinecap="round"
                />
              )}
            </svg>
          </div>
          <div style={{ position: "relative", height: 14, fontSize: 10, color: "var(--tenue)" }}>
            {etichette.map((e) => (
              <span
                key={`${e.l}${e.p}`}
                style={{
                  position: "absolute",
                  left: `${e.p}%`,
                  transform:
                    e.al === "l" ? "none" : e.al === "r" ? "translateX(-100%)" : "translateX(-50%)",
                  whiteSpace: "nowrap",
                }}
              >
                {e.l}
              </span>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

// the sky's step per hour, as the big chart's bands
const LIVELLO = { day: 0, civil: 1, nautical: 2, astronomical: 3, dark: 4 } as const

export function ProssimeNotti({
  meteo,
  colonne,
  formato,
}: {
  meteo: Meteo
  colonne: number
  formato: Formato
}) {
  const tel = formato === "telefono"
  const [aperte, setAperte] = useState(false)
  const calendario = useCalendario().data
  const manca = mancanzaDelMeteo(meteo)
  const notti = manca ? [] : meteo.nights.slice(1, 4)
  // without a forecast the nights stay with the dark the Moon round wrote (board 526)
  const oggi = calendario?.today
  const buie = manca && oggi ? calendario.nights.filter((g) => g.date > oggi).slice(0, 3) : []
  const tante = notti.length || buie.length
  if (!tante) return null
  const titolo = t("dashboard.next.title")
  const senzaMeteo = (g: { date: string; dark_s: number }) => {
    const giorno = maiuscola(giornoENumero(g.date))
    const ore = t("dashboard.next.dark", { ore: alPiu(g.dark_s / 3600, 1) })
    const pillola = (
      <Pillola
        esito="mancante"
        testo={t("dashboard.night.noWeather")}
        fondo="carta"
        dimensione={tel ? "minima" : "media"}
      />
    )
    const cielo = t("dashboard.next.needsForecast")
    if (tel) {
      return (
        <div key={g.date} className="al-dash__colonna-29">
          <span className="al-dash__riga-15">
            <b className="al-dash__testo-7">{giorno}</b>
            {pillola}
          </span>
          <span className="al-dash__testo-41">{ore}</span>
          <span className="al-dash__testo-13">{cielo}</span>
        </div>
      )
    }
    return (
      <div key={g.date} className="al-dash__griglia-11">
        <b className="al-dash__testo-20">{giorno}</b>
        <span className="al-dash__riga-26">{pillola}</span>
        <span className="al-dash__blocco-8">{ore}</span>
        <span className="al-dash__blocco-9">{cielo}</span>
      </div>
    )
  }
  const voce = (n: NotteMeteo) => {
    const rip = ripresaDellaNotte(n)
    const es = esitoDellaNotte(n)
    const giorno = maiuscola(giornoENumero(n.night))
    if (tel) {
      return (
        <div key={n.night} className="al-dash__colonna-29">
          <span className="al-dash__riga-15">
            <b className="al-dash__testo-7">{giorno}</b>
            <Pillola esito={es.esito} testo={es.testo} fondo="carta" dimensione="minima" />
          </span>
          {rip && (
            <span className="al-dash__riga-43">
              <Ripresa tipo={rip.tipo} testo={rip.testo} formato="telefono" />
            </span>
          )}
          <span className="al-dash__testo-41">{oreDellaNotte(n)}</span>
          <span className="al-dash__testo-13">{cieloDellaNotte(n)}</span>
          <span className="al-dash__blocco-14">
            <Curva notte={n} />
          </span>
        </div>
      )
    }
    return (
      <div key={n.night} className="al-dash__griglia-11">
        <b className="al-dash__testo-20">{giorno}</b>
        <span className="al-dash__riga-26">
          {rip && <Ripresa tipo={rip.tipo} testo={rip.testo} />}
          <Pillola esito={es.esito} testo={es.testo} fondo="carta" dimensione="media" />
        </span>
        <span className="al-dash__blocco-8">{oreDellaNotte(n)}</span>
        <span className="al-dash__blocco-9">{cieloDellaNotte(n)}</span>
        <span className="al-dash__blocco-10">
          <Curva notte={n} />
        </span>
      </div>
    )
  }
  const righe = notti.length ? notti.map(voce) : buie.map(senzaMeteo)
  if (tel) {
    const altre = righe.length - 1
    return (
      <Carta formato="telefono" etichetta={titolo} ritardo={300} padding="20px" gap="14">
        <span className="al-dash__testo-29">{titolo}</span>
        {aperte ? righe : righe.slice(0, 1)}
        {altre > 0 && (
          <a
            className="al-bottone al-bottone--testo al-bottone--a-filo"
            style={{ alignSelf: "flex-start" }}
            href="#"
            role="button"
            aria-expanded={aperte}
            onClick={gesto(() => setAperte(!aperte))}
          >
            {aperte
              ? t("dashboard.next.less")
              : t(altre === 1 ? "dashboard.next.more.one" : "dashboard.next.more", {
                  n: numero(altre),
                })}
            <span aria-hidden="true">{aperte ? "\u25b4" : "\u25be"}</span>
          </a>
        )}
      </Carta>
    )
  }
  return (
    <Carta colonne={colonne} ritardo={300} padding="24px" gap="12">
      <div className="al-dash__riga-15">
        <span className="al-dash__testo-1">{titolo}</span>
      </div>
      {righe}
    </Carta>
  )
}
