import { useQuery } from "@tanstack/react-query"
import type { CSSProperties } from "react"
import { Link } from "react-router"

import { api } from "./api/client"
import type { components } from "./api/schema"
import { Avviso } from "./componenti/Avviso"
import { Carta } from "./componenti/Carta"
import type { Formato } from "./componenti/Tema"
import { nomeDelFiltro } from "./FiltriUsati"
import { mesiBrevi, numero, oreEMinuti, t, unDecimale } from "./i18n"
import { pallinoDi } from "./MisureDati"

type Anno = components["schemas"]["YearOut"]
type Mese = Anno["months"][number]
type Filtro = Anno["filters"][number]

// board `hatch(t.sparkOff)`: the months still to come
const TRATTEGGIO =
  "repeating-linear-gradient(135deg, var(--barretta-spenta) 0 3px, transparent 3px 8px)"
// the paused grow-in of the sheet starts with the card
const VIA: CSSProperties = { animationPlayState: "running" }

function useAnno() {
  return useQuery({
    queryKey: ["year"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/year")
      if (error) throw new Error(t("dashboard.year.failed"))
      return data
    },
  })
}

/** Ore come le scrive la tavola: "128 h 40", e zero e' "0 h", non "< 6 min". */
function ore(s: number): string {
  return s === 0 ? t("dashboard.year.zero") : oreEMinuti(s)
}

/** La differenza col segno della tavola, meno tipografico o piu': "+4 h". */
function scarto(s: number): string {
  if (s === 0) return t("dashboard.year.zero")
  return `${s < 0 ? "\u2212" : "+"}${oreEMinuti(Math.abs(s))}`
}

/** Una barra del mese (tavola `months`): altezza dall'API, fra il 14 e l'86% della colonna. */
function barra(m: Mese) {
  return {
    h: m.future ? "40%" : `${14 + m.bar * 72}%`,
    gh: `${14 + m.previous_bar * 72}%`,
    bg: m.future ? TRATTEGGIO : m.current ? "var(--giorno-su)" : "var(--barra-mese)",
    ring: m.future ? "var(--barretta-spenta)" : "transparent",
  }
}

// a gradient is not a colour inside conic-gradient: the colour stripes become three slices
const A_COLORI = ["var(--filtro-r)", "var(--filtro-g)", "var(--filtro-b)"]

/** I colori del pezzo d'anello: senza filtro un grigio (nel pallino e' un filo), a colori R, G, B. */
function tinte(f: Filtro): string[] {
  const p = pallinoDi(f.passband)
  if (p.border) return ["var(--ignoto-tratteggio)"]
  return p.background === "var(--filtro-a-colori)" ? A_COLORI : [p.background]
}

/** L'anello dei filtri (tavola `filterRing`): i pezzi dall'API, separati da un filo di carta. */
function anello(filtri: Filtro[]): string {
  const pezzi = filtri.map((f) => {
    const fine = Math.max(f.ring_from, f.ring_to - 0.6)
    const colori = tinte(f)
    const passo = (fine - f.ring_from) / colori.length
    const fette = colori.map((c, i) => {
      const da = f.ring_from + i * passo
      return `${c} ${da}% ${i === colori.length - 1 ? fine : da + passo}%`
    })
    return `${fette.join(", ")}, var(--carta) ${fine}% ${f.ring_to}%`
  })
  return `conic-gradient(${pezzi.join(", ")})`
}

function Statistiche() {
  return (
    <Link
      className="al-dash__tondo-3"
      to="/statistiche"
      aria-label={t("dashboard.year.open")}
      title={t("nav.stats")}
    >
      {"\u2197"}
    </Link>
  )
}

function Mesi({ anno, telefono }: { anno: Anno; telefono: boolean }) {
  const nomi = mesiBrevi()
  const detto = t(anno.previous_known ? "dashboard.year.bars" : "dashboard.year.bars.alone", {
    anno: String(anno.year),
  })
  return (
    <>
      <div
        className={telefono ? "al-dash__griglia-19" : "al-dash__griglia-13"}
        role="img"
        aria-label={detto}
      >
        {anno.months.map((m) => {
          const b = barra(m)
          const pezzi = (
            <>
              <span
                className="al-dash__pillola-9"
                data-anim="1"
                style={{ ...VIA, height: b.h, background: b.bg, boxShadow: `inset 0 0 0 1px ${b.ring}` }}
              />
              {anno.previous_known && (
                <span
                  className={telefono ? "al-dash__strato-3" : "al-dash__strato-2"}
                  style={{ height: b.gh }}
                />
              )}
            </>
          )
          return telefono ? (
            <div key={m.month} className="al-dash__riga-45">
              {pezzi}
            </div>
          ) : (
            <div key={m.month} className="al-dash__colonna-16">
              {m.current && <span className="al-dash__strato-1">{ore(m.integration_s)}</span>}
              {pezzi}
            </div>
          )
        })}
      </div>
      <div className={telefono ? "al-dash__griglia-20" : "al-dash__griglia-10"} aria-hidden="true">
        {nomi.map((n) => (
          <span key={n}>{n}</span>
        ))}
      </div>
    </>
  )
}

function Anello({ anno, telefono }: { anno: Anno; telefono: boolean }) {
  const primo = anno.filters[0]
  if (!primo) return null
  return (
    <span
      className={telefono ? "al-dash__tondo-15" : "al-dash__tondo-10"}
      data-anim="1"
      style={{ ...VIA, background: anello(anno.filters) }}
    >
      <span className={telefono ? "al-dash__tondo-16" : "al-dash__tondo-11"}>
        <span className={telefono ? "al-dash__testo-41" : "al-dash__testo-26"}>
          {`${numero(primo.share_pct)}%`}
        </span>
        <span className={telefono ? "al-dash__testo-17" : "al-dash__testo-13"}>
          {t("dashboard.year.filters.in", { filtro: nomeDelFiltro(primo.name) })}
        </span>
      </span>
    </span>
  )
}

function Desktop({ anno }: { anno: Anno }) {
  const a = String(anno.year)
  const prima = String(anno.year - 1)
  const media = anno.per_night_s === null ? "\u2014" : ore(anno.per_night_s)
  return (
    <>
      <Carta
        colonne={8}
        etichetta={t("dashboard.year.title", { anno: a })}
        ritardo={360}
        padding="24px 28px"
        griglia="260px minmax(0,1fr)"
        gap="32"
      >
        <div className="al-dash__colonna-15">
          <span className="al-dash__testo-1">{t("dashboard.year.title", { anno: a })}</span>
          <span className="al-dash__colonna-12">
            <span className="al-dash__testo-22">{ore(anno.integration_s)}</span>
            <span className="al-dash__testo-18">
              {t("dashboard.year.inNights", { n: numero(anno.nights) })}
            </span>
          </span>
          <div className="al-dash__griglia-12">
            <span className="al-dash__riquadro-1">
              <b className="al-dash__testo-23">{media}</b>
              <br />
              <span className="al-dash__testo-13">{t("dashboard.year.perNight")}</span>
            </span>
            <span className="al-dash__riquadro-1">
              <b className="al-dash__testo-23">{unDecimale(anno.per_month)}</b>
              <br />
              <span className="al-dash__testo-13">{t("dashboard.year.perMonth")}</span>
            </span>
          </div>
          <Statistiche />
        </div>
        <div className="al-dash__colonna-3">
          <Mesi anno={anno} telefono={false} />
          <div className="al-dash__riga-27">
            <span className="al-dash__riga-28">
              <i className="al-dash__pillola-10" />
              {a}
            </span>
            {anno.previous_known && (
              <>
                <span className="al-dash__riga-28">
                  <i className="al-dash__pillola-11" />
                  {prima}
                </span>
                <span className="al-dash__testo-24">
                  {t("dashboard.year.vs", {
                    ore: ore(anno.integration_s),
                    prima: ore(anno.previous_same_period_s),
                    anno: prima,
                  })}
                  {" \u00b7 "}
                  <b className="al-dash__testo-25">{scarto(anno.vs_previous_s)}</b>
                </span>
              </>
            )}
          </div>
        </div>
      </Carta>
      <Carta
        colonne={4}
        etichetta={t("dashboard.year.filters.title", { anno: a })}
        ritardo={420}
        padding="24px"
        gap="16"
        giustifica={anno.filters.length > 0 ? "space-between" : "flex-start"}
      >
        <span className="al-dash__testo-1">{t("dashboard.year.filters.title", { anno: a })}</span>
        {anno.filters.length > 0 ? (
          <>
            <div className="al-dash__griglia-14">
              <Anello anno={anno} telefono={false} />
              <div className="al-dash__colonna-3">
                {anno.filters.map((f) => (
                  <span key={f.name} className="al-dash__griglia-15">
                    <i className="al-dash__tondo-12" style={pallinoDi(f.passband)} />
                    <span>
                      <b className="al-dash__testo-7">{nomeDelFiltro(f.name)}</b>{" "}
                      <span className="al-dash__testo-27">{ore(f.integration_s)}</span>
                    </span>
                    <b className="al-dash__testo-28">{`${numero(f.share_pct)}%`}</b>
                  </span>
                ))}
              </div>
            </div>
            <span className="al-dash__testo-13">
              {t("dashboard.year.filters.caption", { ore: ore(anno.integration_s) })}
            </span>
          </>
        ) : (
          <span className="al-dash__testo-13">{t("dashboard.year.none", { anno: a })}</span>
        )}
      </Carta>
    </>
  )
}

function Telefono({ anno }: { anno: Anno }) {
  const a = String(anno.year)
  const sotto = [
    t("dashboard.year.tel.nights", { n: numero(anno.nights) }),
    t("dashboard.year.tel.perNight", {
      ore: anno.per_night_s === null ? "\u2014" : ore(anno.per_night_s),
    }),
    t("dashboard.year.tel.perMonth", { n: unDecimale(anno.per_month) }),
  ].join(" \u00b7 ")
  return (
    <Carta
      formato="telefono"
      etichetta={t("dashboard.year.short", { anno: a })}
      ritardo={360}
      padding="20px"
      gap="14"
    >
      <div className="al-dash__riga-25" style={{ alignItems: "center" }}>
        <span style={{ display: "flex", flexDirection: "column", gap: 2, minWidth: 0 }}>
          <span className="al-dash__testo-29">{t("dashboard.year.short", { anno: a })}</span>
          <span className="al-dash__testo-13">{sotto}</span>
        </span>
        <Statistiche />
      </div>
      <span className="al-dash__testo-43">{ore(anno.integration_s)}</span>
      <Mesi anno={anno} telefono />
      {anno.previous_known && (
        <span className="al-dash__testo-13">
          {t("dashboard.year.tel.vs", {
            anno: String(anno.year - 1),
            scarto: scarto(anno.vs_previous_s),
          })}
        </span>
      )}
      <div className="al-dash__griglia-21">
        {anno.filters.length > 0 ? (
          <>
            <Anello anno={anno} telefono />
            <div className="al-dash__colonna-30">
              {anno.filters.map((f) => (
                <span key={f.name} className="al-dash__griglia-22">
                  <i className="al-dash__tondo-17" style={pallinoDi(f.passband)} />
                  <b className="al-dash__testo-7">{nomeDelFiltro(f.name)}</b>
                  <span>{`${numero(f.share_pct)}%`}</span>
                </span>
              ))}
            </div>
          </>
        ) : (
          <span className="al-dash__testo-13" style={{ gridColumn: "1 / -1" }}>
            {t("dashboard.year.none", { anno: a })}
          </span>
        )}
      </div>
    </Carta>
  )
}

/**
 * L'anno della Dashboard (tavola v79): "Il 2026, fino a oggi", una barra per mese col 2025
 * tratteggiato, e "Filtri del 2026" con l'anello; sul telefono in una carta sola. Tutto dall'API.
 */
export function AnnoDellaDashboard({ formato }: { formato: Formato }) {
  const lettura = useAnno()
  if (lettura.isPending) return null
  if (!lettura.data) {
    return (
      <div style={{ gridColumn: "1 / -1" }}>
        <Avviso tipo="riga" formato={formato} segno="!" titolo={t("dashboard.year.failed")} />
      </div>
    )
  }
  return formato === "telefono" ? <Telefono anno={lettura.data} /> : <Desktop anno={lettura.data} />
}
