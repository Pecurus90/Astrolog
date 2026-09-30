import { useInfiniteQuery } from "@tanstack/react-query"
import { useState } from "react"

import { TempoDellePose } from "./TempoDellePose"
import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { Campo } from "./Campo"
import { Altre, paginaDopo } from "./Elenco"
import { Riga } from "./Riga"
import { Sezione } from "./Sezione"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { numero, t } from "./i18n"

// Quanti oggetti gia' visti per volta: una schermata abbondante, senza montarne mille in un colpo.
const PER_VOLTA = 50

type Oggetto = components["schemas"]["ObjectOut"]
type Candidato = components["schemas"]["ObjectCandidate"]
type Risposta = components["schemas"]["ObjectEdit"]

/**
 * Gli oggetti: cosa l'app crede di aver ripreso, e cosa era davvero.
 *
 * - **In cima chi ha un dubbio**, coi candidati da cliccare quando il cielo ne ha trovati; sotto
 *   gli altri nuovi, e chiusi i gia' visti, che si chiedono a pagine solo aprendoli.
 *   L'ordine e' quello che manda l'API e questa
 *   pagina **non lo tocca**: riordinare qui sarebbe lo stesso fatto deciso in due case.
 * - **La risposta viaggia sulla chiave stabile**, mai sul numero di riga: `identify` cancella
 *   gli oggetti rimasti senza pose e li rifa' con numeri nuovi, e una risposta agganciata a un
 *   numero punterebbe al nulla.
 * - **Un bersaglio solo**: lo slug di un candidato **oppure** un nome scritto, mai tutti e due.
 */
export function SezioneOggetti({
  oggetti,
  certi,
  risposte,
  onRisposta,
}: {
  oggetti: Oggetto[]
  /** Quanti sono gli oggetti gia' visti, senza niente da scegliere, che l'API non manda con la pagina. */
  certi: number
  risposte: Record<string, Risposta>
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  // Gli oggetti gia' visti non sono domande, e crescono con l'archivio (Marco, 27/9/2026): stanno
  // chiusi, e si chiedono a pagine solo quando qualcuno li apre. Chiusa la riga non si mostra
  // niente, nemmeno cio' che la cache ricorda: una query spenta non si rilegge dopo l'Applica.
  const [aperti, setAperti] = useState(false)
  const elenco = useInfiniteQuery({
    queryKey: ["review", "settled"],
    enabled: aperti,
    initialPageParam: 0,
    queryFn: async ({ pageParam }) => {
      const { data, error } = await api.GET("/api/v1/review/objects/settled", {
        params: { query: { limit: PER_VOLTA, offset: pageParam } },
      })
      if (error) throw new Error(t("review.objects.settledFailed"))
      return data
    },
    getNextPageParam: paginaDopo,
  })
  const caricati = aperti ? (elenco.data?.pages.flatMap((p) => p.items) ?? []) : []

  return (
    <Sezione
      titolo={t("review.objects")}
      voci={[...oggetti, ...caricati]}
      chiave={(o) => o.id}
      riga={(o) => <RigaOggetti oggetto={o} risposta={risposte[o.key]} onRisposta={onRisposta} />}
      piede={
        <>
          {!aperti && certi > 0 && (
            <Bottone onClick={() => setAperti(true)}>
              {t("review.objects.settled", { n: numero(certi) })}
            </Bottone>
          )}
          {elenco.error && <Avviso esito="allarme">{elenco.error.message}</Avviso>}
          <Altre elenco={elenco} testo="review.objects.more" />
        </>
      }
    />
  )
}

function RigaOggetti({
  oggetto,
  risposta,
  onRisposta,
}: {
  oggetto: Oggetto
  risposta: Risposta | undefined
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  const [aMano, setAMano] = useState(false)
  const scelto = oggetto.candidates.find((c) => c.slug === risposta?.slug)
  // Il nome con cui l'oggetto si presenta: lo stesso in testa alla riga e nell'etichetta del
  // campo, cosi' chi sta rispondendo e chi legge con uno schermo sentono la stessa parola.
  const nome = oggetto.name ?? oggetto.key

  return (
    <Riga
      nome={nome}
      nomeDiCatalogo={oggetto.name !== null}
      frames={oggetto.frames}
      stato={risposta ? "risposta" : undefined}
      dettagli={<TempoDellePose secondi={oggetto.integration_s} senzaTempo={oggetto.untimed} />}
    >
      {scelto && (
        <>
          {/* **Dice che quella e' la risposta.** Collaudando sull'archivio vero la riga si
              leggeva "NGC 5980 60 pose 1 h IC 1133": il bersaglio scelto sembrava un altro
              conteggio, e chi rilegge la pagina non sa piu' cosa ha risposto. */}{" "}
          <span>{t("review.objects.chosen", { nome: nomeCandidato(scelto) })}</span>{" "}
          {/* **Una scelta non e' un vicolo cieco finche' non si preme Applica**: senza questo,
              un clic sbagliato si correggeva solo ricaricando la pagina. */}
          <Bottone
            piccolo
            onClick={() => {
              setAMano(false)
              onRisposta(oggetto.key, null)
            }}
          >
            {t("review.objects.change")}
          </Bottone>
        </>
      )}
      {!scelto && aMano && (
        <>
          {/* L'etichetta **nomina la riga**: con due oggetti aperti insieme ci sono due campi, e
              due campi che si chiamano uguale non si distinguono -- ne' per chi legge con uno
              schermo, ne' per chi ci scrive dentro. Stessa ragione gia' scritta sui filtri. */}
          <Campo id={`oggetto-${oggetto.id}`} etichetta={t("review.objects.name", { nome })}>
          <input
            className="as-campo__input"
            id={`oggetto-${oggetto.id}`}
            value={risposta?.name ?? ""}
            // Un nome svuotato **toglie** la risposta invece di mandarne una vuota: `ObjectEdit`
            // pretende almeno un carattere, e una stringa vuota tornerebbe indietro con un 422
            // che annullerebbe anche le risposte buone -- l'Applica e' una transazione sola.
            onChange={(e) =>
              onRisposta(
                oggetto.key,
                e.target.value ? { key: oggetto.key, name: e.target.value } : null,
              )
            }
          />
          </Campo>
          {/* **Si torna ai candidati.** Aperto il campo, l'elenco del cielo spariva e non c'era
              modo di tornarci: un clic sbagliato si correggeva solo ricaricando la pagina. E'
              la stessa lezione gia' pagata sui filtri, che qui non era stata riportata. */}
          {oggetto.candidates.length > 0 && (
            <Bottone
              piccolo
              onClick={() => {
                setAMano(false)
                onRisposta(oggetto.key, null)
              }}
            >
              {t("review.objects.change")}
            </Bottone>
          )}
        </>
      )}
      {!scelto && !aMano && (
        <>
          {oggetto.candidates.length > 0 && (
            <ul>
              {oggetto.candidates.map((c) => (
                <li key={c.slug}>
                  <Bottone
                    piccolo
                    onClick={() => onRisposta(oggetto.key, { key: oggetto.key, slug: c.slug })}
                  >
                    {t("review.objects.candidate", { nome: nomeCandidato(c), dove: dove(c) })}
                  </Bottone>
                </li>
              ))}
            </ul>
          )}
          {/* Anche su un oggetto certo: una risposta e' una **correzione**, non un lucchetto --
              "cio' che avete trovato come `ngc-7023`, per me e' `ldn-1174`". Il campo si apre
              premendo, non da solo: un archivio con trecento oggetti avrebbe trecento caselle
              aperte, ed e' il difetto che la tendina dei filtri ha gia' pagato. */}
          <Bottone piccolo onClick={() => setAMano(true)}>
            {t("review.objects.correct")}
          </Bottone>
        </>
      )}
    </Riga>
  )
}

/** Il nome del candidato col suo nome comune, quando ce l'ha: `NGC 7023` da solo non dice a
 *  nessuno che e' la Iris, ed e' quello il modo in cui uno riconosce cio' che ha ripreso. */
function nomeCandidato(c: Candidato) {
  return c.common_name ? `${c.name} (${c.common_name})` : c.name
}

/** Se cadeva **dentro** l'inquadratura o era solo li' accanto -- la domanda che fa scegliere: il
 *  piu' vicino al centro non e' sempre il soggetto. E `in_frame` nullo **non e' un no**: senza i
 *  lati e la rotazione il campo si e' approssimato a un cerchio, quindi non si sa. Mostrarlo come
 *  "accanto" sarebbe una bugia; tacerlo farebbe scegliere al buio. */
function dove(c: Candidato) {
  if (c.in_frame === null) return t("review.objects.unknownFrame")
  return c.in_frame ? t("review.objects.inFrame") : t("review.objects.nearby")
}
