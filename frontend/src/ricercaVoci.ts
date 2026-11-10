import type { components } from "./api/schema"
import { type Chiave, dateLette, notte, numero, oreEMinuti, t } from "./i18n"
import { SEZIONI } from "./Impostazioni"
import { PAGINE } from "./pagine"

type Trovati = components["schemas"]["SearchResult"]
type Pezzo = components["schemas"]["FoundPiece"]
type Perche = components["schemas"]["NightsWhy"]

/** Una voce gia' pronta: cosa dice e quale pagina apre; un oggetto apre la sua finestra. */
export type Voce = {
  a: string
  nome: string
  accanto: string | null
  dice: string
  oggetto?: { chiave: string; nome: string }
}
export type Gruppo = { titolo: Chiave; segno: string; perche: string; voci: Voce[]; totale: number }

// [T] Cerca.dc.html:75 the group signs
export const SEGNI = {
  oggetti: "M12 3l2.2 5.4 5.8.5-4.4 3.8 1.4 5.7L12 15.4l-5 3 1.4-5.7L4 8.9l5.8-.5z",
  notti: "M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z",
  attrezzatura: "M4 15l11-6.5 2.5 4.2-11 6.5zM10 16.5L8 21M11 16l3 5",
  siti: "M12 21s6-5.6 6-10.2a6 6 0 0 0-12 0C6 15.4 12 21 12 21zM12 8.6a2.2 2.2 0 1 0 0 4.4 2.2 2.2 0 0 0 0-4.4z",
  pagine: "M4 4h7v9H4zM13 4h7v5h-7zM13 11h7v9h-7zM4 15h7v5H4z",
  impostazioni:
    "M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1 7 17M17 7l2.1-2.1",
} as const

// [T] Cerca.dc.html:121 five per group, then "5 di N"
const PER_GRUPPO = 5

/** Le voci delle Impostazioni che si cercano (tavola, `IMPV`), solo dove l'app ha la sezione. */
const IMPOSTAZIONI: readonly { nome: Chiave; parole?: Chiave; sezione: string }[] = [
  { nome: "search.set.coords", sezione: "/impostazioni/sito" },
  { nome: "search.set.bortle", parole: "search.set.bortle.w", sezione: "/impostazioni/sito" },
  { nome: "search.set.default", sezione: "/impostazioni/sito" },
  { nome: "search.set.folders", parole: "search.set.folders.w", sezione: "/impostazioni/cartelle" },
  { nome: "search.set.scan", sezione: "/impostazioni/letture" },
  {
    nome: "search.set.meteoblue",
    parole: "search.set.meteoblue.w",
    sezione: "/impostazioni/servizi",
  },
  {
    nome: "search.set.astap",
    parole: "search.set.astap.w",
    sezione: "/impostazioni/riconoscitore",
  },
  { nome: "search.set.moon", parole: "search.set.moon.w", sezione: "/impostazioni/luna" },
  {
    nome: "search.set.services",
    parole: "search.set.services.w",
    sezione: "/impostazioni/servizi",
  },
  { nome: "search.set.backup", sezione: "/impostazioni/backup" },
]

/** Senza accenti, minuscolo, solo lettere, cifre e `/`: "NGC 7000" e "ngc7000" si equivalgono. */
function piega(s: string): string {
  return s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9/]/g, "")
}

/** Come nella tavola (`prende`): il nome intero o una sua parola comincia col testo scritto.
 *  Pagine e voci delle Impostazioni si cercano qui perche' i loro nomi stanno solo nei testi. */
function prende(scritto: string, campi: readonly string[]): boolean {
  const q = piega(scritto)
  return (
    q !== "" &&
    campi.some(
      (c) =>
        piega(c).startsWith(q) ||
        c.split(/[\s\-\u00b7,]+/).some((w) => w !== "" && piega(w).startsWith(q)),
    )
  )
}

function gruppo(
  titolo: Chiave,
  segno: string,
  tutte: Voce[],
  totale = tutte.length,
  perche = "",
): Gruppo {
  return { titolo, segno, perche, voci: tutte.slice(0, PER_GRUPPO), totale }
}

/** I gruppi con voci, nell'ordine della tavola; Progetti arriva con la sua pagina. */
export function gruppiDi(trovati: Trovati | undefined, scritto: string): Gruppo[] {
  const pagine = PAGINE.filter((p) => prende(scritto, [t(p.chiave)])).map((p) => ({
    a: p.a,
    nome: t(p.chiave),
    accanto: null,
    dice: "",
  }))
  const sezioni = new Map(SEZIONI.filter((s) => s.elemento).map((s) => [s.a, t(s.chiave)]))
  const impostazioni = IMPOSTAZIONI.filter(
    (v) =>
      sezioni.has(v.sezione) && prende(scritto, [t(v.nome), ...(v.parole ? [t(v.parole)] : [])]),
  ).map((v) => ({
    a: v.sezione,
    nome: t(v.nome),
    accanto: sezioni.get(v.sezione) ?? null,
    dice: "",
  }))
  const gruppi = trovati ? gruppiDellArchivio(trovati) : []
  gruppi.push(gruppo("search.group.settings", SEGNI.impostazioni, impostazioni))
  gruppi.push(gruppo("search.group.pages", SEGNI.pagine, pagine))
  return gruppi.filter((g) => g.voci.length > 0)
}

function gruppiDellArchivio(trovati: Trovati): Gruppo[] {
  const { objects, nights, gear, sites } = trovati
  return [
    gruppo(
      "search.group.objects",
      SEGNI.oggetti,
      objects.items.map((o) => ({
        // outside the frame, no window: the Archive narrowed to it
        a: `/archivio?key=${encodeURIComponent(o.key)}`,
        oggetto: { chiave: o.key, nome: o.name ?? o.key },
        nome: o.name ?? o.key,
        accanto: o.common_name,
        dice:
          o.panels === null
            ? quanto(o.frames, o.integration_s)
            : `${quanto(o.frames, o.integration_s)} \u00b7 ${t("search.mosaic", { n: numero(o.panels) })}`,
      })),
      objects.total,
    ),
    gruppo(
      "search.group.nights",
      SEGNI.notti,
      nights.items.map((n) => ({
        a: `/notti?notte=${n.id}`,
        nome: notte(n.night_date),
        accanto: n.site,
        dice: quanto(n.frames, n.integration_s),
      })),
      nights.total,
      percheDi(nights.why),
    ),
    gruppo(
      "search.group.gear",
      SEGNI.attrezzatura,
      gear.items.map((p) => ({
        a: `/attrezzatura?pezzo=${p.kind === "filter" ? "filtro" : "strumento"}-${p.id}`,
        nome: p.name,
        accanto: t(`search.kind.${p.kind}`),
        ...usoDi(p),
      })),
      gear.total,
    ),
    gruppo(
      "search.group.sites",
      SEGNI.siti,
      sites.items.map((s) => ({
        a: `/impostazioni/sito?sito=${s.id}`,
        nome: s.name,
        accanto: null,
        dice: t("search.site.nights", { n: numero(s.nights) }),
      })),
      sites.total,
    ),
  ]
}

/** Perche' quelle notti: le date lette, l'oggetto ripreso, o piu' oggetti. Lo decide il backend. */
function percheDi(perche: Perche | null): string {
  if (perche === null) return ""
  if (perche.by === "dates") return dateLette(perche.dates)
  if (perche.by === "object" && perche.object !== null)
    return t("search.why.object", { nome: perche.object })
  return t("search.why.objects")
}

/** Frame e ore coi minuti come la tavola (`3 h 24`, `< 6 min`); senza durata "senza durata", mai "0 h". */
function quanto(frame: number, secondi: number): string {
  const n = t("search.frames", { n: numero(frame) })
  return secondi > 0
    ? t("search.timed", { frame: n, ore: oreEMinuti(secondi) })
    : t("search.untimed", { frame: n })
}

/** Le ore di un pezzo, o perche' non ci sono: il perche' lo decide il backend. */
function usoDi(pezzo: Pezzo): { dice: string } {
  if (!pezzo.counted) return { dice: t("search.notCounted") }
  if (pezzo.no_hours !== null || pezzo.frames === null || pezzo.integration_s === null) {
    return { dice: t(pezzo.no_hours === "no_rig" ? "search.noRig" : "search.filesSilent") }
  }
  return { dice: quanto(pezzo.frames, pezzo.integration_s) }
}
