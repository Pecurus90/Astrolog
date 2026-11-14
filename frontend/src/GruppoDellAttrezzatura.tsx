import type { CSSProperties, ReactNode } from "react"

import { GRUPPI, type Gruppo } from "./AttrezzaturaIndice"
import { gesto } from "./componenti/gesto"
import type { Formato } from "./componenti/Tema"
import { ICONE } from "./iconeDeiPezzi"
import { MISURE_DETTAGLIO } from "./misureDelSetup"
import { pallinoDi } from "./MisureDati"
import { ModuloDelFiltro } from "./ModuloDelFiltro"
import { ModuloDelPezzo } from "./ModuloDelPezzo"
import { type Voce, vociDellaScheda } from "./vociDellaScheda"
import type { components } from "./api/schema"
import { type Chiave, alPiu, numero, oreEMinuti, t } from "./i18n"

type Pagina = components["schemas"]["GearList"]
type Pezzo = components["schemas"]["InstrumentOnPage"]
type Filtro = components["schemas"]["FilterOnPage"]

/** "Nessun setup lo porta", per genere: l'aggettivo segue il pezzo. */
const SENZA_SETUP: Partial<Record<Pezzo["kind"], Chiave>> = {
  mount: "gear.noHours.mount",
  reducer: "gear.noHours.reducer",
  guide_scope: "gear.noHours.guide_scope",
  oag: "gear.noHours.oag",
  spacer: "gear.noHours.spacer",
}

// only a real band is shown as one: UNKNOWN, OSC, DUO_HAOIII are codes, not words
const BANDE_VERE = ["L", "R", "G", "B", "HA", "HB", "OIII", "SII"]

interface VoceConPallino extends Voce {
  pallino?: CSSProperties
}

/** The filter's card in one row: the bands with their colour, then its sheet (board `voce`). */
function vociDelFiltro(f: Filtro): VoceConPallino[] {
  // no band written: the one its name gives, as the board shows every filter with its band
  const nome = f.passband && BANDE_VERE.includes(f.passband) ? f.passband : null
  const scritte = f.bands.length || !nome ? f.bands : [{ band: nome, width_nm: null }]
  const voci: VoceConPallino[] = scritte.map((b) => ({
    v:
      b.width_nm === null
        ? t("gear.band.noWidth", { banda: b.band })
        : t("gear.band", { banda: b.band, nm: alPiu(b.width_nm, 2) }),
    calc: false,
    pallino: pallinoDi(b.band),
  }))
  const sp = (v: string) => voci.push({ v, calc: false })
  if (f.filter_size) sp(t(`gear.size.${f.filter_size}`))
  if (f.mounted !== null) sp(t(f.mounted ? "gear.spec.mounted" : "gear.spec.unmounted"))
  if (f.fast_optics) sp(t("gear.spec.fast"))
  if (f.thickness_mm !== null) sp(t("gear.spec.thickness", { mm: alPiu(f.thickness_mm, 2) }))
  return voci
}

/** How much it served (board `usoT`): hours with the bar, or why there are none. */
function Uso({ cosa, onMontatura }: { cosa: Pezzo | Filtro; onMontatura?: () => void }) {
  if (!cosa.counted)
    return (
      <Segno
        tondo={<span className="al-attr__tondo-16" aria-hidden="true" />}
        testo={t("gear.counting")}
      />
    )
  const perche = "no_hours" in cosa ? cosa.no_hours : null
  if (perche === "no_rig" && "kind" in cosa) {
    return (
      <>
        <Segno
          tondo={<span className="al-attr__tondo-18" aria-hidden="true" />}
          testo={t(SENZA_SETUP[cosa.kind] ?? "gear.noHours")}
        />
        {onMontatura && (
          <a
            href="#"
            role="button"
            onClick={gesto(onMontatura)}
            className="al-bottone al-bottone--testo al-bottone--a-filo al-bottone--sottolineato al-attr__blocco-9"
          >
            {t("gear.mount.select")}
          </a>
        )}
      </>
    )
  }
  // no frame yet is not an hour (board `ore: 'file'` for a piece written by hand)
  if (perche !== null || cosa.integration_s === null || cosa.frames === 0) {
    return (
      <Segno
        tondo={<span className="al-attr__tondo-17" aria-hidden="true" />}
        testo={t("gear.noHours")}
      />
    )
  }
  return (
    <>
      <span className="al-attr__testo-28">{oreEMinuti(cosa.integration_s)}</span>
      {cosa.bar_pct !== null && (
        <span className="al-attr__riga-33" aria-hidden="true">
          <span
            className="al-attr__riquadro-3"
            data-an="barra"
            style={{ width: `${cosa.bar_pct}%` }}
          />
        </span>
      )}
    </>
  )
}

function Segno({ tondo, testo }: { tondo: ReactNode; testo: string }) {
  return (
    <span className="al-attr__riga-34">
      {tondo}
      {testo}
    </span>
  )
}

/** One row of the group (board `grp.voci`): the sign, Modifica, name, card, use, and its form. */
function Riga({
  chiave,
  nome,
  sub,
  aMano,
  segno,
  voci,
  uso,
  aperto,
  cercato,
  formato,
  onApri,
  modulo,
}: {
  chiave: string
  nome: string
  sub: string
  aMano: boolean
  segno: ReactNode
  voci: VoceConPallino[]
  uso: ReactNode
  aperto: boolean
  cercato: string | null
  formato: Formato
  onApri: () => void
  modulo: ReactNode
}) {
  const m = MISURE_DETTAGLIO[formato]
  return (
    <li
      className="al-attr__colonna-24"
      data-an="riga"
      id={`pezzo-${chiave}`}
      aria-current={chiave === cercato ? "true" : undefined}
      style={{
        gridColumn: aperto ? "1 / -1" : "auto",
        boxShadow: aperto ? "inset 0 0 0 2px var(--accento)" : "none",
      }}
    >
      <span className="al-attr__riga-30">
        {segno}
        <span className="al-attr__blocco-2" />
        <a
          className="al-attr__riga-15"
          href="#"
          role="button"
          aria-expanded={aperto ? "true" : "false"}
          aria-label={t("gear.edit.label", { nome })}
          onClick={gesto(onApri)}
          style={{
            minHeight: m.bottone,
            background: aperto ? "var(--scelta)" : "var(--carta)",
            color: aperto ? "var(--scelta-testo)" : "var(--testo)",
            boxShadow: `inset 0 0 0 1.5px ${aperto ? "transparent" : "var(--linea)"}`,
          }}
        >
          {t("gear.write.edit")}
        </a>
      </span>
      <span className="al-attr__colonna-25">
        <span className="al-attr__testo-26">{nome}</span>
        {sub && <span className="al-attr__testo-14">{sub}</span>}
        {aMano && <span className="al-attr__pillola-1">{t("gear.declared")}</span>}
      </span>
      <span className="al-attr__riga-31">
        {voci.map((x) => (
          <span key={x.v} className="al-attr__riga-32">
            {x.pallino && (
              <span className="al-attr__tondo-15" aria-hidden="true" style={x.pallino} />
            )}
            <span
              className="al-attr__testo-27"
              style={{ textDecoration: x.calc ? "underline dotted" : "none" }}
            >
              {x.v}
            </span>
            {x.calc && <span className="al-attr__testo-16">{t("gear.rig.computed")}</span>}
          </span>
        ))}
      </span>
      <span className="al-attr__colonna-26">{uso}</span>
      {modulo}
    </li>
  )
}

const sottotitolo = (brand: string | null, model: string | null, nome: string) =>
  [brand, model && model !== nome ? model : null].filter(Boolean).join(" · ") // glifo-ok: board separator

/**
 * Il **gruppo di un tipo** nell'Attrezzatura (tavola v82 `grp`): ogni pezzo con la scheda intera,
 * le ore con la barra o perche' mancano, "inserito manualmente", e il suo modulo che si apre nella
 * riga; un modulo aperto alla volta.
 */
export function GruppoDellAttrezzatura({
  pagina,
  gruppo,
  formato,
  cercato,
  aperto,
  scansione,
  onApri,
  onMontatura,
}: {
  pagina: Pagina
  gruppo: Gruppo
  formato: Formato
  cercato: string | null
  /** The open row (`strumento-12`, `filtro-3`), null for none. */
  aperto: string | null
  scansione: boolean
  onApri: (riga: string | null) => void
  /** "Seleziona montatura": the rig to choose it on, and the mount. */
  onMontatura: (setup: number, montatura: number) => void
}) {
  const m = MISURE_DETTAGLIO[formato]
  const g = GRUPPI.find((x) => x.kind === gruppo)
  const chiudi = () => onApri(null)
  const apri = (k: string) => () => onApri(aperto === k ? null : k)
  const righe =
    gruppo === "filter"
      ? pagina.filters.map((f) => {
          const k = `filtro-${f.id}`
          return (
            <Riga
              key={k}
              chiave={k}
              nome={f.name}
              sub={sottotitolo(f.brand, f.model, f.name)}
              aMano={false}
              segno={
                <span
                  className="al-attr__tondo-13"
                  aria-hidden="true"
                  style={pallinoDi(f.passband ?? undefined)}
                />
              }
              voci={vociDelFiltro(f)}
              uso={<Uso cosa={f} />}
              aperto={aperto === k}
              cercato={cercato}
              formato={formato}
              onApri={apri(k)}
              modulo={
                aperto === k && (
                  <ModuloDelFiltro
                    filtro={f}
                    pagina={pagina}
                    formato={formato}
                    scansione={scansione}
                    onChiudi={chiudi}
                  />
                )
              }
            />
          )
        })
      : pagina.instruments
          .filter((p) => p.kind === gruppo)
          .map((p) => {
            const k = `strumento-${p.id}`
            const setup = p.rig_for_mount
            return (
              <Riga
                key={k}
                chiave={k}
                nome={p.name}
                sub={sottotitolo(p.brand, p.model, p.name)}
                aMano={!p.detected}
                segno={
                  <span className="al-attr__tondo-14" aria-hidden="true">
                    <svg
                      className="al-attr__grafico-1"
                      aria-hidden="true"
                      width="22"
                      height="22"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      {g && <path d={ICONE[g.icona]} />}
                    </svg>
                  </span>
                }
                voci={vociDellaScheda(p)}
                uso={
                  <Uso
                    cosa={p}
                    {...(setup !== null ? { onMontatura: () => onMontatura(setup, p.id) } : {})}
                  />
                }
                aperto={aperto === k}
                cercato={cercato}
                formato={formato}
                onApri={apri(k)}
                modulo={
                  aperto === k && (
                    <ModuloDelPezzo
                      pezzo={p}
                      pagina={pagina}
                      formato={formato}
                      scansione={scansione}
                      onChiudi={chiudi}
                    />
                  )
                }
              />
            )
          })
  return (
    <section
      className="al-attr__colonna-23"
      aria-labelledby="dt-grp"
      style={{ borderRadius: m.angolo, padding: m.dentro }}
    >
      <header className="al-attr__riga-29">
        <h2 className="al-attr__testo-24" id="dt-grp" style={{ fontSize: m.titolo }}>
          {t(g?.titolo ?? "gear.components")}
        </h2>
        <span className="al-attr__testo-25">{numero(righe.length)}</span>
      </header>
      <ul
        className="al-attr__centro-4"
        aria-label={t(g?.titolo ?? "gear.components")}
        style={{ gridTemplateColumns: m.voci }}
      >
        {righe}
      </ul>
    </section>
  )
}
