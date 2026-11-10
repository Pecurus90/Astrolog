import type { Chiave } from "./i18n"

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

/** La parola per un tipo di catalogo, o niente se il codice non lo conosciamo: l'Archivio, la
 *  finestra della notte e quella dell'oggetto dicono lo stesso tipo con la stessa parola. */
export function tipoDi(riga: { type_code: string | null }): Chiave | undefined {
  return riga.type_code ? TIPI[riga.type_code] : undefined
}
