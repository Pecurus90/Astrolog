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
import { ICONE } from "./iconeDeiPezzi"

type Setup = components["schemas"]["NightRig"]

// v77: sizes live in the sheet under data-formato; only the Scheletro gap stays here
export const MISURE = {
  desktop: { gap: "16px" },
  telefono: { gap: "12px" },
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
      >
        <div
          ref={pannello}
          tabIndex={-1}
          onKeyDown={trattieni}
          className="al-c-finestra-riepilogo__blocco-3"
          data-an="pannello"
        >
          {/* the summary root: the sheet's phone rules hang on its data-formato (display: contents) */}
          <div className="al-c-riepilogo__blocco-1" data-formato={formato}>
            {children}
          </div>
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
      className="al-c-riepilogo__tondo-1 al-c-riepilogo__freccia"
      href="#"
      onClick={gesto(on)}
      aria-label={etichetta}
      aria-disabled={on ? undefined : "true"}
    >
      {segno}
    </a>
  )
}

/** La riga in cima: le frecce a sinistra, le pillole dei siti e la x a destra. */
export function RigaDiTesta({
  siti,
  prima,
  dopo,
  onChiudi,
  onPrima,
  onDopo,
}: {
  siti: string[]
  prima: Chiave
  dopo: Chiave
  onChiudi: () => void
  onPrima?: (() => void) | undefined
  onDopo?: (() => void) | undefined
}) {
  return (
    <div className="al-c-riepilogo__riga-1">
      <span className="al-c-riepilogo__riga-3">
        <Tondo etichetta={t(prima)} segno={"\u2039"} on={onPrima} />
        <Tondo etichetta={t(dopo)} segno={"\u203A"} on={onDopo} />
      </span>
      <span className="al-c-riepilogo__testa-destra">
        {siti.map((s) => (
          <span key={s} className="al-c-riepilogo__pillola-1" title={s}>
            {s}
          </span>
        ))}
        <Croce onChiudi={onChiudi} />
      </span>
    </div>
  )
}

function Croce({ onChiudi }: { onChiudi: () => void }) {
  return (
    <a
      className="al-c-riepilogo__tondo-2"
      href="#"
      onClick={gesto(onChiudi)}
      aria-label={t("ui.close")}
    >
      {t("ui.close.sign")}
    </a>
  )
}

/** La x sopra caricamento, errore e non trovato: la finestra si chiude anche senza dati. */
export function CroceDegliStati({ onChiudi }: { onChiudi: () => void }) {
  return (
    <div className="al-c-riepilogo__testa-stato">
      <Croce onChiudi={onChiudi} />
    </div>
  )
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
    <Carta formato={formato} etichetta={t("window.rig")} colonne={5} ritardo={30} gap={12}>
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
                className="al-bottone al-bottone--testo al-bottone--piccolo al-bottone--a-filo al-c-riepilogo__strumenti"
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

/** I numeri della testa: ore (o frame), mediane, cielo della notte se c'e', filtri. Il telefono li
 *  mette in griglia, il desktop in riga. */
export function NumeriInTesta({
  formato,
  grande,
  sotto,
  conOre,
  kpi,
  esito,
  filtri,
}: {
  formato: Formato
  grande: string
  sotto: string
  conOre: boolean
  kpi: { v: string; l: string }[]
  esito?: ReactNode
  filtri: ReactNode
}) {
  if (formato === "telefono")
    return (
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
          {esito && <span className="al-c-riepilogo__testo-8">{t("window.sky.phone")}</span>}
          {esito}
          {filtri}
        </div>
      </div>
    )
  return (
    <div className="al-c-riepilogo__riga-8">
      <span className="al-c-riepilogo__testo-10">{grande}</span>
      <span className="al-c-riepilogo__colonna-6">
        <span className="al-c-riepilogo__testo-11">{conOre ? t("window.integration") : ""}</span>
        <span className="al-c-riepilogo__testo-12">{sotto}</span>
      </span>
      {kpi.map((k) => (
        <span key={k.l} className="al-c-riepilogo__colonna-7">
          <span className="al-c-riepilogo__testo-13">{k.v}</span>
          <span className="al-c-riepilogo__testo-8">{k.l}</span>
        </span>
      ))}
      {esito && (
        <span className="al-c-riepilogo__colonna-8">
          {esito}
          <span className="al-c-riepilogo__testo-8">{t("window.sky")}</span>
        </span>
      )}
      <span className="al-c-riepilogo__riga-9" style={{ marginLeft: "auto" }}>
        {filtri}
      </span>
    </div>
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
