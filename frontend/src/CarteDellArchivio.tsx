import type { ReactNode } from "react"

import { PannelliDelMosaico } from "./PannelliDelMosaico"
import { Costellazione, Filtri, Mosaico, Nome, NonSiSa, Tipo, nomeDi, oreDi, senzaTempo } from "./RigaDellArchivio"
import type { components } from "./api/schema"
import { gesto } from "./componenti/gesto"
import { numero, t } from "./i18n"

type Riga = components["schemas"]["ArchiveObject"]

/**
 * L'Archivio **a carte** (disegno v31, la carta "Di lato"): il caso "guardo cosa ho".
 *
 * - **Un posto di anteprima per produzione**, vuoto: l'immagine non esiste ancora. Vuoto e' il
 *   suo stato, non un guasto, e chi ascolta non lo sente. Una produzione e' la riga ripresa con
 *   un'ottica e una camera (`docs/domini/archivio.md`), e le manda la rotta.
 * - **La griglia la fa il foglio**, non questa pagina.
 * - **Il tocco sulla carta apre la finestra dell'oggetto** (tavola v76), con le produzioni una
 *   alla volta: il nome e' il comando, e il foglio ne stende l'area su tutta la carta.
 */
export function CarteDellArchivio({ righe, onApri }: { righe: Riga[]; onApri: (key: string) => void }) {
  return (
    <ul className="as-archivio__carte" aria-label={t("archive.title")}>
      {righe.map((riga) => (
        <li key={riga.key}>
          <UnaCarta
            riga={riga}
            nome={
              <a
                className="as-carta-oggetto__apri"
                href="#"
                aria-haspopup="dialog"
                onClick={gesto(() => onApri(riga.key))}
              >
                <Nome riga={riga} />
              </a>
            }
          />
        </li>
      ))}
    </ul>
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
            {"\u00A0\u00B7"}
          </span>{" "}
          <span className="as-carta-oggetto__pezzo">
            {t("archive.frames", { n: numero(riga.frames) })}
            {ore !== null && riga.untimed > 0 && "\u00A0\u00B7"}
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
