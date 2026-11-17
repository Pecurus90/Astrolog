import { useState } from "react"
import { BrowserRouter, Route, Routes } from "react-router"

import { RipristinoProposto, useBackup } from "./Backup"
import { Layout } from "./Layout"
import { PaginaCheNonCe } from "./PaginaCheNonCe"
import { AvvioInAttesa, AvvioNonRisponde } from "./PrimoAvvioCornice"
import { Wizard } from "./Wizard"
import { VesteSalvata, vesteDa } from "./componenti/Tema"
import { usaLingua } from "./i18n"
import { ComingSoon } from "./ComingSoon"
import { PAGINE, sezioniAperte } from "./pagine"
import { usePreferenze } from "./preferenze"

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
  // Dopo "Fine" il timbro e' scritto, ma il primo avvio resta a schermo con la sua chiusura
  // finche' non si preme "Apri AstroLog": senza questo, una rilettura delle impostazioni (basta
  // tornare sulla scheda) la toglierebbe da sotto gli occhi. Lo accende il primo avvio stesso,
  // quando chiude: dedotto dal timbro che manca, si accenderebbe anche a meta' di un ripristino.
  const [inChiusura, setInChiusura] = useState(false)

  // Lingua e tema dalle preferenze: cambiata la lingua, `key` rimonta tutto, perche' `t()` non
  // e' reattivo; il tema lo leggono i `Tema` senza props, primo avvio compreso.
  const valori = settings.data?.values
  const lingua = usaLingua(String(valori?.language ?? ""))
  const veste = vesteDa(valori?.theme_mode, valori?.theme_accent)

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
    if (backup.data?.offer === "found") return <RipristinoProposto stato={backup.data} />
    if (settings.data && (inChiusura || !settings.data.wizard_done))
      return (
        <Wizard
          onChiusura={() => setInChiusura(true)}
          // Si spegne a impostazioni rilette: prima, per un attimo varrebbe il timbro vecchio.
          onDone={() => void settings.refetch().then(() => setInChiusura(false))}
          manca={settings.data.missing}
        />
      )
    return null
  })()
  return (
    <VesteSalvata veste={veste}>
    <BrowserRouter key={lingua}>
      {porta ?? (
      <Layout>
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
      </Layout>
      )}
    </BrowserRouter>
    </VesteSalvata>
  )
}
