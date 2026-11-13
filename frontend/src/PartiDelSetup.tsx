import { useState } from "react"

import { gesto } from "./componenti/gesto"
import { CampoDelModulo, Modulo, TendinaDelModulo } from "./componenti/Modulo"
import { PillolaScelta } from "./componenti/PillolaScelta"
import type { Formato } from "./componenti/Tema"
import { MISURE_DETTAGLIO, nomeDelSetup } from "./misureDelSetup"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { maiuscola, numero, t } from "./i18n"
import { ICONE } from "./iconeDeiPezzi"
import { type Scritto, rifiutoDetto, useScrittura } from "./ModuloDelGesto"

type Schema = components["schemas"]
type Pagina = Schema["GearList"]
type Corredo = Schema["RigOnPage"]
type Pezzo = Schema["InstrumentOnPage"]
type Genere = Pezzo["kind"]

/** One of the ten parts of a rig (board v82 `PARTI`). */
export type Parte = Corredo["slots"][number]["kind"]
type Scelta = Schema["RigPart"]["kind"]
type Sceglibile =
  "filter_wheel" | "focuser" | "guide_camera" | "mount" | "reducer" | "guide_scope" | "oag"

const DA_INDICARE = "○" // glifo-ok: the board's "to say" sign (riga-23)
const APRI = "↗" // glifo-ok: the board's arrow to a detail

// [T] Attrezzatura.dc.html `PARTI`, `ICT`, `TPARTE` (423-427, 562): what each part holds and draws
const PARTI: Record<Parte, { icona: string; generi: Scelta[] }> = {
  optics: { icona: ICONE.ottica, generi: [] },
  camera: { icona: ICONE.camera, generi: [] },
  reducer: { icona: ICONE.riduttore, generi: ["reducer"] },
  filter_wheel: { icona: ICONE.ruota, generi: ["filter_wheel"] },
  spacer: { icona: ICONE.dist, generi: ["spacer"] },
  mount: { icona: ICONE.montatura, generi: ["mount"] },
  focuser: { icona: ICONE.focheggiatore, generi: ["focuser"] },
  guide: { icona: ICONE.guida, generi: ["guide_scope", "oag"] },
  guide_camera: { icona: ICONE.camguida, generi: ["guide_camera"] },
  software: { icona: ICONE.programma, generi: ["software"] },
}

// the board writes "(vuoto: dai file)" where the files can name the part (`vociParte`, 242)
const SENZA_DAI_FILE: Parte[] = ["reducer", "guide"]

interface Nome {
  n: string
  f: string
  vai: number | null
}

/** The names a part holds: the files' ones with their frames, the ones you chose said so. */
function nomiDi(r: Corredo, parte: Parte): Nome[] {
  if (parte === "optics") return r.optics ? [{ n: r.optics, f: "", vai: r.optics_id }] : []
  if (parte === "camera") return r.camera ? [{ n: r.camera, f: "", vai: r.camera_id }] : []
  return r.parts
    .filter((p) => PARTI[parte].generi.includes(p.kind))
    .map((p) => ({
      n: p.name,
      f: p.chosen
        ? t("gear.part.byHand")
        : p.frames
          ? t("gear.frames", { n: numero(p.frames) })
          : "",
      vai: p.kind === "software" ? null : p.id,
    }))
}

/**
 * Le **Parti** di un setup (tavola v82, 67-75): le dieci, ognuna coi pezzi che i file nominano o
 * che hai scelto, "da indicare" se vuota. Ogni pezzo si apre fra i componenti; "Seleziona" apre il
 * modulo nella riga. Il programma di ripresa lo dicono solo i file: non si seleziona.
 */
export function PartiDelSetup({
  pagina,
  setup: r,
  formato,
  aperto,
  onApri,
  onVai,
  onAggiungi,
}: {
  pagina: Pagina
  setup: Corredo
  formato: Formato
  aperto: Parte | null
  onApri: (p: Parte | null) => void
  onVai: (pezzo: number) => void
  onAggiungi: (genere: Genere | null) => void
}) {
  const m = MISURE_DETTAGLIO[formato]
  const tel = formato === "telefono"
  return (
    <section
      className="al-attr__colonna-11"
      aria-labelledby="dt-parti"
      style={{ borderRadius: m.angolo, padding: m.dentro }}
    >
      <header className="al-attr__riga-20">
        <h3 className="al-attr__testo-2" id="dt-parti">
          {t("gear.parts")}
        </h3>
        {r.slots_missing > 0 && (
          <span className="al-attr__riga-21">
            <span aria-hidden="true">{DA_INDICARE}</span>
            {t("gear.slotsMissing", { n: numero(r.slots_missing) })}
          </span>
        )}
      </header>
      <ul className="al-attr__centro-4" style={{ gridTemplateColumns: m.parti }}>
        {r.slots.map(({ kind: parte, filled }) => {
          const fisso = parte === "optics" || parte === "camera"
          const su = aperto === parte
          const vuoto = !filled
          const sceglibile = !fisso && parte !== "software"
          const etichetta = t(`gear.slot.${parte}`)
          return (
            <li
              key={parte}
              className="al-attr__colonna-12"
              data-parte={parte}
              data-an="riga"
              style={{
                gridColumn: su || (tel && fisso) ? "1 / -1" : fisso ? "span 2" : "auto",
                minHeight: m.alta,
                background: vuoto ? "transparent" : "var(--carta-2)",
                boxShadow: su
                  ? "inset 0 0 0 2px var(--accento)"
                  : vuoto
                    ? "inset 0 0 0 1.5px var(--linea)"
                    : "none",
              }}
            >
              <span className="al-attr__riga-22">
                <span
                  className="al-attr__tondo-6"
                  aria-hidden="true"
                  style={{
                    background: vuoto ? "transparent" : "var(--carta)",
                    border: vuoto ? "1.5px dashed var(--tenue)" : "0",
                  }}
                >
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
                    <path d={PARTI[parte].icona} />
                  </svg>
                </span>
                <span className="al-attr__testo-14">{etichetta}</span>
              </span>
              <span className="al-attr__colonna-9">
                {nomiDi(r, parte).map((x) => (
                  <span key={`${x.n}-${x.f}`} className="al-attr__colonna-13">
                    {x.vai !== null ? (
                      <a
                        className="al-attr__testo-15"
                        href="#"
                        onClick={gesto(() => onVai(x.vai ?? 0))}
                        aria-label={t("gear.part.open", { nome: x.n })}
                        style={{ fontSize: fisso ? "19px" : "15px" }}
                      >
                        {x.n}{" "}
                        <span className="al-attr__testo-16" aria-hidden="true">
                          {APRI}
                        </span>
                      </a>
                    ) : (
                      <span
                        className="al-attr__testo-15"
                        style={{ fontSize: fisso ? "19px" : "15px" }}
                      >
                        {x.n}
                      </span>
                    )}
                    {x.f && <span className="al-attr__testo-12">{x.f}</span>}
                  </span>
                ))}
                {vuoto && (
                  <span className="al-attr__riga-23">
                    <span aria-hidden="true">{DA_INDICARE}</span>
                    {t("gear.part.toSay")}
                  </span>
                )}
              </span>
              {sceglibile && (
                <a
                  className="al-attr__riga-24"
                  href="#"
                  role="button"
                  aria-expanded={su ? "true" : "false"}
                  aria-label={t("gear.part.select.label", { parte: etichetta })}
                  onClick={gesto(() => onApri(su ? null : parte))}
                  style={{
                    minHeight: m.bottone,
                    background: su || vuoto ? "var(--scelta)" : "var(--carta)",
                    color: su || vuoto ? "var(--scelta-testo)" : "var(--testo)",
                    boxShadow: `inset 0 0 0 1.5px ${su || vuoto ? "transparent" : "var(--linea)"}`,
                  }}
                >
                  {t("gear.part.select")}
                </a>
              )}
              {su && sceglibile && (
                <Seleziona
                  pagina={pagina}
                  setup={r}
                  parte={parte}
                  formato={formato}
                  onChiudi={() => onApri(null)}
                  onAggiungi={onAggiungi}
                />
              )}
            </li>
          )
        })}
      </ul>
    </section>
  )
}

/** The pieces you own that fit a part: a guide is a guide scope or an OAG. */
function vociDi(pagina: Pagina, parte: Parte): Pezzo[] {
  const generi: readonly string[] = PARTI[parte].generi
  return pagina.instruments.filter((p) => generi.includes(p.kind))
}

/** The pieces you chose for the part, by id. */
function sceltiDi(r: Corredo, parte: Parte): Schema["RigPart"][] {
  return r.parts.filter((p) => p.chosen && p.id !== null && PARTI[parte].generi.includes(p.kind))
}

function Seleziona({
  pagina,
  setup: r,
  parte,
  formato,
  onChiudi,
  onAggiungi,
}: {
  pagina: Pagina
  setup: Corredo
  parte: Parte
  formato: Formato
  onChiudi: () => void
  onAggiungi: (genere: Genere | null) => void
}) {
  const voci = vociDi(pagina, parte)
  const prima = sceltiDi(r, parte)
  const [scelti, setScelti] = useState<number[]>(prima.map((p) => p.id ?? 0))
  const cambiato = scelti.join(",") !== prima.map((p) => p.id).join(",")
  const scrivi = useScrittura(() => manda(r, parte, scelti, prima, voci), onChiudi)
  const etichetta = maiuscola(t(`gear.slot.${parte}`))
  const titolo = t("gear.part.title", { parte: etichetta, nome: nomeDelSetup(r) })
  const id = `setup-${r.id}-${parte}`
  if (voci.length === 0) {
    // nothing of that kind to choose: the way to write one (board `soloAnnulla`, 243)
    const genere: Genere | null = parte === "guide" ? null : (parte as Genere)
    return (
      <Modulo titolo={titolo} formato={formato} dentro salva={null} onAnnulla={onChiudi}>
        <CampoDelModulo id={id} etichetta="" largo>
          <a
            href="#"
            role="button"
            onClick={gesto(() => onAggiungi(genere))}
            className="al-bottone al-bottone--contorno al-c-modulo__blocco-5"
            style={{ minHeight: MISURE_DETTAGLIO[formato].bottone }}
          >
            <svg
              aria-hidden="true"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            >
              <path d="M12 6v12M6 12h12" />
            </svg>
            {t("gear.part.addOne")}
          </a>
        </CampoDelModulo>
      </Modulo>
    )
  }
  return (
    <Modulo
      titolo={titolo}
      formato={formato}
      dentro
      errore={rifiutoDetto(scrivi.error)}
      // nothing changed: Salva closes, a write would send the frames back for nothing
      salva={{
        onSalva: () => (cambiato ? scrivi.mutate() : onChiudi()),
        occupato: scrivi.isPending,
        spento: false,
      }}
      onAnnulla={onChiudi}
    >
      {parte === "spacer" ? (
        <CampoDelModulo id={id} etichetta={etichetta} largo>
          <PillolaScelta
            forma="risposta"
            fondo="vuoto"
            multipla
            etichetta={etichetta}
            formato={formato}
            opzioni={voci.map((p) => ({
              l: p.name,
              sel: scelti.includes(p.id),
              on: () =>
                setScelti(
                  scelti.includes(p.id) ? scelti.filter((x) => x !== p.id) : [...scelti, p.id],
                ),
            }))}
          />
        </CampoDelModulo>
      ) : (
        <CampoDelModulo
          id={id}
          etichetta={
            SENZA_DAI_FILE.includes(parte)
              ? etichetta
              : t("gear.part.field.files", { parte: etichetta })
          }
          largo
        >
          <TendinaDelModulo
            id={id}
            valore={String(scelti[0] ?? "")}
            voci={[
              { valore: "", l: "--" },
              ...voci.map((p) => ({ valore: String(p.id), l: p.name })),
            ]}
            onValore={(v) => setScelti(v ? [Number(v)] : [])}
          />
        </CampoDelModulo>
      )}
    </Modulo>
  )
}

/** The write: the spacers as a list, one kind for the others. A guide is one, scope or OAG: the
 *  backend takes off the other kind (`rigs.declare_part`). */
async function manda(
  r: Corredo,
  parte: Parte,
  scelti: number[],
  prima: Schema["RigPart"][],
  voci: Pezzo[],
): Promise<Scritto | undefined> {
  if (parte === "spacer") {
    const { data, error } = await api.PUT("/api/v1/gear/rigs/{rig_id}/spacers", {
      params: { path: { rig_id: r.id } },
      body: { piece_ids: scelti },
    })
    if (error) throw error
    return data
  }
  const nuovo = voci.find((p) => p.id === scelti[0])
  // emptied, it is the kind you had chosen that goes back to the files
  const kind = (nuovo?.kind ?? prima[0]?.kind ?? parte) as Sceglibile
  const { data, error } = await api.PUT("/api/v1/gear/rigs/{rig_id}/parts/{kind}", {
    params: { path: { rig_id: r.id, kind } },
    body: { piece_id: nuovo?.id ?? null },
  })
  if (error) throw error
  return data
}
