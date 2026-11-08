/**
 * **Tutto della notte** (tavola v76, `componenti/FinestraRiepilogo.dc.html` e
 * `componenti/Riepilogo.dc.html`, tipo `notte`): il riepilogo di una notte in una finestra sopra
 * le Notti, larga 1180 sul desktop, pagina intera sul telefono. Si chiude con x, Esc o fuori;
 * le frecce vanno alla notte prima e dopo. Formatta e basta: la notte, i setup e il catalogo da
 * `GET /api/v1/nights/{id}`, le misure da `GET /api/v1/nights/{id}/measures`.
 */
import { useQuery } from "@tanstack/react-query"
import { type MouseEvent, useEffect, useRef, useState } from "react"
import { Link } from "react-router"

import { api } from "./api/client"
import type { components } from "./api/schema"
import { Avviso } from "./componenti/Avviso"
import { Carta } from "./componenti/Carta"
import { trattieni } from "./componenti/Finestra"
import { gesto } from "./componenti/gesto"
import { Pillola } from "./componenti/Pillola"
import { type CartaScheletro, Scheletro } from "./componenti/Scheletro"
import { type Formato, useTema } from "./componenti/Tema"
import { VARIANTE } from "./FiltriUsati"
import { type Chiave, dataLunga, decimali, numero, oraDelSito, oreEMinuti, t } from "./i18n"
import { MisureDellaNotte } from "./MisureDellaNotte"
import { insieme, scritto, statistica } from "./MisureDati"
import { MENTRE_LEGGE_MS } from "./Notti"
import { cielo, segnoDi } from "./NottiDati"
import { tipoDi } from "./RigaDellArchivio"
import { costellazione } from "./costellazioni"

type Dettaglio = components["schemas"]["NightDetail"]
type Setup = components["schemas"]["NightRig"]

class NonTrovata extends Error {}

async function dettaglio(id: number): Promise<Dettaglio> {
  const { data, error, response } = await api.GET("/api/v1/nights/{night_id}", {
    params: { path: { night_id: id } },
  })
  if (response.status === 404) throw new NonTrovata()
  if (error) throw new Error(t("window.failed"))
  return data
}

async function misure(id: number) {
  const { data, error } = await api.GET("/api/v1/nights/{night_id}/measures", {
    params: { path: { night_id: id } },
  })
  if (error) throw new Error(t("window.failed"))
  return data
}

// Le misure della finestra per formato (tavola, `L` e `D`: inline anche li', brief a Design).
const MISURE = {
  desktop: { gap: "16px", pad: "28px", tfs: "44px", bfs: "64px", nav: "44px" },
  telefono: { gap: "12px", pad: "20px", tfs: "30px", bfs: "48px", nav: "44px" },
}

const SCHELETRO: CartaScheletro[] = [
  {
    h: "220px",
    pad: "24px",
    gap: "14px",
    blocchi: [t("window.loading"), { h: "44px", w: "60%" }, { flex: "1" }],
  },
  { h: "520px", pad: "24px", blocchi: [{ h: "100%" }] },
]

export function TuttoDellaNotte({
  id,
  formato,
  onChiudi,
  onPrima,
  onDopo,
}: {
  id: number
  formato: Formato
  onChiudi: () => void
  onPrima?: (() => void) | undefined
  onDopo?: (() => void) | undefined
}) {
  const { modo, accento } = useTema()
  const tel = formato === "telefono"
  const pannello = useRef<HTMLDivElement>(null)
  const chiusura = useRef(onChiudi)
  useEffect(() => {
    chiusura.current = onChiudi
  }, [onChiudi])
  useEffect(() => {
    const prima = document.activeElement
    pannello.current?.focus({ preventScroll: true })
    const esc = (e: globalThis.KeyboardEvent) => {
      if (e.key === "Escape") chiusura.current()
    }
    document.addEventListener("keydown", esc)
    return () => {
      document.removeEventListener("keydown", esc)
      if (prima instanceof HTMLElement) prima.focus()
    }
  }, [])

  const notte = useQuery({
    queryKey: ["nights", "detail", id],
    queryFn: () => dettaglio(id),
    retry: (n, e) => !(e instanceof NonTrovata) && n < 2,
  })
  const mis = useQuery({
    queryKey: ["nights", "measures", id],
    queryFn: () => misure(id),
    refetchInterval: (q) => ((q.state.data?.pending ?? 0) > 0 ? MENTRE_LEGGE_MS : false),
  })
  const fuori = (e: MouseEvent) => {
    if (e.target === e.currentTarget) onChiudi()
  }
  const L = MISURE[formato]

  let corpo
  if (notte.isPending) {
    corpo = (
      <Scheletro
        formato={formato}
        carte={SCHELETRO}
        griglia="minmax(0,1fr)"
        gap={L.gap}
        testo={t("window.loading")}
      />
    )
  } else if (notte.error instanceof NonTrovata) {
    corpo = (
      <Avviso
        tipo="pagina"
        formato={formato}
        segno="?"
        titolo={t("window.gone")}
        testo={t("window.gone.text")}
      />
    )
  } else if (notte.isError) {
    corpo = (
      <Avviso
        tipo="pagina"
        formato={formato}
        segno="!"
        titolo={t("window.failed")}
        testo={t("window.failed.text")}
        azione={t("window.retry")}
        onAzione={() => void notte.refetch()}
      />
    )
  } else {
    const d = notte.data
    corpo = (
      <div
        className="al-c-riepilogo__centro-1"
        style={{
          gridTemplateColumns: tel ? "minmax(0,1fr)" : "repeat(12,minmax(0,1fr))",
          gap: L.gap,
        }}
      >
        <Testa
          d={d}
          misure={mis.data}
          formato={formato}
          onChiudi={onChiudi}
          onPrima={onPrima}
          onDopo={onDopo}
        />
        <Setups setups={d.rigs} formato={formato} />
        <Oggetti d={d} formato={formato} />
        <div className="al-c-riepilogo__blocco-4">
          {mis.data && <MisureDellaNotte key={id} misure={mis.data} formato={formato} />}
          {mis.isError && !mis.data && (
            <Avviso
              formato={formato}
              segno="!"
              titolo={t("window.failed")}
              azione={t("window.retry")}
              onAzione={() => void mis.refetch()}
            />
          )}
        </div>
      </div>
    )
  }

  return (
    <div
      className="al-c-finestra-riepilogo__blocco-1"
      data-modo={modo}
      data-accento={accento}
      data-formato={formato}
    >
      <div
        className="al-c-finestra-riepilogo__blocco-2"
        data-an="velo"
        role="dialog"
        aria-modal="true"
        aria-label={t("window.night")}
        onClick={fuori}
        style={{
          position: "fixed",
          background: tel ? "var(--telaio)" : "rgba(8,8,10,.62)",
          padding: tel ? 0 : "32px",
        }}
      >
        <div
          ref={pannello}
          tabIndex={-1}
          onKeyDown={trattieni}
          className="al-c-finestra-riepilogo__blocco-3"
          data-an="pannello"
          style={{
            maxWidth: tel ? "none" : "1180px",
            borderRadius: tel ? 0 : "32px",
            padding: tel ? "12px 12px 32px" : "20px",
            minHeight: tel ? "100%" : 0,
          }}
        >
          {corpo}
        </div>
      </div>
    </div>
  )
}

function Tondo({
  etichetta,
  segno,
  on,
  classe = "al-c-riepilogo__tondo-1",
}: {
  etichetta: string
  segno: string
  on: (() => void) | undefined
  classe?: string
}) {
  return (
    <a
      className={classe}
      href="#"
      onClick={gesto(on)}
      aria-label={etichetta}
      aria-disabled={on ? undefined : "true"}
      style={{ width: 44, height: 44, opacity: on ? 1 : 0.35 }}
    >
      {segno}
    </a>
  )
}

function Testa({
  d,
  misure: m,
  formato,
  onChiudi,
  onPrima,
  onDopo,
}: {
  d: Dettaglio
  misure: components["schemas"]["NightMeasures"] | undefined
  formato: Formato
  onChiudi: () => void
  onPrima?: (() => void) | undefined
  onDopo?: (() => void) | undefined
}) {
  const tel = formato === "telefono"
  const n = d.night
  const L = MISURE[formato]
  const conOre = n.integration_s > 0
  const periodo =
    d.first_start && d.last_end
      ? t("window.span", { sito: n.site, da: oraDelSito(d.first_start), a: oraDelSito(d.last_end) })
      : t("window.span.untimed", { sito: n.site })
  const grande = conOre ? oreEMinuti(n.integration_s) : t("window.frames", { n: numero(n.frames) })
  const sotto = conOre
    ? `${t("window.frames", { n: numero(n.frames) })} \u00B7 ${t("window.objects", { n: n.objects.length })}`
    : t("window.untimed")
  const tutta = m && insieme(m, null, null)
  const arc = statistica(tutta, "fwhm_arcsec")?.median
  const fwhm = !m
    ? "\u2026"
    : arc != null
      ? scritto("fwhm_arcsec", arc)
      : scritto("fwhm_px", statistica(tutta, "fwhm_px")?.median)
  const snr = !m ? "\u2026" : scritto("snr", statistica(tutta, "snr")?.median)
  const kpi = [
    { v: fwhm, l: t("window.fwhm") },
    { v: snr, l: t("window.snr") },
  ]
  const c = cielo(n)
  const esito = (
    <Pillola
      esito={c.esito === -1 ? "mancante" : c.esito}
      testo={c.pillola}
      segno={segnoDi(c.esito)}
      dimensione="piccola"
      allinea="flex-start"
    />
  )
  const filtri = n.filters.map((f) => (
    <span key={f.name} className="al-c-riepilogo__riga-7">
      <i className={`al-c-riepilogo__tondo-3 ${VARIANTE[f.passband] ?? "as-filtro--ignoto"}`} />
      <b className="al-c-riepilogo__testo-9">{f.name}</b>
      <span className="al-c-riepilogo__testo-3">{numero(f.frames)}</span>
    </span>
  ))
  return (
    <Carta
      formato={formato}
      etichetta={t("window.summary")}
      colonne={7}
      ritardo={0}
      padding={L.pad}
      gap={16}
    >
      <div className="al-c-riepilogo__riga-1">
        <span className="al-c-riepilogo__riga-3">
          <Tondo etichetta={t("nights.prev")} segno={"\u2039"} on={onPrima} />
          <Tondo etichetta={t("nights.next")} segno={"\u203A"} on={onDopo} />
        </span>
        <span className="al-c-riepilogo__riga-4">
          <span className="al-c-riepilogo__pillola-1">{n.site}</span>
          <a
            className="al-c-riepilogo__tondo-2"
            href="#"
            onClick={gesto(onChiudi)}
            aria-label={t("ui.close")}
            style={{ width: L.nav, height: L.nav }}
          >
            {t("ui.close.sign")}
          </a>
        </span>
      </div>
      <div className="al-c-riepilogo__colonna-1">
        <span className="al-c-riepilogo__testo-1">{t("window.above")}</span>
        <span className="al-c-riepilogo__riga-5">
          <b className="al-c-riepilogo__testo-2" style={{ fontSize: L.tfs }}>
            {dataLunga(n.night_date)}
          </b>
        </span>
        <span className="al-c-riepilogo__testo-4">{periodo}</span>
      </div>
      {tel ? (
        <div className="al-c-riepilogo__colonna-3">
          <div className="al-c-riepilogo__griglia-1">
            <span className="al-c-riepilogo__colonna-4">
              <span className="al-c-riepilogo__testo-7">{grande}</span>
              <span className="al-c-riepilogo__blocco-3">{sotto}</span>
            </span>
            {kpi.map((k) => (
              <span key={k.l} className="al-c-riepilogo__colonna-5">
                <span className="al-c-riepilogo__testo-7">{k.v}</span>
                <span className="al-c-riepilogo__blocco-3">{k.l}</span>
              </span>
            ))}
          </div>
          <div className="al-c-riepilogo__riga-4">
            <span className="al-c-riepilogo__testo-8">{t("window.sky.phone")}</span>
            {esito}
            {filtri}
          </div>
        </div>
      ) : (
        <div className="al-c-riepilogo__riga-8">
          <span className="al-c-riepilogo__testo-10" style={{ fontSize: L.bfs }}>
            {grande}
          </span>
          <span className="al-c-riepilogo__colonna-6">
            <span className="al-c-riepilogo__testo-11">
              {conOre ? t("window.integration") : ""}
            </span>
            <span className="al-c-riepilogo__testo-12">{sotto}</span>
          </span>
          {kpi.map((k) => (
            <span key={k.l} className="al-c-riepilogo__colonna-7">
              <span className="al-c-riepilogo__testo-13">{k.v}</span>
              <span className="al-c-riepilogo__testo-8">{k.l}</span>
            </span>
          ))}
          <span className="al-c-riepilogo__colonna-8">
            {esito}
            <span className="al-c-riepilogo__testo-8">{t("window.sky")}</span>
          </span>
          <span className="al-c-riepilogo__riga-9" style={{ marginLeft: "auto" }}>
            {filtri}
          </span>
        </div>
      )}
    </Carta>
  )
}

// Le icone dei pezzi, le stesse della tavola di Attrezzatura (`ICR`, Riepilogo:171).
const ICONE = {
  ottica:
    "M2.8 11.2l12.6-4.4 1.4 4-12.6 4.4zM15.4 6.8l3.6-1.2 1.9 5.3-3.6 1.3M2.4 11.4l-.6.2.9 2.6.6-.2M9 13.6l-2.6 7.2M10.6 13l3 7.8M5.6 20.8h9",
  riduttore:
    "M12 3.5c2.6 2.4 2.6 14.6 0 17-2.6-2.4-2.6-14.6 0-17zM4 8.5h5M4 15.5h5M15 8.5h5M15 15.5h5M4 8.5v7M20 8.5v7",
  ruota:
    "M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0M10 6.6a2 2 0 1 0 4 0a2 2 0 1 0 -4 0M15.1 10.3a2 2 0 1 0 4 0a2 2 0 1 0 -4 0M13.2 16.4a2 2 0 1 0 4 0a2 2 0 1 0 -4 0M6.8 16.4a2 2 0 1 0 4 0a2 2 0 1 0 -4 0M4.9 10.3a2 2 0 1 0 4 0a2 2 0 1 0 -4 0M11.2 12a0.8 0.8 0 1 0 1.6 0a0.8 0.8 0 1 0 -1.6 0",
  camera:
    "M3.5 12a8.5 8.5 0 1 0 17 0a8.5 8.5 0 1 0 -17 0M6 12a6 6 0 1 0 12 0a6 6 0 1 0 -12 0M9.9 9.8h4.2a0.5 0.5 0 0 1 0.5 0.5v3.4a0.5 0.5 0 0 1 -0.5 0.5h-4.2a0.5 0.5 0 0 1 -0.5 -0.5v-3.4a0.5 0.5 0 0 1 0.5 -0.5zM12 1.8v1.7M12 20.5v1.7",
  montatura:
    "M12 21.5V15M6.5 21.5L12 15l5.5 6.5M10.2 8.5h3.6a1.2 1.2 0 0 1 1.2 1.2v4.1a1.2 1.2 0 0 1 -1.2 1.2h-3.6a1.2 1.2 0 0 1 -1.2 -1.2v-4.1a1.2 1.2 0 0 1 1.2 -1.2zM15 11.5l4.8-6.3M9 12l-4 4.4M2.7 17.3a1.5 1.5 0 1 0 3 0a1.5 1.5 0 1 0 -3 0",
  focheggiatore:
    "M4.6 7h7.3a1.6 1.6 0 0 1 1.6 1.6v6.8a1.6 1.6 0 0 1 -1.6 1.6h-7.3a1.6 1.6 0 0 1 -1.6 -1.6v-6.8a1.6 1.6 0 0 1 1.6 -1.6zM5.8 12a2.4 2.4 0 1 0 4.8 0a2.4 2.4 0 1 0 -4.8 0M13.5 10h3M13.5 14h3M16.4 12a2.6 2.6 0 1 0 5.2 0a2.6 2.6 0 1 0 -5.2 0M19 8.4v1M19 14.6v1M15.4 12h1M21.6 12h1",
  guida:
    "M3 11.5l9.4-3.3 1.1 3.1-9.4 3.3zM12.4 8.2l2.6-.9 1.4 4-2.6.9M14.3 17.5a3.2 3.2 0 1 0 6.4 0a3.2 3.2 0 1 0 -6.4 0M17.5 13v1.4M17.5 20.6V22M13 17.5h1.4M20.6 17.5H22",
  programma:
    "M5 4.5h14a2 2 0 0 1 2 2v11a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-11a2 2 0 0 1 2 -2zM3 8.5h18M6.5 15.5l2.5-3 2 2 3-4 3.5 5",
  campo: "M3 6h18v12H3zM3 10h18M9 6v12",
}

type Parte = Setup["parts"][number]["kind"]
// L'ordine e l'icona dei pezzi come la tavola (`dati.js`, `corredi`); i filtri stanno nella testa.
const PEZZI: { kind: Parte; nome: Chiave; icona: keyof typeof ICONE }[] = [
  { kind: "reducer", nome: "review.kind.reducer", icona: "riduttore" },
  { kind: "filter_wheel", nome: "review.kind.filter_wheel", icona: "ruota" },
  { kind: "spacer", nome: "review.kind.spacer", icona: "campo" },
  { kind: "mount", nome: "review.kind.mount", icona: "montatura" },
  { kind: "focuser", nome: "review.kind.focuser", icona: "focheggiatore" },
  { kind: "guide_scope", nome: "review.kind.guide_scope", icona: "guida" },
  { kind: "guide_camera", nome: "review.kind.guide_camera", icona: "guida" },
  { kind: "oag", nome: "review.kind.oag", icona: "guida" },
  { kind: "software", nome: "gear.part.software", icona: "programma" },
]
// Chiusa, la carta mostra solo questi (tavola v56.5, `CORTE`).
const CORTE = new Set<string>(["ottica", "camera", "mount", "campo"])

interface RigaSetup {
  k: string
  l: string
  v: string
  icona: keyof typeof ICONE
}

function righe(s: Setup): RigaSetup[] {
  const r: RigaSetup[] = []
  if (s.optics)
    r.push({
      k: "ottica",
      l: t("review.kind.optics"),
      v: s.focal_mm
        ? t("window.rig.optics.focal", { ottica: s.optics, mm: numero(s.focal_mm) })
        : s.optics,
      icona: "ottica",
    })
  // the key is the kind, not the icon: a spacer borrows the field's icon, not its place
  for (const p of PEZZI.slice(0, 3))
    for (const x of s.parts.filter((q) => q.kind === p.kind))
      r.push({ k: p.kind, l: t(p.nome), v: x.name, icona: p.icona })
  if (s.camera) r.push({ k: "camera", l: t("review.kind.camera"), v: s.camera, icona: "camera" })
  for (const p of PEZZI.slice(3))
    for (const x of s.parts.filter((q) => q.kind === p.kind))
      r.push({ k: p.kind, l: t(p.nome), v: x.name, icona: p.icona })
  if (s.width_deg != null && s.height_deg != null && s.scale_arcsec_px != null) {
    r.push({
      k: "campo",
      l: t("window.rig.field"),
      v: t("window.rig.field.value", {
        w: decimali(s.width_deg, 1),
        h: decimali(s.height_deg, 1),
        s: decimali(s.scale_arcsec_px, 2),
      }),
      icona: "campo",
    })
  }
  return r
}

function Setups({ setups, formato }: { setups: Setup[]; formato: Formato }) {
  const [aperti, setAperti] = useState<Record<number, boolean>>({})
  if (!setups.length) return null
  const titolo =
    setups.length === 1
      ? t("window.rig")
      : setups.length === 2
        ? t("window.rigs.two")
        : t("window.rigs", { n: setups.length })
  return (
    <Carta
      formato={formato}
      etichetta={t("window.rig")}
      colonne={5}
      ritardo={30}
      padding={MISURE[formato].pad}
      gap={12}
    >
      <span className="al-c-riepilogo__riga-13" style={{ alignItems: "center" }}>
        <span className="al-c-riepilogo__testo-14">{titolo}</span>
        <Link
          className="al-c-riepilogo__tondo-1"
          to="/attrezzatura"
          aria-label={t("window.rig.gear")}
          title={t("window.rig.gear.title")}
          style={{ width: 44, height: 44, marginLeft: "auto", flex: "none" }}
        >
          {"\u2197"}
        </Link>
      </span>
      {setups.map((s) => {
        const aperto = !!aperti[s.id]
        const tutte = righe(s)
        const viste = aperto ? tutte : tutte.filter((x) => CORTE.has(x.k))
        const ore = s.integration_s > 0 ? oreEMinuti(s.integration_s) : t("window.untimed")
        return (
          <div key={s.id} className="al-c-riepilogo__colonna-15">
            <span className="al-c-riepilogo__colonna-6">
              <b className="al-c-riepilogo__testo-24">
                {s.name ??
                  t("gear.rig", {
                    ottica: s.optics ?? t("gear.rig.noOptics"),
                    camera: s.camera ?? t("gear.rig.noCamera"),
                  })}
              </b>
              <span className="al-c-riepilogo__testo-8">
                {t("window.rig.use", { frame: t("window.frames", { n: numero(s.frames) }), ore })}
              </span>
            </span>
            {viste.map((x) => (
              <span
                key={`${x.k}:${x.v}`}
                style={{ display: "flex", gap: 10, alignItems: "flex-start", minWidth: 0 }}
              >
                <span
                  aria-hidden="true"
                  style={{
                    flex: "none",
                    width: 32,
                    height: 32,
                    borderRadius: "50%",
                    background: "var(--carta-2)",
                    display: "grid",
                    placeItems: "center",
                    color: "var(--tenue)",
                  }}
                >
                  <svg
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d={ICONE[x.icona]} />
                  </svg>
                </span>
                <span style={{ display: "flex", flexDirection: "column", gap: 1, minWidth: 0 }}>
                  <span className="al-c-riepilogo__testo-3">{x.l}</span>
                  <span style={{ textWrap: "pretty" }}>{x.v}</span>
                </span>
              </span>
            ))}
            {tutte.length > viste.length || aperto ? (
              <a
                className="al-bottone al-bottone--testo al-bottone--piccolo al-bottone--a-filo"
                style={{ alignSelf: "flex-start", minHeight: formato === "telefono" ? 44 : 34 }}
                href="#"
                onClick={gesto(() => setAperti({ ...aperti, [s.id]: !aperto }))}
                aria-expanded={aperto ? "true" : "false"}
              >
                {t(aperto ? "window.rig.fewer" : "window.rig.all")}{" "}
                <span aria-hidden="true">{aperto ? "\u25B4" : "\u25BE"}</span>
              </a>
            ) : null}
          </div>
        )
      })}
    </Carta>
  )
}

function distanza(f: components["schemas"]["ObjectFacts"]): string {
  if (!f.distance) return t("window.fact.distance.none")
  return t(f.distance.unit === "ly" ? "window.fact.ly" : "window.fact.mly", {
    n: numero(f.distance.value),
  })
}

function Oggetti({ d, formato }: { d: Dettaglio; formato: Formato }) {
  const fatti = new Map(d.objects.map((f) => [f.key, f]))
  return (
    <Carta
      formato={formato}
      etichetta={t("window.objects.title")}
      colonne={12}
      ritardo={60}
      padding={MISURE[formato].pad}
      gap={14}
    >
      <span className="al-c-riepilogo__riga-10">
        <span className="al-c-riepilogo__testo-14">{t("window.objects.title")}</span>
        <span className="al-c-riepilogo__testo-8">{t("window.objects.sub")}</span>
      </span>
      <div className="al-c-riepilogo__griglia-3">
        {d.night.objects.map((o) => {
          const f = fatti.get(o.key)
          const dentro =
            !!f && (f.type_code !== null || f.constellation !== null || f.distance !== null)
          const tipo = f && tipoDi(f)
          const dati =
            dentro && f
              ? [
                  { l: t("window.fact.type"), v: tipo ? t(tipo) : "\u2014" },
                  {
                    l: t("window.fact.constellation"),
                    v: f.constellation ? costellazione(f.constellation) : "\u2014",
                  },
                  { l: t("window.fact.distance"), v: distanza(f) },
                  {
                    l: t("window.fact.extent"),
                    v:
                      f.extent_ly != null
                        ? t("window.fact.extent.value", { n: numero(f.extent_ly) })
                        : t("window.fact.extent.none"),
                  },
                ]
              : []
          const nome = !dentro ? t("window.objects.outside") : (f?.common_name ?? "")
          return (
            <span key={o.key} className="al-c-riepilogo__colonna-10">
              <span className="al-c-riepilogo__riga-11">
                <span className="al-c-riepilogo__colonna-11">
                  <b className="al-c-riepilogo__testo-17">{o.name ?? o.key}</b>
                  {nome && <span className="al-c-riepilogo__testo-12">{nome}</span>}
                </span>
                <span style={{ display: "flex", alignItems: "center", gap: 8, flex: "none" }}>
                  <span className="al-c-riepilogo__testo-18">
                    {o.integration_s > 0
                      ? oreEMinuti(o.integration_s)
                      : t("window.frames", { n: numero(o.frames) })}
                  </span>
                </span>
              </span>
              {dati.length > 0 && (
                <span className="al-c-riepilogo__griglia-4">
                  {dati.map((x) => (
                    <span key={x.l} style={{ display: "contents" }}>
                      <span className="al-c-riepilogo__testo-3">{x.l}</span>
                      <span className="al-c-riepilogo__testo-19">{x.v}</span>
                    </span>
                  ))}
                </span>
              )}
            </span>
          )
        })}
      </div>
    </Carta>
  )
}
