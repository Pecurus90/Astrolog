import { Pillola } from "./componenti/Pillola"
import { type Formato, useTema } from "./componenti/Tema"
import { anello } from "./anelloDeiFiltri"
import type { components } from "./api/schema"
import { contiDelSetup } from "./contiDelSetup"
import { decimali, numero, t } from "./i18n"
import { MISURE_DETTAGLIO, nomeDelSetup } from "./misureDelSetup"
import { pallinoDi } from "./MisureDati"

type Pagina = components["schemas"]["GearList"]
type Corredo = components["schemas"]["RigOnPage"]

// [T] Attrezzatura.dc.html `anello` (443): the paper thread between two slices, in percent
const FILO = 0.8
// [T] `lunaBg` (328): the full Moon on the comparison, per mode
const LUNA = { scuro: "rgba(236,230,214,.85)", chiaro: "rgba(138,132,116,.35)" } as const

/**
 * La colonna destra del dettaglio di un setup (tavola v82, 77-97): il **Campo** misurato sul cielo
 * col confronto fra i setup e la Luna, i **Dati del setup** dalle schede, l'anello dei **Filtri**.
 * Riquadri, Luna e fette arrivano in percento dall'API: qui si disegnano.
 */
export function CampoDelSetup({
  pagina,
  setup,
  formato,
}: {
  pagina: Pagina
  setup: Corredo
  formato: Formato
}) {
  return (
    <>
      <Campo pagina={pagina} setup={setup} formato={formato} />
      {setup.numbers && <Dati setup={setup} conti={setup.numbers} formato={formato} />}
      <Filtri setup={setup} formato={formato} />
    </>
  )
}

function Campo({
  pagina,
  setup: r,
  formato,
}: {
  pagina: Pagina
  setup: Corredo
  formato: Formato
}) {
  const { modo } = useTema()
  const m = MISURE_DETTAGLIO[formato]
  const misurato = r.scale_arcsec_px !== null
  const suCornice = pagina.fields.some((b) => b.rig_id === r.id)
  const titoli = new Map(pagina.rigs.map((x) => [x.id, x.title ?? nomeDelSetup(x)]))
  const confronto = t(
    pagina.fields.length > 1 ? "gear.field.compare" : "gear.field.compare.alone",
    {
      nome: nomeDelSetup(r),
    },
  )
  return (
    <section
      className="al-attr__colonna-14"
      aria-label={t("gear.field.label")}
      style={{ borderRadius: m.angolo, padding: m.dentro }}
    >
      {misurato ? (
        <>
          <span className="al-attr__testo-17">{t("gear.field.word")}</span>
          {r.width_deg !== null && r.height_deg !== null && (
            <span className="al-attr__testo-18" data-an="big" style={{ fontSize: m.medio }}>
              {t("gear.field.sides", {
                larghezza: decimali(r.width_deg, 2),
                altezza: decimali(r.height_deg, 2),
              })}
            </span>
          )}
          <span className="al-attr__testo-19">
            <b className="al-attr__testo-20">{decimali(r.scale_arcsec_px ?? 0, 2)}</b>{" "}
            <span className="al-attr__testo-16">
              {t("gear.field.scaleFromSky", { n: r.scale_arcsec_px ?? 0 })}
            </span>
          </span>
        </>
      ) : (
        <span className="al-attr__riga-25">
          <span className="al-attr__tondo-7" aria-hidden="true" />
          {t("gear.noScale")}
        </span>
      )}
      {suCornice && pagina.moon_pct !== null && (
        <div className="al-attr__riquadro-2" role="img" aria-label={confronto}>
          {pagina.fields.map((b, k) => {
            const su = b.rig_id === r.id
            return (
              <span
                key={b.rig_id}
                className="al-attr__strato-1"
                style={{
                  width: `${b.width_pct}%`,
                  height: `${b.height_pct}%`,
                  border: su ? "2px solid var(--accento)" : "1.5px solid var(--tenue)",
                  background: su
                    ? "color-mix(in srgb, var(--accento) 16%, transparent)"
                    : "transparent",
                  zIndex: su ? 2 : 1,
                }}
              >
                <span
                  className="al-attr__strato-2"
                  style={{
                    top: k % 2 ? "auto" : "4px",
                    bottom: k % 2 ? "4px" : "auto",
                    fontWeight: su ? 600 : 500,
                    color: su ? "var(--testo)" : "var(--tenue)",
                  }}
                >
                  {titoli.get(b.rig_id)}
                </span>
              </span>
            )
          })}
          <span className="al-attr__strato-3" style={{ width: `${pagina.moon_pct}%` }}>
            <span className="al-attr__tondo-8" style={{ background: LUNA[modo] }} />
            <span className="al-attr__strato-4">{t("gear.field.moon")}</span>
          </span>
        </div>
      )}
    </section>
  )
}

function Dati({
  setup,
  conti,
  formato,
}: {
  setup: Corredo
  conti: NonNullable<Corredo["numbers"]>
  formato: Formato
}) {
  const m = MISURE_DETTAGLIO[formato]
  return (
    <section
      className="al-attr__colonna-15"
      aria-labelledby="dt-num"
      style={{ borderRadius: m.angolo, padding: m.dentro }}
    >
      <div className="al-attr__colonna-16">
        <h3 className="al-attr__testo-2" id="dt-num">
          {t("gear.numbers")}
        </h3>
        <span className="al-attr__testo-12">{t("gear.numbers.from")}</span>
      </div>
      <ul className="al-attr__colonna-17" aria-labelledby="dt-num">
        {contiDelSetup(setup, conti).map((k) => (
          <li key={k.chiave} className="al-attr__colonna-18" data-an="riga" data-conto={k.chiave}>
            <span className="al-attr__riga-26">
              <span className="al-attr__testo-17">{k.l}</span>
              {k.v && <span className="al-attr__testo-21">{k.v}</span>}
            </span>
            {k.pillola && k.esito !== null && (
              <Pillola
                esito={k.esito}
                testo={k.pillola}
                fondo="carta2"
                dimensione="piccola"
                allinea="flex-start"
              />
            )}
            {k.sub && <span className="al-attr__testo-22">{k.sub}</span>}
            {k.manca && (
              <span className="al-attr__riga-27">
                <span className="al-attr__tondo-9" aria-hidden="true">
                  ?
                </span>
                <span className="al-attr__blocco-8">{k.manca}</span>
              </span>
            )}
          </li>
        ))}
      </ul>
    </section>
  )
}

function Filtri({ setup, formato }: { setup: Corredo; formato: Formato }) {
  const m = MISURE_DETTAGLIO[formato]
  const fette = setup.parts.flatMap((p) =>
    p.kind === "filter" && p.ring_from !== null && p.ring_to !== null && p.passband !== null
      ? [{ nome: p.name, ring_from: p.ring_from, ring_to: p.ring_to, passband: p.passband }]
      : [],
  )
  if (fette.length === 0) return null
  const nomi = fette.map((f) => f.nome).join(", ")
  return (
    <section
      className="al-attr__colonna-19"
      aria-labelledby="dt-filtri"
      style={{ borderRadius: m.angolo, padding: m.dentro }}
    >
      <div className="al-attr__griglia-2">
        <div className="al-attr__colonna-20">
          <div className="al-attr__colonna-21">
            <h3 className="al-attr__testo-2" id="dt-filtri">
              {t("gear.filters")}
            </h3>
            <span className="al-attr__testo-12">{t("gear.ring")}</span>
          </div>
          <ul className="al-attr__colonna-22">
            {fette.map((f) => (
              <li key={f.nome} className="al-attr__riga-28">
                <span
                  className="al-attr__tondo-10"
                  aria-hidden="true"
                  style={pallinoDi(f.passband)}
                />
                {f.nome}
              </li>
            ))}
          </ul>
        </div>
        <div
          className="al-attr__tondo-11"
          role="img"
          aria-label={t("gear.ring.label", { nomi })}
          style={{ width: m.anello, height: m.anello, background: anello(fette, FILO) }}
        >
          <span className="al-attr__tondo-12">
            <span className="al-attr__testo-23">{numero(fette.length)}</span>
            <span className="al-attr__testo-12">{t("gear.ring.n", { n: fette.length })}</span>
          </span>
        </div>
      </div>
    </section>
  )
}
