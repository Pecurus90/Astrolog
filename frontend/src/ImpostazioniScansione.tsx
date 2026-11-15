import { Carta } from "./componenti/Carta"
import { gesto } from "./componenti/gesto"
import type { Formato } from "./componenti/Tema"
import { detto, giornoDetto, statoDi, useGesto, useStato } from "./Scansiona"
import { numero, orario, t } from "./i18n"

/**
 * **Scansione** (tavola Impostazioni v82, 123-128 and 324-329): the last scan or the running one,
 * and the same gesture as Scansiona in the gear menu (the backend's `action`).
 */
export function CartaScansione({ formato }: { formato: Formato }) {
  const tel = formato === "telefono"
  const dati = useStato().data
  const azione = useGesto()
  const stato = statoDi(dati)
  let titolo: string
  let riga: string
  let bottone = t("scan.start")
  if (dati && stato !== "ferma") {
    const d = detto(dati, stato)
    titolo = d.titolo
    riga = d.riga || d.fase
    bottone = d.bottone
  } else if (dati?.last_scan) {
    const u = dati.last_scan
    titolo = t("settings.scan.last", {
      giorno: giornoDetto(u.ended_at, u.ended_day),
      ora: orario(u.ended_at),
    })
    const nuovi = u.new === 0 ? t("frame.scan.new.none") : t("frame.scan.new", { n: numero(u.new) })
    riga =
      u.not_read === 0
        ? t("settings.scan.last.ok", { nuovi })
        : t("settings.scan.last.unread", {
            nuovi,
            nonLetti: t("frame.scan.unread", { n: numero(u.not_read) }),
          })
  } else {
    titolo = t("settings.scan.never")
    riga = t(tel ? "settings.scan.never.how.phone" : "settings.scan.never.how")
  }
  return (
    <Carta
      formato={formato}
      colonne={4}
      ritardo={60}
      padding={tel ? "20px" : "24px 28px"}
      gap={tel ? 12 : 14}
      etichetta={t("frame.scan.group")}
    >
      <span className={tel ? "al-imp__testo-27" : "al-imp__testo-3"}>{t("frame.scan.group")}</span>
      <span className="al-imp__colonna-1" aria-live="polite">
        <b className="al-imp__testo-7">{titolo}</b>
        {riga && <span className="al-imp__testo-5">{riga}</span>}
      </span>
      <a
        href="#"
        role="button"
        aria-disabled={azione.isPending || !dati ? "true" : undefined}
        onClick={gesto(() => {
          if (dati && !azione.isPending) azione.mutate(dati.action)
        })}
        className={
          tel
            ? "al-bottone al-bottone--pieno al-bottone--blocco"
            : "al-bottone al-bottone--pieno al-bottone--blocco al-bottone--a-sinistra al-imp__blocco-10"
        }
      >
        {bottone}
      </a>
      {azione.error && (
        <span className="al-imp__testo-20" aria-live="polite">
          {`✕ ${azione.error.message}` /* glifo-ok: segno della tavola */}
        </span>
      )}
      <span className={tel ? "al-imp__testo-8" : "al-imp__testo-11"}>
        {t(tel ? "settings.scan.also.phone" : "settings.scan.also")}
      </span>
    </Carta>
  )
}
