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

/**
 * L'Archivio **a carte** (disegno v31, la carta "Di lato"): il caso "guardo cosa ho".
 *
 * - **Il posto dell'anteprima e' vuoto e tiene il suo posto.** L'immagine non esiste ancora: vuoto
 *   e' il suo stato, non un guasto, e chi ascolta non lo sente. Oggi e' uno solo; con le
 *   produzioni sara' uno per produzione.
 * - **La griglia la fa il foglio**, non questa pagina.
 * - **La carta non si tocca**: non apre niente finche' le produzioni non ci sono.
 */
export function CarteDellArchivio({ righe }: { righe: Riga[] }) {
  return (
    <ul className="as-archivio__carte" aria-label={t("archive.title")}>
      {righe.map((riga) => (
        <li key={riga.key}>
          <UnaCarta riga={riga} />
        </li>
      ))}
    </ul>
  )
}

function UnaCarta({ riga }: { riga: Riga }) {
  const ore = oreDi(riga.integration_s)
  const filtri = <Filtri riga={riga} />
  return (
    <article className="as-carta as-carta-oggetto as-carta-oggetto--una" aria-label={nomeDi(riga)}>
      <ul className="as-carta-oggetto__anteprime" aria-hidden="true">
        <li>
          <span className="as-carta-oggetto__anteprima">
            <span className="as-carta-oggetto__immagine" />
          </span>
        </li>
      </ul>
      <div className="as-carta-oggetto__dati">
        <h2 className="as-carta-oggetto__nome">
          <Nome riga={riga} />
        </h2>
        <p className="as-archivio__chi as-carta-oggetto__chi">
          <Tipo riga={riga} lungo /> {"\u00b7"} <Costellazione riga={riga} lungo />
        </p>
        <p className="as-carta-oggetto__ore">
          <b>{ore ?? senzaTempo(riga.untimed)}</b> {"\u00b7"} {t("archive.frames", { n: numero(riga.frames) })}
          {ore !== null && riga.untimed > 0 && (
            <>
              {" "}
              <span className="as-archivio__senza">
                {"\u00b7"} {senzaTempo(riga.untimed)}
              </span>
            </>
          )}
        </p>
        {riga.panels !== null && (
          <span className="as-carta-oggetto__segni">
            <Mosaico riga={riga} />
          </span>
        )}
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
