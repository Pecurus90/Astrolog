import type { components } from "./api/schema"
import { costellazione } from "./costellazioni"
import { type Chiave, numero, oreEMinuti, t } from "./i18n"
import { tipoDi } from "./RigaDellArchivio"

export type Elenco = components["schemas"]["ArchiveList"]
export type Riga = components["schemas"]["ArchiveObject"]
export type Criterio = components["schemas"]["ArchiveCriterion"]
export type ChiaveCriterio = Criterio["key"]
export type Voce = Criterio["options"][number]
export type Intero = components["schemas"]["ArchiveWhole"]
export type Fuori = components["schemas"]["ArchiveUnresolved"]

// Il punto in mezzo che separa i pezzi di una riga (tavola).
export const PUNTO = ` ${String.fromCharCode(0xb7)} `

// I criteri nell'ordine della tavola (Archivio.dc.html 140): anche l'indirizzo li scrive cosi'.
export const CRITERI: readonly ChiaveCriterio[] = [
  "year",
  "type",
  "constellation",
  "filter",
  "form",
  "site",
  "optics",
  "camera",
  "catalog",
]

export const ORDINI = ["name", "hours", "recent"] as const
export type Ordine = (typeof ORDINI)[number]

const ORDINE: Record<Ordine, Chiave> = {
  name: "archive.sort.name",
  hours: "archive.sort.hours",
  recent: "archive.sort.recent",
}
const SINTESI: Record<Ordine, Chiave> = {
  name: "archive.summary.name",
  hours: "archive.summary.hours",
  recent: "archive.summary.recent",
}

export const parolaOrdine = (o: Ordine): string => t(ORDINE[o])

/** Il nome di un criterio, come titolo del suo gruppo. */
export const nomeCriterio = (k: ChiaveCriterio): string => t(`archive.criteria.${k}` as Chiave)

/** La parola di una voce: famiglia e forma si traducono, i nomi dei pezzi arrivano col dato. */
export function nomeVoce(k: ChiaveCriterio, v: Voce): string {
  if (k === "constellation") return costellazione(v.value)
  if (k === "type") return t(`archive.family.${v.value}` as Chiave)
  if (k === "form") return t(`archive.form.${v.value}` as Chiave)
  return v.label ?? v.value
}

/** La testa: "240 oggetti, di cui 3 mosaici" e "486 ore, 18 430 frame, 212 notti". */
export function testa(i: Intero): { n: string; parola: string; sotto: string } {
  const mosaici =
    i.mosaics === 0
      ? ""
      : i.mosaics === 1
        ? t("archive.head.mosaics.one")
        : t("archive.head.mosaics", { n: numero(i.mosaics) })
  const parti = [
    i.integration_s > 0 ? oreEMinuti(i.integration_s) : null,
    t(i.frames === 1 ? "archive.frames.one" : "archive.frames", { n: numero(i.frames) }),
    // zero notti con dei frame vuol dire che i frame non la sanno (nessun sito): non si scrive
    i.nights > 0
      ? t(i.nights === 1 ? "archive.head.nights.one" : "archive.head.nights", {
          n: numero(i.nights),
        })
      : null,
  ]
  return {
    n: numero(i.rows),
    parola: t(i.rows === 1 ? "archive.head.object" : "archive.head.objects") + mosaici,
    sotto: parti.filter(Boolean).join(PUNTO),
  }
}

/** Accanto alla ricerca: quanti con i criteri, o quanti ne vedi su quanti e in che ordine. */
export function sintesi(e: Elenco, viste: number, attivi: number, ordine: Ordine): string {
  if (attivi > 0) {
    return t(e.total === 1 ? "archive.summary.found.one" : "archive.summary.found", {
      n: numero(e.total),
    })
  }
  return t(SINTESI[ordine], { n: numero(viste), tot: numero(e.total) })
}

/** "Mostra N oggetti" del telefono, sotto i criteri. */
export function mostra(totale: number): string {
  if (totale === 0) return t("archive.show.none")
  return t(totale === 1 ? "archive.show.one" : "archive.show", { n: numero(totale) })
}

export interface Pezzi {
  nome: string
  comune: string
  sub: string
  ore: string
  fr: string
  tag: string
  prod: string
  filT: string
  aria: string
}

/** Cio' che carta ed elenco dicono di una riga, gia' in parole (tavola, `carte`, 166-170). */
export function pezzi(r: Riga): Pezzi {
  const nome = r.name ?? r.key
  const mosaico = r.panels !== null
  const comune =
    r.common_name ?? (mosaico ? t("archive.mosaic.of", { n: numero(r.panels ?? 0) }) : "")
  const tipo = tipoDi(r)
  const sub = [
    tipo ? t(tipo) : t("archive.unknown.type"),
    r.constellation ? costellazione(r.constellation) : t("archive.unknown.constellation"),
  ].join(PUNTO)
  const conTempo = r.integration_s > 0
  const frame = t(r.frames === 1 ? "archive.frames.one" : "archive.frames", { n: numero(r.frames) })
  const ore = conTempo ? oreEMinuti(r.integration_s) : frame
  const senza = t("archive.untimed", { n: numero(r.untimed) })
  const fr = conTempo
    ? [frame, r.untimed > 0 ? senza : ""].filter(Boolean).join(PUNTO)
    : t("archive.untimed.all")
  const n = r.productions.length
  const tag = mosaico
    ? t("archive.mosaic.badge", { n: numero(r.panels ?? 0) })
    : n > 1
      ? t("archive.productions", { n: numero(n) })
      : ""
  const prod = mosaico
    ? t("archive.list.mosaic", { n: numero(r.panels ?? 0) })
    : n > 1
      ? t("archive.productions", { n: numero(n) })
      : t("archive.list.one")
  const filT = r.filters.length
    ? r.filters.map((f) => f.name).join(PUNTO)
    : t("archive.unknown.filters")
  const aria = t("archive.card.aria", {
    nome: [nome, comune].filter(Boolean).join(", "),
    ore: conTempo ? ore : t("archive.untimed.all"),
  })
  return { nome, comune, sub, ore, fr, tag, prod, filT, aria }
}

/** La carta dei frame senza oggetto: "Non risolti" senza ASTAP, se no "Senza oggetti
 *  identificati" (tavola, stato "nessun oggetto identificato"). */
export function pezziFuori(f: Fuori): Pezzi {
  const senzaAstap = f.solver_missing
  const nome = t(senzaAstap ? "archive.unresolved" : "archive.unnamed")
  const frame = t(f.frames === 1 ? "archive.frames.one" : "archive.frames", { n: numero(f.frames) })
  const conTempo = f.integration_s > 0
  return {
    nome,
    comune: t(senzaAstap ? "archive.unresolved.why" : "archive.unnamed.why"),
    // la tavola dice gruppi e pannelli, che l'API non conta: la riga resta vuota
    sub: "",
    ore: conTempo ? oreEMinuti(f.integration_s) : frame,
    fr: conTempo ? frame : t("archive.untimed.all"),
    tag: t(senzaAstap ? "archive.unresolved.tag" : "archive.unnamed.tag"),
    prod: String.fromCharCode(0x2014),
    filT: f.filters.length
      ? f.filters.map((x) => x.name).join(PUNTO)
      : t("archive.unknown.filters"),
    aria: t("archive.outside.aria", { nome, frame }),
  }
}
