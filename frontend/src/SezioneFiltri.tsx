import { useContext, useState } from "react"

import { Avviso } from "./componenti/Avviso"
import { FormatoConf, statoDi } from "./ConfermareGuscio"
import { Campi, Domanda, Nota, Parte, Risposte, Sotto, rigaDeiFrame, voce } from "./Domanda"
import { Sezione } from "./Sezione"
import { provaDegliOggetti, provaDegliStrumenti } from "./Soggetti"
import { BANDE, nomeDellaBanda } from "./TendinaDellaBanda"
import type { components } from "./api/schema"
import { type Chiave, numero, numeroNelCampo, t } from "./i18n"

type Filtro = components["schemas"]["FilterOut"]
type Mio = components["schemas"]["FilterCandidate"]
type Modello = components["schemas"]["FilterModelOut"]
type Risposta = components["schemas"]["FilterEdit"]
type Banda = components["schemas"]["BandIn"]["band"]

/**
 * I filtri che l'app ha trovato negli header e **non riconosce** (Marco, 25/9/2026): "che filtro e'
 * H?". Quelli che riconosce non sono una domanda e qui non arrivano.
 *
 * **Tre strade, e si sa sempre in quale sei** (Marco, 14/9/2026; tavola v82, 190-199):
 *
 * - **filtro esistente**: uno dei filtri con la banda nota; la grafia dell'header diventa quello.
 * - **dal catalogo**: si cerca fra i modelli in commercio; marca, nome e banda **non si scrivono**,
 *   sono il modello. Senza l'elenco dei modelli la strada si spegne e lo si dice.
 * - **nuovo filtro**: nome, una o piu' bande (i filtri doppi ne hanno due), la larghezza facoltativa.
 *   Parte solo intero: un filtro a meta' non e' una modifica.
 *
 * Il filtro **esiste gia'**: nasce dagli header con banda `UNKNOWN`. Qui gli si da' un'identita'.
 */
export function SezioneFiltri({
  filtri,
  miei,
  modelli,
  senzaModelli,
  risposte,
  onRisposta,
}: {
  filtri: Filtro[]
  miei: Mio[]
  modelli: Modello[]
  /** L'elenco dei modelli non si e' potuto leggere: non e' un elenco vuoto. */
  senzaModelli: boolean
  risposte: Record<number, Risposta>
  onRisposta: (id: number, r: Risposta | null) => void
}) {
  return (
    <Sezione
      quale="filters"
      domanda={t("review.filters.why")}
      voci={filtri}
      chiave={(f) => f.id}
      riga={(f) => (
        <RigaFiltri
          filtro={f}
          miei={miei}
          modelli={modelli}
          senzaModelli={senzaModelli}
          risposta={risposte[f.id]}
          onRisposta={onRisposta}
        />
      )}
    />
  )
}

// I tre modi di rispondere, esclusivi: se ne vede uno alla volta.
const MODI = {
  mio: "review.filters.way.mine",
  catalogo: "review.filters.way.catalog",
  nuovo: "review.filters.way.new",
} as const satisfies Record<string, Chiave>
type Modo = keyof typeof MODI

/** Cio' che si scrive per un filtro nuovo: nome, bande nell'ordine dell'elenco, larghezze. */
interface Nuovo {
  nome: string
  bande: readonly Banda[]
  nm: Partial<Record<Banda, string>>
}

/** Il filtro nuovo come risposta, o `null` finche' non e' intero (nome, una banda, larghezze lette). */
function diNuovo(id: number, n: Nuovo): Risposta | null {
  if (n.nome.trim() === "" || n.bande.length === 0) return null
  const bande = n.bande.map((band) => {
    const scritta = (n.nm[band] ?? "").trim()
    return { band, width_nm: scritta === "" ? null : Number(scritta.replace(",", ".")) }
  })
  // una larghezza che non e' un numero non si manda vuota: la risposta aspetta
  if (bande.some((b) => b.width_nm !== null && !(Number.isFinite(b.width_nm) && b.width_nm > 0)))
    return null
  return {
    id,
    name: n.nome.trim(),
    bands: bande.map((b) => (b.width_nm === null ? { band: b.band } : b)),
  }
}

/** Il modo da cui riparte una domanda gia' in mano (la sezione si rimonta), o quello consigliato. */
function modoDi(risposta: Risposta | undefined, senzaModelli: boolean): Modo {
  if (risposta?.catalog_id != null) return "catalogo"
  if (risposta?.merge_into != null) return "mio"
  if (risposta) return "nuovo"
  return senzaModelli ? "mio" : "catalogo"
}

function RigaFiltri({
  filtro,
  miei,
  modelli,
  senzaModelli,
  risposta,
  onRisposta,
}: {
  filtro: Filtro
  miei: Mio[]
  modelli: Modello[]
  senzaModelli: boolean
  risposta: Risposta | undefined
  onRisposta: (id: number, r: Risposta | null) => void
}) {
  const [scelto, setModo] = useState<Modo>(() => modoDi(risposta, senzaModelli))
  // l'elenco che cade dopo il disegno spegne il catalogo anche qui: si torna ai filtri propri
  const modo: Modo = senzaModelli && scelto === "catalogo" ? "mio" : scelto
  const [cerca, setCerca] = useState("")
  const [mio, setMio] = useState<number | null>(risposta?.merge_into ?? null)
  const [modello, setModello] = useState<string | null>(risposta?.catalog_id ?? null)
  const [nuovo, setNuovo] = useState<Nuovo>(() => ({
    nome: risposta?.catalog_id == null ? (risposta?.name ?? "") : "",
    bande: (risposta?.bands ?? []).map((b) => b.band),
    nm: Object.fromEntries(
      (risposta?.bands ?? [])
        .filter((b) => b.width_nm != null)
        .map((b) => [b.band, numeroNelCampo(b.width_nm ?? 0)]),
    ),
  }))

  // La risposta e' quella della strada scelta: le altre restano scritte, ma non partono.
  const manda = (
    m: Modo,
    quale: { mio?: number | null; modello?: string | null; nuovo?: Nuovo },
  ) => {
    const sceltoMio = quale.mio !== undefined ? quale.mio : mio
    const sceltoModello = quale.modello !== undefined ? quale.modello : modello
    const m2 = modelli.find((x) => x.id === sceltoModello)
    const r: Risposta | null =
      m === "mio"
        ? sceltoMio === null
          ? null
          : { id: filtro.id, merge_into: sceltoMio }
        : m === "catalogo"
          ? m2
            ? {
                id: filtro.id,
                catalog_id: m2.id,
                brand: m2.brand,
                name: etichetta(m2),
                model: m2.name,
              }
            : null
          : diNuovo(filtro.id, quale.nuovo ?? nuovo)
    onRisposta(filtro.id, r)
  }
  const scriviNuovo = (n: Nuovo) => {
    setNuovo(n)
    manda("nuovo", { nuovo: n })
  }

  const parole = cerca.trim().toLowerCase().split(/\s+/).filter(Boolean)
  // L'elenco compare scrivendo, non prima (304 voci tutte insieme mandavano il browser in timeout).
  const trovati = parole.length
    ? modelli.filter((m) => parole.every((p) => etichetta(m).toLowerCase().includes(p)))
    : []
  // il modello in mano resta in vista, in cima, anche se la ricerca non lo comprende
  const inMano = modelli.find((m) => m.id === modello && risposta?.catalog_id === m.id)
  const visti = inMano && !trovati.includes(inMano) ? [inMano, ...trovati] : trovati
  const breve = (): string | null => {
    if (!risposta) return null
    if (risposta.merge_into != null)
      return t("review.filters.mine", {
        nome: miei.find((f) => f.id === risposta.merge_into)?.name ?? "",
      })
    if (risposta.catalog_id != null) return risposta.name ?? ""
    const bande = (risposta.bands ?? [])
      .map((b) =>
        b.width_nm == null
          ? nomeDellaBanda(b.band)
          : `${nomeDellaBanda(b.band)} ${numero(b.width_nm)} nm`,
      )
      .join(" + ")
    return t("review.filters.newNamed", { nome: risposta.name ?? "", bande })
  }
  const detta = breve()
  const capo = t("review.filters.how", { nome: filtro.name })
  return (
    <Domanda
      id={`filters:${filtro.id}`}
      voce={filtro.name}
      nome={filtro.name}
      frame={rigaDeiFrame(filtro.frames)}
      stato={statoDi(false, risposta !== undefined)}
      detta={detta !== null}
      breve={
        detta ??
        Object.values(MODI)
          .map((parola) => t(parola))
          .join(" \u00b7 ")
      }
      prova={[...provaDegliOggetti(filtro.subjects), ...provaDegliStrumenti(filtro.rigs)]}
    >
      <Parte capo={capo} prima>
        <Risposte
          etichetta={capo}
          opzioni={(Object.keys(MODI) as Modo[]).map((m) =>
            voce(
              modo === m,
              t(MODI[m]),
              () => {
                setModo(m)
                manda(m, {})
              },
              undefined,
              m === "catalogo" && senzaModelli,
            ),
          )}
        />
        {senzaModelli && <AvvisoModelli />}
        {modo === "mio" && (
          <Sotto
            etichetta={t("review.filters.way.mine")}
            opzioni={miei.map((f) =>
              voce(mio === f.id, f.name, () => {
                setMio(f.id)
                manda("mio", { mio: f.id })
              }),
            )}
          />
        )}
        {modo === "catalogo" && (
          <>
            <Campi
              campi={[
                {
                  id: `cerca-${filtro.id}`,
                  etichetta: t("review.filters.searchFor", { nome: filtro.name }),
                  valore: cerca,
                  onValore: setCerca,
                  suggerimento: t("review.filters.searchHint"),
                },
              ]}
            />
            {visti.length > 0 && (
              <Modelli
                id={`modelli-${filtro.id}`}
                modelli={visti}
                scelto={modello}
                onScelta={(m) => {
                  setModello(m)
                  manda("catalogo", { modello: m })
                }}
              />
            )}
            {parole.length > 0 && trovati.length === 0 && (
              <Nota>{t("review.filters.noneFound", { cerca: cerca.trim() })}</Nota>
            )}
          </>
        )}
        {modo === "nuovo" && (
          <>
            <Campi
              campi={[
                {
                  id: `nome-${filtro.id}`,
                  etichetta: t("review.filters.name"),
                  valore: nuovo.nome,
                  onValore: (nome) => scriviNuovo({ ...nuovo, nome }),
                },
              ]}
            />
            <Sotto
              titolo={t("review.filters.bands")}
              etichetta={t("review.filters.bands.label")}
              multipla
              opzioni={BANDE.map((b) =>
                voce(nuovo.bande.includes(b), nomeDellaBanda(b), () =>
                  scriviNuovo({
                    ...nuovo,
                    bande: nuovo.bande.includes(b)
                      ? nuovo.bande.filter((x) => x !== b)
                      : BANDE.filter((x) => x === b || nuovo.bande.includes(x)),
                  }),
                ),
              )}
            />
          </>
        )}
      </Parte>
      {modo === "nuovo" && nuovo.bande.length > 0 && (
        <Parte capo={t("review.filters.widths")} prima={false}>
          <Campi
            campi={nuovo.bande.map((b) => ({
              id: `nm-${filtro.id}-${b}`,
              etichetta: t("review.filters.width", { banda: nomeDellaBanda(b) }),
              valore: nuovo.nm[b] ?? "",
              onValore: (v: string) => scriviNuovo({ ...nuovo, nm: { ...nuovo.nm, [b]: v } }),
              suggerimento: t("review.filters.width.hint"),
              aiuto: t("review.gear.optics.optional"),
              numerico: true,
            }))}
          />
        </Parte>
      )}
    </Domanda>
  )
}

/** L'elenco dei modelli non risponde (tavola 191): la strada del catalogo e' spenta, e lo si dice. */
function AvvisoModelli() {
  return (
    <Avviso
      tipo="riga"
      formato={useContext(FormatoConf)}
      segno="!"
      titolo={t("review.models.failed")}
    />
  )
}

/** I modelli trovati (tavola 61): marca e nome, la voce scelta col segno. */
function Modelli({
  id,
  modelli,
  scelto,
  onScelta,
}: {
  id: string
  modelli: readonly Modello[]
  scelto: string | null
  onScelta: (id: string) => void
}) {
  return (
    <div className="al-conf__colonna-20">
      <span className="al-conf__testo-10" id={id}>
        {t("review.filters.found")}
      </span>
      <ul className="al-conf__colonna-21" role="listbox" aria-labelledby={id}>
        {modelli.map((m) => {
          const si = m.id === scelto
          return (
            // Una voce si sceglie col clic, o con Invio e Spazio quando ha il fuoco.
            <li
              key={m.id}
              className="al-conf__riga-14"
              role="option"
              aria-selected={si}
              tabIndex={0}
              onClick={() => onScelta(m.id)}
              onKeyDown={(e) => {
                if (e.key !== "Enter" && e.key !== " ") return
                e.preventDefault()
                onScelta(m.id)
              }}
              style={{
                background: si ? "var(--scelta)" : "transparent",
                color: si ? "var(--scelta-testo)" : "var(--testo)",
              }}
            >
              <b className="al-conf__testo-15">{m.brand}</b>
              <span className="al-conf__blocco-14">{senzaMarca(m)}</span>
              <span className="al-conf__testo-16" aria-hidden="true">
                {si ? "\u2713" : ""}
              </span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

/** Marca e nome, senza ripetere la marca quando il nome la porta gia' dentro ("Antlia Quad Band"):
 *  vale anche per il nome che si scrive nella risposta, o il doppione finirebbe nell'archivio. */
function etichetta(m: Modello) {
  return conMarca(m) ? m.name : `${m.brand} ${m.name}`
}

/** Il nome del modello senza la marca davanti, accanto alla marca in grassetto. */
function senzaMarca(m: Modello) {
  return conMarca(m) ? m.name.slice(m.brand.length).trim() : m.name
}

/** Il nome del modello comincia gia' con la marca. */
function conMarca(m: Modello) {
  return m.name.toLowerCase().startsWith(m.brand.toLowerCase())
}
