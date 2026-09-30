import { PannelliDelMosaico } from "./PannelliDelMosaico"
import { Filtri, Misure, Mosaico, doveECosa, nomeDi } from "./RigaDellArchivio"
import type { components } from "./api/schema"
import { t } from "./i18n"

type Riga = components["schemas"]["ArchiveObject"]

/**
 * L'Archivio **a carte**: il caso "guardo cosa ho".
 *
 * - **Il pozzo dell'anteprima e' vuoto e tiene il suo posto.** L'immagine non esiste ancora (ne' la
 *   foto finale che caricherai tu, ne' il frame migliore): il foglio l'ha disegnato apposta perche'
 *   aspetti. Vuoto e' il suo stato, non un guasto -- e chi ascolta non lo sente affatto, perche' un
 *   riquadro senza contenuto non e' un'informazione.
 * - **La griglia la fa il foglio**, non questa pagina: quante colonne stanno in una finestra e'
 *   una domanda di larghezza, e una risposta scritta qui sarebbe un secondo posto dove deciderlo.
 */
export function CarteDellArchivio({ righe }: { righe: Riga[] }) {
  return (
    <ul className="as-griglia" aria-label={t("archive.title")}>
      {righe.map((riga) => (
        <li key={riga.key}>
          <UnaCarta riga={riga} />
        </li>
      ))}
    </ul>
  )
}

function UnaCarta({ riga }: { riga: Riga }) {
  const dove = doveECosa(riga)
  return (
    <article className="as-carta">
      {/* Il pozzo vuoto non dice niente e si tace; quando porta l'etichetta del mosaico -- che il
          foglio mette **sopra** l'anteprima, perche' dice cos'e' prima che si legga il nome -- si
          sente, o chi ascolta non saprebbe mai di avere davanti un mosaico. */}
      {riga.panels === null ? (
        <div className="as-carta__anteprima" aria-hidden="true" />
      ) : (
        <div className="as-carta__anteprima">
          <div className="as-carta__segni">
            <Mosaico riga={riga} forma="sopra" />
          </div>
        </div>
      )}
      <div className="as-carta__intestazione">
        <div>
          {dove && <p className="as-soprattitolo as-soprattitolo--riga">{dove}</p>}
          <h2 className="as-carta__titolo as-carta__titolo--riga">{nomeDi(riga)}</h2>
        </div>
      </div>
      <div className="as-carta__corpo as-carta__corpo--colonna">
        <Misure riga={riga} />
        <Filtri riga={riga} />
      </div>
      <PannelliDelMosaico pannelli={riga.panel_list} />
    </article>
  )
}
