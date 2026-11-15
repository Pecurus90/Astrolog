import { Link, useLocation } from "react-router"

import { Carta } from "./componenti/Carta"
import { useFormato } from "./componenti/formato"
import { gesto } from "./componenti/gesto"
import { Tema } from "./componenti/Tema"
import { t } from "./i18n"

/**
 * **Meteo** (tavola Impostazioni v82, 131-138 and 332-341): where Meteo opens, and the sources.
 * Deep sky is the only page there is: Sole stays off until the Sun arrives (DECISIONI 9.8), so
 * there is nothing to save yet. The Meteoblue key lives in Servizi only.
 */
export function Meteo() {
  const formato = useFormato()
  const tel = formato === "telefono"
  const search = useLocation().search
  const scelte = (
    <span
      role="radiogroup"
      aria-label={t("settings.weather.opens")}
      className={
        tel
          ? "al-scelta al-scelta--linguette al-scelta--sottili al-scelta--riempie"
          : "al-scelta al-scelta--linguette al-scelta--sottili"
      }
    >
      <a
        href="#"
        role="radio"
        aria-checked="true"
        onClick={gesto(() => {})}
        className="al-scelta__voce"
      >
        {t("settings.weather.deepSky")}
      </a>
      <a
        href="#"
        role="radio"
        aria-checked="false"
        aria-disabled="true"
        onClick={gesto(() => {})}
        className="al-scelta__voce"
      >
        {t("settings.weather.sun")}
      </a>
    </span>
  )
  const servizi = (
    <Link
      to={{ pathname: "/impostazioni/servizi", search }}
      className={
        tel
          ? "al-bottone al-bottone--contorno al-bottone--blocco"
          : "al-bottone al-bottone--contorno al-bottone--piccolo"
      }
    >
      {t("settings.weather.openServices")}
    </Link>
  )
  return (
    <Tema>
      <div className={tel ? "al-imp__colonna-18" : "al-imp__griglia-2"}>
        <Carta
          formato={formato}
          colonne={6}
          ritardo={0}
          padding={tel ? "20px" : "24px 28px"}
          gap={tel ? 12 : 14}
          etichetta={t("settings.weather.card")}
        >
          <span className={tel ? "al-imp__testo-27" : "al-imp__testo-3"}>
            {t("settings.weather.card")}
          </span>
          {tel ? (
            <>
              <span className="al-imp__testo-5">{t("settings.weather.opens")}</span>
              {scelte}
              <span className="al-imp__testo-8">{t("settings.weather.sunOff")}</span>
              <span className="al-imp__testo-8">{t("settings.weather.sources.phone")}</span>
              {servizi}
            </>
          ) : (
            <>
              <span className="al-imp__colonna-8">
                <span className="al-imp__testo-2">{t("settings.weather.opens")}</span>
                {scelte}
                <span className="al-imp__testo-8">{t("settings.weather.sunOff")}</span>
              </span>
              <span className="al-imp__testo-16">{t("settings.weather.sources")}</span>
              <span className="al-imp__riga-4 al-imp__allinea">
                <span className="al-imp__testo-9">{t("settings.weather.key")}</span>
                {servizi}
              </span>
            </>
          )}
        </Carta>
      </div>
    </Tema>
  )
}
