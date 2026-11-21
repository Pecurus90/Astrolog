import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import { BrowserRouter, Route, Routes } from "react-router"

import { RipristinoProposto, useBackup } from "./Backup"
import { Layout } from "./Layout"
import { PaginaCheNonCe } from "./PaginaCheNonCe"
import { AvvioInAttesa, AvvioNonRisponde } from "./PrimoAvvioCornice"
import { VesteSalvata, vesteDa } from "./componenti/Tema"
import { caricaLingua, usaLingua } from "./i18n"
import { LINGUA_SORGENTE } from "./i18n/lingue"
import { ComingSoon } from "./ComingSoon"
import { REVISIONE } from "./api/revisione"
import { PAGINE, precaricaPagina, sezioniAperte } from "./pagine"
import { STATO } from "./Scansiona"
import { STANOTTE } from "./Stanotte"
import { Pigre } from "./Pigre"
import { pigra } from "./pigra"
import { useCambioDelTema, usePreferenze } from "./preferenze"

// only the first start opens it: out of every other download
const Wizard = pigra(() => import("./Wizard"), "Wizard")

/**
 * Il portiere dell'app: prima il **cancelletto** del primo avvio, poi la navigazione.
 *
 * - Senza il timbro non c'e' niente da navigare, e una barra laterale al primo avvio inviterebbe
 *   a girare per un'app che non sa ancora da dove osservi.
 * - Le pagine sono **indirizzi**, non stati: e' l'indirizzo che fa funzionare il tasto indietro e
 *   un collegamento che si manda a qualcuno. Sul NAS l'app si apre da tablet, dove il gesto
 *   indietro **e'** la navigazione: senza, si esce dall'app.
 * - Le pagine **montano** solo dopo il cancelletto, quindi non serve spegnere le loro chiamate a
 *   mano: cio' che non e' montato non chiede niente.
 * - **Quali pagine esistono lo dice `pagine.tsx`**, che e' la casa sola dello scheletro: qui si
 *   montano le rotte, e il `Layout` ne fa il binario.
 */

export function App() {
  const settings = usePreferenze()
  const backup = useBackup()
  const cache = useQueryClient()
  // Beside the gate, not after it: the shell's three questions and the page's file. A first
  // start pays three reads it does not show; every other start waits one round less.
  useEffect(() => {
    void cache.prefetchQuery(REVISIONE)
    void cache.prefetchQuery(STANOTTE)
    void cache.prefetchQuery(STATO)
    precaricaPagina(window.location.pathname)
  }, [cache])
  // Dopo "Fine" il timbro e' scritto, ma il primo avvio resta a schermo con la sua chiusura
  // finche' non si preme "Apri AstroLog": senza questo, una rilettura delle impostazioni (basta
  // tornare sulla scheda) la toglierebbe da sotto gli occhi. Lo accende il primo avvio stesso,
  // quando chiude: dedotto dal timbro che manca, si accenderebbe anche a meta' di un ripristino.
  const [inChiusura, setInChiusura] = useState(false)

  // Lingua e tema dalle preferenze: cambiata la lingua, `key` rimonta tutto, perche' `t()` non
  // e' reattivo; il tema lo leggono i `Tema` senza props, primo avvio compreso.
  const valori = settings.data?.values
  const scelta = String(valori?.language ?? "")
  // its texts download once; on a change the old language stays until the new one arrives.
  // Waits for the settings: else '' resolves to Italian and becomes the placeholder at start
  const testi = useQuery({
    queryKey: ["lingua", scelta],
    queryFn: () => caricaLingua(scelta),
    enabled: settings.data !== undefined,
    staleTime: Infinity,
    placeholderData: (prima) => prima,
  })
  const lingua = usaLingua(testi.data ?? LINGUA_SORGENTE)
  const veste = vesteDa(valori?.theme_mode, valori?.theme_accent, settings.data?.theme_now?.mode)
  useCambioDelTema()

  // Finche' non si sa, non si sceglie: mostrare l'app e poi sostituirla col primo avvio sarebbe
  // uno sfarfallio. E se la domanda non ha risposta non si tira a indovinare.
  // L'errore prende lo schermo solo se non si sa niente: una rilettura fallita lascia cio' che
  // si sapeva gia'. Un database nuovo con le risposte accanto: prima si chiede se rimetterle.
  // `missing` dice al primo avvio se fare la domanda di ASTAP, e quale.
  const porta = (() => {
    // Backup failed once: gate no more, its Riprova sets pending again (#91)
    const backupInLettura = backup.isPending && backup.errorUpdatedAt === 0
    if (settings.isPending || backupInLettura) return <AvvioInAttesa />
    if (settings.error && !settings.data)
      return <AvvioNonRisponde onRiprova={() => void settings.refetch()} />
    // a language that fails to download leaves the source: texts in Italian, not a blank app
    if (testi.isPending) return <AvvioInAttesa />
    if (backup.data?.offer === "found") return <RipristinoProposto stato={backup.data} />
    if (settings.data && (inChiusura || !settings.data.wizard_done))
      return (
        <Pigre attesa={<AvvioInAttesa />} fuoriDalTelaio>
          <Wizard
            onChiusura={() => setInChiusura(true)}
            // Si spegne a impostazioni rilette: prima, per un attimo varrebbe il timbro vecchio.
            onDone={() => void settings.refetch().then(() => setInChiusura(false))}
            manca={settings.data.missing}
          />
        </Pigre>
      )
    return null
  })()
  return (
    <VesteSalvata veste={veste}>
    <BrowserRouter key={lingua}>
      {porta ?? (
      <Layout>
        {/* a page downloads when opened (pagine.tsx): the frame stays while it arrives */}
        <Pigre>
        <Routes>
          {PAGINE.map((p) => (
            <Route key={p.a} path={p.a} element={p.elemento ?? <ComingSoon pagina={p.chiave} />} />
          ))}
          {/* Le sezioni sono indirizzi veri, non ancore: il tasto indietro funziona e il
              collegamento si manda. Portano tutte alla stessa pagina, che legge dall'indirizzo
              quale sezione mostrare. */}
          {PAGINE.flatMap((p) =>
            sezioniAperte(p.sezioni).map((s) => <Route key={s.a} path={s.a} element={p.elemento} />),
          )}
          <Route path="*" element={<PaginaCheNonCe />} />
        </Routes>
        </Pigre>
      </Layout>
      )}
    </BrowserRouter>
    </VesteSalvata>
  )
}
