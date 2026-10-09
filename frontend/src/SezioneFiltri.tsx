import { useState } from "react"
import { Campo } from "./Campo"
import { Scelte } from "./Scelte"
import { TendinaDellaBanda } from "./TendinaDellaBanda"
import { TendinaDiScelta } from "./TendinaDiScelta"

import { Domanda } from "./Domanda"
import { Sezione } from "./Sezione"
import type { components } from "./api/schema"
import { type Chiave, t } from "./i18n"

type Filtro = components["schemas"]["FilterOut"]
type Mio = components["schemas"]["FilterCandidate"]
type Modello = components["schemas"]["FilterModelOut"]
type Risposta = components["schemas"]["FilterEdit"]

/**
 * I filtri che l'app ha trovato negli header e **non riconosce** (Marco, 25/9/2026): "che filtro e'
 * H?". Quelli che riconosce non sono una domanda e qui non arrivano.
 *
 * **Tre strade, e si sa sempre in quale sei** (Marco, 14/9/2026):
 *
 * - **uno dei miei**: si sceglie fra i filtri con la banda nota, e la risposta e' l'unione -- la
 *   grafia dell'header diventa per sempre quel filtro.
 * - **dal catalogo**: si cerca scrivendo fra i modelli in commercio, e quello scelto e' la voce
 *   scelta dell'elenco. Marca, nome e banda **non si scrivono**, perche' sono il modello --
 *   correggerli farebbe nascere un doppione travestito da voce ufficiale.
 * - **a mano**: chi ha un filtro che il catalogo non conosce scrive nome e banda, e `catalog_id`
 *   resta fuori ("NULL se nome libero", lo dice lo schema).
 *
 * Il filtro **esiste gia'** in tutti e due i casi: nasce dagli header quando la scansione lo
 * incontra, con banda `UNKNOWN`. Qui non si crea niente, si da' un'identita'.
 *
 * L'ordine e' quello che manda l'API -- in cima chi chiede una risposta, poi i piu' usati -- e
 * questa pagina **non lo tocca**: riordinare qui sarebbe lo stesso fatto deciso in due case.
 */
export function SezioneFiltri({
  filtri,
  miei,
  modelli,
  risposte,
  onRisposta,
}: {
  filtri: Filtro[]
  miei: Mio[]
  modelli: Modello[]
  risposte: Record<number, Risposta>
  onRisposta: (id: number, r: Risposta | null) => void
}) {
  return (
    <Sezione quale="filters" domanda={t("review.filters.why")}
      voci={filtri}
      chiave={(f) => f.id}
      riga={(f) => (
        <RigaFiltri
          filtro={f}
          miei={miei}
          modelli={modelli}
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

function RigaFiltri({
  filtro,
  miei,
  modelli,
  risposta,
  onRisposta,
}: {
  filtro: Filtro
  miei: Mio[]
  modelli: Modello[]
  risposta: Risposta | undefined
  onRisposta: (id: number, r: Risposta | null) => void
}) {
  const [cerca, setCerca] = useState("")
  // Parte dalla risposta in mano: la sezione si rimonta quando si chiude e si riapre. Senza
  // risposta si parte dal catalogo, che e' la strada di quasi tutti.
  const [modo, setModo] = useState<Modo>(
    risposta === undefined || risposta.catalog_id != null
      ? "catalogo"
      : risposta.merge_into != null
        ? "mio"
        : "nuovo",
  )

  // **L'elenco compare scrivendo, non prima.** Collaudando sull'archivio vero: otto filtri da
  // rispondere per 38 modelli facevano 304 voci tutte insieme, e il browser e' andato in timeout.
  // La ricerca guarda marca e nome insieme: uno scrive "antlia" o "alp" senza pensare a quale dei
  // due campi sia.
  const scritto = cerca.trim().toLowerCase()
  const scelto = modelli.find((m) => m.id === risposta?.catalog_id)
  const trovati = scritto ? modelli.filter((m) => etichetta(m).toLowerCase().includes(scritto)) : []
  // Il modello gia' scelto resta in vista, in cima, anche se la ricerca non lo comprende: una
  // risposta che sta per partire non sparisce dallo schermo.
  const visti = scelto && !trovati.includes(scelto) ? [scelto, ...trovati] : trovati

  const scegli = (m: Modello) =>
    onRisposta(filtro.id, {
      id: filtro.id,
      catalog_id: m.id,
      brand: m.brand,
      name: etichetta(m),
      model: m.name,
    })

  const mio = miei.find((m) => m.id === risposta?.merge_into)
  const idCerca = `cerca-${filtro.id}`
  return (
    <Domanda
      id={`filters:${filtro.id}`}
      voce={filtro.name}
      nome={filtro.name}
      cifre
      frames={filtro.frames}
      salvata={false}
      inMano={risposta !== undefined}
      breve={
        risposta ? (
          <b>{mio?.name ?? risposta.name ?? ""}</b>
        ) : (
          Object.values(MODI)
            .map((parola) => t(parola))
            .join(" \u00b7 ")
        )
      }
    >
      <Scelte
        domanda={t("review.filters.how", { nome: filtro.name })}
        nome={`modo-${filtro.id}`}
        opzioni={(Object.keys(MODI) as Modo[]).map((valore) => ({ valore, etichetta: t(MODI[valore]) }))}
        scelta={modo}
        onScelta={(nuovo) => {
          // Sono strade diverse e non si sommano: la risposta data per un'altra non resta in
          // mano, nascosta, a partire con Applica.
          setModo(nuovo)
          if (risposta) onRisposta(filtro.id, null)
        }}
      />
      <div className="as-domanda-modo">
        {modo === "mio" && (
          // La voce vuota toglie la risposta, invece di mandarne una vuota.
          <TendinaDiScelta
            id={`mio-${filtro.id}`}
            etichetta={t("review.filters.mine", { nome: filtro.name })}
            altri={miei}
            valore={risposta?.merge_into ?? undefined}
            onScelta={(quale) =>
              onRisposta(filtro.id, quale === undefined ? null : { id: filtro.id, merge_into: quale })
            }
          />
        )}
        {modo === "catalogo" && (
          <>
            {/* L'etichetta nomina il filtro: con due filtri ci sono due campi, e due campi che si
                chiamano uguale non si distinguono. */}
            <Campo id={idCerca} etichetta={t("review.filters.searchFor", { nome: filtro.name })}>
              <input
                className="as-campo-modulo__input"
                id={idCerca}
                placeholder={t("review.filters.searchHint")}
                value={cerca}
                onChange={(e) => setCerca(e.target.value)}
              />
            </Campo>
            {visti.length > 0 && (
              <ul className="as-comparsa" role="listbox" aria-label={t("review.filters.found")}>
                {visti.map((m) => (
                  // Una voce si sceglie col clic, o con Invio e Spazio quando ha il fuoco.
                  <li
                    key={m.id}
                    className="as-comparsa__voce"
                    role="option"
                    aria-selected={m.id === risposta?.catalog_id}
                    tabIndex={0}
                    onClick={() => scegli(m)}
                    onKeyDown={(e) => {
                      if (e.key !== "Enter" && e.key !== " ") return
                      e.preventDefault()
                      scegli(m)
                    }}
                  >
                    {/* La marca a parte, senza ripeterla quando il nome la porta gia' dentro. */}
                    {!conMarca(m) && (
                      <>
                        <span className="as-comparsa__marca">{m.brand}</span>{" "}
                      </>
                    )}
                    {m.name}
                  </li>
                ))}
              </ul>
            )}
            {scritto !== "" && trovati.length === 0 && (
              <p className="as-comparsa as-comparsa--niente" aria-live="polite">
                {t("review.filters.noneFound", { cerca: cerca.trim() })}
              </p>
            )}
          </>
        )}
        {modo === "nuovo" && <AMano filtro={filtro} risposta={risposta} onRisposta={onRisposta} />}
      </div>
    </Domanda>
  )
}

/** La strada di chi in catalogo non c'e': il nome che vuole, e la banda -- che e' cio' che
 *  sblocca le pose. La **larghezza** in nanometri e' facoltativa, e pretenderla fermerebbe la
 *  risposta su una cosa che un anti inquinamento luminoso non ha. */
function AMano({
  filtro,
  risposta,
  onRisposta,
}: {
  filtro: Filtro
  risposta: Risposta | undefined
  onRisposta: (id: number, r: Risposta | null) => void
}) {
  // "Uno dei miei" scelto prima si perde: e' l'altra strada, e non si sommano -- restando dentro
  // la risposta, il backend unirebbe e il nome scritto qui sparirebbe.
  const { merge_into: _, ...prima } = risposta ?? { id: filtro.id }
  const banda = risposta?.bands?.[0]
  return (
    <>
      <Campo id={`nome-${filtro.id}`} etichetta={t("review.filters.name")}>
          <input
          className="as-campo-modulo__input"
          id={`nome-${filtro.id}`}
          value={risposta?.name ?? ""}
          onChange={(e) =>
            onRisposta(filtro.id, { ...prima, id: filtro.id, name: e.target.value })
          }
        />
      </Campo>
      <TendinaDellaBanda
        id={`banda-${filtro.id}`}
        etichetta={t("review.filters.band")}
        valore={banda?.band}
        onBanda={(b) => onRisposta(filtro.id, { ...prima, id: filtro.id, bands: [{ band: b }] })}
      />
    </>
  )
}

/** Marca e nome, senza ripetere la marca quando il nome la porta gia' dentro.
 *
 *  Otto modelli su 38 si chiamano cosi' ("Antlia Quad Band", "ZWO Duo-Band", "Optolong CLS"), e
 *  comporre marca + nome dava "Antlia Antlia Quad Band" -- visto collaudando. Vale anche per il
 *  nome che si SCRIVE nella risposta, non solo per quello che si legge: il doppione finirebbe
 *  nell'archivio. */
function etichetta(m: Modello) {
  return conMarca(m) ? m.name : `${m.brand} ${m.name}`
}

/** Il nome del modello comincia gia' con la marca. */
function conMarca(m: Modello) {
  return m.name.toLowerCase().startsWith(m.brand.toLowerCase())
}
