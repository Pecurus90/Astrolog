/**
 * I pezzi comuni al **Riepilogo** di una notte e di un oggetto (tavola v76,
 * `componenti/FinestraRiepilogo.dc.html` e `componenti/Riepilogo.dc.html`): la finestra sopra la
 * pagina, le misure per formato, lo scheletro, i tondi, la carta dei setup. Formattano e basta.
 */
import { type MouseEvent, type ReactNode, useState } from "react"
import { Link } from "react-router"

import type { components } from "./api/schema"
import { trattieni, useApertura } from "./componenti/Finestra"
import { gesto } from "./componenti/gesto"
import { Carta } from "./componenti/Carta"
import type { CartaScheletro } from "./componenti/Scheletro"
import { type Formato, useTema } from "./componenti/Tema"
import { varianteDi } from "./FiltriUsati"
import { type Chiave, decimali, numero, oreEMinuti, t } from "./i18n"

type Setup = components["schemas"]["NightRig"]

// Le misure della finestra per formato (tavola, `L` e `D`: inline anche li', brief a Design).
export const MISURE = {
  desktop: { gap: "16px", pad: "28px", tfs: "44px", sfs: "20px", bfs: "64px", nav: "44px" },
  telefono: { gap: "12px", pad: "20px", tfs: "30px", sfs: "16px", bfs: "48px", nav: "44px" },
}

export const SCHELETRO: CartaScheletro[] = [
  {
    h: "220px",
    pad: "24px",
    gap: "14px",
    blocchi: [t("window.loading"), { h: "44px", w: "60%" }, { flex: "1" }],
  },
  { h: "520px", pad: "24px", blocchi: [{ h: "100%" }] },
]

/** Larga 1180 sul desktop, pagina intera sul telefono; si chiude con x, Esc o fuori. */
export function FinestraRiepilogo({
  aria,
  formato,
  onChiudi,
  children,
}: {
  aria: string
  formato: Formato
  onChiudi: () => void
  children: ReactNode
}) {
  const { modo, accento } = useTema()
  const tel = formato === "telefono"
  const pannello = useApertura(onChiudi)
  const fuori = (e: MouseEvent) => {
    if (e.target === e.currentTarget) onChiudi()
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
        aria-label={aria}
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
          {children}
        </div>
      </div>
    </div>
  )
}

export function Tondo({
  etichetta,
  segno,
  on,
}: {
  etichetta: string
  segno: string
  on: (() => void) | undefined
}) {
  return (
    <a
      className="al-c-riepilogo__tondo-1"
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

/** La riga in cima: le frecce a sinistra, le pillole dei siti e la x a destra. */
export function RigaDiTesta({
  siti,
  formato,
  prima,
  dopo,
  onChiudi,
  onPrima,
  onDopo,
}: {
  siti: string[]
  formato: Formato
  prima: Chiave
  dopo: Chiave
  onChiudi: () => void
  onPrima?: (() => void) | undefined
  onDopo?: (() => void) | undefined
}) {
  const L = MISURE[formato]
  return (
    <div className="al-c-riepilogo__riga-1">
      <span className="al-c-riepilogo__riga-3">
        <Tondo etichetta={t(prima)} segno={"\u2039"} on={onPrima} />
        <Tondo etichetta={t(dopo)} segno={"\u203A"} on={onDopo} />
      </span>
      <span className="al-c-riepilogo__riga-4">
        {siti.map((s) => (
          <span key={s} className="al-c-riepilogo__pillola-1">
            {s}
          </span>
        ))}
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

// Spelled out up to nine, like the board's "Due setup".
const SETUP_IN_LETTERE: Chiave[] = [
  "window.rig",
  "window.rigs.two",
  "window.rigs.three",
  "window.rigs.four",
  "window.rigs.five",
  "window.rigs.six",
  "window.rigs.seven",
  "window.rigs.eight",
  "window.rigs.nine",
]

export function Setups({ setups, formato }: { setups: Setup[]; formato: Formato }) {
  const [aperti, setAperti] = useState<Record<number, boolean>>({})
  if (!setups.length) return null
  const lettere = SETUP_IN_LETTERE[setups.length - 1]
  const titolo = lettere ? t(lettere) : t("window.rigs", { n: setups.length })
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

/** Il catalogo sa dire qualcosa dell'oggetto: per la notte e per l'oggetto, una regola. */
export function inCatalogo(f: components["schemas"]["ObjectFacts"]): boolean {
  return f.type_code !== null || f.constellation !== null || f.distance !== null
}

/** I filtri della testa: tondo del colore, nome, frame. */
export function FiltriInTesta({ filtri }: { filtri: components["schemas"]["FilterUsed"][] }) {
  return filtri.map((f) => (
    <span key={f.name} className="al-c-riepilogo__riga-7">
      <i className={`al-c-riepilogo__tondo-3 ${varianteDi(f.passband)}`} />
      <b className="al-c-riepilogo__testo-9">{f.name}</b>
      <span className="al-c-riepilogo__testo-3">{numero(f.frames)}</span>
    </span>
  ))
}
