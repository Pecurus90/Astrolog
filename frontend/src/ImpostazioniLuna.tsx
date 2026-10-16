import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

import { Avviso } from "./Avviso"
import { Campo } from "./Campo"
import { api } from "./api/client"
import { type Chiave, numero, t } from "./i18n"
import { usePreferenze } from "./preferenze"

type Soglia = "moon_broadband_max_pct" | "moon_broadband_min_dark_h"

const SOGLIE: { chiave: Soglia; etichetta: Chiave }[] = [
  { chiave: "moon_broadband_max_pct", etichetta: "settings.moon.maxPct" },
  { chiave: "moon_broadband_min_dark_h", etichetta: "settings.moon.minDark" },
]
type Misura = { min: number; max: number }

/**
 * La sezione **Luna**: le due soglie delle notti buone per la banda larga, che il calendario della
 * Luna della Dashboard segna. Si salvano lasciando il campo; il backend rigiudica le notti subito.
 */
export function Luna() {
  const preferenze = usePreferenze().data
  const valori = preferenze?.values
  return (
    <section className="as-carta" aria-labelledby="impostazioni-luna">
      <div className="as-carta__intestazione">
        <div>
          <h2 className="as-carta__titolo" id="impostazioni-luna">{t("settings.moon.title")}</h2>
          <p className="as-carta__domanda">{t("settings.moon.what")}</p>
        </div>
      </div>
      <div className="as-carta__corpo as-carta__corpo--stretto">
        {/* la misura la manda il backend (`config.RANGES`): fuori, ogni notte sarebbe buona o nessuna */}
        {valori && SOGLIE.map((s) => {
          const misura = preferenze.ranges[s.chiave]
          return misura && <CampoSoglia key={s.chiave} soglia={s} misura={misura} salvato={Number(valori[s.chiave])} />
        })}
        <p className="as-carta__domanda">{t("settings.moon.source")}</p>
      </div>
    </section>
  )
}

function CampoSoglia({ soglia: s, misura, salvato }: { soglia: (typeof SOGLIE)[number]; misura: Misura; salvato: number }) {
  const [scritto, setScritto] = useState(String(salvato))
  const [fuori, setFuori] = useState(false)
  const dati = useQueryClient()
  const salva = useMutation({
    mutationFn: async (valore: number) => {
      const { data, error } = await api.PATCH("/api/v1/settings", { body: { values: { [s.chiave]: valore } } })
      if (error) throw new Error(t("settings.moon.failed"))
      return data
    },
    onSuccess: (data) => {
      dati.setQueryData(["settings"], data)
      void dati.invalidateQueries({ queryKey: ["moon-calendar"] })
    },
  })
  const lascia = () => {
    const n = Number(scritto)
    const valido = scritto.trim() !== "" && Number.isInteger(n) && n >= misura.min && n <= misura.max
    setFuori(!valido)
    if (valido && n !== salvato) salva.mutate(n)
  }
  const id = `soglia-${s.chiave}`
  return (
    <>
      <Campo id={id} etichetta={t(s.etichetta)} errore={fuori ? t("settings.moon.range", { min: numero(misura.min), max: numero(misura.max) }) : undefined}
        aspetta={salva.isPending}>
        <input id={id} type="number" inputMode="numeric" min={misura.min} max={misura.max} step={1} value={scritto}
          onChange={(ev) => setScritto(ev.target.value)} onBlur={lascia} />
      </Campo>
      {salva.error && <Avviso esito="allarme">{salva.error.message}</Avviso>}
    </>
  )
}
