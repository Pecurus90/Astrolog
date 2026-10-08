import { useQuery } from "@tanstack/react-query"
import { type FocusEvent, type KeyboardEvent, type ReactNode, useEffect, useRef, useState } from "react"
import { useNavigate } from "react-router"

import { Bottone } from "./Bottone"
import { Icon } from "./Icons"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { type Chiave, notte, numero, ore, t } from "./i18n"

type Trovati = components["schemas"]["SearchResult"]
type Pezzo = components["schemas"]["FoundPiece"]

/** Una voce del menu, gia' pronta: cosa dice e quale pagina apre. */
type Voce = { a: string; nome: ReactNode; accanto: string | null; dice: string; non?: boolean }
type Gruppo = { titolo: Chiave; voci: Voce[]; totale: number }

/** Quanto si aspetta dopo l'ultima lettera prima di chiedere: una richiesta per parola, non per tasto. */
const RITARDO_MS = 250
const MENU = "trova"

/**
 * La ricerca nella barra in alto (disegno v31, `53-campo` e `55-trova`; contratto in
 * `docs/domini/navigazione.md`). Chiusa e' un bottone; toccata diventa un campo, e alla prima
 * lettera apre sotto il menu dei trovati, per gruppo.
 *
 * - **L'indirizzo di una voce nasce qui**: la rotta dice chi e' (chiave, id, genere), le pagine e
 *   i loro parametri stanno nel frontend.
 * - **Il fuoco resta nel campo**: le frecce spostano `aria-activedescendant`, non il fuoco, o
 *   scrivere un'altra lettera vorrebbe dire tornare indietro.
 * - **`combobox` sta sull'input** (ARIA 1.2), non sull'involucro come nella tavola: un involucro
 *   senza fuoco non annuncia niente.
 */
export function Ricerca({ aperta, onAperta }: { aperta: boolean; onAperta: (aperta: boolean) => void }) {
  const vai = useNavigate()
  const [testo, setTesto] = useState("")
  const [chiesto, setChiesto] = useState("")
  const [scelta, setScelta] = useState(0)
  const campo = useRef<HTMLInputElement>(null)
  const bottone = useRef<HTMLButtonElement>(null)
  // Chi chiude con Esc o Annulla ritrova il fuoco sul bottone; chi apre una voce no: e' altrove.
  const torna = useRef(false)

  useEffect(() => {
    const dopo = setTimeout(() => setChiesto(testo.trim()), RITARDO_MS)
    return () => clearTimeout(dopo)
  }, [testo])

  const risposta = useQuery({
    queryKey: ["search", chiesto],
    enabled: chiesto !== "",
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/search", { params: { query: { q: chiesto } } })
      if (error) throw new Error(t("search.failed"))
      return data
    },
  })
  useEffect(() => setScelta(0), [risposta.data])

  useEffect(() => {
    if (aperta) campo.current?.focus()
    else if (torna.current) bottone.current?.focus()
    torna.current = false
  }, [aperta])

  // Ctrl K (Cmd K sul Mac) da ogni pagina: e' il tasto che il bottone dichiara.
  useEffect(() => {
    function tasto(e: globalThis.KeyboardEvent) {
      if (e.key.toLowerCase() !== "k" || !(e.ctrlKey || e.metaKey)) return
      e.preventDefault()
      onAperta(true)
    }
    window.addEventListener("keydown", tasto)
    return () => window.removeEventListener("keydown", tasto)
  }, [onAperta])

  function chiudi(riportaIlFuoco: boolean) {
    torna.current = riportaIlFuoco
    setTesto("")
    setChiesto("")
    onAperta(false)
  }
  function apri(voce: Voce) {
    chiudi(false)
    void vai(voce.a)
  }

  if (!aperta) {
    return (
      <button
        className="as-telaio__cerca"
        type="button"
        aria-label={t("search.open")}
        ref={bottone}
        onClick={() => onAperta(true)}
      >
        <Icon name="cerca" />
        <span className="as-telaio__cerca-testo">{t("search.placeholder")}</span>
        <span className="as-telaio__tasto">{t(SUL_MAC ? "search.key.shortcut.mac" : "search.key.shortcut")}</span>
      </button>
    )
  }

  const scritto = testo.trim() !== ""
  // La risposta vale solo per il testo che l'ha chiesta: nel ritardo dopo una lettera il menu di
  // prima non si mostra, o Invio aprirebbe la voce di un'altra ricerca.
  const fresca = scritto && chiesto === testo.trim()
  const gruppi = fresca && risposta.data ? gruppiDi(risposta.data) : []
  const voci = gruppi.flatMap((g) => g.voci)
  const niente = fresca && risposta.isSuccess && voci.length === 0
  const attiva = voci.length > 0 ? `${MENU}-${scelta}` : undefined

  function tasti(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Escape") {
      // qui si ferma: il telaio non deve chiudere anche Stanotte con lo stesso tasto
      e.stopPropagation()
      chiudi(true)
    } else if (voci.length === 0) {
      return
    } else if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault()
      const passo = e.key === "ArrowDown" ? 1 : -1
      setScelta((scelta + passo + voci.length) % voci.length)
    } else if (e.key === "Enter") {
      const voce = voci[scelta]
      if (voce) apri(voce)
    }
  }
  // Uscire dal campo chiude; un tocco dentro il menu o su Annulla no, o il clic non arriverebbe.
  function esce(e: FocusEvent<HTMLDivElement>) {
    if (!e.currentTarget.contains(e.relatedTarget)) chiudi(false)
  }

  let posto = 0
  return (
    <div className="as-cerca" onBlur={esce}>
      <label className="as-campo">
        <Icon name="cerca" className="as-campo__icona" />
        <input
          type="search"
          role="combobox"
          aria-label={t("search.label")}
          aria-expanded={voci.length > 0}
          aria-controls={MENU}
          aria-activedescendant={attiva}
          aria-autocomplete="list"
          autoComplete="off"
          placeholder={t("search.placeholder")}
          ref={campo}
          value={testo}
          onChange={(e) => setTesto(e.target.value)}
          onKeyDown={tasti}
        />
        {scritto && (!fresca || risposta.isFetching) ? (
          <span className="as-campo__attesa">
            <span className="as-attesa" aria-hidden="true" />
            {t("search.busy")}
          </span>
        ) : (
          <span className="as-telaio__tasto" aria-hidden="true">
            {t("search.key.esc")}
          </span>
        )}
      </label>
      {/* la classe sta su un involucro: il bottone e' un mattone e non ne prende altre */}
      <span className="as-cerca__annulla">
        <Bottone verso="nudo" piccolo onClick={() => chiudi(true)}>
          {t("search.cancel")}
        </Bottone>
      </span>
      {voci.length > 0 && (
        <div className="as-trova" id={MENU} role="listbox" aria-label={t("search.found")}>
          {gruppi.map((gruppo) => (
            <div className="as-trova__gruppo" role="group" aria-label={t(gruppo.titolo)} key={gruppo.titolo}>
              <p className="as-trova__capo" aria-hidden="true">
                <span className="as-soprattitolo as-soprattitolo--nudo">{t(gruppo.titolo)}</span>
                <span className="as-trova__quante">
                  {gruppo.voci.length < gruppo.totale
                    ? t("search.some", { n: numero(gruppo.voci.length), tot: numero(gruppo.totale) })
                    : numero(gruppo.totale)}
                </span>
              </p>
              <ul className="as-trova__voci" role="presentation">
                {gruppo.voci.map((voce) => {
                  const qui = posto++
                  return (
                    <li
                      className="as-trova__voce"
                      role="option"
                      id={`${MENU}-${qui}`}
                      aria-selected={qui === scelta}
                      key={voce.a}
                      // il fuoco resta nel campo: senza, il clic lo sposterebbe e il menu si chiuderebbe prima
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => apri(voce)}
                    >
                      <span className="as-trova__nome">
                        {voce.nome}
                        {voce.accanto && <span className="as-trova__comune">{voce.accanto}</span>}
                      </span>
                      <span className={voce.non ? "as-trova__dice as-trova__dice--non" : "as-trova__dice"}>
                        {voce.dice}
                      </span>
                    </li>
                  )
                })}
              </ul>
            </div>
          ))}
          <p className="as-trova__piede" aria-hidden="true">
            <span>
              <span className="as-telaio__tasto">{"\u2191"}</span>
              <span className="as-telaio__tasto">{"\u2193"}</span> {t("search.keys.choose")}
            </span>
            <span>
              <span className="as-telaio__tasto">{t("search.key.enter")}</span> {t("search.keys.open")}
            </span>
            <span>
              <span className="as-telaio__tasto">{t("search.key.esc")}</span> {t("search.keys.close")}
            </span>
          </p>
        </div>
      )}
      {(niente || (fresca && risposta.isError)) && (
        <div className="as-trova" id={MENU} aria-live="polite">
          <p className="as-trova__niente">
            {risposta.isError ? risposta.error.message : t("search.nothing", { q: chiesto })}
          </p>
          {!risposta.isError && <p className="as-trova__nota">{t("search.nothing.why")}</p>}
        </div>
      )}
    </div>
  )
}

const SUL_MAC = typeof navigator !== "undefined" && /Mac|iPhone|iPad/.test(navigator.platform)

/** I gruppi che hanno voci, nell'ordine della tavola. Un gruppo vuoto non si mostra. */
function gruppiDi(trovati: Trovati): Gruppo[] {
  const gruppi: Gruppo[] = [
    {
      titolo: "search.group.objects",
      totale: trovati.objects.total,
      voci: trovati.objects.items.map((o) => ({
        a: `/archivio?key=${encodeURIComponent(o.key)}`,
        // un mosaico porta il nome che gli hai dato tu: non e' una sigla di catalogo
        nome: o.panels === null ? <span className="as-nome-oggetto">{o.name ?? o.key}</span> : <b>{o.name ?? o.key}</b>,
        accanto: o.common_name,
        dice:
          o.panels === null
            ? quanto(o.frames, o.integration_s)
            : `${quanto(o.frames, o.integration_s)} \u00b7 ${t("search.mosaic", { n: numero(o.panels) })}`,
      })),
    },
    {
      titolo: "search.group.nights",
      totale: trovati.nights.total,
      voci: trovati.nights.items.map((n) => ({
        a: `/notti?notte=${n.id}`,
        nome: <b>{notte(n.night_date)}</b>,
        accanto: n.site,
        dice: quanto(n.frames, n.integration_s),
      })),
    },
    {
      titolo: "search.group.gear",
      totale: trovati.gear.total,
      voci: trovati.gear.items.map((p) => ({
        a: `/attrezzatura?pezzo=${p.kind === "filter" ? "filtro" : "strumento"}-${p.id}`,
        nome: <b>{p.name}</b>,
        accanto: t(`search.kind.${p.kind}`),
        ...usoDi(p),
      })),
    },
    {
      titolo: "search.group.sites",
      totale: trovati.sites.total,
      voci: trovati.sites.items.map((s) => ({
        a: `/impostazioni/sito?sito=${s.id}`,
        nome: <b>{s.name}</b>,
        accanto: null,
        dice: t("search.site.nights", { n: numero(s.nights) }),
      })),
    },
  ]
  return gruppi.filter((g) => g.voci.length > 0)
}

/** Frame e ore; senza durata nei file "senza tempo", mai "0 h". */
function quanto(frame: number, secondi: number): string {
  const n = t("search.frames", { n: numero(frame) })
  return secondi > 0 ? t("search.timed", { frame: n, ore: ore(secondi) }) : t("search.untimed", { frame: n })
}

/** Le ore di un pezzo, o perche' non ci sono: il perche' lo decide il backend. */
function usoDi(pezzo: Pezzo): { dice: string; non?: boolean } {
  if (!pezzo.counted) return { dice: t("search.notCounted"), non: true }
  if (pezzo.no_hours !== null || pezzo.frames === null || pezzo.integration_s === null) {
    return { dice: t(pezzo.no_hours === "no_rig" ? "search.noRig" : "search.filesSilent"), non: true }
  }
  return { dice: quanto(pezzo.frames, pezzo.integration_s) }
}
