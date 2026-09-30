import { FiltriUsati } from "./FiltriUsati"
import { TempoDellePose } from "./TempoDellePose"
import type { components } from "./api/schema"
import { type Chiave, numero, t } from "./i18n"
import { costellazione } from "./costellazioni"

type Riga = components["schemas"]["ArchiveObject"]

/**
 * I pezzi che le **due viste dell'Archivio** dicono allo stesso modo: che cosa e' una riga, se e'
 * un mosaico, e con che filtri l'hai ripreso.
 *
 * Stanno qui e non in una delle due viste perche' le carte e le colonne raccontano la **stessa**
 * riga: scriverli due volte vorrebbe dire che un giorno la carta dice "nebulosa a emissione" e la
 * tabella dice "EMISSION_NEBULA", sullo stesso oggetto.
 */

// Che cosa e' un oggetto, dal codice del catalogo alla parola che l'utente legge. I codici sono
// quelli che il catalogo usa davvero (contati sul catalogo vero, non immaginati); uno che non
// fosse in elenco non si mostra affatto, invece di finire a schermo come sigla tecnica.
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

/** La parola per un tipo di catalogo, o niente: un codice che non conosciamo non si mostra come
 *  sigla tecnica, perche' a chi guarda non dice piu' di un vuoto. */
export function tipoDi(riga: Riga) {
  return riga.type_code ? TIPI[riga.type_code] : undefined
}

/** Il nome dell'oggetto come lo si legge. `key` e' la chiave stabile e puo' essere uno slug di
 *  catalogo (`m-31`): non e' roba da mostrare, ma e' meglio di una riga senza nome. */
export function nomeDi(riga: Riga) {
  return riga.name ?? riga.key
}

/** **Dove e cosa**: la costellazione e il tipo, uniti come li scrive il disegno, oppure
 *  `null` se non si sa nessuno dei due -- un separatore da solo non e' un dato.
 *
 *  Torna il **testo**, non un elemento: un elemento e' sempre vero anche quando dentro non
 *  scrive niente, e chi lo mettesse in un `&&` si ritroverebbe il paragrafo vuoto a schermo,
 *  col suo margine, e i titoli di quelle carte piu' in basso delle altre. */
export function doveECosa(riga: Riga): string | null {
  const tipo = tipoDi(riga)
  const pezzi = [riga.constellation && costellazione(riga.constellation), tipo && t(tipo)].filter(Boolean)
  return pezzi.length === 0 ? null : pezzi.join(" \u00b7 ")
}

/** Quante pose e quanto tempo. Le ore passano da `TempoDellePose`, che e' la casa della regola
 *  "le ore **solo se ci sono**": un oggetto le cui pose non dicono la durata ha ripreso, e non si
 *  sa per quanto. */
export function Misure({ riga }: { riga: Riga }) {
  return (
    <div className="as-misure">
      <span className="as-misure__voce">
        <span className="as-misure__nome">{t("archive.measure.frames")}</span>
        <span className="as-misure__dato">{numero(riga.frames)}</span>
      </span>
      <span className="as-misure__voce">
        <span className="as-misure__nome">{t("archive.measure.time")}</span>
        <span className="as-misure__dato">
          <TempoDellePose secondi={riga.integration_s} senzaTempo={riga.untimed} />
        </span>
      </span>
    </div>
  )
}

// Le due forme dell'etichetta, coi nomi interi: chi controlla le classi del foglio legge queste.
const FORME = { sopra: "as-badge--sopra", muto: "as-badge--muto" } as const

/** L'etichetta di un mosaico: *mosaico -- 4 pannelli*, o niente per un oggetto. Il numero e la
 *  parola sono sempre scritti, e il segno e' solo per l'occhio: chi non vede il colore, o ascolta,
 *  legge l'etichetta per intero. Due forme dal foglio: sopra l'anteprima della carta, o muta in
 *  una colonna, dove ce n'e' una per riga e un fondo per ognuna farebbe mille macchie. */
export function Mosaico({ riga, forma }: { riga: Riga; forma: keyof typeof FORME }) {
  if (riga.panels === null) return null
  return (
    <span className={`as-badge as-badge--mosaico ${FORME[forma]}`}>
      <span className="as-badge__segno" aria-hidden="true">
        {"\u229e"}
      </span>
      {t("archive.mosaic")} <span className="as-badge__conta">{numero(riga.panels)}</span>{" "}
      {t("archive.mosaic.panels")}
    </span>
  )
}

/** Con che filtri l'hai ripreso, dal piu' usato. Nessun filtro riconosciuto non si scrive: una
 *  fila vuota sembrerebbe un guasto, mentre vuol dire solo che i file non lo dicevano. */
export function Filtri({ riga }: { riga: Riga }) {
  return <FiltriUsati filtri={riga.filters} etichetta={t("archive.filters")} />
}
