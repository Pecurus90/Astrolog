/**
 * Il nome di una costellazione a partire dalla sua sigla IAU: il **nome latino ufficiale**, uguale
 * in ogni lingua e mai tradotto (Marco, 27/9/2026) -- e' quello dei cataloghi, e vale per tutti.
 *
 * Fonte: la tabella delle 88 costellazioni dell'IAU,
 * https://www.iau.org/IAU/IAU/Astronomy-FAQs/Constellations.aspx (letta il 27/9/2026). Piu' `Se1` e
 * `Se2`, le due parti di Serpens che il catalogo usa accanto a `Ser` (guida di OpenNGC,
 * `NGC_guide.txt`: Serpens Caput e Serpens Cauda). Che ogni sigla del catalogo abbia il suo nome lo
 * prova `frontend/tests/costellazioni.test.ts`, contro il catalogo impacchettato.
 */
export const COSTELLAZIONI: Record<string, string> = {
  And: "Andromeda",
  Ant: "Antlia",
  Aps: "Apus",
  Aqr: "Aquarius",
  Aql: "Aquila",
  Ara: "Ara",
  Ari: "Aries",
  Aur: "Auriga",
  Boo: "Bo\u00f6tes",
  Cae: "Caelum",
  Cam: "Camelopardalis",
  Cnc: "Cancer",
  CVn: "Canes Venatici",
  CMa: "Canis Major",
  CMi: "Canis Minor",
  Cap: "Capricornus",
  Car: "Carina",
  Cas: "Cassiopeia",
  Cen: "Centaurus",
  Cep: "Cepheus",
  Cet: "Cetus",
  Cha: "Chamaeleon",
  Cir: "Circinus",
  Col: "Columba",
  Com: "Coma Berenices",
  CrA: "Corona Australis",
  CrB: "Corona Borealis",
  Crv: "Corvus",
  Crt: "Crater",
  Cru: "Crux",
  Cyg: "Cygnus",
  Del: "Delphinus",
  Dor: "Dorado",
  Dra: "Draco",
  Equ: "Equuleus",
  Eri: "Eridanus",
  For: "Fornax",
  Gem: "Gemini",
  Gru: "Grus",
  Her: "Hercules",
  Hor: "Horologium",
  Hya: "Hydra",
  Hyi: "Hydrus",
  Ind: "Indus",
  Lac: "Lacerta",
  Leo: "Leo",
  LMi: "Leo Minor",
  Lep: "Lepus",
  Lib: "Libra",
  Lup: "Lupus",
  Lyn: "Lynx",
  Lyr: "Lyra",
  Men: "Mensa",
  Mic: "Microscopium",
  Mon: "Monoceros",
  Mus: "Musca",
  Nor: "Norma",
  Oct: "Octans",
  Oph: "Ophiuchus",
  Ori: "Orion",
  Pav: "Pavo",
  Peg: "Pegasus",
  Per: "Perseus",
  Phe: "Phoenix",
  Pic: "Pictor",
  Psc: "Pisces",
  PsA: "Piscis Austrinus",
  Pup: "Puppis",
  Pyx: "Pyxis",
  Ret: "Reticulum",
  Sge: "Sagitta",
  Sgr: "Sagittarius",
  Sco: "Scorpius",
  Scl: "Sculptor",
  Sct: "Scutum",
  Ser: "Serpens",
  Se1: "Serpens Caput",
  Se2: "Serpens Cauda",
  Sex: "Sextans",
  Tau: "Taurus",
  Tel: "Telescopium",
  Tri: "Triangulum",
  TrA: "Triangulum Australe",
  Tuc: "Tucana",
  UMa: "Ursa Major",
  UMi: "Ursa Minor",
  Vel: "Vela",
  Vir: "Virgo",
  Vol: "Volans",
  Vul: "Vulpecula",
}

/** Il nome della costellazione, o la sigla stessa se non la conosce: meglio la sigla che niente. */
export function costellazione(sigla: string): string {
  return COSTELLAZIONI[sigla] ?? sigla
}

/** Le sigle in ordine di **nome**, che e' come si leggono e si cercano a schermo: in ordine di
 *  sigla "CVn" verrebbe dopo "Cep", e Canes Venatici dopo Cepheus. */
export function inOrdineDiNome(sigle: string[]): string[] {
  return [...sigle].sort((a, b) => costellazione(a).localeCompare(costellazione(b)))
}

