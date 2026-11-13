import { useQuery } from "@tanstack/react-query"
import { type ReactNode, useEffect, useState } from "react"
import { useNavigate, useSearchParams } from "react-router"

import { GRUPPI, Indice, type Scelta, esiste, primaScelta } from "./AttrezzaturaIndice"
import { Avviso } from "./componenti/Avviso"
import { useFormato } from "./componenti/formato"
import { gesto } from "./componenti/gesto"
import { Pagina as Cornice } from "./componenti/Pagina"
import { type CartaScheletro, Scheletro } from "./componenti/Scheletro"
import type { Formato } from "./componenti/Tema"
import { DettaglioSetup } from "./DettaglioSetup"
import { AggiungiUnPezzo } from "./GestiDelPezzo"
import { Rielaborati } from "./ModuloDelGesto"
import { UnFiltro, UnPezzo } from "./RigheDellAttrezzatura"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { numero, t } from "./i18n"

type Pagina = components["schemas"]["GearList"]
type Genere = components["schemas"]["InstrumentOnPage"]["kind"]

// [T] Attrezzatura.dc.html `L` (210-213): the page measures per format
const MISURE: Record<Formato, { stacco: string; angolo: string; barra: string; titolo: string }> = {
  desktop: { stacco: "16px", angolo: "28px", barra: "4px 8px 0", titolo: "34px" },
  telefono: { stacco: "12px", angolo: "24px", barra: "4px 4px 0", titolo: "26px" },
}

// [T] Attrezzatura.dc.html `SK` (404-405): the loading skeleton
const SCHELETRO: Record<Formato, CartaScheletro[]> = {
  desktop: [
    { col: "1", h: "420px", blocchi: [{ h: "14px", w: "80px" }, { h: "56px", r: "18px" }, { h: "56px", r: "18px" }, { h: "56px", r: "18px" }, { flex: "1" }] },
    { col: "2", h: "420px", blocchi: [{ riga: [{ h: "30px", w: "320px" }, t("gear.loading")], tra: true }, { h: "64px", w: "200px" }, { riga: [{ h: "36px", w: "90px", r: "999px" }, { h: "36px", w: "90px", r: "999px" }, { h: "36px", w: "160px", r: "999px" }], gap: "8px" }] },
    { col: "1", h: "440px", blocchi: [{ h: "14px", w: "100px" }, { flex: "1" }] },
    { col: "2", h: "440px", blocchi: [{ h: "24px", w: "120px" }, { h: "52px", r: "18px" }, { h: "52px", r: "18px" }, { h: "52px", r: "18px" }, { h: "52px", r: "18px" }] },
  ],
  telefono: [
    { h: "360px", blocchi: [{ riga: [{ h: "14px", w: "80px" }, t("gear.loading")], tra: true }, { h: "64px", r: "18px" }, { h: "64px", r: "18px" }, { h: "64px", r: "18px" }, { flex: "1" }] },
    { h: "420px", blocchi: [{ h: "14px", w: "100px" }, { flex: "1" }] },
  ],
}

// `?pezzo=strumento-12` / `?pezzo=filtro-3` (search): the group that holds it
function sceltaDa(pagina: Pagina, cercato: string | null): Scelta | null {
  const [chi, id] = cercato?.split("-") ?? []
  if (chi === "filtro" && pagina.filters.some((f) => String(f.id) === id)) return { gruppo: "filter" }
  const pezzo = chi === "strumento" ? pagina.instruments.find((p) => String(p.id) === id) : undefined
  return pezzo ? { gruppo: pezzo.kind } : null
}

/**
 * **Attrezzatura** (board v82): what you shot with, and how much. The index on top (*Setup* as
 * cards, *Componenti* as pills), the detail of what you choose below; on the phone the index is
 * the first screen and the detail opens full page, with the way back to it.
 *
 * - **No pagination**: anyone's gear fits in one screen.
 * - **"Aggiungi strumento" stays on top** even with nothing: empty-handed is when it serves most.
 * - **A piece opens from the address** (`?pezzo=`, used by search): its group, its row marked.
 */
export function Attrezzatura() {
  const formato = useFormato()
  const tel = formato === "telefono"
  const m = MISURE[formato]
  const vai = useNavigate()
  const [indirizzo, setIndirizzo] = useSearchParams()
  const cercato = indirizzo.get("pezzo")
  const elenco = useQuery({
    queryKey: ["gear"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/gear")
      if (error) throw new Error(t("gear.failed"))
      return data
    },
  })
  const pagina = elenco.data
  const [scelta, setScelta] = useState<Scelta | null>(null)
  // the add form, and the kind it opens on (null: the bar's button, from the first kind)
  const [aggiungo, setAggiungoDi] = useState<{ genere: Genere | null } | null>(null)
  const setAggiungo = (si: boolean, genere: Genere | null = null) => setAggiungoDi(si ? { genere } : null)
  const [dettaglio, setDettaglio] = useState(cercato !== null)
  const [rielab, setRielab] = useState<number | null>(null)

  const vuota =
    pagina !== undefined &&
    pagina.instruments.length === 0 &&
    pagina.rigs.length === 0 &&
    pagina.filters.length === 0
  // a choice gone from the page (merged, emptied) falls back to the first, as the board does
  const qui =
    pagina === undefined
      ? null
      : scelta !== null && esiste(pagina, scelta)
        ? scelta
        : (sceltaDa(pagina, cercato) ?? primaScelta(pagina))
  // a `?pezzo=` gone from the page (merged, removed) opens the index, not the first rig
  const trovato = scelta !== null || pagina === undefined || sceltaDa(pagina, cercato) !== null
  const aperto = tel ? (dettaglio && trovato) || aggiungo !== null : true
  const sopra = () => window.scrollTo?.({ top: 0, behavior: "smooth" })
  const scegli = (s: Scelta) => {
    setScelta(s)
    setAggiungo(false)
    setDettaglio(true)
    if (tel) sopra()
  }
  // a piece named in a rig's detail opens among the components, its row marked (`vaiComp`)
  const vaiAlPezzo = (id: number) => {
    const p = pagina?.instruments.find((x) => x.id === id)
    if (!p) return
    scegli({ gruppo: p.kind })
    setIndirizzo({ pezzo: `strumento-${id}` }, { replace: true })
  }
  const aggiungiDi = (genere: Genere | null) => {
    setAggiungo(true, genere)
    sopra()
  }

  let corpo: ReactNode = null
  if (elenco.isPending) {
    corpo = <Scheletro formato={formato} carte={SCHELETRO[formato]} testo={t("gear.loading")} griglia={tel ? "minmax(0,1fr)" : "320px minmax(0,1fr)"} gap={m.stacco} />
  } else if (!pagina) {
    corpo = <Avviso tipo="pagina" formato={formato} segno="!" titolo={t("gear.failed")} azione={t("gear.retry")} onAzione={() => void elenco.refetch()} />
  } else if (vuota && !aggiungo) {
    corpo = <Avviso tipo="pagina" formato={formato} segno="?" titolo={t("gear.empty")} testo={t("gear.empty.why")} azione={t("gear.empty.how")} onAzione={() => void vai("/impostazioni/cartelle")} />
  }
  const pieno = pagina !== undefined && (corpo === null || aggiungo !== null)

  return (
    <Cornice formato={formato}>
      <Rielaborati.Provider value={setRielab}>
        <div className="al-attr__colonna-1" style={{ gap: m.stacco }}>
          <div className="al-attr__riga-1" style={{ padding: m.barra }}>
            {tel && aperto && pieno && (
              <a href="#" role="button" onClick={gesto(() => { setDettaglio(false); setAggiungo(false) })} className="al-bottone al-bottone--testo al-bottone--a-filo">
                <span aria-hidden="true">←</span> {t("gear.title")}{/* glifo-ok: freccia della tavola */}
              </a>
            )}
            {/* the board's h1 is hidden by the sheet: the frame's h1 (Layout) already says it */}
            <span className="al-attr__blocco-2" />
            <a
              className="al-attr__riga-2"
              href="#"
              role="button"
              aria-expanded={aggiungo ? "true" : "false"}
              onClick={gesto(() => {
                setAggiungo(!aggiungo)
                if (!aggiungo) sopra()
              })}
              style={{
                background: aggiungo ? "var(--scelta)" : "var(--carta)",
                color: aggiungo ? "var(--scelta-testo)" : "var(--testo)",
                boxShadow: `inset 0 0 0 1.5px ${aggiungo ? "transparent" : "var(--linea)"}`,
              }}
            >
              <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M12 6v12M6 12h12" />
              </svg>
              {t("gear.write.add")}
            </a>
          </div>

          {rielab !== null && (
            <div className="al-attr__riga-3" aria-live="polite" style={{ borderRadius: m.angolo }}>
              <span className="al-attr__tondo-1" aria-hidden="true">↻</span>{/* glifo-ok: segno della tavola */}
              <span className="al-attr__blocco-3">{t("gear.rework", { n: numero(rielab) })}</span>
              <a href="#" role="button" onClick={gesto(() => setRielab(null))} className="al-bottone al-bottone--contorno">
                {t("gear.rework.close")}
              </a>
            </div>
          )}

          {corpo}

          {pieno && (
            <div className="al-attr__colonna-1" style={{ gap: m.stacco }}>
              {aggiungo && (tel ? aperto : true) && (
                <AggiungiUnPezzo
                  key={aggiungo.genere ?? ""}
                  schede={pagina.cards}
                  pezzi={pagina.instruments}
                  onChiudi={() => setAggiungo(false)}
                  {...(aggiungo.genere ? { primo: aggiungo.genere } : {})}
                />
              )}
              {!vuota && (!tel || !aperto) && <Indice pagina={pagina} scelta={aggiungo ? null : qui} formato={formato} onScegli={scegli} />}
              {aperto && !aggiungo && qui !== null && (
                <Dettaglio pagina={pagina} scelta={qui} cercato={cercato} formato={formato} onVai={vaiAlPezzo} onAggiungi={aggiungiDi} />
              )}
            </div>
          )}
        </div>
      </Rielaborati.Provider>
    </Cornice>
  )
}

/**
 * The detail of what is chosen: a rig as the board draws it; a group, until its board lands
 * (step 33, Gear commit D), with the rows of today.
 */
function Dettaglio({
  pagina,
  scelta,
  cercato,
  formato,
  onVai,
  onAggiungi,
}: {
  pagina: Pagina
  scelta: Scelta
  cercato: string | null
  formato: Formato
  onVai: (pezzo: number) => void
  onAggiungi: (genere: Genere | null) => void
}) {
  // the searched row comes into view once, when the page is there
  useEffect(() => {
    if (cercato) document.getElementById(`pezzo-${cercato}`)?.scrollIntoView?.({ block: "center" })
  }, [cercato])
  const segno = (chiave: string) => ({ id: `pezzo-${chiave}`, "aria-current": chiave === cercato ? ("true" as const) : undefined })
  if ("setup" in scelta) {
    const r = pagina.rigs.find((x) => x.id === scelta.setup)
    return r ? (
      <DettaglioSetup key={r.id} pagina={pagina} setup={r} formato={formato} onVai={onVai} onAggiungi={onAggiungi} />
    ) : null
  }
  if (scelta.gruppo === "filter") {
    return (
      <ul aria-label={t("gear.filters")}>
        {pagina.filters.map((f) => (
          <li key={f.id} {...segno(`filtro-${f.id}`)}>
            <UnFiltro filtro={f} tutti={pagina.filters} />
          </li>
        ))}
      </ul>
    )
  }
  const genere = scelta.gruppo
  const titolo = GRUPPI.find((g) => g.kind === genere)?.titolo ?? "gear.components"
  return (
    <ul aria-label={t(titolo)}>
      {pagina.instruments
        .filter((p) => p.kind === genere)
        .map((p) => (
          <li key={p.id} {...segno(`strumento-${p.id}`)}>
            <UnPezzo pezzo={p} campi={pagina.cards[genere] ?? []} tutti={pagina.instruments} />
          </li>
        ))}
    </ul>
  )
}
