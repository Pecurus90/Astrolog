import { useState } from "react"

import { statoDi } from "./ConfermareGuscio"
import { Campi, Domanda, Parte, Risposte, Sotto, rigaDeiFrame, voce } from "./Domanda"
import { type PerGruppo, Sezione } from "./Sezione"
import { provaDegliOggetti, provaDegliStrumenti } from "./Soggetti"
import type { components } from "./api/schema"
import { notte, t } from "./i18n"

type Cartella = components["schemas"]["UndatedFolder"]
type Risposta = components["schemas"]["UndatedEdit"]
type Modo = "data" | "notte"

/**
 * I frame che non dicono **quando** sono stati ripresi (Marco, 6/11/2026: si risponde qui), una
 * domanda per cartella. Si risponde con la sera della ripresa: scritta, o scelta fra le notti con
 * lo stesso setup. La data del file sul disco e' della copia: e' una prova, mai una risposta.
 *
 * - **Una data scritta parte solo se e' un giorno vero**: il 30 febbraio il backend lo rifiuta, e
 *   con lui tutto l'Applica.
 * - **Una cartella risposta resta in pagina**, e ridare la data salvata non manda niente.
 */
export function SezioneSenzaData({ gruppi, risposte, onRisposta }: PerGruppo<Cartella, Risposta>) {
  return (
    <Sezione
      quale="undated"
      domanda={t("review.undated.why")}
      voci={gruppi}
      chiave={(g) => g.key}
      riga={(g, indice) => (
        <RigaSenzaData
          indice={indice}
          cartella={g}
          risposta={risposte[g.key]}
          onRisposta={onRisposta}
        />
      )}
    />
  )
}

/** `gg/mm/aaaa` come data `YYYY-MM-DD`, o `null` se non e' un giorno del calendario. */
export function dataScritta(scritta: string): string | null {
  const parti = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(scritta.trim())
  if (!parti) return null
  const [g, m, a] = [Number(parti[1]), Number(parti[2]), Number(parti[3])]
  const giorno = new Date(Date.UTC(a, m - 1, g))
  if (giorno.getUTCFullYear() !== a || giorno.getUTCMonth() !== m - 1 || giorno.getUTCDate() !== g)
    return null
  const data = `${String(a).padStart(4, "0")}-${String(m).padStart(2, "0")}-${String(g).padStart(2, "0")}`
  // l'ultimo giorno del calendario non ha il mezzogiorno dopo: il backend lo rifiuta (UndatedEdit)
  return data === "9999-12-31" ? null : data
}

/** Una data `YYYY-MM-DD` come si scrive nel campo. */
const nelCampo = (data: string) => data.split("-").reverse().join("/")

function RigaSenzaData({
  indice,
  cartella,
  risposta,
  onRisposta,
}: {
  indice: number
  cartella: Cartella
  risposta: Risposta | undefined
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  const data0 = risposta?.night ?? cartella.answer
  // Una sera fra le notti del setup si riapre scelta; le altre si riaprono scritte.
  const [modo, setModo] = useState<Modo | null>(
    data0 === null ? null : cartella.rig_nights.includes(data0) ? "notte" : "data",
  )
  const [scritta, setScritta] = useState(
    data0 !== null && !cartella.rig_nights.includes(data0) ? nelCampo(data0) : "",
  )
  const [scelta, setScelta] = useState<string | null>(
    data0 !== null && cartella.rig_nights.includes(data0) ? data0 : null,
  )

  const manda = (sera: string | null) =>
    onRisposta(
      cartella.key,
      sera === null || sera === cartella.answer ? null : { key: cartella.key, night: sera },
    )
  const conSito = (sera: string) =>
    cartella.site ? `${notte(sera)}, ${cartella.site}` : notte(sera)
  const detta = risposta?.night ?? cartella.answer
  const capo = t("review.undated.question", { cartella: cartella.key })
  return (
    <Domanda
      id={`undated:${cartella.key}`}
      voce={cartella.key}
      nome={cartella.key}
      frame={rigaDeiFrame(cartella.frames, cartella.integration_s, cartella.untimed)}
      stato={statoDi(cartella.answer !== null, risposta !== undefined)}
      era={
        cartella.answer ? t("review.undated.night", { notte: notte(cartella.answer) }) : undefined
      }
      detta={detta !== null}
      breve={
        detta !== null
          ? t("review.undated.night", { notte: notte(detta) })
          : `${t("review.undated.write")} \u00b7 ${t("review.undated.choose")}`
      }
      prova={[
        { nome: t("review.proof.fileDate"), righe: [t("review.unknown.f")], tenue: true },
        ...(cartella.file_nights.length > 0
          ? [
              {
                nome: t("review.proof.diskDate"),
                righe: [
                  t("review.undated.copy", { date: cartella.file_nights.map(notte).join(", ") }),
                ],
                tenue: true,
              },
            ]
          : []),
        ...provaDegliOggetti(cartella.subjects),
        ...provaDegliStrumenti(cartella.rigs),
      ]}
    >
      <Parte capo={capo} prima>
        <Risposte
          etichetta={capo}
          opzioni={[
            voce(
              modo === "data",
              t("review.undated.write"),
              () => {
                setModo("data")
                manda(dataScritta(scritta))
              },
              t("review.undated.write.why"),
            ),
            voce(
              modo === "notte",
              t("review.undated.choose"),
              () => {
                setModo("notte")
                manda(scelta)
              },
              t("review.undated.choose.why"),
              cartella.rig_nights.length === 0,
            ),
          ]}
        />
        {modo === "data" && (
          <Campi
            campi={[
              {
                id: `senza-data-${indice}`,
                etichetta: t("review.undated.evening"),
                valore: scritta,
                onValore: (v) => {
                  setScritta(v)
                  manda(dataScritta(v))
                },
                suggerimento: t("review.undated.evening.hint"),
                aiuto: cartella.site
                  ? t("review.undated.evening.site", { sito: cartella.site })
                  : t("review.undated.evening.why"),
              },
            ]}
          />
        )}
        {modo === "notte" && (
          <Sotto
            titolo={t("review.undated.rigNights")}
            etichetta={t("review.proof.night")}
            opzioni={cartella.rig_nights.map((sera) =>
              voce(scelta === sera, conSito(sera), () => {
                setScelta(sera)
                manda(sera)
              }),
            )}
          />
        )}
      </Parte>
    </Domanda>
  )
}
