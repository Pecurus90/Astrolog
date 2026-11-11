import { useQuery } from "@tanstack/react-query"
import {
  type CSSProperties,
  type KeyboardEvent,
  type MouseEvent,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react"
import { useNavigate } from "react-router"

import { useApriOggetto } from "./apriOggetto"
import { api } from "./api/client"
import { useFormato } from "./componenti/formato"
import { useTema } from "./componenti/Tema"
import { type Chiave, numero, t } from "./i18n"
import { type Voce, SEGNI, gruppiDi } from "./ricercaVoci"
import { percentualeDi, statoDi, useStato } from "./Scansiona"
import { LENTE } from "./TelaioComune"

/** Quanto si aspetta dopo l'ultima lettera prima di chiedere: una richiesta per parola, non per tasto. */
const RITARDO_MS = 250
const MENU = "cerca-lista"

// [T] Cerca.dc.html:72-73 the two layouts, desktop window and phone page
const DESKTOP = {
  pannello: { maxWidth: 640, maxHeight: "72vh", background: "var(--carta)", borderRadius: 28, boxShadow: "0 24px 64px rgba(0,0,0,.35)" },
  campo: "12px 20px",
  lista: "14px 8px 10px",
  testo: 18,
  riga: 52,
}
const TELEFONO = {
  pannello: { maxWidth: "none", minHeight: "100%", background: "var(--telaio)", borderRadius: 0 },
  campo: "10px 16px",
  lista: "12px 8px",
  testo: 17,
  riga: 56,
}

/** L'aiuto del campo vuoto: cosa si cerca, con un esempio; attrezzatura e sito dal tuo archivio. */
const AIUTO: readonly { nome: Chiave; esempio?: Chiave; segno: string; dato?: "gear" | "site" }[] = [
  { nome: "search.help.objects", esempio: "search.help.objects.e", segno: SEGNI.oggetti },
  { nome: "search.help.nights", esempio: "search.help.nights.e", segno: SEGNI.notti },
  { nome: "search.help.gear", segno: SEGNI.attrezzatura, dato: "gear" },
  { nome: "search.help.sites", segno: SEGNI.siti, dato: "site" },
  { nome: "search.help.settings", esempio: "search.help.settings.e", segno: SEGNI.impostazioni },
  { nome: "search.help.pages", esempio: "search.help.pages.e", segno: SEGNI.pagine },
]

/** Muove un elemento come la tavola (`an`): niente col movimento ridotto o senza `animate`. */
function muovi(el: Element | null | undefined, kf: Keyframe[], o: KeyframeAnimationOptions): Animation | null {
  if (!el || typeof el.animate !== "function" || window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return null
  return el.animate(kf, { duration: 260, easing: "cubic-bezier(.2,.7,.2,1)", fill: "backwards", ...o })
}

/**
 * Cerca (tavola `componenti/Cerca` v77; contratto in `docs/domini/navigazione.md`): sul desktop
 * una finestra al centro sopra un velo, sul telefono una pagina intera con Annulla.
 *
 * - **L'indirizzo di una voce nasce qui**: la rotta dice chi e', le pagine stanno nel frontend.
 * - **Il fuoco resta nel campo**: le frecce spostano `aria-activedescendant`.
 * - **Chi chiude con Esc, Annulla o il velo ritrova il fuoco sul bottone; chi apre una voce no**.
 */
export function Ricerca({ onChiudi }: { onChiudi: (riportaIlFuoco: boolean) => void }) {
  const vai = useNavigate()
  const apriOggetto = useApriOggetto()
  const tel = useFormato() === "telefono"
  const scuro = useTema().modo === "scuro"
  const L = tel ? TELEFONO : DESKTOP
  const [testo, setTesto] = useState("")
  const [chiesto, setChiesto] = useState("")
  const [scelta, setScelta] = useState(0)
  const campo = useRef<HTMLInputElement>(null)
  const velo = useRef<HTMLDivElement>(null)
  const pannello = useRef<HTMLDivElement>(null)
  const esce = useRef(false)
  const lavoro = useStato().data

  useEffect(() => {
    const dopo = setTimeout(() => setChiesto(testo.trim()), RITARDO_MS)
    return () => clearTimeout(dopo)
  }, [testo])

  // anche il campo vuoto chiede: l'aiuto prende gli esempi e "archivio vuoto" dalla rotta
  const risposta = useQuery({
    queryKey: ["search", chiesto],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/search", { params: { query: { q: chiesto } } })
      if (error) throw new Error(t("search.note.failed"))
      return data
    },
  })
  useEffect(() => setScelta(0), [risposta.data])

  useLayoutEffect(() => {
    campo.current?.focus({ preventScroll: true })
    if (tel) muovi(pannello.current, [{ opacity: 0, transform: "translateY(24px)" }, { opacity: 1, transform: "none" }], { duration: 280 })
    else {
      muovi(velo.current, [{ opacity: 0 }, { opacity: 1 }], { duration: 200 })
      muovi(pannello.current, [{ opacity: 0, transform: "translateY(-8px) scale(.98)" }, { opacity: 1, transform: "none" }], { duration: 240 })
    }
  }, [tel])

  function chiudi(riportaIlFuoco: boolean) {
    if (esce.current) return
    esce.current = true
    const via = tel ? "translateY(24px)" : "translateY(-6px) scale(.98)"
    const a = muovi(pannello.current, [{ opacity: 1, transform: "none" }, { opacity: 0, transform: via }], { duration: 160, easing: "ease-in", fill: "forwards" })
    if (!a) return onChiudi(riportaIlFuoco)
    if (!tel) muovi(velo.current, [{ opacity: 1 }, { opacity: 0 }], { duration: 160, fill: "forwards" })
    a.onfinish = () => onChiudi(riportaIlFuoco)
  }
  function apri(voce: Voce) {
    onChiudi(false)
    if (voce.oggetto && apriOggetto) apriOggetto(voce.oggetto.chiave, voce.oggetto.nome)
    else void vai(voce.a)
  }

  const scritto = testo.trim() !== ""
  // La risposta vale solo per il testo che l'ha chiesta: nel ritardo dopo una lettera il menu di
  // prima non si mostra, o Invio aprirebbe la voce di un'altra ricerca.
  const cerco = scritto && (chiesto !== testo.trim() || risposta.isFetching)
  // v60: mentre cerca o se AstroLog non risponde, niente righe
  const ferma = cerco || risposta.isError
  const gruppi = scritto && !ferma ? gruppiDi(risposta.data, chiesto) : []
  const voci = gruppi.flatMap((g) => g.voci)
  const sel = Math.min(scelta, Math.max(0, voci.length - 1))
  const niente = scritto && !ferma && voci.length === 0
  const nota = notaDi(risposta.isError, cerco, risposta.data?.archive_empty === true, lavoro)

  useEffect(() => {
    pannello.current?.querySelectorAll("[data-an=riga]").forEach((e, i) => {
      muovi(e, [{ opacity: 0, transform: "translateY(6px)" }, { opacity: 1, transform: "none" }], { duration: 220, delay: Math.min(i, 10) * 25 })
    })
  }, [chiesto, ferma])

  function scegli(n: number) {
    setScelta(n)
    document.getElementById(`${MENU}-${n}`)?.scrollIntoView?.({ block: "nearest" })
  }
  function tasti(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Escape") {
      // qui si ferma: il telaio non deve chiudere anche altro con lo stesso tasto
      e.stopPropagation()
      e.preventDefault()
      chiudi(true)
    } else if ((e.key === "ArrowDown" || e.key === "ArrowUp") && voci.length > 0) {
      e.preventDefault()
      scegli((sel + (e.key === "ArrowDown" ? 1 : -1) + voci.length) % voci.length)
    } else if (e.key === "Enter") {
      e.preventDefault()
      const voce = voci[sel]
      if (voce) apri(voce)
    }
  }
  // finestra modale: Tab gira fra cio' che sta dentro
  function giro(e: KeyboardEvent<HTMLDivElement>) {
    if (e.key !== "Tab") return
    const dentro = [...e.currentTarget.querySelectorAll<HTMLElement>("input, a[href], button")]
    const qui = dentro.indexOf(document.activeElement as HTMLElement)
    e.preventDefault()
    dentro[(qui + (e.shiftKey ? -1 : 1) + dentro.length) % dentro.length]?.focus()
  }
  function fuori(e: MouseEvent<HTMLDivElement>) {
    if (e.target === e.currentTarget) chiudi(true)
  }

  const fondo: CSSProperties = tel
    ? { position: "fixed", padding: 0, background: "var(--telaio)", overflowY: "auto" }
    : {
        position: "fixed",
        padding: "11vh 24px 24px",
        background: `color-mix(in srgb, var(--nero) ${scuro ? 60 : 35}%, transparent)`,
      }
  let posto = 0
  return (
    <div className="al-c-cerca__riga-1" ref={velo} data-menu="1" onMouseDown={fuori} style={fondo}>
      <div
        className="al-c-cerca__colonna-1"
        ref={pannello}
        role="dialog"
        aria-modal="true"
        aria-label={t("search.dialog")}
        onKeyDown={giro}
        style={L.pannello}
      >
        <div className="al-c-cerca__riga-2" style={{ padding: L.campo }}>
          <svg className="al-c-cerca__grafico-1" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d={LENTE} />
          </svg>
          <input
            className="al-c-cerca__blocco-2"
            ref={campo}
            value={testo}
            onChange={(e) => setTesto(e.target.value)}
            onKeyDown={tasti}
            role="combobox"
            aria-expanded={voci.length > 0}
            aria-controls={MENU}
            aria-activedescendant={voci.length > 0 && !tel ? `${MENU}-${sel}` : undefined}
            aria-autocomplete="list"
            aria-label={t("search.label")}
            placeholder={t(tel ? "search.placeholder.phone" : "search.placeholder")}
            style={{ fontSize: L.testo }}
          />
          {tel ? (
            <a
              className="al-c-cerca__riga-3"
              href="#"
              // the board resets links in its helmet (Cerca.dc.html:12): not a browser link
              style={{ color: "inherit", textDecoration: "none" }}
              onClick={(e) => {
                e.preventDefault()
                chiudi(true)
              }}
            >
              {t("search.cancel")}
            </a>
          ) : (
            <span className="al-c-cerca__blocco-3" aria-hidden="true">
              {t("search.key.esc")}
            </span>
          )}
        </div>
        <div className="al-c-cerca__colonna-2" id={MENU} role="listbox" aria-label={t("search.found")} aria-busy={cerco} style={{ padding: L.lista }}>
          {nota && (
            <p className="al-c-cerca__riga-4" aria-live="polite">
              <span
                className="al-c-cerca__tondo-1"
                aria-hidden="true"
                style={nota.avviso ? { background: "var(--avviso)", color: "var(--avviso-testo)" } : { background: "var(--carta)", color: "var(--testo)" }}
              >
                {nota.segno}
              </span>
              <span className="al-c-cerca__testo-1">{nota.testo}</span>
            </p>
          )}
          {!scritto && (
            <div className="al-c-cerca__colonna-3">
              <span className="al-c-cerca__testo-2">{t("search.help")}</span>
              <div className="al-c-cerca__colonna-4">
                {AIUTO.map((a) => {
                  const esempio = a.dato ? risposta.data?.examples[a.dato] : a.esempio && t(a.esempio)
                  return (
                    <span className="al-c-cerca__riga-5" key={a.nome}>
                      <span className="al-c-cerca__tondo-2" aria-hidden="true">
                        <Segno d={a.segno} />
                      </span>
                      {/* v79: one line with the dots, all of it in the title */}
                      <span
                        className="al-c-cerca__aiuto-t"
                        title={esempio ? `${t(a.nome)} \u00b7 ${esempio}` : t(a.nome)}
                      >
                        <b className="al-c-cerca__testo-3">{t(a.nome)}</b>
                        {esempio && <span className="al-c-cerca__testo-4">{` \u00b7 ${esempio}`}</span>}
                      </span>
                    </span>
                  )
                })}
              </div>
            </div>
          )}
          {niente && (
            <div className="al-c-cerca__colonna-5" aria-live="polite">
              <span className="al-c-cerca__testo-5">{t("search.nothing", { q: chiesto })}</span>
              <span className="al-c-cerca__testo-6">{t("search.nothing.why")}</span>
            </div>
          )}
          {gruppi.map((g) => (
            <div className="al-c-cerca__colonna-6" role="group" aria-label={t(g.titolo)} key={g.titolo}>
              <div className="al-c-cerca__riga-6" aria-hidden="true">
                <span className="al-c-cerca__testo-7">{t(g.titolo)}</span>
                <span>{g.perche}</span>
                <span className="al-c-cerca__testo-8">
                  {g.voci.length < g.totale ? t("search.some", { n: numero(g.voci.length), tot: numero(g.totale) }) : numero(g.totale)}
                </span>
              </div>
              {g.voci.map((v) => {
                const qui = posto++
                const su = !tel && qui === sel
                return (
                  <div className="al-c-cerca__riga-7" key={`${v.a} ${v.nome}`}>
                    <div
                      className="al-c-cerca__riga-8"
                      data-an="riga"
                      id={`${MENU}-${qui}`}
                      role="option"
                      aria-selected={su}
                      // il fuoco resta nel campo: senza, il clic lo sposterebbe
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => apri(v)}
                      onMouseMove={() => !tel && qui !== sel && setScelta(qui)}
                      style={{ minHeight: L.riga, background: su ? "var(--carta-2)" : "transparent", cursor: "pointer" }}
                    >
                      <span
                        className="al-c-cerca__tondo-3"
                        aria-hidden="true"
                        style={su ? { background: "var(--nav-su)", color: "var(--nav-su-testo)" } : { background: "var(--carta-2)", color: "var(--tenue)" }}
                      >
                        <Segno d={g.segno} />
                      </span>
                      <span className="al-c-cerca__colonna-7">
                        <span className="al-c-cerca__blocco-4">
                          {v.nome}
                          {v.accanto && <span className="al-c-cerca__testo-9">{` \u00b7 ${v.accanto}`}</span>}
                        </span>
                        {tel && v.dice && <span className="al-c-cerca__blocco-5">{v.dice}</span>}
                      </span>
                      {!tel && v.dice && <span className="al-c-cerca__blocco-6">{v.dice}</span>}
                      {su && (
                        <span className="al-c-cerca__blocco-3" aria-hidden="true">
                          {t("search.key.enter")}
                        </span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          ))}
        </div>
        {!tel && (
          <div className="al-c-cerca__riga-9" aria-hidden="true">
            <span>{t("search.keys.choose")}</span>
            <span>{t("search.keys.open")}</span>
            <span>{t("search.keys.close")}</span>
          </div>
        )}
      </div>
    </div>
  )
}

function Segno({ d }: { d: string }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d={d} />
    </svg>
  )
}

type Nota = { segno: string; testo: string; avviso?: boolean }

/** La riga in testa ai trovati (tavola, `nota`): una sola, la piu' urgente. */
function notaDi(fallita: boolean, cerco: boolean, vuoto: boolean, lavoro: Parameters<typeof statoDi>[0]): Nota | null {
  if (fallita) return { segno: "!", testo: t("search.note.failed"), avviso: true }
  if (cerco) return { segno: "\u2026", testo: t("search.note.waiting") }
  if (vuoto) return { segno: "?", testo: t("search.note.empty") }
  if (statoDi(lavoro) !== "in corso") return null
  const pct = percentualeDi(lavoro)
  return { segno: "\u2026", testo: pct === null ? t("search.note.scan.nopct") : t("search.note.scan", { pct: numero(pct) }) }
}
