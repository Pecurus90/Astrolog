import { Carta } from "./componenti/Carta"
import { Pillola } from "./componenti/Pillola"
import { mancanza } from "./contiDelSetup"
import { ESITO } from "./DashboardDati"
import { decimali, t } from "./i18n"
import type { Notte } from "./MeteoDati"

type Setup = Notte["setups"][number]

// the sampling's pill (board v82, DECISIONI v16): ideal is good, under and over uncertain
const CAMPIONE = {
  ideal: { esito: 0, testo: "meteo.sampling.ideal" },
  under: { esito: 1, testo: "meteo.sampling.under" },
  over: { esito: 1, testo: "meteo.sampling.over" },
} as const

const SEEING = {
  go: "meteo.sampling.seeing.go",
  marginal: "meteo.sampling.seeing.marginal",
  nogo: "meteo.sampling.seeing.nogo",
} as const

const nome = (s: Setup) => s.name ?? [s.optics, s.camera].filter(Boolean).join(" · ") // glifo-ok: board separator
const scala = (s: Setup) => t("gear.n.arcsecPx", { n: decimali(s.scale_arcsec_px, 2) })
const ottimo = (s: Setup) =>
  t("meteo.sampling.note", { da: decimali(s.seeing_from, 1), a: decimali(s.seeing_to, 1) })

/** Beside the sampling (Marco, 24/11/2026): the seeing against the setup's floor, or what it lacks. */
function limite(s: Setup): string {
  if (s.floor_arcsec !== null) return t("meteo.sampling.floor", { f: decimali(s.floor_arcsec, 1) })
  return s.floor_missing
    ? t("meteo.sampling.floor.missing", { manca: mancanza(s.floor_missing) })
    : ""
}

function Pillole({ s, tel }: { s: Setup; tel: boolean }) {
  const c = CAMPIONE[s.sampling]
  const fondo = tel ? "carta2" : "carta"
  const allinea = tel ? "center" : "flex-start"
  return (
    <>
      <Pillola
        esito={c.esito}
        testo={t(c.testo)}
        fondo={fondo}
        dimensione="piccola"
        allinea={allinea}
      />
      {s.seeing_level && (
        <Pillola
          esito={ESITO[s.seeing_level]}
          testo={t(SEEING[s.seeing_level])}
          fondo={fondo}
          dimensione="piccola"
          allinea={allinea}
        />
      )}
    </>
  )
}

/**
 * **Campionamento** (board v82, after Altre misure): each setup's scale against the night's forecast
 * seeing, and the seeing against the setup's floor. Absent when the night has no setups: the
 * backend sends none without a number of seeing, for a trend night, or without a setup.
 */
export function Campionamento({ notte: n, seeing }: { notte: Notte; seeing: number }) {
  if (n.setups.length === 0) return null
  return (
    <Carta
      etichetta={t("meteo.sampling.title")}
      colonne={12}
      ritardo={280}
      padding="24px 28px"
      gap="12"
      griglia="220px repeat(5,minmax(0,1fr))"
      allinea="center"
    >
      <span className="al-meteo__colonna-11">
        <span className="al-meteo__testo-11">{t("meteo.sampling.title")}</span>
        <span className="al-meteo__testo-2">
          {t("meteo.sampling.sub", { s: decimali(seeing, 1) })}
        </span>
      </span>
      {n.setups.map((s) => (
        <span key={s.rig_id} className="al-meteo__colonna-13">
          <span className="al-meteo__testo-19">{nome(s)}</span>
          <span className="al-meteo__testo-20">{scala(s)}</span>
          <Pillole s={s} tel={false} />
          <span className="al-meteo__testo-21">{ottimo(s)}</span>
          <span className="al-meteo__testo-21">{limite(s)}</span>
        </span>
      ))}
    </Carta>
  )
}

/** The phone's: at the bottom of the card of the other measures (board v82, line 152). */
export function CampionamentoTel({ notte: n, seeing }: { notte: Notte; seeing: number }) {
  if (n.setups.length === 0) return null
  return (
    <div className="al-meteo__colonna-27">
      <span className="al-meteo__testo-23">{t("meteo.sampling.title")}</span>
      <span className="al-meteo__testo-14">
        {t("meteo.sampling.sub.tel", { s: decimali(seeing, 1) })}
      </span>
      {n.setups.map((s) => (
        <span key={s.rig_id} className="al-meteo__riga-38">
          <span className="al-meteo__colonna-28">
            <span className="al-meteo__testo-13">{nome(s)}</span>
            <span className="al-meteo__testo-32">
              {scala(s)} · {ottimo(s) /* glifo-ok: board separator */}
            </span>
            <span className="al-meteo__testo-32">{limite(s)}</span>
          </span>
          <span className="al-meteo__riga-39">
            {/* one over the other: side by side they squeeze the setup's lines */}
            <span className="al-meteo__colonna-5">
              <Pillole s={s} tel />
            </span>
          </span>
        </span>
      ))}
    </div>
  )
}
