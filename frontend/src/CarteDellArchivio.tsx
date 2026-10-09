import { type ReactNode, useEffect, useId, useLayoutEffect, useRef, useState } from "react"

import { BarraDeiFiltri } from "./FiltriUsati"
import { PannelliDelMosaico } from "./PannelliDelMosaico"
import {
  Costellazione,
  Filtri,
  Mosaico,
  Nome,
  NonSiSa,
  Tipo,
  nomeDi,
  oreDi,
  senzaTempo,
} from "./RigaDellArchivio"
import type { components } from "./api/schema"
import { numero, t } from "./i18n"

type Riga = components["schemas"]["ArchiveObject"]
type Produzione = components["schemas"]["ArchiveProduction"]

/**
 * L'Archivio **a carte** (disegno v31, la carta "Di lato"): il caso "guardo cosa ho".
 *
 * - **Un posto di anteprima per produzione**, vuoto: l'immagine non esiste ancora. Vuoto e' il
 *   suo stato, non un guasto, e chi ascolta non lo sente. Una produzione e' la riga ripresa con
 *   un'ottica e una camera (`docs/domini/archivio.md`), e le manda la rotta.
 * - **La griglia la fa il foglio**, non questa pagina.
 * - **Con piu' produzioni il nome apre il loro riepilogo**, sotto la carta: corredo, ore, frame e
 *   filtri di ognuna. Le voci non portano da nessuna parte finche' il modale non c'e': e' una
 *   regione da leggere, non un menu. Una produzione sola non apre niente.
 */
export function CarteDellArchivio({ righe }: { righe: Riga[] }) {
  return (
    <ul className="as-archivio__carte" aria-label={t("archive.title")}>
      {righe.map((riga) => (
        <PostoDellaCarta key={riga.key} riga={riga} />
      ))}
    </ul>
  )
}

/** La carta e, se aperto, il riepilogo delle sue produzioni: il foglio lo appende al `li`. */
function PostoDellaCarta({ riga }: { riga: Riga }) {
  const [aperto, setAperto] = useState(false)
  const posto = useRef<HTMLLIElement>(null)
  const comando = useRef<HTMLAnchorElement>(null)
  const riepilogo = useRef<HTMLDivElement>(null)
  const [aDestra, setADestra] = useState(false)
  const id = useId()
  const apribile = riga.productions.length > 1

  useEffect(() => {
    if (!aperto) return
    const fuori = (e: MouseEvent) => {
      if (!posto.current?.contains(e.target as Node)) setAperto(false)
    }
    // Sul documento: dopo un clic sul riepilogo, o su Safari, il fuoco e' sul body.
    const esc = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return
      setAperto(false)
      comando.current?.focus()
    }
    document.addEventListener("mousedown", fuori)
    document.addEventListener("keydown", esc)
    return () => {
      document.removeEventListener("mousedown", fuori)
      document.removeEventListener("keydown", esc)
    }
  }, [aperto])

  // Il riepilogo e' piu' largo della carta: se esce dalla pagina si allinea al bordo destro.
  useLayoutEffect(() => {
    const el = riepilogo.current
    if (!aperto || !el) return
    const pagina = el.closest(".as-telaio__corpo") ?? document.documentElement
    const dove = el.getBoundingClientRect()
    const limite = pagina.getBoundingClientRect()
    // Il bordo utile, non quello esterno: sotto la barra di scorrimento e' gia' fuori.
    setADestra(dove.right > limite.left + pagina.clientLeft + pagina.clientWidth)
    // Scorre solo il corpo della pagina: `scrollIntoView` muoverebbe anche il telaio.
    if (dove.bottom > limite.bottom) pagina.scrollBy?.({ top: dove.bottom - limite.bottom })
    return () => setADestra(false)
  }, [aperto])

  return (
    <li ref={posto}>
      <UnaCarta
        riga={riga}
        nome={
          apribile ? (
            // Un comando, non un collegamento: il foglio veste questa classe su un'ancora.
            <a
              ref={comando}
              className="as-carta-oggetto__apri"
              href="#"
              role="button"
              aria-expanded={aperto}
              aria-controls={aperto ? id : undefined}
              onClick={(e) => {
                e.preventDefault()
                setAperto(!aperto)
              }}
              onKeyDown={(e) => {
                if (e.key !== " ") return
                e.preventDefault()
                setAperto(!aperto)
              }}
            >
              <Nome riga={riga} />
            </a>
          ) : (
            <Nome riga={riga} />
          )
        }
      />
      {apribile && aperto && (
        <div
          ref={riepilogo}
          className="as-produzioni"
          style={aDestra ? { left: "auto", right: 0 } : undefined}
          id={id}
          role="region"
          aria-label={t("archive.productions.of", { nome: nomeDi(riga) })}
        >
          <p className="as-produzioni__capo">{t("archive.productions", { n: numero(riga.productions.length) })}</p>
          <ul className="as-produzioni__voci">
            {riga.productions.map((p, i) => (
              <li key={i}>
                <UnaProduzione produzione={p} />
              </li>
            ))}
          </ul>
        </div>
      )}
    </li>
  )
}

/** Una produzione nel riepilogo: il corredo, quanto, e con che filtri. Cio' che manca lo dice. */
function UnaProduzione({ produzione: p }: { produzione: Produzione }) {
  const ore = oreDi(p.integration_s)
  return (
    <div className="as-produzioni__voce">
      <span className="as-produzioni__corredo">
        <b>{p.optics ?? t("gear.rig.noOptics")}</b>
        <span>{p.camera ?? t("gear.rig.noCamera")}</span>
      </span>
      <span className="as-produzioni__cifre">
        <b>{ore ?? senzaTempo(p.untimed)}</b>
        <span>{t("archive.frames", { n: numero(p.frames) })}</span>
        {ore !== null && p.untimed > 0 && <span>{senzaTempo(p.untimed)}</span>}
      </span>
      <div className="as-produzioni__filtri">
        {p.filters.length > 0 ? (
          <BarraDeiFiltri filtri={p.filters} perFrame={p.integration_s === 0} />
        ) : (
          <NonSiSa>{t("archive.unknown.filters")}</NonSiSa>
        )}
      </div>
    </div>
  )
}

function UnaCarta({ riga, nome }: { riga: Riga; nome: ReactNode }) {
  const ore = oreDi(riga.integration_s)
  const filtri = <Filtri riga={riga} />
  const quante = riga.productions.length
  // Senza frame contati non ci sono produzioni: resta un posto vuoto, e il conto si tace.
  const posti = Math.max(quante, 1)
  return (
    <article
      // Una produzione sola stringe la colonna delle anteprime; oltre quattro vanno tre per riga.
      className={
        posti === 1
          ? "as-carta as-carta-oggetto as-carta-oggetto--una"
          : quante > 4
            ? "as-carta as-carta-oggetto as-carta-oggetto--molte"
            : "as-carta as-carta-oggetto"
      }
      aria-label={nomeDi(riga)}
    >
      {/* Un posto per produzione, vuoto: quante sono lo dice la parola accanto ai dati. */}
      <ul className="as-carta-oggetto__anteprime" aria-hidden="true">
        {Array.from({ length: posti }, (_, i) => (
          <li key={i}>
            <span className="as-carta-oggetto__anteprima">
              <span className="as-carta-oggetto__immagine" />
            </span>
          </li>
        ))}
      </ul>
      <div className="as-carta-oggetto__dati">
        <h2 className="as-carta-oggetto__nome">{nome}</h2>
        <p className="as-carta-oggetto__chi">
          <span>
            <Tipo riga={riga} lungo />
          </span>
          <span>
            <Costellazione riga={riga} lungo />
          </span>
        </p>
        {/* Ogni pezzo non si spezza, e il punto sta col pezzo prima: a capo va un pezzo intero. */}
        <p className="as-carta-oggetto__ore">
          <span className="as-carta-oggetto__pezzo">
            <b>{ore ?? senzaTempo(riga.untimed)}</b>
            {"\u00a0\u00b7"}
          </span>{" "}
          <span className="as-carta-oggetto__pezzo">
            {t("archive.frames", { n: numero(riga.frames) })}
            {ore !== null && riga.untimed > 0 && "\u00a0\u00b7"}
          </span>
          {ore !== null && riga.untimed > 0 && (
            <>
              {" "}
              <span className="as-carta-oggetto__pezzo">{senzaTempo(riga.untimed)}</span>
            </>
          )}
        </p>
        <span className="as-carta-oggetto__segni">
          {quante > 0 && (
            <span className="as-carta-oggetto__quante">{t("archive.productions", { n: numero(quante) })}</span>
          )}
          <Mosaico riga={riga} />
        </span>
      </div>
      {riga.filters.length > 0 ? (
        <div className="as-carta-oggetto__filtri">{filtri}</div>
      ) : (
        <p className="as-carta-oggetto__filtri">
          <NonSiSa>{t("archive.unknown.filters")}</NonSiSa>
        </p>
      )}
      <PannelliDelMosaico pannelli={riga.panel_list} />
    </article>
  )
}
