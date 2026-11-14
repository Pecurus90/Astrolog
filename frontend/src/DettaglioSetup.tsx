import { useState } from "react"

import { CampoDelSetup } from "./CampoDelSetup"
import { gesto } from "./componenti/gesto"
import { CampoDelModulo, Modulo } from "./componenti/Modulo"
import type { Formato } from "./componenti/Tema"
import { PartiDelSetup, type Parte } from "./PartiDelSetup"
import { TrenoOttico, trenoDelSetup } from "./TrenoOttico"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { alPiu, numero, oreEMinuti, t } from "./i18n"
import { ICONE } from "./iconeDeiPezzi"
import { rifiutoDetto, useScrittura } from "./ModuloDelGesto"
import { MISURE_DETTAGLIO, coppiaDelSetup, nomeDelSetup } from "./misureDelSetup"
import { inBreve } from "./vociDellaScheda"

type Pagina = components["schemas"]["GearList"]
type Corredo = components["schemas"]["RigOnPage"]
type Genere = components["schemas"]["InstrumentOnPage"]["kind"]

/** What is open in the rig's detail: its name, or one of its parts. */
type Aperto = "nome" | Parte | null

/**
 * Il **dettaglio di un setup** (tavola v82, 51-100): a sinistra la carta col nome, le ore e i due
 * pezzi, poi le Parti; a destra il Campo col confronto, i Dati del setup e i Filtri. Sul telefono
 * una colonna sola. Un solo modulo aperto alla volta: il nome o una parte.
 */
export function DettaglioSetup({
  pagina,
  setup,
  formato,
  onVai,
  onAggiungi,
  proposta,
}: {
  pagina: Pagina
  setup: Corredo
  formato: Formato
  /** Opens a piece among the components. */
  onVai: (pezzo: number) => void
  /** "aggiungine uno": the add form, of that kind when there is one. */
  onAggiungi: (genere: Genere | null) => void
  /** "Seleziona montatura" from the group: the part opens with that piece already chosen. */
  proposta?: { parte: Parte; pezzo: number }
}) {
  const m = MISURE_DETTAGLIO[formato]
  const [aperto, setAperto] = useState<Aperto>(proposta?.parte ?? null)
  // the proposal holds for its first opening only: closed, the part reads the rig again
  const [proposto, setProposto] = useState(proposta?.pezzo)
  const apri = (x: Aperto) => {
    setProposto(undefined)
    setAperto(x)
  }
  const treno = trenoDelSetup(pagina, setup)
  return (
    <div className="al-attr__centro-2" style={{ gridTemplateColumns: m.griglia, gap: m.stacco }}>
      <div className="al-attr__colonna-1" style={{ gridColumn: m.otto, gap: m.stacco }}>
        <Carta
          pagina={pagina}
          setup={setup}
          formato={formato}
          aperto={aperto === "nome"}
          onApri={(si) => apri(si ? "nome" : null)}
        />
        {treno && (
          <TrenoOttico treno={treno} nome={nomeDelSetup(setup)} formato={formato} onVai={onVai} />
        )}
        <PartiDelSetup
          pagina={pagina}
          setup={setup}
          formato={formato}
          aperto={aperto === "nome" ? null : aperto}
          onApri={apri}
          onVai={onVai}
          onAggiungi={onAggiungi}
          {...(proposto !== undefined && aperto === proposta?.parte ? { proposto } : {})}
        />
      </div>
      <div className="al-attr__colonna-1" style={{ gridColumn: m.quattro, gap: m.stacco }}>
        <CampoDelSetup pagina={pagina} setup={setup} formato={formato} />
      </div>
    </div>
  )
}

function Carta({
  pagina,
  setup: r,
  formato,
  aperto,
  onApri,
}: {
  pagina: Pagina
  setup: Corredo
  formato: Formato
  aperto: boolean
  onApri: (si: boolean) => void
}) {
  const m = MISURE_DETTAGLIO[formato]
  const nome = nomeDelSetup(r)
  const contato = r.counted && r.integration_s !== null
  const rapporto = r.numbers?.focal_ratio.value ?? null
  // the mount you chose, else the one the files name most (board `mont`, 310)
  const montatura =
    r.parts.find((p) => p.kind === "mount" && p.chosen) ?? r.parts.find((p) => p.kind === "mount")
  const misure = [
    r.focal_mm !== null && { v: t("gear.focal", { mm: numero(r.focal_mm) }), calc: false },
    rapporto !== null && { v: t("gear.rig.ratio", { n: alPiu(rapporto, 1) }), calc: true },
    montatura && { v: t("gear.rig.mount", { nome: montatura.name }), calc: false },
  ].filter((x) => x !== false && x !== undefined)
  const pezzo = (id: number | null) => pagina.instruments.find((p) => p.id === id)
  const chi = [
    {
      tipo: t("review.kind.optics"),
      n: r.optics ?? t("gear.rig.noOptics"),
      icona: ICONE.ottica,
      p: pezzo(r.optics_id),
    },
    {
      tipo: t("review.kind.camera"),
      n: r.camera ?? t("gear.rig.noCamera"),
      icona: ICONE.camera,
      p: pezzo(r.camera_id),
    },
  ]
  return (
    <section
      className="al-attr__colonna-6"
      aria-label={nome}
      style={{
        background: "var(--carta)",
        color: "var(--testo)",
        borderRadius: m.angolo,
        padding: m.dentro,
      }}
    >
      <div className="al-attr__riga-14">
        <div className="al-attr__colonna-7">
          <h2 className="al-attr__testo-8" style={{ fontSize: m.titolo }}>
            {nome}
          </h2>
          {r.name && (
            <span className="al-attr__testo-9" style={{ color: "var(--tenue)" }}>
              {coppiaDelSetup(r)}
            </span>
          )}
        </div>
        <a
          className="al-attr__riga-15"
          href="#"
          role="button"
          aria-expanded={aperto ? "true" : "false"}
          aria-label={t("gear.write.rig.label", { nome })}
          onClick={gesto(() => onApri(!aperto))}
          style={{ minHeight: m.bottone, boxShadow: "inset 0 0 0 1.5px var(--linea)" }}
        >
          {t("gear.write.rig")}
        </a>
      </div>
      <div className="al-attr__centro-3" style={{ gridTemplateColumns: m.testa }}>
        <div className="al-attr__colonna-6">
          {contato ? (
            <span className="al-attr__testo-10" data-an="big" style={{ fontSize: m.grande }}>
              {oreEMinuti(r.integration_s ?? 0)}
            </span>
          ) : (
            <span
              className="al-attr__riga-16"
              style={{ color: "var(--tenue)", minHeight: m.grande }}
            >
              <span className="al-attr__tondo-4" aria-hidden="true" />
              {t("gear.counting")}
            </span>
          )}
          <div className="al-attr__riga-17">
            {misure.map((x) => (
              <span key={x.v} className="al-attr__riga-18" style={{ background: "var(--carta-2)" }}>
                {x.v}
                {x.calc && (
                  <span className="al-attr__testo-11" style={{ color: "var(--tenue)" }}>
                    {t("gear.rig.computed")}
                  </span>
                )}
              </span>
            ))}
          </div>
        </div>
        <ul className="al-attr__colonna-8">
          {chi.map((c) => (
            <li key={c.tipo} className="al-attr__griglia-1">
              <span className="al-attr__tondo-5" aria-hidden="true">
                <svg
                  className="al-attr__grafico-1"
                  aria-hidden="true"
                  width="26"
                  height="26"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d={c.icona} />
                </svg>
              </span>
              <span className="al-attr__colonna-9">
                <span className="al-attr__testo-12">{c.tipo}</span>
                <span className="al-attr__testo-13">{c.n}</span>
                {c.p && inBreve(c.p) && <span className="al-attr__testo-14">{inBreve(c.p)}</span>}
              </span>
            </li>
          ))}
        </ul>
      </div>
      {aperto && (
        <Rinomina setup={r} nome={nome} formato={formato} onChiudi={() => onApri(false)} />
      )}
    </section>
  )
}

function Rinomina({
  setup,
  nome,
  formato,
  onChiudi,
}: {
  setup: Corredo
  nome: string
  formato: Formato
  onChiudi: () => void
}) {
  const [scritto, setScritto] = useState(setup.name ?? "")
  const pulito = scritto.trim()
  const scrivi = useScrittura(async () => {
    const { data, error } = await api.PATCH("/api/v1/gear/rigs/{rig_id}", {
      params: { path: { rig_id: setup.id } },
      body: { name: pulito },
    })
    if (error) throw error
    return data
  }, onChiudi)
  const id = `setup-${setup.id}-nome`
  return (
    <Modulo
      titolo={t("gear.write.rig.title", { nome })}
      formato={formato}
      dentro
      errore={rifiutoDetto(scrivi.error)}
      salva={{ onSalva: () => scrivi.mutate(), occupato: scrivi.isPending, spento: pulito === "" }}
      onAnnulla={onChiudi}
      {...(pulito === "" ? { perche: t("gear.write.needName") } : {})}
    >
      <CampoDelModulo id={id} etichetta={t("gear.write.name")} largo>
        <input
          id={id}
          value={scritto}
          onChange={(e) => setScritto(e.target.value)}
          autoComplete="off"
          spellCheck={false}
          className="al-campo al-campo--vuoto al-campo--piena"
        />
      </CampoDelModulo>
    </Modulo>
  )
}
