/**
 * Tre sezioni delle misure di una notte (tavola v76, `componenti/MisureFrame.dc.html` 74-104): il
 * frame scelto, gli oggetti a confronto sulla stessa scala, le mediane per filtro. Scrivono e
 * basta: valori, quartili, estremi e giudizi arrivano dall'API.
 */
import { Pillola } from "./componenti/Pillola"
import { Quartili } from "./componenti/Quartili"
import { gesto } from "./componenti/gesto"
import { nomeDelFiltro } from "./FiltriUsati"
import { numero, oraDelSito, t } from "./i18n"
import { MISURATO, frameMostrato } from "./FramePerFrameDati"
import {
  ESITO,
  type EsitoDelGruppo,
  type FrameMisurato,
  type Misure,
  type Scelta,
  type Tipo,
  chiaveIn,
  filtriDi,
  pallinoDi,
  insieme,
  nomeDelGruppo,
  nomeDi,
  posizione,
  scritto,
  statistica,
} from "./MisureDati"

function campionamento(s: string | null | undefined): string {
  return s ? t(`measures.sampling.${s as "ideal"}`) : ""
}

function due(f: FrameMisurato, arc: string, px: string): string {
  const a = f.values[arc]
  return a === undefined
    ? scritto(px, f.values[px])
    : `${scritto(arc, a)} \u00B7 ${scritto(px, f.values[px])}`
}

interface Riquadro {
  k: string
  v: string
  sub?: string
  tag?: string
  tilt?: string | null
  grande?: boolean
}

/** Le tessere di un frame misurato, quelle che il frame ha (tavola, `FX.tiles`). */
function riquadri(f: FrameMisurato, tipo: Tipo): Riquadro[] {
  const v = f.values
  const stimata = f.state === "estimated"
  const r: Riquadro[] = [
    {
      k: nomeDi("fwhm"),
      v: due(f, "fwhm_arcsec", "fwhm_px"),
      tag: stimata ? t("shot.estimated") : campionamento(f.sampling),
      grande: true,
    },
    { k: nomeDi("hfd"), v: due(f, "hfd_arcsec", "hfd_px") },
    {
      k: nomeDi("stars"),
      v: scritto("stars", v.stars),
      ...(v.saturated !== undefined
        ? { sub: t("measures.saturated", { n: numero(v.saturated) }) }
        : {}),
    },
  ]
  if (v.eccentricity !== undefined) {
    r.push({
      k: nomeDi("eccentricity"),
      v: scritto("eccentricity", v.eccentricity),
      ...(f.angle_axis ? { sub: t(`measures.axis.${f.angle_axis}`) } : {}),
      ...(stimata ? { tag: t("shot.estimated") } : {}),
    })
  }
  if (v.snr !== undefined)
    r.push({
      k: nomeDi("snr"),
      v: scritto("snr", v.snr),
      sub: t(tipo === "oggetto" ? "shot.snr.sub.object" : "shot.snr.sub"),
    })
  r.push({
    k: nomeDi("background"),
    v: scritto("background_adu", v.background_adu),
    ...(v.noise_adu !== undefined
      ? { sub: t("shot.noise", { n: numero(Math.round(v.noise_adu)) }) }
      : {}),
  })
  if (v.airmass !== undefined)
    r.push({
      k: nomeDi("airmass"),
      v: scritto("airmass", v.airmass),
      ...(v.altitude_deg !== undefined
        ? { sub: `${nomeDi("altitude_deg")} ${scritto("altitude_deg", v.altitude_deg)}` }
        : {}),
    })
  if (v.gradient_noise !== undefined)
    r.push({
      k: nomeDi("gradient"),
      v: scritto("gradient_noise", v.gradient_noise),
      ...(f.gradient_side ? { sub: t(`measures.brighter.${f.gradient_side}`) } : {}),
    })
  if (v.hfd_tilt_pct !== undefined)
    r.push({
      k: nomeDi("tilt"),
      v: scritto("hfd_tilt_pct", v.hfd_tilt_pct),
      sub: t("shot.tilt.sub"),
      tilt: f.tilt_level,
    })
  if (v.off_axis_px !== undefined) {
    const arc =
      v.off_axis_arcsec === undefined
        ? ""
        : ` \u00B7 ${scritto("off_axis_arcsec", v.off_axis_arcsec)}`
    r.push({
      k: nomeDi("curvature"),
      v: `${scritto("off_axis_px", v.off_axis_px)}${arc}`,
      sub: t("shot.curvature.sub"),
    })
  }
  if (v.fwhm_tilt !== undefined && v.fwhm_curvature !== undefined) {
    r.push({
      k: `${nomeDi("tilt")} \u00B7 ${nomeDi("curvature")} (FWHM)`,
      v: `${scritto("fwhm_tilt", v.fwhm_tilt)} \u00B7 ${scritto("fwhm_curvature", v.fwhm_curvature)}`,
      sub: t("shot.fwhm.field.sub"),
    })
  }
  if (v.sqm !== undefined)
    r.push({ k: nomeDi("sqm"), v: scritto("sqm", v.sqm), sub: t("measures.sqm.unit") })
  return r
}

/** La nota sopra le tessere: forma stimata, senza scala del cielo, senza sito. */
function nota(
  f: FrameMisurato,
): { testo: string; segno: string; esito: "incerta" | "mancante" } | null {
  if (f.state === "estimated")
    return { testo: t("shot.estimated.note"), segno: "!", esito: "incerta" }
  if (f.values.fwhm_px !== undefined && f.values.fwhm_arcsec === undefined)
    return { testo: t("shot.no.scale"), segno: "?", esito: "mancante" }
  if (f.values.fwhm_arcsec !== undefined && f.values.fwhm_zenith_arcsec === undefined)
    return { testo: t("shot.no.site"), segno: "?", esito: "mancante" }
  return null
}

export function IlFrame({
  misure,
  scelta,
  sel,
  onSel,
  tipo,
}: {
  misure: Misure
  scelta: Scelta
  sel: number | null
  onSel: (id: number) => void
  tipo: Tipo
}) {
  const nomi = new Map(misure.groups.map((o) => [o.key, nomeDelGruppo(o)]))
  const { vista, f } = frameMostrato(misure, scelta, sel)
  const i = f ? vista.indexOf(f) : -1
  const vai = (d: number) => () => {
    const n = vista[(i + d + vista.length) % vista.length]
    if (n) onSel(n.frame_id)
  }
  const dove = f
    ? [
        f.group ? (nomi.get(f.group) ?? f.group) : null,
        f.start ? oraDelSito(f.start) : null,
        f.values.altitude_deg !== undefined
          ? `${nomeDi("altitude_deg")} ${scritto("altitude_deg", f.values.altitude_deg)}`
          : null,
        f.values.airmass !== undefined
          ? `${nomeDi("airmass")} ${scritto("airmass", f.values.airmass)}`
          : null,
      ].filter(Boolean)
    : []
  const n = f && MISURATO.has(f.state) ? nota(f) : null
  return (
    <section className="al-c-misure-frame__colonna-4" aria-label={t("shot.section")}>
      <div className="al-c-misure-frame__riga-28">
        <div className="al-c-misure-frame__colonna-7">
          <h2 className="al-c-misure-frame__testo-1">
            {f
              ? t("shot.title", {
                  i: numero(i + 1),
                  n: numero(vista.length),
                  f: nomeDelFiltro(f.filter),
                })
              : t("shot.none")}
          </h2>
          <span className="al-c-misure-frame__testo-4">{dove.join(" \u00B7 ")}</span>
        </div>
        <div className="al-c-misure-frame__riga-29">
          <button
            type="button"
            className="al-bottone al-c-misure-frame__tondo-6"
            aria-label={t("shot.prev")}
            onClick={vai(-1)}
            disabled={vista.length < 2}
          >
            {"\u2039"}
          </button>
          <button
            type="button"
            className="al-bottone al-c-misure-frame__tondo-6"
            aria-label={t("shot.next")}
            onClick={vai(1)}
            disabled={vista.length < 2}
          >
            {"\u203A"}
          </button>
        </div>
      </div>
      {f?.state === "pending" && (
        <div className="al-c-misure-frame__riga-30">
          <span className="al-c-misure-frame__tondo-7" aria-hidden="true" />
          {t("measures.pending")}
        </div>
      )}
      {f?.state === "too_few_stars" && (
        <div className="al-c-misure-frame__riga-31">
          <span className="al-c-misure-frame__tondo-8" aria-hidden="true">
            ?
          </span>
          {t("shot.few")}
        </div>
      )}
      {n && (
        <div className="al-c-misure-frame__riga-32">
          <Pillola forma="segno" esito={n.esito} segno={n.segno} fondo="carta2" />
          {n.testo}
        </div>
      )}
      {f && MISURATO.has(f.state) && (
        <div className="al-c-misure-frame__centro-1 al-c-misure-frame__centro-1--frame">
          {riquadri(f, tipo).map((x) => (
            <div key={x.k} className="al-c-misure-frame__colonna-8">
              <span className="al-c-misure-frame__testo-2">{x.k}</span>
              <span
                className={`al-c-misure-frame__testo-13 ${x.grande ? "al-c-misure-frame__testo-13--grande" : ""}`}
              >
                {x.v}
              </span>
              {x.sub && <span className="al-c-misure-frame__testo-14">{x.sub}</span>}
              {x.tilt && (
                <span className="al-c-misure-frame__riga-8">
                  <Pillola
                    esito={ESITO[x.tilt] ?? 0}
                    testo={t(`measures.tilt.${x.tilt as "go"}`)}
                    dimensione="micro"
                    fondo="carta"
                  />
                </span>
              )}
              {x.tag && <span className="al-c-misure-frame__blocco-3">{x.tag}</span>}
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

export function AConfronto({
  misure,
  scelta,
  misura,
  scelte,
  onMisura,
  onOggetto,
  tipo,
  esiti,
}: {
  misure: Misure
  scelta: Scelta
  misura: string
  scelte: string[]
  onMisura: (id: string) => void
  onOggetto: (o: string | null) => void
  tipo: Tipo
  esiti?: ReadonlyMap<string, EsitoDelGruppo> | undefined
}) {
  const titolo = t(tipo === "oggetto" ? "compare.nights" : "compare.objects")
  const tutta = insieme(misure, null, scelta.filtro)
  const chiave = chiaveIn(misura, tutta)
  const scala = statistica(tutta, chiave)
  const basso = scala?.low ?? 0
  const alto = scala?.high ?? 1
  const passband = new Map(misure.filters.map((f) => [f.name, f.passband]))
  return (
    <section className="al-c-misure-frame__colonna-9" aria-label={titolo}>
      <div className="al-c-misure-frame__riga-9">
        <h2 className="al-c-misure-frame__blocco-4">{titolo}</h2>
        <select
          key={misura}
          defaultValue={misura}
          onChange={(e) => onMisura(e.target.value)}
          aria-label={t("compare.measure")}
          className="al-tendina al-tendina--tondo"
          style={{
            flex: "none",
            minHeight: 44,
            boxSizing: "border-box",
            fontFamily: "var(--carattere)",
          }}
        >
          {scelte.map((k) => (
            <option key={k} value={k}>
              {nomeDi(k)}
            </option>
          ))}
        </select>
      </div>
      <div className="al-c-misure-frame__colonna-10">
        {misure.groups.map((o) => {
          const set = insieme(misure, o.key, scelta.filtro)
          const s = statistica(set, chiave)
          const acceso = scelta.gruppo === o.key
          const ha = s?.median != null && s.q1 != null && s.q3 != null
          const es = esiti?.get(o.key)
          return (
            <a
              key={o.key}
              className="al-c-misure-frame__centro-2"
              href="#"
              onClick={gesto(() => onOggetto(acceso ? null : o.key))}
              aria-pressed={acceso ? "true" : "false"}
            >
              <span className="al-c-misure-frame__colonna-11">
                <span className="al-c-misure-frame__testo-15">{nomeDelGruppo(o)}</span>
                <span className="al-c-misure-frame__riga-34">
                  {filtriDi(misure, o.key).map((f) => (
                    <span
                      key={f.name}
                      className="al-c-misure-frame__tondo-10"
                      aria-hidden="true"
                      style={pallinoDi(passband.get(f.name))}
                    />
                  ))}
                  {t("measures.of", { m: numero(s?.measured ?? 0), n: numero(set?.frames ?? 0) })}
                </span>
              </span>
              <span className="al-c-misure-frame__colonna-12">
                <Quartili
                  misura="piccola"
                  q1={ha ? posizione(s.q1 ?? 0, basso, alto) : "0%"}
                  qw={ha ? posizione((s.q3 ?? 0) - (s.q1 ?? 0) + basso, basso, alto) : "0%"}
                  m={ha ? posizione(s.median ?? 0, basso, alto) : "-10%"}
                />
              </span>
              <span className="al-c-misure-frame__colonna-13">
                <span className="al-c-misure-frame__testo-16">{scritto(chiave, s?.median)}</span>
                {es && (
                  <Pillola
                    esito={es.esito}
                    testo={es.testo}
                    segno={es.segno}
                    dimensione="micro"
                    fondo="carta"
                  />
                )}
              </span>
            </a>
          )
        })}
      </div>
      <span className="al-c-misure-frame__riga-35">
        <span>{scritto(chiave, scala?.low)}</span>
        <span>{t("compare.scale")}</span>
        <span>{scritto(chiave, scala?.high)}</span>
      </span>
    </section>
  )
}

// Le colonne della tabella, come la tavola (`PFK`).
const COLONNE = ["fwhm", "hfd", "eccentricity", "snr", "background", "tilt", "curvature", "sqm"]

export function PerFiltro({
  misure,
  scelta,
  altra,
  onFiltro,
}: {
  misure: Misure
  scelta: Scelta
  altra: string | null
  onFiltro: (f: string | null) => void
}) {
  const colonne = [
    ...COLONNE.map((id) => ({ id, testa: nomeDi(id) })),
    ...(altra ? [{ id: altra, testa: nomeDi(altra) }] : []),
  ]
  const griglia = `minmax(92px,1.1fr) ${colonne.map((c) => (c.id === "sqm" || c.id === "fwhm" ? "minmax(84px,1.3fr)" : "minmax(64px,1fr)")).join(" ")}`
  return (
    <section className="al-c-misure-frame__colonna-9" aria-label={t("perfilter.title")}>
      <h2 className="al-c-misure-frame__testo-1">{t("perfilter.title")}</h2>
      <div className="al-c-misure-frame__blocco-9">
        <div
          className="al-c-misure-frame__centro-3"
          role="table"
          aria-label={t("perfilter.table")}
          style={{ gridTemplateColumns: griglia, minWidth: `${100 + colonne.length * 72}px` }}
        >
          <div className="al-c-misure-frame__blocco-1" role="row">
            <span
              className="al-c-misure-frame__blocco-10"
              role="columnheader"
              style={{ textAlign: "left" }}
            >
              {t("perfilter.head.filter")}
            </span>
            {colonne.map((c) => (
              <span
                key={c.id}
                className="al-c-misure-frame__blocco-10"
                role="columnheader"
                style={{ textAlign: "right" }}
              >
                {c.testa}
              </span>
            ))}
          </div>
          {filtriDi(misure, scelta.gruppo).map((f) => {
            const set = insieme(misure, scelta.gruppo, f.name)
            const acceso = scelta.filtro === f.name
            return (
              <a
                key={f.name}
                className="al-c-misure-frame__blocco-1"
                href="#"
                role="row"
                onClick={gesto(() => onFiltro(acceso ? null : f.name))}
                aria-pressed={acceso ? "true" : "false"}
              >
                <span
                  className="al-c-misure-frame__colonna-14"
                  role="cell"
                  style={{ alignItems: "flex-start" }}
                >
                  <span
                    className="al-c-misure-frame__colonna-15"
                    style={{ alignItems: "flex-start", textAlign: "left" }}
                  >
                    <span className="al-c-misure-frame__riga-36" style={{ fontWeight: 600 }}>
                      <span
                        className="al-c-misure-frame__tondo-1"
                        aria-hidden="true"
                        style={pallinoDi(f.passband)}
                      />
                      {nomeDelFiltro(f.name)}
                    </span>
                    <span className="al-c-misure-frame__testo-17">
                      {t("perfilter.frames", {
                        m: numero(statistica(set, "hfd_px")?.measured ?? 0),
                        n: numero(set?.frames ?? 0),
                      })}
                    </span>
                  </span>
                </span>
                {colonne.map((c) => (
                  <Cella key={c.id} id={c.id} set={set} />
                ))}
              </a>
            )
          })}
        </div>
      </div>
      <span className="al-c-misure-frame__testo-18">{t("perfilter.how")}</span>
    </section>
  )
}

function Cella({ id, set }: { id: string; set: ReturnType<typeof insieme> }) {
  const chiave = chiaveIn(id, set)
  const s = statistica(set, chiave)
  let sotto = ""
  if (id === "fwhm") sotto = campionamento(statistica(set, "fwhm_px")?.verdict)
  const rumore = statistica(set, "noise_adu")?.median
  if (id === "background" && s?.median != null && rumore != null)
    sotto = t("perfilter.noise", { n: numero(Math.round(rumore)) })
  const tilt = id === "tilt" ? s?.verdict : null
  return (
    <span className="al-c-misure-frame__colonna-14" role="cell" style={{ alignItems: "flex-end" }}>
      <span
        className="al-c-misure-frame__colonna-15"
        style={{ alignItems: "flex-end", textAlign: "right" }}
      >
        <span className="al-c-misure-frame__riga-36" style={{ fontWeight: 400 }}>
          {scritto(chiave, s?.median)}
        </span>
        {tilt && (
          <Pillola
            esito={ESITO[tilt] ?? 0}
            testo={t(`measures.tilt.${tilt as "go"}`)}
            acapo
            allinea="flex-end"
            dimensione="micro"
            fondo="carta"
          />
        )}
        {sotto && <span className="al-c-misure-frame__testo-17">{sotto}</span>}
      </span>
    </span>
  )
}
