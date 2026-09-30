"""Riempie i buchi del catalogo chiedendo a SIMBAD, e riscrive il file.

Tre buchi e nient'altro: **il nome comune** (che l'app non usa per decidere, ma senza il quale
scrive "NGC 1976" dove serve "Orion Nebula"), **la magnitudine** e **la dimensione** (con cui
`identify` sceglie il soggetto e il Planner dice se ci sta nel campo). Redshift, distanza e
compagnia non si chiedono: nessuna schermata li usa.

Gira a mano quando si vuole ricompletare il catalogo, mai dentro l'app. Dopo, il file e'
completo **offline**.

    python tools/arricchisci_catalogo.py [--prova]
    python tools/arricchisci_catalogo.py --da <bundle di partenza>

`--prova` mostra cosa chiederebbe e a chi, senza toccare la rete ne' il file. `--da` rifa' il
catalogo dalla sorgente, snellendolo ai campi che restano: e' il passo che ha prodotto il file
che spediamo, e senza di lui l'artefatto non sarebbe rifacibile da niente nel repo.
"""

import hashlib
import json
import sys
from pathlib import Path

import catalogo
import simbad

RADICE = Path(__file__).resolve().parents[1]
DATI = RADICE / "backend" / "astrolog" / "catalog" / "data"
# Le voci che SIMBAD non conosce: si ricordano, o si richiederebbero a ogni giro. Un guasto di
# rete NON finisce qui -- quello si ritenta, ed e' la differenza che conta.
ASSENTI = Path(__file__).with_name("simbad-assenti.json")
# Le correzioni nostre: valori che una fonte AFFERMA e che sappiamo falsi. Hanno l'ultima
# parola, dopo l'arricchimento -- SIMBAD dice che `IC 434` e' la Flame Nebula, e non lo e'.
CORREZIONI = DATI / "correzioni.json"


def catalogo_corrente():
    trovati = sorted(DATI.glob("catalogo-*.json"))
    if not trovati:
        raise SystemExit(f"nessun catalogo in {DATI}")
    if len(trovati) > 1:
        # due file in cartella vorrebbe dire caricare il vecchio in silenzio
        raise SystemExit(f"due cataloghi in {DATI}: {[p.name for p in trovati]}")
    return trovati[0]


def regole_di_richiesta():
    """L'impronta delle regole con cui si compone una richiesta. Se cambia -- una spaziatura
    in piu', un catalogo che scopriamo chiamarsi in un altro modo -- la lista delle voci
    "sconosciute" non vale piu': era stata compilata chiedendo male."""
    testo = json.dumps([sorted(simbad.ALTRO_NOME.items()), list(simbad.SPAZI)], sort_keys=True)
    return hashlib.sha256(testo.encode()).hexdigest()[:12]


def assenti_note():
    """Le voci che SIMBAD non conosce, **se** sono state chieste con le regole di oggi."""
    if not ASSENTI.exists():
        return set()
    dati = json.loads(ASSENTI.read_text(encoding="utf-8"))
    if dati.get("regole") != regole_di_richiesta():
        print("  le regole di richiesta sono cambiate: la lista delle sconosciute riparte")
        return set()
    return set(dati.get("sigle", ()))


def cataloghi_delle_sigle(voci):
    """I nomi di catalogo presenti (`NGC`, `Abell`, ...), dal piu' frequente: e' una richiesta
    per ognuno, non una per oggetto."""
    conto = {}
    for voce in voci:
        for c, _d in voce.get("n") or ():
            conto[c] = conto.get(c, 0) + 1
    return sorted(conto, key=lambda c: -conto[c])


def snellisci_da(sorgente):
    """Rifa' il catalogo dalla sorgente, snellito ai campi che restano. La versione porta
    l'impronta del contenuto: cambia se e solo se cambia il dato."""
    testa, voci = catalogo.leggi(sorgente)
    snelle, scarti = catalogo.snellisci_con_scarti(voci)
    impronta = hashlib.sha256(
        json.dumps(snelle, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()[:8]
    testa["version"] = f"{testa.get('built_at', '')[:10].replace('-', '')}-{impronta}"
    for vecchio in DATI.glob("catalogo-*.json"):
        vecchio.unlink()  # due file in cartella si caricherebbero a caso
    nuovo = DATI / f"catalogo-{testa['version']}.json"
    peso = catalogo.scrivi(nuovo, testa, snelle)
    print(f"snellito {sorgente} -> {nuovo.name}: {len(snelle)} voci, {peso / 1048576:.2f} MB")
    if scarti:
        print(f"  scartate perche' senza cielo: {len(scarti)}")
    return nuovo


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    prova = "--prova" in argv
    if "--da" in argv:
        snellisci_da(argv[argv.index("--da") + 1])

    percorso = catalogo_corrente()
    testa, voci = catalogo.leggi(percorso)
    prima = catalogo.copertura(voci)
    assenti = assenti_note()
    chiedere = catalogo.da_chiedere(voci, assenti)
    cataloghi = cataloghi_delle_sigle(voci)

    print(f"catalogo {percorso.name}: {len(voci)} voci")
    print(f"  nomi da chiedere:   {len(cataloghi)} richieste (una per catalogo)")
    print(f"  misure da chiedere: {len(chiedere)} voci in "
          f"{-(-len(chiedere) // simbad.LOTTO)} richieste da {simbad.LOTTO}")  # fmt: skip
    if assenti:
        print(f"  gia' note come sconosciute a SIMBAD, non si richiedono: {len(assenti)}")
    if prova:
        print("\n--prova: non ho chiesto niente e non ho scritto niente")
        return 0

    nomi = {}
    for i, cat in enumerate(cataloghi, 1):
        trovati = simbad.nomi(cat)
        nomi.update(trovati)
        print(f"  [{i}/{len(cataloghi)}] nomi {cat}: {len(trovati)}")

    misure = simbad.misure(chiedere)
    print(f"  misure: {len(misure)} voci riconosciute su {len(chiedere)} chieste")

    voci, conto = catalogo.arricchisci(voci, nomi=nomi, misure=misure)

    curate = json.loads(CORREZIONI.read_text(encoding="utf-8"))["correzioni"]
    voci, applicate = catalogo.correggi(voci, curate)
    print(f"  correzioni curate applicate: {applicate} su {len(curate)}")

    ignote = catalogo.sconosciute(chiedere, misure, assenti)
    ASSENTI.write_text(
        json.dumps({"regole": regole_di_richiesta(), "sigle": ignote}, indent=0), encoding="utf-8"
    )
    impronta = hashlib.sha256(
        json.dumps(voci, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()[:8]
    testa["version"] = f"{testa['version'].split('-')[0]}-{impronta}"
    nuovo = DATI / f"catalogo-{testa['version']}.json"
    peso = catalogo.scrivi(nuovo, testa, voci)
    if nuovo != percorso:
        percorso.unlink()  # due file in cartella si caricherebbero a caso

    dopo = catalogo.copertura(voci)
    print(f"\nscritto {nuovo.name} ({peso / 1048576:.2f} MB)")
    print(f"{'campo':22} {'prima':>7} {'dopo':>7} {'guadagno':>9}")
    for campo in ("common_name", "magnitude", "size_major_arcmin", "size_minor_arcmin"):
        print(f"  {campo:20} {prima[campo]:7} {dopo[campo]:7} {conto.get(campo, 0):+9}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
