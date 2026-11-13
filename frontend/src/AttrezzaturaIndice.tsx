import type { CSSProperties } from "react"

import { gesto } from "./componenti/gesto"
import type { Formato } from "./componenti/Tema"
import type { components } from "./api/schema"
import { type Chiave, numero, oreEMinuti, t } from "./i18n"
import { ICONE, type Icona } from "./iconeDeiPezzi"

type Schema = components["schemas"]
type Pagina = Schema["GearList"]
type Pezzo = Schema["InstrumentOnPage"]

/** What the detail shows: a rig by id, or a group by kind (`filter` for the filters). */
export type Scelta = { setup: number } | { gruppo: Gruppo }
export type Gruppo = Pezzo["kind"] | "filter"

// [T] Attrezzatura.dc.html `GRUPPI` (426) and `ICT` (423): order, title and icon of each group
export const GRUPPI: { kind: Gruppo; titolo: Chiave; icona: Icona }[] = [
  { kind: "optics", titolo: "gear.kind.optics", icona: "ottica" },
  { kind: "camera", titolo: "gear.kind.camera", icona: "camera" },
  { kind: "mount", titolo: "gear.kind.mount", icona: "montatura" },
  { kind: "reducer", titolo: "gear.kind.reducer", icona: "riduttore" },
  { kind: "filter_wheel", titolo: "gear.kind.filter_wheel", icona: "ruota" },
  { kind: "guide_scope", titolo: "gear.kind.guide_scope", icona: "guida" },
  { kind: "oag", titolo: "gear.kind.oag", icona: "oag" },
  { kind: "guide_camera", titolo: "gear.kind.guide_camera", icona: "camguida" },
  { kind: "focuser", titolo: "gear.kind.focuser", icona: "focheggiatore" },
  { kind: "spacer", titolo: "gear.kind.spacer", icona: "dist" },
  { kind: "filter", titolo: "gear.filters", icona: "filtro" },
]

/** The groups that have something, in board order; an empty group is not drawn. */
export function gruppiDi(
  pagina: Pagina,
): { kind: Gruppo; titolo: Chiave; icona: Icona; quanti: number }[] {
  return GRUPPI.map((g) => ({
    ...g,
    quanti:
      g.kind === "filter"
        ? pagina.filters.length
        : pagina.instruments.filter((p) => p.kind === g.kind).length,
  })).filter((g) => g.quanti > 0)
}

/** The first thing the detail shows: the most used rig, else the first group (board `preset`). */
export function primaScelta(pagina: Pagina): Scelta | null {
  const rig = pagina.rigs[0]
  if (rig) return { setup: rig.id }
  const g = gruppiDi(pagina)[0]
  return g ? { gruppo: g.kind } : null
}

/** Is `scelta` still on the page (a rig merged away, a group emptied)? */
export function esiste(pagina: Pagina, scelta: Scelta): boolean {
  if ("setup" in scelta) return pagina.rigs.some((r) => r.id === scelta.setup)
  return gruppiDi(pagina).some((g) => g.kind === scelta.gruppo)
}

// [T] Attrezzatura.dc.html `L` (210-213): the index measures per format
const MISURE: Record<
  Formato,
  { stacco: string; angolo: string; colonne: string; alta: string; dentro: string }
> = {
  desktop: {
    stacco: "16px",
    angolo: "28px",
    colonne: "repeat(auto-fill,minmax(210px,1fr))",
    alta: "220px",
    dentro: "22px",
  },
  telefono: {
    stacco: "12px",
    angolo: "24px",
    colonne: "repeat(2,minmax(0,1fr))",
    alta: "200px",
    dentro: "16px",
  },
}

const DA_INDICARE = "○" // glifo-ok: the board's "to say" sign (riga-11)

// [T] `indC.sh` (388): the chosen card has the accent ring, not a full background (v54)
const anello = (su: boolean) => (su ? "inset 0 0 0 2px var(--accento)" : "none")

/**
 * The index of the Gear page (board v82): *Setup* as cards, with hours, focal, bar and the ten
 * parts as ticks, and *Componenti* as pills, one per group. On the phone nothing is marked chosen:
 * the detail opens full page.
 */
export function Indice({
  pagina,
  scelta,
  formato,
  onScegli,
}: {
  pagina: Pagina
  scelta: Scelta | null
  formato: Formato
  onScegli: (s: Scelta) => void
}) {
  const tel = formato === "telefono"
  const m = MISURE[formato]
  const gruppi = gruppiDi(pagina)
  const suSetup = (id: number) =>
    !tel && scelta !== null && "setup" in scelta && scelta.setup === id
  const suGruppo = (k: Gruppo) =>
    !tel && scelta !== null && "gruppo" in scelta && scelta.gruppo === k
  return (
    <nav className="al-attr__colonna-1" aria-label={t("gear.index")} style={{ gap: m.stacco }}>
      {pagina.rigs.length > 0 && (
        <section className="al-attr__colonna-2" aria-labelledby="ix-cor">
          <header className="al-attr__riga-4">
            <h2 className="al-attr__testo-2" id="ix-cor">
              {t("gear.rigs")}
            </h2>
            <span className="al-attr__testo-3">{numero(pagina.rigs.length)}</span>
          </header>
          <ul
            className="al-attr__centro-1"
            style={{ gridTemplateColumns: m.colonne, gap: m.stacco }}
          >
            {pagina.rigs.map((r) => (
              <li key={r.id} className="al-attr__riga-5">
                <CartaSetup
                  setup={r}
                  su={suSetup(r.id)}
                  stile={{ minHeight: m.alta, padding: m.dentro, borderRadius: m.angolo }}
                  onScegli={() => onScegli({ setup: r.id })}
                />
              </li>
            ))}
          </ul>
        </section>
      )}
      {gruppi.length > 0 && (
        <section className="al-attr__colonna-2" aria-labelledby="ix-comp">
          <header className="al-attr__riga-4">
            <h2 className="al-attr__testo-2" id="ix-comp">
              {t("gear.components")}
            </h2>
            <span className="al-attr__testo-3">
              {numero(pagina.instruments.length + pagina.filters.length)}
            </span>
          </header>
          <ul className="al-attr__riga-12">
            {gruppi.map((g) => {
              const su = suGruppo(g.kind)
              return (
                <li key={g.kind} className="al-attr__riga-5">
                  <a
                    className="al-attr__riga-13"
                    href="#"
                    onClick={gesto(() => onScegli({ gruppo: g.kind }))}
                    aria-current={su ? "true" : undefined}
                    style={{
                      background: "var(--carta)",
                      color: "var(--testo)",
                      boxShadow: anello(su),
                    }}
                  >
                    <span
                      className="al-attr__tondo-3"
                      aria-hidden="true"
                      style={{ background: "var(--carta-2)" }}
                    >
                      <svg
                        className="al-attr__grafico-1"
                        aria-hidden="true"
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d={ICONE[g.icona]} />
                      </svg>
                    </span>
                    <span className="al-attr__testo-6" style={{ fontWeight: su ? 600 : 500 }}>
                      {t(g.titolo)}
                    </span>
                    <span className="al-attr__testo-7" style={{ color: "var(--tenue)" }}>
                      {numero(g.quanti)}
                    </span>
                  </a>
                </li>
              )
            })}
          </ul>
        </section>
      )}
    </nav>
  )
}

function CartaSetup({
  setup: r,
  su,
  stile,
  onScegli,
}: {
  setup: Schema["RigOnPage"]
  su: boolean
  stile: CSSProperties
  onScegli: () => void
}) {
  const contato = r.counted && r.integration_s !== null
  // the API forms the title; null only for a rig with neither piece, which today never exists
  const titolo = r.title ?? ""
  return (
    <a
      className="al-attr__colonna-3"
      href="#"
      onClick={gesto(onScegli)}
      aria-current={su ? "true" : undefined}
      style={{ ...stile, background: "var(--carta)", color: "var(--testo)", boxShadow: anello(su) }}
    >
      <span className="al-attr__colonna-4">
        <span className="al-attr__blocco-4" title={titolo}>
          {titolo}
        </span>
        <ul className="al-attr__colonna-5">
          {[r.optics ?? t("gear.rig.noOptics"), r.camera ?? t("gear.rig.noCamera")].map((x, i) => (
            <li key={i} className="al-attr__riga-6" title={x} style={{ color: "var(--tenue)" }}>
              <span className="al-attr__tondo-2" aria-hidden="true" />
              <span className="al-attr__blocco-5">{x}</span>
            </li>
          ))}
        </ul>
      </span>
      <span className="al-attr__blocco-2" />
      <span className="al-attr__riga-7">
        <span className="al-attr__testo-4" style={{ fontSize: contato ? "34px" : "14px" }}>
          {contato ? oreEMinuti(r.integration_s ?? 0) : t("gear.counting")}
        </span>
        {r.focal_mm !== null && (
          <span className="al-attr__testo-5" style={{ color: "var(--tenue)" }}>
            {t("gear.focal", { mm: numero(r.focal_mm) })}
          </span>
        )}
      </span>
      {contato && r.bar_pct !== null && (
        <span
          className="al-attr__riga-8"
          aria-hidden="true"
          style={{ background: "var(--traccia)" }}
        >
          <span
            className="al-attr__blocco-6"
            data-an="barra"
            style={{ width: `${r.bar_pct}%`, background: "var(--accento)" }}
          />
        </span>
      )}
      <span className="al-attr__riga-9">
        <span className="al-attr__riga-10" aria-hidden="true">
          {r.slots.map((s) => (
            <span
              key={s.kind}
              className="al-attr__blocco-7"
              data-pieno={s.filled ? "true" : "false"}
              style={
                s.filled
                  ? { background: "var(--accento)", border: "0" }
                  : { background: "transparent", border: "1.5px solid var(--tenue)" }
              }
            />
          ))}
        </span>
        {r.slots_missing > 0 && (
          <span
            className="al-attr__riga-11"
            style={{ boxShadow: "inset 0 0 0 1.5px var(--tenue)" }}
          >
            <span aria-hidden="true">{DA_INDICARE}</span>
            {t("gear.slotsMissing", { n: numero(r.slots_missing) })}
          </span>
        )}
      </span>
    </a>
  )
}
