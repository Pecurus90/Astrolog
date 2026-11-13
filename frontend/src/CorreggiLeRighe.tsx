import { type ReactNode, useState } from "react"

import { Campo } from "./Campo"
import { Modulo, NomeDelPezzo, type Scritto, con, useScrittura } from "./ModuloDelGesto"
import { CampoDellaScheda, sulModulo } from "./SchedaDelPezzo"
import { TendinaDiScelta } from "./TendinaDiScelta"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { t } from "./i18n"
import { testo } from "./scritto"

type Pezzo = components["schemas"]["InstrumentOnPage"]
type Schede = components["schemas"]["GearList"]["cards"]
type Scritta = components["schemas"]["InstrumentCorrection"]
type Genere = Pezzo["kind"]
type Filtro = components["schemas"]["FilterOnPage"]
type SchedaDelFiltro = components["schemas"]["FilterCorrection"]

/**
 * I gesti dell'Attrezzatura che **correggono una riga che c'e' gia'**: la scheda di un pezzo, la
 * scheda di un filtro, e "e' lo stesso di". Il gesto che ne scrive uno
 * nuovo, e i pezzi comuni dei moduli, stanno in `GestiDelPezzo`.
 */

/** Una riga dell'Attrezzatura da correggere, **dentro la riga**: il nome, i campi della sua scheda
 *  e "e' lo stesso di". Una casa sola per un pezzo e per un filtro. Un campo non toccato non parte:
 *  rimandare cio' che l'app ha letto dai file lo farebbe diventare una tua dichiarazione. E scelta
 *  l'unione la scheda non conta piu': i suoi campi si nascondono invece di partire e perdersi. */
export function CorreggiUnaRiga<S extends { merge_into?: number | null }>({
  base,
  nome,
  unibili,
  etichettaUnione,
  manda,
  onChiudi,
  campi,
}: {
  base: string
  nome: string
  /** In cosa si puo' unire: solo cio' che l'API dice (`mergeable_into`). */
  unibili: { id: number; name: string }[]
  etichettaUnione: string
  manda: (corpo: S) => Promise<{ data?: Scritto; error?: unknown }>
  onChiudi: () => void
  campi: (scritta: S, cambia: (campo: string, valore: unknown) => void) => ReactNode
}) {
  const [scritta, setScritta] = useState<S>({} as S)
  const unione = scritta.merge_into
  const scrivi = useScrittura(async () => {
    const { data, error } = await manda(unione != null ? ({ merge_into: unione } as S) : scritta)
    if (error) throw error
    return data
  }, onChiudi)
  const cambia = (campo: string, valore: unknown) => setScritta((s) => con(s, campo, valore))
  return (
    <Modulo
      base={base}
      titolo={t("gear.write.edit.title", { nome })}
      onManda={() => scrivi.mutate()}
      onAnnulla={onChiudi}
      salvando={scrivi.isPending}
      valido
      errore={scrivi.error}
    >
      {unione == null && (
        <NomeDelPezzo id={`${base}-name`} cheCera={nome} onNome={(n) => cambia("name", n)} />
      )}
      {unione == null && campi(scritta, cambia)}
      {unibili.length > 0 && (
        <TendinaDiScelta
          id={`${base}-merge`}
          etichetta={etichettaUnione}
          altri={unibili}
          valore={unione ?? undefined}
          // scegliere o togliere l'unione riparte da capo: i campi rimontano col valore di prima,
          // e una scritta rimasta indietro partirebbe senza che a video si veda
          onScelta={(id) => setScritta((id === undefined ? {} : { merge_into: id }) as S)}
        />
      )}
    </Modulo>
  )
}

export function CorreggiIlPezzo({
  pezzo,
  campi,
  unibili,
  onChiudi,
}: {
  pezzo: Pezzo
  campi: Schede[Genere]
  unibili: Pezzo[]
  onChiudi: () => void
}) {
  const base = `correggi-${pezzo.id}`
  return (
    <CorreggiUnaRiga<Scritta>
      base={base}
      nome={pezzo.name}
      unibili={unibili}
      etichettaUnione={t("gear.write.sameAs")}
      manda={(body) =>
        api.PATCH("/api/v1/gear/instruments/{instrument_id}", {
          params: { path: { instrument_id: pezzo.id } },
          body,
        })
      }
      onChiudi={onChiudi}
      campi={(scritta, cambia) =>
        campi
          .filter(sulModulo)
          .map((campo) => (
            <CampoDellaScheda
              key={campo}
              id={`${base}-${campo}`}
              campo={campo}
              valore={scritta[campo] ?? pezzo[campo]}
              onValore={(v) => cambia(campo, v)}
            />
          ))
      }
    />
  )
}

export function CorreggiIlFiltro({
  filtro,
  altri,
  onChiudi,
}: {
  filtro: Filtro
  /** I filtri in cui questo si puo' unire: quelli che l'API dice (`mergeable_into`). */
  altri: Filtro[]
  onChiudi: () => void
}) {
  const base = `filtro-${filtro.id}`
  return (
    <CorreggiUnaRiga<SchedaDelFiltro>
      base={base}
      nome={filtro.name}
      unibili={altri}
      etichettaUnione={t("gear.write.filter.sameAs")}
      manda={(body) =>
        api.PATCH("/api/v1/gear/filters/{filter_id}", {
          params: { path: { filter_id: filtro.id } },
          body,
        })
      }
      onChiudi={onChiudi}
      campi={(_, cambia) =>
        (["brand", "model"] as const).map((campo) => (
          <Campo key={campo} id={`${base}-${campo}`} etichetta={t(`review.card.${campo}`)}>
            <input
              className="as-campo-modulo__input"
              id={`${base}-${campo}`}
              defaultValue={filtro[campo] ?? ""}
              onChange={(e) => cambia(campo, testo(e.target.value, filtro[campo]))}
            />
          </Campo>
        ))
      }
    />
  )
}
