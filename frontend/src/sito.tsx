import { useState } from "react"

import { api } from "./api/client"
import type { components } from "./api/schema"
import { type Asse, coordinataDa, numero, numeroNelCampo, t } from "./i18n"

type Posto = components["schemas"]["PlaceOut"]

/** The nine Bortle classes, in reading order: the scale, not a computed range. */
export const CLASSI = [1, 2, 3, 4, 5, 6, 7, 8, 9] as const
export type ClasseDiCielo = (typeof CLASSI)[number]

/** [C WGS 84] latitude up to 90 degrees from the equator, longitude up to 180 from Greenwich. */
export const TETTO: Record<Asse, number> = { lat: 90, lon: 180 }

/**
 * A site being written at the first run: name, point, sky.
 *
 * - **The manual road is always open**, not only when the search fails: a dark site may have no
 *   network. So the **name is a field of its own**.
 * - **A coordinate is read back by `coordinataDa`**, not `Number`: the field takes the comma, and
 *   an empty field is no coordinate (`Number("")` is zero, a point in the Gulf of Guinea).
 * - **A sky not declared stays not declared**: class 1 as a default would land in the database
 *   as an answer.
 */
export type CampiDelSito = ReturnType<typeof useCampiDelSito>

export function useCampiDelSito() {
  const [nome, setNome] = useState("")
  const [lat, setLat] = useState("")
  const [lon, setLon] = useState("")
  const [cielo, setCielo] = useState<ClasseDiCielo | undefined>(undefined)
  // coordinates taken from a place found by name, until someone rewrites them by hand
  const [trovate, setTrovate] = useState(false)

  const fuoriScala = (scritto: string, asse: Asse) => {
    if (scritto.trim() === "") return undefined
    const n = coordinataDa(scritto, asse)
    if (!Number.isFinite(n)) return t(asse === "lat" ? "site.notANumber" : "site.notANumber.lon")
    if (Math.abs(n) <= TETTO[asse]) return undefined
    return t("site.range", { tetto: numero(TETTO[asse]) })
  }

  return {
    nome,
    lat,
    lon,
    cielo,
    setNome,
    setLat: (v: string) => {
      setTrovate(false)
      setLat(v)
    },
    setLon: (v: string) => {
      setTrovate(false)
      setLon(v)
    },
    /** `undefined`: the chosen class pressed again, no sky declared. */
    setCielo,
    fuoriScala,
    /** The command also reads what the fields already say: lit over a latitude of 120 degrees it
     *  would send a write the backend refuses. */
    valido:
      nome.trim() !== "" &&
      Number.isFinite(coordinataDa(lat, "lat")) &&
      Number.isFinite(coordinataDa(lon, "lon")) &&
      fuoriScala(lat, "lat") === undefined &&
      fuoriScala(lon, "lon") === undefined,
    /** What goes to the API. The class is not stored: the backend derives the brightness. */
    corpo: () => ({
      name: nome.trim(),
      latitude: coordinataDa(lat, "lat"),
      longitude: coordinataDa(lon, "lon"),
      coords_source: trovate ? ("place" as const) : ("declared" as const),
      ...(cielo !== undefined ? { bortle: cielo } : {}),
    }),
    prendiDa: (p: Posto) => {
      setNome(p.name)
      setLat(numeroNelCampo(p.latitude))
      setLon(numeroNelCampo(p.longitude))
      setTrovate(true)
    },
  }
}

/** Search by name, first run and Impostazioni: without network `GET /places` answers an empty
 *  list (sito.md); a fault, answered or not, is "rotto", not "no place". */
export function useCercaPosto(onParte: () => void = () => undefined) {
  const [q, setQ] = useState("")
  const [stato, setStato] = useState<"fermo" | "cerco" | "rotto">("fermo")
  const [trovati, setTrovati] = useState<Posto[] | null>(null)
  const cerca = async (): Promise<void> => {
    if (!q.trim() || stato === "cerco") return
    setStato("cerco")
    onParte()
    const r = await api
      .GET("/api/v1/places", { params: { query: { q: q.trim() } } })
      .catch(() => ({ data: undefined, error: true }))
    setStato(r.error ? "rotto" : "fermo")
    setTrovati(r.error || !r.data ? null : r.data.items)
  }
  return { q, setQ, stato, trovati, setTrovati, cerca }
}
