import { useQuery } from "@tanstack/react-query"
import { type KeyboardEvent, type ReactNode, type UIEvent, useEffect, useRef, useState } from "react"
import { Link, useLocation } from "react-router"

import { Bottone } from "./Bottone"
import { Icon, IconSprite } from "./Icons"
import { Ricerca } from "./Ricerca"
import { AvvisiDellaScansione, Scansiona, ScansioneNelFoglio } from "./Scansiona"
import { Pastiglia, Stanotte } from "./Stanotte"
import { api } from "./api/client"
import { numero, t } from "./i18n"
import { PAGINE, type Pagina, paginaDi } from "./pagine"

/**
 * Il telaio (disegno v26, `51-telaio.css`; contratto in `docs/domini/navigazione.md`): il binario
 * delle pagine, la barra in alto, Stanotte che si apre dalla pastiglia, e sul telefono il foglio
 * "Altro". Stesso markup a ogni misura: lo decide il foglio, dal contenitore.
 *
 * - **Qui non si calcola niente**: il conto delle cose da confermare arriva fatto da
 *   `GET /review`, la stessa query della Dashboard.
 * - **Gli stati sono attributi** (`data-stanotte`, `data-altro`, `data-ritirata`): il foglio
 *   legge quelli. Stanotte ricorda l'ultima scelta in questo browser.
 * - **Il fuoco segue cio' che si apre**, e torna a chi l'ha aperto; Esc chiude, prima Altro.
 */
export function Layout({ children }: { children: ReactNode }) {
  const dove = useLocation()
  const revisione = useQuery({
    queryKey: ["review"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/review")
      if (error) throw new Error(t("review.failed"))
      return data
    },
  })
  const qui = paginaDi(dove.pathname)
  const daConfermare = revisione.data?.to_confirm ?? 0

  const [stanotte, setStanotte] = useState(ricordata)
  const [altro, setAltro] = useState(false)
  const [ritirata, setRitirata] = useState(false)
  const [cerca, setCerca] = useState(false)
  const pastiglia = useRef<HTMLButtonElement>(null)
  const titoloStanotte = useRef<HTMLHeadingElement>(null)
  const apriAltro = useRef<HTMLButtonElement>(null)
  const titoloAltro = useRef<HTMLHeadingElement>(null)
  const prima = useRef(0)
  // Dove va il fuoco dopo il prossimo disegno: il pannello esiste solo dopo, e un focus chiesto
  // prima cadrebbe su un elemento ancora nascosto.
  const fuoco = useRef<HTMLElement | null>(null)
  useEffect(() => {
    fuoco.current?.focus({ preventScroll: true })
    fuoco.current = null
  })

  // Cambiare pagina chiude il foglio del telefono: la voce scelta e' gia' la risposta.
  useEffect(() => setAltro(false), [dove.pathname])

  function cambiaStanotte(apri: boolean) {
    setStanotte(apri)
    ricorda(apri)
    fuoco.current = apri ? titoloStanotte.current : pastiglia.current
  }
  function cambiaAltro(apri: boolean) {
    setAltro(apri)
    fuoco.current = apri ? titoloAltro.current : apriAltro.current
  }
  function chiudiUno() {
    if (altro) cambiaAltro(false)
    else if (stanotte) cambiaStanotte(false)
  }
  // La seconda riga del telefono si ritira scorrendo in giu' e torna risalendo (soglie della tavola).
  function scorre(e: UIEvent<HTMLElement>) {
    const y = e.currentTarget.scrollTop
    if (y > prima.current + 4 && y > 40) setRitirata(true)
    else if (y < prima.current - 4 || y < 40) setRitirata(false)
    prima.current = y
  }

  const voci = PAGINE.filter((p) => !p.coda)
  const coda = PAGINE.filter((p) => p.coda)
  const nelFoglio = PAGINE.filter((p) => !p.telefono)

  return (
    <div className="as-telaio-misura">
      <IconSprite />
      {/* Esc vale solo col fuoco dentro il telaio, come nella tavola. */}
      <div
        className="as-telaio"
        data-stanotte={stanotte ? "aperta" : "chiusa"}
        data-altro={altro ? "aperto" : "chiuso"}
        data-ritirata={ritirata ? "" : undefined}
        onKeyDown={(e) => {
          if (e.key === "Escape") chiudiUno()
        }}
      >
        <a className="as-telaio__salta" href="#contenuto">
          {t("frame.skip")}
        </a>
        <nav className="as-telaio__binario" aria-label={t("nav.label")}>
          <span className="as-telaio__marchio" aria-hidden="true">
            <span className="as-telaio__segno" />
          </span>
          <ul className="as-telaio__voci">
            {voci.map((p) => (
              <Voce key={p.a} pagina={p} accesa={p.a === qui?.a} conta={0} />
            ))}
          </ul>
          <ul className="as-telaio__voci as-telaio__voci--coda">
            {coda.map((p) => (
              <Voce
                key={p.a}
                pagina={p}
                accesa={p.a === qui?.a}
                conta={p.a === "/da-confermare" ? daConfermare : 0}
              />
            ))}
            <li className="as-telaio__posto as-telaio__posto--basso as-telaio__posto--telefono">
              <button
                className="as-telaio__voce"
                type="button"
                aria-expanded={altro}
                aria-controls="altro"
                ref={apriAltro}
                onClick={() => cambiaAltro(!altro)}
              >
                <Icon name="cursori" />
                <span className="as-telaio__parola">{t("frame.more")}</span>
                {daConfermare > 0 && (
                  <span
                    className="as-telaio__conta"
                    aria-label={t("frame.more.count", { n: numero(daConfermare) })}
                  >
                    {numero(daConfermare)}
                  </span>
                )}
              </button>
            </li>
          </ul>
        </nav>
        {/* Con la ricerca aperta il foglio da' al campo la prima riga del telefono. */}
        <header className={cerca ? "as-telaio__alto as-telaio__alto--cerca" : "as-telaio__alto"}>
          <span className="as-telaio__firma" aria-hidden="true">
            <span className="as-telaio__segno" />
          </span>
          <h1 className="as-telaio__titolo">{qui ? t(qui.chiave) : t("nav.unknown")}</h1>
          <Ricerca aperta={cerca} onAperta={setCerca} />
          <Scansiona />
          <Pastiglia ref={pastiglia} aperta={stanotte} onApri={() => cambiaStanotte(!stanotte)} />
        </header>
        <main className="as-telaio__corpo" id="contenuto" tabIndex={-1} onScroll={scorre}>
          <AvvisiDellaScansione />
          {children}
        </main>
        <button
          className="as-telaio__velo"
          type="button"
          tabIndex={-1}
          aria-label={t("frame.close")}
          onClick={chiudiUno}
        />
        <Stanotte titolo={titoloStanotte} aperta={stanotte} onChiudi={() => cambiaStanotte(false)} />
        <div
          className="as-telaio__altro as-foglio"
          id="altro"
          role="dialog"
          aria-modal="true"
          aria-labelledby="altro-titolo"
          hidden={!altro}
          onKeyDown={trattieni}
        >
          <span className="as-foglio__maniglia" aria-hidden="true" />
          <div className="as-foglio__testa">
            <h2 className="as-foglio__titolo" id="altro-titolo" tabIndex={-1} ref={titoloAltro}>
              {t("frame.more")}
            </h2>
            <Bottone verso="nudo" piccolo onClick={() => cambiaAltro(false)}>
              {t("frame.close.word")}
            </Bottone>
          </div>
          <ScansioneNelFoglio />
          <ul className="as-foglio__voci">
            {nelFoglio.map((p) => (
              <li key={p.a}>
                <Link className="as-foglio__voce" to={p.a}>
                  <Icon name={p.icona} />
                  {t(p.chiave)}
                  {p.a === "/da-confermare" && daConfermare > 0 && (
                    <span
                      className="as-telaio__conta"
                      aria-label={t("frame.count", { n: numero(daConfermare) })}
                    >
                      {numero(daConfermare)}
                    </span>
                  )}
                </Link>
              </li>
            ))}
          </ul>
          <p className="as-foglio__piede">{t("app.title")}</p>
        </div>
      </div>
    </div>
  )
}

/** Una voce del binario. Il conto si legge per intero a chi ascolta ("12 casi da confermare"). */
function Voce({ pagina, accesa, conta }: { pagina: Pagina; accesa: boolean; conta: number }) {
  const nome = t(pagina.chiave)
  const spazio = nome.indexOf(" ")
  const parola =
    pagina.dueRighe && spazio > 0 ? (
      <>
        {nome.slice(0, spazio)}
        {/* lo spazio dopo l'a capo tiene il nome intero per chi ascolta ("Da confermare", non
            "Daconfermare"); a inizio riga non si vede */}
        <br /> {nome.slice(spazio + 1)}
      </>
    ) : (
      nome
    )
  return (
    <>
      {pagina.staccata && <li className="as-telaio__stacco" aria-hidden="true" />}
      <li className={pagina.telefono ? "as-telaio__posto as-telaio__posto--basso" : "as-telaio__posto"}>
        <Link className="as-telaio__voce" to={pagina.a} aria-current={accesa ? "page" : undefined}>
          <Icon name={pagina.icona} />
          <span className="as-telaio__parola">{parola}</span>
          {conta > 0 && (
            <span className="as-telaio__conta" aria-label={t("frame.count", { n: numero(conta) })}>
              {numero(conta)}
            </span>
          )}
        </Link>
      </li>
    </>
  )
}

/** Il foglio Altro e' modale: Tab gira fra i suoi controlli e non esce dietro il velo. */
function trattieni(e: KeyboardEvent<HTMLDivElement>) {
  if (e.key !== "Tab") return
  const dentro = e.currentTarget.querySelectorAll<HTMLElement>("a[href], button:not([disabled])")
  const primo = dentro[0]
  const ultimo = dentro[dentro.length - 1]
  if (!primo || !ultimo) return
  // il titolo, dove il fuoco arriva aprendo, conta come prima del primo
  const qui = [...dentro].indexOf(document.activeElement as HTMLElement)
  if (e.shiftKey && qui <= 0) {
    e.preventDefault()
    ultimo.focus()
  } else if (!e.shiftKey && document.activeElement === ultimo) {
    e.preventDefault()
    primo.focus()
  }
}

const CHIAVE_STANOTTE = "astrolog.stanotte"

/** L'ultima scelta su Stanotte, in questo browser. Senza memoria (navigazione privata) si apre
 *  chiusa: il contenuto viene prima. */
function ricordata(): boolean {
  try {
    return localStorage.getItem(CHIAVE_STANOTTE) === "aperta"
  } catch {
    return false
  }
}

function ricorda(aperta: boolean) {
  try {
    localStorage.setItem(CHIAVE_STANOTTE, aperta ? "aperta" : "chiusa")
  } catch {
    // senza memoria si ricomincia chiusa: non e' un errore da mostrare
  }
}
