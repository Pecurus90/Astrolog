import { useState } from "react"
import { Campo } from "./Campo"
import { Bottone } from "./Bottone"
import { TendinaDellaBanda } from "./TendinaDellaBanda"
import { TendinaDiScelta } from "./TendinaDiScelta"

import { Riga } from "./Riga"
import { Sezione } from "./Sezione"
import type { components } from "./api/schema"
import { t } from "./i18n"

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
 * - **dal catalogo**: si cerca scrivendo fra i modelli in commercio; marca, nome e banda si
 *   compilano e restano **fissi**, perche' sono il modello -- correggerli farebbe nascere un
 *   doppione travestito da voce ufficiale, con `catalog_id` a dire una cosa che il nome smentisce.
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
    <Sezione titolo={t("review.filters")} domanda={t("review.filters.why")}
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
  const [aMano, setAMano] = useState(false)
  const dalCatalogo = risposta?.catalog_id != null

  // **L'elenco si apre scrivendo, non prima.** Collaudando sull'archivio vero: otto filtri da
  // rispondere per 38 modelli facevano **304 bottoni** tutti insieme, e il renderer del browser
  // e' andato in timeout. Una tendina si apre quando la si usa.
  // La ricerca guarda marca e nome insieme: uno scrive "antlia" o "alp" senza pensare a quale dei
  // due campi sia.
  const scritto = cerca.trim().toLowerCase()
  const visti = scritto
    ? modelli.filter((m) => etichetta(m).toLowerCase().includes(scritto))
    : []

  const scegli = (m: Modello) => {
    setAMano(false)
    onRisposta(filtro.id, {
      id: filtro.id,
      catalog_id: m.id,
      brand: m.brand,
      name: etichetta(m),
      model: m.name,
    })
  }

  return (
    <Riga
      nome={filtro.name}
      frames={filtro.frames}
      stato={risposta ? "risposta" : undefined}
    >
      {!aMano && !dalCatalogo && (
      <>
        {/* La voce vuota toglie la risposta, invece di mandarne una vuota. */}
        <TendinaDiScelta
          id={`mio-${filtro.id}`}
          etichetta={t("review.filters.mine", { nome: filtro.name })}
          altri={miei}
          valore={risposta?.merge_into ?? undefined}
          onScelta={(mio) =>
            onRisposta(filtro.id, mio === undefined ? null : { id: filtro.id, merge_into: mio })
          }
        />
        {/* L'etichetta nomina il filtro: con due filtri da rispondere ci sono due tendine, e
            due campi che si chiamano uguale non si distinguono -- ne' per chi legge con uno
            schermo, ne' per chi ci scrive dentro. */}
        <Campo id={`cerca-${filtro.id}`} etichetta={t("review.filters.searchFor", { nome: filtro.name })}>
          <input
            className="as-campo-modulo__input"
            id={`cerca-${filtro.id}`}
            value={cerca}
            onChange={(e) => setCerca(e.target.value)}
          />
        </Campo>
        <ul className="as-comparsa__righe">
          {visti.map((m) => (
            <li key={m.id}>
              <button className="as-comparsa__voce" type="button" onClick={() => scegli(m)}>
                {etichetta(m)}
              </button>
            </li>
          ))}
        </ul>
        <Bottone
          verso="nudo"
          piccolo
          onClick={() => {
            // e' l'altra strada: "uno dei miei" scelto prima non resta in mano, nascosto
            setAMano(true)
            if (risposta?.merge_into != null) onRisposta(filtro.id, null)
          }}
        >
          {t("review.filters.notListed")}
        </Bottone>
      </>
      )}

      {dalCatalogo && (
        <>
          <Campo id={`nome-${filtro.id}`} etichetta={t("review.filters.name")}>            {/* Fisso, non spento: si legge e si copia, ma non si corregge -- e' il modello. */}
            <input
              className="as-campo-modulo__input"
              id={`nome-${filtro.id}`}
              value={risposta?.name ?? ""}
              readOnly
            />
          </Campo>
          {/* **Si torna indietro.** Prima, scelto un modello, sparivano sia la ricerca sia "non
              e' in elenco": un clic sbagliato non si correggeva piu' senza ricaricare la pagina.
              Una scelta non e' un vicolo cieco finche' non si preme Applica. */}
          <Bottone piccolo onClick={() => onRisposta(filtro.id, null)}>
            {t("review.filters.change")}
          </Bottone>
        </>
      )}

      {aMano && <AMano filtro={filtro} risposta={risposta} onRisposta={onRisposta} />}
    </Riga>
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
  return m.name.toLowerCase().startsWith(m.brand.toLowerCase()) ? m.name : `${m.brand} ${m.name}`
}
