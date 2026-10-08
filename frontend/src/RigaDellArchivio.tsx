import type { ReactNode } from "react"

import { BarraDeiFiltri } from "./FiltriUsati"
import { Icon } from "./Icons"
import type { components } from "./api/schema"
import { type Chiave, numero, ore, t } from "./i18n"
import { costellazione } from "./costellazioni"

type Riga = components["schemas"]["ArchiveObject"]

/**
 * I pezzi che le **due viste dell'Archivio** dicono allo stesso modo (disegno v31,
 * `73-pagina-archivio`): come si chiama una riga, che cos'e', se e' un mosaico, quanto e con che
 * filtri l'hai ripresa.
 *
 * Stanno qui e non in una delle due viste perche' le carte e le colonne raccontano la **stessa**
 * riga: scriverli due volte vorrebbe dire che un giorno la carta dice "nebulosa a emissione" e la
 * tabella dice "EMISSION_NEBULA", sullo stesso oggetto.
 */

// Che cosa e' un oggetto, dal codice del catalogo alla parola che l'utente legge. I codici sono
// quelli che il catalogo usa davvero (contati sul catalogo vero, non immaginati); uno che non
// fosse in elenco non arriva a schermo come sigla tecnica: dice "non si sa".
const TIPI: Record<string, Chiave> = {
  GALAXY: "archive.type.galaxy",
  GALAXY_CLUSTER: "archive.type.galaxyCluster",
  GALAXY_GROUP: "archive.type.galaxyGroup",
  GALAXY_PAIR: "archive.type.galaxyPair",
  NEBULA: "archive.type.nebula",
  DARK_NEBULA: "archive.type.darkNebula",
  EMISSION_NEBULA: "archive.type.emissionNebula",
  REFLECTION_NEBULA: "archive.type.reflectionNebula",
  PLANETARY_NEBULA: "archive.type.planetaryNebula",
  HII_REGION: "archive.type.hiiRegion",
  SUPERNOVA_REMNANT: "archive.type.supernovaRemnant",
  OPEN_CLUSTER: "archive.type.openCluster",
  GLOBULAR_CLUSTER: "archive.type.globularCluster",
  STAR_CLUSTER: "archive.type.starCluster",
  STAR: "archive.type.star",
  DOUBLE_STAR: "archive.type.doubleStar",
  NOVA_WR: "archive.type.novaWr",
  OTHER: "archive.type.other",
  UNKNOWN: "archive.type.unknown",
}

/** La parola per un tipo di catalogo, o niente se il codice non lo conosciamo. */
export function tipoDi(riga: Riga) {
  return riga.type_code ? TIPI[riga.type_code] : undefined
}

/** Il nome dell'oggetto come lo si legge. `key` e' la chiave stabile e puo' essere uno slug di
 *  catalogo (`m-31`): non e' roba da mostrare, ma e' meglio di una riga senza nome. */
export function nomeDi(riga: Riga) {
  return riga.name ?? riga.key
}

/** Il nome nella veste del foglio: in cifre e in freddo una sigla di catalogo, nel testo il nome
 *  di un mosaico, che gliel'hai dato tu. `inRiga` e' la misura della tabella. */
export function Nome({ riga, inRiga = false }: { riga: Riga; inRiga?: boolean }) {
  const tuo = riga.panels !== null
  if (inRiga) {
    return (
      <span
        className={
          tuo
            ? "as-nome-oggetto as-nome-oggetto--utente as-nome-oggetto--riga"
            : "as-nome-oggetto as-nome-oggetto--riga"
        }
      >
        {nomeDi(riga)}
      </span>
    )
  }
  return (
    <span className={tuo ? "as-nome-oggetto as-nome-oggetto--utente" : "as-nome-oggetto"}>
      {nomeDi(riga)}
    </span>
  )
}

/** Cio' che non si sa: il tondo tratteggiato dell'ignoto **e una parola**, mai un trattino e mai
 *  il solo colore (WCAG 1.4.1). */
export function NonSiSa({ children }: { children: ReactNode }) {
  return <span className="as-nonsisa">{children}</span>
}

/** Il tipo, o che non si sa. `lungo` dice anche **cosa** non si sa: nella carta non c'e'
 *  un'intestazione di colonna a dirlo. */
export function Tipo({ riga, lungo = false }: { riga: Riga; lungo?: boolean }) {
  const tipo = tipoDi(riga)
  if (tipo) return <>{t(tipo)}</>
  return <NonSiSa>{t(lungo ? "archive.unknown.type" : "archive.unknown")}</NonSiSa>
}

/** La costellazione col suo nome, non con la sigla; o che non si sa. */
export function Costellazione({ riga, lungo = false }: { riga: Riga; lungo?: boolean }) {
  if (riga.constellation) return <>{costellazione(riga.constellation)}</>
  return <NonSiSa>{t(lungo ? "archive.unknown.constellation" : "archive.unknown")}</NonSiSa>
}

/** Le ore di una riga, o niente se nessun frame dice la durata: "0 h" direbbe che non hai
 *  ripreso. Chi chiama scrive allora i frame "senza tempo". */
export function oreDi(secondi: number): string | null {
  return secondi > 0 ? t("review.objects.hours", { h: ore(secondi) }) : null
}

/** I frame che non dicono la durata, a parole. */
export function senzaTempo(quanti: number): string {
  return t("review.objects.untimed", { n: numero(quanti) })
}

/** Il segno di un mosaico: *mosaico - 4 pannelli*, o niente per un oggetto. La parola e il numero
 *  sono scritti: il disegno accanto e' solo per l'occhio. */
export function Mosaico({ riga }: { riga: Riga }) {
  if (riga.panels === null) return null
  return (
    <span className="as-archivio__mosaico">
      <Icon name="mosaico" />
      {t("archive.mosaic.badge", { n: numero(riga.panels) })}
    </span>
  )
}

/** Con che filtri l'hai ripresa: la barra delle Notti, che pesa le ore di ognuno (i frame, se
 *  nessuno dice la durata). `null` se i file non dicono il filtro: chi chiama lo scrive a parole. */
export function Filtri({ riga }: { riga: Riga }) {
  if (riga.filters.length === 0) return null
  return <BarraDeiFiltri filtri={riga.filters} perFrame={riga.integration_s === 0} />
}
